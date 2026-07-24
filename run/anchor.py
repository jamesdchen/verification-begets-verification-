"""run/anchor.py -- WP-KA builder B6 (the serial INTEGRATOR): the ∃-anchor runner.

This module WIRES the four wave-3 KA pieces the sibling builders authored -- it
imports them, it never edits them:

  * FI-KA-1  ``generators.math_witness.emit_witness_proofs``  -- the deterministic
             witness-template emitter (proposes a closed proof; never certifies).
  * FI-KA-2  ``kernel.verdict_lattice.classify_verdict``      -- the five-point
             honest join of the bounded-shadow and kernel verdicts.
  * FI-KA-3  ``buildloop.anchor_divergence``                  -- the append-only,
             no-auto-resolve divergence adjudicator (the mint-guard).
  * FI-KA-4  ``kernel.certs`` / ``kernel.check`` v12          -- the
             ``exists-anchor-cert`` contract (minted ONLY at ``kernel-proved``).

Per ∃-shaped reading, the runner (the B6 row of ``KA_INTERFACES.md``):

  1. RECOMPUTES the bounded-shadow verdict FRESH from ``math_eval.exists_instances``
     / ``exists_shadow_shape`` at the pipeline bound -- never parsed from a
     committed CSV (FI-KA-2 input contract).
  2. EMITS the witness-proof ladder via ``math_witness.emit_witness_proofs``.
  3. ELABORATE-PROBES the ladder via ``LeanBackend.elaborate`` (RUN 1, untrusted
     preselection only) -- GUARDED, so with Lean absent it honestly skips and the
     reading maps to its shadow column via the lattice.
  4. Submits the first BUILDING variant to ``kernel.check`` under the v12
     ``exists-anchor-cert`` contract (two-run L5 audit + pp-roundtrip + the
     exhaustive template-eval channel) -- the SOLE mint path.
  5. Computes the lattice point via ``verdict_lattice.classify_verdict`` (the
     ``None`` honest-absence return => emit NO anchor row).
  6. BEFORE any mint, calls ``anchor_divergence.assert_no_unresolved``; on a
     T-a / T-b trigger it ``record_divergence`` and NEVER auto-resolves.
  7. Writes ``results/anchor_report.json`` -- deterministic, byte-stable, no
     wall-clock in the body; per-∃-reading ``{source_id, subject_hash,
     lattice_point, shadow, kernel, template?}`` + summary counts.

Lean-absent reality (this container): ``common.lean_available()`` is False, so the
kernel leg honestly does NOT mint -- every emitted reading maps to ``unavailable``
and the lattice sends it to the shadow column (``shadow-certified`` /
``shadow-edge-refused``).  A report is still produced (the Lean-absent lane); the
mint-against-corpus path is separately gated on full-lean green (§12.2), not the
runner's job to fire here.  REPORTED-FIRST (§12.9): this runner and its report are
the ONLY place lattice points aggregate in wave 3 -- no DL, coverage, census, or
admission surface reads them (proved by ``tests/test_anchor_reported_first.py``).
"""
from __future__ import annotations

import json
import pathlib

import common
import kernel
from kernel import verdict_lattice
from kernel.certs import Certificate
from kernel import certs as _certs
from generators.math_reading import parse_math_reading
from generators.math_compile import compile_math_reading
from generators.math_eval import (
    exists_shadow_shape, exists_instances, conclusions_of, eval_pred, eval_term,
    _ranges_for,
)
from generators import math_witness
from buildloop import anchor_divergence

_ROOT = pathlib.Path(__file__).resolve().parent.parent
REPORT_PATH = _ROOT / "results" / "anchor_report.json"
DIVERGENCE_DIR = anchor_divergence.RESULTS_DIR

# The pipeline bound -- the SAME B the bounded shadow certifies (or honestly
# refuses) at.  Source 43 refutes at B=8 (no in-box m > n=8): the §7.2 permanent
# differential.  The bound rides in the search + the v12 cache key, never in proof
# bytes (FI-KA-1).
BOUND = 8

# The frozen report schema tag.
SCHEMA = "anchor-report/v1"

# The two channels of the v12 exists-anchor contract, in frozen order (FI-KA-4).
_KERNEL_BACKEND, _TEMPLATE_BACKEND = _certs.ANCHOR_CERT_CHANNELS


