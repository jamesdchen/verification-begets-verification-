"""The one currency and the one gate (Combined-Loop W0.3).

Every demand kind is priced in ONE unit, `ledger_dl`, and every move is admitted
through ONE gate: admit iff `ledger_dl` strictly drops, with two bounded,
separately-logged exceptions that are NEVER counted as a DL win (an *expansion*
that newly covers exogenous demand nothing cheaper covers, and the single
conversion formula shared with the W4.2b post-state pricing).

This module is the deliberate successor of the legacy codec-only `buildloop.mdl`
series, which is FROZEN (fact: two same-named `total_dl` metrics must not
coexist -- the loop switches to `ledger_dl` here, a logged semantics change).
`plan_for_features` (planner) is the single chain-cost source; no re-implemented
mirror of the coverage rule lives here.

All pricing is over a FROZEN snapshot (house rule 13): `wall_ms` and any
wall-clock value are reporting-only and never enter DL, scores, or tie-breaks.
Everything here is fixed, deterministic, LLM-free code (house rule 5).
"""
from __future__ import annotations

import dataclasses
import json
import pathlib

import common
import planner as planner_mod
from buildloop import mdl_macros

# --- policy constants (by-fiat inputs to admission; named in TRUST.md) -------
UNCOVERED_PENALTY = 50.0        # finite, capped penalty for unserved demand
READING_CHAIN_COST = 2.0        # nl-request compile-chain cost until W2.3
                                # registers the reading language as a real chain
TOLL_RATE = 0.05                # ledger_dl per ingested task-time call
HORIZON_H = 1000                # toll horizon, unit = sync epochs (never
                                # wall-clock -- house rule 13)
MONITOR_RATE = 0.01             # retention-monitor cost per call after a
                                # conversion
MONITOR_CAP = 25.0              # capped so converting a high-traffic incumbent
                                # can never be ledger_dl-increasing
# ratio rule: a retained monitor must be strictly cheaper than the toll it
# replaces, or conversion could never pay.
assert MONITOR_RATE <= TOLL_RATE / 2

# --- tier-aware chain cost (§0 lattice: a universal link is marginal-cost ~0)
# A chain's cost is the sum of its per-link marginal costs.  A `universal` link
# was paid for once at promotion and is free forever; every other tier
# (emit-check, conformance-relative, ...) is paid per emission.  The ratio must
# make a LONGER all-universal chain strictly cheaper than a SHORTER chain that
# still contains one non-universal link, so the promotion move (emit-check ->
# universal) STRICTLY reduces ledger_dl instead of being self-defeating.
UNIVERSAL_LINK_COST = 0.0       # paid once at promotion; zero marginal cost
EMIT_CHECK_LINK_COST = 1.0      # any non-universal link: paid at every build
# any number of universal links (cost 0) is strictly cheaper than one non-
# universal link (cost 1.0), so promotion can only lower the ledger.
assert UNIVERSAL_LINK_COST < EMIT_CHECK_LINK_COST


def _link_cost(link) -> float:
    """Marginal cost of one chain link, by tier (§0 lattice)."""
    return (UNIVERSAL_LINK_COST if link.get("tier") == "universal"
            else EMIT_CHECK_LINK_COST)


# --------------------------------------------------------------- pricing
def generator_dl(gen_like: dict) -> float:
    """Price the FULL authored artifact (fact 6): the canonical generator body
    PLUS any LLM-authored payload (a tree-sitter `grammar_js`, up to 20 KB) that
    the legacy series popped before pricing.  Unpriced authored content is how an
    overbroad grammar sneaks in cheap; here it is always paid for."""
    emit = gen_like.get("emit_entrypoint", {})
    body = common.canonical_json({
        "spec_grammar": gen_like.get("spec_grammar", {}),
        "emit_entrypoint": emit})
    # A live pre-admission candidate still carries the payload inline; a PERSISTED
    # generator has had it popped (admission.py) and instead records its authored
    # LENGTH as emit_entrypoint["authored_bytes"].  Pay for whichever is present
    # so an overbroad grammar can never sneak in cheap on the persisted path.
    payload = (gen_like.get("_grammar_js")
               or gen_like.get("grammar_js")
               or emit.get("grammar_js")
               or gen_like.get("payload") or "")
    authored = float(emit.get("authored_bytes", 0) or 0)
    return len(body) / 64.0 + len(payload or "") / 64.0 + authored / 64.0


