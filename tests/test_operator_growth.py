"""Teeth for R2 autonomous operator-table growth (generators/operator_growth.py).

All LLM-free and Lean-free.  Relational / structural asserts only; no absolute
solver-count constants.  The battery uses z3 + decidable enumeration and
tolerates an absent cvc5 honestly, so these pass whether or not cvc5 is present.
"""
import dataclasses
import json
import os
import tempfile

import pytest

import common
from generators import operator_growth as og
from generators.math_reading import (
    parse_math_reading, split_envelope, BadMathReading)
from run import formalize as _formalize
from run.formalize import certify_statement

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MULTIPLE_OF = {"word": "multiple_of", "arity": 2, "params": ["a", "b"],
               "definition": {"op": "dvd", "args": [{"ref": "b"}, {"ref": "a"}]}}


@pytest.fixture
def op_dir(monkeypatch):
    """An isolated, initially empty operator registry."""
    d = tempfile.mkdtemp(prefix="op-growth-test-")
    monkeypatch.setenv("CGB_OPERATORS_DIR", d)
    monkeypatch.delenv("CGB_DB", raising=False)
    og.reload()
    # The golden was captured cold; drop the in-process fidelity cache so a
    # second certify of the same reading in-process does not append the
    # ("cache","hit") marker and diverge from the cold golden.
    _formalize._formalize_cache_clear()
    yield d
    og.reload()
    _formalize._formalize_cache_clear()


def _admit_and_save(row, op_dir):
    res = og.admit_operator(row)
    assert res["admitted"], res
    og.save_admitted({row["word"]: {"row": res["row"], "cert": res["cert"]}})
    og.reload()
    return res


# ============================================================ (a) admission
def test_multiple_of_admits_with_green_certificate(op_dir):
    res = og.admit_operator(MULTIPLE_OF)
    assert res["admitted"] is True
    cert = res["cert"]
    assert cert["kind"] == "operator-admission"
    assert cert["word"] == "multiple_of"
    # the id binds the canonical row to the battery digest
    assert cert["id"] == og.cert_id(res["row"], cert["battery_digest"])
    b = cert["battery"]
    assert b["satisfiable"] and b["refutable"]
    # both carriers exercised; every instance carries an enum verdict
    assert set(b["carriers"]) == {"Nat", "Int"}
    assert all("enum" in inst for inst in b["instances"])
    # z3 corroborated the enumeration on at least some instance (a real
    # differential, not enum-only)
    assert b["smt_confirmations"] > 0


def test_admission_is_deterministic(op_dir):
    a = og.admit_operator(MULTIPLE_OF)
    b = og.admit_operator(MULTIPLE_OF)
    assert a["cert"]["id"] == b["cert"]["id"]
    assert a["cert"]["battery_digest"] == b["cert"]["battery_digest"]


def test_every_battery_instance_agrees_z3_enum(op_dir):
    res = og.admit_operator(MULTIPLE_OF)
    for inst in res["cert"]["battery"]["instances"]:
        if inst["z3"] in ("sat", "unsat"):
            assert (inst["z3"] == "sat") == inst["enum"]
        if inst["cvc5"] in ("sat", "unsat"):
            assert (inst["cvc5"] == "sat") == inst["enum"]


# B2 tooth: congruence-mod (the §11.4 motivating word) uses a term `mod(_, m)`
# that a solver could evaluate freely at m=0.  Before the mod-by-zero mirror
# fix the battery REFUSED it with "differential disagreement ... enum=False but
# z3=sat" at m=0; with the guarded rendering enum and z3 agree there, so the
# refusal reason is gone and every battery instance corroborates.
def test_congruence_mod_no_longer_refused_by_mod_by_zero_gap(op_dir):
    congm = {"word": "congm", "arity": 3, "params": ["a", "b", "m"],
             "definition": {"op": "=", "args": [
                 {"op": "mod", "args": [{"ref": "a"}, {"ref": "m"}]},
                 {"op": "mod", "args": [{"ref": "b"}, {"ref": "m"}]}]}}
    res = og.admit_operator(congm, registry={})    # temp registry; never persisted
    # the specific §11.4 refusal reason must be gone (whether it now admits is
    # incidental -- the point is the mirror gap no longer forces disagreement).
    if not res["admitted"]:
        assert "differential disagreement" not in res["refusal"]["reason"]
    else:
        insts = res["cert"]["battery"]["instances"]
        # the previously-divergent m=0 instances now agree enum-vs-z3.
        m0 = [i for i in insts if i["assignment"].get("m") == 0]
        assert m0                                   # the battery reaches m=0
        for inst in m0:
            if inst["z3"] in ("sat", "unsat"):
                assert (inst["z3"] == "sat") == inst["enum"]


