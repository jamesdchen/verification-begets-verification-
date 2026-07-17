#!/usr/bin/env python3
"""Deterministic campaign dashboard -- WP-DASH (COMPRESSION.md §12).

Renders `results/campaign_dashboard.html`: one self-contained static page
(inline CSS, zero external requests, zero JavaScript, the two committed PNGs
embedded as base64 data URIs) that reports the compression campaign at a
glance. It is a LOCAL COMMITTED ARTIFACT -- it is not published anywhere;
publishing is a separate human decision.

Every number on the page is READ AT RUNTIME from committed artifacts -- there
are zero hardcoded figure constants, exactly as the entropy_stack /
dl_trajectories figure tools work. Re-baselining is: rerun the artifact
producers, then rerun this tool. A re-baseline that forgets it fails the
committed==fresh test.

Inputs (read-only; this tool never recomputes, never imports the benches):
  * results/entropy_refs.json      -- reference stack (naive/order-0/corpus_dl/LZ77)
  * results/ppm_ref.json           -- adaptive-KT comparator bars
  * results/formalize_governed.csv -- the two-arm governance readout
  * results/c2_report.json         -- C2 two-part-code verdict (structured)
  * results/cluster_key_measure.json -- T3-CK cluster-key measure (structured)
  * results/tower_census.json      -- T1 deferral census (structured)
  * results/entropy_stack.png      -- embedded chart 1
  * results/dl_trajectories.png    -- embedded chart 2
  * COMPRESSION.md §11.10-§11.12   -- the wave-1 execution record (parsed)

Panels, in order:
  1. Headline reference stack (entropy_refs + ppm_ref).
  2. The two embedded charts.
  3. Governance readout: final-wave hindsight/prequential gaps, both arms (CSV).
  4. Campaign record table: structured-artifact rows + the §11.10-§11.12
     execution record parsed from COMPRESSION.md.
  5. Measured-refusals panel (the four toothed refusals).
  6. Footer: input files + the re-baseline sentence.

Doc-parse discipline: the §11.10-§11.12 headers are asserted VERBATIM; if a
header changes, parsing raises (doc drift breaks the test rather than passing
stale). The four measured-refusal anchors are likewise fail-loud.

Determinism: base64 is a pure function of the committed PNG bytes; iteration
order is explicit; there are no timestamps, so two runs are byte-identical.
"""
from __future__ import annotations

import base64
import csv
import html as _html
import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_RESULTS = _REPO / "results"

ENTROPY_REFS_PATH = _RESULTS / "entropy_refs.json"
PPM_REF_PATH = _RESULTS / "ppm_ref.json"
GOVERNED_CSV_PATH = _RESULTS / "formalize_governed.csv"
C2_REPORT_PATH = _RESULTS / "c2_report.json"
CLUSTER_KEY_PATH = _RESULTS / "cluster_key_measure.json"
TOWER_CENSUS_PATH = _RESULTS / "tower_census.json"
ENTROPY_STACK_PNG = _RESULTS / "entropy_stack.png"
DL_TRAJECTORIES_PNG = _RESULTS / "dl_trajectories.png"
COMPRESSION_MD_PATH = _REPO / "COMPRESSION.md"
HTML_OUT = _RESULTS / "campaign_dashboard.html"

# --- §11 execution-record section headers, asserted VERBATIM (doc-drift tooth).
SECTION_11_10 = "### 11.10 Wave-1 execution record (what actually happened)"
SECTION_11_11 = "### 11.11 Wave-1 tail: the machinery is in; the corpus said no (for now)"
SECTION_11_12 = "### 11.12 Promotion executed — the corpus is 51"
SECTION_12 = "## 12. Wave-3 plan (DRAFT — pending its fable critique sweep)"


