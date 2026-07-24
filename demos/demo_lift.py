#!/usr/bin/env python3
"""Schema-lift demo: turn a hand-written validator into a certified,
schema-derived one, with the incumbent code as the ground-truth anchor.

Part B (deterministic, no LLM) -- teeth: a correct inferred schema certifies
against the incumbent; a too-loose schema (role as a free string instead of
the enum {admin,user}) is caught by the incumbent differential, because
hypothesis generates a role value the loose schema allows but the incumbent
rejects.

Part A (real LLM) -- the LLM infers the schema from the incumbent code and it
certifies by differential against the incumbent (no external ground truth).
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

from generators import toolgen
import kernel
from kernel.certs import Certificate

REQUIRES_LLM = True  # Part A infers the schema via a live LLM (schema_lift.lift)

INCUMBENT = pathlib.Path("specs/incumbent/create_user.py").read_text()
INCUMBENT_FILES = {"incumbent.py": INCUMBENT.encode()}

CORRECT = json.dumps({
    "title": "create_user", "type": "object",
    "properties": {
        "username": {"type": "string"},
        "age": {"type": "integer"},
        "email": {"type": "string"},
        "role": {"type": "string", "enum": ["admin", "user"]},
    },
    "required": ["username", "age", "role"],
    "additionalProperties": False,
})

LOOSE = json.dumps({  # role is any string -> under-constrained vs incumbent
    "title": "create_user", "type": "object",
    "properties": {
        "username": {"type": "string"},
        "age": {"type": "integer"},
        "email": {"type": "string"},
        "role": {"type": "string"},
    },
    "required": ["username", "age", "role"],
    "additionalProperties": False,
})


def _lift_check(schema_text):
    files = toolgen.emit_pydantic_tool(schema_text)
    return kernel.check(
        {"kind": "tool", "files": files},
        {"type": "tool-lift", "schema_text": schema_text,
         "incumbent_files": INCUMBENT_FILES, "max_examples": 60})


def part_b():
    print("== Part B: incumbent anchor certifies a correct lift, catches a "
          "loose one ==")
    v = _lift_check(CORRECT)
    ok = isinstance(v, Certificate)
    print(f"  correct schema certified against incumbent: {ok}  "
          f"channels={[(c['backend'], c['result']) for c in (v.channels if ok else v.to_dict()['channels'])]}")
    v2 = _lift_check(LOOSE)
    caught = not isinstance(v2, Certificate)
    t = v2.to_dict() if caught else None
    print(f"  loose schema (role not enum) caught by incumbent: {caught}")
    if caught:
        fail = next((c for c in t["channels"] if c["result"] != "pass"), {})
        print(f"    verdict={t['verdict']} caught-by={fail.get('backend')}")
        print(f"    witness: {str(fail.get('transcript', {}).get('error',''))[:220]}")
    return ok and caught


def part_a():
    print("\n== Part A: LLM infers the schema from the incumbent; certified "
          "by differential ==")
    from buildloop import schema_lift
    res = schema_lift.lift(INCUMBENT, "create_user")
    print(f"  status={res['status']} rounds={res.get('rounds')} "
          f"channels={res.get('channels')}")
    if res["status"] == "lifted":
        print("  inferred schema:", json.dumps(res["schema"]))
    return res["status"] == "lifted"


if __name__ == "__main__":
    b = part_b()
    a = part_a()
    print("\nsummary:", json.dumps({"part_b_anchor_has_teeth": b,
                                    "part_a_llm_lift_certified": a}))
    sys.exit(0 if all([b, a]) else 1)
