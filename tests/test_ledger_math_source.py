"""FORMALIZATION F3.1/F3.2 -- the `math-source` demand kind: ledger plumbing.

The A1 read-back tooth.  A1's failure mode is SILENT: before the demand-table
CHECK is widened, a `math-source` row violates `CHECK(kind IN (...))` and
`demand_upsert`'s `INSERT OR IGNORE` swallows it -- `ledger sync` reports
success while persisting nothing.  Presence is therefore the test: after a sync
(and after a bare `demand_upsert`) the row must be RETRIEVABLE.

Also pins the A6 (every kind priced explicitly; unknown kinds hard-error) and E3
(dreams propose, they must not bill) pricing rules, and the demand-table rebuild
migration on an older DB that still carries the narrow CHECK.

Pure, LLM-free, deterministic: readings are constructed directly (no
certify-at-seed / WP-H dependency), so unserved pricing -- the part that is
observable now -- is what the teeth assert.
"""
import os
import sqlite3
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
import cgb
from buildloop import dl
from library import Registry


def _reg(tmp_path):
    return Registry(db_path=str(tmp_path / "r.sqlite"))


# --------------------------------------------------------------------------- #
# A1 read-back tooth: sync ingestion (presence, because the failure is silent)
# --------------------------------------------------------------------------- #
def test_ledger_sync_ingests_math_source_rows(tmp_path):
    reg = _reg(tmp_path)
    counts = cgb._ledger_sync(reg)
    assert counts["math-source"] > 0, "sync counted zero math-source rows"

    rows = reg.demand_all("math-source")
    by_ref = {r["payload_ref"]: r for r in rows}

    # read-back tooth: a known exogenous corpus file IS present, origin exogenous
    exo = by_ref.get("specs/mathsources/01_dvd_reflexive.txt")
    assert exo is not None, \
        "exogenous math-source row silently vanished (A1 regression)"
    assert exo["origin"] == "exogenous"
    assert exo["kind"] == "math-source" and exo["status"] == "open"

    # a dream file's row is present and SYSTEM-origin
    dream = by_ref.get("specs/mathsources/dream/d01_common_divisor_diff.txt")
    assert dream is not None, "dream math-source row missing"
    assert dream["origin"] == "system"

    # dream/README.txt is a note, not a statement -> never a demand row
    assert "specs/mathsources/dream/README.txt" not in by_ref

    # demand_id follows sha256("math-source:" + relpath), retrievable by id
    did = common.sha256_bytes(
        b"math-source:specs/mathsources/01_dvd_reflexive.txt")
    got = reg.demand_get(did)
    assert got is not None
    assert got["payload_ref"] == "specs/mathsources/01_dvd_reflexive.txt"


def test_ledger_sync_is_idempotent(tmp_path):
    reg = _reg(tmp_path)
    first = cgb._ledger_sync(reg)
    n_math = len(reg.demand_all("math-source"))
    second = cgb._ledger_sync(reg)
    # a second sync adds nothing new and does not duplicate rows
    assert second["added"] == 0
    assert len(reg.demand_all("math-source")) == n_math
    assert first["math-source"] >= n_math


# --------------------------------------------------------------------------- #
# A1: a bare demand_upsert of a math-source row must PERSIST
# --------------------------------------------------------------------------- #
def test_demand_upsert_persists_math_source(tmp_path):
    reg = _reg(tmp_path)
    reg.demand_upsert({"demand_id": "M", "kind": "math-source",
                       "origin": "exogenous", "status": "open",
                       "language": None, "features": None,
                       "payload_ref": "specs/mathsources/x.txt",
                       "size_bytes": 20})
    got = reg.demand_get("M")
    assert got is not None, \
        "math-source row swallowed by the demand CHECK (A1 regression)"
    assert got["kind"] == "math-source" and got["origin"] == "exogenous"


# --------------------------------------------------------------------------- #
# A6/E3 pricing
# --------------------------------------------------------------------------- #
def test_unserved_pricing_exogenous_penalty_and_dream_zero(tmp_path):
    reg = _reg(tmp_path)
    reg.demand_upsert({"demand_id": "EX", "kind": "math-source",
                       "origin": "exogenous", "status": "open",
                       "language": None, "features": None,
                       "payload_ref": "specs/mathsources/a.txt",
                       "size_bytes": 30})
    reg.demand_upsert({"demand_id": "DR", "kind": "math-source",
                       "origin": "system", "status": "open",
                       "language": None, "features": None,
                       "payload_ref": "specs/mathsources/dream/d.txt",
                       "size_bytes": 30})
    snap = dl.snapshot(reg)
    # unserved exogenous -> the capped penalty; unserved dream -> 0.0 (E3)
    assert dl._demand_cost(reg.demand_get("EX"), snap) == dl.UNCOVERED_PENALTY
    assert dl._demand_cost(reg.demand_get("DR"), snap) == 0.0

    tot = dl.ledger_dl(reg)
    assert tot["total_math"] == 2
    assert tot["covered_math"] == 0
    assert tot["dream_rows"] == 1
    # only the exogenous row bills; the dream contributes nothing
    assert abs(tot["ledger_dl"] - dl.UNCOVERED_PENALTY) < 1e-9


