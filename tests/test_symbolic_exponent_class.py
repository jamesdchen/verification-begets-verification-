"""SYMBOLIC EXPONENTS over the CURRENT fragment semantics: is `^` at a
non-literal exponent additive, the way `not` turned out to be?

THE QUESTION THIS FILE ANSWERS MECHANICALLY.  The `refusal-symbolic-exponent`
row of `results/purchase_frontier.json` (PLAN_FRAGMENT §4's successor to P1,
twelve refused subjects) is DECLARED `iteration-class` -- "the bound IS the
exponent, so nothing bounded-by-a-literal reaches it".  A declaration is not a
measurement, and the ledger has one worked precedent for a declaration that did
not survive contact: P6 was declared tower-class on the assumption that `not`
needs a `Pd` constructor, and `tests/test_nnf_duals.py` measured it down to
additive-desugaring, which is what let an unattended session ship it.  §3.1
rule 3 makes the class a GATE on who may buy the row, so the class had better
be a fact about the slice rather than a habit of the queue.  This file settles
it the same way P6's was settled -- against the fragment's own walkers -- and
it settles it the OTHER way.  A refutation is a result: the row's declaration
survives, and it now rests on a sweep instead of on a sentence.

WHAT COUNTS AS A PROOF HERE (and why it is not a second opinion).  Every
semantic claim below is asserted against `generators/math_eval.eval_pred` and
`generators/math_eval.eval_term` -- the fragment's OWN evaluator -- and never
against a re-implementation.  In particular the meaning of a power is never
recomputed in Python: the reference for `x ** n` at a concrete `n = k` is the
fragment's own LITERAL-exponent term `^(x, k)` put through the same evaluator.
So the headline identity is

    eval_pred(ladder_K(P), x)  ==  eval_pred(P_at_k, x)   at every x with x[n] = k

which is INSTANTIATION taken in Python on the evaluator's own answers, exactly
as P6 took NEGATION in Python on the evaluator's own answers.  Exhaustive over
the box, deterministic, solver-free, Lean-free, network-free.  The blocking
lines quoted in the prose are re-read from the live sources by
`test_the_quoted_blocking_lines_are_still_in_their_sources`, so a quote cannot
drift away from the code it indicts.

WHAT BREAKS, LAYER BY LAYER.  The literal is not one gate check with four
tolerant consumers behind it -- it is a precondition every downstream walker
reads DIRECTLY, by subscript:

  * gate, `generators/math_reading.py:577-579` -- "^ requires a non-negative
    LITERAL exponent (SMT-LIB has no exponentiation; a variable exponent is
    not in the fragment)".  Note the class of the raise, measured below and
    reported rather than tidied: it is a bare `BadMathReading`, NOT a
    `FragmentMiss`, so a symbolic exponent carries no `missing_kind_guess` and
    is filed as a MALFORMED READING rather than as demand.  Its sibling one
    node over -- `bigop:symbolic-bound`, the same shape of refusal at the same
    kind of position -- IS demand data.  That asymmetry is a real finding: the
    twelve subjects on the ledger were measured by the driver, not harvested by
    the fragment-miss machinery, which is why no amount of corpus intake would
    have raised this row's price on its own.
  * eval, `generators/math_eval.py:295-297` -- `return base ** args[1]["lit"]`
  * SMT, `generators/math_smt.py:298-305` -- `k = args[1]["lit"]`, then the
    k-fold `(* base ... base)` unfold (D10: SMT-LIB has no exponentiation)
  * SMT logic selection, `generators/math_smt.py:479-481` --
    `if args[1]["lit"] >= 2 and _has_ref(args[0], bound)`, the QF_NIA push
  * compile, `generators/math_compile.py:233-234` --
    `f"({_render_term(args[0], ctx)} ^ {args[1]['lit']})"`

All four downstream sites fail with the SAME `KeyError('lit')` on a `{"ref": n}`
exponent, which is asserted below.  That is the honest shape of the dependency:
the literal is load-bearing five times over, not once.

THE BOUNDED SUB-CASE, MEASURED AND FOUND REAL -- AND EMPTY.  There IS an
additive encoding, and it needs no purchase at all.  If the exponent object
carries a LITERAL upper bound `K`, then

    forall n <= K, P(x ^ n)      is      and_{k=0..K} ( n = k  ->  P(x ^ k) )

and every `^` on the right has a literal exponent, so the whole ladder is the
EXISTING grammar, verbatim: the gate admits it, the SMT mirror renders it, the
compiler emits it, and -- this is the discriminator -- the reflect slice already
covers it twice over.  Each arm is exactly the guard shape `sall_guard_iff` /
`compile_guard_shape` were proven for (`Pd.pimp (Pd.peq (Tm.tvar k) (Tm.lit c))
q`), and each arm's power is `powTm base k` at a CONCRETE width, which is what
`powTm` already is.  So the bounded sub-case is additive-desugaring and it is
already bought.

And it returns NOTHING.  The twelve subjects are resolved from the ledger to
their corpus prose by hash below, and NOT ONE of them bounds its exponent: ten
say "for all natural numbers n" or "for any integer n", one says "for all
sufficiently large n" (a threshold, i.e. the opposite of an upper bound), and
one is Fermat's little theorem at exponent `p - 1` for an arbitrary prime `p`.
A ladder is a finite conjunction; it is VACUOUS above its top rung, which
`test_the_ladder_proves_strictly_less_than_the_unbounded_subject` demonstrates
with a claim that is true on the whole box and FALSE just past it.  So the
bounded sub-case cannot be sold as a partial refill of this row: the honest
count is 0 of 12.

THE REFLECT ANSWER, from `tools/FgReflect.lean`'s actual text.  `powTm` is

    def powTm (a : Tm) : Nat -> Tm

-- a META-LEVEL recursion on a Lean `Nat`, producing a `Tm`.  Its exponent is
not a `Tm` and cannot be one: `Tm`'s constructors are `lit tvar add sub mul
tmod` and there is no `pow` among them (derived from the inductive block
below, not typed).  A symbolic exponent is a `Tm.tvar`, whose value depends on
`env`, so `powTm a (evalTm env e)` is not a `Tm` at all -- it is an
env-indexed FAMILY of them, and a `Stmt` is one syntax tree, not a family.
Reaching it needs `Tm.pow : Tm -> Tm -> Tm`, and that is the tower: a new
`evalTm` case, a new `evalTmN` case, a new `substTm` case, a new
`substTm_evalTm` case, a new `check`/`decDenote` case -- every certified walker
over the type answering the new constructor, which is §3.1 rule 3(a) verbatim.
The one escape a box normally offers is shut here by construction and the file
says so: `denoteStmt_of_box` / `denoteStmtN_of_box` lift a box-relativized
statement back to the unrelativized one ONLY under `exOnly s = true`, and meet
a universal with `| Stmt.sall _ _, _, hex, _ => nomatch hex`.  Every one of the
twelve subjects is universal in its exponent.  So the box cannot discharge them
even in principle, and the missing ingredient is an INDUCTION principle the
reflect slice does not have -- which is precisely what "iteration-class" names.

THE VERDICT, stated so it can be refuted rather than admired: the row is
GENUINELY ITERATION-CLASS.  The additive sub-case exists, is already bought,
and refills zero subjects.  If a later cycle intakes a corpus whose subjects DO
bound their exponents, `test_no_ledger_subject_falls_in_the_bounded_subcase`
reds and the ladder below is the encoding waiting for them.
"""
import hashlib
import itertools
import json
import os
import pathlib
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators import math_compile as MC  # noqa: E402
from generators import math_eval as ME  # noqa: E402
from generators import math_reading as MR  # noqa: E402
from generators import math_smt as MS  # noqa: E402

