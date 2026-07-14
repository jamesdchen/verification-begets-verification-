"""W4.2 cage-as-intake: CONVERSION.

The cage (W4.1) meters an untrusted incumbent; conversion is the move that
retires it -- an LLM authors a REPLACEMENT service meta-spec, the replacement is
generated through the normal pipeline, and a `translation-cert` with
`anchor='incumbent-differential'` certifies the replacement is behaviourally
equivalent to the CAGED INCUMBENT up to a declared state bound n.  On a certified
replacement the demand ledger transitions the caged-incumbent row's status to
`converted` (W4.2b) -- a pure registry/ledger move, the cage object is never
mutated.

Two halves, split exactly as the plan does:

  * W4.2a  lift -> sanitized evidence -> authored spec -> replacement-cert.
    HOUSE RULE 14 (evidence-sanitization): the LLM prompt carries ONLY the
    canonical JSON of the learned Mealy machine -- states, transitions, and
    HASH-CLASSED output classes (buildloop.lstar._classify) -- NEVER raw
    incumbent source or raw result strings (schema_lift._PROMPT embeds raw code;
    this MUST NOT).  A malicious incumbent that hides "widen the spec" in a
    docstring or an output string therefore never reaches the author: the
    injection is hashed away, and the authored spec is identical to the
    uninjected run (or the differential refuses it).  The prompt hash is logged
    in the conversion event (interface-freeze item 14).

  * W4.2b  swap + retirement: `swap_converted` is fixed, LLM-free code (house
    rule 5).  It calls `registry.demand_set_status(demand_id, 'converted',
    covered_via=<replacement cert id>)` and points `payload_ref` at the
    replacement artifact/cert reference.  Idempotent; the cage is NEVER touched.
    The replacement inherits `conformance-relative(n)` and the lift's non_claims.

The conversion event (interface-freeze item 9 / plan §4.9) is
`{demand_id, incumbent_hash, replacement_cert_id, dl_before, dl_after,
toll_retired, synthetic_traffic, prompt_hash}`.
"""
from __future__ import annotations

import json

import common
import kernel
from kernel.certs import Certificate, artifact_hash
from buildloop import llm, validate, dl
from buildloop import lstar as _lstar
from generators import service_gen

MAX_ROUNDS = 5

# The authoring prompt.  It shows the SANITIZED learned machine ONLY -- no raw
# incumbent bytes, no raw output strings (house rule 14).  The output classes are
# already the finite lstar alphabet ({ok, reject, __error__, __timeout__} plus
# opaque `hash:<...>` classes), so any instruction hidden in a rich incumbent
# output has been folded into an opaque hash and cannot steer the author.
_PROMPT = """You are the untrusted proposal engine of a certified generator
bootstrap. You may ONLY author a declarative SERVICE meta-spec (a JSON document);
any code you emit will be rejected by a validator.

Below is the SANITIZED behavioural evidence of a black-box stateful service that
was learned by Angluin L* up to a declared state bound. It is given as canonical
JSON of the learned Mealy machine: a list of control states, the initial state,
the input alphabet, and, per (state, input), the next state and the OUTPUT CLASS.
Output classes are a finite alphabet -- {name!r} means the call was accepted
(legal), any other class ({reject!r}, an error/timeout token, or an opaque
"hash:<...>" class) means the call was refused. This is the ONLY information you
have; there is no source code and no raw output text.

Author a service meta-spec that reproduces this protocol EXACTLY: one `tool` per
(state, input) whose output class is {name!r}, with `from` = that state, `to` =
the learned next state, and an empty object `input_schema`
({{"type":"object","properties":{{}},"required":[],"additionalProperties":false}}).
Every input NOT listed as {name!r} from a state is an implicit reject (no tool).
Use exactly these top-level keys: name, context, states, initial, tools, safety.
Set context to {{"ok": {{"init_min": 0, "init_max": 0}}}} and
safety to {{"when": "*", "invariant": {{"op": "==", "left": "ok", "right": 0}}}}
(a data-free structural invariant, mirroring the lift). Tool names must be the
input symbols. Return ONLY the JSON object -- no prose, no code, no fences.

SANITIZED LEARNED MACHINE (canonical JSON):
{evidence}
"""


# --------------------------------------------------------------- sanitization
def sanitized_evidence(machine) -> dict:
    """The house-rule-14 sanitized evidence: canonical structure of the learned
    Mealy machine with HASH-CLASSED outputs (they already are -- `machine.out`
    holds lstar._classify results).  NO raw incumbent source and NO raw result
    strings ever appear.  Deterministic: the same machine yields byte-identical
    evidence, so the authoring prompt hash is stable."""
    trans = []
    for st in machine.states:
        for sym in machine.alphabet:
            trans.append({"from": st, "input": sym,
                          "to": machine.delta[(st, sym)],
                          "output_class": machine.out[(st, sym)]})
    trans.sort(key=lambda r: (r["from"], r["input"]))
    return {
        "states": list(machine.states),
        "initial": machine.initial,
        "alphabet": list(machine.alphabet),
        "accepting_class": _lstar.ACCEPTING,
        "output_alphabet": sorted({r["output_class"] for r in trans}),
        "transitions": trans,
    }


