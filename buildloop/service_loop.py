"""Service synthesis loop -- close the flywheel back to the LLM.

The LLM authors ONLY a declarative service meta-spec (a spec, never code) from a
natural-language request.  The spec passes the pure-spec gate
(validate.validate_service_spec), then the deterministic, LLM-free pipeline
certifies it end to end (run.service.certify_service): every tool schema, every
cross-field constraint, the protocol sequencing, and that the composed
dispatcher faithfully ANDs the four certified layers.  On rejection the first
failing layer's machine-checked transcript is fed back and the LLM re-specs
(bounded rounds).  Success yields a whole-service artifact plus its composed
certificate; the code was emitted and checked by trusted machinery, trusted
because it was checked -- not because the LLM produced it.

This is the "verification begets verification" step: the certified library now
turns an English request into practical, whole-service code with a proof.
"""
from __future__ import annotations

import json

from buildloop import llm, validate
from run import service as service_run

MAX_ROUNDS = 5

_PROMPT = """You are the UNTRUSTED proposal engine of a certified generator
bootstrap.  You may ONLY author a declarative JSON service meta-spec (a spec).
Any general-purpose code you emit will be rejected by a validator, and the code
that actually ships is emitted and machine-checked by trusted generators -- your
job is only to describe the service precisely.

Author a service meta-spec for this request:

  {request}

Return ONLY one JSON object (no prose, no code, no fences) with EXACTLY these
keys:

- "name": lowercase identifier (letters/digits/underscore).
- "context": object mapping integer state-variable names to
  {{"type":"integer","init_min":<int>,"init_max":<int>}} -- the mutable
  business state (e.g. an amount due, an auth flag as 0/1).
- "states": a list of >=2 control-state names (the lifecycle).
- "initial": one of the states.
- "tools": a list of tools.  Each tool is BOTH an API call and a protocol
  transition:
    {{"name": <id>,
      "from": <state>, "to": <state>,
      "input_schema": <JSON Schema>,          // the tool's argument contract
      "arg": <name>,                          // OPTIONAL: one integer input the
                                              //   guard/update reads
      "guard": <pred>,                        // OPTIONAL: must hold to fire
      "update": {{<ctxvar>: <expr>, ...}},    // OPTIONAL: state change on fire
      "constraints": <constraint-spec>        // OPTIONAL: cross-field logic
    }}
  input_schema uses ONLY: {{"type":"object","properties":{{...}},
  "required":[...], "additionalProperties":false}}; property types
  string/integer/number/boolean; enum; arrays of a scalar.  If a tool has an
  "arg", that property MUST be an integer in input_schema.
- "safety": {{"when": <state>, "invariant": <pred>}} -- an invariant that must
  hold in every reachable occurrence of that state (this is what the sequencing
  proof establishes; make it a real safety property, e.g. "when shipped, due
  == 0").

The predicate DSL <pred> (integers only):
  {{"op":"<|<=|>|>=|==|!=", "left":<name-or-int>, "right":<name-or-int>}}
  {{"op":"and","preds":[<pred>,...]}}
  {{"op":"implies","if":<pred>,"then":<pred>}}
A guard's names may be the tool's "arg" or any context variable.

The update expr DSL <expr>:
  an int, a context-var name, {{"const":<int>}}, {{"var":<name>}}, or
  {{"op":"+|-","left":<expr>,"right":<expr>}}.

The constraint-spec <constraint-spec> (cross-field logic on the tool's OWN
integer inputs, which JSON Schema cannot express):
  {{"name":<id>,
    "fields":{{<field>:{{"type":"integer"}}, ...}},
    "constraints":[<pred over fields>, ...],
    "invariant":<pred over fields>}}          // must be IMPLIED by the
                                              // constraints (it is PROVEN)
Only add "constraints" to a tool when there is genuine cross-field logic; the
invariant you state will be formally proved to follow from the constraints, so
keep it a true consequence.

Design the states, guards, updates and safety invariant so the protocol is
actually SAFE: no reachable path may violate the safety invariant.
"""


def synthesize_service(request, *, max_rounds=MAX_ROUNDS, model=None,
                       event_sink=None, write_output=True):
    """Turn a natural-language request into a certified whole service.

    Returns {"status": "certified"|"rejected"|"exhausted", ...}."""
    transcripts = []
    total_tokens = 0
    for rnd in range(1, max_rounds + 1):
        prompt = _PROMPT.format(request=request)
        for t in transcripts:
            prompt += ("\n\nYOUR PRIOR META-SPEC WAS NOT CERTIFIED. The checker "
                       f"reported:\n{t[:1800]}\nFix the meta-spec and return only "
                       "the corrected JSON object.")
        resp = llm.call_llm(prompt, model=model)
        total_tokens += resp["input_tokens"] + resp["output_tokens"]
        # gate 1: pure-spec (no code, in the modeled subset)
        try:
            validate.validate_service_spec(resp["text"])
        except validate.SpecViolation as e:
            transcripts.append(f"spec rejected by the pure-spec gate: {e}")
            continue
        spec_text = resp["text"]
        # gate 2: the deterministic, LLM-free certification pipeline
        r = service_run.certify_service(spec_text, event_sink=event_sink,
                                        write_output=write_output)
        if r.ok:
            return {"status": "certified", "rounds": rnd, "name": r.name,
                    "spec": json.loads(spec_text),
                    "layers": [(L["layer"], L["certified"], L["channels"])
                               for L in r.layers],
                    "certificate": r.certificate, "out_dir": r.out_dir,
                    "tokens": total_tokens}
        # localize the failure and feed the machine-checked transcript back
        failed = next((L for L in r.layers if not L["certified"]), None)
        detail = ""
        if failed:
            fail_ch = next((c for c in failed["transcript"]["channels"]
                            if c["result"] != "pass"), {})
            detail = str(fail_ch.get("transcript", {}).get(
                "error", fail_ch.get("detail", "")))[:1200]
        transcripts.append(
            f"layer {r.failed_layer!r} did not certify. channels="
            f"{failed['channels'] if failed else '?'}. witness: {detail}")
    return {"status": "exhausted", "rounds": max_rounds,
            "tokens": total_tokens, "last": transcripts[-1:]}
