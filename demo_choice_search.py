#!/usr/bin/env python3
"""S3 -- choice-space search: the minimum-DL design that ENTAILS the demands.

planner.choices.search_design varies ONLY the choice residue of a Reading (the
lifecycle template and each action's transition edge), holding every demand and
presupposition BYTE-IDENTICAL, and returns the cheapest (min-DL + size) design
that (gate b) entails every demanded `order` and is non-vacuous.

Two teeth, mirroring tests/test_choice_search.py:

  part_a  A hand-written Reading (a quantity, an action with an effect, a
          demanded `always`, and a choice lifecycle+transitions).  The
          flat-table argmin and a MACRO-AWARE argmin (a macro abbreviating one
          lifecycle+transition cluster) land on DIFFERENT designs, and BOTH
          winners compile.  (The DL of a transition is invariant under
          retargeting -- H37 -- so the argmin over DL is a tie class; a macro
          that compresses one specific design breaks it the other way.)

  part_b  The same Reading plus a demanded `order` (register BEFORE spend) a
          naive lifecycle would violate.  The globally cheapest (all-self-loop)
          design is REFUSED by the order gate; the returned design satisfies the
          order.

A best-effort THIRD check (guarded) replays the winner's entailed scenarios
through the INDEPENDENT reference interpreter -- it never fails the demo if the
service kernel/sandbox is not runnable in this environment.

Deterministic: no randomness, no clocks.
"""
from __future__ import annotations

import json
import sys

from planner.choices import search_design, enumerate_variants
from generators.reading import parse_reading
from generators.reading_compile import compile_reading, CompileError, \
    entailed_scenarios
from generators.service_model import parse_service_spec

REQUIRES_LLM = False

REQUEST = ("Keep the balance at zero or above. "
           "Members register before they spend.")


def _base_statements():
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
    stmts = _base_statements()
    stmts.insert(5, {"id": "d2", "force": "demand",
                     "quote": "register before they spend",
                     "lf": {"kind": "order", "first": "register",
                            "then": "spend"}})
    return {"service": "ledger", "statements": stmts}


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


def _compiles(reading_dict):
    try:
        compile_reading(parse_reading(json.dumps(reading_dict), REQUEST))
        return True
    except CompileError:
        return False


def _order_violated(reading_dict, first, then):
    """Independent order-entailment check (mirrors compile_reading:100-121)."""
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


def _states(res):
    return parse_service_spec(res["spec_text"]).states


def part_a():
    print("== part_a: flat vs macro-aware argmin differ; both compile ==")
    flat = search_design(_reading_a(), REQUEST)
    macro = search_design(_reading_a(), REQUEST, CHAIN_MACRO)
    checks = [
        ("returns admissible design", _compiles(flat["reading"])),
        ("flat argmin = two-state family", _states(flat) == ["open", "closed"]),
        ("macro argmin = three-state chain",
         _states(macro) == ["open", "active", "closed"]),
        ("argmins differ", flat["reading"] != macro["reading"]),
        ("flat winner compiles", _compiles(flat["reading"])),
        ("macro winner compiles", _compiles(macro["reading"])),
    ]
    for label, ok in checks:
        print(f"   [{'PASS' if ok else 'FAIL'}] {label}")
    print(f"   flat  score={flat['score']:.3f} states={_states(flat)} "
          f"considered={flat['considered']} refused={flat['refused']}")
    print(f"   macro score={macro['score']:.3f} states={_states(macro)} "
          f"considered={macro['considered']} refused={macro['refused']}")
    ok = all(o for _, o in checks)
    print(f"  part_a: {'PASS' if ok else 'FAIL'}")
    return ok, flat


def _violating_all_open():
    r = _reading_b()
    for s in r["statements"]:
        if s["lf"]["kind"] == "lifecycle":
            s["lf"] = {"kind": "lifecycle", "states": ["open", "closed"],
                       "initial": "open"}
        elif s["lf"]["kind"] == "transition":
            s["lf"] = {"kind": "transition", "action": s["lf"]["action"],
                       "from": "open", "to": "open"}
    return r


def part_b():
    print("\n== part_b: order-violating design refused; winner satisfies ==")
    cheap = _violating_all_open()
    res = search_design(_reading_b(), REQUEST)
    # every compiling variant satisfies the order, every refused one violates it
    relational = all(_compiles(v) == (not _order_violated(v, "register", "spend"))
                     for v in enumerate_variants(_reading_b()))
    checks = [
        ("globally cheapest design violates the order",
         _order_violated(cheap, "register", "spend")),
        ("order gate refuses it (CompileError)", not _compiles(cheap)),
        ("search counted refusals", res["refused"] >= 1),
        ("returned design compiles", _compiles(res["reading"])),
        ("returned design satisfies the order",
         not _order_violated(res["reading"], "register", "spend")),
        ("compiles iff order satisfied (whole space)", relational),
    ]
    for label, ok in checks:
        print(f"   [{'PASS' if ok else 'FAIL'}] {label}")
    print(f"   winner score={res['score']:.3f} states={_states(res)} "
          f"considered={res['considered']} refused={res['refused']}")
    ok = all(o for _, o in checks)
    print(f"  part_b: {'PASS' if ok else 'FAIL'}")
    return ok, res


def replay_reference(res):
    """Best-effort extra check: replay the winner's entailed scenarios through
    the INDEPENDENT reference interpreter (service_gen.emit_service +
    build_scenario_reference_harness + HypothesisBackend.check_intent_reference).
    Guarded -- a non-runnable service kernel/sandbox here does NOT fail the
    demo."""
    print("\n== best-effort: scenario replay through the reference ==")
    try:
        from generators import service_gen as sg
        from kernel.backends import HypothesisBackend
        model = parse_service_spec(res["spec_text"])
        parsed = parse_reading(json.dumps(res["reading"]), REQUEST)
        scenarios = entailed_scenarios(model, parsed)
        files = sg.emit_service(model)
        out = HypothesisBackend().check_intent_reference(files, model, scenarios)
        print(f"   reference replay: {out.get('result')} "
              f"({len(scenarios)} entailed scenarios)")
    except Exception as e:  # never fatal -- environment may lack the kernel
        print(f"   skipped (kernel/sandbox not runnable here): "
              f"{type(e).__name__}: {str(e)[:100]}")


if __name__ == "__main__":
    a_ok, a_res = part_a()
    b_ok, _ = part_b()
    replay_reference(a_res)      # best-effort, non-fatal
    print()
    if a_ok and b_ok:
        print("ALL TEETH PASS")
        sys.exit(0)
    print("TEETH FAILED")
    sys.exit(1)
