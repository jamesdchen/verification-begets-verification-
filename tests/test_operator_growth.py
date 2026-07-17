"""Teeth for R2 autonomous operator-table growth (generators/operator_growth.py).

All LLM-free and Lean-free.  Relational / structural asserts only; no absolute
solver-count constants.  The battery uses z3 + decidable enumeration and
tolerates an absent cvc5 honestly, so these pass whether or not cvc5 is present.

WP-T4a (COMPRESSION.md §11.4 Critical 1) closed the unpriced-vocabulary hole:
admission now runs a TRIVIAL-ALIAS gate (pre-battery) and a PRICING gate (after
the battery, strict corpus-DL drop in the `mdl_macros` currency), and
`save_admitted` is the sole admitter (re-runs the battery, cert-id equality) over
an append-only registry.  The non-alias fixture used throughout is `congm`
(mod-congruence), the real §11.4 candidate that pays; `multiple_of := dvd(b,a)`
is now a trivial alias and is exercised only as the grandfathered / refused case.
"""
import copy
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


# ============================================================ fixtures / helpers
# congm(a,b,m) := (a mod m) = (b mod m) -- a `=`-rooted pred over two `mod`
# terms, so NOT a single-kernel-atom alias.  It is the real §11.4 candidate that
# clears the pricing gate on the committed corpus.
CONGM = {"word": "congm", "arity": 3, "params": ["a", "b", "m"],
         "definition": {"op": "=", "args": [
             {"op": "mod", "args": [{"ref": "a"}, {"ref": "m"}]},
             {"op": "mod", "args": [{"ref": "b"}, {"ref": "m"}]}]}}

# multiple_of := dvd(b,a): a single kernel operator over distinct param refs --
# the trivial-alias hazard.  Persisted (grandfathered) in specs/.../admitted.json.
MULTIPLE_OF = {"word": "multiple_of", "arity": 2, "params": ["a", "b"],
               "definition": {"op": "dvd", "args": [{"ref": "b"}, {"ref": "a"}]}}


def _congsub(x, y, m):
    """A concrete `congm`-shaped kernel subtree (x mod m) = (y mod m)."""
    return {"op": "=", "args": [
        {"op": "mod", "args": [{"ref": x}, {"ref": m}]},
        {"op": "mod", "args": [{"ref": y}, {"ref": m}]}]}


def _congm_reading(n_subtrees=2):
    """A reading carrying `n_subtrees` congm-shaped preds -- a pricing witness."""
    pairs = [("a", "b"), ("c", "d"), ("e", "f"), ("g", "h")][:n_subtrees]
    stmts = []
    for i, (x, y) in enumerate(pairs):
        stmts.append({"id": f"h{i}", "force": "presupposition", "quote": "q",
                      "lf": {"kind": "hypothesis", "pred": _congsub(x, y, "m")}})
    return {"theorem": "witness", "statements": stmts}


# Two readings, two congm subtrees each: saving 44 > model_bits 27, 2 witnesses
# -> congm clears the pricing gate.  Shared by the admission/expansion tests.
CONGM_CORPUS = [_congm_reading(2), _congm_reading(2)]


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


def _admit_and_save(row, op_dir, corpus=CONGM_CORPUS):
    res = og.admit_operator(row, pricing_corpus=corpus)
    assert res["admitted"], res
    og.save_admitted({row["word"]: {"row": res["row"], "cert": res["cert"]}},
                     pricing_corpus=corpus)
    og.reload()
    return res


def _real_corpus():
    """The real pricing corpus: the certified governed exogenous readings, taken
    straight from the committed bench checkpoint (the same readings the WP-T4
    subtree census in results/tower_census.json is built over)."""
    path = os.path.join(HERE, "results", "formalize_bench_state.jsonl")
    out = []
    with open(path) as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("arm") != "governed" or not rec.get("certified"):
                continue
            rj = rec.get("reading_json") or ""
            if not rj:
                continue
            doc = json.loads(rj)
            if isinstance(doc, dict) and isinstance(doc.get("statements"), list):
                out.append(doc)
    return out


