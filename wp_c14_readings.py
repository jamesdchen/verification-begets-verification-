"""C14 (PLAN_FRAGMENT §3.1 cadence): session-inline MathReadings for the
census-sourced corpus additions below -- skeleton emitted by
tools/intake_from_frontier.py, then cut down by the driver session to the
sources that actually certified.  Sibling of wp_c2/c3/c4_readings.py; same
discipline, next batch.

PROVENANCE.  Each source's text is the VERBATIM prose of a census
attempt-candidate node (NOT a sentence a maintainer authored):

    120_07_number_theory_theorem_003 <- math2001 07_Number_Theory#theorem-003
    121_09_sets_problem_001          <- math2001 09_Sets#problem-001

SIX OF THE EIGHT SELECTED SUBJECTS ARE NOT HERE.  09_Sets definition-003 and
problems 002/005/014/015/017 have no faithful in-fragment reading; each was
measured one at a time and recorded as a first-class REFUSAL in
results/frontier_refusals.jsonl (TEN rows across the six -- four of them
earned a second row from a probe that reached past the first blocker), never
bent into a reading and never silently dropped.  Their laid-down source files
were removed (a refused subject is demand data, never a corpus source) and the
two survivors were renumbered 120/121 so the corpus numbering stays tight.
See results/c3_cycle_16.md.

The READINGS below were authored by the driver session (UNMETERED; reused
identically by both arms), gate-checked, and box-verified TRUE via
run.formalize.certify_statement BEFORE they were written.
"""


PROVENANCE = {
    '120_07_number_theory_theorem_003': {
        "corpus": 'math2001',
        "node_id": '07_Number_Theory#theorem-003',
        "text_sha256": 'd25252589a9b237f853afefd0d945155f3d6d8f1c41aefa0e030a37476a9d5e5',
    },
    '121_09_sets_problem_001': {
        "corpus": 'math2001',
        "node_id": '09_Sets#problem-001',
        "text_sha256": '7e257757d358ff8eae49be356937911b6ad07e6aa27a1c9e22ab0c37e3cf03b2',
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

# 120  <- 07_Number_Theory theorem-003: no INTEGERS a,b with b != 0 and
# a^2 = 2b^2.  The Int sibling of cycle 15's source 119 (which is the Nat
# statement); the book states both, and the corpus now carries both.  Same
# non-existence-as-universal reading: `not exists` is `forall not`, the side
# condition carried as a HYPOTHESIS and the equation NEGATED in the conclusion
# with the builtin `!=` atom.  `^` appears only at the LITERAL exponent 2.
#
# HONESTY (inherited from 119 and re-measured here): this green is COVERAGE,
# not a refutation-backed verdict.  The instance box does not reach a
# counterexample of the nearest FALSE variant (a^2 != 4b^2, refuted at
# a=2,b=1), and the nonlinear conclusion leaves the SMT arm at nonvacuity-sat.
# Recorded in the receipt rather than left implicit.
READINGS['120_07_number_theory_theorem_003'] = {
    "theorem": "no_int_sqrt_two",
    "statements": [
        _amb("Int"),
        _obj("oa", "a", r"integers \(a\) and \(b\)", "Int"),
        _obj("ob", "b", r"integers \(a\) and \(b\)", "Int"),
        _q("q", ["a", "b"], r"integers \(a\) and \(b\)"),
        _hyp("h", op("!=", r("b"), lit(0)), r"with \(b\ne 0\)"),
        _con(op("!=", op("^", r("a"), lit(2)),
                      op("*", lit(2), op("^", r("b"), lit(2)))),
             r"for which \(a^2=2b^2\)"),
    ]}

# 121  <- 09_Sets problem-001: the integer 1 belongs to {n : Z | n <= 3}.
# THE SET BLOCK'S DEGENERATE CASE, and the only member of it that ships.
# Membership in a COMPREHENSION is definitionally its own body at the element:
# `1 in {n : Z | n <= 3}` IS `1 <= 3`, with nothing left unexpressed and no
# corpus definition to relocate onto (contrast defined-predicate, cycle 12).
# The unfolding is therefore an EQUIVALENCE, the same standard by which
# cycle 12 shipped source 112 after flattening an exists-in-hypothesis.
#
# What it is NOT: evidence that the fragment covers sets.  The reading is a
# GROUND atom (the source-85 taxicab precedent) and carries no set structure
# whatever -- the set vanishes precisely because this subject's comprehension
# body is decidable arithmetic at a literal element.  Every OTHER subject in
# the 09_Sets window refused on set vocabulary this cycle; see the receipt.
READINGS['121_09_sets_problem_001'] = {
    "theorem": "one_mem_le_three",
    "statements": [
        _amb("Int"),
        _con(op("<=", lit(1), lit(3)),
             r"the integer 1 belongs to the set of integers \(\{n:\mathbb{Z} \mid n\le 3\}\)"),
    ]}
