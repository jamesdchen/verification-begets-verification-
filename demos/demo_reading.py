#!/usr/bin/env python3
"""The semantic path: linguistic theory operationalized, with teeth.

Part A -- a hand-written READING of a vague request ("I run a small venue.
Help me not oversell tickets. Nobody may take more than 8 tickets in one
order.") goes down the deterministic pipeline: groundedness gate, dual-solver
demand consistency, compositional compile with provenance, full certification
(global G safety), solver-entailed scenarios.  The provenance chain is printed:
quoted span -> speech-act force -> logical form -> spec element.

Part B -- five teeth, each a distinct kind of misreading:
  B1 a FABRICATED demand (quote not in the request)      -> groundedness gate
  B2 CONTRADICTORY demands (<=8 and >=10)                -> dual-solver unsat
  B3 a CHOICE that overrides a demanded ordering         -> compile refuses
  B4 an INVERTED effect (selling INCREASES stock)        -> dual BMC refutes:
     the protocol proof quantifies over ALL integer arguments (per-call
     constraints live a layer below), so the solver drives the counter
     negative with an argument no real client would send -- the
     over-approximating adversary catches the wrong verb semantics.
  B5 an OMITTED presupposition (no effect at all: the analyst never wrote
     down that selling depletes stock) -- the honest one: every demanded
     obligation holds VACUOUSLY (the counter never moves), the pipeline
     certifies, and only an examiner-style scenario about what the request
     MEANS ("8 left: selling 8 twice must fail") catches it.  Fidelity to the
     written demands and coverage of the unwritten meaning are different
     properties; this is why both evidence channels exist.
"""
from __future__ import annotations

# demos/-layout shim: put the repo root on sys.path so the flat top-level
# modules (common, cgb, ...) resolve under direct execution
# (python3 demos/<name>.py).
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import sys

import kernel
from kernel.certs import Certificate
from generators import reading as rd, reading_compile as rc, service_model as sm
from run import semantic

REQUIRES_LLM = False

REQUEST = ("I run a small venue. Help me not oversell tickets. "
           "Nobody may take more than 8 tickets in one order.")

READING = {
  "service": "tickets",
  "statements": [
    {"id": "s1", "force": "presupposition", "quote": "tickets",
     "lf": {"kind": "quantity", "name": "tickets_left", "min": 0, "max": 100}},
    {"id": "s2", "force": "presupposition", "quote": "oversell",
     "lf": {"kind": "action", "name": "sell", "arg": "count"}},
    {"id": "s3", "force": "presupposition", "quote": "oversell",
     "lf": {"kind": "effect", "action": "sell", "quantity": "tickets_left",
            "op": "dec", "amount": {"arg": "count"}}},
    {"id": "s4", "force": "demand", "quote": "not oversell tickets",
     "lf": {"kind": "always",
            "pred": {"op": ">=", "left": "tickets_left", "right": 0}}},
    {"id": "s5", "force": "demand", "quote": "not oversell tickets",
     "lf": {"kind": "bound", "action": "sell", "left": "count",
            "cmp": "<=", "right": "tickets_left"}},
    {"id": "s6", "force": "demand", "quote": "more than 8 tickets in one order",
     "lf": {"kind": "bound", "action": "sell", "left": "count",
            "cmp": "<=", "right": 8}},
    {"id": "s7", "force": "presupposition", "quote": "take",
     "lf": {"kind": "bound", "action": "sell", "left": "count",
            "cmp": ">=", "right": 1}},
    {"id": "s8", "force": "choice", "quote": "",
     "lf": {"kind": "action", "name": "close_sales"}},
    {"id": "s9", "force": "choice", "quote": "",
     "lf": {"kind": "lifecycle", "states": ["open", "closed"],
            "initial": "open"}},
    {"id": "s10", "force": "choice", "quote": "",
     "lf": {"kind": "transition", "action": "sell", "from": "open",
            "to": "open"}},
    {"id": "s11", "force": "choice", "quote": "",
     "lf": {"kind": "transition", "action": "close_sales", "from": "open",
            "to": "closed"}},
  ]
}