# --------------------------------------------------------------------------- #
# Corpus loading.  The ∃-math-reading corpus is the WP-AUTH authored readings
# (41-44 carry genuine ∃ quantifier statements; the others are ∀-only or None).
# The subject hash is a pure function of the compiled statement's STRUCTURE, so a
# groundedness-satisfying source built from the reading's own quotes yields a
# byte-identical statement/subject to the real pipeline (the quotes gate parse
# ACCEPTANCE only, never the compiled bytes).
# --------------------------------------------------------------------------- #
def _synthetic_source(doc: dict) -> str:
    """A source sentence that satisfies the groundedness gate for ``doc``: every
    demand/presupposition quote occurs verbatim (each is a substring of the join).
    The compiled statement -- hence the subject hash, the shadow, and the emitted
    proof -- is independent of this source, so it is byte-identical to the real
    pipeline's; only ``parse_math_reading``'s quote check consumes it."""
    return "  ".join(s.get("quote", "") for s in doc["statements"] if s.get("quote"))


def _load_reading(doc: dict, source_id: str):
    """Parse one WP-AUTH reading dict into a ``MathReading`` (groundedness
    satisfied by a synthetic source; see ``_synthetic_source``)."""
    return parse_math_reading(json.dumps(doc), _synthetic_source(doc))


def exists_readings():
    """The ∃-shaped reading corpus, sorted by ``source_id``: every authored
    reading whose ``exists_shadow_shape`` is ``supported`` (∀-outer/∃-inner) -- the
    41/42/44 shadow-certifying class AND the 43 honest-edge-refusal class."""
    import wp_auth_readings as _wp
    out = []
    for source_id in sorted(_wp.READINGS):
        doc = _wp.READINGS[source_id]
        if doc is None:                       # honest non-transcribable (e.g. 51)
            continue
        reading = _load_reading(doc, source_id)
        if exists_shadow_shape(reading, bound=None)["mode"] == "supported":
            out.append((source_id, reading))
    return out


def emitter_hash() -> str:
    """sha256 of the FI-KA-1 emitter source -- the ``emitter_hash`` folded into the
    v12 cache identity (a changed emitter is a clean cache MISS, never a stale
    false-green; FI-KA-4 tooth 6).  Single-sourced from the module file."""
    src = pathlib.Path(math_witness.__file__).read_bytes()
    return common.sha256_bytes(src)


# --------------------------------------------------------------------------- #
# (1) the fresh bounded-shadow recompute.
# --------------------------------------------------------------------------- #
def recompute_shadow(reading, *, bound: int = BOUND) -> dict:
    """Recompute the bounded-shadow verdict FRESH at ``bound`` -- never parsed from
    a committed CSV.  Returns ``{"verdict", "bound", "refuting_outer",
    "n_outer_admitted"}`` with ``verdict`` in ``{"pass", "refuted", "skip"}``
    (``skip`` iff the shape's bounded enumeration would exceed the T6b ceiling)."""
    shape = exists_shadow_shape(reading, bound=bound)
    if shape["mode"] != "supported":
        return {"verdict": "skip", "bound": bound,
                "refuting_outer": None, "n_outer_admitted": 0}
    inst = exists_instances(reading, shape["outer"], shape["exists"], bound)
    verdict = "pass" if inst["ok"] else "refuted"
    return {"verdict": verdict, "bound": bound,
            "refuting_outer": inst["witness"],
            "n_outer_admitted": inst["n_outer_admitted"]}


# --------------------------------------------------------------------------- #
# (4-channel-2) the exhaustive template-eval replay -- RECOMPUTED here (never read
# from the emitter's own claim; FI-KA-4 tooth 4: channel 2 is genuinely disjoint,
# tool-independent evidence).  Result "pass" iff the accepted template makes the
# conclusion hold at EVERY admitted outer point (never sampled).
# --------------------------------------------------------------------------- #
def template_eval_channel(reading, template, *, bound: int = BOUND) -> dict:
    """The FI-KA-4 channel 2: an EXHAUSTIVE, tool-independent replay of the
    emitted template over every admitted outer point in the box.  ``result`` is
    ``"pass"`` iff the eval'd template values make the conclusion hold everywhere,
    else ``"fail"`` (a mismatch the kernel adjudication must count)."""
    from generators.math_eval import _canonical_assignments, hypotheses_of
    shape = exists_shadow_shape(reading, bound=bound)
    carrier_of = reading.objects()
    ambient = reading.ambient_carrier()
    concl = conclusions_of(reading)
    hyps = hypotheses_of(reading)
    ok = True
    n_points = 0
    for outer in _canonical_assignments(shape["outer"], carrier_of, bound):
        if not all(eval_pred(p, outer, carrier_of, ambient) for p in hyps):
            continue
        n_points += 1
        asg = dict(outer)
        for name, term in template.items():
            asg[name] = eval_term(term, outer, carrier_of, ambient)
        if concl is not None and not eval_pred(concl, asg, carrier_of, ambient):
            ok = False
            break
    return {"backend": _TEMPLATE_BACKEND, "role": "cross-impl-differential",
            "result": "pass" if ok else "fail",
            "detail": ("exhaustive template-eval replay over %d admitted outer "
                       "points (never sampled)" % n_points)}


