"""Shared utilities: canonical hashing, tool paths, event log helpers.

Everything here is deterministic plumbing. No policy decisions live in this
module; the kernel (kernel/) is the only adjudicator.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import pathlib
import subprocess
import threading
import time

TASK_TIME_ENV = "CGB_TASK_TIME"


@contextlib.contextmanager
def task_time_guard():
    """Depth-safe task-time guard.

    Sets CGB_TASK_TIME=1 for the dynamic extent and restores the PRIOR value on
    exit, instead of unconditionally popping it.  A nested run_task/certify call
    therefore cannot clear an outer guard mid-session (the old finally-pop bug):
    the innermost exit restores "1", only the outermost exit clears it.
    """
    prev = os.environ.get(TASK_TIME_ENV)
    os.environ[TASK_TIME_ENV] = "1"
    try:
        yield
    finally:
        if prev is None:
            os.environ.pop(TASK_TIME_ENV, None)
        else:
            os.environ[TASK_TIME_ENV] = prev

# Process-wide lock for ALL z3/cvc5 usage.  The solver Python bindings use a
# process-global default context that is not thread-safe; every z3/cvc5 call
# site (SmtBackend, and the solver-as-input-generator helpers in
# constraint_gen / service_gen) acquires this so an orchestrator can fan
# certification layers out across threads without corrupting solver state.
# SMT obligations here are decidable and settle in milliseconds, so serializing
# them costs effectively nothing while the expensive, process-isolated sandbox
# and Dafny channels run fully in parallel.  Re-entrant for safety against any
# same-thread nesting.
SMT_LOCK = threading.RLock()

REPO_ROOT = pathlib.Path(__file__).resolve().parent
ARTIFACTS = pathlib.Path(os.environ.get("CGB_ARTIFACTS", REPO_ROOT / "artifacts"))
DB_PATH = pathlib.Path(os.environ.get("CGB_DB", str(ARTIFACTS / "registry.sqlite")))

# --- outsourced tool locations (overridable via env) -----------------------
KSC_CLASSPATH = os.environ.get("CGB_KSC_CLASSPATH", "/opt/ksc/lib/*")
KSC_MAIN = "io.kaitai.struct.JavaMain"
JAVA = os.environ.get("CGB_JAVA", "java")
TREE_SITTER = os.environ.get("CGB_TREE_SITTER", "/root/.cargo/bin/tree-sitter")
DAFNY = os.environ.get("CGB_DAFNY", "/root/.dotnet/tools/dafny")
CLAUDE_CLI = os.environ.get("CGB_CLAUDE_CLI", "/opt/node22/bin/claude")
CC = os.environ.get("CGB_CC", "cc")


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(obj) -> str:
    return sha256_bytes(canonical_json(obj).encode())


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def run_cmd(cmd, cwd=None, timeout=300, env=None, input_bytes=None):
    """Run a *trusted tool* (compiler/verifier binary) outside the sandbox.

    Emitted (generated) code must never go through here -- use sandbox.run_sandboxed.
    """
    return subprocess.run(
        cmd,
        cwd=cwd,
        timeout=timeout,
        env=env,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def ensure_dirs():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "events").mkdir(exist_ok=True)
    (ARTIFACTS / "certs").mkdir(exist_ok=True)
    (ARTIFACTS / "out").mkdir(exist_ok=True)


# ============================================================================
# F0.1 -- Lean 4 + pinned Mathlib toolchain pins (single-sourced, env-override)
# ============================================================================
#
# House rule (⚠D1, the flloat discipline): the **Mathlib commit is the single
# primary pin**.  The Lean toolchain is *derived* by reading `lean-toolchain`
# from that commit; `setup.sh --with-lean` checks the commit out, reads its
# `lean-toolchain`, and ASSERTS it equals `LEAN_TOOLCHAIN`, refusing on
# mismatch (independent pins that drift => a silent hours-long Mathlib source
# build).  This container has no Lean toolchain, so we cannot perform that
# derive here; we therefore store the *intended* toolchain as an
# env-overridable constant.  A stale placeholder can only ever fail setup (the
# derive-and-assert refuses), never yield a false green -- the safety property
# that makes storing an intended value honest.
#
# Every pin below is env-overridable so `setup.sh` and `common.py` stay
# single-sourced (setup reads the same CGB_* names).  Their joint sha ---
# `lean_toolchain_hash()` --- enters every Lean cache key (L2), alongside the
# narrow import set (⚠D15).

# The primary pin.  40-hex Mathlib commit; setup.sh derives+asserts the
# toolchain from `lean-toolchain` at this commit and refuses on mismatch.
# This is the REAL sha of the mathlib4 release tag `v4.15.0` (resolved via
# `git ls-remote https://github.com/leanprover-community/mathlib4.git
# refs/tags/v4.15.0`), whose `lean-toolchain` is the release
# `leanprover/lean4:v4.15.0` with a matching `lean4checker` tag (⚠D1/D2).
# Override with CGB_MATHLIB_COMMIT.
_PINS_FILE = REPO_ROOT / ".lean-pins"


def _pin_default(name: str, fallback: str) -> str:
    """Read one pin from .lean-pins (the single pin home; CI cache keys hash
    that file).  Env vars still override; the inline fallback only guards a
    missing/corrupt pins file."""
    try:
        for line in _PINS_FILE.read_text().splitlines():
            k, _, v = line.partition("=")
            if k.strip() == name and v.strip():
                return v.strip()
    except OSError:
        pass
    return fallback


MATHLIB_COMMIT = os.environ.get(
    "CGB_MATHLIB_COMMIT",
    _pin_default("MATHLIB_COMMIT", "9837ca9d65d9de6fad1ef4381750ca688774e608"))

# DERIVED (⚠D1): setup reads `lean-toolchain` at MATHLIB_COMMIT and asserts it
# equals this string, refusing on mismatch.  Chosen so the toolchain is a
# release/rc with a matching `lean4checker` tag (⚠D2).  Override CGB_LEAN_TOOLCHAIN.
LEAN_TOOLCHAIN = os.environ.get(
    "CGB_LEAN_TOOLCHAIN",
    _pin_default("LEAN_TOOLCHAIN", "leanprover/lean4:v4.15.0"))

# The pinned NARROW import set (⚠D15): importing all of Mathlib costs 30--60 s
# per process; the fragment touches only a handful of Nat/Int modules.  This
# tuple is BOTH the elaboration import list AND the escape-gate import
# whitelist (F0.4) AND part of cache identity (L2).  Module names are
# domain-knowledge `[dk]` (toolchain absent here); a wrong name = an
# elaboration failure at setup/cert time, never a false green.  `Prime` and
# real-valued modules are DELIBERATELY absent -- the F5.1 non-transcribables
# depend on the fragment being unable to express them.
MATHLIB_IMPORTS = (
    "Mathlib.Data.Nat.Defs",
    "Mathlib.Data.Int.Defs",
    "Mathlib.Data.Nat.GCD.Basic",
    "Mathlib.Data.Int.GCD",
    # Even/Odd live here at v4.15.0 -- `Mathlib.Algebra.Parity` does NOT exist
    # at this pin (CI import probe: "object file ... does not exist"); the
    # remaining five names are probe-verified OK.
    "Mathlib.Algebra.Group.Even",
    "Mathlib.Tactic.NormNum",
)

# H_pin / R_pin -- the lexically-enforced numeric caps for whitelisted
# `set_option`s (F0.4, ⚠D12).  Legitimate proofs need capped
# maxHeartbeats/maxRecDepth; `maxHeartbeats 0` (= unlimited) is refused by the
# gate.  These are the driver-set budgets for the F2.2/F2.3 discharge ladder.
LEAN_MAXHEARTBEATS = int(os.environ.get("CGB_LEAN_MAXHEARTBEATS", "400000"))
LEAN_MAXRECDEPTH = int(os.environ.get("CGB_LEAN_MAXRECDEPTH", "4096"))

# Filesystem location of the setup-time Mathlib checkout (require-by-local-path,
# F0.5).  cert-time elaboration references this read-only; the Sandbox exposes
# it INSIDE the jail at /ro/mathlib via a read-only bind mount (see LeanBackend
# and sandbox.Sandbox(ro_mounts=...)).  Override CGB_LEAN_MATHLIB.
LEAN_MATHLIB_DIR = os.environ.get(
    "CGB_LEAN_MATHLIB", str(REPO_ROOT / ".lean" / "mathlib"))


def _elan_mangle(toolchain: str) -> str:
    """elan's on-disk directory name for a toolchain: '/'->'--', ':'->'---'
    ('leanprover/lean4:v4.15.0' -> 'leanprover--lean4---v4.15.0')."""
    return toolchain.replace("/", "--").replace(":", "---")


# The RESOLVED toolchain's bin directory (lean/lake binaries), read-only-mounted
# at /ro/toolchain inside the jail so cert-time invocations bypass the elan
# proxies entirely (elan wants a writable home; the resolved toolchain does
# not).  Override CGB_LEAN_TOOLCHAIN_DIR.
LEAN_TOOLCHAIN_DIR = os.environ.get(
    "CGB_LEAN_TOOLCHAIN_DIR",
    os.path.expanduser(f"~/.elan/toolchains/{_elan_mangle(LEAN_TOOLCHAIN)}"))

# The setup-time lean4checker build (⚠D2: built from source at the tag equal to
# the derived toolchain version), read-only-mounted at /ro/lean4checker inside
# the jail for the trusted run-2 replay.  Override CGB_LEAN4CHECKER_DIR.
LEAN4CHECKER_DIR = os.environ.get(
    "CGB_LEAN4CHECKER_DIR",
    str(REPO_ROOT / ".lean" / "lean4checker"))


def lean_available() -> bool:
    """True iff a real Lean toolchain is reachable.

    Presence of `lake`/`lean` on PATH, or a truthy `CGB_LEAN` override.  This
    container has neither, so it returns False and every Lean method degrades
    to an honest `unavailable` result (never a crash)."""
    import shutil
    override = os.environ.get("CGB_LEAN")
    if override is not None and override.strip().lower() not in (
            "", "0", "false", "no", "off"):
        return True
    return bool(shutil.which("lake") or shutil.which("lean"))


def lean_toolchain_hash() -> str:
    """sha256 over the joint Lean pins + the narrow import set.

    Single-sourced (the `derivers.lowering_pipeline_hash()` pattern) so two
    builders can never populate the pin differently and silently change every
    cache key.  Deterministic: pure over module constants, no clock/env read
    beyond the already-frozen constants.  Enters every Lean cache key (L2)."""
    return sha256_json({
        "mathlib_commit": MATHLIB_COMMIT,
        "lean_toolchain": LEAN_TOOLCHAIN,
        "imports": list(MATHLIB_IMPORTS),
        "maxHeartbeats": LEAN_MAXHEARTBEATS,
        "maxRecDepth": LEAN_MAXRECDEPTH,
    })


def validate_lean_hash() -> str:
    """sha256 over the bytes of `buildloop/validate_lean.py` -- the escape-gate
    source hash that L2 folds into cache identity (a changed gate is a clean
    cache miss, never a stale false-green).  Deterministic; on a missing file
    it hashes the empty string (mirrors `lowering_pipeline_hash`'s OSError arm)."""
    p = REPO_ROOT / "buildloop" / "validate_lean.py"
    try:
        return sha256_bytes(p.read_bytes())
    except OSError:
        return sha256_bytes(b"")


# ------------------------------------------------------------------ gz io --
# The whole-library queue (WP-LI0) is >100 MB raw -- over GitHub's file
# limit -- so it lives in the repo gzipped.  Compression must not break the
# byte-identity teeth (P-LI0-CENSUS), so gzip output is DETERMINISTIC: mtime
# pinned to 0, no embedded filename.  Readers sniff the .gz suffix, so plain
# .jsonl fixtures keep working unchanged.

def encode_text_auto(path_like, text: str) -> bytes:
    """utf-8 bytes for `text`; deterministically gzipped when `path_like`
    ends in .gz (mtime=0, filename='' -- byte-identical across runs)."""
    import gzip
    import io as _io
    data = text.encode("utf-8")
    if str(path_like).endswith(".gz"):
        buf = _io.BytesIO()
        with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0) as gz:
            gz.write(data)
        data = buf.getvalue()
    return data


def read_text_auto(path) -> str:
    """Read text, transparently gunzipping when the path ends in .gz."""
    import gzip
    p = str(path)
    if p.endswith(".gz"):
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            return fh.read()
    with open(p, encoding="utf-8") as fh:
        return fh.read()
