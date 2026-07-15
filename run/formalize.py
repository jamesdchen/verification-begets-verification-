"""The STATEMENT-FIDELITY pipeline: source sentence + MathReading -> fidelity verdict.

The mathematical analogue of ``run/semantic.py: certify_reading``, and the layer
this whole plan exists to add.  Proof checking (F0's kernel cert) verifies
proof-vs-statement; NOTHING in a bare proof pipeline checks statement-vs-text.
THIS module is that missing layer -- it certifies that the compiled Lean
*statement* faithfully transcribes what the source sentence MEANS, using only
Lean-free channels that are decidable arithmetic over the tiny F-G fragment:

    stage 1  math-reading-gate  parse + groundedness (every demand/presupposition
                                quotes the source verbatim; choices quote
                                nothing).  Catches FABRICATION.          [exact]
    stage 2  nonvacuity (F2.1)  the hypothesis set is satisfiable -- else the
                                theorem certifies VACUOUSLY.  Dual-solver
                                (Z3 AND CVC5) with the direction-split discipline
                                (T4): unsat REFUSES only when the Lean-free
                                enumeration channel corroborates; an
                                uncorroborated unsat is a first-class
                                ``mirror-divergence`` event, never a silent
                                refusal.  Catches CONTRADICTORY hypotheses. [proved/checked]
    stage 3  compile            MathReading -> `theorem ... := sorry` with
                                per-element provenance; the compiler's OWN output
                                is re-run through the escape gate (defense in
                                depth).                                    [checked]
    stage 3.5 statement-cert    the deferred F0 kernel cert.  With Lean ABSENT the
             (F0.2)             kernel channel is unavailable, so this returns a
                                NON-certificate -- recorded honestly as
                                ``statement_cert=None`` (deferred), NOT a pipeline
                                failure.  The FIDELITY layer is what runs here.
    stage 4  instances (F2.2)   the k smallest hypothesis-satisfying instances,
                                replayed against THIS compiled statement: every
                                one MUST make the conclusion hold -- a False
                                instance REFUSES with the witness.  Catches WRONG
                                OPERATOR BINDING and SILENT CARRIER NARROWING.
                                Boundary probes are recorded, never refused.  [checked]
    stage 5  examiner (F2.4a)   optional source-blind expectations, replayed
                                against the compiled statement.  DIVERGENCE is a
                                first-class ``formalization-divergence`` event and
                                ``examiner.converged=False`` -- EVIDENCE, never a
                                refusal (L3).  Catches the OMITTED-PRESUPPOSITION
                                gap that every fidelity gate passes.       [evidence]
    stage 6  proof             Lean-gated F0.3; skipped when Lean is absent.

On refusal the result names the stage, so a refinement loop can tell the analyst
exactly which kind of misformalization to fix.  Every Lean-free gate is decidable
arithmetic over the F-G fragment, so all five teeth are caught in pure Python
WITHOUT a Lean toolchain; the kernel cert (F0) is the stronger, deferred layer.
"""
from __future__ import annotations

import dataclasses

import common
import kernel
from kernel.certs import Certificate
from kernel.backends import SmtBackend
from generators.math_reading import (
    parse_math_reading, BadMathReading, FragmentMiss)
from generators.math_compile import compile_math_reading
from generators import math_smt
from generators import math_eval
from buildloop.validate_lean import validate_lean
from buildloop.validate_expectations import (
    validate_expectations, BadExpectations)


@dataclasses.dataclass
class FormalizeResult:
    """Mirrors ``run.semantic.SemanticResult`` (ok, stage, error, layers) and
    EXTENDS it with the statement-fidelity fields (F-B: new names only, never a
    repurpose of an existing one)."""
    ok: bool
    stage: str = ""                 # failing stage when not ok
    error: str = ""
    layers: list = dataclasses.field(default_factory=list)
    # --- statement-fidelity extension --------------------------------------
    lean_text: str = ""
    statement_hash: str = ""
    provenance: dict = dataclasses.field(default_factory=dict)
    boundary_behavior: list = dataclasses.field(default_factory=list)
    statement_cert: object = None   # Certificate, or None when deferred
    examiner: dict = dataclasses.field(default_factory=dict)


# The subject artifact for a statement-cert carries no emitted files: its
# identity is the statement_hash (mirrors tests/test_statement_cert.py).
_LEAN_STATEMENT_ARTIFACT = {"kind": "lean-statement", "files": {}}


