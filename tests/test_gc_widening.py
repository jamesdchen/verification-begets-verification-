"""S1.6 GC widening teeth for `buildloop.recurrence.gc_macros`.

`gc_macros` runs TWO victim passes per fixpoint step (recurrence.py):

  * pass 1 -- the original W3.3 `uses < 2` fast path (byte-identical): a macro
    stranded below its two-witness threshold whose `dl_macro` is still paid.
    Retirement reason == "below-two-uses-and-dl-reducing".
  * pass 2 -- the S1.6 widening: ANY macro (even one with >= 2 uses) whose
    ablation strictly reduces total `corpus_dl`.  Reason ==
    "ablation-strictly-dl-reducing".

Deterministic and LLM-free: fixtures are seeded on an isolated temp DB and the
widened victim is injected directly with `reg.macro_add`, so nothing calls the
miner, the kernel, or an LLM.  This file only READS the shipped code; it changes
nothing.

Tooth 2 (the widened path) is the load-bearing one: it constructs a >= 2-use
macro whose definition cost outweighs the two invocations' savings, so removing
it STRICTLY reduces the corpus DL even though pass 1 would never touch it (it is
not stranded).  The arithmetic (verified inline before the gc call):

    body = [{"a": {}}, {"b": {}}]          # two leaf_count-1 concrete stmts
    dl_macro          = 1 + 0 + (2 + 2)          = 5
    dl_invocation(0)  = 1 + 1 + 0                = 2
    per-use saving    = body_stmt_cost(4) - 2    = 2
    corpus_dl WITH    = 5 (table) + 2*2 (2 invocations) = 9
    corpus_dl WITHOUT = 0 (table) + 2*4 (raw stmts)     = 8   <-- strictly lower

so ablation saves 9 - 8 = 1 with uses == 2 -- the exact stale-vocabulary hazard
pass 2 exists to close.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
from buildloop import recurrence
from buildloop.mdl_macros import corpus_dl, dl_macro
from library import Registry


def _reg():
    return Registry(db_path=f"{tempfile.mkdtemp()}/r.sqlite")


def _bound(action, left, cmp_, right):
    return {"kind": "bound", "action": action, "left": left,
            "cmp": cmp_, "right": right}


def _stmt(sid, lf, force="demand", quote="span"):
    return {"id": sid, "force": force, "quote": quote, "lf": lf}


def _retired_event(reg, name):
    """The single `macro-retired` event payload for `name` (fail loudly if the
    macro was retired more than once or not at all)."""
    hits = [e["payload"] for e in reg.events("macro-retired")
            if e["payload"]["name"] == name]
    assert len(hits) == 1, f"expected exactly one retirement of {name}: {hits}"
    return hits[0]


# ------------------------------------------------------- pass 1 (unchanged)
def test_pass1_fast_path_reason_unchanged():
    """Fast-path regression (mirrors
    tests/test_scheduler.py::test_macro_gc_retires_stranded_macro).  Admitting
    the longer macro B greedily shadows the shorter A, stranding A at uses == 0;
    A is retired by pass 1 with the ORIGINAL reason and its uses<2 payload.  B,
    a genuine >= 2-use compressor, survives."""
    reg = _reg()
    s1 = _bound("a", "x", "<=", 1)
    s2 = _bound("b", "y", "<=", 2)
    s3 = _bound("c", "z", "<=", 3)
    stmts = [_stmt("s1", s1), _stmt("s2", s2), _stmt("s3", s3)]
    readings = [{"service": "svc", "statements": stmts},
                {"service": "svc2", "statements": stmts}]
    for i, r in enumerate(readings):
        reg.reading_add(f"r{i}", common.canonical_json(r), f"c{i}")

    macro_a = {"name": "A", "params": [], "body": [s1, s2]}
    macro_b = {"name": "B", "params": [], "body": [s1, s2, s3]}
    reg.macro_add("A", common.canonical_json(macro_a))
    reg.macro_add("B", common.canonical_json(macro_b))

    # Precondition: A is stranded (B shadows it) -> A qualifies for pass 1 only.
    uses = corpus_dl(readings, reg.macro_table())["reading_uses"]
    assert uses["A"] < 2 and uses["B"] == 2, uses

    before = corpus_dl(readings, reg.macro_table())["total"]
    retired = recurrence.gc_macros(reg, readings)
    after = corpus_dl(readings, reg.macro_table())["total"]

    assert retired == ["A"]
    assert "A" not in reg.macro_table() and "B" in reg.macro_table()
    # Retirement banked exactly dl_macro(A) (the shadowed, still-paid definition).
    assert abs((before - after) - dl_macro(macro_a)) < 1e-6

    payload = _retired_event(reg, "A")
    assert payload["reason"] == "below-two-uses-and-dl-reducing"
    assert payload["uses"] < 2                       # pass 1 fired, not pass 2


# ------------------------------------------------------- pass 2 (S1.6 widen)
def test_pass2_widened_retires_ge_two_use_macro():
    """Widened path: a macro with uses == 2 whose `dl_macro` exceeds its total
    savings.  Pass 1 skips it (uses >= 2); pass 2 retires it because ablation
    strictly reduces corpus DL.  We verify BOTH properties on `corpus_dl` before
    running gc, then assert the widened reason and the >= 2 uses in the payload
    (which together prove pass 2, not pass 1, fired)."""
    reg = _reg()
    # Two leaf_count-1 concrete LFs: cheap enough that a 2-statement body's
    # definition cost (5) outweighs its 2 invocations' savings (2 each -> 4).
    lf_a, lf_b = {"a": {}}, {"b": {}}
    macro = {"name": "w_two_use", "params": [], "body": [lf_a, lf_b]}
    reg.macro_add("w_two_use", common.canonical_json(macro))

    readings = [
        {"service": "svc",
         "statements": [_stmt("s1", lf_a), _stmt("s2", lf_b)]},
        {"service": "svc2",
         "statements": [_stmt("s1", lf_a), _stmt("s2", lf_b)]},
    ]
    for i, r in enumerate(readings):
        reg.reading_add(f"r{i}", common.canonical_json(r), f"c{i}")

    table = reg.macro_table()
    with_macro = corpus_dl(readings, table)
    without_macro = corpus_dl(readings, {})

    # Property 1: the macro genuinely has >= 2 uses -- pass 1 CANNOT touch it.
    assert with_macro["reading_uses"]["w_two_use"] == 2
    # Property 2: yet removing it strictly reduces total DL (net-negative macro).
    assert without_macro["total"] < with_macro["total"]
    # Pin the exact numbers this tooth relies on (see module docstring).
    assert (with_macro["total"], without_macro["total"]) == (9.0, 8.0)
    assert dl_macro(macro) == 5.0

    retired = recurrence.gc_macros(reg, readings)

    assert retired == ["w_two_use"]
    assert "w_two_use" not in reg.macro_table()

    payload = _retired_event(reg, "w_two_use")
    assert payload["reason"] == "ablation-strictly-dl-reducing"   # pass 2
    assert payload["uses"] >= 2                                    # NOT pass 1
    assert payload["uses"] == 2


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    # Report the corpus_dl arithmetic proving the widened macro is >=2-use and
    # net-negative (the numbers the S1.6 tooth asserts).
    reg = _reg()
    lf_a, lf_b = {"a": {}}, {"b": {}}
    macro = {"name": "w_two_use", "params": [], "body": [lf_a, lf_b]}
    reg.macro_add("w_two_use", common.canonical_json(macro))
    readings = [{"service": "svc",
                 "statements": [_stmt("s1", lf_a), _stmt("s2", lf_b)]},
                {"service": "svc2",
                 "statements": [_stmt("s1", lf_a), _stmt("s2", lf_b)]}]
    w = corpus_dl(readings, reg.macro_table())
    wo = corpus_dl(readings, {})
    print(f"\nwidened macro: dl_macro={dl_macro(macro)} "
          f"uses={w['reading_uses']['w_two_use']} "
          f"corpus_dl WITH={w['total']} WITHOUT={wo['total']} "
          f"(ablation saves {w['total'] - wo['total']})")