def part_a():
    print("== Part A: Reading -> certified service, with provenance ==")
    r = semantic.certify_reading(REQUEST, json.dumps(READING),
                                 write_output=True)
    for name, ok, ch in r.layers:
        print(f"  {'OK' if ok else 'XX'} {name:<24} {ch}")
    print(f"  certified: {r.ok}  -> {r.out_dir}")
    print("  provenance chain (spec element <- statements <- quotes):")
    stmts = {s["id"]: s for s in READING["statements"]}
    for element, sids in sorted(r.provenance.items()):
        srcs = "; ".join(f"{sid}[{stmts[sid]['force']}]"
                         + (f" {stmts[sid]['quote']!r}"
                            if stmts[sid]["quote"] else "")
                         for sid in sids)
        print(f"    {element:<34} <- {srcs}")
    return r.ok


def _mutate(**kw):
    doc = json.loads(json.dumps(READING))
    return doc


def part_b():
    print("\n== Part B: five kinds of misreading, five distinct catches ==")
    ok = []

    # B1: fabricated demand
    doc = _mutate()
    doc["statements"][3]["quote"] = "guarantee same-day refunds"
    r = semantic.certify_reading(REQUEST, json.dumps(doc), write_output=False)
    print(f"  B1 fabricated demand      caught={not r.ok} stage={r.stage!r}")
    print(f"     {r.error[:110]}")
    ok.append(not r.ok and r.stage == "reading-gate")

    # B2: contradictory demands
    doc = _mutate()
    doc["statements"].append(
        {"id": "sX", "force": "demand", "quote": "more than 8",
         "lf": {"kind": "bound", "action": "sell", "left": "count",
                "cmp": ">=", "right": 10}})
    r = semantic.certify_reading(REQUEST, json.dumps(doc), write_output=False)
    print(f"  B2 contradictory demands  caught={not r.ok} stage={r.stage!r}")
    ok.append(not r.ok and r.stage == "consistency")

    # B3: a choice that overrides a demanded ordering
    doc = _mutate()
    doc["statements"].append(
        {"id": "sO", "force": "demand", "quote": "help me",
         "lf": {"kind": "order", "first": "close_sales", "then": "sell"}})
    r = semantic.certify_reading(REQUEST, json.dumps(doc), write_output=False)
    print(f"  B3 choice vs demand order caught={not r.ok} stage={r.stage!r}")
    print(f"     {r.error[:110]}")
    ok.append(not r.ok and r.stage == "compile")

    # B4: inverted effect (selling INCREASES stock) -> the dual BMC refutes
    # it, because the protocol proof quantifies over ALL integer arguments:
    # a negative count passes the guard and drives the counter negative.
    doc = _mutate()
    doc["statements"][2]["lf"]["op"] = "inc"
    r = semantic.certify_reading(REQUEST, json.dumps(doc), write_output=False)
    b4 = (not r.ok) and r.stage.startswith("protocol")
    print(f"  B4 inverted effect        caught={not r.ok} stage={r.stage!r} "
          f"(BMC's unconstrained-argument adversary)")
    ok.append(b4)

    # B5: OMITTED presupposition -- the analyst never states that selling
    # depletes stock.  Every demanded obligation holds VACUOUSLY (the counter
    # never moves), so the pipeline certifies.  The honest gap: fidelity to
    # the written demands cannot see what was never written.  An examiner
    # scenario about the request's MEANING catches it.
    doc = _mutate()
    doc["statements"] = [s for s in doc["statements"] if s["id"] != "s3"]
    r = semantic.certify_reading(REQUEST, json.dumps(doc), write_output=False)
    print(f"  B5 omitted effect: pipeline alone certifies={r.ok} "
          f"(demands hold vacuously -- the honest gap)")
    examiner = {"scenarios": [
        {"name": "sell_out_then_sell_again", "init": {"tickets_left": 8},
         "seq": [["sell", {"count": 8}], ["sell", {"count": 8}]],
         "expect": [True, False],
         "why": "8 seats exist; selling 8 then 8 again must fail"}]}
    v = kernel.check({"kind": "service", "files": r.files},
                     {"type": "intent-scenarios", "spec_text": r.spec_text,
                      "scenarios_text": json.dumps(examiner)})
    caught = not isinstance(v, Certificate)
    print(f"     examiner scenario catches the vacuous reading: {caught}")
    if caught:
        t = v.to_dict()
        f = next(c for c in t["channels"] if c["result"] != "pass")
        print(f"     witness: "
              f"{str(f.get('transcript', {}).get('error', ''))[:150]}")
    ok.append(r.ok and caught)
    return all(ok)


if __name__ == "__main__":
    a = part_a()
    b = part_b()
    print("\nsummary:", json.dumps({"part_a_certified": a,
                                    "part_b_all_teeth": b}))
    sys.exit(0 if all([a, b]) else 1)
