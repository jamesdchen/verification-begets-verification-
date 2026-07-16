"""Metrics: reach, cost, composition depth, tier mix, description length,
library size, and corpus effectiveness -- logged after every admission,
promotion, or retirement; exported as CSV; plotted as reach vs cost."""
from __future__ import annotations

import csv
import json

import common
import planner as planner_mod
from buildloop import mdl


# --------------------------------------------------------------------------
# F-INT-3 (WP-B): the four math-formalization metrics fields.  They are NOT
# added to `metrics_log` -- that table's fixed-column INSERT lives in the
# unowned `library/__init__.py` and would OperationalError on new named params
# (⚠FI-8).  Instead they live in a metrics-owned side table `math_metrics`,
# created lazily here against the SAME sqlite handle the registry exposes, and
# JOINed into `export_csv` on `seq`.  Definitions are frozen (⚠FI-5):
#
#   math_total          = exogenous-origin `math-source` demand rows;
#   math_covered        = exogenous-origin `math-source` rows WITH a persisted
#                         reading (so math_covered <= math_total by construction);
#   math_dream_rows     = system-origin `math-source` rows (dreams);
#   tier_kernel_checked = kernel-checked (proof-cert) certificates -- 0 in a
#                         Lean-absent container.
#
# WP-P1 (COMPRESSION.md C1 / §11.1) appends ONE more, the m9 analogue of the
# bench's counting-prequential column:
#
#   prequential_counting_dl = the COUNTING prequential description length of the
#                         exogenous-origin math corpus: the sum of
#                         `mdl_macros.dl_reading` over each served exogenous
#                         math reading, priced under the PRE-admission macro
#                         table -- read READ-ONLY from `dl.LedgerSnapshot`
#                         .macro_table (the iteration-start snapshot that already
#                         exists).  EXOGENOUS DATA BITS ONLY (dl_reading never
#                         charges dl_macro), so junk vocabulary does NOT pay
#                         upfront in this column.  REPORTED beside the existing
#                         fields, never gated (the dl.py:9-11 one-currency law:
#                         new name, reported first).  NOT -log p; the
#                         `prequential_dl` name stays reserved for C2.
#
# These deliberately differ from dl.py's all-rows total_math/covered_math ledger
# counters; the metrics names are new and scoped (the dl.py:9-11 same-name rule).
# --------------------------------------------------------------------------
MATH_COLUMNS = ["math_total", "math_covered", "math_dream_rows",
                "tier_kernel_checked", "prequential_counting_dl"]


def _ensure_math_metrics(registry):
    registry.db.execute(
        "CREATE TABLE IF NOT EXISTS math_metrics("
        "seq INTEGER PRIMARY KEY, math_total INTEGER, math_covered INTEGER, "
        "math_dream_rows INTEGER, tier_kernel_checked INTEGER, "
        "prequential_counting_dl REAL)")
    # Idempotent forward-migration (⚠FI-8): a DB created before the WP-P1 column
    # existed carries the 4-column table.  SQLite has no ADD COLUMN IF NOT
    # EXISTS, so guard on PRAGMA table_info and ADD once -- existing DBs must not
    # break.  Append-only: never a rename, never a drop.
    cols = {r[1] for r in registry.db.execute("PRAGMA table_info(math_metrics)")}
    if "prequential_counting_dl" not in cols:
        registry.db.execute(
            "ALTER TABLE math_metrics ADD COLUMN prequential_counting_dl REAL")
    registry.db.commit()


def math_fields(registry) -> dict:
    """Compute the four F-INT-3 fields + the WP-P1 counting-prequential DL from
    the registry's live state."""
    demand = registry.demand_all("math-source")
    reading_ids = {r["demand_id"] for r in registry.readings_all()}
    exo = [r for r in demand if r.get("origin") == "exogenous"]
    total = len(exo)
    covered = sum(1 for r in exo if r["demand_id"] in reading_ids)
    dream_rows = sum(1 for r in demand if r.get("origin") == "system")
    kernel_checked = registry.db.execute(
        "SELECT COUNT(*) FROM certificates WHERE tier=?",
        ("kernel-checked",)).fetchone()[0]
    return {"math_total": total, "math_covered": covered,
            "math_dream_rows": dream_rows,
            "tier_kernel_checked": int(kernel_checked),
            "prequential_counting_dl": _math_prequential_counting_dl(registry)}


