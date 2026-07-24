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
iff-connective, not-connective, predicate-variable, hypothesis-quantifier.

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
    hypothesis and states a different (and false) theorem.

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
           "hypothesis-quantifier")


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
