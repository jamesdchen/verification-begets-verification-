#!/usr/bin/env python3
"""Phase 1 -- LTLf eventualities + the certified monitor factory.

Liveness ("every hold is eventually settled") becomes SAFETY at the session
boundary: a temporal demand compiles to a certified monitor DFA, the dispatcher
refuses to close a session while the demand is pending, and the whole thing is
dual-checked -- SMT LTLf semantics AND the flloat automaton, never one checker.

Part A -- CERTIFY.  The `holds` service ("every hold must eventually be
settled") certifies end to end: the monitor DFA (monitor-cert: SMT LTLf
agreement Z3&CVC5 + the independent flloat stepper) AND the service (protocol
sequencing safety, the per-demand LTLf obligation dual-BMC, and the composed
dispatcher vs. an independent reference + an obligation-aware liveness witness).

Part B1 -- STRANDING REFUTED.  A `strands` service adds an `abandon` exit that
ends the session but was NOT marked terminal, so the monitor never guards it: a
held item can be abandoned unsettled.  Both solvers refute the "every complete
session settles" obligation and the BMC returns the SHORTEST stranded trace
[hold, abandon].  (Failure class: an unguarded session-ending action.)

Part B2 -- DROPPED WIRING CAUGHT.  A dispatcher with the monitor wiring deleted
(the obligation-layer check short-circuited) accepts a close-while-pending that
the reference refuses; the composition differential catches it on exactly that
trace.  (Failure class: the dispatcher forgets to enforce a certified monitor.)

Part B3 -- MUTATED TABLE CAUGHT.  A single flipped entry in the shipped monitor
table (settle no longer discharges the obligation) is refuted by monitor-cert:
both the SMT LTLf-agreement channel and the flloat cross-check diverge.
(Failure class: the certified monitor artifact is tampered with.)
"""
from __future__ import annotations

# demos/-layout shim: put the repo root on sys.path so the flat top-level
# modules (common, cgb, ...) resolve under direct execution
# (python3 demos/<name>.py).
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pathlib
import sys

import kernel
from kernel.certs import Certificate
from kernel.backends import SmtBackend
from generators import (service_model, service_gen, protocol_model, protocol_gen,
                        monitor_gen, ltlf_smt)
from run import service as svc

REQUIRES_LLM = False

MAX_LEN = 4       # trace-length bound for monitor-cert (named on the certificate)


def _sch(props=None, req=None):
    return {"type": "object", "properties": props or {},
            "required": req or [], "additionalProperties": False}


# The `holds` service: hold an item, settle it (purchase or release -- modelled
# as one settling transition), then close.  The temporal demand is
# `eventually settle`; `close` is a terminal (session-closing) tool.
HOLDS = {
    "name": "holds",
    "context": {"held": {"init_min": 0, "init_max": 0}},
    "states": ["shop", "active", "closed"],
    "initial": "shop",
    "tools": [
        {"name": "hold", "from": "shop", "to": "active", "input_schema": _sch(),
         "update": {"held": {"op": "+", "left": {"var": "held"}, "right": 1}}},
        {"name": "settle", "from": "active", "to": "active", "input_schema": _sch(),
         "guard": {"op": ">=", "left": "held", "right": 1},
         "update": {"held": {"op": "-", "left": {"var": "held"}, "right": 1}}},
        {"name": "close", "from": "active", "to": "closed", "terminal": True,
         "input_schema": _sch()},
    ],
    "safety": {"when": "*", "invariant": {"op": ">=", "left": "held", "right": 0}},
    "obligations": [{"id": "o1", "kind": "eventually", "action": "settle"}],
}

# The `strands` service: `holds` plus an `abandon` exit the author forgot to mark
# terminal, so the monitor does not guard it.
STRANDS = json.loads(json.dumps(HOLDS))
STRANDS["name"] = "strands"
STRANDS["tools"].append(
    {"name": "abandon", "from": "active", "to": "closed", "input_schema": _sch()})


def _monitor_artifact(model, obligation):
    alphabet = [t.name for t in model.tools]
    params = {k: v for k, v in obligation.items() if k not in ("id", "kind")}
    r = monitor_gen.build_monitor(obligation["kind"], params, alphabet)
    art = {"kind": "monitor", "files": {"monitor.py": r["monitor.py"],
                                        "ref_stepper.py": r["ref_stepper.py"]}}
    con = {"type": "monitor-cert", "kind": obligation["kind"], "params": params,
           "alphabet": alphabet, "max_len": MAX_LEN}
    return art, con, r


def _chans(v):
    ch = v.channels if isinstance(v, Certificate) else v.to_dict()["channels"]
    return [(c["backend"], c["result"]) for c in ch]


