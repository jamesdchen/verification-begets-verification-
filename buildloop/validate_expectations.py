"""The examiner gate: source-blind instance-expectation validation (F2.4a).

The **examiner** is auto-informalization run as a fidelity mechanism: an
independent, semantics-blind pass that reads ONLY the source text -- never the
Reading, never the compiled Lean -- and authors EXPECTED concrete instances of
what the sentence MEANS ("at n = 3 this should hold", "the divisor-0 case is
outside the claim").  Those expectations are later replayed against the
compiled statement by the F2.2 machinery; divergence is a first-class
``formalization-divergence`` event and convergence is intent-admission-tier
evidence (TRUST 3.4).

This module is the GATE on the examiner's JSON.  It is the direct analogue of
``buildloop.validate.validate_scenarios`` (the intent-scenario gate) and
carries the SAME non-vacuity discipline: an expectation set with no positive
instance, or with no boundary instance, has no teeth and is refused.  Per rule
L3 ("fidelity gates are refusals, tripwires are events") the gate REFUSES by
raising :class:`BadExpectations`; it never emits an event and never issues or
blocks a certificate by itself.

**Blindness is enforced as a call signature (⚠T9, the ``CGB_TASK_TIME``
precedent).**  :func:`validate_expectations` accepts only the expectations JSON
plus the keyword ``source_text``.  It has NO ``reading``, ``lean``,
``lean_text`` or ``math_reading`` parameter -- an examiner that could see the
Reading or the Lean would not be blind, so the very shape of the entry point
makes the leak unrepresentable.  ``inspect.signature`` is the enforcement
point (see ``tests/test_expectations.py``).  This is prompt-level independence
only; correlated misreadings survive (TRUST 3.4's caveat, verbatim).
"""
from __future__ import annotations

import json


class BadExpectations(Exception):
    """The examiner's expectation JSON is malformed or vacuous.

    Raised as a refusal (L3): a fidelity gate refuses, it does not log an
    event.  Mirrors ``buildloop.validate.SpecViolation`` for the scenario gate.
    """


#: The examiner's structural vocabulary.  ``kind`` labels the intent of an
#: instance; ``expect`` labels its predicted verdict.  Kept module-level so
#: WP-H can wire the authoring prompt against the exact same tokens the gate
#: enforces.
KINDS = ("positive", "boundary")
EXPECTS = ("holds", "fails", "outside")

#: Structural coherence between ``kind`` and ``expect``.  A ``positive``
#: instance is one the sentence's meaning should make hold; a ``boundary``
#: instance is one the meaning places out of the claim (``outside``) or makes
#: fail (``fails``).  Enforcing this is a check on two declared JSON fields --
#: pure structure, never truth (the gate cannot and does not read the source
#: to decide whether a given instance ACTUALLY holds; that is F2.2's job).
#: A happy consequence: with coherence enforced, ">=1 positive and >=1
#: boundary" (counted by kind) coincides exactly with "teeth in both
#: directions" (counted by verdict), matching validate_scenarios' discipline.
_COHERENT = {"positive": {"holds"}, "boundary": {"fails", "outside"}}

_ITEM_KEYS = {"kind", "assignment", "expect", "why"}
_MAX_EXPECTATIONS = 100


def expectation_prompt_contract() -> str:
    """The blindness contract, named for WP-H's prompt wiring.

    The examiner is handed EXACTLY one thing -- the ``source_text`` -- and must
    emit the expectation JSON shape below.  It is never handed the Reading or
    the compiled Lean; that exclusion is the whole point of the mechanism and
    is enforced by :func:`validate_expectations`'s signature (⚠T9).
    """
    return (
        "The examiner sees ONLY source_text (never the Reading, never the "
        "Lean).  Emit JSON: {\"expectations\": [ {\"kind\": "
        "\"positive\"|\"boundary\", \"assignment\": {objname: int}, "
        "\"expect\": \"holds\"|\"fails\"|\"outside\", \"why\": str}, ... ] }. "
        "Author at least one positive instance (a case the sentence's meaning "
        "makes hold) AND at least one boundary instance (a case the meaning "
        "places outside the claim or makes fail); an expectation set without "
        "teeth in both directions is refused."
    )


