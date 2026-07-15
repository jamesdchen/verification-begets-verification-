"""Planted macro corpora for the S1 searched-admission teeth (WP-F).

Fixed, deterministic, LLM-free.  Each builder returns a fresh list of reading
dicts ({"service", "statements":[{"id","force","quote","lf"}]}) suitable for
`buildloop.recurrence.mine` / `searched_macro_sequence` and
`buildloop.mdl_macros.corpus_dl` -- these operate on the statement stream
structurally, so the LFs here need not satisfy `parse_reading`'s referential
integrity (that is the reading-corpus fixtures' job, not the miner's).

Three corpora, each isolating one claim:

  * trap_corpus (part_b): the greedy scheduler admits ONE max-marginal-saving
    macro per iteration; here that is the len-4 macro A over [always,bound,
    effect,order].  Admitting A shadows the len-2 windows in the three ABCD
    readings, dropping {B=[always,bound], C=[effect,order]} below their two-
    witness threshold -- so greedy is stranded at {A} while the searched
    sequence reaches the strictly cheaper {B, C}.  (Verified numbers live in the
    demo's CSV; the teeth assert the RELATION searched < greedy, which is
    corpus-stable.)
  * incompressible_corpus (part_c): four all-distinct two-statement readings; no
    (length, kind-tuple) window recurs across >= 2 readings, so nothing is
    mined and nothing is admitted.
  * wildcard_corpus (H3): two readings whose only shared (kind,kind) cluster has
    all-DISTINCT content, so anti-unification yields a pure-wildcard body -- the
    H3 filter must reject it (the pre-filter live gate would have minted it,
    Delta<0, because dl_invocation prices args size-blind).
"""
from __future__ import annotations

# Four distinct-kind atomic statement templates, so len-2 windows [A,B] and
# [C,D] land in SEPARATE (kind-tuple) clusters and anti-unify to fully-concrete
# bodies (no placeholders -> pass H3).
_LF = {
    "A": {"kind": "always", "pred": {"op": ">=", "left": "q", "right": 0}},
    "B": {"kind": "bound", "action": "act", "left": "arg",
          "cmp": "<=", "right": "q"},
    "C": {"kind": "effect", "action": "act", "quantity": "q",
          "op": "dec", "amount": {"arg": "arg"}},
    "D": {"kind": "order", "first": "a1", "then": "a2"},
}


def _stmt(sid, code, force="demand", quote="s"):
    return {"id": sid, "force": force, "quote": quote, "lf": dict(_LF[code])}


def _reading(name, seq, force="demand", quote="s"):
    return {"service": name,
            "statements": [_stmt(f"{name}{i}", c, force, quote)
                           for i, c in enumerate(seq)]}


def trap_corpus():
    """3x [A,B,C,D] + 1x [A,B,A,B].  Greedy admits the len-4 macro (blocking the
    better pair); the searched sequence admits {[A,B], [C,D]}."""
    return [_reading("r1", "ABCD"), _reading("r2", "ABCD"),
            _reading("r3", "ABCD"), _reading("r4", "ABAB")]


def incompressible_corpus():
    """No window recurs across >= 2 readings -> nothing mineable."""
    return [_reading("q1", "AB"), _reading("q2", "CD"),
            _reading("q3", "AC"), _reading("q4", "BD")]


def wildcard_corpus():
    """Two readings whose (action,action) cluster has statements with DIFFERENT
    key-sets (one carries `arg`, one does not), so anti-unification cannot keep
    any shared structure and yields a pure bare-wildcard body `["$p0","$p1"]` --
    exactly the candidate the H3 filter must reject (the pre-H3 gate would mint
    it, Delta<0, since dl_invocation prices args size-blind)."""
    r1 = {"service": "w1", "statements": [
        {"id": "a", "force": "demand", "quote": "s",
         "lf": {"kind": "action", "name": "aa"}},
        {"id": "b", "force": "demand", "quote": "s",
         "lf": {"kind": "action", "name": "bb"}}]}
    r2 = {"service": "w2", "statements": [
        {"id": "c", "force": "demand", "quote": "s",
         "lf": {"kind": "action", "name": "cc", "arg": "x"}},
        {"id": "d", "force": "demand", "quote": "s",
         "lf": {"kind": "action", "name": "dd", "arg": "y"}}]}
    return [r1, r2]


def mixed_quote_reading():
    """One reading whose two adjacent demand statements carry DIFFERENT quotes --
    a window the H2 uniform-(force, quote) rule must NOT mine (it would be
    unrealizable as a single legal invocation)."""
    return {"service": "mq", "statements": [
        _stmt("s0", "A", quote="alpha"),
        _stmt("s1", "B", quote="beta")]}
