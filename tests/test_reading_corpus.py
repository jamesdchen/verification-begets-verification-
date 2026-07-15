"""The reading corpus is grounded and structurally valid -- every committed row.

Fast, pure, LLM-free, and needs NO external tool (no ksc / z3 / Dafny): it only
exercises the file->table BRIDGE (buildloop.reading_corpus) and the mechanical
groundedness gate (generators.reading.parse_reading).  The point is a standing
guarantee that everything under specs/readings/ certifies at least this far --
each quote occurs verbatim in its request and each reading is well-formed -- so
the seed step never ingests a broken reading.
"""
from __future__ import annotations

import json
import os
import sys

# Make the repo root importable when this file is run directly as a script
# (under pytest the repo-root conftest.py already does this).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
from buildloop.reading_corpus import load_readings
from generators import reading as rd

READINGS_DIR = common.REPO_ROOT / "specs" / "readings"
DREAM_DIR = READINGS_DIR / "dream"


def _entries():
    # real (exogenous, committed-request byte-match) live at the top level;
    # dream (system-origin) live under dream/.  Both are grounded & valid; only
    # the seed step distinguishes their provenance (via the demand ledger).
    out = list(load_readings(READINGS_DIR))
    if DREAM_DIR.exists():
        out += list(load_readings(DREAM_DIR))
    return out


def test_corpus_has_at_least_eight_entries():
    entries = _entries()
    assert len(entries) >= 8, \
        f"expected >= 8 committed readings, got {len(entries)}"


def test_every_reading_is_grounded_and_valid():
    entries = _entries()
    assert entries, "no readings loaded"
    for entry in entries:
        # recover the service name from the raw file text (source round-trips)
        obj = json.loads(entry.source)
        service = obj["reading"]["service"]
        reading_text = json.dumps({
            "service": service,
            "statements": entry.statements,
        })
        # parse_reading raises BadReading on any groundedness/structural failure
        parsed = rd.parse_reading(reading_text, entry.request)
        assert parsed.statements, "parsed reading has no statements"
        # sanity: at least one demanded obligation (the gate enforces this, but
        # assert it explicitly so a regression is legible)
        assert any(
            s["lf"]["kind"] in rd.OBLIGATION_KINDS and s["force"] == "demand"
            for s in parsed.statements)


def test_source_round_trips_to_original_object():
    entries = _entries()
    assert entries, "no readings loaded"
    for entry in entries:
        obj = json.loads(entry.source)
        # source is the RAW file text; it must reconstruct the file's object,
        # and that object's fields must agree with the CorpusEntry.
        assert set(obj) == {"request", "reading"}
        assert obj["request"] == entry.request
        assert obj["reading"]["statements"] == entry.statements


def _run():
    tests = [
        test_corpus_has_at_least_eight_entries,
        test_every_reading_is_grounded_and_valid,
        test_source_round_trips_to_original_object,
    ]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"  PASS {t.__name__}")
    n = len(_entries())
    print(f"\n{passed}/{len(tests)} tests passed over {n} corpus readings.")


if __name__ == "__main__":
    _run()
