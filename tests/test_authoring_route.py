"""Teeth for the AUTHORING RIDE ROUTE (C3_PROMPTS.md -> the [lean-hammer] lane).

WHAT WENT WRONG THAT THIS CLOSES.  The authoring kind shipped complete --
queue, ride, verdicts, readout, all toothed -- and PLAN_FRAGMENT §3.1 rule 3
named it as the second route to the capability.  But no DRIVER prompt reached
it: the purchase prompt's yield clause ended in a bare YIELD, and the watchdog
merely NAMED the ride in its reporting vocabulary.  A machine with a working
exit that no firing walks is a machine that no-ops all night while reporting
correctly, which is precisely what was measured (PLAN_FRAGMENT §1).

WHY THESE TESTS ARE NOT PROSE-PINNING.  Grepping a prompt for a sentence
proves the sentence is there, not that following it does anything -- and this
repo has been bitten three times by claims that stopped tracking their
evidence (dead census terms, the false-zero purchase queue, the health verdict
that outran its measurement).  So every command the route names is EXECUTED
here: the script must exist, argparse must accept the exact flags quoted, the
marker quoted as the trigger must be the string the workflow actually branches
on, and the schema named must be the schema the committed queue declares.  A
prompt that names a command that does not exist, or a flag argparse would
reject, reds HERE -- in the container that edited the prompt -- rather than at
02:00 in a fired session with nobody reading.

The one genuinely textual assertion is the TITLE DISCIPLINE, and it is checked
as a PROPERTY (the authoring prefix must not collide with the purchase
in-flight guard's prefix) rather than as a quoted sentence.
"""
import json
import os
import re
import subprocess
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

PROMPTS = os.path.join(_ROOT, "C3_PROMPTS.md")
WORKFLOW = os.path.join(_ROOT, ".github", "workflows", "lean-hammer.yml")

# The two prompt section headings the route spans.  Sections are the file's
# own structure (## headings), so slicing on them is reading the document
# rather than guessing at it.
PURCHASE_HEAD = "## PURCHASE DRIVER prompt"
WATCHDOG_HEAD = "## WATCHDOG prompt"


def _sections():
    with open(PROMPTS, encoding="utf-8") as fh:
        text = fh.read()
    out = {}
    for head in (PURCHASE_HEAD, WATCHDOG_HEAD):
        i = text.find(head)
        assert i >= 0, f"{head} missing from C3_PROMPTS.md"
        j = text.find("\n## ", i + len(head))
        out[head] = text[i:j if j > 0 else len(text)]
    return out


@pytest.fixture(scope="module")
def sections():
    return _sections()


@pytest.fixture(scope="module")
def purchase(sections):
    return sections[PURCHASE_HEAD]


@pytest.fixture(scope="module")
def watchdog(sections):
    return sections[WATCHDOG_HEAD]


# --------------------------------------------------------------------------
# 1. The route is REACHED: the yield clause does not dead-end.
# --------------------------------------------------------------------------

def test_purchase_yield_clause_reaches_the_ride(purchase):
    """The lean-absent branch must route somewhere.  Before this shipped it
    ended at YIELD, which is a correct reading and a no-op session."""
    i = purchase.find("On ANY other verdict")
    assert i >= 0, "the non-lean-local branch of the additive-class rule is gone"
    branch = purchase[i:]
    assert "run/reflect_ride.py" in branch, (
        "the lean-absent branch yields without reaching the authoring ride -- "
        "this is the no-op PLAN_FRAGMENT §1 recorded")
    assert "bench/bench_hammer.py assemble" in branch
    assert "[lean-hammer]" in branch


# --------------------------------------------------------------------------
# 2. Every command the route names is REAL and accepts the flags quoted.
#    This is the half that a grep-only tooth cannot see.
# --------------------------------------------------------------------------

# (script, flags quoted in the prompt) -- extend when the route grows a step.
NAMED_COMMANDS = (
    ("run/reflect_ride.py", ("--verdicts", "--batch")),
    ("bench/bench_hammer.py", ("--candidates",)),
)


