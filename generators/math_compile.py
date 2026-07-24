"""Compositional compilation: MathReading -> Lean 4 statement text, deterministically.

The mathematical analogue of generators/reading_compile.py, and trusted by fiat
in exactly the same way (TRUST 1.2e) -- NARROWED by the level-A/B ceremony
(TRUST.md, maintainer-signed 2026-07-24): FgReflect.compile_preserves proves
the compiled statement's reflected denotation equals the emitted form's
meaning, and tools/fg_emit_pins.lean kernel-rfl-pins this module's emitted
bytes against the in-module reference emitter (teeth in
tests/test_fg_emit_pins.py; residual fiat named in the TRUST entry).
This module is LLM-free (rule L1/L2): it
is a PURE, DETERMINISTIC function from a *validated* MathReading (the F-A
envelope's inner reading, already gated by parse_math_reading) to the F-B
compiled artifact

    {lean_text, statement_hash, provenance}

Why "trusted by fiat" is sound here -- the SAME two damage bounds that make
reading_compile trusted (TRUST 1.2e), so a compiler bug is bounded to the
compiler-bug class the certificate discipline already accounts for and can never
manufacture an unearned certificate:

  1. Its output is fully CHECKED downstream by F0's contracts: the emitted
     `theorem ... := sorry` is elaborated by the statement-cert (F0.2), whose
     run-2 trusted audit confirms `sorryAx` alone (D5).  A compiler that emitted
     ill-typed or meaning-changed Lean simply fails to elaborate, or elaborates
     to something the F2 fidelity gates reject.
  2. F2 REPLAYS meaning-level instances against THIS exact compiled statement
     (the SMT mirror / decidable-enumeration channels instantiate witnesses into
     *these* Lean hypotheses -- ⚠T4), so a divergence between what the source
     meant and what we emitted surfaces as a first-class event, never a silent
     false green.

==============================================================================
CANONICAL EMISSION (byte-stable: identical reading => identical statement_hash)
==============================================================================
No clocks, no randomness, no dict-iteration-order dependence.  The single Lean 4
theorem `theorem <thm> : <prop> := sorry` is built so that WP-H / WP-J can rely
on byte-stability.  The concrete rules chosen:

  * `<thm>` = the reading's `theorem` id (validated as a lowercase identifier).

  * STATEMENT ORDER.  Quantifier, hypothesis and conclusion statements are each
    processed in ASCENDING LEXICOGRAPHIC order of their statement `id`
    (`sorted(..., key=id)`).  This is the "statement-id order" of the F1.2 spec,
    and it is total and reading-determined, hence byte-stable.  (Reordering
    hypotheses / conjoined conclusions is meaning-preserving; the relative order
    of distinct quantifier binders is the author's responsibility, fixed by the
    ids they assigned.)

  * BINDERS.  `<prop>` = <binder-prefix> <body>.  The binder-prefix is, in order:
      - a LEADING `∀` over every object that is referenced by a hypothesis /
        conclusion pred but is NOT bound by any `quantifier` statement, in
        SORTED-NAME order (canonical);  emitted only if that set is non-empty;
      - then one segment per `quantifier` statement in statement-id order:
        `∀ (x : C) (y : C) ...` / `∃ (x : C) ...`, its objects in the LISTED
        order.
    Every referenced object is bound EXACTLY once (quantifier binding wins; the
    leading `∀` covers only the remainder).  An object's binder carrier `C` is
    its DECLARED type from `.objects()` -- never the resolution rule below.

  * BODY = hypotheses chained into the conclusion:
    `H1 → H2 → ... → Conclusion` (hypotheses in id order).  If several demanded
    conclusions, they are conjoined with `∧` in id order.  `→` is right
    associative, so the chain means `H1 → (H2 → (... → C))`.

  * PARENTHESES.  Every compound (`op`) pred/term node is fully wrapped in
    parentheses; atoms (`ref`, non-negative `lit`) are bare; a negative literal
    is wrapped `(-k)`.  This preserves the AST's written structure UNAMBIGUOUSLY
    and the compiler NEVER reorders args (F-G).

  * CARRIER RESOLUTION (single deterministic rule, used ONLY where a Lean name
    is carrier-indexed -- `gcd` => Nat.gcd/Int.gcd, `coprime` => Nat.Coprime):
    the carrier of an operator/term is
        (a) the reading's AMBIENT carrier when an `ambient` statement is present;
        (b) else the declared carrier of the FIRST object referenced in a
            left-to-right pre-order walk of the term's argument subtree;
        (c) else (all-literal, no object) `Nat`.
    `dvd`/`even`/`odd` are carrier-independent in Lean (Dvd.dvd/Even/Odd), so
    resolution never affects their emission.  Defensive: if a resolved carrier
    is absent from a word's lean table (e.g. `coprime@Int`, a gate-level
    fragment-miss that in practice never reaches the compiler), the
    lexicographically-first supported carrier is used so emission stays total.

  * `-` (D8).  Subtraction is emitted as `a - b` over the TYPED binders; Lean's
    HSub instance carrier-resolves it (truncated `Nat.sub` vs real `Int.sub`).
    Emitting `a - b` with typed binders is therefore correct WITHOUT any
    compiler-side carrier choice -- the divergence T4 exists to catch lives in
    the SMT mirror's `ite` guard (generators/math_smt.py), not here.  (This note
    lives in the SOURCE, not in the emitted Lean, so lean_text stays a bare
    `theorem ... := sorry`.)

  * `^` uses the literal exponent verbatim: `a ^ 2` (validator guarantees a
    non-negative literal exponent; D10).

  * `%` (mod, both the `%` builtin and the `mod` lexicon word) is emitted as the
    `%` notation on typed operands, which resolves Nat.mod vs Int.emod by
    carrier at Lean elaboration time (D9); no name lookup needed.

PROVENANCE maps each emitted Lean element to the statement id(s) that produced
it -- the chain *quoted span -> force -> LF -> Lean term*:
    binder.<name>       -> [decl-id (+ quantifier-id if quantifier-bound)]
    quantifier.<id>     -> [id]
    hyp.<id>            -> [id]
    conclusion.<id>     -> [id]
Values are de-duplicated and sorted (byte-stable; irrelevant to the hash, which
is over lean_text bytes only).
"""
from __future__ import annotations

