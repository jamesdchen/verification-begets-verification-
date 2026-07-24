"""C9 (PLAN_FRAGMENT §3.1 cadence): session-inline MathReadings for the
census-sourced corpus additions below -- SKELETON emitted by
tools/intake_from_frontier.py.  Sibling of wp_c2/c3/c4_readings.py;
same discipline, next batch.

PROVENANCE.  Each source's text is the VERBATIM prose of a census
attempt-candidate node (NOT a sentence a maintainer authored):

    91_03_parity_and_divisibility_problem_001 <- math2001 03_Parity_and_Divisibility#problem-001
    92_03_parity_and_divisibility_problem_002 <- math2001 03_Parity_and_Divisibility#problem-002
    93_03_parity_and_divisibility_problem_003 <- math2001 03_Parity_and_Divisibility#problem-003
    94_03_parity_and_divisibility_problem_004 <- math2001 03_Parity_and_Divisibility#problem-004
    95_03_parity_and_divisibility_problem_005 <- math2001 03_Parity_and_Divisibility#problem-005
    96_03_parity_and_divisibility_problem_006 <- math2001 03_Parity_and_Divisibility#problem-006
    97_03_parity_and_divisibility_problem_007 <- math2001 03_Parity_and_Divisibility#problem-007
    98_03_parity_and_divisibility_problem_008 <- math2001 03_Parity_and_Divisibility#problem-008

The READINGS themselves are LEFT UNAUTHORED on purpose: intake is
mechanical and makes NO certification claim.  The driver session
authors one reading per source here (UNMETERED; reused identically
by both arms), gate-checks it, box-verifies TRUE, and certifies via
the inline-author checkpoint resume.  A source that then fails to
certify is recorded as a first-class REFUSAL, never dropped.
"""


PROVENANCE = {
    '91_03_parity_and_divisibility_problem_001': {
        "corpus": 'math2001',
        "node_id": '03_Parity_and_Divisibility#problem-001',
        "text_sha256": '3446c6ca9e67938eff25a915278a5b453ffee9e1668b4ca045e2137f6e5ec088',
    },
    '92_03_parity_and_divisibility_problem_002': {
        "corpus": 'math2001',
        "node_id": '03_Parity_and_Divisibility#problem-002',
        "text_sha256": 'dcb19698a87d160d51dfa35dba85cf7a3eea673a89b594b498a19d8f4c8a7eca',
    },
    '93_03_parity_and_divisibility_problem_003': {
        "corpus": 'math2001',
        "node_id": '03_Parity_and_Divisibility#problem-003',
        "text_sha256": 'aecdda2a45891f4229f1e00cfc71a081f0bc18b9167422b7e8e1531b19ccee3f',
    },
    '94_03_parity_and_divisibility_problem_004': {
        "corpus": 'math2001',
        "node_id": '03_Parity_and_Divisibility#problem-004',
        "text_sha256": '302ba3b3ed787bea5e672bee1f01b3e51d4c20a500aa1df7c86ac8c5548e5a57',
    },
    '95_03_parity_and_divisibility_problem_005': {
        "corpus": 'math2001',
        "node_id": '03_Parity_and_Divisibility#problem-005',
        "text_sha256": '42c61654804e0d3dc123a740fce5d1f5acb6a0988988c1382ac6ca546de11ed1',
    },
    '96_03_parity_and_divisibility_problem_006': {
        "corpus": 'math2001',
        "node_id": '03_Parity_and_Divisibility#problem-006',
        "text_sha256": 'e0d2fd82c569686a561b324ca0c68e6ab85c8d3eb1bb6538e8d7244824b8fd5d',
    },
    '97_03_parity_and_divisibility_problem_007': {
        "corpus": 'math2001',
        "node_id": '03_Parity_and_Divisibility#problem-007',
        "text_sha256": 'bfb38114bb469a81f76c4c2f7654cd3f7091848da5fc5024eb567295f48abbb2',
    },
    '98_03_parity_and_divisibility_problem_008': {
        "corpus": 'math2001',
        "node_id": '03_Parity_and_Divisibility#problem-008',
        "text_sha256": '510bc6c22fbc125e1b6471275e739ffb592449dcf6c28e0897282e42d687a546',
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
# THE PARITY BLOCK, RELEASED BY DECISION.  These eight are the head of the
# ch3 Parity-and-Divisibility block that cycle 06 parked, cycle 07 measured
# (all 19 certify), cycle 08 moved from prose into the park ledger, and the
# maintainer's MERGE of the `C3 decision: evenodd-coverage-decision` PR (#50)
# RELEASED -- merge-is-the-sign-off, and the decision's own clause says the
# subjects "return to ready and the next cycle ships them through the normal
# flywheel".  This is that cycle.
#
# Every reading was box-verified by run.formalize.certify_statement BEFORE it
# was written here.  The block is why the arity-1 even/odd op-slot was held
# closed, so it is the FIRST batch in the corpus whose demand lands squarely
# in that slot -- the whole point of the decision.  Vocabulary is otherwise
# frozen: builtin term ops (+ - * ^ at a literal exponent), the connectives
# via the hypothesis list, and the two already-admitted operator words `odd`
# and `even`.  No new operator word, macro, carrier, or trust root.

# 91 <- ch3 problem-001: "Show that 7 is odd."  A GROUND parity atom, no
# binder at all -- the smallest possible statement of the released block.
READINGS['91_03_parity_and_divisibility_problem_001'] = {
    "theorem": "seven_is_odd",
    "statements": [
        _amb("Int"),
        _con(op("odd", lit(7)), r"\(7\) is odd"),
    ]}

# 92 <- ch3 problem-002: "Show that -3 is odd."  The same shape at a NEGATIVE
# literal -- the Int carrier is doing real work here (over Nat the subject
# would not exist), so the pair 91/92 pins parity on both signs.
READINGS['92_03_parity_and_divisibility_problem_002'] = {
    "theorem": "neg_three_is_odd",
    "statements": [
        _amb("Int"),
        _con(op("odd", lit(-3)), r"\(-3\) is odd"),
    ]}

# 93 <- ch3 problem-003: "if n is an odd integer, then 3n+2 is odd."  The
# first PARITY-PRESERVING implication: odd hypothesis, odd conclusion, with
# an affine term between them.
READINGS['93_03_parity_and_divisibility_problem_003'] = {
    "theorem": "three_n_plus_two_odd",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"\(n\) is an odd integer", "Int"),
        _q("q", ["n"], r"\(n\) is an odd integer"),
        _hyp("h", op("odd", r("n")), r"\(n\) is an odd integer",
             force="presupposition"),
        _con(op("odd", op("+", op("*", lit(3), r("n")), lit(2))),
             r"\(3n+2\) is odd"),
    ]}

