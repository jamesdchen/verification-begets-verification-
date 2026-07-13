#!/usr/bin/env python3
"""The hard case: certify cross-field semantic constraints that structural
validation (JSON Schema, the tool/lift generators) provably cannot express.

Part A -- certify `book_meeting` (start<end, priority=high => attendees>=2,
etc.) via the constraint-cert contract: PROVE  constraints => invariant  with
Z3 AND CVC5 independently, and check the emitted validator against
Z3-generated boundary inputs.

Part B -- two teeth of different kinds:
  B1 (validator bug):   flip start < end to start <= end. The solver already
     found start == end as the tightest edge, so the boundary differential
     catches it -- a bug blind fuzzing would essentially never hit.
  B2 (false claim):     assert a false invariant (end_hour >= 2). The dual SMT
     proof refutes it -- Z3 and CVC5 both find a counter-model -- so the
     certificate is denied. Testing cannot establish a universal claim; the
     proof does.
"""
from __future__ import annotations

import json
import pathlib

from generators import constraint_model as cm, constraint_gen as cg
import kernel
from kernel.certs import Certificate

SPEC = pathlib.Path("specs/constraints/book_meeting.json").read_text()


def _check(spec_text, files=None):
    m = cm.parse_constraint_spec(spec_text)
    files = files or cg.emit_validator(m)
    return kernel.check({"kind": "constraint-validator", "files": files},
                        {"type": "constraint-cert", "spec_text": spec_text})


def part_a():
    print("== Part A: certify cross-field constraints (proof + solver-boundary) ==")
    v = _check(SPEC)
    ok = isinstance(v, Certificate)
    ch = [(c["backend"], c["result"]) for c in
          (v.channels if ok else v.to_dict()["channels"])]
    print(f"  certified: {ok}  channels={ch}")
    return ok


def part_b1():
    print("\n== Part B1: a validator bug (< -> <=) caught at the solver's edge ==")
    m = cm.parse_constraint_spec(SPEC)
    good = cg.emit_validator(m)["validator.py"].decode()
    bad = good.replace("data['start_hour'] < data['end_hour']",
                       "data['start_hour'] <= data['end_hour']")
    assert bad != good
    v = _check(SPEC, files={"validator.py": bad.encode()})
    caught = not isinstance(v, Certificate)
    t = v.to_dict() if caught else None
    print(f"  buggy validator certified: {not caught}")
    if caught:
        fail = next((c for c in t["channels"] if c["result"] != "pass"), {})
        print(f"    verdict={t['verdict']} caught-by={fail.get('backend')}")
        print(f"    witness: {str(fail.get('transcript', {}).get('error',''))[:220]}")
    return caught


def part_b2():
    print("\n== Part B2: a FALSE invariant refuted by the dual SMT proof ==")
    doc = json.loads(SPEC)
    doc["invariant"] = {"op": ">=", "left": "end_hour", "right": 2}  # false
    spec2 = json.dumps(doc)
    v = _check(spec2)
    caught = not isinstance(v, Certificate)
    t = v.to_dict() if caught else None
    ch = [(c["backend"], c["result"]) for c in t["channels"]] if caught else None
    print(f"  false-invariant contract certified: {not caught}")
    if caught:
        print(f"    verdict={t['verdict']} channels={ch}")
        print("    (z3-invariant and cvc5-invariant both refute "
              "constraints => end_hour>=2)")
    return caught


if __name__ == "__main__":
    a = part_a()
    b1 = part_b1()
    b2 = part_b2()
    print("\nsummary:", json.dumps({"part_a_certified": a,
                                    "part_b1_boundary_catches_bug": b1,
                                    "part_b2_proof_refutes_false_invariant": b2}))
