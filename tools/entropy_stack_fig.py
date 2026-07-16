#!/usr/bin/env python3
"""Deterministic "progress at a glance" figure for the C3 entropy stack.

Renders `results/entropy_stack.png` from `results/entropy_refs.json` --
NEVER recomputes anything. Every number on the chart (bar heights, the
title's n_readings/stream_length, the LZ77 residual-gap annotation, the
order-1/order-2 singleton-fraction caveat) is read straight from the
committed JSON, so re-baselining is: rerun `tools/entropy_refs.py`, then
rerun this tool -- no hardcoded figure constants to keep in sync.

Bars, left to right (the story the C3 gate tells, COMPRESSION.md §11.8):

    naive (no vocabulary) -> order-0 reference -> corpus_dl (the live
    macro coder, visually emphasized as "here") -> LZ77 proxy (the T2
    gate's actual comparator, residual gap annotated) -> order-1 /
    order-2 plug-in references (visually de-emphasized: hatched, muted,
    labeled optimistic in-sample estimates, NOT floors -- §10.2/§11.8).

Determinism: Agg backend, fixed figsize/dpi, no autolayout randomness,
metadata stripped from the PNG write so two runs are byte-identical.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless, deterministic rasterizer -- before pyplot import
import matplotlib.pyplot as plt  # noqa: E402

_REPO = Path(__file__).resolve().parent.parent
JSON_PATH = _REPO / "results" / "entropy_refs.json"
PNG_OUT = _REPO / "results" / "entropy_stack.png"

# Fixed rendering constants (layout only -- no data values live here).
FIGSIZE = (10.0, 6.0)
DPI = 100

# Palette (dataviz skill categorical slots; muted grays for context/de-emphasis).
COLOR_NEUTRAL_DARK = "#898781"   # naive -- context bar
COLOR_NEUTRAL_MID = "#c3c2b7"    # order-0 -- context bar
COLOR_EMPHASIS = "#2a78d6"       # corpus_dl -- the live/current position
COLOR_COMPARATOR = "#eb6834"     # LZ77 proxy -- the actual T2 comparator
COLOR_DEEMPHASIS = "#d8d6cc"     # order-1/order-2 -- optimistic, de-emphasized
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"


def load_refs(path: Path = JSON_PATH) -> dict:
    """Load the committed entropy-reference JSON. Never recomputes."""
    with path.open() as fh:
        return json.load(fh)


def _bars_from_refs(refs: dict) -> list[dict]:
    """The six bars, every value/label component read from `refs`.

    Returns a list of dicts (in plot order) with keys: label, value,
    color, hatch, annotation (str or None), emphasized (bool).
    """
    order_k = refs["order_k"]
    stack = refs["stack"]
    lz = refs["lz77_proxy"]
    ctx2 = refs["context_stats"]["order2"]

    residual_gap = refs["residual_gap_corpus_dl_minus_lz77"]
    residual_pct = refs["residual_gap_pct_of_corpus_dl"]
    singleton_ct = ctx2["singleton_contexts"]
    distinct_ct = ctx2["distinct_contexts"]
    singleton_pct = round(100.0 * ctx2["singleton_fraction"], 1)

    bars = [
        {
            "label": "naive\n(no vocabulary)",
            "value": refs["naive_counting_dl"],
            "color": COLOR_NEUTRAL_DARK,
            "hatch": None,
            "annotation": None,
            "emphasized": False,
        },
        {
            "label": "order-0\n(memoryless)",
            "value": stack["order0_DL"],
            "color": COLOR_NEUTRAL_MID,
            "hatch": None,
            "annotation": None,
            "emphasized": False,
        },
        {
            "label": "corpus_dl\n(live macro coder)",
            "value": stack["corpus_dl"],
            "color": COLOR_EMPHASIS,
            "hatch": None,
            "annotation": "current position",
            "emphasized": True,
        },
        {
            "label": f"LZ77 proxy\n(z = {lz['z_phrases']})",
            "value": stack["lz77_proxy_DL"],
            "color": COLOR_COMPARATOR,
            "hatch": None,
            "annotation": (
                f"T2 comparator (§11.8)\n"
                f"gap: {residual_gap:g} ({residual_pct:g}%)"
            ),
            "emphasized": False,
        },
        {
            "label": "order-1\n(optimistic)",
            "value": order_k["DL1"],
            "color": COLOR_DEEMPHASIS,
            "hatch": "//",
            "annotation": None,
            "emphasized": False,
        },
        {
            "label": "order-2\n(optimistic)",
            "value": order_k["DL2"],
            "color": COLOR_DEEMPHASIS,
            "hatch": "//",
            "annotation": (
                f"optimistic, NOT a floor:\n"
                f"{singleton_ct}/{distinct_ct} ({singleton_pct:g}%)\n"
                f"contexts singleton (0-bit)"
            ),
            "emphasized": False,
        },
    ]
    return bars


def build_figure(refs: dict):
    """Build the matplotlib Figure. Every plotted number traces to `refs`."""
    bars = _bars_from_refs(refs)

    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")

    x = list(range(len(bars)))
    values = [b["value"] for b in bars]
    colors = [b["color"] for b in bars]
    hatches = [b["hatch"] for b in bars]

    rects = ax.bar(
        x, values, color=colors, width=0.62,
        edgecolor=INK_PRIMARY, linewidth=0.0, zorder=3,
    )
    for rect, hatch, b in zip(rects, hatches, bars):
        if hatch:
            rect.set_hatch(hatch)
            rect.set_edgecolor(INK_MUTED)
            rect.set_linewidth(0.8)
        if b["emphasized"]:
            rect.set_edgecolor(INK_PRIMARY)
            rect.set_linewidth(1.6)

    ax.set_xticks(x)
    ax.set_xticklabels([b["label"] for b in bars], color=INK_SECONDARY, fontsize=9)
    ax.set_ylabel("description length (counting units, bits)", color=INK_SECONDARY, fontsize=10)

    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for spine_name in ("top", "right"):
        ax.spines[spine_name].set_visible(False)
    for spine_name in ("left", "bottom"):
        ax.spines[spine_name].set_color("#c3c2b7")

    ymax = max(values) * 1.32
    ax.set_ylim(0, ymax)

    # Direct value labels above every bar (selective annotation stays below).
    for rect, b in zip(rects, bars):
        weight = "bold" if b["emphasized"] else "normal"
        ax.text(
            rect.get_x() + rect.get_width() / 2, rect.get_height() + ymax * 0.015,
            f"{b['value']:g}", ha="center", va="bottom",
            color=INK_PRIMARY, fontsize=9.5, fontweight=weight, zorder=4,
        )

    # Annotations: emphasis callout + comparator callout + optimism caveat.
    for rect, b in zip(rects, bars):
        if not b["annotation"]:
            continue
        style = dict(ha="center", va="bottom", fontsize=7.2, zorder=4)
        if b["emphasized"]:
            style["color"] = COLOR_EMPHASIS
            style["fontweight"] = "bold"
            y = rect.get_height() + ymax * 0.06
        elif b["color"] == COLOR_COMPARATOR:
            style["color"] = INK_SECONDARY
            y = rect.get_height() + ymax * 0.06
        else:
            style["color"] = INK_MUTED
            y = rect.get_height() + ymax * 0.06
        ax.text(rect.get_x() + rect.get_width() / 2, y, b["annotation"], **style)

    title = (
        f"Compression progress at a glance -- corpus_dl vs. reference floors\n"
        f"({refs['n_readings']} readings, {refs['stream_length']} tokens; "
        f"orientation references, not floors -- COMPRESSION.md §10.2/§11.8)"
    )
    ax.set_title(title, color=INK_PRIMARY, fontsize=11.5, pad=14)

    fig.tight_layout()
    return fig


def render(json_path: Path = JSON_PATH, png_out: Path = PNG_OUT) -> bytes:
    """Read refs, build the figure, write deterministic PNG bytes to `png_out`.

    Returns the bytes written so callers/tests can compare runs without a
    second disk read.
    """
    refs = load_refs(json_path)
    fig = build_figure(refs)
    try:
        # metadata={} strips matplotlib's default PNG text chunks (Software,
        # etc.) so byte output does not depend on wall-clock time or the
        # installed matplotlib/PIL version string.
        fig.savefig(png_out, format="png", metadata={})
    finally:
        plt.close(fig)
    return png_out.read_bytes()


def main() -> int:
    data = render()
    sys.stdout.write(f"wrote {PNG_OUT} ({len(data)} bytes)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
