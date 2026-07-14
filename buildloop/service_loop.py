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

import kernel
from kernel.certs import Certificate
from buildloop import llm, validate
from generators import reading, service_model
from run import service as service_run

MAX_ROUNDS = 5
SCN_ATTEMPTS = 2

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

If the request is VAGUE -- it does not name states, tools, fields or numbers --
you must DESIGN them: choose a minimal lifecycle (3-5 states), 2-4 tools with
obvious names, integer abstractions for the quantities the request cares about,
and a safety invariant that captures the request's central "never" or "always".
Prefer the smallest design that makes the request's intent checkable.
"""

_SCN_PROMPT = """You are the untrusted SCENARIO AUTHOR of a certified generator
bootstrap.  You will write behavioural expectations for a service, derived ONLY
from the request below and the tool INTERFACE -- you are deliberately NOT shown
the service's guards, updates, constraints or safety invariant.  Your
expectations are checked against an independently certified implementation; if
your reading of the request and the implementer's reading diverge, the
divergence is surfaced.  So: express what the REQUEST demands, not what you
guess an implementation might do.

REQUEST:
  {request}

TOOL INTERFACE (names, argument schemas, states, initial state, context
variable ranges -- semantics hidden):
  {interface}

Return ONLY one JSON object (no prose, no fences):
  {{"scenarios": [{{"name": <id>,
                   "init": {{<ctxvar>: <int within its range>, ...}},
                   "seq": [[<tool>, {{<arg>: <value>, ...}}], ...],
                   "expect": [<true|false per step>, ...]}}, ...]}}

Rules: 3-8 scenarios; every init must set every context variable; args must
satisfy the tool's input schema when you intend the step to be accepted; include
at least ONE scenario that is a full legal run (all true) and at least ONE step
that the request clearly forbids (false) -- e.g. exceeding a limit, paying too
little, skipping a required step.  Each false step must be something the REQUEST
rules out, not a schema typo.
"""


# The per-kind grammar block is GENERATED from reading.LF_KINDS (the single
# source of truth), not hand-maintained here -- so prompt and validator cannot
# drift.  {grammar} and {request} are literal markers filled by str.replace
# (NOT str.format -- the signatures carry raw JSON braces), see reading_prompt.
_READING_PROMPT = """You are the untrusted SEMANTIC ANALYST of a certified
generator bootstrap.  You do NOT write specifications or code.  You write a
READING: a semantic analysis of the request below, statement by statement.  A
deterministic compiler turns your Reading into a specification; solvers then
prove or refute every obligation you attribute to the text.  Misattribute
nothing: every demand you write is checked to occur VERBATIM in the request.

REQUEST:
  {request}

Return ONLY one JSON object:
  {"service": <lowercase id>,
   "statements": [{"id": <id>, "force": <force>, "quote": <string>,
                   "lf": <logical form>}, ...]}

FORCE (speech-act) -- the heart of the format:
  "demand"         what the text DIRECTS.  quote MUST be an exact substring of
                   the request (case/whitespace-insensitive).  Never paraphrase
                   inside a quote.
  "presupposition" what the text takes for granted (e.g. "oversell"
                   presupposes selling, and selling presupposes stock that
                   decreases).  quote the trigger word/phrase (also verbatim).
  "choice"         design freedom the text leaves open (lifecycle states,
                   which extra fields exist).  quote MUST be "" -- a choice is
                   yours, not the text's.

LOGICAL FORMS (all names lowercase identifiers; each entry is the field
signature followed by the speech-act force it may carry):
{grammar}

