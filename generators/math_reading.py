"""A MATH READING: the semantic analysis of a mathematical sentence.

The mathematical analogue of generators/reading.py.  Where a Reading is deontic-
temporal over integer aggregates, a MathReading is over typed objects,
quantifiers, operators and an ambient structure.  The architecture transfers
whole (F1 of FORMALIZATION.md):

  * Discourse referents: the `object`s a statement talks about ("n : Nat") are
    introduced explicitly; every later statement refers to declared objects.
  * Speech-act force (the SAME trichotomy):
      - "demand":         the theorem's asserted content, quote-grounded.  The
                          gate checks the quote occurs in the source verbatim.
      - "presupposition": the implicit hypotheses ("n positive", nonzero
                          divisor, nonempty domain) -- first-class, quoted at
                          their trigger.  THE KILLER FEATURE: the side
                          conditions autoformalization silently drops.
      - "choice":         formalization freedom (which structure, what
                          generality).  MUST quote nothing.
  * Logical forms: each statement's content is a term of a small typed fragment
    that compiles compositionally (see generators/math_compile.py).

The LLM authors MathReadings (JSON, a pure spec gated like every other) and,
on the proof path only, tactic scripts.  It NEVER authors Lean (rule L1).

This module is the single source of truth for the fragment (F-G freeze):
MATH_LF_KINDS + _MLF_FIELDS + MATH_OPERATORS + the pred AST -- imported by the
prompt renderer, the SMT mirror (generators/math_smt.py) and the compiler
(generators/math_compile.py), so grammar, mirror and compiler can never drift.
"""
from __future__ import annotations

import dataclasses
import json
import re

_ID = re.compile(r"[a-z][a-zA-Z0-9_]*")
FORCES = ("demand", "presupposition", "choice")

# The carrier whitelist for typed objects and the ambient structure.  v1 is
# deliberately tiny: elementary number theory over the naturals and integers.
CARRIERS = ("Nat", "Int")

# --- the frozen operator lexicon (F-G) --------------------------------------
# word -> {lean: {carrier: Lean-name}, arity, role, enum_only}
#   lean     -- carrier-indexed Lean name (Nat.gcd != Int.gcd); a carrier absent
#               from this dict is unsupported for the word (e.g. coprime is
#               Nat-only in v1) and refuses at the gate.
#   arity    -- operand count.
#   role     -- "pred" (boolean atom) or "term" (value-producing).
#   enum_only-- True when the operator has NO sound SMT rendering, so any
#               hypothesis using it routes to the decidable-enumeration channel
#               (gcd/coprime); the SMT mirror (WP-D) reads this flag.
# A (word, carrier) pair outside this table refuses at the gate as a first-class
# fragment-miss feeding F4 (D9).
MATH_OPERATORS = {
    "dvd":     {"lean": {"Nat": "Dvd.dvd", "Int": "Dvd.dvd"},
                "arity": 2, "role": "pred", "enum_only": False},
    "even":    {"lean": {"Nat": "Even", "Int": "Even"},
                "arity": 1, "role": "pred", "enum_only": False},
    "odd":     {"lean": {"Nat": "Odd", "Int": "Odd"},
                "arity": 1, "role": "pred", "enum_only": False},
    "gcd":     {"lean": {"Nat": "Nat.gcd", "Int": "Int.gcd"},
                "arity": 2, "role": "term", "enum_only": True},
    "coprime": {"lean": {"Nat": "Nat.Coprime"},
                "arity": 2, "role": "pred", "enum_only": True},
    "mod":     {"lean": {"Nat": "Nat.mod", "Int": "Int.emod"},
                "arity": 2, "role": "term", "enum_only": False},
}

