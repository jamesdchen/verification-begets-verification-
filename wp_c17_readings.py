"""C17 (PLAN_FRAGMENT §3.1 cadence): session-inline MathReadings for the
census-sourced corpus addition below -- skeleton emitted by
tools/intake_from_frontier.py, then cut down by the driver session to the
source that actually certified.  Sibling of wp_c2/c3/.../c16_readings.py; same
discipline, next batch.

PROVENANCE.  The source's text is the VERBATIM prose of a census
attempt-candidate node (NOT a sentence a maintainer authored):

    129_proofs_with_structure_ii_problem_015 <- math2001 04_Proofs_with_Structure_II#problem-015

THE SECOND BATCH DRAWN FROM THE `refused:` BLOCKED GROUPS, and the first drawn
with NO purchase in between.  P6 retired `not-connective`, `iff-connective` and
`definition-biconditional` and cycle 18 spent eight of the eighteen subjects
behind them; this cycle spends the SIX whose WHOLE refusal set those three
retirements met.  The selection rule is the frontier's own precedence, applied
by hand because `intake_from_frontier --unblocked` does not apply it: a subject
returns only when EVERY signal filed against it is met, so the six taken here
carry no other live signal, and the subjects still carrying one
(`09_Sets#problem-017` and `#definition-003` under `set-membership`,
`#problem-005` and `03_Parity_and_Divisibility#definition-001/002` under
`exists-only-shape`, `04_Proofs_with_Structure_II#definition-001` under
`predicate-variable`) were NOT taken -- re-measuring an unmet block is the
cycle-05 re-wedge, not a new reading.

ONE OF THE SIX CERTIFIES.  The other five were each measured and recorded as a
first-class REFUSAL in results/frontier_refusals.jsonl, never bent into a
reading and never silently dropped; their laid-down source files were removed
(a refused subject is demand data, never a corpus source).  What EARNS each
refusal is written down in results/c3_cycle_19.md -- including the corruption
probe for `exists-only-shape`, which is a sharper measurement than cycle 18
could take: the exists-aware bounded-shadow gate now genuinely RUNS on these
readings (backend `exists-finitized-enum`), and they still certify with the
definiens corrupted to `b = c`, a clause naming neither divisor nor product.
A gate that passes a definition whose definiens has been emptied is not
evidence for the definition; it is the measurement that the fragment's PRENEX
existential cannot sit where the definition needs it.

The READING below was authored by the driver session (UNMETERED; reused
identically by both arms), gate-checked, and box-verified TRUE via
run.formalize.certify_statement BEFORE it was written -- together with the
FALSE-variant probes recorded in results/c3_cycle_19.md, which is where this
green's SHALLOW teeth are written down rather than implied.
"""


PROVENANCE = {
    '129_proofs_with_structure_ii_problem_015': {
        "corpus": 'math2001',
        "node_id": '04_Proofs_with_Structure_II#problem-015',
        "text_sha256": '07d3e907211878584b47fd41f7a64d430ba01fa9fa7583cbf64c672a88c2ecc4',
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

# 129  <- 04_Proofs_with_Structure_II problem-015: a^2 - 5a + 5 <= -1 if and
# only if a is 2 or 3.  The first source in the corpus to put P6's `iff` around
# an ORDER atom rather than a parity or divisibility one, and the first to need
# `or` on an arm of a biconditional -- so it prices the connective purchase
# against the arithmetic the fragment already owned instead of re-buying parity.
#
# "\(a\) is 2 or 3" is read as `or(a = 2, a = 3)` -- the elliptical predicate is
# equality at each literal, which is what the sentence says and all it says.
# The quadratic is kept in the source's own written order, `(a^2 - 5a) + 5`,
# rather than folded: `^(a, 2)` is the admitted squaring template
# (op_34e1b706c47c, the C2 miner's own word), and the `- 5a` / `+ 5` split is
# the source's spelling, not an arithmetic step taken on its behalf.
#
# HONESTY -- THE TEETH HERE ARE SHALLOW, and this is recorded rather than
# implied by the green.  The instance box is the five smallest instances
# (a in {0, -1, 1, -2, 2}), and the true solution set is exactly {2, 3}, so 3
# lies OUTSIDE the sample: every corruption that only moves the RIGHT arm
# certifies for want of a witness, measured, not guessed -- dropping `a = 3`
# entirely (`... <-> a = 2`) CERTIFIES, and `a = 3` -> `a = 4` CERTIFIES.  What
# the box does separate is the LEFT arm, where a = 2 is inside the sample:
# tightening the bound -1 -> -2 is REFUTED at a = 2, and the coefficient
# 5 -> 4 is REFUTED at a = 2.  So this green is partly COVERAGE in the
# cycle-15/17/18 sense; what it names is demand for an instance box reaching
# past the five smallest, never a reason to withhold a faithful reading.
READINGS['129_proofs_with_structure_ii_problem_015'] = {
    "theorem": "int_quadratic_le_neg_one_iff_two_or_three",
    "statements": [
        _amb("Int"),
        _obj("oa", "a", r"Let \(a\) be an integer", "Int"),
        _q("q", ["a"], r"Let \(a\) be an integer"),
        _con(op("iff",
                op("<=",
                   op("+",
                      op("-", op("^", r("a"), lit(2)), op("*", lit(5), r("a"))),
                      lit(5)),
                   lit(-1)),
                op("or", op("=", r("a"), lit(2)), op("=", r("a"), lit(3)))),
             r"\(a^2-5a+5 \le -1\) , if and only if \(a\) is 2 or 3"),
    ]}
