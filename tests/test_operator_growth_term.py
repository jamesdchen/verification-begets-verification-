"""Teeth for D1 of the compression workstream: TERM-role vocabulary in the R2
operator-growth admission path (generators/operator_growth.py).

All LLM-free and Lean-free (z3 + the fragment evaluator; absent cvc5 tolerated
honestly).  D1 extends the admission path so it can mint value-producing
function words (``sq(a) := a * a``, role "term") alongside the pred-role words
it already mints, with:

  * the SAME closure/self-reference discipline, validated as a TERM through the
    real ``_check_term`` machinery;
  * a VALUE battery: the expanded kernel term's value is computed by
    ``math_eval.eval_term`` and recorded per instance, corroborated by the
    ground-equation SMT differential;
  * degeneracy refusals in place of nonvacuity (a battery-constant term is a
    literal in disguise) and the trivial-alias rule adapted to terms (a bare
    kernel term op over distinct param refs is a rename; a bare ref/lit is a
    projection/literal);
  * the ONE DL currency, with rewrite savings counted over TERM-subtree matches
    in the corpus preds;
  * use-time symmetry: an admitted term word inside a reading's terms expands
    to kernel BEFORE the gates/compile, so the compiled Lean inlines the kernel
    expansion (no new Lean defs);
  * full backward compatibility: role absent = "pred"; the committed
    admitted.json rows load, hash and verify unchanged.
"""
import copy
import json
import os
import tempfile

import pytest

import common
from generators import operator_growth as og
from generators.math_compile import compile_math_reading
from generators.math_reading import parse_math_reading, BadMathReading

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ============================================================ fixtures / helpers
# sq(a) := a * a -- a term-role word.  The repeated ref makes it a diagonal, NOT
# a trivial alias (a bare kernel op over DISTINCT refs would be).
SQ = {"word": "sq", "arity": 1, "params": ["a"], "role": "term",
      "definition": {"op": "*", "args": [{"ref": "a"}, {"ref": "a"}]}}


def _sq_sub(x):
    """A concrete sq-shaped kernel TERM subtree x * x."""
    return {"op": "*", "args": [{"ref": x}, {"ref": x}]}


def _sq_reading(n_subtrees=3):
    """A reading whose hypothesis preds carry `n_subtrees` x*x TERM subtrees
    (each inside a kernel `<=` atom) -- a pricing witness for sq."""
    names = ["a", "b", "c", "d"][:n_subtrees]
    stmts = []
    for i, x in enumerate(names):
        stmts.append({"id": f"h{i}", "force": "presupposition", "quote": "q",
                      "lf": {"kind": "hypothesis",
                             "pred": {"op": "<=",
                                      "args": [_sq_sub(x), {"ref": "n"}]}}})
    return {"theorem": "witness", "statements": stmts}


# Two readings, three x*x subtrees each: saving 18 > model_bits 11, 2 witnesses
# -> sq clears the pricing gate on term-subtree matches alone.
SQ_CORPUS = [_sq_reading(3), _sq_reading(3)]

# congm -- the pred-role fixture from test_operator_growth.py, reused here to
# prove a pred admission still works untouched next to the term path.
CONGM = {"word": "congm", "arity": 3, "params": ["a", "b", "m"],
         "definition": {"op": "=", "args": [
             {"op": "mod", "args": [{"ref": "a"}, {"ref": "m"}]},
             {"op": "mod", "args": [{"ref": "b"}, {"ref": "m"}]}]}}


def _congsub(x, y, m):
    return {"op": "=", "args": [
        {"op": "mod", "args": [{"ref": x}, {"ref": m}]},
        {"op": "mod", "args": [{"ref": y}, {"ref": m}]}]}


def _congm_reading():
    stmts = []
    for i, (x, y) in enumerate([("a", "b"), ("c", "d")]):
        stmts.append({"id": f"h{i}", "force": "presupposition", "quote": "q",
                      "lf": {"kind": "hypothesis", "pred": _congsub(x, y, "m")}})
    return {"theorem": "witness", "statements": stmts}


