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
