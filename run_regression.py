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
      * a best-effort bench_latency.py.
      Wall-clock per item is appended to results/regression.txt.

A demo's REQUIRES_LLM flag is discovered by importing the module and reading
the attribute (defaulting to True if absent).  A per-item PASS/FAIL table with
durations is printed; the process exits 0 iff every selected (non best-effort)
item passed.
"""
from __future__ import annotations

import argparse
import importlib
import os
import pathlib
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

# ---------------------------------------------------------------------------
# F-INT wave-0 merge scaffolding (WP-G/G1).  These items reference files that
# a sibling wave-0 package delivers; in a PRE-MERGE tree they are absent, so
# each is guarded by an existence / registration check and skipped with an
# honest "[pending merge]" note rather than FAILing the gate.  This whole
# block is TEMPORARY SCAFFOLDING: once every F-INT package lands, the guarded
# targets are always present, and the PENDING_* guards below can be removed
# (the plain FAST_DEMOS entry / milestone item / --full bench item then stand
# on their own, exactly like the other harness items).
# ---------------------------------------------------------------------------
PENDING_DEMOS = {"demo_speculate_math"}  # delivered by WP-E


def _milestone_registered(target):
    """True iff milestones.py registers `target` (WP-B lands `m9_planted`).

    Used to guard the explicit fast-tier milestone item: a `milestones.py
    <unknown>` invocation exits nonzero, which would FAIL the gate on a tree
    where WP-B has not yet merged.  Import failures are treated as absent."""
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
        mod = importlib.import_module(module_name)
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
        mod = importlib.import_module(module_name)
    except Exception:
        return False
    return bool(getattr(mod, "REQUIRES_LEAN", False))


def _discover_demos():
    """All demo_*.py modules on disk, by module name, in stable order."""
    return sorted(p.stem for p in REPO_ROOT.glob("demo_*.py"))


def _run(argv, timeout):
    """Run one item as a subprocess with a fresh env; stream its output."""
    env = _fresh_env()
    t0 = time.time()
    try:
        rc = subprocess.run(argv, cwd=str(REPO_ROOT), env=env,
                            timeout=timeout).returncode
    except subprocess.TimeoutExpired:
        rc = 124
    except Exception as exc:  # pragma: no cover - defensive
        print(f"  (harness error running {argv}: {exc})")
        rc = 1
    return rc, time.time() - t0


def _build_items(mode, split="all"):
    """Return a list of (label, argv, best_effort, timeout) for the mode.

    `split` shards the gate for parallel CI runners (the two halves are
    naturally balanced: the pytest suite ~= the scripts+demos total):
      * "pytest" -- only the pytest item;
      * "demos"  -- the guarded scripts + demos (+ bench under --full);
      * "all"    -- everything (the default; local runs).
    """
    items = []

    if split in ("all", "pytest") and mode == "fast":
        items.append(("pytest tests/",
                      [sys.executable, "-m", "pytest", "tests/", "-q"],
                      False, PYTEST_TIMEOUT))
    elif split in ("all", "pytest"):
        items.append(("pytest (full)",
                      [sys.executable, "-m", "pytest", "-q"],
                      False, PYTEST_TIMEOUT))

    if split == "pytest":
        return items

    for script in GUARDED_SCRIPTS:
        if (REPO_ROOT / script).exists():
            items.append((script, [sys.executable, script],
                          False, SCRIPT_TIMEOUT))

    if mode == "fast":
        demos = [d for d in FAST_DEMOS if (REPO_ROOT / f"{d}.py").exists()]
        # F-INT scaffolding: note (don't silently drop) a pending demo whose
        # delivering package has not merged yet.  Remove with PENDING_DEMOS.
        for d in PENDING_DEMOS:
            if d in FAST_DEMOS and not (REPO_ROOT / f"{d}.py").exists():
                print(f"  SKIP {d}: demo file absent [pending merge -- WP-E]")
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
        items.append((label, [sys.executable, f"{name}.py"], False, timeout))

    # F-INT (WP-G/G1): explicit fast-tier milestone item.  milestones are never
    # glob-auto-discovered by the harness (⚠FI-9/FI-10), so m9_planted -- WP-B's
    # LLM-free, Lean-free planted math reach-vs-cost curve -- is listed by name.
    # Guarded: until WP-B merges the target is unregistered and a bare
    # `milestones.py m9_planted` would exit 1; skip-with-note instead.  (Guard
    # is temporary scaffolding -- remove once WP-B has landed.)
    if mode == "fast":
        if _milestone_registered("m9_planted"):
            items.append(("milestones.py m9_planted",
                          [sys.executable, "milestones.py", "m9_planted"],
                          False, DEMO_TIMEOUT))
        else:
            print("  SKIP milestones.py m9_planted: milestone not registered "
                  "[pending merge -- WP-B]")

    if mode == "full" and (REPO_ROOT / "bench_latency.py").exists():
        items.append(("bench_latency [best-effort]",
                      [sys.executable, "bench_latency.py"], True, BENCH_TIMEOUT))

    # F-INT (WP-G/G1): the formalization bench joins --full as a best-effort
    # item, mirroring bench_latency (LLM-requiring -> honest skip when no
    # endpoint; a failure never gates).  WP-D rebuilds bench_formalize.py; the
    # existence guard keeps --full honest in a pre-merge tree.
    if mode == "full" and (REPO_ROOT / "bench_formalize.py").exists():
        items.append(("bench_formalize [best-effort]",
                      [sys.executable, "bench_formalize.py"], True, BENCH_TIMEOUT))

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
    ap.add_argument("--split", choices=["all", "pytest", "demos"],
                    default="all",
                    help="run one shard of the gate (CI matrixes the two)")
    ap.set_defaults(mode="fast")
    args = ap.parse_args()
    mode = args.mode

    os.chdir(REPO_ROOT)
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    items = _build_items(mode, args.split)
    records = []
    for label, argv, best_effort, timeout in items:
        print(f"\n===== [{mode}] {label} =====", flush=True)
        rc, dur = _run(argv, timeout)
        status = "PASS" if rc == 0 else "FAIL"
        records.append({"label": label, "status": status, "dur": dur,
                        "rc": rc, "best_effort": best_effort})
        print(f"----- {label}: {status} (rc={rc}, {dur:.2f}s) -----",
              flush=True)

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
