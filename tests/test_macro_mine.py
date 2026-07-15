"""Teeth for the S1 miner filters and searched admission (WP-E + WP-J).

Deterministic, LLM-free, no external tools -- everything runs over the planted
corpora in tests/fixtures_macro_corpora.py through buildloop.recurrence /
buildloop.mdl_macros only.

Covers:
  * H3  -- the concreteness filter rejects a bare-wildcard candidate the pre-H3
           gate would have minted.
  * H2  -- windows are uniform (force, quote); a mixed-quote window is not mined.
  * S1.3 trap -- the searched admission sequence is STRICTLY cheaper than the
           greedy one-max-saving-per-step baseline on the planted trap.
  * S1.3 never-worse -- searched <= greedy everywhere.
  * part_c -- nothing is admitted on the incompressible corpus.
  * Z1  -- every macro the search admits independently passes the explicit
           macro_admission_decision gate.
"""
from buildloop import recurrence, mdl_macros
from buildloop.mdl_macros import corpus_dl, macro_admission_decision
from tests import fixtures_macro_corpora as fx


# ------------------------------------------------------------------ H3 filter
def test_h3_rejects_bare_wildcard_body():
    assert recurrence._body_admissible(["$p0", "$p1"]) is False
    # a mostly-concrete parametric body is fine (only the varying leaf is a param)
    assert recurrence._body_admissible(
        [{"kind": "always", "pred": {"op": ">=", "left": "$p0", "right": 0}}])


def test_h3_wildcard_corpus_mines_nothing_but_would_without_filter():
    corpus = fx.wildcard_corpus()
    assert recurrence.mine(corpus, {}) == []          # H3 removes the wildcard
    # prove the wildcard is exactly what the pre-H3 gate would have minted
    saved = recurrence._body_admissible
    recurrence._body_admissible = lambda body: True
    try:
        raw = recurrence.mine(corpus, {})
    finally:
        recurrence._body_admissible = saved
    assert len(raw) == 1 and raw[0]["candidate"]["body"] == ["$p0", "$p1"]


# ------------------------------------------------------------------ H2 windows
def test_h2_mixed_quote_window_not_mined():
    assert recurrence._demand_windows(fx.mixed_quote_reading(), 4) == []


def test_h2_uniform_window_is_mined():
    r = {"service": "u", "statements": [
        {"id": "s0", "force": "demand", "quote": "same",
         "lf": {"kind": "always", "pred": {"op": ">=", "left": "q", "right": 0}}},
        {"id": "s1", "force": "demand", "quote": "same",
         "lf": {"kind": "bound", "action": "a", "left": "n",
                "cmp": "<=", "right": "q"}}]}
    wins = recurrence._demand_windows(r, 4)
    assert len(wins) == 1 and len(wins[0]) == 2


# --------------------------------------------------------------- searched trap
def _greedy(corpus):
    return recurrence.searched_macro_sequence(corpus, {}, beam_width=1,
                                              max_depth=6)


def _searched(corpus):
    return recurrence.searched_macro_sequence(corpus, {}, beam_width=10,
                                              max_depth=6)


def test_trap_searched_strictly_beats_greedy():
    corpus = fx.trap_corpus()
    g, s = _greedy(corpus), _searched(corpus)
    gt = corpus_dl(corpus, g)["total"]
    st = corpus_dl(corpus, s)["total"]
    assert st < gt                       # STRICT: the trap is escaped
    assert len(g) == 1                   # greedy stranded on the len-4 macro
    assert len(s) == 2                   # searched admits the better pair {B, C}


def test_searched_never_worse_than_greedy():
    for corpus in (fx.trap_corpus(), fx.incompressible_corpus()):
        gt = corpus_dl(corpus, _greedy(corpus))["total"]
        st = corpus_dl(corpus, _searched(corpus))["total"]
        assert st <= gt


def test_incompressible_admits_nothing():
    corpus = fx.incompressible_corpus()
    assert recurrence.mine(corpus, {}) == []
    assert recurrence.searched_macro_sequence(
        corpus, {}, beam_width=6, max_depth=4) == {}


def test_searched_macros_each_pass_the_explicit_gate():
    # Z1: rebuild the winning table one macro at a time; each admission must be
    # independently justified by the MDL gate against the table so far.
    corpus = fx.trap_corpus()
    winner = _searched(corpus)
    table = {}
    for name in sorted(winner):
        cand = winner[name]
        assert macro_admission_decision(corpus, cand, table)["admit"]
        table[name] = cand


if __name__ == "__main__":
    for fn in list(globals().values()):
        if callable(fn) and getattr(fn, "__name__", "").startswith("test_"):
            fn()
    print("all macro-mine teeth pass")
