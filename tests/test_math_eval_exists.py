"""WP-T6b: the bounded-shadow ∃ mode in generators/math_eval.py (COMPRESSION.md
§11.6 -- the eval-channel-only finitization).

These pin the SEMANTICS the module docstring defines: `exists_shadow_shape`'s
∀-outer/∃-inner classification, `exists_conclusion_holds`'s FULL bounded
disjunction (never k-smallest), and `exists_instances`'s exhaustive-outer gate
with the outer refutation witness.  A companion pin asserts the committed corpus
(zero exists binders) classifies as `forall-only`, so the ∃ machinery is inert
on it and the lazy byte-order pins (tests/test_math_eval_lazy.py) are untouched.
"""
import json
import pathlib

from generators.math_reading import parse_math_reading
from generators import math_eval

_SRC = pathlib.Path(__file__).resolve().parent.parent / "specs" / "mathsources"


def _reading(statements, source, theorem="t"):
    return parse_math_reading(
        json.dumps({"theorem": theorem, "statements": statements}), source)


def _obj(name, ty, quote):
    return {"id": "o" + name, "force": "demand", "quote": quote,
            "lf": {"kind": "object", "name": name, "type": ty}}


def _q(qid, binder, objs, quote):
    return {"id": qid, "force": "demand", "quote": quote,
            "lf": {"kind": "quantifier", "binder": binder, "objects": objs}}


# ----------------------------------------------------- shape classification
def _addinv_reading():
    # ∀ n:Int, ∃ m:Int, m + n = 0
    src = ("for every integer n there exists an integer m with m plus n equal "
           "to zero")
    stmts = [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        _obj("n", "Int", "every integer n"),
        _obj("m", "Int", "there exists an integer m"),
        _q("q1", "forall", ["n"], "for every integer n"),
        _q("q2", "exists", ["m"], "there exists an integer m"),
        {"id": "c", "force": "demand", "quote": "m plus n equal to zero",
         "lf": {"kind": "conclusion", "pred": {"op": "=", "args": [
             {"op": "+", "args": [{"ref": "m"}, {"ref": "n"}]}, {"lit": 0}]}}},
    ]
    return _reading(stmts, src)


def test_shape_supported_forall_outer_exists_inner():
    shape = math_eval.exists_shadow_shape(_addinv_reading())
    assert shape == {"mode": "supported", "outer": ["n"], "exists": ["m"]}


def test_shape_forall_only_when_no_exists():
    src = "for every integer n, n equals n"
    stmts = [
        _obj("n", "Int", "every integer n"),
        _q("q", "forall", ["n"], "for every integer n"),
        {"id": "c", "force": "demand", "quote": "n equals n",
         "lf": {"kind": "conclusion",
                "pred": {"op": "=", "args": [{"ref": "n"}, {"ref": "n"}]}}},
    ]
    assert math_eval.exists_shadow_shape(_reading(stmts, src)) == {
        "mode": "forall-only"}


def test_shape_exists_only_unsupported():
    # ∃ m:Int, m = m  -- no outer scope.
    src = "there exists an integer m with m equal to m"
    stmts = [
        _obj("m", "Int", "there exists an integer m"),
        _q("q", "exists", ["m"], "there exists an integer m"),
        {"id": "c", "force": "demand", "quote": "m equal to m",
         "lf": {"kind": "conclusion",
                "pred": {"op": "=", "args": [{"ref": "m"}, {"ref": "m"}]}}},
    ]
    shape = math_eval.exists_shadow_shape(_reading(stmts, src))
    assert shape["mode"] == "unsupported" and "exists-only" in shape["reason"]


