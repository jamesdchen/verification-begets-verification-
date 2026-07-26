"""The chain re-arms by the CRON, and both mechanisms that were supposed to
replace it are dead.  This file is the record of the second death.

WHAT WAS MEASURED, IN THREE ROUNDS.  The driver prompts once promised `the
merge event fires the next cycle`.  Cycle 06 measured the watchdog half false
(a watchdog-performed merge fired nothing).  On 2026-07-26 the other half went
too: `list_triggers` shows both driver Routines are pure hourly crons, so no
merge fires anything for anyone.  The fix shipped that day mechanized the
re-arm with a `fire_trigger` call after each self-merge, and this file pinned
those edges so they could not rot.

THE THIRD ROUND, AND WHY THIS FILE NOW SAYS THE OPPOSITE.  C3 cycle 23 ran the
mechanized edge for the first time on a real merge and the platform answered:

    fire_trigger: this routine was created via "http_api", not by an agent.
    Agents can only fire routines they created (via create_trigger).

All three C3 Routines read `created_via: http_api` in `list_triggers`, because
all three were created in the claude.ai/code/routines UI -- which is exactly
what gives fired sessions their repo attachment and their GitHub tools.  So the
mechanized re-arm was never available to any session on any edge; it was
authored, pinned, and dead on arrival, and one firing had to spend a call to
find out.  That is not weather and it is not a fault to drive to green: a
policy answer is a decided fact, and retrying it just re-learns it.

WHAT THE CHAIN ACTUALLY IS, then, and has been the whole time:

    driver           cron `36 * * * *`
    purchase driver  cron `3 * * * *`
    watchdog         cron `44 */3 * * *`

plus ONE session-side re-arm that does work: the watchdog running a corpus
driver cycle INLINE, which the cycle-06 patch introduced and which the
mechanization had demoted to a fallback.  It is promoted back to primary here.

The cost is bounded, and stating it is the point: a cycle that merges just
after its slot waits up to an hour for its successor.  Buying that hour back
means a platform change or Routines re-created by an agent -- and the second
would forfeit the repo attachment, which is the cycle-02 trap.  Either way it
is a MAINTAINER decision, never a session's improvisation, and no prompt may
quietly re-mechanize it.

WHAT THESE TEETH CAN AND CANNOT DO, said plainly (the Lean-side-text-checks
precedent): `fire_trigger` is an MCP tool pytest cannot reach, so the call
cannot be executed here -- which is exactly how the last version passed while
pinning a route that did not exist.  What IS checkable is that the prompts
carry the measurement, instruct against the dead call rather than toward it,
name the crons that actually carry the chain, and keep the one re-arm a
session can still perform.  Bound to instruction syntax rather than bare
mentions -- this repo's teeth have been bitten four times now by matching a
mention of the thing instead of the thing.
"""
import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

PROMPTS = os.path.join(_ROOT, "C3_PROMPTS.md")

DRIVER_HEAD = "## DRIVER prompt"
PURCHASE_HEAD = "## PURCHASE DRIVER prompt"
WATCHDOG_HEAD = "## WATCHDOG prompt"

#: The platform's own words, quoted once so every tooth below compares against
#: the same string the session actually read back.
REFUSAL = 'created via "http_api"'


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


def test_the_merge_event_lore_is_gone():
    """Round one's dead lore, still dead.  A prompt that keeps saying it
    teaches sessions to rely on a coupling that does not exist."""
    assert "the merge event fires the next cycle" not in _text(), (
        "the dead merge-event lore is back; no merge fires anything -- both "
        "driver Routines are pure crons (measured 2026-07-26)")


@pytest.mark.parametrize("head", [DRIVER_HEAD, PURCHASE_HEAD, WATCHDOG_HEAD])
def test_no_section_instructs_a_session_to_fire_a_routine(head):
    """Round two's dead lore.  Every `fire_trigger` mention that survives must
    be the MEASUREMENT (naming the refusal) and never an instruction to make
    the call.  This is the tooth the previous version had exactly backwards:
    it required >=4 fire sites, which is why authoring the dead route passed.

    The check is deliberately shaped as `mentions => refusal is nearby`
    rather than as a keyword ban, because the measurement has to stay
    quotable -- a prompt that simply deleted the word would let the next
    firing re-derive the failure from scratch, which is the whole cost this
    record exists to stop anyone paying twice."""
    section = _section(head)
    if "fire_trigger" not in section:
        return
    assert REFUSAL in section, (
        f"{head} mentions fire_trigger without the measurement that retired "
        f"it; a session reading only this section would make the dead call")
    for phrase in ("DO NOT CALL `fire_trigger`",
                   "DO NOT TRY TO FIRE",
                   "there is no mechanical re-arm to attempt"):
        if phrase in section:
            return
    raise AssertionError(
        f"{head} names the refusal but never tells the session not to make "
        f"the call -- a measurement without an instruction is a footnote")


def test_the_measurement_is_recorded_where_the_architecture_lives():
    """Not only in the prompt blocks: the architecture section is what a
    human reads when deciding whether to re-mechanize this, and it must carry
    both the refusal and the reason the Routines are UI-created (the repo
    attachment -- the cycle-02 trap that makes agent-created Routines the
    wrong fix)."""
    architecture = _text().split(DRIVER_HEAD)[0]
    assert REFUSAL in architecture, (
        "the architecture section does not record the fire_trigger refusal")
    assert "attachment" in architecture


def test_the_crons_that_actually_carry_the_chain_are_named():
    """With both mechanisms dead the schedules ARE the chain, so a session
    must be able to read them out of the prompts rather than guess."""
    text = _text()
    for cron, who in (("36 * * * *", "driver"),
                      ("3 * * * *", "purchase driver"),
                      ("44 */3 * * *", "watchdog")):
        assert cron in text, f"the {who} cron is not named in the prompts"


def test_watchdog_keeps_the_inline_cycle_as_the_one_live_rearm(watchdog):
    """The cycle-06 patch told the watchdog to run a driver cycle inline; the
    mechanization demoted it to a fallback behind a call that never worked.
    It is the ONLY re-arm a session can still perform, so it must be stated
    as the thing the watchdog does -- not as a contingency."""
    assert "run one corpus driver cycle yourself IN THIS SAME SESSION" in \
        watchdog, "the watchdog's inline re-arm is gone"
    assert "RE-ARM MECHANICALLY FIRST" not in watchdog, (
        "the watchdog still orders a mechanical re-arm first; that call is "
        "structurally unavailable and would demote the one route that works")


def test_the_purchase_to_corpus_edge_survives_as_a_written_handoff(purchase):
    """The flywheel edge is real even though its mechanization was not: a
    landed purchase un-gates a census signal and the corpus loop is its
    consumer.  With no fire available, the handoff is the SUMMARY and the PR
    body -- which is what the next corpus firing actually reads -- so losing
    the edge entirely would drop the coupling the two loops are built on."""
    assert "NAME THE UN-GATED SIGNAL" in purchase, (
        "the purchase->corpus handoff vanished with its dead mechanization")
    assert "Do NOT fire your own purchase Routine" not in purchase, (
        "a withdrawn instruction left its qualifier behind")


def test_the_prompts_agree_on_the_routine_names():
    """The names are matched against live list_triggers output when a human
    reads them, not against this repo -- so the one drift these teeth CAN
    catch is the prompts disagreeing with each other about what the Routines
    are called."""
    text = _text()
    assert text.count("C3 driver cycle") >= 2
    assert "C3 purchase driver" in text
