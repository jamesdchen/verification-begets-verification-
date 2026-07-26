"""The chain re-arms by a TOOL CALL, not by lore -- and the tool changed once.

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

THE MECHANISM THAT IS PERMITTED: sessions may CREATE triggers, so each edge
now creates ONE chain one-shot -- `create_trigger`, `run_once_at` minutes
out, `create_new_session_on_fire: true`, environment INHERITED from the
creating session (the retired design's cycle-02 stranding was one-shots
WITHOUT an environment, which is exactly what the standing no-triggers rule
fences; an environment-inheriting one-shot is the sanctioned exception, and
the rule's own text now says so).  Every edge stays ATTEMPT-NEVER-DEPEND
with the cron as backstop.

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
        window = text[max(0, i - 400):i + 400]
        assert ("NOT THE MECHANISM" in window
                or PLATFORM_REFUSAL in window
                or "NOT `fire_trigger`" in window
                or "measured `fire_trigger` refusal" in window), (
            f"fire_trigger at offset {i} is not inside the measured-refusal "
            "telling; it reads as an instruction, and the platform refuses "
            "that call for every session")


def test_the_platform_refusal_is_quoted_verbatim():
    assert PLATFORM_REFUSAL in _text(), (
        "the measured platform refusal is gone; without it the create_trigger "
        "mechanism reads as a style choice someone may 'simplify' back to a "
        "fire")


def _one_shot_clause(clause, site):
    """The properties that make a chain one-shot WORK, asserted per edge:
    the permitted verb, the fresh-session mode, and the schedule.  A near
    miss on any of them is a chain that silently dies."""
    assert "create_trigger" in clause, f"{site}: no create_trigger edge"
    assert "create_new_session_on_fire" in clause, (
        f"{site}: the one-shot does not fire a fresh session; it would "
        "deliver into a dead session's transcript")
    assert "run_once_at" in clause, f"{site}: no one-shot schedule"


def test_driver_self_merge_creates_the_chain_one_shot(driver):
    i = driver.find("RE-ARM THE CHAIN MECHANICALLY")
    assert i >= 0, (
        "the driver's self-merge does not re-arm the chain; the next cycle "
        "waits for the cron, which is the dead time this edge removes")
    clause = driver[i:i + 2100]
    _one_shot_clause(clause, "driver edge")
    assert "C3 driver cycle (chain one-shot)" in clause, (
        "the one-shot has no distinguishing name; collisions with the cron "
        "become indistinguishable in list_triggers")
    assert "OMIT `environment_id`" in clause, (
        "the environment-inheritance instruction is gone -- an "
        "environment-less one-shot is the cycle-02 stranding, the exact "
        "thing the no-triggers rule fences")


def test_purchase_self_merge_targets_the_CORPUS_driver_not_its_own(purchase):
    """The flywheel edge, with its direction pinned: purchase -> corpus.
    A one-shot for the purchase Routine here would chain purchase->purchase,
    buying twice from one price list."""
    i = purchase.find("AFTER A SELF-MERGE LANDS, FIRE THE CORPUS DRIVER")
    assert i >= 0, "the purchase->corpus edge is gone"
    clause = purchase[i:i + 2100]
    _one_shot_clause(clause, "purchase edge")
    assert "C3 driver cycle (chain one-shot)" in clause, (
        "the edge does not name its target's one-shot")
    assert "Do NOT create a one-shot for your own purchase Routine" in clause, (
        "nothing stops the edge from becoming purchase->purchase chaining")


def test_watchdog_rearm_fires_first_and_keeps_the_inline_fallback(watchdog):
    """Both loops' rearms must be mechanized (asymmetry is how the last
    three wedges started), and the inline cycle must SURVIVE as the
    fallback -- the meta server is absent in some fired sessions, and a
    rearm rule with no fallback is a chain that dies with the server."""
    sites = [m.start() for m in
             re.finditer("RE-ARM MECHANICALLY FIRST", watchdog)]
    assert len(sites) == 2, (
        f"expected both loops' rearms mechanized, found {len(sites)}")
    for i in sites:
        _one_shot_clause(watchdog[i:i + 1200], f"watchdog rearm @{i}")
    assert "run one corpus driver cycle yourself" in watchdog
    assert "run one purchase driver cycle yourself" in watchdog


def test_every_edge_carries_the_carve_out_and_never_depends():
    """The no-triggers rule must name the chain one-shot as its sanctioned
    exception at every edge, or a session obeying the rule skips the edge --
    the same over-reading the subscribe_pr_activity carve-out had to
    prevent.  And the cron must stay the backstop: a session that treats
    the create as required will report a healthy chain as broken when the
    meta server is absent."""
    text = _text()
    carve = len(re.findall(r"sanctioned[ -]exception", text, re.I))
    edges = len(re.findall(r"create_trigger", text))
    assert edges >= 4, f"expected >=4 chain edges, found {edges}"
    assert carve >= 4, (
        f"only {carve} sanctioned-exception carve-outs for {edges} "
        "create_trigger sites")
    assert ("never depend" in text.lower()
            or "ATTEMPT, NEVER DEPEND" in text), "attempt-never-depend is gone"
    # the rule itself must carry the exception, not just the edges
    i = text.find("Do NOT create triggers or one-shots")
    assert i >= 0
    assert "EXCEPT the chain one-shot" in text[i:i + 300], (
        "the no-triggers rule does not name its exception; the watchdog "
        "obeying it verbatim will skip its own rearm rule")


def test_the_prompts_agree_on_the_routine_names():
    """The names are matched against live list_triggers output at fire time;
    the one drift these teeth CAN catch is the prompts disagreeing with each
    other about what the Routines are called."""
    text = _text()
    assert text.count("C3 driver cycle") >= 3
    assert "C3 purchase driver" in text