_ROOT = pathlib.Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------- #
# AST helpers, same spelling as tests/test_nnf_duals.py so the two measurements
# read as one idiom rather than two dialects.
# --------------------------------------------------------------------------- #
def _lit(k):
    return {"lit": k}


def _ref(n):
    return {"ref": n}


def _t(op, *args):
    return {"op": op, "args": list(args)}


N = _ref("n")
X = _ref("x")


# --------------------------------------------------------------------------- #
# THE ENCODING, written ONCE, as a rewrite on the pred AST.
#
# This IS the quote-time encoding a BOUNDED symbolic exponent would ship: the
# exponent never becomes a node, the universal is split by its literal bound
# into one guarded arm per admissible width, and each arm's `^` takes the
# literal the fragment has always required.  A bound that is not a literal
# raises rather than guessing -- fail-CLOSED, the shape §3.1 rule 3(e) asks of
# a carrier check, and the same discipline an exponent deserves.
# --------------------------------------------------------------------------- #
class UnboundedExponent(Exception):
    """An exponent the ladder cannot reach: no literal upper bound, so there is
    no finite set of widths to unroll to.  A NAMED refusal, never a widening
    and never a silent truncation -- truncating here would be the exact
    dishonesty of proving a box and reporting a theorem."""


def instantiate(pred: dict, var: str, k: int) -> dict:
    """`pred` with every `{"ref": var}` in EXPONENT position replaced by the
    literal `k`.  This is the whole of the encoding's term half: a symbolic
    exponent at a known width is a literal exponent, which the fragment has
    carried since D10.

    Only the exponent moves.  The object keeps its identity everywhere else in
    the pred (`n + 1`, `n ^ 3`, `n` under a comparison), because the guard
    `n = k` is what ties the two together -- substituting everywhere would be a
    different, stronger rewrite whose correctness this file has not measured."""
    def term(t):
        if "ref" in t or "lit" in t:
            return t
        args = t["args"]
        if t["op"] == "^":
            base, exp = args
            if exp == {"ref": var}:
                return _t("^", term(base), _lit(k))
            if "lit" in exp:
                return _t("^", term(base), exp)
            raise UnboundedExponent(
                f"exponent {exp!r} is neither `{var}` nor a literal")
        return {"op": t["op"], "args": [term(a) for a in args]}

    def walk(p):
        if p["op"] in MR._CONNECTIVES:
            return {"op": p["op"], "args": [walk(a) for a in p["args"]]}
        return {"op": p["op"], "args": [term(a) for a in p["args"]]}

    return walk(pred)


def ladder(pred: dict, var: str, bound) -> dict:
    """`forall var <= bound, pred` as a finite guarded conjunction over the
    EXISTING grammar: `and_{k=0..bound} (var = k -> pred[var := k])`.

    `bound` must be a non-negative int -- the literal the whole construction
    rests on.  Anything else is `UnboundedExponent`, which is the entire
    finding of this file said in one raise: without a literal top rung there is
    no ladder, and the twelve ledger subjects have none."""
    if not isinstance(bound, int) or isinstance(bound, bool) or bound < 0:
        raise UnboundedExponent(f"bound {bound!r} is not a non-negative literal")
    return _t("and", *[_t("implies", _t("=", _ref(var), _lit(k)),
                          instantiate(pred, var, k))
                       for k in range(bound + 1)])


# --------------------------------------------------------------------------- #
# The blocking sites, each quoted from the source it indicts.  Re-read live
# below, so the prose above cannot outlive the code.
# --------------------------------------------------------------------------- #
BLOCKING_LINES = {
    "gate": ("generators/math_reading.py",
             '"^ requires a LITERAL exponent: SMT-LIB has no exponentiation, "'),
    "eval": ("generators/math_eval.py",
             'return base ** args[1]["lit"]'),
    "smt-unfold": ("generators/math_smt.py",
                   'k = args[1]["lit"]                 '
                   '# validated non-negative literal (D10)'),
    "smt-logic": ("generators/math_smt.py",
                  'if args[1]["lit"] >= 2 and _has_ref(args[0], bound):'),
    "compile": ("generators/math_compile.py",
                'return f"({_render_term(args[0], ctx)} ^ '
                '{args[1][\'lit\']})"'),
    "reflect": ("tools/FgReflect.lean",
                "def powTm (a : Tm) : Nat -> Tm"),
    "reflect-box-refuses-forall": ("tools/FgReflect.lean",
                                   "| Stmt.sall _ _, _, hex, _ => nomatch hex"),
    "reflect-guard-shape": ("tools/FgReflect.lean",
                            "theorem sall_guard_iff (env : Nat -> Int) "
                            "(k : Nat) (c : Int) (q : Pd) :"),
}


