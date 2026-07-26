"""The chain re-arms by a TOOL CALL, not by lore, and the lore is dead.

WHAT WAS MEASURED.  The driver prompts promised `the merge event fires the
next cycle`.  Cycle 06 measured the watchdog half false (a watchdog-performed
merge fired nothing) and patched it with prose telling the watchdog to run a
whole driver cycle inline.  On 2026-07-26 the other half was measured too:
`list_triggers` shows BOTH driver Routines are pure hourly crons -- there is
no merge-event trigger for anyone, and every chained cycle has been silently
waiting for its next cron slot since the loops were built.  The backstop was
carrying the chain, and nothing said so.

THE MECHANIZATION.  The claude-code-remote meta server these sessions carry
has `fire_trigger`.  One call after a merge replaces both the dead lore and
the inline-rescue prose:

  * DRIVER self-merge, ready work remaining  -> fire `C3 driver cycle`
  * PURCHASE self-merge (conforming bill)    -> fire `C3 driver cycle`
    (the flywheel edge: the purchase just un-gated a census signal and the
    corpus loop is its consumer; the purchase Routine is deliberately NOT
    fired -- the next purchase should be priced after the corpus measures
    with the grown fragment, which the hourly cron already provides)
  * WATCHDOG rearm (both loops)              -> fire the owning Routine,
    inline cycle only as the fallback when the fire fails

Every edge is ATTEMPT-NEVER-DEPEND with the cron as backstop, and every edge
carries the firing-is-not-creating carve-out, because the prompts' standing
`Do NOT create triggers` rule would otherwise be over-read into forbidding
the fire -- exactly the over-reading the subscribe_pr_activity carve-out
already had to prevent once.

WHAT THESE TEETH CAN AND CANNOT DO, said plainly (the Lean-side-text-checks
precedent): `fire_trigger` is an MCP tool on a server pytest cannot reach, so
the CALL cannot be executed here.  What is checkable is the ROUTE: each edge
exists as an instruction bound to its site, the dead lore is gone, the
carve-out and the fallback survive, and the Routine names the prompts cite
are the names the edges agree on.  Bound to instruction syntax rather than
bare mentions -- this repo's teeth have been bitten three times by matching a
mention of the thing instead of the thing.
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


def _section(head):
    with open(PROMPTS, encoding="utf-8") as fh:
        text = fh.read()
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
    """`the merge event fires the next cycle` was false for every actor: both
    Routines are pure crons.  A prompt that keeps saying it teaches sessions
    to rely on a coupling that does not exist."""
    with open(PROMPTS, encoding="utf-8") as fh:
        text = fh.read()
    assert "the merge event fires the next cycle" not in text, (
        "the dead merge-event lore is back; no merge fires anything -- both "
        "driver Routines are pure hourly crons (measured 2026-07-26)")


def test_driver_self_merge_rearms_by_fire_trigger(driver):
    # Anchor on the re-arm instruction itself, not a guessed window after the
    # first SELF-MERGE mention -- the section mentions SELF-MERGE several
    # times before the rule.
    i = driver.find("RE-ARM THE CHAIN MECHANICALLY")
    assert i >= 0, (
        "the driver's self-merge does not re-arm the chain; the next cycle "
        "waits for the cron, which is the dead time this edge removes")
    clause = driver[i:i + 1400]
    assert "fire_trigger" in clause
    assert "C3 driver cycle" in clause, "the edge does not name its Routine"


def test_purchase_self_merge_fires_the_CORPUS_driver_not_its_own(purchase):
    """The flywheel edge, with its direction pinned: purchase -> corpus.
    Firing the purchase Routine here would chain purchase->purchase, buying
    twice from one price list -- the exact thing one-per-flywheel-cycle
    exists to prevent."""
    i = purchase.find("AFTER A SELF-MERGE LANDS, FIRE THE CORPUS DRIVER")
    assert i >= 0, "the purchase->corpus edge is gone"
    clause = purchase[i:i + 1400]
    assert "fire_trigger" in clause and "C3 driver cycle" in clause
    assert "Do NOT fire your own purchase Routine" in clause, (
        "nothing stops the edge from becoming purchase->purchase chaining")


def test_watchdog_rearm_fires_first_and_keeps_the_inline_fallback(watchdog):
    """The cycle-06 patch told the watchdog to re-implement a driver cycle
    inline; the fire is strictly better (full driver context in a fresh
    session) but the inline cycle must SURVIVE as the fallback -- fire_trigger
    rides a server some fired sessions lack, and a rearm rule with no
    fallback is a chain that dies with the server."""
    for routine in ("C3 driver cycle", "C3 purchase driver"):
        i = watchdog.find("RE-ARM MECHANICALLY FIRST")
        assert i >= 0, "the watchdog rearm no longer fires first"
    assert watchdog.count("RE-ARM MECHANICALLY FIRST") == 2, (
        "one loop's rearm was mechanized and the other's was not -- an "
        "asymmetry is how the last three wedges started")
    assert "fall back" in watchdog or "falls back" in watchdog or \
        "only on a failed fire" in watchdog.lower() or \
        "ONLY IF the fire fails" in watchdog, "the inline fallback is gone"


def test_every_edge_carries_the_carve_out_and_never_depends():
    """Two properties per edge, and they are the load-bearing ones.  The
    carve-out: the standing `Do NOT create triggers` rule must not be
    over-read into forbidding a fire (the subscribe_pr_activity lesson).
    Attempt-never-depend: the cron backstop is what actually carried the
    chain until now, and it must stay the backstop."""
    with open(PROMPTS, encoding="utf-8") as fh:
        text = fh.read()
    n_edges = text.count("fire_trigger")
    assert n_edges >= 4, f"expected >=4 chain edges, found {n_edges}"
    carve = (text.count("FIRING AN EXISTING ROUTINE IS NOT CREATING ONE")
             + text.count("FIRING IS NOT CREATING")
             + text.count("firing an existing Routine is NOT creating one")
             + text.count("firing-is-not-creating"))
    assert carve >= 3, (
        f"only {carve} carve-outs for {n_edges} fire sites -- an edge without "
        f"one will be skipped by a session obeying the no-triggers rule")
    assert ("never depend" in text.lower() or "ATTEMPT, NEVER DEPEND" in text), (
        "no edge states attempt-never-depend; a session that treats the fire "
        "as required will report a healthy chain as broken when the meta "
        "server is absent")


def test_the_two_prompts_agree_on_the_routine_names():
    """The names are matched against live list_triggers output at fire time,
    not against this repo -- so the one drift these teeth CAN catch is the
    prompts disagreeing with each other about what the Routines are called."""
    with open(PROMPTS, encoding="utf-8") as fh:
        text = fh.read()
    assert text.count("C3 driver cycle") >= 3
    assert "C3 purchase driver" in text
