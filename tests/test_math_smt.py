"""Tests for the SMT mirror of the MathReading hypothesis set (F2.1).

Readings are built inline (no fixture import -- fixtures may not exist during a
swarm run).  The rendered obligation is driven through BOTH Z3 and CVC5 under
``common.SMT_LOCK``, mirroring ``kernel.backends.SmtBackend``'s dual-solver
call pattern.  These tests exercise the mirror only; the mirror/compiler
agreement discipline (T4) lives in the pipeline, not here.
"""
import json

import common
from generators.math_reading import parse_math_reading
from generators import math_smt


# --------------------------------------------------------------- builders
def _obj(name, ty):
    # objects are formalization freedom -> force "choice", which quotes nothing
    return {"id": f"o_{name}", "force": "choice", "quote": "",
            "lf": {"kind": "object", "name": name, "type": ty}}


def _hyp(sid, pred, quote):
    return {"id": sid, "force": "presupposition", "quote": quote,
            "lf": {"kind": "hypothesis", "pred": pred}}


def _concl(sid, pred, quote):
    return {"id": sid, "force": "demand", "quote": quote,
            "lf": {"kind": "conclusion", "pred": pred}}


def _ambient(carrier):
    return {"id": "amb", "force": "choice", "quote": "",
            "lf": {"kind": "ambient", "carrier": carrier}}


def _reading(statements, source, theorem="thm"):
    doc = {"theorem": theorem, "statements": statements}
    return parse_math_reading(json.dumps(doc), source)


# --------------------------------------------------------- solver drivers
def _z3(smtlib):
    import z3
    with common.SMT_LOCK:
        s = z3.Solver()
        s.add(z3.parse_smt2_string(smtlib))
        return str(s.check())


def _cvc5(smtlib):
    import cvc5
    with common.SMT_LOCK:
        slv = cvc5.Solver()
        parser = cvc5.InputParser(slv)
        parser.setStringInput(cvc5.InputLanguage.SMT_LIB_2_6, smtlib,
                              "obligation.smt2")
        sm = parser.getSymbolManager()
        r = None
        while True:
            cmd = parser.nextCommand()
            if cmd.isNull():
                break
            out = cmd.invoke(slv, sm)
            if out.strip():
                r = out.strip()
        return (r or "").split()[0] if r else ""


def _both(smtlib):
    return _z3(smtlib), _cvc5(smtlib)


# ------------------------------------------------------------------- tests
def test_satisfiable_hypotheses_both_sat():
    # 0 < n over Int -> a world exists, both solvers agree sat.
    r = _reading(
        [_obj("n", "Int"), _ambient("Int"),
         _hyp("h1", {"op": "<", "args": [{"lit": 0}, {"ref": "n"}]}, "0 < n"),
         _concl("c1", {"op": "<=", "args": [{"lit": 1}, {"ref": "n"}]},
                "the claim holds")],
        "for integer n, 0 < n, and the claim holds")
    smt = math_smt.hypotheses_smt(r)
    assert smt is not None
    assert "(set-logic QF_LIA)" in smt
    assert "(declare-const n Int)" in smt
    assert "(assert (< 0 n))" in smt
    assert _both(smt) == ("sat", "sat")


def test_contradictory_hypotheses_both_unsat():
    # 5 < n and n < 3 cannot both hold -> both solvers agree unsat.
    r = _reading(
        [_obj("n", "Int"), _ambient("Int"),
         _hyp("h1", {"op": "<", "args": [{"lit": 5}, {"ref": "n"}]}, "5 < n"),
         _hyp("h2", {"op": "<", "args": [{"ref": "n"}, {"lit": 3}]}, "n < 3"),
         _concl("c1", {"op": "<", "args": [{"lit": 0}, {"ref": "n"}]},
                "the claim")],
        "suppose 5 < n and n < 3, then the claim")
    smt = math_smt.hypotheses_smt(r)
    assert _both(smt) == ("unsat", "unsat")


