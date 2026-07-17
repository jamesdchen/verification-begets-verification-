#!/usr/bin/env python3
"""Deterministic two-currency governance readout for the formalize bench.

Renders `results/dl_trajectories.png` from `results/formalize_governed.csv`
-- NEVER recomputes anything: the standard-library csv module is the only
import used to read data, and none of the bench's miner/macro-coder modules
are imported. Every number on the chart (per-wave DL trajectories for both
arms, the final-wave hindsight-gap and prequential-gap annotations) is read
straight from the committed CSV BY COLUMN NAME (`csv.DictReader`, so the
tool is robust to future appended columns), so re-baselining is: rerun the
bench, then rerun this tool -- no hardcoded figure constants to keep in sync.

The two currencies (COMPRESSION.md WP-P1 / C1 §11.1, `formalize_governed.
meta.json` honesty_notes.prequential_counting_dl):

  * `reported_exogenous_dl`  (solid lines) -- the HINDSIGHT macro-coder DL:
    exogenous data bits + the live macro model's bits, charged in hindsight
    against the final wave's table.
  * `prequential_counting_dl` (dashed lines) -- the PREQUENTIAL, wave-
    granular COUNTING DL: exogenous data bits only, each wave's NEW readings
    priced under the PRE-wave frozen table (no model bits; origin-blind).

Two arms, one line color each: `governed` (exogenous-only mining, per-use
certs) vs `ungoverned` (exogenous+dream mining, no certs). The `dream`
bookkeeping row (wave 0, all-zero) is not a wave of either arm and is
skipped. The final-wave GAP between the two arms in EACH currency is the
governance readout this figure exists to show -- annotated, computed at
render time from whatever the CSV's final wave happens to be.

Determinism: Agg backend, fixed figsize/dpi, no autolayout randomness,
metadata stripped from the PNG write so two runs are byte-identical.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless, deterministic rasterizer -- before pyplot import
import matplotlib.pyplot as plt  # noqa: E402

_REPO = Path(__file__).resolve().parent.parent
CSV_PATH = _REPO / "results" / "formalize_governed.csv"
PNG_OUT = _REPO / "results" / "dl_trajectories.png"

# Fixed rendering constants (layout only -- no data values live here).
FIGSIZE = (11.5, 6.2)
DPI = 100

# Palette (dataviz skill categorical slots).
COLOR_GOVERNED = "#2a78d6"    # blue -- exogenous-only mining, per-use certs
COLOR_UNGOVERNED = "#eb6834"  # orange -- exogenous+dream mining, no certs
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"

ARM_COLORS = {"governed": COLOR_GOVERNED, "ungoverned": COLOR_UNGOVERNED}
ARM_ORDER = ("governed", "ungoverned")
REPORTED_COL = "reported_exogenous_dl"
PREQUENTIAL_COL = "prequential_counting_dl"
DREAM_ARM = "dream"


def load_rows(path: Path = CSV_PATH) -> list[dict]:
    """Load the committed CSV by column name. Never recomputes.

    Skips the `dream` bookkeeping row -- it is not a wave of either arm.
    `csv.DictReader` reads by header name, so appending new columns to the
    CSV in the future does not break this tool.
    """
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        rows = [row for row in reader if row["arm"] != DREAM_ARM]
    return rows


def _series(rows: list[dict], arm: str, col: str) -> list[tuple]:
    """(wave, value) pairs for one arm/column, sorted by wave."""
    pts = [(int(r["wave"]), float(r[col])) for r in rows if r["arm"] == arm]
    pts.sort(key=lambda p: p[0])
    return pts


def _final_wave_gaps(rows: list[dict]) -> tuple:
    """Compute (final_wave, hindsight_gap, prequential_gap), governed minus
    ungoverned, at whatever the CSV's final wave happens to be. Sign-aware,
    never hardcoded."""
    gov_rep = dict(_series(rows, "governed", REPORTED_COL))
    ung_rep = dict(_series(rows, "ungoverned", REPORTED_COL))
    gov_preq = dict(_series(rows, "governed", PREQUENTIAL_COL))
    ung_preq = dict(_series(rows, "ungoverned", PREQUENTIAL_COL))
    final_wave = max(gov_rep)
    hindsight_gap = gov_rep[final_wave] - ung_rep[final_wave]
    prequential_gap = gov_preq[final_wave] - ung_preq[final_wave]
    return final_wave, hindsight_gap, prequential_gap


def build_figure(rows: list[dict]):
    """Build the matplotlib Figure. Every plotted number traces to `rows`."""
    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")

    all_values = []
    for arm in ARM_ORDER:
        color = ARM_COLORS[arm]
        reported = _series(rows, arm, REPORTED_COL)
        prequential = _series(rows, arm, PREQUENTIAL_COL)
        all_values.extend(v for _, v in reported)
        all_values.extend(v for _, v in prequential)

        ax.plot(
            [w for w, _ in reported], [v for _, v in reported],
            color=color, linestyle="-", marker="o", markersize=5,
            linewidth=2.0, zorder=3,
            label=f"{arm}: {REPORTED_COL} (hindsight)",
        )
        ax.plot(
            [w for w, _ in prequential], [v for _, v in prequential],
            color=color, linestyle="--", marker="s", markersize=4.5,
            linewidth=2.0, zorder=3,
            label=f"{arm}: {PREQUENTIAL_COL} (prequential)",
        )

        # direct end labels
        last_w, last_v = reported[-1]
        ax.text(last_w + 0.08, last_v, f"{last_v:g}", color=color,
                 fontsize=8.5, fontweight="bold", va="center", zorder=4)
        last_w2, last_v2 = prequential[-1]
        ax.text(last_w2 + 0.08, last_v2, f"{last_v2:g}", color=color,
                 fontsize=8.5, va="center", zorder=4)

    final_wave, hindsight_gap, prequential_gap = _final_wave_gaps(rows)

    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for spine_name in ("top", "right"):
        ax.spines[spine_name].set_visible(False)
    for spine_name in ("left", "bottom"):
        ax.spines[spine_name].set_color("#c3c2b7")

    all_waves = sorted({int(r["wave"]) for r in rows})
    ax.set_xticks(all_waves)
    ax.set_xticklabels([f"wave {w}" for w in all_waves], color=INK_SECONDARY, fontsize=9)
    ax.set_xlim(min(all_waves) - 0.3, max(all_waves) + 1.6)
    ax.set_ylabel("description length (counting units, bits)", color=INK_SECONDARY, fontsize=10)
    ymax = max(all_values) * 1.18
    ax.set_ylim(0, ymax)

    ax.legend(loc="upper left", fontsize=8, frameon=False, labelcolor=INK_SECONDARY)

    gap_text = (
        f"final wave {final_wave} governance gaps (governed - ungoverned):\n"
        f"hindsight ({REPORTED_COL}): {hindsight_gap:g}\n"
        f"prequential ({PREQUENTIAL_COL}): {prequential_gap:g}"
    )
    ax.text(
        0.98, 0.02, gap_text, transform=ax.transAxes,
        ha="right", va="bottom", fontsize=8.2, color=INK_PRIMARY,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#f0efec",
                   edgecolor="#c3c2b7", linewidth=0.8),
        zorder=5,
    )

    title = (
        "Formalize bench: governed vs. ungoverned -- two-currency governance readout\n"
        f"(solid = {REPORTED_COL} [hindsight]; dashed = {PREQUENTIAL_COL} "
        "[prequential, data bits only]; dream row excluded)"
    )
    ax.set_title(title, color=INK_PRIMARY, fontsize=10.3, pad=14)

    fig.tight_layout()
    return fig


def render(csv_path: Path = CSV_PATH, png_out: Path = PNG_OUT) -> bytes:
    """Read rows, build the figure, write deterministic PNG bytes to `png_out`.

    Returns the bytes written so callers/tests can compare runs without a
    second disk read.
    """
    rows = load_rows(csv_path)
    fig = build_figure(rows)
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
