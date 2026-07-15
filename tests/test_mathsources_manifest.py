"""WP-C quota test: the math-sources corpus manifest is the cross-WP freeze (F-D).

Pure, LLM-free, tool-free.  Everything is asserted FROM ``manifest.json`` (the
F5.1 / F-D freeze that F4's teeth, F4.2's report, and F5.3's plant selection
read), plus a bijection against the ``.txt`` files actually on disk.  Iteration
is sorted throughout, so the test is deterministic.

Engineered quotas (FORMALIZATION.md F5.1):

* >= 8 files tagged ``side-condition``   (implicit side conditions)
* >= 5 files tagged ``ambient-ambiguity`` (Nat-vs-Int truth flips)
* recurring idioms: each non-flood ``idiom:<name>`` in >= 3 distinct files,
  >= 2 distinct idiom names, >= 6 files carrying a recurring idiom
* EXACTLY 3 files tagged ``non-transcribable``, each carrying a
  ``miss_kind_guess`` -- the three intended misses are
  ``operator:prime`` / ``carrier:Real`` / ``kind:set-object``
* the F5.3 flood idiom: EXACTLY 2 exogenous witnesses at the top level plus
  8 system-origin dream paraphrases under ``dream/``
* the remainder tagged ``plain`` so coverage numbers mean something
* file <-> manifest bijection over the top-level ``.txt`` files

The flood idiom is deliberately EXEMPT from the ">= 3 files" rule: F5.3 pins it
to exactly two exogenous witnesses (the two-witness abbreviation the governed
arm admits) with the recurrence supplied by the eight dreams.  It is named by
the manifest's top-level ``flood_idiom`` key so the exemption is data, not a
hard-coded string.
"""
from __future__ import annotations

import json
import os
import sys

# Make the repo root importable when run directly (pytest's conftest also does).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common  # noqa: E402

MATHSOURCES = common.REPO_ROOT / "specs" / "mathsources"
MANIFEST = MATHSOURCES / "manifest.json"
DREAM = MATHSOURCES / "dream"

EXPECTED_TOTAL = 40
IDIOM_PREFIX = "idiom:"
NON_TRANSCRIBABLE = "non-transcribable"
EXPECTED_MISSES = {"operator:prime", "carrier:Real", "kind:set-object"}
VALID_AXES = {
    "side-condition",
    "ambient-ambiguity",
    NON_TRANSCRIBABLE,
    "plain",
}  # plus any "idiom:<name>"


def _load_manifest():
    with open(MANIFEST, encoding="utf-8") as fh:
        return json.load(fh)


def _files(manifest):
    # sorted by filename -> deterministic iteration
    return sorted(manifest["files"], key=lambda e: e["file"])


def _axis_tally(manifest):
    tally = {}
    for entry in _files(manifest):
        for axis in sorted(entry["axes"]):
            tally.setdefault(axis, []).append(entry["file"])
    return tally


def _idiom_files(manifest):
    """name -> sorted list of files carrying idiom:<name>."""
    out = {}
    for entry in _files(manifest):
        for axis in sorted(entry["axes"]):
            if axis.startswith(IDIOM_PREFIX):
                out.setdefault(axis[len(IDIOM_PREFIX):], []).append(entry["file"])
    return {k: sorted(v) for k, v in out.items()}


# --------------------------------------------------------------------------- #
# schema + bijection
# --------------------------------------------------------------------------- #

def test_manifest_shape_and_total():
    manifest = _load_manifest()
    assert isinstance(manifest, dict)
    assert isinstance(manifest.get("files"), list)
    assert "flood_idiom" in manifest and isinstance(manifest["flood_idiom"], str)
    files = _files(manifest)
    assert len(files) == EXPECTED_TOTAL, \
        f"expected {EXPECTED_TOTAL} manifest entries, got {len(files)}"
    for entry in files:
        assert set(entry) <= {"file", "axes", "expect_transcribes", "miss_kind_guess"}
        assert isinstance(entry["file"], str) and entry["file"].endswith(".txt")
        assert isinstance(entry["axes"], list) and entry["axes"], \
            f"{entry['file']}: axes must be a non-empty list"
        assert isinstance(entry["expect_transcribes"], bool)
        for axis in entry["axes"]:
            assert axis in VALID_AXES or axis.startswith(IDIOM_PREFIX), \
                f"{entry['file']}: unknown axis {axis!r}"


def test_file_manifest_bijection():
    manifest = _load_manifest()
    manifest_files = sorted(e["file"] for e in manifest["files"])
    assert len(manifest_files) == len(set(manifest_files)), "duplicate file in manifest"
    disk_files = sorted(
        p.name for p in MATHSOURCES.glob("*.txt")  # top level only; dreams are separate
    )
    assert manifest_files == disk_files, (
        "manifest/disk mismatch:\n"
        f"  only in manifest: {sorted(set(manifest_files) - set(disk_files))}\n"
        f"  only on disk:     {sorted(set(disk_files) - set(manifest_files))}"
    )
    # every listed file exists and is non-empty
    for name in manifest_files:
        p = MATHSOURCES / name
        assert p.is_file(), f"missing on disk: {name}"
        assert p.read_text(encoding="utf-8").strip(), f"empty source file: {name}"


