"""The semantic path down the tower: request + Reading -> certified service.

Deterministic except for nothing: the LLM is NOT here.  It authors only the
Reading (see generators/reading.py); everything below is the machine:

    stage 1  reading gate      parse + groundedness (quotes occur verbatim;
                               choices quote nothing)                [exact]
    stage 2  consistency       the demand set is satisfiable (Z3 AND CVC5,
                               expect sat)                           [proved]
    stage 3  compile           compositional Reading -> meta-spec with
                               per-element provenance; a chosen lifecycle
                               must entail every demanded ordering   [checked]
    stage 3.5 monitor-cert     per compiled temporal (LTLf) obligation, its
                               certified monitor DFA -- the baked table vs the
                               SMT LTLf semantics (Z3 AND CVC5) plus the
                               independent live-flloat cross-check.  Empty (no
                               layer) for a non-temporal reading.     [proved]
    stage 4  certification     the existing full stack: tool schemas,
                               constraint proofs, global-G BMC safety,
                               composition                           [proved/checked]
    stage 5  entailed          scenarios DERIVED from the demands by the
             scenarios         solver replay on dispatcher AND reference
                               (expectations entailed, not guessed)  [checked]

On failure the result names the stage, so the refinement loop can tell the LLM
exactly which kind of misreading to fix.  The output artifact includes
reading.json and provenance.json: every guard, constraint and invariant in the
shipped service traces back to a quoted span of the request and its
speech-act force.
"""
from __future__ import annotations

import dataclasses
import json

import common
import kernel
from kernel.certs import Certificate
from generators import reading as reading_mod
from generators import reading_compile as rc
from generators import service_model
from run import service as service_run


@dataclasses.dataclass
class SemanticResult:
    ok: bool
    stage: str = ""              # failing stage when not ok
    error: str = ""
    layers: list = dataclasses.field(default_factory=list)
    spec_text: str = ""
    provenance: dict = dataclasses.field(default_factory=dict)
    files: dict = dataclasses.field(default_factory=dict)
    out_dir: str = ""


def _channels(v):
    return [(c["backend"], c["result"]) for c in
            (v.channels if isinstance(v, Certificate) else
             v.to_dict()["channels"])]


def _fail_detail(v):
    t = v.to_dict()
    fail = next((c for c in t["channels"] if c["result"] != "pass"), {})
    return str(fail.get("transcript", {}).get(
        "error", fail.get("detail", "")))[:1200]


