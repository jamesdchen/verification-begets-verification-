#!/usr/bin/env python3
"""Tests for tools/campaign_dashboard.py -- the WP-DASH campaign dashboard.

Guards (the determinism discipline template, mirroring test_entropy_stack_fig):
  * determinism: two independent renders of the committed artifacts produce
    byte-identical HTML, in-process AND via a CLI subprocess;
  * committed==fresh: the committed results/campaign_dashboard.html equals a
    fresh render from the committed artifacts (a re-baseline that forgets the
    page fails here);
  * no hardcoding: monkeypatch a loaded JSON value and the rendered text must
    track it -- and the ORIGINAL committed number must NOT leak into the page;
  * self-contained: zero external requests (the only src= URIs are inline
    base64 data URIs), zero <script> tags;
  * doc-parse is fail-loud: shifting a §11.10-§11.12 header (or a refusal
    anchor phrase) raises, so doc drift breaks the test rather than passing a
    stale table;
  * the tool never recomputes: it never imports bench_formalize / mdl_macros /
    recurrence -- it only reads the committed results/ artifacts + COMPRESSION.md.
"""
import copy
import re
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools import campaign_dashboard as dash  # noqa: E402

# A base64 data URI is a giant opaque blob; strip those spans before asserting
# that a committed number did or did not leak into the *text* of the page.
_DATA_URI = re.compile(r"data:image/png;base64,[A-Za-z0-9+/=]+")


def _text_only(html: str) -> str:
    return _DATA_URI.sub("data:image/png;base64,<STRIPPED>", html)


def _ctx():
    return dash.load_context()


# --------------------------------------------------------------------------- #
# Never recomputes -- reads artifacts only.
# --------------------------------------------------------------------------- #
def test_never_recomputes_reads_artifacts_only():
    src = (_REPO / "tools" / "campaign_dashboard.py").read_text()
    # The compute-module names must not appear at all (they are not English words).
    for forbidden in ("bench_formalize", "mdl_macros"):
        assert forbidden not in src, f"tool must not reference {forbidden!r}"
    # No import of any compute/producer module -- the tool reads committed
    # artifacts only. ("recurrence" is also an English word used in prose, so
    # forbid it as an IMPORT specifically, not as a bare substring.)
    import_re = re.compile(
        r"(?:^|\n)\s*(?:import|from)\s+(?:tools\.)?"
        r"(?:bench_formalize|mdl_macros|recurrence|ppm_ref|entropy_refs|"
        r"dl_trajectories_fig|entropy_stack_fig)\b"
    )
    assert import_re.search(src) is None, "tool must not import any producer module"
    # It reads via json/csv/base64 + COMPRESSION.md, never a compute module.
    assert "import json" in src
    assert "import csv" in src
    assert "import base64" in src


# --------------------------------------------------------------------------- #
# Loaders read the committed artifacts verbatim.
# --------------------------------------------------------------------------- #
def test_loaders_read_committed_artifacts():
    import json
    assert dash.load_entropy_refs() == json.loads(
        (_REPO / "results" / "entropy_refs.json").read_text())
    assert dash.load_ppm_ref() == json.loads(
        (_REPO / "results" / "ppm_ref.json").read_text())
    assert dash.load_c2_report() == json.loads(
        (_REPO / "results" / "c2_report.json").read_text())
    assert dash.load_cluster_key() == json.loads(
        (_REPO / "results" / "cluster_key_measure.json").read_text())
    assert dash.load_tower_census() == json.loads(
        (_REPO / "results" / "tower_census.json").read_text())
    rows = dash.load_governed_rows()
    assert {r["arm"] for r in rows} >= {"governed", "ungoverned", "dream"}


