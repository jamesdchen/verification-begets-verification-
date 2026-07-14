"""P5.1 tier-classifier tests -- HAND-BUILT DFAs, runnable under pytest or as
`python3 tests/test_monoid.py` (prints PASS lines, exits 0 on success).

Covered:
  * a*b*            -- star-free / aperiodic (both channels agree star-free)
  * (aa)* parity    -- NOT aperiodic, a 2-cycle (both channels agree NOT)
  * non-minimal DFA -- minimal form is aperiodic; classify must minimize first
                       (the raw monoid is a spurious 2-cycle -> the trap)
  * |Q|>8 cycle     -- tier-unclassified (cap exceeded)
  * channel agreement on EVERY classified DFA (ch1 verdict == ch2 verdict)
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators import monoid
from generators.monoid import (classify, hopcroft_minimize, transition_monoid,
                                CAP_EXCEEDED, _channel_monoid_aperiodic,
                                _channel_counter_free)


# --- hand-built DFAs -------------------------------------------------------

def dfa_astar_bstar():
    """a^i b^j : star-free.  q0 = a-run (acc), q1 = b-run (acc), dead."""
    return {
        "states": {"q0", "q1", "dead"},
        "initial": "q0",
        "accepting": {"q0", "q1"},
        "alphabet": {"a", "b"},
        "delta": {
            ("q0", "a"): "q0", ("q0", "b"): "q1",
            ("q1", "a"): "dead", ("q1", "b"): "q1",
            ("dead", "a"): "dead", ("dead", "b"): "dead",
        },
    }


def dfa_parity():
    """(aa)* : even number of a's.  NOT star-free -- a is a 2-cycle."""
    return {
        "states": {"even", "odd"},
        "initial": "even",
        "accepting": {"even"},
        "alphabet": {"a"},
        "delta": {("even", "a"): "odd", ("odd", "a"): "even"},
    }


def dfa_nonminimal_astar_bstar():
    """a*b* with the a-run state DUPLICATED as A,B and 'a' SWAPPING them.
    A,B are Myhill-Nerode equivalent, so the minimal DFA is a*b* (aperiodic) --
    but the un-minimized transition monoid contains the A<->B swap, a spurious
    2-cycle.  This is the 'wrong monoid on a non-minimal DFA' trap."""
    return {
        "states": {"A", "B", "C", "dead"},
        "initial": "A",
        "accepting": {"A", "B", "C"},
        "alphabet": {"a", "b"},
        "delta": {
            ("A", "a"): "B", ("A", "b"): "C",
            ("B", "a"): "A", ("B", "b"): "C",
            ("C", "a"): "dead", ("C", "b"): "C",
            ("dead", "a"): "dead", ("dead", "b"): "dead",
        },
    }


def dfa_mod9():
    """(a^9)* : length divisible by 9.  Minimal DFA is a 9-state cycle -->
    |Q|=9 > 8 --> feasibility cliff (cap exceeded)."""
    states = {str(i) for i in range(9)}
    delta = {(str(i), "a"): str((i + 1) % 9) for i in range(9)}
    return {"states": states, "initial": "0", "accepting": {"0"},
            "alphabet": {"a"}, "delta": delta}


ALL_CLASSIFIABLE = [
    ("a*b*", dfa_astar_bstar(), "control-skeleton star-free"),
    ("(aa)* parity", dfa_parity(), "not star-free"),
    ("non-minimal a*b*", dfa_nonminimal_astar_bstar(), "control-skeleton star-free"),
]


# --- tests -----------------------------------------------------------------

def test_astar_bstar_star_free():
    res = classify(dfa_astar_bstar())
    assert res["tier"] == "control-skeleton star-free", res
    assert "control skeleton" in res["detail"].lower()
    # both channels independently say star-free
    assert [c["result"] for c in res["channels"]] == ["star-free", "star-free"]
    # and the monoid really is aperiodic
    mon = transition_monoid(hopcroft_minimize(dfa_astar_bstar()))
    ap, _ = _channel_monoid_aperiodic(mon)
    assert ap


def test_parity_not_star_free():
    res = classify(dfa_parity())
    assert res["tier"] == "not star-free", res
    assert [c["result"] for c in res["channels"]] == \
        ["not star-free", "not star-free"]
    # channel 1: the monoid has a non-idempotent-power element (the swap)
    mon = transition_monoid(hopcroft_minimize(dfa_parity()))
    ap, witness = _channel_monoid_aperiodic(mon)
    assert not ap and witness is not None
    # channel 2: a counter of order 2 with a concrete word
    cf, cw = _channel_counter_free(hopcroft_minimize(dfa_parity()))
    assert not cf and cw["order"] == 2 and cw["word"] == "a"


def test_non_minimal_minimizes_first():
    raw = dfa_nonminimal_astar_bstar()
    # THE TRAP: the un-minimized monoid looks non-aperiodic (A<->B swap).
    raw_mon = transition_monoid(raw)          # 4 states, NOT minimized
    ap_raw, _ = _channel_monoid_aperiodic(raw_mon)
    assert not ap_raw, "expected the raw (non-minimal) monoid to look non-aperiodic"
    # minimization collapses A,B: fewer states, and the truth is star-free.
    md = hopcroft_minimize(raw)
    assert len(md["states"]) < len(raw["states"])   # 3 < 4
    res = classify(raw)
    assert res["tier"] == "control-skeleton star-free", res
    assert [c["result"] for c in res["channels"]] == ["star-free", "star-free"]


def test_cap_exceeded():
    md = hopcroft_minimize(dfa_mod9())
    assert len(md["states"]) == 9                    # minimal is 9 states
    assert transition_monoid(md) is CAP_EXCEEDED     # sentinel, not a monoid
    res = classify(dfa_mod9())
    assert res["tier"] == "tier-unclassified (cap exceeded)", res
    # honest non-certificate: channels are unclassified, not "fail"
    assert all(c["result"] == "unclassified" for c in res["channels"])


def test_channels_agree_on_all():
    """The dual-checker point: the two independent channels agree on every
    classified DFA (never a disagreement)."""
    for name, dfa, expected in ALL_CLASSIFIABLE:
        res = classify(dfa)
        assert res["tier"] == expected, (name, res)
        r1, r2 = (c["result"] for c in res["channels"])
        assert r1 == r2, f"{name}: channel disagreement {r1!r} vs {r2!r}"
        assert res["independent_channels"] is True


def test_minimize_completes_and_is_total():
    # a*b* as given omits no transitions, but parity over a 2-symbol alphabet
    # would need a dead sink; check completion adds one and totals delta.
    partial = {
        "states": {"s0", "s1"}, "initial": "s0", "accepting": {"s1"},
        "alphabet": {"a", "b"},
        "delta": {("s0", "a"): "s1", ("s1", "b"): "s1"},   # missing edges
    }
    md = hopcroft_minimize(partial)
    for s in md["states"]:
        for c in md["alphabet"]:
            assert (s, c) in md["delta"], "minimal DFA transition not total"


if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    for name, fn in fns:
        fn()
        print("PASS", name)
    # report the classifications + channel agreement, as the task asks
    print("--- classifications ---")
    for name, dfa, _ in ALL_CLASSIFIABLE + [("(a^9)* mod9", dfa_mod9(), None)]:
        res = classify(dfa)
        chans = "/".join(c["result"] for c in res["channels"])
        agree = "" if len({c["result"] for c in res["channels"]}) == 1 else " !!DISAGREE"
        print(f"  {name:20s} -> {res['tier']:34s} [channels: {chans}]{agree}")
    print("all monoid tier-classifier tests hold")
