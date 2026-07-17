#!/usr/bin/env python3
"""Tests for tools/entropy_stack_fig.py -- the C3 "progress at a glance" figure.

Guards:
  * determinism: two independent renders of the committed JSON produce
    byte-identical PNGs (Agg backend, fixed figsize/dpi, metadata stripped);
  * no hardcoding: every plotted number (bar heights, title's n_readings /
    stream_length, LZ77 residual-gap annotation, order-2 singleton-fraction
    caveat, the three adaptive-KT bars, the k=1 C2-exhibit gap) is read from
    the JSON files -- shift the JSON's numbers and the rendered text must
    shift with them;
  * bar order/labels match the spec: all bars sorted by value descending, so
    naive, adaptive-KT-k0, order-0, corpus_dl (emphasized), LZ77 proxy
    (residual-gap annotated), adaptive-KT-k2, adaptive-KT-k1 (C2 exhibit,
    sign-aware gap annotated), order-1, order-2 (de-emphasized, annotated
    optimistic/not-a-floor);
  * the tool never recomputes (no bench_formalize / mdl_macros / ppm_ref
    import) -- it only reads results/entropy_refs.json and results/ppm_ref.json.
"""
import copy
import json
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools import entropy_stack_fig as fig_tool  # noqa: E402


def _real_refs():
    return fig_tool.load_refs()


def _real_ppm():
    return fig_tool.load_ppm_refs()


def _all_text(fig):
    return "\n".join(t.get_text() for t in fig.axes[0].texts) + "\n" + fig.axes[0].get_title()


def test_never_recomputes_reads_json_only():
    src = (_REPO / "tools" / "entropy_stack_fig.py").read_text()
    assert "bench_formalize" not in src
    assert "mdl_macros" not in src
    assert "import mdl_macros" not in src
    # reads ppm_ref.json directly; must not import the ppm_ref TOOL (which
    # would recompute the adaptive-KT coders instead of reading the committed
    # reference file).
    assert "import ppm_ref" not in src
    assert "from tools import ppm_ref" not in src


def test_load_refs_reads_committed_json():
    refs = _real_refs()
    on_disk = json.loads((_REPO / "results" / "entropy_refs.json").read_text())
    assert refs == on_disk


def test_load_ppm_refs_reads_committed_json():
    ppm = _real_ppm()
    on_disk = json.loads((_REPO / "results" / "ppm_ref.json").read_text())
    assert ppm == on_disk


def test_bars_order_and_labels():
    refs = _real_refs()
    ppm = _real_ppm()
    bars = fig_tool._bars_from_refs(refs, ppm)
    assert len(bars) == 9
    labels = [b["label"].split("\n")[0] for b in bars]
    assert labels == [
        "naive",
        "adaptive KT k=0",
        "order-0",
        "corpus_dl",
        "LZ77 proxy",
        "adaptive KT k=2",
        "adaptive KT k=1",
        "order-1",
        "order-2",
    ]
    # bars are sorted by value, descending -- "placed among the references
    # by value", not a hardcoded position.
    values = [b["value"] for b in bars]
    assert values == sorted(values, reverse=True)
    assert values == [
        refs["naive_counting_dl"],
        ppm["results"]["kt"]["0"]["adaptive_DL"],
        refs["stack"]["order0_DL"],
        refs["stack"]["corpus_dl"],
        refs["stack"]["lz77_proxy_DL"],
        ppm["results"]["kt"]["2"]["adaptive_DL"],
        ppm["results"]["kt"]["1"]["adaptive_DL"],
        refs["order_k"]["DL1"],
        refs["order_k"]["DL2"],
    ]
    # exactly one emphasized bar (corpus_dl -- the current position)
    emphasized = [b for b in bars if b["emphasized"]]
    assert len(emphasized) == 1
    assert emphasized[0]["label"].startswith("corpus_dl")
    # order-1/order-2 are visually de-emphasized (hatched)
    deemph = [b for b in bars if b["label"].startswith(("order-1", "order-2"))]
    assert all(b["hatch"] for b in deemph)
    assert all(not b["emphasized"] for b in deemph)
    # the three adaptive-KT bars share a distinct color and are never hatched
    adaptive = [b for b in bars if b["label"].startswith("adaptive KT")]
    assert len(adaptive) == 3
    assert all(b["color"] == fig_tool.COLOR_ADAPTIVE for b in adaptive)
    assert all(not b["hatch"] for b in adaptive)
    assert all(not b["emphasized"] for b in adaptive)
    # exactly one highlighted bar (k=1 -- the C2 exhibit)
    highlighted = [b for b in bars if b["highlight"]]
    assert len(highlighted) == 1
    assert highlighted[0]["label"].startswith("adaptive KT k=1")


