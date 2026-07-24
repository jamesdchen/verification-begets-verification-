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
      |                        near-last so the one command refreshes it)
      +-> frontier            (reads the census rollup: STRICTLY after
                               census_portfolio -- a group of its own so it
                               never races a stale rollup)

Usage:
    python3 tools/regen_downstream.py            # run the whole DAG
    python3 tools/regen_downstream.py --from ppm_ref   # resume mid-DAG
    python3 tools/regen_downstream.py --list     # print the order and exit
    python3 tools/regen_downstream.py --serial   # no chain concurrency

Each step is the tool's own CLI run as a subprocess (same argv semantics as
running it by hand), stopping at the first failure with the step named --
so a red step resumes with `--from <step>` after the fix.  Steps with no
edge between them run as CONCURRENT subprocess chains (each tool replays
the checkpoint independently and writes disjoint results files, so the
only shared state is read-only); `--serial` collapses to the flattened
order when a run needs to be easy to read.  After a full run, the
committed-artifact teeth (`python3 -m pytest tests/`) are the
verification; this driver regenerates, it does not assert.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cmd(tool: str) -> list:
    return [sys.executable, f"tools/{tool}.py"]


# The DAG as sequential GROUPS of parallel CHAINS: every chain in a group
# may run concurrently; a group starts only when the previous group is
# done; steps inside a chain are strictly ordered (the tools' own STOP
# guards: entropy_refs -> ppm_ref -> c2_report share one stream identity,
# and the figures read their upstream json).
GROUPS = [
    [["subtree_mine"]],
    [["admit_proposals"]],           # mutates the registry: a barrier
    [
        ["tower_census"],
        # service_refs reads ppm_ref's math-domain numbers: same chain
        # (surfaced as a stale-read race when it sat in its own chain).
        ["entropy_refs", "ppm_ref", "c2_report", "entropy_stack_fig",
         "service_refs"],
        ["measure_cluster_key"],
        ["holdout_transfer"],
        ["dl_trajectories_fig"],
    ],
    [["campaign_dashboard"]],        # reads across the group above
    [["census_portfolio"]],
    [["frontier"]],                  # reads the census rollup: its own group
    # the hammer pair rides the DAG so cycle-moved inputs (bench state,
    # lane reports) regenerate the committed queue/batch mechanically --
    # their byte/pin teeth red the NEXT merge otherwise (PR #39 lesson).
    [["proof_queue", "hammer_batch"]],
]

# Flattened order (documentation + --from addressing).
STEPS = [(name, _cmd(name)) for group in GROUPS for chain in group
         for name in chain]


def _run_chain(chain: list, skip: set) -> tuple:
    """Run one chain's steps in order; returns (failed_step | None)."""
    for name in chain:
        if name in skip:
            print(f"[skip] {name}")
            continue
        print(f"[run ] {name}")
        r = subprocess.run(_cmd(name), cwd=_ROOT)
        if r.returncode != 0:
            return name, r.returncode
    return None, 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--from", dest="start", default=None, metavar="STEP",
                    help="resume the DAG at this step (see --list)")
    ap.add_argument("--list", action="store_true",
                    help="print the dependency order and exit")
    ap.add_argument("--serial", action="store_true",
                    help="run chains one at a time (no concurrency)")
    args = ap.parse_args(argv)
    names = [n for n, _ in STEPS]
    if args.list:
        for n in names:
            print(n)
        return 0
    if args.start is not None and args.start not in names:
        print(f"unknown step {args.start!r}; steps are: {', '.join(names)}")
        return 2
    # resume semantics: skip every step BEFORE --from in flattened order.
    skip = set(names[:names.index(args.start)]) if args.start else set()
    for group in GROUPS:
        live = [c for c in group if any(n not in skip for n in c)]
        for chain in group:
            if chain not in live:
                for n in chain:
                    print(f"[skip] {n}")
        if not live:
            continue
        if args.serial or len(live) == 1:
            results = [_run_chain(c, skip) for c in live]
        else:
            with ThreadPoolExecutor(max_workers=len(live)) as ex:
                results = list(ex.map(lambda c: _run_chain(c, skip), live))
        failures = [(n, rc) for n, rc in results if n is not None]
        if failures:
            for n, rc in failures:
                print(f"[FAIL] {n} (exit {rc}) -- fix, then resume with: "
                      f"python3 tools/regen_downstream.py --from {n}")
            return failures[0][1]
    print("[done] all downstream artifacts regenerated; verify with "
          "`python3 -m pytest tests/`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
