"""Metrics: reach, cost, composition depth, tier mix, description length,
library size, and corpus effectiveness -- logged after every admission,
promotion, or retirement; exported as CSV; plotted as reach vs cost."""
from __future__ import annotations

import csv
import json

import common
import planner as planner_mod
from buildloop import mdl


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
    registry.db.execute(
        "INSERT INTO metrics_log(at,event,policy,corpus,reach,covered,"
        "backlog_n,llm_input_tokens,llm_output_tokens,verifier_seconds,"
        "avg_chain_depth,max_chain_depth,tier_universal,tier_emit_check,"
        "total_dl,live_size,corpus_caught,fresh_caught) "
        "VALUES(:at,:event,:policy,:corpus,:reach,:covered,:backlog_n,"
        ":llm_input_tokens,:llm_output_tokens,:verifier_seconds,"
        ":avg_chain_depth,:max_chain_depth,:tier_universal,:tier_emit_check,"
        ":total_dl,:live_size,:corpus_caught,:fresh_caught)", row)
    registry.db.commit()
    return row


COLUMNS = ["seq", "at", "event", "policy", "corpus", "reach", "covered",
           "backlog_n", "llm_input_tokens", "llm_output_tokens",
           "verifier_seconds", "avg_chain_depth", "max_chain_depth",
           "tier_universal", "tier_emit_check", "total_dl", "live_size",
           "corpus_caught", "fresh_caught"]


def export_csv(registry, path):
    rows = registry.db.execute(
        "SELECT " + ",".join(COLUMNS) + " FROM metrics_log ORDER BY seq"
    ).fetchall()
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
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
