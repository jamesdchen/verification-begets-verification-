"""Teeth for D2 of the compression workstream (results/import_findings.md
Finding 3; COMPRESSION.md §11.2 blockers (i) and (ii)).

Deterministic, LLM-free.  Two halves:

  * FIXPOINT EXPANSION (generators.reading._expand_macros): a macro body may
    itself invoke a macro (a level-2+ tower); expansion iterates to fixpoint.
    Depth-1 tables are byte-identical to the historical single pass (the
    INLINED-baseline pin); a cycle / over-deep chain raises BadReading naming
    the offending chain (teeth, not silent truncation).

  * RECODE-THEN-MINE (buildloop.mdl_macros._reading_stats): pricing matches
    candidate bodies against the corpus RECODED in the current vocabulary, so a
    candidate whose body invokes an admitted macro can find its uses (under the
    historical raw-only matching it priced uses=0 forever -- COMPRESSION.md:
    712-716).  The currency is unchanged; flat tables price byte-identically
    (the flat-table equivalence pin), and admissions STACK: the second
    admission's dl_before is exactly the first's dl_after (the chain rule).
"""
import json

import pytest

import common
from buildloop import mdl_macros
from buildloop.mdl_macros import corpus_dl, macro_admission_decision
from generators import reading
from generators.reading import BadReading, _expand_macros
from tests import fixtures_macro_corpora as fx


# ---------------------------------------------------------------- macro tables
def _macro_a():
    """Depth-1: one concrete-template body statement."""
    return {"name": "guard", "params": ["q"],
            "body": [{"kind": "always",
                      "pred": {"op": ">=", "left": "$q", "right": 0}}]}


def _macro_b():
    """Depth-2: the body INVOKES guard (level-2 tower)."""
    return {"name": "sell_rules", "params": ["q", "limit"],
            "body": [{"kind": "macro", "name": "guard", "args": {"q": "$q"}},
                     {"kind": "bound", "action": "sell", "left": "n",
                      "cmp": "<=", "right": "$limit"}]}


def _macro_c():
    """Depth-3: the body invokes sell_rules, which invokes guard."""
    return {"name": "lvl3", "params": ["q", "limit"],
            "body": [{"kind": "macro", "name": "sell_rules",
                      "args": {"q": "$q", "limit": "$limit"}}]}


def _tower_table():
    return {m["name"]: m for m in (_macro_a(), _macro_b(), _macro_c())}


def _inv(sid, name, args, force="demand", quote="s"):
    return {"id": sid, "force": force, "quote": quote,
            "lf": {"kind": "macro", "name": name, "args": args}}


def _old_single_pass(stmts, table):
    """The HISTORICAL (pre-D2) _expand_macros: exactly one linear pass.  Kept
    inline here as the byte-identity reference for depth-1 tables."""
    out = []
    for s in stmts:
        lf = s.get("lf") if isinstance(s, dict) else None
        if isinstance(lf, dict) and lf.get("kind") == "macro":
            out.extend(reading._expand_one(s, table))
        else:
            out.append(s)
    return out


# ------------------------------------------------- fixpoint: depth-1 unchanged
def test_depth1_expansion_byte_identical_to_single_pass():
    table = {"guard": _macro_a()}
    stmts = [
        {"id": "s0", "force": "choice", "quote": "",
         "lf": {"kind": "quantity", "name": "stock", "min": 0, "max": 9}},
        _inv("s1", "guard", {"q": "stock"}),
        {"id": "s2", "force": "choice", "quote": "",
         "lf": {"kind": "action", "name": "sell", "arg": "n"}},
    ]
    got = _expand_macros(list(stmts), table)
    want = _old_single_pass(list(stmts), table)
    assert common.canonical_json(got) == common.canonical_json(want)


def test_no_invocations_stream_is_untouched():
    stmts = [{"id": "s0", "force": "choice", "quote": "",
              "lf": {"kind": "action", "name": "sell"}}]
    got = _expand_macros(stmts, _tower_table())
    assert common.canonical_json(got) == common.canonical_json(stmts)


# ---------------------------------------------------- fixpoint: depth-2 and -3
def test_depth2_expands_to_concrete_statements():
    got = _expand_macros([_inv("s1", "sell_rules", {"q": "stock", "limit": 5})],
                         _tower_table())
    kinds = [s["lf"]["kind"] for s in got]
    assert kinds == ["always", "bound"]          # no kind:"macro" survives
    assert got[0]["lf"]["pred"] == {"op": ">=", "left": "stock", "right": 0}
    assert got[1]["lf"]["right"] == 5
    # each expanded statement inherits the invocation's force+quote, and the
    # accumulated id IS the expansion chain
    assert all(s["force"] == "demand" and s["quote"] == "s" for s in got)
    assert got[0]["id"] == "s1~sell_rules#0~guard#0"


