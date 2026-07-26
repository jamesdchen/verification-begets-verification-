"""P8 admission batteries: NAMED FUNCTION SYMBOLS (a definitional extension).

The PLAN_FRAGMENT §4 bill for the row `refusal-function-symbol`, and the
battery half of paying it.  What P8 buys is a `definition` statement -- the
source NAMES a function and gives it an EXPLICIT body over its own parameters
-- plus the `{"app": f, "args": [...]}` term that applies it.

WHAT MAKES THIS ROW'S BATTERY DIFFERENT, stated first because it decides what
every number below is evidence FOR.  P7 could not run a dual-solver
differential at all: a symbolic exponent has no SMT-LIB rendering, so that
purchase's symbolic battery was ABSENT and recorded as absent.  P8 is the
opposite case, and for a structural reason worth naming: an application is
ELIMINATED at the gate, so by the time any consumer sees the reading there is
no application left in it.  The full dual-solver differential is therefore
available here, and the thing it corroborates is exactly the conservativity
claim -- that a defined symbol adds no meaning the fragment did not have.

THE HEADLINE IDENTITY, and it is what "conservative" means made executable.
For every reading R that uses a definition, let U(R) be the HAND-UNFOLDED
twin -- the same reading with the body substituted by hand and no `definition`
statement at all.  Then at all four consumers:

    eval:    same verdict at every point of a box sweep
    SMT:     same verdict from z3 AND from cvc5
    Lean:    byte-identical `lean_text` AND byte-identical `statement_hash`
    reflect: nothing to compare, because `Tm`/`Pd` are byte-unchanged

The reference is never a Python re-implementation of substitution: it is a
reading a human wrote out longhand in the fragment the purchase did not touch.
That is what makes agreement evidence rather than a tautology -- if
`_unfold_term` substituted the wrong body, the hand-written twin would not
move with it, and `test_unfolding_a_wrong_body_gets_no_certificate` plants
exactly that.

WHAT THE ROW DOES NOT BUY, measured here rather than promised in prose: a
RECURRENCE.  `funcdef:recursive-body` is the refusal, and it is the headline
demand P8 prices and deliberately leaves on the board, because a body that
applies itself has no finite unfolding at a symbolic index.  The other two
freezes -- `funcdef:binder-body` and `funcdef:open-body` -- are what keep the
elimination total, and both are pinned in both directions below.
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from generators import math_compile as MC  # noqa: E402
from generators import math_eval as ME  # noqa: E402
from generators import math_reading as MR  # noqa: E402
from generators import math_smt as MS  # noqa: E402
from kernel.backends import SmtBackend  # noqa: E402


# --------------------------------------------------------------------------- #
# Term helpers and the two readings every differential below compares.
# --------------------------------------------------------------------------- #
def _lit(k):
    return {"lit": k}


def _ref(n):
    return {"ref": n}


def _t(op, *args):
    return {"op": op, "args": list(args)}


#: The source both readings are grounded in.  One sentence, so the quotes are
#: identical in the two readings and groundedness cannot be what makes them
#: differ.
SRC = ("Let f be the function defined by f(k) = 2 k + 1 for every natural "
       "number k. Show that for all natural numbers n, f(n) + f(n) is even.")

#: f's body, written once and used by BOTH readings -- by the definition
#: statement in one, and by hand at each use site in the other.
BODY = _t("+", _t("*", _lit(2), _ref("k")), _lit(1))


def _body_at(name):
    """f's body with the parameter replaced by object `name`, written out
    LONGHAND.  This is the reference: a term in the pre-P8 fragment that no
    P8 code path produced."""
    return _t("+", _t("*", _lit(2), _ref(name)), _lit(1))


def _reading(statements, source=SRC, theorem="funcdef_thm"):
    return MR.parse_math_reading(
        json.dumps({"theorem": theorem, "statements": statements}), source)


def _preamble():
    return [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Nat"}},
        {"id": "obn", "force": "choice", "quote": "",
         "lf": {"kind": "object", "name": "n", "type": "Nat"}},
        {"id": "opev", "force": "choice", "quote": "",
         "lf": {"kind": "operator", "word": "even", "carrier": "Nat"}},
        {"id": "q", "force": "demand", "quote": "for all natural numbers n",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n"]}},
    ]


def _with_definition(body=None, concl=None):
    """The P8 reading: one `definition` statement and two APPLICATIONS."""
    return _reading(_preamble() + [
        {"id": "def", "force": "presupposition",
         "quote": "f(k) = 2 k + 1",
         "lf": {"kind": "definition", "name": "f", "params": ["k"],
                "body": BODY if body is None else body}},
        {"id": "c", "force": "demand", "quote": "f(n) + f(n) is even",
         "lf": {"kind": "conclusion",
                "pred": concl if concl is not None else
                _t("even", _t("+", {"app": "f", "args": [_ref("n")]},
                              {"app": "f", "args": [_ref("n")]}))}},
    ])


def _hand_unfolded():
    """The reference reading: NO definition, NO application -- the body
    written out at each use site, in the fragment as it stood before P8."""
    return _reading(_preamble() + [
        {"id": "c", "force": "demand", "quote": "f(n) + f(n) is even",
         "lf": {"kind": "conclusion",
                "pred": _t("even", _t("+", _body_at("n"), _body_at("n")))}},
    ])


def _concl(reading):
    return [s for s in reading.statements
            if s["lf"]["kind"] == "conclusion"][0]["lf"]["pred"]


def _dual(smtlib, expect):
    """Both solvers, same obligation, same expectation.  `SmtBackend` reports
    `pass`/`fail` AGAINST the expectation rather than the raw sat/unsat, so
    `pass` here means "the solver returned exactly `expect`"."""
    be = SmtBackend()
    z = be.run_z3(smtlib, expect=expect).get("result")
    c = be.run_cvc5(smtlib, expect=expect).get("result")
    return z, c


# --------------------------------------------------------------------------- #
# (a) THE ELIMINATION ITSELF: no application survives the gate.
# --------------------------------------------------------------------------- #
def test_the_gate_leaves_no_application_in_the_reading():
    """The structural fact the whole bill rests on, asserted before anything
    is compared: after `parse_math_reading`, every pred is app-free.  This is
    why the evaluator, the SMT mirror and the Lean emitter needed no new
    code -- and a purchase that claimed that without checking it would be
    claiming the cheapest thing in the bill on trust."""
    def walk(node):
        if not isinstance(node, dict):
            return
        assert "app" not in node, f"an application survived the gate: {node}"
        for a in node.get("args", []):
            walk(a)

    reading = _with_definition()
    for s in reading.statements:
        if s["lf"]["kind"] in ("hypothesis", "conclusion"):
            walk(s["lf"]["pred"])
    # ... and the RECORD of what the source said is still there, because the
    # definition is a thing the text did, not a thing we invented.
    assert set(reading.definitions()) == {"f"}
    assert reading.definitions()["f"]["params"] == ["k"]


def test_the_desugared_pred_is_the_hand_unfolded_pred():
    """The elimination lands on exactly the term a human writes longhand --
    structural equality against a reference nothing in P8 produced."""
    assert _concl(_with_definition()) == _concl(_hand_unfolded())


# --------------------------------------------------------------------------- #
# (b) DIFFERENTIAL battery: the evaluator, swept over a box.
# --------------------------------------------------------------------------- #
def test_the_two_readings_agree_at_every_point_of_the_box():
    """The (b) half of the bill.  Same verdict, point for point -- and the
    sweep is over the DECLARED carrier, so every point is one the reading
    actually admits."""
    defd, hand = _concl(_with_definition()), _concl(_hand_unfolded())
    seen = set()
    for n in range(0, 40):
        a = ME.eval_pred(defd, {"n": n}, {"n": "Nat"}, "Nat")
        b = ME.eval_pred(hand, {"n": n}, {"n": "Nat"}, "Nat")
        assert a == b, (n, a, b)
        seen.add(a)
    # the sweep must be INFORMATIVE: `2n+1 + 2n+1 = 4n+2` is always even, so a
    # constant True here is correct -- and the wrong-body plant below is what
    # shows the comparison can separate two readings at all.
    assert seen == {True}


@pytest.mark.parametrize("params,args,body,point,expect", [
    # two parameters, applied in the written order (the compiler never
    # reorders, and neither does the substitution)
    (["x", "y"], ["a", "b"], _t("-", _ref("x"), _ref("y")),
     {"a": 9, "b": 4}, 5),
    (["x", "y"], ["b", "a"], _t("-", _ref("x"), _ref("y")),
     {"a": 9, "b": 4}, -5),
    # a parameter used TWICE: substitution must copy, not alias
    (["x"], ["a"], _t("*", _ref("x"), _ref("x")), {"a": 7}, 49),
    # a parameter used ZERO times: a constant function is still a function
    (["x"], ["a"], _lit(3), {"a": 7}, 3),
])
def test_substitution_is_positional_and_copying(params, args, body, point,
                                                expect):
    """Argument ORDER and argument MULTIPLICITY, both measured.  A
    substitution that matched parameters by name, or that shared one argument
    subtree where the body used it twice, would pass the single-parameter
    case above and fail here."""
    src = ("Let g be given by its body. Then g of the arguments equals the "
           "value.")
    stmts = [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "d", "force": "choice", "quote": "",
         "lf": {"kind": "definition", "name": "g", "params": params,
                "body": body}},
    ]
    stmts += [{"id": f"o{k}", "force": "choice", "quote": "",
               "lf": {"kind": "object", "name": k, "type": "Int"}}
              for k in sorted(point)]
    stmts += [{"id": "c", "force": "demand",
               "quote": "g of the arguments equals the value",
               "lf": {"kind": "conclusion",
                      "pred": _t("=", {"app": "g",
                                       "args": [_ref(a) for a in args]},
                                 _lit(expect))}}]
    pred = _concl(_reading(stmts, src, "g_thm"))
    carriers = {k: "Int" for k in point}
    assert ME.eval_pred(pred, point, carriers, "Int") is True


# --------------------------------------------------------------------------- #
# (b2) SYMBOLIC battery: the dual-solver differential P7 could not run.
# --------------------------------------------------------------------------- #
def test_both_solvers_agree_the_two_readings_are_equivalent():
    """The (b2) half of the bill, and the strongest statement in this file:
    the defined reading and the hand-unfolded reading are equivalent for ALL
    n, not merely on the box -- and BOTH solvers say so independently.  The
    obligation is the negation of the biconditional, so `unsat` IS the
    equivalence."""
    defd = MS.render_pred(_concl(_with_definition()), {"n": "Nat"}, "Nat")
    hand = MS.render_pred(_concl(_hand_unfolded()), {"n": "Nat"}, "Nat")
    smtlib = (
        "(set-logic QF_NIA)\n"
        "(declare-fun n () Int)\n"
        "(assert (>= n 0))\n"
        f"(assert (not (= {defd} {hand})))\n"
        "(check-sat)\n")
    z, c = _dual(smtlib, "unsat")
    assert z == "pass", z          # z3 returned unsat: equivalent for ALL n
    assert c == "pass", c          # ... and cvc5 agrees, independently


def test_the_smt_rendering_is_byte_identical():
    """Stronger than agreement, and cheap: the two readings render to the
    SAME SMT-LIB bytes, because the elimination happened before the mirror
    ever saw them.  A row that had taught the mirror about applications would
    fail this and have to argue instead."""
    assert (MS.render_pred(_concl(_with_definition()), {"n": "Nat"}, "Nat")
            == MS.render_pred(_concl(_hand_unfolded()), {"n": "Nat"}, "Nat"))


def test_a_definition_reading_is_smt_representable():
    """The routing half: unlike P7's symbolic exponent, this row does NOT
    fall back to enumeration -- there is nothing left in the reading that the
    mirror cannot render."""
    assert MS.smt_representable(_with_definition()) is True


# --------------------------------------------------------------------------- #
# (c) THE LEAN CONSUMER: byte-identical text and hash.
# --------------------------------------------------------------------------- #
def test_the_compiled_lean_is_byte_identical_to_the_hand_unfolded_reading():
    """The emitter is the one consumer where "same meaning" is not enough to
    check cheaply -- so this checks the stronger thing.  Same `lean_text`,
    same `statement_hash`: the definition costs the compiler no rendering
    rule, no new name lookup and no new import pin."""
    a = MC.compile_math_reading(_with_definition())
    b = MC.compile_math_reading(_hand_unfolded())
    assert a["lean_text"] == b["lean_text"], (a["lean_text"], b["lean_text"])
    assert a["statement_hash"] == b["statement_hash"]
    # and the emitted statement is the one a reader would expect
    assert "∀ (n : Nat)" in a["lean_text"]
    assert "f" not in a["lean_text"].split(":", 1)[1], a["lean_text"]


# --------------------------------------------------------------------------- #
# (d) THE DIVERGENCE TOOTH: a planted wrong body gets no certificate.
# --------------------------------------------------------------------------- #
def _sum_is(rhs_lit_mul, rhs_lit_add, body=None):
    """`f(n) + f(n) = <rhs>` -- a conclusion that is MEANING-SENSITIVE to the
    body, which is what the divergence tooth needs.  (The `even` conclusion the
    differentials above use is deliberately NOT: `2k+1` and `2k+2` both give an
    even sum, so an evaluator and a solver would BOTH call them equivalent.
    That is a real limit of an equivalence-only comparison, and the tooth below
    is what covers it rather than a luckier plant hiding it.)"""
    rhs = _t("+", _t("*", _lit(rhs_lit_mul), _ref("n")), _lit(rhs_lit_add))
    concl = _t("=", _t("+", {"app": "f", "args": [_ref("n")]},
                       {"app": "f", "args": [_ref("n")]}), rhs)
    return _with_definition(body=body, concl=concl)


def test_unfolding_a_wrong_body_gets_no_certificate():
    """THE tooth for this row (registered in
    buildloop.growth_protocol GROWERS['funcdef-definitional-extension']).

    If `_unfold_term` substituted a body OTHER than the one the source
    declared, the reading would still parse, evaluate, render and compile --
    every consumer internally consistent, and nothing anywhere raising an
    error.  What it would NOT do is still MEAN what the source said.  So the
    plant is a definition whose body is off by one against a conclusion the
    source asserts, and all three channels witness the divergence: the
    evaluator refutes it pointwise, both solvers refute it symbolically, and
    the emitted Lean bytes differ.

    This is the test that makes every agreement above evidence: without it,
    the comparisons would pass equally well against a broken substitution
    applied consistently on both sides."""
    good = _sum_is(4, 2)                                 # (2n+1)+(2n+1)
    wrong = _sum_is(4, 2, body=_t("+", _t("*", _lit(2), _ref("k")), _lit(2)))
    good_pred, wrong_pred = _concl(good), _concl(wrong)
    assert good_pred != wrong_pred

    # 1. the evaluator refutes the planted reading at every point ...
    for n in range(0, 20):
        assert ME.eval_pred(good_pred, {"n": n}, {"n": "Nat"}, "Nat") is True
        assert ME.eval_pred(wrong_pred, {"n": n}, {"n": "Nat"}, "Nat") is False

    # 2. ... both solvers agree the planted claim is FALSIFIABLE (a model of
    #    its negation exists) while the honest one is not ...
    def obligation(pred):
        return ("(set-logic QF_NIA)\n(declare-fun n () Int)\n"
                "(assert (>= n 0))\n"
                f"(assert (not {MS.render_pred(pred, {'n': 'Nat'}, 'Nat')}))\n"
                "(check-sat)\n")

    z, c = _dual(obligation(good_pred), "unsat")
    assert (z, c) == ("pass", "pass"), (z, c)      # the honest reading holds
    z, c = _dual(obligation(wrong_pred), "sat")
    assert (z, c) == ("pass", "pass"), (z, c)      # the planted one does not

    # 3. ... and the emitted Lean is not the same statement either.
    assert (MC.compile_math_reading(good)["statement_hash"]
            != MC.compile_math_reading(wrong)["statement_hash"])


def test_a_wrong_ARITY_cannot_even_be_stated():
    """The cheaper half of the same protection: an application whose argument
    count disagrees with the definition is a malformed reading, refused at
    the gate rather than silently padded or truncated."""
    with pytest.raises(MR.BadMathReading) as e:
        _with_definition(concl={"op": "even",
                                "args": [{"app": "f",
                                          "args": [_ref("n"), _ref("n")]}]})
    assert "exactly 1 argument" in str(e.value)


def test_the_battery_can_fail():
    """The battery's own falsifiability check (the shape every row above
    uses): the comparison machinery separates two readings that really
    differ, so a green above is not the machinery being unable to say no."""
    a, b = _concl(_sum_is(4, 2)), _concl(_sum_is(4, 3))
    assert a != b
    diff = [n for n in range(20)
            if ME.eval_pred(a, {"n": n}, {"n": "Nat"}, "Nat")
            != ME.eval_pred(b, {"n": n}, {"n": "Nat"}, "Nat")]
    assert len(diff) == 20, diff


# --------------------------------------------------------------------------- #
# (e) THE THREE FREEZES, both directions.
# --------------------------------------------------------------------------- #
def _def_miss(name, params, body, extra_concl=None):
    src = ("Let q be a function of its parameter and let n be given. Then the "
           "claim holds.")
    stmts = [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "on", "force": "choice", "quote": "",
         "lf": {"kind": "object", "name": "n", "type": "Int"}},
        {"id": "d", "force": "choice", "quote": "",
         "lf": {"kind": "definition", "name": name, "params": params,
                "body": body}},
        {"id": "c", "force": "demand", "quote": "the claim holds",
         "lf": {"kind": "conclusion",
                "pred": extra_concl or _t("=", _ref("n"), _lit(1))}},
    ]
    with pytest.raises(MR.FragmentMiss) as e:
        _reading(stmts, src, "q_thm")
    return e.value.missing_kind_guess


def test_a_recursive_body_is_first_class_demand():
    """`funcdef:recursive-body` -- the headline thing this row does NOT buy.
    A recurrence has no finite unfolding at a symbolic index, so it is
    refused as DEMAND (it reaches the fragment-miss sink and can raise a
    future row's price) rather than as a malformed reading."""
    assert _def_miss("q", ["k"],
                     _t("+", {"app": "q", "args": [_ref("k")]}, _lit(2))
                     ) == "funcdef:recursive-body"


def test_a_forward_reference_is_recursion_wearing_a_different_hat():
    """Mutual recursion, refused by the same rule: a body may use only the
    definitions declared BEFORE it, which is what makes the dependency graph
    a DAG and `_unfold_term` terminate without an occurs-check."""
    src = "Let a and b be functions. Then the claim holds."
    stmts = [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "on", "force": "choice", "quote": "",
         "lf": {"kind": "object", "name": "n", "type": "Int"}},
        {"id": "d1", "force": "choice", "quote": "",
         "lf": {"kind": "definition", "name": "a", "params": ["k"],
                "body": {"app": "b", "args": [_ref("k")]}}},
        {"id": "d2", "force": "choice", "quote": "",
         "lf": {"kind": "definition", "name": "b", "params": ["k"],
                "body": _ref("k")}},
        {"id": "c", "force": "demand", "quote": "the claim holds",
         "lf": {"kind": "conclusion", "pred": _t("=", _ref("n"), _lit(1))}},
    ]
    with pytest.raises(MR.BadMathReading) as e:
        _reading(stmts, src, "ab_thm")
    assert "EARLIER in the reading" in str(e.value)


