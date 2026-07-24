"""C10 (PLAN_FRAGMENT §3.1 cadence): session-inline MathReadings for the
census-sourced corpus additions below -- SKELETON emitted by
tools/intake_from_frontier.py.  Sibling of wp_c2/c3/c4_readings.py;
same discipline, next batch.

PROVENANCE.  Each source's text is the VERBATIM prose of a census
attempt-candidate node (NOT a sentence a maintainer authored):

    99_03_parity_and_divisibility_problem_009 <- math2001 03_Parity_and_Divisibility#problem-009
    100_03_parity_and_divisibility_problem_010 <- math2001 03_Parity_and_Divisibility#problem-010
    101_03_parity_and_divisibility_problem_011 <- math2001 03_Parity_and_Divisibility#problem-011
    102_03_parity_and_divisibility_problem_015 <- math2001 03_Parity_and_Divisibility#problem-015
    103_03_parity_and_divisibility_problem_018 <- math2001 03_Parity_and_Divisibility#problem-018
    104_03_parity_and_divisibility_problem_019 <- math2001 03_Parity_and_Divisibility#problem-019
    105_03_parity_and_divisibility_problem_021 <- math2001 03_Parity_and_Divisibility#problem-021

The READINGS themselves are LEFT UNAUTHORED on purpose: intake is
mechanical and makes NO certification claim.  The driver session
authors one reading per source here (UNMETERED; reused identically
by both arms), gate-checks it, box-verifies TRUE, and certifies via
the inline-author checkpoint resume.  A source that then fails to
certify is recorded as a first-class REFUSAL, never dropped.
"""


PROVENANCE = {
    '99_03_parity_and_divisibility_problem_009': {
        "corpus": 'math2001',
        "node_id": '03_Parity_and_Divisibility#problem-009',
        "text_sha256": '87883b0175ded2555fc28dbd4790fa6ba4757a628601df61edd126bf03f99874',
    },
    '100_03_parity_and_divisibility_problem_010': {
        "corpus": 'math2001',
        "node_id": '03_Parity_and_Divisibility#problem-010',
        "text_sha256": '2dc0d8a6feb161472a5b2be8d223a47cd6ffbe75247f52663d622e024c4849cd',
    },
    '101_03_parity_and_divisibility_problem_011': {
        "corpus": 'math2001',
        "node_id": '03_Parity_and_Divisibility#problem-011',
        "text_sha256": '187da4f0f684949412c1f68e0f996faf8f90c8ca25f775b4b0bef418b7bff497',
    },
    '102_03_parity_and_divisibility_problem_015': {
        "corpus": 'math2001',
        "node_id": '03_Parity_and_Divisibility#problem-015',
        "text_sha256": 'dd3ead1608001b34bb4a2a8d383303d7510fdf6eb7bebac1fee277ae0a4e4b8f',
    },
    '103_03_parity_and_divisibility_problem_018': {
        "corpus": 'math2001',
        "node_id": '03_Parity_and_Divisibility#problem-018',
        "text_sha256": '0c34adb93e20d87775c39b4601066ae65435c487171c772a26a67e0a8dbf4b2a',
    },
    '104_03_parity_and_divisibility_problem_019': {
        "corpus": 'math2001',
        "node_id": '03_Parity_and_Divisibility#problem-019',
        "text_sha256": '13c97738c500b89238ede8ae716e660367807e4fe58173869502697c8f60ab85',
    },
    '105_03_parity_and_divisibility_problem_021': {
        "corpus": 'math2001',
        "node_id": '03_Parity_and_Divisibility#problem-021',
        "text_sha256": 'a7ea762c6b26377a27777573061db78bad4eb5c728ceb72e6a740978da34b2af',
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
# The REST of the released ch3 Parity-and-Divisibility block (the head, 91-98,
# shipped in cycle 10 after the maintainer's merge of the decision PR #50).
# Where 91-98 were all parity, this batch is where the block turns to
# DIVISIBILITY and CONGRUENCE: the already-admitted `dvd` atom and the
# grammar's `mod` term word carry it.  Every reading was box-verified by
# run.formalize.certify_statement BEFORE it was written here.  Vocabulary is
# frozen: builtin term ops, the admitted words `even`/`odd`/`dvd`, and `mod`.
# No new operator word, macro, carrier, or trust root.
#
# `dvd(a, b)` is "a DIVIDES b" (divisor first -- generators/math_smt.py:357).

# 99  <- ch3 problem-009: "Let \(n\) be an integer.  Prove that
# \(n ^ 2 + n + 4\) is even."  Parity again, but with NO hypothesis: the
# binder phrase is the whole antecedent, and n^2+n is even for every n.
READINGS['99_03_parity_and_divisibility_problem_009'] = {
    "theorem": "n_sq_plus_n_plus_four_even",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"Let \(n\) be an integer", "Int"),
        _q("q", ["n"], r"Let \(n\) be an integer"),
        _con(op("even", op("+", op("+", op("^", r("n"), lit(2)), r("n")),
                           lit(4))),
             r"\(n ^ 2 + n + 4\) is even"),
    ]}

