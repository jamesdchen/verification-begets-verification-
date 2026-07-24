"""P1 admission batteries: the bounded big-operator node class (bigsum/bigprod).

The PLAN_FRAGMENT §4 bill, applied to the one structural (binding) extension:
LLM-free, Lean-free teeth that would fail if the class's semantics regressed in
ANY of the four translations (gate / eval / SMT mirror / Lean text), in the
operator-growth battery discipline:

  * (b-analogue) DIFFERENTIAL VALUE battery: over planted bigop terms on both
    carriers and small-int instances, ``math_eval.eval_term``'s value is
    corroborated by the ground-equation SMT differential on z3 AND cvc5
    (dual-solver agreement; absent cvc5 degrades honestly).
  * (b2-analogue) SYMBOLIC battery: params FREE (never pinned), the unrolled
    form is asserted DISTINCT from an independently-derived closed form; a
    dual-solver ``unsat`` is the all-values agreement.
  * LOSSY LOWERING GETS NO CERTIFICATE: a planted off-by-one unroll (the last
    body copy dropped) must produce a DEFINITE solver disagreement -- the
    divergence tooth that proves the differential has teeth.
  * The gate's refusal surface (symbolic bound / nesting / shadowing /
    negative bound / stray {"var"} leaf) is pinned as demand data, and the
    Lean rendering + escape gate + hash byte-stability are pinned.
"""
import json

import pytest

from generators.math_reading import (
    parse_math_reading, BadMathReading, FragmentMiss, _check_term)
from generators.math_eval import eval_term, eval_pred
from generators import math_smt
from generators.math_compile import compile_math_reading
from buildloop.validate_lean import validate_lean
from kernel.backends import SmtBackend


def _dual(smtlib, expect):
    """Run both solvers with the given expectation; return the raw SmtBackend
    verdicts ('pass' = the solver answered as expected, 'fail' = it answered
    the opposite, else unknown/error)."""
    be = SmtBackend()
    z = be.run_z3(smtlib, expect=expect).get("result")
    c = be.run_cvc5(smtlib, expect=expect).get("result")
    return z, c


def _bigop(op, var, lo, hi, body):
    return {"op": op, "args": [{"var": var}, {"lit": lo}, {"lit": hi}, body]}


def _ground_equation(term, objects, carrier, assignment, value):
    """Pin every object, assert term = value: ``sat`` iff the solvers'
    arithmetic agrees with the evaluator (the _ground_term_smt discipline)."""
    lines = ["(set-logic QF_NIA)"]
    for name in sorted(objects):
        lines.append(f"(declare-const {name} Int)")
        if objects[name] == "Nat":
            lines.append(f"(assert (>= {name} 0))")
        lines.append(
            f"(assert (= {name} {math_smt._render_lit(assignment[name])}))")
    lines.append(f"(assert (= {math_smt.render_term(term, objects, carrier)} "
                 f"{math_smt._render_lit(value)}))")
    lines.append("(check-sat)")
    return "\n".join(lines) + "\n"


# ================================================= (b) differential value battery
# Planted terms: closed forms are independently known, bodies exercise the
# index, object refs, ^, %, and D8 `-` inside the body.
_PLANTED = [
    # (label, carrier, term, closed_form(assignment))
    ("sum_index", "Nat",
     _bigop("bigsum", "i", 1, 6, {"ref": "i"}),
     lambda a: 21),
    ("sum_affine", "Int",
     _bigop("bigsum", "i", 0, 4,
            {"op": "+", "args": [{"op": "*", "args": [{"lit": 2}, {"ref": "i"}]},
                                 {"ref": "x"}]}),
     lambda a: 20 + 5 * a["x"]),
    ("sum_squares", "Nat",
     _bigop("bigsum", "i", 1, 4, {"op": "^", "args": [{"ref": "i"}, {"lit": 2}]}),
     lambda a: 30),
    ("prod_index", "Nat",
     _bigop("bigprod", "i", 1, 5, {"ref": "i"}),
     lambda a: 120),
    ("prod_const_body", "Int",
     _bigop("bigprod", "i", 1, 3, {"ref": "x"}),
     lambda a: a["x"] ** 3),
    ("sum_mod", "Nat",
     _bigop("bigsum", "i", 0, 7, {"op": "%", "args": [{"ref": "i"}, {"lit": 3}]}),
     lambda a: sum(i % 3 for i in range(8))),
    # D8 inside the body: Nat-truncated subtraction 3 - i (index is Nat).
    ("sum_trunc_sub", "Nat",
     _bigop("bigsum", "i", 0, 5,
            {"op": "-", "args": [{"lit": 3}, {"ref": "i"}]}),
     lambda a: sum(max(0, 3 - i) for i in range(6))),
    ("empty_sum", "Nat", _bigop("bigsum", "i", 5, 4, {"ref": "i"}),
     lambda a: 0),
    ("empty_prod", "Int", _bigop("bigprod", "i", 5, 4, {"ref": "x"}),
     lambda a: 1),
]


