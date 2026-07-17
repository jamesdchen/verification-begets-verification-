#!/usr/bin/env python3
"""Tests for tools/dl_trajectories_fig.py -- the two-currency governance
readout figure over results/formalize_governed.csv.

Guards:
  * determinism: two independent renders of the committed CSV produce
    byte-identical PNGs (Agg backend, fixed figsize/dpi, metadata stripped);
  * no hardcoding: the per-wave trajectories for both arms/both currencies,
    and the final-wave hindsight/prequential gap annotations, are all read
    from the CSV -- shift the CSV's numbers and the rendered text must
    shift with them;
  * BY COLUMN NAME: the tool reads via csv.DictReader, so it is robust to
    future appended columns (row order / extra trailing columns must not
    break it);
  * the dream bookkeeping row is skipped -- it is not a wave of either arm;
  * the tool never recomputes (no bench_formalize / mdl_macros import) --
    csv module only, reading results/formalize_governed.csv.
"""
import copy
import csv
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools import dl_trajectories_fig as fig_tool  # noqa: E402


def _real_rows():
    return fig_tool.load_rows()


def _all_text(fig):
    ax = fig.axes[0]
    parts = [t.get_text() for t in ax.texts]
    parts.append(ax.get_title())
    leg = ax.get_legend()
    if leg is not None:
        parts.extend(t.get_text() for t in leg.get_texts())
    return "\n".join(parts)


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_never_recomputes_reads_csv_only():
    src = (_REPO / "tools" / "dl_trajectories_fig.py").read_text()
    assert "bench_formalize" not in src
    assert "mdl_macros" not in src
    assert "import mdl_macros" not in src
    assert "import bench_formalize" not in src
    assert "import csv" in src


def test_load_rows_reads_committed_csv_by_column_name():
    rows = _real_rows()
    with (_REPO / "results" / "formalize_governed.csv").open(newline="") as fh:
        on_disk = [r for r in csv.DictReader(fh) if r["arm"] != "dream"]
    assert rows == on_disk


def test_dream_row_is_skipped():
    rows = _real_rows()
    assert all(r["arm"] != "dream" for r in rows)
    # sanity: the committed CSV does have a dream row that got filtered out
    with (_REPO / "results" / "formalize_governed.csv").open(newline="") as fh:
        raw = list(csv.DictReader(fh))
    assert any(r["arm"] == "dream" for r in raw)
    assert len(rows) == len(raw) - 1


def test_robust_to_appended_columns():
    # A future column appended at the END of the CSV must not break loading
    # or the by-name series extraction.
    rows = _real_rows()
    fieldnames = list(rows[0].keys()) + ["future_metric"]
    augmented = [dict(r, future_metric="99") for r in rows]
    # re-add the dream row so the on-disk shape matches the real file
    with (_REPO / "results" / "formalize_governed.csv").open(newline="") as fh:
        raw = list(csv.DictReader(fh))
    dream_row = next(r for r in raw if r["arm"] == "dream")
    all_rows = [dict(dream_row, future_metric="99")] + augmented

    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "augmented.csv"
        _write_csv(p, all_rows, fieldnames)
        loaded = fig_tool.load_rows(p)
        assert len(loaded) == len(rows)
        gov_series = fig_tool._series(loaded, "governed", fig_tool.REPORTED_COL)
        real_gov_series = fig_tool._series(rows, "governed", fig_tool.REPORTED_COL)
        assert gov_series == real_gov_series


def test_series_values_match_csv_for_both_arms_and_columns():
    rows = _real_rows()
    for arm in ("governed", "ungoverned"):
        for col in (fig_tool.REPORTED_COL, fig_tool.PREQUENTIAL_COL):
            pts = fig_tool._series(rows, arm, col)
            expected = sorted(
                (int(r["wave"]), float(r[col])) for r in rows if r["arm"] == arm
            )
            assert pts == expected
            assert len(pts) == 5  # waves 0..4


def test_final_wave_gap_values_computed_from_csv():
    rows = _real_rows()
    final_wave, hindsight_gap, prequential_gap = fig_tool._final_wave_gaps(rows)
    assert final_wave == 4
    gov_rep = dict(fig_tool._series(rows, "governed", fig_tool.REPORTED_COL))
    ung_rep = dict(fig_tool._series(rows, "ungoverned", fig_tool.REPORTED_COL))
    gov_preq = dict(fig_tool._series(rows, "governed", fig_tool.PREQUENTIAL_COL))
    ung_preq = dict(fig_tool._series(rows, "ungoverned", fig_tool.PREQUENTIAL_COL))
    assert hindsight_gap == gov_rep[4] - ung_rep[4]
    assert prequential_gap == gov_preq[4] - ung_preq[4]
    # sanity against the currently committed numbers
    assert hindsight_gap == -232.0
    assert prequential_gap == -123.0


