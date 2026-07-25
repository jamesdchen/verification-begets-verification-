"""Teeth for specs/mathsources/provenance.json (the wp_ scripts' evidence, checked).

WHAT THIS ADDS, AND WHY IT IS STRONGER.  The census-sourced additions of
cycles c2-c17 were introduced by 17 one-shot session scripts
(`wp_c*_readings.py`, `wp_auth_readings.py`).  Each carried, in a module-level
`PROVENANCE` dict or in its docstring, the claim that a committed source's
prose IS the verbatim prose of a named census node -- and 47 of those rows
even pinned `sha256` of that node's text.  NOTHING READ ANY OF IT.  The
scripts were spent the moment their readings landed in `specs/`, so the
strongest evidence in them was never checked by anything, which is the exact
defect this repo keeps logging: a claim that stopped tracking its evidence.

So the claims are consolidated into a DERIVED record and checked: these teeth
re-derive every pinned sha from the corpus's own `nodes.jsonl` on every run.
A corpus that drifts, a source misattributed to the wrong node, or a row
quietly edited to make coverage look better all redden HERE.

THE SCRIPTS ARE NOT RETIRED, and an attempt to retire them measured exactly
why not: `wp_auth_readings.py` is imported by PRODUCTION code (`run/anchor.py`,
`bench/bench_hammer.py`), and `tools/intake_from_frontier.py` allocates the
next cycle's index by SCANNING repo root for `wp_c<N>_readings.py`, so an
empty root silently resets that counter to c2 and collides with cycle 2's
identity in every historical receipt.  They remain the source of truth; this
artifact is a reading of them, regenerated and byte-compared below.
"""
import hashlib
import json
import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

MATHSOURCES = os.path.join(_ROOT, "specs", "mathsources")
ARTIFACT = os.path.join(MATHSOURCES, "provenance.json")


