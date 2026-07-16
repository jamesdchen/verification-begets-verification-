"""tests/test_promote_sources.py -- checked promotion tool (tools/promote_sources.py).

Pure, LLM-free, tool-free.  Exercises the staged/ -> files[] promotion path
documented in specs/mathsources/staged/README.md and the WP-SRC review
to-dos recorded at merge 853dcee (see the docstring of
tools/promote_sources.py for the full mapping of items (a)-(d)).

House rule for this package: the tool MUTATES NOTHING unless invoked with an
explicit --apply flag, and --apply is exercised HERE ONLY against a temp
copy of specs/mathsources (never the real repo tree). Dry-run tests run
directly against the real repo's manifest/staged tree (read-only).
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
    # 43 and 44 are blocked -> non-zero exit even in dry-run mode (signal only)
    assert rc == 1


def test_dry_run_plan_names_valid_axes_and_provenance_blocker_for_43(capsys):
    manifest = _real_manifest()
    selected = ps.select_sources(manifest, ["43"], all_staged=False)
    readme_text = (REAL_MATHSOURCES / "staged" / "README.md").read_text(encoding="utf-8")
    plan = ps.build_plan(manifest, selected, readme_text,
                          keep_existential_axis=False, waivers={})
    text = ps.render_plan(plan)

    assert "43_larger_integer_exists.txt" in text
    assert "VALID_AXES" in text
    assert "existential" in text and "plain" in text
    # the provenance/composed-verbatim blocker must be named, not just implied
    assert "composed-verbatim" in text
    assert "provenance" in text.lower()
    assert plan.blocked  # 43 has an unresolved blocker by default


def test_dry_run_plan_names_nc_license_blocker_for_44():
    manifest = _real_manifest()
    selected = ps.select_sources(manifest, ["44"], all_staged=False)
    plan = ps.build_plan(manifest, selected, "", keep_existential_axis=False, waivers={})
    text = ps.render_plan(plan)
    assert "nc-license" in text
    assert "Non-Commercial" in text or "CC BY-NC-SA" in text
    assert plan.blocked


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

def test_apply_without_waiver_refuses_and_mutates_nothing(temp_tree):
    manifest_path = temp_tree / "manifest.json"
    before_manifest = manifest_path.read_bytes()
    before_staged = sorted(p.name for p in (temp_tree / "staged").glob("*.txt"))
    before_files = sorted(p.name for p in temp_tree.glob("*.txt"))

    with pytest.raises(ps.PromotionError, match="unresolved WP-SRC review blockers"):
        ps.apply_promotion(temp_tree, manifest_path, ["43"], False, waivers={})

    assert manifest_path.read_bytes() == before_manifest
    assert sorted(p.name for p in (temp_tree / "staged").glob("*.txt")) == before_staged
    assert sorted(p.name for p in temp_tree.glob("*.txt")) == before_files


def test_apply_with_waive_but_wrong_source_is_rejected(temp_tree):
    manifest_path = temp_tree / "manifest.json"
    # 45 has no recorded blockers -- waiving it should be refused (no waiving
    # into thin air; keeps waivers auditable/meaningful)
    with pytest.raises(ps.PromotionError, match="no recorded blockers"):
        ps.apply_promotion(temp_tree, manifest_path, ["45"], False,
                            waivers={"45_cong_transitive.txt": "not applicable"})


def test_apply_waive_requires_nonempty_reason(temp_tree):
    manifest_path = temp_tree / "manifest.json"
    with pytest.raises(ps.PromotionError, match="non-empty reason"):
        ps.apply_promotion(temp_tree, manifest_path, ["43"], False,
                            waivers={"43_larger_integer_exists.txt": "   "})


def test_apply_with_waiver_succeeds_and_writes_promotion_note(temp_tree):
    manifest_path = temp_tree / "manifest.json"
    reason = "reviewer confirmed the composed rendering against ProofWiki + Epp by hand; acceptable for promotion"
    plan = ps.apply_promotion(
        temp_tree, manifest_path, ["43"], False,
        waivers={"43_larger_integer_exists.txt": reason})
    assert not plan.blocked

    manifest = ps._load_manifest(manifest_path)
    files_by_name = {e["file"]: e for e in manifest["files"]}
    assert "43_larger_integer_exists.txt" in files_by_name
    promoted = files_by_name["43_larger_integer_exists.txt"]
    assert "promotion_note" in promoted
    assert reason in promoted["promotion_note"]
    assert "composed-verbatim" in promoted["promotion_note"]

    # staging-only fields must be gone from the promoted entry
    assert "provenance" not in promoted
    assert "staged_reason" not in promoted
    assert "binder_hint" not in promoted
    assert "existential" not in promoted

    # axis reconciliation: 'existential' retagged to 'plain' by default
    assert "existential" not in promoted["axes"]
    assert "plain" in promoted["axes"]

    # staged[] no longer contains the promoted entry
    staged_files = {e["file"] for e in manifest["staged"]}
    assert "43_larger_integer_exists.txt" not in staged_files


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


def test_apply_all_staged_with_both_waivers_is_all_or_nothing_and_valid(temp_tree):
    manifest_path = temp_tree / "manifest.json"
    plan = ps.apply_promotion(
        temp_tree, manifest_path, [], True,
        waivers={
            "43_larger_integer_exists.txt": "reviewer-confirmed composed rendering",
            "44_divides_witness.txt": "legal cleared the NC-licensed source for this corpus",
        })
    assert len(plan.sources) == 11

    manifest = ps._load_manifest(manifest_path)
    assert len(manifest["files"]) == 40 + 11
    assert manifest["staged"] == []

    manifest_files = sorted(e["file"] for e in manifest["files"])
    disk_files = sorted(p.name for p in temp_tree.glob("*.txt"))
    assert manifest_files == disk_files
    assert len(manifest_files) == len(set(manifest_files))

    # every promoted file's bytes match its original staged bytes
    for name in ("41_division_algorithm.txt", "42_bezout_identity.txt",
                 "43_larger_integer_exists.txt", "44_divides_witness.txt",
                 "51_goldbach.txt"):
        assert (temp_tree / name).is_file()
        assert not (temp_tree / "staged" / name).exists()


def test_apply_refuses_if_any_selected_source_in_batch_is_blocked(temp_tree):
    """--all-staged with only ONE of the two blockers waived must refuse
    entirely (all-or-nothing) and leave the temp tree untouched."""
    manifest_path = temp_tree / "manifest.json"
    before_manifest = manifest_path.read_bytes()
    before_staged = sorted(p.name for p in (temp_tree / "staged").glob("*.txt"))
    before_files = sorted(p.name for p in temp_tree.glob("*.txt"))

    with pytest.raises(ps.PromotionError):
        ps.apply_promotion(
            temp_tree, manifest_path, [], True,
            waivers={"43_larger_integer_exists.txt": "only this one waived"})

    assert manifest_path.read_bytes() == before_manifest
    assert sorted(p.name for p in (temp_tree / "staged").glob("*.txt")) == before_staged
    assert sorted(p.name for p in temp_tree.glob("*.txt")) == before_files


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