import collections
import hashlib

from .math_reading import MATH_OPERATORS, MathReading, _BIGOPS

# Comparison atoms -> Lean unicode notation.
_ATOM_SYM = {"=": "=", "!=": "≠", "<=": "≤", "<": "<"}
# Boolean connectives -> Lean unicode notation.
_CONN_SYM = {"and": "∧", "or": "∨"}

_Ctx = collections.namedtuple("_Ctx", "ambient objects")


class CompileError(Exception):
    """The (already-validated) reading is not compilable -- an operator/term the
    F-G AST admits but this compiler does not render.  Post-gate this is an
    internal invariant violation, surfaced rather than mis-emitted."""


# --------------------------------------------------------------- ref walking
def _term_refs(term: dict) -> list:
    """Object names referenced by a term, in left-to-right pre-order (with
    duplicates).  Drives both the 'referenced' set and carrier resolution.  A
    big-operator's bound index is dropped (bound, not free) -- identical to
    math_eval._term_refs, so the two walks cannot drift."""
    if "ref" in term:
        return [term["ref"]]
    if "lit" in term or "var" in term:
        return []
    if term.get("op") in _BIGOPS:
        var = term["args"][0]["var"]
        out = []
        for a in term["args"][1:]:
            out.extend(r for r in _term_refs(a) if r != var)
        return out
    out = []
    for a in term["args"]:
        out.extend(_term_refs(a))
    return out


def _pred_refs(pred: dict) -> list:
    """Object names referenced by a pred, in left-to-right pre-order."""
    op = pred["op"]
    out = []
    if op in ("and", "or", "implies"):
        for a in pred["args"]:
            out.extend(_pred_refs(a))
    else:
        for a in pred["args"]:
            out.extend(_term_refs(a))
    return out


# ------------------------------------------------------------ carrier / names
def _resolve_carrier(refs: list, ctx: _Ctx) -> str:
    if ctx.ambient is not None:
        return ctx.ambient
    for name in refs:
        if name in ctx.objects:
            return ctx.objects[name]
    return "Nat"


def _lean_name(word: str, carrier: str) -> str:
    lean = MATH_OPERATORS[word]["lean"]
    if carrier in lean:
        return lean[carrier]
    return lean[sorted(lean)[0]]           # defensive totality (see docstring)


# ------------------------------------------------------------------- render
def _render_term(term: dict, ctx: _Ctx) -> str:
    if "ref" in term:
        return term["ref"]
    if "lit" in term:
        v = term["lit"]
        return str(v) if v >= 0 else f"({v})"      # (-k) so it never mis-binds
    op = term["op"]
    args = term["args"]
    if op == "^":                                  # literal exponent (D10)
        return f"({_render_term(args[0], ctx)} ^ {args[1]['lit']})"
    if op in ("+", "*"):
        return "(" + f" {op} ".join(_render_term(a, ctx) for a in args) + ")"
    if op in ("-", "%"):                           # `-`: D8; `%`: D9 (typed)
        return f"({_render_term(args[0], ctx)} {op} {_render_term(args[1], ctx)})"
    if op == "mod":                                # lexicon word -> % notation
        return f"({_render_term(args[0], ctx)} % {_render_term(args[1], ctx)})"
    if op == "gcd":                                # carrier-indexed Lean name
        name = _lean_name("gcd", _resolve_carrier(_term_refs(term), ctx))
        return "(" + name + " " + " ".join(_render_term(a, ctx) for a in args) + ")"
    if op in _BIGOPS:                              # bounded fold (P1)
        # Finset machinery over the LITERAL index interval, prefix form (no
        # notation, escape-gate friendly): Finset.sum/prod (Finset.Icc lo hi)
        # (fun i => body).  Finset.Icc over ℕ gives the index carrier Nat --
        # the same rule the gate, eval and the SMT mirror freeze -- and Lean's
        # empty-interval sum/prod is the identity element, matching eval's
        # lo > hi convention.  The body renders with the index in scope at
        # Nat so carrier-indexed names (gcd) resolve identically to eval.
        var = args[0]["var"]
        lo, hi = args[1]["lit"], args[2]["lit"]
        fn = "Finset.sum" if op == "bigsum" else "Finset.prod"
        inner_ctx = ctx._replace(objects={**ctx.objects, var: "Nat"})
        body = _render_term(args[3], inner_ctx)
        return f"({fn} (Finset.Icc {lo} {hi}) (fun {var} => {body}))"
    raise CompileError(f"unrenderable term operator {op!r}")