def test_lz77_annotation_carries_residual_gap_from_json():
    refs = _real_refs()
    ppm = _real_ppm()
    bars = fig_tool._bars_from_refs(refs, ppm)
    lz_bar = next(b for b in bars if b["label"].startswith("LZ77"))
    gap = refs["residual_gap_corpus_dl_minus_lz77"]
    pct = refs["residual_gap_pct_of_corpus_dl"]
    assert f"{gap:g}" in lz_bar["annotation"]
    assert f"{pct:g}" in lz_bar["annotation"]


def test_order2_annotation_carries_small_sample_caveat_from_json():
    refs = _real_refs()
    ppm = _real_ppm()
    bars = fig_tool._bars_from_refs(refs, ppm)
    o2_bar = next(b for b in bars if b["label"].startswith("order-2"))
    ctx2 = refs["context_stats"]["order2"]
    assert str(ctx2["singleton_contexts"]) in o2_bar["annotation"]
    assert str(ctx2["distinct_contexts"]) in o2_bar["annotation"]
    assert "NOT a floor" in o2_bar["annotation"]


def test_adaptive_kt_k1_annotation_carries_sign_aware_gap_and_c2_label():
    # currently -624.494 (adaptive beats corpus_dl) -- must render WITH sign,
    # not abs(), and must be tagged as the C2 exhibit (COMPRESSION.md §10.7).
    refs = _real_refs()
    ppm = _real_ppm()
    bars = fig_tool._bars_from_refs(refs, ppm)
    k1_bar = next(b for b in bars if b["label"].startswith("adaptive KT k=1"))
    gap = ppm["results"]["kt"]["1"]["adaptive_minus_corpus_dl"]
    assert gap < 0  # sanity: currently beats corpus_dl
    assert f"{gap:g}" in k1_bar["annotation"]
    assert "-" in k1_bar["annotation"].split("adaptive_DL - corpus_dl:")[1].split("\n")[0]
    assert "C2 exhibit" in k1_bar["annotation"]
    assert "§10.7" in k1_bar["annotation"]


def test_adaptive_kt_k0_and_k2_values_from_json():
    refs = _real_refs()
    ppm = _real_ppm()
    bars = fig_tool._bars_from_refs(refs, ppm)
    k0_bar = next(b for b in bars if b["label"].startswith("adaptive KT k=0"))
    k2_bar = next(b for b in bars if b["label"].startswith("adaptive KT k=2"))
    assert k0_bar["value"] == ppm["results"]["kt"]["0"]["adaptive_DL"]
    assert k2_bar["value"] == ppm["results"]["kt"]["2"]["adaptive_DL"]


def test_title_carries_n_readings_and_stream_length():
    refs = _real_refs()
    ppm = _real_ppm()
    fig = fig_tool.build_figure(refs, ppm)
    try:
        title = fig.axes[0].get_title()
        assert str(refs["n_readings"]) in title
        assert str(refs["stream_length"]) in title
    finally:
        matplotlib.pyplot.close(fig)


def test_shifted_json_values_change_the_rendered_labels():
    # No hardcoding: mutate the numbers and the rendered text must follow.
    refs = copy.deepcopy(_real_refs())
    ppm = _real_ppm()
    refs["n_readings"] = 999
    refs["stream_length"] = 123456
    refs["corpus_dl"] = 7777.0
    refs["stack"]["corpus_dl"] = 7777.0
    refs["stack"]["lz77_proxy_DL"] = 6543.21
    refs["residual_gap_corpus_dl_minus_lz77"] = 1234.56
    refs["residual_gap_pct_of_corpus_dl"] = 15.9
    refs["order_k"]["DL1"] = 111.111
    refs["order_k"]["DL2"] = 22.222
    refs["context_stats"]["order2"]["singleton_contexts"] = 88
    refs["context_stats"]["order2"]["distinct_contexts"] = 200

    fig = fig_tool.build_figure(refs, ppm)
    try:
        text_blob = _all_text(fig)
        assert "999" in text_blob
        assert "123456" in text_blob
        assert "7777" in text_blob
        assert "6543.21" in text_blob
        assert "1234.56" in text_blob
        assert "111.111" in text_blob
        assert "22.222" in text_blob
        assert "88" in text_blob
        assert "200" in text_blob
        # the ORIGINAL committed numbers must not leak into this render
        real = _real_refs()
        assert f"{real['stack']['corpus_dl']:g}" not in text_blob
        assert f"{real['n_readings']}" not in text_blob
    finally:
        matplotlib.pyplot.close(fig)


