"""H53 acceptance: prove the live M5 metrics path is no longer dead.

Before the WP-G fix, `metrics.run_experiment.run_config` seeded the on-disk
`backlog` list but NEVER populated the DEMAND ledger.  The miss-typed scheduler
(`buildloop.loop.score_moves`) scores its moves over `snap.demand`, so with an
empty demand table it found no moves and `run_iteration` returned `converged`
on iteration 1 for EVERY policy -- the metrics loop silently did nothing.

`metrics.run_experiment._seed_demand(reg, backlog)` now seeds one exogenous
`spec-file` demand row per backlog entry.  These tests exercise that seed
end-to-end with NO generator admission -- so they are fast, LLM-free, and need
no kaitai-struct-compiler (ksc): the coverage moves fire purely from uncovered
seeded demand against an empty generator set.
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import buildloop.dl as dl
import buildloop.loop as loop
import metrics.run_experiment as run_experiment
from library import Registry


def _fresh_registry():
    return Registry(db_path=tempfile.mkdtemp() + "/r.sqlite")


def test_seed_demand_makes_coverage_moves_pickable():
    """The H53 fix: seeding demand makes score_moves produce a positive-score
    coverage move that the scheduler would pick (i.e. it would NOT converge at
    iteration 1).  No generator is admitted, so no ksc/LLM is required."""
    # 1. Pure, ksc-free backlog read (specs/backlog ksy files via planner.load_spec).
    backlog = run_experiment.ksy_backlog()
    assert backlog, "ksy backlog must be non-empty"

    # 2-3. Fresh temp registry, then seed one spec-file demand row per backlog entry.
    reg = _fresh_registry()
    run_experiment._seed_demand(reg, backlog)

    # 4. Frozen snapshot -> rank the typed misses.
    snap = dl.snapshot(reg)
    moves, log_moves, picked = loop.score_moves(snap, reg)

    # 5. There is at least one coverage move with score > 0, and the scheduler
    #    picks a move -- proving it would not converge at iteration 1.  This is
    #    exactly the state that was unreachable before _seed_demand existed.
    coverage_positive = [m for m in moves
                         if m["kind"] == "coverage" and m["score"] > 0]
    assert coverage_positive, "seeded demand must yield a positive coverage move"
    assert picked is not None, "score_moves must pick a move (not converge)"

    # closure/frequency/lookahead all now have moves to pick from: score_moves'
    # coverage moves are policy-independent (the policy only affects pick_group
    # INSIDE dispatch, not score_moves), so asserting the coverage move exists
    # proves every pick_group policy has a non-empty group set to choose from.


def test_no_seed_demand_converges():
    """Negative control: a fresh registry with NO _seed_demand call has an empty
    demand ledger, so score_moves finds no move and picks None (converged).
    This proves the seed -- not some ambient state -- is what makes M5 live."""
    reg = _fresh_registry()
    snap = dl.snapshot(reg)
    moves, log_moves, picked = loop.score_moves(snap, reg)
    assert picked is None, "empty demand ledger must converge (picked is None)"


if __name__ == "__main__":
    backlog = run_experiment.ksy_backlog()
    reg = _fresh_registry()
    run_experiment._seed_demand(reg, backlog)
    snap = dl.snapshot(reg)
    moves, log_moves, picked = loop.score_moves(snap, reg)
    cov = [m for m in moves if m["kind"] == "coverage" and m["score"] > 0]
    print(f"backlog size:           {len(backlog)}")
    print(f"positive coverage moves: {len(cov)}")
    print(f"picked move kind:        {picked['kind'] if picked else None}")

    reg2 = _fresh_registry()
    _, _, picked2 = loop.score_moves(dl.snapshot(reg2), reg2)
    print(f"control (no seed) picked: {picked2}")
    print("OK")
