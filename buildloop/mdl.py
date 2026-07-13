"""Minimum-description-length accounting (library compression discipline).

DL(library, backlog) =
    sum over live generators of  |canonical generator description| / 64
  + sum over backlog specs of    chain_length + |spec bytes| / 256   if covered
                                 UNCOVERED_PENALTY                    otherwise

A candidate is admitted only if it reduces total DL, except when it newly
covers previously unreachable specs (an *expansion event*, logged as such).
When a new generator's coverage subsumes a live entry, that entry is
retired (kept for provenance, excluded from planning).
"""
from __future__ import annotations

import common

UNCOVERED_PENALTY = 50.0


def _covers(gen, language, atoms) -> bool:
    return (gen["spec_language"] == language
            and set(atoms) <= set(gen["spec_grammar"]["atoms"]))


def chain_length_for(generators, language, atoms):
    """Mirror of the planner's coverage rule (kept deliberately tiny):
    returns the shortest chain length covering (language, atoms), or None."""
    best = None
    for g in generators:
        if _covers(g, language, atoms) and g["output_language"] == "python-codec":
            best = 1 if best is None else min(best, 1)
    if best == 1:
        return 1
    for g1 in generators:
        if not _covers(g1, language, atoms):
            continue
        out = g1["spec_grammar"].get("output")
        if not out:
            continue
        for g2 in generators:
            if g2["output_language"] == "python-codec" and _covers(
                    g2, out["language"], out["atoms"]):
                return 2
    return best


def generator_dl(gen_like) -> float:
    body = common.canonical_json({
        "spec_grammar": gen_like["spec_grammar"],
        "emit_entrypoint": gen_like["emit_entrypoint"]})
    return len(body) / 64.0


def total_dl(generators, backlog) -> dict:
    """backlog: list of {path, language, atoms, size_bytes}."""
    gen_cost = sum(generator_dl(g) for g in generators)
    spec_cost, covered = 0.0, 0
    for s in backlog:
        cl = chain_length_for(generators, s["language"], s["atoms"])
        if cl is None:
            spec_cost += UNCOVERED_PENALTY
        else:
            covered += 1
            spec_cost += cl + s["size_bytes"] / 256.0
    return {"total": gen_cost + spec_cost, "generator_cost": gen_cost,
            "spec_cost": spec_cost, "covered": covered, "n": len(backlog)}


def admission_decision(live_generators, candidate, backlog) -> dict:
    """MDL gate.  candidate is a dict with spec_grammar/emit_entrypoint/
    spec_language/output_language fields (not yet registered)."""
    before = total_dl(live_generators, backlog)
    after = total_dl(live_generators + [candidate], backlog)
    newly = after["covered"] - before["covered"]
    admit = after["total"] < before["total"]
    expansion = False
    if not admit and newly > 0:
        admit, expansion = True, True
    return {"admit": admit, "expansion": expansion,
            "dl_before": round(before["total"], 3),
            "dl_after": round(after["total"], 3),
            "newly_covered": newly,
            "covered_before": before["covered"],
            "covered_after": after["covered"]}


def find_subsumed(live_generators, new_gen) -> list:
    """Live entries whose grammar (and role) the new generator strictly
    contains -- retire them."""
    out = []
    for g in live_generators:
        if g["generator_hash"] == new_gen["generator_hash"]:
            continue
        if (g["spec_language"] == new_gen["spec_language"]
                and g["output_language"] == new_gen["output_language"]
                and g["spec_grammar"].get("output") ==
                    new_gen["spec_grammar"].get("output")
                and set(g["spec_grammar"]["atoms"]) <
                    set(new_gen["spec_grammar"]["atoms"])
                and g["tier"] != "universal"):
            out.append(g)
    return out