# --------------------------------------------------------------------------- #
# THE TWELVE.  The subject SET is derived from the refusal ledger and the
# subject TEXTS are derived from the corpus by hash; only the reading of what
# each one needs is written down here, which is the one part a machine cannot
# supply.  Deriving the other two is what keeps the reading honest: a
# classification that drifted off its text, or off the ledger, reds.
#
# `exponent`: what sits in the exponent slot.
#   var      -- the quantified object itself (`2^n`)
#   compound -- a term over it (`2^(n+2)`, `a^(p-1)`)
#   iterate  -- not arithmetic at all: iteration of a MAP (`L_y^n x`), which is
#               a function-power and would not be `Tm`-shaped even with a
#               `Tm.pow` constructor in hand
# `upper_bound`: the literal ceiling the ladder would need.  `None` everywhere,
#   which IS the finding.
# --------------------------------------------------------------------------- #
SUBJECTS = {
    "fdded7108f04ec4c86595ddaa5ea714624f58a600e0f3fc73fbb9c673855e048": dict(
        label="06_Induction#problem-001", exponent="var", upper_bound=None,
        why="`2^n >= n+1` for every natural n -- an unbounded universal; the "
            "companion `n+1` is already in the fragment, only the power is not"),
    "7e5d574265502b923776260dc663924b81863ddd2d1bc88b2b94a9330d13ff45": dict(
        label="06_Induction#problem-002", exponent="var", upper_bound=None,
        why="`4^n mod 15 in {1,4}` for every natural n -- unbounded; the "
            "residue cycles with period 2, which is an INDUCTION on n and not "
            "a width the ladder could enumerate"),
    "654f73c75b955534ec08a6bd51913f20492211085751a123f68fc359ba98ac0b": dict(
        label="06_Induction#problem-003", exponent="var", upper_bound=None,
        why="`3^n >= 2^n + 5` for n >= 2 -- a LOWER bound on the exponent, "
            "which is the wrong end: a ladder needs a ceiling, and a floor "
            "leaves infinitely many rungs above it"),
    "aed8b65802608143a6801c0c991114b58c26db3fc6ff7012e1d70b46afa0d4a2": dict(
        label="06_Induction#problem-004", exponent="var", upper_bound=None,
        why="`2^n >= n^2` for all SUFFICIENTLY LARGE n -- a threshold, i.e. the "
            "exact opposite of an upper bound; note `n^2` is already fragment-"
            "legal, so the two exponents in one statement land on opposite "
            "sides of D10"),
    "b2f1be6a486601630ab969465ea3f90f8ab688c7e7a9bbddecf4358f04c64b4e": dict(
        label="06_Induction#problem-007", exponent="compound", upper_bound=None,
        why="`x_n = 2^(n+2) + 1` -- unbounded, and the exponent is a TERM over "
            "n rather than n itself, so even a bounded reading would have to "
            "unroll the term's range and not the object's"),
    "8565a125ea6653ed8d9f643353bbb4775084a225dc7851b9e8aa94afc5733193": dict(
        label="06_Induction#problem-010", exponent="var", upper_bound=None,
        why="`(n+1)! >= 2^n` -- unbounded; the factorial is the co-filed "
            "function-symbol demand and the power is this row's"),
    "c0325201ab759e7c6ce89c9f1500812d12f1f06c499decf6e32118e5d7bc6818": dict(
        label="06_Induction#problem-011", exponent="var", upper_bound=None,
        why="`a_n = 2^n + (-1)^n` -- unbounded, and TWO symbolic exponents in "
            "one statement, one over a negative literal base"),
    "e0f1639a5237bef36d56b18a9ba79bbddf7080b9e45c28a0ce8c3b3ccc29497f": dict(
        label="06_Induction#problem-015", exponent="var", upper_bound=None,
        why="`d_n >= 4^n` for all sufficiently large n -- unbounded on both "
            "the sequence and the power"),
    "223bd5d953ff95c8fe54fb39084b0bfc4fadbe18470b9692744d98978e1029c0": dict(
        label="06_Induction#problem-016", exponent="var", upper_bound=None,
        why="`F_n <= 2^n` -- unbounded; the Fibonacci sequence is the co-filed "
            "function-symbol demand"),
    "aa15fa3366639cf78e81b69d8d5409ebab1c71a119669507fb257b801515307a": dict(
        label="06_Induction#theorem-002", exponent="var", upper_bound=None,
        why="`a = b mod d  ->  a^n = b^n mod d` for every natural n -- "
            "unbounded, and the exponent is symbolic on BOTH sides over "
            "SYMBOLIC bases, so no rung of any ladder is a numeral"),
    "c7af97f799452cb065721d1cad81bb98ebfa52bef2cd94f52fb5f3480448d7db": dict(
        label="edge-disjoint", exponent="iterate", upper_bound=None,
        why="`L_y x = L_z x -> L_y^n x = L_z^n x` for any integer n -- the "
            "power is ITERATION OF A MAP, not arithmetic; it is out of the "
            "term algebra entirely and would survive a `Tm.pow` unchanged"),
    "8e94bcaa953f912ed12538b64778d3abef769925c5f0dc8e858ae59779063018": dict(
        label="fermats_little", exponent="compound", upper_bound=None,
        why="`a^(p-1) = 1 mod p` -- the exponent is a term over an arbitrary "
            "prime, so the ceiling would have to be a bound on the primes "
            "themselves"),
}


def _ledger_shas():
    """The subject set, DERIVED from the refusal ledger rather than typed: if a
    later cycle files a thirteenth symbolic-exponent refusal, the coverage
    tooth below reds instead of this file quietly measuring twelve."""
    path = _ROOT / "results" / "frontier_refusals.jsonl"
    out = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row["signal"] == "symbolic-exponent":
            out.append(row["subject_sha256"])
    return out


def _corpus_texts():
    """sha256 -> (corpus, label, prose) over every committed corpus node.  The
    hash is the join key the frontier itself uses, so a subject resolved here
    is the same subject the ledger refused."""
    index = {}
    for path in sorted((_ROOT / "specs" / "mathsources").glob("*/nodes.jsonl")):
        corpus = path.parent.name
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            node = json.loads(line)
            prose = node.get("prose", "")
            index[hashlib.sha256(prose.encode()).hexdigest()] = (
                corpus, node.get("label"), prose)
    return index


def _co_filed_signals():
    """sha256 -> the OTHER refusal signals the same subject carries, derived
    from `results/frontier.json`.  A row that refills nothing alone must say so
    with a number, and this is where the number comes from."""
    frontier = json.loads((_ROOT / "results" / "frontier.json").read_text())
    out = {}
    for group in frontier["blocked"] + frontier["ready"]:
        signal = group.get("signal")
        for node in group.get("nodes", []):
            out.setdefault(node["text_sha256"], set()).add(signal)
    return out


# --------------------------------------------------------------------------- #
# The boxes.  Nat is the carrier the exponent lives on (D10 requires a
# NON-NEGATIVE exponent, and a Nat object is the only one whose whole range is
# admissible); Int rides along for the BASE, where a negative base makes the
# parity of the width observable and an "unroll" that lost a factor would show.
# --------------------------------------------------------------------------- #
BOXES = {
    "Nat": ({"n": "Nat", "x": "Nat"}, {"n": range(0, 7), "x": range(0, 7)}),
    "Int": ({"n": "Nat", "x": "Int"}, {"n": range(0, 7), "x": range(-4, 5)}),
}

#: Conclusion shapes over `x ^ n`, chosen so the exponent appears in every
#: position a subject actually puts it in: alone, under an arithmetic op, on
#: both sides of an atom, beside a LITERAL-exponent power (problem-004's shape,
#: where D10 admits one power and refuses the other), under a connective, and
#: over a negative literal base (problem-011's `(-1)^n`).
SHAPES = {
    "bare": _t("<=", N, _t("^", X, N)),
    "sum": _t("<=", _t("+", N, _lit(1)), _t("^", _lit(2), N)),
    "both-sides": _t("<=", _t("^", X, N), _t("^", _t("+", X, _lit(1)), N)),
    "mixed-D10": _t("<=", _t("^", N, _lit(2)), _t("^", _lit(2), N)),
    "product": _t("=", _t("*", _t("^", X, N), X), _t("^", X, N)),
    "modular": _t("=", _t("%", _t("^", _lit(4), N), _lit(15)), _lit(1)),
    "connective": _t("or", _t("=", _t("%", _t("^", _lit(4), N), _lit(15)),
                              _lit(1)),
                     _t("=", _t("%", _t("^", _lit(4), N), _lit(15)), _lit(4))),
    "negative-base": _t("<=", _t("^", _lit(-1), N), _lit(1)),
    "even-atom": _t("even", _t("^", X, N)),
}

