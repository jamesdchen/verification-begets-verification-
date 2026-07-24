"""C8 (PLAN_FRAGMENT §3.1 cadence): session-inline MathReadings for the
census-sourced corpus additions below -- SKELETON emitted by
tools/intake_from_frontier.py.  Sibling of wp_c2/c3/c4_readings.py;
same discipline, next batch.

PROVENANCE.  Each source's text is the VERBATIM prose of a census
attempt-candidate node (NOT a sentence a maintainer authored):

    86_04_proofs_with_structure_ii_problem_007 <- math2001 04_Proofs_with_Structure_II#problem-007
    87_04_proofs_with_structure_ii_problem_021 <- math2001 04_Proofs_with_Structure_II#problem-021
    88_04_proofs_with_structure_ii_problem_023 <- math2001 04_Proofs_with_Structure_II#problem-023
    89_04_proofs_with_structure_ii_problem_025 <- math2001 04_Proofs_with_Structure_II#problem-025
    90_04_proofs_with_structure_ii_problem_029 <- math2001 04_Proofs_with_Structure_II#problem-029

The READINGS themselves are LEFT UNAUTHORED on purpose: intake is
mechanical and makes NO certification claim.  The driver session
authors one reading per source here (UNMETERED; reused identically
by both arms), gate-checks it, box-verifies TRUE, and certifies via
the inline-author checkpoint resume.  A source that then fails to
certify is recorded as a first-class REFUSAL, never dropped.
"""


PROVENANCE = {
    '86_04_proofs_with_structure_ii_problem_007': {
        "corpus": 'math2001',
        "node_id": '04_Proofs_with_Structure_II#problem-007',
        "text_sha256": '5b1c98e4b8d227871261a3d6d8b866c1ba612bc7dd58b4c362abfd451b7cb0a0',
    },
    '87_04_proofs_with_structure_ii_problem_021': {
        "corpus": 'math2001',
        "node_id": '04_Proofs_with_Structure_II#problem-021',
        "text_sha256": '658a1fc9aa8dba4072c6b566545ea4cb9731f6e3d962901582446321907a8ceb',
    },
    '88_04_proofs_with_structure_ii_problem_023': {
        "corpus": 'math2001',
        "node_id": '04_Proofs_with_Structure_II#problem-023',
        "text_sha256": 'af56519629f41d69fb2e7a188d30e0a480ef418266163d4d980c53ff30cd633a',
    },
    '89_04_proofs_with_structure_ii_problem_025': {
        "corpus": 'math2001',
        "node_id": '04_Proofs_with_Structure_II#problem-025',
        "text_sha256": 'f73a5ae29e622331792b3779c23390992f04d5e7b048ae9c8c890c6c19c407ef',
    },
    '90_04_proofs_with_structure_ii_problem_029': {
        "corpus": 'math2001',
        "node_id": '04_Proofs_with_Structure_II#problem-029',
        "text_sha256": '374bb25c97241d6d96dc1907f7d828517f895943154f28bb97bb7c521aa74301',
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
    # binder is the analyst's choice, not a phrase the text presupposes.
    return {"id": "o_" + name, "force": "choice", "quote": "",
            "lf": {"kind": "object", "name": name, "type": typ}}


READINGS = {}

# --- DRIVER AUTHORS BELOW (one reading per source) ------------------
# Every reading below was box-verified TRUE by run.formalize.certify_statement
# BEFORE authoring (never distort a reading to force a green), and every quote
# is a LITERAL substring of its source file.  Only BUILTIN ops (+ - * ^ = != <
# <=, and/or/implies) and the grammar's `mod` term word appear -- no operator
# word, macro, or trust root grows.  NONE of the five carries parity or
# divisibility structure, so the arity-1 even/odd op-slot and the dvd macros
# are UNTOUCHED (the coverage invariant survives, as in 84-85).

# 86  <- ch4 problem-007: "for all SUFFICIENTLY LARGE integers n, n^3 >= 4n^2+7".
# `sufficiently large` is ch4 definition-001: exists N, for all n >= N.  That
# definition is itself a REFUSAL this cycle (definitional biconditional +
# predicate variable) -- but the reading does not need it: the analyst
# discharges the outer existential CONSTRUCTIVELY in the sanctioned witness-term
# form (T6b), supplying N := 5 as a term.  What remains is a pure forall over
# the Int carrier: 5 <= n  ->  4n^2+7 <= n^3.  (N=5 is tight for this bound:
# at n=4, 4*16+7 = 71 > 64 = 4^3.)  `>=` is written as the `<=` the atom
# lexicon has, arguments swapped -- a notational, not a semantic, choice.
READINGS['86_04_proofs_with_structure_ii_problem_007'] = {
    "theorem": "cube_dominates_eventually",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"integers \(n\)", "Int"),
        _q("q", ["n"], r"for all sufficiently large integers \(n\)"),
        _hyp("h1", op("<=", lit(5), r("n")), r"sufficiently large"),
        _con(op("<=", op("+", op("*", lit(4), op("^", r("n"), lit(2))), lit(7)),
                      op("^", r("n"), lit(3))),
             r"\(n ^ 3 ≥ 4n ^ 2 + 7\)"),
    ]}

