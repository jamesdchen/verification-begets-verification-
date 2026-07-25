"""The wake caps, mechanized as far as the ledger can see them.

PLAN_FRAGMENT §3.1 rule 2 (and the purchase-driver prompt that carries it
into unattended sessions, C3_PROMPTS.md) caps wake-driven fix rounds: **at
most two per session, each naming a root cause distinct from the last**, and
a trust-surface wake is NOTED, never worked.  That cap shipped as prose.  No
done-condition of this loop may live only as prose -- the defect that let the
census's dead terms sit unmeasured -- so here is the half of it the committed
evidence can actually decide.

WHAT THE LEDGER SEES.  `tools/cycle_telemetry.py` owns the stage vocabulary
and `wake` is one of its stages: "the seconds a session spent on a fix round
it took because a red lane verdict WOKE it".  The purchase prompt's RECORD
EVERY WAKE clause says one telemetry row is appended PER PUSH, so a
wake-bearing row is a wake round that happened.

THE GROUPING, and why branch.  A session is issued exactly one branch by the
platform ("push your session's ASSIGNED branch ... do not invent another"),
and a session may push several times, so BRANCH is the ledger's name for
"session" and rows-per-branch is rounds-per-session.  Grouping by ts-date
instead would be wrong in both directions: it splits a session that crosses
midnight UTC and it merges two sessions that ran the same day.  We group
across all three axis ledgers, since the branch identifies the session
whichever axis it wrote to -- the grouping that can only ever join, never
split.

HOW HONEST THE COUNT IS.  Rows-with-wake per branch is a LOWER BOUND on wake
rounds: the writer's own docstring notes that repeated rounds inside one push
would sum into a single `wake` number, so more than two wake rows on a branch
is a definite over-budget red, while two or fewer is not proof of compliance.
We assert the direction the evidence supports and say so rather than claiming
the stronger thing.

WHAT IS NOT MECHANIZABLE HERE (stated, not faked):

  * **"each naming a root cause DISTINCT from the previous round's."**  The
    schema records seconds per stage.  It has no cause field, so no check
    over this ledger can distinguish two rounds that fixed two different
    reds from two rounds that re-fixed the same one -- and the repeat case
    is exactly the one the rule wants yielded.  The minimal schema change
    that WOULD make it checkable: an optional `wake_cause` string on the row
    (a short slug, e.g. `lean:unknown-identifier`), asserted distinct within
    a branch.  NOT implemented here -- adding a field is a writer change with
    its own teeth and its own receipt, and this file is not the place to
    smuggle one in.
  * **"a trust-surface wake is noted, never worked."**  Which surface a red
    came from is likewise not in the schema; the same `wake_cause` field
    (value `trust-surface`) would make "noted, never worked" checkable as
    "no wake row carries that cause", since noting costs no fix round.
  * **the `[lean-fast]` tag on the push that earned the red.**  Commit
    trailers are not ledger fields.  What IS visible is ordering: a wake can
    only follow a push, so a wake row that is its branch's FIRST row records
    a wake with no push behind it.  That is the checkable shadow of the tag
    and it is what `wake_violations` flags; the tag itself would need a
    `lane` field on the row.

Stdlib-only, offline, deterministic.  The helpers below are pure functions of
a row list so the rule is testable on synthetic rows as well as on the
committed ledger; they live in this file rather than in `tools/` because the
governance check has exactly one consumer -- the moment `session_brief.py`
wants to report wake budget too, they lift to a module with their own teeth,
but a tools module imported by a single test is surface without a second
reader.
"""
import datetime as _dt
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import cycle_telemetry as ct  # noqa: E402  (path shim first)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAN = os.path.join(ROOT, "PLAN_FRAGMENT.md")

#: PLAN_FRAGMENT §3.1 rule 2's COUNT clause, as a number.
WAKE_CAP = 2


# --- pure helpers ----------------------------------------------------------

