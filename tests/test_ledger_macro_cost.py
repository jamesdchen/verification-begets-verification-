"""S1.7 / H49: the ledger now charges for macro DEFINITIONS.

Before this seam, `dl._ledger_total` charged nothing for an admitted macro while
`recurrence.mine` gated the same macro on `mdl_macros.corpus_dl` (which DOES
charge `dl_macro` for the stored definition).  A macro admission's realized
`ledger_dl` drop therefore systematically beat the expected saving by exactly
`dl_macro(candidate)` -- the search objective and the ledger disagreed.

These teeth pin the fix: `dl.ledger_dl(reg)["macro_cost"]` equals
`sum(dl_macro(m) for m in the live table)`, is 0.0 on a macro-free ledger (so a
macro-free world is byte-identical to before), and equals exactly
`dl_macro(that_macro)` for a single admitted macro -- and the whole-ledger total
rises by exactly that amount.

Deterministic and LLM-free (no random, no clocks): every fixture is seeded
through the registry on an isolated temp DB, and `macro_cost` depends only on the
macro body, never on wall-clock.
"""
import pathlib
import sys
import tempfile

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))          # runnable as a bare script, not just -m pytest

import common
from buildloop import dl, mdl_macros, recurrence
from library import Registry


# ---- fixtures (replicated from tests/test_scheduler.py, kept self-contained) --
def _reg():
    tmp = tempfile.mkdtemp()
    return Registry(db_path=f"{tmp}/reg.sqlite")


def _bound(action, left, cmp_, right):
    return {"kind": "bound", "action": action, "left": left,
            "cmp": cmp_, "right": right}


def _stmt(sid, lf, force="demand", quote="span"):
    return {"id": sid, "force": force, "quote": quote, "lf": lf}


def _two_bound_reading(r1, r2):
    """A clean 2-statement demand cluster (uniform force+quote) so the miner has
    a single mineable window shared across every reading."""
    return common.canonical_json({"service": "shop", "statements": [
        _stmt("s1", _bound("sell", "n", "<=", r1)),
        _stmt("s2", _bound("buy", "m", ">=", r2))]})


def _seed_readings(reg, n=3):
    # readings only (no nl-request DEMAND rows), so the ledger's demand_cost is a
    # constant 0.0 and the ONLY moving part between before/after is macro_cost.
    for i in range(n):
        reg.reading_add(f"req-{i}", _two_bound_reading(5, 1), f"cert-{i}")


# ------------------------------------------------------------------ the teeth
def test_macro_free_ledger_charges_zero():
    """A fresh Registry with NO macros: macro_cost is 0.0 and the whole ledger is
    0.0 -- byte-identical to a macro-free world (no generators, no demand)."""
    reg = _reg()
    led = dl.ledger_dl(reg)
    assert led["macro_cost"] == 0.0
    assert led["ledger_dl"] == 0.0
    # readings alone (no demand rows) still charge nothing: readings are only
    # priced when a matching nl-request demand row exists.
    _seed_readings(reg)
    led2 = dl.ledger_dl(reg)
    assert led2["macro_cost"] == 0.0
    assert led2["ledger_dl"] == 0.0


def test_macro_cost_equals_dl_macro_of_admitted_macro():
    """Admitting the mined macro makes macro_cost == dl_macro(that_macro), and
    the whole ledger rises by exactly that macro_cost (nothing else moves)."""
    reg = _reg()
    _seed_readings(reg)

    before = dl.ledger_dl(reg)
    assert before["macro_cost"] == 0.0
    assert before["ledger_dl"] == 0.0

    # mine the top candidate over the seeded corpus and admit it (the exact
    # move the scheduler's greedy recurrence dispatch performs).
    snap = dl.snapshot(reg)
    readings = list(snap.readings.values())
    cands = recurrence.mine(readings, reg.macro_table())
    assert cands, "the shared 2-statement cluster must be mineable"
    macro = cands[0]["candidate"]
    reg.macro_add(macro["name"], common.canonical_json(macro))

    after = dl.ledger_dl(reg)
    expected = mdl_macros.dl_macro(macro)          # the exact definition cost
    assert expected == 23.0                          # pinned for this corpus
    # the macro_cost field IS the definition cost of the one admitted macro ...
    assert after["macro_cost"] == expected
    # ... and equals sum(dl_macro) over the whole live table (the invariant).
    assert after["macro_cost"] == sum(
        mdl_macros.dl_macro(m) for m in reg.macro_table().values())
    # ... and the whole ledger rose by EXACTLY that macro_cost, nothing else.
    assert (after["ledger_dl"] - before["ledger_dl"]) == expected
    assert after["ledger_dl"] == expected


def test_macro_cost_is_sum_over_live_table():
    """The macro_cost field is exactly sum(dl_macro) over the LIVE macro table,
    for any admitted set (here: two hand-built macros)."""
    reg = _reg()
    _seed_readings(reg)
    m1 = {"name": "m1", "params": [],
          "body": [_bound("sell", "n", "<=", 5)]}
    m2 = {"name": "m2", "params": [],
          "body": [_bound("buy", "m", ">=", 1),
                   _bound("sell", "n", "<=", 5)]}
    reg.macro_add(m1["name"], common.canonical_json(m1))
    reg.macro_add(m2["name"], common.canonical_json(m2))
    led = dl.ledger_dl(reg)
    assert led["macro_cost"] == mdl_macros.dl_macro(m1) + mdl_macros.dl_macro(m2)
    assert led["macro_cost"] == sum(
        mdl_macros.dl_macro(m) for m in reg.macro_table().values())


if __name__ == "__main__":
    test_macro_free_ledger_charges_zero()
    test_macro_cost_equals_dl_macro_of_admitted_macro()
    test_macro_cost_is_sum_over_live_table()
    print("ALL LEDGER-MACRO-COST TEETH PASS")
