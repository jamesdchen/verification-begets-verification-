#!/usr/bin/env python3
"""Branch hygiene, DERIVED: keep / delete per remote branch, decided by code.

THE LITTER THIS RETIRES.  Every routine firing ships on a platform-assigned
`claude/<words>` branch, and no session can remove one afterwards: the
session git proxy restricts pushes to the current working branch and
answers 403 to `git push origin --delete` (MEASURED 2026-07-26, and worse,
that push prints the 403 and EXITS 0 with `Everything up-to-date`, so one
firing reported a deletion that had not happened).  The driver prompts
already say the only deletion that works is repo-side -- and this tool plus
its workflow (.github/workflows/branch-reaper.yml) IS the repo side: the
one place holding a token that may delete refs.  MEASURED 2026-07-27, the
day this shipped: 108 remote branches, of which 4 carried open PRs, 29 rode
merged PRs, 71 rode closed-unmerged PRs (superseded work, which the
protocol discards and never rebases), and 3 were watchdog telemetry strays
with no PR at all.

THE SEAM, same as loop_guard: the FETCH stays with the caller (the workflow
holds the token; this tool has no network and wants none), the DECISION
lives here.  Pipe in the branch list and the full PR list, get one verdict
line per branch:

    KEEP    default-branch | open-pr #N | stray inside grace | reads-fail-safe
    DELETE  merged-pr #N | closed-pr #N | stray past grace

Precedence per branch, first match wins:
  1. the default branch is KEEP, unconditionally;
  2. any OPEN PR on the branch is KEEP (deleting the head closes the PR);
  3. any MERGED PR is DELETE (the squash landed; the branch is residue);
  4. all PRs closed-unmerged is DELETE (superseded work is DISCARDED,
     never rebased -- the cycle-10/11/12 precedent, in ref form);
  5. no PR at all: DELETE only past the grace window, else KEEP -- a fresh
     stray may be a session mid-claim whose PR has not appeared yet, and
     the watchdog's telemetry-only branches deserve a salvage look before
     they age out.

MERGED IS READ OFF `merged_at`, NEVER the `merged` boolean: the list
endpoint's boolean was measured `false` on all 217 PRs of this repo while
`merged_at` was set on the 139 that had in fact merged (2026-07-27).  A
field that is wrong 139 times out of 139 is not a fallback, it is a decoy.

READS FAIL SAFE toward KEEPING: an unreadable --now or input file exits 2
with NOTHING on stdout (an errored call must never impersonate a delete
list); a malformed branch row, or a stray with an unreadable commit date,
is KEEP with the reason saying so.  The failure direction matters -- a kept
branch costs a listing line, a wrongly deleted one costs an open PR.

CLOCKS ARE INJECTED, never read: --now is required, so every verdict is a
pure function of its inputs and the grace boundary is testable exactly.

Usage (the workflow already has both lists):
    python3 tools/branch_reaper.py --now <RFC3339> \\
        --branches branches.json --prs prs.json \\
        [--default-branch main] [--grace-days 14] [--porcelain]

`branches.json` is a list of {"name", "newest_commit_at" (RFC3339|null)};
`prs.json` is the raw GitHub PR list (state=all) -- rows may carry either
the nested `head.ref` or a flat `head_ref`, extra keys are ignored, so
both the REST payload and a pre-thinned TSV-derived list pipe in unchanged.
`--porcelain` prints only the DELETE branch names, one per line, for the
workflow's deletion loop.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys

KEEP, DELETE = "KEEP", "DELETE"

#: A branch with NO PR is deletable only past this age.  Fresh strays are
#: either a claim whose PR the eventually-consistent index has not surfaced
#: yet, or watchdog telemetry worth a salvage look; two weeks is long past
#: both and short enough that strays never re-accumulate into a pile.
GRACE_DAYS = 14


def _parse(ts):
    """RFC3339 -> aware datetime, or None if unreadable (fails safe upstream)."""
    if not isinstance(ts, str) or not ts:
        return None
    try:
        return _dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _head_ref(pr):
    head = pr.get("head")
    if isinstance(head, dict):
        return head.get("ref")
    return pr.get("head_ref")


def verdicts(branches, prs, now_iso, default_branch="main",
             grace_days=GRACE_DAYS):
    """[(verdict, branch, reason)] -- the whole policy, as one pure function.

    Returns None when --now or either list is unreadable: the caller must
    treat that as "no delete list exists", never as an empty one.
    """
    now = _parse(now_iso)
    if now is None or not isinstance(branches, list) \
            or not isinstance(prs, list):
        return None

    by_ref = {}
    for pr in prs:
        if not isinstance(pr, dict):
            continue
        ref = _head_ref(pr)
        if isinstance(ref, str) and ref:
            by_ref.setdefault(ref, []).append(pr)

    out = []
    for row in branches:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str) \
                or not row.get("name"):
            out.append((KEEP, "<malformed-row>",
                        "malformed branch row; reads fail safe"))
            continue
        name = row["name"]
        if name == default_branch:
            out.append((KEEP, name, "the default branch"))
            continue

        rows = by_ref.get(name, [])
        open_prs = [p for p in rows if p.get("state") == "open"]
        if open_prs:
            out.append((KEEP, name,
                        f"open PR #{open_prs[0].get('number')}: deleting the "
                        "head would close it"))
            continue
        # merged_at, never the `merged` boolean -- see the module docstring.
        merged = [p for p in rows if _parse(p.get("merged_at")) is not None]
        if merged:
            out.append((DELETE, name,
                        f"PR #{merged[0].get('number')} merged; the branch "
                        "is residue"))
            continue
        if rows:
            out.append((DELETE, name,
                        f"every PR closed unmerged (newest "
                        f"#{max(p.get('number') or 0 for p in rows)}): "
                        "superseded work is discarded, never rebased"))
            continue

        age = None
        t = _parse(row.get("newest_commit_at"))
        if t is not None:
            age = (now - t).total_seconds()
        if age is None:
            out.append((KEEP, name,
                        "no PR and no readable commit date; reads fail safe"))
        elif age >= grace_days * 86400:
            out.append((DELETE, name,
                        f"no PR and {int(age // 86400)}d old "
                        f"(grace {grace_days}d): an abandoned stray"))
        else:
            out.append((KEEP, name,
                        f"no PR but only {int(age // 86400)}d old "
                        f"(grace {grace_days}d): could be a claim the PR "
                        "index has not surfaced, or telemetry worth salvage"))
    return out


def _load(path):
    try:
        with (sys.stdin if path == "-" else open(path)) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="keep/delete verdicts for remote branches; the caller "
                    "fetches, this tool decides (see module docstring)")
    ap.add_argument("--now", required=True, help="RFC3339; injected, never read")
    ap.add_argument("--branches", required=True,
                    help="JSON file (or -) of {name, newest_commit_at} rows")
    ap.add_argument("--prs", required=True,
                    help="JSON file (or -) of GitHub PR rows, state=all")
    ap.add_argument("--default-branch", default="main")
    ap.add_argument("--grace-days", type=int, default=GRACE_DAYS)
    ap.add_argument("--porcelain", action="store_true",
                    help="print only DELETE branch names, one per line")
    args = ap.parse_args(argv)

    got = verdicts(_load(args.branches), _load(args.prs), args.now,
                   args.default_branch, args.grace_days)
    if got is None:
        print("unreadable input; no delete list exists -- an errored call "
              "must never impersonate an answer", file=sys.stderr)
        return 2
    for verdict, name, reason in got:
        if args.porcelain:
            if verdict == DELETE:
                print(name)
        else:
            print(f"{verdict}\t{name}\t{reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