def test_a_binder_in_a_body_is_first_class_demand():
    """`funcdef:binder-body` -- the freeze that makes capture IMPOSSIBLE by
    construction rather than by a delicate argument."""
    assert _def_miss("q", ["k"],
                     _t("bigsum", {"var": "i"}, _lit(1), _lit(3), _ref("k"))
                     ) == "funcdef:binder-body"


def test_an_open_body_is_first_class_demand():
    """`funcdef:open-body` -- a body that reads an ambient object is not a
    definition, it is a hypothesis about one."""
    assert _def_miss("q", ["k"], _t("+", _ref("k"), _ref("n"))
                     ) == "funcdef:open-body"


def test_the_freezes_admit_what_they_should():
    """The other direction, so the three rules above are fences and not
    walls: a body that recurs on NOTHING, binds NOTHING and reads NO object
    is admitted, and its use site evaluates."""
    reading = _with_definition()
    assert set(reading.definitions()) == {"f"}
    assert ME.eval_pred(_concl(reading), {"n": 3}, {"n": "Nat"}, "Nat") is True


# --------------------------------------------------------------------------- #
# (e2) COMPOSITION WITH P1's BINDER -- what the widened signature pins buy.
# --------------------------------------------------------------------------- #
def test_an_application_composes_with_the_big_operator_binder():
    """P8 widened `_check_bigop`/`_check_setbuild`/`_check_card` by one
    OPTIONAL parameter -- the function environment in scope -- and this is
    the test that says why, rather than leaving three edited signature pins
    justified by nothing.

    Without the threading, `bigsum(i, 1, 3, f(i))` would refuse with
    "undefined function f": the binder body is walked by `_check_bigop`, so a
    definition invisible there is a definition that stops at the first
    binder.  With it, an application composes with P1's bounded iteration and
    the whole thing unfolds to a term the fragment already had -- which is
    the composition a reader would expect a named function to have, and the
    reason the parameter is a real cost rather than an incidental one.

    2 + 3 + 4 = 9, computed by the evaluator over the unfolded body."""
    src = ("Let f be defined by f(k) = k + 1. Then the sum of f(i) for i "
           "from 1 to 3 equals 9.")
    stmts = [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Nat"}},
        {"id": "d", "force": "presupposition", "quote": "f(k) = k + 1",
         "lf": {"kind": "definition", "name": "f", "params": ["k"],
                "body": _t("+", _ref("k"), _lit(1))}},
        {"id": "c", "force": "demand",
         "quote": "the sum of f(i) for i from 1 to 3 equals 9",
         "lf": {"kind": "conclusion",
                "pred": _t("=", _t("bigsum", {"var": "i"}, _lit(1), _lit(3),
                                   {"app": "f", "args": [_ref("i")]}),
                           _lit(9))}},
    ]
    pred = _concl(_reading(stmts, src, "sum_thm"))
    # the application is gone, and the BINDER survived it intact
    assert pred["args"][0]["op"] == "bigsum"
    assert pred["args"][0]["args"][3] == _t("+", _ref("i"), _lit(1))
    assert ME.eval_pred(pred, {}, {}, "Nat") is True
    # ... and the index is still the binder's, not a captured object: a
    # reading that ALSO declares an object `i` is refused by P1's own
    # shadowing rule, which is what keeps the substitution honest here.
    shadowed = list(stmts)
    shadowed.insert(2, {"id": "oi", "force": "choice", "quote": "",
                        "lf": {"kind": "object", "name": "i", "type": "Nat"}})
    with pytest.raises(MR.BadMathReading) as e:
        _reading(shadowed, src, "sum_thm")
    assert "shadowing" in str(e.value)


