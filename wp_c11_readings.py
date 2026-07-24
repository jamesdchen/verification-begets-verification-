"""C11 (PLAN_FRAGMENT §3.1 cadence): session-inline MathReadings for the
census-sourced corpus additions below -- SKELETON emitted by
tools/intake_from_frontier.py.  Sibling of wp_c2/c3/c4_readings.py;
same discipline, next batch.

PROVENANCE.  Each source's text is the VERBATIM prose of a census
attempt-candidate node (NOT a sentence a maintainer authored):

    106_03_parity_and_divisibility_problem_023 <- math2001 03_Parity_and_Divisibility#problem-023
    107_03_parity_and_divisibility_problem_024 <- math2001 03_Parity_and_Divisibility#problem-024
    108_03_parity_and_divisibility_problem_025 <- math2001 03_Parity_and_Divisibility#problem-025
    109_04_proofs_with_structure_ii_problem_016 <- math2001 04_Proofs_with_Structure_II#problem-016
    110_04_proofs_with_structure_ii_problem_030 <- math2001 04_Proofs_with_Structure_II#problem-030
    111_04_proofs_with_structure_ii_theorem_001 <- math2001 04_Proofs_with_Structure_II#theorem-001
    112_04_proofs_with_structure_ii_theorem_003 <- math2001 04_Proofs_with_Structure_II#theorem-003
    113_05_logic_problem_005     <- math2001 05_Logic#problem-005

The READINGS themselves are LEFT UNAUTHORED on purpose: intake is
mechanical and makes NO certification claim.  The driver session
authors one reading per source here (UNMETERED; reused identically
by both arms), gate-checks it, box-verifies TRUE, and certifies via
the inline-author checkpoint resume.  A source that then fails to
certify is recorded as a first-class REFUSAL, never dropped.
"""


