"""C16 (PLAN_FRAGMENT §3.1 cadence): session-inline MathReadings for the
census-sourced corpus additions below -- skeleton emitted by
tools/intake_from_frontier.py, then cut down by the driver session to the
sources that actually certified.  Sibling of wp_c2/c3/c4_readings.py; same
discipline, next batch.

PROVENANCE.  Each source's text is the VERBATIM prose of a census
attempt-candidate node (NOT a sentence a maintainer authored):

    123_proofs_with_structure_ii_lemma_003   <- math2001 04_Proofs_with_Structure_II#lemma-003
    124_proofs_with_structure_ii_lemma_004   <- math2001 04_Proofs_with_Structure_II#lemma-004
    125_sets_problem_002                     <- math2001 09_Sets#problem-002
    126_proofs_with_structure_ii_problem_011 <- math2001 04_Proofs_with_Structure_II#problem-011
    127_proofs_with_structure_ii_problem_012 <- math2001 04_Proofs_with_Structure_II#problem-012
    128_proofs_with_structure_ii_problem_013 <- math2001 04_Proofs_with_Structure_II#problem-013

THIS IS THE FIRST BATCH DRAWN FROM THE `refused:` BLOCKED GROUPS.  P6 retired
`not-connective`, `iff-connective` and `definition-biconditional`, so every
subject here had ALREADY passed selection in an earlier cycle and was demoted
by a MEASURED refusal against the pre-P6 fragment.  Those refusal rows STAND as
the reading they were; these are NEW measurements at the grown fragment, never
re-measurements staged to force a green.  Every reading below uses the words
the purchase bought -- which is the whole reason these subjects were re-selected.

TWO OF THE EIGHT SELECTED SUBJECTS ARE NOT HERE.  03_Parity_and_Divisibility
definition-001 and definition-002 (the definitions of `odd` and `even`) have no
faithful in-fragment reading even with `iff` in hand: their definiens is an
EXISTENTIAL that has to sit UNDER the biconditional, and the fragment's
quantifier is a prenex STATEMENT block.  Each was measured and recorded as a
first-class REFUSAL under `exists-only-shape` in results/frontier_refusals.jsonl,
never bent into a reading and never silently dropped; their laid-down source
files were removed (a refused subject is demand data, never a corpus source).
The measurement that EARNS the refusal is in results/c3_cycle_18.md: the prenex
form still CERTIFIES with the definiens corrupted to the vacuous `a = k`, i.e.
it does not carry the definition it claims to render.

The READINGS below were authored by the driver session (UNMETERED; reused
identically by both arms), gate-checked, and box-verified TRUE via
run.formalize.certify_statement BEFORE they were written -- together with the
FALSE-variant probes recorded in results/c3_cycle_18.md, which is where the
one green that is partly COVERAGE is written down.
"""