@pytest.fixture
def op_dir(monkeypatch):
    """An isolated, initially empty operator registry."""
    d = tempfile.mkdtemp(prefix="op-growth-term-test-")
    monkeypatch.setenv("CGB_OPERATORS_DIR", d)
    og.reload()
    yield d
    og.reload()


def _admit_and_save(row, corpus):
    res = og.admit_operator(row, pricing_corpus=corpus)
    assert res["admitted"], res
    og.save_admitted({row["word"]: {"row": res["row"], "cert": res["cert"]}},
                     pricing_corpus=corpus)
    og.reload()
    return res


# ============================================================ (1) admission
def test_sq_admits_end_to_end_with_value_battery(op_dir):
    res = og.admit_operator(SQ, pricing_corpus=SQ_CORPUS)
    assert res["admitted"] is True, res
    cert = res["cert"]
    assert cert["kind"] == "operator-admission"
    assert cert["word"] == "sq"
    assert cert["role"] == "term"
    # the cert id binds the canonical row (role included) to the battery digest
    assert cert["id"] == og.cert_id(res["row"], cert["battery_digest"])
    assert res["row"]["role"] == "term"
    b = cert["battery"]
    assert b["role"] == "term"
    assert set(b["carriers"]) == {"Nat", "Int"}
    # VALUE battery: every instance records the computed kernel-term value ...
    assert all("value" in inst for inst in b["instances"])
    # ... and the values are the actual squares (spot-check both carriers)
    by = {(i["carrier"], i["assignment"]["a"]): i["value"]
          for i in b["instances"]}
    assert by[("Nat", 3)] == 9
    assert by[("Int", -2)] == 4
    assert by[("Nat", 0)] == 0
    # not constant, and z3 corroborated the evaluator's values
    assert b["distinct_values"] > 1
    assert b["smt_confirmations"] > 0
    # DL-priced in the one currency, over TERM-subtree matches
    pr = cert["pricing"]
    assert pr["saving"] > pr["model_bits"]
    assert pr["witnesses"] >= 2
    assert pr["dl_after"] < pr["dl_before"]


def test_term_admission_is_deterministic(op_dir):
    a = og.admit_operator(SQ, pricing_corpus=SQ_CORPUS)
    b = og.admit_operator(SQ, pricing_corpus=SQ_CORPUS)
    assert a["cert"]["id"] == b["cert"]["id"]
    assert a["cert"]["battery_digest"] == b["cert"]["battery_digest"]


def test_term_battery_value_agrees_with_smt(op_dir):
    res = og.admit_operator(SQ, pricing_corpus=SQ_CORPUS)
    for inst in res["cert"]["battery"]["instances"]:
        # a "sat" verdict corroborates the ground equation term = value; an
        # "unsat" would have refused admission outright.
        assert inst["z3"] in ("sat", "unknown", "error")
        assert inst["cvc5"] in ("sat", "unknown", "absent")


def test_save_and_load_roundtrip_preserves_role(op_dir):
    _admit_and_save(SQ, SQ_CORPUS)
    reg = og.load_admitted()
    assert reg["sq"]["row"]["role"] == "term"
    # the persisted row re-verifies (role is hash-bound via canonical_row)
    og._verify_entry("sq", reg["sq"])


def test_tampered_role_refuses_to_lower(op_dir):
    # role participates in the row hash: flipping it on disk after admission is
    # tamper, and the word refuses to lower at use time.
    _admit_and_save(SQ, SQ_CORPUS)
    path = os.path.join(op_dir, "admitted.json")
    with open(path) as fh:
        disk = json.load(fh)
    del disk["sq"]["row"]["role"]                 # silently "become" a pred row
    with open(path, "w") as fh:
        json.dump(disk, fh)
    og.reload()
    doc = {"theorem": "t", "statements": [
        {"id": "c", "force": "demand", "quote": "q",
         "lf": {"kind": "conclusion", "pred": {"op": "=", "args": [
             {"op": "sq", "args": [{"ref": "a"}]}, {"lit": 4}]}}}]}
    with pytest.raises(og.OperatorExpansionError) as ei:
        og.expand_reading_doc(doc)
    assert "mismatch" in str(ei.value)


