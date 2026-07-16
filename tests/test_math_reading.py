"""Teeth for the F1.1/F-G math-reading gate (`generators/math_reading.py`).

Fast, LLM-free, deterministic.  Drives the ONE owned fixture home
(`tests/fixtures_math_readings.py`, X16) through `parse_math_reading` and pins:

  * every "parse" fixture parses; every ("refuse", stage) fixture is refused at
    the math-reading-gate (a FragmentMiss, carrying `.missing_kind_guess`, for
    the fragment-miss entries);
  * byte-stability: parsing a fixture twice yields structurally-equal
    statements (the gate is a pure function of reading+source);
  * the force trichotomy is enforced per kind (F1.1 force column);
  * the single-source discipline of the LF kind sets (the reading.py pattern);
  * fragment-miss carries the F4 demand data (`missing_kind_guess`).
"""
import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import common
from generators.math_reading import (
    parse_math_reading,
    BadMathReading,
    FragmentMiss,
    MathReading,
    MATH_LF_KINDS,
    _MLF_FIELDS,
    _MLF_FORCES,
)
from tests.fixtures_math_readings import (
    FIXTURES,
    FRAGMENT_MISS,
    reading_text,
    source,
)

_PARSE = sorted(n for n, e in FIXTURES.items() if e["expect"] == "parse")
_REFUSE = sorted(n for n, e in FIXTURES.items() if e["expect"] != "parse")


# --- the fixture home itself ------------------------------------------------
def test_fixture_counts():
    """F1 done-when: ten hand-written MathReadings that parse (we ship >= 10),
    plus the refusal fixtures."""
    assert len(FIXTURES) >= 10
    assert len(_PARSE) >= 10
    # the mandated refusals are all present.
    for required in ("bad_fabricated_quote", "bad_choice_quote",
                     "bad_undeclared_ref"):
        assert required in _REFUSE
    assert FRAGMENT_MISS <= set(_REFUSE)


# --- parse / refuse behaviour ----------------------------------------------
@pytest.mark.parametrize("name", _PARSE)
def test_parse_fixture_parses(name):
    mr = parse_math_reading(reading_text(name), source(name))
    assert isinstance(mr, MathReading)
    # F1.1: the asserted content is present as a demanded conclusion.
    assert any(s["lf"]["kind"] == "conclusion" and s["force"] == "demand"
               for s in mr.statements)


@pytest.mark.parametrize("name", _REFUSE)
def test_refuse_fixture_is_refused_at_gate(name):
    stage = FIXTURES[name]["expect"][1]
    assert stage == "math-reading-gate"
    with pytest.raises(BadMathReading) as ei:
        parse_math_reading(reading_text(name), source(name))
    if name in FRAGMENT_MISS:
        assert isinstance(ei.value, FragmentMiss)
        assert ei.value.missing_kind_guess is not None


def test_every_parse_quote_occurs_verbatim_in_source():
    """The gate's groundedness contract, stated over the fixture home: every
    demand/presupposition quotes a span literally present in the source, and
    every choice quotes nothing."""
    def _norm(t):
        return " ".join(t.lower().split())
    for name in _PARSE:
        src = _norm(source(name))
        for s in FIXTURES[name]["reading"]["statements"]:
            q = s.get("quote", "")
            if s["force"] in ("demand", "presupposition"):
                assert q.strip(), f"{name}/{s['id']}: non-empty quote required"
                assert _norm(q) in src, f"{name}/{s['id']}: {q!r} not in source"
            else:
                assert not q.strip(), f"{name}/{s['id']}: choice must be empty"


# --- byte-stability: the gate is a pure function ----------------------------
@pytest.mark.parametrize("name", _PARSE)
def test_parse_is_byte_stable(name):
    a = parse_math_reading(reading_text(name), source(name))
    b = parse_math_reading(reading_text(name), source(name))
    # structural equality via canonical re-serialisation of the statements.
    assert common.canonical_json(a.statements) == common.canonical_json(
        b.statements)
    # and the parse did not mutate the fixture's meaning between calls.
    assert a.theorem == b.theorem


# --- force-rule enforcement (F1.1 force column), by mutating a valid fixture -
# even_add carries exactly one of every kind we need to poke: object, operator,
# ambient, quantifier, hypothesis, conclusion.
_FORCE_BASE = "even_add"


def _mutate(base_name, kind, **overrides):
    """Deep-copy `base_name`'s reading, apply `overrides` to the first statement
    of the given lf kind, and return (reading_json, source)."""
    entry = FIXTURES[base_name]
    reading = copy.deepcopy(entry["reading"])
    for st in reading["statements"]:
        if st["lf"]["kind"] == kind:
            for k, v in overrides.items():
                st[k] = v
            break
    else:  # pragma: no cover - guards the base fixture's shape
        raise AssertionError(f"no {kind!r} statement in {base_name!r}")
    return json.dumps(reading), entry["source"]


def test_conclusion_tagged_non_demand_is_refused():
    # conclusion is demand-only; a presupposition conclusion is refused.
    txt, src = _mutate(_FORCE_BASE, "conclusion", force="presupposition")
    with pytest.raises(BadMathReading):
        parse_math_reading(txt, src)


def test_ambient_tagged_non_choice_is_refused():
    # ambient is choice-only; give it a non-empty in-source quote so the refusal
    # is the FORCE rule, not the empty-quote rule.
    txt, src = _mutate(_FORCE_BASE, "ambient",
                       force="presupposition", quote="even")
    with pytest.raises(BadMathReading):
        parse_math_reading(txt, src)


