"""Property-style teeth for `planner.search.beam_search` (freeze Z-A).

These complement -- and deliberately do NOT duplicate -- tests/test_search.py.
That file pins exact winners on a hand-traced trap; this file asserts the
structural INVARIANTS the rest of Zone 3 leans on, over families of inputs:

  1. beam-width monotonicity  -- a wider beam is never worse (best-ever-visited);
  2. expand-order invariance   -- reversing successor order is byte-identical;
  3. dedup                     -- duplicate successors don't change the winner
                                  (nor let a diamond-shaped graph blow up);
  4. empty expand / depth 0    -- degenerate searches return `initial`;
  5. argument guards           -- beam_width < 1 and max_depth < 0 raise.

Deterministic and LLM-free: no randomness, no wall-clock.  `score` is MINIMIZED
and ties break by canonical JSON, so every "identical winner" check compares the
canonical-JSON bytes, not just Python `==`.
"""
import pytest

import common
from planner.search import beam_search


# --------------------------------------------------------------------------
# A fixed non-trivial landscape: subsets of {a,b,c,d} as sorted tuples, where
# `expand` adds one missing element.  The costs are non-monotone in the
# admission count (adding an element can raise OR lower cost), and they are
# tuned so that the best state reachable by a width-w search STRICTLY improves
# as w grows through 1 -> 2 -> 3 and then plateaus:
#     w=1 (greedy) is trapped at 10.0 via the locally-cheapest chain,
#     w=2 unlocks ('b','c','d') = 3.0,
#     w>=3 unlocks the global optimum ('b','c') = 1.0.
# (Verified exhaustively for w up to 9 before freezing these numbers.)
# --------------------------------------------------------------------------
_ELEMS = ("a", "b", "c", "d")
_COST = {
    (): 28.0,
    ("a",): 10.0, ("b",): 23.0, ("c",): 20.0, ("d",): 12.0,
    ("a", "b"): 22.0, ("a", "c"): 27.0, ("a", "d"): 25.0,
    ("b", "c"): 1.0,  ("b", "d"): 27.0, ("c", "d"): 17.0,
    ("a", "b", "c"): 35.0, ("a", "b", "d"): 35.0,
    ("a", "c", "d"): 30.0, ("b", "c", "d"): 3.0,
    ("a", "b", "c", "d"): 37.0,
}


def _expand(state):
    # state is a sorted tuple of chosen elements; grow it by one missing element.
    s = set(state)
    return [tuple(sorted(s | {x})) for x in _ELEMS if x not in s]


def _score(state):
    return _COST[tuple(state)]


def test_beam_width_monotonic_never_worse():
    """For 1 <= w1 <= w2, score(width=w2) <= score(width=w1): a wider beam is
    never worse, because the search returns the best state EVER visited and a
    wider beam's visited set only grows on this landscape."""
    widths = range(1, 8)
    results = {w: beam_search((), _expand, _score, beam_width=w, max_depth=4)
               for w in widths}
    scores = {w: _score(results[w]) for w in widths}

    # (a) the whole width->score sequence is non-increasing.
    seq = [scores[w] for w in widths]
    assert all(seq[i] >= seq[i + 1] for i in range(len(seq) - 1)), seq

    # (b) the pairwise inequality holds for every ordered pair w1 <= w2.
    for w1 in widths:
        for w2 in widths:
            if w1 <= w2:
                assert scores[w2] <= scores[w1], (w1, w2, scores[w1], scores[w2])

    # (c) this landscape actually has teeth: widening STRICTLY helps twice, so
    #     the assertions above are not vacuously satisfied by a flat sequence.
    assert scores[1] == 10.0
    assert scores[2] == 3.0
    assert scores[3] == 1.0
    assert scores[1] > scores[2] > scores[3]


