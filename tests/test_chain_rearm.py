"""The chain is the CRON.  Three mechanisms were tried; all three are dead.

WHAT WAS MEASURED, twice.  First (2026-07-26, morning): the prompts promised
`the merge event fires the next cycle`, and `list_triggers` showed BOTH
driver Routines are pure hourly crons -- no merge fired anything, ever; the
cron backstop had been silently carrying the chain.  The replacement edges
called `fire_trigger`.  Second (2026-07-26T23:11Z): the FIRST live attempt at
that call was refused by the platform itself -- `Agents can only fire
routines they created (via create_trigger)` -- and both driver Routines are
UI-created (`created_via: http_api`), so the fire edge never worked once for
any session either.  The two off-cron cycle starts that evening were the
maintainer firing by hand, which a session-side reading mistook for the
mechanism working: a lesson in attributing platform state to your own
machinery.

THE THIRD DEATH, and the one that cost the maintainer directly (measured
2026-07-27).  The replacement for `fire_trigger` was a session-created
chain one-shot: `create_trigger`, minutes out, `create_new_session_on_fire`,
environment inherited.  It fired -- and every session it fired woke with NO
REPO ATTACHED, because `create_trigger` has no `sources` parameter: the
UI-created Routines carry `sources`/`outcomes` in their session_context and
meta_mcp-created triggers do not.  Each fired session therefore had to call
`add_repo` / `register_repo_root`, which PROMPTS THE MAINTAINER.  Five
one-shots, five prompt storms, in under two hours.  That is the cycle-02
stranding in a new costume, and the PR that shipped it claimed the
opposite in writing ("environment inheritance is precisely what the
retired stranded design lacked") -- a claim about a platform behaviour
that was never measured before it was written down.

SO THE CHAIN IS THE CRON, and it always was: the hourly Routines have
carried every cycle since the loops were built.  Sessions create no
triggers and fire none; the watchdog's INLINE cycle is the only working
re-arm and is primary rather than a fallback; and the derived
NEXT-SELECTION line, not a trigger payload, is what carries routing state
across firings.  Buying back sub-hour dead time needs a platform change or
maintainer-created Routines -- a MAINTAINER decision, never a session's.

WHAT THESE TEETH CAN AND CANNOT DO (unchanged): the meta server is not
reachable from pytest, so the CALLS cannot be executed here.  Checkable is
the ROUTE: each edge exists bound to its site and instructs create_trigger,
`fire_trigger` survives in the text ONLY inside the measured-refusal
telling, the carve-out and fallback survive, and the prompts agree on the
Routine names.  Bound to instruction syntax rather than bare mentions --
this repo's teeth have been bitten four times by matching a mention of the
thing instead of the thing.
"""
import os
import re
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

PROMPTS = os.path.join(_ROOT, "C3_PROMPTS.md")

DRIVER_HEAD = "## DRIVER prompt"
PURCHASE_HEAD = "## PURCHASE DRIVER prompt"
WATCHDOG_HEAD = "## WATCHDOG prompt"

#: The platform's own refusal text, quoted -- the measurement the whole
#: mechanism change rests on.  If this leaves the prompts, the next session
#: to read them has no reason not to reinstate the fire edge.
PLATFORM_REFUSAL = "Agents can only fire routines they created"


def _text():
    with open(PROMPTS, encoding="utf-8") as fh:
        return fh.read()


def _section(head):
    text = _text()
    i = text.find(head)
    assert i >= 0, f"{head} missing"
    j = text.find("\n## ", i + len(head))
    return text[i:j if j > 0 else len(text)]


@pytest.fixture(scope="module")
def driver():
    return _section(DRIVER_HEAD)


@pytest.fixture(scope="module")
def purchase():
    return _section(PURCHASE_HEAD)


@pytest.fixture(scope="module")
def watchdog():
    return _section(WATCHDOG_HEAD)


def test_the_dead_lore_is_gone():
    """`the merge event fires the next cycle` was false for every actor; a
    prompt that keeps saying it teaches sessions to rely on a coupling that
    does not exist."""
    assert "the merge event fires the next cycle" not in _text(), (
        "the dead merge-event lore is back; no merge fires anything -- both "
        "driver Routines are pure hourly crons (measured 2026-07-26)")


def test_fire_trigger_is_never_the_instructed_mechanism():
    """EXECUTED over every occurrence, not a style preference: the platform
    refuses agent fires of UI-created Routines, so any site that instructs
    `fire_trigger` is an edge that fails on every firing while reading as
    mechanized.  The name may survive only inside the measured-refusal
    telling -- history that explains WHY the mechanism is create_trigger."""
    text = _text()
    sites = [m.start() for m in re.finditer(r"fire_trigger", text)]
    assert sites, ("fire_trigger vanished entirely -- with it goes the "
                   "measured reason the mechanism is create_trigger, and "
                   "the fire edge will be reinvented")
    for i in sites:
        window = text[max(0, i - 600):i + 600]
        assert ("NOT THE MECHANISM" in window
                or PLATFORM_REFUSAL in window
                or "NOT `fire_trigger`" in window
                or "measured `fire_trigger` refusal" in window
                or "platform-refused" in window
                or "do NOT call fire_trigger" in window), (
            f"fire_trigger at offset {i} is not inside the measured-refusal "
            "telling; it reads as an instruction, and the platform refuses "
            "that call for every session")


