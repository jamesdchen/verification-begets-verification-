#!/usr/bin/env python3
"""The lessons ledger: a recorded lesson cites a tooth, or declares why not.

THE DEBT THIS STOPS (measured across 2026-07-22..26, the five-day
shakedown).  Every incident produced a lesson, and the cheapest encoding of
a lesson at write time was a sentence -- receipts grew "written down so the
next firing does not re-derive it" paragraphs, prompts grew clauses, and
each such sentence was a claim that stopped tracking its evidence the
moment the tree moved.  The recurring result: dead merge-event lore, a
selection rule skipped by the exact cycle it addressed, a fence firing on
self-declared titles.  Mechanization always lagged the prose by exactly one
failure.

THE RATCHET, placed where the debt is born: a lesson is a LEDGER ROW, not a
paragraph, and the row must carry exactly one of

  * ``tooth`` -- ``tests/<file>.py::<test_name>``, and the tool REFUSES a
    tooth that does not resolve (file must exist, test function must be
    defined in it).  A lesson may not cite vapor.
  * ``prose_only_reason`` -- the declared, non-empty reason this claim has
    no executable form (the dead-term-canary pattern: exemptions are
    declarations, never defaults).

Rows are append-only, canonical JSON, provenance-mandatory
(``recorded_by`` names the receipt / PR / session that learned it), and
clock-free -- provenance carries the era, exactly as in
``results/frontier_refusals.jsonl``.  Receipts then CITE rows instead of
restating them; the free-text lesson with no ledger row is the
mechanization debt this ledger exists to stop.

Usage:
    python3 tools/lessons.py --claim "..." --by "results/c3_cycle_NN.md" \\
        --tooth tests/test_x.py::test_y
    python3 tools/lessons.py --claim "..." --by "PR #NNN" \\
        --prose-only "why no executable form exists"

An exact-duplicate row (same claim + same tooth/reason) is refused: the
ledger records each lesson once, and a re-learning is a new claim with its
own provenance, never a silent double row.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(_ROOT, "results", "lessons.jsonl")

ROW_KEYS = ("claim", "prose_only_reason", "recorded_by", "tooth")
#: Optional, and append-only's answer to a lesson that stops being true: a
#: later row may name an earlier row's claim as SUPERSEDED.  The earlier row
#: is never edited or deleted -- it stands as the reading it was, exactly as
#: a refusal row stands as its pre-purchase reading -- but its dead tooth
#: stops being a lie the moment a successor says why.  (Measured within two
#: hours of this ledger landing: the chain-one-shot rows cited teeth that
#: the very next night's revert deleted, and the committed-rows tooth caught
#: it.)
OPTIONAL_KEYS = ("supersedes",)


def resolve_tooth(tooth: str, root: str = _ROOT) -> str | None:
    """None if the tooth resolves; else the reason it does not.

    A tooth is ``<relpath>.py::<test_name>``.  Resolution is EXECUTED, not
    trusted: the file must exist under the repo root and the named function
    must be a top-level ``def`` in it (AST, so a mention in a docstring can
    never satisfy this -- the matched-a-mention lesson, applied to the tool
    that records lessons)."""
    if "::" not in tooth:
        return "tooth must be <path>::<test_name>"
    path, name = tooth.split("::", 1)
    if not path.endswith(".py") or not name:
        return "tooth must be <path>.py::<test_name>"
    abspath = os.path.join(root, path)
    if not os.path.isfile(abspath):
        return f"no such file: {path}"
    try:
        tree = ast.parse(open(abspath, encoding="utf-8").read())
    except SyntaxError as e:
        return f"{path} does not parse: {e}"
    defs = {n.name for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    if name not in defs:
        return f"{path} defines no top-level function {name!r}"
    return None


def validate_row(row: dict, root: str = _ROOT) -> str | None:
    """None if the row is a valid lesson; else the refusal reason."""
    extra = set(row) - set(ROW_KEYS)
    if set(ROW_KEYS) - set(row) or extra - set(OPTIONAL_KEYS):
        return (f"row keys must be {sorted(ROW_KEYS)} "
                f"(optional: {sorted(OPTIONAL_KEYS)})")
    if "supersedes" in row and not (isinstance(row["supersedes"], str)
                                    and row["supersedes"].strip()):
        return "supersedes must be a non-empty claim string"
    if not (isinstance(row["claim"], str) and row["claim"].strip()):
        return "claim must be a non-empty string"
    if not (isinstance(row["recorded_by"], str) and row["recorded_by"].strip()):
        return "recorded_by must be a non-empty string (provenance-mandatory)"
    tooth, reason = row["tooth"], row["prose_only_reason"]
    if (tooth is None) == (reason is None):
        return ("exactly one of tooth / prose_only_reason -- a lesson is "
                "mechanized or it declares why not, never both, never "
                "neither")
    if tooth is not None:
        bad = resolve_tooth(tooth, root)
        if bad:
            return f"tooth does not resolve: {bad}"
    elif not (isinstance(reason, str) and reason.strip()):
        return "prose_only_reason must be a non-empty string"
    return None


def load(ledger: str = LEDGER) -> list:
    if not os.path.isfile(ledger):
        return []
    with open(ledger, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def superseded_claims(rows) -> set:
    """Claims some LATER row has explicitly retired."""
    return {r["supersedes"] for r in rows if r.get("supersedes")}


def record(claim: str, by: str, tooth: str | None, prose_only: str | None,
           ledger: str = LEDGER, root: str = _ROOT,
           supersedes: str | None = None) -> dict:
    """Validate, refuse duplicates, append.  Returns the row appended."""
    row = {"claim": claim, "prose_only_reason": prose_only,
           "recorded_by": by, "tooth": tooth}
    if supersedes:
        rows = load(ledger)
        if not any(r.get("claim") == supersedes for r in rows):
            raise SystemExit(
                "lessons: refused: --supersedes names no recorded claim; a "
                "supersession must point at a row that exists")
        row["supersedes"] = supersedes
    bad = validate_row(row, root)
    if bad:
        raise SystemExit(f"lessons: refused: {bad}")
    for prior in load(ledger):
        if (prior.get("claim") == claim and prior.get("tooth") == tooth
                and prior.get("prose_only_reason") == prose_only):
            raise SystemExit(
                "lessons: refused: exact-duplicate row (already recorded "
                f"by {prior.get('recorded_by')!r})")
    with open(ledger, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    return row


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--claim", required=True,
                    help="the lesson, one sentence, stated as a claim")
    ap.add_argument("--by", required=True,
                    help="provenance: the receipt / PR / session that "
                         "learned it")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--tooth",
                   help="tests/<file>.py::<test_name> that EXECUTES the "
                        "claim; refused unless it resolves")
    g.add_argument("--prose-only", dest="prose_only",
                   help="the declared reason this claim has no executable "
                        "form")
    ap.add_argument("--supersedes", default=None,
                    help="the exact claim of an earlier row this lesson "
                         "retires; the earlier row is never edited")
    ap.add_argument("--ledger", default=LEDGER)
    args = ap.parse_args(argv)
    row = record(args.claim, args.by, args.tooth, args.prose_only,
                 ledger=args.ledger, supersedes=args.supersedes)
    kind = row["tooth"] or f"prose-only: {row['prose_only_reason']}"
    print(f"lessons: recorded ({kind}) -> {args.ledger}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
