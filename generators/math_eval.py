"""Carrier-aware evaluation of the F-G pred/term fragment (F2.1 / F2.2).

THE THIRD TRANSLATION.  ``generators/math_reading.py`` freezes one grammar (the
F-G pred/term AST).  Two hand-written translations of that grammar already
exist: the compiler (``generators/math_compile.py``, source -> Lean statement
text) and the SMT mirror (``generators/math_smt.py``, hypothesis set -> SMT-LIB).
This module is the THIRD -- a direct Python evaluator of the same AST.  All three
descend from one source and MUST AGREE; a disagreement is the designed
``mirror-divergence`` / ``formalization-divergence`` surface (T4), a first-class
event to be recorded, never a silent bug (TRUST 1.2e's two-translations-of-one-
text class).  Because Lean is absent in this container, this evaluator is the
Lean-free channel the F2 statement-fidelity gates run on:

  * F2.1 non-vacuity  -> ``bounded_nonvacuous`` corroborates a dual-SMT unsat
    (dual-unsat refuses only when THIS also finds no in-bound witness).
  * F2.2 entailed instances -> ``satisfying_instances`` (the k smallest
    hypothesis-satisfying assignments; the caller checks ``conclusion_holds``)
    and ``boundary_probes`` (just-outside probes, recorded never auto-refused).

CARRIER-RESOLUTION RULE (WP-H depends on this AGREEING with the SMT mirror).
Value carriers only ever matter for ``gcd`` (``Nat.gcd`` and ``Int.gcd`` return
the same |gcd|, so resolution never changes a value) and ``-`` (``Nat.sub``
truncates, ``Int.sub`` is real).  So the ONE value-carrier-sensitive operator is
``-``, and its carrier is resolved to MATCH ``math_smt._minus_carrier`` node for
node (the two are mirrors; a disagreement is the B1 divergence the gate closes):

    carrier of a ``-`` term = the reading's declared AMBIENT carrier when one is
    present (B1-A: ambient precedence -- the SMT mirror lets ambient win, so the
    eval mirror must too, else a declared-ambient reading diverges); else the
    declared carrier of the FIRST object referenced in a left-to-right pre-order
    walk (with no ambient, the gate has already refused a mixed-carrier ``-``,
    so "first ref" and the mirror's "any Nat operand" coincide); an all-literal
    term falls back to ``"Int"``.

So ``a - b`` over ``Nat`` truncates (``max(0, a - b)``, ``Nat.sub``) while over
``Int`` it is real (``a - b``, ``Int.sub``) -- the ℕ/ℤ divergence tooth T4 exists
to catch.  The compiler emits a bare ``a - b`` over the objects' DECLARED-carrier
binders and lets Lean's ``HSub`` resolve it; Lean's coercion-join (any ``Int``
operand => ``Int``) equals this ambient carrier on every reading the gate admits
(mixed-carrier ``-`` without ambient is refused; committed ambient readings all
have first-ref carrier == ambient), so eval, SMT and Lean agree three-way.

P3 adds ``Rat`` as a third carrier and ``/`` as a Rat-only term operator.  A Rat
reading evaluates to ``Fraction`` throughout (exact, never float -- a float
channel could not be a mirror of anything), sweeps the Farey-style grid
``rat_values(bound)`` instead of an interval, and totalises ``q / 0 = 0`` to
match Lean's field division and the SMT mirror's ``ite`` guard.  The gate
refuses a Rat/integer mix (rat:no-coercion), so every reading here is
single-carrier and the box choice is total.

Operator semantics match the emitted Lean (see the module docstrings of
math_compile.py / math_smt.py): ``+ * ^`` usual (``^`` a non-negative literal
exponent); ``-`` carrier-resolved (D8); ``/`` Rat-only, totalised at zero (P3);
``%`` / ``mod`` = ``a % b`` with Lean's
totalisation ``x % 0 = x`` (Python ``%`` matches ``Nat.mod`` / ``Int.emod`` on
the in-[0,|b|) convention for a positive divisor, D9); ``gcd(a,b)`` =
``gcd(|a|,|b|)`` (``Nat.gcd`` / ``Int.gcd``-returns-Nat).  Predicate atoms:
``= != <= <``; ``dvd(a,b)`` ("a divides b") = ``b % a == 0`` when ``a != 0`` else
``b == 0`` (Lean ``0 ∣ b ↔ b = 0``, D9/D13); ``even`` / ``odd`` by ``n % 2``;
``coprime(a,b)`` = ``gcd(|a|,|b|) == 1``; connectives ``and / or / implies``.

THE RESIDUE CARRIER (P4).  A ``ZMod n`` object's declared range is ``0..n-1``
-- the WHOLE carrier, not a bounded window on an infinite one.  That changes the
epistemic status of every sweep below on a pure-residue reading: ``bounded_
nonvacuous``, ``satisfying_instances`` and the ∃ shadow stop being bound-relative
EVIDENCE and become COMPLETE DECISIONS (raising ``bound`` cannot reach a value
the carrier does not have).  Arithmetic runs exactly over the integers and is
reduced ``% n`` at each ``=``/``!=`` atom, the one node where the quotient is
observable -- so ``-`` is real subtraction there, never ``Nat``'s truncation,
and the SMT mirror's atom wrap is the same rule written twice (T4).

Determinism: no clocks, no randomness; the domain is enumerated in a canonical
order (sum of |values|, then lexicographic) so every result is reproducible.

==============================================================================
THE BOUNDED-SHADOW ∃ MODE (WP-T6b; COMPRESSION.md §11.6 -- eval-channel only)
==============================================================================
The forall-only gates above enumerate EVERY declared object universally.  A
reading whose compiled statement carries a real `∃` (math_compile emits it)
cannot be mirrored that way -- an ∃-bound object enumerated universally checks
the WRONG statement.  §11.6 re-specifies the rung as an EVAL-CHANNEL
finitization: the compiled `∃` stays untouched in `lean_text`; here we add a
BOUNDED-SHADOW mode that models the ∃ as a FINITE DISJUNCTION over the bounded
range -- never the k-smallest sample (the §11.6 F1 soundness trace: a k-smallest
mask certifying a FALSE disjunction green is exactly what this must never do).

Supported shape (`exists_shadow_shape` classifies; anything else honest-skips
UPSTREAM in run/formalize.py, never universalised silently): the ∀-OUTER /
∃-INNER split that `parse_math_reading` admits -- the compiled binder prefix is
`∀* ∃*` (all universal binders precede all existential ones), there is at least
one ∃-bound object AND at least one OUTER object, the ∀/∃ object sets are
disjoint, and every HYPOTHESIS references OUTER objects only (hypotheses filter
the outer scope, as in the forall path).  Multiple ∃ objects (a product
disjunction) and multiple ∃ segments are supported; exists-only (no outer),
∃-before-∀ interleaving, and hypotheses over ∃-bound objects are OUT of the
mode (declared limitations, honest-skipped).

EXACT bounded-shadow semantics (the design decision §11.6 left implicit, made
explicit here and mirrored in the cert's `exists-finitized-enum` channel):

  * OUTER SCOPE.  Every OUTER assignment (each outer object over its declared
    bounded range: `Nat` -> `0..B`, `Int` -> `-B..B`) that satisfies ALL
    hypotheses is IN SCOPE -- the bounded shadow of the leading `∀`.  It is an
    EXHAUSTIVE ∀ over the bounded outer box (NOT the k-smallest sample the
    forall path uses for its corroboration instances), so a PASS means every
    in-bound hypothesis-admitted outer world has a witness.
  * EXISTS RANGE.  For an in-scope outer assignment the conclusion holds iff
    SOME assignment of the ∃-bound objects -- each over its FULL declared
    bounded range -- makes the conclusion evaluate True.  The disjunction is the
    FULL bounded product, never a k-smallest prefix.
  * EDGE POLICY (the deliberate bound-edge honesty).  The shadow certifies only
    the BOUNDED claim "∀ outer∈box with H, ∃ inner∈box, C"; it NEVER claims the
    unbounded `∃ m∈ℤ`.  A bounded witness IS a real witness, so a PASS is sound
    evidence FOR the real ∃ statement on the in-bound outer overlap.  But an
    outer assignment whose only witnesses lie OUTSIDE the box (e.g. `∀n ∃m, n<m`
    at n = B: no m∈[-B,B] exceeds B) legitimately REFUTES the bounded shadow --
    the shadow is conservative (it may over-refuse a truly-true UNBOUNDED
    statement), which is the SAFE direction: never a false green, per §11.6.
    Refutation witness = the OUTER assignment with no in-bound inner witness
    (same shape as the forall path's instance refutations).

Public API (kept small):
    eval_term, eval_pred,
    hypotheses_of, conclusions_of, hypotheses_hold, conclusion_holds,
    enumerate_domain, satisfying_instances, boundary_probes, bounded_nonvacuous,
    exists_shadow_shape, exists_conclusion_holds, exists_instances.
"""
from __future__ import annotations