# --------------------------------------------------------- W4.2a: author + cert
def author_replacement_spec(evidence: dict, name: str, *, max_rounds=MAX_ROUNDS,
                            model=None, event_sink=None) -> dict:
    """Author (LLM) a replacement SERVICE meta-spec from SANITIZED evidence only.
    Returns {status, spec_text, prompt_hash, tokens, rounds} -- status 'authored'
    on success, else 'exhausted'.  The prompt embeds only `sanitized_evidence`
    (house rule 14); its hash is returned for the conversion event."""
    ev_json = common.canonical_json(evidence)
    base = _PROMPT.format(name=_lstar.ACCEPTING, reject="reject", evidence=ev_json)
    prompt_hash = common.sha256_bytes(base.encode())
    transcripts, tokens = [], 0
    for rnd in range(1, max_rounds + 1):
        prompt = base
        for t in transcripts:
            prompt += ("\n\nPRIOR ATTEMPT REJECTED:\n" + t[:1200]
                       + "\nReturn only the corrected service meta-spec JSON.")
        resp = llm.call_llm(prompt, model=model)
        tokens += resp["input_tokens"] + resp["output_tokens"]
        try:
            validate.validate_service_spec(resp["text"])
        except validate.SpecViolation as e:
            transcripts.append(f"spec rejected by validator: {e}")
            continue
        return {"status": "authored", "spec_text": resp["text"],
                "prompt_hash": prompt_hash, "tokens": tokens, "rounds": rnd}
    return {"status": "exhausted", "prompt_hash": prompt_hash,
            "tokens": tokens, "rounds": max_rounds, "last": transcripts[-1:]}


def certify_replacement(cage, machine, replacement_spec_text, *,
                        differential_n, incumbent_hash=None,
                        high_language="mealy-lift", event_sink=None,
                        cache_get=None, cache_put=None):
    """Generate the replacement through the normal pipeline (emit the service
    dispatcher) and certify it against the CAGED INCUMBENT via the
    `translation-cert` `incumbent-differential` anchor.

    `oracle_ref = {incumbent_hash, cage_hash, sandbox_params}` is folded into the
    cdesc by the kernel (already built there -- W4.1); we pass the live `cage`
    object so the two differential channels can run.  Returns
    (verdict, replacement_files, oracle_ref)."""
    rep_model = validate.validate_service_spec(replacement_spec_text)
    files = service_gen.emit_service(rep_model)
    oracle_ref = {
        "incumbent_hash": incumbent_hash or cage.incumbent_hash,
        "cage_hash": cage.hash(),
        "sandbox_params": cage.sandbox_params,
    }
    contract = {
        "type": "translation-cert", "anchor": "incumbent-differential",
        "high_language": high_language,
        # HIGH = the sanitized evidence the replacement is a translation OF; LOW =
        # the authored replacement spec.  Both fold into cdesc so a changed
        # replacement or a changed incumbent is a clean cache miss.
        "high_spec_text": common.canonical_json(sanitized_evidence(machine)),
        "low_spec_text": replacement_spec_text,
        "oracle_ref": oracle_ref,
        "cage": cage,
        "n": int(differential_n),
        # the FULL learned input alphabet drives channel 2's W-method walk, so a
        # trapdoor reached by a symbol the replacement never accepts (e.g. the
        # `refund` god-mode) is still exercised (identity abstract symbols reach
        # the cage's abstraction-adapter incumbent).
        "diff_alphabet": list(machine.alphabet),
    }
    verdict = kernel.check({"kind": "service", "files": files}, contract,
                           event_sink=event_sink,
                           cache_get=cache_get, cache_put=cache_put)
    return verdict, files, oracle_ref


