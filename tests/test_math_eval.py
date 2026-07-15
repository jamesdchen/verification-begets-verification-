"""Tests for generators/math_eval.py -- the third (Lean-free) translation of the
F-G pred/term AST that the F2 fidelity gates run on.

The eval functions take raw pred/term dicts + a `carrier_of` map + `ambient`, so
the atom / T4 tests build AST nodes directly (no groundedness ceremony).  The
instance-construction tests need a `MathReading`, built inline through
`parse_math_reading` (with source sentences that ground every quote), reusing the
Wave-0 fixture constructors.
"""
from __future__ import annotations

import json

from generators.math_reading import parse_math_reading
from generators import math_eval as M
from tests.fixtures_math_readings import (
    _obj, _amb, _qf, _hyp, _concl, _ref, _lit, _ap, _reading,
)


def _build(theorem, statements, source):
    return parse_math_reading(json.dumps(_reading(theorem, statements)), source)


# A one-object reading with a `0 < n` hypothesis, reused by several tests.
_POS_SOURCE = "For every natural n, if n is positive then n is at least 1."


def _positive_reading():
    return _build("pos_ge_one", [
        _obj("o_n", "n", "Nat"),
        _amb("amb", "Nat"),
        _qf("q", "forall", ["n"], "for every natural n"),
        _hyp("h", _ap("<", _lit(0), _ref("n")), "n is positive"),
        _concl("c", _ap("<=", _lit(1), _ref("n")), "n is at least 1"),
    ], _POS_SOURCE)


# --------------------------------------------------------------- eval_pred atoms
def test_eval_pred_atoms():
    co = {"a": "Int", "b": "Int"}
    asg = {"a": 6, "b": 3}
    assert M.eval_pred(_ap("=", _ref("a"), _lit(6)), asg, co, None) is True
    assert M.eval_pred(_ap("!=", _ref("a"), _ref("b")), asg, co, None) is True
    assert M.eval_pred(_ap("<=", _ref("b"), _ref("a")), asg, co, None) is True
    assert M.eval_pred(_ap("<", _ref("b"), _ref("a")), asg, co, None) is True
    assert M.eval_pred(_ap("<", _ref("a"), _ref("b")), asg, co, None) is False

    # dvd: 3 divides 6, 6 does not divide 3
    assert M.eval_pred(_ap("dvd", _ref("b"), _ref("a")), asg, co, None) is True
    assert M.eval_pred(_ap("dvd", _ref("a"), _ref("b")), asg, co, None) is False

    # even / odd
    assert M.eval_pred(_ap("even", _ref("a")), asg, co, None) is True   # 6
    assert M.eval_pred(_ap("odd", _ref("a")), asg, co, None) is False
    assert M.eval_pred(_ap("odd", _ref("b")), asg, co, None) is True    # 3
    assert M.eval_pred(_ap("even", _ref("b")), asg, co, None) is False

    # gcd (a term) inside `=`  and coprime (a pred)
    assert M.eval_pred(_ap("=", _ap("gcd", _ref("a"), _ref("b")), _lit(3)),
                       asg, co, None) is True
    assert M.eval_pred(_ap("coprime", _ref("a"), _ref("b")),
                       asg, co, None) is False                          # gcd 3
    assert M.eval_pred(_ap("coprime", _lit(4), _lit(9)), {}, {}, None) is True

    # connectives
    pos_a = _ap("<", _lit(0), _ref("a"))
    neg_a = _ap("<", _ref("a"), _lit(0))
    pos_b = _ap("<", _lit(0), _ref("b"))
    assert M.eval_pred(_ap("and", pos_a, pos_b), asg, co, None) is True
    assert M.eval_pred(_ap("and", pos_a, neg_a), asg, co, None) is False
    assert M.eval_pred(_ap("or", neg_a, pos_b), asg, co, None) is True
    # implies with a false antecedent is vacuously true
    assert M.eval_pred(_ap("implies", neg_a, neg_a), asg, co, None) is True
    assert M.eval_pred(_ap("implies", pos_a, neg_a), asg, co, None) is False


# --------------------------------------------------------------- eval_term ops
def test_eval_term_ops():
    co = {"n": "Int"}
    assert M.eval_term(_ap("+", _lit(2), _lit(3), _lit(4)), {}, {}, None) == 9
    assert M.eval_term(_ap("*", _lit(2), _lit(3), _lit(4)), {}, {}, None) == 24
    assert M.eval_term(_ap("^", _ref("n"), _lit(3)), {"n": 2}, co, None) == 8
    # % and the `mod` word agree; `x % 0 = x` (Lean totalisation)
    assert M.eval_term(_ap("%", _lit(7), _lit(3)), {}, {}, None) == 1
    assert M.eval_term(_ap("mod", _lit(7), _lit(3)), {}, {}, None) == 1
    assert M.eval_term(_ap("%", _lit(7), _lit(0)), {}, {}, None) == 7
    # gcd(12, 18) = 6
    assert M.eval_term(_ap("gcd", _lit(12), _lit(18)), {}, {}, None) == 6


