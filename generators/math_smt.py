"""The SMT mirror of the MathReading hypothesis set (F2.1 non-vacuity).

This module renders the *hypothesis set* of a MathReading to SMT-LIB -- the
mathematical analogue of ``reading_compile.demands_smt``.  The kernel feeds the
rendered obligation to Z3 AND CVC5 (``kernel.backends.SmtBackend``) to decide,
before anyone proves the theorem, whether a world satisfying every side
condition exists.  An unsatisfiable hypothesis set would certify *vacuously*, so
non-vacuity refuses it (F2.1).

TRUST RELATIONSHIP (T4 -- read this before treating a disagreement as a bug).
This mirror and the compiler (``generators/math_compile.py``) are TWO
hand-written translations of ONE source -- the F-G pred/term AST frozen in
``generators/math_reading.py``.  They must AGREE.  This is emphatically NOT an
independence differential (house rule 7 does not apply): both sides descend from
the same grammar, so a shared misreading is invisible to a mirror-vs-compiler
comparison.  The hazard here is the two-translations-of-one-text bug class
(TRUST 1.2e), and F2.1 handles it with a direction split: dual-solver ``sat``
is corroborated by Lean ``decide`` on the compiled hypotheses (a witness the
mirror cannot fake), and dual-solver ``unsat`` alone never refuses -- it needs
Lean-side corroboration too, else it is a first-class ``mirror-divergence``
event.  Nothing in THIS module adjudicates; it only renders.

Rendering rules (all from the F-G freeze):
  * Every declared object becomes ``(declare-const x Int)`` -- BOTH Nat- and
    Int-carrier objects are modelled over the integers.  A Nat-carrier object
    additionally asserts ``(assert (>= x 0))``.
  * Comparisons: ``=`` -> ``=``, ``!=`` -> ``distinct``, ``<=`` -> ``<=``,
    ``<`` -> ``<``.
  * ``dvd(a, b)`` (a divides b) -> ``(ite (= a 0) (= b 0) (= (mod b a) 0))``.
    The a=0 arm matches Lean's convention and is MANDATORY: SMT mod-by-zero is
    underspecified (D9).
  * ``even(n)`` -> ``(= (mod n 2) 0)``; ``odd(n)`` -> ``(= (mod n 2) 1)``
    (emod convention, D9).
  * term ``%`` and the ``mod`` word (term role) are rendered to match eval's
    Python ``%`` EXACTLY over ALL divisors (D9/B2), closing two seams between
    SMT-LIB ``mod`` and ``%``:
      - ``y = 0``: SMT-LIB leaves ``mod`` unconstrained, so a bare ``(mod x y)``
        lets a solver invent a value; totalise to ``x`` (Lean ``x % 0 = x``, B2).
      - ``y < 0``: SMT-LIB ``mod`` is EUCLIDEAN (remainder in ``[0,|y|)``) while
        Python ``%`` takes the sign of the DIVISOR (B2-A).  They agree for
        ``y > 0``; for ``y < 0`` the divisor-signed remainder is rebuilt from the
        Euclidean one as ``-((-x) emod (-y))``.
    The emitted term is
    ``(ite (= y 0) x (ite (> y 0) (mod x y) (- (mod (- x) (- y)))))`` -- verified
    cell-by-cell against ``eval_term`` on ``[-6,6]^2``.
  * ``-`` is CARRIER-RESOLVED (D8/T4).  Over Int: ``(- x y)``.  Over Nat:
    truncated ``(ite (>= x y) (- x y) 0)`` -- a bare ``-`` would silently
    reintroduce the N/Z divergence T4 exists to catch.  The carrier is the
    reading's ambient carrier; with no ambient it defaults to the operands'
    object carriers (any Nat operand -> truncated, else Int).
  * ``+``, ``*`` -> ``(+ ...)``, ``(* ...)`` (n-ary).
  * ``^`` with a LITERAL exponent unfolds to repeated ``*`` (SMT-LIB has no
    exponentiation, D10); exponent 0 -> ``1``, exponent 1 -> the base.
  * ``gcd`` and ``coprime`` are ``enum_only`` -- they have NO sound SMT
    rendering.  ``smt_representable`` returns False for any hypothesis using
    one and ``hypotheses_smt`` returns None, routing the obligation to the
    decidable-enumeration channel named on the certificate.

Logic selection.  ``QF_LIA`` when every hypothesis is linear; else ``QF_NIA``.
A hypothesis is nonlinear when a ``*`` has two or more non-constant operands,
when a ``%``/``mod`` (or the ``mod b a`` a ``dvd`` unfolds to) divides by a
non-constant, or when ``^`` raises a non-constant base to an exponent >= 2.
CVC5's parser enforces the declared logic strictly -- it errors on ``mod`` by a
variable under ``QF_LIA`` -- so this classification is required for
correctness, not merely advisory.  Nonlinear (``QF_NIA``) hypotheses may return
``unknown`` from a solver (D10); F2.1 reads that as the enumeration-fallback
signal, not a refusal.
"""
from __future__ import annotations

