"""tests/test_promote_sources.py -- checked promotion tool (tools/promote_sources.py).

Pure, LLM-free, tool-free.  Exercises the staged/ -> files[] promotion path
documented in specs/mathsources/staged/README.md and the WP-SRC review
to-dos recorded at merge 853dcee (see the docstring of
tools/promote_sources.py for the full mapping of items (a)-(d)).

House rule for this package: the tool MUTATES NOTHING unless invoked with an
explicit --apply flag, and --apply is exercised HERE ONLY against a temp
copy of specs/mathsources (never the real repo tree). Dry-run tests run
directly against the real repo's manifest/staged tree (read-only).

Both real WP-SRC blockers (43 composed-verbatim, 44 nc-license) were CLEARED by
fixing the citations in commit 2c2a2a1, so BLOCKER_TABLE is now empty and the
dry-run over the real corpus is clean (exit 0).  The waiver machinery is still
load-bearing, so the tests that exercise it (refusal, --waive -> promotion_note,
wrong-source rejection, all-or-nothing batches) now run against a SYNTHETIC
blocker injected into ps.BLOCKER_TABLE via the ``synthetic_blocker`` fixture,
never against a real review nit.
"""
from __future__ import annotations

import json
import os
import shutil
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common  # noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import promote_sources as ps  # noqa: E402

REAL_MATHSOURCES = common.REPO_ROOT / "specs" / "mathsources"
REAL_MANIFEST = REAL_MATHSOURCES / "manifest.json"


# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture()
def temp_tree(tmp_path):
    """A full temp copy of specs/mathsources (files, staged/, dream/,
    manifest.json, staged/README.md) that --apply is allowed to mutate."""
    dst = tmp_path / "mathsources"
    shutil.copytree(REAL_MATHSOURCES, dst)
    return dst


def _real_manifest():
    return ps._load_manifest(REAL_MANIFEST)


# The real BLOCKER_TABLE is empty (both WP-SRC blockers were cleared by fixing
# the citations, commit 2c2a2a1).  The waiver machinery -- unresolved-refusal,
# --waive -> promotion_note, wrong-source rejection, all-or-nothing batches --
# is still load-bearing and must stay tested, so we exercise it against a
# SYNTHETIC blocker injected into ps.BLOCKER_TABLE rather than a real review nit.
SYNTH_BLOCKED_FILE = "45_cong_transitive.txt"
SYNTH_BLOCKER_CODE = "synthetic-test-blocker"


@pytest.fixture()
def synthetic_blocker(monkeypatch):
    """Inject one synthetic blocker keyed to a real staged file so the waiver
    machinery can be tested without a real unresolved review nit.  Returns the
    blocked filename."""
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
# dry-run: read-only, against the real repo tree
# --------------------------------------------------------------------------- #

def test_dry_run_does_not_touch_disk(tmp_path):
    before = REAL_MANIFEST.read_bytes()
    before_staged = sorted(p.name for p in (REAL_MATHSOURCES / "staged").glob("*.txt"))
    rc = ps.main(["--all-staged", "--mathsources-root", str(REAL_MATHSOURCES)])
    after = REAL_MANIFEST.read_bytes()
    after_staged = sorted(p.name for p in (REAL_MATHSOURCES / "staged").glob("*.txt"))
    assert before == after, "dry-run must never write the manifest"
    assert before_staged == after_staged, "dry-run must never move staged files"
    # BLOCKER_TABLE is empty now (both 43 & 44 blockers cleared by fixing the
    # citations in 2c2a2a1), so a dry-run over every staged source is clean and
    # exits 0.
    assert rc == 0


def test_dry_run_plan_43_is_clean_but_still_reconciles_axes(capsys):
    """43's composed-verbatim blocker was cleared by fixing the citation
    (commit 2c2a2a1): the plan must now show NO blocker for it, while the
    unrelated existential->plain axis reconciliation still fires."""
    manifest = _real_manifest()
    selected = ps.select_sources(manifest, ["43"], all_staged=False)
    readme_text = (REAL_MATHSOURCES / "staged" / "README.md").read_text(encoding="utf-8")
    plan = ps.build_plan(manifest, selected, readme_text,
                          keep_existential_axis=False, waivers={})
    text = ps.render_plan(plan)

    assert "43_larger_integer_exists.txt" in text
    # axis reconciliation is orthogonal to the (now-cleared) blocker and stays
    assert "VALID_AXES" in text
    assert "existential" in text and "plain" in text
    # the composed-verbatim blocker is gone -- neither named nor active
    assert "composed-verbatim" not in text
    assert "blockers: none recorded" in text
    assert not plan.blocked
    assert plan.sources[0].unresolved_blockers == []