# 94 <- ch3 problem-004: "if n is odd, then 7n-4 is odd."  Sibling of 93 with
# SUBTRACTION -- on Int that is real subtraction (the D8 carrier rule), which
# is why the ambient choice is Int and not Nat.
READINGS['94_03_parity_and_divisibility_problem_004'] = {
    "theorem": "seven_n_minus_four_odd",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"Let \(n\) be an integer", "Int"),
        _q("q", ["n"], r"Let \(n\) be an integer"),
        _hyp("h", op("odd", r("n")), r"\(n\) is odd",
             force="presupposition"),
        _con(op("odd", op("-", op("*", lit(7), r("n")), lit(4))),
             r"\(7n-4\) is odd"),
    ]}

# 95 <- ch3 problem-005: "if x and y are odd, then x+y+1 is odd."  The first
# TWO-OBJECT parity hypothesis: one source span ("x and y are odd") carries
# BOTH hypotheses, so both quote it -- the quote is the span that licenses
# the claim, and a conjunctive span licensing two atoms is not a fabrication.
READINGS['95_03_parity_and_divisibility_problem_005'] = {
    "theorem": "odd_plus_odd_plus_one_odd",
    "statements": [
        _amb("Int"),
        _obj("ox", "x", r"the integers \(x\)", "Int"),
        _obj("oy", "y", r"\(y\)", "Int"),
        _q("q", ["x", "y"], r"the integers \(x\) and \(y\)"),
        _hyp("hx", op("odd", r("x")), r"\(x\) and \(y\) are odd",
             force="presupposition"),
        _hyp("hy", op("odd", r("y")), r"\(x\) and \(y\) are odd",
             force="presupposition"),
        _con(op("odd", op("+", op("+", r("x"), r("y")), lit(1))),
             r"\(x+y+1\) is odd"),
    ]}

# 96 <- ch3 problem-006: "if x and y are odd, then xy+2y is odd."  Sibling of
# 95 whose conclusion is NONLINEAR in the objects (the product x*y), so the
# SMT channel meets a QF_NIA obligation rather than an affine one.
READINGS['96_03_parity_and_divisibility_problem_006'] = {
    "theorem": "xy_plus_two_y_odd",
    "statements": [
        _amb("Int"),
        _obj("ox", "x", r"the integers \(x\)", "Int"),
        _obj("oy", "y", r"\(y\)", "Int"),
        _q("q", ["x", "y"], r"the integers \(x\) and \(y\)"),
        _hyp("hx", op("odd", r("x")), r"\(x\) and \(y\) are odd",
             force="presupposition"),
        _hyp("hy", op("odd", r("y")), r"\(x\) and \(y\) are odd",
             force="presupposition"),
        _con(op("odd", op("+", op("*", r("x"), r("y")),
                          op("*", lit(2), r("y")))),
             r"\(xy+2y\) is odd"),
    ]}

# 97 <- ch3 problem-007: "if m is odd, then 3m-5 is even."  The first
# parity-FLIPPING claim in the corpus: the hypothesis slot and the conclusion
# slot hold DIFFERENT op-slot words (odd -> even), which is exactly the
# coverage the closed slot could not previously express.
READINGS['97_03_parity_and_divisibility_problem_007'] = {
    "theorem": "three_m_minus_five_even",
    "statements": [
        _amb("Int"),
        _obj("om", "m", r"Let \(m\) be an integer", "Int"),
        _q("q", ["m"], r"Let \(m\) be an integer"),
        _hyp("h", op("odd", r("m")), r"\(m\) is odd",
             force="presupposition"),
        _con(op("even", op("-", op("*", lit(3), r("m")), lit(5))),
             r"\(3m-5\) is even"),
    ]}

# 98 <- ch3 problem-008: "n an even integer; n^2+2n-5 is odd."  The flip in
# the other direction (even -> odd) over a QUADRATIC term -- `^` at the
# literal exponent 2, so the D10 discipline holds and no symbolic exponent
# enters.
READINGS['98_03_parity_and_divisibility_problem_008'] = {
    "theorem": "even_quadratic_is_odd",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"Let \(n\) be an even integer", "Int"),
        _q("q", ["n"], r"Let \(n\) be an even integer"),
        _hyp("h", op("even", r("n")), r"Let \(n\) be an even integer",
             force="presupposition"),
        _con(op("odd", op("-", op("+", op("^", r("n"), lit(2)),
                                  op("*", lit(2), r("n"))), lit(5))),
             r"\(n ^ 2 + 2 n - 5\) is odd"),
    ]}