from .math_reading import MATH_OPERATORS, CARRIERS, MathReading, _BIGOPS

# Single-sourced from the frozen operator table: the connectives (whose args
# are preds, not terms) and the words that have no sound SMT rendering.
_CONNECTIVES = ("and", "or", "implies")
_ENUM_ONLY = frozenset(w for w, i in MATH_OPERATORS.items() if i.get("enum_only"))


# --------------------------------------------------------------- helpers
def _render_lit(v: int) -> str:
    # SMT-LIB2 has no negative numerals; a negative literal is `(- n)`.
    return f"(- {-v})" if v < 0 else str(v)


def _collect_refs(term, out) -> None:
    """Gather every object name referenced anywhere inside a term.  A
    big-operator's bound index is dropped (bound, not free) so declarations and
    carrier checks only ever see declared objects."""
    if not isinstance(term, dict):
        return
    if "ref" in term:
        out.add(term["ref"])
        return
    if "lit" in term or "var" in term:
        return
    if term.get("op") in _BIGOPS:
        var = term["args"][0]["var"]
        inner: set = set()
        for a in term["args"][1:]:
            _collect_refs(a, inner)
        out.update(inner - {var})
        return
    if term.get("op") == "card":                # P2: the set's index is bound
        setnode = term["args"][0]
        var = setnode["args"][0]["var"]
        inner2: set = set()
        for a in setnode["args"][1:]:           # bounds + the filter pred
            _collect_refs(a, inner2)
        out.update(inner2 - {var})
        return
    for a in term.get("args", []):
        _collect_refs(a, out)


def _minus_carrier(args, objects, ambient) -> str:
    """Resolve the carrier of a `-` node (D8).  The ambient carrier wins; with
    no ambient, any Nat operand object forces the truncated rendering, else
    Int."""
    if ambient in CARRIERS:
        return ambient
    refs = set()
    for a in args:
        _collect_refs(a, refs)
    if any(objects.get(r) == "Nat" for r in refs):
        return "Nat"
    return "Int"