def _channels(v):
    """(backend, result) pairs from a Certificate or an ErrorTranscript."""
    chans = v.channels if isinstance(v, Certificate) else v.to_dict()["channels"]
    return [(c.get("backend", ""), c.get("result", "")) for c in chans]


def _sat_verdict(ch: dict) -> str:
    """Map an SmtBackend result (run with ``expect="sat"``) back to the raw
    solver verdict.  With expect='sat': raw ``sat`` -> pass, raw ``unsat`` ->
    fail (a check-sat obligation returns only sat/unsat/unknown), raw
    ``unknown`` -> unknown; an exception -> error."""
    r = ch.get("result")
    if r == "pass":
        return "sat"
    if r == "fail":
        return "unsat"
    return r or "error"                        # "unknown" | "error"


# =============================================================== stage 2
def _nonvacuity(reading, bound, event_sink):
    """F2.1 non-vacuity with the T4 direction split.

    Refuses ONLY when the hypothesis set is contradictory AND the Lean-free
    enumeration channel corroborates.  Dual-solver ``unsat`` without
    corroboration is a first-class ``mirror-divergence`` event (inconclusive,
    never a silent refusal); ``unknown``/enum-only falls to the enumeration
    channel, which refuses only when no bounded world satisfies the hypotheses.
    """
    bounded = bool(math_eval.bounded_nonvacuous(reading, bound=bound))

    if math_smt.smt_representable(reading):
        smt = math_smt.hypotheses_smt(reading)          # not None (representable)
        be = SmtBackend()
        z = be.run_z3(smt, expect="sat")                # locks under common.SMT_LOCK
        c = be.run_cvc5(smt, expect="sat")
        zv, cv = _sat_verdict(z), _sat_verdict(c)
        channels = [("z3", zv), ("cvc5", cv), ("enum-nonvacuous", str(bounded))]

        if zv == "sat" and cv == "sat":
            return {"ok": True, "channels": channels, "error": ""}

        if zv == "unsat" and cv == "unsat":
            if not bounded:
                return {"ok": False, "channels": channels,
                        "error": ("the hypothesis set is contradictory "
                                  "(dual-solver unsat, enumeration-corroborated): "
                                  "no world satisfies every side condition, so the "
                                  "theorem would certify VACUOUSLY")}
            # Dual-unsat WITHOUT Lean-free corroboration: the mirror and the
            # enumeration channel disagree.  A first-class event (F-I), not a
            # refusal -- both descend from the same grammar, so a disagreement
            # is a signal for human eyes, never a green light and never a silent
            # kill (⚠T4).
            if event_sink:
                event_sink("mirror-divergence", {
                    "theorem": reading.theorem, "stage": "nonvacuity",
                    "detail": "dual-solver unsat but a bounded satisfying "
                              "assignment exists (nonvacuity-inconclusive)"})
            return {"ok": True,
                    "channels": channels + [("mirror-divergence",
                                             "nonvacuity-inconclusive")],
                    "error": ""}

        # unknown / error / solver split -> the decidable-enumeration channel.
        if not bounded:
            return {"ok": False, "channels": channels,
                    "error": ("no bounded world satisfies every hypothesis "
                              "(enumeration channel; SMT inconclusive): the "
                              "theorem would certify VACUOUSLY")}
        return {"ok": True, "channels": channels, "error": ""}

    # enum-only (a gcd/coprime hypothesis has no sound SMT rendering) -> the
    # decidable-enumeration channel decides non-vacuity alone.
    channels = [("enum-only", str(bounded))]
    if not bounded:
        return {"ok": False, "channels": channels,
                "error": ("no bounded world satisfies every hypothesis "
                          "(decidable-enumeration channel): the theorem would "
                          "certify VACUOUSLY")}
    return {"ok": True, "channels": channels, "error": ""}


# =============================================================== stage 4
def _instances(reading, bound):
    """F2.2: replay the k smallest hypothesis-satisfying instances against the
    compiled statement; also record boundary behaviour (never a refusal)."""
    insts = math_eval.satisfying_instances(reading, k=5, bound=bound)
    ok, witness = True, None
    for a in insts:
        if not math_eval.conclusion_holds(reading, a):
            ok, witness = False, a
            break

    boundary_behavior = []
    for p in math_eval.boundary_probes(reading, bound=bound):
        a = p["assignment"]
        boundary_behavior.append({
            "assignment": a,
            "hypothesis_id": p.get("hypothesis_id"),
            "holds": bool(math_eval.conclusion_holds(reading, a)),
        })
    # canonical order so the recorded evidence is byte-stable.
    boundary_behavior.sort(key=common.canonical_json)
    return {"ok": ok, "witness": witness, "n_instances": len(insts),
            "boundary_behavior": boundary_behavior}