def certify_reading(request: str, reading_text: str, *, event_sink=None,
                    cache_get=None, cache_put=None, write_output=True,
                    macro_table=None, on_certified=None):
    """Run the full semantic pipeline on one Reading.  Returns SemanticResult.

    P5.2: `macro_table` (a checker input, LLM-free) lets the Reading use macro
    invocations that expand to concrete statements before the groundedness gate;
    with none, the path is byte-identical to before.

    W0.2: `on_certified(result, cert_id)` -- an optional callable invoked ONLY on
    success, so a caller can persist the certified Reading into the corpus store
    without this module ever importing the registry (house rule 9).  `cert_id`
    is sha256 of the canonical JSON of the successful layer list (a SemanticResult
    issues many certificates; this is the single stable id of the whole run)."""
    layers = []
    # stage 1: reading gate (groundedness is here -- exact string containment)
    try:
        r = reading_mod.parse_reading(reading_text, request,
                                      macro_table=macro_table)
    except reading_mod.BadReading as e:
        return SemanticResult(ok=False, stage="reading-gate", error=str(e))
    layers.append(("reading-gate", True,
                   [("groundedness", "pass"), ("trichotomy", "pass")]))

    # stage 2: demand-set consistency (dual solver, expect sat)
    v = kernel.check({"kind": "reading", "files": {}},
                     {"type": "reading-consistency",
                      "smtlib": rc.demands_smt(r)},
                     event_sink=event_sink, cache_get=cache_get,
                     cache_put=cache_put)
    layers.append(("consistency", isinstance(v, Certificate), _channels(v)))
    if not isinstance(v, Certificate):
        return SemanticResult(ok=False, stage="consistency", layers=layers,
                              error="the demand set is contradictory: "
                                    + _fail_detail(v))

    # stage 3: compositional compile (choices must entail demanded orderings)
    try:
        spec_text, provenance = rc.compile_reading(r)
    except rc.CompileError as e:
        return SemanticResult(ok=False, stage="compile", layers=layers,
                              error=str(e))
    layers.append(("compile", True, [("order-entailment", "pass")]))

    # stage 3.5: monitor-cert -- certify each compiled temporal obligation's
    # LTLf MONITOR DFA (dual channels: the baked table vs the SMT LTLf semantics,
    # Z3 AND CVC5, plus the independent live-flloat cross-check).  This is the
    # layer that turns liveness into safety at the session boundary; it is EMPTY
    # for a non-temporal reading, so that path is byte-identical to before.
    m = service_model.parse_service_spec(spec_text)
    if m.obligations:
        from generators import monitor_gen
        alphabet = [t.name for t in m.tools]
        max_len = max([4] + [int(o["steps"]) for o in m.obligations
                             if o["kind"] == "within"])
        for o in m.obligations:
            params = {k: val for k, val in o.items() if k not in ("id", "kind")}
            mon = monitor_gen.build_monitor(o["kind"], params, alphabet)
            art = {"kind": "monitor",
                   "files": {"monitor.py": mon["monitor.py"],
                             "ref_stepper.py": mon["ref_stepper.py"]}}
            con = {"type": "monitor-cert", "kind": o["kind"], "params": params,
                   "alphabet": alphabet, "max_len": max_len}
            mv = kernel.check(art, con, event_sink=event_sink,
                              cache_get=cache_get, cache_put=cache_put)
            layers.append((f"monitor-cert[{o['id']}]",
                           isinstance(mv, Certificate), _channels(mv)))
            if not isinstance(mv, Certificate):
                return SemanticResult(
                    ok=False, stage="monitor-cert", layers=layers,
                    spec_text=spec_text, provenance=provenance,
                    error="a temporal obligation's monitor DFA did not "
                          "certify: " + _fail_detail(mv))

    # stage 4: the existing certification stack on the compiled spec
    res = service_run.certify_service(spec_text, event_sink=event_sink,
                                      cache_get=cache_get,
                                      cache_put=cache_put,
                                      write_output=write_output)
    layers.extend((L["layer"], L["certified"], L["channels"])
                  for L in res.layers)
    if not res.ok:
        return SemanticResult(ok=False, stage=res.failed_layer, layers=layers,
                              spec_text=spec_text, provenance=provenance,
                              error=res.error)

    # stage 5: entailed scenarios (solver-derived from the demands); `m` is the
    # model parsed above for the monitor-cert stage.
    scs = rc.entailed_scenarios(m, r)
    if scs:
        sc_text = json.dumps({"scenarios": scs})
        v = kernel.check({"kind": "service", "files": res.files},
                         {"type": "intent-scenarios", "spec_text": spec_text,
                          "scenarios_text": sc_text},
                         event_sink=event_sink, cache_get=cache_get,
                         cache_put=cache_put)
        layers.append(("entailed-scenarios", isinstance(v, Certificate),
                       _channels(v)))
        if not isinstance(v, Certificate):
            return SemanticResult(
                ok=False, stage="entailed-scenarios", layers=layers,
                spec_text=spec_text, provenance=provenance,
                error="a demand's entailed expectation is violated: "
                      + _fail_detail(v))

    out_dir = res.out_dir
    if write_output and out_dir:
        od = common.ARTIFACTS / "out" / out_dir.split("/")[-1]
        (od / "reading.json").write_text(reading_text)
        (od / "provenance.json").write_text(json.dumps(provenance, indent=2))
        (od / "request.txt").write_text(request)

    result = SemanticResult(ok=True, layers=layers, spec_text=spec_text,
                            provenance=provenance, files=res.files,
                            out_dir=out_dir)
    if on_certified is not None:
        cert_id = common.sha256_json(
            [[L[0], bool(L[1])] for L in layers])
        on_certified(result, cert_id)
    return result