PROVENANCE = {
    '123_proofs_with_structure_ii_lemma_003': {
        "corpus": 'math2001',
        "node_id": '04_Proofs_with_Structure_II#lemma-003',
        "text_sha256": '3340194fba611d6e0531f9618c4f82a7df97a69d76f05cb875d359deff70e830',
    },
    '124_proofs_with_structure_ii_lemma_004': {
        "corpus": 'math2001',
        "node_id": '04_Proofs_with_Structure_II#lemma-004',
        "text_sha256": '5553682b4f48a5e53513b75b7e45bf7e780015abea31ec7a72c0324182fa0bf5',
    },
    '125_sets_problem_002': {
        "corpus": 'math2001',
        "node_id": '09_Sets#problem-002',
        "text_sha256": 'e75281156141d08885b226b86ca5afa34c4844f4e51555c71dfee98f9f96b79a',
    },
    '126_proofs_with_structure_ii_problem_011': {
        "corpus": 'math2001',
        "node_id": '04_Proofs_with_Structure_II#problem-011',
        "text_sha256": 'e721a43decec879cb8bb2322a5d43b21bb15a0d2bd907a15f72569dd428a401a',
    },
    '127_proofs_with_structure_ii_problem_012': {
        "corpus": 'math2001',
        "node_id": '04_Proofs_with_Structure_II#problem-012',
        "text_sha256": 'b90324f91b981266961871f07a15f6082ce1f48ea5c55a68d86d24e345385d75',
    },
    '128_proofs_with_structure_ii_problem_013': {
        "corpus": 'math2001',
        "node_id": '04_Proofs_with_Structure_II#problem-013',
        "text_sha256": '4346fe282c1fcc5ae52194f9ee0d4f3c6595c002fa7c3a6f4b275783afc9d8b8',
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

# 123  <- 04_Proofs_with_Structure_II lemma-003: an integer is EVEN if and only
# if it is NOT ODD.  The first source in the corpus whose reading needs BOTH of
# P6's words, and the cleanest witness the purchase could have asked for: before
# P6 the gate stopped at `unknown atom/connective 'not'` (cycle 16's probe
# table), and there was no weaker faithful reading to fall back on -- "even iff
# not odd" is ENTIRELY a claim about a negation and a biconditional.
#
# The `not` is written as a `not`, NOT hand-lowered to `even`.  P6's freeze IS
# negation-normal form: `_check_connective_nnf` pushes `not (odd n)` to the dual
# atom `even n` inside the gate, so the lowered form is what the mirror and the
# compiler see.  Doing that push HERE instead would erase the source's own shape
# and turn the reading into the tautology `even n <-> even n` -- a reading that
# says nothing about the word the source actually used.  The duality is exactly
# what the subject ASSERTS, so it belongs on the machine's side of the seam,
# where `_ATOM_DUALS` is witnessed by both solvers.
#
# TEETH (results/c3_cycle_18.md): dropping the negation (`even n <-> odd n`) is
# REFUTED at n = 0, and negating the left arm as well (`not even n <-> not odd
# n`, which lowers to `odd n <-> even n`) is REFUTED at n = 0.
READINGS['123_proofs_with_structure_ii_lemma_003'] = {
    "theorem": "int_even_iff_not_odd",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"an integer \(n\)", "Int"),
        _q("q", ["n"], r"an integer \(n\)"),
        _con(op("iff", op("even", r("n")), op("not", op("odd", r("n")))),
             "is even if and only if it is not odd"),
    ]}

# 124  <- 04_Proofs_with_Structure_II lemma-004: the converse pairing, an
# integer is ODD if and only if it is NOT EVEN.  Kept as its own source rather
# than folded into 123: the corpus states them as two lemmas, and `_ATOM_DUALS`
# carries `even -> odd` and `odd -> even` as two separate rows, so the pair
# exercises both directions of the table the purchase shipped.
#
# TEETH: dropping the negation is REFUTED at n = 0; negating the left arm as
# well is REFUTED at n = 0.
READINGS['124_proofs_with_structure_ii_lemma_004'] = {
    "theorem": "int_odd_iff_not_even",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"an integer \(n\)", "Int"),
        _q("q", ["n"], r"an integer \(n\)"),
        _con(op("iff", op("odd", r("n")), op("not", op("even", r("n")))),
             "is odd if and only if it is not even"),
    ]}

# 125  <- 09_Sets problem-002: 10 is NOT a member of the odd naturals.  The
# fragment still has no set objects, and this subject still does not need one:
# membership in a comprehension AT A LITERAL ELEMENT unfolds definitionally to
# the comprehension's own body at that element (Mathlib's Set.mem_setOf_eq) --
# the source-121 pattern from cycle 16, where `1 in {n : Int | n <= 3}` shipped
# as `1 <= 3`.  Nothing is relocated onto a corpus definition the fragment also
# lacks; what survives the unfolding is exactly `not (odd 10)`.
#
# This is the subject cycle 16 measured and refused under `not-connective`
# ALONE -- its probe past `not` reached a positive atom that is entirely in
# fragment, so that cycle recorded ONE row for it and no second.  P6 retired the
# one blocker it had, and the subject flipped.  It is the sharpest evidence in
# this batch that the refusal ledger prices demand accurately: the row said
# `not` was the whole bill, and it was.
#
# HONESTY -- this is NOT evidence that the fragment covers sets, for the same
# reason cycle 16 wrote down for source 121.  Every 09_Sets subject whose set
# SURVIVES unfolding (problems 005/014/015/017, definition-003) is still refused.
#
# A GROUND reading: no objects, no quantifier.  The instance box therefore holds
# exactly one instance -- the empty assignment -- and that is enough, because the
# statement is closed.  TEETH: dropping the negation (`odd 10`) is REFUTED, and
# moving the element to 11 (`not (odd 11)`) is REFUTED.
READINGS['125_sets_problem_002'] = {
    "theorem": "ten_is_not_odd",
    "statements": [
        _amb("Nat"),
        _con(op("not", op("odd", lit(10))),
             r"\(10\notin \{n:\mathbb{N} \mid n\text{ is odd}\}\)"),
    ]}

