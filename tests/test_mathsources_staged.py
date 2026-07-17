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

WP-SRC2 UPDATE (this batch re-fills ``staged``): COMPRESSION.md §11.12 pinned
the *post-promotion* state as ``staged`` empty.  The WP-SRC2 review batch
(sources 52-62) deliberately re-populates ``staged`` with 11 new exogenous,
citation-carrying sources awaiting the next reviewer-gated promotion.  So the
"empty forever" assertion no longer holds by design.  Rather than delete the
tooth, ``test_staged_is_empty_after_promotion`` was CONVERTED into
``test_staged_pins_wp_src2_batch``: it now pins the exact WP-SRC2 staged
membership (``WP_SRC2_STAGED``) on both the manifest side and disk.  The
§11.12 empty-state invariant is preserved as the documented base case, and the
next promotion (which empties ``staged`` again) will fail this pin loudly,
forcing the promoter to consciously update ``WP_SRC2_STAGED`` (back to the
empty set, or to whatever the *next* batch stages).  The bijection and
no-top-level-collision invariants the original test leaned on are independently
enforced by ``test_staged_bijection_holds_over_residual`` and
``test_no_staged_entry_duplicates_a_toplevel_slot`` below.
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

# The WP-SRC2 batch currently held under `staged` (sources 52-62), awaiting the
# next reviewer-gated promotion.  §11.12's post-promotion invariant is `staged`
# empty; this batch re-fills it, so the pin below is set to THIS batch's exact
# membership.  When the next promotion empties `staged`, `test_staged_pins_
# wp_src2_batch` will fail until this constant is updated (to the empty set, or
# to the next batch) -- the deliberate forcing function replacing "empty forever".
WP_SRC2_STAGED = {
    "52_archimedean.txt", "53_additive_inverse.txt", "54_common_multiple.txt",
    "55_solvable_addition.txt", "56_parity_dichotomy.txt",
    "57_cong_divides_diff.txt", "58_divides_zero.txt", "59_gcd_commutative.txt",
    "60_gcd_zero.txt", "61_square_mod_four.txt", "62_gcd_divides.txt",
}


def _load():
    with open(MANIFEST, encoding="utf-8") as fh:
        return json.load(fh)


def _staged(manifest):
    return sorted(manifest.get("staged", []), key=lambda e: e["file"])


# --------------------------------------------------------------------------- #
# staged membership pin (§11.12 base case: empty; WP-SRC2 re-fill: these 11)
# --------------------------------------------------------------------------- #

def test_staged_pins_wp_src2_batch():
    """Successor to ``test_staged_is_empty_after_promotion``.

    COMPRESSION.md §11.12 pinned the post-promotion state as ``staged`` empty.
    The WP-SRC2 batch (52-62) re-fills it by design, so this tooth now pins the
    EXACT WP-SRC2 membership on both the manifest side and disk.  The empty set
    is the documented §11.12 base case; the next promotion empties ``staged``
    again and MUST update ``WP_SRC2_STAGED`` (this assertion fails until it
    does -- the forcing function that replaces "empty forever")."""
    manifest = _load()
    manifest_staged = {e["file"] for e in manifest.get("staged", [])}
    assert manifest_staged == WP_SRC2_STAGED, (
        "manifest.staged membership does not match the pinned WP-SRC2 batch:\n"
        f"  unexpected in manifest: {sorted(manifest_staged - WP_SRC2_STAGED)}\n"
        f"  missing from manifest:  {sorted(WP_SRC2_STAGED - manifest_staged)}\n"
        "  (if a promotion just emptied staged, update WP_SRC2_STAGED to the "
        "new batch -- the empty set for the §11.12 post-promotion base case)"
    )
    disk_staged = {p.name for p in STAGED.glob("*.txt")}
    assert disk_staged == WP_SRC2_STAGED, (
        "staged/ on-disk membership does not match the pinned WP-SRC2 batch:\n"
        f"  unexpected on disk: {sorted(disk_staged - WP_SRC2_STAGED)}\n"
        f"  missing on disk:    {sorted(WP_SRC2_STAGED - disk_staged)}"
    )


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
        test_staged_pins_wp_src2_batch,
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
    print(f"\n{passed}/{len(tests)} tests passed; staged holds the WP-SRC2 batch "
          f"({len(manifest.get('staged', []))} entries pinned to WP_SRC2_STAGED), "
          f"{len(PROMOTED)} sources from the prior WP-SRC batch promoted to files[].")


if __name__ == "__main__":
    _run()