@pytest.mark.parametrize("script,flags", NAMED_COMMANDS)
def test_named_command_exists(script, flags):
    assert os.path.isfile(os.path.join(_ROOT, script)), (
        f"the prompt names {script}, which does not exist -- a fired session "
        f"would discover this with nobody reading")


def _help(argv):
    res = subprocess.run([sys.executable] + argv + ["--help"],
                         cwd=_ROOT, capture_output=True, text=True, timeout=120)
    assert res.returncode == 0, f"{argv} --help failed: {res.stderr[-800:]}"
    return res.stdout


def test_reflect_ride_accepts_the_quoted_flags(purchase):
    out = _help(["run/reflect_ride.py"])
    for flag in ("--verdicts", "--batch"):
        assert flag in out, f"run/reflect_ride.py rejects {flag}"
        assert flag in purchase, f"the prompt stopped quoting {flag}"


def test_bench_assemble_accepts_the_candidates_flag(purchase):
    out = _help(["bench/bench_hammer.py", "assemble"])
    assert "--candidates" in out, "bench_hammer assemble rejects --candidates"
    assert "--candidates results/reflect_candidates.json" in purchase


def test_the_paths_the_prompt_quotes_are_the_paths_that_exist(purchase):
    """Every results/*.json the route reads or writes must be a real path.
    A typo'd artifact name is a silent no-op, not an error."""
    quoted = set(re.findall(r"results/[A-Za-z0-9_]+\.json", purchase))
    assert "results/reflect_candidates.json" in quoted
    assert "results/hammer_verdicts.json" in quoted
    for rel in quoted:
        assert os.path.isfile(os.path.join(_ROOT, rel)), (
            f"the purchase prompt names {rel}, which is not committed")


def test_the_schema_named_is_the_schema_declared(purchase):
    """The prompt tells the session which schema to write.  If the queue's
    own declared schema moves, the instruction is stale."""
    with open(os.path.join(_ROOT, "results", "reflect_candidates.json"),
              encoding="utf-8") as fh:
        declared = json.load(fh)["schema"]
    assert declared in purchase, (
        f"the queue declares schema {declared!r}, which the prompt no longer "
        f"names -- a session would author against a schema that moved")


# --------------------------------------------------------------------------
# 3. The marker quoted as the trigger IS the trigger.
# --------------------------------------------------------------------------

def test_the_quoted_marker_is_the_workflows_actual_trigger(purchase):
    """The prompt says the literal marker IS the trigger.  Verify against the
    workflow's own branch condition, not against a memory of it."""
    with open(WORKFLOW, encoding="utf-8") as fh:
        wf = fh.read()
    m = re.search(r"contains\(github\.event\.head_commit\.message,\s*'([^']+)'\)", wf)
    assert m, "lean-hammer.yml no longer branches on a head-commit marker"
    marker = m.group(1)
    assert marker == "[lean-hammer]", marker
    # Bind the marker to the COMMIT INSTRUCTION, not to the section.  The
    # lane's name appears in this section as prose ("the [lean-hammer] lane
    # already elaborates..."), so a bare `marker in purchase` passes even when
    # the string a session is told to COMMIT has drifted -- caught by mutating
    # only the instruction and watching this tooth stay green.
    instr = re.search(
        r"commit the batch with the literal marker `([^`]+)` in the commit message",
        purchase)
    assert instr, ("the prompt no longer tells sessions which marker to commit; "
                   "without it the batch lands and the lane never fires")
    assert instr.group(1) == marker, (
        f"the workflow triggers on {marker!r} but the prompt tells sessions to "
        f"commit {instr.group(1)!r}, so the ride would never fire")


