"""Schema-lift loop: infer a JSON Schema from incumbent validator code, then
certify the inferred schema by differential against the incumbent.

This is the aggressive boilerplate-elimination move applied to tool
boundaries: turn a hand-written validator into a certified, schema-derived
one, using the *existing code as the ground-truth anchor* (no external oracle
needed).  The LLM authors ONLY the JSON Schema (a spec); the incumbent code is
the input, never something the LLM writes.  The differential against the
incumbent is the oracle; divergence drives refinement (max rounds).  If the
incumbent's contract is inexpressible in the modeled JSON Schema subset (e.g.
cross-field constraints), the differential correctly fails -- a truthful
"cannot certify a faithful schema" outcome, not a silent wrong lift.
"""
from __future__ import annotations

import json

import kernel
from kernel.certs import Certificate
from buildloop import llm, validate
from generators import toolgen

MAX_ROUNDS = 5

_PROMPT = """You are the untrusted proposal engine of a certified generator
bootstrap. You may ONLY author a declarative JSON Schema (a spec); any code
you emit will be rejected by a validator.

Below is an existing hand-written validator `accepts(data) -> bool` for a tool
called {name!r}. Infer the JSON Schema (Draft-7) describing EXACTLY the inputs
it accepts. Use only: an object with properties; property types
string/integer/number/boolean; enum (string or integer values); arrays of a
scalar type; nested objects; a "required" list; and "additionalProperties":
false. Return ONLY the JSON Schema object -- no prose, no code, no fences.

INCUMBENT VALIDATOR:
{code}
"""


def lift(incumbent_src, name, *, max_rounds=MAX_ROUNDS, model=None,
         event_sink=None):
    src = incumbent_src if isinstance(incumbent_src, str) \
        else incumbent_src.decode()
    incumbent_files = {"incumbent.py": src.encode()}
    transcripts = []
    for rnd in range(1, max_rounds + 1):
        prompt = _PROMPT.format(name=name, code=src)
        for t in transcripts:
            prompt += ("\n\nPRIOR ATTEMPT FAILED. The inferred schema "
                       f"disagreed with the incumbent:\n{t[:1500]}\nFix the "
                       "schema and return only the corrected JSON Schema.")
        resp = llm.call_llm(prompt, model=model)
        try:
            validate.validate_inferred_schema(resp["text"])
        except validate.SpecViolation as e:
            transcripts.append(f"schema rejected by validator: {e}")
            continue
        schema_text = resp["text"]
        files = toolgen.emit_pydantic_tool(schema_text)
        v = kernel.check(
            {"kind": "tool", "files": files},
            {"type": "tool-lift", "schema_text": schema_text,
             "incumbent_files": incumbent_files},
            event_sink=event_sink)
        if isinstance(v, Certificate):
            return {"status": "lifted", "rounds": rnd,
                    "schema": json.loads(schema_text),
                    "channels": [(c["backend"], c["result"]) for c in v.channels],
                    "tokens": resp["input_tokens"] + resp["output_tokens"]}
        t = v.to_dict()
        fail = next((c for c in t["channels"] if c["result"] != "pass"), {})
        transcripts.append(str(fail.get("transcript", {}).get(
            "error", fail.get("detail", "")))[:1500])
    return {"status": "exhausted", "rounds": max_rounds,
            "last": transcripts[-1:] }
