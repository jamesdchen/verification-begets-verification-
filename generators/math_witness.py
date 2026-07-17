"""FI-KA-1 -- the witness-template emitter (COMPRESSION.md §11.5/§12.2; the
frozen interface `KA_INTERFACES.md` FI-KA-1).

THE FOURTH TRANSLATION.  ``generators/math_reading.py`` freezes one grammar (the
F-G pred/term AST).  Three deterministic siblings already descend from it: the
compiler (``math_compile.py``, source -> Lean statement text), the SMT mirror
(``math_smt.py``), and the direct evaluator (``math_eval.py``).  This is the
FOURTH -- a deterministic *emitter* that, for a bounded-shadow ∃ reading, PROPOSES
a closed Lean proof term (the ∃ witnesses + a tactic-ladder discharge).  It is
LLM-free and Lean-free (E3/L1: nothing here dreams; the emitter is deterministic
code and its output is *proposed*, never certified).  The kernel is the SOLE
certifier -- the runner (B6) probes and submits the emitted text to
``kernel.check``; an emitted term is CHECKED, never TRUSTED because we emitted it.

Read-only imports only (no edits to either file -- they are T6b/F1 property, not
KA's ownership row): from ``generators.math_eval`` the bounded enumerator and the
F-G evaluator; from ``generators.math_compile`` the term renderer ``_render_term``
(imported, NEVER copied, so term rendering can never drift from the compiler) and
``compile_math_reading`` (the statement-cert subject, emitted byte-identically);
from ``buildloop.validate_lean`` the escape gate the emitter runs on its OWN
output (compile-stage convention, ``run/formalize.py:555-562``).

------------------------------------------------------------------------------
WHAT `emit_witness_proofs(reading, *, bound)` DOES (the frozen shape)
------------------------------------------------------------------------------
In scope exactly when ``exists_shadow_shape(reading, bound=None)["mode"] ==
"supported"`` -- the bounded shadow's own ∀-outer/∃-inner class, which includes
both the shadow-certifiable readings (41/42/44-class) AND the honest edge-refusal
class (source 43: shape-supported, gate-refuting).  Shape uses ``bound=None``
DELIBERATELY: an ``exists-domain-too-large`` reading is still shape-eligible for
the kernel channel; its *search* is what gets the ceiling.  Everything else
returns a named honest skip (frozen vocabulary below).

The witness search REUSES the bounded enumerator, full-product semantics, NEVER
k-smallest:

  1. Domain guard -- reuse the T6b constant ``EXISTS_SHADOW_MAX_ASSIGNMENTS``
     read-only (NO new ceiling -- a fresh one would be a tuned constant); an
     over-ceiling search honest-skips ``witness-search-domain-too-large``.
  2. Sweep every hypothesis-admitted outer assignment in the bounded box
     (``_canonical_assignments`` + ``hypotheses_of`` filter -- byte-identical
     semantics to ``exists_instances``' outer walk).  For each, collect the FULL
     set of in-bound witness tuples (``itertools.product`` over ``_ranges_for``,
     ``eval_pred`` on the conclusion) -- the full bounded product, never a
     k-smallest prefix.
  3. Candidate template family (frozen, v1, DATA-DERIVED -- no tuned constants,
     E5/H52).  Per ∃-object a candidate F-G term is one of: a literal from the
     intersection of witnessed position-values; an outer ref matching a witness
     component at every witnessed point; ``x ± c`` with ``c > 0`` from the
     intersection of the per-point difference sets; or a pairwise ``x op x'``
     (``+ - *``) matching a witness component at every witnessed point.  EVERY
     constant is the intersection of observed data -- its provenance is the
     record, not a menu.  Integer division is EXCLUDED in v1 (Int ``ediv``
     convention hazard; declared limitation -- 44 certifies via the shadow and
     does not need this channel).  Joint candidates = cross product over
     ∃-objects, ordered canonically by ``(sum of term sizes, canonical_json)``.
  4. Full-check filter (EXHAUSTIVE, never sampled): a candidate survives iff for
     EVERY admitted outer point in the box -- INCLUDING edge points with no
     in-bound witness (this is the point of the channel) -- substituting the
     eval'd template values into the conclusion yields True under ``eval_pred``.
     Template values may lie outside the box (``eval_term`` is pure-integer,
     unbounded).  Source 43 at B=8: the data-fit literal ``m := 8`` (the {8}
     intersection) FAILS the full check at the edge point n=8 (8 < 8 is False),
     while the difference-intersection survivor ``m := n + 1`` passes there
     (m = 9, out of box, still True) -- the shadow keeps refusing, the emitter
     proposes.
  5. First surviving joint candidate wins (canonical order); none => honest skip.

THE BOUND NEVER ENTERS PROOF BYTES.  ``bound`` parameterizes the search (and the
v12 cache identity, FI-KA-4); the emitted proof bytes carry only reading-derived
names and data-derived witness constants.  Tooth: emitting at B=8 and B=12 yields
BYTE-IDENTICAL proofs; only ``search.bound`` (provenance / cache key) differs.

Frozen skip vocabulary (a skip is NEVER a refutation, never mutates the shadow
verdict, never surfaces as ok=False): ``no-exists-binder``,
``shape-unsupported:<exists_shadow_shape reason>``,
``witness-search-domain-too-large``, ``no-template-found``.

Public API: ``emit_witness_proofs``, ``RUNGS``, ``RUNG``, ``WitnessEmitError``.
"""
from __future__ import annotations