def validate_expectations(expectations_json: str, *, source_text: str) -> dict:
    """Parse and validate the examiner's instance expectations; return the
    normalized dict.

    The signature carries ONLY ``source_text`` besides the expectations -- this
    is the blindness contract (⚠T9).  Do NOT add a ``reading`` or ``lean``
    parameter; the examiner is source-blind by construction.

    Refuses (raises :class:`BadExpectations`) unless the document is:

    * valid JSON of shape ``{"expectations": [...], "notes"?: ...}``;
    * a non-empty list (<= %d) of items each with EXACTLY the keys
      ``kind``, ``assignment``, ``expect``, ``why``;
    * ``kind`` in %r, ``expect`` in %r, coherent per :data:`_COHERENT`;
    * ``assignment`` a non-empty dict of ``str -> int`` (a concrete instance
      binds at least one object; bools are rejected -- ``True``/``False`` are
      not integer assignments even though ``bool`` subclasses ``int``);
    * ``why`` a non-empty string;
    * NON-VACUOUS: at least one ``positive`` AND at least one ``boundary``
      expectation (the analogue of ``validate_scenarios`` requiring both a
      fully-accepted scenario and a rejected one).

    Returns a normalized ``{"expectations": [...], "notes"?: ...}`` dict.
    """
    # source_text is the ONE thing the examiner was allowed to read.  We do not
    # inspect its content (the gate is semantics-blind), but a real examiner
    # cannot author expectations from nothing, so require a non-empty string.
    if not isinstance(source_text, str) or not source_text.strip():
        raise BadExpectations("source_text must be a non-empty string")

    try:
        doc = json.loads(expectations_json)
    except Exception as e:  # json.JSONDecodeError, or non-str input
        raise BadExpectations(f"not valid JSON: {e}")
    if not isinstance(doc, dict) or set(doc) - {"expectations", "notes"}:
        raise BadExpectations(
            "expectations doc must be {expectations: [...], notes?: ...}")

    exps = doc.get("expectations")
    if not isinstance(exps, list) or not exps:
        raise BadExpectations("expectations must be a non-empty list")
    if len(exps) > _MAX_EXPECTATIONS:
        raise BadExpectations(
            f"too many expectations (>{_MAX_EXPECTATIONS})")

    normalized: list[dict] = []
    n_positive = n_boundary = 0
    for i, exp in enumerate(exps):
        where = f"expectation[{i}]"
        if not isinstance(exp, dict) or set(exp) != _ITEM_KEYS:
            raise BadExpectations(
                f"{where}: keys must be exactly {sorted(_ITEM_KEYS)}, "
                f"got {sorted(exp) if isinstance(exp, dict) else type(exp).__name__}")

        kind = exp["kind"]
        if kind not in KINDS:
            raise BadExpectations(f"{where}: kind must be one of {list(KINDS)}")

        expect = exp["expect"]
        if expect not in EXPECTS:
            raise BadExpectations(
                f"{where}: expect must be one of {list(EXPECTS)}")
        if expect not in _COHERENT[kind]:
            raise BadExpectations(
                f"{where}: a {kind} expectation must expect one of "
                f"{sorted(_COHERENT[kind])}, not {expect!r}")

        assignment = exp["assignment"]
        if not isinstance(assignment, dict) or not assignment:
            raise BadExpectations(
                f"{where}: assignment must be a non-empty object of str->int")
        norm_assignment: dict[str, int] = {}
        for name, val in assignment.items():
            # bool is a subclass of int -- reject it explicitly; an assignment
            # is a concrete integer instance, not a truth value.
            if not isinstance(name, str) or not name:
                raise BadExpectations(
                    f"{where}: assignment keys must be non-empty strings")
            if isinstance(val, bool) or not isinstance(val, int):
                raise BadExpectations(
                    f"{where}: assignment {name!r}={val!r} must be an integer")
            norm_assignment[name] = val

        why = exp["why"]
        if not isinstance(why, str) or not why.strip():
            raise BadExpectations(f"{where}: why must be a non-empty string")

        if kind == "positive":
            n_positive += 1
        else:
            n_boundary += 1
        normalized.append({
            "kind": kind,
            "assignment": norm_assignment,
            "expect": expect,
            "why": why,
        })

    # The non-vacuous-expectations rule (the analogue of validate_scenarios
    # requiring >=1 fully-accepted and >=1 rejected scenario).  Refuse, per L3.
    if n_positive == 0:
        raise BadExpectations(
            "need at least one positive expectation "
            "(a concrete instance the claim's meaning makes hold)")
    if n_boundary == 0:
        raise BadExpectations(
            "need at least one boundary expectation "
            "(a concrete instance the claim's meaning places outside/fails)")

    out: dict = {"expectations": normalized}
    if "notes" in doc:
        out["notes"] = doc["notes"]
    return out


# Interpolate the constants into the docstring so it stays in sync.
validate_expectations.__doc__ = validate_expectations.__doc__ % (
    _MAX_EXPECTATIONS, list(KINDS), list(EXPECTS))