# --------------------------------------------------------------------------- #
# Panel data traces to the artifacts.
# --------------------------------------------------------------------------- #
def test_reference_stack_values_from_json():
    refs, ppm = dash.load_entropy_refs(), dash.load_ppm_ref()
    rows = dash.reference_stack(refs, ppm)
    by = {r["name"].split(" (")[0]: r["value"] for r in rows}
    assert by["naive"] == refs["naive_counting_dl"]
    assert by["order-0"] == refs["stack"]["order0_DL"]
    assert by["corpus_dl"] == refs["stack"]["corpus_dl"]
    assert by["LZ77 proxy"] == refs["stack"]["lz77_proxy_DL"]
    for k in ("0", "1", "2"):
        assert by[f"adaptive KT k={k}"] == ppm["results"]["kt"][k]["adaptive_DL"]
    # exactly the best-adaptive bar is highlighted (the C2 exhibit)
    hi = [r for r in rows if r.get("highlight")]
    assert len(hi) == 1
    assert hi[0]["name"] == f"adaptive KT k={ppm['headline']['best_adaptive']['order_k']}"


def test_governance_readout_final_wave_from_csv():
    gov = dash.governance_readout(dash.load_governed_rows())
    assert gov["governed"]["wave"] == 4
    assert gov["governed"]["hindsight"] == 2139.0
    assert gov["governed"]["prequential"] == 2336.0
    assert gov["ungoverned"]["hindsight"] == 2371.0
    assert gov["ungoverned"]["prequential"] == 2459.0
    # governance effect = ungoverned - governed, positive in both currencies
    assert gov["hindsight_gap"] == pytest.approx(232.0)
    assert gov["prequential_gap"] == pytest.approx(123.0)


def test_structured_rows_from_json():
    c2, cluster, tower = dash.load_c2_report(), dash.load_cluster_key(), dash.load_tower_census()
    rows = dash.structured_campaign_rows(c2, cluster, tower)
    src = {r["source"]: r for r in rows}
    assert set(src) == {"cluster_key_measure.json", "c2_report.json", "tower_census.json"}
    # T3-CK headline carries the refined corpus_dl and the congruence delta
    ck = src["cluster_key_measure.json"]["headline"]
    assert dash._fmt(cluster["governed"]["refined"]["corpus_dl"]) in ck
    assert dash._fmt(cluster["congruence_macro"]["realized_marginal_delta"]) in ck
    # C2 headline carries the vocabulary cost from the JSON
    assert dash._fmt(c2["headline"]["vocabulary_cost_under_c2"]) in src["c2_report.json"]["headline"]
    # T1 headline carries the realizable-max and the bar
    t1 = src["tower_census.json"]["headline"]
    tc = tower["tower_census"]["governed"]
    assert dash._fmt(tc["max_witness_macro_macro_pair"]) in t1
    assert dash._fmt(tc["level2_witness_bar"]) in t1


def test_measured_refusals_read_where_available():
    c2, tower = dash.load_c2_report(), dash.load_tower_census()
    md = dash.load_compression_md()
    r = {x["title"].split(" —")[0]: x for x in dash.measured_refusals(md, c2, tower)}
    assert r["T3 window rule"]["figure"] == "+29 DL"          # 2168 - 2139, from §11.10
    assert "2748" in r["Pilot canonicalization rung"]["figure"]  # from §11.11
    # C2 counter-indication reads the exact JSON number (rounds to +254.9)
    assert dash._fmt(c2["headline"]["vocabulary_cost_under_c2"]) in r["C2"]["figure"]
    # T1 realizable-max-1 deferral from the census
    tc = tower["tower_census"]["governed"]
    assert dash._fmt(tc["max_witness_macro_macro_pair"]) in r["T1"]["figure"]
    assert dash._fmt(tc["level2_witness_bar"]) in r["T1"]["figure"]


# --------------------------------------------------------------------------- #
# §11 execution-record parse.
# --------------------------------------------------------------------------- #
def test_execution_record_covers_the_three_sections():
    recs = dash.parse_execution_record(dash.load_compression_md())
    sections = {r["section"] for r in recs}
    assert sections == {"§11.10", "§11.11", "§11.12"}
    pkgs = " | ".join(r["package"] for r in recs)
    for anchor in ("(P1)", "(T1)", "(T3)", "(T4)", "(T6a)", "(T6b)", "Source promotion"):
        assert anchor in pkgs
    # §11.1 headline number is the origin-blind counting-prequential figure
    p1 = next(r for r in recs if "(P1)" in r["package"])
    assert p1["figure"] == "2336"
    assert "LANDED" in p1["verdict"]


def test_doc_drift_on_header_raises():
    md = dash.load_compression_md()
    broken = md.replace(dash.SECTION_11_11, "### 11.11 RENAMED SECTION")
    with pytest.raises(ValueError, match="doc drift"):
        dash.parse_execution_record(broken)


