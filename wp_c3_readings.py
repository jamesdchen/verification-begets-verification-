"""C3 (PLAN_FRAGMENT §3.1 cadence): session-inline MathReadings for the SECOND
census-sourced corpus additions -- sources 71-74.

Sibling of wp_c2_readings.py (sources 67-70); same discipline, next batch.
PROVENANCE.  Each source's text is the VERBATIM prose of a blueprint-census
attempt-candidate from the math2001 corpus
(`specs/mathsources/math2001/nodes.jsonl`; The Mechanics of Proof,
H. Macbeth, chapter 3), NOT a sentence a maintainer authored:

    71_dvd_pos      <- math2001 03_Parity_and_Divisibility#problem-017
    72_dvd_cancel8  <- math2001 03_Parity_and_Divisibility#problem-026
    73_dvd_cancel5  <- math2001 03_Parity_and_Divisibility#problem-027
    74_dvd_both     <- math2001 03_Parity_and_Divisibility#problem-028

Authoring mirrors wp_c2_readings.py EXACTLY: one reading per source, authored
by the orchestrating session (UNMETERED -- cost columns VOID), reused
identically by both arms.  Quotes are LITERAL source substrings
(whitespace/case-normalized), which for this corpus means quoting the
sentence's LaTeX spans verbatim.

The batch stays in the divisibility family already priced by sources 67-70
(the coprime-cancellation and divides-both shapes math2001 chapter 3 closes
with) -- arity-2 `dvd` hypotheses, deliberately NOT the arity-1 even/odd
op-slot, so the census-of-record even/odd macro coverage invariant
(tests/test_cluster_key.py::test_b_evenodd_macro_survives_and_covers) is left
undisturbed.  All four are forall-class, in-fragment (Nat/Int carriers,
`dvd`/`<` lexicon), and TRUE over the B=8 box (checked before authoring by
`run.formalize.certify_statement`; never distort a reading to force a green):
  * 71  0 < b, a | b        ->  0 < a           (Nat)  -- companion to 70
  * 72  8 | 5n              ->  8 | n            (Int)  -- coprime cancellation
  * 73  5 | 3n              ->  5 | n            (Int)  -- coprime cancellation
  * 74  8 | m, 5 | m        ->  40 | m           (Int)  -- divides-both / lcm
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

READINGS["71_dvd_pos"] = {"theorem": "dvd_pos",
    "statements": [
        _amb("Nat"),
        _obj("oa", "a", r"\(a\) and \(b\) be natural numbers", "Nat"),
        _obj("ob", "b", r"\(a\) and \(b\) be natural numbers", "Nat"),
        _q("q", ["a", "b"], r"Let \(a\) and \(b\) be natural numbers"),
        _hyp("h1", op("<", lit(0), r("b")), r"\(b\) positive",
             force="presupposition"),
        _hyp("h2", op("dvd", r("a"), r("b")), r"\(a\) divides \(b\)"),
        _con(op("<", lit(0), r("a")), r"\(a\) is positive")]}

READINGS["72_dvd_cancel8"] = {"theorem": "dvd_cancel8",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"\(n\) be an integer", "Int"),
        _q("q", ["n"], r"Let \(n\) be an integer"),
        _hyp("h1", op("dvd", lit(8), op("*", lit(5), r("n"))),
             r"\(5n\) is a multiple of \(8\)"),
        _con(op("dvd", lit(8), r("n")),
             r"\(n\) is also a multiple of \(8\)")]}

READINGS["73_dvd_cancel5"] = {"theorem": "dvd_cancel5",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"for some integer \(n\)", "Int"),
        _q("q", ["n"], r"for some integer \(n\)"),
        _hyp("h1", op("dvd", lit(5), op("*", lit(3), r("n"))),
             r"\(5\) divides \(3n\)"),
        _con(op("dvd", lit(5), r("n")), r"\(5\) also divides \(n\)")]}

READINGS["74_dvd_both"] = {"theorem": "dvd_both",
    "statements": [
        _amb("Int"),
        _obj("om", "m", r"\(m\) be an integer", "Int"),
        _q("q", ["m"], r"Let \(m\) be an integer"),
        _hyp("h1", op("dvd", lit(8), r("m")), r"divisible by 8 and by 5"),
        _hyp("h2", op("dvd", lit(5), r("m")), r"divisible by 8 and by 5"),
        _con(op("dvd", lit(40), r("m")), r"divisible by 40")]}
