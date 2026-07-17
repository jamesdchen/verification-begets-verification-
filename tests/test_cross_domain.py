"""WP-XDOM — the COMPRESSION.md §5 cross-domain sharing tooth.

§5's cross-domain worry, in the plan's words: "math and service readings flow
through one miner and one macro table per registry; cluster keys keep the
domains from cross-witnessing spuriously … worth a tooth that a shared registry
never mints a cross-domain macro without genuine shared structure." The miner
(`buildloop.recurrence`) and the macro table (`library.Registry.macro_table`)
ARE shared — one of each per registry, no domain column — so the guarantee has
to come from the cluster key, not from any per-domain partitioning. This file is
that tooth.

WHICH FORM OF THE TOOTH DOES THE CODE'S REALITY SUPPORT? The two LF-kind
vocabularies are PROVABLY DISJOINT sets of strings:

    math (generators.math_reading.MATH_LF_KINDS):
        {object, operator, hypothesis, conclusion, quantifier, ambient}
    service (generators.reading.LF_KINDS):
        {quantity, action, effect, bound, always, order,
         eventually, until, before, within, lifecycle, transition, input}

The intersection is EMPTY (note in particular: math has `quantifier`; service
does NOT — it renders comparatives/quantifiers as `bound`). Because the miner's
cluster key is `(window_length, tuple_of_lf_kinds)` (recurrence.mine) and every
mined macro body carries its cluster's kinds LITERALLY (a cluster fixes the
kind-tuple, so anti-unification never generalizes a kind position to a $param),
a math kind-tuple can never equal a service kind-tuple. So a cross-domain
cluster — and therefore a cross-domain macro — is impossible BY CONSTRUCTION,
and no "genuine shared structure" between the domains exists at the kind-tuple
level for one to be minted from.

The tooth is therefore the DISJOINTNESS PIN plus a SENTINEL: a planted
adversarial math/service pair contrived to collide at the kind-tuple level CANNOT
be built without one vocabulary gaining the other's kind, so instead of a
byte-similar-shapes fixture we pin the disjointness itself AND fail loudly the
day either vocabulary gains a kind the other already has (the only way the
guarantee could ever silently break). The three claims:

  (a) mining the combined math+service corpus mints NO macro whose cluster key
      (kind-tuple) mixes the vocabularies — verified by construction against the
      committed checkpoint + committed service corpus;
  (b) the disjointness pin + the drift sentinel (the planted-collision tooth, in
      the form the code's reality supports);
  (c) per-domain corpus_dl decomposition: the combined table over the combined
      corpus costs EXACTLY the sum of the two separate-domain runs — no
      cross-subsidy (a math macro never abbreviates a service reading, and vice
      versa, because its literal kinds never unify with the other domain's).

Relational asserts throughout (no magic-number goldens): equalities and
subset/disjointness relations that hold for any corpora with these vocabularies.
LLM-free, fast; loads only committed fixtures. House rule: full suite in CI.
"""
import json
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from generators import reading as service_reading
from generators import math_reading
from buildloop import recurrence, mdl_macros
from buildloop.reading_corpus import load_readings

_REPO = pathlib.Path(__file__).resolve().parent.parent
_SERVICE_DIR = _REPO / "specs" / "readings"
_MATH_STATE = _REPO / "results" / "formalize_bench_state.jsonl"

_MATH_KINDS = frozenset(math_reading.MATH_LF_KINDS)
_SERVICE_KINDS = frozenset(service_reading.LF_KINDS)


# ------------------------------------------------------------- corpus loaders
def _service_docs():
    """The committed REAL service readings (top-level specs/readings/*.json),
    as mining/pricing docs. dream/ excluded (system-origin, S5)."""
    docs = []
    for entry in load_readings(_SERVICE_DIR):
        obj = json.loads(entry.source)
        docs.append({"service": obj["reading"]["service"],
                     "statements": entry.statements})
    return docs


def _math_docs():
    """The committed math checkpoint's certified governed exogenous readings.

    Reproduces tools.entropy_refs.load_governed_certified_docs' filter so the
    tooth reads the SAME math corpus the math reference stack does."""
    docs = []
    with _MATH_STATE.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("arm") != "governed" or not rec.get("certified"):
                continue
            rj = rec.get("reading_json") or ""
            if not rj:
                continue
            doc = json.loads(rj)
            if not isinstance(doc, dict) or "statements" not in doc:
                continue
            docs.append({"theorem": doc.get("theorem", "t"),
                         "statements": doc["statements"]})
    return docs