# =============================================================== stage 5
def _examiner(reading, expectations_json, source_text, boundary_behavior,
              event_sink):
    """F2.4a: replay the SOURCE-BLIND examiner's expectations against the
    compiled statement.  EVIDENCE, never a refusal (L3) -- the examiner neither
    issues nor blocks a certificate.

    A ``positive``/``holds`` expectation must make the conclusion evaluate True.
    A ``boundary``/``fails`` expectation must make the conclusion evaluate False.
    A ``boundary``/``outside`` expectation asserts the point is out of the
    intended claim's scope; convergence means the FORMALIZATION also excludes it
    (its hypotheses do not hold there).  Divergence -- e.g. the examiner marks a
    boundary ``outside`` but the compiled statement's hypotheses still admit it
    (a dropped presupposition), so the statement HOLDS there -- is a first-class
    ``formalization-divergence`` event.
    """
    try:
        doc = validate_expectations(expectations_json, source_text=source_text)
    except BadExpectations as e:
        # The examiner never blocks the cert; a malformed expectation set is
        # recorded as (non-converged) evidence, not a pipeline refusal.
        return {"converged": False, "tier": "", "gate": "refused",
                "error": str(e), "expectations": [], "diverged": []}

    results, diverged = [], []
    for exp in doc["expectations"]:
        a = exp["assignment"]
        kind, expect = exp["kind"], exp["expect"]
        concl = bool(math_eval.conclusion_holds(reading, a))
        hyps = bool(math_eval.hypotheses_hold(reading, a))
        if kind == "positive":                       # expect holds
            converged_i = concl is True
        elif expect == "outside":                    # intent excludes this point
            # convergence: the formalization's guards ALSO exclude it.
            converged_i = hyps is False
        else:                                        # boundary / fails
            converged_i = concl is False
        rec = {"kind": kind, "expect": expect, "assignment": a,
               "conclusion_holds": concl, "hypotheses_hold": hyps,
               "converged": converged_i, "why": exp["why"]}
        results.append(rec)
        if not converged_i:
            diverged.append(rec)

    converged = not diverged
    if not converged and event_sink:
        event_sink("formalization-divergence", {
            "theorem": reading.theorem, "stage": "examiner",
            "diverged": diverged, "boundary_behavior": boundary_behavior})
    return {"converged": converged,
            "tier": "intent-admission" if converged else "",
            "expectations": results, "diverged": diverged}