_LADDER_BOUND = 6


def _points(values):
    """Every assignment over the box, in a fixed order (sorted names, product
    in the declared value order): deterministic by construction."""
    names = sorted(values)
    for combo in itertools.product(*(values[n] for n in names)):
        yield dict(zip(names, combo))


# ------------------------------------------------------- what actually breaks
def test_the_gate_admits_a_symbolic_exponent_only_at_carrier_Nat():
    """P7 PAID -- and this tooth is the inversion the pre-purchase version
    advertised.  It used to assert that `_check_term` refuses every non-literal
    exponent.  It now asserts the rule that REPLACED that one, and the
    replacement is narrower rather than merely weaker, which is the whole
    content of the purchase:

      * `_check_term` is carrier-BLIND, so it admits a well-formed symbolic
        exponent and decides nothing.  (Structure here, carrier there -- the
        one-rule-in-one-place discipline; two copies could disagree.)
      * `_check_carrier_ops` admits it at carrier `Nat` and REFUSES it
        anywhere else, because only at `Nat` is non-negativity a property of
        the type instead of a side condition.  That is what keeps the power
        `Monoid.npow` and keeps the reflect slice's `Int.toNat` totalisation
        unreachable from any admitted reading.
      * a MALFORMED exponent is still a `BadMathReading`, unchanged.  The
        purchase bought expressiveness, not tolerance."""
    # (1) the carrier-blind structural check now ADMITS the well-formed shapes
    for exponent in (N, _t("+", N, _lit(2)), _t("-", N, _lit(1)),
                     _t("*", N, N)):
        MR._check_term(_t("^", _lit(2), exponent), {"n": "Nat"})
    # ...and still refuses the two that are not well-formed exponents at all
    for exponent in (_lit(-1), {"lit": True}):
        with pytest.raises(MR.BadMathReading):
            MR._check_term(_t("^", _lit(2), exponent), {"n": "Nat"})

    # (2) the CARRIER walk is where admissibility is decided.  At Nat: fine.
    MR._check_carrier_ops(_t("=", _t("^", _lit(2), N), N), {"n": "Nat"},
                          None, "c1")
    # At Int: a FragmentMiss naming the carrier -- demand, not a broken reading.
    with pytest.raises(MR.FragmentMiss) as exc:
        MR._check_carrier_ops(_t("=", _t("^", _lit(2), N), N), {"n": "Int"},
                              None, "c1")
    assert exc.value.missing_kind_guess == "pow:symbolic-exponent@Int"
    # (3) the literal side of the rule is byte-unchanged, so nothing above is
    # the probe's doing
    MR._check_term(_t("^", _lit(2), _lit(0)), {"n": "Nat"})
    MR._check_term(_t("^", N, _lit(3)), {"n": "Nat"})


def test_a_symbolic_exponent_is_filed_as_demand_the_asymmetry_is_closed():
    """THE ASYMMETRY THIS FINDING REPORTED, AND ITS LATER REPAIR.

    As measured, `bigop`'s symbolic BOUND was a `FragmentMiss` carrying
    `bigop:symbolic-bound` -- first-class demand the fragment-miss machinery
    can price -- while `^`'s symbolic EXPONENT was a bare `BadMathReading`
    with no `missing_kind_guess`, so it never entered demand data at all.
    The twelve subjects on the ledger got there by DRIVER measurement, not by
    intake, and corpus growth alone could never have raised this row's price.

    That was a fact about the PLUMBING, not the mathematics, which is why the
    finding put it beside the class verdict rather than inside it -- and why
    fixing it changes nothing about the verdict.  It has since been fixed:
    the exponent branch now raises `FragmentMiss` for a well-formed exponent
    the fragment cannot express, and keeps `BadMathReading` for a malformed
    one (tests/test_symbolic_exponent_demand.py owns that split in both
    directions).  This test now pins the REPAIR, so the asymmetry cannot
    silently return.

    THE CLASS VERDICT IS UNTOUCHED.  Demand reaching the histogram makes the
    row PRICEABLE; it does not make it takeable.  `refusal-symbolic-exponent`
    is still iteration-class, still needs `Tm.pow` and an induction principle
    the slice lacks, and is still not something an unattended session may
    take."""
    # P7 moved WHERE this fires and NARROWED what it says -- both on purpose.
    # Pre-purchase the guess was the bare `pow:symbolic-exponent`, meaning "the
    # fragment cannot express a symbolic exponent at all".  It can now, at Nat,
    # so the honest residual demand is the carrier-suffixed one: an exponent
    # that may be NEGATIVE is still outside the integer carriers.  Same idiom
    # P3 used for its own residue (`operator:/@{carrier}`).
    with pytest.raises(MR.FragmentMiss) as exc:
        MR._check_carrier_ops(_t("=", _t("^", _lit(2), N), N), {"n": "Int"},
                              None, "c1")
    assert exc.value.missing_kind_guess == "pow:symbolic-exponent@Int", (
        "the symbolic exponent no longer carries its demand guess -- the "
        "asymmetry this finding reported has returned")

    # the sibling that was ALREADY demand, unchanged: the two are now peers
    with pytest.raises(MR.FragmentMiss) as sibling:
        MR._check_term(
            _t("bigsum", {"var": "i"}, _lit(0), N, _ref("i")), {"n": "Nat"})
    assert sibling.value.missing_kind_guess == "bigop:symbolic-bound"

    # and a MALFORMED exponent is still not demand -- closing the seam must
    # not have opened the opposite one (a transcription bug priced as demand)
    with pytest.raises(MR.BadMathReading) as bad:
        MR._check_term(_t("^", _lit(2), {"lit": True}), {"n": "Nat"})
    assert not isinstance(bad.value, MR.FragmentMiss)

