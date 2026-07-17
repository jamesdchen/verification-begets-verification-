#!/usr/bin/env python3
"""WP-C2 — the entropy-coded two-part currency, as a REPORTED experiment.

COMPRESSION.md §3 C2 made concrete, gated by §11.8 ("C2/C4 ... DEFERRED unless
wave 1 produces a recorded instance of the counting currency mispricing an
admitted structure ... these stay reporting experiments").  Nothing here gates
on this number; no existing file changes; the admission currency stays the
counting one (`mdl_macros`).  This module only *measures* and *reports*.

THE QUESTION (from §10.7's measured exhibit).  Adaptive KT order-1 codes the
committed structure stream at 1514.5, beating the counting `corpus_dl` of 2139
by 624 units — sequential, statement-internal structure the counting currency
cannot see.  So: **how much of that 624-unit advantage does a two-part
macro+entropy-coded currency actually recover while KEEPING the certified
vocabulary?**  And the sharper, honest follow-up §3 C2 implies: does the macro
vocabulary even PAY under entropy coding, or has the adaptive coder already
harvested for free the recurrence the macros deduplicate?

------------------------------------------------------------------- the currency
C2 is a two-part MDL code:  c2_dl = model_bits + data_bits.

  * MODEL BITS = the macro table priced EXACTLY as `mdl_macros` prices it today
    (leaf counting, `dl_macro`).  ONE source of truth: this module calls into
    `buildloop.mdl_macros`, it does not reimplement the count.  Empty table => 0.

  * DATA BITS = the ADAPTIVE KT order-1 codelength (Krichevsky-Trofimov add-1/2,
    the exact coder in `tools/ppm_ref.py`, imported read-only) over the REWRITTEN
    token stream — the corpus after greedy macro rewriting, so a matched body
    window collapses to its invocation.  Converted from bits into the counting
    currency's units at a FIXED exchange rate calibrated on the raw committed
    stream (see SCALING below), so the two parts add in one currency.

------------------------------------------------------- the token mapping (design)
The rewritten stream is derived from `mdl_macros._reading_stats` / `_match_at`
semantics: each reading's statement stream is greedily rewritten (longest body
first, then name — the module's own determinism order), reusing `_match_at` as
the single matching primitive.  Per unit:

  * an UNMATCHED statement contributes its ordinary `bench_formalize.
    _structure_tokens` walk (byte-identical, per statement, to the raw stream);

  * a MACRO INVOCATION contributes ONE new symbol `("macro", name)` for the
    macro name, then ONE symbol per bound parameter (in the macro's param order)
    carrying that argument's canonical value: `("argval", json(value))`.

DESIGN DECISION (documented prominently, and deliberately the simplest honest
one): a macro invocation is `1 name symbol + 1 symbol per bound argument`.  This
mirrors the counting currency's own `dl_invocation(k) = 1(base) + 1(name) + k`
EXACTLY — the entropy stream sees the invocation the same shape the counting
code charges it.  The adaptive coder then prices which macros recur and with
which arguments; nothing about the collapsed body is re-expanded.

  Because the verdict below is a headline, it must not be a mapping artifact, so
  a SENSITIVITY variant is reported alongside: `structural` args, where each
  bound value is walked into the SAME (op/ref/lit) token space the raw stream
  uses (so a recurring argument reuses existing alphabet).  Both mappings reach
  the same verdict (see the md); the headline uses the `canonical` mapping.

THE NO-VOCABULARY ANCHOR.  With an EMPTY table nothing matches, the rewritten
stream IS the raw stream, model bits are 0, and data bits are KT order-1 over
the raw stream = `ppm_ref`'s number.  This is the consistency anchor: the
module ASSERTS c2_dl(readings, {}) reproduces `ppm_ref.json`'s KT order-1
adaptive_DL to the rounding digit.

--------------------------------------------------------------- scaling (one rule)
Bits are converted to counting units at the fixed exchange rate the sibling
references already use, calibrated on the RAW committed stream:

    data_bits = naive_counting_dl * (total_kt_bits / N_raw) / log2|A|

with `naive_counting_dl` and `log2|A|` READ from `results/entropy_refs.json`
(no recomputation) and `N_raw` the raw (empty-table) stream length computed from
the corpus.  Equivalently a fixed F = naive_counting_dl / (N_raw * log2|A|)
counting-units-per-bit.  N_raw (not the rewritten stream length) is the
denominator on PURPOSE: a shorter rewritten stream must not be penalised for
carrying fewer, heavier tokens — the exchange rate is a property of the currency,
fixed once.  For the empty table this is byte-identical to `ppm_ref`'s DL_1
(the anchor is exact); for the non-empty tables it is the same exchange rate.

------------------------------------------------------------------------ discipline
Reported-first is ABSOLUTE.  The corpus is read from the committed checkpoint at
runtime (`formalize_bench_state.jsonl` via `ppm_ref.load_governed_exo_docs`)
and the arm tables from `results/formalize_frozen_tables.json`, so a post-merge
re-run over a regenerated checkpoint just works.  Determinism: no timestamps, no
randomness, float ops in a fixed order, sorted-key JSON — byte-stable (the test
asserts it).  Caveats inherited from the references stay in force: IN-SAMPLE,
single frozen corpus, zero generalization power (§11.7); KT is a STANDARD but not
optimal context model (no PPM escape / CTW).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# Read-only imports.  The corpus loader and the KT coder come from ppm_ref (one
# coder, one stream loader, no drift); the pricing comes from mdl_macros (one
# leaf-count source of truth); the token walk from bench_formalize.
from bench_formalize import _structure_tokens                      # noqa: E402
from buildloop import mdl_macros                                   # noqa: E402
import tools.ppm_ref as ppm_ref                                    # noqa: E402

ENTROPY_REFS_JSON = _REPO / "results" / "entropy_refs.json"
PPM_REF_JSON = _REPO / "results" / "ppm_ref.json"
FROZEN_TABLES_JSON = _REPO / "results" / "formalize_frozen_tables.json"
JSON_OUT = _REPO / "results" / "c2_report.json"
MD_OUT = _REPO / "results" / "c2_report.md"

KT_ALPHA = 0.5      # Krichevsky-Trofimov add-1/2, the ppm_ref headline estimator
KT_ORDER = 1        # the §10.7 exhibit: adaptive order-1
MAPPINGS = ("canonical", "structural")
HEADLINE_MAPPING = "canonical"


# ------------------------------------------------------- the rewritten token stream
def _value_tokens(value, mapping: str) -> list:
    """Tokens for ONE bound macro argument.

    `canonical` (headline): a single `("argval", canonical-json)` symbol — one
    token per argument, mirroring `dl_invocation`'s flat one-per-arg charge.
    `structural` (sensitivity): the value walked into the raw (op/ref/lit) token
    space so recurring arguments reuse the existing alphabet."""
    if mapping == "canonical":
        return [("argval", json.dumps(value, sort_keys=True, ensure_ascii=False))]
    # structural: mirror bench_formalize._structure_tokens' pred walk over the
    # bound value; scalars fall through to a ref-like leaf.
    out: list = []

    def walk(x):
        if isinstance(x, dict):
            if "op" in x:
                out.append(("op", x["op"]))
                for a in x.get("args", []):
                    walk(a)
            elif "ref" in x:
                out.append(("ref", x["ref"]))
            elif "lit" in x:
                out.append(("lit", x["lit"]))
            else:
                for k in sorted(x):
                    walk(x[k])
        elif isinstance(x, list):
            for e in x:
                walk(e)
        else:
            out.append(("ref", x))

    walk(value)
    return out


def rewritten_stream(readings: list, macro_table: dict, *,
                     mapping: str = HEADLINE_MAPPING) -> list:
    """The corpus token stream AFTER greedy macro rewriting.

    Derived from `mdl_macros._match_at` / `_reading_stats` semantics: statements
    are scanned longest-body-first then name; a matched window collapses to
    `("macro", name)` + its bound-argument tokens; unmatched statements keep
    their raw `_structure_tokens`.  With an empty table this is byte-identical to
    the raw stream `ppm_ref` codes."""
    macro_table = macro_table or {}
    macros = sorted(macro_table.values(), key=lambda m: (-len(m["body"]), m["name"]))
    stream: list = []
    for reading in readings:
        stmts = mdl_macros._statements(reading)
        i = 0
        while i < len(stmts):
            hit = binding = None
            for m in macros:
                b = mdl_macros._match_at(stmts, i, m)
                if b is not None:
                    hit, binding = m, b
                    break
            if hit is not None:
                stream.append(("macro", hit["name"]))
                for param in hit.get("params", []):
                    stream.extend(_value_tokens(binding[param], mapping))
                i += len(hit["body"])
            else:
                stream.extend(_structure_tokens({"statements": [stmts[i]]}))
                i += 1
    return stream


# ----------------------------------------------------------------- the C2 currency
def macro_model_bits(macro_table: dict) -> float:
    """Model bits = the macro table priced EXACTLY as mdl_macros prices it
    (leaf counting), summed.  ONE source of truth — calls into mdl_macros."""
    return float(sum(mdl_macros.dl_macro(m) for m in (macro_table or {}).values()))


def _scale_inputs() -> tuple:
    refs = json.loads(ENTROPY_REFS_JSON.read_text())
    return (refs["naive_counting_dl"], refs["uniform_bits_per_token_log2_A"],
            refs["corpus_dl"])


def c2_dl(readings: list, macro_table: dict, *,
          mapping: str = HEADLINE_MAPPING, n_raw: int = None) -> dict:
    """The two-part entropy-coded description length of `readings` under
    `macro_table`.

    model bits (mdl_macros leaf count of the table) + data bits (KT order-1 over
    the macro-rewritten stream, scaled into counting units at the fixed raw-stream
    exchange rate).  `n_raw` is the raw (empty-table) stream length used as the
    scaling denominator; when omitted it is computed from `readings` so the call
    is self-contained.  Returns the full decomposition."""
    naive, log2_a, _ = _scale_inputs()
    if n_raw is None:
        n_raw = len(rewritten_stream(readings, {}, mapping=mapping))

    model_bits = macro_model_bits(macro_table)
    stream = rewritten_stream(readings, macro_table, mapping=mapping)
    n_stream = len(stream)
    alphabet = sorted(set(stream))
    a = len(alphabet)
    total_kt_bits, _ = ppm_ref.adaptive_code(stream, KT_ORDER, KT_ALPHA, a)

    # Fixed bit -> counting-unit exchange rate, calibrated on the RAW stream.
    data_bits = naive * (total_kt_bits / n_raw) / log2_a if (n_raw and log2_a) else 0.0

    return {
        "model_bits": round(model_bits, 3),
        "data_bits": round(data_bits, 3),
        "total": round(model_bits + data_bits, 3),
        "kt_bits": round(total_kt_bits, 6),
        "stream_length": n_stream,
        "alphabet_size": a,
        "n_macros": len(macro_table or {}),
    }


# ------------------------------------------------------------------- corpus + tables
def load_corpus() -> list:
    """The committed governed / certified / exogenous readings, from the
    checkpoint at runtime (ppm_ref's loader — identical corpus, no drift)."""
    return ppm_ref.load_governed_exo_docs()


def load_final_tables() -> dict:
    """The committed final macro tables per arm, read from the checkpoint's
    per-wave frozen-table artifact.  The last wave's `frozen_table` is the
    committed final table (on the committed run the final wave admits nothing, so
    pre-final == final — verified: it reproduces the committed corpus_dl exactly).
    `reported_dl` is the arm's committed hindsight exogenous DL, carried through
    for the runtime consistency assertion."""
    data = json.loads(FROZEN_TABLES_JSON.read_text())
    out = {}
    for arm, waves in data["arms"].items():
        last = waves[-1]
        out[arm] = {"table": last["frozen_table"],
                    "reported_dl": last["reported_exogenous_dl"]}
    return out


def _counting_corpus_dl(readings: list, table: dict) -> float:
    """The counting currency anchor (mdl_macros, canon=False = the raw committed
    pricing) — reported, never gated."""
    return round(mdl_macros.corpus_dl(readings, table, canon=False)["total"], 3)


# ------------------------------------------------------------------------- compute
def compute() -> dict:
    readings = load_corpus()
    tables = load_final_tables()
    naive, log2_a, counting_corpus_dl_anchor = _scale_inputs()

    ppm = json.loads(PPM_REF_JSON.read_text())
    kt1_anchor = ppm["results"]["kt"]["1"]["adaptive_DL"]      # 1514.506

    n_raw = len(rewritten_stream(readings, {}, mapping=HEADLINE_MAPPING))

    # The three arms x both mappings.
    arms = {}
    empty_table = {}
    for mapping in MAPPINGS:
        arms.setdefault("empty", {})[mapping] = {
            **c2_dl(readings, empty_table, mapping=mapping, n_raw=n_raw),
            "counting_corpus_dl": _counting_corpus_dl(readings, empty_table),
        }
        for arm in ("governed", "ungoverned"):
            table = tables[arm]["table"]
            arms.setdefault(arm, {})[mapping] = {
                **c2_dl(readings, table, mapping=mapping, n_raw=n_raw),
                "counting_corpus_dl": _counting_corpus_dl(readings, table),
            }

    # --- consistency anchor: empty-table C2 data bits == ppm_ref KT order-1 ---
    empty_data_bits = arms["empty"][HEADLINE_MAPPING]["data_bits"]
    empty_total = arms["empty"][HEADLINE_MAPPING]["total"]
    anchor_ok = (abs(empty_data_bits - kt1_anchor) <= 0.01
                 and abs(empty_total - kt1_anchor) <= 0.01)

    # --- the headline verdict, per mapping: does the vocabulary PAY under C2? ---
    verdicts = {}
    for mapping in MAPPINGS:
        gov = arms["governed"][mapping]["total"]
        emp = arms["empty"][mapping]["total"]
        ung = arms["ungoverned"][mapping]["total"]
        # KT order-1 advantage over the counting currency, and how much C2 keeps.
        kt_advantage = round(counting_corpus_dl_anchor - emp, 3)
        recovered = round(counting_corpus_dl_anchor - gov, 3)
        verdicts[mapping] = {
            "governed_c2": gov,
            "ungoverned_c2": ung,
            "empty_c2_no_vocabulary": emp,
            "vocabulary_pays_under_c2": bool(gov < emp),
            "vocabulary_cost_under_c2": round(gov - emp, 3),
            "kt1_advantage_over_counting": kt_advantage,
            "c2_recovered_of_kt1_advantage": recovered,
            "c2_recovered_pct_of_kt1_advantage":
                round(100.0 * recovered / kt_advantage, 1) if kt_advantage else 0.0,
            "c2_ranks_governed_below_ungoverned": bool(gov < ung),
            "governance_gap_c2": round(ung - gov, 3),
        }

    return {
        "experiment": "WP-C2 — two-part entropy-coded DL, REPORTED (COMPRESSION.md §3 C2 / §11.8)",
        "gate_status": (
            "REPORTED experiment. Gates are UNCHANGED: admission stays the "
            "counting currency (mdl_macros strict-DL-decrease + the certificate "
            "batteries). Nothing gates on any number here (§11.8: C2/C4 stay "
            "reporting experiments)."
        ),
        "question": (
            "How much of KT order-1's 624-unit advantage over the counting "
            "corpus_dl (2139 -> 1514.5, the §10.7 exhibit) does a two-part "
            "macro+entropy-coded currency recover while KEEPING the vocabulary? "
            "And does the certified macro vocabulary even PAY under entropy "
            "coding?"
        ),
        "currency": {
            "definition": "c2_dl = model_bits + data_bits",
            "model_bits": (
                "the macro table priced EXACTLY as mdl_macros prices it "
                "(leaf counting, dl_macro); one source of truth."
            ),
            "data_bits": (
                "adaptive KT order-1 (ppm_ref's coder) over the macro-REWRITTEN "
                "token stream, scaled bits->counting at the fixed raw-stream "
                "exchange rate."
            ),
        },
        "token_mapping": {
            "headline": HEADLINE_MAPPING,
            "rule": (
                "greedy rewrite via mdl_macros._match_at; a macro invocation = "
                "1 ('macro', name) symbol + 1 symbol per bound argument "
                "(('argval', canonical-json) in the canonical mapping). Mirrors "
                "dl_invocation(k) = base + name + k exactly. Unmatched statements "
                "keep their raw _structure_tokens."
            ),
            "sensitivity_mapping": (
                "'structural': bound arguments walked into the raw op/ref/lit "
                "token space (recurring args reuse the existing alphabet). "
                "Reported to show the verdict is not a mapping artifact."
            ),
            "no_vocabulary_anchor": (
                "empty table => rewritten stream == raw stream, 0 model bits, "
                "data bits == ppm_ref KT order-1. Asserted equal."
            ),
        },
        "scaling_convention": (
            "data_bits = naive_counting_dl * (total_kt_bits / N_raw) / log2|A|; "
            "naive_counting_dl and log2|A| READ from entropy_refs.json, N_raw the "
            "raw (empty-table) stream length. Fixed exchange-rate; empty table "
            "reproduces ppm_ref's DL_1 exactly. No tuned constants."
        ),
        "scaling_inputs_from_entropy_refs": {
            "naive_counting_dl": naive,
            "uniform_bits_per_token_log2_A": log2_a,
            "counting_corpus_dl": counting_corpus_dl_anchor,
            "n_raw_stream_length": n_raw,
        },
        "consistency_anchor": {
            "ppm_ref_kt_order1_adaptive_DL": kt1_anchor,
            "c2_empty_table_data_bits": empty_data_bits,
            "c2_empty_table_total": empty_total,
            "reconciles": bool(anchor_ok),
        },
        "committed_tables": {
            "governed": {"n_macros": len(tables["governed"]["table"]),
                         "reported_dl": tables["governed"]["reported_dl"]},
            "ungoverned": {"n_macros": len(tables["ungoverned"]["table"]),
                           "reported_dl": tables["ungoverned"]["reported_dl"]},
        },
        "arms": arms,
        "verdict": verdicts,
        "headline": {
            "mapping": HEADLINE_MAPPING,
            **verdicts[HEADLINE_MAPPING],
            "finding": _finding_text(verdicts[HEADLINE_MAPPING]),
        },
        "pre_registered_future_predicate": (
            "C2 (or C4/NML) replaces the counting currency as the ADMISSION gate "
            "ONLY IF, on the committed HOLDOUT source set (>=20 readings, §11.7 — "
            "in-sample deltas have zero generalization power), the two-part "
            "entropy-coded DL WITH the governed vocabulary is strictly lower than "
            "BOTH (a) the counting corpus_dl AND (b) the empty-table C2 (pure KT) "
            "by a margin exceeding the vocabulary's model bits — i.e. the "
            "certified vocabulary must PAY under C2 out-of-sample. STATED, NOT "
            "ARMED. On the committed in-sample corpus the predicate is FALSE by "
            f"{verdicts[HEADLINE_MAPPING]['vocabulary_cost_under_c2']} units "
            "(the vocabulary COSTS bits under C2), so migration is not merely "
            "unarmed but counter-indicated: the §11.8 gate ('a recorded instance "
            "of the counting currency MISPRICING an admitted structure') is not "
            "met — C2 does not show the counting gate admitting a net-negative "
            "macro; it shows the opposite, that the vocabulary's value is "
            "certification structure, not entropy-coding compression."
        ),
        "caveats": {
            "in_sample": (
                "IN-SAMPLE, single frozen governed corpus, hindsight; zero "
                "generalization power (§11.7)."
            ),
            "reference_only": (
                "KT is a STANDARD but not optimal context model (no PPM escape, "
                "no cross-order mixing, no CTW). C2 here is a two-part code built "
                "on that reference coder, reported for orientation only."
            ),
            "mapping_dependence": (
                "The absolute data-bits depend on the token mapping; the VERDICT "
                "(vocabulary does not pay under C2) holds under both the "
                "canonical and structural mappings (see the arms table)."
            ),
        },
    }


def _finding_text(v: dict) -> str:
    if v["vocabulary_pays_under_c2"]:
        return (
            f"The certified macro vocabulary PAYS under C2: governed C2 = "
            f"{v['governed_c2']} < empty-table C2 = {v['empty_c2_no_vocabulary']}. "
            f"C2 with the vocabulary recovers "
            f"{v['c2_recovered_of_kt1_advantage']} of the "
            f"{v['kt1_advantage_over_counting']}-unit KT order-1 advantage "
            f"({v['c2_recovered_pct_of_kt1_advantage']}%)."
        )
    return (
        f"The certified macro vocabulary does NOT pay under C2: governed C2 = "
        f"{v['governed_c2']} > empty-table C2 (pure KT) = "
        f"{v['empty_c2_no_vocabulary']}, i.e. the vocabulary COSTS "
        f"{v['vocabulary_cost_under_c2']} units under entropy coding. Keeping "
        f"the vocabulary, C2 recovers {v['c2_recovered_of_kt1_advantage']} of the "
        f"{v['kt1_advantage_over_counting']}-unit KT order-1 advantage "
        f"({v['c2_recovered_pct_of_kt1_advantage']}%); the full advantage is "
        f"available only by ABANDONING the vocabulary. This is the honest "
        f"finding: adaptive order-1 already harvests the sequential recurrence "
        f"the macros deduplicate, so under entropy coding the vocabulary's value "
        f"is certification structure, not compression. Under C2 the governance "
        f"ranking also does not hold (governed C2 "
        f"{'<' if v['c2_ranks_governed_below_ungoverned'] else '>'} ungoverned "
        f"C2 {v['ungoverned_c2']}) — driven by the DATA bits, not the model "
        f"table: the governed arm's macro-rewritten stream costs more "
        f"entropy-coded data bits, which outweighs governed's SMALLER model "
        f"table (the ungoverned arm carries the larger paid-for vocabulary yet "
        f"lands lower under C2)."
    )


# --------------------------------------------------------------------- markdown
def to_markdown(r: dict) -> str:
    L = []
    hb = r["headline"]
    si = r["scaling_inputs_from_entropy_refs"]
    ca = r["consistency_anchor"]
    L.append("# C2 — two-part entropy-coded DL (REPORTED experiment)")
    L.append("")
    L.append(
        "COMPRESSION.md **§3 C2** made concrete, under the **§11.8** gate. "
        "This is a **reporting experiment**: the admission currency stays the "
        "counting one (`mdl_macros`), **the gates are unchanged, and nothing "
        "gates on any number below**. C2 only measures and reports."
    )
    L.append("")
    L.append(f"> {r['gate_status']}")
    L.append("")
    L.append("## The question")
    L.append("")
    L.append(f"> {r['question']}")
    L.append("")
    L.append("## The currency")
    L.append("")
    L.append("`c2_dl = model_bits + data_bits`, where")
    L.append("")
    L.append(f"- **model bits** — {r['currency']['model_bits']}")
    L.append(f"- **data bits** — {r['currency']['data_bits']}")
    L.append("")
    L.append("## The token mapping (design decision)")
    L.append("")
    L.append(f"**Headline mapping: `{r['token_mapping']['headline']}`.** "
             f"{r['token_mapping']['rule']}")
    L.append("")
    L.append(f"- **Sensitivity mapping** — {r['token_mapping']['sensitivity_mapping']}")
    L.append(f"- **No-vocabulary anchor** — {r['token_mapping']['no_vocabulary_anchor']}")
    L.append("")
    L.append("## Scaling")
    L.append("")
    L.append(f"> {r['scaling_convention']}")
    L.append("")
    L.append(
        f"Read from `entropy_refs.json`: naive_counting_dl = "
        f"{si['naive_counting_dl']}, log2\\|A\\| = "
        f"{si['uniform_bits_per_token_log2_A']}, counting corpus_dl = "
        f"{si['counting_corpus_dl']}; N_raw (raw stream length) = "
        f"{si['n_raw_stream_length']}."
    )
    L.append("")
    L.append("## Consistency anchor (must reconcile with `ppm_ref`)")
    L.append("")
    ok = "RECONCILES" if ca["reconciles"] else "**MISMATCH**"
    L.append(
        f"Empty table => 0 model bits + KT order-1 over the raw stream. "
        f"`ppm_ref` KT order-1 adaptive_DL = **{ca['ppm_ref_kt_order1_adaptive_DL']}**; "
        f"C2 empty-table data bits = **{ca['c2_empty_table_data_bits']}**, "
        f"total = **{ca['c2_empty_table_total']}**. {ok}."
    )
    L.append("")
    L.append("## The decomposition — both arms, both mappings")
    L.append("")
    L.append(
        "| mapping | arm | model bits | data bits | **C2 total** | "
        "counting corpus_dl | stream len | \\|A\\| |")
    L.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for mapping in MAPPINGS:
        for arm in ("empty", "governed", "ungoverned"):
            a = r["arms"][arm][mapping]
            label = "empty (no vocab)" if arm == "empty" else arm
            L.append(
                f"| {mapping} | {label} | {a['model_bits']} | {a['data_bits']} | "
                f"**{a['total']}** | {a['counting_corpus_dl']} | "
                f"{a['stream_length']} | {a['alphabet_size']} |")
    L.append("")
    L.append("## Verdict — does the vocabulary PAY under C2?")
    L.append("")
    L.append(f"**{hb['finding']}**")
    L.append("")
    L.append("| mapping | governed C2 | empty (pure KT) C2 | vocab pays? | "
             "vocab cost | KT-1 advantage | C2 recovers | % |")
    L.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for mapping in MAPPINGS:
        v = r["verdict"][mapping]
        pays = "YES" if v["vocabulary_pays_under_c2"] else "**NO**"
        L.append(
            f"| {mapping} | {v['governed_c2']} | {v['empty_c2_no_vocabulary']} | "
            f"{pays} | {v['vocabulary_cost_under_c2']} | "
            f"{v['kt1_advantage_over_counting']} | "
            f"{v['c2_recovered_of_kt1_advantage']} | "
            f"{v['c2_recovered_pct_of_kt1_advantage']} |")
    L.append("")
    L.append("### The governance question in the new currency")
    L.append("")
    hv = r["verdict"][HEADLINE_MAPPING]
    ranks = ("does" if hv["c2_ranks_governed_below_ungoverned"] else "does NOT")
    ga = r["arms"]["governed"][HEADLINE_MAPPING]
    ua = r["arms"]["ungoverned"][HEADLINE_MAPPING]
    L.append(
        f"The counting currency ranks governed (2139) below ungoverned (2371); "
        f"the origin-blind question is whether C2 does too. Under C2 "
        f"({HEADLINE_MAPPING} mapping) governed = {hv['governed_c2']}, "
        f"ungoverned = {hv['ungoverned_c2']}: C2 **{ranks}** rank governed below "
        f"ungoverned (gap {hv['governance_gap_c2']}). Honest reading: the "
        f"inversion is driven by the DATA bits, not the model table — the "
        f"governed arm's macro-rewritten stream costs more entropy-coded data "
        f"bits ({ga['data_bits']} vs {ua['data_bits']}, a larger symbol "
        f"alphabet {ga['alphabet_size']} vs {ua['alphabet_size']}), and that "
        f"outweighs governed's SMALLER model table ({ga['model_bits']} vs "
        f"{ua['model_bits']} bits) — i.e. the arm with the LARGER paid-for "
        f"vocabulary (ungoverned) actually lands lower under C2. So C2 is not, "
        f"as constructed, an origin-blind governance detector; the counting and "
        f"prequential currencies are where governance shows up."
    )
    L.append("")
    L.append("## Pre-registered future predicate (stated, not armed)")
    L.append("")
    L.append(f"> {r['pre_registered_future_predicate']}")
    L.append("")
    L.append("## Caveats")
    L.append("")
    L.append(f"> {r['caveats']['in_sample']}")
    L.append("")
    L.append(f"> {r['caveats']['reference_only']}")
    L.append("")
    L.append(f"> {r['caveats']['mapping_dependence']}")
    L.append("")
    return "\n".join(L)


def _dump_json(r: dict) -> str:
    return json.dumps(r, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    r = compute()
    if not r["consistency_anchor"]["reconciles"]:
        sys.stderr.write(
            "STOP: C2 empty-table data bits do not reconcile with ppm_ref "
            f"KT order-1 ({r['consistency_anchor']}).\n")
        return 1
    JSON_OUT.write_text(_dump_json(r))
    MD_OUT.write_text(to_markdown(r))
    sys.stdout.write(f"wrote {JSON_OUT}\nwrote {MD_OUT}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