# ============================================================ (2) refusals
def test_plus2_is_a_trivial_alias_of_kernel_plus(op_dir):
    # plus2(a,b) := a + b IS a bare kernel term op over distinct param refs --
    # a pure rename, refused pre-battery exactly like the pred-role case.
    plus2 = {"word": "plus2", "arity": 2, "params": ["a", "b"], "role": "term",
             "definition": {"op": "+", "args": [{"ref": "a"}, {"ref": "b"}]}}
    res = og.admit_operator(plus2, pricing_corpus=SQ_CORPUS)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "trivial-alias"
    assert "'+'" in res["refusal"]["reason"]


def test_bare_ref_projection_is_trivial(op_dir):
    proj = {"word": "ident", "arity": 1, "params": ["a"], "role": "term",
            "definition": {"ref": "a"}}
    res = og.admit_operator(proj, pricing_corpus=SQ_CORPUS)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "trivial-alias"
    assert "projection" in res["refusal"]["reason"]


def test_constant_term_degeneracy_refused(op_dir):
    # a * 0 is 0 everywhere on the battery domain: a literal in disguise.
    zt = {"word": "zero_times", "arity": 1, "params": ["a"], "role": "term",
          "definition": {"op": "*", "args": [{"ref": "a"}, {"lit": 0}]}}
    res = og.admit_operator(zt, pricing_corpus=SQ_CORPUS)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "degeneracy"
    assert "CONSTANT" in res["refusal"]["reason"]


def test_self_reference_refused_for_term_role(op_dir):
    row = {"word": "loopyt", "arity": 1, "params": ["a"], "role": "term",
           "definition": {"op": "loopyt", "args": [{"ref": "a"}]}}
    res = og.admit_operator(row, pricing_corpus=SQ_CORPUS)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "well-formedness"
    assert "self-reference" in res["refusal"]["reason"]


def test_role_term_with_pred_body_refused(op_dir):
    # role says term, body is a pred atom: _check_term refuses the mismatch.
    row = {"word": "tpred", "arity": 2, "params": ["a", "b"], "role": "term",
           "definition": {"op": "dvd", "args": [{"ref": "a"}, {"ref": "b"}]}}
    res = og.admit_operator(row, pricing_corpus=SQ_CORPUS)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "well-formedness"
    assert "not a valid term" in res["refusal"]["reason"]


def test_role_pred_with_term_body_refused(op_dir):
    # role (defaulted) pred, body is a term: _check_pred refuses the mismatch.
    row = {"word": "ptermish", "arity": 1, "params": ["a"],
           "definition": {"op": "*", "args": [{"ref": "a"}, {"ref": "a"}]}}
    res = og.admit_operator(row, pricing_corpus=SQ_CORPUS)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "well-formedness"
    assert "not a valid pred" in res["refusal"]["reason"]


def test_unknown_role_refused(op_dir):
    row = dict(SQ, word="sqx", role="function")
    res = og.admit_operator(row, pricing_corpus=SQ_CORPUS)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "well-formedness"
    assert "role" in res["refusal"]["reason"]


def test_enum_only_term_refused_no_differential(op_dir):
    # gcd is enum_only: a term word built on it has no SMT channel, so the
    # value battery cannot be corroborated -- refused, mirroring the pred rule.
    row = {"word": "gcd_succ", "arity": 2, "params": ["a", "b"], "role": "term",
           "definition": {"op": "+", "args": [
               {"op": "gcd", "args": [{"ref": "a"}, {"ref": "b"}]}, {"lit": 1}]}}
    res = og.admit_operator(row, pricing_corpus=SQ_CORPUS)
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "battery"
    assert "enum-only" in res["refusal"]["reason"]


def test_term_word_refused_on_economics_without_witnesses(op_dir):
    # a corpus with no a*a subtree: zero saving -> refused at pricing.
    empty = {"theorem": "t", "statements": [
        {"id": "c", "force": "demand", "quote": "q",
         "lf": {"kind": "conclusion",
                "pred": {"op": "even", "args": [{"ref": "a"}]}}}]}
    res = og.admit_operator(SQ, pricing_corpus=[empty, empty])
    assert res["admitted"] is False
    assert res["refusal"]["stage"] == "pricing"