def _render_pred(pred: dict, ctx: _Ctx) -> str:
    op = pred["op"]
    args = pred["args"]
    if op in _CONN_SYM:
        sym = _CONN_SYM[op]
        return "(" + f" {sym} ".join(_render_pred(a, ctx) for a in args) + ")"
    if op == "implies":
        return f"({_render_pred(args[0], ctx)} → {_render_pred(args[1], ctx)})"
    if op in _ATOM_SYM:
        sym = _ATOM_SYM[op]
        return f"({_render_term(args[0], ctx)} {sym} {_render_term(args[1], ctx)})"
    if op == "dvd":
        return f"({_render_term(args[0], ctx)} ∣ {_render_term(args[1], ctx)})"
    if op == "even":
        return f"(Even {_render_term(args[0], ctx)})"
    if op == "odd":
        return f"(Odd {_render_term(args[0], ctx)})"
    if op == "coprime":                            # carrier-indexed Lean name
        name = _lean_name("coprime", _resolve_carrier(_pred_refs(pred), ctx))
        return "(" + name + " " + " ".join(_render_term(a, ctx) for a in args) + ")"
    raise CompileError(f"unrenderable pred operator {op!r}")


# --------------------------------------------------------------- the compiler
def compile_math_reading(reading: MathReading) -> dict:
    """Deterministically compile a *validated* MathReading into the F-B artifact
    `{lean_text, statement_hash, provenance}` (see the module docstring for the
    canonical-emission rules)."""
    objects = reading.objects()
    ctx = _Ctx(ambient=reading.ambient_carrier(), objects=objects)

    prov: dict = {}

    def add(key: str, sids: list) -> None:
        cur = prov.setdefault(key, [])
        for s in sids:
            if s not in cur:
                cur.append(s)

    decl_sid = {s["lf"]["name"]: s["id"] for s in reading.by_kind("object")}

    _by_id = lambda s: s["id"]
    q_stmts = sorted(reading.by_kind("quantifier"), key=_by_id)
    hyp_stmts = sorted(reading.by_kind("hypothesis"), key=_by_id)
    concl_stmts = sorted(reading.by_kind("conclusion"), key=_by_id)

    # --- quantifier binder segments (id order; objects in listed order) ------
    bound_q: set = set()
    q_segments = []
    for s in q_stmts:
        lf = s["lf"]
        qid = s["id"]
        sym = "∀" if lf["binder"] == "forall" else "∃"
        objs = lf["objects"]
        q_segments.append(sym + " " + " ".join(f"({o} : {objects[o]})"
                                               for o in objs))
        add(f"quantifier.{qid}", [qid])
        for o in objs:
            bound_q.add(o)
            add(f"binder.{o}", sorted({decl_sid.get(o, qid), qid}))

    # --- leading ∀ over referenced-but-unbound objects (sorted-name order) ---
    referenced: set = set()
    for s in hyp_stmts + concl_stmts:
        referenced.update(_pred_refs(s["lf"]["pred"]))
    leading = sorted(referenced - bound_q)
    segments = []
    if leading:
        segments.append("∀ " + " ".join(f"({o} : {objects[o]})" for o in leading))
        for o in leading:
            add(f"binder.{o}", [decl_sid[o]])
    segments.extend(q_segments)

    # --- body: H1 → ... → (C1 ∧ C2 ...) --------------------------------------
    hyp_strs = []
    for s in hyp_stmts:
        hyp_strs.append(_render_pred(s["lf"]["pred"], ctx))
        add(f"hyp.{s['id']}", [s["id"]])
    concl_strs = []
    for s in concl_stmts:
        concl_strs.append(_render_pred(s["lf"]["pred"], ctx))
        add(f"conclusion.{s['id']}", [s["id"]])
    conclusion = (concl_strs[0] if len(concl_strs) == 1
                  else "(" + " ∧ ".join(concl_strs) + ")")
    body = " → ".join(hyp_strs + [conclusion])

    prop = "".join(seg + ", " for seg in segments) + body
    lean_text = f"theorem {reading.theorem} : {prop} := sorry"
    statement_hash = hashlib.sha256(lean_text.encode("utf-8")).hexdigest()
    provenance = {k: sorted(v) for k, v in prov.items()}
    return {"lean_text": lean_text,
            "statement_hash": statement_hash,
            "provenance": provenance}