PROVENANCE = {
    '106_03_parity_and_divisibility_problem_023': {
        "corpus": 'math2001',
        "node_id": '03_Parity_and_Divisibility#problem-023',
        "text_sha256": 'cd46743f02ac591ad4348dc0faa99afb7afb878bea5ca46b8e7fdfa77674a404',
    },
    '107_03_parity_and_divisibility_problem_024': {
        "corpus": 'math2001',
        "node_id": '03_Parity_and_Divisibility#problem-024',
        "text_sha256": '8fb6abe787bde86801f368051b1e58e7b6ec01b5bfc3d8b297bfe6d0c97f0043',
    },
    '108_03_parity_and_divisibility_problem_025': {
        "corpus": 'math2001',
        "node_id": '03_Parity_and_Divisibility#problem-025',
        "text_sha256": '88ec25c4f64aca645f01c8dd94ce701cebb21ef902e1daf40866531868939292',
    },
    '109_04_proofs_with_structure_ii_problem_016': {
        "corpus": 'math2001',
        "node_id": '04_Proofs_with_Structure_II#problem-016',
        "text_sha256": '217880cfeea0ea4a143ce3eff48155ce76589215c1a8572c13a113258719b9d1',
    },
    '110_04_proofs_with_structure_ii_problem_030': {
        "corpus": 'math2001',
        "node_id": '04_Proofs_with_Structure_II#problem-030',
        "text_sha256": '67f4fd2d7c4587146b8b5fb69f760999d40bf571661b94cb90e9e89ef824852f',
    },
    '111_04_proofs_with_structure_ii_theorem_001': {
        "corpus": 'math2001',
        "node_id": '04_Proofs_with_Structure_II#theorem-001',
        "text_sha256": 'eb0eee472acddb9d4810b4fc96f83a96d166da33ddbd7b2411a7e287eb75b686',
    },
    '112_04_proofs_with_structure_ii_theorem_003': {
        "corpus": 'math2001',
        "node_id": '04_Proofs_with_Structure_II#theorem-003',
        "text_sha256": '31d2d5cc111c76c5655bdffbc19dc3fafa84a7ae64828934a3532a4213dc2e48',
    },
    '113_05_logic_problem_005': {
        "corpus": 'math2001',
        "node_id": '05_Logic#problem-005',
        "text_sha256": '148c46a262cfce5e5aedbee382d9acc410147c773aa2b46075bd0026095b1805',
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
# The tail of the ch3 congruence block plus the first ch4 residue.  Every
# reading below was box-verified by run.formalize.certify_statement BEFORE it
# was written (never distort a reading to force a green), and every quote is a
# LITERAL substring of its source.  Vocabulary frozen: builtin term ops, the
# `and`/`or`/`implies` connectives, the admitted words even/odd, and the
# grammar's `mod` term word.  No new operator word, macro, carrier, or trust
# root.
#
# TWO of the eight selected subjects are NOT here: 112 and 113 have no
# faithful in-fragment reading at all, and are recorded as first-class
# REFUSALS in results/frontier_refusals.jsonl rather than bent into one.
# See the cycle receipt for what each one measures.

# 106  <- ch3 problem-023: two congruence hypotheses (a = 4, b = 3 mod 5)
# discharging a cubic congruence conclusion.  Same residue-equality reading as
# 103-105; the first source with TWO congruence hypotheses.
READINGS['106_03_parity_and_divisibility_problem_023'] = {
    "theorem": "cong_two_hyp_mod_five",
    "statements": [
        _amb("Int"),
        _obj("oa", "a", r"Let \(a\) and \(b\) be integers", "Int"),
        _obj("ob", "b", r"Let \(a\) and \(b\) be integers", "Int"),
        _q("q", ["a", "b"], r"Let \(a\) and \(b\) be integers"),
        _hyp("h1", op("=", op("mod", r("a"), lit(5)), op("mod", lit(4), lit(5))),
             r"\(a \equiv 4\mod 5\)"),
        _hyp("h2", op("=", op("mod", r("b"), lit(5)), op("mod", lit(3), lit(5))),
             r"\(b \equiv 3\mod 5\)"),
        _con(op("=",
                op("mod", op("+", op("+", op("*", r("a"), r("b")),
                                     op("^", r("b"), lit(3))), lit(3)), lit(5)),
                op("mod", lit(2), lit(5))),
             r"\(ab+b^3+3 \equiv 2\mod 5\)"),
    ]}

# 107  <- ch3 problem-024: "there EXISTS an integer a with 6a = 4 mod 11".  The
# sanctioned WITNESS-TERM form (the 84/85/86 precedent): the analyst discharges
# the existential constructively by SUPPLYING the witness a := 8 (6*8 = 48 =
# 44+4, so 48 = 4 mod 11) and demanding the resulting ground congruence.  No
# exists binder is smuggled in, and nothing is universalised.
READINGS['107_03_parity_and_divisibility_problem_024'] = {
    "theorem": "exists_sol_six_a_cong_four_mod_eleven",
    "statements": [
        _amb("Int"),
        _con(op("=", op("mod", op("*", lit(6), lit(8)), lit(11)),
                     op("mod", lit(4), lit(11))),
             r"\(6a \equiv 4\mod 11\)"),
    ]}

# 108  <- ch3 problem-025: Fermat's little theorem at p = 3, stated as a
# universal congruence over Int -- the batch's cubic.
READINGS['108_03_parity_and_divisibility_problem_025'] = {
    "theorem": "x_cubed_cong_x_mod_three",
    "statements": [
        _amb("Int"),
        _obj("ox", "x", r"Let \(x\) be an integer", "Int"),
        _q("q", ["x"], r"Let \(x\) be an integer"),
        _con(op("=", op("mod", op("^", r("x"), lit(3)), lit(3)),
                     op("mod", r("x"), lit(3))),
             r"\(x ^ 3 \equiv x\mod 3\)"),
    ]}

# 109  <- ch4 problem-016: "n^2 - 10n + 24 = 0 implies n is even".  THE source
# cycle 09 parked under the then-open evenodd-coverage-decision.  That decision
# was answered "ship it" by the maintainer's merge of #50, so it enters here as
# ordinary material -- the last subject the park was holding.
READINGS['109_04_proofs_with_structure_ii_problem_016'] = {
    "theorem": "quadratic_root_is_even",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"Let \(n\) be an integer", "Int"),
        _q("q", ["n"], r"Let \(n\) be an integer"),
        _hyp("h", op("=", op("+", op("-", op("^", r("n"), lit(2)),
                                     op("*", lit(10), r("n"))), lit(24)),
                     lit(0)),
             r"\(n ^ 2 - 10 n + 24 = 0\)"),
        _con(op("even", r("n")), r"Show that \(n\) is even"),
    ]}

