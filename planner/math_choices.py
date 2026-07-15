"""F-INT-6 (WP-F, closes G6): searched formalization choices.

The service lifecycle has ``planner/choices.py`` -- a search over the residual
formalization freedom (which lifecycle family, what generality).  MathReadings
carry the SAME residue in a different key: the CARRIER of a typed object, an
operator binding, and the ambient structure are formalization CHOICES (the F1
trichotomy's third force), and NOTHING searched that residue.  This module is
that search, and it is deterministic and LLM-free.

    ⚠FI-6 (verified by a full compile/eval trace).  The residue does NOT live in
    the ambient statement.  Truncated subtraction (``Nat.sub`` vs ``Int.sub``)
    and the instance domain are decided by the objects' DECLARED types
    (``math_compile.py``'s typed binders, ``math_eval.py``'s ``_term_carrier``);
    the ambient only selects a carrier-indexed Lean NAME (``Nat.gcd`` vs
    ``Int.gcd``), which never changes a computed value.  So a search over
    "formalization freedom" must substitute WHOLE carrier assignments -- object
    types + operator carriers + the ambient, together -- on a COPIED reading,
    not tweak the ambient alone (which is semantically inert).

``search_carrier`` enumerates the consistent carrier assignments over a
reading's CHOICE-force elements, applies each to a deep-copied, re-parsed
candidate, re-runs the Lean-free fidelity gates (parse -> nonvacuity via
math_smt/enum -> compile -> entailed-instance replay via math_eval), and ranks:
certifying candidates first, then by compiled-statement description length.

The speech-act trichotomy is LOAD-BEARING.  Only ``choice``-force carriers are
formalization freedom; a ``demand``- or ``presupposition``-force type/carrier is
quoted from the source and is NEVER a free variable -- attempting to search one
raises ``NonChoiceForceError``.  A ``(word, carrier)`` pair outside
``MATH_OPERATORS`` is not a crash: it is DEMAND DATA (F4), recorded as a
``fragment_miss`` candidate entry.

No new certificate type.  The result is examiner-grade EVIDENCE (L3) -- a
ranking a caller consults, never a certificate this module issues.  The original
reading object is never mutated: every candidate is a fresh ``json.loads`` deep
copy, re-parsed from scratch.
"""
from __future__ import annotations

import copy
import itertools
import json

import common
from generators.math_reading import (
    CARRIERS, parse_math_reading, split_envelope, FragmentMiss)
from generators.math_compile import compile_math_reading
from generators import math_smt, math_eval
from buildloop.validate_lean import validate_lean
from kernel.backends import SmtBackend


class NonChoiceForceError(Exception):
    """Attempt to search (override the carrier of) a demand- or presupposition-
    force element.  The trichotomy is load-bearing: only CHOICE-force carriers
    are formalization freedom.  A demand/presupposition carrier is quoted from
    the source and is never a free variable, so overriding one would fabricate
    meaning the text does not license."""


# Which statements carry a searchable CHOICE carrier, and in which lf field it
# lives (an object's carrier is its ``type``; an operator's and the ambient's is
# ``carrier``).  Single-sourced so the slot finder and the substitution agree.
_CARRIER_FIELD = {"object": "type", "operator": "carrier", "ambient": "carrier"}


def _slot_field(stmt: dict):
    """The lf field name holding this statement's carrier IF it is a searchable
    formalization choice, else ``None``.  A statement is searchable only when its
    kind has a carrier AND its force is ``choice`` -- the trichotomy gate."""
    lf = stmt.get("lf") or {}
    kind = lf.get("kind")
    if kind not in _CARRIER_FIELD:
        return None
    if stmt.get("force") != "choice":
        return None
    return _CARRIER_FIELD[kind]


