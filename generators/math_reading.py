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

# The carrier whitelist for typed objects and the ambient structure.  v1 was
# deliberately tiny: elementary number theory over the naturals and integers.
# P3 (PLAN_FRAGMENT §4) adds the RATIONALS as the third carrier, spelled with
# its ASCII Lean type name -- the `ℚ` glyph is escape-gate refused, and the
# compiler emits binders `(x : Rat)` verbatim, so the ASCII spelling is the
# only one that ever reaches Lean.  What Rat buys and what it deliberately
# does NOT (the v1 freeze, all named limits, all first-class misses):
#   * admissible at Rat: `+ - * / ^` and the comparison atoms `= != <= <`
#     (order on the rationals is decidable; the SMT mirror runs QF_LRA/QF_NRA);
#   * REFUSED at Rat: the divisibility family -- `%`/`mod`, dvd, gcd, coprime,
#     even, odd -- none of which has a meaning we are willing to freeze over a
#     field.  Lexicon words refuse through the absence of a "Rat" key in their
#     `lean` tables; the BUILTIN `%` (carrier-blind until now) refuses through
#     `_check_carrier_ops` below;
#   * `/` is the mirror image: a NEW builtin term op admissible ONLY at Rat, so
#     Lean's floor division on ℕ/ℤ can never be reached by a reading (and the
#     census's `operator:div` demand row keeps pricing integer division);
#   * rat:no-coercion -- a Rat object may not share a reading with an integer-
#     carrier object, and a binder (bigop/card) is refused inside a Rat reading,
#     because the index stays pinned Nat.  There is no ℕ→ℚ coercion story this
#     cycle; a mix is a REFUSAL, never a silent cast.
CARRIERS = ("Nat", "Int", "Rat")

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
# (SMT-LIB has no exponentiation; D10) -- the compiler unfolds it.  `/` (P3) is
# the one carrier-RESTRICTED builtin: admissible only at Rat, where Lean's HDiv
# is field division and totalises `q / 0 = 0` (the D9-class convention eval and
# the SMT mirror both mirror exactly).  At Nat/Int it would be floor division --
# a divergence we refuse rather than model, so `/@Nat` / `/@Int` are first-class
# fragment misses (`_check_carrier_ops`).
_BUILTIN_TERM_OPS = {"+", "*", "-", "%", "^", "/"}
# --- the MINING carrier domain of the built-in ops (op_signature) -----------
# DECOUPLED from CARRIERS (P3), for the same reason
# `operator_growth.CARRIERS` is: `op_signature`'s carrier-support field feeds
# ONE consumer, the recurrence miner's op-slot typing, and its job there is to
# stop a `$`-op slot ranging across ops whose carrier domains disagree.  Every
# committed reading is integer-carrier, so widening the built-ins' support to a
# carrier none of them uses would buy no new slot and would silently RE-KEY
# every mined skeleton -- it would also break a coincidence the miner has been
# relying on (the built-in atoms and `dvd` shared a support set), splitting
# clusters for a reason that has nothing to do with what the readings say.
# So the mining domain stays the integer carriers and grows only when readings
# on a new carrier actually exist to mine.
_BUILTIN_CARRIER_SUPPORT = frozenset({"Nat", "Int"})
# Where a builtin's support is genuinely NARROWER still, it is written here.
# `/` is the whole reason the table exists: pinning it to {Rat} makes it
# incompatible with every integer-carrier op, so no mined slot can ever range
# over `{+, /}` and manufacture the integer division the gate refuses.
_BUILTIN_OP_CARRIERS = {"/": frozenset({"Rat"})}
# Built-in comparison atoms (all binary).
_BUILTIN_ATOM_OPS = {"=", "!=", "<=", "<"}
# --- the propositional connectives (P6 grows this set by `not` and `iff`) ---
# P6 (PLAN_FRAGMENT §4) is the first purchase on the CONNECTIVE axis, and the
# only one so far whose whole admissibility argument is that it adds NOTHING to
# any downstream representation:
#   * `iff` is pure DESUGARING.  `a <-> b` IS `(a -> b) and (b -> a)`; every
#     mirror renders it as that conjunction (SMT literally, Lean through the `↔`
#     notation Lean itself unfolds to it), so no channel learns a new idea.
#   * `not` is NEGATION-NORMAL FORM.  It is never a node any representation has
#     to CARRY: it pushes through the connectives by De Morgan
#     (`not (a -> b)` == `a and not b`) until it reaches an atom, and every
#     comparison/parity atom the fragment has carries its dual IN the fragment
#     (`=`/`!=`, `<=`/`<` with the arguments SWAPPED, `even`/`odd`).
# That is why P6 is ADDITIVE-class under §3.1 rule 3 rather than tower-class:
# it needs no new AST node in the reflect slice's `Tm`/`Pd` and no new
# `Decidable` instance, only the vocabulary and the four renderings.
# The freeze that keeps the argument true is `_check_connective_nnf` below: the
# atoms with NO dual in the fragment (`dvd`, `coprime`) refuse under a negation
# as a first-class `not:<op>-no-dual` FragmentMiss -- demand data for the
# purchase that would buy a negation constructor, never a silent widening.
_CONNECTIVES = {"and", "or", "implies", "not", "iff"}
# Per-connective operand count; None = variadic (any width >= 2).  Single
# source for `op_signature`'s arity field and `_check_pred`'s shape check, so
# the miner's op-slot typing and the gate can never disagree about a width.
_CONNECTIVE_ARITY = {"and": None, "or": None, "implies": 2, "iff": 2, "not": 1}

# --- bounded big-operators (P1: the one binding AST node CLASS) --------------
# {"op":"bigsum"|"bigprod","args":[{"var":i},{"lit":lo},{"lit":hi},body]}
# folds `body` over the index i = lo..hi (inclusive; lo > hi is the empty fold:
# 0 for bigsum, 1 for bigprod).  NOT an operator word: it BINDS an index, which
# no MATH_OPERATORS row can.  The whole class is admissible because iteration
# is bounded by NON-NEGATIVE LITERAL bounds (the ^ / D10 discipline): decidable
# by exhaustive computation (eval iterates), SMT by unrolling (the mirror
# substitutes each concrete index), Lean via Finset.Icc.  v1 freezes:
#   * bounds are non-negative int literals -- a symbolic bound is a
#     first-class FragmentMiss (`bigop:symbolic-bound`), the demand class the
#     census prices under sequences-sums;
#   * no nesting -- a big-operator inside a big-operator body is a
#     FragmentMiss (`bigop:nested`), keeping the reflect slice's single-index
#     representation sound;
#   * the bound index is Nat-carrier (its values are the non-negative bounds'
#     range) and may not collide with any declared object, so scope is
#     extension-only and every ref walker can treat it uniformly.
_BIGOPS = {"bigsum", "bigprod"}

# --- bounded Finset carrier + cardinality (P2: rides P1's binding machinery) --
# The second structural extension in the PLAN_FRAGMENT §4 queue (sets-
# cardinality).  A `setbuild` is a bounded finite SET node -- a filtered literal
# interval -- and `card` is the term operator that brings it back into the
# arithmetic fragment as a Nat value:
#   set  := {"op":"setbuild","args":[{"var":i},{"lit":lo},{"lit":hi},filter]}
#   card := {"op":"card","args":[set]}                       # a value-term
# `setbuild` denotes `{ i in Finset.Icc lo hi | filter }` (the index Nat), and
# `card` its cardinality.  This is admissible for exactly P1's reason -- the
# LITERAL bounds make the set finite and exactly enumerable: eval counts, the
# SMT mirror unrolls card to a sum of `(ite filter 1 0)` indicators (the D10
# discipline again), Lean via `Finset.card (Finset.filter ...)`.  A `setbuild`
# is NOT a value: it may appear ONLY as `card`'s argument (the sort discipline
# -- exactly as a {"var"} leaf may appear only as a big-operator's first arg).
# v1 freezes mirror P1's: a symbolic bound is `set:symbolic-bound`, and any
# binder (setbuild/card/bigop) inside a setbuild filter -- or a setbuild inside
# a binder body -- is `set:nested` (the single-binder freeze that keeps the
# reflect slice's unroll sound).  card's filter may be object-dependent (that is
# what makes counting interesting to the SMT channel); an object-dependent
# filter is a named reflect skip (`card:object-filter`), not a widening.
_SETOPS = {"card", "setbuild"}

# --- named sets by comprehension + the membership atom (P9) ------------------
# The PLAN_FRAGMENT §4 P9 row (`set objects: a set carrier and its membership
# atom`) is priced against the `refused:set-membership` group, and it is the
# SECOND row whose declared bill turns out to be priced against two different
# objects -- the P8 shape, measured again in tests/test_set_object_class.py.
#
#   setdef := {"kind":"setdef","name":s,"param":x,"body":<pred>}
#   mem    := {"op":"mem","args":[<term>, {"set":s}]}
#
# `setdef` lets a source say "let a be {n | n even}" once and then write
# `k in a` as an ATOM.  It is the PRED-layer twin of P8's `definition` (which is
# the same idea over TERMS), and it is admissible for exactly P8's reason: a
# comprehension with an explicit body is ELIMINABLE.  `e in {x | phi(x)}` IS
# `phi(e)`, by capture-free substitution, so the membership is desugared HERE,
# once, at the gate, and the evaluator, the SMT mirror, the Lean emitter and the
# reflect slice see a pred with no membership in it at all.  Nothing enters
# `Tm`/`Pd`, `decDenote` keeps deciding by computation, and §3.1 rule 3(a) is
# not reached -- which is why this slice is additive-desugaring and NOT the
# tower-class purchase the row's headline declares.
#
# WHAT THIS DELIBERATELY DOES NOT BUY, because the elimination is exactly what
# stops working there -- each a first-class FragmentMiss, i.e. the demand data
# that keeps the tower-class residue of the row priced instead of claimed:
#   * `set:free-set-variable` -- an object whose TYPE is a set (`Set Int`, an
#     arbitrary `U` the source never gives a body for).  A set variable has no
#     comprehension to substitute, so membership in it survives unfolding: it
#     needs a genuine second-order carrier value, an uninterpreted predicate in
#     the SMT mirror and a `Pd` constructor in the reflect slice.  THAT is the
#     tower-class purchase, and it stays open and priced.
#   * `set:set-valued-param` -- a comprehension whose PARAMETER ranges over
#     sets (a powerset comprehension, `{s : P(N) | 3 in s}`).  Its body applies
#     membership to a set the reading has no body for, so the same wall.
# The three freezes below mirror `_check_definition`'s one for one, and for the
# same reason in each case: they are what keep the elimination TOTAL.
#   * `setdef:recursive-body` -- the body may not mention the set being defined
#     nor any set defined LATER (mutual recursion wearing a different hat).
#   * `setdef:binder-body` -- no big-operator and no set binder inside a body,
#     which makes capture IMPOSSIBLE BY CONSTRUCTION rather than by argument.
#   * `setdef:open-body` -- the body may mention its PARAMETER only, never a
#     declared object.  A body reading an ambient object is not a set, it is a
#     hypothesis about one.
# Set ALGEBRA (union, intersection, complement, the empty set, set equality) is
# deliberately NOT new vocabulary: extensionality states each of them with the
# connectives the fragment already has (`x in a and x in b`, `not (x in a)`,
# `forall x, x in a <-> x in b`), and P6 bought those.  Adding algebra NODES
# would buy a second spelling of preds we can already write -- and would have to
# survive unfolding, which is the tower-class purchase again.
_MEM_OP = "mem"
# The SET-typed carrier strings a source reaches for when it means an arbitrary
# set (`Set Int`, `Set Nat`, and the powerset spelling `Set (Set Int)`).  These
# are REFUSED -- the tower-class residue named above -- and the pattern exists
# only so `_carrier_miss_guess` can price them under ONE signal.
_SET_CARRIER = re.compile(r"Set[ (].*")