def test_the_platform_refusal_is_quoted_verbatim():
    assert PLATFORM_REFUSAL in _text(), (
        "the measured platform refusal is gone; without it the create_trigger "
        "mechanism reads as a style choice someone may 'simplify' back to a "
        "fire")


def test_no_prompt_instructs_a_session_to_create_a_trigger():
    """THE TOOTH THAT COST THE MAINTAINER.  A session-created one-shot fires
    a session with no repo attachment, which prompts a human before it can
    do anything -- so an instruction to create one is worse than no chain at
    all.  Both mentions of create_trigger must sit inside the measured
    refusal, never in an instruction."""
    text = _text()
    for m in re.finditer(r"create_trigger", text):
        window = text[max(0, m.start() - 500):m.start() + 500]
        assert ("no `sources` parameter" in window
                or "measured HARMFUL" in window
                or "withdrawn the same night" in window), (
            "create_trigger reads as an instruction; the session it fires "
            "wakes with no checkout and prompts the maintainer via add_repo")


def test_the_add_repo_measurement_is_quoted():
    """Keep the cost quotable, or the next session reinvents the one-shot:
    the failure is invisible from inside the repo (the fired session looks
    like it works -- after a human answers a prompt)."""
    text = _text()
    assert "add_repo" in text and "sources" in text, (
        "the repo-attachment measurement is gone; nothing stops the chain "
        "one-shot from being reinvented")


def test_the_no_triggers_rule_carries_no_exception():
    """The carve-out was tried and withdrawn in one night.  A rule with an
    exception nobody can safely take is a rule that will be re-read as
    permission."""
    text = _text()
    i = text.find("Do NOT create triggers or one-shots")
    assert i >= 0, "the no-triggers rule is gone"
    clause = text[i:i + 400]
    assert "NO EXCEPTIONS" in clause, clause[:200]
    assert "EXCEPT the chain one-shot" not in text


def test_both_watchdog_rearms_are_the_inline_cycle():
    """The inline cycle is the ONLY re-arm that works, so it is primary in
    BOTH clauses.  Asymmetry between the two loops is how the last three
    wedges started."""
    wd = _section(WATCHDOG_HEAD)
    assert wd.count("RE-ARM BY RUNNING THE CYCLE YOURSELF") == 2, (
        "a watchdog rearm is back to a mechanism that does not work")
    assert "run one corpus driver cycle" in wd
    assert "run one purchase driver cycle" in wd
    assert "RE-ARM MECHANICALLY FIRST" not in wd


def test_the_purchase_to_corpus_edge_survives_as_a_WRITTEN_handoff():
    """Losing the mechanized edge must not lose the coupling: the purchase
    names the un-gated signal where the next corpus firing actually reads
    it."""
    purchase = _section(PURCHASE_HEAD)
    i = purchase.find("HAND OFF TO THE CORPUS DRIVER IN WRITING")
    assert i >= 0, "the flywheel handoff is gone entirely"
    assert "create no trigger" in purchase[i:i + 400]


def test_the_prompts_still_name_both_routines():
    """The names used to appear once per chain edge; with the edges gone the
    count is down to the pointer text and the watchdog's per-loop report,
    which is the only place a name still has to be right -- the watchdog
    reads `list_triggers` to health-check each loop."""
    text = _text()
    assert "C3 driver cycle" in text
    assert "C3 purchase driver" in text


def test_the_watchdog_may_not_edit_or_merge_another_loops_work():
    """MEASURED 2026-07-27: the watchdog rebased a purchase branch, resolved
    a conflict in it, and merged the purchase.  Each step was defensible
    under drive-to-green; the aggregate is a third driver with no in-flight
    guard, and the alarm channel doing the work stops being an alarm
    channel.  The scope fence is bound to its own clause."""
    wd = _section(WATCHDOG_HEAD)
    i = wd.find("SCOPE, and it is narrow ON PURPOSE")
    assert i >= 0, "the watchdog's scope fence is gone"
    clause = wd[i:i + 1200]
    assert "YOU MAY NOT" in clause
    for forbidden in ("another session's branch", "merge a PURCHASE PR"):
        assert forbidden in clause, forbidden
    assert "belongs to ITS OWN loop" in clause, (
        "nothing says who DOES own a stuck PR; a fence with no owner named "
        "is a fence sessions route around")