# 126  <- 04_Proofs_with_Structure_II problem-011: 5n is a multiple of 8 if and
# only if n is.  "is a multiple of 8" is `dvd(8, .)` -- the divisor is the FIRST
# argument -- and the elliptical "if and only if \(n\) is" is that same predicate
# at `n`, which is where the second arm comes from.
#
# HONESTY -- the box's teeth here are SHALLOW, and this is recorded rather than
# implied by the green.  The refutation sample is the five smallest instances
# (n in {0, -1, 1, -2, 2}), so a corrupted coefficient is separated only when its
# least witness falls inside that sample: 5 -> 4 is REFUTED at n = -2 and the
# modulus 8 -> 2 is REFUTED, but 5 -> 2, 5 -> 6 and 5 -> 10 all CERTIFY because
# their least witness is n = 4, and the moduli 8 -> 3/4/6/7/9/16 all CERTIFY for
# the same reason.  (5 -> 3, 5 -> 7 and 5 -> 9 are not false variants at all: any
# coefficient coprime to 8 makes the biconditional TRUE.)  This green is partly
# COVERAGE in the cycle-15/17 sense, and what it names is demand for a wider
# instance box -- never a reason to withhold a faithful reading.
READINGS['126_proofs_with_structure_ii_problem_011'] = {
    "theorem": "int_five_n_multiple_of_eight_iff_n_is",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"Let \(n\) be an integer", "Int"),
        _q("q", ["n"], r"Let \(n\) be an integer"),
        _con(op("iff",
                op("dvd", lit(8), op("*", lit(5), r("n"))),
                op("dvd", lit(8), r("n"))),
             r"\(5n\) is a multiple of \(8\) if and only if \(n\) is"),
    ]}

# 127  <- 04_Proofs_with_Structure_II problem-012: an integer is odd if and only
# if it is congruent to 1 modulo 2.  Congruence is rendered `dvd(2, n - 1)`, the
# SAME choice source 122 recorded last cycle and for the same reasons: `dvd` is
# total where SMT-LIB leaves `mod` by zero unspecified, and the two renderings
# are equivalent for every modulus (Int.modEq_iff_dvd).  Here it also keeps the
# reading inside the arity-3 congruence TEMPLATE `dvd(v0, v1 - v2)`
# (op_a7da9abc6817) that source 122's fourth use admitted -- so this pair is
# priced against a word the corpus already owns rather than staging a new one.
#
# TEETH: `odd` -> `even` REFUTED at n = 0; residue 1 -> 0 REFUTED at n = 0;
# modulus 2 -> 3 REFUTED at n = -1.  (`n - 1` -> `n + 1` CERTIFIES and is NOT a
# false variant: at modulus 2 the two differ by 2 and denote the same set.)
READINGS['127_proofs_with_structure_ii_problem_012'] = {
    "theorem": "int_odd_iff_congruent_one_mod_two",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"an integer \(n\)", "Int"),
        _q("q", ["n"], r"an integer \(n\)"),
        _con(op("iff",
                op("odd", r("n")),
                op("dvd", lit(2), op("-", r("n"), lit(1)))),
             "is odd, if and only if it is congruent to 1 modulo 2"),
    ]}

# 128  <- 04_Proofs_with_Structure_II problem-013: the even half of the same
# pair, congruent to 0 modulo 2.
#
# THE `- 0` IS DELIBERATE and is not noise.  "congruent to 0 modulo 2" is the
# corpus's OWN definition instantiated at 0 (03_Parity_and_Divisibility
# definition-005: a and b are congruent modulo n if n | (a - b)), so `2 | (n -
# 0)` is what the source SAYS; folding it to `dvd(2, n)` is an arithmetic step
# we would be taking on the source's behalf rather than a reading of it.  It
# also keeps 127 and 128 in the same congruence-template shape, so the miner
# sees the pair the corpus wrote instead of one template use and one bare `dvd`.
#
# TEETH: `even` -> `odd` REFUTED at n = 0; residue 0 -> 1 REFUTED at n = 0;
# modulus 2 -> 3 REFUTED at n = -2.
READINGS['128_proofs_with_structure_ii_problem_013'] = {
    "theorem": "int_even_iff_congruent_zero_mod_two",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"an integer \(n\)", "Int"),
        _q("q", ["n"], r"an integer \(n\)"),
        _con(op("iff",
                op("even", r("n")),
                op("dvd", lit(2), op("-", r("n"), lit(0)))),
             "is even, if and only if it is congruent to 0 modulo 2"),
    ]}