@pytest.mark.parametrize("label,carrier,term,closed", _PLANTED,
                         ids=[p[0] for p in _PLANTED])
def test_value_battery_eval_agrees_with_dual_solver(label, carrier, term, closed):
    objects = {"x": carrier}
    for xv in ([0, 1, 3] if carrier == "Nat" else [-3, 0, 2]):
        a = {"x": xv}
        v = eval_term(term, a, objects, carrier)
        assert v == closed(a), f"{label}: evaluator disagrees with closed form"
        z, c = _dual(_ground_equation(term, objects, carrier, a, v), "sat")
        assert z == "pass", f"{label}@{a}: z3 {z}"
        assert c in ("pass", "unknown", "error"), f"{label}@{a}: cvc5 {c}"


def test_lossy_lowering_gets_no_certificate():
    """The divergence tooth: drop the LAST body copy from the unroll (a lossy
    lowering) and the ground differential must refuse -- definite unsat from
    both solvers, never a silent pass."""
    term = _bigop("bigsum", "i", 1, 6, {"ref": "i"})
    lossy = _bigop("bigsum", "i", 1, 5, {"ref": "i"})   # off-by-one unroll
    objects = {"x": "Nat"}
    a = {"x": 0}
    v = eval_term(term, a, objects, "Nat")
    lossy_smt = _ground_equation(lossy, objects, "Nat", a, v)
    z, c = _dual(lossy_smt, "sat")
    assert z == "fail", f"lossy unroll must be refused, z3 said {z}"
    assert c in ("fail", "error"), f"lossy unroll must be refused, cvc5 said {c}"


# ======================================================== (b2) symbolic battery
def _symbolic_distinct(term, closed_smt, objects):
    """Params FREE (Nat >= 0), assert term != closed form: unsat = all-values
    agreement (the b2 shape)."""
    lines = ["(set-logic QF_NIA)"]
    for name in sorted(objects):
        lines.append(f"(declare-const {name} Int)")
        if objects[name] == "Nat":
            lines.append(f"(assert (>= {name} 0))")
    lines.append(f"(assert (distinct "
                 f"{math_smt.render_term(term, objects, None)} {closed_smt}))")
    lines.append("(check-sat)")
    return "\n".join(lines) + "\n"


def test_symbolic_battery_sum_of_scaled_index():
    # sum_{i=1..4} (i*x) = 10*x, for ALL x (free param, never pinned).
    term = _bigop("bigsum", "i", 1, 4,
                  {"op": "*", "args": [{"ref": "i"}, {"ref": "x"}]})
    z, c = _dual(_symbolic_distinct(term, "(* 10 x)", {"x": "Int"}), "unsat")
    assert z == "pass"
    assert c in ("pass", "unknown", "error")


def test_symbolic_battery_prod_is_power():
    # prod_{i=1..3} x = x*x*x, for ALL x.
    term = _bigop("bigprod", "i", 1, 3, {"ref": "x"})
    z, c = _dual(_symbolic_distinct(term, "(* x x x)", {"x": "Int"}), "unsat")
    assert z == "pass"
    assert c in ("pass", "unknown", "error")


# ==================================================== gate refusals (demand data)
def test_symbolic_bound_is_a_fragment_miss():
    symbolic = {"op": "bigsum",
                "args": [{"var": "i"}, {"lit": 1}, {"ref": "n"}, {"ref": "i"}]}
    with pytest.raises(FragmentMiss) as e:
        _check_term(symbolic, {"n": "Nat"})
    assert e.value.missing_kind_guess == "bigop:symbolic-bound"