def _anchor_contract(*, subject, proof_text, template, discharge, shadow,
                     template_channel):
    """Assemble the v12 ``exists-anchor-cert`` contract dict for ``kernel.check``
    (the FI-KA-4 dispatch shape).  The subject is the RAW ``:= sorry`` statement's
    sha; the emitted proof rides in ``lean_text`` (evidence, never identity); the
    bound/shadow/emitter fold into the cache identity via the shared cdesc."""
    return {"type": _certs.ANCHOR_CERT_TYPE,
            "statement_hash": subject,
            "lean_text": proof_text,
            "template": template,
            "discharge": discharge,
            "shadow": {"verdict": shadow["verdict"], "bound": shadow["bound"]},
            "emitter_hash": emitter_hash(),
            "axioms": (),
            "import_set": list(common.MATHLIB_IMPORTS),
            "mathlib_commit": common.MATHLIB_COMMIT,
            "toolchain": common.LEAN_TOOLCHAIN,
            "template_eval_channel": template_channel}


# --------------------------------------------------------------------------- #
# (3)/(4) the GUARDED elaborate-probe + v12 kernel.check mint leg.
# --------------------------------------------------------------------------- #
def _kernel_leg(reading, subject, emit, shadow, *, bound, divergence_dir):
    """Run the guarded kernel leg for one reading.  Returns
    ``(kernel_verdict, certificate_or_None, transcript_tail)`` with
    ``kernel_verdict`` in ``{"proved", "failed", "unavailable", "not-attempted"}``
    (FI-KA-2's kernel vocabulary).

      * emitter skipped                    -> ``not-attempted`` (nothing to check)
      * ``common.lean_available()`` False  -> ``unavailable``   (Lean-absent lane;
        the probe HONESTLY skips -- no false green without the kernel)
      * Lean present: RUN-1 elaborate-probe preselects the first BUILDING ladder
        variant (untrusted), then -- AFTER the divergence mint-guard -- submits it
        to ``kernel.check`` v12; a ``Certificate`` => ``proved``, else ``failed``.
    """
    if emit["status"] != "emitted":
        return "not-attempted", None, None
    if not common.lean_available():
        # The Lean-absent lane: honest skip.  The lattice maps this reading to its
        # shadow column (unavailable is NEVER kernel-failed).
        return "unavailable", None, None

    # --- Lean-present path (NOT exercised in this container; gated on full-lean
    # green for the first corpus mint, §12.2). -----------------------------------
    from kernel.backends import LeanBackend
    backend = LeanBackend()
    variant = None
    for proof in emit["proofs"]:
        probe = backend.elaborate(proof["lean_text"], expect_sorry=False)
        if probe.get("unavailable"):
            return "unavailable", None, None      # toolchain vanished mid-run
        if probe.get("ok"):
            variant = proof
            break
    if variant is None:
        # v13 (PLAN_REFLECT S4b): the REFLECTION route, incumbent-last -- the
        # ladder stays first so every previously-minting reading mints
        # byte-identically; reflection catches what the ladder cannot close.
        # The probe is the lane-tested shadow discharge record (FgReflect's
        # checkAll_witness, rfl per box point); its claim rides route-
        # qualified as reflection/checkAll_witness (ANCHOR_LIVE_DISCHARGES).
        from run import reflect_shadow
        rec = reflect_shadow.discharge_reflection(
            reading, "checkAll_witness", bound=bound)
        if rec["status"] == "proposed":
            probe = backend.elaborate(rec["probe"], expect_sorry=False)
            if probe.get("unavailable"):
                return "unavailable", None, None
            if probe.get("ok"):
                variant = {"lean_text": rec["probe"],
                           "discharge": rec["route"]}
    if variant is None:
        return "failed", None, ("no building ladder variant and no reflection "
                                "discharge (run-1 preselection)")

    # (6) THE MINT-GUARD -- runs BEFORE kernel.check, so the block is
    # order-independent: an unresolved divergence for this subject refuses the
    # mint regardless of when it was recorded.
    anchor_divergence.assert_no_unresolved(subject, out_dir=divergence_dir)

    template_channel = template_eval_channel(reading, emit["template"], bound=bound)
    contract = _anchor_contract(
        subject=subject, proof_text=variant["lean_text"], template=emit["template"],
        discharge=variant["discharge"], shadow=shadow,
        template_channel=template_channel)
    artifact = {"kind": "exists-anchor-admission", "files": {}}
    result = kernel.check(artifact, contract)
    if isinstance(result, Certificate):
        return "proved", result, None
    return "failed", None, getattr(result, "detail", "kernel.check refused")