# --------------------------------------------------------------- rendering
def render_term(term, objects, carrier, env=None) -> str:
    """Render a value-producing term to an SMT-LIB expression over Int.

    `objects` maps declared object name -> carrier; `carrier` is the reading's
    ambient carrier (or None), used only to resolve `-` (D8).  `env` maps a
    big-operator's bound index to its CONCRETE value during unrolling (the P1
    analogue of ^'s D10 unfold): the index is never declared as a const -- each
    unrolled copy substitutes the numeral.  Carrier resolution for `-` inside a
    body reads the index from `objects` (extended to Nat by the bigop case), so
    the truncation decision matches eval's index-is-Nat rule, never the
    already-substituted numeral."""
    if "ref" in term:
        if env is not None and term["ref"] in env:
            return _render_lit(env[term["ref"]])
        return term["ref"]
    if "lit" in term:
        return _render_lit(term["lit"])
    op, args = term["op"], term["args"]
    if op in _BIGOPS:                      # bounded fold: unroll (P1 / D10 kin)
        var = args[0]["var"]
        lo, hi = args[1]["lit"], args[2]["lit"]
        body = args[3]
        if lo > hi:                        # empty fold: the identity element
            return "0" if op == "bigsum" else "1"
        inner_objects = {**objects, var: "Nat"}
        pieces = [render_term(body, inner_objects, carrier,
                              {**(env or {}), var: v})
                  for v in range(lo, hi + 1)]
        if len(pieces) == 1:
            return pieces[0]
        smt_op = "+" if op == "bigsum" else "*"
        return f"({smt_op} " + " ".join(pieces) + ")"
    if op == "card":                      # bounded cardinality: unroll (P2)
        # |{i in Icc lo hi | filter}| = sum over the LITERAL index range of the
        # 0/1 indicator (ite filter 1 0) -- the same unroll discipline as the
        # fold, so the count is a total Int expression the solver evaluates
        # exactly.  The filter renders with the index in scope at Nat and the
        # numeral substituted through `env`, mirroring eval's counting.
        setnode = args[0]
        var = setnode["args"][0]["var"]
        lo, hi = setnode["args"][1]["lit"], setnode["args"][2]["lit"]
        filt = setnode["args"][3]
        if lo > hi:                        # empty set: cardinality 0
            return "0"
        inner_objects = {**objects, var: "Nat"}
        pieces = [f"(ite {render_pred(filt, inner_objects, carrier, {**(env or {}), var: v})} 1 0)"
                  for v in range(lo, hi + 1)]
        if len(pieces) == 1:
            return pieces[0]
        return "(+ " + " ".join(pieces) + ")"
    if op == "+":
        return "(+ " + " ".join(render_term(a, objects, carrier, env)
                                for a in args) + ")"
    if op == "*":
        return "(* " + " ".join(render_term(a, objects, carrier, env)
                                for a in args) + ")"
    if op == "-":
        a = render_term(args[0], objects, carrier, env)
        b = render_term(args[1], objects, carrier, env)
        if _minus_carrier(args, objects, carrier) == "Nat":
            return f"(ite (>= {a} {b}) (- {a} {b}) 0)"   # truncated Nat.sub
        return f"(- {a} {b})"
    if op in ("%", "mod"):                 # match eval's Python `%` EXACTLY (D9/B2)
        x = render_term(args[0], objects, carrier, env)
        y = render_term(args[1], objects, carrier, env)
        # Two seams between SMT-LIB `mod` and eval's Python `%`, both closed here:
        #   y = 0: SMT-LIB leaves `mod` unconstrained -> totalise to x (Lean's
        #          `x % 0 = x`), else a solver invents a value and diverges (B2).
        #   y < 0: SMT-LIB `mod` is EUCLIDEAN (remainder in [0,|y|)) while Python
        #          `%` takes the sign of the DIVISOR (B2-A).  They agree for y>0;
        #          for y<0, Python r = -((-x) emod (-y)) rebuilds the divisor-
        #          signed remainder from the Euclidean one (verified exhaustively
        #          on [-6,6]^2 against eval_term; test_term_mod_matches_eval_grid).
        return (f"(ite (= {y} 0) {x} "
                f"(ite (> {y} 0) (mod {x} {y}) (- (mod (- {x}) (- {y})))))")
    if op == "^":
        k = args[1]["lit"]                 # validated non-negative literal (D10)
        if k == 0:
            return "1"
        base = render_term(args[0], objects, carrier, env)
        if k == 1:
            return base
        return "(* " + " ".join([base] * k) + ")"
    # gcd is enum_only: unreachable once smt_representable gates the reading.
    raise ValueError(f"term operator {op!r} has no SMT rendering "
                     f"(enum_only?); render only smt_representable readings")