def test_nat_truncated_subtraction_uses_ite_and_is_sat():
    # a < b with (a - b) = 0 over Nat: truncated subtraction makes this SAT
    # (a=0,b=1 gives a-b=0), whereas a naive `(- a b)` would force a=b and be
    # UNSAT.  No ambient here, so `-` resolves to Nat from the operand objects.
    r = _reading(
        [_obj("a", "Nat"), _obj("b", "Nat"),
         _hyp("h1", {"op": "<", "args": [{"ref": "a"}, {"ref": "b"}]}, "a < b"),
         _hyp("h2", {"op": "=", "args": [
             {"op": "-", "args": [{"ref": "a"}, {"ref": "b"}]}, {"lit": 0}]},
             "a - b = 0"),
         _concl("c1", {"op": "<=", "args": [{"ref": "a"}, {"ref": "b"}]},
                "conclusion follows")],
        "let a and b be naturals with a < b and a - b = 0, conclusion follows")
    smt = math_smt.hypotheses_smt(r)
    # the truncated-subtraction guard must be emitted
    assert "(ite (>= a b) (- a b) 0)" in smt
    # Nat carriers force non-negativity constraints
    assert "(assert (>= a 0))" in smt
    assert "(assert (>= b 0))" in smt
    assert _both(smt) == ("sat", "sat")


def test_dvd_renders_a_equals_zero_special_case():
    # dvd(a,b) must render the mandatory a=0 arm (D9): SMT mod-by-zero is
    # underspecified, so the special case is not optional.
    r = _reading(
        [_obj("a", "Int"), _obj("b", "Int"), _ambient("Int"),
         _hyp("h1", {"op": "dvd", "args": [{"ref": "a"}, {"ref": "b"}]},
              "a divides b"),
         _concl("c1", {"op": "<=", "args": [{"lit": 0}, {"ref": "b"}]},
                "done")],
        "assume a divides b, done")
    smt = math_smt.hypotheses_smt(r)
    assert "(ite (= a 0) (= b 0) (= (mod b a) 0))" in smt
    # variable divisor -> nonlinear -> QF_NIA (CVC5 would reject QF_LIA here)
    assert "(set-logic QF_NIA)" in smt
    assert _both(smt) == ("sat", "sat")


def test_term_mod_totalises_at_zero_like_eval_mirror():
    # B2/B2-A: SMT-LIB `mod` diverges from eval's Python `%` at two seams --
    # y=0 (SMT leaves it unconstrained; Lean totalises `x % 0 = x`, B2) and y<0
    # (SMT `mod` is Euclidean, `%` is divisor-signed, B2-A).  The guarded
    # rendering pins the SMT term to the SAME value the eval channel computes at
    # BOTH seams -- a mirror-agreement tooth, not a tuned constant: the rendered
    # term is FORCED equal to `eval_term` and cannot take any other value.
    from generators import math_eval
    objects = {"a": "Int", "m": "Int"}
    term = {"op": "mod", "args": [{"ref": "a"}, {"ref": "m"}]}
    rendered = math_smt.render_term(term, objects, None)
    assert rendered == ("(ite (= m 0) a "
                        "(ite (> m 0) (mod a m) (- (mod (- a) (- m)))))")
    for asg in ({"a": 5, "m": 0},        # divisor 0: Lean totalises to a
                {"a": 7, "m": -3},       # negative divisor: `%` signs to m (B2-A)
                {"a": -7, "m": -3}):
        eval_val = math_eval.eval_term(term, asg, objects, None)
        pin = ("(set-logic QF_NIA)\n(declare-const a Int)\n(declare-const m Int)\n"
               f"(assert (= a {asg['a']}))\n(assert (= m {asg['m']}))\n")
        agree = pin + f"(assert (= {rendered} {eval_val}))\n(check-sat)\n"
        differ = pin + f"(assert (distinct {rendered} {eval_val}))\n(check-sat)\n"
        # the SMT term MUST equal the eval value there, and CANNOT differ from it.
        assert _both(agree) == ("sat", "sat"), asg
        assert _both(differ) == ("unsat", "unsat"), asg