# ============================================================ (a) admission
def test_congm_admits_with_green_certificate(op_dir):
    res = og.admit_operator(CONGM, pricing_corpus=CONGM_CORPUS)
    assert res["admitted"] is True
    cert = res["cert"]
    assert cert["kind"] == "operator-admission"
    assert cert["word"] == "congm"
    # the id binds the canonical row to the battery digest (NOT the corpus)
    assert cert["id"] == og.cert_id(res["row"], cert["battery_digest"])
    b = cert["battery"]
    assert b["satisfiable"] and b["refutable"]
    # both carriers exercised; every instance carries an enum verdict
    assert set(b["carriers"]) == {"Nat", "Int"}
    assert all("enum" in inst for inst in b["instances"])
    # z3 corroborated the enumeration on at least some instance
    assert b["smt_confirmations"] > 0
    # pricing evidence rides in the cert: the corpus DL strictly dropped
    pr = cert["pricing"]
    assert pr["saving"] > pr["model_bits"]
    assert pr["witnesses"] >= 2
    assert pr["dl_after"] < pr["dl_before"]


def test_admission_is_deterministic(op_dir):
    a = og.admit_operator(CONGM, pricing_corpus=CONGM_CORPUS)
    b = og.admit_operator(CONGM, pricing_corpus=CONGM_CORPUS)
    assert a["cert"]["id"] == b["cert"]["id"]
    assert a["cert"]["battery_digest"] == b["cert"]["battery_digest"]


def test_cert_id_is_independent_of_the_pricing_corpus(op_dir):
    # the id binds row + battery only, so a different (still-paying) corpus
    # yields the SAME cert id -- pricing is evidence, not identity.
    bigger = CONGM_CORPUS + [_congm_reading(2)]
    a = og.admit_operator(CONGM, pricing_corpus=CONGM_CORPUS)
    b = og.admit_operator(CONGM, pricing_corpus=bigger)
    assert a["admitted"] and b["admitted"]
    assert a["cert"]["id"] == b["cert"]["id"]
    # ... but the recorded pricing arithmetic differs
    assert b["cert"]["pricing"]["saving"] > a["cert"]["pricing"]["saving"]


def test_every_battery_instance_agrees_z3_enum(op_dir):
    res = og.admit_operator(CONGM, pricing_corpus=CONGM_CORPUS)
    for inst in res["cert"]["battery"]["instances"]:
        if inst["z3"] in ("sat", "unsat"):
            assert (inst["z3"] == "sat") == inst["enum"]
        if inst["cvc5"] in ("sat", "unsat"):
            assert (inst["cvc5"] == "sat") == inst["enum"]


# B2 tooth: congruence-mod (the §11.4 motivating word) uses a term `mod(_, m)`
# that a solver could evaluate freely at m=0.  Before the mod-by-zero mirror
# fix the battery REFUSED it with "differential disagreement ... enum=False but
# z3=sat" at m=0; with the guarded rendering enum and z3 agree there.
def test_congruence_mod_no_longer_refused_by_mod_by_zero_gap(op_dir):
    res = og.admit_operator(CONGM, registry={}, pricing_corpus=CONGM_CORPUS)
    if not res["admitted"]:
        assert "differential disagreement" not in res["refusal"]["reason"]
    else:
        insts = res["cert"]["battery"]["instances"]
        m0 = [i for i in insts if i["assignment"].get("m") == 0]
        assert m0                                   # the battery reaches m=0
        for inst in m0:
            if inst["z3"] in ("sat", "unsat"):
                assert (inst["z3"] == "sat") == inst["enum"]


# ==================================================== (b) trivial-alias refusal
def test_divides_alias_refused_pre_battery(op_dir):
    row = {"word": "divides_alias", "arity": 2, "params": ["a", "b"],
           "definition": {"op": "dvd", "args": [{"ref": "a"}, {"ref": "b"}]}}
    res = og.admit_operator(row, pricing_corpus=CONGM_CORPUS)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "trivial-alias"
    assert "alias" in res["refusal"]["reason"]
    assert "dvd" in res["refusal"]["reason"]