def render_pred(pred, objects, carrier, env=None) -> str:
    """Render a boolean pred to an SMT-LIB formula.  Public helper (F2.1 API).
    `env` (P2) maps a set node's bound index to its concrete value while
    unrolling a `card` filter -- threaded to render_term exactly as in the
    big-operator unroll, so a filter over the index substitutes numerals."""
    op, args = pred["op"], pred["args"]
    if op == "and":
        return "(and " + " ".join(render_pred(a, objects, carrier, env)
                                  for a in args) + ")"
    if op == "or":
        return "(or " + " ".join(render_pred(a, objects, carrier, env)
                                 for a in args) + ")"
    if op == "implies":
        return (f"(=> {render_pred(args[0], objects, carrier, env)} "
                f"{render_pred(args[1], objects, carrier, env)})")

    def t(x):
        return render_term(x, objects, carrier, env)

    if op == "=":
        return f"(= {t(args[0])} {t(args[1])})"
    if op == "!=":
        return f"(distinct {t(args[0])} {t(args[1])})"
    if op == "<=":
        return f"(<= {t(args[0])} {t(args[1])})"
    if op == "<":
        return f"(< {t(args[0])} {t(args[1])})"
    if op == "dvd":                         # a divides b, D9 a=0 special case
        a, b = t(args[0]), t(args[1])
        return f"(ite (= {a} 0) (= {b} 0) (= (mod {b} {a}) 0))"
    if op == "even":
        return f"(= (mod {t(args[0])} 2) 0)"
    if op == "odd":
        return f"(= (mod {t(args[0])} 2) 1)"
    # coprime is enum_only: unreachable once smt_representable gates the reading.
    raise ValueError(f"atom {op!r} has no SMT rendering (enum_only?); render "
                     f"only smt_representable readings")


# --------------------------------------------------------- representability
def _term_uses_enum(term) -> bool:
    if "ref" in term or "lit" in term or "var" in term:
        return False
    if term["op"] == "card":                    # P2: descend into the filter pred
        return _pred_uses_enum(term["args"][0]["args"][3])
    if term["op"] in _ENUM_ONLY:
        return True
    return any(_term_uses_enum(a) for a in term["args"])


def _pred_uses_enum(pred) -> bool:
    op = pred["op"]
    if op in _CONNECTIVES:
        return any(_pred_uses_enum(a) for a in pred["args"])
    if op in _ENUM_ONLY:                    # coprime
        return True
    return any(_term_uses_enum(a) for a in pred["args"])


def smt_representable(reading: MathReading) -> bool:
    """False when any hypothesis uses an enum_only operator (gcd/coprime),
    which has no sound SMT rendering -- that reading routes to the decidable-
    enumeration channel instead (F2.1)."""
    return not any(_pred_uses_enum(s["lf"]["pred"])
                   for s in reading.by_kind("hypothesis"))


# --------------------------------------------------------- logic selection
def _has_ref(term, bound=frozenset()) -> bool:
    """True when the term depends on any object (is non-constant).  A
    big-operator's bound index is a CONSTANT here: after unrolling, every
    occurrence is a numeral, so only free (declared-object) refs count."""
    if "ref" in term:
        return term["ref"] not in bound
    if "lit" in term or "var" in term:
        return False
    if term.get("op") in _BIGOPS:
        var = term["args"][0]["var"]
        return any(_has_ref(a, bound | {var}) for a in term["args"][1:])
    if term.get("op") == "card":                # P2: the count depends on a free
        setnode = term["args"][0]               # object iff the filter does
        var = setnode["args"][0]["var"]
        return _pred_has_ref(setnode["args"][3], bound | {var})
    return any(_has_ref(a, bound) for a in term["args"])


def _pred_has_ref(pred, bound=frozenset()) -> bool:
    """True when a pred depends on any FREE object (the bound-aware sibling of
    _has_ref for a card filter)."""
    if pred["op"] in _CONNECTIVES:
        return any(_pred_has_ref(a, bound) for a in pred["args"])
    return any(_has_ref(a, bound) for a in pred["args"])


