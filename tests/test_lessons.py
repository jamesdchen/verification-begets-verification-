"""Teeth for the lessons ledger (tools/lessons.py) and its committed rows.

WHAT THIS LEDGER IS FOR.  The five-day shakedown (2026-07-22..26) had one
recurring defect class with one recurring shape: a lesson learned, written
down as a sentence, and thereafter unable to track its own evidence.  The
ledger puts a declare-or-red ratchet where lessons are BORN -- a row cites a
tooth that resolves, or declares in writing why the claim has no executable
form.

WHAT THESE TEETH DO.  The tool's refusals are EXECUTED here (a vapor tooth,
a both/neither row, a missing provenance, a duplicate), and the committed
ledger is validated row-by-row through the tool's own validator, so a row
whose tooth is later deleted or renamed reds THIS suite rather than sitting
in the ledger as a lie.  That last property is the whole point: the ledger
is only worth having if its citations stay live.
"""
import json
import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "tools"))

import lessons as L  # noqa: E402


# --------------------------------------------------------------- resolution
def test_a_tooth_that_resolves_is_accepted():
    """The control: this very test, cited by path::name, must resolve --
    otherwise every refusal below could be passing for the wrong reason."""
    assert L.resolve_tooth(
        "tests/test_lessons.py::test_a_tooth_that_resolves_is_accepted") is None


def test_a_tooth_naming_a_missing_file_is_refused():
    assert L.resolve_tooth("tests/test_no_such_file.py::test_x")


def test_a_tooth_naming_a_missing_test_is_refused():
    """Vapor citation: the file exists, the test does not."""
    reason = L.resolve_tooth("tests/test_lessons.py::test_not_defined_here")
    assert reason and "defines no top-level function" in reason


def test_a_tooth_mentioned_only_in_prose_does_not_resolve(tmp_path):
    """The matched-a-mention lesson, applied to the tool that RECORDS
    lessons: a docstring naming the test is not the test.  This repo's teeth
    have been bitten four times by matching a mention of the thing."""
    root = tmp_path
    (root / "tests").mkdir()
    (root / "tests" / "test_fake.py").write_text(
        '"""See test_the_claim for the check."""\n'
        '# def test_the_claim(): ...\n')
    reason = L.resolve_tooth("tests/test_fake.py::test_the_claim", root=str(root))
    assert reason and "defines no top-level function" in reason


def test_a_malformed_tooth_is_refused():
    assert L.resolve_tooth("tests/test_lessons.py")          # no ::
    assert L.resolve_tooth("tests/test_lessons.py::")        # no name
    assert L.resolve_tooth("notpython::test_x")              # not .py


# ------------------------------------------------------------- row validity
def _row(**kw):
    row = {"claim": "c", "recorded_by": "results/x.md",
           "tooth": None, "prose_only_reason": None}
    row.update(kw)
    return row


def test_a_row_with_neither_tooth_nor_reason_is_refused():
    """The debt shape itself: a lesson with no executable form and no
    declared reason is exactly the paragraph this ledger replaces."""
    bad = L.validate_row(_row())
    assert bad and "exactly one of" in bad


def test_a_row_with_both_is_refused():
    bad = L.validate_row(_row(
        tooth="tests/test_lessons.py::test_a_row_with_both_is_refused",
        prose_only_reason="also unmechanizable"))
    assert bad and "exactly one of" in bad


def test_a_row_without_provenance_is_refused():
    """Provenance-mandatory, as in every other ledger here: a lesson whose
    origin is unrecorded cannot be re-read against what it measured."""
    bad = L.validate_row(_row(recorded_by="  ", prose_only_reason="r"))
    assert bad and "provenance" in bad


def test_an_empty_prose_reason_is_refused():
    """A blank exemption is the default this ratchet exists to forbid."""
    bad = L.validate_row(_row(prose_only_reason="   "))
    assert bad and "non-empty" in bad


def test_an_unknown_key_is_refused():
    row = _row(prose_only_reason="r")
    row["extra"] = 1
    assert L.validate_row(row)


# ------------------------------------------------------------------ writing
def test_recording_appends_a_canonical_row_and_refuses_duplicates(tmp_path):
    ledger = str(tmp_path / "lessons.jsonl")
    tooth = ("tests/test_lessons.py::"
             "test_recording_appends_a_canonical_row_and_refuses_duplicates")
    L.record("a claim", "PR #1", tooth, None, ledger=ledger)
    rows = L.load(ledger)
    assert len(rows) == 1 and rows[0]["tooth"] == tooth
    # canonical: sorted keys, one line, round-trips
    assert open(ledger).read() == json.dumps(rows[0], sort_keys=True) + "\n"
    with pytest.raises(SystemExit):
        L.record("a claim", "PR #2", tooth, None, ledger=ledger)
    assert len(L.load(ledger)) == 1, "a refused duplicate must not append"


def test_recording_a_vapor_tooth_writes_nothing(tmp_path):
    """Refusal must happen BEFORE the append, or the ledger accumulates the
    rows the validator was meant to keep out."""
    ledger = str(tmp_path / "lessons.jsonl")
    with pytest.raises(SystemExit):
        L.record("c", "PR #1", "tests/test_lessons.py::test_nope", None,
                 ledger=ledger)
    assert L.load(ledger) == []


# ---------------------------------------------------------- committed rows
def test_every_committed_lesson_still_validates():
    """THE LOAD-BEARING TOOTH.  A cited tooth that is later deleted or
    renamed turns its ledger row into exactly the thing the ledger exists to
    abolish -- a claim that stopped tracking its evidence.  Re-validating
    every committed row here means the citation stays live or the suite
    reds."""
    rows = L.load()
    assert rows, "the committed lessons ledger is empty"
    for row in rows:
        bad = L.validate_row(row)
        assert bad is None, f"{row.get('claim')!r}: {bad}"


def test_the_committed_ledger_is_canonical_and_append_only_shaped():
    """Same contract as the other ledgers: one canonical JSON object per
    line, no clocks (provenance carries the era)."""
    path = L.LEDGER
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            assert line == json.dumps(row, sort_keys=True) + "\n", (
                "non-canonical row; write through tools/lessons.py")
            assert not any(k in row for k in ("ts", "when", "timestamp")), (
                "ledgers carry no clocks -- provenance carries the era")