def test_shape_exists_before_forall_unsupported():
    src = ("there exists an integer m such that for every integer n we have m "
           "equal to n")
    stmts = [
        _obj("n", "Int", "every integer n"),
        _obj("m", "Int", "there exists an integer m"),
        _q("q1", "exists", ["m"], "there exists an integer m"),
        _q("q2", "forall", ["n"], "for every integer n"),
        {"id": "c", "force": "demand", "quote": "m equal to n",
         "lf": {"kind": "conclusion",
                "pred": {"op": "=", "args": [{"ref": "m"}, {"ref": "n"}]}}},
    ]
    shape = math_eval.exists_shadow_shape(_reading(stmts, src))
    assert shape["mode"] == "unsupported"
    assert "exists-before-forall" in shape["reason"]


def test_shape_hypothesis_over_exists_object_unsupported():
    # a hypothesis referencing the ∃-bound object cannot filter the outer scope.
    src = ("for every integer n there exists an integer m with m positive and "
           "m plus n equal to zero")
    stmts = [
        _obj("n", "Int", "every integer n"),
        _obj("m", "Int", "there exists an integer m"),
        _q("q1", "forall", ["n"], "for every integer n"),
        _q("q2", "exists", ["m"], "there exists an integer m"),
        {"id": "h", "force": "presupposition", "quote": "m positive",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "<", "args": [{"lit": 0}, {"ref": "m"}]}}},
        {"id": "c", "force": "demand", "quote": "m plus n equal to zero",
         "lf": {"kind": "conclusion", "pred": {"op": "=", "args": [
             {"op": "+", "args": [{"ref": "m"}, {"ref": "n"}]}, {"lit": 0}]}}},
    ]
    shape = math_eval.exists_shadow_shape(_reading(stmts, src))
    assert shape["mode"] == "unsupported"
    assert "hypothesis references an exists-bound object" in shape["reason"]


# -------------------------------------- combinatorial ceiling (attack-2 guard)
def _wide_reading(n_outer, n_inner):
    # ∀ o0..o{n_outer-1}:Int, ∃ e0..e{n_inner-1}:Int, e0 = e0 (shape only; the
    # conclusion is irrelevant to classification/sizing).
    src = "for all integers there exist integers with something equal"
    onames = ["o%d" % i for i in range(n_outer)]
    enames = ["e%d" % i for i in range(n_inner)]
    stmts = [{"id": "amb", "force": "choice", "quote": "",
              "lf": {"kind": "ambient", "carrier": "Int"}}]
    for nm in onames + enames:
        stmts.append(_obj(nm, "Int", "integers"))
    stmts.append(_q("q1", "forall", onames, "for all integers"))
    stmts.append(_q("q2", "exists", enames, "there exist integers"))
    stmts.append({"id": "c", "force": "demand", "quote": "something equal",
                  "lf": {"kind": "conclusion", "pred": {
                      "op": "=", "args": [{"ref": enames[0]}, {"ref": enames[0]}]}}})
    return _reading(stmts, src)


def test_shape_oversize_honest_skips_at_bound():
    # 3-outer/3-inner Int at bound 8: 17^3 * 17^3 = 24.1M evals, an exhaustive
    # gate that would run for MINUTES -- reclassified `exists-domain-too-large`
    # (honest-skip) rather than hang.
    r = _wide_reading(3, 3)
    shape = math_eval.exists_shadow_shape(r, bound=8)
    assert shape["mode"] == "unsupported"
    assert "exists-domain-too-large" in shape["reason"]


def test_shape_ceiling_is_bound_relative_and_pure_without_bound():
    # The SAME reading is supported when the enumeration is small: pure shape
    # (bound=None, no guard) and a small bound both classify `supported`; only a
    # large bound trips the ceiling.  Pins that the guard is bound-relative and
    # never fires on the pure-shape API the other tests use.
    r = _wide_reading(3, 3)
    assert math_eval.exists_shadow_shape(r)["mode"] == "supported"        # no guard
    assert math_eval.exists_shadow_shape(r, bound=2)["mode"] == "supported"  # 5^6=15625
    assert math_eval.exists_shadow_shape(r, bound=8)["mode"] == "unsupported"


