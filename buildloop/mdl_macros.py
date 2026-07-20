"""Minimum-description-length accounting for READING MACROS (P5.2).

A *macro* is an abbreviation that expands -- transitively, to fixpoint -- to
>= 1 concrete Reading statements (generators.reading._expand_macros); a body may
itself invoke an already-admitted macro (a level-2+ tower, D2).  Capturing a
recurring statement cluster as one macro compresses every future Reading that
uses it -- but only if the compression actually pays for the macro's stored
definition.  This module is the MDL gate that decides.  Pricing matches
candidates against the corpus RECODED in the current vocabulary
(recode-then-mine, `_reading_stats`), so tower bodies are priceable; the
currency constants are unchanged.

It deliberately mirrors the dl_before/dl_after GATE SHAPE of
`buildloop.mdl.admission_decision` -- and ONLY that shape.  The rest of mdl.py
(_covers / chain_length_for / generator_dl) is welded to the codec generators'
atoms/backlogs/emit-chains and is NOT reused here; a Reading macro's description
length is a different thing (statement / field counts + a token proxy over the
logical forms).

Description length (all monotone in "more statements / more fields = more DL"):

    dl_statement(s)   = 1  +  #fields/leaves in s.lf              (a concrete stmt)
    dl_invocation(k)  = 1  +  1(name) + k                          (a macro call, k args)
    dl_macro(m)       = 1  +  #params + sum(dl_statement over body) (stored once)
    corpus_dl         = sum(dl_macro over the table)   [paid once per admitted macro]
                      + sum, over readings, of the reading's DL when its statement
                        stream is greedily rewritten with the available macros
                        (a matched body window collapses to one cheap invocation).

macro_admission_decision admits a candidate macro IFF it strictly reduces the
corpus DL (dl_after < dl_before) AND it is actually used by >= 2 readings in the
corpus -- the two-witness discipline that keeps a one-off "macro" from being
minted just because it happened to shave a token off a single reading.
"""
from __future__ import annotations

# per-unit costs (kept as named constants so the token proxy is auditable)
_STMT_BASE = 1.0
_MACRO_BASE = 1.0
_INVOKE_BASE = 1.0


def _leaf_count(x) -> int:
    """A structural token proxy: one token per dict key and per list element,
    plus one per scalar leaf.  Bigger / more-nested logical forms cost more."""
    if isinstance(x, dict):
        return sum(1 + _leaf_count(v) for v in x.values())
    if isinstance(x, list):
        return sum(1 + _leaf_count(v) for v in x)
    return 1


def _lf_of(stmt):
    """Accept either a full statement {id,force,quote,lf} or a bare lf dict."""
    if isinstance(stmt, dict) and "lf" in stmt:
        return stmt["lf"]
    return stmt


def dl_statement(stmt) -> float:
    """DL of ONE concrete Reading statement: a per-statement base plus the
    field/leaf count of its logical form."""
    return float(_STMT_BASE + _leaf_count(_lf_of(stmt)))


def dl_invocation(n_args: int) -> float:
    """DL of a macro INVOCATION: a base + the macro name token + one per arg."""
    return float(_INVOKE_BASE + 1 + n_args)


def dl_macro(macro: dict) -> float:
    """DL of a macro DEFINITION (its stored, once-paid cost): a base + its
    parameter list + the DL of every statement template in its body."""
    body_cost = sum(dl_statement({"lf": t}) for t in macro["body"])
    return float(_MACRO_BASE + len(macro.get("params", [])) + body_cost)


# --------------------------------------------------------------- matching
def _unify(template, concrete, binding: dict) -> bool:
    """Unify a macro body TEMPLATE against a concrete logical form under a single
    parameter binding.  A string "$p" is a placeholder that binds parameter p to
    the concrete value (and must stay consistent across the whole match); every
    other node must be structurally equal (same dict key-set, same list length,
    equal scalars).  Deterministic, LLM-free."""
    if isinstance(template, str) and template.startswith("$"):
        p = template[1:]
        if p in binding:
            return binding[p] == concrete
        binding[p] = concrete
        return True
    if isinstance(template, dict):
        if not isinstance(concrete, dict) or set(template) != set(concrete):
            return False
        return all(_unify(template[k], concrete[k], binding) for k in template)
    if isinstance(template, list):
        if not isinstance(concrete, list) or len(template) != len(concrete):
            return False
        return all(_unify(a, b, binding) for a, b in zip(template, concrete))
    return template == concrete