# --------------------------------------------------------------------------- #
# (T-a) the in-bound-witness contradiction trigger.  Computed ONLY when the kernel
# proved AND the shadow refuted: if the accepted template's inner values at the
# refuting outer point all lie INSIDE the bounded box, the shadow's exhaustive
# sweep should have found that witness -- a real divergence (one of
# enumerator/evaluator/kernel is wrong).  (T-b needs a Lean `decide` disproof
# during probing; it can only fire on the Lean-present path.)
# --------------------------------------------------------------------------- #
def _in_bound_witness_contradiction(reading, template, shadow, *, bound):
    """Return the T-a witness-eval evidence dict when the trigger fires, else
    ``None``.  Fires iff shadow refuted, a refuting outer point exists, and the
    template's eval'd inner values at that point are ALL inside the bounded box."""
    if shadow["verdict"] != "refuted" or shadow["refuting_outer"] is None:
        return None
    if not template:
        return None
    outer = shadow["refuting_outer"]
    carrier_of = reading.objects()
    ambient = reading.ambient_carrier()
    shape = exists_shadow_shape(reading, bound=bound)
    exists_names = shape["exists"]
    ranges = {n: rg for n, rg in zip(exists_names,
                                     _ranges_for(exists_names, carrier_of, bound))}
    values = {}
    all_in_bound = True
    for name in exists_names:
        v = eval_term(template[name], outer, carrier_of, ambient)
        values[name] = v
        rg = ranges[name]
        if not (rg.start <= v < rg.stop):
            all_in_bound = False
    if not all_in_bound:
        return None                          # out-of-box witness => NOT T-a (43)
    concl = conclusions_of(reading)
    asg = dict(outer)
    asg.update(values)
    holds = concl is None or eval_pred(concl, asg, carrier_of, ambient)
    return {"outer": dict(outer), "template_values": values,
            "in_bound": True, "conclusion_holds_eval": bool(holds)}


# --------------------------------------------------------------------------- #
# The per-reading pipeline (steps 1-6) and the report writer (step 7).
# --------------------------------------------------------------------------- #
def evaluate_reading(source_id, reading, *, bound: int = BOUND,
                     divergence_dir=DIVERGENCE_DIR, registry=None):
    """Run steps 1-6 for one ∃-shaped reading.  Returns the report ROW dict, or
    ``None`` for the honest-absence lattice cell (skip × unavailable/not-attempted
    -- emit no anchor row, per FI-KA-2's ``None`` return)."""
    subject = compile_math_reading(reading)["statement_hash"]

    # (1) fresh bounded-shadow recompute.
    shadow = recompute_shadow(reading, bound=bound)

    # (2) emit the witness-proof ladder.
    emit = math_witness.emit_witness_proofs(reading, bound=bound)
    template = emit.get("template") if emit["status"] == "emitted" else None

    # (3)/(4) the guarded kernel leg (Lean-absent => unavailable, honest skip).
    kernel_v, cert, transcript_tail = _kernel_leg(
        reading, subject, emit, shadow, bound=bound, divergence_dir=divergence_dir)

    # (6) divergence stickiness: while an unresolved artifact sits on the subject,
    # the lattice returns `divergent` unconditionally (checked BEFORE any mint).
    unresolved = anchor_divergence.unresolved_divergence(
        subject, out_dir=divergence_dir) is not None

    # (T-a) the concrete contradiction trigger (only when kernel proved & shadow
    # refuted).  T-b is a Lean-present `decide`-disproof signal, absent here.
    contradiction = False
    evidence = None
    witness_eval = None
    if kernel_v == "proved":
        witness_eval = _in_bound_witness_contradiction(
            reading, template, shadow, bound=bound)
        if witness_eval is not None:
            contradiction = True
            evidence = {"trigger": anchor_divergence.TRIGGERS[0]}   # T-a

    # (5) the lattice point (None => honest absence, emit no anchor row).
    lattice_point = verdict_lattice.classify_verdict(
        shadow["verdict"], kernel_v,
        contradiction=contradiction, evidence=evidence,
        unresolved_divergence=unresolved)

    # (6) on a fresh trigger, record the divergence -- append-only, NEVER
    # auto-resolved.  The mint-guard already ran inside _kernel_leg before the
    # cert attempt; recording here (after) still blocks the NEXT mint.
    if contradiction:
        payload = {
            "subject_hash": subject, "source_id": source_id,
            "trigger": evidence["trigger"],
            "shadow": {"verdict": shadow["verdict"], "bound": shadow["bound"],
                       "refuting_outer": shadow["refuting_outer"],
                       "n_outer_admitted": shadow["n_outer_admitted"]},
            "kernel": {"verdict": kernel_v,
                       "cert_id": (cert.cert_id if cert is not None else None),
                       "discharge": (emit["proofs"][0]["discharge"]
                                     if emit["status"] == "emitted" else None),
                       "transcript_tail": transcript_tail or ""},
            "template": template or {},
            "witness_eval": witness_eval,
            "identity": {"certs_version": _certs.CERTS_VERSION,
                         "rung": _certs.ANCHOR_RUNG,
                         "toolchain_hash": common.lean_toolchain_hash(),
                         "mathlib_commit": common.MATHLIB_COMMIT,
                         "driver_hash": _driver_hash(),
                         "emitter_hash": emitter_hash()},
        }
        anchor_divergence.record_divergence(
            payload, out_dir=divergence_dir, registry=registry)

    if lattice_point is None:
        return None                          # honest absence: emit NO anchor row

    row = {"source_id": source_id, "subject_hash": subject,
           "lattice_point": lattice_point,
           "shadow": {"verdict": shadow["verdict"], "bound": shadow["bound"],
                      "refuting_outer": shadow["refuting_outer"],
                      "n_outer_admitted": shadow["n_outer_admitted"]},
           "kernel": {"verdict": kernel_v,
                      "cert_id": (cert.cert_id if cert is not None else None)}}
    if template is not None:
        row["template"] = template
    return row


