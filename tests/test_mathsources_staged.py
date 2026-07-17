"""WP-SRC validation: the staged exogenous corpus (specs/mathsources/staged/).

Pure, LLM-free, tool-free.

STATUS -- PROMOTED (WP-SRC decided policy executed): the 11 staged exogenous
sources were promoted to top level (``manifest.staged`` -> ``manifest.files``,
files moved staged/ -> top level) with ``--keep-existential-axis``.  ``staged``
is therefore now EMPTY.  This module used to validate the quarantined staged
array; it now asserts the POST-promotion invariant instead:

  * ``manifest.staged`` is empty and ``staged/`` holds no ``.txt`` sources;
  * every one of the 11 formerly-staged sources landed in ``files`` and on disk
    at top level (the promotion actually happened -- not silently dropped);
  * the COMPRESSION.md §11.6 / T6b requirement (>= 2 exogenous exists-sources)
    is now satisfied from ``files`` (41-44 keep the ``existential`` axis), where
    the frozen ``test_mathsources_manifest.py`` quotas already cover them.

Any residual entries a future review re-stages under ``staged`` are still held
to the staged schema below, so the quarantine machinery stays tested even while
the array is empty.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common  # noqa: E402

MATHSOURCES = common.REPO_ROOT / "specs" / "mathsources"
MANIFEST = MATHSOURCES / "manifest.json"
STAGED = MATHSOURCES / "staged"

# axes valid in the frozen files-schema, plus the staging-only `existential` axis
FILES_VALID_AXES = {"side-condition", "ambient-ambiguity", "non-transcribable", "plain"}
STAGED_EXTRA_AXES = {"existential"}
IDIOM_PREFIX = "idiom:"
# fields the frozen `files` schema allows, plus staging-only metadata
BASE_FIELDS = {"file", "axes", "expect_transcribes", "miss_kind_guess"}
STAGED_FIELDS = BASE_FIELDS | {"existential", "binder_hint", "provenance", "staged_reason"}

# The 11 sources promoted out of staging by tools/promote_sources.py --all-staged
# --keep-existential-axis (the decided WP-SRC policy).  Pinned so this test proves
# the promotion actually landed rather than the sources vanishing.
PROMOTED = {
    "41_division_algorithm.txt", "42_bezout_identity.txt",
    "43_larger_integer_exists.txt", "44_divides_witness.txt",
    "45_cong_transitive.txt", "46_cong_add_const.txt",
    "47_cong_scalar_mul.txt", "48_db_sum.txt", "49_cd_combo_diff.txt",
    "50_even_times_even.txt", "51_goldbach.txt",
}
# Of those, the in-fragment existential witnesses that carried the `existential`
# axis and transcribe (COMPRESSION.md §11.6 / T6b: >= 2 exogenous exists-sources).
PROMOTED_EXISTENTIAL_WITNESSES = {
    "41_division_algorithm.txt", "42_bezout_identity.txt",
    "43_larger_integer_exists.txt", "44_divides_witness.txt",
}


def _load():
    with open(MANIFEST, encoding="utf-8") as fh:
        return json.load(fh)


def _staged(manifest):
    return sorted(manifest.get("staged", []), key=lambda e: e["file"])


# --------------------------------------------------------------------------- #
# post-promotion: staged is empty and inert
# --------------------------------------------------------------------------- #

def test_staged_is_empty_after_promotion():
    manifest = _load()
    assert manifest.get("staged", []) == [], \
        f"staged must be empty after WP-SRC promotion, got {manifest.get('staged')}"
    disk_staged = sorted(p.name for p in STAGED.glob("*.txt"))
    assert disk_staged == [], \
        f"staged/ must hold no .txt after promotion, got {disk_staged}"


def test_promotion_actually_landed():
    """Every formerly-staged source is now in files[] AND on disk at top level."""
    manifest = _load()
    files_names = {e["file"] for e in manifest["files"]}
    assert PROMOTED <= files_names, \
        f"promoted sources missing from files[]: {sorted(PROMOTED - files_names)}"
    for name in sorted(PROMOTED):
        p = MATHSOURCES / name
        assert p.is_file(), f"promoted source missing on disk at top level: {name}"
        assert p.read_text(encoding="utf-8").strip(), f"empty promoted source: {name}"
        assert not (STAGED / name).exists(), f"stale staged copy left behind: {name}"


def test_existential_witnesses_present_in_files():
    """COMPRESSION.md §11.6 / T6b hard requirement, now discharged from files[]:
    the in-fragment existential witnesses were promoted with the `existential`
    axis preserved (--keep-existential-axis)."""
    manifest = _load()
    by_file = {e["file"]: e for e in manifest["files"]}
    ex = [name for name in PROMOTED_EXISTENTIAL_WITNESSES
          if "existential" in by_file.get(name, {}).get("axes", [])
          and by_file.get(name, {}).get("expect_transcribes")]
    assert len(ex) >= 2, \
        f"expected >= 2 in-fragment existential witnesses in files[], got {sorted(ex)}"


# --------------------------------------------------------------------------- #
# schema of any residual staged array (empty today; machinery stays tested)
# --------------------------------------------------------------------------- #

def test_residual_staged_entries_are_well_shaped():
    """If a future review re-stages entries under `staged`, they must still obey
    the staged schema.  Vacuously true while staged is empty -- kept so the
    quarantine schema stays enforced the moment anything is re-staged."""
    manifest = _load()
    assert isinstance(manifest.get("staged", []), list), "staged must be a list"
    for entry in _staged(manifest):
        assert set(entry) <= STAGED_FIELDS, \
            f"{entry.get('file')}: unexpected keys {sorted(set(entry) - STAGED_FIELDS)}"
        assert isinstance(entry["file"], str) and entry["file"].endswith(".txt")
        assert isinstance(entry["axes"], list) and entry["axes"], \
            f"{entry['file']}: axes must be a non-empty list"
        assert isinstance(entry["expect_transcribes"], bool)
        for axis in entry["axes"]:
            ok = (axis in FILES_VALID_AXES or axis in STAGED_EXTRA_AXES
                  or axis.startswith(IDIOM_PREFIX))
            assert ok, f"{entry['file']}: unknown axis {axis!r}"
        is_nt = "non-transcribable" in entry["axes"]
        assert entry["expect_transcribes"] == (not is_nt), \
            f"{entry['file']}: expect_transcribes must be False iff non-transcribable"


def test_staged_bijection_holds_over_residual():
    """The manifest.staged <-> staged/*.txt bijection still holds (both empty
    today; asserted so a re-stage that forgets the file, or vice versa, fails)."""
    manifest = _load()
    manifest_files = sorted(e["file"] for e in manifest.get("staged", []))
    assert len(manifest_files) == len(set(manifest_files)), "duplicate staged file"
    disk_files = sorted(p.name for p in STAGED.glob("*.txt"))
    assert manifest_files == disk_files, (
        "staged manifest/disk mismatch:\n"
        f"  only in manifest: {sorted(set(manifest_files) - set(disk_files))}\n"
        f"  only on disk:     {sorted(set(disk_files) - set(manifest_files))}"
    )


def test_no_staged_entry_duplicates_a_toplevel_slot():
    """No residual staged entry may claim a top-level files[] slot (guards a
    re-stage that collides with a promoted source)."""
    manifest = _load()
    files_names = {e["file"] for e in manifest["files"]}
    staged_names = {e["file"] for e in manifest.get("staged", [])}
    assert not (files_names & staged_names), \
        f"staged entry duplicated in files[]: {sorted(files_names & staged_names)}"


def _run():
    tests = [
        test_staged_is_empty_after_promotion,
        test_promotion_actually_landed,
        test_existential_witnesses_present_in_files,
        test_residual_staged_entries_are_well_shaped,
        test_staged_bijection_holds_over_residual,
        test_no_staged_entry_duplicates_a_toplevel_slot,
    ]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"  PASS {t.__name__}")
    manifest = _load()
    print(f"\n{passed}/{len(tests)} tests passed; staged now empty "
          f"({len(manifest.get('staged', []))} entries), "
          f"{len(PROMOTED)} sources promoted to files[].")


if __name__ == "__main__":
    _run()