def test_depth3_expands_to_concrete_statements():
    got = _expand_macros([_inv("s1", "lvl3", {"q": "seats", "limit": 3})],
                         _tower_table())
    kinds = [s["lf"]["kind"] for s in got]
    assert kinds == ["always", "bound"]
    assert got[0]["lf"]["pred"]["left"] == "seats"
    assert got[1]["lf"]["right"] == 3


def test_depth2_parses_end_to_end_through_the_lf_gates():
    """The D2 headline: pre-fix, the inner invocation reached parse_reading's
    LF-kind gate as kind:"macro" and threw BadReading; now it parses."""
    request = "sell at most 5 per call and never go negative"
    doc = {"service": "shop", "statements": [
        {"id": "s1", "force": "choice", "quote": "",
         "lf": {"kind": "quantity", "name": "stock", "min": 0, "max": 10}},
        {"id": "s2", "force": "choice", "quote": "",
         "lf": {"kind": "action", "name": "sell", "arg": "n"}},
        {"id": "s3", "force": "choice", "quote": "",
         "lf": {"kind": "lifecycle", "states": ["open", "closed"],
                "initial": "open"}},
        {"id": "s4", "force": "choice", "quote": "",
         "lf": {"kind": "transition", "action": "sell",
                "from": "open", "to": "open"}},
        _inv("s5", "sell_rules", {"q": "stock", "limit": 5},
             quote="sell at most 5"),
    ]}
    r = reading.parse_reading(json.dumps(doc), request,
                              macro_table=_tower_table())
    assert not r.by_kind("macro")
    assert len(r.by_kind("always")) == 1 and len(r.by_kind("bound")) == 1


# ----------------------------------------------------- fixpoint: cycle + bound
def test_cycle_raises_badreading_naming_the_chain():
    table = {
        "cyc_a": {"name": "cyc_a", "params": [],
                  "body": [{"kind": "macro", "name": "cyc_b", "args": {}}]},
        "cyc_b": {"name": "cyc_b", "params": [],
                  "body": [{"kind": "macro", "name": "cyc_a", "args": {}}]},
    }
    with pytest.raises(BadReading, match="did not reach a fixpoint"):
        _expand_macros([_inv("s1", "cyc_a", {})], table)


def test_depth_bound_raises_and_a_wider_bound_expands():
    # a linear (acyclic) chain DEEPER than the bound: m19 -> m18 -> ... -> m0
    table = {"m0": {"name": "m0", "params": [],
                    "body": [{"kind": "order", "first": "a1", "then": "a2"}]}}
    for i in range(1, 20):
        table[f"m{i}"] = {
            "name": f"m{i}", "params": [],
            "body": [{"kind": "macro", "name": f"m{i-1}", "args": {}}]}
    stmts = [_inv("s1", "m19", {})]
    with pytest.raises(BadReading, match="within depth 16"):
        _expand_macros(list(stmts), table)
    got = _expand_macros(list(stmts), table, depth_bound=32)
    assert [s["lf"]["kind"] for s in got] == ["order"]


# ======================================================== recode-then-mine (B)
# Admitted macro A abbreviates a [quantity, always] pair; candidate B is a
# level-2 tower whose body INVOKES A and appends an effect.  B's uses are only
# visible once the corpus is recoded with A.
_PRICE_A = {"name": "a_pair", "params": ["q"], "body": [
    {"kind": "quantity", "name": "$q", "min": 0, "max": 10},
    {"kind": "always", "pred": {"op": ">=", "left": "$q", "right": 0}}]}
_PRICE_B = {"name": "b_tower", "params": ["q"], "body": [
    {"kind": "macro", "name": "a_pair", "args": {"q": "$q"}},
    {"kind": "effect", "action": "sell", "quantity": "$q",
     "op": "dec", "amount": {"arg": "n"}}]}


def _tower_corpus():
    out = []
    for i, q in enumerate(("stock", "seats", "units", "slots")):
        out.append({"service": f"r{i}", "statements": [
            {"id": f"r{i}s0", "force": "demand", "quote": "s",
             "lf": {"kind": "quantity", "name": q, "min": 0, "max": 10}},
            {"id": f"r{i}s1", "force": "demand", "quote": "s",
             "lf": {"kind": "always",
                    "pred": {"op": ">=", "left": q, "right": 0}}},
            {"id": f"r{i}s2", "force": "demand", "quote": "s",
             "lf": {"kind": "effect", "action": "sell", "quantity": q,
                    "op": "dec", "amount": {"arg": "n"}}}]})
    return out