def part_a():
    print("== Part A: certify the `holds` service (monitor-cert + service) ==")
    m = service_model.parse_service_spec(json.dumps(HOLDS))
    ok = True
    # (1) every temporal demand's monitor DFA
    for o in m.obligations:
        art, con, _r = _monitor_artifact(m, o)
        v = kernel.check(art, con)
        cert = isinstance(v, Certificate)
        ok = ok and cert
        print(f"  {'OK' if cert else 'XX'} monitor-cert[{o['id']}] "
              f"kind={o['kind']} tier={getattr(v, 'tier', '')} "
              f"claims={getattr(v, 'claims', ())}")
        print(f"       channels={_chans(v)}")
    # (2) the whole service: tool schemas, protocol sequencing + LTLf obligation
    #     (dual BMC), and the composed dispatcher (conformance + liveness)
    r = svc.certify_service(json.dumps(HOLDS), write_output=True)
    for L in r.layers:
        print(f"  {'OK' if L['certified'] else 'XX'} {L['layer']:<24} "
              f"{L['channels']}")
    ok = ok and r.ok
    print(f"  -> holds service certified: {r.ok}; monitor(s)+service all green: "
          f"{ok}")
    return ok


def part_b1():
    print("\n== Part B1: a stranding service, refuted by BOTH solvers ==")
    m = service_model.parse_service_spec(json.dumps(STRANDS))
    pm = protocol_model.parse_protocol_spec(m.protocol_spec_text())
    K = protocol_gen.temporal_bound(pm, pm.acyclic_bound()[0])
    o = pm.obligations[0]
    obl = ltlf_smt.protocol_temporal_smtlib(pm, o, K)
    smt = SmtBackend()
    z = smt.run_z3(obl)["result"]        # sat => "fail" (obligation refuted)
    c = smt.run_cvc5(obl)["result"]
    refuted = (z == "fail" and c == "fail")
    ce = protocol_gen.temporal_counterexample(pm, o, K)
    trace = [step[0] for step in ce["trace"]] if ce else None
    print(f"  obligation '{o['id']}' (eventually {o['action']}): "
          f"z3={z} cvc5={c}  (fail == sat == a stranded trace exists)")
    print(f"  shortest stranded trace: {trace}")
    # honest teeth: the shortest stranding is [hold, abandon] -- reaching the
    # unguarded session-ending exit with the obligation still pending.
    ok = refuted and trace == ["hold", "abandon"]
    print(f"  -> stranding refuted by both solvers with shortest trace: {ok}")
    return ok


def part_b2():
    print("\n== Part B2: a dispatcher with the monitor wiring dropped ==")
    m = service_model.parse_service_spec(json.dumps(HOLDS))
    files = service_gen.emit_service(m)
    good = files["service.py"].decode()
    # delete the obligation-layer enforcement: the terminal is no longer refused
    # while a monitor pends, so a held item can be closed unsettled.
    bad = good.replace("if tool in TERMINAL_TOOLS and any(",
                       "if False and any(")
    assert bad != good, "mutation did not apply"
    files["service.py"] = bad.encode()
    v = kernel.check({"kind": "service", "files": files},
                     {"type": "service-conformance", "spec_text": json.dumps(HOLDS)})
    caught = not isinstance(v, Certificate)
    print(f"  mutated dispatcher certified: {not caught}")
    if caught:
        t = v.to_dict()
        fail = next((c for c in t["channels"] if c["result"] != "pass"), {})
        err = str(fail.get("transcript", {}).get("error", ""))[:220]
        print(f"    verdict={t['verdict']}  caught-by={fail.get('backend')}")
        print(f"    witness: {err}")
    print(f"  -> dropped monitor wiring caught by the composition differential: "
          f"{caught}")
    return caught


def part_b3():
    print("\n== Part B3: a mutated monitor table, caught by monitor-cert ==")
    m = service_model.parse_service_spec(json.dumps(HOLDS))
    o = m.obligations[0]
    art, con, r = _monitor_artifact(m, o)
    good = art["files"]["monitor.py"]
    parsed = monitor_gen.parse_monitor_module(good)
    init = parsed["INITIAL"]
    # flip the discharging edge: from the initial state, `settle` no longer moves
    # to the accepting state (it self-loops), so the monitor never discharges.
    acc = sorted(parsed["ACCEPTING"])[0]
    bad = good.replace(
        ("%d: {'close': %d, 'hold': %d, 'settle': %d}"
         % (init, init, init, acc)).encode(),
        ("%d: {'close': %d, 'hold': %d, 'settle': %d}"
         % (init, init, init, init)).encode())
    assert bad != good, "mutation did not apply"
    art["files"]["monitor.py"] = bad
    v = kernel.check(art, con)
    caught = not isinstance(v, Certificate)
    print(f"  mutated table certified: {not caught}")
    if caught:
        print(f"    verdict={v.verdict}  channels={_chans(v)}")
    print(f"  -> mutated monitor table caught by monitor-cert: {caught}")
    return caught


if __name__ == "__main__":
    a = part_a()
    b1 = part_b1()
    b2 = part_b2()
    b3 = part_b3()
    summary = {"part_a_certified": a,
               "part_b1_stranding_refuted": b1,
               "part_b2_dropped_wiring_caught": b2,
               "part_b3_mutated_table_caught": b3}
    print("\nsummary:", json.dumps(summary))
    sys.exit(0 if all(summary.values()) else 1)
