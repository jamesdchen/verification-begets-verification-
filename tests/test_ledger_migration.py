"""Combined-Loop W0 -- migration parity + the demand-ledger contract.

The demand / readings / macros / ledger_metrics tables are additive: a registry
opened over an OLD database (one that predates them) must end up with byte-for-
byte the same schema and rows as a registry created fresh.  This freezes the
additive-migration discipline (house rule 9) so a later schema change cannot
silently diverge fresh vs. migrated DBs.
"""
import os
import sqlite3
import tempfile

import pytest

import common
import planner
from buildloop import dl
from library import Registry, _SCHEMA


def _schema_of(db_path):
    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT name,sql FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
    con.close()
    return dict(rows)


def test_fresh_and_migrated_schema_are_equal(tmp_path):
    # a "fresh" DB: opened by the current Registry from nothing.
    fresh = str(tmp_path / "fresh.sqlite")
    Registry(db_path=fresh).db.close()

    # a "legacy" DB: only the pre-W0 tables exist, then the current Registry
    # opens it and runs its additive migration.
    legacy = str(tmp_path / "legacy.sqlite")
    con = sqlite3.connect(legacy)
    con.executescript("""
      CREATE TABLE generators(generator_hash TEXT PRIMARY KEY, name TEXT NOT NULL,
        tier TEXT NOT NULL, spec_language TEXT NOT NULL,
        output_language TEXT NOT NULL, spec_grammar TEXT NOT NULL,
        emit_entrypoint TEXT NOT NULL, contract TEXT NOT NULL,
        provenance TEXT NOT NULL, emission_checked INTEGER NOT NULL DEFAULT 0,
        emission_failures INTEGER NOT NULL DEFAULT 0, admitted_at TEXT NOT NULL,
        retired INTEGER NOT NULL DEFAULT 0, subsumed_by TEXT,
        description_length REAL NOT NULL DEFAULT 0);
      CREATE TABLE certificates(cert_id TEXT PRIMARY KEY, kind TEXT,
        subject_hash TEXT, contract_hash TEXT, channels TEXT,
        generator_hash TEXT, created_at TEXT);
      CREATE TABLE counters(key TEXT PRIMARY KEY, value REAL NOT NULL DEFAULT 0);
    """)
    con.commit()
    con.close()
    Registry(db_path=legacy).db.close()

    fs, ls = _schema_of(fresh), _schema_of(legacy)
    # every W0 table exists in both, with identical DDL.
    for t in ("demand", "readings", "macros", "ledger_metrics"):
        assert t in fs and t in ls, f"{t} missing"
        assert fs[t] == ls[t], f"{t} DDL diverged fresh vs migrated"


def test_demand_ledger_is_idempotent_and_respects_rows(tmp_path):
    reg = Registry(db_path=str(tmp_path / "r.sqlite"))
    row = {"demand_id": "X", "kind": "spec-file", "origin": "exogenous",
           "status": "open", "language": "ksy", "features": ["uint:1"],
           "payload_ref": "p", "size_bytes": 10}
    reg.demand_upsert(row)
    # a second upsert with a DIFFERENT status must NOT re-tag (house rule 12).
    reg.demand_upsert({**row, "status": "converted"})
    got = reg.demand_get("X")
    assert got["status"] == "open"
    assert got["features"] == ["uint:1"]
    assert len(reg.demand_all()) == 1


def test_ledger_dl_prices_every_kind(tmp_path):
    reg = Registry(db_path=str(tmp_path / "r.sqlite"))
    reg.demand_upsert({"demand_id": "S", "kind": "spec-file",
                       "origin": "exogenous", "status": "open",
                       "language": "ksy", "features": ["uint:1"],
                       "payload_ref": "s", "size_bytes": 64})
    reg.demand_upsert({"demand_id": "R", "kind": "nl-request",
                       "origin": "exogenous", "status": "open",
                       "language": None, "features": None,
                       "payload_ref": "r", "size_bytes": 100})
    reg.demand_upsert({"demand_id": "I", "kind": "caged-incumbent",
                       "origin": "exogenous", "status": "open",
                       "language": None, "features": None,
                       "payload_ref": "i", "size_bytes": 500})
    tot = dl.ledger_dl(reg)
    # nothing registered / no readings / no toll -> spec + request uncovered at
    # 50 each, incumbent at 0 toll.
    assert tot["total_spec"] == 1 and tot["total_request"] == 1
    assert tot["total_incumbent"] == 1
    assert abs(tot["ledger_dl"] - 100.0) < 1e-9


def test_plan_for_features_matches_plan(tmp_path):
    """The W0 wrapper shares ONE coverage rule with the live planner (fact 2)."""
    reg = Registry(db_path=str(tmp_path / "r.sqlite"))
    g = {"name": "g", "tier": "emit-check", "spec_language": "ksy",
         "output_language": "python-codec",
         "spec_grammar": {"atoms": ["endian:be", "uint:1", "uint:2"]},
         "emit_entrypoint": {"kind": "ksc-python-rw"},
         "contract": {"type": "codec-roundtrip"}, "provenance": {}}
    reg.register(**{k: g[k] for k in
                    ("name", "tier", "spec_language", "output_language",
                     "spec_grammar", "emit_entrypoint", "contract",
                     "provenance")})
    live = reg.live_generators()
    spec = "meta:\n  id: t\n  endian: be\nseq:\n  - id: a\n    type: u1\n"
    p = planner.plan(reg, spec)
    assert not isinstance(p, planner.CoverageMiss)
    _lang, _text, atoms = planner.load_spec(spec)
    chain = planner.plan_for_features(live, "ksy", atoms)
    assert chain is not None and len(chain) == len(p.links)
    assert [l["generator_hash"] for l in chain] == \
           [l["generator_hash"] for l in p.links]