# 100  <- ch3 problem-010: "Show that the natural number 88 is divisible by
# 11."  The corpus's first GROUND divisibility atom -- divisor first, so this
# is dvd(11, 88).  The source says "natural number", so the carrier is Nat.
READINGS['100_03_parity_and_divisibility_problem_010'] = {
    "theorem": "eighty_eight_div_by_eleven",
    "statements": [
        _amb("Nat"),
        _con(op("dvd", lit(11), lit(88)),
             r"the natural number 88 is divisible by 11"),
    ]}

# 101  <- ch3 problem-011: "Show that the integer 6 is divisible by -2."  The
# same atom at a NEGATIVE divisor -- which is exactly why the source says
# "integer": the subject does not exist over Nat.
READINGS['101_03_parity_and_divisibility_problem_011'] = {
    "theorem": "six_div_by_neg_two",
    "statements": [
        _amb("Int"),
        _con(op("dvd", lit(-2), lit(6)),
             r"the integer 6 is divisible by -2"),
    ]}

# 102  <- ch3 problem-015: "Show that 12 is not divisible by 5."  A NEGATED
# divisibility, and the fragment has no `not` connective.  The same move
# source 90 made for the negated existential: state it with a FROZEN atom
# instead of a missing connective -- "5 does not divide 12" is exactly
# "12 mod 5 is not 0", built from the already-admitted `mod` term word and the
# builtin disequality.  Faithful, not a weakening: for a nonzero modulus the
# two are the same proposition, and no primitive is smuggled in.
READINGS['102_03_parity_and_divisibility_problem_015'] = {
    "theorem": "twelve_not_div_by_five",
    "statements": [
        _amb("Int"),
        _con(op("!=", op("mod", lit(12), lit(5)), lit(0)),
             r"12 is not divisible by 5"),
    ]}

# 103  <- ch3 problem-018: "Show that \(11\equiv 3 \mod 4\)."  A GROUND
# congruence, read as residue equality exactly as source 88 reads its
# congruences (mod-to-mod, never a new congruence primitive).
READINGS['103_03_parity_and_divisibility_problem_018'] = {
    "theorem": "eleven_cong_three_mod_four",
    "statements": [
        _amb("Int"),
        _con(op("=", op("mod", lit(11), lit(4)), op("mod", lit(3), lit(4))),
             r"\(11\equiv 3 \mod 4\)"),
    ]}

# 104  <- ch3 problem-019: "Show that \(-5\equiv 1 \mod 3\)."  The same
# ground shape at a NEGATIVE residue -- the pair 103/104 pins the congruence
# reading on both signs, as 91/92 did for parity.
READINGS['104_03_parity_and_divisibility_problem_019'] = {
    "theorem": "neg_five_cong_one_mod_three",
    "statements": [
        _amb("Int"),
        _con(op("=", op("mod", lit(-5), lit(3)), op("mod", lit(1), lit(3))),
             r"\(-5\equiv 1 \mod 3\)"),
    ]}

# 105  <- ch3 problem-021: "Let \(a\) and \(b\) be integers, and suppose
# that \(a\equiv 2 \mod 4\).  Show that
# \(a b ^ 2 + a ^ 2 b + 3 a \equiv 2 b ^ 2 + 2 ^ 2 \cdot b + 3 \cdot 2
# \mod 4\)."  The first HYPOTHETICAL congruence, and the batch's only
# genuinely nonlinear one (a*b^2 and a^2*b in the same term).  ch3
# problem-022's prose is VERBATIM-IDENTICAL to this one, so this single source
# retires both ready entries.
READINGS['105_03_parity_and_divisibility_problem_021'] = {
    "theorem": "cong_substitution_mod_four",
    "statements": [
        _amb("Int"),
        _obj("oa", "a", r"Let \(a\) and \(b\) be integers", "Int"),
        _obj("ob", "b", r"Let \(a\) and \(b\) be integers", "Int"),
        _q("q", ["a", "b"], r"Let \(a\) and \(b\) be integers"),
        _hyp("h", op("=", op("mod", r("a"), lit(4)), op("mod", lit(2), lit(4))),
             r"\(a\equiv 2 \mod 4\)"),
        _con(op("=",
                op("mod",
                   op("+", op("+", op("*", r("a"), op("^", r("b"), lit(2))),
                                   op("*", op("^", r("a"), lit(2)), r("b"))),
                        op("*", lit(3), r("a"))),
                   lit(4)),
                op("mod",
                   op("+", op("+", op("*", lit(2), op("^", r("b"), lit(2))),
                                   op("*", op("^", lit(2), lit(2)), r("b"))),
                        op("*", lit(3), lit(2))),
                   lit(4))),
             r"\(a b ^ 2 + a ^ 2 b + 3 a \equiv 2 b ^ 2 + 2 ^ 2 \cdot b + 3 \cdot 2 \mod 4\)"),
    ]}
