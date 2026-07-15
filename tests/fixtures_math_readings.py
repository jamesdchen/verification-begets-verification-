"""The ONE owned fixture home for hand-written MathReadings (F1 done-when, X16).

Imported by the parser tests (this WP), and later by the compiler and pipeline
tests -- a single source of ground-truth Readings so the parser, the F1.2
compiler and the F2 pipeline all exercise the SAME hand-authored specs and can
never silently diverge on what a legal Reading looks like.

Shape (F-A envelope, inner form):

    FIXTURES[name] = {
        "source":  <the raw sentence>,
        "reading": {"theorem": <lowercase ident>, "statements": [<stmt>, ...]},
        "expect":  "parse" | ("refuse", "<stage>"),
    }

where each statement is `{id, force, quote, lf}` exactly as the Reading's, and
`parse_math_reading(json.dumps(reading), source)` must behave per `expect`:
  * "parse"                       -> returns a MathReading;
  * ("refuse", "math-reading-gate") -> raises BadMathReading (a FragmentMiss,
    which is a BadMathReading subclass carrying `.missing_kind_guess`, for the
    fragment-miss entries named in FRAGMENT_MISS).

Every demand/presupposition quote below occurs VERBATIM in its source (the gate
checks string containment, whitespace/case-normalised); every choice quotes
nothing.  These are hand-written, but assembled through tiny constructors so the
pred/term AST stays legible and typo-free.
"""
from __future__ import annotations

import json

# --- statement constructors (kept minimal + explicit) -----------------------
def _obj(sid, name, ty, force="choice", quote=""):
    # object force is "any force"; declaring the referent as a formalization
    # choice keeps its quote empty (the carrier Nat/Int is the real freedom).
    return {"id": sid, "force": force, "quote": quote,
            "lf": {"kind": "object", "name": name, "type": ty}}


def _op(sid, word, carrier, quote, force="presupposition"):
    # an operator binds a lexicon word at a carrier and quotes the word it
    # construes (presupposition), or is a pure choice (empty quote).
    return {"id": sid, "force": force, "quote": quote,
            "lf": {"kind": "operator", "word": word, "carrier": carrier}}


def _amb(sid, carrier):
    return {"id": sid, "force": "choice", "quote": "",
            "lf": {"kind": "ambient", "carrier": carrier}}


def _qf(sid, binder, objs, quote, force="presupposition"):
    return {"id": sid, "force": force, "quote": quote,
            "lf": {"kind": "quantifier", "binder": binder,
                   "objects": list(objs)}}


def _hyp(sid, pred, quote, force="presupposition"):
    return {"id": sid, "force": force, "quote": quote,
            "lf": {"kind": "hypothesis", "pred": pred}}


def _concl(sid, pred, quote):
    return {"id": sid, "force": "demand", "quote": quote,
            "lf": {"kind": "conclusion", "pred": pred}}


# --- pred / term nodes (F-G AST) --------------------------------------------
def _ref(n):
    return {"ref": n}


def _lit(v):
    return {"lit": v}


def _ap(op, *args):
    # one shape for both value-producing terms and boolean atoms/connectives.
    return {"op": op, "args": list(args)}


def _reading(theorem, statements):
    return {"theorem": theorem, "statements": statements}


