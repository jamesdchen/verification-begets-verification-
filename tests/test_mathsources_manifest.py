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
* EXACTLY 4 files tagged ``non-transcribable``, each carrying a
  ``miss_kind_guess`` -- three distinct intended miss KINDS
  ``operator:prime`` / ``carrier:Real`` / ``kind:set-object`` over four
  entries: ``51_goldbach`` (WP-SRC promotion) shares ``38_infinitude_primes``'
  ``operator:prime`` miss, illustrating where the fragment's exists-reach ends
* the F5.3 flood idiom: its two ORIGINAL planted exogenous witnesses (which
  seeded the frozen 40-source bench) present at the top level plus 8
  system-origin dream paraphrases under ``dream/``; WP-SRC promotion may add
  further ``divides-both`` family members, so the top-level tally is a
  >= 2-witness FLOOR pinned by the two named originals, not an exact 2
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

# WP-SRC promotion (11 staged exogenous sources -> top level): 40 -> 51.
# S4a' (PLAN_REFLECT) exists-class corpus growth: +4 existential sources in
# slots 63-66 (52-62 are RESERVED by the WP-SRC2 staged batch): 51 -> 55.
# C2 (PLAN_FRAGMENT §3) census-sourced growth: +4 sources in slots 67-70,
# each the VERBATIM prose of a math2001 blueprint-census attempt-candidate
# (provenance in wp_c2_readings.py): 55 -> 59.  The number itself lives in
# the corpus-era registration (ONE re-baseline point for corpus growth).
import json as _json
with open(MATHSOURCES / "registration.json") as _fh:
    EXPECTED_TOTAL = _json.load(_fh)["n_top_level_sources"]
IDIOM_PREFIX = "idiom:"
NON_TRANSCRIBABLE = "non-transcribable"
# distinct miss KINDS (three); after the WP-SRC promotion 51_goldbach shares
# 38_infinitude_primes' operator:prime miss, so there are 4 non-transcribable
# ENTRIES over these 3 distinct kinds.
EXPECTED_MISSES = {"operator:prime", "carrier:Real", "kind:set-object"}
NON_TRANSCRIBABLE_TOTAL = 4  # was 3; 51_goldbach promoted (operator:prime, dup of 38)
VALID_AXES = {
    "side-condition",
    "ambient-ambiguity",
    NON_TRANSCRIBABLE,
    "plain",
    # 'existential' preserved at promotion (--keep-existential-axis, the decided
    # WP-SRC policy) on 41-44; the frozen VALID_AXES set gains it here.
    "existential",
}  # plus any "idiom:<name>"

# The two ORIGINAL F5.3 flood witnesses that seeded the frozen 40-source bench
# run (results/formalize_bench_state.jsonl).  WP-SRC promotion grew the
# divides-both family (44_divides_witness, 48_db_sum also carry idiom:divides-both),
# so the flood idiom now tags >2 top-level files; but the F5.3 two-witness
# abbreviation plant is these two, and the frozen bench rests on exactly them.
FROZEN_FLOOD_WITNESSES = {"36_db_gcd.txt", "37_db_diff.txt"}


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
    witnesses = set(idioms[flood])
    # F5.3: the two-witness abbreviation the governed arm admits.  The two
    # ORIGINAL planted witnesses (which seeded the frozen 40-source bench) must
    # still be present; WP-SRC promotion adds further divides-both family members
    # (44_divides_witness, 48_db_sum), so the top-level tally is a >= 2 FLOOR
    # pinned by the two named originals rather than an exact 2.
    assert FROZEN_FLOOD_WITNESSES <= witnesses, \
        f"F5.3 flood plant {sorted(FROZEN_FLOOD_WITNESSES)} missing from {sorted(witnesses)}"
    assert len(witnesses) >= 2, \
        f"flood idiom {flood!r} needs the >= 2-witness abbreviation, got {sorted(witnesses)}"
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
    assert len(nt) == NON_TRANSCRIBABLE_TOTAL, \
        f"expected EXACTLY {NON_TRANSCRIBABLE_TOTAL} non-transcribable files, got {len(nt)}"
    for entry in nt:
        assert entry["expect_transcribes"] is False, \
            f"{entry['file']}: non-transcribable must have expect_transcribes=false"
        assert entry.get("miss_kind_guess"), \
            f"{entry['file']}: non-transcribable must carry a miss_kind_guess"
    misses = sorted(e["miss_kind_guess"] for e in nt)
    # three DISTINCT miss kinds across the four entries ...
    assert set(misses) == EXPECTED_MISSES, \
        f"expected miss kinds {sorted(EXPECTED_MISSES)}, got {sorted(set(misses))}"
    # ... with 51_goldbach (WP-SRC) recorded alongside 38_infinitude_primes on
    # the shared operator:prime miss (the fragment's exists-reach boundary).
    from collections import Counter
    assert Counter(misses)["operator:prime"] == 2, \
        f"38_infinitude_primes + 51_goldbach both miss operator:prime, got {sorted(misses)}"
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
