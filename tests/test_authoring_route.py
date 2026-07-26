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
# 3b. MARKER DISCIPLINE.  The marker is machinery, not a word.
#
# Measured the hard way: the commit that SHIPPED this route fired the lane,
# because its message described the instruction ("commit under the literal
# [lean-hammer] marker") and the workflow matches that string ANYWHERE in the
# head commit message.  The blast radius is real -- the lane commits verdicts
# back with GITHUB_TOKEN, producing a zero-check tip on the branch that the
# self-merge rule must then refuse.
#
# The fence cannot be the workflow: `.github/` is trust-surface PROTECTED, so
# narrowing the match there would turn every such fix into a maintainer-merged
# ceremony.  So the fence is the TEXT: exactly one bracketed occurrence in the
# prompts -- the commit instruction itself -- and none at all in the artifacts
# a driver is told to quote.
# --------------------------------------------------------------------------

MARKER = "[lean-hammer]"


def test_prompts_carry_the_marker_exactly_once(sections):
    """One bracketed occurrence, and it must be the commit instruction.  Every
    other mention is a copy hazard: a session quoting it into a commit message
    fires a ride it did not intend."""
    with open(PROMPTS, encoding="utf-8") as fh:
        whole = fh.read()
    n = whole.count(MARKER)
    assert n == 1, (
        f"C3_PROMPTS.md carries {n} bracketed markers; exactly one (the commit "
        f"instruction) is allowed, because the bracketed form is a TRIGGER and "
        f"every other mention invites a session to fire the lane by quoting it")
    assert re.search(
        r"commit the batch with the literal marker `\[lean-hammer\]` in the commit message",
        whole), "the single bracketed marker is not the commit instruction"


QUOTED_ARTIFACTS = ("results/supply_status.json", "results/purchase_frontier.json")


@pytest.mark.parametrize("rel", QUOTED_ARTIFACTS)
def test_quotable_artifacts_carry_no_bracketed_marker(rel):
    """The watchdog is told to quote the supply verdict and the exits it names.
    A bracketed marker inside a string a driver is INSTRUCTED to reproduce is a
    trigger with a delivery mechanism."""
    path = os.path.join(_ROOT, rel)
    if not os.path.isfile(path):
        pytest.skip(f"{rel} not committed")
    with open(path, encoding="utf-8") as fh:
        body = fh.read()
    assert MARKER not in body, (
        f"{rel} carries the bracketed lane marker; a session quoting this "
        f"artifact into a commit message would fire the lane")


# --------------------------------------------------------------------------
# 3c. THE COLD START AND THE SPLICE.  Both measured on 2026-07-26, when the
# first firing to reach this route consumed an empty queue and stopped --
# correctly, per the instruction as written, which asked it to derive the next
# candidate from a PREVIOUS round that had never happened.  An instruction
# that requires a prior ride to start a ride can never start one.
#
# The second defect is worse because it would have survived the first fix: a
# candidate is APPENDED after the committed slice, so it cannot add a
# constructor to `Tm` -- which is precisely what all three open rows need.  A
# session told only to "author the next round" would write an impossible
# candidate and read the failure as the row being hard.  The route must say
# PARALLEL TOWER.
# --------------------------------------------------------------------------

def test_an_open_finished_authoring_pr_is_CONSUMED_not_deferred_to(purchase):
    """THE WEDGE THIS CLOSES, measured on 2026-07-26.

    The authoring channel is a single file, so an open `C3 authoring` PR owns
    it.  Nothing in the route closed the slot: the driver deferred to the open
    PR, and the watchdog -- which correctly refuses to merge the lane's
    zero-check commit-back tip -- called consumption the driver's job.  Every
    actor reasoned correctly and the ride ran exactly ONCE, then stalled for
    three firings.  A defect that survives every participant behaving
    correctly is a defect in the protocol, not in anyone's judgement.

    So the route must name CONSUME as the action and reserve deferral for the
    one case that warrants it: a lane still running."""
    i = purchase.find("(1) CONSUME FIRST")
    assert i >= 0, "the consume step is gone"
    clause = purchase[i:purchase.find("(2) THEN AUTHOR", i)]
    assert "SINGLE-SLOT" in clause, (
        "the route does not say the channel is single-slot, so nothing "
        "explains why a second round cannot simply be authored beside it")
    assert "CONSUME IT IN THIS SESSION" in clause, (
        "the route still permits deferring to a FINISHED ride, which is the "
        "2026-07-26 wedge verbatim")
    # deferral must survive for the one case it fits, and no other
    assert "NOT finished" in clause and "ONE honest defer" in clause


def test_the_wedge_clause_names_its_own_evidence(purchase):
    """A protocol rule with no evidence behind it is the prose this repo keeps
    having to re-derive.  The clause cites the PR and the outcome, so the next
    reader can check it rather than trust it."""
    i = purchase.find("(1) CONSUME FIRST")
    clause = purchase[i:purchase.find("(2) THEN AUTHOR", i)]
    assert "#129" in clause and "2026-07-26" in clause