import itertools
import math
from fractions import Fraction

from .math_reading import (MathReading, CARRIERS as _CARRIERS, _BIGOPS,
                           _zmod_modulus)

__all__ = [
    "eval_term", "eval_pred",
    "hypotheses_of", "conclusions_of", "hypotheses_hold", "conclusion_holds",
    "enumerate_domain", "satisfying_instances", "boundary_probes",
    "bounded_nonvacuous", "rat_values",
    "exists_shadow_shape", "exists_conclusion_holds", "exists_instances",
]

# The carrier whitelist is IMPORTED, never re-typed (P3).  It used to be a hand
# copy of math_reading.CARRIERS sitting one module away from the thing it
# mirrored -- a drift point that would have gone quiet the moment a carrier was
# added and this file was not touched.  Closed: one source, one tuple.


# --------------------------------------------------------------- ref walking
def _term_refs(term: dict) -> list:
    """Object names referenced by a term, left-to-right pre-order (dups kept) --
    the same walk the compiler uses, so carrier resolution cannot drift.  A
    big-operator's bound index is NOT an object: refs of the index are dropped
    from the walk (they are bound, not free), so callers only ever see declared
    objects."""
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
    if term.get("op") == "card":                     # P2: the set's index is bound
        setnode = term["args"][0]
        var = setnode["args"][0]["var"]
        out = []
        for a in setnode["args"][1:]:                 # bounds ({lit}) + filter pred
            out.extend(r for r in _term_refs(a) if r != var)
        return out
    out: list = []
    for a in term["args"]:
        out.extend(_term_refs(a))
    return out


def _zmod_carrier_of(carrier_of: dict, ambient):
    """P4: the `ZMod n` carrier a reading sits over, or None when it is not a
    residue reading.  SELF-CONTAINED -- it never consults the bare-name carrier
    tuple, so the pre-P4 resolution path below is untouched.

    Unlike the `-` carrier rule this is a property of the READING, not of a
    term's refs, and deliberately so: the gate pins ONE carrier per residue
    READING, so an all-literal term like `2 - 4` inside a `ZMod 5` reading is a
    residue term even though it references no object.  Resolving it by first-ref
    would silently hand such a term to the Int rule, which is the divergence the
    D8-class tooth plants.  Scanning in sorted name order keeps it
    deterministic; the gate makes the choice unique anyway."""
    if _zmod_modulus(ambient) is not None:
        return ambient
    for name in sorted(carrier_of):
        if _zmod_modulus(carrier_of[name]) is not None:
            return carrier_of[name]
    return None


