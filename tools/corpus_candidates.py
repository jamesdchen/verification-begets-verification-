#!/usr/bin/env python3
"""The corpus-candidate selector -- PLAN_FRAGMENT §3.2 path (c), made mechanical.

Path (c) is the only supply lever that has ever moved the intake window, and
it was the one lever no Routine could reach.  The reason was not a missing
tool -- ``tools/intake_corpus.py`` has existed since §3.1 rule 4 -- it was a
missing DECISION.  The driver prompt required a maintainer to NAME a corpus,
so an unattended firing found nothing named and exited, and the working lever
sat unused while both loops idled.

The obvious fix is the forbidden one.  A session that picks its own corpus
picks the corpus that looks like it would certify, and a corpus intaken
because it would certify is the portfolio reading lying to itself.  So we do
not delete the refusal; we MOVE the judgment:

    SHOPPING (forbidden, forever)
        choosing a corpus BECAUSE it would certify, or because it would move
        a number.  Outcome-driven selection distorts the measurement, which
        is the one thing this system exists to prevent.

    SELECTION (fine, mechanical)
        consuming a PRE-DECLARED list in a fixed order.  The judgment -- is
        this corpus near the fragment and worth intaking? -- is made ONCE, in
        advance, by a human writing a row into
        ``specs/mathsources/corpus_candidates.json``.  The per-cycle act is
        then order-based and blind to yield.

The human judgment did not disappear.  It moved from per-cycle to
per-candidate, which is exactly where it can be reviewed as a diff.

WHAT MAKES THE SELECTION YIELD-BLIND, mechanically.  ``next_candidate`` is
the first row whose status is ``candidate``, in DECLARATION ORDER, and that
is the whole rule.  This module reads ONE file -- the registry -- and
``tests/test_corpus_candidates.py`` inspects this source to assert that no
portfolio-reading, intake-window or queue artifact is named anywhere in
it.  That tooth is the mechanical statement of "yield-blind": the selector
CANNOT rank by what an intake would buy, because it cannot see it.

Ordering is therefore load-bearing.  It is the maintainer's declared
priority, and a row is never reordered to put a more promising corpus first
-- that reordering IS the shopping we forbade, spelled as a diff.

OUTCOMES ARE ROWS, NOT DELETIONS.  ``--mark`` flips a row's status in place:
``intaken`` when the intake landed, ``refused`` (with a reason) when the
fetch or the adapter refused, or when the portfolio reading placed the corpus
far from the fragment.  Nothing is ever removed.  A registry that deletes
consumed rows is inventory; one that keeps them is evidence, and the refusal
rows are the more valuable half -- they record what we tried and what it
measured, so no later cycle silently retries the same source.

Usage:
    python3 tools/corpus_candidates.py                 # print the selection
    python3 tools/corpus_candidates.py --list          # every row + status
    python3 tools/corpus_candidates.py --json          # machine-readable
    python3 tools/corpus_candidates.py --mark NAME intaken
    python3 tools/corpus_candidates.py --mark NAME refused --reason TEXT
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from buildloop import lanes

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(_ROOT, "specs", "mathsources", "corpus_candidates.json")

#: The fields a declared row must carry.  ``rationale`` and ``declared_by``
#: are as mandatory as the URL: the park-ledger REASONS idiom, applied to
#: intake -- a row with no stated reason is an unexplained fetch, and a row
#: with no provenance is an anonymous one.
REQUIRED_FIELDS = ("adapter", "declared_by", "name", "project", "rationale",
                   "source", "status")

#: status -> what the status means.  Grow by appending; rows are evidence, so
#: a status is never repurposed once written.
STATUSES = {
    "candidate": "declared and not yet consumed; selectable",
    "example": "documentation only (non-real URL); never selected",
    "intaken": "the intake ran and the corpus is committed; the row STAYS",
    "refused": "the intake did not happen or did not pay; carries "
               "refused_reason.  A refusal is data, never a silent retry",
}

#: The two statuses a cycle may WRITE.  ``candidate`` is a human declaration
#: and ``example`` is documentation; neither is an outcome a driver records.
TERMINAL_STATUSES = ("intaken", "refused")

#: The adapters ``tools/intake_corpus.py`` dispatches on.
ADAPTERS = ("blueprint", "sphinx")

#: reason -> what it means and what changes it.  A selector that returns
#: nothing must say WHICH nothing: a missing file, a file with no rows, and a
#: file whose rows are all spent are three different maintainer actions.
REASONS = {
    "candidate-available":
        "a declared row is selectable; the driver may intake it unattended",
    "registry-absent":
        "specs/mathsources/corpus_candidates.json is not on disk -- the "
        "declaration point itself is missing, which is a tree problem, not a "
        "supply reading",
    "registry-empty":
        "the registry parses and declares no rows at all; the first row a "
        "maintainer appends turns this path on",
    "registry-exhausted":
        "every declared row is already intaken, refused, or documentation -- "
        "the loop consumed the list.  UNBLOCKED BY: a maintainer appending "
        "one row (name, source, adapter, project, declared_by, rationale)",
    "registry-unreadable":
        "the registry is on disk but did not parse as JSON; an errored read "
        "never impersonates an answer, so this is not 'no candidates'",
}


# ------------------------------------------------------------------- reading

def load(path: str = REGISTRY) -> dict:
    """Parse the registry.  Never raises on a missing or malformed file: the
    failure is returned as a named reason under ``_unavailable``, because a
    driver asking "is there a candidate?" must get an ANSWER, not a crash."""
    if not os.path.exists(path):
        return {"_unavailable": "registry-absent"}
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (ValueError, UnicodeDecodeError):
        return {"_unavailable": "registry-unreadable"}
    if not isinstance(doc, dict) or not isinstance(doc.get("candidates"), list):
        return {"_unavailable": "registry-unreadable"}
    return doc


def rows(path: str = REGISTRY) -> list:
    """Declared rows in DECLARATION ORDER (the file's own order, never sorted)."""
    doc = load(path)
    return [] if "_unavailable" in doc else list(doc["candidates"])


def counts(path: str = REGISTRY) -> dict:
    """status -> row count, over every status in the vocabulary."""
    out = {s: 0 for s in STATUSES}
    for row in rows(path):
        st = row.get("status")
        out[st] = out.get(st, 0) + 1
    return out


def next_candidate(path: str = REGISTRY):
    """The FIRST row with status ``candidate``, in declaration order, or None.

    This is the whole selection rule.  It consults nothing else -- no reading
    of what the corpus would buy enters here, by construction."""
    for row in rows(path):
        if row.get("status") == "candidate":
            return row
    return None


def select(path: str = REGISTRY) -> dict:
    """The selection, or a NAMED reason for its absence.

    Returns ``{"reason", "selected", "counts"}`` where ``reason`` is always a
    key of :data:`REASONS` -- the empty and exhausted paths are answers, not
    errors."""
    doc = load(path)
    if "_unavailable" in doc:
        return {"counts": {s: 0 for s in STATUSES},
                "reason": doc["_unavailable"], "selected": None}
    declared = list(doc["candidates"])
    picked = next_candidate(path)
    if picked is not None:
        reason = "candidate-available"
    elif not declared:
        reason = "registry-empty"
    else:
        reason = "registry-exhausted"
    return {"counts": counts(path), "reason": reason, "selected": picked}


def intake_command(row: dict) -> str:
    """The exact ``tools/intake_corpus.py`` invocation this row declares.

    Built from the row's own fields so the unattended path never has to
    compose a URL -- the one thing the honesty bounds forbid it to invent."""
    missing = [f for f in REQUIRED_FIELDS if not str(row.get(f, "")).strip()]
    if missing:
        raise SystemExit(f"row {row.get('name')!r} is missing required "
                         f"field(s): {', '.join(missing)}")
    if row["adapter"] not in ADAPTERS:
        raise SystemExit(f"row {row['name']!r}: unknown adapter "
                         f"{row['adapter']!r} ({'|'.join(ADAPTERS)})")
    return ("python3 tools/intake_corpus.py "
            f"--name {row['name']} --source {row['source']} "
            f"--adapter {row['adapter']} --project {json.dumps(row['project'])}")


# ------------------------------------------------------------------- writing

def _write(doc: dict, path: str) -> None:
    """Canonical form: sorted keys, indent 1, trailing newline -- the same
    discipline the portfolio and window writers use.  ``ensure_ascii`` stays off
    so a section sign survives a round trip byte-identically."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True, ensure_ascii=False)
        fh.write("\n")


def mark(name: str, status: str, *, reason: str = None,
         path: str = REGISTRY) -> dict:
    """Record an outcome by FLIPPING a row's status in place.

    Never deletes and never reorders: declaration order is the selection
    rule, and a consumed row is the evidence that we consumed it."""
    if status not in TERMINAL_STATUSES:
        raise SystemExit(f"cannot mark {status!r}: a cycle records only "
                         f"{'/'.join(TERMINAL_STATUSES)} "
                         "(candidate is a human declaration)")
    if status == "refused" and not (reason or "").strip():
        raise SystemExit("--mark NAME refused requires --reason: a refusal "
                         "with no stated reason is not a measurement")
    doc = load(path)
    if "_unavailable" in doc:
        raise SystemExit(f"registry not usable: {doc['_unavailable']}")
    for row in doc["candidates"]:
        if row.get("name") != name:
            continue
        if row.get("status") == "example":
            raise SystemExit(f"{name!r} is the documentation row; it is never "
                             "intaken or refused")
        row["status"] = status
        if status == "refused":
            row["refused_reason"] = reason.strip()
        _write(doc, path)
        return row
    raise SystemExit(f"no declared row named {name!r}")


# ----------------------------------------------------------------------- CLI

def _render(sel: dict, path: str = REGISTRY) -> str:
    out = [f"reason: {sel['reason']}  ({REASONS[sel['reason']]})",
           "declared: " + ", ".join(f"{s}={sel['counts'].get(s, 0)}"
                                    for s in sorted(STATUSES))]
    row = sel["selected"]
    if row is None:
        out.append("SELECTED: none -- path (c) has nothing declared to take.")
        out.append(f"Declaration point: {os.path.relpath(path, _ROOT)}")
    else:
        out.append(f"SELECTED: {row['name']}  (adapter {row['adapter']})")
        out.append(f"  source:      {row['source']}")
        out.append(f"  declared_by: {row['declared_by']}")
        out.append(f"  rationale:   {row['rationale']}")
        out.append("  run: " + intake_command(row))
    out.append("selection is by DECLARATION ORDER only; nothing about what "
               "the intake would buy is consulted here")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--registry", default=REGISTRY)
    ap.add_argument("--list", action="store_true",
                    help="print every declared row with its status")
    ap.add_argument("--json", action="store_true",
                    help="emit the selection as canonical JSON")
    ap.add_argument("--mark", nargs=2, metavar=("NAME", "STATUS"),
                    help=f"record an outcome ({'|'.join(TERMINAL_STATUSES)})")
    ap.add_argument("--reason", default=None,
                    help="refusal reason (required with --mark NAME refused)")
    args = ap.parse_args(argv)

    with lanes.token_free("corpus-candidates"):
        if args.mark:
            row = mark(args.mark[0], args.mark[1], reason=args.reason,
                       path=args.registry)
            print(f"{row['name']}: status -> {row['status']}"
                  + (f"  ({row['refused_reason']})"
                     if row.get("refused_reason") else ""))
            return 0
        if args.list:
            for row in rows(args.registry):
                extra = (f"  -- {row['refused_reason']}"
                         if row.get("refused_reason") else "")
                print(f"{row.get('status','?'):10s} {row.get('name','?')}"
                      f"{extra}")
            return 0
        sel = select(args.registry)
        if args.json:
            print(json.dumps(sel, sort_keys=True, indent=1, ensure_ascii=False))
        else:
            print(_render(sel, args.registry))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
