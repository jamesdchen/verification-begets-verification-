#!/usr/bin/env python3
"""One-command regeneration of every committed artifact downstream of the
bench checkpoint, in dependency order (the C2-cycle latency lesson).

Growing the corpus (or changing the admitted-operator registry, the prompt
grammar, or the miner) invalidates a WEB of committed results whose
regeneration order matters -- the ordering knowledge used to live only in
the tools' own STOP guards, discovered at runtime, and the C2 cycle paid
for it twice (a second full pass after the admission runner moved the
registry).  This driver makes the DAG executable:

    (bench checkpoint: results/formalize_bench_state.jsonl -- UPSTREAM,
     not regenerated here: it needs an author; see bench_formalize.run_bench)
      |
      +-> subtree_mine        (stages proposals from the certified corpus)
      +-> admit_proposals     (re-prices staged proposals; MUTATES the
      |                        admitted registry -- everything below reads it)
      +-> tower_census        (census-of-record replay)
      +-> entropy_refs        (must precede ppm_ref: shared-stream guard)
      +-> ppm_ref             (must precede c2_report: KT anchor)
      +-> c2_report
      +-> measure_cluster_key
      +-> holdout_transfer    (registered-slice replay; reproduces, never
      |                        re-registers)
      +-> service_refs
      +-> dl_trajectories_fig
      +-> entropy_stack_fig
      +-> campaign_dashboard
      +-> census_portfolio    (independent of the checkpoint; cheap, kept
                               last so the one command refreshes everything)

Usage:
    python3 tools/regen_downstream.py            # run the whole DAG
    python3 tools/regen_downstream.py --from ppm_ref   # resume mid-DAG
    python3 tools/regen_downstream.py --list     # print the order and exit

Each step is the tool's own CLI run as a subprocess (same argv semantics as
running it by hand), stopping at the first failure with the step named --
so a red step resumes with `--from <step>` after the fix.  After a full
run, the committed-artifact teeth (`python3 -m pytest tests/`) are the
verification; this driver regenerates, it does not assert.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (step name, argv) in dependency order.  A step's name is its tools/ module.
STEPS = [
    ("subtree_mine", [sys.executable, "tools/subtree_mine.py"]),
    ("admit_proposals", [sys.executable, "tools/admit_proposals.py"]),
    ("tower_census", [sys.executable, "tools/tower_census.py"]),
    ("entropy_refs", [sys.executable, "tools/entropy_refs.py"]),
    ("ppm_ref", [sys.executable, "tools/ppm_ref.py"]),
    ("c2_report", [sys.executable, "tools/c2_report.py"]),
    ("measure_cluster_key", [sys.executable, "tools/measure_cluster_key.py"]),
    ("holdout_transfer", [sys.executable, "tools/holdout_transfer.py"]),
    ("service_refs", [sys.executable, "tools/service_refs.py"]),
    ("dl_trajectories_fig", [sys.executable, "tools/dl_trajectories_fig.py"]),
    ("entropy_stack_fig", [sys.executable, "tools/entropy_stack_fig.py"]),
    ("campaign_dashboard", [sys.executable, "tools/campaign_dashboard.py"]),
    ("census_portfolio", [sys.executable, "tools/census_portfolio.py"]),
]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--from", dest="start", default=None, metavar="STEP",
                    help="resume the DAG at this step (see --list)")
    ap.add_argument("--list", action="store_true",
                    help="print the dependency order and exit")
    args = ap.parse_args(argv)
    names = [n for n, _ in STEPS]
    if args.list:
        for n in names:
            print(n)
        return 0
    if args.start is not None and args.start not in names:
        print(f"unknown step {args.start!r}; steps are: {', '.join(names)}")
        return 2
    started = args.start is None
    for name, cmd in STEPS:
        if not started:
            if name == args.start:
                started = True
            else:
                print(f"[skip] {name}")
                continue
        print(f"[run ] {name}")
        r = subprocess.run(cmd, cwd=_ROOT)
        if r.returncode != 0:
            print(f"[FAIL] {name} (exit {r.returncode}) -- fix, then resume "
                  f"with: python3 tools/regen_downstream.py --from {name}")
            return r.returncode
    print("[done] all downstream artifacts regenerated; verify with "
          "`python3 -m pytest tests/`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