def _match_at(stmts: list, i: int, macro: dict):
    """If macro's body matches the window of len(body) statements starting at i
    (under one consistent binding that covers every parameter), return the
    binding; else None."""
    body = macro["body"]
    if i + len(body) > len(stmts):
        return None
    binding: dict = {}
    for j, template in enumerate(body):
        lf = _lf_of(stmts[i + j])
        if not isinstance(lf, dict) or not _unify(template, lf, binding):
            return None
    if any(p not in binding for p in macro.get("params", [])):
        return None      # a partial match would not be a faithful abbreviation
    return binding


def _statements(reading) -> list:
    return reading.statements if hasattr(reading, "statements") \
        else reading["statements"]


def _rewrite_pass(stmts, macros, used: set):
    """ONE greedy, longest-body-first rewrite pass over a statement stream: a
    matched body window collapses to one INVOCATION item -- a statement whose lf
    is the concrete `{"kind":"macro","name",...,"args":binding}` invocation,
    tagged `"_inv": n_params` so the DL pass prices it as `dl_invocation`
    (never as a concrete statement) -- and everything else copies through.
    Returns (new_stream, changed).  Deterministic, mutation-free."""
    out, i, changed, n = [], 0, False, len(stmts)
    while i < n:
        hit = binding = None
        for m in macros:
            b = _match_at(stmts, i, m)
            if b is not None:
                hit, binding = m, b
                break
        if hit is not None:
            out.append({"lf": {"kind": "macro", "name": hit["name"],
                               "args": binding},
                        "_inv": len(hit.get("params", []))})
            used.add(hit["name"])
            i += len(hit["body"])
            changed = True
        else:
            out.append(stmts[i])
            i += 1
    return out, changed


def _reading_stats(reading, macro_table: dict, *, canon: bool = True):
    """Rewrite a reading's statement stream with the available macros and return
    (dl, statement_count, used_macro_names).

    RECODE-THEN-MINE (D2, COMPRESSION.md:712-716 / the §13.1 (greedy;GC)*
    fixpoint policy): the greedy longest-body-first rewrite is iterated to a
    FIXPOINT.  Pass 1 recodes the raw corpus in the current vocabulary (each
    matched window collapses to an invocation item); later passes match against
    that RECODED stream, so a macro whose body itself INVOKES an admitted macro
    (a level-2+ tower body containing a `kind:"macro"` template) can find its
    uses -- under raw-only matching such a body priced uses=0 forever.  The
    CURRENCY is unchanged: the final stream is priced with exactly the existing
    `dl_invocation`/`dl_statement` constants; only the corpus REPRESENTATION
    candidates are matched against changed.

    FLAT-TABLE EQUIVALENCE PIN: for a table with no invocation-bearing body,
    later passes can never match (a concrete template does not unify with an
    invocation item, and collapsing creates no new concrete adjacency), so the
    fixpoint halts after pass 1 with (dl, count, used) byte-identical to the
    historical single-pass rewrite.

    Pass bound: len(macro_table) passes suffice for any DAG table (each pass
    collapses at least one more tower level); the bound makes a hand-built
    CYCLIC table terminate deterministically instead of looping.

    FI-W1-2 seam 1/4 (COMPRESSION.md §11.9): pricing sees the CANON VIEW of the
    reading (the admitted rung pipeline applied to a COPY of each pred).  With an
    empty rung registry `canon` is the identity, so this is byte-identical to the
    pre-integration pricing (the rung-free pin); the store/certs/authored bytes
    stay raw -- only the priced view is canonicalized.  `canon=False` DISABLES the
    view (it does not add a call site -- it bypasses seam 1) so a measurement
    harness can price the RAW baseline beside the canon one (bench_formalize's
    corpus_dl_canon reported-first column)."""
    if canon:
        from buildloop import rung_registry as _rung
        reading = _rung.canon(reading)
    stmts = _statements(reading)
    macros = sorted(macro_table.values(),
                    key=lambda m: (-len(m["body"]), m["name"]))
    used: set = set()
    for _ in range(max(1, len(macros))):
        stmts, changed = _rewrite_pass(stmts, macros, used)
        if not changed:
            break
    dl = 0.0
    for s in stmts:
        if isinstance(s, dict) and "_inv" in s:
            dl += dl_invocation(s["_inv"])
        else:
            dl += dl_statement(s)
    return dl, len(stmts), used