# Built-in term operators (arithmetic).  `-` is carrier-resolved by the compiler
# (Nat.sub is truncated, Int.sub is real; D8) and the SMT mirror renders Nat
# subtraction with an `ite` guard (D8/T4).  `^` takes a LITERAL exponent only
# (SMT-LIB has no exponentiation; D10) -- the compiler unfolds it.
_BUILTIN_TERM_OPS = {"+", "*", "-", "%", "^"}
# Built-in comparison atoms (all binary).
_BUILTIN_ATOM_OPS = {"=", "!=", "<=", "<"}
_CONNECTIVES = {"and", "or", "implies"}

# Derived, single-sourced from MATH_OPERATORS: which words are predicate atoms
# vs term operators, so the pred grammar and the operator table can never drift.
_OP_PRED_WORDS = {w for w, i in MATH_OPERATORS.items() if i["role"] == "pred"}
_OP_TERM_WORDS = {w for w, i in MATH_OPERATORS.items() if i["role"] == "term"}
_ATOM_OPS = _BUILTIN_ATOM_OPS | _OP_PRED_WORDS
_TERM_OPS = _BUILTIN_TERM_OPS | _OP_TERM_WORDS


# --- the ONE source of truth for the LF fragment ----------------------------
# MATH_LF_KINDS maps every accepted logical-form kind to (signature_line,
# force_rule) exactly as reading.LF_KINDS does; the Reading prompt's grammar
# block is rendered from this (F1.3), so prompt grammar is generated, never
# hand-maintained, and the validator's accepted-kind set is derived from the
# same dict.
MATH_LF_KINDS = {
    "object": (
        '{"kind":"object","name":x,"type":"Nat|Int"} '
        '-- a typed discourse referent (the carrier whitelist is Nat, Int).',
        "any force"),
    "operator": (
        '{"kind":"operator","word":w,"carrier":"Nat|Int"} '
        '-- bind a lexicon word (dvd,even,odd,gcd,coprime,mod) at a carrier; '
        'refused if (word,carrier) is outside MATH_OPERATORS (a fragment-miss).',
        "presupposition or choice"),
    "hypothesis": (
        '{"kind":"hypothesis","pred":<pred>} -- a side condition ("n > 0", a '
        'nonzero divisor): the implicit hypotheses autoformalization drops.',
        "demand or presupposition; never choice"),
    "conclusion": (
        '{"kind":"conclusion","pred":<pred>} -- the asserted content, quoted '
        'verbatim from the source.',
        "demand only"),
    "quantifier": (
        '{"kind":"quantifier","binder":"forall|exists","objects":[x,...]} '
        '-- bind declared object referents.',
        "demand or presupposition; never choice"),
    "ambient": (
        '{"kind":"ambient","carrier":"Nat|Int"} -- formalization freedom made '
        'legible: which structure the statement is stated over.',
        "choice only"),
}

# Per-kind allowed field-key sets, keyed by EXACTLY set(MATH_LF_KINDS); the
# import-time assert makes any divergence a hard error (the reading.py pattern).
_MLF_FIELDS = {
    "object": {"kind", "name", "type"},
    "operator": {"kind", "word", "carrier"},
    "hypothesis": {"kind", "pred"},
    "conclusion": {"kind", "pred"},
    "quantifier": {"kind", "binder", "objects"},
    "ambient": {"kind", "carrier"},
}
assert set(_MLF_FIELDS) == set(MATH_LF_KINDS), \
    "MATH_LF_KINDS and _MLF_FIELDS disagree on the accepted LF kinds"

# Per-kind allowed forces (the F1.1 force column), single-sourced so the gate
# and any renderer agree.
_MLF_FORCES = {
    "object": {"demand", "presupposition", "choice"},
    "operator": {"presupposition", "choice"},
    "hypothesis": {"demand", "presupposition"},
    "conclusion": {"demand"},
    "quantifier": {"demand", "presupposition"},
    "ambient": {"choice"},
}
assert set(_MLF_FORCES) == set(MATH_LF_KINDS), \
    "MATH_LF_KINDS and _MLF_FORCES disagree on the accepted LF kinds"