@pytest.fixture(scope="module")
def doc():
    with open(ARTIFACT, encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def nodes():
    """label -> prose, per corpus, read from the primary artifacts."""
    out = {}
    for corpus in sorted(os.listdir(MATHSOURCES)):
        path = os.path.join(MATHSOURCES, corpus, "nodes.jsonl")
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as fh:
            out[corpus] = {json.loads(line)["label"]: json.loads(line)["prose"]
                           for line in fh if line.strip()}
    return out


def test_schema_and_shape(doc):
    assert doc["schema"] == "mathsource-provenance/v1"
    assert doc["rows"], "an empty provenance record is not a passing one"
    for sid, row in doc["rows"].items():
        assert set(row) == {"corpus", "node_id", "text_sha256",
                            "introduced_by", "source_committed"}, sid
        assert isinstance(row["source_committed"], bool), sid
        assert row["corpus"] and row["node_id"] and row["introduced_by"], sid


def test_every_row_resolves_to_a_real_census_node(doc, nodes):
    """The ATTRIBUTION half, checked for every row regardless of strength."""
    unresolved = [
        sid for sid, r in doc["rows"].items()
        if r["corpus"] in nodes and r["node_id"] not in nodes[r["corpus"]]
    ]
    assert not unresolved, (
        f"rows naming a node their corpus does not contain: {unresolved[:5]} -- "
        f"either the corpus drifted or the source was misattributed")


def test_every_pinned_row_reproduces_its_sha_from_the_corpus(doc, nodes):
    """The TEXT-IDENTITY half.  This is the claim the wp_ scripts made and
    nothing verified: the source's prose IS this node's prose."""
    checked = 0
    bad = []
    for sid, r in doc["rows"].items():
        if not r["text_sha256"]:
            continue
        prose = nodes.get(r["corpus"], {}).get(r["node_id"])
        if prose is None:
            continue
        checked += 1
        if hashlib.sha256(prose.encode("utf-8")).hexdigest() != r["text_sha256"]:
            bad.append(sid)
    assert checked, "no pinned row was checkable -- the tooth would pass silently"
    assert not bad, f"pinned sha no longer matches the corpus prose: {bad[:5]}"


def test_the_committed_source_is_the_node_prose(doc, nodes):
    """Close the chain the pin only half-covers: the committed .txt must BE
    that prose (modulo the trailing newline the intake writes)."""
    mismatched = []
    for sid, r in doc["rows"].items():
        if not r["source_committed"]:
            continue
        path = os.path.join(MATHSOURCES, sid + ".txt")
        if not os.path.isfile(path):
            mismatched.append((sid, "absent"))
            continue
        prose = nodes.get(r["corpus"], {}).get(r["node_id"])
        if prose is None:
            continue
        with open(path, encoding="utf-8") as fh:
            if fh.read().strip() != prose.strip():
                mismatched.append((sid, "text differs"))
    assert not mismatched, (
        f"committed source is not its node's prose: {mismatched[:5]}")


def test_source_committed_is_a_reading_not_a_wish(doc):
    """`source_committed` must describe the tree as it is.  A row that claims a
    committed source without one would launder a refusal into coverage."""
    wrong = [
        sid for sid, r in doc["rows"].items()
        if r["source_committed"] != os.path.isfile(
            os.path.join(MATHSOURCES, sid + ".txt"))
    ]
    assert not wrong, f"source_committed disagrees with the tree: {wrong[:5]}"


def test_refused_subjects_stay_in_writing(doc):
    """The honesty rule this record exists under: a subject that was selected
    and did not certify is RECORDED, never dropped.  If every row were
    committed, the file would be indistinguishable from one that had been
    quietly pruned -- so the count is asserted, not assumed."""
    uncommitted = [s for s, r in doc["rows"].items() if not r["source_committed"]]
    assert len(uncommitted) >= 1, (
        "no selected-but-uncommitted subject survives in the record; the "
        "scripts carry at least one, and dropping it would flatter the "
        "coverage count")


def test_honesty_string_names_every_weakening(doc):
    """Each weakening must be named where a reader meets the data: unpinned
    rows are not verified, coverage is partial, and the record is derived."""
    h = doc["honesty"]
    assert "never 'verified'" in h or "never \"verified\"" in h
    assert "PARTIAL BY CONSTRUCTION" in h
    assert "CONFERS NO AUTHORITY" in h


def test_regenerate_byte_identical():
    """The seed-drift tooth every derived artifact in this repo carries: the
    scripts are the source of truth, so a hand-edit here -- or a script whose
    PROVENANCE moved without a regen -- reddens rather than drifting."""
    import tools.mathsource_provenance as P
    with open(ARTIFACT, "rb") as fh:
        committed = fh.read()
    import io, json as _json
    buf = io.StringIO()
    _json.dump(P.build(), buf, indent=1, sort_keys=True)
    buf.write("\n")
    assert buf.getvalue().encode("utf-8") == committed, (
        "provenance.json drifted from the wp_ scripts -- regenerate: "
        "python3 tools/mathsource_provenance.py")


def test_the_scripts_remain_the_source_of_truth():
    """This artifact must never become a second copy that outlives its source.
    The family is NOT retirable and the reasons are mechanical, not stylistic:
    wp_auth_readings is imported by run/anchor.py and bench/bench_hammer.py,
    and tools/intake_from_frontier.py allocates the next cycle index by
    scanning repo root for wp_c<N>_readings.py -- so an empty root resets that
    counter to c2 and collides with cycle 2's identity."""
    import glob
    scripts = glob.glob(os.path.join(_ROOT, "wp_*_readings.py"))
    assert scripts, ("the wp_ scripts are gone; provenance.json cannot be "
                     "regenerated and intake_from_frontier will re-allocate c2")
    src = open(os.path.join(_ROOT, "tools", "intake_from_frontier.py"),
               encoding="utf-8").read()
    assert "wp_c" in src, "the index allocator no longer keys on these names"


def test_honesty_string_denies_itself_authority(doc):
    """A derived reading that does not say it is derived invites being cited
    as the source."""
    assert "CONFERS NO AUTHORITY" in doc["honesty"]
    assert "the scripts win" in doc["honesty"]