# --------------------------------------------------------------------------- #
# engineered quotas
# --------------------------------------------------------------------------- #

def test_side_condition_quota():
    tally = _axis_tally(_load_manifest())
    n = len(tally.get("side-condition", []))
    assert n >= 8, f"expected >= 8 side-condition files, got {n}"


def test_ambient_ambiguity_quota():
    tally = _axis_tally(_load_manifest())
    n = len(tally.get("ambient-ambiguity", []))
    assert n >= 5, f"expected >= 5 ambient-ambiguity files, got {n}"


def test_recurring_idiom_quota():
    manifest = _load_manifest()
    flood = manifest["flood_idiom"]
    idioms = _idiom_files(manifest)
    assert len(idioms) >= 2, \
        f"expected >= 2 distinct idiom names, got {sorted(idioms)}"
    recurring = {name: files for name, files in idioms.items() if name != flood}
    assert len(recurring) >= 2, \
        f"expected >= 2 recurring (non-flood) idioms, got {sorted(recurring)}"
    for name in sorted(recurring):
        files = recurring[name]
        assert len(files) >= 3, \
            f"idiom:{name} must appear in >= 3 files, got {len(files)}: {files}"
    covered = sorted({f for files in recurring.values() for f in files})
    assert len(covered) >= 6, \
        f"expected >= 6 files sharing recurring idioms, got {len(covered)}: {covered}"


def test_flood_idiom_plant():
    manifest = _load_manifest()
    flood = manifest["flood_idiom"]
    idioms = _idiom_files(manifest)
    assert flood in idioms, f"flood_idiom {flood!r} tagged on no file"
    witnesses = idioms[flood]
    # F5.3: exactly two exogenous witnesses (the two-witness abbreviation).
    assert len(witnesses) == 2, \
        f"flood idiom {flood!r} needs exactly 2 exogenous witnesses, got {witnesses}"
    manifest_by_file = {e["file"]: e for e in manifest["files"]}
    for w in witnesses:
        assert manifest_by_file[w]["expect_transcribes"] is True, \
            f"flood witness {w} should transcribe"
    # ...and eight system-origin dream paraphrases under dream/.
    dreams = sorted(p.name for p in DREAM.glob("d*.txt"))
    assert len(dreams) == 8, f"expected 8 dream paraphrases, got {len(dreams)}: {dreams}"
    assert (DREAM / "README.txt").is_file(), "dream/README.txt (system-origin note) missing"


def test_non_transcribable_quota_and_misses():
    manifest = _load_manifest()
    files = _files(manifest)
    nt = [e for e in files if NON_TRANSCRIBABLE in e["axes"]]
    assert len(nt) == 3, f"expected EXACTLY 3 non-transcribable files, got {len(nt)}"
    for entry in nt:
        assert entry["expect_transcribes"] is False, \
            f"{entry['file']}: non-transcribable must have expect_transcribes=false"
        assert entry.get("miss_kind_guess"), \
            f"{entry['file']}: non-transcribable must carry a miss_kind_guess"
    misses = sorted(e["miss_kind_guess"] for e in nt)
    assert set(misses) == EXPECTED_MISSES, \
        f"expected misses {sorted(EXPECTED_MISSES)}, got {misses}"
    # miss_kind_guess appears ONLY on non-transcribable entries
    for entry in files:
        if NON_TRANSCRIBABLE not in entry["axes"]:
            assert "miss_kind_guess" not in entry, \
                f"{entry['file']}: miss_kind_guess only allowed on non-transcribable"


def test_expect_transcribes_partition():
    manifest = _load_manifest()
    files = _files(manifest)
    for entry in files:
        is_nt = NON_TRANSCRIBABLE in entry["axes"]
        assert entry["expect_transcribes"] == (not is_nt), (
            f"{entry['file']}: expect_transcribes must be False iff non-transcribable"
        )


def test_plain_remainder_exists():
    tally = _axis_tally(_load_manifest())
    plain = tally.get("plain", [])
    assert plain, "no plain files -- coverage numbers would be meaningless"


# --------------------------------------------------------------------------- #
# script entry point (mirrors tests/test_reading_corpus.py)
# --------------------------------------------------------------------------- #

def _run():
    tests = [
        test_manifest_shape_and_total,
        test_file_manifest_bijection,
        test_side_condition_quota,
        test_ambient_ambiguity_quota,
        test_recurring_idiom_quota,
        test_flood_idiom_plant,
        test_non_transcribable_quota_and_misses,
        test_expect_transcribes_partition,
        test_plain_remainder_exists,
    ]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"  PASS {t.__name__}")
    manifest = _load_manifest()
    tally = _axis_tally(manifest)
    print(f"\n{passed}/{len(tests)} tests passed over {len(manifest['files'])} sources.")
    for axis in sorted(tally):
        print(f"  {axis}: {len(tally[axis])}")


if __name__ == "__main__":
    _run()
