"""Minimum-description-length accounting for READING MACROS (P5.2).

A *macro* is an abbreviation that expands to >= 1 concrete Reading statements
(generators.reading._expand_macros).  Capturing a recurring statement cluster as
one macro compresses every future Reading that uses it -- but only if the
compression actually pays for the macro's stored definition.  This module is the
MDL gate that decides.

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


def _reading_stats(reading, macro_table: dict):
    """Greedily rewrite a reading's statement stream with the available macros
    (longest body first, then name, for determinism) and return
    (dl, statement_count, used_macro_names).  A matched body window collapses to
    one invocation; unmatched statements stay as themselves."""
    stmts = _statements(reading)
    macros = sorted(macro_table.values(),
                    key=lambda m: (-len(m["body"]), m["name"]))
    dl, count, used, i = 0.0, 0, set(), 0
    while i < len(stmts):
        hit = next((m for m in macros if _match_at(stmts, i, m) is not None),
                   None)
        if hit is not None:
            dl += dl_invocation(len(hit.get("params", [])))
            count += 1
            used.add(hit["name"])
            i += len(hit["body"])
        else:
            dl += dl_statement(stmts[i])
            count += 1
            i += 1
    return dl, count, used


def dl_reading(reading, macro_table: dict) -> float:
    """DL of one reading given the macros available to abbreviate it."""
    return _reading_stats(reading, macro_table or {})[0]


def statement_count(reading, macro_table: dict) -> int:
    """Number of statements the reading needs when written with these macros
    (matched clusters count as ONE invocation each)."""
    return _reading_stats(reading, macro_table or {})[1]


def corpus_dl(readings: list, macro_table: dict) -> dict:
    """Total description length of a corpus of readings given a macro table:
    the once-paid cost of every macro definition plus each reading's macro-
    rewritten DL.  Also reports mean statements/reading and, per macro, HOW MANY
    readings actually use it (the >= 2 witness count)."""
    macro_table = macro_table or {}
    macro_cost = sum(dl_macro(m) for m in macro_table.values())
    reading_cost, total_stmts = 0.0, 0
    reading_uses = {name: 0 for name in macro_table}
    for r in readings:
        dl, cnt, used = _reading_stats(r, macro_table)
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
                             macro_table: dict = None) -> dict:
    """The MDL gate (mirrors mdl.admission_decision's dl_before/dl_after shape).

    Admit the candidate macro IFF adding it to the table strictly reduces the
    corpus description length AND it is used by >= 2 readings.  `candidate` is a
    macro definition {name, params, body}; `macro_table` is any already-admitted
    macros (default none)."""
    macro_table = dict(macro_table or {})
    before = corpus_dl(readings, macro_table)
    after_table = dict(macro_table)
    after_table[candidate["name"]] = candidate
    after = corpus_dl(readings, after_table)
    uses = after["reading_uses"].get(candidate["name"], 0)
    admit = (after["total"] < before["total"]) and (uses >= 2)
    return {"admit": admit,
            "dl_before": round(before["total"], 3),
            "dl_after": round(after["total"], 3),
            "delta": round(after["total"] - before["total"], 3),
            "uses": uses, "used_by_ge_2": uses >= 2,
            "mean_statements_before": round(before["mean_statements"], 3),
            "mean_statements_after": round(after["mean_statements"], 3)}
