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

CARRIER-RESOLUTION RULE (WP-H depends on this AGREEING with the compiler).
Every evaluation models the meaning of the compiled Lean, whose binders are the
objects' DECLARED carriers (``MathReading.objects()``) -- never the compiler's
ambient-first ``_resolve_carrier`` rule, which the compiler uses ONLY to pick a
carrier-indexed Lean NAME (``Nat.gcd`` vs ``Int.gcd``, ``Nat.Coprime``) and which
never changes a computed value (``Nat.gcd`` and ``Int.gcd`` return the same
|gcd|).  So the ONE value-carrier-sensitive operator is ``-``:

    carrier of a term = the declared carrier of the FIRST object referenced in a
    left-to-right pre-order walk of the term (its operands share it in-fragment);
    a term with no object refs (a bare / all-literal term) adopts the surrounding
    carrier, falling back to ``ambient`` then ``"Int"``.

This is exactly what Lean's typed binders produce, so ``a - b`` over ``Nat``
binders truncates (``max(0, a - b)``, ``Nat.sub``) while over ``Int`` it is real
(``a - b``, ``Int.sub``) -- the ℕ/ℤ divergence tooth T4 exists to catch.

Operator semantics match the emitted Lean (see the module docstrings of
math_compile.py / math_smt.py): ``+ * ^`` usual (``^`` a non-negative literal
exponent); ``-`` carrier-resolved (D8); ``%`` / ``mod`` = ``a % b`` with Lean's
totalisation ``x % 0 = x`` (Python ``%`` matches ``Nat.mod`` / ``Int.emod`` on
the in-[0,|b|) convention for a positive divisor, D9); ``gcd(a,b)`` =
``gcd(|a|,|b|)`` (``Nat.gcd`` / ``Int.gcd``-returns-Nat).  Predicate atoms:
``= != <= <``; ``dvd(a,b)`` ("a divides b") = ``b % a == 0`` when ``a != 0`` else
``b == 0`` (Lean ``0 ∣ b ↔ b = 0``, D9/D13); ``even`` / ``odd`` by ``n % 2``;
``coprime(a,b)`` = ``gcd(|a|,|b|) == 1``; connectives ``and / or / implies``.

Determinism: no clocks, no randomness; the domain is enumerated in a canonical
order (sum of |values|, then lexicographic) so every result is reproducible.

Public API (kept small):
    eval_term, eval_pred,
    hypotheses_of, conclusions_of, hypotheses_hold, conclusion_holds,
    enumerate_domain, satisfying_instances, boundary_probes, bounded_nonvacuous.
"""
from __future__ import annotations

import itertools
import math

from .math_reading import MathReading

__all__ = [
    "eval_term", "eval_pred",
    "hypotheses_of", "conclusions_of", "hypotheses_hold", "conclusion_holds",
    "enumerate_domain", "satisfying_instances", "boundary_probes",
    "bounded_nonvacuous",
]

_CARRIERS = ("Nat", "Int")


# --------------------------------------------------------------- ref walking
def _term_refs(term: dict) -> list:
    """Object names referenced by a term, left-to-right pre-order (dups kept) --
    the same walk the compiler uses, so carrier resolution cannot drift."""
    if "ref" in term:
        return [term["ref"]]
    if "lit" in term:
        return []
    out: list = []
    for a in term["args"]:
        out.extend(_term_refs(a))
    return out


def _term_carrier(term: dict, carrier_of: dict, ambient) -> str:
    """The carrier Lean's typed binders give this term (see module docstring)."""
    for name in _term_refs(term):
        c = carrier_of.get(name)
        if c in _CARRIERS:
            return c
    return ambient if ambient in _CARRIERS else "Int"


# --------------------------------------------------------------- evaluation
def eval_term(term: dict, assignment: dict, carrier_of: dict, ambient) -> int:
    """Evaluate a value-producing F-G term to an int under `assignment`
    (objname -> int).  `carrier_of` maps objname -> "Nat"|"Int"; `ambient` is the
    reading's ambient carrier ("Nat"|"Int") or None.  Models the compiled Lean's
    meaning; the only value-carrier-sensitive operator is `-` (D8/T4)."""
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
        return x - y                                 # real Int.sub
    if op in ("%", "mod"):                          # Nat.mod / Int.emod (D9)
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
def enumerate_domain(reading: MathReading, bound: int = 8):
    """Yield every in-bound assignment (objname -> int) in a CANONICAL,
    deterministic order: ascending sum of |values|, then lexicographic on the
    value tuple in sorted-name order.  Each `Nat` object ranges `0..bound`; each
    `Int` object ranges `-bound..bound`."""
    objects = reading.objects()
    names = sorted(objects)
    ranges = []
    for n in names:
        if objects[n] == "Nat":
            ranges.append(range(0, bound + 1))
        else:                                        # Int
            ranges.append(range(-bound, bound + 1))
    combos = sorted(itertools.product(*ranges),
                    key=lambda vals: (sum(abs(v) for v in vals), vals))
    for vals in combos:
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
    hypotheses) the canonical-minimal violator is used."""
    hyps = sorted(reading.by_kind("hypothesis"), key=_id)
    if not hyps:
        return []
    carrier_of = reading.objects()
    ambient = reading.ambient_carrier()
    names = sorted(carrier_of)
    domain = list(enumerate_domain(reading, bound))     # canonical order

    results: list = []
    for i, h in enumerate(hyps):
        hi = h["lf"]["pred"]
        others = [hh["lf"]["pred"] for j, hh in enumerate(hyps) if j != i]
        cands: list = []                                # satisfy others, not hi
        satisfiers: list = []                           # satisfy all hyps
        for asg in domain:
            others_ok = all(eval_pred(p, asg, carrier_of, ambient)
                            for p in others)
            if not others_ok:
                continue
            if eval_pred(hi, asg, carrier_of, ambient):
                satisfiers.append(asg)
            else:
                cands.append(asg)
        if not cands:
            continue
        if satisfiers:
            def _dist(v):
                return min(sum(abs(v[n] - s[n]) for n in names)
                           for s in satisfiers)
            best = min(_dist(v) for v in cands)
            probe = next(v for v in cands if _dist(v) == best)
        else:
            probe = cands[0]                            # canonical-minimal
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