def _driver_hash() -> str:
    """sha256 of THIS runner's source (the driver identity folded into a recorded
    divergence's provenance -- the ``_driver_hash`` pattern; deterministic)."""
    return common.sha256_bytes(pathlib.Path(__file__).read_bytes())


def build_report(*, bound: int = BOUND, divergence_dir=DIVERGENCE_DIR,
                 registry=None) -> dict:
    """Build the full ∃-anchor report dict (steps 1-6 over the corpus + the
    summary).  Deterministic and pure: no wall-clock, no randomness; the rows are
    sorted by ``source_id`` (``exists_readings`` order)."""
    rows = []
    n_absence = 0
    for source_id, reading in exists_readings():
        row = evaluate_reading(source_id, reading, bound=bound,
                               divergence_dir=divergence_dir, registry=registry)
        if row is None:
            n_absence += 1
        else:
            rows.append(row)

    by_point = {p: 0 for p in verdict_lattice.LATTICE_POINTS}
    by_shadow = {v: 0 for v in verdict_lattice.SHADOW_INPUTS}
    by_kernel = {v: 0 for v in verdict_lattice.KERNEL_INPUTS}
    for r in rows:
        by_point[r["lattice_point"]] += 1
        by_shadow[r["shadow"]["verdict"]] += 1
        by_kernel[r["kernel"]["verdict"]] += 1

    # Count committed, unresolved divergences over the reported subjects.
    n_div = sum(1 for r in rows
                if anchor_divergence.unresolved_divergence(
                    r["subject_hash"], out_dir=divergence_dir) is not None)

    return {
        "schema": SCHEMA,
        "bound": bound,
        "lean_available": bool(common.lean_available()),
        "readings": rows,
        "summary": {
            "n_exists_readings": len(rows) + n_absence,
            "n_anchor_rows": len(rows),
            "n_honest_absence": n_absence,
            "by_lattice_point": by_point,
            "by_shadow": by_shadow,
            "by_kernel": by_kernel,
            "n_unresolved_divergences": n_div,
        },
    }


def render_json(report: dict) -> str:
    """Serialize the report to canonical, byte-deterministic JSON (sorted keys, no
    wall-clock) -- the committed-artifact form."""
    return common.canonical_json(report) + "\n"


def write_report(*, path=REPORT_PATH, bound: int = BOUND,
                 divergence_dir=DIVERGENCE_DIR) -> pathlib.Path:
    """Build and write ``results/anchor_report.json`` (deterministic, byte-stable).
    Returns the artifact ``Path``.  Regeneration joins the re-baseline-coupled
    artifact set (the WP-DASH coupling-tooth pattern)."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    report = build_report(bound=bound, divergence_dir=divergence_dir)
    path.write_text(render_json(report))
    return path


if __name__ == "__main__":                   # pragma: no cover
    p = write_report()
    print(f"wrote {p}")
