"""C15 (PLAN_FRAGMENT §3.1 cadence): session-inline MathReadings for the
census-sourced corpus additions below -- skeleton emitted by
tools/intake_from_frontier.py, then authored by the driver session.
Sibling of wp_c2/c3/c4_readings.py; same discipline, next batch.

PROVENANCE.  Each source's text is the VERBATIM prose of a census
attempt-candidate node (NOT a sentence a maintainer authored):

    122_10_relations_problem_008 <- math2001 10_Relations#problem-008

THE WHOLE READY LIST WAS ONE SUBJECT this cycle (cycle 16 left ready = 1),
so this is a one-source batch and the corpus's FIRST 10_Relations source.

The READING below was authored by the driver session (UNMETERED; reused
identically by both arms), gate-checked, and box-verified TRUE via
run.formalize.certify_statement BEFORE it was written -- together with the
FALSE-variant probes recorded in results/c3_cycle_17.md, which is where the
one conjunct the box does NOT have teeth on is written down.
"""


PROVENANCE = {
    '122_10_relations_problem_008': {
        "corpus": 'math2001',
        "node_id": '10_Relations#problem-008',
        "text_sha256": 'aaa1238ee16bf473d5925859f162d2566bb47675bc0f9c8eb56626098c98a130',
    },
}


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

# --- DRIVER AUTHORS BELOW (one reading per source) ------------------

# 122  <- 10_Relations problem-008: the relation x ~ y iff x = y (mod n) on Z
# is an EQUIVALENCE RELATION.  The corpus's first 10_Relations source.
#
# THE RELATION VANISHES, the way source 121's set did.  The fragment has no
# relation objects and no second-order quantifier, but this subject never needs
# one: `~` is DEFINED in the source itself, at the point of use, by an
# in-fragment condition -- so unfolding it is definitional, not a relocation of
# the demand onto some corpus definition the fragment also lacks (contrast
# `defined-predicate`, cycle 12).  What survives the unfolding is exactly the
# three properties the phrase "is an equivalence relation" DEMANDS, written
# out: reflexivity, symmetry, transitivity, conjoined.
#
# CONGRUENCE IS RENDERED AS `dvd(n, x - y)`, not as the residue equality
# `mod(x,n) = mod(y,n)` that source 118 used.  BOTH readings were measured and
# BOTH certify; the choice is recorded rather than silent:
#   * the two are equivalent for every n (Mathlib's Int.modEq_iff_dvd), so this
#     is a choice between equivalent renderings, never a weakening;
#   * `dvd` is TOTAL at n = 0 -- it compiles to (ite (= n 0) (= (x-y) 0) ...),
#     whereas SMT-LIB leaves `mod` by zero unspecified, and "Let n be an
#     integer" admits n = 0;
#   * under residue equality all three conjuncts collapse into properties of
#     `=` itself (reflexivity becomes the syntactic tautology t = t), so the
#     reading would carry no divisibility content at all.
#
# ONE OBJECT IS NOT NAMED IN THE PROSE: `z`.  Transitivity needs a third
# element, and the source names only x and y in its definition of `~`; z is
# grounded in the phrase that demands transitivity ("is an equivalence
# relation"), which is where it genuinely comes from.
#
# The single forall block over n,x,y,z is equivalent to quantifying each
# conjunct over only the variables it uses (Int is non-empty), so the shared
# binder is a notation, not a strengthening.
#
# HONESTY -- the box has teeth on TWO of the three conjuncts, not three.
# Measured false variants: an unconditional congruence, a false reflexivity
# (n | x), and a false symmetry consequent are ALL refuted at instances.  But
# transitivity with its conclusion corrupted from n | (x-z) to n | (x+z) STILL
# CERTIFIES: the five smallest hypothesis-satisfying instances are the origin
# and its four unit neighbours, where z = 0 in four of them and the fifth has a
# false antecedent, so the box never separates x-z from x+z.  The transitivity
# conjunct's green is COVERAGE, not a refutation-backed verdict.  Recorded in
# results/c3_cycle_17.md rather than left implicit behind a green.
READINGS['122_10_relations_problem_008'] = {
    "theorem": "int_congruence_is_equivalence",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"Let \(n\) be an integer", "Int"),
        _obj("ox", "x", r"\(x\sim y\) if \(x\equiv y\mod n\)", "Int"),
        _obj("oy", "y", r"\(x\sim y\) if \(x\equiv y\mod n\)", "Int"),
        _obj("oz", "z", "is an equivalence relation", "Int"),
        _q("q", ["n", "x", "y", "z"], "is an equivalence relation"),
        _con(op("and",
                # reflexive: x ~ x
                op("dvd", r("n"), op("-", r("x"), r("x"))),
                # symmetric: x ~ y -> y ~ x
                op("implies",
                   op("dvd", r("n"), op("-", r("x"), r("y"))),
                   op("dvd", r("n"), op("-", r("y"), r("x")))),
                # transitive: x ~ y and y ~ z -> x ~ z
                op("implies",
                   op("and",
                      op("dvd", r("n"), op("-", r("x"), r("y"))),
                      op("dvd", r("n"), op("-", r("y"), r("z")))),
                   op("dvd", r("n"), op("-", r("x"), r("z"))))),
             "is an equivalence relation"),
    ]}
