"""Reach-vs-cost plot: one curve per steering policy (and per corpus flag)."""
from __future__ import annotations

import csv
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _load(csv_path):
    with open(csv_path) as f:
        return list(csv.DictReader(f))


def reach_vs_cost(csv_paths, out_png, title="Reach vs cumulative cost",
                  cost_label="cumulative cost (LLM kilotokens + verifier seconds)"):
    """csv_paths: {label: path}.  Cost = LLM tokens (in+out, thousands)
    + verifier seconds.  Callers that pin ``verifier_seconds`` to 0 (the
    F-INT-3 math shim, so the axis is kilotokens-only per E6) pass a
    ``cost_label`` that says so instead of the legacy composite label."""
    fig, ax = plt.subplots(figsize=(8, 5), dpi=140)
    for label, path in csv_paths.items():
        rows = _load(path)
        series = defaultdict(list)
        for r in rows:
            key = f"{label}"
            cost = (float(r["llm_input_tokens"]) +
                    float(r["llm_output_tokens"])) / 1000.0 + \
                float(r["verifier_seconds"])
            series[key].append((cost, float(r["reach"])))
        for key, pts in series.items():
            pts.sort()
            ax.plot([p[0] for p in pts], [p[1] for p in pts],
                    marker="o", markersize=3, linewidth=1.5, label=key)
    ax.set_xlabel(cost_label)
    ax.set_ylabel("reach (fraction of backlog coverable)")
    ax.set_ylim(0, 1.02)
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)
    return out_png