def _term_carrier(term: dict, carrier_of: dict, ambient) -> str:
    """The carrier of a value-carrier-sensitive term (`-`), resolved to AGREE
    with the SMT mirror's ``math_smt._minus_carrier`` on every gate-passing
    reading (B1-A).  A declared ambient WINS; with no ambient the FIRST ref's
    declared carrier is used (identical to any-Nat-operand once the gate has
    refused the only shape where they differ -- a mixed-carrier `-` with no
    ambient); an all-literal term falls back to ``"Int"``.

    That ``"Int"`` fallback is reachable ONLY for a literal-only term (no ref
    resolves, no ambient is declared), and it is harmless there: over the
    integers a literal-only `-` is the same value on either carrier unless it
    goes negative, which is exactly the Nat-vs-Int case the gate's ambient rule
    already adjudicates.  A Rat reading never reaches it -- the gate refuses a
    Rat object mixed with an integer one, so any Rat ref present makes the
    first-ref rule return ``"Rat"`` (and a Rat reading with no refs at all
    carries an ambient).

    P4: a RESIDUE term answers with its `ZMod n` carrier STRING, which is
    neither ``"Nat"`` nor ``"Int"`` -- so ``-`` over a residue carrier takes the
    real-subtraction arm (never Nat truncation), and the reduction happens once,
    at the comparing atom, which is the only place the quotient is observable.
    The residue arm answers FIRST because it is a property of the reading, not
    of the term's refs: the first-ref rule below would hand an all-literal
    residue term to the integer carriers."""
    zmod = _zmod_carrier_of(carrier_of, ambient)            # P4
    if zmod is not None:
        return zmod
    if ambient in _CARRIERS:                         # ambient precedence (B1-A)
        return ambient
    for name in _term_refs(term):
        c = carrier_of.get(name)
        if c in _CARRIERS:
            return c
    return "Int"


# --------------------------------------------------------------- evaluation
def eval_term(term: dict, assignment: dict, carrier_of: dict, ambient):
    """Evaluate a value-producing F-G term under `assignment` (objname -> value)
    to an ``int`` on the integer carriers and a ``Fraction`` at Rat (P3).
    `carrier_of` maps objname -> "Nat"|"Int"|"Rat"; `ambient` is the reading's
    ambient carrier or None.  Models the compiled Lean's meaning; the
    value-carrier-sensitive operators are `-` (D8/T4 -- truncated at Nat, real
    everywhere else, Rat included) and `/` (Rat-only by the gate)."""
    if "ref" in term:
        return assignment[term["ref"]]
    if "lit" in term:
        return term["lit"]
    op = term["op"]
    args = term["args"]
    if op == "+":
        total = 0
        for a in args:
            total += eval_term(a, assignment, carrier_of, ambient)
        return total
    if op == "*":
        prod = 1
        for a in args:
            prod *= eval_term(a, assignment, carrier_of, ambient)
        return prod
    if op == "-":                                   # carrier-resolved (D8/T4)
        x = eval_term(args[0], assignment, carrier_of, ambient)
        y = eval_term(args[1], assignment, carrier_of, ambient)
        if _term_carrier(term, carrier_of, ambient) == "Nat":
            return max(0, x - y)                     # truncated Nat.sub
        # real Int.sub -- and, unchanged, real Rat.sub (P3): ONLY Nat
        # truncates, so the third carrier rides the arm Int already took.
        # `3 - 5` is -2 over Rat and 0 over Nat -- the D8 divergence tooth,
        # now witnessed against a third carrier.
        return x - y
    if op == "/":                                 # Rat-only division (P3/D9)
        x = eval_term(args[0], assignment, carrier_of, ambient)
        y = eval_term(args[1], assignment, carrier_of, ambient)
        # Lean TOTALISES division on a field: `q / 0 = 0` (the D9-class move
        # `%`'s `x % 0 = x` already makes).  The SMT mirror emits the mirror
        # image, `(ite (= y 0.0) 0.0 (/ x y))`, so the two channels agree cell
        # for cell including on the divisor-zero row a solver would otherwise
        # be free to invent a value for.
        if y == 0:
            return Fraction(0)
        return Fraction(x) / Fraction(y)
    if op in ("%", "mod"):                          # Nat.mod / Int.emod (D9)
        # UNREACHABLE at Rat: `_check_carrier_ops` refuses `%`/`mod` (and the
        # whole divisibility family: dvd, gcd, coprime, even, odd) over Rat at
        # the gate, so no Fraction ever reaches Python's `%` here.  Stated as a
        # note rather than a branch -- an extra arm would be dead code claiming
        # a semantics we have deliberately not frozen.
        x = eval_term(args[0], assignment, carrier_of, ambient)
        y = eval_term(args[1], assignment, carrier_of, ambient)
        if y == 0:
            return x                                  # Lean totalises x % 0 = x
        return x % y
    if op == "^":                                   # literal exponent (D10)
        base = eval_term(args[0], assignment, carrier_of, ambient)
        return base ** args[1]["lit"]
    if op == "gcd":                                 # Nat.gcd / Int.gcd (Nat val)
        x = eval_term(args[0], assignment, carrier_of, ambient)
        y = eval_term(args[1], assignment, carrier_of, ambient)
        return math.gcd(abs(x), abs(y))
    if op in _BIGOPS:                               # bounded fold (P1)
        # args = [{"var": i}, {"lit": lo}, {"lit": hi}, body]: exact exhaustive
        # iteration over the LITERAL index range (the whole admissibility
        # argument -- no approximation, no bound to trust).  The index enters
        # scope at carrier Nat, mirroring the gate and the SMT mirror.
        var = args[0]["var"]
        lo, hi = args[1]["lit"], args[2]["lit"]
        body = args[3]
        acc = 0 if op == "bigsum" else 1
        inner_carriers = {**carrier_of, var: "Nat"}
        for v in range(lo, hi + 1):
            val = eval_term(body, {**assignment, var: v},
                            inner_carriers, ambient)
            acc = acc + val if op == "bigsum" else acc * val
        return acc
    if op == "card":                                # bounded cardinality (P2)
        # |{ i in Icc lo hi | filter }| by exact exhaustive counting -- the same
        # admissibility argument as the fold: literal bounds, no approximation.
        # The index enters the filter's scope at carrier Nat (gate/SMT/compile
        # agree), and eval_pred decides the filter at each concrete index.
        setnode = args[0]
        var = setnode["args"][0]["var"]
        lo, hi = setnode["args"][1]["lit"], setnode["args"][2]["lit"]
        filt = setnode["args"][3]
        inner_carriers = {**carrier_of, var: "Nat"}
        return sum(1 for v in range(lo, hi + 1)
                   if eval_pred(filt, {**assignment, var: v},
                                inner_carriers, ambient))
    raise ValueError(f"eval_term: unknown term operator {op!r}")


