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
from planner import search

DEFAULT_MAX_LEN = 4          # longest contiguous statement window mined

# H3: a candidate body template must be at least this fraction concrete (non-
# placeholder) leaves, and no body statement may be a bare placeholder.  The
# live gate would otherwise admit the pure wildcard body `["$p0","$p1"]` on an
# all-distinct corpus (dl_invocation prices args size-blind), minting a "macro"
# that abbreviates nothing realizable.
MIN_CONCRETE_FRACTION = 0.6


def _statements(reading) -> list:
    if isinstance(reading, dict):
        return reading.get("statements", [])
    return getattr(reading, "statements", [])


def _demand_windows(reading, max_len: int):
    """Contiguous windows of UNIFORM (force, quote) statements, lengths 2..max_len.

    H2: the old restriction was demand-force ONLY.  A macro invocation expands to
    statements that ALL inherit the invocation's single force AND quote
    (reading._expand_one), so a window whose statements disagree on force or quote
    "compresses" in the DL arithmetic yet is UNREALIZABLE as a legal invocation
    (a demand must quote a span, a choice must quote nothing --
    reading.parse_reading).  Mining uniform-(force, quote) windows is therefore
    both the honesty rule and what makes presupposition clusters and S3's
    choice-tail idiom mineable.  Returns the raw statement dicts so the caller can
    read both the LF and the force."""
    stmts = _statements(reading)
    n = len(stmts)
    out = []
    for i in range(n):
        force_i, quote_i = stmts[i].get("force"), stmts[i].get("quote", "")
        for L in range(2, max_len + 1):
            if i + L > n:
                break
            if all(stmts[i + k].get("force") == force_i
                   and stmts[i + k].get("quote", "") == quote_i
                   for k in range(L)):
                out.append(tuple(stmts[i + k] for k in range(L)))
    return out


def _leaf_concreteness(template) -> tuple:
    """(concrete_leaves, total_leaves) of one body template: a scalar leaf is
    concrete unless it is a `$param` placeholder string; dict/list structure
    recurses.  Used by the H3 filter."""
    if isinstance(template, dict):
        c = t = 0
        for v in template.values():
            cc, tt = _leaf_concreteness(v)
            c += cc
            t += tt
        return c, t
    if isinstance(template, list):
        c = t = 0
        for v in template:
            cc, tt = _leaf_concreteness(v)
            c += cc
            t += tt
        return c, t
    if isinstance(template, str) and template.startswith("$"):
        return 0, 1
    return 1, 1