def _kinds_present(docs):
    present = set()
    for d in docs:
        for s in d["statements"]:
            lf = s.get("lf", {})
            if isinstance(lf, dict):
                present.add(lf.get("kind"))
    present.discard(None)
    return present


# ---------------------------------------------------- (b) disjointness pin
def test_vocabularies_are_disjoint_by_construction():
    """The load-bearing fact: the two LF-kind vocabularies share no string.
    Everything else in this file rests on this."""
    assert _MATH_KINDS & _SERVICE_KINDS == frozenset(), (
        "math and service LF-kind vocabularies OVERLAP: "
        f"{sorted(_MATH_KINDS & _SERVICE_KINDS)} — a shared cluster key across "
        "domains becomes possible, and the §5 cross-domain guarantee is void")


def test_quantifier_is_math_only_not_shared():
    """The §5 question named `quantifier` explicitly. Math has it; service does
    NOT (service uses `bound` for comparatives/quantifiers). Pin that the one
    plausibly-overlapping name is single-domain."""
    assert "quantifier" in _MATH_KINDS
    assert "quantifier" not in _SERVICE_KINDS


def test_drift_sentinel_neither_vocabulary_gains_the_others_kind():
    """SENTINEL (the planted-collision tooth in the form reality supports).

    A cross-domain cluster is impossible while the vocabularies are disjoint, so
    a byte-similar adversarial pair CANNOT be constructed. The only way the
    guarantee could ever silently break is a future edit that adds one domain's
    kind to the other's vocabulary. This fails LOUDLY the day that happens."""
    leaked_into_service = _SERVICE_KINDS & _MATH_KINDS
    leaked_into_math = _MATH_KINDS & _SERVICE_KINDS
    assert not leaked_into_service, (
        f"service vocabulary gained math kind(s) {sorted(leaked_into_service)}")
    assert not leaked_into_math, (
        f"math vocabulary gained service kind(s) {sorted(leaked_into_math)}")
    # And the miner's math discriminator must stay single-sourced from the math
    # vocabulary (so _is_math_domain classifies by exactly this set).
    assert recurrence._MATH_LF_KINDS == _MATH_KINDS


def test_is_math_domain_discriminates_by_kind_vocabulary():
    """`recurrence._is_math_domain` is the merged-domain discriminator: a window
    is math-domain iff every statement kind is a math kind. Pin BOTH directions
    on real statements so a service window and a math window never co-classify."""
    svc = _service_docs()
    math = _math_docs()
    # every committed service reading is classified NON-math (service branch)
    for d in svc:
        assert not recurrence._is_math_domain(d["statements"]), (
            f"service reading {d.get('service')!r} misclassified as math-domain")
    # every committed math reading is classified math
    for d in math:
        assert recurrence._is_math_domain(d["statements"]), (
            "math checkpoint reading misclassified as non-math")


# ------------------------------------------- (a) no cross-domain macro minted
def _cluster_domain(kind_tuple):
    kinds = set(kind_tuple)
    if kinds <= _MATH_KINDS:
        return "math"
    if kinds <= _SERVICE_KINDS:
        return "service"
    return "MIXED"


def test_combined_mine_mints_no_cross_domain_cluster():
    """(a) Mining the combined math+service corpus mints NO candidate whose
    kind-tuple spans both vocabularies. Every mined cluster key is drawn ENTIRELY
    from one vocabulary — the shared miner never cross-witnesses."""
    combined = _math_docs() + _service_docs()
    cands = recurrence.mine(combined, {})
    assert cands, "expected the combined corpus to mine at least one candidate"
    for c in cands:
        kinds = tuple(c["cluster_key"])
        dom = _cluster_domain(kinds)
        assert dom != "MIXED", (
            f"cross-domain macro minted: cluster key {list(kinds)} mixes "
            "math and service LF kinds")
    # and BOTH domains actually contributed candidates (so this is a real test,
    # not a vacuous pass on an empty mine)
    doms = {_cluster_domain(tuple(c["cluster_key"])) for c in cands}
    assert doms == {"math", "service"}, (
        f"expected both domains to mine candidates, got {sorted(doms)}")