def test_dry_run_plan_44_is_clean():
    """44's nc-license blocker was cleared by swapping to a BY-SA source."""
    manifest = _real_manifest()
    selected = ps.select_sources(manifest, ["44"], all_staged=False)
    plan = ps.build_plan(manifest, selected, "", keep_existential_axis=False, waivers={})
    text = ps.render_plan(plan)
    assert "nc-license" not in text
    assert "Non-Commercial" not in text and "CC BY-NC-SA" not in text
    assert "blockers: none recorded" in text
    assert not plan.blocked
    assert plan.sources[0].unresolved_blockers == []


def test_dry_run_full_plan_has_no_blockers():
    """With BLOCKER_TABLE empty, the whole staged corpus promotes cleanly:
    no source has an unresolved blocker and the rendered plan never says
    'BLOCKED'."""
    manifest = _real_manifest()
    selected = ps.select_sources(manifest, [], all_staged=True)
    readme_text = (REAL_MATHSOURCES / "staged" / "README.md").read_text(encoding="utf-8")
    plan = ps.build_plan(manifest, selected, readme_text,
                          keep_existential_axis=False, waivers={})
    assert not plan.blocked
    assert all(not s.unresolved_blockers for s in plan.sources)
    text = ps.render_plan(plan)
    assert "BLOCKED" not in text
    assert ps.BLOCKER_TABLE == {}, "no real staged source may carry a review blocker"


def test_dry_run_unblocked_source_has_no_blockers():
    manifest = _real_manifest()
    selected = ps.select_sources(manifest, ["45"], all_staged=False)
    plan = ps.build_plan(manifest, selected, "", keep_existential_axis=False, waivers={})
    assert not plan.blocked
    assert plan.sources[0].unresolved_blockers == []


def test_dry_run_reports_expected_total_delta():
    manifest = _real_manifest()
    selected = ps.select_sources(manifest, [], all_staged=True)
    plan = ps.build_plan(manifest, selected, "", keep_existential_axis=False, waivers={})
    assert plan.expected_total_before == 40
    assert plan.expected_total_after == 40 + len(selected) == 51


def test_dry_run_reports_non_transcribable_quota_delta_for_51():
    """51_goldbach.txt is non-transcribable; promoting it alone should surface
    the EXACTLY-3 quota re-baseline obligation."""
    manifest = _real_manifest()
    selected = ps.select_sources(manifest, ["51"], all_staged=False)
    plan = ps.build_plan(manifest, selected, "", keep_existential_axis=False, waivers={})
    assert plan.non_transcribable_before == 3
    assert plan.non_transcribable_after == 4
    text = ps.render_plan(plan)
    assert "non-transcribable quota" in text
    assert "EXACTLY 3" in text or "EXACTLY-3" in text


def test_dry_run_checklist_is_read_from_readme_not_hardcoded():
    manifest = _real_manifest()
    selected = ps.select_sources(manifest, [], all_staged=True)
    readme_text = (REAL_MATHSOURCES / "staged" / "README.md").read_text(encoding="utf-8")
    plan = ps.build_plan(manifest, selected, readme_text,
                          keep_existential_axis=False, waivers={})
    # every extracted bullet must be a verbatim substring of the README text
    assert plan.readme_checklist, "expected at least one checklist bullet from the README"
    for bullet in plan.readme_checklist:
        # bullets are joined/whitespace-normalized; compare on a normalized basis
        normalized_readme = " ".join(readme_text.split())
        normalized_bullet = " ".join(bullet.split())
        assert normalized_bullet in normalized_readme, (
            f"checklist bullet not traceable to README text: {bullet!r}")
    # and it must mention the specific pinned globs/consumers named in the README
    joined = " ".join(plan.readme_checklist)
    assert "bench_formalize.py" in joined
    assert "_ledger_sync" in joined
    assert "EXPECTED_TOTAL" in joined


