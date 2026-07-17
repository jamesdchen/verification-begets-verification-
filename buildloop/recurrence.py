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

FI-W1-3 (COMPRESSION.md §11.9) slot typing (window half HELD after adjudication):

  * `_demand_windows` keeps uniform-(force, quote) for BOTH domains (the H2
    realizability rule).  The FI-W1-3 math-domain relaxation (force-only) was
    MEASURED to regress the greedy governed corpus_dl by +29 while its -179
    congruence gain stayed counterfactual, so it is HELD pending a cluster-key
    design that makes it net positive (see _demand_windows' docstring).  Only the
    SLOT-TYPING half of FI-W1-3 lands here -- it is a pure honesty restriction
    that changes NO realized number.

  * `_op_slots_admissible` types op-slots (T3 proper): a `$`-param at an op-key
    position is admissible only when every witnessed op binding shares
    (role, arity, carrier-support) per generators.math_reading's single-source
    tables (`op_signature`) -- the honesty restriction that stops a slot from
    ranging over ops whose meaning/arity/carrier disagree.  Slot pricing stays 1
    token; log2|vocab| re-pricing is a reported-first experiment, not here.
"""
from __future__ import annotations

import common
from buildloop import mdl_macros
from generators import math_reading
from planner import search

DEFAULT_MAX_LEN = 4          # longest contiguous statement window mined

# The math-reading LF-kind vocabulary, single-sourced from generators.math_reading
# (F1's frozen fragment).  It is DISJOINT from the service reading's LF kinds
# (generators.reading.LF_KINDS: quantity/action/effect/bound/always/...), which
# is what makes "are this window's statement kinds drawn from the math set?" a
# clean domain discriminator -- see _is_math_domain and the FI-W1-3 split in
# _demand_windows.  A window inherits its reading's domain: a Reading is either a
# service Reading or a MathReading, never a mix, so classifying by the kinds
# PRESENT in the data needs no separate origin column.
_MATH_LF_KINDS = frozenset(math_reading.MATH_LF_KINDS)

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


def _lf_kind(stmt):
    lf = mdl_macros._lf_of(stmt)
    return lf.get("kind") if isinstance(lf, dict) else None


def _is_math_domain(stmts) -> bool:
    """The FI-W1-3 domain discriminator (COMPRESSION.md §11.9).

    A window inherits its reading's DOMAIN, and the cleanest discriminator
    already in the data is the LF KIND vocabulary: math readings
    (parse_math_reading) use kinds drawn from `_MATH_LF_KINDS`
    (object/operator/hypothesis/conclusion/quantifier/ambient), which is
    DISJOINT from the service reading's LF kinds.  A reading is math-domain iff
    every statement's kind is a math kind (a service reading has zero math
    kinds; an empty/degenerate reading is NOT math -> the conservative service
    branch, byte-identical to the old rule)."""
    kinds = {_lf_kind(s) for s in stmts}
    kinds.discard(None)
    return bool(kinds) and kinds <= _MATH_LF_KINDS


def _demand_windows(reading, max_len: int):
    """Contiguous windows of UNIFORM (force, quote) statements, lengths 2..max_len.

    H2: the restriction is uniform-(force, quote) for BOTH domains.  A macro
    invocation expands to statements that ALL inherit the invocation's single
    force AND quote (reading._expand_one), so a window whose statements disagree
    on force or quote "compresses" in the DL arithmetic yet is UNREALIZABLE as a
    legal invocation (a demand must quote a span, a choice must quote nothing --
    reading.parse_reading).  Mining uniform-(force, quote) windows is therefore
    both the honesty rule and what makes presupposition clusters and S3's
    choice-tail idiom mineable.  Returns the raw statement dicts so the caller can
    read both the LF and the force.

    WP-T3-REAL adjudication (COMPRESSION.md §11.9 FI-W1-3, window half HELD):
      The FI-W1-3 math-domain relaxation (force-uniformity only, quotes carried
      but not matched) was measured to REGRESS the greedy governed corpus_dl by
      +29 (2139 -> 2168): force-only coarsens the (width, kind-tuple) cluster key,
      so the (hyp,hyp) cluster grows from a clean even/odd pair to 15 diverse
      readings whose anti-unification over-generalizes past the H3 concreteness
      filter, and the even/odd op-slot macro is lost.  The -179 congruence gain
      the fix was to realize is only a COUNTERFACTUAL (census pass 3 hand-picks
      the triple by source_id; `mine`'s cluster key cannot).  Per the house
      rule (measure-then-decide / never land a regression as the new baseline),
      the window relaxation is HELD pending a cluster-key design that makes it net
      positive (a role/shape-keyed refinement measured at ~2060 < 2139 is the
      promising direction, but not yet at a merge bar).  The SLOT-TYPING half of
      FI-W1-3 (op_signature + _op_slots_admissible, below) is a pure honesty
      restriction that changes NO realized number and lands independently --
      `_is_math_domain` remains, now used only to gate slot typing to math bodies.
    """
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


# ---------------------------------------------------- op-slot semantic typing
def _op_slot_params(body: list) -> dict:
    """The parameters that sit at an OP-KEY position in `body`, mapped to the
    WITNESSED arity at that position (the length of the sibling `args` list).

    A slot is an op-slot iff a template node is `{"op": "$pN", "args": [...]}`.
    Because anti-unification only generalizes a position to a `$param` when the
    siblings match structurally, the sibling `args` length is identical across
    all occurrences -- so the witnessed arity is well-defined here."""
    found: dict = {}
    def walk(node):
        if isinstance(node, dict):
            op = node.get("op")
            if isinstance(op, str) and op.startswith("$"):
                found[op[1:]] = len(node.get("args", []))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    for template in body:
        walk(template)
    return found


def _op_binding_compatible(ops, witnessed_arity: int) -> bool:
    """The honesty restriction that survives as T3 proper (COMPRESSION.md §11.9
    / §11.3): the set of operator words a slot binds is admissible ONLY when
    every one is a known op sharing (role, carrier-support) AND each legally
    accepts the witnessed arity.

    Arity is checked as "each declared arity accepts the witnessed width" (fixed
    == width, or a variadic connector with width >= 2), not as a raw equality,
    because the witnessed width is already shared across occurrences by
    anti-unification -- the real hazard is a slot whose ops disagree in ROLE
    (term vs pred) or CARRIER-SUPPORT (an op undefined at another op's carrier,
    e.g. coprime is Nat-only).  Unknown op => incompatible (refuse)."""
    sigs = [math_reading.op_signature(op) for op in ops]
    if any(s is None for s in sigs):
        return False
    roles = {role for role, _arity, _carrier in sigs}
    carriers = {carrier for _role, _arity, carrier in sigs}
    if len(roles) != 1 or len(carriers) != 1:
        return False
    for _role, arity, _carrier in sigs:
        if arity is not None and arity != witnessed_arity:
            return False
        if arity is None and witnessed_arity < 2:
            return False
    return True


def _op_slots_admissible(body: list, params: list, occurrences: list) -> bool:
    """Slot typing for a candidate body (COMPRESSION.md §11.9, T3 proper).

    Applies ONLY to MATH-domain bodies (service candidates are untouched -- the
    op-signature tables are the math lexicon, and service-side mining is pinned
    byte-identical).  For every op-slot param, gather the concrete operator each
    occurrence binds there and require `_op_binding_compatible`.  A body with no
    op-slot is trivially admissible; slot PRICING is unchanged (1 token per
    param -- the log2|vocab| re-pricing is a reported-first experiment, not
    implemented here)."""
    if not _is_math_domain([{"lf": t} for t in body]):
        return True
    slots = _op_slot_params(body)
    if not slots:
        return True
    macro = {"name": "_typing_probe", "params": list(params), "body": body}
    witnessed: dict = {p: set() for p in slots}
    for lfs in occurrences:
        stmts = [{"lf": lf} for lf in lfs]
        binding = mdl_macros._match_at(stmts, 0, macro)
        if binding is None:
            return False                          # not a faithful abbreviation
        for p in slots:
            op = binding.get(p)
            if not isinstance(op, str):
                return False                      # op position bound a non-op
            witnessed[p].add(op)
    for p, arity in slots.items():
        if not _op_binding_compatible(witnessed[p], arity):
            return False
    return True


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
         max_len: int = DEFAULT_MAX_LEN, *, witness_filter=None,
         canon: bool = True) -> list:
    """Deterministically mine recurrence-macro candidates from `readings`.

    Cluster key = (window length, tuple of LF kinds).  A cluster is a candidate
    iff it occurs in >= 2 readings, its anti-unified body binds every parameter,
    passes the H3 concreteness filter, and adding it to the LIVE `macro_table`
    strictly reduces `corpus_dl`.  Each result is {candidate, dl_saving, uses,
    cluster_key}; sorted by descending saving then name (deterministic).

    `witness_filter` (Z-E, S5): when given, restricts the readings that count as
    witnesses and price the corpus to those satisfying it (real, exogenous-origin
    readings) -- default None is byte-identical to before.

    FI-W1-2 seam 2/4 (COMPRESSION.md §11.9): the miner windows the CANON VIEW of
    each reading, so mined bodies match the canonicalized pricing `_reading_stats`
    sees.  Empty rung registry ⇒ `canon` is the identity ⇒ byte-identical mining
    (the rung-free pin); the store/authored bytes stay raw.  `canon=False`
    DISABLES the seam so the rung admission gate can price a RAW counterfactual
    isolated from the ambient registry (it must not double-apply the live rungs)."""
    from buildloop import rung_registry as _rung
    macro_table = macro_table or {}
    if witness_filter is not None:
        readings = [r for r in readings if witness_filter(r)]
    if canon:
        readings = _rung._canon_all(readings)
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
        if not _op_slots_admissible(body, params,    # §11.9 slot typing (T3)
                                    [lfs for _, lfs in occ]):
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
    default None is byte-identical to before.

    FI-W1-2 seam 3/4 (COMPRESSION.md §11.9): GC prices the CANON VIEW of the
    corpus (via `canon`), matching what mining/pricing see.  Empty rung registry
    ⇒ identity ⇒ byte-identical GC (the rung-free pin)."""
    from buildloop import rung_registry as _rung
    if witness_filter is not None:
        readings = [r for r in readings if witness_filter(r)]
    readings = _rung._canon_all(readings)
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
                            witness_filter=None, canon: bool = True) -> dict:
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
        for c in mine(readings, table, canon=canon):
            cand = c["candidate"]
            if cand["name"] in table:
                continue
            if not mdl_macros.macro_admission_decision(
                    readings, cand, table, canon=canon)["admit"]:
                continue                             # the gate is the arbiter
            nxt = dict(table)
            nxt[cand["name"]] = cand
            out.append(nxt)
        return out

    def score(table):
        return mdl_macros.corpus_dl(readings, table, canon=canon)["total"]

    return search.beam_search(initial_table, expand, score,
                              beam_width=beam_width, max_depth=max_depth)
