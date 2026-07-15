"""Integration teeth for the additive `lookahead` pick_group POLICY (Zone 3, S2).

Where tests/test_lookahead.py exercises `planner.lookahead.rollout_value` as a
pure function, THIS file proves the policy is wired correctly INTO
`buildloop.loop.pick_group(groups, "lookahead", backlog, registry)`:

  * pick_group("lookahead") returns a real group (never None on a non-empty
    input), never crashes, and is DETERMINISTIC (two calls -> the same group);
  * it minimizes `rollout_value` (LOWER ledger cost wins) -- the `min` branch,
    NOT the `max` that "frequency"/"closure" take -- so it can genuinely DISAGREE
    with the greedy "closure" pick on a planted non-monotone world;
  * an empty `groups` list returns None;
  * a non-ksy (abnf) group prices to float("inf") through rollout_value, so
    "lookahead" never picks it over a finite-priced ksy group.

FAST, pure, deterministic, LLM-free, ksc-free: the registry is a throwaway
temp-dir sqlite with NO live generators, and every price is subset arithmetic
over made-up ksy atoms.  No real generator is ever admitted.

The planted world (identical structure to demo_lookahead.py's Part A, which the
policy exists to catch):
  * Z-specs: five specs each with atoms {"z"}.
  * P-specs: three specs {"h1","t"}, {"h2","t"}, {"h3","t"} sharing a tail "t".
  * X.atoms_union = {"z"}                 -> covers the 5 Z-specs (greedy max).
  * Y.atoms_union = {"h1","h2","h3","t"}  -> covers the 3 P-specs.
Greedy "closure" picks X (5 > 3).  But depth-2: admitting X strands the 3
P-specs across THREE distinct coverage groups (missing signatures {h_i,t}
differ), so one more admission finishes only one of them; admitting Y leaves the
5 Z-specs as ONE group {z}, so a single cheap second admission finishes them
ALL.  Y reaches full coverage in two admissions and X cannot, so
rollout_value(Y) < rollout_value(X) and "lookahead" picks Y -- the two policies
DISAGREE.
"""
import pathlib
import sys
import tempfile

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))          # runnable as a bare script, not just -m pytest

from buildloop import loop
from planner import lookahead
from library import Registry


def _fresh_registry():
    """A throwaway registry on its own temp-dir sqlite -- no live generators, so
    the lookahead rollout prices against the same empty generator set the
    integration exercises (one writer per DB, the house rule)."""
    return Registry(db_path=tempfile.mkdtemp() + "/r.sqlite")


def _spec(path, atoms, size=64):
    """A backlog spec-file dict (the shape buildloop.loop.backlog_index emits,
    with a set() of atoms as the task specifies)."""
    return {"path": path, "language": "ksy",
            "atoms": set(atoms), "size_bytes": size}


def _planted():
    """5 Z-specs {z}; 3 P-specs {h_i,t} sharing tail t; groups X (greedy max) and
    Y (the enabling group)."""
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


def _lookahead_key(reg, backlog, g):
    """Re-derive pick_group's OWN lookahead sort key (min over this tuple): the
    rollout ledger cost, then the missing-atom string tie-break.  Priced against
    the registry's live generators, exactly like the policy branch does."""
    return (lookahead.rollout_value(reg.live_generators(), backlog, g,
                                    depth=loop.LOOKAHEAD_DEPTH),
            "".join(g["missing"]))


# ---------------------------------------------------------------- tooth 1
def test_pick_group_returns_a_group_and_is_deterministic():
    backlog, X, Y = _planted()
    groups = [X, Y]
    reg = _fresh_registry()

    picked = loop.pick_group(groups, "lookahead", backlog, reg)
    assert picked is not None
    assert picked in groups                       # a real member, not a fresh dict

    # Deterministic: no clock, no randomness -> the same group object every call.
    again = loop.pick_group(groups, "lookahead", backlog, reg)
    assert again is picked


# ---------------------------------------------------------------- tooth 2
def test_lookahead_disagrees_with_closure_and_minimizes_rollout_value():
    backlog, X, Y = _planted()
    groups = [X, Y]
    reg = _fresh_registry()

    picked_closure = loop.pick_group(groups, "closure", backlog, reg)
    picked_lookahead = loop.pick_group(groups, "lookahead", backlog, reg)

    # The policies GENUINELY DISAGREE on this planted, non-monotone world:
    # greedy closure picks the immediately-dominant X, lookahead picks Y.
    assert picked_closure is X
    assert picked_lookahead is Y
    assert picked_lookahead is not picked_closure

    # Faithful integration check: pick_group's lookahead branch is exactly the
    # argmin of rollout_value under its (value, missing-string) tie-break.
    expected = min(groups, key=lambda g: _lookahead_key(reg, backlog, g))
    assert picked_lookahead is expected

    # LOWER ledger cost wins (the `min` branch): Y's rollout is STRICTLY below X's.
    vx = lookahead.rollout_value(reg.live_generators(), backlog, X,
                                 depth=loop.LOOKAHEAD_DEPTH)
    vy = lookahead.rollout_value(reg.live_generators(), backlog, Y,
                                 depth=loop.LOOKAHEAD_DEPTH)
    assert vy < vx
    assert vx < float("inf") and vy < float("inf")   # both finite ledger costs


# ---------------------------------------------------------------- tooth 3
def test_empty_groups_returns_none():
    backlog, _X, _Y = _planted()
    reg = _fresh_registry()
    assert loop.pick_group([], "lookahead", backlog, reg) is None


# ---------------------------------------------------------------- tooth 4
def test_abnf_group_prices_to_inf_and_is_never_picked():
    backlog, X, _Y = _planted()
    reg = _fresh_registry()

    abnf = {"language": "abnf", "missing": ["abnf:lit"],
            "specs": [], "atoms_union": {"abnf:lit"}}

    # An abnf / non-ksy group cannot be hypothetically priced -> float("inf").
    assert lookahead.rollout_value(reg.live_generators(), backlog, abnf,
                                   depth=loop.LOOKAHEAD_DEPTH) == float("inf")

    # So among a finite-priced ksy group and the inf-priced abnf group,
    # "lookahead" (a min) never picks the abnf one -- in either input order.
    assert loop.pick_group([X, abnf], "lookahead", backlog, reg) is X
    assert loop.pick_group([abnf, X], "lookahead", backlog, reg) is X


if __name__ == "__main__":
    test_pick_group_returns_a_group_and_is_deterministic()
    test_lookahead_disagrees_with_closure_and_minimizes_rollout_value()
    test_empty_groups_returns_none()
    test_abnf_group_prices_to_inf_and_is_never_picked()

    _backlog, _X, _Y = _planted()
    _reg = _fresh_registry()
    _vx = lookahead.rollout_value(_reg.live_generators(), _backlog, _X,
                                  depth=loop.LOOKAHEAD_DEPTH)
    _vy = lookahead.rollout_value(_reg.live_generators(), _backlog, _Y,
                                  depth=loop.LOOKAHEAD_DEPTH)
    print("closure picks X; lookahead picks Y (policies disagree)")
    print("rollout_value: X=%.6f  Y=%.6f  (STRICT vy < vx: %s)"
          % (_vx, _vy, _vy < _vx))
    print("ALL LOOKAHEAD POLICY TESTS PASS")