import itertools
import json

from .math_eval import (
    exists_shadow_shape, hypotheses_of, conclusions_of, eval_pred, eval_term,
    _canonical_assignments, _ranges_for, EXISTS_SHADOW_MAX_ASSIGNMENTS,
)
from .math_compile import _render_term, _Ctx, compile_math_reading
from buildloop.validate_lean import validate_lean

__all__ = ["emit_witness_proofs", "RUNGS", "RUNG", "WitnessEmitError"]

# The eval_props ladder order, frozen (KA_INTERFACES.md FI-KA-1).  `native_decide`
# is forbidden by the escape gate and must NEVER appear -- the ladder is pinned to
# exactly these four legal rungs.
RUNGS = ("decide", "omega", "norm_num", "simp")
# The v1 rung tag threaded into search provenance and the v12 cache identity.
RUNG = "exists-anchor/v1"


class WitnessEmitError(Exception):
    """The deterministic emitter produced Lean that fails its OWN escape gate --
    an internal invariant violation, surfaced rather than mis-emitted (the
    ``run/formalize.py`` compile-stage convention: the compiler refuses its own
    gate-failing output).  A gate failure is NOT in the frozen skip vocabulary,
    so it can never be laundered into an honest skip."""


# --------------------------------------------------------------- box sizing
def _box_size(names, carrier_of, bound: int) -> int:
    """The number of in-bound assignments over `names` -- the product of each
    object's range width -- computed from the imported `_ranges_for` so the width
    convention (`Nat` -> B+1, `Int` -> 2B+1) can never drift from the enumerator."""
    n = 1
    for rg in _ranges_for(names, carrier_of, bound):
        n *= len(rg)
    return n


# --------------------------------------------------- witness collection (step 2)
def _collect_witnesses(reading, outer_names, exists_names, bound):
    """Sweep the bounded outer box; return ``(admitted_outers, witnessed)``.

    ``admitted_outers`` is EVERY hypothesis-admitted outer assignment in the box
    (in the enumerator's canonical order, including edge points with no in-bound
    witness -- the full-check needs them).  ``witnessed`` is the subset that HAS
    at least one in-bound witness, paired with the FULL list of witness tuples
    (each a value tuple over ``exists_names``) -- the full bounded product, never
    a k-smallest prefix (§11.6 F1)."""
    carrier_of = reading.objects()
    ambient = reading.ambient_carrier()
    concl = conclusions_of(reading)
    hyps = hypotheses_of(reading)
    inner_ranges = _ranges_for(exists_names, carrier_of, bound)
    admitted_outers = []
    witnessed = []
    for outer in _canonical_assignments(outer_names, carrier_of, bound):
        if not all(eval_pred(p, outer, carrier_of, ambient) for p in hyps):
            continue
        admitted_outers.append(outer)
        tuples = []
        for combo in itertools.product(*inner_ranges):
            asg = dict(outer)
            asg.update(zip(exists_names, combo))
            if eval_pred(concl, asg, carrier_of, ambient):
                tuples.append(combo)
        if tuples:
            witnessed.append((outer, tuples))
    return admitted_outers, witnessed


# ---------------------------------------------- candidate template family (step 3)
def _pair_val(op, o, x, x2):
    if op == "+":
        return o[x] + o[x2]
    if op == "-":
        return o[x] - o[x2]
    return o[x] * o[x2]                                 # "*"


