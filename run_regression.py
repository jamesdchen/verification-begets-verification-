#!/usr/bin/env python3
"""Regression harness for the certified-generator-bootstrap repo.

Every item runs as its OWN subprocess with a FRESH temp CGB_DB / CGB_ARTIFACTS
exported into the child environment, so no registry / artifact state is ever
shared between items (each item starts from an empty database).

Modes:
  --fast (default, LLM-free, target <90s):
      * python3 -m pytest tests/ -q
      * python3 tests/test_channel_parity.py  (if present)
      * python3 tests/test_prompt.py          (if present)
      * the five hand-written-spec demos: demo_constraint, demo_protocol,
        demo_tool, demo_reading, demo_service -- each must exit 0.
  --full:
      * everything in --fast, but with a whole-repo ("full") pytest run, PLUS
      * every demo discovered on disk, including the LLM-driven ones and
        demo_differential / demo_lift, PLUS
      * a best-effort bench/bench_latency.py.
      Wall-clock per item is appended to results/regression.txt.

A demo's REQUIRES_LLM flag is discovered by importing the module and reading
the attribute (defaulting to True if absent).  A per-item PASS/FAIL table with
durations is printed; the process exits 0 iff every selected (non best-effort)
item passed.

Sharding (`--split`, CI matrixes these): `pytest-<i>of<n>` runs the i-th of n
file-parity shards of the pytest suite; `demos-<i>of<n>` the i-th of n
round-robin shards of the scripts+demos lane.  `pytest-a` / `pytest-b` remain
as aliases for `pytest-1of2` / `pytest-2of2`.

Parallelism (`--jobs N`, SESSIONS ONLY -- CI stays serial by law, CLAUDE.md):
runs up to N items concurrently.  Safe because every item already gets its own
subprocess with a private CGB_DB / CGB_ARTIFACTS; with N > 1 each item's
output is captured and printed atomically on completion instead of streamed.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import importlib
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parent

FAST_DEMOS = ["demo_constraint", "demo_protocol", "demo_tool", "demo_reading",
              "demo_service", "demo_temporal", "demo_guarded", "demo_nested",
              "demo_tier", "demo_macros", "demo_ledger",
              "demo_translation_cert", "demo_scheduler", "demo_passes",
              "demo_translation_abnf", "demo_promote_translation",
              "demo_pass_certs", "demo_formalize", "demo_formalize_governor",
              # F-INT (WP-G/G1): WP-E's LLM-free speculative-math demo.
              "demo_speculate_math"]

def _milestone_registered(target):
    """True iff milestones.py registers `target` (defensive: a `milestones.py
    <unknown>` invocation exits nonzero, which would FAIL the gate)."""
    try:
        import milestones
        return target in getattr(milestones, "MILESTONES", {})
    except Exception:
        return False
GUARDED_SCRIPTS = ["tests/test_channel_parity.py", "tests/test_prompt.py",
                   "tests/test_byte_identity.py", "tests/test_monitor_gen.py",
                   "tests/test_cage_teeth.py"]

PYTEST_TIMEOUT = 600
SCRIPT_TIMEOUT = 300
DEMO_TIMEOUT = 300
LLM_TIMEOUT = 900
BENCH_TIMEOUT = 900


def _fresh_env():
    """A copy of the environment with this child's own CGB_DB / CGB_ARTIFACTS.

    The registry tooling reads CGB_DB / CGB_ARTIFACTS at import time; giving
    each subprocess a private mkdtemp for both guarantees isolation.  The
    outsourced-tool locations (PATH additions, Kaitai classpath) are set too so
    codec / service items find java, maven and the ksc jars.
    """
    env = dict(os.environ)
    env["CGB_DB"] = os.path.join(tempfile.mkdtemp(), "t.sqlite")
    env["CGB_ARTIFACTS"] = os.path.join(tempfile.mkdtemp(), "a")
    env["CGB_KSC_CLASSPATH"] = "/opt/ksc/lib/*"
    env["PATH"] = ("/opt/maven/bin:/root/.cargo/bin" + os.pathsep
                   + env.get("PATH", ""))
    return env


def _requires_llm(module_name):
    """Import the demo module and read REQUIRES_LLM (default True if absent)."""
    try:
        mod = importlib.import_module("demos." + module_name)
    except Exception:
        return True
    return bool(getattr(mod, "REQUIRES_LLM", True))


def _requires_lean(module_name):
    """Import the demo module and read REQUIRES_LEAN (default False if absent).

    F0 (⚠X7/A7): Lean demos are `REQUIRES_LEAN = True` and NEVER enter
    FAST_DEMOS, so `--fast` stays Lean-free.  Under `--full` a Lean-requiring
    demo is skipped-with-note (not failed) when the toolchain is absent -- the
    honest-tier discipline that keeps the regression green on a container with
    no Lean.  Default False so ordinary demos are unaffected."""
    try:
        mod = importlib.import_module("demos." + module_name)
    except Exception:
        return False
    return bool(getattr(mod, "REQUIRES_LEAN", False))


def _discover_demos():
    """All demos/demo_*.py modules on disk, by module name, in stable order."""
    return sorted(p.stem for p in (REPO_ROOT / "demos").glob("demo_*.py"))


def _run(argv, timeout, capture=False):
    """Run one item as a subprocess with a fresh env.

    Streams the child's output by default; with `capture` (the --jobs > 1
    path) the combined stdout+stderr is returned instead, so concurrent
    items' output never interleaves."""
    env = _fresh_env()
    t0 = time.time()
    out = b""
    try:
        if capture:
            proc = subprocess.run(argv, cwd=str(REPO_ROOT), env=env,
                                  timeout=timeout, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
            rc, out = proc.returncode, proc.stdout or b""
        else:
            rc = subprocess.run(argv, cwd=str(REPO_ROOT), env=env,
                                timeout=timeout).returncode
    except subprocess.TimeoutExpired as exc:
        rc = 124
        out = getattr(exc, "stdout", None) or b""
    except Exception as exc:  # pragma: no cover - defensive
        print(f"  (harness error running {argv}: {exc})")
        rc = 1
    return rc, time.time() - t0, out


_LEGACY_SPLITS = {"pytest-a": ("pytest", 0, 2), "pytest-b": ("pytest", 1, 2)}


def _parse_split(split):
    """'all' or (kind, index0, nshards).

    Grammar: all | pytest | demos | pytest-<i>of<n> | demos-<i>of<n>
    (1-based i) | pytest-a | pytest-b (legacy aliases for the 2-way split)."""
    if split == "all":
        return ("all", 0, 1)
    if split in _LEGACY_SPLITS:
        return _LEGACY_SPLITS[split]
    m = re.fullmatch(r"(pytest|demos)(?:-(\d+)of(\d+))?", split)
    if not m:
        raise SystemExit(
            f"unknown --split {split!r} (want all | pytest[-<i>of<n>] | "
            f"demos[-<i>of<n>] | pytest-a | pytest-b)")
    i, n = int(m.group(2) or 1), int(m.group(3) or 1)
    if not 1 <= i <= n:
        raise SystemExit(f"--split {split!r}: want 1 <= i <= n")
    return (m.group(1), i - 1, n)


def _build_items(mode, split="all"):
    """Return a list of (label, argv, best_effort, timeout) for the mode.

    `split` shards the gate for parallel CI runners (see _parse_split):
      * "pytest[-<i>of<n>]" -- the pytest suite, or one deterministic
        sorted-file-parity shard of it (together the n shards are exactly
        `pytest tests/`; conftest applies to each);
      * "demos[-<i>of<n>]"  -- the guarded scripts + demos (+ bench under
        --full), or one round-robin shard of that lane;
      * "all"    -- everything (the default; local runs).
    """
    kind, shard_i, shard_n = _parse_split(split)
    items = []

    if kind in ("all", "pytest"):
        if kind == "pytest" and shard_n > 1 and mode == "fast":
            files = sorted(str(f.relative_to(REPO_ROOT))
                           for f in (REPO_ROOT / "tests").glob("test_*.py"))
            shard = [f for i, f in enumerate(files) if i % shard_n == shard_i]
            items.append((f"pytest {split}",
                          [sys.executable, "-m", "pytest", *shard, "-q"],
                          False, PYTEST_TIMEOUT))
        elif mode == "fast":
            items.append(("pytest tests/",
                          [sys.executable, "-m", "pytest", "tests/", "-q"],
                          False, PYTEST_TIMEOUT))
        elif kind == "all" or shard_i == 0:
            # --full has a single whole-repo pytest item; under a sharded
            # pytest split only shard 1 carries it (never duplicated).
            items.append(("pytest (full)",
                          [sys.executable, "-m", "pytest", "-q"],
                          False, PYTEST_TIMEOUT))

    if kind == "pytest":
        return items

    # the scripts+demos lane, collected first so a demos-<i>of<n> split can
    # take a deterministic round-robin shard of the whole lane at the end.
    lane = []

    for script in GUARDED_SCRIPTS:
        if (REPO_ROOT / script).exists():
            lane.append((script, [sys.executable, script],
                         False, SCRIPT_TIMEOUT))

    if mode == "fast":
        demos = list(FAST_DEMOS)
    else:
        demos = _discover_demos()
    for name in demos:
        # F0 (⚠X6): under --full, skip-with-note (NOT fail) any Lean-requiring
        # demo when the toolchain is absent.  Omitting it from `items` means it
        # never runs and so never reports FAIL; the printed SKIP note keeps the
        # deferral auditable.  (--fast never reaches Lean demos: they are never
        # in FAST_DEMOS.)
        if mode == "full" and _requires_lean(name):
            import common
            if not common.lean_available():
                print(f"  SKIP {name}: REQUIRES_LEAN and lean toolchain absent "
                      f"(common.lean_available() is False) -- deferred, not a failure")
                continue
        llm = _requires_llm(name)
        timeout = LLM_TIMEOUT if llm else DEMO_TIMEOUT
        label = name + (" [LLM]" if llm else "")
        lane.append((label, [sys.executable, f"demos/{name}.py"], False, timeout))

    # F-INT (WP-G/G1): explicit fast-tier milestone item.  milestones are never
    # glob-auto-discovered by the harness (⚠FI-9/FI-10), so m9_planted -- WP-B's
    # LLM-free, Lean-free planted math reach-vs-cost curve -- is listed by name.
    if mode == "fast":
        if _milestone_registered("m9_planted"):
            lane.append(("milestones.py m9_planted",
                          [sys.executable, "milestones.py", "m9_planted"],
                          False, DEMO_TIMEOUT))
        else:
            print("  SKIP milestones.py m9_planted: milestone not registered")

    if mode == "full" and (REPO_ROOT / "bench/bench_latency.py").exists():
        lane.append(("bench_latency [best-effort]",
                      [sys.executable, "bench/bench_latency.py"], True, BENCH_TIMEOUT))

    # F-INT (WP-G/G1): the formalization bench joins --full as a best-effort
    # item, mirroring bench_latency (LLM-requiring -> honest skip when no
    # endpoint; a failure never gates).  WP-D rebuilds bench/bench_formalize.py; the
    # existence guard keeps --full honest in a pre-merge tree.
    if mode == "full" and (REPO_ROOT / "bench/bench_formalize.py").exists():
        lane.append(("bench_formalize [best-effort]",
                      [sys.executable, "bench/bench_formalize.py"], True, BENCH_TIMEOUT))

    if kind == "demos" and shard_n > 1:
        lane = lane[shard_i::shard_n]
    items.extend(lane)
    return items


def _append_results(records, total_dur):
    path = REPO_ROOT / "results" / "regression.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(path, "a") as fh:
        fh.write(f"# regression --full {stamp}\n")
        for r in records:
            fh.write(f"  {r['label']:<34}{r['status']:<6}{r['dur']:8.2f}s\n")
        fh.write(f"  {'TOTAL':<34}{'':<6}{total_dur:8.2f}s\n")
    print(f"\nappended wall-clock per item to {path}")


def main():
    ap = argparse.ArgumentParser(
        description="Subprocess-isolated regression harness.")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--fast", action="store_const", dest="mode", const="fast",
                   help="LLM-free items only (default; target <90s)")
    g.add_argument("--full", action="store_const", dest="mode", const="full",
                   help="all items incl. LLM demos + bench")
    ap.add_argument("--split", default="all", metavar="SPLIT",
                    help="run one shard of the gate (CI matrixes these): "
                         "all | pytest[-<i>of<n>] | demos[-<i>of<n>] | "
                         "pytest-a | pytest-b (legacy 2-way aliases)")
    ap.add_argument("--jobs", type=int, default=1, metavar="N",
                    help="run up to N items concurrently (SESSIONS ONLY; "
                         "CI stays serial).  Items are already "
                         "subprocess-isolated; output is captured per item")
    ap.set_defaults(mode="fast")
    args = ap.parse_args()
    mode = args.mode
    jobs = max(1, args.jobs)

    os.chdir(REPO_ROOT)
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    items = _build_items(mode, args.split)
    records = []
    if jobs == 1:
        for label, argv, best_effort, timeout in items:
            print(f"\n===== [{mode}] {label} =====", flush=True)
            rc, dur, _ = _run(argv, timeout)
            status = "PASS" if rc == 0 else "FAIL"
            records.append({"label": label, "status": status, "dur": dur,
                            "rc": rc, "best_effort": best_effort})
            print(f"----- {label}: {status} (rc={rc}, {dur:.2f}s) -----",
                  flush=True)
    else:
        def _one(item):
            label, argv, best_effort, timeout = item
            rc, dur, out = _run(argv, timeout, capture=True)
            return item, rc, dur, out

        by_label = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as ex:
            futs = [ex.submit(_one, item) for item in items]
            for fut in concurrent.futures.as_completed(futs):
                (label, argv, best_effort, timeout), rc, dur, out = fut.result()
                status = "PASS" if rc == 0 else "FAIL"
                by_label[label] = {"label": label, "status": status,
                                   "dur": dur, "rc": rc,
                                   "best_effort": best_effort}
                # one atomic block per item: header, captured output, footer
                sys.stdout.write(
                    f"\n===== [{mode}] {label} =====\n"
                    + out.decode(errors="replace")
                    + f"----- {label}: {status} (rc={rc}, {dur:.2f}s) -----\n")
                sys.stdout.flush()
        # the summary table keeps the deterministic item order
        records = [by_label[label] for label, *_ in items]

    print("\n" + "=" * 58)
    print(f"REGRESSION SUMMARY  (mode={mode})")
    print("=" * 58)
    print(f"{'ITEM':<36}{'RESULT':<8}{'DURATION':>10}")
    print("-" * 58)
    for r in records:
        best = "  (best-effort)" if r["best_effort"] else ""
        print(f"{r['label']:<36}{r['status']:<8}{r['dur']:>8.2f}s{best}")
    print("-" * 58)

    gating = [r for r in records if not r["best_effort"]]
    failed = [r for r in gating if r["status"] == "FAIL"]
    total_dur = sum(r["dur"] for r in records)
    print(f"{len(gating) - len(failed)}/{len(gating)} gating items passed; "
          f"wall-clock {total_dur:.2f}s")
    if failed:
        print("FAILED:", ", ".join(r["label"] for r in failed))

    if mode == "full":
        _append_results(records, total_dur)

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