def test_mined_macro_bodies_carry_literal_single_domain_kinds():
    """The mechanism behind (a): a mined macro body's kind positions are LITERAL
    (a cluster fixes the kind-tuple, so anti-unification never $param-izes a
    kind), and those literal kinds all belong to ONE vocabulary. So the macro can
    only ever match statements of its own domain."""
    combined = _math_docs() + _service_docs()
    for c in recurrence.mine(combined, {}):
        body = c["candidate"]["body"]
        body_kinds = set()
        for template in body:
            assert isinstance(template, dict), "macro body statement not a dict"
            kind = template.get("kind")
            assert isinstance(kind, str) and not kind.startswith("$"), (
                f"macro body kind position is not a literal: {kind!r}")
            body_kinds.add(kind)
        assert _cluster_domain(tuple(body_kinds)) != "MIXED", (
            f"macro body kinds {sorted(body_kinds)} span both domains")


def test_cross_domain_macro_never_matches_the_other_domain():
    """A macro mined from one domain never unifies against a reading of the
    other — the concrete witness-crossing guarantee. Mine each domain's table,
    then assert zero matches on the opposite corpus."""
    svc, math = _service_docs(), _math_docs()
    svc_table = recurrence.searched_macro_sequence(svc, {})
    math_table = recurrence.searched_macro_sequence(math, {})

    def _hits(macro, docs):
        return sum(1 for r in docs
                   for i in range(len(r["statements"]))
                   if mdl_macros._match_at(r["statements"], i, macro) is not None)

    for m in math_table.values():
        assert _hits(m, svc) == 0, (
            f"math macro {m['name']} matched a service reading")
    for m in svc_table.values():
        assert _hits(m, math) == 0, (
            f"service macro {m['name']} matched a math reading")


# ------------------------------------- (c) per-domain corpus_dl decomposition
def test_combined_table_corpus_dl_decomposes_with_no_cross_subsidy():
    """(c) The combined table over the combined corpus costs EXACTLY the sum of
    the two separate-domain runs. Because each domain's macros never abbreviate
    the other's readings, there is no cross-subsidy: the shared registry prices
    each domain independently even though the miner and table are one."""
    svc, math = _service_docs(), _math_docs()
    svc_table = recurrence.searched_macro_sequence(svc, {})
    math_table = recurrence.searched_macro_sequence(math, {})

    # macro names are content-hashed, so the two tables never collide
    assert set(svc_table) & set(math_table) == set(), (
        "macro-name collision across domains breaks the decomposition premise")

    combined_table = dict(math_table)
    combined_table.update(svc_table)
    combined_corpus = math + svc

    total_combined = mdl_macros.corpus_dl(combined_corpus, combined_table)["total"]
    total_math = mdl_macros.corpus_dl(math, math_table)["total"]
    total_svc = mdl_macros.corpus_dl(svc, svc_table)["total"]

    assert total_combined == pytest.approx(total_math + total_svc, abs=1e-9), (
        f"cross-subsidy detected: combined {total_combined} != "
        f"math {total_math} + service {total_svc}")

    # And the per-macro witness counts are unchanged by combining (no macro
    # gains a witness from the other domain).
    combined_uses = mdl_macros.corpus_dl(
        combined_corpus, combined_table)["reading_uses"]
    math_uses = mdl_macros.corpus_dl(math, math_table)["reading_uses"]
    svc_uses = mdl_macros.corpus_dl(svc, svc_table)["reading_uses"]
    for name, u in math_uses.items():
        assert combined_uses[name] == u, (
            f"math macro {name} changed witness count in the combined corpus")
    for name, u in svc_uses.items():
        assert combined_uses[name] == u, (
            f"service macro {name} changed witness count in the combined corpus")


def test_combined_run_reproduces_separate_run_tables():
    """Stronger relational form of (c): mining the COMBINED corpus and mining
    each domain SEPARATELY admit the same per-domain macros. The presence of the
    other domain neither adds nor suppresses a domain's macros (the shared miner
    is domain-decomposable)."""
    svc, math = _service_docs(), _math_docs()
    svc_table = recurrence.searched_macro_sequence(svc, {})
    math_table = recurrence.searched_macro_sequence(math, {})
    combined_table = recurrence.searched_macro_sequence(math + svc, {})

    expected = set(math_table) | set(svc_table)
    assert set(combined_table) == expected, (
        f"combined mine differs from the union of separate mines: "
        f"combined {sorted(combined_table)} vs "
        f"union {sorted(expected)}")