def test_served_pricing_prices_the_math_reading(tmp_path):
    """A covered math-source row (a MathReading present) prices on the
    nl-request shape: READING_CHAIN_COST + dl_reading over its statements --
    proving mdl_macros.dl_reading is generic over math statement dicts."""
    reg = _reg(tmp_path)
    reg.demand_upsert({"demand_id": "EX", "kind": "math-source",
                       "origin": "exogenous", "status": "open",
                       "language": None, "features": None,
                       "payload_ref": "specs/mathsources/a.txt",
                       "size_bytes": 30})
    reading = {"theorem": "dvd_reflexive", "statements": [
        {"id": "s1", "force": "assert", "quote": "n divides n",
         "lf": {"kind": "atom", "op": "dvd",
                "args": [{"ref": "n"}, {"ref": "n"}]}}]}
    reg.reading_add("EX", common.canonical_json(reading), "cert-1")

    snap = dl.snapshot(reg)
    cost = dl._demand_cost(reg.demand_get("EX"), snap)
    expected = dl.READING_CHAIN_COST + dl.dl_reading(reading, {})
    assert abs(cost - expected) < 1e-9

    tot = dl.ledger_dl(reg)
    assert tot["total_math"] == 1 and tot["covered_math"] == 1
    assert tot["dream_rows"] == 0


def test_envelope_shaped_reading_prices(tmp_path):
    """The pricing shim tolerates a MathReading persisted as the F-A envelope
    `{source, reading:{theorem, statements}}` as well as the flattened shape, so
    pricing does not depend on how WP-H's certify-at-seed lands the reading."""
    reg = _reg(tmp_path)
    reg.demand_upsert({"demand_id": "EX", "kind": "math-source",
                       "origin": "exogenous", "status": "open",
                       "language": None, "features": None,
                       "payload_ref": "specs/mathsources/a.txt",
                       "size_bytes": 30})
    stmts = [{"id": "s1", "force": "assert", "quote": "n divides n",
              "lf": {"kind": "atom", "op": "dvd",
                     "args": [{"ref": "n"}, {"ref": "n"}]}}]
    envelope = {"source": "n divides n",
                "reading": {"theorem": "dvd_reflexive", "statements": stmts}}
    reg.reading_add("EX", common.canonical_json(envelope), "cert-1")

    snap = dl.snapshot(reg)
    cost = dl._demand_cost(reg.demand_get("EX"), snap)
    expected = dl.READING_CHAIN_COST + dl.dl_reading({"statements": stmts}, {})
    assert abs(cost - expected) < 1e-9


def test_unknown_kind_hard_errors(tmp_path):
    """A6: every kind must be priced explicitly; an unknown kind fails loud
    instead of silently pricing 0.0."""
    reg = _reg(tmp_path)
    snap = dl.snapshot(reg)
    with pytest.raises(ValueError):
        dl._demand_cost({"demand_id": "B", "kind": "bogus", "status": "open"},
                        snap)


# --------------------------------------------------------------------------- #
# A1: the demand-table CHECK-widening rebuild migration
# --------------------------------------------------------------------------- #
_OLD_DEMAND = """
CREATE TABLE demand(
  demand_id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK(kind IN
        ('spec-file','nl-request','caged-incumbent')),
  origin TEXT NOT NULL CHECK(origin IN ('exogenous','system')),
  status TEXT NOT NULL CHECK(status IN
        ('open','covered','converted','retired')),
  language TEXT, features TEXT, payload_ref TEXT, size_bytes INTEGER,
  covered_via TEXT, created_at TEXT NOT NULL);
"""


def test_demand_migration_rebuilds_and_preserves_rows(tmp_path):
    legacy = str(tmp_path / "legacy.sqlite")
    con = sqlite3.connect(legacy)
    con.executescript(_OLD_DEMAND)
    con.execute("INSERT INTO demand(demand_id,kind,origin,status,created_at) "
                "VALUES('S','spec-file','exogenous','open','t0')")
    con.commit()
    # sanity: the OLD CHECK rejects math-source (the A1 hazard)
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO demand(demand_id,kind,origin,status,created_at)"
                    " VALUES('M','math-source','exogenous','open','t0')")
    con.rollback()
    con.close()

    # open with the current Registry -> the migration rebuilds the CHECK
    reg = Registry(db_path=legacy)
    sql = reg.db.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' "
        "AND name='demand'").fetchone()[0]
    assert "'math-source'" in sql, "CHECK not widened by the migration"
    # the pre-existing row is preserved
    got = reg.demand_get("S")
    assert got is not None and got["kind"] == "spec-file"
    # and math-source now persists
    reg.demand_upsert({"demand_id": "M", "kind": "math-source",
                       "origin": "exogenous", "status": "open",
                       "language": None, "features": None,
                       "payload_ref": "p", "size_bytes": 1})
    assert reg.demand_get("M") is not None
    reg.db.close()

    # idempotent: a second open neither rebuilds again nor loses rows
    reg2 = Registry(db_path=legacy)
    assert reg2.demand_get("S") is not None
    assert reg2.demand_get("M") is not None
    assert len(reg2.demand_all()) == 2
    reg2.db.close()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