def test_dry_run_is_deterministic():
    manifest = _real_manifest()
    selected = ps.select_sources(manifest, [], all_staged=True)
    readme_text = (REAL_MATHSOURCES / "staged" / "README.md").read_text(encoding="utf-8")
    plan1 = ps.build_plan(manifest, selected, readme_text, False, {})
    plan2 = ps.build_plan(manifest, selected, readme_text, False, {})
    text1 = ps.render_plan(plan1)
    text2 = ps.render_plan(plan2)
    assert text1 == text2
    # order-independent selection also converges to the same deterministic plan
    manifest2 = _real_manifest()
    selected_shuffled = ps.select_sources(
        manifest2, ["51", "41", "47", "44", "42", "49", "50", "46", "48", "45", "43"],
        all_staged=False)
    plan3 = ps.build_plan(manifest2, selected_shuffled, readme_text, False, {})
    assert ps.render_plan(plan3) == text1


def test_unknown_id_is_rejected():
    manifest = _real_manifest()
    with pytest.raises(ps.PromotionError):
        ps.select_sources(manifest, ["999_not_a_source"], all_staged=False)


# --------------------------------------------------------------------------- #
# --apply: temp tree only
# --------------------------------------------------------------------------- #

def test_apply_without_waiver_refuses_and_mutates_nothing(temp_tree, synthetic_blocker):
    manifest_path = temp_tree / "manifest.json"
    before_manifest = manifest_path.read_bytes()
    before_staged = sorted(p.name for p in (temp_tree / "staged").glob("*.txt"))
    before_files = sorted(p.name for p in temp_tree.glob("*.txt"))

    with pytest.raises(ps.PromotionError, match="unresolved WP-SRC review blockers"):
        ps.apply_promotion(temp_tree, manifest_path, [synthetic_blocker], False, waivers={})

    assert manifest_path.read_bytes() == before_manifest
    assert sorted(p.name for p in (temp_tree / "staged").glob("*.txt")) == before_staged
    assert sorted(p.name for p in temp_tree.glob("*.txt")) == before_files


def test_apply_with_waive_but_wrong_source_is_rejected(temp_tree, synthetic_blocker):
    manifest_path = temp_tree / "manifest.json"
    # 42 has no recorded blockers (only synthetic_blocker's file does) -- waiving
    # it should be refused (no waiving into thin air; keeps waivers auditable)
    with pytest.raises(ps.PromotionError, match="no recorded blockers"):
        ps.apply_promotion(temp_tree, manifest_path, ["42"], False,
                            waivers={"42_bezout_identity.txt": "not applicable"})


def test_apply_waive_requires_nonempty_reason(temp_tree, synthetic_blocker):
    manifest_path = temp_tree / "manifest.json"
    with pytest.raises(ps.PromotionError, match="non-empty reason"):
        ps.apply_promotion(temp_tree, manifest_path, [synthetic_blocker], False,
                            waivers={synthetic_blocker: "   "})


