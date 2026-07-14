"""The generator library: a SQLite registry.

Every entry has type Spec -> Code (no plain components).  Entries are never
deleted: retirement keeps them for provenance while excluding them from
planning.  The registry also stores certificates, first-class events
(disagreements, rejections, admissions, ...), the counterexample corpus,
and the kernel verdict cache.
"""
from __future__ import annotations

import json
import sqlite3

import common
from kernel.certs import Certificate, ErrorTranscript, CERTS_VERSION

_SCHEMA = """
CREATE TABLE IF NOT EXISTS generators(
  generator_hash TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  tier TEXT NOT NULL CHECK(tier IN ('emit-check','universal')),
  spec_language TEXT NOT NULL,
  output_language TEXT NOT NULL,
  spec_grammar TEXT NOT NULL,      -- JSON {atoms: [...]} or {kind: ...}
  emit_entrypoint TEXT NOT NULL,   -- JSON
  contract TEXT NOT NULL,          -- JSON
  provenance TEXT NOT NULL,        -- JSON
  emission_checked INTEGER NOT NULL DEFAULT 0,
  emission_failures INTEGER NOT NULL DEFAULT 0,
  admitted_at TEXT NOT NULL,
  retired INTEGER NOT NULL DEFAULT 0,
  subsumed_by TEXT,
  description_length REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS certificates(
  cert_id TEXT PRIMARY KEY,
  kind TEXT, subject_hash TEXT, contract_hash TEXT,
  channels TEXT, generator_hash TEXT, created_at TEXT,
  tier TEXT NOT NULL DEFAULT '',
  claims TEXT NOT NULL DEFAULT '[]',
  non_claims TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS generator_certs(
  generator_hash TEXT, cert_id TEXT,
  PRIMARY KEY (generator_hash, cert_id)
);
CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT, kind TEXT, payload TEXT
);
CREATE TABLE IF NOT EXISTS corpus(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  added_at TEXT, contract_type TEXT, spec_hash TEXT,
  atoms TEXT, failing_input TEXT, transcript TEXT
);
CREATE TABLE IF NOT EXISTS kernel_cache(
  key TEXT PRIMARY KEY, blob BLOB, created_at TEXT
);
CREATE TABLE IF NOT EXISTS counters(
  key TEXT PRIMARY KEY, value REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS metrics_log(
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT, event TEXT, policy TEXT, corpus INTEGER,
  reach REAL, covered INTEGER, backlog_n INTEGER,
  llm_input_tokens REAL, llm_output_tokens REAL, verifier_seconds REAL,
  avg_chain_depth REAL, max_chain_depth INTEGER,
  tier_universal INTEGER, tier_emit_check INTEGER,
  total_dl REAL, live_size INTEGER,
  corpus_caught INTEGER, fresh_caught INTEGER
);
"""