# --- the parametric residue carrier (P4: `ZMod n`) ---------------------------
# The third PLAN_FRAGMENT §4 structural purchase, and the first that grows the
# CARRIER axis rather than the node axis.  `CARRIERS` above stays a tuple of
# BARE carrier names, because ZMod is a FAMILY and not a name: its members are
# the strings `ZMod n` for a LITERAL modulus n >= 1.  The space form is the
# exact Lean type text, and the compiler's binders emit an object's declared
# type verbatim, so `(x : ZMod 7)` costs the emitter no new rule.  A PREDICATE
# therefore carries the family: every `ty not in CARRIERS` site pairs with
# `_zmod_modulus(ty) is None`, and nothing that ENUMERATES CARRIERS (the miner's
# op-slot typing, the operator-growth battery domain, the census's surface
# aliases, the choice-space product) is widened by this purchase -- the carrier
# whitelist's consumers keep their pre-P4 behaviour byte for byte.
#
# v1 freezes, mirroring P1/P2's literal-bound discipline (bounded = decidable):
#   * the modulus is a LITERAL >= 1.  `ZMod n` is `carrier:zmod-symbolic-
#     modulus` and `ZMod 0` (which Lean reads as the integers, not a finite
#     quotient) is `carrier:zmod-zero-modulus` -- two first-class demand signals
#     the frontier prices APART, never one silent widening.  A literal modulus
#     is what makes the domain sweep EXACT: `range(0, n)` is the whole carrier,
#     so a pure-ZMod bounded gate is a COMPLETE decision, not a sample.
#   * the admissible operations are `+ * - ^` and the atoms `= !=` ONLY.
#     `ZMod n` is an unordered commutative ring, so the order atoms `<= <` and
#     the whole mod/divisibility family (`% mod dvd gcd coprime even odd`) have
#     no meaning on congruence classes and refuse at `operator:<op>@ZMod <n>`.
#   * no binder node (bigsum/bigprod/card/setbuild) inside a residue reading:
#     the bound index carrier is pinned Nat (P1's freeze), so a fold inside a
#     ZMod reading would mix carriers behind every walker's back
#     (`zmod:binder-index-carrier`).
#   * ONE carrier per READING (not per pred -- both mirrors resolve the modulus
#     from the object map, so the discipline has to hold reading-wide or an
#     Int atom in a residue reading gets silently wrapped).  ZMod mixed with
#     Nat/Int -- or with a DIFFERENT modulus -- is the B1 mirror-divergence
#     class; `ZMod 5` and `ZMod 7` are distinct carrier strings, so the second
#     case falls out of the first.
_ZMOD_ADMISSIBLE_TERM_OPS = frozenset({"+", "*", "-", "^"})
_ZMOD_ADMISSIBLE_ATOM_OPS = frozenset({"=", "!="})
_ZMOD_LITERAL = re.compile(r"ZMod [1-9][0-9]*")
_ZMOD_ZERO = re.compile(r"ZMod 0+")
_ZMOD_SYMBOLIC = re.compile(r"ZMod [A-Za-z_][A-Za-z0-9_]*")


def _zmod_modulus(ty):
    """The literal modulus of an ADMISSIBLE `ZMod n` carrier string, or None for
    anything else (every non-ZMod carrier AND every refused ZMod shape).  THE
    predicate that carries the parametric family: it is what each carrier check
    pairs with `ty not in CARRIERS`, so ZMod never enters the bare-name tuple
    and no CARRIERS consumer changes behaviour."""
    if not isinstance(ty, str) or not _ZMOD_LITERAL.fullmatch(ty):
        return None
    return int(ty.split(" ", 1)[1])


def _carrier_miss_guess(ty):
    """The `missing_kind_guess` for a REFUSED carrier string.  A ZMod-SHAPED
    string that is not an admissible `ZMod n` splits into its own two signals,
    so the frontier prices a symbolic modulus and the degenerate n = 0 apart
    (a split is non-destructive: neither signal is the other's excuse).  Every
    other refused carrier keeps the generic `carrier:<ty>` shape the fragment-
    miss machinery has always emitted.

    P9 splits one more off the generic shape for the same non-destructive
    reason: a SET-typed object is the tower-class residue of the
    `refusal-set-carrier` row -- an arbitrary `U` the source never gives a
    comprehension for, whose membership therefore SURVIVES unfolding -- and
    naming it `set:free-set-variable` prices it as the distinct demand it is
    instead of burying it in `carrier:Set Int` / `carrier:Set Nat`, where the
    carrier STRING would split one demand into a row per element type."""
    if isinstance(ty, str):
        if _ZMOD_ZERO.fullmatch(ty):
            return "carrier:zmod-zero-modulus"
        if _ZMOD_SYMBOLIC.fullmatch(ty):
            return "carrier:zmod-symbolic-modulus"
        if _SET_CARRIER.fullmatch(ty):
            return "set:free-set-variable"
    return f"carrier:{ty}"


# Derived, single-sourced from MATH_OPERATORS: which words are predicate atoms
# vs term operators, so the pred grammar and the operator table can never drift.
_OP_PRED_WORDS = {w for w, i in MATH_OPERATORS.items() if i["role"] == "pred"}
_OP_TERM_WORDS = {w for w, i in MATH_OPERATORS.items() if i["role"] == "term"}
_ATOM_OPS = _BUILTIN_ATOM_OPS | _OP_PRED_WORDS
_TERM_OPS = _BUILTIN_TERM_OPS | _OP_TERM_WORDS

# The three semantic ROLES an operator word carries.  Kept distinct so the
# miner's op-slot typing (recurrence._op_slots_admissible) can never let a slot
# range across the category boundary -- a term (a value), a pred (a boolean over
# values) and a connective (a boolean over booleans) are not interchangeable
# even at equal arity.
_ROLE_TERM = "term"                 # value-producing (arithmetic, gcd, mod)
_ROLE_PRED = "pred"                 # boolean atom over terms (=, dvd, even, ...)
_ROLE_CONN = "connective"           # boolean over booleans (and, or, implies)


def op_signature(word):
    """The (role, arity, carrier_support) SIGNATURE of one operator word -- the
    SINGLE SOURCE for the recurrence miner's op-slot typing (COMPRESSION.md
    §11.9 / §11.3).  A `$`-param at an op-key position is legal only when every
    witnessed binding shares this signature, so a mined slot can never range
    over ops whose meaning, arity, or carrier-support disagree (the
    Int-mined-`-`-matching-Nat hazard §11.3 names).

      role   -- `_ROLE_TERM` / `_ROLE_PRED` / `_ROLE_CONN` (above).
      arity  -- the fixed operand count, or None for the variadic connectors
                (`+`, `*`, `and`, `or`) which accept any width >= 2.
      carrier_support -- the frozenset of carriers the op is DEFINED over IN
                THE MINING DOMAIN.  Lexicon words read it from
                `MATH_OPERATORS[word]["lean"]` keys (so coprime, Nat-only in
                v1, is {Nat} while dvd is {Nat, Int}); built-in arithmetic and
                comparison read `_BUILTIN_CARRIER_SUPPORT`, deliberately the
                integer carriers rather than all of `CARRIERS` (see that
                constant), narrowed further by `_BUILTIN_OP_CARRIERS` -- `/` is
                {Rat} alone (P3), so a mined `$`-op slot can never range over
                `/` together with an integer-carrier op and thereby manufacture
                the integer division the gate refuses.

    Returns None for a word outside the lexicon and the built-in sets -- the
    caller treats an unknown op as incompatible (refuse the slot).  The
    big-operators (`bigsum`/`bigprod`) DELIBERATELY return None: they bind an
    index (their first arg is a {"var"} declaration, not a term), so a mined
    slot must never range over them -- the miner's self-containment rule
    refuses the {"var"} leaf independently; this is the belt to that brace.
    The set nodes (`card`/`setbuild`, P2) return None for the same reason:
    `setbuild` binds an index and is not a value, and `card`'s sole argument
    must be a `setbuild`, so no mined slot may ever range over either."""
    if word in _BIGOPS or word in _SETOPS:
        return None
    info = MATH_OPERATORS.get(word)
    if info is not None:
        return (info["role"], info["arity"], frozenset(info["lean"].keys()))
    if word in _BUILTIN_TERM_OPS:
        arity = None if word in ("+", "*") else 2
        return (_ROLE_TERM, arity,
                _BUILTIN_OP_CARRIERS.get(word, _BUILTIN_CARRIER_SUPPORT))
    if word in _BUILTIN_ATOM_OPS:
        return (_ROLE_PRED, 2, _BUILTIN_CARRIER_SUPPORT)
    if word in _CONNECTIVES:
        return (_ROLE_CONN, _CONNECTIVE_ARITY[word], _BUILTIN_CARRIER_SUPPORT)
    return None


