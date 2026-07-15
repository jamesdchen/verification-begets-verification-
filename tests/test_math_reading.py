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


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