def test_doc_drift_on_refusal_anchor_raises():
    # Mutate a CONTIGUOUS anchor word (the markdown source hard-wraps phrases
    # mid-sentence, so a multi-word replace can silently miss).
    md = dash.load_compression_md()
    with pytest.raises(ValueError, match="doc drift"):
        dash.parse_t3_window_refusal(md.replace("REGRESSED", "moved"))
    with pytest.raises(ValueError, match="doc drift"):
        dash.parse_pilot_rung_refusal(md.replace("counterfactual", "hypothetical"))


# --------------------------------------------------------------------------- #
# Self-contained page: no external requests, no JS.
# --------------------------------------------------------------------------- #
def test_page_is_self_contained_no_external_requests():
    html = dash.build_html(_ctx())
    assert "<script" not in html.lower()
    # every image src is an inline data URI -- no http(s), no relative asset refs
    for m in re.finditer(r"src=['\"]([^'\"]+)['\"]", html):
        assert m.group(1).startswith("data:image/png;base64,")
    assert "http://" not in html
    assert "https://" not in html
    # both committed PNGs are embedded
    assert html.count("data:image/png;base64,") == 2


# --------------------------------------------------------------------------- #
# No hardcoding: monkeypatched inputs track; committed numbers don't leak.
# --------------------------------------------------------------------------- #
def test_shifted_json_values_track_and_originals_do_not_leak():
    ctx = _ctx()
    real_naive = ctx["refs"]["naive_counting_dl"]            # panel 1 only
    real_kt0 = ctx["ppm"]["results"]["kt"]["0"]["adaptive_DL"]  # panel 1 only
    real_c2cost = ctx["c2"]["headline"]["vocabulary_cost_under_c2"]  # panels 4 & 5

    mutated = copy.deepcopy(ctx)
    mutated["refs"]["naive_counting_dl"] = 31337.0
    mutated["ppm"]["results"]["kt"]["0"]["adaptive_DL"] = 55555.25
    mutated["c2"]["headline"]["vocabulary_cost_under_c2"] = 98765.5

    text = _text_only(dash.build_html(mutated))
    assert "31337" in text
    assert "55555.25" in text
    assert "98765.5" in text
    # the committed originals must be gone from the rendered text
    assert dash._fmt(real_naive) not in text
    assert dash._fmt(real_kt0) not in text
    assert dash._fmt(real_c2cost) not in text


def test_shifted_csv_values_track_governance_readout():
    ctx = _ctx()
    real_hind = None
    mutated = copy.deepcopy(ctx)
    for r in mutated["csv_rows"]:
        if r["arm"] == "governed" and r["wave"] == "4":
            real_hind = r["reported_exogenous_dl"]
            r["reported_exogenous_dl"] = "40404.0"
    assert real_hind is not None
    text = _text_only(dash.build_html(mutated))
    assert "40404" in text


# --------------------------------------------------------------------------- #
# Determinism: two-run byte identity + committed == fresh.
# --------------------------------------------------------------------------- #
def test_render_is_deterministic_across_two_runs(tmp_path):
    a = tmp_path / "a.html"
    b = tmp_path / "b.html"
    assert dash.render(html_out=a) == dash.render(html_out=b)
    assert a.read_bytes() == b.read_bytes()


def test_render_deterministic_via_cli_subprocess(tmp_path):
    out1 = tmp_path / "out1.html"
    out2 = tmp_path / "out2.html"
    script = (
        "import sys; sys.path.insert(0, %r); "
        "from tools import campaign_dashboard as d; "
        "from pathlib import Path; d.render(html_out=Path(%r))"
    )
    for out in (out1, out2):
        subprocess.run(
            [sys.executable, "-c", script % (str(_REPO), str(out))],
            check=True, cwd=str(_REPO),
        )
    assert out1.read_bytes() == out2.read_bytes()


def test_committed_html_matches_fresh_render():
    committed = (_REPO / "results" / "campaign_dashboard.html").read_bytes()
    fresh = dash.render(html_out=_REPO / "results" / "campaign_dashboard.html")
    assert committed == fresh


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
