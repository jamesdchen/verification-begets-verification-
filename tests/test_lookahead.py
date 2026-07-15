"""Teeth for S2 lookahead steering (planner/lookahead.py).

FAST, pure, deterministic, LLM-free -- no ksc, no z3, no registry, no disk.  The
planted world exhibits the exact greedy-vs-lookahead disagreement the policy
exists to catch:

  * a one-step "closure" score (immediate single-generator coverage gain) picks
    group X, because X's hypothetical covers the most backlog specs RIGHT NOW;
  * a depth-2 rollout strictly prefers group Y, because resolving Y first lets a
    single cheap SECOND admission finish the whole backlog, whereas resolving X
    first strands the remaining specs across coverage groups that no single
    second admission can consolidate (their missing signatures differ).

Concretely (all made-up ksy atoms, so pricing is pure subset arithmetic):
  * Z-specs: five specs each with atoms {"z"}.
  * P-specs: three specs {"h1","t"}, {"h2","t"}, {"h3","t"} sharing a tail "t".
  * X.atoms_union = {"z"}                 -> covers the 5 Z-specs (greedy max).
  * Y.atoms_union = {"h1","h2","h3","t"}  -> covers the 3 P-specs.

Greedy picks X (covers 5 > 3).  But depth-2:
  * admit X -> the 3 P-specs remain, each a SEPARATE coverage group (distinct
    missing signature {h_i,t}), so one more admission covers only ONE of them;
  * admit Y -> the 5 Z-specs remain as ONE group {z}, so one more admission
    covers ALL five.
So Y reaches full coverage in two admissions while X cannot -> rollout_value(Y)
is STRICTLY below rollout_value(X).
"""
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))          # runnable as a bare script, not just -m pytest

import common
from planner import lookahead


def _spec(path, atoms, size=64):
    return {"path": path, "language": "ksy",
            "atoms": frozenset(atoms), "size_bytes": size}


def _planted():
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


def _immediate_gain(backlog, group):
    """One-step 'closure' coverage gain: backlog specs whose atoms are already a
    subset of the group's atoms_union (what a single admission covers now)."""
    cand = set(group["atoms_union"])
    return sum(1 for s in backlog
               if s["language"] == group["language"]
               and set(s["atoms"]) <= cand)


def test_greedy_prefers_X_but_lookahead_prefers_Y():
    backlog, X, Y = _planted()

    # Greedy (immediate single-admission coverage) strictly prefers X.
    gx, gy = _immediate_gain(backlog, X), _immediate_gain(backlog, Y)
    assert gx > gy, (gx, gy)          # X covers 5 now, Y covers 3

    # Depth-2 rollout STRICTLY prefers Y (the enabling group).
    vx = lookahead.rollout_value([], backlog, X, depth=2)
    vy = lookahead.rollout_value([], backlog, Y, depth=2)
    assert vy < vx, (vy, vx)
    # And both are finite ledger costs.
    assert vx == float(vx) and vy == float(vy)
    assert vx < float("inf") and vy < float("inf")


def test_non_ksy_group_is_uninf():
    """abnf / json-subset groups need an LLM-authored payload and cannot be
    hypothetically priced -> float('inf'), so they never win the min."""
    backlog, X, _ = _planted()
    abnf = {"language": "abnf", "missing": ["abnf:lit"],
            "specs": [], "atoms_union": {"abnf:lit"}}
    js = {"language": "json-subset", "missing": ["obj"],
          "specs": [], "atoms_union": {"obj"}}
    assert lookahead.rollout_value([], backlog, abnf, depth=2) == float("inf")
    assert lookahead.rollout_value([], backlog, js, depth=2) == float("inf")


def test_determinism():
    """Two calls over the same inputs return byte-identical values (no random,
    no clock; canonical-JSON tie-breaks inside beam_search)."""
    backlog, X, Y = _planted()
    a1 = lookahead.rollout_value([], backlog, Y, depth=2)
    a2 = lookahead.rollout_value([], backlog, Y, depth=2)
    assert a1 == a2
    b1 = lookahead.rollout_value([], backlog, X, depth=2)
    b2 = lookahead.rollout_value([], backlog, X, depth=2)
    assert b1 == b2
    # canonical-JSON of the value is identical (byte-for-byte).
    assert common.canonical_json(a1) == common.canonical_json(a2)


def test_hypothetical_generator_pins():
    """The hypothetical entry carries the H54/H57 pins (authored_bytes: 0 is
    REQUIRED so the eventual real admission is not underpriced)."""
    h = lookahead.hypothetical_generator({"uint:2", "uint:1"})
    assert h["spec_language"] == "ksy"
    assert h["output_language"] == "python-codec"
    assert h["spec_grammar"]["atoms"] == ["uint:1", "uint:2"]   # sorted
    assert h["emit_entrypoint"]["authored_bytes"] == 0
    assert h["emit_entrypoint"]["kind"] == "ksc-python-rw"
    assert h["contract"] == {"type": "codec-roundtrip"}


if __name__ == "__main__":
    test_greedy_prefers_X_but_lookahead_prefers_Y()
    test_non_ksy_group_is_uninf()
    test_determinism()
    test_hypothetical_generator_pins()
    backlog, X, Y = _planted()
    vx = lookahead.rollout_value([], backlog, X, depth=2)
    vy = lookahead.rollout_value([], backlog, Y, depth=2)
    print("greedy gain: X=%d  Y=%d  (closure picks X)"
          % (_immediate_gain(backlog, X), _immediate_gain(backlog, Y)))
    print("rollout_value: X=%.6f  Y=%.6f  (lookahead picks Y)" % (vx, vy))
    print("STRICT vy < vx:", vy < vx)
    print("ALL LOOKAHEAD TESTS PASS")