def _math_prequential_counting_dl(registry) -> float:
    """WP-P1 (C1) counting prequential DL of the exogenous math corpus.

    Prices each served exogenous math reading with `mdl_macros.dl_reading` under
    the PRE-admission macro table -- read READ-ONLY from `dl.LedgerSnapshot`
    .macro_table (the iteration-start frozen snapshot that already exists; house
    rule 13).  Data bits only, no macro model bits.  Reported, never gated."""
    from buildloop import dl as dl_mod, mdl_macros
    snap = dl_mod.snapshot(registry)          # frozen iteration-start view
    pre_table = snap.macro_table              # pre-admission snapshot (read-only)
    exo_ids = {r["demand_id"] for r in snap.demand
               if r["kind"] == "math-source" and r.get("origin") == "exogenous"}
    total = 0.0
    for did, reading in snap.readings.items():
        if did in exo_ids and isinstance(reading, dict) and "statements" in reading:
            total += mdl_macros.dl_reading(reading, pre_table)
    return round(total, 3)


def snapshot(registry, backlog, *, event: str, policy: str = "",
             corpus: bool = False) -> dict:
    live = registry.live_generators()
    depths, covered = [], 0
    for s in backlog:
        pl = planner_mod.plan(registry, s["path"])
        if not isinstance(pl, planner_mod.CoverageMiss):
            covered += 1
            depths.append(len(pl.links))
    dl = mdl.total_dl(live, backlog)
    corpus_caught = fresh_caught = 0
    for ev in registry.events("admission-rejection") + \
            registry.events("emission-rejection"):
        cb = ev["payload"].get("caught_by")
        if cb == "corpus-replay":
            corpus_caught += 1
        elif cb == "fresh":
            fresh_caught += 1
    row = {
        "at": common.now_iso(), "event": event, "policy": policy,
        "corpus": int(corpus),
        "reach": round(covered / max(1, len(backlog)), 4),
        "covered": covered, "backlog_n": len(backlog),
        "llm_input_tokens": registry.counter_get("llm_input_tokens"),
        "llm_output_tokens": registry.counter_get("llm_output_tokens"),
        "verifier_seconds": round(registry.counter_get("verifier_seconds"), 2),
        "avg_chain_depth": round(sum(depths) / len(depths), 3) if depths else 0,
        "max_chain_depth": max(depths) if depths else 0,
        "tier_universal": sum(1 for g in live if g["tier"] == "universal"),
        "tier_emit_check": sum(1 for g in live if g["tier"] == "emit-check"),
        "total_dl": round(dl["total"], 3),
        "live_size": len(live),
        "corpus_caught": corpus_caught, "fresh_caught": fresh_caught,
    }
    cur = registry.db.execute(
        "INSERT INTO metrics_log(at,event,policy,corpus,reach,covered,"
        "backlog_n,llm_input_tokens,llm_output_tokens,verifier_seconds,"
        "avg_chain_depth,max_chain_depth,tier_universal,tier_emit_check,"
        "total_dl,live_size,corpus_caught,fresh_caught) "
        "VALUES(:at,:event,:policy,:corpus,:reach,:covered,:backlog_n,"
        ":llm_input_tokens,:llm_output_tokens,:verifier_seconds,"
        ":avg_chain_depth,:max_chain_depth,:tier_universal,:tier_emit_check,"
        ":total_dl,:live_size,:corpus_caught,:fresh_caught)", row)
    seq = cur.lastrowid
    registry.db.commit()
    # F-INT-3: side-table the four math fields against the SAME seq, so the
    # export_csv JOIN aligns them onto this metrics_log row (⚠FI-8).
    mf = math_fields(registry)
    _ensure_math_metrics(registry)
    registry.db.execute(
        "INSERT OR REPLACE INTO math_metrics(seq,math_total,math_covered,"
        "math_dream_rows,tier_kernel_checked,prequential_counting_dl) "
        "VALUES(?,?,?,?,?,?)",
        (seq, mf["math_total"], mf["math_covered"], mf["math_dream_rows"],
         mf["tier_kernel_checked"], mf["prequential_counting_dl"]))
    registry.db.commit()
    row.update(mf)
    return row


