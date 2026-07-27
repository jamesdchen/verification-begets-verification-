#!/usr/bin/env python3
"""The loop guards, DERIVED: claim / yield / exit, decided by code.

WHAT WAS PROSE UNTIL NOW.  Both driver prompts open with a dense paragraph
of in-flight arithmetic -- the freshness guard (CI in progress, commits
under 45 minutes, a draft claim under 2 hours), the stale-claim rule (a
claim-only draft OVER 2 hours is a dead session's lock), yield-on-earlier-
claim (cycle 12 measured an EIGHT-SECOND open-PR index lag, so two sessions
built the identical cycle and one threw 20 minutes away), the purchase
loop's stricter any-open-purchase-exits rule, and READS-FAIL-SAFE.  Every
one of those is a pure function of state the session has already fetched,
executed by an LLM reading a paragraph.  That is the shape this repo has
been paying for all week: a decision that branches on machine-readable
state has no business being a sentence.

THE SEAM, and why it is where it is.  The FETCH stays with the session (it
holds the GitHub tools; this tool has no network and wants none) and the
DECISION moves here.  The session pipes the open-PR list it already has in,
and gets back one verdict line plus its reason:

    CLAIM        -- no blocker; open your claim draft
    YIELD        -- an earlier claim exists; close yours and exit
    EXIT         -- in-flight work; this firing is done
    CLOSE-STALE  -- an abandoned claim-only lock; close it, then claim

READS FAIL SAFE is the default, not a branch: an unreadable or malformed
input yields EXIT, because an errored call must never impersonate an
answer, and for the purchase loop an unreadable list means "a purchase may
be in flight" -- the reading that protects one-purchase-per-cycle through
an outage.

CLOCKS ARE INJECTED, never read.  ``--now`` is required, so the verdict is
a pure function of its inputs and every threshold is testable at the
boundary rather than approximately.  (The repo's ledgers ban clocks for the
same reason: a value the caller supplies is a value a test can pin.)

Usage (the session already has the PR list):
    python3 tools/loop_guard.py --loop corpus --now <RFC3339> --prs -
    python3 tools/loop_guard.py --loop purchase --now <RFC3339> \\
        --prs prs.json [--mine <created_at>]

Each PR object carries what the guard actually branches on -- extra keys
are ignored, so the raw GitHub payload can be piped in unchanged:
    title, draft (bool), created_at (RFC3339),
    checks_in_progress (bool), newest_commit_at (RFC3339 or null),
    claim_only (bool -- carries nothing but its empty claim commit)
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys

CORPUS_TITLE = "C3 cycle"
PURCHASE_TITLE = "C3 purchase"

#: The measured thresholds, named once so prose and code cannot disagree.
FRESH_COMMIT_S = 45 * 60      # a branch pushed inside this window is live work
CLAIM_LOCK_S = 2 * 60 * 60    # a claim draft is a lock for this long, then dead

CLAIM, YIELD, EXIT, CLOSE_STALE = "CLAIM", "YIELD", "EXIT", "CLOSE-STALE"


def _parse(ts):
    """RFC3339 -> aware datetime, or None if unreadable (fails safe upstream)."""
    if not isinstance(ts, str) or not ts:
        return None
    try:
        return _dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _age_s(ts, now):
    t = _parse(ts)
    return None if t is None else (now - t).total_seconds()


def verdict(loop: str, prs, now_iso: str, mine_created_at: str | None = None):
    """(verdict, reason, subject) -- the whole guard, as one pure function.

    ``subject`` names the PR the verdict is about (a number or None) so the
    caller can act without re-deriving which row decided it."""
    now = _parse(now_iso)
    if now is None:
        return EXIT, "unreadable --now; reads fail safe", None
    if not isinstance(prs, list):
        return EXIT, ("unreadable PR list; reads fail safe -- an errored "
                      "call must never impersonate an answer"), None

    title = PURCHASE_TITLE if loop == "purchase" else CORPUS_TITLE
    open_prs = []
    for pr in prs:
        if not isinstance(pr, dict):
            return EXIT, "malformed PR row; reads fail safe", None
        if str(pr.get("title", "")).startswith(title):
            open_prs.append(pr)

    # TWO PHASES, and conflating them was this tool's own first bug.
    # WITHOUT --mine the session holds no claim: the question is "is anyone
    # else working?", answered by each loop's in-flight rule below.  WITH
    # --mine it already holds one: every open PR in this loop's namespace is
    # now either the race it must win or the race it lost, and the tie-break
    # is the ONLY question -- reusing the in-flight check there would make a
    # session EXIT on the very claim it just opened, leaving its own lock
    # behind as litter.
    #
    # THE SPLIT IS LOOP-AGNOSTIC, and shipping it corpus-only wedged the
    # purchase loop shut (MEASURED 2026-07-27, the first purchase firing
    # after this tool landed).  The purchase branch used to return BEFORE
    # this block, so the mandated post-claim call answered EXIT on the
    # session's own draft, every time.  That is not one lost firing but a
    # closed loop: the abandoned claim then trips the pre-claim
    # any-open-purchase rule for an hour, goes CLOSE-STALE at two, and the
    # next firing re-claims and exits identically -- while the watchdog
    # reads a sub-lock claim draft as a cycle in flight and reports the loop
    # HEALTHY.  A guard that cannot be obeyed without wedging the loop it
    # guards is worse than the paragraph it replaced.
    #
    # YIELD-ON-EARLIER-CLAIM.  Claiming alone does not close the race:
    # cycle 12 measured the open-PR index EIGHT SECONDS behind a PR that
    # already existed, so two sessions passed the guard and built the
    # same cycle.  created_at decides; the later claim closes itself.
    if mine_created_at:
        mine = _parse(mine_created_at)
        if mine is None:
            return EXIT, "unreadable --mine; reads fail safe", None
        for pr in open_prs:
            theirs = _parse(pr.get("created_at"))
            if theirs is not None and theirs < mine:
                return (YIELD,
                        "an earlier claim exists (created_at precedes "
                        "yours); close yours with a supersession comment "
                        "naming the winner and exit",
                        pr.get("number"))
        return CLAIM, "your claim is the earliest open claim; proceed", None

    # THE PURCHASE LOOP IS STRICTER, and deliberately: any open purchase PR
    # exits the firing regardless of age or CI state, because the previous
    # purchase must MERGE before the next is priced (one purchase per
    # flywheel cycle).  No staleness escape hatch -- a purchase PR waiting
    # on a maintainer is not abandoned work, it is the handoff working.
    # (Pre-claim only: the post-claim phase above has already returned.)
    if loop == "purchase":
        for pr in open_prs:
            # THE NO-CI CONJUNCT, and it was missing here while the corpus
            # branch below has always carried it (MEASURED 2026-07-27, the
            # same asymmetry class as the post-claim phase: a rule
            # implemented for one of two symmetric loops, with the tooth
            # that pins it exercising only the loop that has it).  A
            # purchase is the long job -- P8 and P9 each ran past the claim
            # lock -- so closing an over-age draft whose CI is ACTIVELY
            # RUNNING evicts a session that is still working, and the next
            # firing then claims and builds a SECOND purchase concurrently.
            # That is one-purchase-per-flywheel-cycle broken by the guard
            # meant to protect it.
            if (pr.get("claim_only") and not pr.get("checks_in_progress")
                    and (_age_s(pr.get("created_at"), now)
                         or 0) > CLAIM_LOCK_S):
                return (CLOSE_STALE,
                        "claim-only purchase draft older than the claim lock: "
                        "a dead session's lock, not work in flight",
                        pr.get("number"))
        if open_prs:
            pr = open_prs[0]
            return (EXIT,
                    "an open `C3 purchase` PR exists; one purchase per "
                    "flywheel cycle means the previous bill must merge first",
                    pr.get("number"))
        return CLAIM, "no open purchase PR; the price list is unspent", None

    # --- corpus loop, pre-claim: the freshness guard ---------------------
    for pr in open_prs:
        if pr.get("checks_in_progress"):
            return EXIT, "an open cycle PR has CI in progress", pr.get("number")
        age = _age_s(pr.get("newest_commit_at"), now)
        if age is not None and age < FRESH_COMMIT_S:
            return (EXIT,
                    f"an open cycle PR's branch carries commits {int(age)}s "
                    f"old (< {FRESH_COMMIT_S}s): live work",
                    pr.get("number"))
        if pr.get("claim_only"):
            c_age = _age_s(pr.get("created_at"), now)
            if c_age is None:
                return EXIT, "a claim draft with unreadable created_at; " \
                             "reads fail safe", pr.get("number")
            if c_age < CLAIM_LOCK_S:
                return (EXIT, f"an open claim draft is {int(c_age)}s old "
                              f"(< {CLAIM_LOCK_S}s): the in-flight lock holds",
                        pr.get("number"))
            return (CLOSE_STALE,
                    f"a claim-only draft is {int(c_age)}s old with no CI: a "
                    "dead session's abandoned lock, not in-flight work",
                    pr.get("number"))

    return CLAIM, "no in-flight cycle work; open your claim draft", None


#: A loop is expected to COMPLETE a cycle at least this often.  Both drivers
#: fire hourly, so six hours is five forgiven firings -- generous enough that
#: a slow night is never alarmed, tight enough that claim-churn surfaces
#: within two watchdog firings.
COMPLETION_WINDOW_S = 6 * 60 * 60

HEALTHY, IN_FLIGHT, CLAIM_CHURN, DEAD = (
    "HEALTHY", "IN-FLIGHT", "CLAIM-CHURN", "DEAD")


def health(loop: str, prs, merged_at, now_iso: str):
    """(status, reason) -- is this loop actually COMPLETING cycles?

    THE BLINDNESS THIS CLOSES (measured 2026-07-27).  The watchdog's rule was
    "a claim-only draft under 2 hours old is a cycle in flight and counts as
    activity".  Both drivers fire HOURLY and the watchdog every THREE hours,
    so a loop that claims and exits every firing always presents a fresh
    claim draft -- and reads HEALTHY forever.  That is exactly how the
    purchase loop's post-claim wedge (#198) survived four firings with the
    only alarm channel reporting both loops fine.

    A CLAIM IS A PROMISE; A MERGE IS A CYCLE.  So the predicate asks what the
    loop has FINISHED, and treats a claim draft as evidence of intent, never
    of progress:

      HEALTHY      merged a cycle inside the completion window
      IN-FLIGHT    no recent merge, but real work is open (a non-claim PR, or
                   CI running) -- a slow cycle, not a stuck loop
      CLAIM-CHURN  no recent merge and the ONLY thing open is a claim draft:
                   the wedge signature, and the one the old rule called
                   healthy
      DEAD         no recent merge and nothing open at all

    ``merged_at`` is the list of RFC3339 merge times for THIS loop's cycle
    PRs (the caller fetches; this tool decides).  Unreadable input fails
    safe to DEAD rather than HEALTHY: an alarm channel that goes quiet on a
    bad read is worse than one that cries once.
    """
    now = _parse(now_iso)
    if now is None or not isinstance(prs, list) or not isinstance(
            merged_at, list):
        return DEAD, "unreadable input; an alarm fails LOUD, never quiet"

    title = PURCHASE_TITLE if loop == "purchase" else CORPUS_TITLE
    mine = [pr for pr in prs if isinstance(pr, dict)
            and str(pr.get("title", "")).startswith(title)]

    ages = [a for a in (_age_s(t, now) for t in merged_at) if a is not None]
    if ages and min(ages) <= COMPLETION_WINDOW_S:
        return HEALTHY, (f"completed a cycle {int(min(ages))}s ago "
                         f"(window {COMPLETION_WINDOW_S}s)")

    substantive = [pr for pr in mine
                   if not pr.get("claim_only") or pr.get("checks_in_progress")]
    if substantive:
        return IN_FLIGHT, ("no completed cycle in the window, but real work "
                           "is open -- a slow cycle, not a stuck loop")
    if mine:
        return CLAIM_CHURN, (
            "no completed cycle in the window and the only open PR is a claim "
            "draft: the loop is claiming and exiting without finishing, which "
            "the old `a fresh claim counts as activity` rule read as healthy")
    return DEAD, "no completed cycle in the window and nothing open"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--loop", required=True, choices=("corpus", "purchase"))
    ap.add_argument("--now", required=True,
                    help="RFC3339 now (injected, never read: the verdict is "
                         "a pure function of its inputs)")
    ap.add_argument("--prs", required=True,
                    help="path to the open-PR JSON list, or - for stdin")
    ap.add_argument("--mine", default=None,
                    help="your own claim's created_at; enables the "
                         "yield-on-earlier-claim tie-break")
    args = ap.parse_args(argv)

    raw = sys.stdin.read() if args.prs == "-" else open(args.prs).read()
    try:
        prs = json.loads(raw)
    except (ValueError, TypeError):
        prs = None          # reads fail safe -- verdict() turns this into EXIT

    v, reason, subject = verdict(args.loop, prs, args.now, args.mine)
    where = f" (PR #{subject})" if subject is not None else ""
    print(f"{v}{where}: {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