# ------------------------- the service-domain reference stack (tools.service_refs)
# The second half of WP-XDOM: guards for tools/service_refs.py under the sibling
# tools' determinism discipline (byte-stable artifacts, committed == fresh) plus
# the scaling-ratio and headline consistency the math stack's tests enforce.
from tools import service_refs as sr  # noqa: E402


def test_service_refs_stream_shape_and_alphabet_is_service_only():
    r = sr.compute()
    assert r["n_readings"] == len(_service_docs())
    assert r["stream_length"] == sum(r["reading_token_lengths"])
    assert r["stream_length"] > 0 and r["alphabet_size"] > 1
    # Every kind token in the service stream names a SERVICE kind, never a math
    # one -- the token stream is second-domain by construction.
    docs = sr.load_service_readings()
    toks = sr.token_stream(docs)
    kind_values = {t.split("=", 1)[1].strip('"')
                   for t in toks if t.startswith("kind=")}
    assert kind_values <= _SERVICE_KINDS
    assert kind_values & _MATH_KINDS == set()


def test_service_refs_dl_is_ratio_of_bits_per_token():
    """Scaling discipline: every DL is naive * (bits_per_token / log2|A|), the
    same ratio convention the math stack uses (units reconciled, never mixed)."""
    r = sr.compute()
    naive = r["naive_counting_dl"]
    log2a = r["uniform_bits_per_token_log2_A"]
    for est in ("kt", "laplace"):
        for k in ("0", "1", "2"):
            row = r["adaptive"][est][k]
            assert row["adaptive_DL"] == round(
                naive * (row["bits_per_token"] / log2a), 3)


def test_service_refs_corpus_dl_is_fresh_mine_not_hardcoded():
    """corpus_dl is recomputed from a fresh mine over the committed corpus (no
    committed live service macro table exists)."""
    docs = sr.load_service_readings()
    table = recurrence.searched_macro_sequence(docs, {})
    r = sr.compute()
    assert r["corpus_dl"] == round(
        mdl_macros.corpus_dl(docs, table)["total"], 3)
    assert r["macros_admitted"] == sorted(table)


def test_service_refs_headline_matches_rows():
    r = sr.compute()
    hl = r["headline"]
    all_dls = [r["adaptive"][est][str(k)]["adaptive_DL"]
               for est in ("kt", "laplace") for k in (0, 1, 2)]
    assert hl["best_adaptive"]["adaptive_DL"] == min(all_dls)
    any_beat = any(r["adaptive"][est][str(k)]["beats_corpus_dl"]
                   for est in ("kt", "laplace") for k in (0, 1, 2))
    assert hl["any_adaptive_order_k_beats_corpus_dl"] == any_beat


def test_service_refs_math_side_by_side_read_from_committed_artifacts():
    """The math comparators are READ from the committed math artifacts, never
    recomputed -- so the side-by-side cannot drift from the math stack."""
    r = sr.compute()
    e = json.loads((_REPO / "results" / "entropy_refs.json").read_text())
    ms = r["math_side_by_side"]["entropy_refs"]
    assert ms["corpus_dl"] == e["corpus_dl"]
    assert ms["DL1"] == e["order_k"]["DL1"]
    p = json.loads((_REPO / "results" / "ppm_ref.json").read_text())
    assert r["math_side_by_side"]["ppm_ref"]["kt"]["1"] == \
        p["results"]["kt"]["1"]["adaptive_DL"]


def test_service_refs_different_profile_verdict_holds():
    """The headline finding is relational, not a magic number: the service
    order-1 surplus is a much smaller fraction of corpus_dl than the math one
    (the math domain's order-1-sequential-structure surplus does NOT recur)."""
    r = sr.compute()
    hl = r["headline"]
    svc = hl["service_order1_surplus_pct_of_corpus_dl"]
    math = hl["math_order1_surplus_pct_of_corpus_dl"]
    assert math is not None
    assert svc < math, "expected service order-1 surplus below the math one"
    assert hl["same_profile_as_math"] is False
    assert "DIFFERENT profile" in hl["profile_verdict"]


def test_service_refs_byte_stability():
    r1 = sr.compute()
    r2 = sr.compute()
    assert sr._dump_json(r1) == sr._dump_json(r2)
    assert sr.to_markdown(r1) == sr.to_markdown(r2)


def test_service_refs_committed_artifacts_match_recompute():
    r = sr.compute()
    assert (_REPO / "results" / "service_refs.json").read_text() == \
        sr._dump_json(r)
    assert (_REPO / "results" / "service_refs.md").read_text() == \
        sr.to_markdown(r)
