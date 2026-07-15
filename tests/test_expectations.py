"""Tests for the examiner gate (F2.4a), the source-blind instance-expectation
validator that mirrors ``buildloop.validate.validate_scenarios``.

Covers: a well-formed set passes and normalizes; the non-vacuity rule (a
missing positive OR a missing boundary is refused); per-item malformations are
refused; and -- the ⚠T9 enforcement -- the entry point's SIGNATURE proves
blindness (it can accept ``source_text`` and nothing that would let the Reading
or the Lean reach the examiner).
"""
import inspect
import json

import pytest

from buildloop.validate_expectations import (
    BadExpectations,
    validate_expectations,
    expectation_prompt_contract,
)

SRC = "For every natural number n, if n divides m then ..."


def _exp(kind, assignment, expect, why="because the meaning says so"):
    return {"kind": kind, "assignment": assignment, "expect": expect, "why": why}


def _doc(*items, **extra):
    d = {"expectations": list(items)}
    d.update(extra)
    return json.dumps(d)


# --------------------------------------------------------------------------- #
# happy path
# --------------------------------------------------------------------------- #

def test_wellformed_passes_and_normalizes():
    text = _doc(
        _exp("positive", {"n": 3}, "holds", "at n=3 the claim holds"),
        _exp("boundary", {"n": 0, "d": 0}, "outside", "divisor 0 is outside"),
    )
    out = validate_expectations(text, source_text=SRC)
    assert isinstance(out, dict)
    assert set(out) == {"expectations"}
    assert [e["kind"] for e in out["expectations"]] == ["positive", "boundary"]
    assert out["expectations"][0]["assignment"] == {"n": 3}
    assert out["expectations"][1]["expect"] == "outside"


def test_boundary_may_expect_fails_and_notes_preserved():
    text = _doc(
        _exp("positive", {"n": 5}, "holds"),
        _exp("boundary", {"n": 2}, "fails"),
        notes="examiner scratch",
    )
    out = validate_expectations(text, source_text=SRC)
    assert out["notes"] == "examiner scratch"
    assert out["expectations"][1]["expect"] == "fails"


def test_multiple_of_each_kind_ok():
    text = _doc(
        _exp("positive", {"n": 3}, "holds"),
        _exp("positive", {"n": 4}, "holds"),
        _exp("boundary", {"n": 0}, "outside"),
    )
    out = validate_expectations(text, source_text=SRC)
    assert len(out["expectations"]) == 3


# --------------------------------------------------------------------------- #
# non-vacuity (the validate_scenarios discipline)
# --------------------------------------------------------------------------- #

def test_missing_boundary_refused():
    text = _doc(
        _exp("positive", {"n": 3}, "holds"),
        _exp("positive", {"n": 7}, "holds"),
    )
    with pytest.raises(BadExpectations, match="boundary"):
        validate_expectations(text, source_text=SRC)


def test_missing_positive_refused():
    text = _doc(
        _exp("boundary", {"n": 0}, "outside"),
        _exp("boundary", {"n": 1}, "fails"),
    )
    with pytest.raises(BadExpectations, match="positive"):
        validate_expectations(text, source_text=SRC)


def test_empty_list_refused():
    with pytest.raises(BadExpectations, match="non-empty list"):
        validate_expectations(_doc(), source_text=SRC)


# --------------------------------------------------------------------------- #
# malformed items
# --------------------------------------------------------------------------- #

def test_bad_kind_refused():
    text = _doc(
        _exp("supporting", {"n": 3}, "holds"),
        _exp("boundary", {"n": 0}, "outside"),
    )
    with pytest.raises(BadExpectations, match="kind"):
        validate_expectations(text, source_text=SRC)


def test_bad_expect_refused():
    text = _doc(
        _exp("positive", {"n": 3}, "maybe"),
        _exp("boundary", {"n": 0}, "outside"),
    )
    with pytest.raises(BadExpectations, match="expect"):
        validate_expectations(text, source_text=SRC)


def test_incoherent_positive_expect_refused():
    # a "positive" instance asserting the claim is "outside" is internally
    # incoherent -- pure structure, no source reading required.
    text = _doc(
        _exp("positive", {"n": 3}, "outside"),
        _exp("boundary", {"n": 0}, "outside"),
    )
    with pytest.raises(BadExpectations, match="positive"):
        validate_expectations(text, source_text=SRC)


def test_incoherent_boundary_expect_refused():
    text = _doc(
        _exp("positive", {"n": 3}, "holds"),
        _exp("boundary", {"n": 0}, "holds"),
    )
    with pytest.raises(BadExpectations, match="boundary"):
        validate_expectations(text, source_text=SRC)