# ---------------------------------------------------------------------------
# Parse fixtures (>= 10 hand-written MathReadings covering the F1 vocabulary).
# ---------------------------------------------------------------------------
FIXTURES = {

    # divisibility (dvd) + quantifier + hypothesis + term multiplication.
    "dvd_basic": {
        "source": "For integers a, b and c, if a divides b then a divides b "
                  "times c.",
        "reading": _reading("dvd_mul_of_dvd", [
            _obj("o_a", "a", "Int"),
            _obj("o_b", "b", "Int"),
            _obj("o_c", "c", "Int"),
            _op("op_dvd", "dvd", "Int", "divides"),
            _amb("amb", "Int"),
            _qf("q", "forall", ["a", "b", "c"], "for integers a, b and c"),
            _hyp("h", _ap("dvd", _ref("a"), _ref("b")), "a divides b"),
            _concl("c", _ap("dvd", _ref("a"),
                            _ap("*", _ref("b"), _ref("c"))),
                   "a divides b times c"),
        ]),
        "expect": "parse",
    },

    # parity: even, the `and` connective, Nat ambient, `+`.
    "even_add": {
        "source": "For naturals m and n, if m is even and n is even then m "
                  "plus n is even.",
        "reading": _reading("even_add", [
            _obj("o_m", "m", "Nat"),
            _obj("o_n", "n", "Nat"),
            _op("op_even", "even", "Nat", "even"),
            _amb("amb", "Nat"),
            _qf("q", "forall", ["m", "n"], "for naturals m and n"),
            _hyp("h", _ap("and", _ap("even", _ref("m")),
                          _ap("even", _ref("n"))),
                 "m is even and n is even"),
            _concl("c", _ap("even", _ap("+", _ref("m"), _ref("n"))),
                   "m plus n is even"),
        ]),
        "expect": "parse",
    },

    # parity: odd, an integer literal in a term.
    "odd_succ": {
        "source": "For every natural n, if n is even then n plus 1 is odd.",
        "reading": _reading("odd_succ_of_even", [
            _obj("o_n", "n", "Nat"),
            _op("op_even", "even", "Nat", "even"),
            _op("op_odd", "odd", "Nat", "odd"),
            _amb("amb", "Nat"),
            _qf("q", "forall", ["n"], "for every natural n"),
            _hyp("h", _ap("even", _ref("n")), "n is even"),
            _concl("c", _ap("odd", _ap("+", _ref("n"), _lit(1))),
                   "n plus 1 is odd"),
        ]),
        "expect": "parse",
    },

    # gcd (a term operator) + coprime (a pred, Nat-only).
    "coprime_gcd": {
        "source": "For naturals a and b, if a and b are coprime then the gcd "
                  "of a and b equals 1.",
        "reading": _reading("gcd_eq_one_of_coprime", [
            _obj("o_a", "a", "Nat"),
            _obj("o_b", "b", "Nat"),
            _op("op_cop", "coprime", "Nat", "coprime"),
            _op("op_gcd", "gcd", "Nat", "gcd"),
            _amb("amb", "Nat"),
            _qf("q", "forall", ["a", "b"], "for naturals a and b"),
            _hyp("h", _ap("coprime", _ref("a"), _ref("b")),
                 "a and b are coprime"),
            _concl("c", _ap("=", _ap("gcd", _ref("a"), _ref("b")), _lit(1)),
                   "the gcd of a and b equals 1"),
        ]),
        "expect": "parse",
    },

    # mod (the lexicon term operator) + the `<` inequality + positivity hyp.
    "mod_lt": {
        "source": "For naturals n and k, if k is positive then n mod k is "
                  "less than k.",
        "reading": _reading("mod_lt_of_pos", [
            _obj("o_n", "n", "Nat"),
            _obj("o_k", "k", "Nat"),
            _op("op_mod", "mod", "Nat", "mod"),
            _amb("amb", "Nat"),
            _qf("q", "forall", ["n", "k"], "for naturals n and k"),
            # "k is positive" is 0 < k -- only `<`/`<=` exist (F-G note).
            _hyp("h", _ap("<", _lit(0), _ref("k")), "k is positive"),
            _concl("c", _ap("<", _ap("mod", _ref("n"), _ref("k")), _ref("k")),
                   "n mod k is less than k"),
        ]),
        "expect": "parse",
    },

    # `%` (the built-in term operator) + the `or` connective.
    "mod_two_cases": {
        "source": "For every natural n, n modulo 2 is 0 or n modulo 2 is 1.",
        "reading": _reading("mod_two_eq_zero_or_one", [
            _obj("o_n", "n", "Nat"),
            _amb("amb", "Nat"),
            _qf("q", "forall", ["n"], "for every natural n"),
            _concl("c", _ap("or",
                            _ap("=", _ap("%", _ref("n"), _lit(2)), _lit(0)),
                            _ap("=", _ap("%", _ref("n"), _lit(2)), _lit(1))),
                   "n modulo 2 is 0 or n modulo 2 is 1"),
        ]),
        "expect": "parse",
    },

    # integer subtraction (`-` over Int -- real, not truncated) + `<`.
    "int_sub": {
        "source": "For all integers a and b, if b is less than a then a minus "
                  "b is positive.",
        "reading": _reading("sub_pos_of_lt", [
            _obj("o_a", "a", "Int"),
            _obj("o_b", "b", "Int"),
            _amb("amb", "Int"),
            _qf("q", "forall", ["a", "b"], "for all integers a and b"),
            _hyp("h", _ap("<", _ref("b"), _ref("a")), "b is less than a"),
            _concl("c", _ap("<", _lit(0), _ap("-", _ref("a"), _ref("b"))),
                   "a minus b is positive"),
        ]),
        "expect": "parse",
    },

    # a MULTI-HYPOTHESIS theorem + the `<=` inequality.
    "le_trans": {
        "source": "For naturals a, b and c, if a is at most b and b is at "
                  "most c then a is at most c.",
        "reading": _reading("le_trans_nat", [
            _obj("o_a", "a", "Nat"),
            _obj("o_b", "b", "Nat"),
            _obj("o_c", "c", "Nat"),
            _amb("amb", "Nat"),
            _qf("q", "forall", ["a", "b", "c"], "for naturals a, b and c"),
            _hyp("h1", _ap("<=", _ref("a"), _ref("b")), "a is at most b"),
            _hyp("h2", _ap("<=", _ref("b"), _ref("c")), "b is at most c"),
            _concl("c", _ap("<=", _ref("a"), _ref("c")), "a is at most c"),
        ]),
        "expect": "parse",
    },

    # an Int ambient where the carrier CHOICE is load-bearing: `a - b + b = a`
    # holds over Int but not over truncated Nat -- the killer ambient.
    "sub_add_cancel": {
        "source": "For all integers a and b, a minus b plus b equals a.",
        "reading": _reading("sub_add_cancel", [
            _obj("o_a", "a", "Int"),
            _obj("o_b", "b", "Int"),
            _amb("amb", "Int"),
            _qf("q", "forall", ["a", "b"], "for all integers a and b"),
            _concl("c", _ap("=",
                            _ap("+", _ap("-", _ref("a"), _ref("b")),
                                _ref("b")),
                            _ref("a")),
                   "a minus b plus b equals a"),
        ]),
        "expect": "parse",
    },

    # dvd + mod together (the % lexicon operator inside an `=` atom).
    "dvd_mod": {
        "source": "For naturals a and n, if a divides n then n mod a equals 0.",
        "reading": _reading("mod_eq_zero_of_dvd", [
            _obj("o_a", "a", "Nat"),
            _obj("o_n", "n", "Nat"),
            _op("op_dvd", "dvd", "Nat", "divides"),
            _op("op_mod", "mod", "Nat", "mod"),
            _amb("amb", "Nat"),
            _qf("q", "forall", ["a", "n"], "for naturals a and n"),
            _hyp("h", _ap("dvd", _ref("a"), _ref("n")), "a divides n"),
            _concl("c", _ap("=", _ap("mod", _ref("n"), _ref("a")), _lit(0)),
                   "n mod a equals 0"),
        ]),
        "expect": "parse",
    },

    # `^` with a LITERAL exponent (SMT-LIB has no exponentiation; D10).
    "sq_even": {
        "source": "For every natural n, if n is even then n squared is even.",
        "reading": _reading("sq_even_of_even", [
            _obj("o_n", "n", "Nat"),
            _op("op_even", "even", "Nat", "even"),
            _amb("amb", "Nat"),
            _qf("q", "forall", ["n"], "for every natural n"),
            _hyp("h", _ap("even", _ref("n")), "n is even"),
            _concl("c", _ap("even", _ap("^", _ref("n"), _lit(2))),
                   "n squared is even"),
        ]),
        "expect": "parse",
    },

    # -----------------------------------------------------------------------
    # Refusal fixtures -- every one is caught at the math-reading-gate.
    # -----------------------------------------------------------------------

    # a fabricated-quote conclusion: the demand quotes a span the source never
    # says ("n times 1 ...") -- a demand may not be fabricated.
    "bad_fabricated_quote": {
        "source": "For every natural n, n plus 0 equals n.",
        "reading": _reading("add_zero", [
            _obj("o_n", "n", "Nat"),
            _amb("amb", "Nat"),
            _qf("q", "forall", ["n"], "for every natural n"),
            _concl("c", _ap("=", _ap("+", _ref("n"), _lit(0)), _ref("n")),
                   "n times 1 equals n"),
        ]),
        "expect": ("refuse", "math-reading-gate"),
    },

    # a choice carrying a non-empty quote: a choice is formalization freedom,
    # not something the text says, so its quote MUST be empty.
    "bad_choice_quote": {
        "source": "For every natural n, n plus 0 equals n.",
        "reading": _reading("add_zero", [
            _obj("o_n", "n", "Nat"),
            {"id": "amb", "force": "choice", "quote": "natural",
             "lf": {"kind": "ambient", "carrier": "Nat"}},
            _qf("q", "forall", ["n"], "for every natural n"),
            _concl("c", _ap("=", _ap("+", _ref("n"), _lit(0)), _ref("n")),
                   "n plus 0 equals n"),
        ]),
        "expect": ("refuse", "math-reading-gate"),
    },

    # an undeclared-referent pred: `m` is never introduced as an object.
    "bad_undeclared_ref": {
        "source": "For every natural n, n plus m equals m plus n.",
        "reading": _reading("add_comm_partial", [
            _obj("o_n", "n", "Nat"),
            _amb("amb", "Nat"),
            _qf("q", "forall", ["n"], "for every natural n"),
            _concl("c", _ap("=", _ap("+", _ref("n"), _ref("m")),
                            _ap("+", _ref("m"), _ref("n"))),
                   "n plus m equals m plus n"),
        ]),
        "expect": ("refuse", "math-reading-gate"),
    },

    # fragment-miss: an operator word outside MATH_OPERATORS (`prime`).  Raises
    # FragmentMiss with missing_kind_guess="operator:prime" -- F4 demand data.
    "miss_prime": {
        "source": "For every natural n, if n is prime then n is at least 2.",
        "reading": _reading("ge_two_of_prime", [
            _obj("o_n", "n", "Nat"),
            _op("op_prime", "prime", "Nat", "prime"),
            _amb("amb", "Nat"),
            _qf("q", "forall", ["n"], "for every natural n"),
            _concl("c", _ap("<=", _lit(2), _ref("n")), "n is at least 2"),
        ]),
        "expect": ("refuse", "math-reading-gate"),
    },

    # fragment-miss: a real-valued carrier is outside the whitelist (Nat, Int).
    # Raises FragmentMiss with missing_kind_guess="carrier:Real".
    "miss_real_carrier": {
        "source": "For every real number x, x plus 0 equals x.",
        "reading": _reading("add_zero_real", [
            _obj("o_x", "x", "Real"),
            _amb("amb", "Int"),
            _qf("q", "forall", ["x"], "for every real number x"),
            _concl("c", _ap("=", _ap("+", _ref("x"), _lit(0)), _ref("x")),
                   "x plus 0 equals x"),
        ]),
        "expect": ("refuse", "math-reading-gate"),
    },
}

# The refusal fixtures whose refusal is a first-class FragmentMiss (a
# BadMathReading subclass carrying `.missing_kind_guess`, the F4 demand data).
FRAGMENT_MISS = {"miss_prime", "miss_real_carrier"}


def reading_text(name: str) -> str:
    """The reading JSON string {theorem, statements} for `name` -- the first
    argument to parse_math_reading."""
    return json.dumps(FIXTURES[name]["reading"])


def source(name: str) -> str:
    """The raw source sentence for `name` -- parse_math_reading's second arg."""
    return FIXTURES[name]["source"]