# --------------------------------------------------------------------------- #
# (f) THE REFLECT SLICE IS BYTE-UNCHANGED -- the finding, pinned.
# --------------------------------------------------------------------------- #
def test_this_purchase_adds_no_reflect_constructor():
    """`tests/test_function_symbol_class.py` finding (4) priced this rung at
    an application node in `Tm` PLUS a new `Decidable` story, on the argument
    that "an uninterpreted symbol constrained only by axioms has no
    computable interpretation".  That is right about an uninterpreted symbol,
    and it is why this row bought a DEFINED one instead: an explicit body is
    eliminable, so nothing enters `Tm`/`Pd` and `decDenote` keeps deciding by
    computation.

    Pinned here so the claim cannot rot into prose: the constructor list this
    purchase left behind is P7's, unchanged."""
    with open(os.path.join(HERE, "tools", "FgReflect.lean")) as fh:
        lean = fh.read()
    head = lean.split("inductive Tm where", 1)[1].split("inductive Pd", 1)[0]
    declared = tuple(line.split("|", 1)[1].split(":", 1)[0].strip()
                     for line in head.splitlines()
                     if line.strip().startswith("| "))
    assert declared == ("lit", "tvar", "add", "sub", "mul", "tmod", "pow"), \
        declared
    assert "instance decDenote" in lean
