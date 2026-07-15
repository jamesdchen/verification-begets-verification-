"""Deterministic beam search over admission *sequences* (Zone 3, freeze Z-A).

The one shared search primitive of the speculative planner.  Both Zone-3 DL
objectives it drives -- `mdl_macros.corpus_dl` over macro-admission sequences
(S1.3) and `dl._ledger_total` over hypothetical coverage admissions (S2.1) --
are NON-MONOTONE in the admission count: adding one more macro / one more
generator can raise the running cost even when a deeper sequence lowers it
below anything a greedy step would reach.  So the search:

  * keeps the `beam_width` lowest-`score` states at each depth (a greedy step is
    exactly `beam_width == 1`), and
  * returns the best state EVER VISITED -- not merely the best leaf -- because a
    shallower state may score lower than everything reachable past it (H19).

`score` is minimized (lower is better): a description length, a ledger cost.
Everything is deterministic and side-effect-free (house rule 5): ties break by
canonical JSON, so two runs over the same inputs return byte-identical winners.
No wall-clock, no randomness.  This module exports ONLY `beam_search`.
"""
from __future__ import annotations

import common


def beam_search(initial, expand, score, *, beam_width, max_depth):
    """Minimize `score` over states reachable from `initial` by `expand`.

    Args:
      initial:    the start state (any canonical-JSON-serializable value).
      expand:     state -> iterable of successor states.
      score:      state -> float; LOWER is better.
      beam_width: states carried forward per depth (>= 1; 1 == greedy).
      max_depth:  maximum expansion rounds.

    Returns the single best state ever visited (including `initial` and every
    intermediate), ties broken by lexicographically smallest canonical JSON.
    """
    if beam_width < 1:
        raise ValueError("beam_width must be >= 1")
    if max_depth < 0:
        raise ValueError("max_depth must be >= 0")

    def _key(state):
        # (score, canonical-json) -- the total order that makes both the beam
        # cut and the best-ever pick deterministic.
        return (float(score(state)), common.canonical_json(state))

    best = initial
    best_key = _key(initial)

    # Frontier entries carry their canonical JSON so we can dedup states that
    # are reachable by more than one path (keeps the beam from multiplying and
    # keeps the round deterministic regardless of expansion order).
    frontier = [(best_key, initial)]
    for _depth in range(max_depth):
        seen = set()
        scored = []
        for _pk, state in frontier:
            for succ in expand(state):
                cj = common.canonical_json(succ)
                if cj in seen:
                    continue
                seen.add(cj)
                k = (float(score(succ)), cj)
                scored.append((k, succ))
                if k < best_key:
                    best, best_key = succ, k
        if not scored:
            break
        scored.sort(key=lambda t: t[0])
        frontier = scored[:beam_width]
    return best
