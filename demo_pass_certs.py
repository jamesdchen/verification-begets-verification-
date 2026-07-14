#!/usr/bin/env python3
"""W6.2 teeth (a) -- PER-PASS certification of the service compiler passes.

`demo_passes.py` showed the passes are byte-preserving and that a defect is
ATTRIBUTABLE to one pass by diffing bundle keys.  This demo goes one step
further: each byte-affecting pass is INDIVIDUALLY machine-checked by its
DESIGNATED EXISTING kernel contract (no new contract type), so a planted defect
in ONE pass's bundle output is REFUSED by THAT pass's certificate while every
other pass still certifies -- pass-level attribution by CERTIFICATE, not just by
byte-diff.

Contract per pass (all Dafny-free -- Z3/CVC5/pydantic/jsonschema):
    pass 2 tool_schema        -> tool-differential  (per emitted tool schema)
    pass 3 constraint         -> constraint-cert    (dual-SMT + solver boundary)
    pass 4 protocol_stack     -> protocol-cert      (emitted TRANSITIONS conform
                                                     to the BMC model / refsim)
    pass 5 obligation_monitor -> monitor-cert       (per obligation; genuine
                                                     no-op when obligations == [])
    pass 7 assemble           -> service-conformance (composed dispatcher)
Passes 1 (parse/normalize) and 6 (adversary/golden) are structural/adversarial
and honestly carry NO single kernel contract -- reported as such.

LLM-free, Dafny-free.  Exercises `orders` (schema+constraint+protocol+
composition; pass 5 a genuine no-op) and `holds` (adds a temporal obligation, so
pass 5's monitor-cert fires).
"""
from __future__ import annotations

import json
import pathlib
import sys

from generators import service_model, service_passes

REQUIRES_LLM = False

ORDERS = pathlib.Path("specs/services/orders.json").read_text()

# `holds`: hold -> settle -> close, with `eventually settle` -- a temporal
# obligation so pass 5 (obligation_monitor) has a monitor-cert to earn.
HOLDS = json.dumps({
    "name": "holds",
    "context": {"held": {"init_min": 0, "init_max": 0}},
    "states": ["shop", "active", "closed"],
    "initial": "shop",
    "tools": [
        {"name": "hold", "from": "shop", "to": "active",
         "input_schema": {"type": "object", "properties": {}, "required": [],
                          "additionalProperties": False},
         "update": {"held": {"op": "+", "left": {"var": "held"}, "right": 1}}},
        {"name": "settle", "from": "active", "to": "active",
         "input_schema": {"type": "object", "properties": {}, "required": [],
                          "additionalProperties": False},
         "guard": {"op": ">=", "left": "held", "right": 1},
         "update": {"held": {"op": "-", "left": {"var": "held"}, "right": 1}}},
        {"name": "close", "from": "active", "to": "closed", "terminal": True,
         "input_schema": {"type": "object", "properties": {}, "required": [],
                          "additionalProperties": False}},
    ],
    "safety": {"when": "*", "invariant": {"op": ">=", "left": "held",
                                          "right": 0}},
    "obligations": [{"id": "o1", "kind": "eventually", "action": "settle"}],
})


def _print(records) -> None:
    for r in records:
        c = {True: "OK", False: "XX", None: "--"}[r["certified"]]
        con = r["contract"] or "(structural)"
        print(f"  [{c}] {r['pass']:<18} {con:<20} {r.get('note', '')}")
        for s in r["subjects"]:
            sc = "OK" if s["certified"] else "XX"
            print(f"          {sc} {s['subject']:<16} {s['channels']}")


def _contracted(records):
    """Records for passes that carry a kernel contract AND had something to
    certify on this model (certified is a real bool, not a no-op None)."""
    return [r for r in records if r["contract"] and r["certified"] is not None]


def part_clean() -> bool:
    print("== Part A: every contract-bearing pass certifies (orders + holds) ==")
    ok = True
    for name, spec in (("orders", ORDERS), ("holds", HOLDS)):
        m = service_model.parse_service_spec(spec)
        print(f"\n-- service `{name}` --")
        recs = service_passes.certify_passes(m)
        _print(recs)
        ok = ok and all(r["certified"] for r in _contracted(recs))
    return ok


def _defect(label, spec, mutate, owner_pass, owner_contract) -> bool:
    print(f"\n== {label} ==")
    m = service_model.parse_service_spec(spec)
    recs = service_passes.certify_passes(m, mutate=mutate)
    by = {r["pass"]: r for r in recs}
    failed = [r for r in _contracted(recs) if not r["certified"]]
    # exactly the owning pass fails; its contract is the designated one; every
    # other contract-bearing pass still certifies.
    only_owner = [r["pass"] for r in failed] == [owner_pass]
    owns = by[owner_pass]["contract"] == owner_contract
    others_ok = all(r["certified"] for r in _contracted(recs)
                    if r["pass"] != owner_pass)
    print(f"  failing pass(es): {[r['pass'] for r in failed]}  "
          f"(owning contract: {by[owner_pass]['contract']})")
    print(f"  every other contract-bearing pass still certifies: {others_ok}")
    ok = only_owner and owns and others_ok
    print(f"  pass-level attribution to `{owner_pass}`: {ok}")
    return ok


def part_attribution() -> bool:
    print("\n== Part B: a defect in ONE pass fails ONLY that pass's cert ==")

    def drop_transition(b):
        b["transitions"] = b["transitions"][1:]        # drop `login`
        return b

    def weaken_constraint(b):
        b["constraints_table"]["pay"] = [               # amount >= 0  ->  >= -5
            {"op": ">=", "left": "amount", "right": -5}]
        return b

    d1 = _defect("Defect 1: pass 4 drops a transition -> protocol-cert refuses",
                 ORDERS, drop_transition, "protocol_stack", "protocol-cert")
    d2 = _defect("Defect 2: pass 3 weakens a constraint -> constraint-cert refuses",
                 ORDERS, weaken_constraint, "constraint", "constraint-cert")
    return d1 and d2


if __name__ == "__main__":
    a = part_clean()
    b = part_attribution()
    print("\nsummary:", json.dumps({
        "part_a_all_contract_passes_certify": a,
        "part_b_pass_level_attribution": b}))
    sys.exit(0 if (a and b) else 1)
