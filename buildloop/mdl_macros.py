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

PRICING MEMO (throughput; no admission-surface change): `_reading_stats` is
memoized on (reading identity, macro-table CONTENT, canon-view state).  The
same reading priced against the same table under the same admitted-rung
registry is a pure function, and the callers recompute it heavily -- every
candidate in a greedy-grow step re-prices the identical dl_before corpus, and
every census/bench replay re-prices unchanged readings wave after wave.  The
memo returns exactly what the uncached path would; the table is keyed by
canonical CONTENT (never object id -- an equal rebuilt table hits, an in-place
table[name]=cand grow misses the old key), and the canon view is keyed with
the same granularity `rung_registry.load_admitted`'s own mtime cache uses.
The memoized inputs are treated as immutable, which every current caller
honors (mutation sites clone first).  A test whose TOOTH is genuine
recomputation (two-run byte-stability; the reported-first anchor install)
calls `clear_pricing_cache()` between its runs, mirroring
`rung_registry.reload()`.
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


# ------------------------------------------------------------- pricing memo
#: (reading-content-key, table-content-key, canon-token) -> (dl, count,
#: frozen used, strong refs).  The refs pin the registry object alive so a
#: recycled id can never alias a dead token.  Bounded: cleared wholesale at
#: the cap -- results never depend on cache state, so clearing is always sound.
_PRICING_CACHE: dict = {}
_PRICING_CACHE_MAX = 1 << 17

#: id(reading) -> (content digest, strong ref).  A dict reading's memo key is
#: its CONTENT digest, computed once per object (a replay that rebuilds the
#: same docs from the same checkpoint re-hits the same entries); the strong
#: ref pins the object so its id can never be recycled onto a stale digest.
_READING_KEY_CACHE: dict = {}


def clear_pricing_cache() -> None:
    """Drop the `_reading_stats` memo (mirrors `rung_registry.reload()`).  A
    test whose tooth is GENUINE recomputation -- two-run byte-stability, the
    reported-first anchor-install byte-identity -- calls this between runs so
    the second run exercises the full pricing path instead of the memo."""
    _PRICING_CACHE.clear()
    _READING_KEY_CACHE.clear()


def _reading_key(reading):
    """Memo key of one reading: the sha-256 of its canonical JSON for a plain
    dict doc (content-keyed -- a replay's rebuilt-but-equal doc hits), cached
    per object; ``id(reading)`` for anything else (opaque objects price per
    instance)."""
    if not isinstance(reading, dict):
        return id(reading)
    ent = _READING_KEY_CACHE.get(id(reading))
    if ent is not None:
        return ent[0]
    from common import sha256_json
    digest = sha256_json(reading)
    if len(_READING_KEY_CACHE) >= _PRICING_CACHE_MAX:
        _READING_KEY_CACHE.clear()
    _READING_KEY_CACHE[id(reading)] = (digest, reading)
    return digest


def _table_key(macro_table: dict) -> tuple:
    """CONTENT key of a macro table: the sorted canonical JSON of every macro.
    Content-keyed (never id-keyed), so an equal-but-rebuilt table hits and an
    in-place `table[name] = cand` grow misses the old key."""
    from common import canonical_json
    return tuple(sorted(canonical_json(m) for m in macro_table.values()))


def _canon_token():
    """Identity of the canon view's input state, as ``(token, registry)``.
    ``None`` when the admitted-rung registry is empty (canon is the identity,
    so the entry is shared with the raw ``canon=False`` pricing); otherwise
    ``(rungs_dir, id(registry))``.  ``load_admitted``'s mtime cache returns
    the SAME object while admitted.json is unchanged, so object identity
    tracks registry content with exactly that cache's granularity (a rewrite
    or ``reload()`` yields a fresh object, hence a fresh token)."""
    from buildloop import rung_registry as _rung
    reg = _rung.load_admitted()
    if not reg:
        return None, None
    return (_rung.rungs_dir(), id(reg)), reg


