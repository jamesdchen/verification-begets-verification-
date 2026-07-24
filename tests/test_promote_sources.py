"""tests/test_promote_sources.py -- checked promotion tool (tools/promote_sources.py).

Pure, LLM-free, tool-free.  Exercises the staged/ -> files[] promotion path
documented in specs/mathsources/staged/README.md and the WP-SRC review
to-dos recorded at merge 853dcee (see the docstring of
tools/promote_sources.py for the full mapping of items (a)-(d)).

House rule for this package: the tool MUTATES NOTHING unless invoked with an
explicit --apply flag.

NOTE (post-promotion): the WP-SRC decided policy has been EXECUTED -- the 11
real staged sources were promoted to top level, so the live repo's
``manifest.staged`` array is now EMPTY.  The promotion tool is general and stays
load-bearing (a future review may re-stage sources), so these tests no longer
read the live corpus; they build a SELF-CONTAINED synthetic mathsources tree
(files[] + staged[] + staged/*.txt + staged/README.md) in a temp dir and run
every tool behaviour against it.  This decouples the tool's coverage from the
live corpus that its one real use drained.  The real repo tree is asserted
untouched at the end.

Both real WP-SRC blockers (43 composed-verbatim, 44 nc-license) were CLEARED by
fixing the citations in commit 2c2a2a1, so BLOCKER_TABLE is empty; the waiver
machinery is still load-bearing and is exercised here against a SYNTHETIC
blocker injected into ps.BLOCKER_TABLE, never a real review nit.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common  # noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import promote_sources as ps  # noqa: E402

REAL_MATHSOURCES = common.REPO_ROOT / "specs" / "mathsources"
REAL_MANIFEST = REAL_MATHSOURCES / "manifest.json"


# --------------------------------------------------------------------------- #
# synthetic staged tree (self-contained; independent of the live corpus)
# --------------------------------------------------------------------------- #

# A pinned synthetic manifest that reproduces every shape the tool must handle:
# a couple of pre-existing top-level files[], and a staged[] array with an
# existential source (axis reconciliation / --keep-existential-axis), an idiom
# source, a non-transcribable source (quota delta), and the synthetic-blocker
# file (waiver machinery).  Staging-only fields (existential / binder_hint /
# provenance / staged_reason) are present so the "stripped at promotion"
# assertions are meaningful.
SYNTH_MANIFEST = {
    "flood_idiom": "divides-both",
    "files": [
        {"file": "01_base_plain.txt", "axes": ["plain"], "expect_transcribes": True},
        {"file": "02_base_side.txt", "axes": ["side-condition"], "expect_transcribes": True},
    ],
    "staged_note": "synthetic staged tree for tool tests (see module docstring).",
    "staged": [
        {"file": "41_division_algorithm.txt",
         "axes": ["existential", "side-condition"], "expect_transcribes": True,
         "existential": True, "binder_hint": "exists",
         "staged_reason": "synthetic existential witness",
         "provenance": {"reference": "synthetic", "url": "https://example.org/x",
                        "license": "CC BY-SA", "verbatim": "there exist q and r"}},
        {"file": "42_bezout_identity.txt",
         "axes": ["existential", "idiom:common-divisor"], "expect_transcribes": True,
         "existential": True, "binder_hint": "exists",
         "staged_reason": "synthetic idiom existential",
         "provenance": {"reference": "synthetic", "url": "https://example.org/y",
                        "license": "CC BY-SA", "verbatim": "there exist x and y"}},
        {"file": "45_cong_transitive.txt",
         "axes": ["idiom:congruent-mod"], "expect_transcribes": True,
         "staged_reason": "synthetic idiom source (also the synthetic-blocker file)",
         "provenance": {"reference": "synthetic", "url": "https://example.org/z",
                        "license": "CC BY-SA", "verbatim": "a congruent to c mod m"}},
        {"file": "51_goldbach.txt",
         "axes": ["non-transcribable"], "expect_transcribes": False,
         "miss_kind_guess": "operator:prime",
         "existential": True, "binder_hint": "exists",
         "staged_reason": "synthetic boundary source (exists but out of fragment)",
         "provenance": {"reference": "synthetic", "url": "https://example.org/g",
                        "license": "CC BY-SA", "verbatim": "sum of two primes"}},
    ],
}
N_STAGED = len(SYNTH_MANIFEST["staged"])            # 4
N_FILES_BEFORE = len(SYNTH_MANIFEST["files"])       # 2

# The tool retags/preserves an `existential` axis; the README the checklist is
# read from must carry the pinned-glob bullets the checklist test asserts.
SYNTH_README = """# synthetic staged/ README (tool test fixture)