def searchable_slots(reading_doc: dict) -> list:
    """``[(statement_id, field, current_carrier), ...]`` for every choice-force
    carrier slot, in statement order (deterministic).  These are the only
    elements ``search_carrier`` substitutes."""
    slots = []
    for s in reading_doc.get("statements", []):
        field = _slot_field(s)
        if field is not None:
            slots.append((s["id"], field, s["lf"].get(field)))
    return slots


def apply_carrier_assignment(reading_doc: dict, assignment: dict) -> dict:
    """Return a DEEP COPY of ``reading_doc`` with each slot named in
    ``assignment`` (``statement_id -> carrier``) substituted.

    Raises ``NonChoiceForceError`` if any id names a statement that is not a
    choice-force carrier slot -- a demand- or presupposition-force type/carrier
    is NEVER overridden (the trichotomy is load-bearing).  The input doc is not
    mutated."""
    by_id = {s.get("id"): s for s in reading_doc.get("statements", [])}
    for sid in assignment:
        s = by_id.get(sid)
        if s is None:
            raise NonChoiceForceError(f"no statement with id {sid!r} to search")
        if _slot_field(s) is None:
            force = s.get("force")
            kind = (s.get("lf") or {}).get("kind")
            raise NonChoiceForceError(
                f"{sid!r} is a {force}-force {kind}; only CHOICE-force carrier "
                f"elements are formalization freedom -- a {force} carrier is "
                f"quoted from the source and may not be searched")
    out = copy.deepcopy(reading_doc)
    for s in out["statements"]:
        sid = s.get("id")
        if sid in assignment:
            s["lf"][_slot_field(s)] = assignment[sid]
    return out


# --------------------------------------------------------------- the gate ladder
def _sat_verdict(ch: dict) -> str:
    """Map an SmtBackend result (run ``expect="sat"``) back to the raw solver
    verdict, mirroring ``run.formalize._sat_verdict``."""
    r = ch.get("result")
    if r == "pass":
        return "sat"
    if r == "fail":
        return "unsat"
    return r or "error"


def _nonvacuous(reading, bound: int) -> bool:
    """Lean-free non-vacuity for the search (F2.1).  The decidable-enumeration
    channel (``math_eval.bounded_nonvacuous``) is authoritative within ``bound``;
    a dual-solver SAT (z3 AND cvc5) can additionally accept a witness that only
    exists beyond ``bound`` (the T4 direction split).  cvc5 may be ABSENT ->
    honest degradation: with no cvc5 verdict the enumeration channel decides
    alone (never a silent green from z3 unaccompanied)."""
    bounded = bool(math_eval.bounded_nonvacuous(reading, bound=bound))
    if not math_smt.smt_representable(reading):
        return bounded                       # enum-only (gcd/coprime hypothesis)
    smt = math_smt.hypotheses_smt(reading)
    be = SmtBackend()
    try:
        zv = _sat_verdict(be.run_z3(smt, expect="sat"))
    except Exception:
        zv = "error"
    try:
        cv = _sat_verdict(be.run_cvc5(smt, expect="sat"))
    except Exception:
        cv = "unavailable"                   # cvc5 absent -> enum channel decides
    if zv == "sat" and cv == "sat":
        return True
    # unsat / unknown / solver-split / cvc5-absent all fall to the decidable
    # channel: a dual-unsat with a bounded witness is a mirror-divergence (not a
    # refusal); a dual-unsat with no bounded witness is vacuous.
    return bounded