Requirements: declare every quantity/action before referring to it; exactly one
lifecycle; one transition per action; at least ONE demanded obligation of any
kind (the request's central directive, quoted) -- a state invariant/precedence
("always"/"order"/"bound") OR a temporal one ("eventually"/"until"/"before"/
"within").  For a temporal obligation (e.g. "must eventually be settled"), model
the owed action as a repeatable transition that does NOT itself leave the
lifecycle, and give the lifecycle a final state entered by a distinct
session-closing action (a transition into a state with no outgoing transitions):
the compiler marks that closing action terminal so the monitor guards it, and
the owed action must be reachable before it.  Keep the Reading MINIMAL -- only
what the request demands or presupposes, plus the fewest choices that make it
runnable.
"""

# per-call prompt keeps only the LAST 2 refinement transcripts, each capped
_READING_TRANSCRIPTS_KEPT = 2
_READING_TRANSCRIPT_CAP = 1800


def _reading_grammar_block():
    """Render the per-kind LF grammar block from reading.LF_KINDS."""
    out = []
    for kind, (sig, force) in reading.LF_KINDS.items():
        out.append(f"  {sig}")
        out.append(f"      (force: {force})")
    return "\n".join(out)


def reading_static_prompt():
    """The reusable Reading prompt scaffold: the grammar block rendered from
    reading.LF_KINDS, with the {request} marker left in place."""
    return _READING_PROMPT.replace("{grammar}", _reading_grammar_block())


def reading_prompt(request, transcripts=()):
    """The per-call Reading prompt: the static scaffold with the request filled
    in and at most the LAST 2 refinement transcripts (each capped) appended."""
    prompt = reading_static_prompt().replace("{request}", request)
    for t in list(transcripts)[-_READING_TRANSCRIPTS_KEPT:]:
        prompt += ("\n\nYOUR PRIOR READING FAILED. The pipeline reported:\n"
                   f"{t[:_READING_TRANSCRIPT_CAP]}\nFix the Reading and return "
                   "only the corrected JSON object.")
    return prompt


def _intent_stage(request, spec_text, m, files, model, event_sink,
                  cache_get, cache_put):
    """The tower's top rung: an INDEPENDENT scenario author derives concrete
    accept/reject expectations from the request and the tool interface only
    (never the spec's guards/updates/constraints/safety), and the kernel checks
    the certified dispatcher AND the independent reference against them.
    Returns (verdict_or_None, tokens_spent, failure_detail)."""
    tokens, gate_feedback = 0, []
    for _ in range(SCN_ATTEMPTS):
        prompt = _SCN_PROMPT.format(request=request,
                                    interface=m.interface_text())
        for g in gate_feedback:
            prompt += (f"\n\nYOUR PRIOR SCENARIOS WERE REJECTED: {g[:800]}\n"
                       "Return only the corrected JSON object.")
        resp = llm.call_llm(prompt, model=model)
        tokens += resp["input_tokens"] + resp["output_tokens"]
        try:
            validate.validate_scenarios(resp["text"], m)
        except validate.SpecViolation as e:
            gate_feedback.append(str(e))
            continue
        v = kernel.check(
            {"kind": "service", "files": files},
            {"type": "intent-scenarios", "spec_text": spec_text,
             "scenarios_text": resp["text"]},
            event_sink=event_sink, cache_get=cache_get, cache_put=cache_put)
        if isinstance(v, Certificate):
            return v, tokens, ""
        t = v.to_dict()
        fail = next((c for c in t["channels"] if c["result"] != "pass"), {})
        detail = str(fail.get("transcript", {}).get(
            "error", fail.get("detail", "")))[:1200]
        if event_sink:
            event_sink("intent-divergence", {
                "request": request[:500], "channels":
                [(c["backend"], c["result"]) for c in t["channels"]],
                "detail": detail})
        return None, tokens, detail
    return None, tokens, ("scenario author could not produce valid scenarios: "
                          + "; ".join(gate_feedback)[:800])


def synthesize_semantic(request, *, max_rounds=MAX_ROUNDS, model=None,
                        event_sink=None, cache_get=None, cache_put=None,
                        write_output=True, examiner=True):
    """The linguistically principled path: the LLM authors only a READING (a
    quoted, force-tagged semantic analysis); the deterministic pipeline
    (run/semantic.py) does everything else.  Failures come back stage-labeled
    -- a misquote, a contradictory demand set, a choice that overrides a
    demand, a certification failure, or a violated entailed expectation -- so
    each round fixes a specific kind of misreading.

    With examiner=True, the independent scenario examiner (the earlier intent
    channel) additionally cross-checks the finished service: entailed scenarios
    cover what the demands SAY; the examiner covers what the analyst may have
    failed to write down at all (coverage, not just fidelity)."""
    from run import semantic as semantic_run
    transcripts = []
    total_tokens = 0
    for rnd in range(1, max_rounds + 1):
        prompt = reading_prompt(request, transcripts)
        resp = llm.call_llm(prompt, model=model)
        total_tokens += resp["input_tokens"] + resp["output_tokens"]
        r = semantic_run.certify_reading(
            request, resp["text"], event_sink=event_sink,
            cache_get=cache_get, cache_put=cache_put,
            write_output=write_output)
        if not r.ok:
            transcripts.append(f"stage {r.stage!r}: {r.error[:1200]}")
            continue
        layers = list(r.layers)
        if examiner:
            m = service_model.parse_service_spec(r.spec_text)
            iv, itok, idetail = _intent_stage(
                request, r.spec_text, m, r.files, model, event_sink,
                cache_get, cache_put)
            total_tokens += itok
            if iv is None:
                transcripts.append(
                    "the Reading compiled and certified, but an independent "
                    "examiner's expectations diverge -- something the request "
                    "demands is missing from your statements: " + idetail)
                continue
            layers.append(("examiner", True,
                           [(c["backend"], c["result"]) for c in iv.channels]))
        spec_doc = json.loads(r.spec_text)
        return {"status": "certified", "rounds": rnd,
                "name": spec_doc.get("name", "service"),
                "reading": json.loads(resp["text"]),
                "spec": spec_doc,
                "provenance": r.provenance, "layers": layers,
                "out_dir": r.out_dir, "tokens": total_tokens}
    return {"status": "exhausted", "rounds": max_rounds,
            "tokens": total_tokens, "last": transcripts[-1:]}


def synthesize_service(request, *, max_rounds=MAX_ROUNDS, model=None,
                       event_sink=None, cache_get=None, cache_put=None,
                       write_output=True, intent=True):
    """Turn a natural-language request into a certified whole service.

    Returns {"status": "certified"|"rejected"|"exhausted", ...}.  The cache
    hooks make refinement cheap: when the LLM fixes one tool across rounds, the
    layers it did not touch hit the certificate cache instead of re-proving.

    With intent=True (the default), a certified spec must additionally match
    INDEPENDENTLY-derived scenario expectations (see _intent_stage) -- the
    dual-checker discipline applied to the language->spec gap itself.  A
    divergence between the two readings of the request is fed back and the spec
    is re-authored: the loop converges the two derivations or exhausts."""
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
                                        cache_get=cache_get, cache_put=cache_put,
                                        write_output=write_output)
        if not r.ok:
            # localize the failure, feed the machine-checked transcript back
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
            continue
        layers = [(L["layer"], L["certified"], L["channels"])
                  for L in r.layers]
        # gate 3: intent -- the independent scenario cross-check
        if intent:
            m = service_model.parse_service_spec(spec_text)
            iv, itok, idetail = _intent_stage(
                request, spec_text, m, r.files, model, event_sink,
                cache_get, cache_put)
            total_tokens += itok
            if iv is None:
                transcripts.append(
                    "the spec CERTIFIED, but an independent reading of the "
                    "request disagrees with its behaviour (intent divergence). "
                    f"Reconcile the spec with the request: {idetail}")
                continue
            layers.append(("intent", True,
                           [(c["backend"], c["result"]) for c in iv.channels]))
        return {"status": "certified", "rounds": rnd, "name": r.name,
                "spec": json.loads(spec_text), "layers": layers,
                "certificate": r.certificate, "out_dir": r.out_dir,
                "tokens": total_tokens}
    return {"status": "exhausted", "rounds": max_rounds,
            "tokens": total_tokens, "last": transcripts[-1:]}