def _macro_sig(macro):
    """Fast-reject signature of a macro's FIRST body template: its key set when
    the template is a dict (keys are always concrete -- `_unify` demands exact
    key-set equality, placeholders bind only in value position), else None
    (a non-dict template carries no cheap discriminator; always try it)."""
    body = macro["body"]
    t = body[0] if body else None
    return frozenset(t) if isinstance(t, dict) else None


def _rewrite_pass(stmts, macros, used: set, sigs=None):
    """ONE greedy, longest-body-first rewrite pass over a statement stream: a
    matched body window collapses to one INVOCATION item -- a statement whose lf
    is the concrete `{"kind":"macro","name",...,"args":binding}` invocation,
    tagged `"_inv": n_params` so the DL pass prices it as `dl_invocation`
    (never as a concrete statement) -- and everything else copies through.
    Returns (new_stream, changed).  Deterministic, mutation-free.

    `sigs` (parallel to `macros`) carries each macro's `_macro_sig`; a position
    whose lf key-set cannot equal the macro's first-template key-set is skipped
    without a `_match_at` call.  Pure fast-reject: `_unify`'s own first dict
    check is exactly key-set equality, so the skip can never change which macro
    matches (the longest-body-first order over the survivors is unchanged)."""
    out, i, changed, n = [], 0, False, len(stmts)
    if sigs is None:
        sigs = [_macro_sig(m) for m in macros]
    while i < n:
        hit = binding = None
        lf0 = _lf_of(stmts[i])
        ks = frozenset(lf0) if isinstance(lf0, dict) else None
        for m, sig in zip(macros, sigs):
            if sig is not None and sig != ks:
                continue
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


#: sentinel: "compute the canon token here" (None is a REAL token -- the
#: empty-registry / raw-equivalent state -- so it cannot be the default).
_TOK_UNSET = object()


def _reading_stats(reading, macro_table: dict, *, canon: bool = True,
                   _tkey=None, _tok=_TOK_UNSET):
    """Rewrite a reading's statement stream with the available macros and return
    (dl, statement_count, used_macro_names).

    MEMOIZED (module header): a pure function of (reading, table content,
    canon-view state), keyed exactly so; `_tkey` / `_tok` let `corpus_dl` pay
    the table-content key and the canon token once per corpus instead of once
    per reading.  On a hit the returned `used` is a fresh set (callers may
    mutate it).

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
    if _tok is not _TOK_UNSET:
        token, reg = _tok
    else:
        token, reg = _canon_token() if canon else (None, None)
    tkey = _table_key(macro_table) if _tkey is None else _tkey
    key = (_reading_key(reading), tkey, token)
    hit = _PRICING_CACHE.get(key)
    if hit is not None:
        return hit[0], hit[1], set(hit[2])

    if reg is not None:                       # non-empty registry: canon view
        from buildloop import rung_registry as _rung
        priced = _rung.canon(reading, registry=reg)
    else:                                     # empty registry: identity
        priced = reading
    stmts = _statements(priced)
    macros = sorted(macro_table.values(),
                    key=lambda m: (-len(m["body"]), m["name"]))
    sigs = [_macro_sig(m) for m in macros]
    used: set = set()
    for _ in range(max(1, len(macros))):
        stmts, changed = _rewrite_pass(stmts, macros, used, sigs)
        if not changed:
            break
    dl = 0.0
    for s in stmts:
        if isinstance(s, dict) and "_inv" in s:
            dl += dl_invocation(s["_inv"])
        else:
            dl += dl_statement(s)
    if len(_PRICING_CACHE) >= _PRICING_CACHE_MAX:
        _PRICING_CACHE.clear()
    _PRICING_CACHE[key] = (dl, len(stmts), frozenset(used), reg)
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
    tkey = _table_key(macro_table)            # pay the content key once
    tok = _canon_token() if canon else (None, None)   # ...and the token once
    macro_cost = sum(dl_macro(m) for m in macro_table.values())
    reading_cost, total_stmts = 0.0, 0
    reading_uses = {name: 0 for name in macro_table}
    for r in readings:
        dl, cnt, used = _reading_stats(r, macro_table, canon=canon,
                                       _tkey=tkey, _tok=tok)
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