class BadMathReading(Exception):
    pass


class FragmentMiss(BadMathReading):
    """A source construal that does not transcribe into the F1 fragment -- a
    (word, carrier) outside MATH_OPERATORS, an unsupported carrier, etc.  This
    is DEMAND DATA (F4), not a failure to hide: it carries a missing_kind_guess
    so the fragment-miss machinery can rank frontier growth."""

    def __init__(self, message, missing_kind_guess=None):
        super().__init__(message)
        self.missing_kind_guess = missing_kind_guess


@dataclasses.dataclass
class MathReading:
    theorem: str
    statements: list        # list[dict], validated
    source: str

    def by_kind(self, kind):
        return [s for s in self.statements if s["lf"]["kind"] == kind]

    def demands(self):
        return [s for s in self.statements if s["force"] == "demand"]

    def objects(self):
        """name -> carrier for every declared object."""
        return {s["lf"]["name"]: s["lf"]["type"] for s in self.by_kind("object")}

    def ambient_carrier(self):
        """The single ambient carrier (a choice); None if unspecified."""
        amb = self.by_kind("ambient")
        return amb[0]["lf"]["carrier"] if amb else None


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


# --- pred / term AST validation (F-G) ---------------------------------------
def _check_term(term, objects):
    """A value-producing term over declared objects, int literals and the
    built-in/lexicon term operators.  Raises BadMathReading on any malformation
    and FragmentMiss when a lexicon word/carrier is unknown."""
    if not isinstance(term, dict):
        raise BadMathReading(f"term must be an object: {term!r}")
    if "ref" in term:
        if set(term) != {"ref"}:
            raise BadMathReading(f"a ref term takes only 'ref': {sorted(term)}")
        if term["ref"] not in objects:
            raise BadMathReading(
                f"term references undeclared object {term['ref']!r}")
        return
    if "lit" in term:
        if set(term) != {"lit"}:
            raise BadMathReading(f"a lit term takes only 'lit': {sorted(term)}")
        v = term["lit"]
        if not isinstance(v, int) or isinstance(v, bool):
            raise BadMathReading(f"lit must be an integer: {v!r}")
        return
    if "op" not in term or set(term) - {"op", "args"}:
        raise BadMathReading(f"term must be {{ref}}, {{lit}} or {{op,args}}: "
                             f"{term!r}")
    op, args = term["op"], term.get("args", [])
    if op not in _TERM_OPS:
        raise BadMathReading(f"unknown term operator {op!r}")
    if not isinstance(args, list):
        raise BadMathReading(f"{op}: args must be a list")
    if op == "^":
        if len(args) != 2:
            raise BadMathReading("^ takes exactly [base, exponent]")
        _check_term(args[0], objects)
        exp = args[1]
        if not (isinstance(exp, dict) and set(exp) == {"lit"}
                and isinstance(exp["lit"], int) and not isinstance(exp["lit"], bool)
                and exp["lit"] >= 0):
            raise BadMathReading(
                "^ requires a non-negative LITERAL exponent (SMT-LIB has no "
                "exponentiation; a variable exponent is not in the fragment)")
        return
    if op in _OP_TERM_WORDS:
        arity = MATH_OPERATORS[op]["arity"]
        if len(args) != arity:
            raise BadMathReading(f"{op} takes {arity} args, got {len(args)}")
    elif op in ("-", "%"):
        if len(args) != 2:
            raise BadMathReading(f"{op} takes exactly 2 args")
    else:  # + or *
        if len(args) < 2:
            raise BadMathReading(f"{op} takes >= 2 args")
    for a in args:
        _check_term(a, objects)