def test_term_mod_matches_eval_grid():
    # B2-A exhaustive tooth: the rendered `mod` term must equal `eval_term`
    # (Python `%`, Lean-totalised) at EVERY cell of [-6,6]^2 -- covering y<0
    # (Euclidean-vs-divisor-signed), y=0 (totalisation), and y>0 (agreement).
    # Each cell is decided by the SAME solver(s) the pipeline trusts, so a
    # convention gap anywhere is a hard failure, not a masked one.
    from generators import math_eval
    objects = {"a": "Int", "m": "Int"}
    term = {"op": "mod", "args": [{"ref": "a"}, {"ref": "m"}]}
    rendered = math_smt.render_term(term, objects, None)
    R = range(-6, 7)
    for x in R:
        for y in R:
            eval_val = math_eval.eval_term(term, {"a": x, "m": y}, objects, None)
            pin = ("(set-logic QF_NIA)\n(declare-const a Int)\n"
                   "(declare-const m Int)\n"
                   f"(assert (= a {x}))\n(assert (= m {y}))\n")
            # negative literals wrap in SMT-LIB; _render_lit handles the pin RHS
            rhs = math_smt._render_lit(eval_val)
            agree = pin + f"(assert (= {rendered} {rhs}))\n(check-sat)\n"
            differ = pin + f"(assert (distinct {rendered} {rhs}))\n(check-sat)\n"
            assert _both(agree) == ("sat", "sat"), (x, y, eval_val)
            assert _both(differ) == ("unsat", "unsat"), (x, y, eval_val)


def test_even_stays_qf_lia():
    # even(n) -> (= (mod n 2) 0): constant divisor, so the obligation is linear.
    r = _reading(
        [_obj("n", "Int"), _ambient("Int"),
         _hyp("h1", {"op": "even", "args": [{"ref": "n"}]}, "n is even"),
         _concl("c1", {"op": "<=", "args": [{"lit": 0}, {"ref": "n"}]}, "ok")],
        "suppose n is even, ok")
    smt = math_smt.hypotheses_smt(r)
    assert "(= (mod n 2) 0)" in smt
    assert "(set-logic QF_LIA)" in smt
    assert _both(smt) == ("sat", "sat")


def test_coprime_is_not_smt_representable():
    # coprime is enum_only: no sound SMT rendering -> route to enumeration.
    r = _reading(
        [_obj("a", "Nat"), _obj("b", "Nat"),
         _hyp("h1", {"op": "coprime", "args": [{"ref": "a"}, {"ref": "b"}]},
              "a and b are coprime"),
         _concl("c1", {"op": "<=", "args": [{"lit": 0}, {"ref": "a"}]},
                "trivially")],
        "if a and b are coprime, trivially")
    assert math_smt.smt_representable(r) is False
    assert math_smt.hypotheses_smt(r) is None


def test_gcd_term_is_not_smt_representable():
    # gcd is an enum_only TERM; using it anywhere in a hypothesis blocks SMT.
    r = _reading(
        [_obj("a", "Nat"), _obj("b", "Nat"),
         _hyp("h1", {"op": "=", "args": [
             {"op": "gcd", "args": [{"ref": "a"}, {"ref": "b"}]}, {"lit": 1}]},
             "gcd of a and b is 1"),
         _concl("c1", {"op": "<=", "args": [{"lit": 0}, {"ref": "a"}]},
                "trivially")],
        "if gcd of a and b is 1, trivially")
    assert math_smt.smt_representable(r) is False
    assert math_smt.hypotheses_smt(r) is None


def test_deterministic_bytes():
    # the same reading renders byte-identically on every call.
    r = _reading(
        [_obj("n", "Int"), _ambient("Int"),
         _hyp("h1", {"op": "<", "args": [{"lit": 0}, {"ref": "n"}]}, "0 < n"),
         _concl("c1", {"op": "<=", "args": [{"lit": 1}, {"ref": "n"}]},
                "the claim holds")],
        "for integer n, 0 < n, and the claim holds")
    first = math_smt.hypotheses_smt(r)
    second = math_smt.hypotheses_smt(r)
    assert first == second
    assert first.encode() == second.encode()


def test_run_cvc5_absent_degrades_honestly(monkeypatch):
    """An absent cvc5 binding is an honest ``error`` verdict, never a crash
    (the "cvc5 may be absent" discipline): four F-INT builders independently
    hit ``import cvc5`` above the try in ``run_cvc5``, which raised straight
    through ``certify_statement`` in cvc5-less containers."""
    import sys
    from kernel.backends import SmtBackend
    monkeypatch.setitem(sys.modules, "cvc5", None)   # import cvc5 -> ImportError
    r = SmtBackend().run_cvc5("(check-sat)\n", expect="sat")
    assert r["backend"] == "cvc5"
    assert r["result"] == "error"                    # honest, not a pass