def dl_reading(reading, macro_table: dict, *, canon: bool = True) -> float:
    """DL of one reading given the macros available to abbreviate it.  `canon`
    threads the FI-W1-2 view bypass (see `_reading_stats`)."""
    return _reading_stats(reading, macro_table or {}, canon=canon)[0]


def statement_count(reading, macro_table: dict, *, canon: bool = True) -> int:
    """Number of statements the reading needs when written with these macros
    (matched clusters count as ONE invocation each)."""
    return _reading_stats(reading, macro_table or {}, canon=canon)[1]


def corpus_dl(readings: list, macro_table: dict, *, canon: bool = True) -> dict:
    """Total description length of a corpus of readings given a macro table:
    the once-paid cost of every macro definition plus each reading's macro-
    rewritten DL.  Also reports mean statements/reading and, per macro, HOW MANY
    readings actually use it (the >= 2 witness count).  `canon` threads the
    FI-W1-2 view bypass (default True = the seam; False = the raw baseline)."""
    macro_table = macro_table or {}
    macro_cost = sum(dl_macro(m) for m in macro_table.values())
    reading_cost, total_stmts = 0.0, 0
    reading_uses = {name: 0 for name in macro_table}
    for r in readings:
        dl, cnt, used = _reading_stats(r, macro_table, canon=canon)
        reading_cost += dl
        total_stmts += cnt
        for name in used:
            reading_uses[name] += 1
    n = len(readings)
    return {"total": macro_cost + reading_cost,
            "macro_cost": macro_cost, "reading_cost": reading_cost,
            "reading_uses": reading_uses, "n": n,
            "total_statements": total_stmts,
            "mean_statements": (total_stmts / n) if n else 0.0}


def macro_admission_decision(readings: list, candidate: dict,
                             macro_table: dict = None, *,
                             witness_filter=None, canon: bool = True) -> dict:
    """The MDL gate (mirrors mdl.admission_decision's dl_before/dl_after shape).

    Admit the candidate macro IFF adding it to the table strictly reduces the
    corpus description length AND it is used by >= 2 readings.  `candidate` is a
    macro definition {name, params, body}; `macro_table` is any already-admitted
    macros (default none).

    `witness_filter` (Z-E witness discipline, S5.2/S5.3): dreams propose but only
    real witnesses decide.  When given, the readings that price BOTH corpus_dl
    computations (dl_before and dl_after) are restricted to those satisfying the
    predicate -- the real, exogenous-origin readings -- so a cluster witnessed
    only by dream (system-origin) readings can never clear the >= 2 real-witness
    admission bar.  Default None is byte-identical to before."""
    macro_table = dict(macro_table or {})
    if witness_filter is not None:
        readings = [r for r in readings if witness_filter(r)]
    before = corpus_dl(readings, macro_table, canon=canon)
    after_table = dict(macro_table)
    after_table[candidate["name"]] = candidate
    after = corpus_dl(readings, after_table, canon=canon)
    uses = after["reading_uses"].get(candidate["name"], 0)
    admit = (after["total"] < before["total"]) and (uses >= 2)
    return {"admit": admit,
            "dl_before": round(before["total"], 3),
            "dl_after": round(after["total"], 3),
            "delta": round(after["total"] - before["total"], 3),
            "uses": uses, "used_by_ge_2": uses >= 2,
            "mean_statements_before": round(before["mean_statements"], 3),
            "mean_statements_after": round(after["mean_statements"], 3)}