def test_multiple_of_is_a_trivial_alias(op_dir):
    # the reordering dvd(b,a) is still a single kernel atom over distinct refs.
    res = og.admit_operator(MULTIPLE_OF, pricing_corpus=CONGM_CORPUS)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "trivial-alias"


def test_compound_word_rename_is_not_an_alias(op_dir):
    # a rename of an admitted COMPOUND word (congm) is NOT a bare kernel atom,
    # so the alias gate must NOT fire -- it is judged on economics instead.
    _admit_and_save(CONGM, op_dir)
    reg = og.load_admitted()
    row = {"word": "congm_alias", "arity": 3, "params": ["x", "y", "z"],
           "definition": {"op": "congm",
                          "args": [{"ref": "x"}, {"ref": "y"}, {"ref": "z"}]}}
    kd = og._expand_definition_to_kernel(row, reg)
    assert og._is_trivial_alias(kd) is False
    res = og.admit_operator(row, registry=reg, pricing_corpus=[])
    assert res["refusal"]["stage"] != "trivial-alias"


# ============================================================ (c) pricing gate
def test_no_pricing_corpus_refuses_fail_closed(op_dir):
    res = og.admit_operator(CONGM)          # no pricing_corpus
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "pricing"
    assert "no pricing corpus" in res["refusal"]["reason"]


def test_planted_subtree_admits_at_2_readings_refuses_at_1_on_economics(op_dir):
    # A planted congm-bearing corpus: each reading carries two congm subtrees
    # (saving 22/reading) against model_bits 27.  ONE reading cannot pay (22 <
    # 27) and is refused ON ECONOMICS; TWO readings pay (44 > 27) and admit.
    one = og.admit_operator(CONGM, registry={},
                            pricing_corpus=[_congm_reading(2)])
    assert one["admitted"] is False
    assert one["refusal"]["stage"] == "pricing"
    r1 = one["refusal"]["reason"]
    assert "strict corpus-DL drop" in r1                   # economic refusal
    assert "saving" in r1 and "model_bits" in r1           # names the arithmetic

    two = og.admit_operator(CONGM, registry={},
                            pricing_corpus=[_congm_reading(2), _congm_reading(2)])
    assert two["admitted"] is True
    pr = two["cert"]["pricing"]
    assert pr["saving"] > pr["model_bits"] and pr["witnesses"] >= 2


def test_unused_word_refused_on_economics(op_dir):
    # a corpus in which congm never appears: zero saving, refused (not fail-
    # closed -- a real corpus, just no witnesses).
    empty_witness = {"theorem": "t", "statements": [
        {"id": "c", "force": "demand", "quote": "q",
         "lf": {"kind": "conclusion",
                "pred": {"op": "even", "args": [{"ref": "a"}]}}}]}
    res = og.admit_operator(CONGM, registry={},
                            pricing_corpus=[empty_witness, empty_witness])
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "pricing"
    assert "0 uses" in res["refusal"]["reason"]


def test_congm_admits_and_even_sum_refuses_on_the_real_corpus(op_dir):
    # The headline §11.4 numbers, priced against the REAL certified governed
    # corpus.  congm pays handsomely; even_sum -- a real non-alias census
    # candidate -- does NOT pay under the current currency.
    corpus = _real_corpus()
    assert len(corpus) >= 30
    congm_kd = og._expand_definition_to_kernel(CONGM, {})
    cp = og.price_operator(CONGM, congm_kd, corpus)
    assert cp["saving"] > cp["model_bits"]        # admits on economics
    assert cp["witnesses"] >= 2

    even_sum = {"word": "even_sum", "arity": 2, "params": ["a", "b"],
                "definition": {"op": "even", "args": [
                    {"op": "+", "args": [{"ref": "a"}, {"ref": "b"}]}]}}
    es_kd = og._expand_definition_to_kernel(even_sum, {})
    ep = og.price_operator(even_sum, es_kd, corpus)
    assert ep["saving"] <= ep["model_bits"]       # does not pay -> would refuse

    # and end-to-end through admit_operator with the real corpus:
    res = og.admit_operator(CONGM, registry={}, pricing_corpus=corpus)
    assert res["admitted"] is True
    res2 = og.admit_operator(even_sum, registry={}, pricing_corpus=corpus)
    assert res2["admitted"] is False
    assert res2["refusal"]["stage"] == "pricing"