def _historical_raw_uses(readings, table):
    """The PRE-D2 pricer's matching, reimplemented verbatim as the before/after
    reference: ONE greedy longest-body-first pass over the RAW statement
    stream.  A tower body (invocation templates) can never unify with raw
    concrete statements here -- the uses=0-forever fact this file documents."""
    macros = sorted(table.values(), key=lambda m: (-len(m["body"]), m["name"]))
    uses = {name: 0 for name in table}
    for r in readings:
        stmts, used, i = r["statements"], set(), 0
        while i < len(stmts):
            hit = next((m for m in macros
                        if mdl_macros._match_at(stmts, i, m) is not None), None)
            if hit is not None:
                used.add(hit["name"])
                i += len(hit["body"])
            else:
                i += 1
        for name in used:
            uses[name] += 1
    return uses


def test_level2_candidate_prices_with_uses_after_recode():
    corpus = _tower_corpus()
    # BEFORE (the historical raw matching): B is invisible even WITH A admitted
    raw = _historical_raw_uses(corpus, {"a_pair": _PRICE_A,
                                        "b_tower": _PRICE_B})
    assert raw["b_tower"] == 0                      # uses=0 forever, pre-fix
    assert raw["a_pair"] == 4
    # AFTER (recode-then-mine): B matches the recoded stream in every reading
    d = macro_admission_decision(corpus, _PRICE_B, {"a_pair": _PRICE_A})
    assert d["uses"] == 4
    assert d["delta"] < 0                           # a real DL improvement
    assert d["admit"] is True
    # the concrete priced numbers, pinned (currency unchanged: these follow
    # from the existing _STMT_BASE/_INVOKE_BASE/_MACRO_BASE constants alone)
    assert (d["dl_before"], d["dl_after"], d["delta"]) == (81.0, 55.0, -26.0)


def test_level2_candidate_is_blind_without_the_vocabulary():
    """With an EMPTY admitted table there is nothing to recode with, so the
    tower body still (correctly) finds no uses -- dependency-closed pricing."""
    d = macro_admission_decision(_tower_corpus(), _PRICE_B, {})
    assert d["uses"] == 0 and d["admit"] is False


def test_admissions_stack_chain_rule():
    """Operator n+1 is priced against operator n's dl_after: the second
    admission's dl_before is BYTE-EQUAL to the first's dl_after (the
    compounding property the audit found missing)."""
    corpus = _tower_corpus()
    d1 = macro_admission_decision(corpus, _PRICE_A, {})
    assert d1["admit"] is True and d1["uses"] == 4
    d2 = macro_admission_decision(corpus, _PRICE_B, {"a_pair": _PRICE_A})
    assert d2["dl_before"] == d1["dl_after"]        # admissions STACK
    assert d2["dl_after"] < d2["dl_before"]
    # and the recoded-corpus DL is what corpus_dl reports for the current table
    assert d2["dl_before"] == round(
        corpus_dl(corpus, {"a_pair": _PRICE_A})["total"], 3)


def test_flat_table_pricing_byte_identical_to_single_pass():
    """The flat-table equivalence pin: for a table with no invocation-bearing
    body, the fixpoint rewrite halts after pass 1 and (total, uses, counts) are
    byte-identical to the historical single-pass pricer, reimplemented here."""
    corpus = fx.trap_corpus()
    table = {"AB": {"name": "AB", "params": [],
                    "body": [dict(fx._LF["A"]), dict(fx._LF["B"])]},
             "CD": {"name": "CD", "params": [],
                    "body": [dict(fx._LF["C"]), dict(fx._LF["D"])]}}
    got = corpus_dl(corpus, table)

    # historical single-pass reference (verbatim pre-D2 _reading_stats)
    macros = sorted(table.values(), key=lambda m: (-len(m["body"]), m["name"]))
    macro_cost = sum(mdl_macros.dl_macro(m) for m in table.values())
    reading_cost, total_stmts = 0.0, 0
    uses = {name: 0 for name in table}
    for r in corpus:
        stmts, used, i = r["statements"], set(), 0
        while i < len(stmts):
            hit = next((m for m in macros
                        if mdl_macros._match_at(stmts, i, m) is not None), None)
            if hit is not None:
                reading_cost += mdl_macros.dl_invocation(
                    len(hit.get("params", [])))
                total_stmts += 1
                used.add(hit["name"])
                i += len(hit["body"])
            else:
                reading_cost += mdl_macros.dl_statement(stmts[i])
                total_stmts += 1
                i += 1
        for name in used:
            uses[name] += 1
    assert got["total"] == macro_cost + reading_cost
    assert got["reading_uses"] == uses
    assert got["total_statements"] == total_stmts


def test_pricing_never_mutates_the_corpus():
    corpus = _tower_corpus()
    before = common.canonical_json(corpus)
    corpus_dl(corpus, {"a_pair": _PRICE_A, "b_tower": _PRICE_B})
    assert common.canonical_json(corpus) == before
