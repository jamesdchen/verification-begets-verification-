"""S2 lookahead steering: price a coverage group by a depth-bounded rollout of
hypothetical admissions (Zone 3).

The additive `lookahead` pick_group policy (buildloop.loop.pick_group) minimizes
`rollout_value(generators, backlog, group, depth)` over the candidate coverage
groups.  Where `closure` scores a group by its IMMEDIATE single-generator
coverage gain (a one-step greedy), `lookahead` asks a deeper question: if we
resolve THIS group first -- admit one hypothetical generator covering its
`atoms_union` -- and then optimally admit up to `depth-1` further hypothetical
generators (each covering some still-uncovered ksy coverage group), what is the
LOWEST `ledger_dl` reachable within `depth` admissions?  Because the loop's DL
objective is NON-MONOTONE in the admission count (H19), a group that scores
worse greedily can lead to a strictly cheaper multi-spec world two moves out.

Everything here is pure, deterministic, LLM-free and side-effect-free (house
rule 5).  LOWER is better (a `ledger_dl`, a ledger cost).  All pricing goes
through the ONE live currency and the ONE coverage rule -- never a re-implemented
mirror:

  * coverage: a ksy spec with atoms A is covered by a generator set `gens` iff
    `planner.plan_for_features(gens, "ksy", A, target_language="python-codec")`
    is not None (buildloop.mdl.chain_length_for is verified-divergent legacy and
    is deliberately NOT used);
  * ledger cost: `dl._ledger_total(LedgerSnapshot(...))["ledger_dl"]` over a
    frozen snapshot whose demand rows mirror dl.py's spec-file expectations, so
    an uncovered spec costs `dl.UNCOVERED_PENALTY` and a covered spec costs its
    tier-aware chain cost + size/256.

Only ksy groups are hypothetically priceable: an abnf / json-subset group needs
an LLM-authored payload (a tree-sitter grammar_js) that cannot be conjured
deterministically, so `rollout_value` returns `float("inf")` for them -- they can
never win the `min`.

--- grouping choice (documented per the freeze) --------------------------------
At every rollout state the still-uncovered ksy backlog specs are grouped by their
SMALLEST-MISSING-ATOM signature over the current generator set -- byte-identical
to how `buildloop.loop` forms coverage-miss groups (`group_misses` /
`_coverage_moves`): a spec's missing atoms are its atoms minus the atoms of the
single live generator that already covers the most of them, and specs sharing a
missing signature form one group whose candidate hypothetical covers the union
of the group's atoms.  Each such group contributes exactly one successor
admission.  This is the same grouping the live loop would face on the next
iteration, so the rollout searches over the real move set, not an invented one.
"""
from __future__ import annotations

import planner as planner_mod
from buildloop import dl
from planner.search import beam_search

# The hypothetical is a ksy -> python-codec emitter; only that spec language can
# be priced without an authored payload (H54/H57).
HYP_SPEC_LANGUAGE = "ksy"
HYP_TARGET_LANGUAGE = "python-codec"
DEFAULT_BEAM_WIDTH = 4


def _atoms_key(atoms) -> tuple:
    """Canonical (sorted, de-duplicated) signature of an atom-set."""
    return tuple(sorted(set(atoms)))


def hypothetical_generator(atoms) -> dict:
    """The generator that would cover a set of ksy atoms `atoms` if admitted
    (H54/H57 pin).  `authored_bytes: 0` is REQUIRED -- a real admission stamps
    that field, and omitting it would underprice the eventual real entry."""
    a = sorted(set(atoms))
    return {
        "name": "hyp:" + ",".join(a),
        "spec_language": HYP_SPEC_LANGUAGE,
        "output_language": HYP_TARGET_LANGUAGE,
        "spec_grammar": {"atoms": a},
        "emit_entrypoint": {"kind": "ksc-python-rw", "authored_bytes": 0},
        "contract": {"type": "codec-roundtrip"},
        "provenance": {"author": "lookahead-hypothetical"},
    }


