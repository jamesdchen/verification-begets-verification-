"""Teeth for the two content-fired fences in trust-surface.yml.

WHAT WAS MEASURED, and why these fences stopped being title-fired.  The
bill-manifest job used to run under `if: startsWith(title, 'C3 purchase')`
-- the fence fired on the author's own self-declaration, and #81 shipped a
purchase-shaped diff under another title, skipping the mechanical bill
verification silently.  Separately, #174 shipped a detailed, accurate PR
body over an EMPTY diff (zero changed files), and the only detector was a
human running get_files.  Both are the same disease -- a claim standing in
for evidence -- and both fences now key on what the DIFF IS.

WHAT THESE TEETH CAN AND CANNOT DO (the test_chain_rearm precedent): the
jobs run on GitHub's runners, so the RUN cannot be executed here.  What is
checkable is the fence's LOGIC: the detection pattern is extracted from the
committed workflow text and EXECUTED against known purchase/non-purchase
paths, so a pattern edit that re-opens the #81 hole (or "completes" the
pattern with registration.json and starts firing on every corpus PR) fails
a behavior test, not a string match.  Bound to instruction syntax, never to
mentions -- this repo's teeth have been bitten four times by matching a
mention of the thing instead of the thing.
"""
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW = os.path.join(_ROOT, ".github", "workflows", "trust-surface.yml")


def _text():
    with open(WORKFLOW, encoding="utf-8") as fh:
        return fh.read()


def _job(name):
    """The job's block: from its key to the next top-level job key."""
    text = _text()
    m = re.search(rf"^  {re.escape(name)}:\n", text, re.M)
    assert m, f"job {name} missing from trust-surface.yml"
    nxt = re.search(r"^  [a-z][a-z0-9-]*:\n", text[m.end():], re.M)
    return text[m.start():m.end() + (nxt.start() if nxt else len(text))]


def _detection_pattern():
    """The grep -E pattern the bill-manifest step detects purchases with."""
    m = re.search(r"grep -Eq '([^']+)'", _job("bill-manifest"))
    assert m, "the purchase-shape detection grep is gone from bill-manifest"
    return m.group(1)


def test_bill_manifest_has_no_job_level_title_gate():
    """The #81 hole: a job-level `if: startsWith(title, ...)` means the fence
    fires on self-declaration.  The title may still appear INSIDE the step
    (as the second trigger direction) -- what must not exist is the job-level
    skip."""
    job = _job("bill-manifest")
    header = job.split("steps:")[0]
    assert "if:" not in header, (
        "bill-manifest is job-level-gated again; a purchase-shaped diff "
        "under a non-purchase title will skip the fence exactly as #81 did")


def test_detection_fires_on_both_purchase_shapes():
    """Executed, not quoted: the committed grep pattern must match the
    fragment-purchase flag (a growth-registry touch) and the
    instrument-purchase flag (a delta receipt).  grep -E and Python re agree
    on this pattern class."""
    pat = re.compile(_detection_pattern(), re.M)
    assert pat.match("buildloop/growth_protocol.py")
    assert pat.match("results/p9_delta.md")


def test_detection_ignores_corpus_growth_and_ordinary_work():
    """registration.json is a valid delta RECEIPT but a terrible detection
    SIGNAL -- ordinary corpus growth touches it too, and a detector that
    fires on every corpus PR is a detector nobody reads.  The tempting edit
    is to 'complete' the detection pattern from the tool's DELTA_RECEIPT_RE;
    this tooth is what that edit fails."""
    pat = re.compile(_detection_pattern(), re.M)
    assert not pat.match("specs/mathsources/registration.json")
    assert not pat.match("tools/frontier.py")
    assert not pat.match("tests/test_math_reading.py")
    # Anchored: a delta receipt lives at results/ top level, per the P1
    # worked example; a nested look-alike is not the receipt convention.
    assert not pat.match("docs/results/p9_delta.md")


def test_a_purchase_title_still_forces_the_manifest():
    """The second trigger direction: a PR that CLAIMS to be a purchase but
    carries no purchase-shaped diff must run the manifest (and go red on the
    missing bill items), never skip.  Bound to the step's own conditional
    syntax: the title expression feeds a variable the skip branch tests."""
    job = _job("bill-manifest")
    assert re.search(
        r'TITLED="\$\{\{ startsWith\(github\.event\.pull_request\.title,'
        r" 'C3 purchase'\) \}\}\"", job), "the title trigger is gone"
    assert '[ "$PURCHASE_SHAPED" = "0" ] && [ "$TITLED" != "true" ]' in job, (
        "the skip branch no longer requires BOTH triggers absent; either the "
        "shape or the claim alone must be enough to run the manifest")


def test_the_manifest_invocation_survives():
    """Control tooth: firing logic without the verification it fires is a
    fence around nothing."""
    job = _job("bill-manifest")
    assert "python3 tools/purchase_bill_manifest.py" in job
    assert "--base" in job and "--head" in job


