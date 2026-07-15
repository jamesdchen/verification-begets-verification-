#!/usr/bin/env python3
"""S2 lookahead steering -- the additive `lookahead` pick_group policy end to end.

`buildloop.loop.pick_group(groups, "lookahead", backlog, registry)` minimizes
`planner.lookahead.rollout_value` over the candidate coverage groups: a
depth-LOOKAHEAD_DEPTH rollout of hypothetical admissions, priced in the ONE live
currency (`dl._ledger_total`) through the ONE coverage rule
(`planner.plan_for_features`) -- never a re-implemented mirror.  Where `closure`
scores a group by its immediate single-generator coverage gain (a one-step
greedy), `lookahead` sees two admissions out and can pick a group that scores
worse greedily yet unlocks a strictly cheaper multi-spec world.

REQUIRES_LLM = False -- pure, deterministic ledger accounting; no LLM, no codec
emission, no ksc, no solver.  No real generator is ever admitted.

Part A (planted, ksc-free): a hand-built backlog + candidate groups where
  `pick_group(..., "closure", ...)` picks the greedily-dominant group X while
  `pick_group(..., "lookahead", ...)` picks the enabling group Y, and Y's
  rollout_value is STRICTLY lower than X's.

Part B (best-effort, real backlog): price a bounded, deterministic slice of the
  real ksy backlog's coverage groups with rollout_value, print the ranking, and
  assert only relational teeth (finite + deterministic).  Wrapped in try/except.
"""
from __future__ import annotations

import csv
import sys
import tempfile

import common
from buildloop import loop
from planner import lookahead
from library import Registry

REQUIRES_LLM = False

_FAILURES = []


def _check(cond, label):
    print(("  PASS " if cond else "  FAIL ") + label)
    if not cond:
        _FAILURES.append(label)
    return cond


def _spec(path, atoms, size=64):
    return {"path": path, "language": "ksy",
            "atoms": frozenset(atoms), "size_bytes": size}


def _planted_world():
    """5 Z-specs {z}; 3 P-specs {h_i,t} sharing tail t.
       X.union={z} covers 5 now (greedy max); Y.union={h1,h2,h3,t} covers 3.
       Depth-2: Y then one cheap admission finishes ALL 8; X strands the P-specs
       across distinct coverage groups."""
    backlog = [
        _spec("planted://P/0", {"h1", "t"}),
        _spec("planted://P/1", {"h2", "t"}),
        _spec("planted://P/2", {"h3", "t"}),
        _spec("planted://Z/0", {"z"}),
        _spec("planted://Z/1", {"z"}),
        _spec("planted://Z/2", {"z"}),
        _spec("planted://Z/3", {"z"}),
        _spec("planted://Z/4", {"z"}),
    ]
    X = {"language": "ksy", "missing": ["z"],
         "specs": [b for b in backlog if "z" in b["atoms"]],
         "atoms_union": {"z"}}
    Y = {"language": "ksy", "missing": ["h1", "h2", "h3", "t"],
         "specs": [b for b in backlog if "t" in b["atoms"]],
         "atoms_union": {"h1", "h2", "h3", "t"}}
    return backlog, X, Y


def part_a():
    print("PART A -- planted greedy-vs-lookahead disagreement (ksc-free)")
    backlog, X, Y = _planted_world()
    groups = [X, Y]

    # An EMPTY registry: no live generators, nothing covered yet.  pick_group's
    # closure reads covered_now via plan() (CoverageMiss for these synthetic
    # paths -> nothing covered) and lookahead reads registry.live_generators()
    # (empty), matching the [] generator list priced below.  No real admission.
    reg = Registry(db_path=tempfile.mkdtemp() + "/lookahead_demo.sqlite")

    picked_closure = loop.pick_group(groups, "closure", backlog, reg)
    picked_lookahead = loop.pick_group(groups, "lookahead", backlog, reg)

    def _name(g):
        return "X" if g is X else "Y" if g is Y else "?"

    print("  closure   picks group %s (missing=%s)"
          % (_name(picked_closure), picked_closure["missing"]))
    print("  lookahead picks group %s (missing=%s)"
          % (_name(picked_lookahead), picked_lookahead["missing"]))

    vx = lookahead.rollout_value([], backlog, X, depth=loop.LOOKAHEAD_DEPTH)
    vy = lookahead.rollout_value([], backlog, Y, depth=loop.LOOKAHEAD_DEPTH)
    print("  rollout_value(X)=%.6f   rollout_value(Y)=%.6f" % (vx, vy))

    _check(picked_closure is X, "closure picks the greedily-dominant group X")
    _check(picked_lookahead is Y, "lookahead picks the enabling group Y")
    _check(vy < vx, "rollout_value(Y) STRICTLY below rollout_value(X)")
    _check(picked_closure is not picked_lookahead,
           "the two policies DISAGREE on this planted world")