def dl_reading(reading, macro_table: dict) -> float:
    """DL of one certified Reading, given the macros available to abbreviate it
    (reuses the P5.2 token proxy; a matched macro window collapses to one cheap
    invocation)."""
    return mdl_macros.dl_reading(reading, macro_table or {})


def _statements_view(reading):
    """Normalize a persisted reading dict to one carrying a top-level
    `statements` list, so `mdl_macros.dl_reading` -- generic over statement dicts
    (each `{id,force,quote,lf}`) -- prices it unchanged.  The nl-request seed
    persists the flattened `{service, statements}` shape; a MathReading (F-A)
    may be persisted as the envelope `{source, reading:{theorem, statements}}`.
    Accept both, so pricing does not depend on which shape WP-H's certify-at-seed
    lands.  A dict already carrying `statements` (or a non-dict) passes through
    untouched, so nl-request pricing is byte-identical."""
    if isinstance(reading, dict) and "statements" not in reading:
        inner = reading.get("reading")
        if isinstance(inner, dict) and "statements" in inner:
            return inner
    return reading


def incumbent_hash_of(row: dict) -> str:
    """Stable identity of a caged incumbent: the sha256 of its source bytes if
    the payload is on disk (what the cage hashes at task time), else the sha256
    of the payload reference string.  The toll counter is keyed
    `toll:{incumbent_hash}:calls`.

    A CONVERTED row's payload_ref points at the replacement, not the incumbent,
    so conversion stashes the original incumbent hash in `features`
    (`{"incumbent_hash": ...}`); honor it here so the retained-monitor toll of a
    converted incumbent still keys to the original's ingested calls."""
    feats = row.get("features")
    if isinstance(feats, dict) and feats.get("incumbent_hash"):
        return feats["incumbent_hash"]
    ref = row.get("payload_ref") or row.get("demand_id") or ""
    p = common.REPO_ROOT / ref if ref else None
    if p is not None and p.exists() and p.is_file():
        return common.sha256_bytes(p.read_bytes())
    return common.sha256_bytes(str(ref).encode())


def toll_stock(calls: float) -> float:
    """Capped toll pressure a caged incumbent contributes.  Uncapped, a
    high-traffic toll made *un-serving* demand optimal (the v1 defect); the cap
    at UNCOVERED_PENALTY guarantees caging is never worse than leaving demand
    uncovered."""
    horizoned = min(float(calls), float(HORIZON_H))
    return min(TOLL_RATE * horizoned, UNCOVERED_PENALTY)


# --------------------------------------------------------------- snapshot
@dataclasses.dataclass
class LedgerSnapshot:
    """A frozen view read at iteration start (house rule 13).  Two runs over the
    same snapshot produce byte-identical pricing and ranked-move logs."""
    generators: list
    demand: list
    macro_table: dict
    toll_calls: dict          # incumbent_hash -> ingested-call count
    readings: dict            # demand_id -> parsed reading dict

    def snapshot_hash(self) -> str:
        # Two snapshots that PRICE differently must HASH differently.  Pricing
        # depends on more than generator identity + (demand_id, status): the
        # generator TIER drives chain cost (a universal link is ~0) and is NOT in
        # generator_hash; and a spec-file row's cost is chain(features) +
        # size_bytes/256, keyed by (language, features, size_bytes, kind).  Fold
        # them all in, alongside the macro table and toll calls.
        return common.sha256_json({
            "generators": sorted((g.get("generator_hash", ""),
                                  g.get("tier", ""))
                                 for g in self.generators),
            "demand": sorted((r["demand_id"], r["status"],
                              r.get("language") or "",
                              list(r.get("features") or ()),
                              float(r.get("size_bytes") or 0),
                              r["kind"])
                             for r in self.demand),
            "macros": sorted(self.macro_table),
            "toll": sorted(self.toll_calls.items()),
            "readings": sorted(self.readings)})


