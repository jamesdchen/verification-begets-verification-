"""Teeth for the derived loop guards (tools/loop_guard.py).

WHAT THESE PIN THAT PROSE COULD NOT.  Until this tool existed, the guards
were a paragraph at the head of each driver prompt, executed by an LLM: the
45-minute fresh-commit window, the 2-hour claim lock, the stale-claim
close, the purchase loop's stricter any-open-purchase-exits rule, and
READS-FAIL-SAFE.  A paragraph cannot be tested at its boundaries, and the
one measurement that mattered most -- cycle 12's EIGHT-SECOND open-PR index
lag, which let two sessions build the identical cycle -- was discovered in
production rather than by a test staging the race.

Every verdict below is EXECUTED against synthetic PR state, including both
sides of each threshold, which is the property the prompt version never had
at any price.
"""
import json
import os
import subprocess
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "tools"))

import loop_guard as G  # noqa: E402

NOW = "2026-07-27T00:00:00Z"


def _ago(seconds):
    """An RFC3339 stamp `seconds` before NOW, computed from NOW itself so no
    test reads a clock (the same discipline the tool's --now enforces)."""
    import datetime as dt
    t = dt.datetime.fromisoformat(NOW.replace("Z", "+00:00"))
    return (t - dt.timedelta(seconds=seconds)).isoformat().replace(
        "+00:00", "Z")


def _pr(title="C3 cycle 26", number=1, **kw):
    pr = {"title": title, "number": number, "draft": False,
          "created_at": _ago(10), "checks_in_progress": False,
          "newest_commit_at": None, "claim_only": False}
    pr.update(kw)
    return pr


def _v(loop, prs, mine=None):
    return G.verdict(loop, prs, NOW, mine)[0]


# ------------------------------------------------------------ corpus loop
def test_an_empty_board_claims():
    assert _v("corpus", []) == G.CLAIM


def test_ci_in_progress_exits():
    assert _v("corpus", [_pr(checks_in_progress=True)]) == G.EXIT


def test_the_fresh_commit_window_is_pinned_on_BOTH_sides():
    """45 minutes, at the boundary.  A threshold tested only from the inside
    is a threshold nobody has measured."""
    just_inside = _pr(newest_commit_at=_ago(G.FRESH_COMMIT_S - 1))
    just_outside = _pr(newest_commit_at=_ago(G.FRESH_COMMIT_S + 1))
    assert _v("corpus", [just_inside]) == G.EXIT
    assert _v("corpus", [just_outside]) == G.CLAIM


def test_the_claim_lock_is_pinned_on_BOTH_sides():
    """Under 2 hours a claim draft is an in-flight lock; over it, the lock is
    a dead session's litter and the next firing supersedes it."""
    live = _pr(claim_only=True, draft=True,
               created_at=_ago(G.CLAIM_LOCK_S - 1))
    dead = _pr(claim_only=True, draft=True,
               created_at=_ago(G.CLAIM_LOCK_S + 1))
    assert _v("corpus", [live]) == G.EXIT
    assert _v("corpus", [dead]) == G.CLOSE_STALE


@pytest.mark.parametrize("loop,title", [("corpus", "C3 cycle 26"),
                                        ("purchase", "C3 purchase P11")])
def test_a_stale_claim_with_live_CI_is_still_in_flight(loop, title):
    """The conjunct that keeps CLOSE-STALE honest: over-age AND no CI.  A
    slow session that is genuinely running must never have its lock closed
    out from under it.

    PARAMETERIZED OVER BOTH LOOPS, and it had to be: this tooth exercised
    `corpus` alone while the PURCHASE branch shipped without the conjunct at
    all (measured 2026-07-27).  A purchase is the LONG job -- P8 and P9 each
    ran past the claim lock -- so the missing conjunct evicts a session that
    is still working, and the next firing builds a SECOND purchase
    concurrently: one-purchase-per-flywheel-cycle broken by its own guard.
    Same defect class as the post-claim phase (#198), found by auditing for
    it rather than by another wedged night."""
    pr = _pr(title=title, claim_only=True, draft=True,
             checks_in_progress=True,
             created_at=_ago(G.CLAIM_LOCK_S * 3))
    assert _v(loop, [pr]) == G.EXIT


def test_a_merged_or_unrelated_pr_never_blocks():
    """In-flight means OPEN CYCLE work: the caller passes open PRs, and a
    title outside this loop's namespace is not this loop's business."""
    assert _v("corpus", [_pr(title="Some refactor",
                            checks_in_progress=True)]) == G.CLAIM
    assert _v("corpus", [_pr(title="C3 purchase P9",
                            checks_in_progress=True)]) == G.CLAIM


