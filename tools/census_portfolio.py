#!/usr/bin/env python3
"""Portfolio census: every intaken corpus, one command (PLAN_FRAGMENT §2).

The flywheel's measuring step is 're-census the full corpus portfolio'.  This
tool walks ``specs/mathsources/*/nodes.jsonl`` (a corpus = a directory holding
the intake pair ``nodes.jsonl`` + ``fetch_meta.json``), runs the same
``tools/blueprint_census.py`` census on each, and writes:

- ``results/blueprint_census_<corpus>.json`` / ``.md`` -- the per-corpus
  report, unchanged in shape from the single-corpus tool;
- ``results/census_portfolio.json`` / ``.md`` -- the rollup the flywheel
  diffs across cycles: per-corpus verdict counts + miss histograms, the
  portfolio-wide totals, and the attempt-candidate labels per corpus (the
  C2 mining queue, in document order).

Deterministic, LLM-free, Lean-free, network-free: corpora in sorted name
order, everything downstream of the committed intake.  Same honesty rule as
the census itself: signals, never fidelity verdicts.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.blueprint_census import census, render_md


def portfolio(sources_root: str) -> dict:
    """Census every corpus under ``sources_root``; rollup + per-corpus reports.

    Returns ``{"portfolio": <rollup>, "reports": {corpus: <census report>}}``.
    """
    corpora = sorted(
        name for name in os.listdir(sources_root)
        if os.path.isfile(os.path.join(sources_root, name, "nodes.jsonl")))
    reports: dict = {}
    rollup_rows = []
    total_hist: dict = {}
    total_verdicts: dict = {}
    n_total = 0
    for name in corpora:
        nodes = []
        with open(os.path.join(sources_root, name, "nodes.jsonl")) as fh:
            for line in fh:
                if line.strip():
                    nodes.append(json.loads(line))
        rep = census(nodes)
        reports[name] = rep
        n_total += rep["n_nodes"]
        for k, v in rep["verdicts"].items():
            total_verdicts[k] = total_verdicts.get(k, 0) + v
        for k, v in rep["miss_histogram"].items():
            total_hist[k] = total_hist.get(k, 0) + v
        rollup_rows.append({
            "corpus": name,
            "n_nodes": rep["n_nodes"],
            "verdicts": rep["verdicts"],
            "miss_histogram": rep["miss_histogram"],
            "attempt_candidates": [
                r["label"] for r in rep["rows"]
                if r["verdict"] == "attempt-candidate"],
        })
    rollup = {
        "tool": "census_portfolio",
        "honesty": ("rollup of lexical censuses, deterministic, LLM-free, "
                    "Lean-free; REPORTS signals -- never a fidelity verdict. "
                    "attempt_candidates is the C2 mining queue, not a claim "
                    "any node certifies."),
        "n_corpora": len(corpora),
        "n_nodes": n_total,
        "verdicts": total_verdicts,
        "miss_histogram": dict(sorted(total_hist.items(),
                                      key=lambda kv: (-kv[1], kv[0]))),
        "corpora": rollup_rows,
    }
    return {"portfolio": rollup, "reports": reports}


def render_portfolio_md(rollup: dict) -> str:
    lines = ["# Corpus portfolio census", "",
             f"corpora: {rollup['n_corpora']}  ·  nodes: {rollup['n_nodes']}"
             "  ·  verdicts: "
             + ", ".join(f"{k}={v}" for k, v in
                         sorted(rollup["verdicts"].items())), "",
             "**" + rollup["honesty"] + "**", "",
             "## Portfolio miss histogram (the price list)", ""]
    for cat, n in rollup["miss_histogram"].items():
        lines.append(f"- {cat}: {n}")
    lines += ["", "## Per corpus", "",
              "| corpus | nodes | attempt-candidates | out-of-fragment "
              "| no-signal | top miss |",
              "|---|---|---|---|---|---|"]
    for row in rollup["corpora"]:
        v = row["verdicts"]
        top = next(iter(row["miss_histogram"]), "—")
        lines.append("| {} | {} | {} | {} | {} | {} |".format(
            row["corpus"], row["n_nodes"],
            v.get("attempt-candidate", 0), v.get("out-of-fragment", 0),
            v.get("no-signal", 0), top))
    lines += ["", "## C2 mining queue (attempt-candidate labels)", ""]
    for row in rollup["corpora"]:
        if row["attempt_candidates"]:
            lines.append(f"- **{row['corpus']}** "
                         f"({len(row['attempt_candidates'])}): "
                         + ", ".join(row["attempt_candidates"]))
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sources", default="specs/mathsources",
                    help="corpus root (dirs holding nodes.jsonl)")
    ap.add_argument("--out-dir", default="results",
                    help="where per-corpus and rollup reports land")
    args = ap.parse_args(argv)
    from buildloop import lanes
    with lanes.token_free("census-portfolio"):
        result = portfolio(args.sources)
    for name, rep in result["reports"].items():
        base = os.path.join(args.out_dir, f"blueprint_census_{name}")
        with open(base + ".json", "w") as fh:
            json.dump(rep, fh, indent=1, sort_keys=True)
        with open(base + ".md", "w") as fh:
            fh.write(render_md(rep))
    rollup = result["portfolio"]
    base = os.path.join(args.out_dir, "census_portfolio")
    with open(base + ".json", "w") as fh:
        json.dump(rollup, fh, indent=1, sort_keys=True)
    with open(base + ".md", "w") as fh:
        fh.write(render_portfolio_md(rollup))
    print(f"portfolio: {rollup['n_corpora']} corpora, "
          f"{rollup['n_nodes']} nodes -> {base}.json/.md")
    print("verdicts:", rollup["verdicts"])
    print("miss histogram:", rollup["miss_histogram"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