def snapshot(registry) -> LedgerSnapshot:
    demand = registry.demand_all()
    toll = {}
    for r in demand:
        if r["kind"] == "caged-incumbent":
            ih = incumbent_hash_of(r)
            toll[ih] = registry.counter_get(f"toll:{ih}:calls")
    # Join the demand ledger's provenance onto each reading (Zone 3 S5): the
    # readings table has no origin column -- origin lives on the demand row --
    # so attach it here as a derived `origin` key so the witness filter can tell
    # real (exogenous) readings from dreams (system) on the LIVE path, not only
    # in tagged-dict tests.  Pricing (corpus_dl / dl_reading) reads only
    # `statements`, so the extra key is inert, and snapshot_hash folds reading
    # KEYS only, so the hash is unchanged (byte-identical).
    origin_by_id = {r["demand_id"]: r.get("origin") for r in demand}
    readings = {}
    for rd in registry.readings_all():
        try:
            parsed = json.loads(rd["reading_json"])
        except (ValueError, TypeError):
            continue
        did = rd["demand_id"]
        if isinstance(parsed, dict) and did in origin_by_id:
            parsed = {**parsed, "origin": origin_by_id[did]}
        readings[did] = parsed
    return LedgerSnapshot(
        generators=registry.live_generators(),
        demand=demand,
        macro_table=registry.macro_table(),
        toll_calls=toll,
        readings=readings)


# ------------------------------------------------------- coverage helpers
def _spec_target(row) -> str:
    """Demand-kind -> chain target language (pinned in W0.1)."""
    return "python-service" if row["kind"] == "nl-request" else "python-codec"


def _covered_spec_ids(generators, demand) -> set:
    out = set()
    for r in demand:
        if r["kind"] != "spec-file" or r["status"] == "retired":
            continue
        lang, feats = r.get("language"), r.get("features")
        if not lang or not feats:
            continue
        chain = planner_mod.plan_for_features(
            generators, lang, feats, target_language="python-codec")
        if chain is not None:
            out.add(r["demand_id"])
    return out


def _chain_cost(generators, row) -> float | None:
    lang, feats = row.get("language"), row.get("features")
    if not lang or not feats:
        return None
    chain = planner_mod.plan_for_features(
        generators, lang, feats, target_language="python-codec")
    if chain is None:
        return None
    # tier-aware (M3): a universal link is marginal-cost ~0, so promoting a link
    # to universal makes an all-universal chain strictly cheaper than any chain
    # containing an emit-check link -- the promotion move lowers ledger_dl.
    return sum(_link_cost(l) for l in chain)


# ------------------------------------------ the single conversion formula
def _conversion_post_cost(replacement_chain_cost: float, replacement_size: float,
                          delta_generator_dl: float, calls: float) -> float:
    """The ONE post-conversion cost (W0.3), shared by the conversion GATE
    (`conversion_admissible`) and the LEDGER pricing of a 'converted' row
    (`_demand_cost`).  Factoring it into a single helper is what stops the two
    from silently diverging (a fact-2 mirror hazard):

        replacement_chain_cost + replacement_size/256 + Δgenerator_dl
            + min(MONITOR_RATE × calls, MONITOR_CAP)
    """
    return (replacement_chain_cost + replacement_size / 256.0
            + delta_generator_dl + min(MONITOR_RATE * calls, MONITOR_CAP))


def _converted_replacement_terms(row) -> tuple:
    """A converted caged-incumbent row carries the replacement it was lifted to,
    so ledger pricing can reuse the EXACT conversion-gate formula.  W4.2b writes
    these fields at conversion time; when absent (no converted rows exist yet in
    W0) they default to zero, leaving only the capped retention monitor -- but
    through the identical code path, so it cannot drift from the gate."""
    return (float(row.get("replacement_chain_cost") or 0.0),
            float(row.get("replacement_size") or 0.0),
            float(row.get("delta_generator_dl") or 0.0))