# =========================================================== (a) other refusals
def test_vacuous_tautology_refused(op_dir):
    row = {"word": "always_geq", "arity": 2, "params": ["a", "b"],
           "definition": {"op": "or", "args": [
               {"op": "<=", "args": [{"ref": "a"}, {"ref": "b"}]},
               {"op": "<=", "args": [{"ref": "b"}, {"ref": "a"}]}]}}
    res = og.admit_operator(row, pricing_corpus=CONGM_CORPUS)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "nonvacuity"
    assert "tautology" in res["refusal"]["reason"].lower()


def test_contradiction_refused_as_vacuous(op_dir):
    row = {"word": "never_eq", "arity": 1, "params": ["a"],
           "definition": {"op": "!=", "args": [{"ref": "a"}, {"ref": "a"}]}}
    res = og.admit_operator(row, pricing_corpus=CONGM_CORPUS)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "nonvacuity"
    assert "contradiction" in res["refusal"]["reason"].lower()


def test_unknown_operator_refused_at_wellformedness(op_dir):
    row = {"word": "weird", "arity": 1, "params": ["a"],
           "definition": {"op": "frobnicate", "args": [{"ref": "a"}]}}
    res = og.admit_operator(row, pricing_corpus=CONGM_CORPUS)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "well-formedness"
    assert "frobnicate" in res["refusal"]["reason"]


def test_self_reference_refused(op_dir):
    row = {"word": "loopy", "arity": 1, "params": ["a"],
           "definition": {"op": "loopy", "args": [{"ref": "a"}]}}
    res = og.admit_operator(row, pricing_corpus=CONGM_CORPUS)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "well-formedness"
    assert "self-reference" in res["refusal"]["reason"]


def test_arity_mismatch_refused(op_dir):
    row = {"word": "bad", "arity": 3, "params": ["a", "b"],
           "definition": {"op": "dvd", "args": [{"ref": "a"}, {"ref": "b"}]}}
    res = og.admit_operator(row, pricing_corpus=CONGM_CORPUS)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "well-formedness"


def test_word_shadowing_kernel_refused(op_dir):
    row = {"word": "dvd", "arity": 2, "params": ["a", "b"],
           "definition": {"op": "=", "args": [{"ref": "a"}, {"ref": "b"}]}}
    res = og.admit_operator(row, pricing_corpus=CONGM_CORPUS)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "well-formedness"


def test_enum_only_definition_refused_no_differential(op_dir):
    # coprime is enum_only (no sound SMT rendering); wrapped in a `+` so it is
    # not a bare kernel alias -> it reaches the battery and refuses there for
    # want of an independent SMT differential.
    row = {"word": "rel_prime_sum", "arity": 2, "params": ["a", "b"],
           "definition": {"op": "coprime", "args": [
               {"op": "+", "args": [{"ref": "a"}, {"lit": 1}]}, {"ref": "b"}]}}
    res = og.admit_operator(row, pricing_corpus=CONGM_CORPUS)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "battery"
    assert "enum-only" in res["refusal"]["reason"]


# ============================================================ expansion
def test_expansion_substitutes_args_for_params(op_dir):
    _admit_and_save(CONGM, op_dir)
    doc = {"theorem": "t", "statements": [
        {"id": "c", "force": "demand", "quote": "q",
         "lf": {"kind": "conclusion",
                "pred": {"op": "congm",
                         "args": [{"ref": "x"},
                                  {"op": "+", "args": [{"ref": "y"}, {"lit": 1}]},
                                  {"ref": "n"}]}}}]}
    out = og.expand_reading_doc(doc)
    # congm(x, y+1, n) := (x mod n) = ((y+1) mod n)
    assert out["statements"][0]["lf"]["pred"] == {
        "op": "=", "args": [
            {"op": "mod", "args": [{"ref": "x"}, {"ref": "n"}]},
            {"op": "mod", "args": [
                {"op": "+", "args": [{"ref": "y"}, {"lit": 1}]}, {"ref": "n"}]}]}


