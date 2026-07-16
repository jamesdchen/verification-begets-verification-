"""WP-SRC validation: the staged exogenous corpus (specs/mathsources/staged/).

Pure, LLM-free, tool-free.  Asserts that the manifest's ``staged`` array and the
files under ``staged/`` agree, that staged sources are inert with respect to the
committed-results globs (top-level ``.txt`` and ``dream/``), and that each staged
entry parses as the schema the reviewer will promote into ``files``.

This does NOT touch the frozen ``test_mathsources_manifest.py`` quotas — the
staged sources are held out of ``files`` on purpose (see staged/README.md), so
``EXPECTED_TOTAL = 40`` and the top-level bijection stay green untouched.
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


def _load():
    with open(MANIFEST, encoding="utf-8") as fh:
        return json.load(fh)


def _staged(manifest):
    return sorted(manifest.get("staged", []), key=lambda e: e["file"])


# --------------------------------------------------------------------------- #
# schema of the staged array
# --------------------------------------------------------------------------- #

def test_staged_key_present_and_shaped():
    manifest = _load()
    assert isinstance(manifest.get("staged"), list) and manifest["staged"], \
        "manifest.staged must be a non-empty list"
    assert isinstance(manifest.get("staged_note"), str) and manifest["staged_note"], \
        "manifest.staged_note (the human explanation) must be present"
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


def test_staged_expect_transcribes_partition():
    # same invariant the frozen test enforces on files: non-transcribable iff not expected
    for entry in _staged(_load()):
        is_nt = "non-transcribable" in entry["axes"]
        assert entry["expect_transcribes"] == (not is_nt), \
            f"{entry['file']}: expect_transcribes must be False iff non-transcribable"
        if is_nt:
            assert entry.get("miss_kind_guess"), \
                f"{entry['file']}: non-transcribable must carry a miss_kind_guess"
        else:
            assert "miss_kind_guess" not in entry, \
                f"{entry['file']}: miss_kind_guess only on non-transcribable"


def test_staged_provenance_recorded():
    for entry in _staged(_load()):
        prov = entry.get("provenance")
        assert isinstance(prov, dict), f"{entry['file']}: provenance block required"
        for k in ("reference", "url", "license", "verbatim"):
            assert prov.get(k), f"{entry['file']}: provenance.{k} required"
        assert prov["url"].startswith("http"), f"{entry['file']}: provenance.url must be a URL"


# --------------------------------------------------------------------------- #
# file <-> manifest bijection over staged/, and non-emptiness / verbatim
# --------------------------------------------------------------------------- #

def test_staged_file_manifest_bijection():
    manifest = _load()
    manifest_files = sorted(e["file"] for e in manifest["staged"])
    assert len(manifest_files) == len(set(manifest_files)), "duplicate staged file"
    disk_files = sorted(p.name for p in STAGED.glob("*.txt"))
    assert manifest_files == disk_files, (
        "staged manifest/disk mismatch:\n"
        f"  only in manifest: {sorted(set(manifest_files) - set(disk_files))}\n"
        f"  only on disk:     {sorted(set(disk_files) - set(manifest_files))}"
    )
    for name in manifest_files:
        p = STAGED / name
        assert p.is_file(), f"missing on disk: {name}"
        assert p.read_text(encoding="utf-8").strip(), f"empty staged source: {name}"


def test_staged_provenance_verbatim_is_substantive():
    """Provenance discipline: the recorded upstream `verbatim` must be a real,
    substantive statement (not a stub), so a reviewer can audit the rendering by
    hand.  We do NOT lexically match verbatim against the source text: the source
    files render operators as words ("plus", "divides", "modulo") while upstream
    quotes use symbols ("+", "|", "==="), so token overlap is meaningless.  The
    binding groundedness rule (reading quotes must be literal substrings of the
    SOURCE file, H44) is enforced later at the gated reading step by
    cgb._seed_math_readings, not here."""
    for entry in _staged(_load()):
        verb = entry["provenance"]["verbatim"].strip()
        assert len(verb.split()) >= 5, \
            f"{entry['file']}: provenance.verbatim too short to audit: {verb!r}"


# --------------------------------------------------------------------------- #
# inertness: staged sources must NOT be seen by the committed-results globs
# --------------------------------------------------------------------------- #

def test_staged_is_inert_to_toplevel_globs():
    """The whole point of staging: bench denominators, the ledger, and the frozen
    EXPECTED_TOTAL must not move.  The top-level and dream globs must not pick up
    anything under staged/."""
    toplevel = {p.name for p in MATHSOURCES.glob("*.txt")}
    staged = {p.name for p in STAGED.glob("*.txt")}
    assert not (toplevel & staged), \
        "a staged file name collides with a top-level source (glob would double-count)"
    # the frozen bijection is over MATHSOURCES.glob('*.txt') (top level only);
    # confirm staged files are not reachable by that non-recursive glob.
    assert staged, "expected staged sources present"
    assert all("/staged/" not in str(p.parent) or p.parent.name == "staged"
               for p in STAGED.glob("*.txt"))
    # and none of the staged entries claim a top-level slot in `files`
    files_names = {e["file"] for e in _load()["files"]}
    assert not (files_names & staged), "staged entry duplicated in files[]"


def test_at_least_two_existential_witnesses():
    """COMPRESSION.md 11.6 hard requirement for T6b: >= 2 exogenous exists-sources."""
    ex = [e for e in _staged(_load())
          if e.get("existential") and e.get("expect_transcribes")]
    assert len(ex) >= 2, \
        f"expected >= 2 in-fragment existential witnesses, got {[e['file'] for e in ex]}"


def _run():
    tests = [
        test_staged_key_present_and_shaped,
        test_staged_expect_transcribes_partition,
        test_staged_provenance_recorded,
        test_staged_file_manifest_bijection,
        test_staged_provenance_verbatim_is_substantive,
        test_staged_is_inert_to_toplevel_globs,
        test_at_least_two_existential_witnesses,
    ]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"  PASS {t.__name__}")
    manifest = _load()
    staged = _staged(manifest)
    ex = [e["file"] for e in staged if e.get("existential")]
    print(f"\n{passed}/{len(tests)} tests passed over {len(staged)} staged sources.")
    print(f"  existential: {ex}")


if __name__ == "__main__":
    _run()
