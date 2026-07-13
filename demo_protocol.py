#!/usr/bin/env python3
"""Protocol / sequencing contracts -- certify that a *sequence* of calls is
safe, which per-message validation cannot express.

Part A -- certify the `order` protocol: prove (Z3 AND CVC5, bounded model
checking, complete because the control graph is acyclic) that no reachable
state ships an unpaid order, and check the emitted session validator against
an independent reference simulator.

Part B1 -- an UNSAFE protocol (partial payment + no ship guard). The dual SMT
proof finds it: both solvers return the shortest illegal trace reaching
`shipped` with `due != 0` -- a sequencing/data bug no per-message schema and
no amount of single-call fuzzing could catch.

Part B2 -- a validator BUG (drops the pay guard). The conformance differential
against the reference simulator catches a trace the buggy validator accepts
but the protocol forbids.
"""
from __future__ import annotations

import json
import pathlib

from generators import protocol_model as pm, protocol_gen as pg
import kernel
from kernel.certs import Certificate

SPEC = pathlib.Path("specs/protocols/order.json").read_text()


def _check(spec_text, files=None):
    m = pm.parse_protocol_spec(spec_text)
    files = files or pg.emit_validator(m)
    return kernel.check({"kind": "protocol-validator", "files": files},
                        {"type": "protocol-cert", "spec_text": spec_text})


def part_a():
    print("== Part A: certify sequencing safety (BMC proof + conformance) ==")
    v = _check(SPEC)
    ok = isinstance(v, Certificate)
    ch = [(c["backend"], c["result"]) for c in
          (v.channels if ok else v.to_dict()["channels"])]
    print(f"  certified: {ok}  channels={ch}")
    return ok


def part_b1():
    print("\n== Part B1: an UNSAFE protocol caught by the dual BMC proof ==")
    doc = json.loads(SPEC)
    doc["actions"][0]["guard"] = {"op": ">=", "left": "amount", "right": 0}
    doc["actions"][0]["update"] = {
        "due": {"op": "-", "left": {"var": "due"}, "right": {"var": "amount"}}}
    spec2 = json.dumps(doc)
    v = _check(spec2)
    caught = not isinstance(v, Certificate)
    t = v.to_dict() if caught else None
    ch = [(c["backend"], c["result"]) for c in t["channels"]] if caught else None
    print(f"  unsafe protocol certified: {not caught}  channels={ch}")
    if caught:
        m2 = pm.parse_protocol_spec(spec2); K, _ = m2.acyclic_bound()
        print("  solver's shortest illegal trace:",
              json.dumps(pg.counterexample(m2, K)))
    return caught


def part_b2():
    print("\n== Part B2: a validator bug (drops the pay guard) caught by "
          "conformance ==")
    m = pm.parse_protocol_spec(SPEC)
    good = pg.emit_validator(m)["validator.py"].decode()
    bad = good.replace("if not (arg >= ctx['due']):", "if not (True):")
    assert bad != good
    v = _check(SPEC, files={"validator.py": bad.encode()})
    caught = not isinstance(v, Certificate)
    t = v.to_dict() if caught else None
    print(f"  buggy validator certified: {not caught}")
    if caught:
        fail = next((c for c in t["channels"] if c["result"] != "pass"), {})
        print(f"    verdict={t['verdict']} caught-by={fail.get('backend')}")
        print(f"    witness: {str(fail.get('transcript', {}).get('error',''))[:240]}")
    return caught


if __name__ == "__main__":
    a = part_a()
    b1 = part_b1()
    b2 = part_b2()
    print("\nsummary:", json.dumps({"part_a_certified": a,
                                    "part_b1_proof_catches_unsafe": b1,
                                    "part_b2_conformance_catches_bug": b2}))