def _demand_row(spec: dict) -> dict:
    """A spec-file demand row mirroring dl.py's expectations, so an uncovered
    spec prices at dl.UNCOVERED_PENALTY and a covered one at chain-cost +
    size/256 (the exact live `_demand_cost` path)."""
    return {
        "demand_id": spec.get("path") or spec.get("demand_id") or "",
        "kind": "spec-file",
        "origin": "exogenous",
        "status": "open",
        "language": spec["language"],
        "features": sorted(spec["atoms"]),
        "payload_ref": spec.get("path"),
        "size_bytes": spec.get("size_bytes", 0),
        "covered_via": None,
    }


def _is_covered(gens, spec) -> bool:
    """The ONE coverage rule (never a re-implemented mirror)."""
    return planner_mod.plan_for_features(
        gens, spec["language"], sorted(spec["atoms"]),
        target_language=HYP_TARGET_LANGUAGE) is not None


def _smallest_missing(gens, language, atoms):
    """Smallest uncovered remainder of `atoms` over any single live generator of
    the language -- identical to CoverageMiss.missing_atoms / loop._missing_atoms
    (the grouping key)."""
    best = set(atoms)
    for g in gens:
        if g.get("spec_language") != language:
            continue
        rem = set(atoms) - set(g.get("spec_grammar", {}).get("atoms", []))
        if len(rem) < len(best):
            best = rem
    return best


def _coverage_groups(gens, ksy_specs):
    """Group still-uncovered ksy specs by smallest-missing-atom signature (the
    documented grouping; mirrors buildloop.loop).  Returns a list of atom-set
    keys (sorted tuples of the group's atoms_union), deterministic order."""
    groups = {}
    for s in ksy_specs:
        if _is_covered(gens, s):
            continue
        missing = _smallest_missing(gens, s["language"], s["atoms"])
        key = tuple(sorted(missing))
        groups.setdefault(key, set()).update(s["atoms"])
    return sorted(_atoms_key(union) for union in groups.values())


def rollout_value(generators, backlog, group, depth) -> float:
    """Depth-bounded rollout cost of resolving `group` first.  LOWER is better.

    Returns the LOWEST `ledger_dl` reachable within `depth` hypothetical
    admissions, the FIRST of which is FORCED to be a generator covering
    `group["atoms_union"]`, and each subsequent one covering some still-uncovered
    ksy coverage group (grouped as documented in the module docstring).  The
    search is `planner.search.beam_search` over admission SEQUENCES; it returns
    the best state EVER VISITED (not just leaves), because the objective is
    non-monotone in the admission count.

    `float("inf")` for a non-ksy group: an abnf / json-subset group needs an
    LLM-authored payload and cannot be hypothetically priced.
    """
    if group.get("language") != HYP_SPEC_LANGUAGE:
        return float("inf")

    base_gens = list(generators)
    # Price EVERY backlog spec (faithful "price the backlog"); non-ksy rows stay
    # uncovered at a constant penalty, so they never affect the argmin.
    demand = [_demand_row(s) for s in backlog]
    ksy_specs = [s for s in backlog if s["language"] == HYP_SPEC_LANGUAGE]

    def _gens_for(state):
        return base_gens + [hypothetical_generator(a) for a in state]

    def _snapshot(state):
        return dl.LedgerSnapshot(
            generators=_gens_for(state), demand=demand,
            macro_table={}, toll_calls={}, readings={})

    def score(state):
        # state is a tuple of atom-set signatures (each a tuple of atoms).
        return dl._ledger_total(_snapshot(state))["ledger_dl"]

    def expand(state):
        gens = _gens_for(state)
        succ = []
        for key in _coverage_groups(gens, ksy_specs):
            if key in state:
                continue
            succ.append(tuple(sorted(set(state) | {key})))
        return succ

    # Force the first admission to be THIS group's hypothetical, then let the
    # beam search spend the remaining depth-1 admissions.
    forced = (_atoms_key(group["atoms_union"]),)
    max_depth = max(0, int(depth) - 1)
    best = beam_search(forced, expand, score,
                       beam_width=DEFAULT_BEAM_WIDTH, max_depth=max_depth)
    return float(score(best))