# --------------------------------------------------------- the currency
def _demand_cost(row, snap: LedgerSnapshot) -> float:
    kind = row["kind"]
    if row["status"] == "retired":
        return 0.0
    if kind == "spec-file":
        cc = _chain_cost(snap.generators, row)
        if cc is None:
            return UNCOVERED_PENALTY
        return cc + (row.get("size_bytes") or 0) / 256.0
    if kind == "nl-request":
        reading = snap.readings.get(row["demand_id"])
        if reading is None:
            return UNCOVERED_PENALTY
        return READING_CHAIN_COST + dl_reading(reading, snap.macro_table)
    if kind == "math-source":
        # F3.1: served (a certified MathReading is present -> the row is covered)
        # is priced on the nl-request shape; the DL is generic over statement
        # dicts.  Unserved: E3 -- a system-origin row is a DREAM (dreams propose,
        # they must NOT bill), so it prices at 0; an exogenous row pays the cap.
        reading = snap.readings.get(row["demand_id"])
        if reading is not None:
            return READING_CHAIN_COST + dl_reading(
                _statements_view(reading), snap.macro_table)
        if row.get("origin") == "system":
            return 0.0
        return UNCOVERED_PENALTY
    if kind == "caged-incumbent":
        if row["status"] == "converted":
            # priced by the SINGLE conversion formula (W4.2b right-hand side),
            # the exact code path `conversion_admissible` uses -- replacement
            # chain + replacement_size/256 + Δgen + a capped retention monitor.
            calls = snap.toll_calls.get(incumbent_hash_of(row), 0.0)
            rc, rs, dg = _converted_replacement_terms(row)
            return _conversion_post_cost(rc, rs, dg, calls)
        calls = snap.toll_calls.get(incumbent_hash_of(row), 0.0)
        return toll_stock(calls)
    # A6: every kind must be priced explicitly.  A silent 0.0 fallback let a new
    # demand kind (e.g. 'math-source' before its branch existed) enter the ledger
    # free -- a systematic under-count nothing would flag.  Fail loud instead.
    raise ValueError(f"unknown demand kind {kind!r}")


def _ledger_total(snap: LedgerSnapshot) -> dict:
    gen_cost = sum(generator_dl(g) for g in snap.generators)
    # Macro-definition cost (Zone 3, S1.7 / H49).  `mine` gates a macro on
    # `mdl_macros.corpus_dl`, which charges `dl_macro` for the stored definition;
    # the ledger charged nothing, so a macro admission's realized `ledger_dl`
    # drop systematically BEAT the expected saving by exactly `dl_macro`.  Pay
    # for every live macro definition here so the search objective (corpus_dl)
    # and the ledger agree.  Empty table -> 0.0, so a macro-free ledger is
    # byte-identical to before.
    macro_cost = sum(mdl_macros.dl_macro(m) for m in snap.macro_table.values())
    covered_spec = covered_request = covered_math = 0
    total_spec = total_request = total_incumbent = total_math = 0
    dream_rows = 0            # E3: unserved system-origin math rows (dreams),
                             # priced at 0 and reported separately from covered
    demand_cost = 0.0
    for r in snap.demand:
        demand_cost += _demand_cost(r, snap)
        if r["kind"] == "spec-file":
            total_spec += 1
            if _chain_cost(snap.generators, r) is not None:
                covered_spec += 1
        elif r["kind"] == "nl-request":
            total_request += 1
            if snap.readings.get(r["demand_id"]) is not None:
                covered_request += 1
        elif r["kind"] == "caged-incumbent":
            total_incumbent += 1
        elif r["kind"] == "math-source":
            total_math += 1
            if snap.readings.get(r["demand_id"]) is not None:
                covered_math += 1        # covered iff a MathReading is present
            elif r.get("origin") == "system":
                dream_rows += 1          # unserved dream -> zero-priced (E3)
    return {"ledger_dl": gen_cost + demand_cost + macro_cost,
            "generator_cost": gen_cost, "demand_cost": demand_cost,
            "macro_cost": macro_cost,
            "covered_spec": covered_spec, "total_spec": total_spec,
            "covered_request": covered_request, "total_request": total_request,
            "total_incumbent": total_incumbent,
            "covered_math": covered_math, "total_math": total_math,
            "dream_rows": dream_rows}