def test_the_cold_start_is_not_a_no_op(purchase):
    """An empty queue must route to the SEED rule, not to a stop."""
    i = purchase.find("THEN TAKE THE AUTHORING RIDE")
    clause = purchase[i:]
    assert "COLD START" in clause, (
        "an empty authoring queue has no seed rule -- the ride cannot start, "
        "which is the 2026-07-26 no-op verbatim")
    assert "CLASS MEASUREMENT" in clause
    # The seed must be DERIVED from something committed, and the prompt must
    # name the file, not gesture at one.
    named = [m for m in re.findall(r"tests/test_\w+\.py", clause)]
    assert named, "the seed rule names no committed measurement to derive from"
    for rel in named:
        assert os.path.isfile(os.path.join(_ROOT, rel)), (
            f"the seed rule names {rel}, which does not exist -- a cold start "
            f"would derive from nothing")


def test_the_seed_rule_covers_every_outcome_the_ride_can_emit(purchase):
    """THE GAP THIS CLOSES, measured twice before it was closed once.

    run/reflect_ride.py returns exactly three per-candidate outcomes.  The
    seed rule originally had a next-round rule for FAILED (drive from the
    transcript tail) and for the empty queue, and NONE for PASSED -- whose
    `detail` is null by design, because a pass has no transcript.  So the
    first passing candidate produced a second no-op for the same shape of
    reason as the first: an instruction with no branch for the state the
    machine was actually in.

    The outcome names are imported from the ride rather than written here, so
    a fourth outcome added later reds this test instead of silently acquiring
    no rule."""
    from run import reflect_ride as R
    outcomes = {R.PASSED, R.FAILED, R.NOT_RUN}
    assert len(outcomes) == 3, "the ride's outcome vocabulary moved"
    i = purchase.find("SECOND, THE SEED")
    assert i >= 0, "the seed rule is gone"
    clause = purchase[i:]
    # Bind to the BRANCH, not to the name.  The clause enumerates all three
    # outcomes in its preamble, so a bare `o in clause` is satisfied by the
    # enumeration even when the branch is gone -- the same
    # matched-an-incidental-mention flaw this file's marker tooth already had
    # once.  A branch is "On <OUTCOME>:", so require that.
    missing = [o for o in sorted(outcomes) if f"On {o}:" not in clause]
    assert not missing, (
        f"the seed rule has no `On <outcome>:` branch for {missing} -- a "
        f"firing landing in that outcome has an instruction it cannot follow, "
        f"which is how PASSED produced a no-op")


def test_a_pass_is_not_treated_as_a_dead_end(purchase):
    """The specific wrong reading to forbid: a pass looks like completion, and
    the row is not done until the class measurement stops naming unmet work."""
    i = purchase.find("On PASSED:")
    assert i >= 0
    clause = purchase[i:i + 1200]
    assert "null BY DESIGN" in clause, "the empty detail is unexplained"
    assert "EXTEND" in clause
    # and the terminal case must hand off rather than silently continue
    assert "attended purchase decision" in clause


def test_the_splice_constraint_is_stated(purchase):
    """Without this, every candidate for every open row is impossible text."""
    i = purchase.find("THEN TAKE THE AUTHORING RIDE")
    clause = purchase[i:]
    assert "PARALLEL TOWER" in clause, (
        "the route does not tell sessions to prototype a parallel tower; a "
        "candidate cannot extend Tm, so tower-class candidates would all fail "
        "for a reason the session would misread as difficulty")
    assert "CANNOT add a constructor" in clause


def test_a_parallel_tower_actually_passes_the_escape_gate():
    """The instruction is only sound if the thing it asks for is admissible.
    Measure it rather than assume it: a new inductive plus a walker must pass
    the gate the ride applies BEFORE the backend is ever reached."""
    from buildloop.validate_lean import validate_lean
    ok, reason = validate_lean(
        "inductive TmP : Type\n"
        "  | lit : Int -> TmP\n"
        "  | powp : TmP -> TmP -> TmP\n"
        "def evalTmP : TmP -> Int\n"
        "  | TmP.lit n => n\n"
        "  | TmP.powp _ _ => 0\n")
    assert ok, f"a parallel tower is refused by the escape gate: {reason} -- " \
                "the seed rule would ask for text the ride can never run"


def test_the_empty_queue_hatch_cannot_swallow_the_seed(purchase):
    """The old hatch fired whenever the queue was empty, which is always true
    at a cold start.  It must now require a read of the measurement."""
    i = purchase.find("THEN TAKE THE AUTHORING RIDE")
    clause = purchase[i:]
    assert "ONLY honest no-op" in clause
    assert "never on its own a reason to stop" in clause


def test_branch_deletion_is_not_retried_and_is_verified_by_the_ref(sections):
    """MEASURED 2026-07-26: `git push origin --delete` through the session git
    proxy answers HTTP 403 -- the proxy restricts pushes to the current
    working branch -- and STILL EXITS 0 with `Everything up-to-date`.  A
    session reading the exit code concludes the branch is gone; one firing
    reported exactly that and had to post a correction on its own PR.

    Two rules follow, and both must survive in every prompt that deletes a
    claim branch: verify by the REF, not the exit code; and attempt once,
    because a policy denial is a decided fact and retrying it spends ~30s per
    claim close re-learning it."""
    whole = "".join(sections.values())
    assert "git push origin --delete" in whole, "the hygiene step vanished"
    assert "ls-remote" in whole, (
        "no prompt verifies the deletion by the REF; the exit code is 0 even "
        "when the 403 refused it, so every close would report success")
    assert "EXITS 0" in whole or "exit code" in whole, (
        "the lying exit code is not named where a session would read it")
    assert "ATTEMPT ONCE" in whole or "ATTEMPT IT ONCE" in whole, (
        "the prompts still permit backoff retries on a structural denial")


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
