"""C7 (PLAN_FRAGMENT §3.1 cadence): session-inline MathReadings for the
census-sourced corpus additions below -- SKELETON emitted by
tools/intake_from_frontier.py.  Sibling of wp_c2/c3/c4_readings.py;
same discipline, next batch.

PROVENANCE.  Each source's text is the VERBATIM prose of a census
attempt-candidate node (NOT a sentence a maintainer authored):

    84_02_proofs_with_structure_problem_026 <- math2001 02_Proofs_with_Structure#problem-026
    85_02_proofs_with_structure_problem_028 <- math2001 02_Proofs_with_Structure#problem-028

The READINGS themselves are LEFT UNAUTHORED on purpose: intake is
mechanical and makes NO certification claim.  The driver session
authors one reading per source here (UNMETERED; reused identically
by both arms), gate-checks it, box-verifies TRUE, and certifies via
the inline-author checkpoint resume.  A source that then fails to
certify is recorded as a first-class REFUSAL, never dropped.
"""


PROVENANCE = {
    '84_02_proofs_with_structure_problem_026': {
        "corpus": 'math2001',
        "node_id": '02_Proofs_with_Structure#problem-026',
        "text_sha256": '8ad46fd0bf6629c488e3ba2d93d567556c97f9f9c8044f897ac57b4f17c362da',
    },
    '85_02_proofs_with_structure_problem_028': {
        "corpus": 'math2001',
        "node_id": '02_Proofs_with_Structure#problem-028',
        "text_sha256": '0b1248a7c24d10a12a6daa805ab65bc4c492c3a97fbbcb9ee3d8cf613fbab6c4',
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


def _objc(name, typ):
    # a formalization-choice object referent (empty quote): used when the
    # witness/carrier is the analyst's choice, not the text's presupposition.
    return {"id": "o_" + name, "force": "choice", "quote": "",
            "lf": {"kind": "object", "name": name, "type": typ}}


def _qp(sid, objects, quote):
    # a universally-quantified binder presupposed by the source ("Let a be...").
    return {"id": sid, "force": "presupposition", "quote": quote,
            "lf": {"kind": "quantifier", "binder": "forall",
                   "objects": objects}}


READINGS = {}

# --- DRIVER AUTHORS BELOW (one reading per source) ------------------
# Both readings are the SANCTIONED WITNESS-TERM form of an existential claim
# (the T6b pattern -- tests/test_t6b_predecessor_int.py: "the committed reading
# is the witness-term form: a forall (no exists binder)").  The source asks to
# SHOW existence; the analyst discharges it constructively by SUPPLYING the
# witnesses as terms and demanding the resulting in-fragment identity.  Both were
# box-verified TRUE by run.formalize.certify_statement BEFORE authoring (never
# distort a reading to force a green); each uses only BUILTIN ops (+, -, *, ^ at
# literal exponents, =, !=), so no operator word, macro, or trust root grows, and
# neither carries parity/divisibility structure (the even/odd op-slot and dvd
# macros are UNTOUCHED -- the coverage invariant survives as in 82-83).

# 84  <- ch2 problem-026: "there exist integers m and n such that m^2-n^2=2a+1".
# Witnesses m := a+1, n := a make (a+1)^2 - a^2 = 2a+1 a pure forall identity
# over the ambient Int carrier (a^2 + 2a + 1 - a^2 = 2a+1 for every a).
READINGS['84_02_proofs_with_structure_problem_026'] = {
    "theorem": "sq_diff_hits_every_odd",
    "statements": [
        _amb("Int"),
        _objc("a", "Int"),
        _qp("qa", ["a"], r"Let \(a\) be an integer"),
        _con(op("=",
                op("-", op("^", op("+", r("a"), lit(1)), lit(2)),
                        op("^", r("a"), lit(2))),
                op("+", op("*", lit(2), r("a")), lit(1))),
             "m^2-n^2=2a+1"),
    ]}

# 85  <- ch2 problem-028: "there exist natural numbers a,b,c,d such that
# a^3+b^3=1729=c^3+d^3, but a!=c and a!=d".  The Hardy-Ramanujan taxicab number:
# witnesses a:=1, b:=12, c:=9, d:=10 (1 + 1728 = 1729 = 729 + 1000, 1 != 9,
# 1 != 10) discharge the whole existential as a ground in-fragment conjunction.
READINGS['85_02_proofs_with_structure_problem_028'] = {
    "theorem": "taxicab_1729",
    "statements": [
        _amb("Nat"),
        _con(op("and",
                op("and",
                   op("=", op("+", op("^", lit(1), lit(3)),
                                   op("^", lit(12), lit(3))), lit(1729)),
                   op("=", lit(1729), op("+", op("^", lit(9), lit(3)),
                                              op("^", lit(10), lit(3))))),
                op("and", op("!=", lit(1), lit(9)),
                          op("!=", lit(1), lit(10)))),
             "a^3+b^3=1729=c^3+d^3"),
    ]}