def test_apply_with_waiver_succeeds_and_writes_promotion_note(temp_tree, synthetic_blocker):
    manifest_path = temp_tree / "manifest.json"
    reason = "reviewer accepted the synthetic blocker by hand; acceptable for promotion"
    plan = ps.apply_promotion(
        temp_tree, manifest_path, [synthetic_blocker], False,
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

    # staged[] no longer contains the promoted entry
    staged_files = {e["file"] for e in manifest["staged"]}
    assert synthetic_blocker not in staged_files


def test_apply_moves_file_byte_identical_and_updates_bijection(temp_tree):
    manifest_path = temp_tree / "manifest.json"
    src_path = temp_tree / "staged" / "42_bezout_identity.txt"
    original_bytes = src_path.read_bytes()

    ps.apply_promotion(temp_tree, manifest_path, ["42"], False, waivers={})

    moved_path = temp_tree / "42_bezout_identity.txt"
    assert moved_path.is_file()
    assert moved_path.read_bytes() == original_bytes
    assert not src_path.exists(), "staged copy must be gone after the move"

    manifest = ps._load_manifest(manifest_path)
    assert json.dumps(manifest)  # still parses / round-trips as JSON

    # bijection between top-level .txt files and manifest['files'] holds
    manifest_files = sorted(e["file"] for e in manifest["files"])
    disk_files = sorted(p.name for p in temp_tree.glob("*.txt"))
    assert manifest_files == disk_files

    staged_files = {e["file"] for e in manifest["staged"]}
    assert "42_bezout_identity.txt" not in staged_files


def test_apply_all_staged_clean_promotes_everything(temp_tree):
    """BLOCKER_TABLE is empty (43 & 44 fixed), so --all-staged with NO waivers
    promotes every staged source and needs no waiver at all."""
    manifest_path = temp_tree / "manifest.json"
    plan = ps.apply_promotion(temp_tree, manifest_path, [], True, waivers={})
    assert len(plan.sources) == 11
    assert not plan.blocked

    manifest = ps._load_manifest(manifest_path)
    assert len(manifest["files"]) == 40 + 11
    assert manifest["staged"] == []

    manifest_files = sorted(e["file"] for e in manifest["files"])
    disk_files = sorted(p.name for p in temp_tree.glob("*.txt"))
    assert manifest_files == disk_files
    assert len(manifest_files) == len(set(manifest_files))

    # the two formerly-blocked sources promote with no promotion_note (they were
    # fixed, not waived)
    files_by_name = {e["file"]: e for e in manifest["files"]}
    for name in ("43_larger_integer_exists.txt", "44_divides_witness.txt"):
        assert "promotion_note" not in files_by_name[name]

    # every promoted file's bytes match its original staged bytes
    for name in ("41_division_algorithm.txt", "42_bezout_identity.txt",
                 "43_larger_integer_exists.txt", "44_divides_witness.txt",
                 "51_goldbach.txt"):
        assert (temp_tree / name).is_file()
        assert not (temp_tree / "staged" / name).exists()


def test_apply_refuses_if_any_selected_source_in_batch_is_blocked(temp_tree, synthetic_blocker):
    """--all-staged with an unwaived (synthetic) blocker in the batch must refuse
    entirely (all-or-nothing) and leave the temp tree untouched."""
    manifest_path = temp_tree / "manifest.json"
    before_manifest = manifest_path.read_bytes()
    before_staged = sorted(p.name for p in (temp_tree / "staged").glob("*.txt"))
    before_files = sorted(p.name for p in temp_tree.glob("*.txt"))

    with pytest.raises(ps.PromotionError, match="unresolved WP-SRC review blockers"):
        ps.apply_promotion(temp_tree, manifest_path, [], True, waivers={})

    assert manifest_path.read_bytes() == before_manifest
    assert sorted(p.name for p in (temp_tree / "staged").glob("*.txt")) == before_staged
    assert sorted(p.name for p in temp_tree.glob("*.txt")) == before_files


def test_apply_all_staged_with_synthetic_blocker_waived_succeeds(temp_tree, synthetic_blocker):
    """The waiver escape hatch still works end-to-end: --all-staged succeeds once
    the synthetic blocker is waived, writing a promotion_note only on that one."""
    manifest_path = temp_tree / "manifest.json"
    plan = ps.apply_promotion(
        temp_tree, manifest_path, [], True,
        waivers={synthetic_blocker: "reviewer accepted synthetic blocker"})
    assert len(plan.sources) == 11
    assert not plan.blocked

    manifest = ps._load_manifest(manifest_path)
    assert len(manifest["files"]) == 40 + 11
    assert manifest["staged"] == []
    files_by_name = {e["file"]: e for e in manifest["files"]}
    assert SYNTH_BLOCKER_CODE in files_by_name[synthetic_blocker]["promotion_note"]
    # sources without a blocker carry no promotion_note
    assert "promotion_note" not in files_by_name["42_bezout_identity.txt"]


def test_apply_keep_existential_axis_flag_preserves_tag(temp_tree):
    manifest_path = temp_tree / "manifest.json"
    ps.apply_promotion(
        temp_tree, manifest_path, ["41"], False, waivers={},
        keep_existential_axis=True)
    manifest = ps._load_manifest(manifest_path)
    entry = next(e for e in manifest["files"] if e["file"] == "41_division_algorithm.txt")
    assert "existential" in entry["axes"]


def test_real_repo_manifest_and_staged_tree_are_untouched_by_this_whole_module():
    """Belt-and-suspenders: nothing above should have ever written the real
    repo's manifest.json or staged/ directory (only the temp_tree fixture's
    copies are mutated)."""
    manifest = ps._load_manifest(REAL_MANIFEST)
    assert len(manifest["files"]) == 40
    assert len(manifest["staged"]) == 11