def test_no_downstream_layer_reads_the_literal_by_subscript_any_more():
    """THE FOUR SITES THIS ROW WAS PRICED ON, PAID -- and this is the tooth
    that proves the bill reached all of them rather than just the gate.

    Pre-purchase, all four consumers reached for `args[1]["lit"]` directly and
    all four died the same `KeyError('lit')`.  That fourfold dependency WAS the
    row's price.  Post-purchase each answers a symbolic exponent in its own
    honest way, and the differences between them are the interesting part:

      * eval COMPUTES it (the carrier makes the exponent non-negative);
      * the compiler RENDERS it (`Monoid.npow` needs no coercion at Nat);
      * the SMT logic classifier ANSWERS it (nonlinear -- total, not lucky);
      * the SMT renderer REFUSES it, by name and on purpose.  SMT-LIB has no
        exponentiation and a k-fold unroll needs a k, so there is nothing to
        render; the reading routes to enumeration instead (see the sibling
        below).  A ValueError naming the reason beats a `KeyError('lit')`
        that merely happened to stop."""
    sym = _t("^", _lit(2), N)
    ctx = MC._Ctx(ambient=None, objects={"n": "Nat"})
    # eval: real exponentiation at the assignment's width
    assert ME.eval_term(sym, {"n": 3}, {"n": "Nat"}, None) == 8
    # compile: the exponent is emitted as a TERM, not as a numeral
    assert MC._render_term(sym, ctx) == "(2 ^ n)"
    # smt-logic: total, and honest about what it is
    assert MS._term_nonlinear(sym) is True
    # smt-render: refuses, and says why
    with pytest.raises(ValueError) as exc:
        MS.render_term(sym, {"n": "Nat"}, "Nat")
    assert "no SMT rendering" in str(exc.value)
    assert "no exponentiation" in str(exc.value)
    # and NONE of the four raises KeyError('lit') any more -- the subscript
    # dependency the row was priced on is gone from every one of them
    for probe in (lambda: ME.eval_term(sym, {"n": 3}, {"n": "Nat"}, None),
                  lambda: MC._render_term(sym, ctx),
                  lambda: MS._term_nonlinear(sym)):
        probe()                             # no raise at all


def test_a_symbolic_exponent_routes_the_reading_to_enumeration():
    """The SMT bill item, paid as a REFUSAL rather than as a rendering -- and
    the reason that is payment and not a gap.

    `smt_representable` was a predicate on operator WORDS (`gcd`, `coprime`):
    the head alone decided, because those have no sound rendering at any
    argument.  `^` is not like that -- at a literal exponent it unrolls to a
    k-fold product, and only the SYMBOLIC exponent has no rendering.  So the
    predicate had to start looking at the NODE, which is the first shape-keyed
    enum-only route in the file.

    Routing to enumeration is not a downgrade: enumeration is exhaustive over
    the box, which is a stronger claim about that box than a solver's `sat`.
    What it is not is a proof of the unbounded universal -- results/p7_delta.md
    carries that limit as its headline."""
    assert MS._term_uses_enum(_t("^", _lit(2), N)) is True
    assert MS._pred_uses_enum(_t("=", _t("^", _lit(2), N), N)) is True
    # ...and the LITERAL exponent is untouched: it still has an SMT rendering,
    # so the new route is keyed to the shape and not to the operator
    assert MS._term_uses_enum(_t("^", _lit(2), _lit(3))) is False
    assert MS.render_term(_t("^", _ref("a"), _lit(3)),
                          {"a": "Int"}, "Int") == "(* a a a)"


def test_the_python_side_blocks_are_EXECUTED_not_quoted():
    """WHY THIS REPLACED A STRING MATCH.  This tooth used to assert that
    quoted source LINES were still present.  That is prose-pinning wearing a
    test's clothes: it broke when the exponent refusal was reworded, even
    though every claim the finding makes remained true, and it would equally
    have PASSED on a line that was still present but no longer reached.

    So the Python-side claims are now RUN.  Each one drives the real function
    and asserts the behaviour the finding rests on -- which is strictly
    stronger, because a line can exist and be dead, but a behaviour cannot."""
    # (1) the GATE: post-P7 a symbolic exponent is ADMITTED at Nat, and the
    #     residual Int case is still refused as DEMAND
    MR._check_carrier_ops(_t("=", _t("^", _lit(2), N), N), {"n": "Nat"},
                          None, "c1")
    with pytest.raises(MR.FragmentMiss) as exc:
        MR._check_carrier_ops(_t("=", _t("^", _lit(2), N), N), {"n": "Int"},
                              None, "c1")
    assert exc.value.missing_kind_guess == "pow:symbolic-exponent@Int"

    # (2) EVAL: a LITERAL exponent evaluates by real exponentiation
    from generators import math_eval as ME
    assert ME.eval_term(_t("^", _ref("a"), _lit(3)),
                        {"a": 2}, {"a": "Int"}, "Int") == 8

    # (3) SMT: the literal exponent UNROLLS -- there is no `^` in SMT-LIB, and
    #     that is the mechanism the row's whole class argument depends on
    from generators import math_smt as MS
    assert MS.render_term(_t("^", _ref("a"), _lit(3)),
                          {"a": "Int"}, "Int") == "(* a a a)"

    # (4) ...and the unroll is STILL only available because the width is known.
    #     P7 did not buy an unroll for the symbolic case -- it bought a term
    #     constructor and an enumeration route.  The SMT renderer refuses a
    #     symbolic exponent exactly as before; what changed is that it now says
    #     why instead of dying on a subscript.
    with pytest.raises(ValueError):
        MS.render_term(_t("^", _ref("a"), N), {"a": "Int", "n": "Nat"}, "Int")
    #     eval, by contrast, now answers it -- the asymmetry is the purchase
    assert ME.eval_term(_t("^", _ref("a"), N), {"a": 2, "n": 3},
                        {"a": "Int", "n": "Nat"}, None) == 8


def test_the_lean_side_blocks_are_still_quoted_because_lean_cannot_run_here():
    """The residue, named rather than pretended away.  The reflect-slice
    claims are about Lean DECLARATIONS, and elaborating them is CI-lane work
    by network policy -- so these stay text checks, and they are matched
    whitespace-tolerantly so a reformat is not mistaken for a retraction.
    A text check is weaker than an executed one; saying which is which is the
    point."""
    import re
    for site, (rel, needle) in BLOCKING_LINES.items():
        if not rel.endswith(".lean"):
            continue
        text = (_ROOT / rel).read_text()
        pattern = re.compile(r"\s+".join(re.escape(w) for w in needle.split()))
        assert pattern.search(text), (
            f"{site}: the quoted declaration has moved in {rel}")
def test_the_bounded_ladder_is_pointwise_the_instantiated_power():
    """THE ADDITIVE SUB-CASE, exhaustively.  Over every box and every
    conclusion shape, the guarded conjunction agrees with the fragment's OWN
    literal-exponent reading of the same statement at every point of the box.

    The reference side never recomputes a power in Python: `instantiate` builds
    the term the fragment has always admitted, and `eval_pred` answers both
    sides.  So this asserts that the ladder MEANS instantiation, which is the
    whole of the encoding, and it asserts it against the walker the gates
    actually run."""
    swept = 0
    for name, (carrier_of, values) in BOXES.items():
        for shape, pred in SHAPES.items():
            rungs = ladder(pred, "n", _LADDER_BOUND)
            for point in _points(values):
                k = point["n"]
                assert k <= _LADDER_BOUND, "the box outgrew the ladder"
                got = ME.eval_pred(rungs, point, carrier_of, None)
                want = ME.eval_pred(instantiate(pred, "n", k), point,
                                    carrier_of, None)
                assert got == want, (
                    f"{name}/{shape}: the ladder disagrees with instantiation "
                    f"at {point} (ladder says {got}, the width-{k} reading "
                    f"says {want})")
                swept += 1
    assert swept == sum(len(SHAPES) * len(list(_points(v)))
                        for _c, v in BOXES.values())
    assert swept > 800, f"the ladder sweep collapsed to {swept} points"