def test_non_int_assignment_refused():
    text = _doc(
        _exp("positive", {"n": "three"}, "holds"),
        _exp("boundary", {"n": 0}, "outside"),
    )
    with pytest.raises(BadExpectations, match="integer"):
        validate_expectations(text, source_text=SRC)


def test_bool_assignment_refused():
    # bool subclasses int in Python; the gate must reject it explicitly.
    text = _doc(
        _exp("positive", {"n": True}, "holds"),
        _exp("boundary", {"n": 0}, "outside"),
    )
    with pytest.raises(BadExpectations, match="integer"):
        validate_expectations(text, source_text=SRC)


def test_empty_assignment_refused():
    text = _doc(
        _exp("positive", {}, "holds"),
        _exp("boundary", {"n": 0}, "outside"),
    )
    with pytest.raises(BadExpectations, match="assignment"):
        validate_expectations(text, source_text=SRC)


def test_empty_why_refused():
    text = _doc(
        _exp("positive", {"n": 3}, "holds", why="   "),
        _exp("boundary", {"n": 0}, "outside"),
    )
    with pytest.raises(BadExpectations, match="why"):
        validate_expectations(text, source_text=SRC)


def test_extra_item_key_refused():
    bad = {"kind": "positive", "assignment": {"n": 3}, "expect": "holds",
           "why": "ok", "extra": 1}
    text = json.dumps({"expectations": [
        bad, _exp("boundary", {"n": 0}, "outside")]})
    with pytest.raises(BadExpectations, match="keys must be exactly"):
        validate_expectations(text, source_text=SRC)


def test_missing_item_key_refused():
    bad = {"kind": "positive", "assignment": {"n": 3}, "expect": "holds"}
    text = json.dumps({"expectations": [
        bad, _exp("boundary", {"n": 0}, "outside")]})
    with pytest.raises(BadExpectations, match="keys must be exactly"):
        validate_expectations(text, source_text=SRC)


def test_non_json_refused():
    with pytest.raises(BadExpectations, match="not valid JSON"):
        validate_expectations("{not json", source_text=SRC)


def test_top_level_not_object_refused():
    with pytest.raises(BadExpectations):
        validate_expectations("[]", source_text=SRC)


def test_unexpected_top_level_key_refused():
    text = json.dumps({"expectations": [_exp("positive", {"n": 3}, "holds")],
                       "reading": "leak"})
    with pytest.raises(BadExpectations):
        validate_expectations(text, source_text=SRC)


# --------------------------------------------------------------------------- #
# source_text handling
# --------------------------------------------------------------------------- #

def test_empty_source_text_refused():
    text = _doc(
        _exp("positive", {"n": 3}, "holds"),
        _exp("boundary", {"n": 0}, "outside"),
    )
    with pytest.raises(BadExpectations, match="source_text"):
        validate_expectations(text, source_text="   ")


# --------------------------------------------------------------------------- #
# BLINDNESS: the call signature is the enforcement point (⚠T9)
# --------------------------------------------------------------------------- #

def test_blindness_signature_has_only_source_text():
    sig = inspect.signature(validate_expectations)
    params = sig.parameters
    # exactly two parameters: the expectations payload and source_text
    assert list(params) == ["expectations_json", "source_text"]
    # source_text is keyword-only (the blindness contract is explicit at the
    # call site, never positional smuggling)
    assert params["source_text"].kind is inspect.Parameter.KEYWORD_ONLY


def test_blindness_signature_forbids_reading_and_lean():
    sig = inspect.signature(validate_expectations)
    forbidden = {"reading", "lean", "lean_text", "math_reading"}
    leaked = forbidden & set(sig.parameters)
    assert not leaked, (
        f"examiner entry point exposes {leaked}: an examiner that could see "
        f"the Reading or the Lean would not be blind (⚠T9)")


def test_blindness_call_rejects_reading_kwarg():
    # Passing a reading/lean keyword must be a TypeError -- the signature has
    # no such slot, so the leak is unrepresentable at the call site.
    text = _doc(
        _exp("positive", {"n": 3}, "holds"),
        _exp("boundary", {"n": 0}, "outside"),
    )
    for bad_kw in ("reading", "lean", "lean_text", "math_reading"):
        with pytest.raises(TypeError):
            validate_expectations(text, source_text=SRC, **{bad_kw: "leak"})


def test_prompt_contract_names_blindness():
    contract = expectation_prompt_contract()
    assert isinstance(contract, str) and contract
    assert "source_text" in contract
    assert "positive" in contract and "boundary" in contract