def _object_candidates(j, outer_names, witnessed):
    """The data-derived candidate F-G terms for the ``j``-th ∃-object (frozen v1
    family).  Every constant is the INTERSECTION of observed witness data across
    the witnessed points -- provenance is the record, not a menu (E5/H52).
    ``witnessed`` must be non-empty (the caller skips otherwise)."""
    # per witnessed point: (outer_assignment, {position-j witness values}).
    posvals = [(o, {t[j] for t in tuples}) for (o, tuples) in witnessed]
    cands = []
    seen = set()

    def emit(term):
        key = json.dumps(term, sort_keys=True)
        if key not in seen:
            seen.add(key)
            cands.append(term)

    # (a) literal: c in the intersection of witnessed position-j values.
    common = None
    for _, vals in posvals:
        common = set(vals) if common is None else (common & vals)
    for c in sorted(common):
        emit({"lit": c})

    # (b) outer ref: x whose value is a witness component at EVERY witnessed point.
    for x in outer_names:
        if all(o[x] in vals for o, vals in posvals):
            emit({"ref": x})

    # (c) x + c / x - c with c > 0 from the intersection of per-point difference
    # sets ({w - a(x)} resp. {a(x) - w}).
    for x in outer_names:
        plus = None
        minus = None
        for o, vals in posvals:
            dp = {v - o[x] for v in vals}
            dm = {o[x] - v for v in vals}
            plus = dp if plus is None else (plus & dp)
            minus = dm if minus is None else (minus & dm)
        for c in sorted(v for v in plus if v > 0):
            emit({"op": "+", "args": [{"ref": x}, {"lit": c}]})
        for c in sorted(v for v in minus if v > 0):
            emit({"op": "-", "args": [{"ref": x}, {"lit": c}]})

    # (d) pairwise x op x' (+, -, *) matching a witness component at every point.
    for op in ("+", "-", "*"):
        for x in outer_names:
            for x2 in outer_names:
                if all(_pair_val(op, o, x, x2) in vals for o, vals in posvals):
                    emit({"op": op, "args": [{"ref": x}, {"ref": x2}]})
    return cands


def _term_size(term: dict) -> int:
    """Node count of an F-G term (the canonical-ordering key's first component)."""
    if "ref" in term or "lit" in term:
        return 1
    return 1 + sum(_term_size(a) for a in term["args"])


# ---------------------------------------------------- full-check filter (step 4)
def _template_passes(template, admitted_outers, concl, carrier_of, ambient) -> bool:
    """EXHAUSTIVE full check: True iff for EVERY admitted outer point (including
    edge points with no in-bound witness) the eval'd template values make the
    conclusion hold.  Never sampled -- a k-smallest prefix over the admitted
    points is exactly the mask this must never use (§11.6 F1)."""
    if concl is None:
        return True
    for outer in admitted_outers:
        asg = dict(outer)
        for name, term in template.items():
            asg[name] = eval_term(term, outer, carrier_of, ambient)
        if not eval_pred(concl, asg, carrier_of, ambient):
            return False
    return True


# --------------------------------------------------------- proof-text emission
def _emit_proofs(reading, statement_lean_text, template, outer_names, exists_names):
    """Build the four ladder proofs (one per rung), each the compiled statement
    with ``:= sorry`` replaced by the frozen tactic shape.  Binder order MIRRORS
    the compiler (``math_compile``): leading-∀ (sorted, referenced-but-unbound)
    then the ∀-segment objects in id/listed order for ``intro``; the ∃ witnesses
    in emitted binder order for the anonymous constructor; the hypothesis chain --
    which sits AFTER the ∃ binder in the compiled prop -- introduced last."""
    ctx = _Ctx(ambient=reading.ambient_carrier(), objects=reading.objects())
    q_stmts = sorted(reading.by_kind("quantifier"), key=lambda s: s["id"])
    forall_emitted = []
    exists_emitted = []
    for s in q_stmts:
        objs = s["lf"]["objects"]
        (forall_emitted if s["lf"]["binder"] == "forall"
         else exists_emitted).extend(objs)
    # leading-∀ = outer objects not bound by a ∀ quantifier (referenced-but-unbound
    # free objects); sorted, exactly as the compiler emits them before the ∀
    # segments.  For the ∃-shadow corpus every outer object is ∀-bound, so this is
    # empty -- but it keeps the intro list in lock-step with the compiled binders.
    leading = sorted(set(outer_names) - set(forall_emitted))
    outer_intro = leading + forall_emitted
    refine_terms = [_render_term(template[name], ctx) for name in exists_emitted]
    hyp_ids = [s["id"] for s in
               sorted(reading.by_kind("hypothesis"), key=lambda s: s["id"])]

    assert statement_lean_text.endswith(" := sorry")
    head = statement_lean_text[:-len(" := sorry")]

    proofs = []
    for rung in RUNGS:
        lines = [" := by",
                 "  intro " + " ".join(outer_intro),
                 "  refine ⟨" + ", ".join(refine_terms) + ", ?_⟩"]
        if hyp_ids:
            lines.append("  intro " + " ".join("hyp_" + h for h in hyp_ids))
        lines.append("  " + rung)
        proofs.append({"discharge": rung, "lean_text": head + "\n".join(lines)})
    return proofs