def test_transitive_expansion_over_admitted_word(op_dir):
    # even_congm(a,b,m) := and(congm(a,b,m), even(a)) references an already-
    # admitted derived word, so its definition must expand transitively.
    _admit_and_save(CONGM, op_dir)
    even_congm = {"word": "even_congm", "arity": 3, "params": ["a", "b", "m"],
                  "definition": {"op": "and", "args": [
                      {"op": "congm", "args": [
                          {"ref": "a"}, {"ref": "b"}, {"ref": "m"}]},
                      {"op": "even", "args": [{"ref": "a"}]}]}}
    # a paying corpus for even_congm (saving 44 > model_bits 27 at 2 witnesses).
    ec_sub = {"op": "and", "args": [
        _congsub("a", "b", "m"), {"op": "even", "args": [{"ref": "a"}]}]}
    ec_reading = {"theorem": "w", "statements": [
        {"id": "h", "force": "presupposition", "quote": "q",
         "lf": {"kind": "hypothesis", "pred": ec_sub}}]}
    _admit_and_save(even_congm, op_dir,
                    corpus=[ec_reading, copy.deepcopy(ec_reading)])
    doc = {"theorem": "t", "statements": [
        {"id": "c", "force": "demand", "quote": "q",
         "lf": {"kind": "conclusion",
                "pred": {"op": "even_congm",
                         "args": [{"ref": "p"}, {"ref": "q"}, {"ref": "r"}]}}}]}
    out = og.expand_reading_doc(doc)
    ops = set()
    og._pred_ops(out["statements"][0]["lf"]["pred"], ops)
    assert ops <= og.KERNEL_OPS
    assert "congm" not in ops and "even_congm" not in ops


def test_empty_registry_expansion_is_identity(op_dir):
    doc = {"theorem": "t", "statements": [
        {"id": "c", "force": "demand", "quote": "q",
         "lf": {"kind": "conclusion",
                "pred": {"op": "dvd", "args": [{"ref": "a"}, {"ref": "b"}]}}}]}
    assert og.expand_reading_doc(doc) is doc


def test_no_derived_usage_expansion_is_identity(op_dir):
    _admit_and_save(CONGM, op_dir)
    doc = {"theorem": "t", "statements": [
        {"id": "c", "force": "demand", "quote": "q",
         "lf": {"kind": "conclusion",
                "pred": {"op": "even", "args": [{"ref": "a"}]}}}]}
    assert og.expand_reading_doc(doc) is doc


# ============================================================ end-to-end
_PLANTED_SOURCE = ("For all a, b and m, if a and b are congruent mod m then a "
                   "and b are congruent mod m.")
_PLANTED_READING = {
    "theorem": "cong_refl_planted",
    "statements": [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "oa", "force": "presupposition", "quote": "a, b and m",
         "lf": {"kind": "object", "name": "a", "type": "Int"}},
        {"id": "ob", "force": "presupposition", "quote": "a, b and m",
         "lf": {"kind": "object", "name": "b", "type": "Int"}},
        {"id": "om", "force": "presupposition", "quote": "a, b and m",
         "lf": {"kind": "object", "name": "m", "type": "Int"}},
        {"id": "q", "force": "demand", "quote": "a, b and m",
         "lf": {"kind": "quantifier", "binder": "forall",
                "objects": ["a", "b", "m"]}},
        {"id": "h", "force": "presupposition",
         "quote": "a and b are congruent mod m",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "congm",
                         "args": [{"ref": "a"}, {"ref": "b"}, {"ref": "m"}]}}},
        {"id": "c", "force": "demand", "quote": "a and b are congruent mod m",
         "lf": {"kind": "conclusion",
                "pred": {"op": "congm",
                         "args": [{"ref": "a"}, {"ref": "b"}, {"ref": "m"}]}}},
    ],
}