# ============================================================ (3) DL pricing
def test_pricing_counts_term_subtree_matches(op_dir):
    kernel_def = og._expand_definition_to_kernel(SQ, {})
    pr = og.price_operator(SQ, kernel_def, SQ_CORPUS)
    # 3 x*x subtrees per reading, 2 readings; each collapses 9 -> 6 leaves.
    assert pr["uses"] == 6
    assert pr["witnesses"] == 2
    assert pr["saving"] == 18.0
    assert pr["model_bits"] == 11.0
    assert pr["dl_after"] == pr["dl_before"] - pr["saving"] + pr["model_bits"]


def test_binding_consistency_no_false_term_match(op_dir):
    # a * b (distinct refs) must NOT match the sq pattern a * a.
    reading = {"theorem": "t", "statements": [
        {"id": "h", "force": "presupposition", "quote": "q",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "<=", "args": [
                    {"op": "*", "args": [{"ref": "a"}, {"ref": "b"}]},
                    {"ref": "n"}]}}}]}
    kernel_def = og._expand_definition_to_kernel(SQ, {})
    pr = og.price_operator(SQ, kernel_def, [reading, reading])
    assert pr["uses"] == 0


# ====================================================== (4) use-time integration
_SQ_SOURCE = "for every natural a the square of a equals a times a"
_SQ_READING = {
    "theorem": "term_word_probe",
    "statements": [
        {"id": "oa", "force": "presupposition", "quote": "a",
         "lf": {"kind": "object", "name": "a", "type": "Nat"}},
        {"id": "q", "force": "demand", "quote": "for every natural a",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["a"]}},
        {"id": "c", "force": "demand",
         "quote": "the square of a equals a times a",
         "lf": {"kind": "conclusion", "pred": {"op": "=", "args": [
             {"op": "sq", "args": [{"ref": "a"}]},
             {"op": "*", "args": [{"ref": "a"}, {"ref": "a"}]}]}}},
    ],
}


def test_reading_using_term_word_parses_and_compiles_inlined(op_dir):
    _admit_and_save(SQ, SQ_CORPUS)
    reading = parse_math_reading(json.dumps(_SQ_READING), _SQ_SOURCE)
    # the parse-layer hook already expanded sq to kernel form
    assert reading.statements[-1]["lf"]["pred"] == {
        "op": "=", "args": [_sq_sub("a"), _sq_sub("a")]}
    compiled = compile_math_reading(reading)
    # the compiled Lean INLINES the kernel expansion: no new Lean defs, no
    # trace of the derived word.
    assert "sq" not in compiled["lean_text"]
    assert compiled["lean_text"] == \
        "theorem term_word_probe : ∀ (a : Nat), ((a * a) = (a * a)) := sorry"


def test_unadmitted_term_word_refuses_at_gate(op_dir):
    with pytest.raises(BadMathReading) as ei:
        parse_math_reading(json.dumps(_SQ_READING), _SQ_SOURCE)
    assert "sq" in str(ei.value)


def test_expansion_reaches_nested_term_positions(op_dir):
    _admit_and_save(SQ, SQ_CORPUS)
    # sq nested inside a term inside a hypothesis: sq(x + 1) <= n
    doc = {"theorem": "t", "statements": [
        {"id": "h", "force": "presupposition", "quote": "q",
         "lf": {"kind": "hypothesis", "pred": {"op": "<=", "args": [
             {"op": "sq", "args": [
                 {"op": "+", "args": [{"ref": "x"}, {"lit": 1}]}]},
             {"ref": "n"}]}}}]}
    out = og.expand_reading_doc(doc)
    arg = {"op": "+", "args": [{"ref": "x"}, {"lit": 1}]}
    assert out["statements"][0]["lf"]["pred"] == {
        "op": "<=", "args": [{"op": "*", "args": [arg, arg]}, {"ref": "n"}]}
    ops = set()
    og._pred_ops(out["statements"][0]["lf"]["pred"], ops)
    assert ops <= og.KERNEL_OPS