def _ts_key(row: dict, index: int) -> tuple:
    """Chronological sort key, ties broken by append order.

    The ledgers mix `...Z` and `...+00:00` spellings and one axis carries
    naive stamps; we normalize rather than string-sort, which would order
    those spellings wrongly.  An unparseable stamp sorts last on its own
    text instead of raising: this is an audit over committed evidence, and a
    malformed row is the writer's tooth to catch, not this one's.
    """
    ts = str(row.get("ts", ""))
    try:
        parsed = _dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=_dt.timezone.utc)
        return (0, parsed.timestamp(), index)
    except ValueError:
        return (1, float(index), index)


def has_wake(row: dict) -> bool:
    """True when the row records a wake-driven fix round: a `wake` stage
    that is present and non-null."""
    stages = row.get("stages") or {}
    return stages.get("wake") is not None


def wake_rounds_by_branch(rows) -> dict:
    """Wake-bearing rows per branch -- the lower bound on rounds per session
    (see the module docstring: one row per push, rounds inside a push sum)."""
    counts = {}
    for row in rows:
        if has_wake(row):
            branch = str(row.get("branch", ""))
            counts[branch] = counts.get(branch, 0) + 1
    return counts


def wake_violations(rows, cap: int = WAKE_CAP) -> list:
    """Every §3.1 rule 2 breach this ledger can decide, as readable strings.

    Two checks, both one-directional (a finding is a breach; an empty list is
    "nothing visible", not "compliant"):

      * COUNT -- more than ``cap`` wake-bearing rows on one branch.
      * ORDER -- a wake row that is its branch's first row, i.e. a wake with
        no push behind it, which no red verdict could have caused.
    """
    ordered = sorted(
        ((_ts_key(r, i), r) for i, r in enumerate(rows)), key=lambda p: p[0])
    out = []
    for branch, count in sorted(wake_rounds_by_branch(rows).items()):
        if count > cap:
            out.append(
                f"branch {branch!r} carries {count} wake-bearing telemetry "
                f"rows; PLAN_FRAGMENT §3.1 rule 2 caps wake-driven fix rounds "
                f"at {cap} per session (one row per push), and a red that "
                f"repeats is environment or design -- it yields with the "
                f"cause named, it does not buy another round")
    seen = set()
    for _key, row in ordered:
        branch = str(row.get("branch", ""))
        first = branch not in seen
        seen.add(branch)
        if first and has_wake(row):
            out.append(
                f"branch {branch!r} opens with a wake-bearing row: a wake "
                f"round can only FOLLOW a push (the red it answers is a "
                f"verdict on pushed work), so this row has no push behind it")
    return out


def load_ledger_rows(axes=ct.AXES, root=None) -> list:
    """Every committed telemetry row across the given axes."""
    rows = []
    for axis in axes:
        path = ct.ledger_path(axis, root=root)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


# --- the committed ledger --------------------------------------------------

def test_committed_ledger_respects_the_wake_budget():
    """The real evidence, skipped BY NAME until a cycle seeds it.

    Wake-on-red is unmeasured as of the amendment that wrote it down: the
    first purchase cycle that logs a `wake` stage is what turns it from a
    claim into evidence.  Until then this skips loudly -- the reflect-shadow
    ledger's skip-until-seeded precedent -- because a silent pass over an
    empty ledger would read exactly like a satisfied cap and would be the
    prose defect wearing a green.
    """
    rows = load_ledger_rows()
    if not any(has_wake(r) for r in rows):
        pytest.skip(
            "no `wake` stage in any committed telemetry ledger yet: the cap "
            "is asserted, not observed, until a cycle logs a wake round")
    bad = wake_violations(rows)
    assert not bad, (
        "the committed telemetry ledger breaches PLAN_FRAGMENT §3.1 rule 2:\n"
        + "\n".join("  - " + b for b in bad))


def test_wake_stage_is_in_the_writer_vocabulary():
    # The check would silently measure nothing if the stage were renamed or
    # dropped: the ledger's own vocabulary is what makes `wake` recordable.
    assert "wake" in ct.STAGES


# --- synthetic fixtures: the rule itself, on rows we control ---------------

def _row(branch, ts, stages, sha="deadbeef"):
    return ct.build_row("purchase", ts, branch, sha, 1, stages)