def test_planted_reading_certifies_via_expansion(op_dir):
    _admit_and_save(CONGM, op_dir)
    r = certify_statement(_PLANTED_SOURCE, json.dumps(_PLANTED_READING))
    assert r.ok is True, (r.stage, r.error)
    # the derived word never reached the compiler: the emitted Lean is the
    # kernel `%` mod atom, and the theorem body carries no derived word.
    assert "congm" not in r.lean_text
    assert "%" in r.lean_text


def test_derived_word_unadmitted_refuses_at_gate(op_dir):
    # with no admission, congm is just an unknown atom -> parse refuses.
    r = certify_statement(_PLANTED_SOURCE, json.dumps(_PLANTED_READING))
    assert r.ok is False
    assert r.stage == "math-reading-gate"


# ============================================================ tamper safety
def test_tampered_row_refuses_to_lower(op_dir):
    _admit_and_save(CONGM, op_dir)
    path = os.path.join(op_dir, "admitted.json")
    with open(path) as fh:
        disk = json.load(fh)
    # edit the definition after admission: hash no longer matches cert id.
    disk["congm"]["row"]["definition"] = {
        "op": "=", "args": [
            {"op": "mod", "args": [{"ref": "b"}, {"ref": "m"}]},
            {"op": "mod", "args": [{"ref": "a"}, {"ref": "m"}]}]}
    with open(path, "w") as fh:
        json.dump(disk, fh)
    og.reload()
    with pytest.raises(BadMathReading) as ei:
        parse_math_reading(json.dumps(_PLANTED_READING), _PLANTED_SOURCE)
    assert "cert" in str(ei.value).lower() and "mismatch" in str(ei.value).lower()
    # and it surfaces as a pipeline refusal, never a silent green
    r = certify_statement(_PLANTED_SOURCE, json.dumps(_PLANTED_READING))
    assert r.ok is False and r.stage == "math-reading-gate"


# ============================================ save_admitted: sole admitter etc.
def test_save_refuses_forged_cert_id(op_dir):
    res = og.admit_operator(CONGM, pricing_corpus=CONGM_CORPUS)
    entry = {"congm": {"row": res["row"], "cert": dict(res["cert"])}}
    entry["congm"]["cert"]["id"] = "0" * 64            # forge the id
    with pytest.raises(og.SaveRefused) as ei:
        og.save_admitted(entry, pricing_corpus=CONGM_CORPUS)
    assert "cert id mismatch" in str(ei.value)


def test_save_refuses_when_row_does_not_readmit(op_dir):
    # hand save a green-looking entry but withhold the pricing corpus: the
    # sole-admitter re-run refuses fail-closed, so nothing is persisted.
    res = og.admit_operator(CONGM, pricing_corpus=CONGM_CORPUS)
    entry = {"congm": {"row": res["row"], "cert": res["cert"]}}
    with pytest.raises(og.SaveRefused) as ei:
        og.save_admitted(entry)                        # no pricing_corpus
    assert "re-admission refused" in str(ei.value)
    assert not os.path.exists(os.path.join(op_dir, "admitted.json"))


def test_save_is_idempotent_on_same_digest(op_dir):
    _admit_and_save(CONGM, op_dir)
    path = os.path.join(op_dir, "admitted.json")
    first = open(path).read()
    # re-save the identical row: append-only allows a same-digest re-save.
    res = og.admit_operator(CONGM, pricing_corpus=CONGM_CORPUS)
    og.save_admitted({"congm": {"row": res["row"], "cert": res["cert"]}},
                     pricing_corpus=CONGM_CORPUS)
    assert open(path).read() == first                  # byte-idempotent


