"""C8 (PLAN_FRAGMENT §3.1 cadence): session-inline MathReadings for the
census-sourced corpus additions below -- SKELETON emitted by
tools/intake_from_frontier.py.  Sibling of wp_c2/c3/c4_readings.py;
same discipline, next batch.

PROVENANCE.  Each source's text is the VERBATIM prose of a census
attempt-candidate node (NOT a sentence a maintainer authored):

    86_04_proofs_with_structure_ii_problem_007 <- math2001 04_Proofs_with_Structure_II#problem-007
    87_04_proofs_with_structure_ii_problem_023 <- math2001 04_Proofs_with_Structure_II#problem-023
    88_04_proofs_with_structure_ii_problem_025 <- math2001 04_Proofs_with_Structure_II#problem-025
    89_04_proofs_with_structure_ii_problem_029 <- math2001 04_Proofs_with_Structure_II#problem-029
    90_04_proofs_with_structure_ii_problem_030 <- math2001 04_Proofs_with_Structure_II#problem-030

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
    '87_04_proofs_with_structure_ii_problem_023': {
        "corpus": 'math2001',
        "node_id": '04_Proofs_with_Structure_II#problem-023',
        "text_sha256": 'af56519629f41d69fb2e7a188d30e0a480ef418266163d4d980c53ff30cd633a',
    },
    '88_04_proofs_with_structure_ii_problem_025': {
        "corpus": 'math2001',
        "node_id": '04_Proofs_with_Structure_II#problem-025',
        "text_sha256": 'f73a5ae29e622331792b3779c23390992f04d5e7b048ae9c8c890c6c19c407ef',
    },
    '89_04_proofs_with_structure_ii_problem_029': {
        "corpus": 'math2001',
        "node_id": '04_Proofs_with_Structure_II#problem-029',
        "text_sha256": '374bb25c97241d6d96dc1907f7d828517f895943154f28bb97bb7c521aa74301',
    },
    '90_04_proofs_with_structure_ii_problem_030': {
        "corpus": 'math2001',
        "node_id": '04_Proofs_with_Structure_II#problem-030',
        "text_sha256": '67f4fd2d7c4587146b8b5fb69f760999d40bf571661b94cb90e9e89ef824852f',
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
# Every reading below was box-verified by run.formalize.certify_statement
# BEFORE it was written here (signals order the frontier; certification
# MEASURES -- never distort a reading to force a green).  The batch uses
# ONLY frozen vocabulary: builtin term ops (+ - * ^ at literal exponents),
# the builtin atoms (= != <= <), the connectives and/or/implies, and ONE
# already-admitted operator word, `mod`.  No operator word, macro, carrier,
# or trust root grows.  No reading has a parity or divisibility conclusion,
# so the arity-1 even/odd op-slot and the dvd macros are UNTOUCHED.
#
# The batch's theme is the ch4 "Proofs with Structure II" residue that is
# in-fragment ONCE READ FAITHFULLY -- three shapes that LOOK out of reach
# and are not:
#   (a) an EVENTUALLY-claim, discharged by supplying the threshold as a
#       term (86: the T6b witness-term pattern, as in sources 84-85);
#   (b) a NEGATED EXISTENTIAL, which is a universal INEQUALITY the frozen
#       != atom already states -- no negation connective needed (89, 90);
#   (c) MODULAR-residue claims, which the admitted `mod` term operator
#       states directly (87, 90).
# The window's other five entries measured as refusals and one as a park;
# see results/c3_cycle_09.md.

# 86 <- ch4 problem-007: "for all SUFFICIENTLY LARGE integers n, n^3 >= 4n^2+7".
# The eventually-quantifier is discharged the T6b way: the THRESHOLD is
# supplied as a term (N := 5), leaving a pure forall over the Int carrier.
# 5 is TIGHT and the certifier says so -- boundary_behavior reports n = 4
# failing the hypothesis, and n = 4 is exactly where the conclusion fails
# (64 < 71).  ">=" is written with the frozen <= atom, operands swapped.
READINGS['86_04_proofs_with_structure_ii_problem_007'] = {
    "theorem": "large_n_cube_dominates",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"integers \(n\)", "Int"),
        _q("q", ["n"], r"for all sufficiently large integers \(n\)"),
        _hyp("h", op("<=", lit(5), r("n")), "sufficiently large",
             force="presupposition"),
        _con(op("<=",
                op("+", op("*", lit(4), op("^", r("n"), lit(2))), lit(7)),
                op("^", r("n"), lit(3))),
             r"\(n ^ 3 ≥ 4n ^ 2 + 7\)"),
    ]}

# 87 <- ch4 problem-023: "if n^2+n+1 = 1 mod 3 then n = 0 mod 3 or n = 2 mod 3".
# Straight into the fragment: `mod` is an admitted term operator, `implies`
# and `or` are frozen connectives.  Int `mod` is Int.emod, so the residues are
# non-negative for negative n too (n = -1: 1 - 1 + 1 = 1 mod 3, and
# -1 emod 3 = 2 -- the second disjunct).
READINGS['87_04_proofs_with_structure_ii_problem_023'] = {
    "theorem": "quad_residue_mod_three",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"\(n^2+n+1\equiv 1\mod 3\)", "Int"),
        _q("q", ["n"], r"\(n^2+n+1\equiv 1\mod 3\)"),
        _hyp("h", op("=", op("mod",
                             op("+", op("+", op("^", r("n"), lit(2)),
                                        r("n")), lit(1)),
                             lit(3)), lit(1)),
             r"\(n^2+n+1\equiv 1\mod 3\)", force="presupposition"),
        _con(op("or", op("=", op("mod", r("n"), lit(3)), lit(0)),
                op("=", op("mod", r("n"), lit(3)), lit(2))),
             r"\(n\equiv 0\mod 3\) or \(n\equiv 2\mod 3\)"),
    ]}

# 88 <- ch4 problem-025: "a, b, c positive naturals with a^2+b^2=c^2.
# Show 3 <= a."  The FIRST three-object hypothesis batch in the corpus and
# the first Pythagorean-triple source.  Positivity is the text's own
# presupposition ("positive natural numbers"), carried as a conjunctive
# hypothesis -- it is what makes the claim non-vacuous AND true (a = 1 and
# a = 2 both force b = 0).
READINGS['88_04_proofs_with_structure_ii_problem_025'] = {
    "theorem": "pythagorean_leg_ge_three",
    "statements": [
        _amb("Nat"),
        _obj("oa", "a", r"Let \(a\)", "Nat"),
        _obj("ob", "b", r"\(b\)", "Nat"),
        _obj("oc", "c", r"\(c\)", "Nat"),
        _q("q", ["a", "b", "c"],
           r"Let \(a\) , \(b\) and \(c\) be positive natural numbers"),
        _hyp("hp", op("and", op("<", lit(0), r("a")),
                      op("and", op("<", lit(0), r("b")),
                         op("<", lit(0), r("c")))),
             "be positive natural numbers", force="presupposition"),
        _hyp("h", op("=", op("+", op("^", r("a"), lit(2)),
                             op("^", r("b"), lit(2))),
                     op("^", r("c"), lit(2))),
             r"satisfying \(a^2+b^2=c^2\)", force="presupposition"),
        _con(op("<=", lit(3), r("a")), r"Show that \(3 \le a\)"),
    ]}

# 89 <- ch4 problem-029: "there does NOT exist a natural n such that n^2=2".
# A negated existential is a UNIVERSAL INEQUALITY, which the frozen != atom
# states with no negation connective and no exists binder -- the same move
# that makes `not` unnecessary here and NOT available for sources 87/88 of
# the previous window (even <-> not odd), whose negation sits under a
# biconditional.  Its subject text is verbatim-identical to 05_Logic
# problem-009, so intaking it retires BOTH ready entries (intake keys on
# subject text, as refusals and parks do).
READINGS['89_04_proofs_with_structure_ii_problem_029'] = {
    "theorem": "no_natural_root_of_two",
    "statements": [
        _amb("Nat"),
        _obj("on", "n", r"a natural number \(n\)", "Nat"),
        _q("q", ["n"], r"a natural number \(n\)"),
        _con(op("!=", op("^", r("n"), lit(2)), lit(2)), r"\(n^2=2\)"),
    ]}

# 90 <- ch4 problem-030: "n^2 is NOT congruent to 2 mod 3".  Both shapes at
# once -- the negation is an inequality (89) and the congruence is `mod`
# (87) -- so the whole claim is one frozen atom over an admitted operator.
READINGS['90_04_proofs_with_structure_ii_problem_030'] = {
    "theorem": "square_never_two_mod_three",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"Let \(n\) be an integer", "Int"),
        _q("q", ["n"], r"Let \(n\) be an integer"),
        _con(op("!=", op("mod", op("^", r("n"), lit(2)), lit(3)), lit(2)),
             r"\(n^2\not\equiv 2 \mod 3\)"),
    ]}