def test_the_entrypoint_the_lane_runs_is_the_one_the_route_feeds():
    """H-H1.3's entry predicate: the lane must still invoke the ride
    entrypoint.  If the workflow were repointed, the queue would be dead
    weight and the prompt would be instructing a session to fill it."""
    with open(WORKFLOW, encoding="utf-8") as fh:
        wf = fh.read()
    assert "run/hammer_ride.py" in wf
    assert "bench/bench_hammer.py consume" in wf


# --------------------------------------------------------------------------
# 4. Title discipline, checked as a property of the guards.
# --------------------------------------------------------------------------

AUTHORING_TITLE = "C3 authoring"
PURCHASE_TITLE = "C3 purchase"


def test_authoring_title_cannot_trip_the_purchase_in_flight_guard(purchase):
    """The in-flight guard matches purchase PRs by TITLE PREFIX.  An authoring
    ride buys nothing, so it must not be visible to a guard that enforces
    one-purchase-per-flywheel-cycle -- otherwise a ride consumes the slot."""
    assert not AUTHORING_TITLE.startswith(PURCHASE_TITLE)
    assert not PURCHASE_TITLE.startswith(AUTHORING_TITLE)
    assert f"`{AUTHORING_TITLE} ...`" in purchase, (
        "the prompt no longer fixes the authoring PR title, so a session may "
        "pick one that trips the in-flight guard")


def test_watchdog_knows_the_fourth_pr_kind(watchdog):
    """A PR kind the watchdog cannot name is a PR kind whose red nobody
    reports -- the watchdog is the sole alarm channel."""
    assert AUTHORING_TITLE in watchdog
    assert "NEVER MERGE THE LANE'S OWN COMMIT-BACK TIP" in watchdog


def test_watchdog_will_not_read_a_riding_purchase_loop_as_dead(watchdog):
    """The purchase loop yielding-and-riding is the loop WORKING.  Reading it
    as dead spawns a duplicate driver that yields identically (cycle-06)."""
    i = watchdog.find("NOT DEAD WHILE IT IS RIDING")
    assert i >= 0, ("the watchdog can still call a correctly-riding purchase "
                    "loop dead, which spawns a duplicate rescue cycle")
    clause = watchdog[i:i + 900]
    assert "BLOCKED" in clause and "NO rescue cycle" in clause


# --------------------------------------------------------------------------
# 5. The BOUND, mechanized rather than promised.
#    The prompt claims the candidate queue has no write path to the slice.
#    Check the code, not the claim.
# --------------------------------------------------------------------------

RIDE_MODULES = ("run/reflect_ride.py", "bench/bench_hammer.py")


@pytest.mark.parametrize("rel", RIDE_MODULES)
def test_no_write_path_from_the_candidate_queue_to_the_slice(rel):
    """`tools/FgReflect.lean` has no write path from the candidate queue: a
    passed candidate is a PROPOSAL, and adopting it is an ordinary authored
    edit.  Mechanized by refusing any write-mode open of the slice in the
    modules the ride runs."""
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as fh:
        src = fh.read()
    for m in re.finditer(r"open\(([^)]*)\)", src):
        args = m.group(1)
        if "FgReflect" not in args:
            continue
        assert not re.search(r"""["'][wa]\+?["']""", args), (
            f"{rel} opens tools/FgReflect.lean for writing -- the candidate "
            f"queue must never edit the slice")
    assert ".write_text(" not in src or "FgReflect" not in src.split(
        ".write_text(")[0][-200:], f"{rel} may write the slice via write_text"


def test_the_honest_bound_survives_in_the_prompt(purchase):
    """H-H1.3's mandatory honesty clause: elaboration is evidence, never a
    done-predicate.  A route that drops this is a route that will report a
    ride as a proof."""
    i = purchase.find("THEN TAKE THE AUTHORING RIDE")
    assert i >= 0
    clause = purchase[i:]
    assert "done-predicate" in clause, (
        "the route dropped the clause that keeps an elaboration from being "
        "reported as a proof")
    assert "PROPOSAL" in clause
    assert "NEVER edits tools/FgReflect.lean" in clause