def test_the_ladder_rides_the_gate_the_smt_mirror_and_the_compiler_unchanged():
    """...and it is not merely semantically right, it is ADMISSIBLE: the same
    ladders the sweep above evaluates pass the gate, render to SMT-LIB and
    compile to Lean -- with nothing added anywhere.  This is the "no purchase
    needed" half of the sub-case finding; the symbolic form is checked beside
    it so the contrast is measured rather than asserted."""
    ctx = MC._Ctx(ambient=None, objects={"n": "Nat", "x": "Int"})
    for shape, pred in SHAPES.items():
        rungs = ladder(pred, "n", 4)
        MR._check_pred(rungs, {"n": "Nat", "x": "Int"})
        rendered = MS.render_pred(rungs, {"n": "Nat", "x": "Int"}, "Int")
        assert rendered.startswith("(and "), shape
        assert "^" not in rendered, f"{shape}: SMT-LIB has no exponentiation"
        emitted = MC._render_pred(rungs, ctx)
        assert emitted, shape
        # The symbolic original, for contrast -- and the contrast MOVED with
        # P7.  Pre-purchase `_check_pred` itself refused it.  Post-purchase the
        # grammar admits it (that is the purchase) and the refusal, where it
        # still applies, is the CARRIER walk's at Int.  The ladder's own
        # admissibility -- the "no purchase needed" finding -- is unchanged,
        # which is what this test is really for.
        MR._check_pred(pred, {"n": "Nat", "x": "Int"})
        with pytest.raises(MR.FragmentMiss):
            MR._check_carrier_ops(pred, {"n": "Int", "x": "Int"}, None, shape)


def test_the_ladder_emits_no_new_operator_and_no_symbolic_exponent():
    """The class question, stated as an assertion about the OUTPUT -- the
    `_NNF_OUTPUT_CONNECTIVES` move from the P6 measurement, transposed to
    terms.  Every op in a ladder is one the grammar already had, and EVERY `^`
    in it carries a non-negative integer literal.  So the bounded sub-case adds
    no `Tm` constructor, which is §3.1 rule 3(a)'s criterion read off the
    artifact rather than argued."""
    known_terms = set(MR._TERM_OPS)
    known_preds = set(MR._ATOM_OPS) | set(MR._CONNECTIVES)

    def term_ops(t):
        if "ref" in t or "lit" in t:
            return set()
        out = {t["op"]}
        if t["op"] == "^":
            exp = t["args"][1]
            assert set(exp) == {"lit"} and isinstance(exp["lit"], int) \
                and not isinstance(exp["lit"], bool) and exp["lit"] >= 0, \
                f"the ladder emitted a non-literal exponent: {exp!r}"
        for a in t["args"]:
            out |= term_ops(a)
        return out

    def pred_ops(p):
        out = {p["op"]}
        if p["op"] in MR._CONNECTIVES:
            for a in p["args"]:
                out |= pred_ops(a)
        else:
            for a in p["args"]:
                out |= term_ops(a)
        return out

    for shape, pred in SHAPES.items():
        emitted = pred_ops(ladder(pred, "n", _LADDER_BOUND))
        assert emitted <= known_preds | known_terms, shape


def test_the_ladder_refuses_an_unbounded_exponent_by_name():
    """Fail-CLOSED, and by name.  Without a literal ceiling the ladder raises
    rather than picking one -- picking one would be the silent widening §3.1
    rule 3(e) exists to forbid, and it is the precise dishonesty the next test
    shows the cost of."""
    for bound in (None, "6", _ref("n"), -1, True, 2.0):
        with pytest.raises(UnboundedExponent):
            ladder(SHAPES["sum"], "n", bound)
    # a symbolic exponent that is neither the object nor a literal is refused
    # inside the arm too, not silently copied through
    with pytest.raises(UnboundedExponent):
        instantiate(_t("<=", _lit(0), _t("^", X, _t("+", N, _lit(2)))), "n", 3)


# ---------------------------------------------------------- the refutation
def test_the_ladder_proves_strictly_less_than_the_unbounded_subject():
    """THE TOOTH THAT MAKES THE VERDICT HONEST, and the reason 0-of-12 is a
    finding rather than an omission.

    A ladder is a finite conjunction, so it is VACUOUSLY TRUE above its top
    rung.  `2^n <= n^3 + 1` is true at every natural n <= 9 and FALSE at
    n = 10, so the ladder at bound 9 is green over its whole box while the
    statement it was built from is false.  Anyone selling a bounded ladder as a
    partial answer to an unbounded subject would be shipping exactly this.  The
    evaluator answers both sides, so the gap is measured, not argued."""
    carrier_of = {"n": "Nat"}
    subject = _t("<=", _t("^", _lit(2), N),
                 _t("+", _t("^", N, _lit(3)), _lit(1)))
    rungs = ladder(subject, "n", 9)
    # green everywhere, including far past the top rung
    for k in range(0, 40):
        assert ME.eval_pred(rungs, {"n": k}, carrier_of, None) is True, \
            f"the ladder is not vacuous above its bound (n={k})"
    # ...while the statement it encodes is false, and the fragment's own
    # literal-exponent reading is what says so
    false_at = [k for k in range(0, 40)
                if not ME.eval_pred(instantiate(subject, "n", k), {"n": k},
                                    carrier_of, None)]
    assert false_at and min(false_at) == 10, false_at
    assert all(k > 9 for k in false_at), \
        "the counterexample is inside the box, so the tooth proves nothing"