def _term_nonlinear(term, bound=frozenset()) -> bool:
    if "ref" in term or "lit" in term or "var" in term:
        return False
    op, args = term["op"], term["args"]
    if op in _BIGOPS:
        # The unrolled form is a +/* over body copies with a CONCRETE index.
        # bigsum: nonlinear iff the body is (the sum of linear pieces is
        # linear).  bigprod: like ^ (D10) -- a product of >= 2 object-
        # dependent factors is nonlinear, else it inherits from the body.
        var = args[0]["var"]
        lo, hi = args[1]["lit"], args[2]["lit"]
        body = args[3]
        inner = bound | {var}
        if op == "bigprod" and (hi - lo + 1) >= 2 and _has_ref(body, inner):
            return True
        return _term_nonlinear(body, inner)
    if op == "card":
        # The unrolled form is a sum of (ite filter 1 0) with a CONCRETE index.
        # ite over the constant branches 1/0 stays linear; only a nonlinear
        # FILTER condition (a mod/dvd by an object, or a product of objects)
        # pushes the obligation to QF_NIA.
        setnode = args[0]
        var = setnode["args"][0]["var"]
        return _pred_nonlinear(setnode["args"][3], bound | {var})
    if op == "*":
        # nonlinear once two operands vary (constant * variable stays linear)
        if sum(1 for a in args if _has_ref(a, bound)) >= 2:
            return True
        return any(_term_nonlinear(a, bound) for a in args)
    if op in ("%", "mod"):
        # mod by a non-constant divisor is nonlinear (CVC5 rejects it in QF_LIA)
        return _has_ref(args[1], bound) or \
            any(_term_nonlinear(a, bound) for a in args)
    if op == "^":
        if args[1]["lit"] >= 2 and _has_ref(args[0], bound):
            return True
        return _term_nonlinear(args[0], bound)
    # + or - : linear in their operands
    return any(_term_nonlinear(a, bound) for a in args)


def _pred_nonlinear(pred, bound=frozenset()) -> bool:
    op = pred["op"]
    if op in _CONNECTIVES:
        return any(_pred_nonlinear(a, bound) for a in pred["args"])
    if op == "dvd":                          # unfolds to (mod b a): divisor a
        return _has_ref(pred["args"][0], bound) or \
            any(_term_nonlinear(a, bound) for a in pred["args"])
    if op in ("even", "odd"):                # (mod n 2): constant divisor
        return _term_nonlinear(pred["args"][0], bound)
    return any(_term_nonlinear(a, bound) for a in pred["args"])


def _logic(reading: MathReading) -> str:
    if any(_pred_nonlinear(s["lf"]["pred"])
           for s in reading.by_kind("hypothesis")):
        return "QF_NIA"
    return "QF_LIA"


# ------------------------------------------------------------- entry point
def hypotheses_smt(reading: MathReading) -> str | None:
    """Render the hypothesis set to a complete SMT-LIB obligation, or None when
    the reading is not SMT-representable (gcd/coprime -> enumeration channel).

    Expected verdict: ``sat`` (a world satisfying every side condition exists).
    ``unsat`` means the hypotheses contradict each other -- but see the T4 note:
    only Lean-corroborated unsat refuses at stage ``nonvacuity``.  A nonlinear
    (``QF_NIA``) obligation may settle to ``unknown`` (D10); that is the
    enumeration-fallback signal, not a refusal.

    Deterministic: objects are declared in sorted name order, hypotheses in
    statement order, so the same reading yields byte-identical output."""
    if not smt_representable(reading):
        return None
    objects = reading.objects()
    carrier = reading.ambient_carrier()
    lines = [f"(set-logic {_logic(reading)})"]
    for name in sorted(objects):
        lines.append(f"(declare-const {name} Int)")
        if objects[name] == "Nat":
            lines.append(f"(assert (>= {name} 0))")
    for s in reading.by_kind("hypothesis"):
        lines.append(f"(assert {render_pred(s['lf']['pred'], objects, carrier)})")
    lines.append("(check-sat)")
    return "\n".join(lines) + "\n"