# =============================================================== the pipeline
def certify_statement(source_text, math_reading_json, *, event_sink=None,
                      cache_get=None, cache_put=None, expectations_json=None,
                      bound=8, source_id=None):
    """Run the statement-fidelity pipeline on one MathReading.  Returns a
    ``FormalizeResult``.

    Every gate here is a Lean-FREE fidelity channel decidable over the F-G
    fragment; the kernel statement-cert (F0.2) is the stronger, deferred layer
    and does NOT issue in a Lean-absent container (recorded honestly, not
    failed).  ``expectations_json`` is the OPTIONAL source-blind examiner
    evidence (never a refusal)."""
    layers = []

    # ---- stage 1: math-reading-gate (groundedness; catches fabrication) -----
    sid = source_id or ("math-source:" + common.sha256_bytes(
        source_text.encode())[:16])
    try:
        reading = parse_math_reading(math_reading_json, source_text)
    except FragmentMiss as e:
        # F4.1: a source construal that does not transcribe into the fragment is
        # DEMAND DATA, not a failure to hide -- log a first-class fragment-miss
        # event (F-I) so the ranking report (cgb.py fragment report) can price
        # frontier growth.  The miss carries the analyst's missing_kind_guess.
        if event_sink:
            event_sink("fragment-miss", {
                "source_id": sid, "span": str(e)[:200],
                "missing_kind_guess": e.missing_kind_guess})
        return FormalizeResult(ok=False, stage="math-reading-gate",
                               error=str(e))
    except BadMathReading as e:
        return FormalizeResult(ok=False, stage="math-reading-gate",
                               error=str(e))
    layers.append(("math-reading-gate", True,
                   [("groundedness", "pass"), ("trichotomy", "pass")]))

    # ---- stage 2: nonvacuity (F2.1 refusal; catches contradictory hyps) -----
    nv = _nonvacuity(reading, bound, event_sink)
    layers.append(("nonvacuity", nv["ok"], nv["channels"]))
    if not nv["ok"]:
        return FormalizeResult(ok=False, stage="nonvacuity", layers=layers,
                               error=nv["error"])

    # ---- stage 3: compile -> `theorem ... := sorry` -------------------------
    compiled = compile_math_reading(reading)
    lean_text = compiled["lean_text"]
    statement_hash = compiled["statement_hash"]
    provenance = compiled["provenance"]
    gate_ok, gate_reason = validate_lean(lean_text)          # defense in depth
    if not gate_ok:
        return FormalizeResult(
            ok=False, stage="compile", layers=layers, lean_text=lean_text,
            statement_hash=statement_hash, provenance=provenance,
            error=("the compiler's OWN output failed the escape gate -- an "
                   f"internal invariant violation: {gate_reason}"))
    layers.append(("compile", True, [("escape-gate", "pass")]))

    # ---- stage 4 data: instances (computed early to fill the fidelity channel)
    inst = _instances(reading, bound)
    boundary_behavior = inst["boundary_behavior"]

    # ---- stage 3.5: statement-cert (F0.2) -- the deferred F0 kernel layer ----
    fidelity_channels = [
        {"backend": "nonvacuity-z3^cvc5+enum", "result": "pass",
         "role": "cross-impl-differential",
         "detail": "hypotheses satisfiable (dual-solver sat / enumeration)"},
        {"backend": "entailed-instances",
         "result": "pass" if inst["ok"] else "fail",
         "role": "behavioral-witness",
         "detail": ("the k smallest hypothesis-satisfying instances all make "
                    "the conclusion hold" if inst["ok"]
                    else f"a satisfying instance refutes the conclusion: "
                         f"{inst['witness']}")},
    ]
    cert_contract = {
        "type": "statement-cert",
        "lean_text": lean_text,
        "statement_hash": statement_hash,
        "fidelity_channels": fidelity_channels,
        "mathlib_commit": common.MATHLIB_COMMIT,
        "toolchain": common.LEAN_TOOLCHAIN,
        "import_set": list(common.MATHLIB_IMPORTS),
        "boundary_behavior": boundary_behavior,
    }
    v = kernel.check(_LEAN_STATEMENT_ARTIFACT, cert_contract,
                     event_sink=event_sink, cache_get=cache_get,
                     cache_put=cache_put)
    if isinstance(v, Certificate):
        statement_cert = v
        layers.append(("statement-cert", True, _channels(v)))
    else:
        # Lean absent -> the kernel channel is unavailable -> honest non-cert.
        # The FIDELITY layer is what runs here; do NOT fail the pipeline (F0 is
        # the deferred layer).  ``common.lean_available()`` gates a real cert.
        statement_cert = None
        layers.append(("statement-cert", None,
                       [("lean-elaborate+lean4checker",
                         "deferred: lean toolchain absent")]))

    # ---- stage 4: instances refusal (F2.2; catches binding/carrier bugs) ----
    layers.append(("instances", inst["ok"],
                   [("smallest-instances", "pass" if inst["ok"] else "fail"),
                    ("n_checked", str(inst["n_instances"]))]))
    if not inst["ok"]:
        return FormalizeResult(
            ok=False, stage="instances", layers=layers, lean_text=lean_text,
            statement_hash=statement_hash, provenance=provenance,
            boundary_behavior=boundary_behavior, statement_cert=statement_cert,
            error=("a hypothesis-satisfying instance refutes the compiled "
                   f"conclusion (wrong binding or narrowed carrier): "
                   f"witness={inst['witness']}"))

    # ---- stage 5: examiner (F2.4a; EVIDENCE, never a refusal) ---------------
    examiner = {}
    if expectations_json is not None:
        examiner = _examiner(reading, expectations_json, source_text,
                             boundary_behavior, event_sink)
        layers.append(("examiner", examiner.get("converged"),
                       [("convergence",
                         "converged" if examiner.get("converged")
                         else "diverged")]))

    # ---- stage 6: proof (Lean-gated F0.3) -- skipped when Lean is absent -----
    # (No layer appended: the proof cert is the deferred kernel-checked tier.)

    return FormalizeResult(
        ok=True, layers=layers, lean_text=lean_text,
        statement_hash=statement_hash, provenance=provenance,
        boundary_behavior=boundary_behavior, statement_cert=statement_cert,
        examiner=examiner)