COLUMNS = ["seq", "at", "event", "policy", "corpus", "reach", "covered",
           "backlog_n", "llm_input_tokens", "llm_output_tokens",
           "verifier_seconds", "avg_chain_depth", "max_chain_depth",
           "tier_universal", "tier_emit_check", "total_dl", "live_size",
           "corpus_caught", "fresh_caught"]


def export_csv(registry, path):
    """Export metrics_log LEFT JOIN math_metrics on seq.  The four F-INT-3
    columns (MATH_COLUMNS) are APPENDED after every pre-existing metrics_log
    column -- append-only, so downstream readers keyed on the old columns are
    byte-stable (verified against the pre-edit header pin)."""
    _ensure_math_metrics(registry)
    select = ["m." + c for c in COLUMNS] + ["mm." + c for c in MATH_COLUMNS]
    rows = registry.db.execute(
        "SELECT " + ",".join(select) + " FROM metrics_log m "
        "LEFT JOIN math_metrics mm ON m.seq = mm.seq ORDER BY m.seq"
    ).fetchall()
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS + MATH_COLUMNS)
        w.writerows(rows)
    return path


# --------------------------------------------------------------------------
# The ledger_dl series (Combined-Loop W0.4).  A NEW, separate series with its
# own table and CSV: the legacy `total_dl` codec series above is untouched, so
# two same-named metrics never coexist and milestones m5/m7/m8 keep reading the
# legacy series.  See METRICS.md for the distinction.
# --------------------------------------------------------------------------
def _kernel_loc() -> int:
    total = 0
    for p in sorted((common.REPO_ROOT / "kernel").glob("*.py")):
        try:
            total += sum(1 for _ in p.open())
        except OSError:
            continue
    return total


def ledger_snapshot(registry, *, epoch: int = 0, event: str = "manual") -> dict:
    """Record one row of the ledger_dl dashboard series over a frozen snapshot.

    Columns: ledger_dl, covered/total by kind, tier mix, toll paid/retired,
    max chain depth used (exogenous-serving only), and kernel LOC."""
    from buildloop import dl as dl_mod
    snap = dl_mod.snapshot(registry)
    tot = dl_mod._ledger_total(snap)

    tier_mix = {}
    for g in snap.generators:
        tier_mix[g["tier"]] = tier_mix.get(g["tier"], 0) + 1

    toll_paid = sum(dl_mod.toll_stock(
        snap.toll_calls.get(dl_mod.incumbent_hash_of(r), 0.0))
        for r in snap.demand if r["kind"] == "caged-incumbent"
        and r["status"] != "converted")
    toll_retired = registry.counter_get("toll_retired")

    max_depth = 0
    for r in snap.demand:
        if (r["kind"] == "spec-file" and r.get("origin") == "exogenous"
                and r.get("language") and r.get("features")):
            chain = planner_mod.plan_for_features(
                snap.generators, r["language"], r["features"],
                target_language="python-codec")
            if chain is not None:
                max_depth = max(max_depth, len(chain))

    row = {
        "epoch": epoch, "event": event,
        "ledger_dl": round(tot["ledger_dl"], 3),
        "covered_spec": tot["covered_spec"],
        "covered_request": tot["covered_request"],
        "total_spec": tot["total_spec"],
        "total_request": tot["total_request"],
        "total_incumbent": tot["total_incumbent"],
        "tier_mix": tier_mix,
        "toll_paid": round(toll_paid, 3),
        "toll_retired": round(toll_retired, 3),
        "max_chain_depth_used": max_depth,
        "kernel_loc": _kernel_loc(),
    }
    registry.ledger_metric_add(row)
    return row


LEDGER_COLUMNS = ["seq", "at", "epoch", "event", "ledger_dl", "covered_spec",
                  "covered_request", "total_spec", "total_request",
                  "total_incumbent", "tier_mix", "toll_paid", "toll_retired",
                  "max_chain_depth_used", "kernel_loc"]


def export_ledger_csv(registry, path):
    rows = registry.ledger_metrics_rows()
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(LEDGER_COLUMNS)
        for r in rows:
            w.writerow([r.get(c) for c in LEDGER_COLUMNS])
    return path