def eval_pred(pred: dict, assignment: dict, carrier_of: dict, ambient) -> bool:
    """Evaluate a boolean F-G pred to a bool under `assignment` (see eval_term
    for the argument contract)."""
    op = pred["op"]
    args = pred["args"]
    if op == "and":
        return all(eval_pred(a, assignment, carrier_of, ambient) for a in args)
    if op == "or":
        return any(eval_pred(a, assignment, carrier_of, ambient) for a in args)
    if op == "implies":
        return (not eval_pred(args[0], assignment, carrier_of, ambient)
                or eval_pred(args[1], assignment, carrier_of, ambient))

    def t(x):
        return eval_term(x, assignment, carrier_of, ambient)

    if op in ("=", "!="):
        # P4 -- THE RESIDUE ATOM.  A `ZMod n` equation compares CONGRUENCE
        # CLASSES, so both sides evaluate EXACTLY over the integers (that is
        # what keeps `-` real subtraction rather than Nat truncation) and are
        # reduced `% n` HERE, at the one node where the quotient is observable.
        # Assignments already range over 0..n-1 (the exact domain sweep), so in
        # practice only literals exceed the modulus -- but reducing both sides
        # unconditionally keeps the rule a property of the ATOM, not of where a
        # value came from, which is what the SMT mirror's wrap also does.
        zmod = _zmod_carrier_of(carrier_of, ambient)
        if zmod is not None:
            n = _zmod_modulus(zmod)
            lhs, rhs = t(args[0]) % n, t(args[1]) % n
            return lhs == rhs if op == "=" else lhs != rhs
    if op == "=":
        return t(args[0]) == t(args[1])
    if op == "!=":
        return t(args[0]) != t(args[1])
    if op == "<=":
        return t(args[0]) <= t(args[1])
    if op == "<":
        return t(args[0]) < t(args[1])
    if op == "dvd":                                 # a divides b (D9/D13)
        a, b = t(args[0]), t(args[1])
        return (b % a == 0) if a != 0 else (b == 0)  # Lean 0 ∣ b ↔ b = 0
    if op == "even":
        return t(args[0]) % 2 == 0
    if op == "odd":
        return t(args[0]) % 2 != 0
    if op == "coprime":
        return math.gcd(abs(t(args[0])), abs(t(args[1]))) == 1
    raise ValueError(f"eval_pred: unknown atom/connective {op!r}")


# ---------------------------------------------------- hypotheses / conclusions
def _id(s: dict) -> str:
    return s["id"]


def hypotheses_of(reading: MathReading) -> list:
    """The hypothesis preds, in statement-id order (the compiler's chain order)."""
    return [s["lf"]["pred"]
            for s in sorted(reading.by_kind("hypothesis"), key=_id)]


def conclusions_of(reading: MathReading):
    """The single demanded-conclusion pred: the lone conclusion, or the several
    conclusions conjoined with `and` in id order -- exactly what the compiler
    emits as `C1 ∧ C2 ...`.  None only if there is no conclusion (the gate
    guarantees at least one, so this is defensive)."""
    preds = [s["lf"]["pred"]
             for s in sorted(reading.by_kind("conclusion"), key=_id)]
    if not preds:
        return None
    if len(preds) == 1:
        return preds[0]
    return {"op": "and", "args": preds}


def hypotheses_hold(reading: MathReading, assignment: dict) -> bool:
    """True iff EVERY hypothesis holds at `assignment` (vacuously True when the
    reading has no hypotheses)."""
    carrier_of = reading.objects()
    ambient = reading.ambient_carrier()
    return all(eval_pred(p, assignment, carrier_of, ambient)
               for p in hypotheses_of(reading))


def conclusion_holds(reading: MathReading, assignment: dict) -> bool:
    """True iff the demanded conclusion holds at `assignment`.  F2.2 (i): the
    caller instantiates a satisfying assignment and REQUIRES this to be True; a
    False instance refutes the formalization before proof search."""
    concl = conclusions_of(reading)
    if concl is None:
        return True
    return eval_pred(concl, assignment, reading.objects(),
                     reading.ambient_carrier())