def test_shifted_kt_values_change_adaptive_labels_and_c2_gap():
    # No hardcoding on the ppm_ref.json side either: shift the kt adaptive
    # values/gap and the rendered adaptive-KT bars + C2 exhibit must follow.
    refs = _real_refs()
    ppm = copy.deepcopy(_real_ppm())
    ppm["results"]["kt"]["0"]["adaptive_DL"] = 2601.5
    ppm["results"]["kt"]["1"]["adaptive_DL"] = 1401.25
    ppm["results"]["kt"]["1"]["adaptive_minus_corpus_dl"] = -737.75
    ppm["results"]["kt"]["2"]["adaptive_DL"] = 1701.75

    fig = fig_tool.build_figure(refs, ppm)
    try:
        text_blob = _all_text(fig)
        assert "2601.5" in text_blob
        assert "1401.25" in text_blob
        assert "-737.75" in text_blob
        assert "1701.75" in text_blob
        # the ORIGINAL committed kt numbers must not leak into this render
        real_ppm = _real_ppm()
        orig_gap = real_ppm["results"]["kt"]["1"]["adaptive_minus_corpus_dl"]
        assert f"{orig_gap:g}" not in text_blob
        assert f"{real_ppm['results']['kt']['0']['adaptive_DL']:g}" not in text_blob
    finally:
        matplotlib.pyplot.close(fig)

    # bar order must also track the shift (k=0 now the single highest value
    # among the three adaptive bars, still slotted in by value).
    bars = fig_tool._bars_from_refs(refs, ppm)
    labels = [b["label"].split("\n")[0] for b in bars]
    assert labels.index("adaptive KT k=0") < labels.index("order-0")
    assert labels.index("naive") < labels.index("adaptive KT k=0")


def test_render_is_deterministic_across_two_runs(tmp_path):
    out_a = tmp_path / "a.png"
    out_b = tmp_path / "b.png"
    bytes_a = fig_tool.render(png_out=out_a)
    bytes_b = fig_tool.render(png_out=out_b)
    assert bytes_a == bytes_b
    assert out_a.read_bytes() == out_b.read_bytes()


def test_render_deterministic_via_cli_subprocess(tmp_path):
    # End-to-end: invoke the script as a subprocess twice against copies of
    # the committed JSON files, confirm byte-identical PNGs without touching
    # the committed results/entropy_stack.png.
    json_copy = tmp_path / "entropy_refs.json"
    json_copy.write_text((_REPO / "results" / "entropy_refs.json").read_text())
    ppm_copy = tmp_path / "ppm_ref.json"
    ppm_copy.write_text((_REPO / "results" / "ppm_ref.json").read_text())
    out1 = tmp_path / "out1.png"
    out2 = tmp_path / "out2.png"
    script = (
        "import sys; sys.path.insert(0, %r); "
        "from tools import entropy_stack_fig as f; "
        "from pathlib import Path; "
        "f.render(json_path=Path(%r), ppm_json_path=Path(%r), png_out=Path(%r))"
    )
    subprocess.run(
        [sys.executable, "-c",
         script % (str(_REPO), str(json_copy), str(ppm_copy), str(out1))],
        check=True, cwd=str(_REPO),
    )
    subprocess.run(
        [sys.executable, "-c",
         script % (str(_REPO), str(json_copy), str(ppm_copy), str(out2))],
        check=True, cwd=str(_REPO),
    )
    assert out1.read_bytes() == out2.read_bytes()


def test_committed_png_matches_fresh_render():
    # The committed results/entropy_stack.png must equal what the tool
    # currently produces from the committed JSON files (no drift).
    committed = (_REPO / "results" / "entropy_stack.png").read_bytes()
    fresh = fig_tool.render(png_out=_REPO / "results" / "entropy_stack.png")
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