# ------------------------------------------------------------------- the emitter
def emit_witness_proofs(reading, *, bound: int) -> dict:
    """Emit the frozen witness-proof output dict for a bounded-shadow ∃ reading,
    or a named honest skip.  See the module docstring for the full contract."""
    shape = exists_shadow_shape(reading, bound=None)      # pure shape (no guard)
    if shape["mode"] == "forall-only":
        return {"status": "skip", "reason": "no-exists-binder"}
    if shape["mode"] == "unsupported":
        return {"status": "skip", "reason": "shape-unsupported:" + shape["reason"]}

    outer_names = shape["outer"]
    exists_names = shape["exists"]
    carrier_of = reading.objects()

    # step 1: domain guard -- reuse the T6b ceiling read-only (no new constant).
    if (_box_size(outer_names, carrier_of, bound)
            * _box_size(exists_names, carrier_of, bound)
            > EXISTS_SHADOW_MAX_ASSIGNMENTS):
        return {"status": "skip", "reason": "witness-search-domain-too-large"}

    # step 2: sweep the outer box, collect the full in-bound witness sets.
    admitted_outers, witnessed = _collect_witnesses(
        reading, outer_names, exists_names, bound)
    if not witnessed:
        # no observed witness anywhere -> no data to derive a template from.
        return {"status": "skip", "reason": "no-template-found"}

    # step 3: the data-derived candidate family, per ∃-object.
    per_object = [_object_candidates(j, outer_names, witnessed)
                  for j in range(len(exists_names))]
    if any(not lst for lst in per_object):
        return {"status": "skip", "reason": "no-template-found"}

    # joint candidates = cross product over ∃-objects, canonical order.
    joints = []
    for combo in itertools.product(*per_object):
        joints.append({name: combo[i] for i, name in enumerate(exists_names)})
    joints.sort(key=lambda t: (sum(_term_size(t[n]) for n in exists_names),
                               json.dumps(t, sort_keys=True)))

    # step 4/5: exhaustive full check; first survivor wins.
    concl = conclusions_of(reading)
    ambient = reading.ambient_carrier()
    winner = None
    tried = 0
    for template in joints:
        tried += 1
        if _template_passes(template, admitted_outers, concl, carrier_of, ambient):
            winner = template
            break
    if winner is None:
        return {"status": "skip", "reason": "no-template-found"}

    # emit: the compiled statement (byte-identical, still `:= sorry`) + the ladder.
    compiled = compile_math_reading(reading)
    statement_lean_text = compiled["lean_text"]
    statement_hash = compiled["statement_hash"]
    proofs = _emit_proofs(reading, statement_lean_text, winner,
                          outer_names, exists_names)

    # escape-gate self-validation: refuse our OWN gate-failing output (a gate
    # failure is an internal invariant violation, never a skip).
    for p in proofs:
        ok, why = validate_lean(p["lean_text"])
        if not ok:
            raise WitnessEmitError(
                f"emitted proof failed the escape gate ({why}) -- an internal "
                f"invariant violation:\n{p['lean_text']}")

    return {"status": "emitted",
            "statement_lean_text": statement_lean_text,
            "statement_hash": statement_hash,
            "template": winner,
            "proofs": proofs,
            "search": {"bound": bound, "rung": RUNG,
                       "n_outer_admitted": len(admitted_outers),
                       "n_witnessed": len(witnessed),
                       "candidates_tried": tried}}