# ============================================================ (a) refusals
def test_vacuous_tautology_refused(op_dir):
    row = {"word": "always_geq", "arity": 2, "params": ["a", "b"],
           "definition": {"op": "or", "args": [
               {"op": "<=", "args": [{"ref": "a"}, {"ref": "b"}]},
               {"op": "<=", "args": [{"ref": "b"}, {"ref": "a"}]}]}}
    res = og.admit_operator(row)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "nonvacuity"
    assert "tautology" in res["refusal"]["reason"].lower()


def test_contradiction_refused_as_vacuous(op_dir):
    row = {"word": "never_eq", "arity": 1, "params": ["a"],
           "definition": {"op": "!=", "args": [{"ref": "a"}, {"ref": "a"}]}}
    res = og.admit_operator(row)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "nonvacuity"
    assert "contradiction" in res["refusal"]["reason"].lower()


def test_unknown_operator_refused_at_wellformedness(op_dir):
    row = {"word": "weird", "arity": 1, "params": ["a"],
           "definition": {"op": "frobnicate", "args": [{"ref": "a"}]}}
    res = og.admit_operator(row)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "well-formedness"
    assert "frobnicate" in res["refusal"]["reason"]


def test_self_reference_refused(op_dir):
    row = {"word": "loopy", "arity": 1, "params": ["a"],
           "definition": {"op": "loopy", "args": [{"ref": "a"}]}}
    res = og.admit_operator(row)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "well-formedness"
    assert "self-reference" in res["refusal"]["reason"]


def test_arity_mismatch_refused(op_dir):
    row = {"word": "bad", "arity": 3, "params": ["a", "b"],
           "definition": {"op": "dvd", "args": [{"ref": "a"}, {"ref": "b"}]}}
    res = og.admit_operator(row)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "well-formedness"


def test_word_shadowing_kernel_refused(op_dir):
    row = {"word": "dvd", "arity": 2, "params": ["a", "b"],
           "definition": {"op": "=", "args": [{"ref": "a"}, {"ref": "b"}]}}
    res = og.admit_operator(row)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "well-formedness"


def test_enum_only_definition_refused_no_differential(op_dir):
    # coprime is enum_only (no sound SMT rendering) -> no independent SMT
    # differential is available, so the battery refuses rather than admit on
    # enumeration alone.
    row = {"word": "rel_prime", "arity": 2, "params": ["a", "b"],
           "definition": {"op": "coprime", "args": [{"ref": "a"}, {"ref": "b"}]}}
    res = og.admit_operator(row)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "battery"
    assert "enum-only" in res["refusal"]["reason"]


# ============================================================ expansion
def test_expansion_substitutes_args_for_params(op_dir):
    _admit_and_save(MULTIPLE_OF, op_dir)
    doc = {"theorem": "t", "statements": [
        {"id": "c", "force": "demand", "quote": "q",
         "lf": {"kind": "conclusion",
                "pred": {"op": "multiple_of",
                         "args": [{"ref": "x"}, {"op": "+", "args": [
                             {"ref": "y"}, {"lit": 1}]}]}}}]}
    out = og.expand_reading_doc(doc)
    # multiple_of(x, y+1) := dvd(y+1, x)
    assert out["statements"][0]["lf"]["pred"] == {
        "op": "dvd", "args": [{"op": "+", "args": [{"ref": "y"}, {"lit": 1}]},
                              {"ref": "x"}]}


def test_transitive_expansion_over_admitted_word(op_dir):
    # even_multiple(a,b) := and(multiple_of(a,b), even(a)) -- references an
    # already-admitted derived word, so its definition must expand transitively.
    _admit_and_save(MULTIPLE_OF, op_dir)
    row = {"word": "even_multiple", "arity": 2, "params": ["a", "b"],
           "definition": {"op": "and", "args": [
               {"op": "multiple_of", "args": [{"ref": "a"}, {"ref": "b"}]},
               {"op": "even", "args": [{"ref": "a"}]}]}}
    _admit_and_save(row, op_dir)
    doc = {"theorem": "t", "statements": [
        {"id": "c", "force": "demand", "quote": "q",
         "lf": {"kind": "conclusion",
                "pred": {"op": "even_multiple",
                         "args": [{"ref": "p"}, {"ref": "q"}]}}}]}
    out = og.expand_reading_doc(doc)
    # fully lowered to kernel ops only
    ops = set()
    og._pred_ops(out["statements"][0]["lf"]["pred"], ops)
    assert ops <= og.KERNEL_OPS
    assert "multiple_of" not in ops and "even_multiple" not in ops


def test_empty_registry_expansion_is_identity(op_dir):
    doc = {"theorem": "t", "statements": [
        {"id": "c", "force": "demand", "quote": "q",
         "lf": {"kind": "conclusion",
                "pred": {"op": "dvd", "args": [{"ref": "a"}, {"ref": "b"}]}}}]}
    assert og.expand_reading_doc(doc) is doc


