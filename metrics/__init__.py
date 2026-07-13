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