# ----------------------------------------------------------- domain / instances
def _shell_tuples(ranges, budget, suffix_max):
    """Yield, in LEXICOGRAPHIC order over the given per-dimension ranges, every
    value tuple whose sum of |values| equals `budget`.  DFS with two exact
    prunes (a value's |v| must fit in the remaining budget, and the remaining
    dimensions' maximum reachable |sum| must cover what is left), so the walk
    touches only viable prefixes."""
    n = len(ranges)
    prefix = [0] * n

    def rec(i, remaining):
        if i == n:
            if remaining == 0:
                yield tuple(prefix)
            return
        if remaining > suffix_max[i]:
            return                                   # unreachable: prune
        for v in ranges[i]:
            a = abs(v)
            if a > remaining:
                continue
            if remaining - a > suffix_max[i + 1]:
                continue
            prefix[i] = v
            yield from rec(i + 1, remaining - a)

    yield from rec(0, budget)


# ------------------------------------------------------- the Rat sweep (P3)
# The integer carriers enumerate an INTERVAL; the rationals cannot -- there is
# no "next" rational, so a bounded box has to be chosen, and the choice is part
# of what the gate means.  The v1 box is a FAREY-STYLE grid: every p/q with
# 1 <= q <= Q and |p| <= P, Q = P = max(2, bound // 2).  Two properties earn it:
#
#   * it is DETERMINISTIC and duplicate-free -- Fraction normalizes 2/4 to 1/2,
#     so the set is built once and sorted, never accumulated by luck of order;
#   * its width stays comparable to the integer boxes (bound 8 -> 23 values vs
#     the Int box's 17), so the ceilings the exists-shadow already reasons about
#     (EXISTS_SHADOW_MAX_ASSIGNMENTS) keep meaning what they meant.
#     (23 is MEASURED -- `len(rat_values(8))` -- not the 25 the grid's corner
#     count suggests: p/q duplicates like 2/4 collapse under Fraction, which is
#     exactly why `_box_size` counts the grid instead of multiplying a formula.)
#
# The canonical ORDER is the same contract the integer path states: ascending
# SIZE, then the value itself.  Size generalizes |v| to `|p| + q - 1`, which
# agrees with |v| on the integers (q = 1), so the two carriers' shell walks are
# one idea and not two.  Rat and integer objects never share a reading (the gate
# refuses the mix, rat:no-coercion), so the box choice is per-reading total.
def _rat_size(v: Fraction) -> int:
    """The shell coordinate of a rational: `|p| + q - 1` for the canonical p/q.
    Equals `abs(v)` on the integers, so it extends the integer contract rather
    than replacing it."""
    return abs(v.numerator) + v.denominator - 1


