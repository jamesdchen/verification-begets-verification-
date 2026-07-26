#!/usr/bin/env python3
"""The measured-refusal ledger (the frontier-demotion fix, cycle-05 lesson).

The census orders ``ready`` by SIGNALS; certification MEASURES.  Before this
ledger existed, a measured refusal evaporated into the driver session's
summary: the same refused candidates permanently occupied the head of the
intake window (cycle 05 wedged on exactly that -- 8 measured refusals at
positions 84-91, transcribable candidates stuck behind the cap).  House law
says refusals are FIRST-CLASS demand data, so they get a committed,
append-only home:

    results/frontier_refusals.jsonl   -- one canonical JSON row per
    (subject text sha256, named refusal signal): {"measured_by", "signal",
    "subject_sha256"}.  No wall-clock in rows; provenance (a cycle receipt
    ref, or the honest pre-ledger note) carries the era.  A multi-signal
    refusal appears as one row PER signal, mirroring the census convention.

``tools/frontier.py`` consumes the ledger: refused subjects leave ``ready``
and join ``blocked`` under ``refused:<signal>`` groups -- so measured
refusals become purchase-naming demand exactly like census miss signals,
and the intake window can never wedge on them again.

Named signal vocabulary (grow by appending, never rename -- rows are
evidence): symbolic-exponent, function-symbol, mod-operator, nonvacuity,
cmp-outside-lexicon, exists-only-shape, definition-biconditional,
iff-connective, not-connective, predicate-variable, hypothesis-quantifier,
div-operator, set-membership.

The last four are cycle-09 appends, each naming a DISTINCT missing
primitive measured on the ch4 Proofs-with-Structure-II block:
  * iff-connective       -- the faithful form is a biconditional, and
    `_CONNECTIVES` is exactly {and, or, implies}.  Sibling of
    definition-biconditional, which stays reserved for DEFINITIONS
    (whose content IS the biconditional); this one names a lemma or
    problem that merely STATES one.  Same purchase, different subject
    kind -- kept apart so the rows never claim a definition where the
    source has a theorem.
  * not-connective       -- the faithful form negates an atom; the
    fragment has no propositional negation.
  * predicate-variable   -- the source quantifies over a PROPERTY (a
    second-order binder); objects are carrier-typed values only.
  * hypothesis-quantifier -- the faithful hypothesis carries its OWN
    binder (`... is a factor of EVERY natural number m`); the fragment's
    binders are top-level, so flattening moves the binder out of the
    hypothesis and states a different (and false) theorem.  NOTE the
    boundary measured in cycle 12: an exists-binder in the hypothesis is
    NOT automatically this signal.  `(exists q. P(q)) -> Q` is logically
    `forall q. (P(q) -> Q)` whenever Q does not mention q, so flattening
    is then an EQUIVALENCE, not a distortion, and the subject ships
    (source 112).  This signal is for the case where the conclusion DOES
    depend on the bound variable, where flattening genuinely changes the
    theorem -- which is why cycle 09's row carries a refuting witness.

The cycle-12 append:
  * defined-predicate    -- the source states its subject through a
    predicate NAME the corpus DEFINES elsewhere (`k is superpowered`,
    05_Logic#definition-001), and the fragment has no definitional-
    extension mechanism, so the name is simply an unknown atom
    (measured: `unknown atom/connective 'superpowered'`).  Distinct from
    definition-biconditional, which is the DEFINITION itself; this names
    a subject that merely USES one -- the same split that keeps
    iff-connective apart from definition-biconditional.  Unfolding the
    definition does not rescue it, it RELOCATES the demand onto whatever
    the definition's body needs (here `prime`, already named on the
    census axis as the `primality` miss signal).

The cycle-14 append:
  * metatheoretic-subject -- the source's subject is not a proposition
    about carrier VALUES at all: it asserts a property OF A DEFINITION.
    Measured once, on 06_Induction#proposition-001 ("The recursive
    definition gcd is well-founded"), where the gate answers `unknown
    atom/connective 'well_founded'`.  Deliberately kept apart from
    defined-predicate despite the identical-looking gate response: that
    signal names a subject that USES a predicate the corpus defines
    elsewhere, and unfolding the definition RELOCATES its demand onto
    ordinary vocabulary.  Here there is nothing to unfold and no amount
    of arithmetic vocabulary would help -- `well-founded` is not defined
    anywhere in the corpus, and its argument is the recursive definition
    06_Induction#definition-001 rather than any integer.  So this signal
    names a demand NO operator-word or carrier purchase can ever meet,
    which is exactly why it must not be filed under one that can.  Named
    narrowly on the strength of ONE measurement; if a later cycle finds
    the class has internal structure, that is an append, not a rename.

The cycle-15 append:
  * div-operator         -- the source needs INTEGER DIVISION (the
    quotient), and the fragment has the remainder but not the quotient.
    Measured once, on 06_Induction#theorem-006
    (`mod(n,d) + d * div(n,d) = n`), where the gate answers `unknown
    term operator 'div'`.  Filed apart from function-symbol, whose rows
    name subjects that need an arbitrary NAMED function the corpus has
    no word for (`factorial`, the sequences `a_n`/`d_n`/`F_n`, the
    Bezout coefficients `L`/`R`), each of which needs its own definition
    mechanism.  `div` is instead ONE standard arithmetic operator word
    -- exactly the shape `mod` had when it was the named refusal
    `mod-operator` and a single purchase retired it -- so this signal
    names a demand ONE purchase meets, and the sibling precedent is what
    it is named after.  Probed past its blocker: with the quotient
    replaced by a plain object variable the reading passes the gate, so
    `div` is the ONLY missing kind here and the subject earns exactly
    one row.

The cycle-16 append:
  * set-membership       -- the subject needs the `in` ATOM over a SET
    OBJECT, and the fragment has no set objects: P2 bought `setbuild`
    only as `card`'s argument (a bounded, filtered literal interval), so
    a set can be COUNTED but never inhabited, named, or compared.
    Measured twice on the 09_Sets window, each time as the SECOND row of
    a subject whose first blocker was a connective -- 09_Sets#
    definition-003 (`unknown atom/connective 'mem'` once the
    biconditional is probed past) and 09_Sets#problem-017 (the same,
    once the negation is).  Kept apart from the connective signals
    because it names a DIFFERENT purchase: `iff`/`not` are propositional
    primitives, while this one needs a set carrier and its membership
    atom.  Note the boundary this signal does NOT cover, measured the
    same cycle: membership in a COMPREHENSION at a literal element
    (09_Sets#problem-001, `1 in {n : Z | n <= 3}`) unfolds definitionally
    to its own body, leaves nothing unexpressed, and SHIPS as source 121
    -- so the signal is for set objects that survive unfolding, not for
    every appearance of the membership sign.

The cycle-23 append -- the FIRST batch drawn from an ANALYTIC corpus
(prime_number_theorem_and), and the first whose whole take refused.  All
five are gate-MEASURED on real subjects, each quoted verbatim in
results/c3_cycle_23.md; none is inferred from the prose.  They are filed
APART rather than crammed into one "analysis" signal for the reason the
cycle-16 append gives: a signal is a promise about which purchase returns
the subject, so one signal covering a carrier, a limit and an integral
would promise that a single purchase retires all three.
  * complex-carrier      -- the reading gate answers `amb: ambient carrier
    'Complex' is outside ('Nat', 'Int', 'Rat') (+ the parametric
    `ZMod <n>`)`, missing_kind_guess `carrier:Complex`.  Measured on five
    subjects (B-affine-periodic, BlaschkeNonZero, TaxicabIntegral, and
    both halves of ch2-lemma-5-1).  Every carrier the fragment owns is a
    decidable arithmetic domain with an enumerable instance box; ℂ has
    neither a decidable order nor a box, so this is not the shape p3/p4
    bought.
  * real-carrier         -- the same gate answer one carrier over
    (`carrier:Real`), measured on buthe2-buthe-chi-star-icc, whose weight
    is defined on a real interval.  Kept apart from complex-carrier
    because `parked-real-analysis` is a REAL row about exactly this
    demand and ℂ is strictly past it.
  * limit-operator       -- `unknown term operator 'lim'`, measured at an
    ADMISSIBLE carrier on both halves of ch2-lemma-5-1 so the ℂ refusal
    could not mask it.  Filing only complex-carrier would have returned
    these subjects to ready on a carrier purchase and re-wedged them on
    the limit -- the cycle-05 lesson, applied before it could happen.
  * integral-operator    -- `unknown term operator 'integral'`, measured
    the same way on TaxicabIntegral.  Apart from limit-operator: a
    contour integral is not a limit of a sequence, and no one purchase
    is promised both.
  * set-symbolic-bound   -- the ONE signal here the gate names in its own
    vocabulary: `setbuild: hi bound must be a LITERAL -- bounded, exactly
    enumerable sets are what make cardinality decidable (eval counts, SMT
    unrolls the indicator sum); a symbolic bound is not in the fragment`,
    missing_kind_guess `set:symbolic-bound`.  Measured on Q-def
    (`Q(x)` = the count of squarefree integers ≤ x) with the squarefree
    filter replaced by `even`, so the bound is the only thing left
    refusing.  This is the demand results/p2_delta.md named in prose when
    P2's re-census came back zero; it now has a subject behind it.

Usage:
    python3 tools/frontier_refusals.py --record SHA256 SIGNAL --by RECEIPT
    python3 tools/frontier_refusals.py --list
Recording is idempotent per (sha, signal); after recording, regenerate the
frontier (the regen chain) and COMMIT both -- a refusal-only cycle is a real
cycle whose product is demand data.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

LEDGER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "results", "frontier_refusals.jsonl")

SIGNALS = ("symbolic-exponent", "function-symbol", "mod-operator",
           "nonvacuity", "cmp-outside-lexicon", "exists-only-shape",
           "definition-biconditional",
           "iff-connective", "not-connective", "predicate-variable",
           "hypothesis-quantifier", "defined-predicate",
           "metatheoretic-subject", "div-operator", "set-membership",
           "complex-carrier", "real-carrier", "limit-operator",
           "integral-operator", "set-symbolic-bound")


def load_rows(path: str = LEDGER) -> list:
    if not os.path.exists(path):
        return []
    rows = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def refused_by_subject(path: str = LEDGER) -> dict:
    """subject_sha256 -> sorted list of refusal signals."""
    out: dict = {}
    for row in load_rows(path):
        out.setdefault(row["subject_sha256"], set()).add(row["signal"])
    return {k: sorted(v) for k, v in out.items()}


def record(sha: str, signal: str, measured_by: str,
           path: str = LEDGER) -> bool:
    """Append one row; idempotent per (sha, signal). Returns True if written."""
    if signal not in SIGNALS:
        raise SystemExit(f"unknown refusal signal {signal!r} "
                         f"(vocabulary: {', '.join(SIGNALS)})")
    if len(sha) != 64:
        raise SystemExit("subject_sha256 must be the 64-hex text hash")
    for row in load_rows(path):
        if row["subject_sha256"] == sha and row["signal"] == signal:
            return False
    row = {"measured_by": measured_by, "signal": signal,
           "subject_sha256": sha}
    with open(path, "a") as fh:
        fh.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--record", nargs=2, metavar=("SHA256", "SIGNAL"))
    ap.add_argument("--by", default=None,
                    help="provenance: cycle receipt ref (required with --record)")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)
    if args.record:
        if not args.by:
            raise SystemExit("--record requires --by RECEIPT (provenance is "
                             "mandatory: rows are evidence)")
        wrote = record(args.record[0], args.record[1], args.by)
        print(("recorded" if wrote else "already recorded (idempotent)")
              + f": {args.record[1]} {args.record[0][:12]}…")
        return 0
    if args.list:
        for sha, signals in sorted(refused_by_subject().items()):
            print(f"{sha}  {','.join(signals)}")
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
