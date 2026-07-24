"""WP-HOLDOUT validation: the contamination-resistant held-out exogenous set
(specs/mathsources/holdout/) — COMPRESSION.md §11.7 / §12 precondition.

Pure, LLM-free, tool-free.  Everything is asserted FROM ``manifest.json``'s
``holdout`` array plus a bijection against the ``.txt`` files on disk under
``holdout/``.  Iteration is sorted throughout, so the test is deterministic.

What is pinned:

* **schema** — every ``holdout`` entry is well-shaped (the ``files`` fields plus
  the two staging-style blocks ``provenance`` and ``curation``);
* **bijection** — ``manifest.holdout`` ↔ ``holdout/*.txt`` on disk, no orphan
  either way, every file non-empty;
* **INERTNESS** — no *live* top-level glob reaches ``holdout/`` (the promotion
  review established top-level-only globs; this pins the same guarantee for
  ``holdout/`` that ``staged/`` enjoys), and there is no ``rglob``/``**`` over
  ``specs/mathsources`` in the shipped corpus/ledger/bench code;
* **provenance completeness** — reference/url/license/verbatim present on every
  entry; ``verified_via`` present (snippet-concordant vs direct-fetch recorded);
  ``rendering_note`` present wherever the source text is an adaptation;
* **curation-log completeness** — every entry carries the neutral-rule fields
  (``neutral_rule``/``source_walk``/``walk_index``/``block``/``disposition``/
  ``in_fragment``); ``expect_transcribes`` and the non-transcribable
  ``miss_kind_guess`` are consistent with ``in_fragment``;
* **parse/groundedness spot-check** — each source text is a plain (non-JSON)
  sentence that normalizes non-empty under the fragment's own ``_norm`` (the
  same normalizer parse_math_reading's groundedness check uses).  No candidate
  READING exists yet (authoring is a later gated step), so verbatim-substring
  quote checks are deliberately NOT performed — there is nothing to quote
  against.

None of these touch the frozen ``files`` schema or ``test_mathsources_manifest``'s
``EXPECTED_TOTAL`` — the holdout array is a separate, append-only structure.
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common  # noqa: E402

MATHSOURCES = common.REPO_ROOT / "specs" / "mathsources"
MANIFEST = MATHSOURCES / "manifest.json"
HOLDOUT = MATHSOURCES / "holdout"

# §11.7 asks for ~20 held-out readings; this set is exactly 20.
EXPECTED_HOLDOUT_TOTAL = 20

# Reuse the frozen files-schema axis vocabulary, plus the staging-style
# `existential` axis and idiom:<name>.  Kept as a local pin so a change to the
# holdout's allowed axes is a visible edit here.
VALID_AXES = {"side-condition", "ambient-ambiguity", "non-transcribable",
              "plain", "existential"}
IDIOM_PREFIX = "idiom:"

BASE_FIELDS = {"file", "axes", "expect_transcribes", "miss_kind_guess"}
HOLDOUT_FIELDS = BASE_FIELDS | {"provenance", "curation"}
PROV_REQUIRED = {"reference", "url", "license", "verbatim"}
PROV_OPTIONAL = {"rendering_note", "verified_via"}
CURATION_REQUIRED = {"neutral_rule", "source_walk", "walk_index", "block",
                     "disposition", "in_fragment"}


def _load():
    with open(MANIFEST, encoding="utf-8") as fh:
        return json.load(fh)


def _holdout(manifest):
    return sorted(manifest.get("holdout", []), key=lambda e: e["file"])


# --------------------------------------------------------------------------- #
# schema + total + bijection
# --------------------------------------------------------------------------- #

def test_holdout_present_and_sized():
    manifest = _load()
    assert isinstance(manifest.get("holdout"), list), "manifest.holdout must be a list"
    entries = _holdout(manifest)
    assert len(entries) == EXPECTED_HOLDOUT_TOTAL, \
        f"expected {EXPECTED_HOLDOUT_TOTAL} holdout entries, got {len(entries)}"
    # ~20 in-fragment sources: the transcribable majority + an honest handful of
    # non-transcribable boundary cases (never zero — the neutral rule surfaced them).
    nt = [e for e in entries if not e["expect_transcribes"]]
    assert 1 <= len(nt) <= 6, \
        f"expected a small honest non-transcribable minority, got {len(nt)}"


def test_holdout_entry_schema():
    for entry in _holdout(_load()):
        f = entry["file"]
        assert set(entry) <= HOLDOUT_FIELDS, \
            f"{f}: unexpected keys {sorted(set(entry) - HOLDOUT_FIELDS)}"
        assert isinstance(f, str) and f.endswith(".txt")
        assert isinstance(entry["axes"], list) and entry["axes"], \
            f"{f}: axes must be a non-empty list"
        assert isinstance(entry["expect_transcribes"], bool)
        for axis in entry["axes"]:
            assert axis in VALID_AXES or axis.startswith(IDIOM_PREFIX), \
                f"{f}: unknown axis {axis!r}"
        is_nt = "non-transcribable" in entry["axes"]
        assert entry["expect_transcribes"] == (not is_nt), \
            f"{f}: expect_transcribes must be False iff non-transcribable"
        if is_nt:
            assert entry.get("miss_kind_guess"), \
                f"{f}: a non-transcribable holdout must carry a miss_kind_guess"
        else:
            assert "miss_kind_guess" not in entry, \
                f"{f}: miss_kind_guess only allowed on non-transcribable entries"


def test_holdout_bijection():
    manifest = _load()
    manifest_files = sorted(e["file"] for e in manifest.get("holdout", []))
    assert len(manifest_files) == len(set(manifest_files)), "duplicate holdout file"
    disk_files = sorted(p.name for p in HOLDOUT.glob("*.txt"))
    assert manifest_files == disk_files, (
        "holdout manifest/disk mismatch:\n"
        f"  only in manifest: {sorted(set(manifest_files) - set(disk_files))}\n"
        f"  only on disk:     {sorted(set(disk_files) - set(manifest_files))}"
    )
    for name in manifest_files:
        p = HOLDOUT / name
        assert p.is_file(), f"missing on disk: {name}"
        assert p.read_text(encoding="utf-8").strip(), f"empty holdout source: {name}"


def test_no_holdout_entry_duplicates_a_toplevel_or_staged_slot():
    manifest = _load()
    hold = {e["file"] for e in manifest.get("holdout", [])}
    files_names = {e["file"] for e in manifest["files"]}
    staged_names = {e["file"] for e in manifest.get("staged", [])}
    assert not (hold & files_names), \
        f"holdout entry collides with files[]: {sorted(hold & files_names)}"
    assert not (hold & staged_names), \
        f"holdout entry collides with staged[]: {sorted(hold & staged_names)}"


# --------------------------------------------------------------------------- #
# provenance + curation completeness (the point of the exercise)
# --------------------------------------------------------------------------- #

def test_provenance_completeness():
    for entry in _holdout(_load()):
        f = entry["file"]
        prov = entry.get("provenance")
        assert isinstance(prov, dict), f"{f}: provenance block required"
        assert PROV_REQUIRED <= set(prov), \
            f"{f}: provenance missing {sorted(PROV_REQUIRED - set(prov))}"
        assert set(prov) <= (PROV_REQUIRED | PROV_OPTIONAL), \
            f"{f}: provenance has unexpected keys {sorted(set(prov) - PROV_REQUIRED - PROV_OPTIONAL)}"
        for k in PROV_REQUIRED:
            assert isinstance(prov[k], str) and prov[k].strip(), \
                f"{f}: provenance.{k} must be a non-empty string"
        # rule (a): a DIFFERENT reference work than the main corpus's
        # (ProofWiki / Wikipedia / LibreTexts).
        low = (prov["reference"] + " " + prov["url"]).lower()
        for banned in ("proofwiki", "wikipedia", "libretexts"):
            assert banned not in low, \
                f"{f}: holdout must not reuse the main corpus's reference works ({banned})"
        # verification provenance is recorded (snippet-concordant vs direct-fetch)
        assert prov.get("verified_via", "").strip(), \
            f"{f}: verified_via must record how the quote was checked"


def test_rendering_note_present_when_adapted():
    """Every taken source here is a disclosed adaptation of Euclid's terse
    wording (measures->divides, existential unfolding, ambient choice), so each
    carries a rendering_note.  Pins the honesty clause: no silent composition."""
    for entry in _holdout(_load()):
        f = entry["file"]
        prov = entry["provenance"]
        assert prov.get("rendering_note", "").strip(), \
            f"{f}: an adapted source must disclose the adaptation in rendering_note"


def test_curation_log_completeness():
    seen_index = {}
    for entry in _holdout(_load()):
        f = entry["file"]
        cur = entry.get("curation")
        assert isinstance(cur, dict), f"{f}: curation block required"
        assert CURATION_REQUIRED <= set(cur), \
            f"{f}: curation missing {sorted(CURATION_REQUIRED - set(cur))}"
        assert cur["neutral_rule"] == "sequential-canonical-order", \
            f"{f}: neutral_rule must name the stated selection rule"
        assert isinstance(cur["source_walk"], str) and cur["source_walk"].strip()
        assert isinstance(cur["walk_index"], int) and not isinstance(cur["walk_index"], bool), \
            f"{f}: walk_index must be an int (encounter position in the canonical walk)"
        assert isinstance(cur["block"], str) and cur["block"].strip()
        assert cur["disposition"] in {"take-transcribable", "take-non-transcribable"}, \
            f"{f}: disposition {cur['disposition']!r} must be a 'take-*' (skips are logged in README, not committed)"
        assert isinstance(cur["in_fragment"], bool)
        # curation.in_fragment must agree with expect_transcribes and disposition
        assert cur["in_fragment"] == entry["expect_transcribes"], \
            f"{f}: curation.in_fragment must match expect_transcribes"
        assert (cur["disposition"] == "take-non-transcribable") == (not entry["expect_transcribes"]), \
            f"{f}: disposition must agree with expect_transcribes"
        seen_index.setdefault((cur["block"], cur["walk_index"]), []).append(f)
    # walk positions are unique within a block (a real sequential walk visits each once)
    dupes = {k: v for k, v in seen_index.items() if len(v) > 1}
    assert not dupes, f"duplicate (block, walk_index) in the curation log: {dupes}"


# --------------------------------------------------------------------------- #
# INERTNESS — no live glob reaches holdout/ (mirrors the staged/ guarantee)
# --------------------------------------------------------------------------- #

def test_holdout_inert_under_toplevel_globs():
    """The corpus/ledger/bench enumerations are top-level `*.txt` (+ explicit
    dream/, readings/).  A file under holdout/ must appear in NONE of them, so
    committing this set cannot shift bench denominators or the ledger base."""
    hold_names = {p.name for p in HOLDOUT.glob("*.txt")}
    assert hold_names, "no holdout sources on disk to check inertness against"

    # the exact enumerations the shipped code runs over specs/mathsources:
    toplevel = {p.name for p in MATHSOURCES.glob("*.txt")}           # bench, cgb, demo, manifest bijection
    dreams = {p.name for p in (MATHSOURCES / "dream").glob("*.txt")}  # cgb dream, bench dreams
    readings = set()
    rdir = MATHSOURCES / "readings"
    if rdir.exists():
        readings = {p.name for p in rdir.glob("*.json")}

    assert not (hold_names & toplevel), \
        f"holdout leaked into the top-level *.txt glob: {sorted(hold_names & toplevel)}"
    assert not (hold_names & dreams), \
        f"holdout leaked into dream/: {sorted(hold_names & dreams)}"
    assert not (hold_names & readings), \
        f"holdout leaked into readings/: {sorted(hold_names & readings)}"

    # and holdout is NOT in the frozen files-bijection denominator
    manifest = _load()
    files_names = {e["file"] for e in manifest["files"]}
    assert not (hold_names & files_names), \
        "a holdout .txt is listed in manifest.files — it must stay in `holdout` only"


def test_no_recursive_glob_over_mathsources_in_shipped_code():
    """Pins the promotion review's finding — the corpus/ledger/bench globs are
    top-level only.  A future `rglob`/`**` over specs/mathsources would silently
    pull holdout/ (and staged/, dream/) into the corpus; refuse it here."""
    suspects = ["bench/bench_formalize.py", "cgb.py", "demos/demo_ledger.py"]
    pat = re.compile(r"(rglob\s*\(|glob\s*\(\s*[\"']\*\*)")
    for name in suspects:
        path = common.REPO_ROOT / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        # only flag recursive globs in files that actually touch mathsources
        if "mathsources" not in text:
            continue
        assert not pat.search(text), \
            f"{name}: a recursive glob (rglob/**) over the tree would reach holdout/ — " \
            "keep the corpus enumeration top-level only"


# --------------------------------------------------------------------------- #
# parse / groundedness spot-check (no candidate reading needed)
# --------------------------------------------------------------------------- #

def test_sources_are_plain_sentences_normalizing_nonempty():
    """Groundedness machinery spot-check WITHOUT a candidate reading: each source
    is plain prose (not a reading envelope / not JSON) that normalizes non-empty
    under the fragment's own `_norm` — the normalizer parse_math_reading uses when
    it checks that a quote occurs in the source.  Verbatim-substring quote checks
    are intentionally omitted: no readings exist yet, so there is nothing to
    quote against."""
    from generators import math_reading  # the fragment module (F-G source of truth)
    norm = math_reading._norm
    for entry in _holdout(_load()):
        f = entry["file"]
        text = (HOLDOUT / f).read_text(encoding="utf-8")
        assert norm(text).strip(), f"{f}: source normalizes empty"
        stripped = text.strip()
        assert not (stripped.startswith("{") or stripped.startswith("[")), \
            f"{f}: a source is a plain sentence, not a JSON reading/envelope"
        # the manifest verbatim is a real (non-empty) upstream quote, and the
        # rendered source shares the statement's key nouns — a light sanity tie
        # between the committed .txt and the cited provenance (not a substring law).
        verbatim = entry["provenance"]["verbatim"]
        assert len(verbatim.split()) >= 4, f"{f}: verbatim quote implausibly short"


# --------------------------------------------------------------------------- #
# script entry point (mirrors the sibling manifest tests)
# --------------------------------------------------------------------------- #

def _run():
    tests = [
        test_holdout_present_and_sized,
        test_holdout_entry_schema,
        test_holdout_bijection,
        test_no_holdout_entry_duplicates_a_toplevel_or_staged_slot,
        test_provenance_completeness,
        test_rendering_note_present_when_adapted,
        test_curation_log_completeness,
        test_holdout_inert_under_toplevel_globs,
        test_no_recursive_glob_over_mathsources_in_shipped_code,
        test_sources_are_plain_sentences_normalizing_nonempty,
    ]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"  PASS {t.__name__}")
    manifest = _load()
    entries = _holdout(manifest)
    nt = [e for e in entries if not e["expect_transcribes"]]
    print(f"\n{passed}/{len(tests)} tests passed over {len(entries)} holdout sources "
          f"({len(entries) - len(nt)} transcribable, {len(nt)} non-transcribable).")


if __name__ == "__main__":
    _run()