def test_title_states_two_currency_governance_readout():
    rows = _real_rows()
    fig = fig_tool.build_figure(rows)
    try:
        title = fig.axes[0].get_title()
        assert "two-currency" in title
        assert "governance" in title
        assert fig_tool.REPORTED_COL in title
        assert fig_tool.PREQUENTIAL_COL in title
    finally:
        matplotlib.pyplot.close(fig)


def test_gap_annotation_text_carries_computed_values():
    rows = _real_rows()
    fig = fig_tool.build_figure(rows)
    try:
        text_blob = _all_text(fig)
        final_wave, hindsight_gap, prequential_gap = fig_tool._final_wave_gaps(rows)
        assert f"{hindsight_gap:g}" in text_blob
        assert f"{prequential_gap:g}" in text_blob
        assert str(final_wave) in text_blob
    finally:
        matplotlib.pyplot.close(fig)


def test_shifted_csv_values_move_the_gap_annotations():
    # No hardcoding: mutate the final-wave CSV values and the rendered gap
    # annotations must follow (and the ORIGINAL gap values must not leak).
    rows = copy.deepcopy(_real_rows())
    for r in rows:
        if r["arm"] == "governed" and r["wave"] == "4":
            r["reported_exogenous_dl"] = "1900.0"
            r["prequential_counting_dl"] = "2000.0"
        if r["arm"] == "ungoverned" and r["wave"] == "4":
            r["reported_exogenous_dl"] = "2500.0"
            r["prequential_counting_dl"] = "2450.0"

    fig = fig_tool.build_figure(rows)
    try:
        text_blob = _all_text(fig)
        new_final, new_hind, new_preq = fig_tool._final_wave_gaps(rows)
        assert new_hind == 1900.0 - 2500.0
        assert new_preq == 2000.0 - 2450.0
        assert f"{new_hind:g}" in text_blob
        assert f"{new_preq:g}" in text_blob

        real_rows = _real_rows()
        _, real_hind, real_preq = fig_tool._final_wave_gaps(real_rows)
        assert f"{real_hind:g}" not in text_blob
        assert f"{real_preq:g}" not in text_blob
    finally:
        matplotlib.pyplot.close(fig)


def test_render_is_deterministic_across_two_runs(tmp_path):
    out_a = tmp_path / "a.png"
    out_b = tmp_path / "b.png"
    bytes_a = fig_tool.render(png_out=out_a)
    bytes_b = fig_tool.render(png_out=out_b)
    assert bytes_a == bytes_b
    assert out_a.read_bytes() == out_b.read_bytes()


def test_render_deterministic_via_cli_subprocess(tmp_path):
    # End-to-end: invoke the script as a subprocess twice against a copy of
    # the committed CSV, confirm byte-identical PNGs without touching the
    # committed results/dl_trajectories.png.
    csv_copy = tmp_path / "formalize_governed.csv"
    csv_copy.write_text((_REPO / "results" / "formalize_governed.csv").read_text())
    out1 = tmp_path / "out1.png"
    out2 = tmp_path / "out2.png"
    script = (
        "import sys; sys.path.insert(0, %r); "
        "from tools import dl_trajectories_fig as f; "
        "from pathlib import Path; "
        "f.render(csv_path=Path(%r), png_out=Path(%r))"
    )
    subprocess.run(
        [sys.executable, "-c", script % (str(_REPO), str(csv_copy), str(out1))],
        check=True, cwd=str(_REPO),
    )
    subprocess.run(
        [sys.executable, "-c", script % (str(_REPO), str(csv_copy), str(out2))],
        check=True, cwd=str(_REPO),
    )
    assert out1.read_bytes() == out2.read_bytes()


def test_committed_png_matches_fresh_render():
    # The committed results/dl_trajectories.png must equal what the tool
    # currently produces from the committed CSV (no drift).
    committed = (_REPO / "results" / "dl_trajectories.png").read_bytes()
    fresh = fig_tool.render(png_out=_REPO / "results" / "dl_trajectories.png")
    assert committed == fresh


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            if "tmp_path" in fn.__code__.co_varnames[: fn.__code__.co_argcount]:
                import tempfile
                with tempfile.TemporaryDirectory() as d:
                    fn(Path(d))
            else:
                fn()
            print("ok", name)