def test_hypothesis_tagged_choice_is_refused():
    # hypothesis is demand-or-presupposition, never choice; empty quote so the
    # refusal is the FORCE rule, not the choice-must-be-empty rule.
    txt, src = _mutate(_FORCE_BASE, "hypothesis", force="choice", quote="")
    with pytest.raises(BadMathReading):
        parse_math_reading(txt, src)


def test_operator_tagged_demand_is_refused():
    # operator is presupposition-or-choice; demand is refused (quote kept, and
    # it is in-source, so the refusal is the FORCE rule).
    txt, src = _mutate(_FORCE_BASE, "operator", force="demand")
    with pytest.raises(BadMathReading):
        parse_math_reading(txt, src)


# --- single-source discipline (the reading.py pattern) ----------------------
def test_lf_kind_sets_are_single_sourced():
    assert set(_MLF_FIELDS) == set(MATH_LF_KINDS) == set(_MLF_FORCES)


def _math_grammar_block():
    """Render the per-kind LF grammar block from MATH_LF_KINDS, mirroring
    buildloop/service_loop.py:_reading_grammar_block (F1.3)."""
    out = []
    for kind, (sig, force) in MATH_LF_KINDS.items():
        out.append(f"  {sig}")
        out.append(f"      (force: {force})")
    return "\n".join(out)


def test_grammar_render_names_every_kind():
    block = _math_grammar_block()
    for kind in MATH_LF_KINDS:
        assert kind in block, f"grammar render omits kind {kind!r}"


# --- fragment-miss is F4 demand data ----------------------------------------
@pytest.mark.parametrize("name", sorted(FRAGMENT_MISS))
def test_fragment_miss_carries_missing_kind_guess(name):
    with pytest.raises(FragmentMiss) as ei:
        parse_math_reading(reading_text(name), source(name))
    assert ei.value.missing_kind_guess is not None
    assert isinstance(ei.value.missing_kind_guess, str)


# --- B1: mixed-carrier `-` without ambient is refused at the gate ------------
# The eval mirror resolves a `-` node's carrier by its FIRST ref (order-
# sensitive) while the SMT mirror truncates on any Nat operand (order-
# insensitive); on a mixed-carrier `-` with no ambient the two channels
# disagree, so the gate refuses it (§11.0 B1 / §11.5).
def _obj(name, ty):
    return {"id": "o_" + name, "force": "choice", "quote": "",
            "lf": {"kind": "object", "name": name, "type": ty}}


def _concl(sid, pred, quote):
    return {"id": sid, "force": "demand", "quote": quote,
            "lf": {"kind": "conclusion", "pred": pred}}


def _minus_reading(a_ty, b_ty, ambient=None):
    stmts = [_obj("a", a_ty), _obj("b", b_ty),
             _concl("c1", {"op": "=", "args": [
                 {"op": "-", "args": [{"ref": "a"}, {"ref": "b"}]}, {"lit": 0}]},
                 "a minus b is zero")]
    if ambient is not None:
        stmts.insert(0, {"id": "amb", "force": "choice", "quote": "",
                         "lf": {"kind": "ambient", "carrier": ambient}})
    doc = {"theorem": "thm", "statements": stmts}
    return json.dumps(doc), "let a and b be given, a minus b is zero"


def test_mixed_carrier_minus_without_ambient_is_refused():
    txt, src = _minus_reading("Nat", "Int")
    with pytest.raises(BadMathReading) as ei:
        parse_math_reading(txt, src)
    assert "carrier" in str(ei.value).lower()


def test_mixed_carrier_minus_with_ambient_is_allowed():
    # the fix is scoped to the no-ambient case (§11.0); a declared ambient parses.
    txt, src = _minus_reading("Nat", "Int", ambient="Int")
    parse_math_reading(txt, src)


def test_shared_carrier_minus_without_ambient_is_allowed():
    # a `-` whose operands share one carrier has no divergence, so it parses.
    txt, src = _minus_reading("Int", "Int")
    parse_math_reading(txt, src)


def test_refused_minus_shape_is_exactly_a_mirror_divergence():
    # the refused shape is not arbitrary: bypassing the gate, the eval and SMT
    # carrier rules genuinely disagree on the SAME `-` node.  Reordering the sum
    # in `(n + b) - 5` flips the eval carrier (first ref) while the SMT carrier
    # (any-Nat-operand) is unchanged -- a relational witness that the gate is
    # closing a real divergence, not a phantom one.
    from generators import math_smt, math_eval
    minus = {"op": "-", "args": [{"op": "+", "args": [{"ref": "n"}, {"ref": "b"}]},
                                 {"lit": 5}]}
    reordered = {"op": "-", "args": [{"op": "+", "args": [{"ref": "b"},
                                     {"ref": "n"}]}, {"lit": 5}]}
    objects = {"n": "Int", "b": "Nat"}          # mixed carriers, no ambient
    # eval carrier = first ref in pre-order -> order-sensitive
    assert math_eval._term_carrier(minus, objects, None) == "Int"
    assert math_eval._term_carrier(reordered, objects, None) == "Nat"
    # SMT carrier = any Nat operand -> order-insensitive (Nat both ways)
    assert math_smt._minus_carrier(minus["args"], objects, None) == "Nat"
    assert math_smt._minus_carrier(reordered["args"], objects, None) == "Nat"
    # so eval(minus)=Int disagrees with smt(minus)=Nat: exactly what the gate bars


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
