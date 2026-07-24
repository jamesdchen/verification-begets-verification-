"""C2 (PLAN_FRAGMENT §3): session-inline MathReadings for the FIRST
census-sourced corpus additions -- sources 67-70.

PROVENANCE (the point of the exercise).  Each source's text is the VERBATIM
prose of a blueprint-census attempt-candidate from the math2001 corpus
(`specs/mathsources/math2001/nodes.jsonl`; The Mechanics of Proof,
H. Macbeth, chapter 3), NOT a sentence a maintainer authored:

    67_square_dvd_shift       <- math2001 03_Parity_and_Divisibility#problem-012
    68_square_dvd_chain       <- math2001 03_Parity_and_Divisibility#problem-013
    69_product_dvd_projection <- math2001 03_Parity_and_Divisibility#problem-014
    70_dvd_le_bound           <- math2001 03_Parity_and_Divisibility#problem-016

Authoring mirrors wp_auth_readings.py EXACTLY: one reading per source,
authored by the orchestrating session (UNMETERED -- cost columns VOID),
reused identically by both arms.  Quotes are LITERAL source substrings
(whitespace/case-normalized), which for this corpus means quoting the
sentence's LaTeX spans verbatim.

All four are forall-class, in-fragment, and TRUE over the B=8 box (checked
before authoring; never distort a reading to force a green):
  * 67  a | b  ->  a | b^2 + 2b            (Int)
  * 68  a | b, b^2 | c  ->  a^2 | c        (Nat)
  * 69  x*y | z  ->  x | z                 (Nat)
  * 70  0 < b, a | b  ->  a <= b           (Nat)
"""


def _amb(carrier):
    return {"id": "amb", "force": "choice", "quote": "",
            "lf": {"kind": "ambient", "carrier": carrier}}


def _obj(i, name, quote, typ):
    return {"id": i, "force": "presupposition", "quote": quote,
            "lf": {"kind": "object", "name": name, "type": typ}}


def _q(sid, objects, quote):
    return {"id": sid, "force": "demand", "quote": quote,
            "lf": {"kind": "quantifier", "binder": "forall",
                   "objects": objects}}


def _hyp(i, pred, quote, force="demand"):
    return {"id": i, "force": force, "quote": quote,
            "lf": {"kind": "hypothesis", "pred": pred}}


def _con(pred, quote):
    return {"id": "c", "force": "demand", "quote": quote,
            "lf": {"kind": "conclusion", "pred": pred}}


def r(name):
    return {"ref": name}


def lit(n):
    return {"lit": n}


def op(o, *args):
    return {"op": o, "args": list(args)}


READINGS = {}

READINGS["67_square_dvd_shift"] = {"theorem": "square_dvd_shift",
    "statements": [
        _amb("Int"),
        _obj("oa", "a", r"\(a\) and \(b\) be integers", "Int"),
        _obj("ob", "b", r"\(a\) and \(b\) be integers", "Int"),
        _q("q", ["a", "b"], r"Let \(a\) and \(b\) be integers"),
        _hyp("h1", op("dvd", r("a"), r("b")), r"\(a \mid b\)"),
        _con(op("dvd", r("a"),
                op("+", op("^", r("b"), lit(2)), op("*", lit(2), r("b")))),
             r"\(a \mid b^2+2b\)")]}

READINGS["68_square_dvd_chain"] = {"theorem": "square_dvd_chain",
    "statements": [
        _amb("Nat"),
        _obj("oa", "a", r"\(c\) be natural numbers", "Nat"),
        _obj("ob", "b", r"\(c\) be natural numbers", "Nat"),
        _obj("oc", "c", r"\(c\) be natural numbers", "Nat"),
        _q("q", ["a", "b", "c"], r"be natural numbers"),
        _hyp("h1", op("dvd", r("a"), r("b")), r"\(a \mid b\)"),
        _hyp("h2", op("dvd", op("^", r("b"), lit(2)), r("c")),
             r"\(b ^2\mid c\)"),
        _con(op("dvd", op("^", r("a"), lit(2)), r("c")), r"\(a^2 \mid c\)")]}

READINGS["69_product_dvd_projection"] = {"theorem": "product_dvd_projection",
    "statements": [
        _amb("Nat"),
        _obj("ox", "x", r"\(z\) be natural numbers", "Nat"),
        _obj("oy", "y", r"\(z\) be natural numbers", "Nat"),
        _obj("oz", "z", r"\(z\) be natural numbers", "Nat"),
        _q("q", ["x", "y", "z"], r"be natural numbers"),
        _hyp("h1", op("dvd", op("*", r("x"), r("y")), r("z")),
             r"\(xy \mid z\)"),
        _con(op("dvd", r("x"), r("z")), r"\(x \mid z\)")]}

READINGS["70_dvd_le_bound"] = {"theorem": "dvd_le_bound",
    "statements": [
        _amb("Nat"),
        _obj("oa", "a", r"\(a\) and \(b\) be natural numbers", "Nat"),
        _obj("ob", "b", r"\(a\) and \(b\) be natural numbers", "Nat"),
        _q("q", ["a", "b"], r"Let \(a\) and \(b\) be natural numbers"),
        _hyp("h1", op("<", lit(0), r("b")), r"\(b\) positive",
             force="presupposition"),
        _hyp("h2", op("dvd", r("a"), r("b")), r"\(a\) divides \(b\)"),
        _con(op("<=", r("a"), r("b")), r"\(a \le b\)")]}
