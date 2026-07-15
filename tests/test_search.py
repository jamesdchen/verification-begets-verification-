"""Teeth for the Zone-3 beam search skeleton (freeze Z-A, planner/search.py).

Deterministic and LLM-free.  The properties the rest of Zone 3 relies on:
  * greedy == beam_width 1 (so the searched upgrade has a faithful baseline);
  * best-ever-visited, not best-leaf (both DL objectives are non-monotone in
    admissions -- a shallow state can beat everything past it);
  * a wider beam escapes a greedy local optimum the trap needs escaped;
  * determinism -- ties break by canonical JSON, two runs agree byte-for-byte.
"""
import common
from planner.search import beam_search


def _sorted_int_state(state):
    # a state is a sorted tuple of chosen ints (as a list, JSON-canonical)
    return list(state)


def test_greedy_is_beam_width_one():
    # A landscape where the greedy first step (pick the locally cheapest) leads
    # into a dead end while a costlier first step reaches the global optimum.
    #   score(state) = the classic non-monotone trap:
    #     {}      -> 0
    #     {a}     -> 5   (locally the ONLY improving single step is 'a'? no)
    # Encode states as frozenset-like sorted lists over {'a','b','c'}.
    COST = {(): 10.0,
            ("a",): 5.0, ("b",): 8.0, ("c",): 9.0,
            ("a", "b"): 6.0, ("a", "c"): 7.0, ("b", "c"): 3.0,
            ("a", "b", "c"): 4.0}

    def expand(state):
        s = set(state)
        return [tuple(sorted(s | {x})) for x in ("a", "b", "c") if x not in s]

    def score(state):
        return COST[tuple(state)]

    # width 1 (greedy) walks the single-cheapest chain {} -> {a}(5) -> {a,b}(6)
    # -> {a,b,c}(4); its best-EVER is 4.0.  It never visits {b,c}=3 because the
    # forced chain went through 'a' first.
    greedy = beam_search((), expand, score, beam_width=1, max_depth=3)
    assert score(greedy) == 4.0
    assert tuple(greedy) == ("a", "b", "c")

    # width 2 keeps {a}=5 AND {b}=8 at depth 1; expanding {b} reaches {b,c}=3,
    # the global optimum a greedy chain never sees.
    searched = beam_search((), expand, score, beam_width=2, max_depth=3)
    assert score(searched) == 3.0
    assert tuple(searched) == ("b", "c")


def test_best_ever_not_best_leaf():
    # Every path strictly worsens after depth 1, so the best LEAF at max_depth is
    # worse than an intermediate.  best-ever must return the intermediate.
    def expand(state):
        n = len(state)
        return [state + [n]] if n < 3 else []

    def score(state):
        # 0 -> 1 -> then climbs: [] =5, [0]=1, [0,1]=2, [0,1,2]=3
        return {0: 5.0, 1: 1.0, 2: 2.0, 3: 3.0}[len(state)]

    best = beam_search([], expand, score, beam_width=1, max_depth=3)
    assert score(best) == 1.0
    assert best == [0]


def test_determinism_and_tiebreak():
    # Two states tie on score; the winner is the lexicographically smaller
    # canonical JSON, and repeated runs agree.
    def expand(state):
        s = set(state)
        return [tuple(sorted(s | {x})) for x in ("x", "y") if x not in s]

    def score(state):
        return 0.0 if state else 1.0   # any non-empty state ties at 0.0

    r1 = beam_search((), expand, score, beam_width=4, max_depth=2)
    r2 = beam_search((), expand, score, beam_width=4, max_depth=2)
    assert r1 == r2
    # ('x',) and ('y',) and ('x','y') all score 0.0; smallest canonical JSON wins
    tied = [("x",), ("y",), ("x", "y")]
    winner = min(tied, key=lambda s: common.canonical_json(s))
    assert tuple(r1) == winner


def test_zero_depth_returns_initial():
    best = beam_search([1, 2], lambda s: [], lambda s: 0.0,
                       beam_width=3, max_depth=0)
    assert best == [1, 2]


if __name__ == "__main__":
    test_greedy_is_beam_width_one()
    test_best_ever_not_best_leaf()
    test_determinism_and_tiebreak()
    test_zero_depth_returns_initial()
    print("all search teeth pass")