# ------------------------------------------------- yield-on-earlier-claim
def test_an_earlier_claim_wins_the_race():
    """Cycle 12's measurement, staged: the open-PR index lagged 8 seconds, so
    both sessions passed the guard.  created_at is the tie-break, and the
    later claim yields."""
    theirs = _pr(number=7, claim_only=True, draft=True, created_at=_ago(120))
    assert _v("corpus", [theirs], mine=_ago(112)) == G.YIELD


def test_the_earliest_claim_proceeds():
    theirs = _pr(number=7, claim_only=True, draft=True, created_at=_ago(100))
    assert _v("corpus", [theirs], mine=_ago(140)) == G.CLAIM


def test_the_tie_break_is_only_asked_when_this_session_holds_a_claim():
    """Without --mine there is nothing to compare, and inventing a
    comparison would make every firing yield to any open draft."""
    theirs = _pr(claim_only=True, draft=True, created_at=_ago(60))
    assert _v("corpus", [theirs]) == G.EXIT      # the lock, not a yield


# ---------------------------------------------------------- purchase loop
def test_any_open_purchase_pr_exits_regardless_of_age_or_ci():
    """Stricter by design: one purchase per flywheel cycle means the previous
    bill must MERGE first.  An ancient, idle, maintainer-awaiting purchase PR
    is the handoff working, not abandoned work."""
    old_idle = _pr(title="C3 purchase P8", created_at=_ago(86400),
                   newest_commit_at=_ago(86400))
    assert _v("purchase", [old_idle]) == G.EXIT


def test_a_stale_purchase_CLAIM_draft_is_still_closable():
    """The one exception, and only for a claim-only lock: a dead session's
    empty draft is litter under either loop's rules."""
    dead = _pr(title="C3 purchase (in progress)", claim_only=True, draft=True,
               created_at=_ago(G.CLAIM_LOCK_S + 1))
    assert _v("purchase", [dead]) == G.CLOSE_STALE


def test_a_clear_purchase_board_claims():
    assert _v("purchase", [_pr(title="C3 cycle 26",
                              checks_in_progress=True)]) == G.CLAIM


# -------------------------------------------------------- reads fail safe
def test_unreadable_inputs_exit_never_claim():
    """An errored call must never impersonate an answer.  For the purchase
    loop this is what protects one-purchase-per-cycle through an outage."""
    assert _v("corpus", None) == G.EXIT
    assert _v("purchase", None) == G.EXIT
    assert _v("corpus", ["not a dict"]) == G.EXIT
    assert G.verdict("corpus", [], "not-a-timestamp")[0] == G.EXIT
    assert _v("corpus", [_pr(claim_only=True, created_at="garbage")]) == G.EXIT


