"""S3 choice-space search (planner.choices) -- the teeth.

The search varies ONLY the choice residue of a Reading (lifecycle template +
per-action transition edges), holding every demand/presupposition byte-identical,
and returns the minimum-DL design that (b) entails every demanded order and is
non-vacuous.  These tests pin:

  part_a  -- an admissible design is returned; the flat-table argmin and a
             macro-aware argmin (a macro abbreviating one lifecycle+transition
             cluster) land on DIFFERENT designs, and BOTH winners compile.
  part_b  -- with a demanded `order` a naive lifecycle would violate, the
             globally cheapest (all-self-loop) design is REFUSED by the order
             gate, and the returned design satisfies the order.
  immutability / vacuity -- every enumerated variant leaves the demand/
             presupposition statements byte-identical, and empty-scenario
             variants are discarded (never returned).

z3/cvc5 are available here; ksc/tree-sitter are not, so nothing emits a codec.
Everything is deterministic (no randomness, no clocks).
"""
from __future__ import annotations

import copy
import json

from planner.choices import search_design, enumerate_variants
from generators.reading import parse_reading
from generators.reading_compile import compile_reading, CompileError, \
    entailed_scenarios
from generators.service_model import parse_service_spec


# --- a small synthetic request + its Reading ---------------------------------
# Every demand/presupposition quote below is a verbatim substring of REQUEST
# (groundedness is mechanical -- see generators/reading.py).
REQUEST = ("Keep the balance at zero or above. "
           "Members register before they spend.")


def _base_statements():
    """A hand-written Reading: a quantity, an action with an effect, a demanded
    `always` obligation, and a choice lifecycle + one transition per action.
    The choice tail (lifecycle, register-transition, spend-transition) is
    consecutive at the end so a structural macro can abbreviate it."""
    return [
        {"id": "q1", "force": "presupposition", "quote": "balance",
         "lf": {"kind": "quantity", "name": "balance", "min": 0, "max": 100}},
        {"id": "a1", "force": "presupposition", "quote": "register",
         "lf": {"kind": "action", "name": "register"}},
        {"id": "a2", "force": "presupposition", "quote": "spend",
         "lf": {"kind": "action", "name": "spend", "arg": "amount"}},
        {"id": "e1", "force": "presupposition", "quote": "spend",
         "lf": {"kind": "effect", "action": "spend", "quantity": "balance",
                "op": "dec", "amount": {"arg": "amount"}}},
        {"id": "d1", "force": "demand", "quote": "balance at zero or above",
         "lf": {"kind": "always",
                "pred": {"op": ">=", "left": "balance", "right": 0}}},
        {"id": "c_life", "force": "choice", "quote": "",
         "lf": {"kind": "lifecycle", "states": ["open", "closed"],
                "initial": "open"}},
        {"id": "c_reg", "force": "choice", "quote": "",
         "lf": {"kind": "transition", "action": "register",
                "from": "open", "to": "open"}},
        {"id": "c_spd", "force": "choice", "quote": "",
         "lf": {"kind": "transition", "action": "spend",
                "from": "open", "to": "open"}},
    ]


def _reading_a():
    return {"service": "ledger", "statements": _base_statements()}


def _reading_b():
    """part_b: the same Reading plus a demanded `order` (register BEFORE spend)
    that a naive lifecycle (spend firing from the initial state) would violate."""
    stmts = _base_statements()
    # insert the order demand before the choice tail so the tail stays trailing
    order = {"id": "d2", "force": "demand",
             "quote": "register before they spend",
             "lf": {"kind": "order", "first": "register", "then": "spend"}}
    stmts.insert(5, order)
    return {"service": "ledger", "statements": stmts}


# A macro that abbreviates exactly ONE lifecycle+transition cluster: the
# three-state chain (register: open->active, spend: active->closed).  It matches
# that single variant and no other, so it discounts that design's DL heavily and
# can flip the argmin away from the (otherwise cheaper) two-state family.
CHAIN_MACRO = {
    "chaintail": {
        "name": "chaintail", "params": [],
        "body": [
            {"kind": "lifecycle", "states": ["open", "active", "closed"],
             "initial": "open"},
            {"kind": "transition", "action": "register",
             "from": "open", "to": "active"},
            {"kind": "transition", "action": "spend",
             "from": "active", "to": "closed"},
        ]}}


def _compiles(reading_dict, request=REQUEST):
    """True iff the design compiles (gate b passes -- no CompileError)."""
    try:
        compile_reading(parse_reading(json.dumps(reading_dict), request))
        return True
    except CompileError:
        return False


def _transitions(reading_dict):
    return {s["lf"]["action"]: (s["lf"]["from"], s["lf"]["to"])
            for s in reading_dict["statements"]
            if s["lf"]["kind"] == "transition"}


def _order_violated(reading_dict, first, then):
    """Independent re-implementation of the order-entailment check (mirrors
    reading_compile.compile_reading:100-121): with all `first`-edges removed,
    is `then` enabled in any state reachable from the initial one?"""
    stmts = reading_dict["statements"]
    life = next(s["lf"] for s in stmts if s["lf"]["kind"] == "lifecycle")
    edges = [(s["lf"]["from"], s["lf"]["to"], s["lf"]["action"])
             for s in stmts if s["lf"]["kind"] == "transition"]
    reach, frontier = {life["initial"]}, [life["initial"]]
    while frontier:
        u = frontier.pop()
        for frm, to, a in edges:
            if frm == u and a != first and to not in reach:
                reach.add(to)
                frontier.append(to)
    return any(frm in reach and a == then for frm, to, a in edges)