# 110  <- ch4 problem-030: "n^2 NOT= 2 mod 3" -- a negated congruence.  Read
# like 102 and like source 90: state it with the FROZEN disequality atom rather
# than the `not` connective the fragment lacks.  `n^2 mod 3 != 2 mod 3` is the
# same proposition as the source's non-congruence, for every n.
READINGS['110_04_proofs_with_structure_ii_problem_030'] = {
    "theorem": "n_sq_not_cong_two_mod_three",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"Let \(n\) be an integer", "Int"),
        _q("q", ["n"], r"Let \(n\) be an integer"),
        _con(op("!=", op("mod", op("^", r("n"), lit(2)), lit(3)),
                       op("mod", lit(2), lit(3))),
             r"\(n^2\not\equiv 2 \mod 3\)"),
    ]}

# 111  <- ch4 theorem-001: "Every integer is either even or odd."  The corpus's
# first source whose whole content is a DISJUNCTION over the parity slot --
# `or` is one of the fragment's three connectives, so the excluded middle for
# parity is statable directly, with no case-split machinery.
READINGS['111_04_proofs_with_structure_ii_theorem_001'] = {
    "theorem": "every_int_even_or_odd",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"Every integer", "Int"),
        _q("q", ["n"], r"Every integer"),
        _con(op("or", op("even", r("n")), op("odd", r("n"))),
             r"Every integer is either even or odd"),
    ]}

# 112  <- ch4 theorem-003: "Let a and b be integers.  If there EXISTS an
# integer q such that bq < a < b(q+1), then a is not a multiple of b."
#
# Two shapes that have each been refused before appear here, and BOTH are
# measured rather than assumed:
#
#  (1) An exists binder in the HYPOTHESIS.  Cycle 09 refused exactly that
#      shape (`refused:hypothesis-quantifier`, ch4 problem-002) because
#      flattening the binder to the top level stated a DIFFERENT and false
#      theorem -- and recorded a refuting witness.  Here it does not:
#      `(exists q. P(q)) -> Q` is logically `forall q. (P(q) -> Q)` whenever
#      Q does not mention q, and this conclusion speaks only of a and b.  The
#      flattening is an EQUIVALENCE, so the reading is faithful, and the
#      refusal signal does not apply.  The distinction is the conclusion's
#      dependence on the binder, not the mere presence of `there exists`.
#
#  (2) A NEGATED divisibility, at a SYMBOLIC divisor -- the exact boundary
#      cycle 11 recorded when it shipped source 102 (`12 mod 5 != 0`) and
#      said the move relied on the divisor being a nonzero LITERAL.  It holds
#      here too, for a reason the source supplies: b = 0 makes the hypothesis
#      `0 < a < 0` unsatisfiable, so the implication is vacuously true at
#      b = 0 under BOTH the source's reading and this one.  They agree on
#      every model, so `a mod b != 0` is faithful here -- not an extension of
#      the cycle-11 move to symbolic divisors in general.
READINGS['112_04_proofs_with_structure_ii_theorem_003'] = {
    "theorem": "between_consecutive_multiples_not_multiple",
    "statements": [
        _amb("Int"),
        _obj("oa", "a", r"Let \(a\) and \(b\) be integers", "Int"),
        _obj("ob", "b", r"Let \(a\) and \(b\) be integers", "Int"),
        _obj("oq", "q", r"there exists an integer \(q\)", "Int"),
        _q("qq", ["a", "b", "q"], r"Let \(a\) and \(b\) be integers"),
        _hyp("h1", op("<", op("*", r("b"), r("q")), r("a")),
             r"\(bq<a<b(q + 1)\)"),
        _hyp("h2", op("<", r("a"), op("*", r("b"), op("+", r("q"), lit(1)))),
             r"\(bq<a<b(q + 1)\)"),
        _con(op("!=", op("mod", r("a"), r("b")), lit(0)),
             r"\(a\) is not a multiple of \(b\)"),
    ]}