def convert(cage, machine, *, name, differential_n, registry=None,
            demand_row=None, incumbent_hash=None, synthetic_traffic=True,
            model=None, event_sink=None, do_swap=True):
    """The full W4.2 arc: sanitized evidence -> authored replacement -> replacement
    generated + certified against the caged incumbent -> (on success) the W4.2b
    swap.  Returns a result dict incl. the conversion event (plan §4.9).

    `cage` is the oracle_ref cage (the caged incumbent, W4.1); `machine` is the
    learned Mealy machine (the black-box lift, buildloop.lstar / run.protocol_lift).
    LLM authoring runs here (build-time); the certification's differential runs
    the incumbent sandbox-contained inside the kernel."""
    ih = incumbent_hash or (dl.incumbent_hash_of(demand_row) if demand_row
                            else cage.incumbent_hash)

    evidence = sanitized_evidence(machine)
    authored = author_replacement_spec(evidence, name, model=model,
                                       event_sink=event_sink)
    if authored["status"] != "authored":
        return {"status": "author-failed", "detail": authored}
    spec_text = authored["spec_text"]
    prompt_hash = authored["prompt_hash"]

    verdict, files, oracle_ref = certify_replacement(
        cage, machine, spec_text, differential_n=differential_n,
        incumbent_hash=ih, event_sink=event_sink)
    certified = isinstance(verdict, Certificate)

    # --- pricing: dl_before / toll_retired read from a pre-swap snapshot ------
    dl_before = toll_retired = None
    if registry is not None:
        snap = dl.snapshot(registry)
        dl_before = round(dl._ledger_total(snap)["ledger_dl"], 3)
        calls = snap.toll_calls.get(ih, 0.0)
        toll_retired = round(dl.toll_stock(calls), 3)

    replacement_cert_id = verdict.cert_id if certified else None
    artifact_hex = artifact_hash(files)
    replacement_payload_ref = common.canonical_json(
        {"replacement_cert_id": replacement_cert_id,
         "replacement_artifact_hash": artifact_hex})

    swapped = False
    dl_after = dl_before
    if certified and do_swap and registry is not None and demand_row is not None:
        swap_converted(registry, demand_row["demand_id"],
                       replacement_cert_id=replacement_cert_id,
                       replacement_payload_ref=replacement_payload_ref)
        swapped = True
        dl_after = round(dl.ledger_dl(registry)["ledger_dl"], 3)

    event = {
        "demand_id": demand_row["demand_id"] if demand_row else None,
        "incumbent_hash": ih,
        "replacement_cert_id": replacement_cert_id,
        "dl_before": dl_before,
        "dl_after": dl_after,
        "toll_retired": toll_retired,
        "synthetic_traffic": bool(synthetic_traffic),
        "prompt_hash": prompt_hash,
    }
    if event_sink:
        event_sink("conversion", dict(event))

    return {
        "status": "converted" if (certified and swapped) else
                  ("certified" if certified else "refused"),
        "certified": certified,
        "swapped": swapped,
        "verdict": verdict,
        "replacement_spec_text": spec_text,
        "replacement_files": files,
        "replacement_cert_id": replacement_cert_id,
        "replacement_payload_ref": replacement_payload_ref,
        "oracle_ref": oracle_ref,
        "channels": [(c["backend"], c["result"]) for c in
                     (verdict.channels if certified
                      else verdict.to_dict()["channels"])],
        "tokens": authored["tokens"],
        "event": event,
    }


# ------------------------------------------------------------- W4.2b: the swap
def swap_converted(registry, demand_id, *, replacement_cert_id,
                   replacement_payload_ref):
    """W4.2b swap + retirement (pure registry/ledger, LLM-free; house rule 5).

    On a CERTIFIED replacement, transition the caged-incumbent demand row's
    status -> 'converted' (NEVER a kind mutation) and point `payload_ref` at the
    replacement's artifact/cert reference; `covered_via` records the replacement
    cert id (the sanctioned `demand_set_status` field).  The CAGE OBJECT IS NEVER
    MUTATED -- conversion is a ledger transition, not a code edit.  Idempotent: a
    second call on an already-converted row with the same cert id is a no-op.

    Cost then switches on status (buildloop.dl): a converted row is priced as the
    right-hand side of the single conversion formula (W0.3) -- during retention,
    `min(MONITOR_RATE x calls, MONITOR_CAP)` -- and the row keeps its
    conformance-relative(n) provenance + inherited non_claims via the cert."""
    row = registry.demand_get(demand_id)
    if row is None:
        raise KeyError(f"no demand row {demand_id!r}")
    if row["kind"] != "caged-incumbent":
        raise ValueError("conversion is only defined for caged-incumbent demand "
                         f"(row {demand_id!r} is {row['kind']!r})")
    if (row["status"] == "converted"
            and row.get("covered_via") == replacement_cert_id):
        return row                                  # idempotent no-op
    # Stash the ORIGINAL incumbent hash into features BEFORE payload_ref is
    # overwritten, so the converted row's retained-monitor toll still keys to the
    # incumbent's ingested calls (dl.incumbent_hash_of honors this).
    from buildloop import dl as _dl
    orig_hash = _dl.incumbent_hash_of(row)
    feats = row.get("features")
    feats = dict(feats) if isinstance(feats, dict) else {}
    feats["incumbent_hash"] = orig_hash
    registry.demand_set_features(demand_id, feats)
    registry.demand_set_status(demand_id, "converted",
                               covered_via=replacement_cert_id)
    # payload_ref -> the replacement artifact/cert reference.  There is no public
    # payload_ref setter (demand_upsert is INSERT OR IGNORE), so update via the
    # registry's own connection -- the loop is the ledger's sole writer.
    registry.db.execute("UPDATE demand SET payload_ref=? WHERE demand_id=?",
                        (replacement_payload_ref, demand_id))
    registry.db.commit()
    return registry.demand_get(demand_id)