def test_nested_bigop_is_a_fragment_miss():
    inner = _bigop("bigprod", "j", 1, 2, {"ref": "j"})
    with pytest.raises(FragmentMiss) as e:
        _check_term(_bigop("bigsum", "i", 1, 3, inner), {})
    assert e.value.missing_kind_guess == "bigop:nested"

    # nesting hides one level down inside a + as well
    with pytest.raises(FragmentMiss):
        _check_term(_bigop("bigsum", "i", 1, 3,
                           {"op": "+", "args": [{"ref": "i"}, inner]}), {})


def test_shadowing_and_negative_bounds_and_stray_var_refuse():
    with pytest.raises(BadMathReading):
        _check_term(_bigop("bigsum", "n", 1, 3, {"ref": "n"}), {"n": "Nat"})
    with pytest.raises(BadMathReading):
        _check_term(_bigop("bigsum", "i", -1, 3, {"ref": "i"}), {})
    with pytest.raises(BadMathReading):
        _check_term({"op": "+", "args": [{"var": "i"}, {"lit": 1}]}, {})


def test_index_is_bound_not_free():
    # the body may use the index without declaring it; outside a body the same
    # ref refuses as undeclared.
    _check_term(_bigop("bigsum", "i", 1, 3, {"ref": "i"}), {})
    with pytest.raises(BadMathReading):
        _check_term({"ref": "i"}, {})


# ============================================== end-to-end reading + Lean + hash
_SRC = ("For every natural number n, the sum of i squared for i from 1 to 4 "
        "is at most n plus 30.")


def _reading():
    return {
        "theorem": "bigop_e2e",
        "statements": [
            {"id": "amb", "force": "choice", "quote": "",
             "lf": {"kind": "ambient", "carrier": "Nat"}},
            {"id": "on", "force": "demand", "quote": "natural number n",
             "lf": {"kind": "object", "name": "n", "type": "Nat"}},
            {"id": "qf", "force": "demand",
             "quote": "For every natural number n",
             "lf": {"kind": "quantifier", "binder": "forall",
                    "objects": ["n"]}},
            {"id": "c", "force": "demand",
             "quote": "the sum of i squared for i from 1 to 4 is at most "
                      "n plus 30",
             "lf": {"kind": "conclusion",
                    "pred": {"op": "<=", "args": [
                        _bigop("bigsum", "i", 1, 4,
                               {"op": "^", "args": [{"ref": "i"}, {"lit": 2}]}),
                        {"op": "+", "args": [{"ref": "n"}, {"lit": 30}]}]}}},
        ]}


def test_end_to_end_gate_eval_compile_escape():
    r = parse_math_reading(json.dumps(_reading()), _SRC)
    pred = [s for s in r.statements if s["lf"]["kind"] == "conclusion"][0]
    assert eval_pred(pred["lf"]["pred"], {"n": 0}, {"n": "Nat"}, "Nat")
    art = compile_math_reading(r)
    assert "Finset.sum (Finset.Icc 1 4) (fun i =>" in art["lean_text"]
    ok, reason = validate_lean(art["lean_text"])
    assert ok, reason
    # byte-stability: recompilation is hash-identical
    art2 = compile_math_reading(parse_math_reading(json.dumps(_reading()), _SRC))
    assert art["statement_hash"] == art2["statement_hash"]


def test_bigprod_pushes_qf_nia_bigsum_stays_linear():
    """CVC5 enforces the declared logic strictly: a bigprod of an
    object-dependent body must classify QF_NIA; a bigsum of an affine body
    stays QF_LIA (the index is a constant after unrolling)."""
    prod_t = _bigop("bigprod", "i", 1, 3, {"ref": "x"})
    sum_t = _bigop("bigsum", "i", 1, 3,
                   {"op": "*", "args": [{"ref": "i"}, {"ref": "x"}]})
    assert math_smt._term_nonlinear(prod_t)
    assert not math_smt._term_nonlinear(sum_t)
    # and the miner-facing signature refuses to type the binding class
    from generators.math_reading import op_signature
    assert op_signature("bigsum") is None
    assert op_signature("bigprod") is None
