#!/usr/bin/env python3
"""The governance-park ledger -- the sibling of the measured-refusal ledger.

``tools/frontier_refusals.py`` demotes subjects certification MEASURED as
refusals.  It cannot speak for the other way a subject leaves the intake
window: a source that certifies perfectly well but is held by an explicit
governance decision.  House law says *parked items stay parked in writing*,
and until this ledger existed "in writing" meant PROSE -- a sentence in a
cycle receipt that the frontier could not read.  Cycle 07 wedged on exactly
that: the ready head was 19 consecutive ch3 Parity-and-Divisibility problems
parked by cycle 06 pending an even/odd coverage decision; all 19 certify, so
the refusal ledger correctly refused to demote them, and every unattended
cycle re-previewed the same block and could not proceed in listed order.

    results/frontier_parks.jsonl -- one canonical JSON row per (subject text
    sha256, named park reason): {"parked_by", "reason", "subject_sha256"}.
    No wall-clock in rows; provenance carries the era, exactly as refusal
    rows do.

``tools/frontier.py`` consumes the ledger: parked subjects leave ``ready``
and join ``blocked`` under ``parked:<reason>`` groups.

A PARK IS NOT A REFUSAL, and the distinction is the point:

- a refusal is a MEASUREMENT (the reading did not certify) and names a
  PURCHASE that would unblock it -- demand data;
- a park is a DECISION (the reading certifies; a human hold says not yet)
  and names the DECISION that would lift it.  It asserts nothing about
  fidelity, and it is REVERSIBLE: when the decision lands, delete the rows
  and regenerate -- the subjects return to ``ready`` in listed order.

Recording a park NEVER makes the decision it is waiting on.  This ledger
only moves an already-written hold out of prose and into machinery, so the
intake window opens onto the next UNPARKED material instead of re-wedging.

Park reasons name what lifts them (grow by appending, never rename -- rows
are evidence):

    evenodd-coverage-decision
        Census-sourced parity material held pending an explicit maintainer
        decision on even/odd coverage: ship the ch3 parity problem block
        into the main corpus, or record it as a standing exclusion.
        LIFTED BY: that maintainer decision (either answer lifts it; an
        exclusion answer keeps the rows and records them as standing).

Usage:
    python3 tools/frontier_parks.py --record SHA256 REASON --by RECEIPT
    python3 tools/frontier_parks.py --lift SHA256 REASON
    python3 tools/frontier_parks.py --list
Recording is idempotent per (sha, reason); after recording or lifting,
regenerate the frontier (the regen chain) and COMMIT both.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

LEDGER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "results", "frontier_parks.jsonl")

#: reason -> the decision that lifts the park (the park's unblocking clause,
#: the analogue of a refusal signal naming its unblocking purchase).
REASONS = {
    "evenodd-coverage-decision":
        "an explicit maintainer decision on even/odd coverage: ship the ch3 "
        "parity problem block into the main corpus, or record it as a "
        "standing exclusion",
}


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


def parked_by_subject(path: str = LEDGER) -> dict:
    """subject_sha256 -> sorted list of park reasons."""
    out: dict = {}
    for row in load_rows(path):
        out.setdefault(row["subject_sha256"], set()).add(row["reason"])
    return {k: sorted(v) for k, v in out.items()}


def record(sha: str, reason: str, parked_by: str,
           path: str = LEDGER) -> bool:
    """Append one row; idempotent per (sha, reason). Returns True if written."""
    if reason not in REASONS:
        raise SystemExit(f"unknown park reason {reason!r} "
                         f"(vocabulary: {', '.join(sorted(REASONS))})")
    if len(sha) != 64:
        raise SystemExit("subject_sha256 must be the 64-hex text hash")
    for row in load_rows(path):
        if row["subject_sha256"] == sha and row["reason"] == reason:
            return False
    row = {"parked_by": parked_by, "reason": reason, "subject_sha256": sha}
    with open(path, "a") as fh:
        fh.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    return True


def lift(sha: str, reason: str, path: str = LEDGER) -> bool:
    """Remove one (sha, reason) row -- the decision landed.  Returns True if
    a row was removed.  Parks are reversible BY DESIGN; refusals are not."""
    rows = load_rows(path)
    kept = [r for r in rows
            if not (r["subject_sha256"] == sha and r["reason"] == reason)]
    if len(kept) == len(rows):
        return False
    with open(path, "w") as fh:
        for r in kept:
            fh.write(json.dumps(r, sort_keys=True,
                                separators=(",", ":")) + "\n")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--record", nargs=2, metavar=("SHA256", "REASON"))
    ap.add_argument("--lift", nargs=2, metavar=("SHA256", "REASON"))
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
    if args.lift:
        gone = lift(args.lift[0], args.lift[1])
        print(("lifted" if gone else "no such park row")
              + f": {args.lift[1]} {args.lift[0][:12]}…")
        return 0
    if args.list:
        for sha, reasons in sorted(parked_by_subject().items()):
            print(f"{sha}  {','.join(reasons)}")
        for reason, unblocks in sorted(REASONS.items()):
            print(f"\nparked:{reason}\n  LIFTED BY: {unblocks}")
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