def test_malformed_json_on_the_cli_exits(tmp_path):
    """End-to-end through the CLI: the parse failure must reach the same
    fail-safe verdict, not a traceback the caller might read as 'no
    blocker'."""
    bad = tmp_path / "prs.json"
    bad.write_text("{not json")
    out = subprocess.run(
        [sys.executable, os.path.join(_ROOT, "tools", "loop_guard.py"),
         "--loop", "corpus", "--now", NOW, "--prs", str(bad)],
        capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert out.stdout.startswith("EXIT"), out.stdout


def test_the_cli_prints_one_verdict_line_with_its_subject(tmp_path):
    """The prompt binds to this line, so its shape is part of the contract:
    VERDICT (PR #n): reason."""
    prs = tmp_path / "prs.json"
    prs.write_text(json.dumps([_pr(number=42, checks_in_progress=True)]))
    out = subprocess.run(
        [sys.executable, os.path.join(_ROOT, "tools", "loop_guard.py"),
         "--loop", "corpus", "--now", NOW, "--prs", str(prs)],
        capture_output=True, text=True)
    line = out.stdout.strip()
    assert line.startswith("EXIT (PR #42): "), line
    assert "\n" not in line, "one verdict line, or the prompt cannot bind"


def test_the_tool_reaches_no_network():
    """The seam this tool exists to keep: the session FETCHES (it holds the
    GitHub tools), the tool DECIDES.  An import of a client here would make
    the guard untestable in exactly the way the prose version was."""
    import ast
    src = open(os.path.join(_ROOT, "tools", "loop_guard.py"),
               encoding="utf-8").read()
    imported = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            imported |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not (imported & {"urllib", "http", "requests", "socket",
                            "subprocess"}), sorted(imported)


@pytest.mark.parametrize("loop,title", [
    ("corpus", "C3 cycle (in progress)"),
    ("purchase", "C3 purchase (in progress)"),
])
def test_a_session_never_exits_on_its_own_claim(loop, title):
    """THIS TOOL'S OWN FIRST BUG, pinned -- ON BOTH LOOPS, which is the half
    the first pinning missed.  The first draft ran the in-flight guard and
    the tie-break in one pass, so a session that had just opened its claim
    hit the lock branch on ITS OWN draft and exited, leaving the lock behind
    as litter.  The two phases are separate questions: pre-claim asks 'is
    anyone else working?', post-claim asks 'did I win the race?'.

    SHIPPED CORPUS-ONLY, this test parameterized over one loop while the
    purchase branch still returned before the tie-break -- so it stayed
    green through 2026-07-27, when the first purchase firing after the tool
    landed measured EXIT on its own claim.  A tooth that exercises one of
    two symmetric callers is a tooth that certifies the caller it skips."""
    mine_at = _ago(60)
    my_own = _pr(title=title, number=99, claim_only=True, draft=True,
                 created_at=mine_at)
    v, _, _ = G.verdict(loop, [my_own], NOW, mine_at)
    assert v == G.CLAIM, f"the {loop} loop exited on its own claim draft"


@pytest.mark.parametrize("loop,title", [
    ("corpus", "C3 cycle (in progress)"),
    ("purchase", "C3 purchase (in progress)"),
])
def test_the_post_claim_tie_break_yields_to_an_earlier_claim_on_both_loops(
        loop, title):
    """The other side of the same split: the post-claim phase must still be
    a REAL tie-break on both loops, not a rubber stamp.  Pinning only the
    CLAIM direction would let 'return CLAIM' pass as the fix."""
    mine_at = _ago(112)
    theirs = _pr(title=title, number=7, claim_only=True, draft=True,
                 created_at=_ago(120))
    mine = _pr(title=title, number=8, claim_only=True, draft=True,
               created_at=mine_at)
    assert _v(loop, [mine, theirs], mine=mine_at) == G.YIELD


def test_the_purchase_guard_stays_strict_in_its_PRE_claim_phase():
    """The fix must not widen the purchase loop's in-flight rule, which is
    what protects one-purchase-per-flywheel-cycle.  WITHOUT --mine, an open
    purchase PR still exits regardless of age or CI state."""
    live = _pr(title="C3 purchase P10", created_at=_ago(30),
               newest_commit_at=_ago(30))
    assert _v("purchase", [live]) == G.EXIT
    claim = _pr(title="C3 purchase (in progress)", claim_only=True,
                draft=True, created_at=_ago(60))
    assert _v("purchase", [claim]) == G.EXIT


def test_the_purchase_post_claim_phase_fails_safe_on_an_unreadable_mine():
    """READS FAIL SAFE reaches the new branch too: an unreadable --mine is a
    transport-shaped input, and it must never resolve to CLAIM."""
    claim = _pr(title="C3 purchase (in progress)", claim_only=True,
                draft=True, created_at=_ago(60))
    assert _v("purchase", [claim], mine="garbage") == G.EXIT


# ------------------------------------------------- the prompts BIND to it
PROMPTS = os.path.join(_ROOT, "C3_PROMPTS.md")


def _prompts():
    with open(PROMPTS, encoding="utf-8") as fh:
        return fh.read()


def test_both_driver_prompts_run_the_guard_rather_than_reciting_it():
    """The migration's own tooth.  A tool nobody is told to run leaves the
    decision exactly where it was -- in a paragraph -- and this repo has
    already paid for that twice (the merge-event lore, the selection rule
    cycle 23 skipped).  Bound to the invocation, not to a mention."""
    text = _prompts()
    for loop in ("corpus", "purchase"):
        assert f"tools/loop_guard.py --loop {loop}" in text, (
            f"the {loop} prompt no longer runs the guard; its thresholds are "
            "back to being executed by a reader")
    assert "--mine" in text, (
        "the post-claim tie-break phase is unreachable from the prompts")


def test_the_prompts_do_not_re_specify_the_thresholds_they_delegated():
    """Two copies of a threshold is one copy that will drift.  The numbers
    live in the tool (FRESH_COMMIT_S / CLAIM_LOCK_S) and are pinned by the
    boundary teeth above; the prompt may NAME them in passing but must not
    restate the branch as an instruction to compute."""
    text = _prompts()
    for recital in ("exit immediately with a one-line summary if an open PR",
                    "carries commits less than 45 minutes old"):
        assert recital not in text, (
            f"the prompt re-specifies a delegated guard: {recital!r}")


# ------------------------------------------------- the health predicate
# MEASURED 2026-07-27: the watchdog's rule was "a claim-only draft under 2
# hours old is a cycle in flight and counts as activity".  Both drivers fire
# HOURLY and the watchdog every THREE hours, so a loop that claims and exits
# every firing always shows a fresh claim draft and reads HEALTHY forever.
# That is how #198's wedge survived four firings with the alarm channel
# reporting both loops fine.  A claim is a promise; a merge is a cycle.

@pytest.mark.parametrize("loop,title", [("corpus", "C3 cycle 40"),
                                        ("purchase", "C3 purchase P11")])
def test_claim_churn_is_not_health_on_either_loop(loop, title):
    """THE WEDGE SIGNATURE, and the reading that used to call it healthy."""
    fresh_claim = _pr(title=title, claim_only=True, draft=True,
                      created_at=_ago(600))
    status, _ = G.health(loop, [fresh_claim],
                         [_ago(G.COMPLETION_WINDOW_S + 1)], NOW)
    assert status == G.CLAIM_CHURN, status


@pytest.mark.parametrize("loop,title", [("corpus", "C3 cycle 40"),
                                        ("purchase", "C3 purchase P11")])
def test_a_recent_merge_is_health_on_either_loop(loop, title):
    """The other direction: a loop that FINISHES cycles is healthy even with
    a claim draft open, or the predicate would alarm on every live loop."""
    status, _ = G.health(loop, [_pr(title=title, claim_only=True, draft=True)],
                         [_ago(60)], NOW)
    assert status == G.HEALTHY, status


def test_real_open_work_reads_in_flight_not_churn():
    """A slow cycle is not a stuck loop: a substantive PR, or CI running on
    the claim, is work in progress and must not be alarmed."""
    old = [_ago(G.COMPLETION_WINDOW_S + 1)]
    substantive = _pr(title="C3 cycle 40", claim_only=False)
    assert G.health("corpus", [substantive], old, NOW)[0] == G.IN_FLIGHT
    running = _pr(title="C3 cycle 40", claim_only=True, draft=True,
                  checks_in_progress=True)
    assert G.health("corpus", [running], old, NOW)[0] == G.IN_FLIGHT


def test_an_empty_board_with_no_recent_merge_is_dead():
    assert G.health("corpus", [], [_ago(G.COMPLETION_WINDOW_S + 1)],
                    NOW)[0] == G.DEAD
    assert G.health("corpus", [], [], NOW)[0] == G.DEAD


def test_the_health_read_fails_LOUD_never_quiet():
    """An alarm channel that goes silent on a bad read is worse than one
    that cries once -- the inverse of the claim guard's fail-safe, and
    deliberately so."""
    for bad in (G.health("corpus", None, [], NOW),
                G.health("corpus", [], None, NOW),
                G.health("corpus", [], [], "not-a-timestamp")):
        assert bad[0] == G.DEAD, bad


def test_the_other_loops_merges_never_count():
    """Independent evaluation: a busy corpus loop must never mask a dead
    purchase loop.  The caller passes this loop's merges, and the PR filter
    is by this loop's title."""
    old = [_ago(G.COMPLETION_WINDOW_S + 1)]
    corpus_claim = _pr(title="C3 cycle 40", claim_only=True, draft=True)
    assert G.health("purchase", [corpus_claim], old, NOW)[0] == G.DEAD


def test_the_watchdog_derives_health_rather_than_eyeballing_activity():
    """The prompt must RUN the predicate, not restate it.  Bound to the
    verdict vocabulary the tool actually returns, so a prompt that keeps the
    words while dropping the call still fails."""
    with open(os.path.join(_ROOT, "C3_PROMPTS.md"), encoding="utf-8") as fh:
        text = fh.read()
    i = text.find("## WATCHDOG prompt")
    assert i >= 0
    wd = text[i:]
    assert "health(loop, prs, merged_at, now)" in wd, (
        "the watchdog no longer derives health; a fresh claim draft will "
        "read as activity again (the #198 blindness)")
    for verdict_word in (G.HEALTHY, G.IN_FLIGHT, G.CLAIM_CHURN, G.DEAD):
        assert verdict_word in wd, verdict_word
    assert "A CLAIM IS A PROMISE; A MERGE IS A CYCLE" in wd
