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
from kernel.certs import Certificate, ErrorTranscript, CERTS_VERSION, _tuplify

_SCHEMA = """
CREATE TABLE IF NOT EXISTS generators(
  generator_hash TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  tier TEXT NOT NULL,              -- no CHECK: the tier vocabulary is open
                                   -- (§4.12); register() validates against the
                                   -- kernel's TIERS constant instead, because
                                   -- SQLite cannot ALTER a CHECK (W2.1).
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
  description_length REAL NOT NULL DEFAULT 0,
  kind TEXT NOT NULL DEFAULT 'emitter'  -- emitter | translator | pass (W2.1);
                                   -- translator iff output_language is a spec
                                   -- language; pass set explicitly by W6.
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
-- The one demand ledger (Combined-Loop W0): every demand kind is a row here,
-- priced in one currency (ledger_dl) and admitted through one gate.  Conversion
-- is a status transition, never a kind mutation.
CREATE TABLE IF NOT EXISTS demand(
  demand_id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK(kind IN
        ('spec-file','nl-request','caged-incumbent')),
  origin TEXT NOT NULL CHECK(origin IN ('exogenous','system')),
  status TEXT NOT NULL CHECK(status IN
        ('open','covered','converted','retired')),
  language TEXT,
  features TEXT,        -- canonical-JSON: atoms list | LF-kind multiset |
                        -- tool alphabet; NULL until observable
  payload_ref TEXT,     -- repo-relative path or artifact/cert reference
  size_bytes INTEGER,
  covered_via TEXT,     -- rewrite demand_id when covered by a system rewrite
  created_at TEXT NOT NULL
);
-- The recurrence corpus (W0.2): certified Readings and admitted macros, so the
-- height axis has a queryable store to mine and price against.
CREATE TABLE IF NOT EXISTS readings(
  demand_id TEXT PRIMARY KEY,
  reading_json TEXT NOT NULL,
  cert_id TEXT NOT NULL,
  admitted_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS macros(
  name TEXT PRIMARY KEY,
  template_json TEXT NOT NULL,
  admitted_at TEXT NOT NULL,
  cert_id TEXT,
  retired INTEGER NOT NULL DEFAULT 0
);
-- The ledger_dl series (W0.4): its OWN table so the fixed-column metrics_log
-- INSERT (the legacy codec series) is never touched.
CREATE TABLE IF NOT EXISTS ledger_metrics(
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT, epoch INTEGER, event TEXT,
  ledger_dl REAL, covered_spec INTEGER, covered_request INTEGER,
  total_spec INTEGER, total_request INTEGER, total_incumbent INTEGER,
  tier_mix TEXT, toll_paid REAL, toll_retired REAL,
  max_chain_depth_used INTEGER, kernel_loc INTEGER
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
        self._migrate_generators()

    def _migrate_generators(self):
        """W2.1: widen the tier vocabulary and add the `kind` column on an older
        DB.  SQLite cannot ALTER a table-level CHECK, so a DB whose generators
        table still carries `CHECK(tier IN ('emit-check','universal'))` (or lacks
        `kind`) must be REBUILT (the canonical 12-step pattern) -- otherwise a
        later `conformance-relative(n)` / `monitored` tier insert (W4.3/W5.1) hits
        the stale CHECK with no workpackage allowed to touch this file by then."""
        cols = [r[1] for r in self.db.execute(
            "PRAGMA table_info(generators)").fetchall()]
        row = self.db.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' "
            "AND name='generators'").fetchone()
        sql = (row[0] if row else "") or ""
        needs_rebuild = ("kind" not in cols) or ("CHECK(tier IN" in sql)
        if not needs_rebuild:
            return
        old = [c for c in cols]  # preserve source column order for the copy
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS generators_new(
          generator_hash TEXT PRIMARY KEY, name TEXT NOT NULL,
          tier TEXT NOT NULL, spec_language TEXT NOT NULL,
          output_language TEXT NOT NULL, spec_grammar TEXT NOT NULL,
          emit_entrypoint TEXT NOT NULL, contract TEXT NOT NULL,
          provenance TEXT NOT NULL, emission_checked INTEGER NOT NULL DEFAULT 0,
          emission_failures INTEGER NOT NULL DEFAULT 0, admitted_at TEXT NOT NULL,
          retired INTEGER NOT NULL DEFAULT 0, subsumed_by TEXT,
          description_length REAL NOT NULL DEFAULT 0,
          kind TEXT NOT NULL DEFAULT 'emitter');
        """)
        shared = [c for c in old if c != "kind"]
        collist = ",".join(shared)
        self.db.execute(
            f"INSERT INTO generators_new({collist},kind) "
            f"SELECT {collist},'emitter' FROM generators")
        # kind backfill: translator iff output_language is a spec language.
        import planner as _pl
        specs = tuple(sorted(_pl.LANGUAGES))
        qmarks = ",".join("?" * len(specs))
        self.db.execute(
            f"UPDATE generators_new SET kind='translator' "
            f"WHERE output_language IN ({qmarks})", specs)
        self.db.execute("DROP TABLE generators")
        self.db.execute("ALTER TABLE generators_new RENAME TO generators")

    # ---------------------------------------------------------- generators
    # Explicit column list (order matches _SCHEMA), so reads never rely on
    # SELECT-* positional zip -- adding a column at the end (kind, W2.1) no
    # longer silently drops off the tail of a hardcoded name list.
    _GEN_COLS = ("generator_hash", "name", "tier", "spec_language",
                 "output_language", "spec_grammar", "emit_entrypoint",
                 "contract", "provenance", "emission_checked",
                 "emission_failures", "admitted_at", "retired", "subsumed_by",
                 "description_length", "kind")

    @staticmethod
    def _derive_kind(output_language: str) -> str:
        import planner as _pl
        return "translator" if output_language in _pl.SPEC_LANGUAGES \
            else "emitter"

    def register(self, *, name, tier, spec_language, output_language,
                 spec_grammar, emit_entrypoint, contract, provenance,
                 certificates=(), description_length=0.0, kind=None) -> str:
        from kernel.certs import TIERS
        if tier not in TIERS:
            raise ValueError(f"unknown tier {tier!r} (not in kernel TIERS)")
        body = {"name": name, "spec_language": spec_language,
                "output_language": output_language, "spec_grammar": spec_grammar,
                "emit_entrypoint": emit_entrypoint, "contract": contract}
        ghash = common.sha256_json(body)
        kind = kind or self._derive_kind(output_language)
        self.db.execute(
            "INSERT OR REPLACE INTO generators(generator_hash,name,tier,"
            "spec_language,output_language,spec_grammar,emit_entrypoint,"
            "contract,provenance,admitted_at,description_length,kind) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (ghash, name, tier, spec_language, output_language,
             common.canonical_json(spec_grammar),
             common.canonical_json(emit_entrypoint),
             common.canonical_json(contract),
             common.canonical_json(provenance),
             common.now_iso(), description_length, kind))
        for cert in certificates:
            self.store_certificate(cert, ghash)
        self.db.commit()
        return ghash

    def get(self, ghash: str) -> dict:
        row = self.db.execute(
            "SELECT " + ",".join(self._GEN_COLS)
            + " FROM generators WHERE generator_hash=?", (ghash,)).fetchone()
        if row is None:
            raise KeyError(ghash)
        return self._row_to_dict(row)

    def _row_to_dict(self, row):
        d = dict(zip(self._GEN_COLS, row))
        for k in ("spec_grammar", "emit_entrypoint", "contract", "provenance"):
            d[k] = json.loads(d[k])
        return d

    def live_generators(self) -> list:
        rows = self.db.execute(
            "SELECT " + ",".join(self._GEN_COLS)
            + " FROM generators WHERE retired=0 ORDER BY generator_hash"
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def all_generators(self) -> list:
        rows = self.db.execute(
            "SELECT " + ",".join(self._GEN_COLS)
            + " FROM generators ORDER BY admitted_at, generator_hash").fetchall()
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
                 "claims": _tuplify(json.loads(r[8])),
                 "non_claims": _tuplify(json.loads(r[9]))} for r in rows]

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

    def ingest_toll_jsonl(self, path) -> int:
        """W0.1 pre-lands the toll INGEST path (§4.8 JSONL format), so W4.1's
        cage side only has to emit; the loop stays the ledger's sole writer.

        Each line is a per-call record {incumbent_hash, tool, verdict_layer,
        wall_ms} appended by the cage at TASK TIME to its own file.  Ingestion
        increments `toll:{incumbent_hash}:calls` by one per record; `wall_ms`
        is reporting-only (house rule 13) and never enters the counter.  A
        sidecar `.pos` file records the byte offset consumed so re-ingesting is
        idempotent (append-only file, monotone offset)."""
        import pathlib
        p = pathlib.Path(path)
        if not p.exists():
            return 0
        pos_file = p.with_suffix(p.suffix + ".pos")
        start = 0
        if pos_file.exists():
            try:
                start = int(pos_file.read_text().strip() or "0")
            except ValueError:
                start = 0
        raw = p.read_bytes()
        if start > len(raw):
            start = 0  # file was truncated/rotated -> re-read from the top
        ingested = 0
        for line in raw[start:].split(b"\n"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                ih = rec["incumbent_hash"]
            except (ValueError, TypeError, KeyError):
                continue
            self.counter_add(f"toll:{ih}:calls", 1)
            ingested += 1
        pos_file.write_text(str(len(raw)))
        return ingested

    # -------------------------------------------------------------- demand
    _DEMAND_COLS = ("demand_id", "kind", "origin", "status", "language",
                    "features", "payload_ref", "size_bytes", "covered_via",
                    "created_at")

    def demand_upsert(self, row: dict) -> str:
        """Insert a demand row.  Idempotent by demand_id: an existing row is
        NEVER re-tagged (house rule 12 -- `ledger sync` respects prior
        origin/status), so this is INSERT OR IGNORE, not REPLACE."""
        d = {k: row.get(k) for k in self._DEMAND_COLS}
        d.setdefault("status", "open")
        d["created_at"] = d.get("created_at") or common.now_iso()
        if isinstance(d.get("features"), (list, dict)):
            d["features"] = common.canonical_json(d["features"])
        self.db.execute(
            "INSERT OR IGNORE INTO demand(demand_id,kind,origin,status,"
            "language,features,payload_ref,size_bytes,covered_via,created_at) "
            "VALUES(:demand_id,:kind,:origin,:status,:language,:features,"
            ":payload_ref,:size_bytes,:covered_via,:created_at)", d)
        self.db.commit()
        return d["demand_id"]

    def demand_set_status(self, demand_id: str, status: str,
                          covered_via: str = None):
        self.db.execute(
            "UPDATE demand SET status=?, covered_via=? WHERE demand_id=?",
            (status, covered_via, demand_id))
        self.db.commit()

    def demand_set_features(self, demand_id: str, features):
        if isinstance(features, (list, dict)):
            features = common.canonical_json(features)
        self.db.execute("UPDATE demand SET features=? WHERE demand_id=?",
                        (features, demand_id))
        self.db.commit()

    def _demand_row(self, row) -> dict:
        d = dict(zip(self._DEMAND_COLS, row))
        if d.get("features") is not None:
            try:
                d["features"] = json.loads(d["features"])
            except (ValueError, TypeError):
                pass
        return d

    def demand_get(self, demand_id: str):
        row = self.db.execute(
            "SELECT " + ",".join(self._DEMAND_COLS)
            + " FROM demand WHERE demand_id=?", (demand_id,)).fetchone()
        return self._demand_row(row) if row else None

    def demand_all(self, kind=None) -> list:
        q = "SELECT " + ",".join(self._DEMAND_COLS) + " FROM demand"
        args = ()
        if kind:
            q += " WHERE kind=?"
            args = (kind,)
        return [self._demand_row(r)
                for r in self.db.execute(q + " ORDER BY demand_id", args)]

    def demand_payload_hashes(self) -> set:
        """Payload hashes of committed system rewrites -- so `ledger sync`
        never launders a committed rewrite back into an exogenous row
        (house rule 12)."""
        return {r[0] for r in self.db.execute(
            "SELECT payload_ref FROM demand WHERE origin='system'")
            if r[0]}

    # ---------------------------------------------------------- readings
    def reading_add(self, demand_id: str, reading_json: str, cert_id: str):
        self.db.execute(
            "INSERT OR REPLACE INTO readings(demand_id,reading_json,cert_id,"
            "admitted_at) VALUES(?,?,?,?)",
            (demand_id, reading_json, cert_id, common.now_iso()))
        self.db.commit()

    def reading_get(self, demand_id: str):
        row = self.db.execute(
            "SELECT demand_id,reading_json,cert_id,admitted_at FROM readings "
            "WHERE demand_id=?", (demand_id,)).fetchone()
        if not row:
            return None
        return {"demand_id": row[0], "reading_json": row[1],
                "cert_id": row[2], "admitted_at": row[3]}

    def readings_all(self) -> list:
        rows = self.db.execute(
            "SELECT demand_id,reading_json,cert_id,admitted_at FROM readings "
            "ORDER BY demand_id").fetchall()
        return [{"demand_id": r[0], "reading_json": r[1], "cert_id": r[2],
                 "admitted_at": r[3]} for r in rows]

    # ------------------------------------------------------------- macros
    def macro_add(self, name: str, template_json: str, cert_id: str = None):
        self.db.execute(
            "INSERT OR REPLACE INTO macros(name,template_json,admitted_at,"
            "cert_id,retired) VALUES(?,?,?,?,0)",
            (name, template_json, common.now_iso(), cert_id))
        self.db.commit()

    def macro_retire(self, name: str):
        self.db.execute("UPDATE macros SET retired=1 WHERE name=?", (name,))
        self.db.commit()

    def macros_all(self, include_retired=False) -> list:
        q = ("SELECT name,template_json,admitted_at,cert_id,retired "
             "FROM macros")
        if not include_retired:
            q += " WHERE retired=0"
        rows = self.db.execute(q + " ORDER BY name").fetchall()
        return [{"name": r[0], "template_json": r[1], "admitted_at": r[2],
                 "cert_id": r[3], "retired": r[4]} for r in rows]

    def macro_table(self) -> dict:
        """Live macro table as {name: template} -- the checker input the DL
        gate and the reading compiler consume."""
        out = {}
        for m in self.macros_all():
            try:
                out[m["name"]] = json.loads(m["template_json"])
            except (ValueError, TypeError):
                continue
        return out

    # ------------------------------------------------------ ledger metrics
    _LEDGER_COLS = ("seq", "at", "epoch", "event", "ledger_dl",
                    "covered_spec", "covered_request", "total_spec",
                    "total_request", "total_incumbent", "tier_mix",
                    "toll_paid", "toll_retired", "max_chain_depth_used",
                    "kernel_loc")

    def ledger_metric_add(self, row: dict):
        d = {k: row.get(k) for k in self._LEDGER_COLS if k != "seq"}
        d["at"] = d.get("at") or common.now_iso()
        if isinstance(d.get("tier_mix"), (dict, list)):
            d["tier_mix"] = common.canonical_json(d["tier_mix"])
        cols = [c for c in self._LEDGER_COLS if c != "seq"]
        self.db.execute(
            "INSERT INTO ledger_metrics(" + ",".join(cols) + ") VALUES("
            + ",".join(":" + c for c in cols) + ")", d)
        self.db.commit()

    def ledger_metrics_rows(self) -> list:
        rows = self.db.execute(
            "SELECT " + ",".join(self._LEDGER_COLS)
            + " FROM ledger_metrics ORDER BY seq").fetchall()
        return [dict(zip(self._LEDGER_COLS, r)) for r in rows]

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
        if not isinstance(env, dict):
            return None  # a scalar/array blob (never written by us) -> miss
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
