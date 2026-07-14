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


# --------------------------------------------------------------- pricing
def generator_dl(gen_like: dict) -> float:
    """Price the FULL authored artifact (fact 6): the canonical generator body
    PLUS any LLM-authored payload (a tree-sitter `grammar_js`, up to 20 KB) that
    the legacy series popped before pricing.  Unpriced authored content is how an
    overbroad grammar sneaks in cheap; here it is always paid for."""
    body = common.canonical_json({
        "spec_grammar": gen_like.get("spec_grammar", {}),
        "emit_entrypoint": gen_like.get("emit_entrypoint", {})})
    payload = (gen_like.get("_grammar_js")
               or gen_like.get("grammar_js")
               or gen_like.get("emit_entrypoint", {}).get("grammar_js")
               or gen_like.get("payload") or "")
    return len(body) / 64.0 + len(payload or "") / 64.0


def dl_reading(reading, macro_table: dict) -> float:
    """DL of one certified Reading, given the macros available to abbreviate it
    (reuses the P5.2 token proxy; a matched macro window collapses to one cheap
    invocation)."""
    return mdl_macros.dl_reading(reading, macro_table or {})


def incumbent_hash_of(row: dict) -> str:
    """Stable identity of a caged incumbent: the sha256 of its source bytes if
    the payload is on disk (what the cage hashes at task time), else the sha256
    of the payload reference string.  The toll counter is keyed
    `toll:{incumbent_hash}:calls`."""
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
        return common.sha256_json({
            "generators": sorted(g.get("generator_hash", "")
                                 for g in self.generators),
            "demand": sorted((r["demand_id"], r["status"])
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
    readings = {}
    for rd in registry.readings_all():
        try:
            readings[rd["demand_id"]] = json.loads(rd["reading_json"])
        except (ValueError, TypeError):
            continue
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
    return None if chain is None else float(len(chain))


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
    if kind == "caged-incumbent":
        if row["status"] == "converted":
            # priced as its replacement spec plus, during retention, a capped
            # monitor toll -- the right-hand side of the single conversion
            # formula (W4.2b); the replacement chain cost rides payload_ref.
            calls = snap.toll_calls.get(incumbent_hash_of(row), 0.0)
            return min(MONITOR_RATE * calls, MONITOR_CAP)
        calls = snap.toll_calls.get(incumbent_hash_of(row), 0.0)
        return toll_stock(calls)
    return 0.0


def _ledger_total(snap: LedgerSnapshot) -> dict:
    gen_cost = sum(generator_dl(g) for g in snap.generators)
    covered_spec = covered_request = 0
    total_spec = total_request = total_incumbent = 0
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
    return {"ledger_dl": gen_cost + demand_cost,
            "generator_cost": gen_cost, "demand_cost": demand_cost,
            "covered_spec": covered_spec, "total_spec": total_spec,
            "covered_request": covered_request, "total_request": total_request,
            "total_incumbent": total_incumbent}


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
    post = (replacement_chain_cost + replacement_size / 256.0
            + delta_generator_dl + min(MONITOR_RATE * calls, MONITOR_CAP))
    return {"admit": stock > post,
            "toll_stock": round(stock, 3), "post_cost": round(post, 3),
            "calls": calls}
