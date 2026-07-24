"""C3 cycle-02 (PLAN_FRAGMENT §3.1 cadence): session-inline MathReadings for the
THIRD census-sourced corpus additions -- sources 75-78.

Sibling of wp_c3_readings.py (sources 71-74) and wp_c2_readings.py (67-70);
same discipline, next batch.  PROVENANCE.  Each source's text is the VERBATIM
prose of a blueprint-census attempt-candidate from the math2001 corpus
(`specs/mathsources/math2001/nodes.jsonl`; The Mechanics of Proof,
H. Macbeth, chapter 1 "Proofs by Calculation"), NOT a sentence a maintainer
authored:

    75_solve_shift   <- math2001 01_Proofs_by_Calculation#problem-007
    76_solve_halve   <- math2001 01_Proofs_by_Calculation#problem-010
    77_solve_system  <- math2001 01_Proofs_by_Calculation#problem-011
    78_square_bound  <- math2001 01_Proofs_by_Calculation#problem-022

Authoring mirrors wp_c3_readings.py EXACTLY: one reading per source, authored
by the orchestrating session (UNMETERED -- cost columns VOID), reused
identically by both arms.  Quotes are LITERAL source substrings
(whitespace/case-normalized), which for this corpus means quoting the
sentence's LaTeX spans verbatim.

The batch DELIBERATELY LEAVES the divisibility family (67-74) for the
chapter-1 LINEAR-CALCULATION family -- Int carriers under the `+ - * = <=`
lexicon, no `dvd`/parity operators at all -- precisely BECAUSE the ch3
`dvd`-forall census candidates are exhausted (only ground facts 010/011/015
remain, non-forall) and because a linear-arithmetic cluster cannot perturb
the even/odd macro coverage invariant
(tests/test_cluster_key.py::test_b_evenodd_macro_survives_and_covers) that the
`dvd` batches were shaped around -- it touches neither the parity op-slot nor
the `dvd` macros.  All four are forall-class, in-fragment, and TRUE over the
B=8 box (checked before authoring by `run.formalize.certify_statement`; never
distort a reading to force a green; the `>`/`>=` candidates 016/021 were
MEASURED to fall outside the `< <=` lexicon at the reading gate and were NOT
shipped):
  * 75  x+4=2                    ->  x=-2     (Int)  -- solve a linear equation
  * 76  2x+3=x                   ->  x=-3     (Int)  -- solve a linear equation
  * 77  2x-y=4, y-x+1=2          ->  x=5      (Int)  -- solve a linear system
  * 78  m^2+n <= 2               ->  n <= 2   (Int)  -- square-nonnegativity bound
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

READINGS["75_solve_shift"] = {"theorem": "solve_shift",
    "statements": [
        _amb("Int"),
        _obj("ox", "x", r"\(x\) be an integer", "Int"),
        _q("q", ["x"], r"Let \(x\) be an integer"),
        _hyp("h1", op("=", op("+", r("x"), lit(4)), lit(2)), r"\(x+4=2\)"),
        _con(op("=", r("x"), lit(-2)), r"\(x=-2\)")]}

READINGS["76_solve_halve"] = {"theorem": "solve_halve",
    "statements": [
        _amb("Int"),
        _obj("ox", "x", r"\(x\) be an integer", "Int"),
        _q("q", ["x"], r"Let \(x\) be an integer"),
        _hyp("h1", op("=", op("+", op("*", lit(2), r("x")), lit(3)), r("x")),
             r"\(2x + 3 = x\)"),
        _con(op("=", r("x"), lit(-3)), r"\(x=-3\)")]}

READINGS["77_solve_system"] = {"theorem": "solve_system",
    "statements": [
        _amb("Int"),
        _obj("ox", "x", r"\(x\) and \(y\) be integers", "Int"),
        _obj("oy", "y", r"\(x\) and \(y\) be integers", "Int"),
        _q("q", ["x", "y"], r"Let \(x\) and \(y\) be integers"),
        _hyp("h1", op("=", op("-", op("*", lit(2), r("x")), r("y")), lit(4)),
             r"\(2x-y=4\)"),
        _hyp("h2", op("=", op("+", op("-", r("y"), r("x")), lit(1)), lit(2)),
             r"\(y-x+1=2\)"),
        _con(op("=", r("x"), lit(5)), r"\(x=5\)")]}

READINGS["78_square_bound"] = {"theorem": "square_bound",
    "statements": [
        _amb("Int"),
        _obj("om", "m", r"\(m\) and \(n\) be integers", "Int"),
        _obj("on", "n", r"\(m\) and \(n\) be integers", "Int"),
        _q("q", ["m", "n"], r"\(m\) and \(n\) be integers"),
        _hyp("h1", op("<=", op("+", op("*", r("m"), r("m")), r("n")), lit(2)),
             r"\(m ^ 2 + n \le 2\)"),
        _con(op("<=", r("n"), lit(2)), r"\(n \le 2\)")]}