def test_a_planted_ladder_error_is_caught_by_these_boxes():
    """THE PLANTED VIOLATION.  A sweep that proves the encoding green has to be
    shown capable of reddening: three plausible mis-statements of the ladder --
    the top rung dropped, the guard read as `<=` instead of `=` (which makes
    every arm at or above k fire at once), and the arms conjoined with `or`
    instead of `and` (which makes the whole thing vacuous, since an arm whose
    guard is false is already true) -- must each disagree with instantiation
    somewhere in the boxes, on some shape.  A tooth that cannot bite is
    decoration.

    "On SOME shape" is the honest quantifier, not a weakening.  A mis-stated
    ladder agrees with instantiation on any statement that happens to be TRUE
    at every width in the box, so a planted error is observable only against a
    shape the box can falsify -- which is why `SHAPES` carries statements that
    are false somewhere (`n <= x^n` at x = 0, `n^2 <= 2^n` at n = 3) as well as
    the true ones.  The catching shapes are collected rather than short-
    circuited, so a later edit that narrows `SHAPES` cannot quietly blind one
    of the three."""
    def _arms(pred):
        return [(_t("=", N, _lit(k)), instantiate(pred, "n", k))
                for k in range(_LADDER_BOUND + 1)]

    planted = {
        "top-rung-dropped":
            lambda a: _t("and", *[_t("implies", g, b) for g, b in a[:-1]]),
        "guard-widened":
            lambda a: _t("and", *[_t("implies", _t("<=", N, _lit(k)), b)
                                  for k, (_g, b) in enumerate(a)]),
        "arms-disjoined":
            lambda a: _t("or", *[_t("implies", g, b) for g, b in a]),
    }
    catchers = {}
    for label, build in planted.items():
        for box, (carrier_of, values) in BOXES.items():
            for shape, pred in SHAPES.items():
                wrong = build(_arms(pred))
                if any(ME.eval_pred(wrong, point, carrier_of, None)
                       != ME.eval_pred(instantiate(pred, "n", point["n"]),
                                       point, carrier_of, None)
                       for point in _points(values)):
                    catchers.setdefault(label, []).append(f"{box}/{shape}")
        assert label in catchers, \
            f"{label}: no box and no shape can see this error"


# ------------------------------------------------------- the reflect answer
def _fgreflect_tm_constructors():
    """The `Tm` constructor names, DERIVED from `tools/FgReflect.lean`'s
    inductive block rather than typed here.  A purchase that adds `Tm.pow`
    reds the assertions below, which is the point: the class claim must be
    falsifiable by the very edit that would change it."""
    text = (_ROOT / "tools" / "FgReflect.lean").read_text()
    start = text.index("inductive Tm where")
    body = text[start:].split("\n\n", 1)[0]
    return [line.strip().split()[1]
            for line in body.splitlines()[1:] if line.strip().startswith("| ")]


def test_the_reflect_slice_now_has_a_term_level_exponent_and_every_walker_answers_it():
    """THE TOWER, PAID -- the assertion the pre-purchase version said would be
    reddened by "the very edit that would change it".  This is that edit, and
    this is the tooth on the other side of it.

    Pre-purchase: `Tm` had six constructors and `powTm : Tm -> Nat -> Tm` was a
    META-level recursion, so a symbolic exponent was an env-indexed FAMILY of
    terms rather than one tree.  The class verdict named the price exactly --
    `Tm.pow` plus a new case in every certified walker over the type.

    Post-purchase every item on that list is present, and the list is checked
    ITEM BY ITEM rather than by trusting that the file elaborates: a walker can
    be total and still be wrong, but a MISSING case cannot be either, and Lean
    would have refused the file for it (which is the local-elaboration half of
    the receipt, results/p7_delta.md).

    `powTm` is deliberately KEPT.  A literal-width power still has a
    literal-width spelling, and deleting it would have re-verdicted every
    existing bigop reading to buy nothing -- the purchase is additive to the
    slice's vocabulary, not a replacement of it."""
    ctors = _fgreflect_tm_constructors()
    assert ctors == ["lit", "tvar", "add", "sub", "mul", "tmod", "pow"], ctors
    text = (_ROOT / "tools" / "FgReflect.lean").read_text()
    # the constructor, at the arity the class measurement named
    assert "| pow : Tm -> Tm -> Tm" in text
    # `powTm` survives at its META-level type: additive, not a replacement
    assert "def powTm (a : Tm) : Nat -> Tm" in text
    # every certified walker over `Tm` now has a `Tm.pow` case -- the five the
    # class verdict billed, named individually so a silent omission is visible
    for walker in ("def evalTm ", "def evalTmN ", "def substTm ",
                   "theorem evalTm_subst", "theorem evalTmN_subst"):
        assert walker in text, walker
    assert text.count("| Tm.pow ") >= 6, (
        "a Tm.pow case is missing from a walker -- evalTm, substTm, "
        "evalTm_subst, evalTmN, evalTmN_subst and emitTm each owe one")
    # the Int evaluator's totalisation is EXPLICIT rather than an `else` -- the
    # fail-OPEN hazard results/p3_delta.md measured, closed here by naming it
    assert "(evalTm env b).toNat" in text
    # ...and the Nat evaluator needs no totalisation at all, which is the
    # reason the gate insists a symbolic exponent be carrier-Nat
    assert "(evalTmN env a) ^ (evalTmN env b)" in text


def test_the_reflect_box_route_cannot_discharge_a_universal():
    """...and the one escape a box normally offers is shut by construction.
    `denoteStmt_of_box` / `denoteStmtN_of_box` lift a box-relativized statement
    back to the real one ONLY under `exOnly s = true`, meeting a universal with
    `nomatch hex`.  Every one of the twelve subjects is universal in its
    exponent, so "enumerate the widths the box admits" cannot reach them even
    in principle -- the missing ingredient is an INDUCTION principle the slice
    does not have, which is what `iteration-class` names."""
    text = (_ROOT / "tools" / "FgReflect.lean").read_text()
    assert text.count("| Stmt.sall _ _, _, hex, _ => nomatch hex") == 2, \
        "the box-lift lemmas no longer refuse universals the same way"
    for lemma in ("theorem denoteStmt_of_box", "theorem denoteStmtN_of_box"):
        assert lemma in text, lemma
    # the guard shape the BOUNDED ladder's arms would ride is already proven,
    # which is the other half of the answer: the sub-case needs no reflect work
    assert "theorem sall_guard_iff" in text
    assert "theorem compile_guard_shape" in text
    assert "Pd.pimp (Pd.peq (Tm.tvar k) (Tm.lit c)) q" in text


def test_each_ladder_arm_has_the_shape_the_guard_lemmas_already_cover():
    """The bounded sub-case's reflect claim, made structural rather than
    verbal: every arm of every ladder is `guard -> body` with the guard an
    equality between the bound object and a LITERAL -- precisely the
    `Stmt.sall k (Stmt.base (Pd.pimp (Pd.peq (Tm.tvar k) (Tm.lit c)) q))`
    shape `sall_guard_iff` collapses and `compile_guard_shape` preserves.  So
    the sub-case rides proven machinery, and the only thing it lacks is
    subjects."""
    for shape, pred in SHAPES.items():
        rungs = ladder(pred, "n", _LADDER_BOUND)
        assert rungs["op"] == "and"
        assert len(rungs["args"]) == _LADDER_BOUND + 1
        for k, arm in enumerate(rungs["args"]):
            assert arm["op"] == "implies", shape
            guard, _body = arm["args"]
            assert guard == _t("=", _ref("n"), _lit(k)), (shape, k)