# ------------------------------------------------------------------ part_a
def test_part_a_returns_admissible_design():
    res = search_design(_reading_a(), REQUEST)
    # an admissible design is returned, with the S3 ledger fields
    assert set(res) >= {"reading", "spec_text", "score", "considered", "refused"}
    assert res["considered"] == len(enumerate_variants(_reading_a()))
    # it compiles (gate b) and is non-vacuous
    parsed = parse_reading(json.dumps(res["reading"]), REQUEST)
    model = parse_service_spec(res["spec_text"])
    assert entailed_scenarios(model, parsed) != []
    assert _compiles(res["reading"])


def test_part_a_flat_and_macro_argmins_differ_both_compile():
    flat = search_design(_reading_a(), REQUEST)                # table = {}
    macro = search_design(_reading_a(), REQUEST, CHAIN_MACRO)  # macro-aware
    # the two objectives land on DIFFERENT designs ...
    assert flat["reading"] != macro["reading"]
    # ... the flat argmin favours the cheaper two-state family ...
    assert parse_service_spec(flat["spec_text"]).states == ["open", "closed"]
    # ... the macro argmin is exactly the three-state chain the macro abbreviates
    assert parse_service_spec(macro["spec_text"]).states == \
        ["open", "active", "closed"]
    assert _transitions(macro["reading"]) == {
        "register": ("open", "active"), "spend": ("active", "closed")}
    # ... and BOTH winners compile (no CompileError).
    assert _compiles(flat["reading"])
    assert _compiles(macro["reading"])


def test_part_a_deterministic():
    a = search_design(_reading_a(), REQUEST)
    b = search_design(_reading_a(), REQUEST)
    assert a["reading"] == b["reading"] and a["score"] == b["score"]


# ------------------------------------------------------------------ part_b
def _violating_all_open():
    """The globally cheapest design by the size proxy: both actions self-loop in
    the initial state (every state name is the short "open"), so spend fires from
    the initial state -- a naive lifecycle that VIOLATES the demanded order."""
    r = _reading_b()
    for s in r["statements"]:
        if s["lf"]["kind"] == "lifecycle":
            s["lf"] = {"kind": "lifecycle", "states": ["open", "closed"],
                       "initial": "open"}
        elif s["lf"]["kind"] == "transition":
            s["lf"] = {"kind": "transition", "action": s["lf"]["action"],
                       "from": "open", "to": "open"}
    return r


def test_part_b_order_violator_refused_returned_design_satisfies():
    cheap = _violating_all_open()
    # the globally cheapest design violates the order (independent check) ...
    assert _order_violated(cheap, "register", "spend")
    # ... so the order gate (b) refuses it (compile raises CompileError).
    assert not _compiles(cheap)

    res = search_design(_reading_b(), REQUEST)
    # the search counted refusals (order-violating variants) ...
    assert res["refused"] >= 1
    # ... and the returned design SATISFIES the order: it compiles ...
    assert _compiles(res["reading"])
    # ... and, by the independent reachability check, never enables spend before
    # register.
    assert not _order_violated(res["reading"], "register", "spend")


def test_part_b_compiles_iff_order_satisfied():
    """The relational property gate (b) enforces: over the WHOLE choice space, a
    variant compiles iff it does not violate the demanded order."""
    for v in enumerate_variants(_reading_b()):
        assert _compiles(v) == (not _order_violated(v, "register", "spend"))


# --------------------------------------------------- immutability / vacuity
def test_demand_presupposition_statements_are_byte_identical():
    reading = _reading_b()
    pinned = {s["id"]: json.dumps(s, sort_keys=True)
              for s in reading["statements"]
              if s["force"] in ("demand", "presupposition")}
    variants = enumerate_variants(reading)
    assert variants  # non-empty choice space
    for v in variants:
        for s in v["statements"]:
            if s["id"] in pinned:
                assert json.dumps(s, sort_keys=True) == pinned[s["id"]], \
                    f"variant mutated pinned statement {s['id']}"


def test_empty_scenario_variants_are_discarded():
    # A concrete vacuous design: nothing fires from the initial state (both
    # actions live inside a three-state lifecycle's later states), so no legal
    # run exists and the demands entail NO scenario.
    vac = _reading_a()
    for s in vac["statements"]:
        if s["lf"]["kind"] == "lifecycle":
            s["lf"] = {"kind": "lifecycle",
                       "states": ["open", "active", "closed"], "initial": "open"}
        elif s["lf"]["kind"] == "transition" and s["lf"]["action"] == "register":
            s["lf"] = {"kind": "transition", "action": "register",
                       "from": "active", "to": "active"}
        elif s["lf"]["kind"] == "transition" and s["lf"]["action"] == "spend":
            s["lf"] = {"kind": "transition", "action": "spend",
                       "from": "active", "to": "closed"}
    # it is a real member of the enumerated choice space ...
    assert any(v == vac for v in enumerate_variants(_reading_a()))
    # ... it compiles, yet its demands entail no scenario ...
    parsed = parse_reading(json.dumps(vac), REQUEST)
    model = parse_service_spec(compile_reading(parsed)[0])
    assert entailed_scenarios(model, parsed) == []
    # ... so the search never returns it (non-vacuity filter discards it).
    assert search_design(_reading_a(), REQUEST)["reading"] != vac


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"ALL {len(tests)} TESTS PASS")
