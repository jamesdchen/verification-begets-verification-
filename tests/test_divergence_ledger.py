#!/usr/bin/env python3
"""Z-D divergence ledger acceptance -- LLM-free, fast, events-only.

`speculate.log_divergence(registry, *, stage, direction, candidate_sha,
request_sha)` records a PREDICTION MISS as a first-class `speculation-divergence`
event.  These teeth prove the ledger is:

  * QUERYABLE  -- `registry.events("speculation-divergence")` returns the logged
    rows in id order, each carrying exactly the frozen Z-D payload keys
    {stage, direction, candidate_sha, request_sha} with the logged values;
  * DISCIPLINED (validation) -- an unknown `direction` (outside the two frozen
    prediction-miss directions the module validates) is rejected with a
    ValueError and writes NO row;
  * DISCIPLINED (Z1, events-only) -- logging a divergence touches NONE of the
    four Combined-Loop tables: no certificate and no readings row is created.

Runnable under pytest AND as a bare script
(`python3 tests/test_divergence_ledger.py` -> PASS lines, exit 0).
"""
from __future__ import annotations

import pathlib
import sys
import tempfile

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))          # runnable as a bare script, not just -m pytest

from buildloop import speculate
from library import Registry

# The two prediction-miss directions the module freezes (Z-D vocabulary).
_DIRS = speculate.DIVERGENCE_DIRECTIONS
assert len(_DIRS) == 2, _DIRS            # exactly the two miss directions
_ZD_KEYS = {"stage", "direction", "candidate_sha", "request_sha"}


def _fresh_registry():
    return Registry(db_path=tempfile.mkdtemp() + "/r.sqlite")


# --------------------------------------------------------------------------- #
def test_single_divergence_is_queryable_with_zd_payload():
    """(1) One logged divergence => exactly one queryable row whose payload has
    exactly the Z-D keys with the logged values."""
    reg = _fresh_registry()
    ret = speculate.log_divergence(
        reg, stage="consistency", direction=_DIRS[0],
        candidate_sha="abc", request_sha="def")
    rows = reg.events("speculation-divergence")
    assert len(rows) == 1, rows
    got = rows[0]["payload"]
    assert set(got) == _ZD_KEYS, got
    assert got["stage"] == "consistency", got
    assert got["direction"] == _DIRS[0], got
    assert got["candidate_sha"] == "abc", got
    assert got["request_sha"] == "def", got
    # the return value echoes exactly what was persisted
    assert ret == got, (ret, got)
    # and the ledger is filtered by kind: this is a first-class event kind
    assert rows[0]["kind"] == "speculation-divergence", rows[0]


def test_two_divergences_returned_in_order():
    """(2) A second divergence at a different stage => both rows returned, in
    insertion (id) order."""
    reg = _fresh_registry()
    first = speculate.log_divergence(
        reg, stage="consistency", direction=_DIRS[0],
        candidate_sha="abc", request_sha="def")
    second = speculate.log_divergence(
        reg, stage="compile", direction=_DIRS[1],
        candidate_sha="ghi", request_sha="jkl")
    rows = reg.events("speculation-divergence")
    assert len(rows) == 2, rows
    # ordered by id: first-logged first
    assert [r["id"] for r in rows] == sorted(r["id"] for r in rows), rows
    assert rows[0]["payload"] == first, rows
    assert rows[1]["payload"] == second, rows
    # distinct stages preserved in order
    assert [r["payload"]["stage"] for r in rows] == ["consistency", "compile"], rows
    assert [r["payload"]["direction"] for r in rows] == [_DIRS[0], _DIRS[1]], rows


def test_invalid_direction_is_rejected_and_writes_nothing():
    """(3) The module validates `direction` (`if direction not in
    DIVERGENCE_DIRECTIONS: raise ValueError`), so an unknown direction raises
    ValueError and NO divergence row is written."""
    reg = _fresh_registry()
    try:
        speculate.log_divergence(
            reg, stage="consistency", direction="not-a-real-direction",
            candidate_sha="abc", request_sha="def")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "an unknown divergence direction must be rejected with ValueError")
    # a rejected call leaves the ledger empty
    assert reg.events("speculation-divergence") == [], \
        reg.events("speculation-divergence")


def test_divergence_is_events_only_no_cert_no_reading():
    """(4) Z1 discipline: logging a divergence is events-table only.  It creates
    NO certificate and NO readings row -- the divergence ledger never launders a
    prediction miss into a proof artifact."""
    reg = _fresh_registry()
    speculate.log_divergence(
        reg, stage="consistency", direction=_DIRS[0],
        candidate_sha="abc", request_sha="def")
    speculate.log_divergence(
        reg, stage="compile", direction=_DIRS[1],
        candidate_sha="ghi", request_sha="jkl")
    # the event ledger has the rows...
    assert len(reg.events("speculation-divergence")) == 2
    # ...but no readings row was minted
    assert reg.readings_all() == [], reg.readings_all()
    # ...and no certificate side effect: the certificates table stays empty
    (cert_count,) = reg.db.execute(
        "SELECT COUNT(*) FROM certificates").fetchone()
    assert cert_count == 0, cert_count


if __name__ == "__main__":
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print("PASS", _name)
    print("divergence ledger holds "
          "(queryable Z-D payload; ordered; bad direction rejected ValueError; "
          "events-only -- no cert, no reading)")