def rat_values(bound: int = 8) -> list:
    """The in-bound Rat sweep, in canonical order (ascending size, then value).
    Deterministic and duplicate-free: built as a SET of `Fraction`s (which
    normalize, so 2/4 and 1/2 are one value) and sorted once."""
    q_max = max(2, bound // 2)
    p_max = q_max
    vals = {Fraction(p, q)
            for q in range(1, q_max + 1)
            for p in range(-p_max, p_max + 1)}
    return sorted(vals, key=lambda v: (_rat_size(v), v))


def _rat_shell_tuples(values, sizes, budget, suffix_max):
    """`_shell_tuples` for the Rat grid: the identical DFS with the identical
    two exact prunes, over per-dimension VALUE lists and their parallel SIZE
    lists instead of integer ranges.  Kept as its own function so the integer
    path -- whose lazy byte-order pins are load-bearing -- is not touched at
    all by the third carrier."""
    n = len(values)
    prefix = [None] * n

    def rec(i, remaining):
        if i == n:
            if remaining == 0:
                yield tuple(prefix)
            return
        if remaining > suffix_max[i]:
            return                                   # unreachable: prune
        for v, a in zip(values[i], sizes[i]):
            if a > remaining:
                continue
            if remaining - a > suffix_max[i + 1]:
                continue
            prefix[i] = v
            yield from rec(i + 1, remaining - a)

    yield from rec(0, budget)


def _rat_assignments(names, bound: int):
    """Every in-bound assignment over Rat-carrier `names`, in the canonical
    order (ascending size-sum, then lexicographic in the sorted value order) --
    the Rat sibling of `enumerate_domain`'s shell walk."""
    grid = rat_values(bound)
    values = [grid for _ in names]
    sizes = [[_rat_size(v) for v in grid] for _ in names]
    d = len(values)
    suffix_max = [0] * (d + 1)
    for i in range(d - 1, -1, -1):
        suffix_max[i] = suffix_max[i + 1] + (max(sizes[i]) if sizes[i] else 0)
    for budget in range(0, suffix_max[0] + 1):
        for vals in _rat_shell_tuples(values, sizes, budget, suffix_max):
            yield dict(zip(names, vals))


def _is_rat_box(carrier_of: dict) -> bool:
    """True when the reading's objects live on the Rat grid.  The gate refuses
    a Rat/integer mix, so this is all-or-nothing -- one reading, one box."""
    return "Rat" in carrier_of.values()


def enumerate_domain(reading: MathReading, bound: int = 8):
    """Yield every in-bound assignment (objname -> value) in a CANONICAL,
    deterministic order: ascending sum of |values|, then lexicographic on the
    value tuple in sorted-name order.  Each `Nat` object ranges `0..bound`; each
    `Int` object ranges `-bound..bound`; each `Rat` object ranges the Farey-style
    grid `rat_values(bound)` under the same contract with |v| generalized to the
    shell size (P3).

    LAZY by shells of equal |value|-sum: the previous implementation
    materialized and sorted the full cross product, which is 17^d tuples for d
    Int objects -- 1.4M for the corpus's five-object readings -- before the
    caller (which usually needs only the k SMALLEST satisfiers) saw the first
    one.  The shell DFS yields the IDENTICAL canonical sequence (same key,
    same lexicographic tie order) with early consumers touching only the
    shells they need."""
    objects = reading.objects()
    names = sorted(objects)
    if _is_rat_box(objects):                         # P3: the Rat grid
        yield from _rat_assignments(names, bound)
        return
    ranges = []
    for n in names:
        m = _zmod_modulus(objects[n])
        if m is not None:                            # P4: EXACT residue sweep
            # `range(0, n)` is the WHOLE carrier, not a bounded window on an
            # infinite one -- so a pure-residue sweep is a COMPLETE decision
            # (`bounded_nonvacuous` and the ∃ shadow stop being bound-relative
            # evidence and become verdicts).  `bound` is ignored here on
            # purpose: widening it cannot reach a value the carrier lacks.
            ranges.append(range(0, m))
        elif objects[n] == "Nat":
            ranges.append(range(0, bound + 1))
        else:                                        # Int
            ranges.append(range(-bound, bound + 1))
    d = len(ranges)
    suffix_max = [0] * (d + 1)
    for i in range(d - 1, -1, -1):
        suffix_max[i] = suffix_max[i + 1] + max(
            (abs(v) for v in (ranges[i].start, ranges[i].stop - 1)), default=0)
    for budget in range(0, suffix_max[0] + 1):
        for vals in _shell_tuples(ranges, budget, suffix_max):
            yield dict(zip(names, vals))


def satisfying_instances(reading: MathReading, k: int = 5,
                         bound: int = 8) -> list:
    """The k smallest (canonical order) in-bound assignments where ALL hypotheses
    hold (F2.2 (i)).  The caller checks `conclusion_holds` on each -- a False
    result refutes the formalization (wrong operator binding, wrong carrier)."""
    out: list = []
    for assignment in enumerate_domain(reading, bound):
        if hypotheses_hold(reading, assignment):
            out.append(assignment)
            if len(out) >= k:
                break
    return out


def boundary_probes(reading: MathReading, bound: int = 8) -> list:
    """For each hypothesis, ONE `{assignment, hypothesis_id}` that satisfies every
    OTHER hypothesis but MINIMALLY violates this one -- the "just outside" probe
    of F2.2 (ii) (n = 0 for `0 < n`, n = 2 for `2 < n`).  Recorded on the
    certificate as `boundary_behavior`, never auto-refused.

    "Minimally violate" = closest to the satisfying region: among in-bound
    assignments that satisfy the others but not this hypothesis, the one at
    least L1 distance from an assignment satisfying ALL hypotheses (canonical
    order breaks ties).  With no such satisfying assignment (contradictory
    hypotheses) the canonical-minimal violator is used.

    On a Rat box (P3) distances are `Fraction`s and the search's `dmin == 1`
    early exits are DISABLED: they encode "no two distinct integer points are
    closer than 1", which is exactly the assumption a dense carrier breaks.
    The remaining prune (abandon a partial sum once it reaches the running
    best) holds for any metric, so the Rat probe is the same probe, computed
    without the integer shortcut -- never a different verdict, only a slower
    one.  The integer paths keep both exits and stay byte-identical."""
    hyps = sorted(reading.by_kind("hypothesis"), key=_id)
    if not hyps:
        return []
    carrier_of = reading.objects()
    ambient = reading.ambient_carrier()
    names = sorted(carrier_of)
    # the L1 floor is an INTEGER-lattice fact; a dense box has no floor (P3).
    lattice = not _is_rat_box(carrier_of)

    # ONE canonical-order pass evaluating each hypothesis pred ONCE per
    # assignment (the previous implementation listed the full domain and
    # re-scanned it once per hypothesis).  An assignment with exactly one
    # false hypothesis is a candidate probe for that hypothesis; one with
    # none false satisfies all.  Semantics identical, work /(|hyps|+1).
    preds = [h["lf"]["pred"] for h in hyps]
    sat_all: list = []                    # value tuples satisfying every hyp
    cands_for: list = [[] for _ in hyps]  # per-hyp: satisfy others, not it
    for asg in enumerate_domain(reading, bound):
        truth = [eval_pred(p, asg, carrier_of, ambient) for p in preds]
        nfalse = truth.count(False)
        vals = tuple(asg[n] for n in names)
        if nfalse == 0:
            sat_all.append(vals)
        elif nfalse == 1:
            cands_for[truth.index(False)].append(vals)

    results: list = []
    for i, h in enumerate(hyps):
        cands = cands_for[i]
        if not cands:
            continue
        if sat_all:
            # best = min over cands of (min L1 to any all-hyps satisfier);
            # probe = the canonically FIRST cand achieving it.  Exact early
            # exits (no verdict change): a distance can never be < 1 (the
            # tuples differ), a partial L1 sum >= the running dmin/best can
            # be abandoned, and once best == 1 no later cand can win.
            best, probe_vals = None, None
            for c in cands:
                dmin = None
                for s in sat_all:
                    dcs, cut = 0, (dmin if best is None
                                   else min(dmin, best) if dmin is not None
                                   else best)
                    for a, b2 in zip(c, s):
                        dcs += abs(a - b2)
                        if cut is not None and dcs >= cut:
                            break
                    else:
                        if dmin is None or dcs < dmin:
                            dmin = dcs
                            if lattice and dmin == 1:
                                break                 # L1 floor reached
                if dmin is not None and (best is None or dmin < best):
                    best, probe_vals = dmin, c
                    if lattice and best == 1:
                        break                         # no cand can beat 1
            probe = dict(zip(names, probe_vals))
        else:
            probe = dict(zip(names, cands[0]))        # canonical-minimal
        results.append({"assignment": probe, "hypothesis_id": h["id"]})
    return results


def bounded_nonvacuous(reading: MathReading, bound: int = 8) -> bool:
    """True iff some in-bound assignment satisfies ALL hypotheses -- the Lean-free
    corroboration channel for F2.1.  A dual-SMT `unsat` refuses at stage
    `nonvacuity` ONLY when this ALSO finds no witness (else it is a first-class
    `mirror-divergence` event, never a silent refusal; T4)."""
    for assignment in enumerate_domain(reading, bound):
        if hypotheses_hold(reading, assignment):
            return True
    return False


# ================================================== bounded-shadow ∃ mode (T6b)
# The forall-only gates above are UNTOUCHED (their lazy byte-order pins must stay
# green).  Everything below is the SEPARATE ∃-aware path per COMPRESSION.md
# §11.6; run/formalize.py routes a reading here only after `exists_shadow_shape`
# classifies it as a supported ∀-outer/∃-inner reading.
def _pred_refs(pred: dict) -> list:
    """Object names referenced anywhere in a pred, pre-order (dups kept) -- the
    ∃-mode's own walker (mirrors math_compile._pred_refs; used only to check that
    hypotheses stay within the outer scope)."""
    op = pred["op"]
    out: list = []
    if op in ("and", "or", "implies"):
        for a in pred["args"]:
            out.extend(_pred_refs(a))
    else:
        for a in pred["args"]:
            out.extend(_term_refs(a))
    return out


# Combinatorial ceiling for the bounded-shadow enumeration (§11.6 attack-2
# guard).  The gate is an EXHAUSTIVE outer box times the FULL inner product:
# |box|^|outer| * |box|^|exists| conclusion evaluations, where |box| is 2B+1
# (Int) or B+1 (Nat).  This grows as ~17^(o+e) at B=8, so five combined Int
# objects is ~1.4M evals (seconds) and six is ~24M (MINUTES).  An oversize
# SUPPORTED shape therefore HONEST-SKIPS with an `exists-domain-too-large`
# reason rather than hanging -- a documented combinatorial bound, never a false
# green (the skip is the same refusal plumbing as the other out-of-mode shapes).
# The ceiling is chosen to admit every realistic authored reading (the committed
# and staged ∃ sources are all <=3 combined objects, ~5k evals) while cutting off
# the minutes-plus regime.
EXISTS_SHADOW_MAX_ASSIGNMENTS = 2_000_000


def _box_size(names, carrier_of, bound: int) -> int:
    """The number of in-bound assignments over `names` (product of each object's
    range width: `Nat` -> B+1, `Int` -> 2B+1, `Rat` -> the Farey grid's width,
    `len(rat_values(bound))`, `ZMod n` -> n, its EXACT size).  Empty name set ->
    1.  The Rat width is MEASURED, not formula'd: the grid drops duplicates, so
    counting it is the only honest way to keep the exists-shadow ceiling meaning
    what it says.  Kept in step with `_ranges_for`: this is the ∃-shadow
    ceiling's arithmetic, so a residue object must contribute its true width or
    the ceiling would price a complete sweep as if it were an Int box."""
    rat_width = None
    n = 1
    for name in names:
        c = carrier_of[name]
        m = _zmod_modulus(c)                         # P4: exact carrier size
        if m is not None:
            n *= m
        elif c == "Rat":
            if rat_width is None:
                rat_width = len(rat_values(bound))
            n *= rat_width
        elif c == "Nat":
            n *= bound + 1
        else:
            n *= 2 * bound + 1
    return n


def exists_shadow_shape(reading: MathReading, bound=None) -> dict:
    """Classify a reading's quantifier structure for the bounded-shadow ∃ mode.

    Returns one of:
      {"mode": "forall-only"}                       -- no ∃ binder (existing path)
      {"mode": "supported", "outer": [...], "exists": [...]}   -- ∀-outer/∃-inner
      {"mode": "unsupported", "reason": <str>}      -- honest-skip beyond the mode

    Supported iff the compiled binder prefix is `∀* ∃*` with >=1 ∃-bound object
    AND >=1 outer object, the ∀/∃ object sets are disjoint, and no hypothesis
    references an ∃-bound object (see the module docstring for the exact
    semantics).  `outer` is every declared object that is NOT ∃-bound (the
    forall-bound objects plus the leading-∀ free objects), sorted; `exists` is
    the ∃-bound objects, sorted.

    When `bound` is given, an otherwise-supported shape whose bounded-shadow
    enumeration would exceed `EXISTS_SHADOW_MAX_ASSIGNMENTS` evaluations is
    reclassified `unsupported` (`exists-domain-too-large`); with `bound=None`
    the classification is pure shape (no size guard)."""
    q_stmts = sorted(reading.by_kind("quantifier"), key=_id)
    exists_objs: set = set()
    forall_objs: set = set()
    for s in q_stmts:
        binder = s["lf"].get("binder")
        objs = s["lf"].get("objects", [])
        if binder == "exists":
            exists_objs.update(objs)
        elif binder == "forall":
            forall_objs.update(objs)

    if not exists_objs:
        return {"mode": "forall-only"}

    # `∀* ∃*` prefix order: once an ∃ segment appears (statement-id order), no
    # later segment may be ∀ (that would compile to ∃...∀..., ∃-outer/∀-inner --
    # not this mode).
    seen_exists = False
    for s in q_stmts:
        b = s["lf"].get("binder")
        if b == "exists":
            seen_exists = True
        elif b == "forall" and seen_exists:
            return {"mode": "unsupported",
                    "reason": ("exists-before-forall: the compiled binder order "
                               "is not ∀*∃* (a forall segment follows an exists "
                               "segment); the bounded-shadow models only the "
                               "∀-outer/∃-inner split")}

    if forall_objs & exists_objs:
        return {"mode": "unsupported",
                "reason": ("an object is bound by BOTH a forall and an exists "
                           "quantifier; the outer/inner split is ambiguous")}

    objects = reading.objects()
    exists_names = sorted(exists_objs)
    outer_names = sorted(set(objects) - exists_objs)
    if not outer_names:
        return {"mode": "unsupported",
                "reason": ("exists-only (no forall/outer scope): beyond the "
                           "∀-outer/∃-inner bounded-shadow mode")}

    for h in reading.by_kind("hypothesis"):
        refs = set(_pred_refs(h["lf"]["pred"]))
        if refs & exists_objs:
            return {"mode": "unsupported",
                    "reason": ("a hypothesis references an exists-bound object; "
                               "the bounded-shadow requires hypotheses to filter "
                               "the outer scope only")}

    if bound is not None:
        n_outer = _box_size(outer_names, objects, bound)
        n_inner = _box_size(exists_names, objects, bound)
        if n_outer * n_inner > EXISTS_SHADOW_MAX_ASSIGNMENTS:
            return {"mode": "unsupported",
                    "reason": (
                        "exists-domain-too-large: the bounded-shadow gate is an "
                        "exhaustive outer box x full inner product, "
                        f"{n_outer}*{n_inner} = {n_outer * n_inner} conclusion "
                        f"evaluations at bound {bound}, over the "
                        f"{EXISTS_SHADOW_MAX_ASSIGNMENTS} ceiling (minutes+); the "
                        "shape honest-skips rather than hang -- a documented "
                        "combinatorial bound, never a false green")}

    return {"mode": "supported", "outer": outer_names, "exists": exists_names}


def _ranges_for(names, carrier_of, bound):
    """The per-object in-bound value sequence for a subset of object names
    (`Nat` -> 0..bound, `Int` -> -bound..bound, `Rat` -> the Farey grid list,
    `ZMod n` -> the EXACT 0..n-1 carrier; see `enumerate_domain`).  Every
    consumer iterates it, so a list and a `range` are interchangeable here; the
    integer carriers keep their `range` objects verbatim so the integer callers
    (math_witness, run/anchor) see byte-identical sequences."""
    ranges = []
    for n in names:
        m = _zmod_modulus(carrier_of[n])
        if m is not None:                            # P4: EXACT residue sweep
            ranges.append(range(0, m))
        elif carrier_of[n] == "Nat":
            ranges.append(range(0, bound + 1))
        elif carrier_of[n] == "Rat":                 # P3: the Farey grid
            ranges.append(rat_values(bound))
        else:
            ranges.append(range(-bound, bound + 1))
    return ranges


def _canonical_assignments(names, carrier_of, bound):
    """Yield every in-bound assignment over `names` in the SAME canonical order
    as `enumerate_domain` (ascending |value|-sum, then lexicographic), restricted
    to a subset of objects -- reuses the shell DFS so the outer refutation
    witness is the canonically-first offender."""
    if _is_rat_box(carrier_of):                      # P3: the Rat grid
        yield from _rat_assignments(names, bound)
        return
    ranges = _ranges_for(names, carrier_of, bound)
    d = len(ranges)
    suffix_max = [0] * (d + 1)
    for i in range(d - 1, -1, -1):
        suffix_max[i] = suffix_max[i + 1] + max(
            (abs(v) for v in (ranges[i].start, ranges[i].stop - 1)), default=0)
    for budget in range(0, suffix_max[0] + 1):
        for vals in _shell_tuples(ranges, budget, suffix_max):
            yield dict(zip(names, vals))


def exists_conclusion_holds(reading: MathReading, outer_assignment: dict,
                            exists_names, bound: int = 8) -> bool:
    """∃-disjunct over the FULL bounded range of the ∃-bound objects: True iff
    SOME assignment of `exists_names` (each over its full declared bounded range)
    makes the conclusion hold with the outer objects fixed by `outer_assignment`.
    The FULL bounded product, NEVER a k-smallest prefix (§11.6 F1: a k-smallest
    mask certifying a false disjunction green is what this must never do)."""
    concl = conclusions_of(reading)
    if concl is None:
        return True
    carrier_of = reading.objects()
    ambient = reading.ambient_carrier()
    ranges = _ranges_for(exists_names, carrier_of, bound)
    for combo in itertools.product(*ranges):
        asg = dict(outer_assignment)
        asg.update(zip(exists_names, combo))
        if eval_pred(concl, asg, carrier_of, ambient):
            return True
    return False


def exists_instances(reading: MathReading, outer_names, exists_names,
                     bound: int = 8) -> dict:
    """The bounded-shadow instance gate (T6b): for EVERY hypothesis-admitted
    outer assignment within the bounded box, require an in-bound ∃ witness making
    the conclusion hold.  Exhaustive over the outer box (not the k-smallest
    sample), so a pass means the bounded statement holds for every in-bound outer
    world.

    Returns ``{"ok", "witness", "n_outer_checked", "n_outer_admitted"}``.  On
    failure ``witness`` is the canonically-first hypothesis-admitted outer
    assignment with NO in-bound ∃ witness (same shape as the forall-path
    instance refutation)."""
    carrier_of = reading.objects()
    ambient = reading.ambient_carrier()
    hyps = hypotheses_of(reading)
    n_checked = 0
    n_admitted = 0
    for outer in _canonical_assignments(outer_names, carrier_of, bound):
        n_checked += 1
        if not all(eval_pred(p, outer, carrier_of, ambient) for p in hyps):
            continue
        n_admitted += 1
        if not exists_conclusion_holds(reading, outer, exists_names, bound):
            return {"ok": False, "witness": outer,
                    "n_outer_checked": n_checked, "n_outer_admitted": n_admitted}
    return {"ok": True, "witness": None,
            "n_outer_checked": n_checked, "n_outer_admitted": n_admitted}