def test_no_derived_usage_expansion_is_identity(op_dir):
    _admit_and_save(MULTIPLE_OF, op_dir)
    doc = {"theorem": "t", "statements": [
        {"id": "c", "force": "demand", "quote": "q",
         "lf": {"kind": "conclusion",
                "pred": {"op": "even", "args": [{"ref": "a"}]}}}]}
    assert og.expand_reading_doc(doc) is doc


# ============================================================ end-to-end
_PLANTED_SOURCE = "For a and b, if b divides a then a is a multiple of b."
_PLANTED_READING = {
    "theorem": "dvd_gives_mult",
    "statements": [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "oa", "force": "presupposition", "quote": "a and b",
         "lf": {"kind": "object", "name": "a", "type": "Int"}},
        {"id": "ob", "force": "presupposition", "quote": "a and b",
         "lf": {"kind": "object", "name": "b", "type": "Int"}},
        {"id": "q", "force": "demand", "quote": "a and b",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["a", "b"]}},
        {"id": "h", "force": "presupposition", "quote": "b divides a",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "dvd", "args": [{"ref": "b"}, {"ref": "a"}]}}},
        {"id": "c", "force": "demand", "quote": "a is a multiple of b",
         "lf": {"kind": "conclusion",
                "pred": {"op": "multiple_of",
                         "args": [{"ref": "a"}, {"ref": "b"}]}}},
    ],
}


def test_planted_reading_certifies_via_expansion(op_dir):
    _admit_and_save(MULTIPLE_OF, op_dir)
    r = certify_statement(_PLANTED_SOURCE, json.dumps(_PLANTED_READING))
    assert r.ok is True, (r.stage, r.error)
    # the derived word never reached the compiler: the emitted Lean is the
    # kernel divides atom, and the theorem body carries no derived word.
    assert "multiple_of" not in r.lean_text
    assert "∣" in r.lean_text            # ∣


def test_derived_word_unadmitted_refuses_at_gate(op_dir):
    # with no admission, multiple_of is just an unknown atom -> parse refuses.
    r = certify_statement(_PLANTED_SOURCE, json.dumps(_PLANTED_READING))
    assert r.ok is False
    assert r.stage == "math-reading-gate"


# ============================================================ tamper safety
def test_tampered_row_refuses_to_lower(op_dir):
    _admit_and_save(MULTIPLE_OF, op_dir)
    path = os.path.join(op_dir, "admitted.json")
    with open(path) as fh:
        disk = json.load(fh)
    # edit the definition after admission: hash no longer matches cert id.
    disk["multiple_of"]["row"]["definition"] = {
        "op": "dvd", "args": [{"ref": "a"}, {"ref": "b"}]}
    with open(path, "w") as fh:
        json.dump(disk, fh)
    og.reload()
    with pytest.raises(BadMathReading) as ei:
        parse_math_reading(json.dumps(_PLANTED_READING), _PLANTED_SOURCE)
    assert "cert" in str(ei.value).lower() and "mismatch" in str(ei.value).lower()
    # and it surfaces as a pipeline refusal, never a silent green
    r = certify_statement(_PLANTED_SOURCE, json.dumps(_PLANTED_READING))
    assert r.ok is False and r.stage == "math-reading-gate"


# ============================================================ byte-identity
def _serial(res):
    d = dataclasses.asdict(res)
    d["statement_cert"] = None if res.statement_cert is None else "CERT"
    return d


def _golden():
    with open(os.path.join(HERE, "tests", "golden",
                           "operator_growth_zero_rows.json")) as fh:
        return json.load(fh)


def test_zero_rows_byte_identical_to_golden(op_dir):
    golden = _golden()
    for name in sorted(golden):
        rj, src = split_envelope(open(os.path.join(
            HERE, "specs", "mathsources", "readings", name)).read())
        res = certify_statement(src, rj)
        assert common.canonical_json(_serial(res)) == \
            common.canonical_json(golden[name]), name


def test_populated_registry_byte_identical_for_non_using_readings(op_dir):
    # even with multiple_of admitted, readings that do NOT use it are unchanged.
    _admit_and_save(MULTIPLE_OF, op_dir)
    golden = _golden()
    for name in sorted(golden):
        rj, src = split_envelope(open(os.path.join(
            HERE, "specs", "mathsources", "readings", name)).read())
        res = certify_statement(src, rj)
        assert common.canonical_json(_serial(res)) == \
            common.canonical_json(golden[name]), name


# ============================================================ proposed staging
def test_proposed_row_admits(op_dir):
    # the committed proposed/multiple_of.json is a valid, admissible row.
    proposed = og.load_proposed(
        op_dir=os.path.join(HERE, "specs", "mathsources", "operators"))
    words = {r["word"] for r in proposed}
    assert "multiple_of" in words
    row = next(r for r in proposed if r["word"] == "multiple_of")
    assert og.admit_operator(row)["admitted"] is True