def _evaluate(reading_doc: dict, source: str, bound: int) -> dict:
    """Run the Lean-free gate ladder on ONE candidate reading doc and return the
    frozen entry body (minus ``assignment``, plus an internal ``_dl`` used for
    ranking).  Raises ``FragmentMiss`` for an out-of-table ``(word, carrier)``
    so the caller can record a fragment-miss entry instead of crashing."""
    cand_json = json.dumps(reading_doc)
    reading = parse_math_reading(cand_json, source)          # may raise FragmentMiss
    compiled = compile_math_reading(reading)
    lean_text = compiled["lean_text"]
    statement_hash = compiled["statement_hash"]
    gate_ok, _reason = validate_lean(lean_text)              # defense in depth
    # DL of the compiled statement: the byte length of the emitted Lean text --
    # a description-length proxy, used only for RELATIVE ranking (never asserted
    # as an absolute constant).
    dl = float(len(lean_text))

    nonvacuous = _nonvacuous(reading, bound)

    # entailed-instance replay: the k smallest hypothesis-satisfying instances
    # must all make the conclusion hold; a False one refutes (wrong binding or a
    # narrowed carrier) and is the witness.  Rank-only downstream, never a crash.
    witness = None
    for a in math_eval.satisfying_instances(reading, k=5, bound=bound):
        if not math_eval.conclusion_holds(reading, a):
            witness = a
            break
    instances_ok = witness is None

    certifies = bool(gate_ok and nonvacuous and instances_ok)

    boundary_behavior = []
    for p in math_eval.boundary_probes(reading, bound=bound):
        a = p["assignment"]
        boundary_behavior.append({
            "assignment": a,
            "hypothesis_id": p.get("hypothesis_id"),
            "holds": bool(math_eval.conclusion_holds(reading, a)),
        })
    boundary_behavior.sort(key=common.canonical_json)

    return {"certifies": certifies, "witness": witness,
            "boundary_behavior": boundary_behavior,
            "statement_hash": statement_hash, "_dl": dl}


# --------------------------------------------------------------------- the search
def search_carrier(reading_json, *, bound: int = 8) -> list:
    """Enumerate the consistent carrier assignments over a MathReading's
    CHOICE-force elements and rank them by the Lean-free fidelity gates.

    ``reading_json`` -- an F-A envelope ``{source, reading:{theorem,
    statements}}`` (a json string; the source is needed to re-check
    groundedness on every re-parse).  ``bound`` -- the enumeration/instance
    bound (default 8), threaded to every gate.

    Enumeration: the searchable slots are each CHOICE-force object's declared
    type, each CHOICE-force operator statement's carrier, and the ambient's
    carrier.  A consistent assignment fixes all of them together, drawn from the
    carrier whitelist ``CARRIERS``; the full product is enumerated.  Each
    assignment is applied to a fresh DEEP COPY of the reading, re-parsed from
    json, and run through parse -> nonvacuity -> compile -> entailed-instance
    replay.

    Returns a ranked list -- certifying candidates first, then ascending
    compiled-statement DL (ties broken by statement_hash).  An in-fragment entry
    is ``{assignment, certifies, witness, boundary_behavior, statement_hash}``.
    An out-of-table ``(word, carrier)`` pair yields ``{assignment,
    fragment_miss}`` (DEMAND DATA, not a crash), ranked last.  This is
    examiner-grade EVIDENCE (L3): a ranking, never a certificate.  The original
    reading object is never mutated.
    """
    inner_json, source = split_envelope(reading_json)
    base_doc = json.loads(inner_json)                    # {theorem, statements}
    slot_ids = [sid for sid, _f, _c in searchable_slots(base_doc)]

    keyed = []
    for combo in itertools.product(CARRIERS, repeat=len(slot_ids)):
        assignment = dict(zip(slot_ids, combo))
        cand_doc = apply_carrier_assignment(base_doc, assignment)   # deep copy
        try:
            body = _evaluate(cand_doc, source, bound)
        except FragmentMiss as e:
            # (word, carrier) outside MATH_OPERATORS -> fragment-miss entry.
            key = (2, 0.0, common.canonical_json(assignment))
            keyed.append((key, {"assignment": assignment,
                                "fragment_miss": str(e)}))
            continue
        dl = body.pop("_dl")
        entry = {"assignment": assignment, **body}
        key = (0 if entry["certifies"] else 1, dl, entry["statement_hash"])
        keyed.append((key, entry))

    keyed.sort(key=lambda ke: ke[0])
    return [entry for _key, entry in keyed]