def test_term_word_composes_transitively(op_dir):
    # quart(a) := sq(a) * sq(a) references the admitted term word; expansion
    # must bottom out in kernel and validate as a term.
    _admit_and_save(SQ, SQ_CORPUS)
    reg = og.load_admitted()
    quart = {"word": "quart", "arity": 1, "params": ["a"], "role": "term",
             "definition": {"op": "*", "args": [
                 {"op": "sq", "args": [{"ref": "a"}]},
                 {"op": "sq", "args": [{"ref": "a"}]}]}}
    ok, reason = og._check_wellformed(quart, reg)
    assert ok, reason
    kd = og._expand_definition_to_kernel(quart, reg)
    ops = set()
    og._pred_ops(kd, ops)
    assert ops == {"*"}
    assert kd == {"op": "*", "args": [_sq_sub("a"), _sq_sub("a")]}


def test_term_word_used_at_pred_position_refuses(op_dir):
    # role safety at use time: an admitted TERM word cannot stand as a pred --
    # the expanded kernel term fails _check_pred at the gate.
    _admit_and_save(SQ, SQ_CORPUS)
    doc = {"theorem": "t", "statements": [
        {"id": "oa", "force": "presupposition", "quote": "a",
         "lf": {"kind": "object", "name": "a", "type": "Nat"}},
        {"id": "c", "force": "demand", "quote": "a",
         "lf": {"kind": "conclusion",
                "pred": {"op": "sq", "args": [{"ref": "a"}]}}}]}
    with pytest.raises(BadMathReading):
        parse_math_reading(json.dumps(doc), "a source mentioning a")


# ====================================================== (5) backward compat
def test_committed_admitted_json_loads_and_verifies_unchanged():
    # every committed row (all pre-D1, no role key) still loads, treats role as
    # "pred", and re-verifies: canonical_row omits the default role, so the
    # historical digests and cert ids are untouched.
    op_path = os.path.join(HERE, "specs", "mathsources", "operators")
    admitted = og.load_admitted(op_dir=op_path)
    assert admitted
    for word, entry in admitted.items():
        assert "role" not in entry["row"]
        assert "role" not in og.canonical_row(entry["row"])
        og._verify_entry(word, entry)          # raises on any digest drift


def test_pred_admission_still_works_next_to_term_path(op_dir):
    corpus = [_congm_reading(), _congm_reading()]
    res = og.admit_operator(CONGM, pricing_corpus=corpus)
    assert res["admitted"] is True
    b = res["cert"]["battery"]
    # the pred battery keeps its exact historical shape (no role key)
    assert "role" not in b and "role" not in res["cert"]
    assert b["satisfiable"] and b["refutable"]
    assert "role" not in res["row"]
    og.save_admitted({"congm": {"row": res["row"], "cert": res["cert"]}},
                     pricing_corpus=corpus)
    og.reload()
    assert "congm" in og.load_admitted()


def test_pred_and_term_words_coexist_in_one_registry(op_dir):
    _admit_and_save(SQ, SQ_CORPUS)
    _admit_and_save(CONGM, [_congm_reading(), _congm_reading()])
    reg = og.load_admitted()
    assert set(reg) == {"sq", "congm"}
    # one reading using BOTH expands fully to kernel
    doc = {"theorem": "t", "statements": [
        {"id": "h", "force": "presupposition", "quote": "q",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "congm", "args": [
                    {"op": "sq", "args": [{"ref": "x"}]},
                    {"ref": "y"}, {"ref": "m"}]}}},
        {"id": "c", "force": "demand", "quote": "q",
         "lf": {"kind": "conclusion",
                "pred": {"op": "even", "args": [{"ref": "x"}]}}}]}
    out = og.expand_reading_doc(doc)
    expanded = out["statements"][0]["lf"]["pred"]
    ops = set()
    og._pred_ops(expanded, ops)
    assert ops <= og.KERNEL_OPS
    # congm(sq(x), y, m) := ((x*x) mod m) = (y mod m), fully inlined
    assert expanded == {"op": "=", "args": [
        {"op": "mod", "args": [_sq_sub("x"), {"ref": "m"}]},
        {"op": "mod", "args": [{"ref": "y"}, {"ref": "m"}]}]}