def _push(branch, ts):
    return _row(branch, ts, {"author": 600.0, "suite": 70.0, "ship": 30.0})


def _wake(branch, ts, secs=180.0):
    return _row(branch, ts, {"wake": secs, "ship": 20.0})


def test_two_wake_rounds_are_inside_budget():
    rows = [
        _push("claude/a", "2026-07-25T01:00:00+00:00"),
        _wake("claude/a", "2026-07-25T01:30:00+00:00"),
        _wake("claude/a", "2026-07-25T02:10:00+00:00"),
    ]
    assert wake_rounds_by_branch(rows) == {"claude/a": 2}
    assert wake_violations(rows) == []


def test_three_wake_rounds_are_red():
    rows = [
        _push("claude/a", "2026-07-25T01:00:00+00:00"),
        _wake("claude/a", "2026-07-25T01:30:00+00:00"),
        _wake("claude/a", "2026-07-25T02:10:00+00:00"),
        _wake("claude/a", "2026-07-25T02:55:00+00:00"),
    ]
    bad = wake_violations(rows)
    assert len(bad) == 1
    assert "3 wake-bearing" in bad[0]
    # and the cap is per SESSION, not per ledger: a second branch's rounds
    # are its own budget and never spill into this one.
    rows += [_push("claude/b", "2026-07-25T03:00:00+00:00"),
             _wake("claude/b", "2026-07-25T03:20:00+00:00")]
    assert len(wake_violations(rows)) == 1


def test_wake_with_no_push_behind_it_is_flagged():
    # The checkable shadow of "the push that earned the red": a wake round
    # that opens its branch answers a verdict on nothing.
    rows = [_wake("claude/c", "2026-07-25T04:00:00+00:00")]
    bad = wake_violations(rows)
    assert len(bad) == 1 and "no push behind it" in bad[0]
    # Chronology decides it, not file order: the same rows appended in the
    # other order are a normal push-then-wake session.
    rows = [_wake("claude/c", "2026-07-25T04:00:00+00:00"),
            _push("claude/c", "2026-07-25T03:00:00+00:00")]
    assert wake_violations(rows) == []


def test_null_and_absent_wake_stages_are_not_rounds():
    # Only a present, non-null `wake` is a round.  A row without the stage is
    # an ordinary push and must never inflate a session's count.
    assert not has_wake(_push("claude/a", "2026-07-25T01:00:00+00:00"))
    assert not has_wake({"branch": "claude/a", "stages": {}})
    assert not has_wake({"branch": "claude/a", "stages": {"wake": None}})
    assert has_wake({"branch": "claude/a", "stages": {"wake": 0.0}})


def test_mixed_timestamp_spellings_sort_chronologically():
    # The committed ledgers carry both `...Z` and `...+00:00`; a string sort
    # would order them wrongly and turn a real first-row wake into a pass.
    rows = [_wake("claude/d", "2026-07-25T04:00:00+00:00"),
            _push("claude/d", "2026-07-24T23:00:00Z")]
    assert wake_violations(rows) == []


# --- the rule and its mechanism stay tied together -------------------------

def test_rule_and_mechanism_cannot_drift_apart():
    """§3.1 rule 2 must name this file (growth_protocol.conformance()'s
    teeth-index idiom: an unnamed mechanism decays back into prose the first
    time someone rewrites the paragraph)."""
    with open(PLAN, encoding="utf-8") as fh:
        plan = fh.read()
    needle = "tests/test_wake_budget.py"
    assert needle in plan, (
        f"PLAN_FRAGMENT.md no longer names {needle}: the wake cap would be "
        "prose again.  Restore the citation, or retire the check "
        "deliberately -- never let the rule and its mechanism drift apart.")
    window = " ".join(plan[max(0, plan.index(needle) - 4000):
                           plan.index(needle)].split())
    assert "lean-last" in window.lower(), (
        f"{needle} is cited in PLAN_FRAGMENT.md but no longer inside the "
        "Lean-last / wake-budget rule (§3.1 rule 2).")