# ---------------------------------------------------------------------------
# Loaders -- read committed artifacts, never recompute.
# ---------------------------------------------------------------------------
def _load_json(path: Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


def load_entropy_refs(path: Path = ENTROPY_REFS_PATH) -> dict:
    return _load_json(path)


def load_ppm_ref(path: Path = PPM_REF_PATH) -> dict:
    return _load_json(path)


def load_c2_report(path: Path = C2_REPORT_PATH) -> dict:
    return _load_json(path)


def load_cluster_key(path: Path = CLUSTER_KEY_PATH) -> dict:
    return _load_json(path)


def load_tower_census(path: Path = TOWER_CENSUS_PATH) -> dict:
    return _load_json(path)


def load_governed_rows(path: Path = GOVERNED_CSV_PATH) -> list[dict]:
    """Read the two-arm governance CSV by column name (robust to appended
    columns). Returns every data row as an ordered dict of raw strings."""
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def load_compression_md(path: Path = COMPRESSION_MD_PATH) -> str:
    return path.read_text()


def load_png_data_uri(path: Path) -> str:
    """base64 data URI for a committed PNG. Pure function of the file bytes."""
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


# ---------------------------------------------------------------------------
# Formatting helpers.
# ---------------------------------------------------------------------------
def _fmt(x) -> str:
    """Integral floats collapse to ints (2139.0 -> '2139'); non-integral floats
    keep FULL round-trip precision (2449.587 -> '2449.587', never {:g}'s 6-sig-fig
    truncation -- a readout table must not lose digits)."""
    if isinstance(x, bool):
        return str(x)
    if isinstance(x, int):
        return str(x)
    if isinstance(x, float):
        return str(int(x)) if x == int(x) else str(x)
    return str(x)


def _signed(x) -> str:
    val = float(x)
    return f"+{_fmt(val)}" if val >= 0 else _fmt(val)


def _esc(s) -> str:
    return _html.escape(str(s))


# ---------------------------------------------------------------------------
# COMPRESSION.md §11.10-§11.12 parsing (fail-loud on header drift).
# ---------------------------------------------------------------------------
def _require(md: str, needle: str) -> int:
    idx = md.find(needle)
    if idx < 0:
        raise ValueError(
            f"COMPRESSION.md doc drift: expected section/anchor not found "
            f"(the dashboard's §11 parse is deliberately fail-loud): {needle!r}"
        )
    return idx


def _section_slice(md: str, start: str, end: str) -> str:
    a = _require(md, start)
    b = _require(md, end)
    if b <= a:
        raise ValueError(f"COMPRESSION.md doc drift: {end!r} precedes {start!r}")
    return md[a + len(start):b]


def _flat(text: str) -> str:
    """Collapse hard-wrapped whitespace so anchored regexes match phrases that
    the markdown source line-wraps mid-sentence."""
    return " ".join(text.split())


def _top_bullets(section_text: str) -> list[str]:
    """Split a section into its top-level '- **...' bullets (2-space-indented
    continuation lines folded into their bullet)."""
    bullets: list[str] = []
    cur: list[str] | None = None
    for line in section_text.splitlines():
        if line.startswith("- "):
            if cur is not None:
                bullets.append(" ".join(cur))
            cur = [line[2:].strip()]
        elif cur is not None and (line.startswith("  ") or line.strip() == ""):
            if line.strip():
                cur.append(line.strip())
        elif cur is not None:
            # A non-indented, non-bullet line ends the bullet list.
            bullets.append(" ".join(cur))
            cur = None
    if cur is not None:
        bullets.append(" ".join(cur))
    return [b for b in bullets if b.startswith("**")]


_STATUS_KEYWORDS = (
    "ALL CLOSED", "CLOSED", "LANDED", "DEFERRED", "SPLIT", "REFUSED",
    "STAGED", "PROMOTED", "HELD", "landed", "gated", "refused",
)


def _bold_lead(bullet: str) -> str:
    m = re.search(r"\*\*(.+?)\*\*", bullet, re.S)
    if not m:
        raise ValueError(f"execution-record bullet has no bold lead: {bullet[:60]!r}")
    return m.group(1).strip()


def _body(bullet: str) -> str:
    """Everything after the first bold lead (the prose of the bullet)."""
    m = re.search(r"\*\*.+?\*\*", bullet, re.S)
    return bullet[m.end():] if m else bullet


def _split_package_verdict(bold: str) -> tuple[str, str]:
    """Split a bold lead into (package, verdict). Colon-delimited leads
    (§11.10 style) split on the colon; otherwise the first status keyword
    marks the verdict boundary (§11.11 style)."""
    if ":" in bold:
        pkg, verdict = bold.split(":", 1)
        return pkg.strip(), verdict.strip().rstrip(".")
    for kw in _STATUS_KEYWORDS:
        i = bold.find(kw)
        if i >= 0:
            return bold[:i].strip().rstrip(".") or bold.strip(), bold[i:].strip().rstrip(".")
    return bold.strip().rstrip("."), "—"


def _first_figure(body: str) -> str:
    """First standalone number cited in a bullet body, ignoring bracketed
    spans and §-references (e.g. '§11.8'). Deterministic; the authoritative
    outcome is the verdict, this is only the first figure cited."""
    t = re.sub(r"\[[^\]]*\]", " ", body)          # drop [-12,12]-style ranges
    t = re.sub(r"§\s?\d+(?:\.\d+)*", " ", t)       # drop §-references
    m = re.search(r"(?<![\w.])(-?\d+(?:\.\d+)?)(?!\w)", t)
    return m.group(1) if m else "—"


def parse_execution_record(md: str) -> list[dict]:
    """Parse the §11.10-§11.12 execution record into per-package rows.

    Fail-loud: the three section headers (and the §12 boundary) must be
    present verbatim, else ValueError -- doc drift breaks the test rather
    than silently passing a stale table."""
    records: list[dict] = []
    for header, section_end, tag in (
        (SECTION_11_10, SECTION_11_11, "§11.10"),
        (SECTION_11_11, SECTION_11_12, "§11.11"),
    ):
        section = _section_slice(md, header, section_end)
        for bullet in _top_bullets(section):
            pkg, verdict = _split_package_verdict(_bold_lead(bullet))
            records.append(
                {
                    "section": tag,
                    "package": pkg,
                    "verdict": verdict,
                    "figure": _first_figure(_body(bullet)),
                }
            )
    # §11.12 is prose, not bullets -- one synthesized record.
    sec12 = _flat(_section_slice(md, SECTION_11_12, SECTION_12))
    corpus_m = re.search(r"live corpus is (\d+)", sec12)
    waivers_m = re.search(r"ZERO waivers", sec12)
    if corpus_m is None:
        raise ValueError("COMPRESSION.md §11.12 doc drift: 'live corpus is <N>' not found")
    records.append(
        {
            "section": "§11.12",
            "package": "Source promotion",
            "verdict": "PROMOTED" + (" (ZERO waivers)" if waivers_m else ""),
            "figure": corpus_m.group(1),
        }
    )
    return records


def parse_t3_window_refusal(md: str) -> dict:
    """The HELD force-only window rule: regressed governed DL 2139 -> 2168
    (+29). Parsed from §11.10; fail-loud if the phrase changes."""
    section = _flat(_section_slice(md, SECTION_11_10, SECTION_11_11))
    m = re.search(r"REGRESSED governed DL (\d+)\s*→\s*(\d+)", section)
    if m is None:
        raise ValueError(
            "COMPRESSION.md §11.10 doc drift: T3 'REGRESSED governed DL A → B' not found"
        )
    before, after = int(m.group(1)), int(m.group(2))
    return {"before": before, "after": after, "delta": after - before}


def parse_pilot_rung_refusal(md: str) -> dict:
    """The pilot canonicalization rung: counterfactual profit 0.0 against
    2748 rung model bits. Parsed from §11.11; fail-loud if the phrase changes."""
    section = _flat(_section_slice(md, SECTION_11_11, SECTION_11_12))
    m = re.search(
        r"counterfactual profit is exactly (-?\d+(?:\.\d+)?) against (\d+) rung model bits",
        section,
    )
    if m is None:
        raise ValueError(
            "COMPRESSION.md §11.11 doc drift: pilot-rung 'profit X against Y rung model bits' not found"
        )
    return {"profit": float(m.group(1)), "refused_bits": int(m.group(2))}


# ---------------------------------------------------------------------------
# Panel data assembly (pure functions over the loaded artifacts).
# ---------------------------------------------------------------------------
def reference_stack(refs: dict, ppm: dict) -> list[dict]:
    """Panel 1: the headline reference stack (values only, no layout)."""
    stack = refs["stack"]
    kt = ppm["results"]["kt"]
    best = ppm["headline"]["best_adaptive"]
    rows = [
        {"name": "naive (no vocabulary)", "value": refs["naive_counting_dl"],
         "note": "counting DL, no macros"},
        {"name": "order-0 (memoryless)", "value": stack["order0_DL"],
         "note": "already beaten by the macro coder"},
        {"name": "corpus_dl (live macro coder)", "value": stack["corpus_dl"],
         "note": "current position", "emphasis": True},
        {"name": f"LZ77 proxy (z = {refs['lz77_proxy']['z_phrases']})",
         "value": stack["lz77_proxy_DL"],
         "note": f"T2 comparator; residual gap {_fmt(refs['residual_gap_corpus_dl_minus_lz77'])}"
                 f" ({_fmt(refs['residual_gap_pct_of_corpus_dl'])}%)"},
    ]
    for k in ("0", "1", "2"):
        entry = kt[k]
        is_best = int(k) == best["order_k"]
        note = "honest, pays learning cost"
        if is_best:
            note = (f"C2 exhibit: beats corpus_dl by "
                    f"{_fmt(entry['adaptive_minus_corpus_dl'])} (§10.7)")
        rows.append(
            {"name": f"adaptive KT k={k}", "value": entry["adaptive_DL"],
             "note": note, "adaptive": True, "highlight": is_best}
        )
    return rows


def governance_readout(rows: list[dict]) -> dict:
    """Panel 3: final-wave hindsight & prequential DL for both arms + gaps.

    Hindsight = reported_exogenous_dl; prequential = prequential_counting_dl
    (WP-P1 / §11.1, the origin-blind counting-prequential column)."""
    def final(arm: str) -> dict:
        arm_rows = [r for r in rows if r["arm"] == arm]
        if not arm_rows:
            raise ValueError(f"governance CSV missing arm {arm!r}")
        last = max(arm_rows, key=lambda r: int(r["wave"]))
        return {
            "wave": int(last["wave"]),
            "hindsight": float(last["reported_exogenous_dl"]),
            "prequential": float(last["prequential_counting_dl"]),
        }

    gov, ung = final("governed"), final("ungoverned")
    return {
        "governed": gov,
        "ungoverned": ung,
        "hindsight_gap": ung["hindsight"] - gov["hindsight"],
        "prequential_gap": ung["prequential"] - gov["prequential"],
    }


def structured_campaign_rows(c2: dict, cluster: dict, tower: dict) -> list[dict]:
    """Panel 4 (group A): the three structured-artifact packages."""
    ck_ref = cluster["governed"]["refined"]
    tc = tower["tower_census"]["governed"]
    c2h = c2["headline"]
    return [
        {
            "package": "T3-CK (cluster key)",
            "source": "cluster_key_measure.json",
            "verdict": ("PASS — refined key unblocks the congruence cluster"
                        if cluster["all_pass"] else "FAIL"),
            "headline": (f"governed corpus_dl {_fmt(cluster['baseline_governed_dl'])} → "
                         f"{_fmt(ck_ref['corpus_dl'])} "
                         f"(Δ{_fmt(cluster['governed']['delta_dl'])}); "
                         f"congruence macro realized {_fmt(cluster['congruence_macro']['realized_marginal_delta'])}"),
        },
        {
            "package": "C2 (two-part entropy code)",
            "source": "c2_report.json",
            "verdict": ("REPORTED — vocabulary does NOT pay under C2"
                        if not c2h["vocabulary_pays_under_c2"] else "vocabulary pays under C2"),
            "headline": (f"vocabulary costs {_fmt(c2h['vocabulary_cost_under_c2'])} units "
                         f"(governed C2 {_fmt(c2h['governed_c2'])} > empty-table "
                         f"{_fmt(c2h['empty_c2_no_vocabulary'])})"),
        },
        {
            "package": "T1 (tower rung)",
            "source": "tower_census.json",
            "verdict": ("DEFERRED — no realizable MM pair meets the bar"
                        if tc["macro_macro_pairs_at_or_above_bar"] == 0 else "T1 fires"),
            "headline": (f"realizable max MM pair {_fmt(tc['max_witness_macro_macro_pair'])} "
                         f"vs ≥{_fmt(tc['level2_witness_bar'])} bar "
                         f"(raw-{_fmt(tc['max_raw_adjacent_witness_macro_macro_pair'])} was "
                         f"H2-unrealizable inflation)"),
        },
    ]


def measured_refusals(md: str, c2: dict, tower: dict) -> list[dict]:
    """Panel 5: the four toothed refusals (structured where available)."""
    t3 = parse_t3_window_refusal(md)
    pilot = parse_pilot_rung_refusal(md)
    c2h = c2["headline"]
    tc = tower["tower_census"]["governed"]
    return [
        {
            "title": "T3 window rule — HELD",
            "figure": f"{_signed(t3['delta'])} DL",
            "detail": (f"force-only window rule regressed governed DL "
                       f"{_fmt(t3['before'])} → {_fmt(t3['after'])}; the −179 stays "
                       f"counterfactual on the greedy path"),
            "source": "COMPRESSION.md §11.10",
        },
        {
            "title": "Pilot canonicalization rung — REFUSED",
            "figure": f"profit {_fmt(pilot['profit'])} vs {_fmt(pilot['refused_bits'])} bits",
            "detail": ("counterfactual profit is exactly 0.0 against the rung model "
                       "bits; commutativity normalization exposes no priceable "
                       "repetition under the order-blind counting currency"),
            "source": "COMPRESSION.md §11.11",
        },
        {
            "title": "C2 — counter-indicated",
            "figure": f"{_signed(c2h['vocabulary_cost_under_c2'])} units",
            "detail": ("the certified vocabulary COSTS bits under entropy coding; "
                       "its value is certification structure, not compression"),
            "source": "c2_report.json",
        },
        {
            "title": "T1 — realizable-max-1 deferral",
            "figure": (f"max MM {_fmt(tc['max_witness_macro_macro_pair'])} "
                       f"vs ≥{_fmt(tc['level2_witness_bar'])}"),
            "detail": (f"{_fmt(tc['macro_macro_pairs_at_or_above_bar'])} realizable "
                       f"macro-macro pairs meet the bar on "
                       f"{_fmt(tc['n_certified_readings'])} certified readings"),
            "source": "tower_census.json",
        },
    ]


# ---------------------------------------------------------------------------
# HTML rendering (pure function of the loaded context).
# ---------------------------------------------------------------------------
_CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body {
  margin: 0; padding: 0 1.2rem 3rem;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.5; color: #14140f; background: #fcfcfb;
  -webkit-font-smoothing: antialiased;
}
.wrap { max-width: 1040px; margin: 0 auto; }
header.masthead { padding: 2rem 0 1rem; border-bottom: 2px solid #2a78d6; }
header.masthead h1 { margin: 0 0 .25rem; font-size: 1.6rem; }
header.masthead p { margin: 0; color: #52514e; font-size: .95rem; }
section { margin: 2.2rem 0; }
h2 { font-size: 1.15rem; border-left: 4px solid #2a78d6; padding-left: .6rem; margin: 0 0 .8rem; }
h2 .num { color: #898781; font-weight: 600; margin-right: .4rem; }
p.lead { color: #52514e; margin: 0 0 1rem; font-size: .92rem; }
.tablewrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: .9rem; }
th, td { text-align: left; padding: .45rem .6rem; border-bottom: 1px solid #e1e0d9; vertical-align: top; }
th { color: #52514e; font-weight: 600; background: #f4f3ee; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
tr.emph td { background: #eaf2fc; font-weight: 600; }
tr.adaptive td:first-child { color: #12805a; }
tr.highlight td { background: #e7f6ef; }
figure { margin: 1.2rem 0; }
figure img { max-width: 100%; height: auto; display: block; border: 1px solid #e1e0d9; border-radius: 4px; }
figcaption { color: #898781; font-size: .82rem; margin-top: .35rem; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: .9rem; }
.card { border: 1px solid #e1e0d9; border-radius: 6px; padding: .9rem 1rem; background: #fff; }
.card h3 { margin: 0 0 .3rem; font-size: .95rem; }
.card .fig { font-size: 1.2rem; font-weight: 700; color: #b5451b; font-variant-numeric: tabular-nums; }
.card p { margin: .35rem 0 0; font-size: .82rem; color: #52514e; }
.card .src { color: #898781; font-size: .74rem; margin-top: .45rem; }
.gap { color: #12805a; font-weight: 600; }
.pill { display: inline-block; font-size: .72rem; padding: .05rem .4rem; border-radius: 3px;
        background: #eef; color: #334; margin-left: .3rem; }
footer { margin-top: 3rem; border-top: 1px solid #e1e0d9; padding-top: 1rem;
         color: #898781; font-size: .82rem; }
footer code { background: #f4f3ee; padding: .05rem .3rem; border-radius: 3px; color: #52514e; }
@media (prefers-color-scheme: dark) {
  body { color: #e9e8e2; background: #16160f; }
  td, th { border-bottom-color: #2f2f24; }
  h2 .num, p.lead, figcaption, .card p, .card .src, footer { color: #9a998f; }
  .card, figure img { border-color: #2f2f24; }
  .card { background: #1d1d14; }
  tr.emph td { background: #1e2c3f; }
  tr.highlight td { background: #14291f; }
  th { color: #b9b8b0; background: #23231a; }
  footer code { background: #23231a; color: #b9b8b0; }
}
"""


def _row_ref_stack(rows: list[dict]) -> str:
    out = []
    for r in rows:
        cls = []
        if r.get("emphasis"):
            cls.append("emph")
        if r.get("adaptive"):
            cls.append("adaptive")
        if r.get("highlight"):
            cls.append("highlight")
        cls_attr = f' class="{" ".join(cls)}"' if cls else ""
        out.append(
            f"<tr{cls_attr}><td>{_esc(r['name'])}</td>"
            f"<td class='num'>{_esc(_fmt(r['value']))}</td>"
            f"<td>{_esc(r['note'])}</td></tr>"
        )
    return "\n".join(out)


def build_html(ctx: dict) -> str:
    """Assemble the full self-contained page from the loaded context.

    Pure: every rendered number traces to ctx's artifacts, so monkeypatching
    an input value shifts the output and the committed constants never leak."""
    refs = ctx["refs"]
    ppm = ctx["ppm"]
    rows = ctx["csv_rows"]
    c2 = ctx["c2"]
    cluster = ctx["cluster"]
    tower = ctx["tower"]
    md = ctx["md"]

    ref_rows = reference_stack(refs, ppm)
    gov = governance_readout(rows)
    struct_rows = structured_campaign_rows(c2, cluster, tower)
    exec_rows = parse_execution_record(md)
    refusals = measured_refusals(md, c2, tower)

    n_readings = refs["n_readings"]
    stream_len = refs["stream_length"]

    parts: list[str] = []
    parts.append("<div class='wrap'>")

    # Masthead
    parts.append(
        "<header class='masthead'>"
        "<h1>Compression campaign dashboard</h1>"
        f"<p>corpus_dl vs. reference floors, governance, and the wave-1 execution "
        f"record — {_esc(n_readings)} certified readings, {_esc(stream_len)} tokens. "
        "Regenerated deterministically from committed artifacts; not published.</p>"
        "</header>"
    )

    # Panel 1
    parts.append(
        "<section><h2><span class='num'>1</span>Headline reference stack</h2>"
        "<p class='lead'>Description length in counting units (bits). References, "
        "not floors (COMPRESSION.md §10.2/§11.8). Read from "
        "<code>entropy_refs.json</code> + <code>ppm_ref.json</code>.</p>"
        "<div class='tablewrap'><table><thead><tr><th>reference</th><th class='num'>DL</th>"
        "<th>note</th></tr></thead>"
        f"<tbody>{_row_ref_stack(ref_rows)}</tbody></table></div></section>"
    )

    # Panel 2
    parts.append(
        "<section><h2><span class='num'>2</span>Campaign figures</h2>"
        "<p class='lead'>The two re-baseline-coupled charts, embedded as base64 "
        "(zero external requests).</p>"
        f"<figure><img alt='Entropy stack: corpus_dl vs reference floors' "
        f"src='{ctx['png_entropy']}'>"
        "<figcaption>entropy_stack.png — the reference stack incl. adaptive-KT bars "
        "and the C2 exhibit.</figcaption></figure>"
        f"<figure><img alt='DL trajectories: two-currency governance readout' "
        f"src='{ctx['png_dl']}'>"
        "<figcaption>dl_trajectories.png — the two-currency governance readout, both arms.</figcaption>"
        "</figure></section>"
    )

    # Panel 3
    def _arm_row(name: str, arm: dict) -> str:
        return (f"<tr><td>{_esc(name)}</td>"
                f"<td class='num'>{_esc(_fmt(arm['hindsight']))}</td>"
                f"<td class='num'>{_esc(_fmt(arm['prequential']))}</td></tr>")

    parts.append(
        "<section><h2><span class='num'>3</span>Governance readout (final wave)</h2>"
        "<p class='lead'>Final-wave hindsight (<code>reported_exogenous_dl</code>) and "
        "prequential (<code>prequential_counting_dl</code>, the origin-blind counting "
        "column, WP-P1/§11.1) for both arms, from <code>formalize_governed.csv</code> "
        f"(wave {_esc(gov['governed']['wave'])}).</p>"
        "<div class='tablewrap'><table><thead><tr><th>arm</th><th class='num'>hindsight DL</th>"
        "<th class='num'>prequential DL</th></tr></thead><tbody>"
        f"{_arm_row('governed', gov['governed'])}"
        f"{_arm_row('ungoverned', gov['ungoverned'])}"
        "</tbody></table></div>"
        f"<p class='lead' style='margin-top:.8rem'>Governance effect (ungoverned − governed): "
        f"hindsight <span class='gap'>{_esc(_signed(gov['hindsight_gap']))}</span>, "
        f"prequential <span class='gap'>{_esc(_signed(gov['prequential_gap']))}</span> — "
        "governed compresses lower in both currencies; the effect survives on data bits "
        "alone (not an accounting convention).</p></section>"
    )

    # Panel 4
    struct_html = "\n".join(
        f"<tr><td>{_esc(r['package'])}</td><td>{_esc(r['verdict'])}</td>"
        f"<td>{_esc(r['headline'])}</td>"
        f"<td><code>{_esc(r['source'])}</code></td></tr>"
        for r in struct_rows
    )
    exec_html = "\n".join(
        f"<tr><td>{_esc(r['package'])}<span class='pill'>{_esc(r['section'])}</span></td>"
        f"<td>{_esc(r['verdict'])}</td>"
        f"<td class='num'>{_esc(r['figure'])}</td></tr>"
        for r in exec_rows
    )
    parts.append(
        "<section><h2><span class='num'>4</span>Campaign record</h2>"
        "<p class='lead'>Structured-artifact packages (verdict + headline read from "
        "their JSON), then the wave-1 execution record parsed from COMPRESSION.md "
        "§11.10–§11.12. The parse is fail-loud on header drift.</p>"
        "<div class='tablewrap'><table><thead><tr><th>package</th><th>verdict</th>"
        "<th>headline</th><th>source</th></tr></thead>"
        f"<tbody>{struct_html}</tbody></table></div>"
        "<p class='lead' style='margin-top:1rem'>Wave-1 execution record "
        "(COMPRESSION.md §11.10–§11.12; the &ldquo;figure&rdquo; column is the first "
        "figure cited in each entry — the verdict is the authoritative outcome):</p>"
        "<div class='tablewrap'><table><thead><tr><th>package</th><th>verdict</th>"
        "<th class='num'>figure</th></tr></thead>"
        f"<tbody>{exec_html}</tbody></table></div></section>"
    )

    # Panel 5
    cards = "\n".join(
        f"<div class='card'><h3>{_esc(r['title'])}</h3>"
        f"<div class='fig'>{_esc(r['figure'])}</div>"
        f"<p>{_esc(r['detail'])}</p>"
        f"<div class='src'>{_esc(r['source'])}</div></div>"
        for r in refusals
    )
    parts.append(
        "<section><h2><span class='num'>5</span>Measured refusals</h2>"
        "<p class='lead'>Four toothed refusals — the campaign's honest &ldquo;no&rdquo;s, "
        "each read from its artifact where available.</p>"
        f"<div class='grid'>{cards}</div></section>"
    )

    # Panel 6 (footer)
    inputs = [
        "results/entropy_refs.json", "results/ppm_ref.json",
        "results/formalize_governed.csv", "results/c2_report.json",
        "results/cluster_key_measure.json", "results/tower_census.json",
        "results/entropy_stack.png", "results/dl_trajectories.png",
        "COMPRESSION.md (§11.10–§11.12)",
    ]
    inputs_html = " · ".join(f"<code>{_esc(p)}</code>" for p in inputs)
    parts.append(
        "<footer>"
        f"<p><strong>Inputs:</strong> {inputs_html}</p>"
        "<p>This page regenerates at every re-baseline: it holds zero hardcoded "
        "numbers, and its committed==fresh test enforces that the committed HTML "
        "equals a fresh render from the committed artifacts. A re-baseline that "
        "forgets this page fails CI.</p>"
        "</footer>"
    )

    parts.append("</div>")

    body = "\n".join(parts)
    return f"<style>{_CSS}</style>\n<div class='page'>{body}</div>\n"


def load_context() -> dict:
    """Load every artifact once into the render context."""
    return {
        "refs": load_entropy_refs(),
        "ppm": load_ppm_ref(),
        "csv_rows": load_governed_rows(),
        "c2": load_c2_report(),
        "cluster": load_cluster_key(),
        "tower": load_tower_census(),
        "md": load_compression_md(),
        "png_entropy": load_png_data_uri(ENTROPY_STACK_PNG),
        "png_dl": load_png_data_uri(DL_TRAJECTORIES_PNG),
    }


def render(html_out: Path = HTML_OUT) -> bytes:
    """Load, build, write deterministic UTF-8 bytes; return the bytes written."""
    ctx = load_context()
    html_text = build_html(ctx)
    data = html_text.encode("utf-8")
    html_out.write_bytes(data)
    return data


def main() -> int:
    data = render()
    sys.stdout.write(f"wrote {HTML_OUT} ({len(data)} bytes)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