# 87  <- ch4 problem-021: "there exists a UNIQUE integer r such that 0<=r<5 and
# 14 = r mod 5".  The first EXISTS-UNIQUE source in the corpus.  Both halves are
# discharged in-fragment, and BOTH are stated -- a uniqueness half alone would
# be the distortion (it holds vacuously if nothing satisfies the condition):
#   * EXISTENCE: the witness r := 4 supplied as a term, leaving the GROUND
#     conjunction 0<=4 and 4<5 and 14 mod 5 = 4 mod 5;
#   * UNIQUENESS: the universally-quantified `implies` -- any r meeting the
#     same condition equals 4.
# `14 = r (mod 5)` is read with the grammar's `mod` term word as the equality of
# residues mod 5 (the reading wp_auth_readings.py already uses), NOT as a new
# congruence primitive.
READINGS['87_04_proofs_with_structure_ii_problem_021'] = {
    "theorem": "unique_residue_14_mod5",
    "statements": [
        _amb("Int"),
        _objc("r", "Int"),
        _q("q", ["r"], r"a unique integer \(r\)"),
        _con(op("and",
                op("and",
                   op("and", op("<=", lit(0), lit(4)), op("<", lit(4), lit(5))),
                   op("=", op("mod", lit(14), lit(5)), op("mod", lit(4), lit(5)))),
                op("implies",
                   op("and",
                      op("and", op("<=", lit(0), r("r")), op("<", r("r"), lit(5))),
                      op("=", op("mod", lit(14), lit(5)), op("mod", r("r"), lit(5)))),
                   op("=", r("r"), lit(4)))),
             r"there exists a unique integer \(r\) , such that \(0\le r < 5\) and \(14\equiv r\mod 5\)"),
    ]}

# 88  <- ch4 problem-023: "if n^2+n+1 = 1 (mod 3) then n = 0 (mod 3) or
# n = 2 (mod 3)".  A case-split conclusion: the source's own `or`, in fragment.
# Each congruence is residue equality mod 3 (the `mod` term word again).  The
# binder is a formalization choice -- the source names no "let n be ..." phrase,
# so the object referent carries an empty quote rather than a fabricated one.
READINGS['88_04_proofs_with_structure_ii_problem_023'] = {
    "theorem": "quad_cong_cases",
    "statements": [
        _amb("Int"),
        _objc("n", "Int"),
        _q("q", ["n"], r"\(n^2+n+1\equiv 1\mod 3\)"),
        _hyp("h1", op("=", op("mod",
                              op("+", op("+", op("^", r("n"), lit(2)), r("n")), lit(1)),
                              lit(3)),
                           op("mod", lit(1), lit(3))),
             r"\(n^2+n+1\equiv 1\mod 3\)"),
        _con(op("or",
                op("=", op("mod", r("n"), lit(3)), op("mod", lit(0), lit(3))),
                op("=", op("mod", r("n"), lit(3)), op("mod", lit(2), lit(3)))),
             r"\(n\equiv 0\mod 3\) or \(n\equiv 2\mod 3\)"),
    ]}

# 89  <- ch4 problem-025: "a, b, c positive naturals with a^2+b^2=c^2; show
# 3 <= a".  A genuinely NONLINEAR Nat theorem (no witness, no case split): the
# smallest leg of a Pythagorean triple is at least 3, because a=1 forces
# (c-b)(c+b)=1 and a=2 forces (c-b)(c+b)=4 with c-b and c+b of equal parity,
# neither of which admits a positive b.  "positive" is read as 1 <= x on the Nat
# carrier (the carrier's own lower bound would make it vacuous prose).
READINGS['89_04_proofs_with_structure_ii_problem_025'] = {
    "theorem": "pythag_leg_ge3",
    "statements": [
        _amb("Nat"),
        _obj("oa", "a", r"\(a\)", "Nat"),
        _obj("ob", "b", r"\(b\)", "Nat"),
        _obj("oc", "c", r"\(c\)", "Nat"),
        _q("q", ["a", "b", "c"], r"be positive natural numbers"),
        _hyp("h1", op("and",
                      op("and", op("<=", lit(1), r("a")), op("<=", lit(1), r("b"))),
                      op("<=", lit(1), r("c"))),
             r"positive natural numbers"),
        _hyp("h2", op("=", op("+", op("^", r("a"), lit(2)), op("^", r("b"), lit(2))),
                           op("^", r("c"), lit(2))),
             r"\(a^2+b^2=c^2\)"),
        _con(op("<=", lit(3), r("a")), r"\(3 \le a\)"),
    ]}

# 90  <- ch4 problem-029: "there does NOT exist a natural number n such that
# n^2=2".  A negated existential -- and the one negation shape the fragment can
# state WITHOUT a `not` connective (which it does not have): the De Morgan dual
# is a universal whose body is the built-in DISEQUALITY atom, so the reading is
# `for all n : Nat, n^2 != 2`.  Faithful, not a distortion: the two are the same
# proposition, and no primitive is smuggled in.
READINGS['90_04_proofs_with_structure_ii_problem_029'] = {
    "theorem": "no_nat_sqrt_two",
    "statements": [
        _amb("Nat"),
        _obj("on", "n", r"a natural number \(n\)", "Nat"),
        _q("q", ["n"], r"a natural number \(n\)"),
        _con(op("!=", op("^", r("n"), lit(2)), lit(2)), r"\(n^2=2\)"),
    ]}
