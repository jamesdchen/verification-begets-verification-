"""C3 cycle-03 (PLAN_FRAGMENT §3.1 cadence): session-inline MathReadings for the
FOURTH census-sourced corpus additions -- sources 79-81.

Sibling of wp_c4_readings.py (sources 75-78), wp_c3_readings.py (71-74) and
wp_c2_readings.py (67-70); same discipline, next batch.  PROVENANCE.  Each
source's text is the VERBATIM prose of a blueprint-census attempt-candidate from
the math2001 corpus (`specs/mathsources/math2001/nodes.jsonl`; The Mechanics of
Proof, H. Macbeth), NOT a sentence a maintainer authored:

    79_solve_subst   <- math2001 01_Proofs_by_Calculation#problem-006
    80_linear_le     <- math2001 02_Proofs_with_Structure#problem-002
    81_product_zero  <- math2001 01_Proofs_by_Calculation#problem-004

Authoring mirrors wp_c4_readings.py EXACTLY: one reading per source, authored by
the orchestrating session (UNMETERED -- cost columns VOID), reused identically by
both arms.  Quotes are LITERAL source substrings (whitespace/case-normalized),
which for this corpus means quoting the sentence's LaTeX spans verbatim.

The batch CONTINUES the chapter-1/2 LINEAR-CALCULATION family (75-78) -- Int
carriers under the `+ - * = <=` lexicon, no `dvd`/parity operators at all -- and
NEARLY EXHAUSTS it: the remaining in-lexicon calculation candidates are these
three.  All three are forall-class, in-fragment, and TRUE over the B=8 box
(checked before authoring by `run.formalize.certify_statement`; never distort a
reading to force a green):
  * 79  a=2b+5, b=3            ->  a=11           (Int)  -- linear substitution
  * 80  m+3<=2n-1, n<=5        ->  m<=6           (Int)  -- linear <= chaining
  * 81  ad=bc, cf=de           ->  d(af-be)=0     (Int)  -- product identity

MEASURED-and-NOT-shipped this cycle (honesty; the census reports signals, never
fidelity verdicts, and a refusal is first-class demand data):
  * ch1 003 (b^2=2a^2, am+bn=1 -> (2an+bm)^2=2): TRUE but VACUOUS over the
    integers -- b^2=2a^2 forces a=b=0, then am+bn=0!=1, so the hypothesis has no
    integer witness and the F2.1 nonvacuity gate refuses it (recorded, never
    universalised into a green).
  * ch1 016/021, ch2 006: `>`/`>=` conclusions outside the `< <=` reading-gate
    lexicon (same refusal class as cycle-02's 016/021).
  * ch1 026, ch2 017: verbatim DUPLICATES of already-shipped 75_solve_shift /
    77_solve_system.
  * ch2 023/025/026/028, ch4/05/07 exists-class: `there exist ...` binders --
    the fragment is forall-class; existential shapes honest-skip.
  * the arity-1 parity op-slot and the `dvd` macros are UNTOUCHED (no parity/
    divisibility structure in the batch), so the even/odd macro coverage
    invariant survives exactly as in 71-78.

This file is the provenance record; the inline author reads READINGS[sid] and
returns the compiled reading to `bench_formalize.run_bench` on checkpoint resume
(only the 3 new source_ids enter; nothing prior is re-authored).
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

READINGS["79_solve_subst"] = {"theorem": "solve_subst",
    "statements": [
        _amb("Int"),
        _obj("oa", "a", r"\(a\) and \(b\) be integers", "Int"),
        _obj("ob", "b", r"\(a\) and \(b\) be integers", "Int"),
        _q("q", ["a", "b"], r"Let \(a\) and \(b\) be integers"),
        _hyp("h1", op("=", r("a"), op("+", op("*", lit(2), r("b")), lit(5))),
             r"\(a = 2b + 5\)"),
        _hyp("h2", op("=", r("b"), lit(3)), r"\(b = 3\)"),
        _con(op("=", r("a"), lit(11)), r"\(a = 11\)")]}

READINGS["80_linear_le"] = {"theorem": "linear_le",
    "statements": [
        _amb("Int"),
        _obj("om", "m", r"\(m\) and \(n\) be integers", "Int"),
        _obj("on", "n", r"\(m\) and \(n\) be integers", "Int"),
        _q("q", ["m", "n"], r"Let \(m\) and \(n\) be integers"),
        _hyp("h1", op("<=", op("+", r("m"), lit(3)),
                      op("-", op("*", lit(2), r("n")), lit(1))),
             r"\(m+3\le 2n-1\)"),
        _hyp("h2", op("<=", r("n"), lit(5)), r"\(n\le 5\)"),
        _con(op("<=", r("m"), lit(6)), r"\(m\le 6\)")]}

READINGS["81_product_zero"] = {"theorem": "product_zero",
    "statements": [
        _amb("Int"),
        _obj("oa", "a", r"\(a\) , \(b\) , \(c\) , \(d\) , \(e\) and \(f\) be integers", "Int"),
        _obj("ob", "b", r"\(a\) , \(b\) , \(c\) , \(d\) , \(e\) and \(f\) be integers", "Int"),
        _obj("oc", "c", r"\(a\) , \(b\) , \(c\) , \(d\) , \(e\) and \(f\) be integers", "Int"),
        _obj("od", "d", r"\(a\) , \(b\) , \(c\) , \(d\) , \(e\) and \(f\) be integers", "Int"),
        _obj("oe", "e", r"\(a\) , \(b\) , \(c\) , \(d\) , \(e\) and \(f\) be integers", "Int"),
        _obj("of", "f", r"\(a\) , \(b\) , \(c\) , \(d\) , \(e\) and \(f\) be integers", "Int"),
        _q("q", ["a", "b", "c", "d", "e", "f"],
           r"Let \(a\) , \(b\) , \(c\) , \(d\) , \(e\) and \(f\) be integers"),
        _hyp("h1", op("=", op("*", r("a"), r("d")), op("*", r("b"), r("c"))),
             r"\(ad = bc\)"),
        _hyp("h2", op("=", op("*", r("c"), r("f")), op("*", r("d"), r("e"))),
             r"\(cf=de\)"),
        _con(op("=", op("*", r("d"),
                        op("-", op("*", r("a"), r("f")), op("*", r("b"), r("e")))),
                 lit(0)),
             r"\(d(af - be) = 0\)")]}