def test_empty_diff_pr_goes_red():
    """The #174 fence: a non-draft PR whose diff changes no files is red
    unconditionally.  Bound to the exit and the count test, not to prose."""
    job = _job("non-empty-diff")
    assert 'if [ "$N" = "0" ]' in job, "the zero-changed-files test is gone"
    assert re.search(r'\[ "\$N" = "0" \][\s\S]*?exit 1', job), (
        "an empty diff no longer exits nonzero; #174's shape passes again")
    assert "git diff --name-only" in job


def test_empty_diff_fence_exempts_claim_drafts():
    """Claim-by-PR drafts hold the in-flight lock with an empty COMMIT --
    zero changed files by design.  The fence must skip drafts at the job
    level, or every claim lock goes red the moment it opens."""
    job = _job("non-empty-diff")
    header = job.split("steps:")[0]
    assert "github.event.pull_request.draft == false" in header, (
        "the draft exemption is gone; claim-by-PR locks will go red and "
        "sessions obeying merge-on-green rules will treat every claim as "
        "broken")


# ---------------------------------------------------------------------------
# C3 cycle 24: why a check the SELF-MERGE rule needs can be MISSING.
#
# trust-surface.yml's own header says a missing check "means exactly one thing
# -- the CI config was altered".  That was INCOMPLETE, and cycle 24 measured
# the case it missed: a PR CONFLICTED with its base runs no `pull_request`
# workflows AT ALL, because those runs are built against the merge ref and a
# conflicted PR has none.  The checks do not go red; they never exist.
#
# Measured on PR #188 -- green trust-surface on the claim sha at 22:51:41Z (the
# PR-opened event, before any conflict); the P8 purchase merged to main at
# 23:14:45Z; the ship push at 23:17:13Z and a second push at 23:28Z then
# produced ONLY push-event runs, every job skipped.  In a repo where two loops
# merge independently that is ROUTINE, so the diagnosis has to be mechanical
# rather than remembered: read `mergeable_state` before reading anything into a
# missing check.
#
# The teeth below pin the two facts that make the story true, so neither can
# rot into prose.
CI_WORKFLOW = os.path.join(_ROOT, ".github", "workflows", "ci.yml")


def _ci_text():
    with open(CI_WORKFLOW, encoding="utf-8") as fh:
        return fh.read()


def test_push_event_runs_gate_nothing_on_a_branch():
    """Half of why a conflicted PR is dangerous rather than merely stuck: the
    push-event runs that DO survive gate nothing, so the head commit looks like
    it has CI when it has none.  Pinned as the literal condition, because
    C3_PROMPTS.md quotes it verbatim in both driver prompts."""
    m = re.search(r"^  fast:\n(?:.*\n)*?    if: (.+)$", _ci_text(), re.M)
    assert m, "the `fast` job or its `if:` gate is gone from ci.yml"
    cond = m.group(1).strip()
    assert cond == (
        "github.event_name != 'push' || github.ref == 'refs/heads/main'"), cond


def test_trust_surface_is_pull_request_only():
    """The other half: trust-surface has NO `push` trigger, so when the
    pull_request event cannot fire there is no second route that would produce
    the check anyway.  If a future edit adds `push:` here, the cycle-24
    diagnosis stops holding and the prompts that state it must be corrected in
    the same commit -- which is what this tooth forces."""
    block = _on_block(_text())
    assert "pull_request" in block, "trust-surface no longer runs on pull_request"
    assert not re.search(r"^\s*push:", block, re.M), (
        "trust-surface now also runs on push -- C3_PROMPTS.md's Architecture "
        "section and both driver prompts explain a MISSING check in terms of "
        "pull_request being the only route.  Update them.")


def test_the_prompts_tell_a_driver_to_check_mergeable_state():
    """The measurement is only worth anything if it reaches the session that
    needs it, and the prompts are what a fired session actually reads.  Assert
    the two-cause diagnosis survives in the DRIVER prompt rather than trusting
    that an edit to the Architecture prose carried into it."""
    with open(os.path.join(_ROOT, "C3_PROMPTS.md"), encoding="utf-8") as fh:
        prompts = fh.read()
    driver = prompts.split("## DRIVER prompt")[1].split("## PURCHASE DRIVER")[0]
    assert "mergeable_state" in driver, (
        "the DRIVER prompt no longer tells a session to read mergeable_state "
        "when a check is missing -- the cycle-24 measurement")
    assert "TWO CAUSES" in driver.upper(), (
        "the DRIVER prompt no longer states that a missing trust-surface has "
        "two causes; a session reading the old one-cause rule would diagnose "
        "an ordinary merge conflict as CI tampering")


def _on_block(text):
    """The workflow's `on:` block, up to the next top-level key."""
    m = re.search(r"^on:\n", text, re.M)
    assert m, "workflow has no `on:` block"
    nxt = re.search(r"^[a-z][a-z0-9_-]*:\n", text[m.end():], re.M)
    return text[m.end():m.end() + (nxt.start() if nxt else len(text))]