def _real_groups(reg, backlog, cap):
    """The real ksy backlog's coverage groups over an empty registry (grouped by
    missing signature, exactly as the loop forms them), sorted deterministically
    and capped so the demo stays fast."""
    misses = loop.coverage_misses(reg, backlog)
    groups = [g for g in loop.group_misses(misses) if g["language"] == "ksy"]
    groups.sort(key=lambda g: "".join(g["missing"]))
    return groups[:cap]


def part_b():
    print("PART B -- best-effort ranking of the real ksy backlog (bounded)")
    try:
        backlog = loop.backlog_index(common.REPO_ROOT / "specs" / "backlog")
        ksy = [b for b in backlog if b["language"] == "ksy"]
        if not ksy:
            print("  SKIP: no ksy backlog specs available")
            return
        reg = Registry(db_path=tempfile.mkdtemp() + "/lookahead_real.sqlite")
        groups = _real_groups(reg, backlog, cap=8)
        if not groups:
            print("  SKIP: no ksy coverage groups")
            return

        ranking = []
        for g in groups:
            v = lookahead.rollout_value([], backlog, g,
                                        depth=loop.LOOKAHEAD_DEPTH)
            ranking.append((v, tuple(g["missing"]), len(g["specs"])))
        ranking.sort(key=lambda r: (r[0], "".join(r[1])))

        print("  rollout_value ranking (lower = better first admission):")
        for v, missing, nspecs in ranking:
            print("    %10.3f  specs=%d  missing=%s"
                  % (v, nspecs, ",".join(missing)))

        # relational teeth only -- NO absolute magic constants.
        _check(all(v == float(v) and v < float("inf") for v, _, _ in ranking),
               "every real ksy group prices to a FINITE ledger cost")
        # determinism: re-price the first group, must match byte-for-byte.
        g0 = groups[0]
        r1 = lookahead.rollout_value([], backlog, g0, loop.LOOKAHEAD_DEPTH)
        r2 = lookahead.rollout_value([], backlog, g0, loop.LOOKAHEAD_DEPTH)
        _check(common.canonical_json(r1) == common.canonical_json(r2),
               "real-backlog rollout_value is deterministic (two calls equal)")

        # optional CSV of the ranking.
        try:
            out = common.REPO_ROOT / "results" / "lookahead_ranking.csv"
            with open(out, "w", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["rank", "rollout_value", "num_specs", "missing"])
                for i, (v, missing, nspecs) in enumerate(ranking):
                    w.writerow([i, "%.6f" % v, nspecs, ",".join(missing)])
            print("  wrote ranking CSV -> %s" % out)
        except OSError as e:
            print("  (CSV write skipped: %s)" % e)
    except Exception as e:  # best-effort: never fail the demo on part B setup
        print("  SKIP: real-backlog pricing unavailable (%r)" % e)


def main():
    print("=" * 68)
    print("demo_lookahead -- S2 lookahead steering (REQUIRES_LLM=%s)"
          % REQUIRES_LLM)
    print("=" * 68)
    part_a()
    part_b()
    print("-" * 68)
    if _FAILURES:
        print("TEETH FAILED: %d" % len(_FAILURES))
        for f in _FAILURES:
            print("  - " + f)
        sys.exit(1)
    print("ALL TEETH PASS")


if __name__ == "__main__":
    main()
