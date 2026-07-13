#!/usr/bin/env python3
"""Service composition -- one meta-spec fans out to all four certified
generator families and binds their certificates into a whole-service.

This is where the certified library stops producing isolated snippets and
produces a practical, whole-service artifact: a dispatcher whose every layer
carries a machine-checked certificate, and whose composition is itself checked.

Part A -- certify the `orders` service end to end: four tool schemas
(tool-differential), one cross-field constraint (dual-SMT proof +
solver-boundary), the protocol sequencing (dual BMC, complete), and the
composition (dispatcher vs. an independent reference service + a liveness
witness).  Seven certificates, one service.

Part B1 -- a BROKEN protocol layer (partial payment + no ship guard).  The
orchestrator localizes the failure: the dual BMC proof refutes the sequencing
safety, and the whole-service report names `protocol` as the first failing
layer -- not an opaque "service failed".

Part B2 -- a BROKEN composition: a hand-mutated dispatcher that DROPS the guard
layer (accepts an under-payment).  Each individual layer still certifies in
isolation, but the composition check catches it: the dispatcher-vs-reference
differential finds the trace the mutated dispatcher accepts and the reference
forbids.  Composing certified parts is not free -- the composition needs its
own certificate, and here it earns its keep.
"""
from __future__ import annotations

import json
import pathlib

import kernel
from kernel.certs import Certificate
from generators import service_model, service_gen
from run import service as svc

SPEC = pathlib.Path("specs/services/orders.json").read_text()


def part_a():
    print("== Part A: certify the whole `orders` service (7 layers) ==")
    r = svc.certify_service(SPEC, write_output=True)
    for L in r.layers:
        print(f"  {'OK' if L['certified'] else 'XX'} {L['layer']:<28} "
              f"{L['channels']}")
    print(f"  service certified: {r.ok}  ({len(r.layers)} layers) -> {r.out_dir}")
    return r.ok


def part_b1():
    print("\n== Part B1: a BROKEN protocol layer, localized by the composition ==")
    doc = json.loads(SPEC)
    # make `pay` a partial payment with no guarantee, and drop the ship guard's
    # teeth by letting `pay` succeed for any amount -> unpaid orders can ship.
    for t in doc["tools"]:
        if t["name"] == "pay":
            t["guard"] = {"op": ">=", "left": "amount", "right": 0}
            t["update"] = {"due": {"op": "-", "left": {"var": "due"},
                                   "right": {"var": "amount"}}}
    broken = json.dumps(doc)
    r = svc.certify_service(broken, write_output=False)
    caught = (not r.ok)
    print(f"  broken service certified: {r.ok}   first failing layer: "
          f"{r.failed_layer!r}")
    for L in r.layers:
        print(f"  {'OK' if L['certified'] else 'XX'} {L['layer']:<28} "
              f"{L['channels']}")
    return caught and r.failed_layer == "protocol"


def part_b2():
    print("\n== Part B2: a BROKEN composition (dispatcher drops the guard) ==")
    m = service_model.parse_service_spec(SPEC)
    files = service_gen.emit_service(m)
    good = files["service.py"].decode()
    # drop the guard layer: the guard check never fires, so an under-payment
    # (amount < due) is accepted by the dispatcher though the protocol forbids it.
    bad = good.replace(
        'if tr["guard"] is not None and not _pred(tr["guard"], env):',
        'if False:')
    assert bad != good, "mutation did not apply"
    files["service.py"] = bad.encode()
    v = kernel.check({"kind": "service", "files": files},
                     {"type": "service-conformance", "spec_text": SPEC})
    caught = not isinstance(v, Certificate)
    t = v.to_dict() if caught else None
    print(f"  mutated dispatcher certified: {not caught}")
    if caught:
        print(f"    verdict={t['verdict']}  channels="
              f"{[(c['backend'], c['result']) for c in t['channels']]}")
        fail = next((c for c in t["channels"] if c["result"] != "pass"), {})
        err = str(fail.get("transcript", {}).get("error", ""))[:260]
        print(f"    caught-by={fail.get('backend')}  witness: {err}")
    return caught


if __name__ == "__main__":
    a = part_a()
    b1 = part_b1()
    b2 = part_b2()
    print("\nsummary:", json.dumps({
        "part_a_service_certified": a,
        "part_b1_broken_protocol_localized": b1,
        "part_b2_broken_composition_caught": b2}))