# ------------------------------------------------------- the twelve subjects
def test_the_classified_subject_set_is_exactly_the_ledger_s():
    """DERIVED, not typed.  The subjects measured here are the subjects
    `results/frontier_refusals.jsonl` files under `symbolic-exponent` -- no
    more, no fewer.  A thirteenth refusal reds here rather than being silently
    left out of a count that claims to be complete."""
    ledger = _ledger_shas()
    assert len(ledger) == len(set(ledger)) == 12, ledger
    assert set(ledger) == set(SUBJECTS), \
        f"classification drifted from the ledger: "\
        f"{set(ledger) ^ set(SUBJECTS)}"


def test_every_classified_subject_resolves_to_its_committed_corpus_text():
    """...and each classification is tied to the PROSE it classifies, by the
    same hash the frontier joins on.  A reading that drifted off its text is
    the failure mode a per-subject table invites, so the text is re-derived
    from the corpus on every run."""
    texts = _corpus_texts()
    for sha, row in SUBJECTS.items():
        assert sha in texts, f"{row['label']}: no committed node hashes to it"
        _corpus, label, prose = texts[sha]
        assert label == row["label"], (label, row["label"])
        assert prose.strip(), row["label"]
        # the reading must be about a power: every subject's prose carries one
        assert "^" in prose, f"{row['label']}: no exponent in the source text"


def test_no_ledger_subject_falls_in_the_bounded_subcase():
    """THE COUNT, and the verdict.  The bounded sub-case is additive, already
    bought, and refills ZERO of the twelve: not one subject bounds its exponent
    above.  Every classification names its reason, so the claim is a table a
    reader can check against the prose rather than a number to be trusted.

    This is the tooth that flips if the finding ever becomes wrong: intake a
    corpus with bounded-exponent subjects, give one an `upper_bound`, and this
    reds -- at which point the ladder above is the encoding those subjects
    need, and the smaller purchase becomes real."""
    bounded = {sha: row for sha, row in SUBJECTS.items()
               if row["upper_bound"] is not None}
    assert bounded == {}, (
        "a ledger subject now bounds its exponent -- the bounded sub-case is "
        f"no longer empty and the row's class must be re-measured: {bounded}")
    for sha, row in SUBJECTS.items():
        assert row["exponent"] in ("var", "compound", "iterate"), row
        assert len(row["why"].split()) >= 12, \
            f"{row['label']}: a classification that names no reason is a guess"


def test_the_row_refills_at_most_five_subjects_even_if_it_were_bought():
    """The other number the bill needs, derived from `results/frontier.json`:
    seven of the twelve carry a SECOND refusal (six `function-symbol`, one
    `mod-operator`), so even a full symbolic-exponent purchase returns five
    subjects on its own.  Recorded because "twelve subjects" is the row's
    price and not its delta, and the projection counts subjects rather than
    summing groups.

    THE BILL'S NUMBER IS UNCHANGED AND ITS EXPLANATION IS FINER (C3 cycle 26,
    results/c3_cycle_26.md).  `solo == 5` is the claim the row is priced on
    and it still holds exactly.  What moved is the SHAPE of the joint set:
    four of the six subjects whose only other refusal was the single word
    `function-symbol` were taken through the gate by cycle 26 and refused
    again -- on `recursive-definition`, `elided-sequence-definition`,
    `factorial-operator` + `bigop-symbolic-bound`, and
    `uninterpreted-function-symbol` + `iterated-application` respectively.
    P8 met `function-symbol` for the eliminable-body rung only, so a count
    that read "six held by function-symbol" was reading one word standing
    for three rungs.  All six STILL carry `refused:function-symbol` (the
    ledger is append-only and its rows stand); they now carry more, which is
    why this asserts the containment and the refinement separately rather
    than an exact-equality on a word whose meaning the cycle split."""
    co_filed = _co_filed_signals()
    solo, joint = [], {}
    for sha, row in SUBJECTS.items():
        others = {s for s in co_filed.get(sha, set())
                  if s and s != "refused:symbolic-exponent"}
        assert "refused:symbolic-exponent" in co_filed.get(sha, set()), \
            f"{row['label']}: the frontier does not carry this refusal"
        if others:
            joint[row["label"]] = sorted(others)
        else:
            solo.append(row["label"])
    assert len(solo) == 5, sorted(solo)
    assert len(joint) == 7, sorted(joint)
    # the row's own reading: six of the seven are held by function-symbol, one
    # (fermats_little) by mod-operator.  Containment, not equality -- a subject
    # measured past the word keeps the row it was filed under.
    assert sum(1 for v in joint.values()
               if "refused:function-symbol" in v) == 6, joint
    assert [k for k, v in joint.items()
            if "refused:function-symbol" not in v] == ["fermats_little"], joint
    # the cycle-26 refinement, pinned so a later re-widening of the word reds
    # here: four of those six are now held by a signal NAMING WHICH RUNG.
    cycle26 = {"refused:recursive-definition",
               "refused:elided-sequence-definition",
               "refused:factorial-operator",
               "refused:uninterpreted-function-symbol",
               "refused:iterated-application"}
    assert sum(1 for v in joint.values() if cycle26 & set(v)) == 4, joint


def test_the_measurement_covers_the_positions_the_subjects_actually_use():
    """THE COMPLETENESS CANARY.  Every exponent SHAPE the classification names
    is exercised by at least one probe in `SHAPES`, so the sweep is measuring
    the fragment the subjects need and not a convenient corner of it.  A later
    subject with a genuinely new exponent position reds here -- where it reads
    as "the sweep has stopped covering the demand" -- instead of passing
    silently on shapes nobody files."""
    used = {row["exponent"] for row in SUBJECTS.values()}
    assert used == {"var", "compound", "iterate"}, used
    # `var` is the shape the ladder handles, and it is swept in every position
    # the subjects put it in: alone, under `+`, on both sides, beside a
    # literal-exponent power, under `%`, under a connective, over a negative
    # base, and under a unary atom.
    assert len(SHAPES) >= 9
    assert any("%" in json.dumps(p) for p in SHAPES.values())
    assert any(json.dumps(p).count('"^"') >= 2 for p in SHAPES.values())
    assert SHAPES["negative-base"]["args"][0]["args"][0] == _lit(-1)
    assert SHAPES["mixed-D10"]["args"][0]["args"][1] == _lit(2), \
        "the one shape where D10 admits one power and refuses the other"
    # `compound` and `iterate` are NOT reachable by the ladder, and the encoding
    # says so by raising rather than by omission -- asserted so the two shapes
    # are covered as REFUSALS rather than merely unmentioned.
    with pytest.raises(UnboundedExponent):
        instantiate(_t("=", _t("^", _lit(2), _t("+", N, _lit(2))), _lit(0)),
                    "n", 3)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            if fn.__code__.co_argcount:
                continue
            fn()
            print("ok", name)
