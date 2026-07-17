#!/usr/bin/env python3
"""WP-LI0 (PLAN_LEAN_IMPORT.md §4) -- the queue enumerator RUNNER.

Drives tools/EnumerateMathlib.lean against the pinned Mathlib checkout and
normalizes its raw JSONL into the declaration queue:

    specs/mathsources/mathlib/queue.jsonl

    one row per declaration:
    {"decl_name", "module", "kind", "statement_pp", "statement_hash",
     "status": "pending"}

Layout facts (from setup.sh --with-lean, single-sourced via common.py):
  * Mathlib checkout:  common.LEAN_MATHLIB_DIR   (default <repo>/.lean/mathlib)
  * toolchain manager: elan, binaries in ~/.elan/bin (setup.sh prepends it to
    PATH for its own run only, so this runner re-derives it);
  * the checkout is `lake build`-t at setup time, so `lake env lean --run`
    here resolves everything from prebuilt oleans -- no network, no rebuild.

Division of labour (plan WP-LI0):
  * the Lean side emits TEXT ONLY (decl_name/module/kind/statement_pp), in a
    deterministic order of its own;
  * THIS side is canonical: it re-sorts by (module, decl_name), attaches
    "status": "pending" and the Python-side statement_hash, and writes
    byte-stable output -- common.canonical_json per row (sorted keys, fixed
    separators, ensure_ascii) + LF, the exact serialization
    buildloop/import_driver.write_queue uses, so a driver rewrite of an
    untouched queue is byte-identical.

statement_hash (the R1 anchor half): common.sha256_json over
{"mathlib_commit": common.MATHLIB_COMMIT, "statement_pp": <text>} -- the
repo's single-sourced canonical hashing; the pin is folded in because plan
§2.5 R1 defines identity as (decl_name, statement_hash AT THE PIN).

Refusals (clean, never a stack trace; exit code 2):
  * common.lean_available() False        -> the toolchain is absent;
  * the Mathlib checkout dir is missing  -> setup.sh --with-lean not run;
  * the checkout has no .lake/build      -> setup still fetching/building.

Flags: --limit N and --modules A,B for smoke runs (both forwarded to the
Lean side; --modules also narrows the import set so a smoke run never pays
the whole-library import), --out for a non-default queue path.

House rules: deterministic everything, zero LLM calls, no network (every
network-touching lake operation happened at setup time).
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import common  # noqa: E402

LEAN_TOOL = REPO_ROOT / "tools" / "EnumerateMathlib.lean"
DEFAULT_QUEUE = (REPO_ROOT / "specs" / "mathsources" / "mathlib"
                 / "queue.jsonl.gz")

# The four keys the Lean side must emit, all strings.  Anything else in the
# raw stream is a corrupted tool run and refuses (deterministic tools do not
# get best-effort parsing).
_RAW_KEYS = ("decl_name", "module", "kind", "statement_pp")

_MODULE_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*$")


def statement_hash(statement_pp: str) -> str:
    """The Python-side statement hash (single-sourced canonical hashing,
    common.sha256_json).  Folds in the Mathlib pin: R1 identity is
    (decl_name, statement_hash AT THE PIN)."""
    return common.sha256_json({
        "mathlib_commit": common.MATHLIB_COMMIT,
        "statement_pp": statement_pp,
    })


def _refuse(msg: str) -> int:
    sys.stderr.write("REFUSED: " + msg + "\n")
    return 2


def _find_lake():
    """lake per the setup.sh layout: PATH first, then ~/.elan/bin (setup
    prepends that dir only for its own shell)."""
    lake = shutil.which("lake")
    if lake:
        return lake
    cand = pathlib.Path.home() / ".elan" / "bin" / "lake"
    if cand.is_file():
        return str(cand)
    return None


def _lean_env():
    """Subprocess env with ~/.elan/bin on PATH (harmless if already there)."""
    env = os.environ.copy()
    elan_bin = str(pathlib.Path.home() / ".elan" / "bin")
    env["PATH"] = elan_bin + os.pathsep + env.get("PATH", "")
    return env


def normalize_raw_rows(raw_lines):
    """Parse + validate the Lean side's JSONL, attach status/statement_hash,
    and sort canonically.  Pure over its input; raises ValueError on any
    malformation (a deterministic tool that emitted garbage is an error,
    never something to paper over)."""
    rows = []
    seen = set()
    for i, line in enumerate(raw_lines, 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"raw line {i} is not JSON: {e}")
        if (not isinstance(obj, dict) or sorted(obj) != sorted(_RAW_KEYS)
                or not all(isinstance(obj[k], str) for k in _RAW_KEYS)):
            raise ValueError(
                f"raw line {i} does not match the WP-LI0 raw schema "
                f"{_RAW_KEYS}: {line[:120]}")
        if obj["decl_name"] in seen:
            raise ValueError(
                f"raw line {i}: duplicate decl_name {obj['decl_name']!r}")
        seen.add(obj["decl_name"])
        rows.append({
            "decl_name": obj["decl_name"],
            "module": obj["module"],
            "kind": obj["kind"],
            "statement_pp": obj["statement_pp"],
            "statement_hash": statement_hash(obj["statement_pp"]),
            "status": "pending",
        })
    rows.sort(key=lambda r: (r["module"], r["decl_name"]))
    return rows


def write_queue(rows, out_path: pathlib.Path) -> None:
    """Byte-stable queue serialization: common.canonical_json (sorted keys,
    fixed separators, ensure_ascii) + LF per row -- identical to
    buildloop/import_driver.write_queue's serialization.  Deterministically
    gzipped when the path ends in .gz (the whole-library queue exceeds
    GitHub's 100 MB file limit raw)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    text = "".join(common.canonical_json(r) + "\n" for r in rows)
    with open(tmp, "wb") as fh:
        fh.write(common.encode_text_auto(out_path, text))
    os.replace(tmp, out_path)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="WP-LI0: enumerate Mathlib declarations at the pin into "
                    "the declaration queue (specs/mathsources/mathlib/"
                    "queue.jsonl).")
    ap.add_argument("--limit", type=int, default=0,
                    help="keep only the first N rows after sorting (smoke)")
    ap.add_argument("--modules", default=None,
                    help="comma-separated module list for smoke runs "
                         "(imports ONLY these; default: all of Mathlib)")
    ap.add_argument("--out", default=str(DEFAULT_QUEUE),
                    help="queue output path (default: %(default)s)")
    ap.add_argument("--raw-out", default=None,
                    help="keep the Lean side's raw JSONL at this path "
                         "(default: a temp file, discarded)")
    args = ap.parse_args(argv)

    # --- clean refusals (plan house rule: honest unavailable, never a crash)
    if not common.lean_available():
        return _refuse(
            "lean toolchain absent (common.lean_available() is False). "
            "Run ./setup.sh --with-lean first; enumeration is Lean-lane work.")
    lake = _find_lake()
    if lake is None:
        return _refuse(
            "lean_available() is True but no `lake` binary was found on PATH "
            "or in ~/.elan/bin -- cannot invoke the enumeration meta-program.")
    mathlib_dir = pathlib.Path(common.LEAN_MATHLIB_DIR)
    if not ((mathlib_dir / "lakefile.lean").exists()
            or (mathlib_dir / "lakefile.toml").exists()):
        return _refuse(
            f"pinned Mathlib checkout not found at {mathlib_dir} "
            "(setup.sh --with-lean clones it there; override with "
            "CGB_LEAN_MATHLIB).")
    if not (mathlib_dir / ".lake" / "build").exists():
        return _refuse(
            f"Mathlib checkout at {mathlib_dir} has no .lake/build -- "
            "setup.sh --with-lean has not finished building; retry when it "
            "completes.")

    modules = None
    if args.modules:
        modules = [m for m in args.modules.split(",") if m]
        for m in modules:
            if not _MODULE_NAME_RE.match(m):
                return _refuse(f"--modules entry {m!r} is not a Lean module "
                               "name")

    if args.raw_out:
        raw_path = pathlib.Path(args.raw_out)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_ctx = None
    else:
        raw_ctx = tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", prefix="enumerate-mathlib-",
            delete=False)
        raw_path = pathlib.Path(raw_ctx.name)
        raw_ctx.close()

    # lean's `--run` does NOT forward dash-prefixed argv to the program (lean
    # parses them itself and dies on unknowns -- observed live: "unrecognized
    # option '--out'"), so parameters travel via ENUMERATE_* env vars instead.
    cmd = [lake, "env", "lean", "--run", str(LEAN_TOOL)]
    env = _lean_env()
    env["ENUMERATE_OUT"] = str(raw_path)
    if args.limit > 0:
        env["ENUMERATE_LIMIT"] = str(args.limit)
    if modules:
        env["ENUMERATE_MODULES"] = ",".join(modules)

    sys.stderr.write("[enumerate_mathlib] running: " + " ".join(cmd)
                     + f"\n[enumerate_mathlib] ENUMERATE_OUT={raw_path}"
                     + f"\n[enumerate_mathlib] cwd: {mathlib_dir}\n")
    # No timeout: the whole-library run is a one-time USER-GATED elaboration
    # job (plan §4); wall-clock never enters any decision.
    proc = subprocess.run(cmd, cwd=str(mathlib_dir), env=env,
                          stdout=sys.stderr, stderr=sys.stderr)
    if proc.returncode != 0:
        return _refuse(f"EnumerateMathlib.lean exited {proc.returncode} "
                       "(see stderr above)")

    with open(raw_path, encoding="utf-8") as fh:
        rows = normalize_raw_rows(fh)
    if args.limit > 0:
        rows = rows[:args.limit]

    out_path = pathlib.Path(args.out)
    write_queue(rows, out_path)
    if not args.raw_out:
        raw_path.unlink(missing_ok=True)
    print(f"[enumerate_mathlib] wrote {len(rows)} row(s) to {out_path} "
          f"(pin {common.MATHLIB_COMMIT[:12]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