def test_expand_order_shuffle_is_byte_identical():
    """Reversing the order `expand` yields successors must not change the winner:
    the beam cut and the best-ever pick both order by (score, canonical JSON), so
    successor emission order is irrelevant.  Compared as canonical-JSON bytes."""
    def rev_expand(state):
        return list(reversed(_expand(state)))

    for w in (1, 2, 3, 4, 5):
        forward = beam_search((), _expand, _score, beam_width=w, max_depth=4)
        reversed_ = beam_search((), rev_expand, _score, beam_width=w, max_depth=4)
        assert common.canonical_json(forward) == common.canonical_json(reversed_), w

    # A landscape engineered so many states TIE on score -- order would matter if
    # the tie-break were anything other than canonical JSON.  Reversal still ties.
    def tie_expand(state):
        s = set(state)
        return [tuple(sorted(s | {x})) for x in ("x", "y", "z") if x not in s]

    def tie_score(state):
        return 0.0 if state else 1.0  # every non-empty state ties at 0.0

    a = beam_search((), tie_expand, tie_score, beam_width=4, max_depth=3)
    b = beam_search((), lambda s: list(reversed(tie_expand(s))),
                    tie_score, beam_width=4, max_depth=3)
    assert common.canonical_json(a) == common.canonical_json(b)
    # and the winner is exactly the smallest-canonical-JSON tied state seen.
    tied = [("x",), ("y",), ("z",), ("x", "y"), ("x", "z"), ("y", "z"),
            ("x", "y", "z")]
    winner = min(tied, key=common.canonical_json)
    assert common.canonical_json(a) == common.canonical_json(winner)


def test_duplicate_successors_do_not_change_winner():
    """Yielding the same successor by multiple paths (a diamond graph) must give
    the same winner as a dedup'd expand, and must not blow the search up: expand
    is called at most once per beam slot per round regardless of duplication."""
    # Diamond lattice over subsets of {a,b,c}: e.g. "ab" is reachable via both
    # "a"->"ab" and "b"->"ab".
    elems = ("a", "b", "c")
    cost = {"": 9.0, "a": 7.0, "b": 6.0, "c": 8.0,
            "ab": 5.0, "ac": 4.0, "bc": 2.0, "abc": 3.0}

    def base_expand(state):
        s = set(state)
        return ["".join(sorted(s | {x})) for x in elems if x not in s]

    def score(state):
        return cost[state]

    calls = {"n": 0}

    def dup_expand(state):
        # every successor emitted three times, by multiple "paths"
        calls["n"] += 1
        return base_expand(state) * 3

    for w in (1, 2, 3, 4):
        clean = beam_search("", base_expand, score, beam_width=w, max_depth=3)
        calls["n"] = 0
        dupd = beam_search("", dup_expand, score, beam_width=w, max_depth=3)
        assert common.canonical_json(clean) == common.canonical_json(dupd), (w, clean, dupd)
        # the winner is the true global optimum "bc" = 2.0 for w >= 2.
        if w >= 2:
            assert dupd == "bc"
        # bounded work: round 0 expands 1 state, each later round <= w states,
        # so total expand calls <= 1 + w * (max_depth - 1) despite the 3x fan-out.
        assert calls["n"] <= 1 + w * 3, (w, calls["n"])


def test_empty_expand_and_zero_depth_return_initial():
    """A search that can take no step returns `initial` unchanged, for any
    beam_width >= 1 and max_depth >= 0.  Two ways to take no step: an expand that
    yields nothing, or max_depth == 0 (the expansion loop never runs)."""
    for k in (1, 2, 5):
        # empty expand, various depths
        for d in (0, 1, 3):
            r = beam_search([1, 2], lambda s: [], lambda s: 0.0,
                            beam_width=k, max_depth=d)
            assert r == [1, 2]
            assert common.canonical_json(r) == common.canonical_json([1, 2])
        # depth 0 short-circuits even when expand WOULD produce successors.
        r0 = beam_search({"x": 1}, lambda s: [{"x": 2}], lambda s: 0.0,
                         beam_width=k, max_depth=0)
        assert r0 == {"x": 1}
        assert common.canonical_json(r0) == common.canonical_json({"x": 1})


def test_invalid_arguments_raise_value_error():
    """beam_width < 1 and max_depth < 0 are rejected with ValueError (a greedy
    step is beam_width == 1, and max_depth == 0 is the smallest valid depth)."""
    for bad_width in (0, -1, -5):
        with pytest.raises(ValueError):
            beam_search((), _expand, _score, beam_width=bad_width, max_depth=1)
    for bad_depth in (-1, -2):
        with pytest.raises(ValueError):
            beam_search((), _expand, _score, beam_width=1, max_depth=bad_depth)
    # the smallest valid combination does NOT raise.
    assert beam_search((), _expand, _score, beam_width=1, max_depth=0) == ()


if __name__ == "__main__":
    test_beam_width_monotonic_never_worse()
    test_expand_order_shuffle_is_byte_identical()
    test_duplicate_successors_do_not_change_winner()
    test_empty_expand_and_zero_depth_return_initial()
    test_invalid_arguments_raise_value_error()
    print("all search property teeth pass")