class Registry:
    def __init__(self, db_path=None):
        common.ensure_dirs()
        self.path = str(db_path or common.DB_PATH)
        # timeout + WAL + busy_timeout so a swarm of loops (each ideally on its
        # own CGB_DB file, per the one-writer-per-DB rule) does not throw
        # "database is locked" under brief contention.
        self.db = sqlite3.connect(self.path, timeout=30)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA busy_timeout=30000")
        self.db.executescript(_SCHEMA)
        self._migrate()
        self.db.commit()

    def _migrate(self):
        """Additively bring an older DB's schema up to date.  The certificates
        table historically had a fixed 7 columns and silently dropped the
        honest-tier fields; add them if absent (SQLite ADD COLUMN is cheap and
        preserves existing rows)."""
        have = {r[1] for r in self.db.execute(
            "PRAGMA table_info(certificates)").fetchall()}
        for col, decl in (("tier", "TEXT NOT NULL DEFAULT ''"),
                          ("claims", "TEXT NOT NULL DEFAULT '[]'"),
                          ("non_claims", "TEXT NOT NULL DEFAULT '[]'")):
            if col not in have:
                self.db.execute(
                    f"ALTER TABLE certificates ADD COLUMN {col} {decl}")

    # ---------------------------------------------------------- generators
    def register(self, *, name, tier, spec_language, output_language,
                 spec_grammar, emit_entrypoint, contract, provenance,
                 certificates=(), description_length=0.0) -> str:
        body = {"name": name, "spec_language": spec_language,
                "output_language": output_language, "spec_grammar": spec_grammar,
                "emit_entrypoint": emit_entrypoint, "contract": contract}
        ghash = common.sha256_json(body)
        self.db.execute(
            "INSERT OR REPLACE INTO generators(generator_hash,name,tier,"
            "spec_language,output_language,spec_grammar,emit_entrypoint,"
            "contract,provenance,admitted_at,description_length) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (ghash, name, tier, spec_language, output_language,
             common.canonical_json(spec_grammar),
             common.canonical_json(emit_entrypoint),
             common.canonical_json(contract),
             common.canonical_json(provenance),
             common.now_iso(), description_length))
        for cert in certificates:
            self.store_certificate(cert, ghash)
        self.db.commit()
        return ghash

    def get(self, ghash: str) -> dict:
        row = self.db.execute(
            "SELECT * FROM generators WHERE generator_hash=?", (ghash,)).fetchone()
        if row is None:
            raise KeyError(ghash)
        return self._row_to_dict(row)

    def _row_to_dict(self, row):
        cols = ["generator_hash", "name", "tier", "spec_language",
                "output_language", "spec_grammar", "emit_entrypoint",
                "contract", "provenance", "emission_checked",
                "emission_failures", "admitted_at", "retired", "subsumed_by",
                "description_length"]
        d = dict(zip(cols, row))
        for k in ("spec_grammar", "emit_entrypoint", "contract", "provenance"):
            d[k] = json.loads(d[k])
        return d

    def live_generators(self) -> list:
        rows = self.db.execute(
            "SELECT * FROM generators WHERE retired=0 "
            "ORDER BY generator_hash").fetchall()
        return [self._row_to_dict(r) for r in rows]

    def all_generators(self) -> list:
        rows = self.db.execute(
            "SELECT * FROM generators ORDER BY admitted_at, generator_hash").fetchall()
        return [self._row_to_dict(r) for r in rows]

    def set_tier(self, ghash: str, tier: str):
        self.db.execute("UPDATE generators SET tier=? WHERE generator_hash=?",
                        (tier, ghash))
        self.db.commit()

    def retire(self, ghash: str, subsumed_by: str):
        self.db.execute(
            "UPDATE generators SET retired=1, subsumed_by=? WHERE generator_hash=?",
            (subsumed_by, ghash))
        self.db.commit()

    def bump_emission_record(self, ghash: str, ok: bool):
        col = "emission_checked" if ok else "emission_failures"
        self.db.execute(
            f"UPDATE generators SET {col}={col}+1 WHERE generator_hash=?", (ghash,))
        if not ok:
            self.db.execute(
                "UPDATE generators SET emission_checked=emission_checked+1 "
                "WHERE generator_hash=?", (ghash,))
        self.db.commit()

    # -------------------------------------------------------- certificates
    def store_certificate(self, cert, generator_hash=None):
        d = cert.to_dict() if hasattr(cert, "to_dict") else cert
        self.db.execute(
            "INSERT OR IGNORE INTO certificates(cert_id,kind,subject_hash,"
            "contract_hash,channels,generator_hash,created_at,tier,claims,"
            "non_claims) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (d["cert_id"], d["kind"], d["subject_hash"], d["contract_hash"],
             common.canonical_json(d["channels"]), generator_hash,
             d["created_at"], d.get("tier", ""),
             common.canonical_json(list(d.get("claims", ()))),
             common.canonical_json(list(d.get("non_claims", ())))))
        if generator_hash:
            self.db.execute(
                "INSERT OR IGNORE INTO generator_certs VALUES(?,?)",
                (generator_hash, d["cert_id"]))
        self.db.commit()

    def certs_for(self, ghash: str) -> list:
        rows = self.db.execute(
            "SELECT c.cert_id,c.kind,c.subject_hash,c.contract_hash,c.channels,"
            "c.generator_hash,c.created_at,c.tier,c.claims,c.non_claims "
            "FROM certificates c JOIN generator_certs g "
            "ON c.cert_id=g.cert_id WHERE g.generator_hash=?", (ghash,)).fetchall()
        return [{"cert_id": r[0], "kind": r[1], "subject_hash": r[2],
                 "contract_hash": r[3], "channels": json.loads(r[4]),
                 "created_at": r[6], "tier": r[7],
                 "claims": tuple(json.loads(r[8])),
                 "non_claims": tuple(json.loads(r[9]))} for r in rows]

    # -------------------------------------------------------------- events
    def log_event(self, kind: str, payload: dict):
        self.db.execute("INSERT INTO events(at,kind,payload) VALUES(?,?,?)",
                        (common.now_iso(), kind, common.canonical_json(payload)))
        self.db.commit()

    def events(self, kind=None) -> list:
        q = "SELECT id,at,kind,payload FROM events"
        args = ()
        if kind:
            q += " WHERE kind=?"
            args = (kind,)
        return [{"id": r[0], "at": r[1], "kind": r[2],
                 "payload": json.loads(r[3])}
                for r in self.db.execute(q + " ORDER BY id", args)]

    # -------------------------------------------------------------- corpus
    def corpus_add(self, contract_type, spec_hash, atoms, failing_input_hex,
                   transcript):
        if not failing_input_hex:
            return
        self.db.execute(
            "INSERT INTO corpus(added_at,contract_type,spec_hash,atoms,"
            "failing_input,transcript) VALUES(?,?,?,?,?,?)",
            (common.now_iso(), contract_type, spec_hash,
             common.canonical_json(sorted(atoms)), failing_input_hex,
             common.canonical_json(transcript)))
        self.db.commit()

    def corpus_inputs(self, atoms: frozenset) -> list:
        """Stored failing inputs relevant to a spec's feature signature."""
        rows = self.db.execute(
            "SELECT atoms, failing_input FROM corpus ORDER BY id").fetchall()
        out = []
        for a_json, hx in rows:
            if set(json.loads(a_json)) & set(atoms):
                out.append(hx)
        return out[:200]

    # ------------------------------------------------------------ counters
    def counter_add(self, key: str, delta: float):
        self.db.execute(
            "INSERT INTO counters(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=value+excluded.value",
            (key, float(delta)))
        self.db.commit()

    def counter_get(self, key: str) -> float:
        row = self.db.execute(
            "SELECT value FROM counters WHERE key=?", (key,)).fetchone()
        return row[0] if row else 0.0

    # -------------------------------------------------------- kernel cache
    #
    # Versioned JSON, not pickle: a schema/obligation change bumps CERTS_VERSION
    # (which also prefixes the cache key), so an entry written under an older
    # version rehydrates to None (a clean cache miss) instead of a stale hit or
    # an unpickling AttributeError.  The blob shape is
    #   {"schema_version": N, "record": "certificate"|"transcript", "data": ...}
    def cache_get(self, key: str):
        row = self.db.execute(
            "SELECT blob FROM kernel_cache WHERE key=?", (key,)).fetchone()
        if not row:
            return None
        try:
            env = json.loads(row[0])
        except (ValueError, TypeError):
            return None
        if env.get("schema_version") != CERTS_VERSION:
            return None  # unknown/older version -> cache miss, never stale
        data = env.get("data", {})
        if env.get("record") == "certificate":
            return Certificate.from_dict(data)
        if env.get("record") == "transcript":
            return ErrorTranscript.from_dict(data)
        return None

    def cache_put(self, key: str, value):
        if isinstance(value, Certificate):
            record = "certificate"
        elif isinstance(value, ErrorTranscript):
            record = "transcript"
        else:
            return  # only kernel verdicts are cacheable
        env = {"schema_version": CERTS_VERSION, "record": record,
               "data": value.to_dict()}
        self.db.execute(
            "INSERT OR REPLACE INTO kernel_cache VALUES(?,?,?)",
            (key, common.canonical_json(env), common.now_iso()))
        self.db.commit()