def test_save_refuses_different_digest_overwrite(op_dir):
    _admit_and_save(CONGM, op_dir)
    # a DIFFERENT congm (swapped args) admits on its own, but overwriting the
    # existing word with it would rewrite already-certified corpus bytes.
    congm2 = {"word": "congm", "arity": 3, "params": ["a", "b", "m"],
              "definition": {"op": "=", "args": [
                  {"op": "mod", "args": [{"ref": "b"}, {"ref": "m"}]},
                  {"op": "mod", "args": [{"ref": "a"}, {"ref": "m"}]}]}}
    assert og.row_digest(congm2) != og.row_digest(CONGM)
    res = og.admit_operator(congm2, registry={}, pricing_corpus=CONGM_CORPUS)
    assert res["admitted"]
    with pytest.raises(og.SaveRefused) as ei:
        og.save_admitted({"congm": {"row": res["row"], "cert": res["cert"]}},
                         pricing_corpus=CONGM_CORPUS)
    assert "append-only" in str(ei.value)


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
    # even with congm admitted, readings that do NOT use it are unchanged.
    _admit_and_save(CONGM, op_dir)
    golden = _golden()
    for name in sorted(golden):
        rj, src = split_envelope(open(os.path.join(
            HERE, "specs", "mathsources", "readings", name)).read())
        res = certify_statement(src, rj)
        assert common.canonical_json(_serial(res)) == \
            common.canonical_json(golden[name]), name


# ==================================================== grandfathered admitted.json
def test_committed_admitted_rows_still_re_battery_green(op_dir):
    # The persisted specs/.../admitted.json rows were admitted under the
    # pre-WP-T4a gate.  Their gate-correctness battery (well-formedness /
    # differential / compile) is STILL green -- we assert that and DO NOT touch
    # specs/.  Any row that would now fail the NEW alias/pricing gate is
    # grandfathered, documented by test_multiple_of_is_grandfathered below.
    op_path = os.path.join(HERE, "specs", "mathsources", "operators")
    with open(os.path.join(op_path, "admitted.json")) as fh:
        admitted = json.load(fh)
    assert admitted                                    # there is at least one row
    for word, entry in admitted.items():
        row = entry["row"]
        reg = {w: e for w, e in admitted.items() if w != word}
        wf_ok, wf = og._check_wellformed(row, reg)
        assert wf_ok, (word, wf)
        bat_ok, reason, battery = og._run_battery(
            row, reg, og.DEFAULT_BATTERY_BOUND, og.DEFAULT_MAX_INSTANCES)
        assert bat_ok, (word, reason)
        assert battery["satisfiable"] and battery["refutable"]
        breg = dict(reg)
        breg[word] = {"row": og.canonical_row(row)}
        comp_ok, comp = og._compile_roundtrip(row, breg)
        assert comp_ok, (word, comp)


def test_multiple_of_is_grandfathered(op_dir):
    # multiple_of := dvd(b,a) is persisted (and still re-batteries green above),
    # but under the WP-T4a gate it is a TRIVIAL ALIAS: admit_operator now
    # refuses it pre-battery.  It survives only as a grandfathered row; specs/
    # is untouched.
    kd = og._expand_definition_to_kernel(MULTIPLE_OF, {})
    assert og._is_trivial_alias(kd) is True
    # re-battery is green (gate-correctness intact) ...
    bat_ok, _, _ = og._run_battery(
        MULTIPLE_OF, {}, og.DEFAULT_BATTERY_BOUND, og.DEFAULT_MAX_INSTANCES)
    assert bat_ok
    # ... but the NEW gate refuses it as an alias.
    res = og.admit_operator(MULTIPLE_OF, pricing_corpus=CONGM_CORPUS)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "trivial-alias"


# ============================================================ proposed staging
def test_committed_proposed_multiple_of_now_refused_as_alias(op_dir):
    # the committed proposed/multiple_of.json was admissible under the old gate;
    # WP-T4a refuses it as a trivial alias (the census flagged it too).
    proposed = og.load_proposed(
        op_dir=os.path.join(HERE, "specs", "mathsources", "operators"))
    words = {r["word"] for r in proposed}
    assert "multiple_of" in words
    row = next(r for r in proposed if r["word"] == "multiple_of")
    res = og.admit_operator(row, pricing_corpus=CONGM_CORPUS)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "trivial-alias"