def ledger_dl(registry) -> dict:
    """The `ledger_dl` of the whole ledger, read from a fresh snapshot."""
    return _ledger_total(snapshot(registry))


# --------------------------------------------------------------- the gate
def _with(snap: LedgerSnapshot, candidate: dict) -> LedgerSnapshot:
    c = dict(candidate)
    c.setdefault("tier", "emit-check")
    if not c.get("generator_hash"):
        c["generator_hash"] = planner_mod._hash_entry(c)
    return dataclasses.replace(snap, generators=snap.generators + [c])


def admission_decision(snap: LedgerSnapshot, candidate: dict, *,
                       alternatives=()) -> dict:
    """The one gate.  Admit `candidate` (a generator) iff `ledger_dl` strictly
    drops.  Bounded exceptions, each its OWN logged outcome, never a DL win:

      * expansion -- admit a DL-inflating candidate ONLY if it newly covers
        EXOGENOUS demand AND no already-admissible alternative covers the same
        rows (system-origin rewrites can never trigger it; exogeneity rule).

    `alternatives` are other candidate generators the caller has in hand that
    could cover the same rows more cheaply.
    """
    before = _ledger_total(snap)
    after = _ledger_total(_with(snap, candidate))
    admit = after["ledger_dl"] < before["ledger_dl"]

    before_ids = _covered_spec_ids(snap.generators, snap.demand)
    after_ids = _covered_spec_ids(_with(snap, candidate).generators, snap.demand)
    newly_ids = after_ids - before_ids
    exo_by_id = {r["demand_id"]: r for r in snap.demand}
    exo_newly = {i for i in newly_ids
                 if exo_by_id.get(i, {}).get("origin") == "exogenous"}
    system_newly = newly_ids - exo_newly

    expansion = False
    blocked_by = None
    if not admit and newly_ids:
        if exo_newly:
            for alt in alternatives:
                alt_snap = _with(snap, alt)
                if _ledger_total(alt_snap)["ledger_dl"] < before["ledger_dl"]:
                    alt_ids = _covered_spec_ids(alt_snap.generators, snap.demand)
                    if exo_newly <= alt_ids:
                        blocked_by = planner_mod._hash_entry(dict(alt))
                        break
            if blocked_by is None:
                admit, expansion = True, True
    return {
        "admit": admit, "expansion": expansion,
        "dl_before": round(before["ledger_dl"], 3),
        "dl_after": round(after["ledger_dl"], 3),
        "newly_covered": sorted(newly_ids),
        "exogenous_newly_covered": sorted(exo_newly),
        "system_newly_covered": sorted(system_newly),
        "blocked_by_cheaper_alternative": blocked_by,
    }


def conversion_admissible(snap: LedgerSnapshot, incumbent_row: dict, *,
                          replacement_chain_cost: float,
                          replacement_size: int,
                          delta_generator_dl: float) -> dict:
    """The SINGLE conversion admissibility formula (W0.3), identical to the
    W4.2b post-state pricing.  Admit iff the capped toll stock exceeds the full
    post-conversion cost:

        min(TOLL_STOCK, UNCOVERED_PENALTY) >
            replacement_chain_cost + replacement_size/256 + Δgenerator_dl
            + min(MONITOR_RATE × calls, MONITOR_CAP)

    A cheap-to-run incumbent honestly stays caged.  This is here (not W4) so the
    formula has exactly one home.
    """
    calls = snap.toll_calls.get(incumbent_hash_of(incumbent_row), 0.0)
    stock = toll_stock(calls)
    post = _conversion_post_cost(replacement_chain_cost, replacement_size,
                                 delta_generator_dl, calls)
    return {"admit": stock > post,
            "toll_stock": round(stock, 3), "post_cost": round(post, 3),
            "calls": calls}