def test_shape_small_reading_still_supported_at_bound():
    # A realistic-size ∃ reading (1-outer/1-inner) is well under the ceiling and
    # stays supported with the bound passed -- the guard does not over-refuse.
    assert math_eval.exists_shadow_shape(_addinv_reading(), bound=8) == {
        "mode": "supported", "outer": ["n"], "exists": ["m"]}


# ----------------------------------------------- exists_conclusion_holds (∃)
def test_exists_conclusion_full_disjunction_true():
    r = _addinv_reading()
    # for n = 3 the witness m = -3 is in [-8,8]; the full bounded disjunction
    # finds it.
    assert math_eval.exists_conclusion_holds(r, {"n": 3}, ["m"], bound=8)


def test_exists_conclusion_bound_edge_false():
    # ∀ n:Int, ∃ m:Int, n < m: at n = B no in-bound m exceeds B, so the FULL
    # bounded disjunction is empty (the bound-edge honesty -- a k-smallest sample
    # would never even look at m = B and could not mask this).
    src = "for every integer n there exists an integer m with n less than m"
    stmts = [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        _obj("n", "Int", "every integer n"),
        _obj("m", "Int", "there exists an integer m"),
        _q("q1", "forall", ["n"], "for every integer n"),
        _q("q2", "exists", ["m"], "there exists an integer m"),
        {"id": "c", "force": "demand", "quote": "n less than m",
         "lf": {"kind": "conclusion",
                "pred": {"op": "<", "args": [{"ref": "n"}, {"ref": "m"}]}}},
    ]
    r = _reading(stmts, src)
    assert math_eval.exists_conclusion_holds(r, {"n": 7}, ["m"], bound=8)
    assert not math_eval.exists_conclusion_holds(r, {"n": 8}, ["m"], bound=8)


# --------------------------------------------------- exists_instances (gate)
def test_exists_instances_true_reading_passes_exhaustively():
    r = _addinv_reading()
    res = math_eval.exists_instances(r, ["n"], ["m"], bound=8)
    assert res["ok"] and res["witness"] is None
    # exhaustive over the outer box: every one of the 17 in-bound n was admitted
    # (no hypotheses) and checked.
    assert res["n_outer_admitted"] == 17


def test_exists_instances_false_reading_refutes_with_outer_witness():
    # ∀ n:Nat, ∃ m:Nat, m + 1 = n -- refutes at the canonically-first offender
    # n = 0 (the Nat predecessor that does not exist).
    src = ("for every natural number n there exists a natural number m with m "
           "plus one equal to n")
    stmts = [
        _obj("n", "Nat", "every natural number n"),
        _obj("m", "Nat", "there exists a natural number m"),
        _q("q1", "forall", ["n"], "for every natural number n"),
        _q("q2", "exists", ["m"], "there exists a natural number m"),
        {"id": "c", "force": "demand", "quote": "m plus one equal to n",
         "lf": {"kind": "conclusion", "pred": {"op": "=", "args": [
             {"op": "+", "args": [{"ref": "m"}, {"lit": 1}]}, {"ref": "n"}]}}},
    ]
    res = math_eval.exists_instances(_reading(stmts, src), ["n"], ["m"], bound=8)
    assert not res["ok"]
    assert res["witness"] == {"n": 0}


# --------------------------------------------- committed-corpus inertness pin
def test_committed_readings_classify_forall_only():
    # The committed corpus has ZERO exists binders (COMPRESSION.md §11.6): every
    # committed reading must classify `forall-only`, so the ∃ machinery is inert
    # and cannot perturb their bytes (the lazy pins in test_math_eval_lazy.py stay
    # green; the full certify byte-identity is pinned in test_formalize_pipeline).
    readings = sorted((_SRC / "readings").glob("*.json"))
    assert readings, "expected committed readings"
    for f in readings:
        obj = json.loads(f.read_text())
        r = parse_math_reading(json.dumps(obj["reading"]), obj["source"])
        assert math_eval.exists_shadow_shape(r) == {"mode": "forall-only"}, f.stem
