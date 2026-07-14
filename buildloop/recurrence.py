"""Recurrence mining and macro garbage collection (Combined-Loop W3).

Fixed, deterministic, LLM-free code (house rule 5).  This module is the
`recurrence-miss` signal of the miss-typed scheduler: it reads the W0.2 readings
store and proposes reading MACROS for statement clusters that recur across the
corpus.

Two disciplines the plan calls out explicitly:

  * Savings are priced **against the live macro table** (`mdl_macros.corpus_dl`),
    never table-blind.  `mdl_macros._reading_stats` rewrites greedily
    longest-body-first, so a new macro's marginal saving is only the compression
    it adds on top of what already-admitted macros capture -- table-blind mining
    would double-count that.

  * A candidate body is the anti-unification (least general generalization) of
    its occurrences: positions that agree stay literal, positions that differ
    become a `$param`.  `_match_at` requires every parameter to bind, so a body
    that failed to cover a parameter would never be a faithful abbreviation --
    `mine` verifies full coverage before pricing.

Macro GC (W3.3): after a macro is admitted, greedy longest-first rewriting can
strand an older, shorter macro below its two-witness threshold while its
`dl_macro` is still paid every epoch.  `gc_macros` retires any macro under two
uses whose removal STRICTLY reduces `corpus_dl['total']`, as a first-class event.
"""
from __future__ import annotations

import common
from buildloop import mdl_macros

DEFAULT_MAX_LEN = 4          # longest contiguous statement window mined


def _statements(reading) -> list:
    if isinstance(reading, dict):
        return reading.get("statements", [])
    return getattr(reading, "statements", [])


def _demand_windows(reading, max_len: int):
    """Contiguous windows of DEMAND-force statements, lengths 2..max_len.

    A window is admissible only if EVERY statement in it carries
    `force == 'demand'` (the plan mines demand-force clusters); returns the raw
    statement dicts so the caller can read both the LF and the force."""
    stmts = _statements(reading)
    n = len(stmts)
    out = []
    for i in range(n):
        if stmts[i].get("force") != "demand":
            continue
        for L in range(2, max_len + 1):
            if i + L > n:
                break
            if all(stmts[i + k].get("force") == "demand" for k in range(L)):
                out.append(tuple(stmts[i + k] for k in range(L)))
    return out


# --------------------------------------------------------- anti-unification
def _antiunify(values: list, memo: dict, counter: list):
    """Least general generalization of a list of concrete nodes (one per
    occurrence): identical subtrees stay literal; a position that differs
    becomes a parameter `$pN`.  A repeated value-tuple reuses its parameter so
    the generalization stays least-general (deterministic)."""
    first = values[0]
    if all(v == first for v in values[1:]):
        return first                                   # a shared literal
    if all(isinstance(v, dict) for v in values):
        keys = set(values[0])
        if all(set(v) == keys for v in values):
            return {k: _antiunify([v[k] for v in values], memo, counter)
                    for k in sorted(keys)}
    if all(isinstance(v, list) for v in values):
        ln = len(values[0])
        if all(len(v) == ln for v in values):
            return [_antiunify([v[i] for v in values], memo, counter)
                    for i in range(ln)]
    key = common.canonical_json(values)
    if key not in memo:
        memo[key] = "$p%d" % counter[0]
        counter[0] += 1
    return memo[key]


def _antiunify_windows(occurrences: list):
    """`occurrences` is a list of equal-length LF sequences.  Returns
    (body, params): body[j] is the generalization of the j-th LF across all
    occurrences; params is the sorted parameter-name list (no `$`)."""
    width = len(occurrences[0])
    memo: dict = {}
    counter = [0]
    body = [_antiunify([occ[j] for occ in occurrences], memo, counter)
            for j in range(width)]
    params = sorted(name[1:] for name in memo.values())
    return body, params


def _macro_name(body: list) -> str:
    """Deterministic, collision-resistant macro name from its body."""
    return "m_" + common.sha256_json(body)[:12]


def _verifies(candidate: dict, occurrences: list) -> bool:
    """Every occurrence must match the candidate body with all parameters bound
    (the `_match_at` full-coverage rule); otherwise it is not a faithful
    abbreviation."""
    for lfs in occurrences:
        stmts = [{"lf": lf} for lf in lfs]
        if mdl_macros._match_at(stmts, 0, candidate) is None:
            return False
    return True


def mine(readings: list, macro_table: dict = None,
         max_len: int = DEFAULT_MAX_LEN) -> list:
    """Deterministically mine recurrence-macro candidates from `readings`.

    Cluster key = (window length, tuple of LF kinds).  A cluster is a candidate
    iff it occurs in >= 2 readings, its anti-unified body binds every parameter,
    and adding it to the LIVE `macro_table` strictly reduces `corpus_dl`.  Each
    result is {candidate, dl_saving, uses, cluster_key}; sorted by descending
    saving then name (deterministic)."""
    macro_table = macro_table or {}
    clusters: dict = {}
    for ridx, r in enumerate(readings):
        for win in _demand_windows(r, max_len):
            lfs = [mdl_macros._lf_of(s) for s in win]
            if any(not isinstance(lf, dict) for lf in lfs):
                continue
            key = (len(win), tuple(lf.get("kind") for lf in lfs))
            clusters.setdefault(key, []).append((ridx, lfs))

    base_total = mdl_macros.corpus_dl(readings, macro_table)["total"]
    out = []
    for (width, kinds), occ in sorted(clusters.items()):
        if len({ridx for ridx, _ in occ}) < 2:      # >= 2 distinct readings
            continue
        body, params = _antiunify_windows([lfs for _, lfs in occ])
        candidate = {"name": _macro_name(body), "params": params, "body": body}
        if not _verifies(candidate, [lfs for _, lfs in occ]):
            continue
        trial = dict(macro_table)
        trial[candidate["name"]] = candidate
        after = mdl_macros.corpus_dl(readings, trial)
        saving = base_total - after["total"]
        uses = after["reading_uses"].get(candidate["name"], 0)
        if saving > 0 and uses >= 2:
            out.append({"candidate": candidate,
                        "dl_saving": round(saving, 3), "uses": uses,
                        "cluster_key": list(kinds)})
    out.sort(key=lambda c: (-c["dl_saving"], c["candidate"]["name"]))
    return out


# ------------------------------------------------------------------- macro GC
def gc_macros(registry, readings: list) -> list:
    """Retire any live macro under two uses whose removal STRICTLY reduces the
    corpus description length (W3.3).  Runs to a fixpoint, sorted for
    determinism, logging each retirement as a first-class event.  Returns the
    list of retired names."""
    retired = []
    table = registry.macro_table()
    while True:
        stats = mdl_macros.corpus_dl(readings, table)
        uses = stats["reading_uses"]
        victim = None
        for name in sorted(table):
            if uses.get(name, 0) < 2:
                trial = {k: v for k, v in table.items() if k != name}
                if mdl_macros.corpus_dl(readings, trial)["total"] < stats["total"]:
                    victim = name
                    break
        if victim is None:
            break
        registry.macro_retire(victim)
        registry.log_event("macro-retired", {
            "name": victim,
            "reason": "below-two-uses-and-dl-reducing",
            "uses": uses.get(victim, 0),
            "dl_macro": round(mdl_macros.dl_macro(table[victim]), 3)})
        retired.append(victim)
        del table[victim]
    return retired