# --- the ONE source of truth for the LF fragment ----------------------------
# MATH_LF_KINDS maps every accepted logical-form kind to (signature_line,
# force_rule) exactly as reading.LF_KINDS does; the Reading prompt's grammar
# block is rendered from this (F1.3), so prompt grammar is generated, never
# hand-maintained, and the validator's accepted-kind set is derived from the
# same dict.
MATH_LF_KINDS = {
    "object": (
        '{"kind":"object","name":x,"type":"Nat|Int|Rat|ZMod <n>"} '
        '-- a typed discourse referent (the carrier whitelist is Nat, Int, '
        'Rat, plus the parametric residue carrier ZMod <n> at a LITERAL '
        'modulus n >= 1).',
        "any force"),
    "operator": (
        '{"kind":"operator","word":w,"carrier":"Nat|Int|Rat|ZMod <n>"} '
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
        '{"kind":"ambient","carrier":"Nat|Int|Rat|ZMod <n>"} -- formalization '
        'freedom made legible: which structure the statement is stated over.',
        "choice only"),
    "definition": (
        '{"kind":"definition","name":f,"params":[x,...],"body":<term>} '
        '-- P8: the source NAMES a function and gives it an EXPLICIT body over '
        'its own parameters; write f(args) as the term {"app":f,"args":[...]}. '
        'The body is a term over the PARAMETERS ONLY -- it may not mention a '
        'declared object, may not mention f (a recurrence is '
        'funcdef:recursive-body, not in the fragment) and may not contain a '
        'big-operator or set binder.',
        "presupposition or choice"),
    "setdef": (
        '{"kind":"setdef","name":s,"param":x,"body":<pred>} '
        '-- P9: the source NAMES a set by a COMPREHENSION over one parameter; '
        'write membership as the atom {"op":"mem","args":[<term>,{"set":s}]}. '
        'The body is a pred over the PARAMETER ONLY -- it may not mention a '
        'declared object (setdef:open-body), may not mention s or a set '
        'defined later (setdef:recursive-body) and may not contain a '
        'big-operator or set binder (setdef:binder-body).  Union, '
        'intersection, complement, the empty set and set equality are stated '
        'EXTENSIONALLY with the connectives, not as new nodes.',
        "presupposition or choice"),
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
    "definition": {"kind", "name", "params", "body"},
    "setdef": {"kind", "name", "param", "body"},
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
    "definition": {"presupposition", "choice"},
    "setdef": {"presupposition", "choice"},
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

    def definitions(self):
        """P8: name -> {params, body} for every named function symbol the
        source defined.  The RECORD survives in the reading (it is what the
        source said, and it carries the quote that grounds it); the
        APPLICATIONS do not -- `parse_math_reading` has already eliminated
        them by substitution, so every pred a consumer sees is app-free."""
        return {s["lf"]["name"]: {"params": list(s["lf"]["params"]),
                                  "body": s["lf"]["body"]}
                for s in self.by_kind("definition")}

    def setdefs(self):
        """P9: name -> {param, body} for every named set the source defined by
        a comprehension.  Same discipline as `definitions()`: the RECORD
        survives (it is what the source said, and it carries the quote that
        grounds it) while the MEMBERSHIPS do not -- `parse_math_reading` has
        already eliminated them by substitution, so every pred a consumer sees
        is membership-free."""
        return {s["lf"]["name"]: {"param": s["lf"]["param"],
                                  "body": s["lf"]["body"]}
                for s in self.by_kind("setdef")}


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


# --- pred / term AST validation (F-G) ---------------------------------------
def _check_bigop(term, objects, in_bigop, definitions=None):
    """The bounded big-operator node (P1).  Shape, bounds, index scope:
    args = [{"var": i}, {"lit": lo}, {"lit": hi}, body], lo/hi non-negative
    literals, the index Nat-carrier and collision-free, the body a term over
    objects + the index.  Symbolic bounds and nesting are first-class
    FragmentMisses (demand data), never silent widenings."""
    op, args = term["op"], term.get("args", [])
    if in_bigop:
        raise FragmentMiss(
            f"{op}: a big-operator inside a big-operator body is outside the "
            f"v1 fragment (single-index freeze)",
            missing_kind_guess="bigop:nested")
    if not isinstance(args, list) or len(args) != 4:
        raise BadMathReading(
            f"{op} takes exactly [{{var}}, {{lit lo}}, {{lit hi}}, body]")
    var_decl = args[0]
    if not (isinstance(var_decl, dict) and set(var_decl) == {"var"}
            and isinstance(var_decl.get("var"), str)
            and _ID.fullmatch(var_decl["var"])):
        raise BadMathReading(
            f"{op}: first arg must declare the bound index as "
            f'{{"var": name}} with a lowercase-identifier name')
    var = var_decl["var"]
    if var in objects:
        raise BadMathReading(
            f"{op}: bound index {var!r} collides with a declared object -- "
            f"the fragment refuses shadowing")
    for which, b in (("lo", args[1]), ("hi", args[2])):
        if not (isinstance(b, dict) and set(b) == {"lit"}
                and isinstance(b.get("lit"), int)
                and not isinstance(b["lit"], bool)):
            raise FragmentMiss(
                f"{op}: {which} bound must be a LITERAL -- bounded iteration "
                f"is what makes the class decidable (exhaustive computation, "
                f"SMT unrolling); a symbolic bound is not in the fragment",
                missing_kind_guess="bigop:symbolic-bound")
        if b["lit"] < 0:
            raise BadMathReading(
                f"{op}: {which} bound must be non-negative (the index is "
                f"Nat-carrier)")
    _check_term(args[3], {**objects, var: "Nat"}, in_bigop=True,
                definitions=definitions)


def _check_setbuild(term, objects, in_bigop, definitions=None):
    """The bounded Finset carrier node (P2): a filtered literal interval
    `{ i in Icc lo hi | filter }`.  Same bound/index discipline as a big-
    operator, but the fourth arg is a PRED (the filter), and the index enters
    the filter's scope at carrier Nat.  A setbuild inside any binder body/filter
    is `set:nested`; a symbolic bound is `set:symbolic-bound` -- both demand
    data, never silent widenings."""
    op, args = term["op"], term.get("args", [])
    if in_bigop:
        raise FragmentMiss(
            f"{op}: a set inside a binder body/filter is outside the v1 "
            f"fragment (single-binder freeze -- keeps the reflect unroll sound)",
            missing_kind_guess="set:nested")
    if not isinstance(args, list) or len(args) != 4:
        raise BadMathReading(
            f"{op} takes exactly [{{var}}, {{lit lo}}, {{lit hi}}, filter-pred]")
    var_decl = args[0]
    if not (isinstance(var_decl, dict) and set(var_decl) == {"var"}
            and isinstance(var_decl.get("var"), str)
            and _ID.fullmatch(var_decl["var"])):
        raise BadMathReading(
            f"{op}: first arg must declare the bound index as "
            f'{{"var": name}} with a lowercase-identifier name')
    var = var_decl["var"]
    if var in objects:
        raise BadMathReading(
            f"{op}: bound index {var!r} collides with a declared object -- "
            f"the fragment refuses shadowing")
    for which, b in (("lo", args[1]), ("hi", args[2])):
        if not (isinstance(b, dict) and set(b) == {"lit"}
                and isinstance(b.get("lit"), int)
                and not isinstance(b["lit"], bool)):
            raise FragmentMiss(
                f"{op}: {which} bound must be a LITERAL -- bounded, exactly "
                f"enumerable sets are what make cardinality decidable "
                f"(eval counts, SMT unrolls the indicator sum); a symbolic "
                f"bound is not in the fragment",
                missing_kind_guess="set:symbolic-bound")
        if b["lit"] < 0:
            raise BadMathReading(
                f"{op}: {which} bound must be non-negative (the index is "
                f"Nat-carrier)")
    _check_pred(args[3], {**objects, var: "Nat"}, in_bigop=True,
                definitions=definitions)


def _check_card(term, objects, in_bigop, definitions=None):
    """The cardinality term (P2): `card` takes exactly one argument, which MUST
    be a `setbuild` set-node.  `card` is a value-term (its Nat cardinality); a
    `setbuild` is a set and never a value, so this is the ONLY place one may
    appear."""
    op, args = term["op"], term.get("args", [])
    if not isinstance(args, list) or len(args) != 1:
        raise BadMathReading(f"{op} takes exactly [set-node]")
    setnode = args[0]
    if not (isinstance(setnode, dict) and setnode.get("op") == "setbuild"):
        raise BadMathReading(
            f"{op}'s argument must be a `setbuild` set-node (a bounded, "
            f"filtered interval) -- no other term denotes a set")
    _check_setbuild(setnode, objects, in_bigop, definitions)


def _check_definition(lf, sid, objects, definitions, param_carrier):
    """P8 -- a NAMED FUNCTION SYMBOL given by an EXPLICIT body over its own
    parameters.  This is a DEFINITIONAL extension, and the word is load-bearing
    in both directions.

    WHAT IT IS.  `{"kind":"definition","name":"b","params":["k"],"body":<term>}`
    lets a source say "let b(k) = 2*k + 1" once and then write `b(n)`,
    `b(n+1)`, `b(0)` as terms.  Before this, the only thing the fragment could
    do with a named function was DECLARE ITS VALUES as objects at literal
    indices and constrain them by hypotheses -- the unfolding shape measured in
    tests/test_function_symbol_class.py, which works at `b_5` and cannot reach
    `for all n, b_n`.

    WHY IT COSTS NO NEW REPRESENTATION -- the finding, and it is the same shape
    as P6's.  `tests/test_function_symbol_class.py` finding (4) priced this rung
    at an APPLICATION NODE in `tools/FgReflect.lean`'s `Tm` plus a new
    `Decidable` story, on the argument that "an uninterpreted symbol constrained
    only by axioms has no computable interpretation".  That is exactly right
    ABOUT AN UNINTERPRETED SYMBOL, and it is why THIS row does not buy one.  A
    symbol with an explicit, non-recursive body is ELIMINABLE: every application
    rewrites, by capture-free substitution, to a term the fragment already had.
    So the reading is desugared HERE, once, at the gate, and the evaluator, the
    SMT mirror, the Lean emitter and the reflect slice see a term with no
    application in it at all.  Nothing enters `Tm`/`Pd`, `decDenote` keeps
    deciding by computation, and PLAN_FRAGMENT §3.1 rule 3(a) is not reached.
    Conservativity is not argued in prose either: it is the substitution, and
    tests/test_funcdef_battery.py measures the desugared reading against the
    hand-unfolded one at all four consumers.

    THE THREE FREEZES, each a first-class FragmentMiss (demand data, never a
    silent widening), and each one the thing that keeps the elimination TOTAL:

      * `funcdef:recursive-body` -- the body may not mention the function being
        defined, nor any function defined LATER in the reading (which is
        mutual recursion wearing a different hat).  A recurrence is the
        headline demand this row does NOT buy: `a_{k+1} = a_k + 2 a_{k-1}` has
        no finite unfolding at a symbolic index, and reaching it needs
        well-founded recursion and a termination argument -- a different
        purchase, priced by this refusal rather than claimed by this one.
      * `funcdef:binder-body` -- no big-operator and no set binder inside a
        body.  This is what makes capture IMPOSSIBLE BY CONSTRUCTION rather
        than by a delicate argument: a body with no binder has nothing to
        capture an argument's free names, so substitution is capture-free for
        structural reasons a reader can check.
      * `funcdef:open-body` -- the body may mention its PARAMETERS ONLY, never
        a declared object.  A body that reads an ambient object is not a
        definition, it is a hypothesis about one, and the two have different
        conservativity stories.

    `param_carrier` types the parameters for the STRUCTURAL walk only.  Carrier
    admissibility is deliberately NOT decided here: it is decided after
    unfolding by `_check_carrier_ops`, at the USE site, where the actual
    argument's carrier is known.  Deciding it twice is how two rules drift."""
    name, params, body = lf.get("name"), lf.get("params"), lf.get("body")
    if not (isinstance(name, str) and _ID.fullmatch(name)):
        raise BadMathReading(
            f"{sid}: definition name must be a lowercase identifier: {name!r}")
    if name in definitions:
        raise BadMathReading(f"{sid}: duplicate definition {name!r}")
    if name in objects:
        raise BadMathReading(
            f"{sid}: definition {name!r} collides with a declared object -- "
            f"the fragment refuses shadowing")
    if not (isinstance(params, list) and params):
        raise BadMathReading(
            f"{sid}: definition {name!r} needs a non-empty params list")
    seen = set()
    for p in params:
        if not (isinstance(p, str) and _ID.fullmatch(p)):
            raise BadMathReading(
                f"{sid}: parameter names must be lowercase identifiers: {p!r}")
        if p in seen:
            raise BadMathReading(
                f"{sid}: definition {name!r} repeats parameter {p!r}")
        if p in objects:
            raise BadMathReading(
                f"{sid}: parameter {p!r} collides with a declared object -- "
                f"the fragment refuses shadowing")
        seen.add(p)
    if body is None:
        raise BadMathReading(f"{sid}: definition {name!r} needs a body")
    # the body's scope is the PARAMETERS, and nothing else: an object reference
    # inside a body is `funcdef:open-body`, raised by the ref branch of
    # _check_term through this scope rather than by a second rule here.
    _check_term(body, {p: param_carrier for p in params},
                definitions=definitions, in_defbody=name)
    # store the body already unfolded against the EARLIER definitions.  That is
    # what makes `_unfold_term` a single pass with a fixed point rather than a
    # rewrite loop needing its own termination argument.
    return {"params": list(params), "body": _unfold_term(body, definitions)}


def _check_setdef(lf, sid, objects, definitions, setdefs, param_carrier):
    """P9 -- a NAMED SET given by an explicit COMPREHENSION over one parameter.
    The pred-layer twin of `_check_definition`, and deliberately its mirror
    image line for line: where that one names a FUNCTION by a term body, this
    names a SET by a pred body, and where that one eliminates `app` this one
    eliminates `mem`.

    WHY IT COSTS NO NEW REPRESENTATION.  `e in {x | phi(x)}` IS `phi(e)`.  The
    membership atom is therefore eliminable by exactly P8's capture-free
    substitution, so it never reaches the evaluator, the SMT mirror, the Lean
    emitter or the reflect slice -- all four stay byte-unchanged, as
    tests/test_setdef_battery.py measures against a HAND-UNFOLDED twin rather
    than asserting in prose.

    WHAT IT DOES NOT BUY, and the distinction is the whole honesty of the row:
    a set the source never gives a body for.  `refusal-set-carrier` is priced
    against `09_Sets#definition-003`, whose `U` and `V` are ARBITRARY sets --
    membership in them survives unfolding, and reaching it needs an
    uninterpreted predicate in the mirror and a `Pd` constructor in the slice.
    That refuses at the carrier gate as `set:free-set-variable`, and a
    comprehension whose PARAMETER is used as a set refuses here as
    `set:set-valued-param`.  Both stay open, priced, and named.

    `param_carrier` types the parameter for the STRUCTURAL walk only; carrier
    admissibility is decided post-unfold at the USE site, where the element
    term's real carrier is known -- deciding it twice is how two rules drift."""
    name, param, body = lf.get("name"), lf.get("param"), lf.get("body")
    if not (isinstance(name, str) and _ID.fullmatch(name)):
        raise BadMathReading(
            f"{sid}: setdef name must be a lowercase identifier: {name!r}")
    if name in setdefs:
        raise BadMathReading(f"{sid}: duplicate setdef {name!r}")
    if name in definitions:
        raise BadMathReading(
            f"{sid}: setdef {name!r} collides with a definition of the same "
            f"name -- the fragment refuses shadowing")
    if name in objects:
        raise BadMathReading(
            f"{sid}: setdef {name!r} collides with a declared object -- "
            f"the fragment refuses shadowing")
    if not (isinstance(param, str) and _ID.fullmatch(param)):
        raise BadMathReading(
            f"{sid}: setdef {name!r} needs a parameter name (a lowercase "
            f"identifier): {param!r}")
    if param in objects:
        raise BadMathReading(
            f"{sid}: parameter {param!r} collides with a declared object -- "
            f"the fragment refuses shadowing")
    if body is None:
        raise BadMathReading(f"{sid}: setdef {name!r} needs a body")
    # The body's scope is the PARAMETER, and nothing else: an object reference
    # inside it is `setdef:open-body`, raised by the ref branch of _check_term
    # through this scope rather than by a second rule here.
    _check_pred(body, {param: param_carrier}, definitions=definitions,
                in_defbody=name, setdefs=setdefs, in_setbody=(name, param))
    # store the body already unfolded against the EARLIER setdefs -- what makes
    # `_unfold_pred` a single pass with a fixed point rather than a rewrite
    # loop needing its own termination argument (the P8 argument verbatim).
    return {"param": param,
            "body": _unfold_mem(_unfold_pred(body, definitions), setdefs)}


def _unfold_mem(pred, setdefs):
    """Eliminate every `{"op":"mem","args":[e,{"set":s}]}` by capture-free
    substitution of s's comprehension body at the element term e.  Total and
    terminating for P8's reason exactly: each setdef's body is itself already
    membership-free when it is stored (bodies are unfolded against the setdefs
    declared BEFORE them, and `setdef:recursive-body` refuses the rest), so one
    pass reaches a fixed point and no recursion can diverge."""
    if not isinstance(pred, dict) or "op" not in pred:
        return pred
    op = pred["op"]
    if op in _CONNECTIVES:
        return {"op": op, "args": [_unfold_mem(a, setdefs)
                                   for a in pred.get("args", [])]}
    if op == _MEM_OP:
        elem, setref = pred["args"][0], pred["args"][1]
        d = setdefs[setref["set"]]
        return _substitute_pred(d["body"], {d["param"]: elem})
    return pred


def _substitute_pred(pred, bound):
    """Replace parameter refs by their argument TERMS throughout a pred.  A
    setdef body carries no binder (`setdef:binder-body`) and no membership left
    (it was unfolded when stored), so there is nothing here to capture and this
    is a plain structural rewrite -- P8's `_substitute` at the pred layer."""
    if not isinstance(pred, dict) or "op" not in pred:
        return pred
    op = pred["op"]
    if op in _CONNECTIVES:
        return {"op": op, "args": [_substitute_pred(a, bound)
                                   for a in pred.get("args", [])]}
    return {"op": op, "args": [_substitute(a, bound)
                               for a in pred.get("args", [])]}


def _unfold_term(term, definitions):
    """Eliminate every `{"app": f, "args": [...]}` by capture-free substitution
    of f's body.  Total and terminating: each definition's body is itself
    already app-free when it is stored (bodies are unfolded against the
    definitions declared BEFORE them, and `funcdef:recursive-body` refuses the
    rest), so one pass reaches a fixed point and no recursion can diverge."""
    if not isinstance(term, dict):
        return term
    if "app" in term:
        d = definitions[term["app"]]
        bound = dict(zip(d["params"],
                         [_unfold_term(a, definitions) for a in term["args"]]))
        return _substitute(d["body"], bound)
    if "op" in term:
        return {"op": term["op"],
                "args": [_unfold_term(a, definitions)
                         for a in term.get("args", [])]}
    return term


def _substitute(term, bound):
    """Replace parameter refs by their argument terms.  A body carries no
    binder (`funcdef:binder-body`), so there is nothing here to capture and
    this is a plain structural rewrite."""
    if not isinstance(term, dict):
        return term
    if "ref" in term and term["ref"] in bound:
        return bound[term["ref"]]
    if "op" in term:
        return {"op": term["op"],
                "args": [_substitute(a, bound) for a in term.get("args", [])]}
    return term


def _unfold_pred(pred, definitions):
    """`_unfold_term` lifted to the pred layer."""
    if not isinstance(pred, dict) or "op" not in pred:
        return pred
    op = pred["op"]
    if op in _CONNECTIVES:
        return {"op": op, "args": [_unfold_pred(a, definitions)
                                   for a in pred.get("args", [])]}
    return {"op": op, "args": [_unfold_term(a, definitions)
                               for a in pred.get("args", [])]}


def _check_term(term, objects, in_bigop=False, definitions=None,
                in_defbody=None, in_setbody=None):
    """A value-producing term over declared objects, int literals and the
    built-in/lexicon term operators.  Raises BadMathReading on any malformation
    and FragmentMiss when a lexicon word/carrier is unknown.  `objects` is the
    scope (declared objects, extended with the bound index inside a
    big-operator body); `in_bigop` refuses nested big-operators.  `definitions`
    is the P8 function environment in scope (name -> {params, body}); when
    `in_defbody` is a name, this walk is inside THAT definition's body and the
    three P8 freezes apply.  `in_setbody` (P9) is the `(name, param)` of the
    SETDEF whose body this walk is inside; it selects which of the two mirror
    freezes a violation is reported under, so a comprehension's demand never
    lands in the function-symbol row's ledger or the other way round."""
    if not isinstance(term, dict):
        raise BadMathReading(f"term must be an object: {term!r}")
    if "set" in term and set(term) == {"set"}:
        raise BadMathReading(
            "a {'set'} leaf names a setdef and may appear ONLY as mem's "
            "second argument -- a set is not a value")
    if "ref" in term:
        if set(term) != {"ref"}:
            raise BadMathReading(f"a ref term takes only 'ref': {sorted(term)}")
        if term["ref"] not in objects:
            if in_setbody is not None:
                # P9 `setdef:open-body`, the mirror of the P8 clause below: a
                # comprehension body reading an ambient object is not a set, it
                # is a hypothesis about one, and the two have different
                # conservativity stories.
                raise FragmentMiss(
                    f"setdef {in_setbody[0]!r}: body references "
                    f"{term['ref']!r}, which is not its parameter -- a "
                    f"comprehension body is closed over its parameter, so that "
                    f"a membership site can be eliminated by substitution "
                    f"alone",
                    missing_kind_guess="setdef:open-body")
            if in_defbody is not None:
                # P8 `funcdef:open-body`: inside a body the scope IS the
                # parameter list, so an unknown ref is an object reference (or
                # a typo) and either way the body is not closed over its
                # parameters.  Demand data rather than a malformed reading:
                # "let f(k) = k + n" is a real thing sources write, and it is a
                # definition SCHEMA over an ambient object, not this row.
                raise FragmentMiss(
                    f"definition {in_defbody!r}: body references {term['ref']!r},"
                    f" which is not one of its parameters -- a definition body "
                    f"is closed over its parameters, so that a use site can be "
                    f"eliminated by substitution alone",
                    missing_kind_guess="funcdef:open-body")
            raise BadMathReading(
                f"term references undeclared object {term['ref']!r}")
        return
    if "app" in term:
        # P8: apply a named function symbol.  Eliminated after validation by
        # `_unfold_term`, so no consumer downstream of the gate ever sees one.
        if set(term) - {"app", "args"}:
            raise BadMathReading(
                f"an app term takes only 'app' and 'args': {sorted(term)}")
        fname, fargs = term["app"], term.get("args", [])
        if not isinstance(fname, str):
            raise BadMathReading(f"app: function name must be a string")
        if not isinstance(fargs, list):
            raise BadMathReading(f"app {fname!r}: args must be a list")
        env = definitions or {}
        if fname not in env:
            if fname == in_defbody:
                raise FragmentMiss(
                    f"definition {fname!r}: the body applies the function being"
                    f" defined -- a recurrence has no finite unfolding at a "
                    f"symbolic index, and discharging one needs well-founded "
                    f"recursion the fragment does not have",
                    missing_kind_guess="funcdef:recursive-body")
            raise BadMathReading(
                f"app references undefined function {fname!r} -- a function "
                f"must be introduced by a `definition` statement EARLIER in "
                f"the reading than its first use")
        arity = len(env[fname]["params"])
        if len(fargs) != arity:
            raise BadMathReading(
                f"app {fname!r}: takes exactly {arity} argument(s), got "
                f"{len(fargs)}")
        for a in fargs:
            _check_term(a, objects, in_bigop, definitions, in_defbody,
                        in_setbody)
        return
    if "lit" in term:
        if set(term) != {"lit"}:
            raise BadMathReading(f"a lit term takes only 'lit': {sorted(term)}")
        v = term["lit"]
        if not isinstance(v, int) or isinstance(v, bool):
            raise BadMathReading(f"lit must be an integer: {v!r}")
        return
    if "var" in term:
        raise BadMathReading(
            "a {'var'} leaf declares a big-operator index and may appear "
            "ONLY as bigsum/bigprod's first argument")
    if "op" not in term or set(term) - {"op", "args"}:
        raise BadMathReading(f"term must be {{ref}}, {{lit}} or {{op,args}}: "
                             f"{term!r}")
    op, args = term["op"], term.get("args", [])
    if in_setbody is not None and (op in _BIGOPS or op in ("card", "setbuild")):
        # P9 `setdef:binder-body`, the mirror of P8's clause below and true for
        # the same structural reason: a binder-free comprehension body cannot
        # capture the element term's free names, so `_substitute_pred` is
        # capture-free by construction rather than by a delicate argument.
        raise FragmentMiss(
            f"setdef {in_setbody[0]!r}: a big-operator or set binder inside a "
            f"comprehension body is outside the v1 fragment -- a binder-free "
            f"body is what makes the membership substitution capture-free by "
            f"construction",
            missing_kind_guess="setdef:binder-body")
    if in_defbody is not None and (op in _BIGOPS or op in ("card", "setbuild")):
        # P8 `funcdef:binder-body`.  A body with no binder cannot capture an
        # argument's free names, which is what makes the substitution in
        # `_unfold_term` capture-free for a STRUCTURAL reason instead of a
        # delicate one.  Named as demand rather than engineered around: a
        # definition whose body sums or counts is a real ask, and it wants a
        # renaming discipline this row deliberately does not buy.
        raise FragmentMiss(
            f"definition {in_defbody!r}: a big-operator or set binder inside a "
            f"definition body is outside the v1 fragment -- a binder-free body "
            f"is what makes the use-site substitution capture-free by "
            f"construction",
            missing_kind_guess="funcdef:binder-body")
    if op in _BIGOPS:
        _check_bigop(term, objects, in_bigop, definitions)
        return
    if op == "card":
        _check_card(term, objects, in_bigop, definitions)
        return
    if op == "setbuild":
        raise BadMathReading(
            "a `setbuild` set-node is not a value; it may appear ONLY as "
            "`card`'s argument")
    if op not in _TERM_OPS:
        raise BadMathReading(f"unknown term operator {op!r}")
    if not isinstance(args, list):
        raise BadMathReading(f"{op}: args must be a list")
    if op == "^":
        if len(args) != 2:
            raise BadMathReading("^ takes exactly [base, exponent]")
        _check_term(args[0], objects, in_bigop, definitions, in_defbody)
        exp = args[1]
        _is_int_lit = (isinstance(exp, dict) and set(exp) == {"lit"}
                       and isinstance(exp["lit"], int)
                       and not isinstance(exp["lit"], bool))
        if _is_int_lit and exp["lit"] >= 0:
            return
        # THE SEAM THIS CLOSES.  Every refusal on this branch used to be a
        # bare BadMathReading, which files it as a MALFORMED READING -- and
        # only FragmentMiss reaches run/formalize.py's fragment-miss event
        # sink, which is the automatic half of the demand pipeline.  So a
        # symbolic exponent was measured as "this reading is broken" rather
        # than as "the FRAGMENT is missing something", and no amount of
        # corpus intake could ever raise refusal-symbolic-exponent's price.
        # Output that structurally cannot become input.
        #
        # The two outcomes must NOT be conflated in the other direction
        # either: labelling a malformed exponent as demand would inflate the
        # price list with readings that are simply wrong, which is the
        # dishonesty the census rules exist to prevent.  Discriminate by
        # running the term checker on the exponent -- if it type-checks, the
        # READING is fine and the fragment is what cannot express it.
        _check_term(exp, objects, in_bigop, definitions,
                    in_defbody)                 # malformed -> BadMathReading
        if _is_int_lit:                         # ... so it is a NEGATIVE one
            raise FragmentMiss(
                "^ requires a NON-NEGATIVE literal exponent; a negative "
                "exponent is a reciprocal power and leaves the integer "
                "carrier entirely",
                missing_kind_guess="pow:negative-exponent")
        # P7 -- THE SYMBOLIC EXPONENT IS ADMITTED HERE, and deliberately not
        # decided here.  Admissibility turns on the exponent's CARRIER (only a
        # `Nat` exponent is non-negative by construction, which is what keeps
        # `Monoid.npow` the power being talked about and keeps the reflect
        # slice's `Int.toNat` totalisation unreachable), and `_check_term` is
        # carrier-BLIND -- carriers resolve in `_check_carrier_ops`, which is
        # the one walk that knows the ambient and the object table.  Deciding
        # it in both places would be two rules that can disagree; deciding it
        # in neither would be a hole.  So: structure here, carrier there.
        return
    if op in _OP_TERM_WORDS:
        arity = MATH_OPERATORS[op]["arity"]
        if len(args) != arity:
            raise BadMathReading(f"{op} takes {arity} args, got {len(args)}")
    elif op in ("-", "%", "/"):                 # the binary builtins (P3: `/`)
        if len(args) != 2:
            raise BadMathReading(f"{op} takes exactly 2 args")
    else:  # + or *
        if len(args) < 2:
            raise BadMathReading(f"{op} takes >= 2 args")
    for a in args:
        _check_term(a, objects, in_bigop, definitions, in_defbody,
                    in_setbody)


def _check_pred(pred, objects, in_bigop=False, definitions=None,
                in_defbody=None, setdefs=None, in_setbody=None):
    """A boolean pred over terms: connectives over preds, comparison atoms and
    lexicon predicate words over terms.  `in_bigop` is carried through so a
    binder (bigop/setbuild/card) buried inside a setbuild filter is still
    refused as `*:nested` -- the filter pred is checked with in_bigop=True.
    `setdefs` are the named comprehensions in scope (P9) and `in_setbody`, when
    set, is the `(name, param)` of the setdef whose body this walk is inside."""
    if not isinstance(pred, dict) or "op" not in pred or set(pred) - {"op", "args"}:
        raise BadMathReading(f"pred must be {{op, args}}: {pred!r}")
    op, args = pred["op"], pred.get("args", [])
    if not isinstance(args, list) or not args:
        raise BadMathReading(f"{op}: args must be a non-empty list")
    if op in _CONNECTIVES:
        want = _CONNECTIVE_ARITY[op]
        if want is None:
            if len(args) < 2:
                raise BadMathReading(f"{op} takes >= 2 preds")
        elif len(args) != want:
            raise BadMathReading(
                f"{op} takes exactly {want} pred"
                f"{'' if want == 1 else 's'}, got {len(args)}")
        for a in args:
            _check_pred(a, objects, in_bigop, definitions, in_defbody,
                        setdefs, in_setbody)
        return
    if op == _MEM_OP:
        # P9.  Handled HERE rather than by a row in `_BUILTIN_ATOM_OPS`,
        # exactly as `app` is handled inside `_check_term` rather than by a row
        # in `_BUILTIN_TERM_OPS`: membership is eliminated at the gate and
        # reaches no consumer, so widening the atom-op set would re-key the
        # miner's op-slot typing and the prompt seam for a word no committed
        # reading can contain.  The atom-op tables stay byte-unchanged.
        _check_mem(pred, objects, in_bigop, definitions, in_defbody,
                   setdefs, in_setbody)
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
        _check_term(a, objects, in_bigop, definitions, in_defbody,
                    in_setbody)


def _check_mem(pred, objects, in_bigop, definitions, in_defbody,
               setdefs, in_setbody):
    """P9's membership atom: `{"op":"mem","args":[<term>, {"set":s}]}`.

    The SORT DISCIPLINE is the same one `setbuild` has carried since P2 and
    `app` since P8: a set is NOT a value, so `{"set":s}` is a leaf that may
    appear in exactly one position -- membership's second argument -- and
    nowhere a term is expected.  `_check_term` refuses it everywhere else, so
    no reading can smuggle a set into arithmetic.

    The two REFUSALS this raises are the tower-class residue of the row, and
    both are FragmentMisses (demand data) rather than malformations:
      * `set:free-set-variable` -- membership in a name the reading declared as
        an OBJECT rather than defining as a comprehension.  There is no body to
        substitute, so it survives unfolding.  (An object typed `Set ...` never
        reaches here: it refuses earlier at the carrier gate, under the same
        signal, so the demand stays one row however the source spells it.)
      * `set:set-valued-param` -- membership in a setdef's own PARAMETER, i.e.
        a comprehension binding a set (`{s | 3 in s}`, the powerset shape).
        The parameter ranges over sets the reading has no body for: the same
        wall, reached from the other side."""
    args = pred.get("args", [])
    if len(args) != 2:
        raise BadMathReading(
            f"atom mem takes 2 args (an element term and a {{'set':s}} "
            f"reference), got {len(args)}")
    elem, setref = args
    if not (isinstance(setref, dict) and set(setref) == {"set"}
            and isinstance(setref["set"], str)):
        raise BadMathReading(
            f"mem's second argument must be a set reference {{'set':s}} naming "
            f"a setdef -- a set is not a value: {setref!r}")
    sname = setref["set"]
    if in_setbody is not None and sname == in_setbody[1]:
        raise FragmentMiss(
            f"setdef {in_setbody[0]!r}: its body takes membership in its own "
            f"PARAMETER {sname!r} -- a comprehension whose parameter ranges "
            f"over SETS (the powerset shape).  The parameter has no "
            f"comprehension body to substitute, so the membership survives "
            f"unfolding; that is a set carrier value, a separate purchase",
            missing_kind_guess="set:set-valued-param")
    if sname in objects:
        raise FragmentMiss(
            f"mem: {sname!r} is a declared OBJECT, not a named set -- an "
            f"arbitrary set has no comprehension to substitute, so membership "
            f"in it survives unfolding and needs a set carrier value (an "
            f"uninterpreted predicate in the mirror, a `Pd` constructor in the "
            f"reflect slice); define it with a `setdef` or state the theorem "
            f"about a set the source gives a body for",
            missing_kind_guess="set:free-set-variable")
    env = setdefs or {}
    if sname not in env:
        if in_setbody is not None and sname == in_setbody[0]:
            raise FragmentMiss(
                f"setdef {sname!r}: the body takes membership in the set being "
                f"defined -- a recursive comprehension has no finite "
                f"unfolding, so it is not eliminable and this row does not buy "
                f"it",
                missing_kind_guess="setdef:recursive-body")
        raise FragmentMiss(
            f"mem references undefined set {sname!r} -- a set must be "
            f"introduced by a `setdef` statement EARLIER in the reading (a "
            f"forward reference is mutual recursion wearing a different hat)",
            missing_kind_guess="setdef:recursive-body")
    _check_term(elem, objects, in_bigop, definitions, in_defbody, in_setbody)


# --- P6: the ATOM DUAL table, and the negation freeze it licenses -----------
# `not` is admitted because it never has to be REPRESENTED: negation-normal
# form pushes it through the connectives until it reaches an atom, and there it
# becomes a DIFFERENT ATOM THE FRAGMENT ALREADY HAS.  This table is that claim,
# written down where every reader of the freeze can check it:
#
#     not (a =  b)   ==   a != b            not (a != b)  ==  a =  b
#     not (a <= b)   ==   b <  a            not (a <  b)  ==  b <= a
#     not (even n)   ==   odd n             not (odd n)   ==  even n
#
# The value is `(dual_op, swap_args)`; the order atoms are the only rows that
# swap, and they swap because `<=`/`<` are duals only across the ARGUMENTS
# (`not (a <= b)` is `b < a`, not `a < b`).  Every mirror that ever pushes a
# negation to an atom reads THIS table, so gate, eval, SMT and Lean cannot
# drift on what a negated atom means.
_ATOM_DUALS = {
    "=":  ("!=", False),
    "!=": ("=",  False),
    "<=": ("<",  True),
    "<":  ("<=", True),
    "even": ("odd",  False),
    "odd":  ("even", False),
}


def _dual_atom(pred):
    """The NNF dual of an ATOM pred, or None when the fragment has none.
    The one place the `_ATOM_DUALS` table is consumed, so a caller can never
    hand-roll a swap and get the order atoms backwards."""
    row = _ATOM_DUALS.get(pred.get("op"))
    if row is None:
        return None
    dual, swap = row
    args = pred.get("args", [])
    return {"op": dual, "args": list(reversed(args)) if swap else list(args)}


def _setbuild_filters(node):
    """Every `setbuild` FILTER pred reachable inside a term/pred, in pre-order.
    P2 lets a pred hide a whole second pred under `card`'s set argument, and a
    walk that only follows connectives would never see it."""
    if not isinstance(node, dict):
        return
    if node.get("op") == "setbuild":
        args = node.get("args", [])
        if len(args) == 4:
            yield args[3]
        return
    for a in node.get("args", []):
        yield from _setbuild_filters(a)


def _check_connective_nnf(pred, sid, negated=False):
    """P6: refuse exactly the negations that negation-normal form cannot push
    to an atom the fragment already carries -- the freeze that makes this
    purchase ADDITIVE rather than tower-class.

    A NO-OP on every pre-P6 reading, and structurally so: `negated` can only
    become True underneath a `not` node, and no reading written before this
    purchase could contain one.  A pre-existing `implies` is walked at
    polarity False on BOTH arms, so nothing that parsed yesterday can refuse
    today -- the same byte-unchanged discipline P3's and P4's carrier walks
    hold to.

    The polarity algebra is the reflect slice's `Pd`, not classical NNF, and
    the difference is load-bearing: `Pd` carries `pand`/`por`/`pimp` as
    CONSTRUCTORS, so a POSITIVE implication (and a positive `iff`, which is the
    `and` of two of them) needs no push at all and its arms stay positive.
    Only a `not` forces the push:

      * `not (not a)`      -> a                        (polarity flips twice)
      * `not (a and b)`    -> (not a) or  (not b)      De Morgan
      * `not (a or  b)`    -> (not a) and (not b)      De Morgan
      * `not (a -> b)`     -> a and (not b)            the antecedent comes back
                                                       POSITIVE, the consequent
                                                       negative
      * `not (a <-> b)`    -> (a and not b) or (b and not a) -- both arms are
                              needed at BOTH polarities, which is why a negated
                              biconditional is the one shape that demands more
                              of its operands than a positive one
      * `not <atom>`       -> the `_ATOM_DUALS` row, or a FragmentMiss

    `dvd` and `coprime` have no dual IN THE FRAGMENT (`a` not dividing `b` is
    not any other atom we carry, and non-coprimality is not coprimality of
    anything), so a negation that lands on one is `not:<op>-no-dual`: honest
    demand data for a negation constructor -- the purchase §4 P6 declares
    tower-class and this one deliberately does not make."""
    if not isinstance(pred, dict):
        return
    op, args = pred.get("op"), pred.get("args", [])
    if op == "not":
        _check_connective_nnf(args[0], sid, not negated)
        return
    if op in ("and", "or"):
        for a in args:
            _check_connective_nnf(a, sid, negated)
        return
    if op == "implies":
        # positive: `pimp` carries it, both arms stay positive.  negated:
        # `a and not b` -- arm 0 positive, arm 1 negative.
        _check_connective_nnf(args[0], sid, False)
        _check_connective_nnf(args[1], sid, negated)
        return
    if op == "iff":
        # positive: the `and` of two implications, so both arms positive.
        # negated: both arms are needed at both polarities.
        for a in args:
            _check_connective_nnf(a, sid, False)
            if negated:
                _check_connective_nnf(a, sid, True)
        return
    # An atom.  Before deciding it, descend into any `setbuild` FILTER buried
    # in its terms (P2): a filter is a pred in its own right and its
    # negations need the same freeze -- at polarity FALSE, because the filter
    # sits under `card`, a value, so no negation outside the atom reaches it.
    for filt in _setbuild_filters(pred):
        _check_connective_nnf(filt, sid, False)
    if negated and _dual_atom(pred) is None:
        raise FragmentMiss(
            f"{sid}: `{op}` has no negation dual in the fragment, so a "
            f"negation cannot be pushed to an atom -- and the fragment carries "
            f"no negation NODE to leave it at (that is a constructor, and a "
            f"separate purchase); state the atom positively",
            missing_kind_guess=f"not:{op}-no-dual")


def _iter_op_nodes(node):
    """Yield every {op, args} node (pred connective / atom / term operator)
    inside a pred, in pre-order.  Preds and terms share the {op, args} shape, so
    one walk reaches both."""
    if not isinstance(node, dict) or "op" not in node:
        return
    yield node
    for a in node.get("args", []):
        yield from _iter_op_nodes(a)


def _term_ref_carriers(term, objects, out):
    """Collect the declared carriers of every object referenced anywhere inside
    a term (for the `-` shared-carrier check).  Inside a big-operator body the
    bound index counts as a Nat-carrier ref (its values are the non-negative
    bounds' range), so a `-` mixing the index with an Int object is caught by
    the same B1 rule as any other mixed-carrier subtraction."""
    if not isinstance(term, dict):
        return
    if "ref" in term:
        c = objects.get(term["ref"])
        if c in CARRIERS or _zmod_modulus(c) is not None:
            out.add(c)
        return
    if "lit" in term or "var" in term:
        return
    if term.get("op") in _BIGOPS:
        args = term.get("args", [])
        var = args[0]["var"] if args else None
        inner = {**objects, var: "Nat"} if var else objects
        for a in args[1:]:
            _term_ref_carriers(a, inner, out)
        return
    if term.get("op") == "card":
        setnode = term.get("args", [None])[0]
        sargs = setnode.get("args", []) if isinstance(setnode, dict) else []
        var = sargs[0]["var"] if sargs and isinstance(sargs[0], dict) else None
        inner = {**objects, var: "Nat"} if var else objects
        for a in sargs[1:]:                     # bounds ({lit}) + filter (pred)
            _term_ref_carriers(a, inner, out)
        return
    for a in term.get("args", []):
        _term_ref_carriers(a, objects, out)


def _zmod_of(objects, ambient):
    """P4: the single `ZMod n` carrier a READING sits over, or None when it is
    not a residue reading.  Reads the ambient first, then the declared objects
    in sorted-name order -- the identical rule ``math_eval._zmod_carrier_of``
    and ``math_smt._zmod_carrier`` use, so the gate decides "is this a residue
    reading?" by exactly the question the two mirrors will ask (T4).  That
    agreement is what `_check_zmod_carrier` below then makes UNAMBIGUOUS."""
    if _zmod_modulus(ambient) is not None:
        return ambient
    for name in sorted(objects):
        if _zmod_modulus(objects[name]) is not None:
            return objects[name]
    return None


def _check_zmod_carrier(objects, ambient):
    """P4: a residue reading declares ONE carrier, reading-wide.

    NOT a per-pred rule, and deliberately so.  Both mirrors resolve the residue
    carrier from the reading's OBJECT MAP rather than from a term's refs (an
    all-literal term inside a `ZMod 5` reading is still a residue term, and
    resolving by first-ref would hand `2 - 4` to the Int rule -- the D8-class
    divergence).  That resolution is only well-defined while the reading has a
    single carrier, so a reading pairing a modulus with `Nat`/`Int`/another
    modulus would have its non-residue atoms silently wrapped.  Enforcing the
    mirrors' assumption HERE, at the gate, is the B1 discipline: refuse the
    shape rather than let a divergence surface downstream."""
    declared = set(objects.values())
    if ambient in CARRIERS or _zmod_modulus(ambient) is not None:
        declared.add(ambient)
    zmods = sorted(c for c in declared if _zmod_modulus(c) is not None)
    if not zmods:
        return                                   # not a residue reading: no-op
    if len(zmods) > 1:
        raise BadMathReading(
            f"the reading declares residue carriers {zmods} -- a value of "
            f"`ZMod n` is a congruence class MODULO n, so two moduli are two "
            f"unrelated carriers and no reading may span them")
    if len(declared) > 1:
        raise BadMathReading(
            f"the reading mixes {sorted(declared)} with the residue carrier "
            f"`{zmods[0]}` -- a congruence class and an integer are not the "
            f"same kind of value, and the fragment has no coercion; a residue "
            f"reading declares one modulus and nothing else")


def _check_zmod_ops(pred, objects, ambient, sid):
    """P4: the OPERATION whitelist for one hypothesis/conclusion pred of a
    residue reading (carrier discipline is `_check_zmod_carrier`'s, so each rule
    has exactly one home).

    A NO-OP unless the reading sits over a residue carrier, so every pre-P4
    reading walks through this byte-identically -- the purchase is additive at
    the gate, exactly as P1's binder class and P2's set class were.  On a
    residue reading it enforces two of the v1 freezes written at
    `_zmod_modulus`, each with its OWN signal so a coarser refusal never
    swallows a finer demand:

      * a binder node (bigsum/bigprod/card/setbuild) is
        `zmod:binder-index-carrier` -- P1 pins a bound index to carrier Nat, so
        a fold inside a residue reading would mix carriers behind every walker's
        back;
      * an operation outside `+ * - ^` and the atoms `= !=` is
        `operator:<op>@ZMod <n>`.  Congruence classes carry no order and no
        division, so the order atoms and the whole mod/divisibility family are
        real demand data here (the ordered and field carriers are separate
        purchases), never a malformation."""
    zmod = _zmod_of(objects, ambient)
    if zmod is None:
        return
    for node in _iter_op_nodes(pred):
        op = node["op"]
        if op in _BIGOPS or op in _SETOPS:
            raise FragmentMiss(
                f"{sid}: `{op}` binds its index at carrier Nat, which cannot "
                f"appear inside a `{zmod}` reading -- the v1 residue freeze "
                f"pins one carrier per reading",
                missing_kind_guess="zmod:binder-index-carrier")
        if (op in _CONNECTIVES or op in _ZMOD_ADMISSIBLE_TERM_OPS
                or op in _ZMOD_ADMISSIBLE_ATOM_OPS):
            continue
        raise FragmentMiss(
            f"{sid}: `{op}` is not defined over `{zmod}` -- v1 admits "
            f"{sorted(_ZMOD_ADMISSIBLE_TERM_OPS)} and the atoms "
            f"{sorted(_ZMOD_ADMISSIBLE_ATOM_OPS)} only (a congruence class "
            f"carries no order and no division)",
            missing_kind_guess=f"operator:{op}@{zmod}")


def _check_minus_shared_carrier(pred, objects, ambient_declared, sid):
    """B1: refuse a `-` term whose ref args resolve to MIXED carriers with no
    ambient declared.  The eval mirror resolves a `-` node's carrier by its
    FIRST ref in pre-order (argument-order-sensitive) while the SMT mirror uses
    any-Nat-operand => Nat (order-insensitive); on a mixed-carrier `-` with no
    shared carrier the two channels disagree.  The evaluator's docstring already
    ASSUMES a shared carrier -- this enforces it at the gate rather than letting
    a mirror divergence surface downstream.  The walk is scope-aware: inside a
    big-operator body the bound index is in scope at carrier Nat."""
    def walk(node, scope):
        if not isinstance(node, dict) or "op" not in node:
            return
        if node["op"] in _BIGOPS:
            args = node.get("args", [])
            var = args[0]["var"] if args else None
            inner = {**scope, var: "Nat"} if var else scope
            for a in args[1:]:
                walk(a, inner)
            return
        if node["op"] == "card":
            setnode = node.get("args", [None])[0]
            sargs = setnode.get("args", []) if isinstance(setnode, dict) else []
            var = sargs[0]["var"] if sargs and isinstance(sargs[0], dict) else None
            inner = {**scope, var: "Nat"} if var else scope
            for a in sargs[1:]:                 # bounds + the filter pred
                walk(a, inner)
            return
        if node["op"] in ("-", "/"):             # P3: `/` rides the `-` template
            carriers = set()
            _term_ref_carriers(node, scope, carriers)
            if "Rat" in carriers and len(carriers) > 1:
                # rat:no-coercion (P3).  Ambient does NOT rescue a Rat/integer
                # mix the way it rescues Nat/Int: there is no coercion story
                # this cycle, so the mixed term has no single denotation the
                # three translations could agree on.  Refused unconditionally,
                # and named as the limit it is.
                raise BadMathReading(
                    f"{sid}: a `{node['op']}` term mixes carriers "
                    f"{sorted(carriers)} -- Rat has no coercion to or from the "
                    f"integer carriers in v1 (rat:no-coercion), so an ambient "
                    f"declaration cannot resolve the mix; keep the term on one "
                    f"carrier")
            if len(carriers) > 1 and not ambient_declared:
                raise BadMathReading(
                    f"{sid}: a `{node['op']}` term mixes carriers "
                    f"{sorted(carriers)} with "
                    f"no ambient declared -- the eval mirror resolves "
                    f"subtraction by the first operand's carrier "
                    f"(order-sensitive) while the SMT mirror truncates on any "
                    f"Nat operand, so the channels diverge; declare an ambient "
                    f"carrier or keep `{node['op']}` operands on one carrier")
        for a in node.get("args", []):
            walk(a, scope)

    walk(pred, objects)


# --- P3: carrier ADMISSIBILITY of the operators inside a pred ---------------
# The binder ops.  A binder's index is pinned Nat in every walker (gate, eval,
# SMT unroll, compile's Finset.Icc), which is exactly why a binder cannot ride
# into a Rat reading: the fold/count would need a ℕ→ℚ coercion nobody has
# proven here.  Named miss, demand data for the next purchase (P1's move for
# symbolic bounds, again).
_BINDER_OPS = _BIGOPS | _SETOPS


def _ordered_ref_carriers(node, scope, out):
    """The declared carriers of every object referenced inside a term/pred, in
    left-to-right PRE-ORDER with duplicates kept -- the ORDERED sibling of
    `_term_ref_carriers` (which returns a set and so cannot answer "the FIRST
    ref's carrier", the resolution rule the compiler freezes).  Scope-aware in
    the same way: inside a binder the bound index is a Nat-carrier ref."""
    if not isinstance(node, dict):
        return
    if "ref" in node:
        c = scope.get(node["ref"])
        if c in CARRIERS:
            out.append(c)
        return
    if "lit" in node or "var" in node:
        return
    op = node.get("op")
    if op in _BIGOPS or op == "setbuild":
        args = node.get("args", [])
        var = args[0]["var"] if args and isinstance(args[0], dict) else None
        inner = {**scope, var: "Nat"} if var else scope
        for a in args[1:]:
            _ordered_ref_carriers(a, inner, out)
        return
    for a in node.get("args", []):
        _ordered_ref_carriers(a, scope, out)


def _check_pow_exponent(exp, carrier, sid):
    """P7: the carrier half of the symbolic-exponent admission -- the ONE rule
    that decides whether a non-literal exponent is in the fragment.

    A LITERAL exponent never reaches here: it is a Lean-level `Nat` already, it
    is carrier-free, and its behaviour is byte-unchanged by this purchase (the
    additivity claim `tests/test_pow_battery.py` measures).  A SYMBOLIC exponent
    is admissible ONLY at carrier `Nat`, and the reason is that non-negativity
    then holds by TYPE rather than as a side condition somebody has to
    re-establish at each of the four consumers:

      * eval computes `base ** e` and stays inside the integer carriers -- no
        Fraction, no float;
      * the compiler emits `base ^ e`, which elaborates against `Monoid.npow`
        (`HPow _ Nat _`) with no coercion.  `zpow` would want a `DivisionRing`
        the integer carriers do not have, so an Int exponent has no Lean
        rendering here at all;
      * the reflect slice's `evalTm` totalises a negative exponent through
        `Int.toNat`, and this rule is what makes that branch UNREACHABLE from
        any admitted reading rather than merely mirrored.

    FAIL CLOSED, which is §3.1 rule 3(e)'s shape and the hazard
    `results/p3_delta.md` measured directly: refusal is the DEFAULT and `Nat` is
    the single admitted case, so a carrier this walk has never heard of refuses
    instead of falling through to a power whose meaning someone would then have
    to guess.  A silent `else` here is exactly the fail-OPEN site P3 found.

    The refusal is a `FragmentMiss`, so it is DEMAND
    (`pow:symbolic-exponent@Int`) rather than a malformed reading -- the same
    carrier-suffixed idiom P3 used for its own residue (`operator:/@{carrier}`).
    """
    if carrier != "Nat":
        raise FragmentMiss(
            f"{sid}: `^` admits a SYMBOLIC exponent only at carrier 'Nat' "
            f"(non-negative by construction, so the power stays Monoid.npow); "
            f"at {carrier!r} an exponent may be negative and a reciprocal "
            f"power leaves the carrier entirely",
            missing_kind_guess=f"pow:symbolic-exponent@{carrier}")


def _check_carrier_ops(pred, objects, ambient, sid):
    """P3: refuse every operator whose RESOLVED CARRIER puts it outside the
    fragment -- the carrier-admissibility half of the Rat purchase, and the one
    place a BUILTIN (until now carrier-blind) is carrier-checked.

    Three refusals, all first-class `FragmentMiss`es named `operator:<op>@<c>`
    so F4 can price them:

      * `/` anywhere its carrier resolves to Nat or Int.  Lean's HDiv there is
        FLOOR division; modelling it would reintroduce exactly the ℕ/ℤ-style
        divergence T4 exists to catch, so we refuse the reading instead and
        leave `operator:div` standing as census demand.
      * `%` (and the `mod` lexicon word) at Rat.  Remainder over a field has no
        meaning we are willing to freeze; the divisibility family stays integer.
      * any other MATH_OPERATORS word at Rat -- dvd, gcd, coprime, even, odd.
        Their `lean` tables have no "Rat" key, so an explicit `operator`
        statement already refuses; this closes the same hole for a pred that
        uses the word WITHOUT declaring it, which the pred grammar allows.
        Deliberately Rat-only: the Nat/Int behaviour of every one of these is
        byte-unchanged, so this walk can never re-verdict an existing reading.

    Plus the binder freeze: a `bigsum`/`bigprod`/`card` inside a Rat reading is
    `operator:<binder>@Rat` (the index is pinned Nat -- rat:no-coercion).

    CARRIER RESOLUTION is the compiler's rule verbatim (math_compile.
    _resolve_carrier), so gate and emitter can never disagree about which
    carrier a node is at: the declared AMBIENT wins; else the declared carrier
    of the FIRST object referenced in a left-to-right pre-order walk of the
    node's own subtree, then of the enclosing pred; else `"Nat"` -- which is why
    an all-literal `/` in an object-free, ambient-free reading is a miss rather
    than a silently-Nat division (a Rat reading always carries a Rat object or
    an ambient Rat choice)."""
    outer: list = []
    _ordered_ref_carriers(pred, objects, outer)
    # The binder freeze is a property of the READING, not of the binder's own
    # subtree: the index resolves to Nat by construction (that is the whole
    # point), so asking the node would always answer "Nat" and never fire.
    rat_reading = ambient == "Rat" or "Rat" in objects.values()

    def resolve(node, scope):
        if ambient in CARRIERS:
            return ambient
        own: list = []
        _ordered_ref_carriers(node, scope, own)
        for c in own + outer:
            if c in CARRIERS:
                return c
        return "Nat"                    # math_compile._resolve_carrier's default

    def walk(node, scope):
        if not isinstance(node, dict) or "op" not in node:
            return
        op = node["op"]
        if op in _BINDER_OPS:
            if rat_reading:
                raise FragmentMiss(
                    f"{sid}: `{op}` binds a Nat-carrier index, so it cannot "
                    f"appear in a Rat reading without a ℕ→ℚ coercion -- "
                    f"outside the v1 fragment (rat:no-coercion)",
                    missing_kind_guess=f"operator:{op}@Rat")
            args = node.get("args", [])
            if op == "card":
                for a in args:
                    walk(a, scope)
                return
            var = args[0]["var"] if args and isinstance(args[0], dict) else None
            inner = {**scope, var: "Nat"} if var else scope
            for a in args[1:]:
                walk(a, inner)
            return
        if op == "^":
            exp_node = node.get("args", [None, None])[1]
            if not (isinstance(exp_node, dict) and "lit" in exp_node):
                _check_pow_exponent(exp_node, resolve(exp_node, scope), sid)
        if op == "/" or op in ("%", "mod") or op in MATH_OPERATORS:
            carrier = resolve(node, scope)
            if op == "/" and carrier != "Rat":
                raise FragmentMiss(
                    f"{sid}: `/` is admissible only over Rat -- at {carrier!r} "
                    f"Lean's division FLOORS, and the fragment refuses to model "
                    f"a lossy operator rather than diverge from it",
                    missing_kind_guess=f"operator:/@{carrier}")
            if carrier == "Rat" and op != "/":
                raise FragmentMiss(
                    f"{sid}: operator {op!r} is not supported over carrier "
                    f"'Rat' (the divisibility family stays on the integer "
                    f"carriers in v1)",
                    missing_kind_guess=f"operator:{op}@Rat")
        for a in node.get("args", []):
            walk(a, scope)

    walk(pred, objects)


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


def _expand_derived_operators(doc):
    """R2 reading-layer hook: rewrite any statement whose operator is an ADMITTED
    derived word to its expanded kernel-fragment form BEFORE validation, so the
    downstream engines (compile / eval / smt) only ever see kernel operators
    (``generators/operator_growth.py``).  A missing / empty operator registry --
    or a reading that uses no derived word -- returns ``doc`` UNCHANGED, so
    existing behaviour is byte-identical (the no-op path).  A tampered admitted
    row (cert-id mismatch) or a use-site arity mismatch surfaces as a
    ``BadMathReading`` refusal, so a stale row can never silently lower.

    Lazily imported (no import cycle: ``operator_growth`` imports this module) and
    fail-safe: if the growth module is unavailable the reading is left untouched."""
    try:
        from generators import operator_growth
    except Exception:
        return doc
    try:
        return operator_growth.expand_reading_doc(doc)
    except operator_growth.OperatorExpansionError as e:
        raise BadMathReading(str(e))


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
    # R2 reading-layer hook: expand any admitted derived-operator statement to
    # its kernel form BEFORE validation (no-op with an empty registry / no
    # derived usage, so existing behaviour is byte-identical).
    doc = _expand_derived_operators(doc)
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
    ambient_carrier = None  # the single declared ambient: P3 carrier-checks
    #                         it, P4 resolves the residue modulus out of it

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
            if ty not in CARRIERS and _zmod_modulus(ty) is None:
                raise FragmentMiss(
                    f"{sid}: object type {ty!r} is outside the carrier "
                    f"whitelist {CARRIERS} (+ the parametric `ZMod <n>`)",
                    missing_kind_guess=_carrier_miss_guess(ty))
            objects[n] = ty
        elif kind == "ambient":
            ambient_count += 1
            if (lf.get("carrier") not in CARRIERS
                    and _zmod_modulus(lf.get("carrier")) is None):
                raise FragmentMiss(
                    f"{sid}: ambient carrier {lf.get('carrier')!r} is outside "
                    f"{CARRIERS} (+ the parametric `ZMod <n>`)",
                    missing_kind_guess=_carrier_miss_guess(lf.get("carrier")))
            ambient_carrier = lf.get("carrier")
    if ambient_count > 1:
        raise BadMathReading("at most one ambient statement")
    # P4: one carrier per residue reading, checked once the object map is
    # complete (both mirrors resolve the modulus from THIS map).
    _check_zmod_carrier(objects, ambient_carrier)

    # P3 rat:no-coercion, at the READING level.  A Rat object may not share a
    # reading with an integer-carrier object (nor with an integer ambient).  Not
    # a stylistic rule: the SMT mirror declares ONE sort per reading (Real for
    # Rat, Int otherwise), so a mixed reading would either emit an ill-sorted
    # obligation or silently pick a mixed logic -- and the compiler would lean
    # on Lean's ℕ→ℚ coercion, which nothing here has proven agrees with eval.
    # Refusing the mix is what lets every downstream translation stay a total,
    # single-carrier function.  The limit is named, not hidden.
    _declared = set(objects.values()) | (
        {ambient_carrier} if ambient_carrier else set())
    if "Rat" in _declared and len(_declared) > 1:
        raise BadMathReading(
            f"a reading mixes the Rat carrier with {sorted(_declared - {'Rat'})}"
            f" -- v1 has no coercion between Rat and the integer carriers "
            f"(rat:no-coercion), and every mirror renders a reading over ONE "
            f"carrier; state the theorem over a single carrier")

    # P8 pass: collect the named function symbols, IN STATEMENT ORDER.  Order
    # is the whole non-recursion argument: a body is checked against only the
    # definitions declared before it, so the dependency graph is a DAG by
    # construction and `_unfold_term` terminates without a occurs-check.  The
    # parameters are typed at the ambient carrier for the structural walk only
    # -- carrier admissibility is decided post-unfold at the use site, where
    # the argument's real carrier is known.
    definitions = {}
    for s in stmts:
        if s["lf"]["kind"] == "definition":
            definitions[s["lf"]["name"]] = _check_definition(
                s["lf"], s["id"], objects, definitions,
                ambient_carrier or "Int")

    # P9 pass: collect the named SETS, IN STATEMENT ORDER, and after the
    # definitions -- so a comprehension body may apply a function symbol the
    # source already named, and the DAG argument that makes both unfoldings
    # terminate is the same one, read in one direction only.
    setdefs = {}
    for s in stmts:
        if s["lf"]["kind"] == "setdef":
            setdefs[s["lf"]["name"]] = _check_setdef(
                s["lf"], s["id"], objects, definitions, setdefs,
                ambient_carrier or "Int")

    # second pass: referential integrity of preds / operators / quantifiers
    for s in stmts:
        sid, lf = s["id"], s["lf"]
        kind = lf["kind"]
        if kind in ("hypothesis", "conclusion"):
            _check_pred(lf.get("pred"), objects, definitions=definitions,
                        setdefs=setdefs)
            # P8 DESUGARING, and the single place it happens.  Every check
            # below this line -- NNF, the residue walk, the shared-carrier
            # rule, carrier admissibility -- runs on the UNFOLDED pred, so
            # each one keeps seeing exactly the fragment it was written for
            # and none of them learns a second rule about applications.  This
            # is also what makes the four consumers byte-unchanged.
            #
            # P9 joins the SAME line, in the same spirit and deliberately right
            # here: membership is eliminated immediately after application, so
            # every check below -- NNF included -- sees a pred with neither in
            # it.  That ordering is load-bearing rather than tidy: a negated
            # membership (`10 not in {n | n odd}`, the 09_Sets#problem-002
            # shape) only has an NNF dual AFTER the comprehension is
            # substituted, because what carries the dual is the body's atom
            # (`odd`/`even`) and not the membership.  Unfolding second would
            # refuse the very readings this row buys.
            lf["pred"] = _unfold_mem(
                _unfold_pred(lf.get("pred"), definitions), setdefs)
            _check_connective_nnf(lf.get("pred"), sid)
            _check_zmod_ops(lf.get("pred"), objects, ambient_carrier, sid)
            _check_minus_shared_carrier(lf.get("pred"), objects,
                                        ambient_count > 0, sid)
            _check_carrier_ops(lf.get("pred"), objects, ambient_carrier, sid)
        elif kind == "operator":
            w, c = lf.get("word"), lf.get("carrier")
            if not isinstance(w, str):
                raise BadMathReading(f"{sid}: operator word must be a string")
            if c not in CARRIERS and _zmod_modulus(c) is None:
                raise FragmentMiss(
                    f"{sid}: operator carrier {c!r} outside {CARRIERS} "
                    f"(+ the parametric `ZMod <n>`)",
                    missing_kind_guess=_carrier_miss_guess(c))
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
