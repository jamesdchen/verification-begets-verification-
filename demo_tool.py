#!/usr/bin/env python3
"""Tool-contract generator demo.

Part A -- the kernel's tool-differential contract certifies a tool boundary
when the strict Pydantic validator and the independent jsonschema-library
validator agree (round-trip + accept/reject agreement on generated instances).

Part B -- teeth, in the exact shape of a real agent-tool bug.  A "lax"
validator that forgets extra='forbid' ACCEPTS unexpected keys in a tool call
(a genuine injection surface when the caller is an LLM).  It is internally
self-consistent -- it round-trips and accepts every valid call -- so no
single-validator check flags it.  The independent differential against the
jsonschema reference catches it: the schema forbids the extra key, the lax
Pydantic accepts it, the two disagree.
"""
from __future__ import annotations

import json
import pathlib

from generators import toolgen
import kernel
from kernel.certs import Certificate

SCHEMA = pathlib.Path("specs/tools/create_calendar_event.json").read_text()


def part_a():
    print("== Part A: tool-differential certificate (Pydantic == jsonschema) ==")
    files = toolgen.emit_pydantic_tool(SCHEMA)
    v = kernel.check({"kind": "tool", "files": files},
                     {"type": "tool-differential", "schema_text": SCHEMA,
                      "max_examples": 50})
    ok = isinstance(v, Certificate)
    ch = [(c["backend"], c["result"]) for c in
          (v.channels if ok else v.to_dict()["channels"])]
    print(f"  certified: {ok}  channels={ch}")
    return ok


def part_b():
    print("\n== Part B: a lax validator accepts unexpected keys; "
          "the differential catches it ==")
    files = toolgen.emit_pydantic_tool(SCHEMA)
    lax = {name: data.replace(b"extra='forbid'", b"extra='ignore'")
           for name, data in files.items()}
    # the lax validator is self-consistent (round-trips, accepts valid calls)
    v = kernel.check({"kind": "tool", "files": lax},
                     {"type": "tool-differential", "schema_text": SCHEMA,
                      "max_examples": 50})
    caught = not isinstance(v, Certificate)
    t = v.to_dict() if caught else None
    ch = [(c["backend"], c["result"]) for c in
          (t["channels"] if caught else v.channels)]
    print(f"  lax validator certified: {not caught}  channels={ch}")
    if caught:
        fail = next((c for c in t["channels"] if c["result"] != "pass"), {})
        print(f"  verdict={t['verdict']}  caught-by={fail.get('backend')}")
        print(f"  witness: {str(fail.get('transcript', {}).get('error',''))[:200]}")
    return caught


if __name__ == "__main__":
    a = part_a()
    b = part_b()
    print("\nsummary:", json.dumps({"part_a_certified": a,
                                    "part_b_differential_has_teeth": b}))