def _check_pred(pred, objects):
    """A boolean pred over terms: connectives over preds, comparison atoms and
    lexicon predicate words over terms."""
    if not isinstance(pred, dict) or "op" not in pred or set(pred) - {"op", "args"}:
        raise BadMathReading(f"pred must be {{op, args}}: {pred!r}")
    op, args = pred["op"], pred.get("args", [])
    if not isinstance(args, list) or not args:
        raise BadMathReading(f"{op}: args must be a non-empty list")
    if op in _CONNECTIVES:
        if op == "implies" and len(args) != 2:
            raise BadMathReading("implies takes exactly [antecedent, consequent]")
        if op in ("and", "or") and len(args) < 2:
            raise BadMathReading(f"{op} takes >= 2 preds")
        for a in args:
            _check_pred(a, objects)
        return
    if op not in _ATOM_OPS:
        raise BadMathReading(f"unknown atom/connective {op!r}")
    if op in _OP_PRED_WORDS:
        arity = MATH_OPERATORS[op]["arity"]
    else:  # =, !=, <=, < are binary
        arity = 2
    if len(args) != arity:
        raise BadMathReading(f"atom {op} takes {arity} args, got {len(args)}")
    for a in args:
        _check_term(a, objects)


def _check_operator_binding(word, carrier, sid):
    info = MATH_OPERATORS.get(word)
    if info is None:
        raise FragmentMiss(
            f"{sid}: operator word {word!r} is outside MATH_OPERATORS",
            missing_kind_guess=f"operator:{word}")
    if carrier not in info["lean"]:
        raise FragmentMiss(
            f"{sid}: operator {word!r} is not supported over carrier "
            f"{carrier!r} (v1 supports {sorted(info['lean'])})",
            missing_kind_guess=f"operator:{word}@{carrier}")


def split_envelope(text: str):
    """Split an F-A envelope {source, reading:{theorem, statements}} into
    (reading_json_text, source).  Accepts the inner reading form too."""
    doc = json.loads(text)
    if isinstance(doc, dict) and set(doc) >= {"source", "reading"}:
        return json.dumps(doc["reading"]), doc["source"]
    raise BadMathReading("not an envelope {source, reading}")


