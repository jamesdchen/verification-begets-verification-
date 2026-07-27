"""Teeth for the derived branch reaper (tools/branch_reaper.py).

WHAT THESE PIN THAT PROSE COULD NOT.  The driver prompts have carried the
branch-hygiene rule as measured prose since 2026-07-26 -- attempt the
deletion once, verify with ls-remote, note the 403 -- and the pile still
grew to 108 branches, because no session holds a token that may delete a
ref.  The policy now lives in one pure function the workflow obeys, and
these teeth hold both sides of every rule: what may be deleted, and what
must never be (the default branch, any open PR's head, a stray inside its
grace window, anything behind an unreadable read).

The merged_at-not-merged rule has its own tooth because it was MEASURED,
not designed: the list endpoint returned `merged: false` for all 217 PRs
of this repo while `merged_at` was set on the 139 that had merged
(2026-07-27).  A reaper trusting that boolean would have kept all 100
stale branches and called itself green.
"""
import datetime as dt
import json
import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "tools"))

import branch_reaper as R  # noqa: E402

NOW = "2026-07-27T00:00:00Z"


def _ago(days):
    """An RFC3339 stamp `days` before NOW, computed from NOW itself so no
    test reads a clock (the same discipline the tool's --now enforces)."""
    t = dt.datetime.fromisoformat(NOW.replace("Z", "+00:00"))
    return (t - dt.timedelta(days=days)).isoformat().replace("+00:00", "Z")


def _br(name, days_old=None):
    return {"name": name,
            "newest_commit_at": None if days_old is None else _ago(days_old)}


def _pr(ref, number=1, state="closed", merged_at=None, merged=False,
        nested=True):
    row = {"number": number, "state": state, "merged_at": merged_at,
           "merged": merged, "title": "C3 cycle n"}
    if nested:
        row["head"] = {"ref": ref}
    else:
        row["head_ref"] = ref
    return row


def _one(branches, prs, **kw):
    got = R.verdicts(branches, prs, NOW, **kw)
    assert got is not None and len(got) == 1
    return got[0]


# ------------------------------------------------------- the keep fences
def test_the_default_branch_is_kept_whatever_the_prs_say():
    v, name, _ = _one([_br("main", days_old=400)],
                      [_pr("main", merged_at=_ago(1))])
    assert v == R.KEEP and name == "main"


def test_a_nondefault_name_for_the_default_branch_is_honoured():
    v, _, _ = _one([_br("trunk", days_old=400)], [],
                   default_branch="trunk")
    assert v == R.KEEP


def test_an_open_pr_head_is_kept_even_when_an_older_pr_merged():
    # The branch rode one merged PR and now carries a second, open one:
    # deleting the head would close the open PR.  Open wins, always.
    v, _, reason = _one(
        [_br("claude/x", days_old=30)],
        [_pr("claude/x", number=7, merged_at=_ago(9)),
         _pr("claude/x", number=9, state="open")])
    assert v == R.KEEP and "#9" in reason


# --------------------------------------------------- the delete verdicts
def test_a_merged_pr_branch_is_residue():
    v, _, reason = _one([_br("claude/x", days_old=1)],
                        [_pr("claude/x", number=3, merged_at=_ago(1))])
    assert v == R.DELETE and "#3" in reason


def test_merged_is_read_off_merged_at_never_the_boolean():
    # MEASURED 2026-07-27: `merged` was false on every one of 217 rows while
    # merged_at told the truth.  A merged_at with merged=False still deletes;
    # a merged=True with no merged_at is NOT treated as merged.
    v, _, _ = _one([_br("claude/x")],
                   [_pr("claude/x", merged_at=_ago(2), merged=False)])
    assert v == R.DELETE
    v2, _, reason2 = _one([_br("claude/y")],
                          [_pr("claude/y", merged=True, merged_at=None)])
    assert v2 == R.DELETE and "unmerged" in reason2  # closed-unmerged path


def test_a_closed_unmerged_branch_is_superseded_work():
    v, _, reason = _one([_br("claude/x", days_old=1)],
                        [_pr("claude/x", number=5)])
    assert v == R.DELETE and "superseded" in reason


def test_a_flat_head_ref_row_reads_the_same_as_the_nested_payload():
    v, _, _ = _one([_br("claude/x")],
                   [_pr("claude/x", merged_at=_ago(1), nested=False)])
    assert v == R.DELETE


# ------------------------------------------------- strays and the grace
def test_a_stray_past_grace_is_deleted():
    v, _, _ = _one([_br("claude/stray", days_old=15)], [])
    assert v == R.DELETE


def test_a_stray_inside_grace_is_kept():
    v, _, _ = _one([_br("claude/stray", days_old=13)], [])
    assert v == R.KEEP


def test_the_grace_boundary_deletes_at_exactly_grace_days():
    v, _, _ = _one([_br("claude/stray", days_old=14)], [])
    assert v == R.DELETE


def test_grace_days_is_a_knob():
    v, _, _ = _one([_br("claude/stray", days_old=2)], [], grace_days=1)
    assert v == R.DELETE


def test_a_stray_with_no_readable_date_is_kept():
    v, _, reason = _one([_br("claude/stray")], [])
    assert v == R.KEEP and "fail safe" in reason


# ------------------------------------------------------ reads fail safe
def test_unreadable_now_yields_no_list_at_all():
    assert R.verdicts([_br("claude/x")], [], "not-a-time") is None


def test_unreadable_inputs_yield_no_list_at_all():
    assert R.verdicts(None, [], NOW) is None
    assert R.verdicts([], None, NOW) is None


def test_a_malformed_branch_row_is_kept_not_skipped():
    got = R.verdicts([{"nonsense": 1}], [], NOW)
    assert got == [(R.KEEP, "<malformed-row>",
                    "malformed branch row; reads fail safe")]


def test_a_malformed_pr_row_is_ignored_not_fatal():
    v, _, _ = _one([_br("claude/x", days_old=15)],
                   ["not-a-dict", {"head": "not-a-dict-either"}])
    assert v == R.DELETE  # falls through to the stray rule


# ------------------------------------------------------------- the CLI
def _run(args, stdin=None):
    return subprocess.run(
        [sys.executable, os.path.join(_ROOT, "tools", "branch_reaper.py")]
        + args, input=stdin, capture_output=True, text=True)


def test_porcelain_prints_only_delete_names(tmp_path):
    b = tmp_path / "b.json"
    p = tmp_path / "p.json"
    b.write_text(json.dumps([_br("main"), _br("claude/gone", days_old=1),
                             _br("claude/held", days_old=1)]))
    p.write_text(json.dumps([_pr("claude/gone", merged_at=_ago(1)),
                             _pr("claude/held", state="open")]))
    r = _run(["--now", NOW, "--branches", str(b), "--prs", str(p),
              "--porcelain"])
    assert r.returncode == 0
    assert r.stdout.split() == ["claude/gone"]


def test_unreadable_input_exits_2_with_empty_stdout(tmp_path):
    b = tmp_path / "b.json"
    b.write_text("{not json")
    p = tmp_path / "p.json"
    p.write_text("[]")
    r = _run(["--now", NOW, "--branches", str(b), "--prs", str(p),
              "--porcelain"])
    assert r.returncode == 2
    assert r.stdout == ""  # an errored call never impersonates a delete list
