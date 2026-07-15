#!/usr/bin/env python3
"""S3 part_a / WP-M -- the structural CHOICE-force tail macro (the H2 win).

Deterministic, LLM-free, no external tools.  Everything runs over a hand-planted
corpus through ``buildloop.recurrence`` / ``planner.choices`` /
``buildloop.mdl_macros`` only.

The claim under test.  ``buildloop.recurrence._demand_windows`` now mines
UNIFORM-(force, quote) windows, not demand-force-only (read recurrence.py:
the docstring calls this "H2" and names "S3's choice-tail idiom" as exactly what
it unlocks).  A CHOICE-force tail -- a run of statements all ``force="choice"``,
``quote=""`` -- was therefore UNMINEABLE pre-H2 (the old rule kept demand-force
windows only).  This file proves it is mineable now, and that the mined body is a
CHOICE-force macro:

  * a corpus of two readings that share a contiguous choice-force transition tail
    yields a mined macro whose body IS that tail, and the statements it abstracts
    are force="choice", quote="" (the H2 win);
  * NEGATIVE CONTROL -- give the SAME tail's two statements DIFFERENT quotes and
    the H2 uniform-(force, quote) rule drops the window: nothing is mined (an
    honest macro invocation expands to statements that ALL inherit one force AND
    one quote, so a mixed-quote window would be unrealizable);
  * flat vs macro-aware DL differ against the LIVE macro table: scoring a reading
    with the mined choice-tail macro in the table is STRICTLY cheaper than the
    flat (empty-table) score -- the choice-tail macro compresses the design.
"""
from __future__ import annotations

import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))       # runnable as a bare script, not just -m pytest

from buildloop import recurrence, mdl_macros
import planner.choices as ch

# --------------------------------------------------------------------------- #
# The choice-force tail idiom under test: two adjacent transition statements,
# both force="choice", quote="" -- exactly the S3 example.  Distinct actions and
# targets keep them concrete (so anti-unification yields a literal, param-free
# body -- the tail itself -- that clears the H3 concreteness filter).
TAIL = [
    {"kind": "transition", "action": "a", "from": "open", "to": "open"},
    {"kind": "transition", "action": "close_out", "from": "open", "to": "closed"},
]
TAIL_CLUSTER_KEY = ["transition", "transition"]


def _choice(sid, lf, quote=""):
    """A choice-force tail statement (quote="" is the realizable choice form)."""
    return {"id": sid, "force": "choice", "quote": quote, "lf": dict(lf)}


def _demand_prefix(sid, quote):
    """A single demand statement in front of the tail, so the choice cluster is a
    genuine TAIL.  One statement forms no length>=2 window on its own, and its
    force ("demand") differs from the tail's, so it never merges into the choice
    window -- it is inert to the miner.  Distinct quotes per reading keep the
    prefix from forming any recurring cluster of its own."""
    return {"id": sid, "force": "demand", "quote": quote,
            "lf": {"kind": "always", "pred": {"op": ">=", "left": "q", "right": 0}}}


def _reading(name, prefix_quote, tail_quotes=("", "")):
    return {"service": name, "statements": [
        _demand_prefix(name + "_d", prefix_quote),
        _choice(name + "_t0", TAIL[0], tail_quotes[0]),
        _choice(name + "_t1", TAIL[1], tail_quotes[1])]}


def _good_corpus():
    """Two readings sharing the byte-identical choice-force tail (quote="")."""
    return [_reading("svc1", "keep the quantity non negative here"),
            _reading("svc2", "an entirely different demand quote string")]


def _mismatched_corpus():
    """The SAME two readings, but each tail's two statements carry DIFFERENT
    quotes -- the H2 uniform-quote violation the negative control needs."""
    return [_reading("svc1", "keep the quantity non negative here",
                     tail_quotes=("alpha", "beta")),
            _reading("svc2", "an entirely different demand quote string",
                     tail_quotes=("alpha", "beta"))]


def _choice_tail_candidate(candidates):
    """The mined candidate abstracting the transition/transition choice tail."""
    hits = [c for c in candidates if c["cluster_key"] == TAIL_CLUSTER_KEY]
    return hits[0] if hits else None


