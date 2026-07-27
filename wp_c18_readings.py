"""C18 (PLAN_FRAGMENT §3.1 cadence): session-inline MathReadings for the
census-sourced corpus additions below.  Sibling of wp_c2/c3/c4_readings.py;
same discipline, next batch.

PROVENANCE.  Each source's text is the VERBATIM prose of a census
attempt-candidate node (NOT a sentence a maintainer authored):

    130_induction_problem_001    <- math2001 06_Induction#problem-001
    131_induction_problem_002    <- math2001 06_Induction#problem-002
    132_induction_problem_003    <- math2001 06_Induction#problem-003

THE BATCH THESE THREE CAME OUT OF.  C3 cycle 27 took EIGHT subjects through
`intake_from_frontier --unblocked` -- five from `refused:symbolic-exponent`,
three from `refused:function-symbol`.  THREE certified and are read here;
five refused and are recorded in the ledger as first-class demand data, each
gate verdict quoted verbatim in results/c3_cycle_27.md.

These three are the FIRST readings in the corpus to use P7's SYMBOLIC
EXPONENT -- `2^n`, `4^n`, `3^n` at a bound variable -- which is what makes
this batch the row's re-measurement rather than more vocabulary.  Carrier
`Nat` throughout is P7's admission condition
(`generators/math_reading._check_pow_exponent`), not a preference: at `Int`
an exponent may be negative and the power leaves the carrier, and the same
batch measured that refusal on a subject that needed it (source 137 of the
take, `a^n = b^n mod d`).

Each reading keeps the source's own written order and spelling.  The prose's
`>=` has no atom op in the fragment -- cycle 20 measured that and declined
the converse rewriting on fidelity -- so the comparison is stated with `<=`
and the source's own two sides in the source's own form, which reverses
nothing about what is being compared.
"""


PROVENANCE = {
    '130_induction_problem_001': {
        "corpus": 'math2001',
        "node_id": '06_Induction#problem-001',
        "text_sha256": 'fdded7108f04ec4c86595ddaa5ea714624f58a600e0f3fc73fbb9c673855e048',
    },
    '131_induction_problem_002': {
        "corpus": 'math2001',
        "node_id": '06_Induction#problem-002',
        "text_sha256": '7e5d574265502b923776260dc663924b81863ddd2d1bc88b2b94a9330d13ff45',
    },
    '132_induction_problem_003': {
        "corpus": 'math2001',
        "node_id": '06_Induction#problem-003',
        "text_sha256": '654f73c75b955534ec08a6bd51913f20492211085751a123f68fc359ba98ac0b',
    },
}


def _amb(carrier):
    return {"id": "amb", "force": "choice", "quote": "",
            "lf": {"kind": "ambient", "carrier": carrier}}


def _obj(i, name, quote, typ):
    return {"id": i, "force": "presupposition", "quote": quote,
            "lf": {"kind": "object", "name": name, "type": typ}}


def _q(sid, objects, quote):
    return {"id": sid, "force": "demand", "quote": quote,
            "lf": {"kind": "quantifier", "binder": "forall",
                   "objects": objects}}


def _hyp(i, pred, quote, force="demand"):
    return {"id": i, "force": force, "quote": quote,
            "lf": {"kind": "hypothesis", "pred": pred}}


def _con(pred, quote):
    return {"id": "c", "force": "demand", "quote": quote,
            "lf": {"kind": "conclusion", "pred": pred}}


def r(name):
    return {"ref": name}


def lit(n):
    return {"lit": n}


def op(o, *args):
    return {"op": o, "args": list(args)}


READINGS = {}

# 130 <- 06_Induction#problem-001: "Let n be a natural number.  Show that
# 2^n >= n+1."  The simplest symbolic-exponent statement in the corpus, and
# deliberately the first one read: it exercises `Tm.pow` in the ONE position
# the ladder handles (a bare bound variable as the exponent) with nothing else
# in the way, so a red here would be about the exponent and not about anything
# standing around it.
READINGS['130_induction_problem_001'] = {
    "theorem": "nat_two_pow_ge_succ",
    "statements": [
        _amb("Nat"),
        _obj("on", "n", r"Let \(n\) be a natural number", "Nat"),
        _q("q", ["n"], r"Let \(n\) be a natural number"),
        _con(op("<=", op("+", r("n"), lit(1)), op("^", lit(2), r("n"))),
             r"\(2 ^n\ge n+1\)"),
    ]}

# 131 <- 06_Induction#problem-002: "Show that 4^n is congruent to either 1 or
# 4 modulo 15."  A symbolic exponent UNDER `mod` -- the second position the
# class measurement's sweep names -- and the elliptical "either 1 or 4" read
# as the `or` of two equalities, the cycle-17 pattern for an elided predicate:
# the disjunction is what the sentence says and all it says.
READINGS['131_induction_problem_002'] = {
    "theorem": "nat_four_pow_mod_fifteen",
    "statements": [
        _amb("Nat"),
        _obj("on", "n", r"Let \(n\) be a natural number", "Nat"),
        _q("q", ["n"], r"Let \(n\) be a natural number"),
        _con(op("or",
                op("=", op("mod", op("^", lit(4), r("n")), lit(15)), lit(1)),
                op("=", op("mod", op("^", lit(4), r("n")), lit(15)), lit(4))),
             r"\(4^n\) is congruent to either \(1\) or \(4\) modulo 15"),
    ]}

# 132 <- 06_Induction#problem-003: "Let n be a natural number greater than or
# equal to 2.  Show that 3^n >= 2^n + 5."  TWO symbolic exponents in one atom,
# on both sides of the comparison -- the shape the sweep pins as `two powers`
# -- with a hypothesis-bounded index.  The bound `2 <= n` is carried as the
# source's own hypothesis rather than folded into the conclusion, so the
# reading declines to assert anything at n < 2, exactly where the source does.
READINGS['132_induction_problem_003'] = {
    "theorem": "nat_three_pow_ge_two_pow_add_five",
    "statements": [
        _amb("Nat"),
        _obj("on", "n",
             r"Let \(n\) be a natural number greater than or equal to 2",
             "Nat"),
        _q("q", ["n"],
           r"Let \(n\) be a natural number greater than or equal to 2"),
        _hyp("h", op("<=", lit(2), r("n")),
             r"greater than or equal to 2"),
        _con(op("<=", op("+", op("^", lit(2), r("n")), lit(5)),
                op("^", lit(3), r("n"))),
             r"\(3 ^n\ge 2^n+5\)"),
    ]}