def parse_math_reading(text: str, source: str) -> MathReading:
    """Validate a MathReading against its source sentence.  Groundedness is
    checked HERE, mechanically, exactly as parse_reading does: every demand and
    presupposition must quote a span that literally occurs in the source; every
    choice must quote nothing.  `text` is the reading JSON
    {theorem, statements}; `source` is the raw sentence."""
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as e:
        raise BadMathReading(f"not valid JSON: {e}")
    if not isinstance(doc, dict) or set(doc) - {"theorem", "statements"}:
        raise BadMathReading("math reading must be {theorem, statements}")
    theorem = doc.get("theorem", "theorem")
    if not (isinstance(theorem, str) and _ID.fullmatch(theorem)):
        raise BadMathReading("theorem must be a lowercase identifier")
    stmts = doc.get("statements")
    if not isinstance(stmts, list) or not (1 <= len(stmts) <= 60):
        raise BadMathReading("statements must be a list of 1..60")
    src_norm = _norm(source)

    seen_ids = set()
    objects = {}            # name -> carrier
    ambient_count = 0
    # first pass: structural validation + declare object referents
    for s in stmts:
        if not isinstance(s, dict) or set(s) - {"id", "force", "quote", "lf"}:
            raise BadMathReading(f"statement keys must be id/force/quote/lf: "
                                 f"{str(s)[:120]}")
        sid, force, quote, lf = (s.get("id"), s.get("force"),
                                 s.get("quote", ""), s.get("lf"))
        if isinstance(sid, int) and not isinstance(sid, bool):
            sid = str(sid)
        if not isinstance(sid, str) or not sid:
            raise BadMathReading(f"statement id must be a non-empty string; "
                                 f"got {s.get('id')!r}")
        if sid in seen_ids:
            raise BadMathReading(f"duplicate statement id {sid!r}")
        seen_ids.add(sid)
        s["id"] = sid
        if force not in FORCES:
            raise BadMathReading(f"{sid}: force must be one of {FORCES}")
        if not isinstance(quote, str):
            raise BadMathReading(f"{sid}: quote must be a string")
        # groundedness: the speech-act trichotomy is enforced here
        if force in ("demand", "presupposition"):
            if not quote.strip():
                raise BadMathReading(
                    f"{sid}: a {force} must quote the source span that "
                    f"carries it")
            if _norm(quote) not in src_norm:
                raise BadMathReading(
                    f"{sid}: quote {quote!r} does not occur in the source "
                    f"-- a {force} may not be fabricated")
        else:  # choice
            if quote.strip():
                raise BadMathReading(
                    f"{sid}: a choice is formalization freedom, not something "
                    f"the text says -- its quote must be empty")
        if not isinstance(lf, dict) or "kind" not in lf:
            raise BadMathReading(f"{sid}: lf must be an object with kind")
        kind = lf["kind"]
        if kind not in MATH_LF_KINDS:
            raise BadMathReading(f"{sid}: unknown lf kind {kind!r}")
        if set(lf) - _MLF_FIELDS[kind]:
            raise BadMathReading(f"{sid}: unexpected lf keys "
                                 f"{sorted(set(lf) - _MLF_FIELDS[kind])}")
        if force not in _MLF_FORCES[kind]:
            raise BadMathReading(
                f"{sid}: a {kind} may carry force "
                f"{sorted(_MLF_FORCES[kind])}, not {force!r}")
        if kind == "object":
            n, ty = lf.get("name"), lf.get("type")
            if not (isinstance(n, str) and _ID.fullmatch(n)) or n in objects:
                raise BadMathReading(f"{sid}: bad/duplicate object name {n!r}")
            if ty not in CARRIERS:
                raise FragmentMiss(
                    f"{sid}: object type {ty!r} is outside the carrier "
                    f"whitelist {CARRIERS}", missing_kind_guess=f"carrier:{ty}")
            objects[n] = ty
        elif kind == "ambient":
            ambient_count += 1
            if lf.get("carrier") not in CARRIERS:
                raise FragmentMiss(
                    f"{sid}: ambient carrier {lf.get('carrier')!r} is outside "
                    f"{CARRIERS}", missing_kind_guess=f"carrier:{lf.get('carrier')}")
    if ambient_count > 1:
        raise BadMathReading("at most one ambient statement")

    # second pass: referential integrity of preds / operators / quantifiers
    for s in stmts:
        sid, lf = s["id"], s["lf"]
        kind = lf["kind"]
        if kind in ("hypothesis", "conclusion"):
            _check_pred(lf.get("pred"), objects)
        elif kind == "operator":
            w, c = lf.get("word"), lf.get("carrier")
            if not isinstance(w, str):
                raise BadMathReading(f"{sid}: operator word must be a string")
            if c not in CARRIERS:
                raise FragmentMiss(
                    f"{sid}: operator carrier {c!r} outside {CARRIERS}",
                    missing_kind_guess=f"carrier:{c}")
            _check_operator_binding(w, c, sid)
        elif kind == "quantifier":
            binder, objs = lf.get("binder"), lf.get("objects")
            if binder not in ("forall", "exists"):
                raise BadMathReading(f"{sid}: binder must be forall/exists")
            if not (isinstance(objs, list) and objs):
                raise BadMathReading(f"{sid}: quantifier needs a non-empty "
                                     f"objects list")
            for o in objs:
                if o not in objects:
                    raise BadMathReading(
                        f"{sid}: quantifier binds undeclared object {o!r}")

    # the asserted content must be present: at least one demanded conclusion
    if not any(s["lf"]["kind"] == "conclusion" and s["force"] == "demand"
               for s in stmts):
        raise BadMathReading(
            "no demanded conclusion -- the theorem's asserted content must "
            "appear as a quoted demand of kind 'conclusion'")
    return MathReading(theorem=theorem, statements=stmts, source=source)