def _body_admissible(body: list) -> bool:
    """H3 candidate filter: reject a body with a bare-placeholder statement, or
    any body template below MIN_CONCRETE_FRACTION concrete leaves.  A pure
    wildcard abbreviates nothing a real invocation could ground."""
    for template in body:
        if isinstance(template, str) and template.startswith("$"):
            return False                       # bare-placeholder statement
        concrete, total = _leaf_concreteness(template)
        if total == 0 or (concrete / total) < MIN_CONCRETE_FRACTION:
            return False
    return True


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
         max_len: int = DEFAULT_MAX_LEN, *, witness_filter=None) -> list:
    """Deterministically mine recurrence-macro candidates from `readings`.

    Cluster key = (window length, tuple of LF kinds).  A cluster is a candidate
    iff it occurs in >= 2 readings, its anti-unified body binds every parameter,
    passes the H3 concreteness filter, and adding it to the LIVE `macro_table`
    strictly reduces `corpus_dl`.  Each result is {candidate, dl_saving, uses,
    cluster_key}; sorted by descending saving then name (deterministic).

    `witness_filter` (Z-E, S5): when given, restricts the readings that count as
    witnesses and price the corpus to those satisfying it (real, exogenous-origin
    readings) -- default None is byte-identical to before."""
    macro_table = macro_table or {}
    if witness_filter is not None:
        readings = [r for r in readings if witness_filter(r)]
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
        if not _body_admissible(body):               # H3 wildcard filter
            continue
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
def gc_macros(registry, readings: list, *, witness_filter=None) -> list:
    """Retire any live macro whose removal STRICTLY reduces the corpus
    description length (W3.3, widened in S1.6).  Runs to a fixpoint, sorted for
    determinism, logging each retirement as a first-class event.  Returns the
    list of retired names.

    Two victim passes per fixpoint step, in this order:
      1. the uses<2 fast path (the original W3.3 rule, byte-identical) -- a macro
         stranded below its two-witness threshold whose `dl_macro` is still paid;
      2. S1.6 widening -- ANY macro (even one with >=2 uses) whose ablation
         strictly reduces total DL, closing the stale-vocabulary shadowing hazard
         the greedy-by-past-output trap creates.  The fast path runs first so an
         existing stranded victim is picked exactly as before.

    `witness_filter` (Z-E, S5): restricts the readings that price the corpus;
    default None is byte-identical to before."""
    if witness_filter is not None:
        readings = [r for r in readings if witness_filter(r)]
    retired = []
    table = registry.macro_table()
    while True:
        stats = mdl_macros.corpus_dl(readings, table)
        uses = stats["reading_uses"]
        victim = reason = None
        for name in sorted(table):                   # pass 1: uses<2 fast path
            if uses.get(name, 0) < 2:
                trial = {k: v for k, v in table.items() if k != name}
                if mdl_macros.corpus_dl(readings, trial)["total"] < stats["total"]:
                    victim, reason = name, "below-two-uses-and-dl-reducing"
                    break
        if victim is None:                           # pass 2: any DL-reducing
            for name in sorted(table):
                trial = {k: v for k, v in table.items() if k != name}
                if mdl_macros.corpus_dl(readings, trial)["total"] < stats["total"]:
                    victim, reason = name, "ablation-strictly-dl-reducing"
                    break
        if victim is None:
            break
        registry.macro_retire(victim)
        registry.log_event("macro-retired", {
            "name": victim,
            "reason": reason,
            "uses": uses.get(victim, 0),
            "dl_macro": round(mdl_macros.dl_macro(table[victim]), 3)})
        retired.append(victim)
        del table[victim]
    return retired


# ----------------------------------------------- searched admission sequence
def searched_macro_sequence(readings: list, initial_table: dict = None, *,
                            beam_width: int = 4, max_depth: int = DEFAULT_MAX_LEN,
                            witness_filter=None) -> dict:
    """S1.3: beam-search over macro-admission SEQUENCES for the table that
    minimizes `corpus_dl` over the corpus -- the searched upgrade of the
    scheduler's greedy one-max-saving-macro-per-iteration behavior.

    State = a macro table; a successor adds one `mine` candidate that still
    passes the explicit `macro_admission_decision` gate (Z1: the gate is the
    arbiter, not `mine`'s inline check).  Because `corpus_dl` depends only on the
    table SET (not admission order), order-permuted paths dedup to one state, and
    the search returns the best table EVER VISITED -- a shallower table can beat
    everything past it (the objective is non-monotone in admissions, H19).

    Returns the winning macro table (a superset of `initial_table`); the admitted
    sequence is its keys minus the initial table's."""
    if witness_filter is not None:
        readings = [r for r in readings if witness_filter(r)]
    initial_table = dict(initial_table or {})

    def expand(table):
        out = []
        for c in mine(readings, table):
            cand = c["candidate"]
            if cand["name"] in table:
                continue
            if not mdl_macros.macro_admission_decision(
                    readings, cand, table)["admit"]:
                continue                             # the gate is the arbiter
            nxt = dict(table)
            nxt[cand["name"]] = cand
            out.append(nxt)
        return out

    def score(table):
        return mdl_macros.corpus_dl(readings, table)["total"]

    return search.beam_search(initial_table, expand, score,
                              beam_width=beam_width, max_depth=max_depth)