# ------------------------------------------------------------------ T4 tooth
def test_t4_nat_int_subtraction_divergence():
    """`a - b + b = a` at a=1,b=3: FALSE over Nat (1-3 truncates to 0, 0+3=3≠1),
    TRUE over Int -- the exact ℕ/ℤ divergence the tooth exists to plant."""
    minus = _ap("-", _ref("a"), _ref("b"))
    pred = _ap("=", _ap("+", minus, _ref("b")), _ref("a"))
    asg = {"a": 1, "b": 3}

    # the subtraction itself: truncated vs real
    assert M.eval_term(minus, asg, {"a": "Nat", "b": "Nat"}, None) == 0
    assert M.eval_term(minus, asg, {"a": "Int", "b": "Int"}, None) == -2

    # the whole identity flips with the carrier
    assert M.eval_pred(pred, asg, {"a": "Nat", "b": "Nat"}, None) is False
    assert M.eval_pred(pred, asg, {"a": "Int", "b": "Int"}, None) is True


# ----------------------------------------------------- hypotheses / conclusions
def test_hypotheses_and_conclusions_of():
    r = _positive_reading()
    assert M.hypotheses_of(r) == [_ap("<", _lit(0), _ref("n"))]
    assert M.conclusions_of(r) == _ap("<=", _lit(1), _ref("n"))
    assert M.hypotheses_hold(r, {"n": 3}) is True
    assert M.hypotheses_hold(r, {"n": 0}) is False
    assert M.conclusion_holds(r, {"n": 3}) is True     # 1 <= 3
    assert M.conclusion_holds(r, {"n": 0}) is False    # 1 <= 0 is false


# ------------------------------------------------------- satisfying_instances
def test_satisfying_instances_positive():
    r = _positive_reading()
    inst = M.satisfying_instances(r, k=5, bound=8)
    assert len(inst) == 5
    assert all(a["n"] > 0 for a in inst)               # none has n <= 0
    assert [a["n"] for a in inst] == [1, 2, 3, 4, 5]   # canonical order
    # the caller's F2.2(i) check: the instantiated statement holds
    assert all(M.conclusion_holds(r, a) for a in inst)


def test_satisfying_instances_deterministic():
    r = _positive_reading()
    assert M.satisfying_instances(r) == M.satisfying_instances(r)


# ------------------------------------------------------------- boundary_probes
def test_boundary_probes_zero():
    r = _positive_reading()
    probes = M.boundary_probes(r, bound=8)
    assert len(probes) == 1
    p = probes[0]
    assert p["assignment"] == {"n": 0}                 # just outside 0 < n
    assert p["hypothesis_id"] == "h"
    # the probe indeed violates the hypothesis (recorded, never auto-refused)
    assert M.hypotheses_hold(r, p["assignment"]) is False


def test_boundary_probes_just_outside_two():
    # 2 < n : the "just outside" probe is n = 2, not the canonical-minimal n = 0
    r = _build("gt_two", [
        _obj("o_n", "n", "Nat"),
        _amb("amb", "Nat"),
        _qf("q", "forall", ["n"], "for every natural n"),
        _hyp("h", _ap("<", _lit(2), _ref("n")), "n is more than 2"),
        _concl("c", _ap("<=", _lit(3), _ref("n")), "n is at least 3"),
    ], "For every natural n, if n is more than 2 then n is at least 3.")
    probes = M.boundary_probes(r, bound=8)
    assert probes == [{"assignment": {"n": 2}, "hypothesis_id": "h"}]


# ------------------------------------------------------------ bounded_nonvacuous
def test_bounded_nonvacuous_contradiction_and_sat():
    contra = _build("contra", [
        _obj("o_n", "n", "Nat"),
        _amb("amb", "Nat"),
        _qf("q", "forall", ["n"], "for every natural n"),
        _hyp("h1", _ap("<", _lit(5), _ref("n")), "n is more than 5"),
        _hyp("h2", _ap("<", _ref("n"), _lit(3)), "n is less than 3"),
        _concl("c", _ap("<=", _lit(0), _ref("n")), "n is at least 0"),
    ], "For every natural n, if n is more than 5 and n is less than 3 then "
       "n is at least 0.")
    assert M.bounded_nonvacuous(contra, bound=8) is False

    assert M.bounded_nonvacuous(_positive_reading(), bound=8) is True


# --------------------------------------------------------------- dvd zero edge
def test_dvd_zero_divisor():
    p = _ap("dvd", _lit(0), _ref("b"))
    assert M.eval_pred(p, {"b": 0}, {"b": "Int"}, None) is True    # 0 ∣ 0
    assert M.eval_pred(p, {"b": 5}, {"b": "Int"}, None) is False   # 0 ∤ 5


# -------------------------------------------------------- enumerate_domain order
def test_enumerate_domain_canonical_int():
    # a single Int object over a small bound: sum-of-abs then lexicographic.
    r = _build("id_int", [
        _obj("o_x", "x", "Int"),
        _amb("amb", "Int"),
        _qf("q", "forall", ["x"], "for every integer x"),
        _concl("c", _ap("=", _ref("x"), _ref("x")), "x equals x"),
    ], "For every integer x, x equals x.")
    got = [a["x"] for a in M.enumerate_domain(r, bound=2)]
    assert got == [0, -1, 1, -2, 2]