## Promotion re-baseline obligations

* `bench_formalize.py` (`_CORPUS.glob("*.txt")`, line ~585) enumerates every
  top-level source; the committed `results/formalize_bench_state.jsonl` records
  the denominators -- moving these files up shifts them.
* `cgb.py` `_ledger_sync` (`ms.glob("*.txt")`) bills every top-level source as a
  `math-source` demand row -- top-level placement changes the corpus DL base.
* `tests/test_mathsources_manifest.py` pins `EXPECTED_TOTAL` and a strict
  top-level `.txt` <-> `manifest["files"]` bijection.
"""


@pytest.fixture()
def synth_tree(tmp_path):
    """Write the synthetic mathsources tree to a temp dir and return its root.
    ``--apply`` is allowed to mutate this copy (never the real repo)."""
    root = tmp_path / "mathsources"
    (root / "staged").mkdir(parents=True)
    # top-level source files (bijection targets)
    for e in SYNTH_MANIFEST["files"]:
        (root / e["file"]).write_text(f"synthetic top-level source {e['file']}\n",
                                      encoding="utf-8")
    # staged source files
    for e in SYNTH_MANIFEST["staged"]:
        (root / "staged" / e["file"]).write_text(
            f"synthetic staged source {e['file']}\n", encoding="utf-8")
    (root / "staged" / "README.md").write_text(SYNTH_README, encoding="utf-8")
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(SYNTH_MANIFEST, indent=2) + "\n",
                             encoding="utf-8")
    return root


def _synth_manifest(root):
    return ps._load_manifest(root / "manifest.json")


# The waiver machinery is exercised against a SYNTHETIC blocker keyed to a real
# staged file in the synthetic tree.
SYNTH_BLOCKED_FILE = "45_cong_transitive.txt"
SYNTH_BLOCKER_CODE = "synthetic-test-blocker"


@pytest.fixture()
def synthetic_blocker(monkeypatch):
    table = {
        SYNTH_BLOCKED_FILE: (
            ps.Blocker(
                code=SYNTH_BLOCKER_CODE,
                reason="synthetic blocker injected by the test suite to exercise "
                       "the waiver machinery; not a real WP-SRC review nit.",
            ),
        ),
    }
    monkeypatch.setattr(ps, "BLOCKER_TABLE", table)
    return SYNTH_BLOCKED_FILE


# --------------------------------------------------------------------------- #
# dry-run: read-only, against the synthetic tree
# --------------------------------------------------------------------------- #

def test_dry_run_does_not_touch_disk(synth_tree):
    manifest_path = synth_tree / "manifest.json"
    before = manifest_path.read_bytes()
    before_staged = sorted(p.name for p in (synth_tree / "staged").glob("*.txt"))
    rc = ps.main(["--all-staged", "--mathsources-root", str(synth_tree)])
    after = manifest_path.read_bytes()
    after_staged = sorted(p.name for p in (synth_tree / "staged").glob("*.txt"))
    assert before == after, "dry-run must never write the manifest"
    assert before_staged == after_staged, "dry-run must never move staged files"
    # BLOCKER_TABLE is empty, so a dry-run over every staged source is clean.
    assert rc == 0


def test_dry_run_plan_existential_source_reconciles_axes(synth_tree):
    """An existential staged source's plan shows NO blocker while the
    existential->plain axis reconciliation fires (default retag)."""
    manifest = _synth_manifest(synth_tree)
    selected = ps.select_sources(manifest, ["41"], all_staged=False)
    plan = ps.build_plan(manifest, selected, SYNTH_README,
                          keep_existential_axis=False, waivers={})
    text = ps.render_plan(plan)
    assert "41_division_algorithm.txt" in text
    assert "VALID_AXES" in text
    assert "existential" in text and "plain" in text
    assert "blockers: none recorded" in text
    assert not plan.blocked
    assert plan.sources[0].unresolved_blockers == []


def test_dry_run_full_plan_has_no_blockers(synth_tree):
    """With BLOCKER_TABLE empty, the whole synthetic staged set promotes cleanly."""
    manifest = _synth_manifest(synth_tree)
    selected = ps.select_sources(manifest, [], all_staged=True)
    plan = ps.build_plan(manifest, selected, SYNTH_README,
                          keep_existential_axis=False, waivers={})
    assert not plan.blocked
    assert all(not s.unresolved_blockers for s in plan.sources)
    text = ps.render_plan(plan)
    assert "BLOCKED" not in text
    # the REAL corpus carries no review blocker either (both cleared in 2c2a2a1).
    assert ps.BLOCKER_TABLE == {}, "no real staged source may carry a review blocker"


def test_dry_run_unblocked_source_has_no_blockers(synth_tree):
    manifest = _synth_manifest(synth_tree)
    selected = ps.select_sources(manifest, ["42"], all_staged=False)
    plan = ps.build_plan(manifest, selected, "", keep_existential_axis=False, waivers={})
    assert not plan.blocked
    assert plan.sources[0].unresolved_blockers == []


def test_dry_run_reports_expected_total_delta(synth_tree):
    manifest = _synth_manifest(synth_tree)
    selected = ps.select_sources(manifest, [], all_staged=True)
    plan = ps.build_plan(manifest, selected, "", keep_existential_axis=False, waivers={})
    assert plan.expected_total_before == N_FILES_BEFORE
    assert plan.expected_total_after == N_FILES_BEFORE + N_STAGED == N_FILES_BEFORE + len(selected)


def test_dry_run_reports_non_transcribable_quota_delta(synth_tree):
    """51_goldbach.txt is non-transcribable; promoting it surfaces the quota
    re-baseline obligation in the plan."""
    manifest = _synth_manifest(synth_tree)
    selected = ps.select_sources(manifest, ["51"], all_staged=False)
    plan = ps.build_plan(manifest, selected, "", keep_existential_axis=False, waivers={})
    # the synthetic files[] carries zero non-transcribable entries.
    assert plan.non_transcribable_before == 0
    assert plan.non_transcribable_after == 1
    text = ps.render_plan(plan)
    assert "non-transcribable quota" in text
    assert "EXACTLY 3" in text or "EXACTLY-3" in text


def test_dry_run_checklist_is_read_from_readme_not_hardcoded(synth_tree):
    manifest = _synth_manifest(synth_tree)
    selected = ps.select_sources(manifest, [], all_staged=True)
    plan = ps.build_plan(manifest, selected, SYNTH_README,
                          keep_existential_axis=False, waivers={})
    assert plan.readme_checklist, "expected at least one checklist bullet from the README"
    normalized_readme = " ".join(SYNTH_README.split())
    for bullet in plan.readme_checklist:
        normalized_bullet = " ".join(bullet.split())
        assert normalized_bullet in normalized_readme, (
            f"checklist bullet not traceable to README text: {bullet!r}")
    joined = " ".join(plan.readme_checklist)
    assert "bench_formalize.py" in joined
    assert "_ledger_sync" in joined
    assert "EXPECTED_TOTAL" in joined


def test_dry_run_is_deterministic(synth_tree):
    manifest = _synth_manifest(synth_tree)
    selected = ps.select_sources(manifest, [], all_staged=True)
    plan1 = ps.build_plan(manifest, selected, SYNTH_README, False, {})
    plan2 = ps.build_plan(manifest, selected, SYNTH_README, False, {})
    assert ps.render_plan(plan1) == ps.render_plan(plan2)
    # order-independent selection converges to the same deterministic plan
    manifest2 = _synth_manifest(synth_tree)
    selected_shuffled = ps.select_sources(
        manifest2, ["51", "45", "41", "42"], all_staged=False)
    plan3 = ps.build_plan(manifest2, selected_shuffled, SYNTH_README, False, {})
    assert ps.render_plan(plan3) == ps.render_plan(plan1)


def test_unknown_id_is_rejected(synth_tree):
    manifest = _synth_manifest(synth_tree)
    with pytest.raises(ps.PromotionError):
        ps.select_sources(manifest, ["999_not_a_source"], all_staged=False)


# --------------------------------------------------------------------------- #
# --apply: synthetic tree only
# --------------------------------------------------------------------------- #

def test_apply_without_waiver_refuses_and_mutates_nothing(synth_tree, synthetic_blocker):
    manifest_path = synth_tree / "manifest.json"
    before_manifest = manifest_path.read_bytes()
    before_staged = sorted(p.name for p in (synth_tree / "staged").glob("*.txt"))
    before_files = sorted(p.name for p in synth_tree.glob("*.txt"))

    with pytest.raises(ps.PromotionError, match="unresolved WP-SRC review blockers"):
        ps.apply_promotion(synth_tree, manifest_path, [synthetic_blocker], False, waivers={})

    assert manifest_path.read_bytes() == before_manifest
    assert sorted(p.name for p in (synth_tree / "staged").glob("*.txt")) == before_staged
    assert sorted(p.name for p in synth_tree.glob("*.txt")) == before_files


def test_apply_with_waive_but_wrong_source_is_rejected(synth_tree, synthetic_blocker):
    manifest_path = synth_tree / "manifest.json"
    # 42 has no recorded blockers -- waiving it is refused (no waiving into thin air)
    with pytest.raises(ps.PromotionError, match="no recorded blockers"):
        ps.apply_promotion(synth_tree, manifest_path, ["42"], False,
                            waivers={"42_bezout_identity.txt": "not applicable"})


def test_apply_waive_requires_nonempty_reason(synth_tree, synthetic_blocker):
    manifest_path = synth_tree / "manifest.json"
    with pytest.raises(ps.PromotionError, match="non-empty reason"):
        ps.apply_promotion(synth_tree, manifest_path, [synthetic_blocker], False,
                            waivers={synthetic_blocker: "   "})


def test_apply_with_waiver_succeeds_and_writes_promotion_note(synth_tree, synthetic_blocker):
    manifest_path = synth_tree / "manifest.json"
    reason = "reviewer accepted the synthetic blocker by hand; acceptable for promotion"
    plan = ps.apply_promotion(
        synth_tree, manifest_path, [synthetic_blocker], False,
        waivers={synthetic_blocker: reason})
    assert not plan.blocked

    manifest = ps._load_manifest(manifest_path)
    files_by_name = {e["file"]: e for e in manifest["files"]}
    assert synthetic_blocker in files_by_name
    promoted = files_by_name[synthetic_blocker]
    assert "promotion_note" in promoted
    assert reason in promoted["promotion_note"]
    assert SYNTH_BLOCKER_CODE in promoted["promotion_note"]

    # staging-only fields must be gone from the promoted entry
    assert "provenance" not in promoted
    assert "staged_reason" not in promoted
    assert "binder_hint" not in promoted
    assert "existential" not in promoted

    staged_files = {e["file"] for e in manifest["staged"]}
    assert synthetic_blocker not in staged_files


def test_apply_moves_file_byte_identical_and_updates_bijection(synth_tree):
    manifest_path = synth_tree / "manifest.json"
    src_path = synth_tree / "staged" / "42_bezout_identity.txt"
    original_bytes = src_path.read_bytes()

    ps.apply_promotion(synth_tree, manifest_path, ["42"], False, waivers={})

    moved_path = synth_tree / "42_bezout_identity.txt"
    assert moved_path.is_file()
    assert moved_path.read_bytes() == original_bytes
    assert not src_path.exists(), "staged copy must be gone after the move"

    manifest = ps._load_manifest(manifest_path)
    assert json.dumps(manifest)  # still parses / round-trips as JSON

    manifest_files = sorted(e["file"] for e in manifest["files"])
    disk_files = sorted(p.name for p in synth_tree.glob("*.txt"))
    assert manifest_files == disk_files

    staged_files = {e["file"] for e in manifest["staged"]}
    assert "42_bezout_identity.txt" not in staged_files


def test_apply_all_staged_clean_promotes_everything(synth_tree):
    """BLOCKER_TABLE empty, so --all-staged with NO waivers promotes every staged
    source and needs no waiver at all."""
    manifest_path = synth_tree / "manifest.json"
    plan = ps.apply_promotion(synth_tree, manifest_path, [], True, waivers={})
    assert len(plan.sources) == N_STAGED
    assert not plan.blocked

    manifest = ps._load_manifest(manifest_path)
    assert len(manifest["files"]) == N_FILES_BEFORE + N_STAGED
    assert manifest["staged"] == []

    manifest_files = sorted(e["file"] for e in manifest["files"])
    disk_files = sorted(p.name for p in synth_tree.glob("*.txt"))
    assert manifest_files == disk_files
    assert len(manifest_files) == len(set(manifest_files))

    # clean sources promote with no promotion_note (nothing was waived)
    files_by_name = {e["file"]: e for e in manifest["files"]}
    for e in SYNTH_MANIFEST["staged"]:
        assert "promotion_note" not in files_by_name[e["file"]]
        assert (synth_tree / e["file"]).is_file()
        assert not (synth_tree / "staged" / e["file"]).exists()


def test_apply_refuses_if_any_selected_source_in_batch_is_blocked(synth_tree, synthetic_blocker):
    """--all-staged with an unwaived (synthetic) blocker in the batch must refuse
    entirely (all-or-nothing) and leave the tree untouched."""
    manifest_path = synth_tree / "manifest.json"
    before_manifest = manifest_path.read_bytes()
    before_staged = sorted(p.name for p in (synth_tree / "staged").glob("*.txt"))
    before_files = sorted(p.name for p in synth_tree.glob("*.txt"))

    with pytest.raises(ps.PromotionError, match="unresolved WP-SRC review blockers"):
        ps.apply_promotion(synth_tree, manifest_path, [], True, waivers={})

    assert manifest_path.read_bytes() == before_manifest
    assert sorted(p.name for p in (synth_tree / "staged").glob("*.txt")) == before_staged
    assert sorted(p.name for p in synth_tree.glob("*.txt")) == before_files


def test_apply_all_staged_with_synthetic_blocker_waived_succeeds(synth_tree, synthetic_blocker):
    """The waiver escape hatch works end-to-end: --all-staged succeeds once the
    synthetic blocker is waived, writing a promotion_note only on that one."""
    manifest_path = synth_tree / "manifest.json"
    plan = ps.apply_promotion(
        synth_tree, manifest_path, [], True,
        waivers={synthetic_blocker: "reviewer accepted synthetic blocker"})
    assert len(plan.sources) == N_STAGED
    assert not plan.blocked

    manifest = ps._load_manifest(manifest_path)
    assert len(manifest["files"]) == N_FILES_BEFORE + N_STAGED
    assert manifest["staged"] == []
    files_by_name = {e["file"]: e for e in manifest["files"]}
    assert SYNTH_BLOCKER_CODE in files_by_name[synthetic_blocker]["promotion_note"]
    # sources without a blocker carry no promotion_note
    assert "promotion_note" not in files_by_name["42_bezout_identity.txt"]


def test_apply_keep_existential_axis_flag_preserves_tag(synth_tree):
    manifest_path = synth_tree / "manifest.json"
    ps.apply_promotion(
        synth_tree, manifest_path, ["41"], False, waivers={},
        keep_existential_axis=True)
    manifest = ps._load_manifest(manifest_path)
    entry = next(e for e in manifest["files"] if e["file"] == "41_division_algorithm.txt")
    assert "existential" in entry["axes"]


# --------------------------------------------------------------------------- #
# the live repo reflects the EXECUTED WP-SRC promotion, and this module never
# touched it (all mutation was against the synthetic temp tree).
# --------------------------------------------------------------------------- #

def test_real_repo_reflects_executed_promotion_and_is_untouched_here():
    """The WP-SRC promotion has landed on the real tree (51 files), and nothing
    in this module wrote it (only the synth_tree fixture is mutated).  The
    staged array was empty after §11.12; WP-SRC2 re-staged the next batch
    (52-62), so the pin is now relational: staged entries are exactly the
    on-disk staged/*.txt set and none collides with a promoted top-level slot
    (the exact-membership pin lives in test_mathsources_staged)."""
    manifest = ps._load_manifest(REAL_MANIFEST)
    # 51 post-promotion + the S4a' exists-class sources (63..66 then 67..69;
    # slots 52-62 stay reserved for the WP-SRC2 staged batch below).
    assert len(manifest["files"]) == 58
    staged_files = {e["file"] for e in manifest["staged"]}
    on_disk = {p.name for p in (REAL_MANIFEST.parent / "staged").glob("*.txt")}
    assert staged_files == on_disk
    assert not staged_files & {e["file"] for e in manifest["files"]}
    # the 11 promoted sources are all present in files[] and on disk at top level
    promoted = {
        "41_division_algorithm.txt", "42_bezout_identity.txt",
        "43_larger_integer_exists.txt", "44_divides_witness.txt",
        "45_cong_transitive.txt", "46_cong_add_const.txt",
        "47_cong_scalar_mul.txt", "48_db_sum.txt", "49_cd_combo_diff.txt",
        "50_even_times_even.txt", "51_goldbach.txt",
    }
    files_names = {e["file"] for e in manifest["files"]}
    assert promoted <= files_names
    for name in promoted:
        assert (REAL_MATHSOURCES / name).is_file()
        assert not (REAL_MATHSOURCES / "staged" / name).exists()