# --------------------------------------------------------------------------- #
def test_choice_force_tail_is_mined():
    """mine() returns a candidate whose body IS the choice-tail cluster, and the
    statements it abstracts are force="choice" -- the H2 win (pre-H2 a choice
    window was not mineable)."""
    corpus = _good_corpus()

    # The choice tail forms a uniform-(force, quote) window -- and it is CHOICE.
    win = recurrence._demand_windows(corpus[0], recurrence.DEFAULT_MAX_LEN)
    tail_win = [w for w in win
                if [s["lf"]["kind"] for s in w] == TAIL_CLUSTER_KEY]
    assert len(tail_win) == 1, win
    assert all(s["force"] == "choice" and s.get("quote", "") == ""
               for s in tail_win[0]), "the mined window must be CHOICE-force"

    cands = recurrence.mine(corpus, {})
    macro = _choice_tail_candidate(cands)
    assert macro is not None, cands                       # >= 1 choice-tail macro
    cand = macro["candidate"]
    assert cand["body"] == TAIL, cand["body"]             # body IS the tail cluster
    assert macro["uses"] >= 2 and macro["dl_saving"] > 0, macro

    # Confirm CHOICE-force at the source: every statement the mined body matches,
    # in every reading, carries force="choice", quote="".
    for r in corpus:
        tail_stmts = r["statements"][-2:]
        assert [s["lf"] for s in tail_stmts] == TAIL
        assert all(s["force"] == "choice" and s["quote"] == "" for s in tail_stmts)


def test_mismatched_quotes_drops_the_window():
    """NEGATIVE CONTROL (H2 uniform-quote rule): give the tail's two statements
    DIFFERENT quotes and the window is dropped -- so the choice-tail macro is NOT
    mined, even though the uniform-quote corpus mines it."""
    good, bad = _good_corpus(), _mismatched_corpus()

    # The uniform corpus DOES surface the transition/transition window ...
    good_win = [w for w in recurrence._demand_windows(good[0],
                                                      recurrence.DEFAULT_MAX_LEN)
                if [s["lf"]["kind"] for s in w] == TAIL_CLUSTER_KEY]
    assert len(good_win) == 1

    # ... but the mismatched-quote corpus surfaces NO such window (H2 drops it).
    bad_win = [w for w in recurrence._demand_windows(bad[0],
                                                     recurrence.DEFAULT_MAX_LEN)
               if [s["lf"]["kind"] for s in w] == TAIL_CLUSTER_KEY]
    assert bad_win == [], bad_win

    # And so mine() yields no choice-tail macro on the mismatched corpus, where
    # the uniform corpus does.
    assert _choice_tail_candidate(recurrence.mine(good, {})) is not None
    assert recurrence.mine(bad, {}) == []
    assert _choice_tail_candidate(recurrence.mine(bad, {})) is None


def test_flat_vs_macro_aware_scores_differ():
    """The mined choice-tail macro compresses the design: scoring a reading
    against the LIVE macro table (planner.choices.score_reading) is strictly
    cheaper than the flat, empty-table score."""
    corpus = _good_corpus()
    macro = _choice_tail_candidate(recurrence.mine(corpus, {}))
    assert macro is not None
    cand = macro["candidate"]
    table = {cand["name"]: cand}                          # the LIVE macro table

    reading = corpus[0]
    flat = ch.score_reading(reading, {})
    macroed = ch.score_reading(reading, table)
    assert macroed < flat, (macroed, flat)               # the compression

    # Freeze contract: the flat score IS the flat reading DL, byte-for-byte; and
    # the compression is real -- the reading needs one fewer statement to write
    # (its choice tail collapses to a single macro invocation).
    assert flat == mdl_macros.dl_reading(reading, {})
    assert mdl_macros.statement_count(reading, table) < \
        mdl_macros.statement_count(reading, {})


if __name__ == "__main__":
    failures = 0
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print("PASS", _name)
            except AssertionError as exc:
                failures += 1
                print("FAIL", _name, "--", exc)
    if failures:
        print(f"{failures} choice-tail teeth FAILED")
        sys.exit(1)
    print("all choice-tail teeth pass "
          "(a CHOICE-force tail is mined post-H2; mismatched quotes drop it; "
          "the mined macro compresses the design)")
