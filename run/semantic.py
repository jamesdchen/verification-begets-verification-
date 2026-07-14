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
                    cache_get=None, cache_put=None, write_output=True):
    """Run the full semantic pipeline on one Reading.  Returns SemanticResult."""
    layers = []
    # stage 1: reading gate (groundedness is here -- exact string containment)
    try:
        r = reading_mod.parse_reading(reading_text, request)
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

    # stage 5: entailed scenarios (solver-derived from the demands)
    m = service_model.parse_service_spec(spec_text)
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

    return SemanticResult(ok=True, layers=layers, spec_text=spec_text,
                          provenance=provenance, files=res.files,
                          out_dir=out_dir)
