"""S1.3: the searched recurrence dispatcher is FLAG-GATED and default-greedy.

`buildloop.loop.SEARCHED_RECURRENCE` defaults to False, so `_dispatch_recurrence`
is byte-identical to the landed greedy scheduler -- it admits the single picked
max-marginal-saving macro per iteration.  Flipping the flag on turns the same
dispatcher into a beam search over admission SEQUENCES (S1.3) that admits every
macro in the corpus_dl-minimizing table.

The teeth use the planted TRAP corpus (`tests/fixtures_macro_corpora.trap_corpus`)
where greedy admission of the len-4 macro A shadows the strictly-better pair
{B=[A,B], C=[C,D]} below their two-witness threshold: greedy is stranded at {A}
while the searched sequence reaches {B, C}.  We assert the corpus-STABLE relation
(searched corpus_dl < greedy corpus_dl), never brittle absolute constants.

Deterministic and LLM-free.  The flag is ALWAYS reset to False in a finally block
so it can never leak into another test's process state.
"""
import pathlib
import sys
import tempfile

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))          # runnable as a bare script, not just -m pytest

import common
from buildloop import dl, loop, recurrence
from buildloop.mdl_macros import corpus_dl
from library import Registry
import tests.fixtures_macro_corpora as fx


def _reg():
    tmp = tempfile.mkdtemp()
    return Registry(db_path=f"{tmp}/reg.sqlite")


def _seed_trap(reg):
    """Seed the TRAP corpus as certified readings (reading_add each)."""
    for i, r in enumerate(fx.trap_corpus()):
        reg.reading_add(f"trap-{i}", common.canonical_json(r), f"cert-{i}")


def _top_move(reg):
    """The greedy pick: mine over the snapshot and wrap its top candidate as the
    move dict the scheduler hands the dispatcher."""
    snap = dl.snapshot(reg)
    readings = list(snap.readings.values())
    cands = recurrence.mine(readings, reg.macro_table())
    assert cands, "the trap corpus must be mineable"
    top = cands[0]
    move = {"candidate": top["candidate"], "uses": top["uses"],
            "cluster_key": top["cluster_key"]}
    return move, snap, readings


# ------------------------------------------------------------------ the teeth
def test_default_greedy_admits_exactly_one_macro():
    """SEARCHED_RECURRENCE off (the default): exactly ONE macro is admitted --
    the greedy len-4 pick -- with status 'macro-admitted' and a 'macro' key."""
    reg = _reg()
    _seed_trap(reg)
    move, snap, _ = _top_move(reg)

    assert loop.SEARCHED_RECURRENCE is False           # the shipped default
    try:
        loop.SEARCHED_RECURRENCE = False
        res = loop._dispatch_recurrence(move, snap, reg, [], "frequency",
                                        False, None)
    finally:
        loop.SEARCHED_RECURRENCE = False               # never leak the flag

    assert res["status"] == "macro-admitted"
    assert "macro" in res and "macros" not in res      # singular -> greedy
    assert res["macro"] == move["candidate"]["name"]
    # exactly one macro is live (the greedy pick; nothing GC-stranded it).
    assert len(reg.macro_table()) == 1
    assert move["candidate"]["name"] in reg.macro_table()


def test_searched_admits_pair_cheaper_than_greedy():
    """SEARCHED_RECURRENCE on: the dispatcher admits the searched PAIR {B, C}
    (plural 'macros', strategy 'search'), and its table's corpus_dl is strictly
    below the greedy single-macro table's -- the trap the plan documents."""
    # -- greedy baseline table (for the < comparison) -----------------------
    greedy_reg = _reg()
    _seed_trap(greedy_reg)
    g_move, g_snap, g_readings = _top_move(greedy_reg)
    try:
        loop.SEARCHED_RECURRENCE = False
        loop._dispatch_recurrence(g_move, g_snap, greedy_reg, [], "frequency",
                                  False, None)
    finally:
        loop.SEARCHED_RECURRENCE = False
    greedy_table = greedy_reg.macro_table()
    greedy_dl = corpus_dl(g_readings, greedy_table)["total"]
    assert len(greedy_table) == 1                       # greedy stranded at {A}

    # -- searched table on a FRESH registry, same trap corpus ---------------
    reg = _reg()
    _seed_trap(reg)
    move, snap, readings = _top_move(reg)
    try:
        loop.SEARCHED_RECURRENCE = True
        res = loop._dispatch_recurrence(move, snap, reg, [], "frequency",
                                        False, None)
    finally:
        loop.SEARCHED_RECURRENCE = False               # ALWAYS reset the flag

    assert res["status"] == "macro-admitted"
    assert "macros" in res                              # plural -> searched
    assert res.get("strategy") == "search"
    assert len(res["macros"]) == 2                       # the searched pair {B,C}
    searched_table = reg.macro_table()
    assert len(searched_table) == 2

    searched_dl = corpus_dl(readings, searched_table)["total"]
    # the corpus-stable relation the trap exists to demonstrate.
    assert searched_dl < greedy_dl, (searched_dl, greedy_dl)


def test_flag_is_false_after_the_teeth():
    """Belt-and-suspenders: the module flag is back to its shipped default, so
    no recorded greedy fixture is perturbed by these teeth."""
    assert loop.SEARCHED_RECURRENCE is False


if __name__ == "__main__":
    test_default_greedy_admits_exactly_one_macro()
    test_searched_admits_pair_cheaper_than_greedy()
    test_flag_is_false_after_the_teeth()
    print("ALL SEARCHED-RECURRENCE-FLAG TEETH PASS")
