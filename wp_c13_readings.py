"""C13 (PLAN_FRAGMENT §3.1 cadence): session-inline MathReadings for the
census-sourced corpus additions below -- skeleton emitted by
tools/intake_from_frontier.py, then cut down by the driver session to the
sources that actually certified.  Sibling of wp_c2/c3/c4_readings.py; same
discipline, next batch.

PROVENANCE.  Each source's text is the VERBATIM prose of a census
attempt-candidate node (NOT a sentence a maintainer authored):

    115_06_induction_theorem_001      <- math2001 06_Induction#theorem-001
    116_06_induction_theorem_007      <- math2001 06_Induction#theorem-007
    117_06_induction_theorem_008      <- math2001 06_Induction#theorem-008
    118_06_induction_theorem_009      <- math2001 06_Induction#theorem-009
    119_07_number_theory_theorem_002  <- math2001 07_Number_Theory#theorem-002

THREE OF THE EIGHT SELECTED SUBJECTS ARE NOT HERE.  06_Induction theorems
002 and 010 and 06_Induction theorem-006 have no faithful in-fragment
reading; each was measured one at a time and recorded as a first-class
REFUSAL in results/frontier_refusals.jsonl, never bent into a reading and
never silently dropped.  Their laid-down source files were removed (a
refused subject is demand data, never a corpus source) and the five
survivors were renumbered 115-119 so the corpus numbering stays tight.
Each refusal was ALSO probed past its first blocker, and no probe reached a
SECOND missing kind -- so each earned exactly one ledger row, not two.
See results/c3_cycle_15.md.

The READINGS below were authored by the driver session (UNMETERED; reused
identically by both arms), gate-checked, and box-verified TRUE via
run.formalize.certify_statement BEFORE they were written.
"""


PROVENANCE = {
    '115_06_induction_theorem_001': {
        "corpus": 'math2001',
        "node_id": '06_Induction#theorem-001',
        "text_sha256": '3ead7850d4260e7403c1ada61309706cdbea408de7ace7f8039728f29ba6245f',
    },
    '116_06_induction_theorem_007': {
        "corpus": 'math2001',
        "node_id": '06_Induction#theorem-007',
        "text_sha256": 'b552953068b156b652bcbd59b53d76caa22d565ee6b02f467c4d2a6a6cbadacf',
    },
    '117_06_induction_theorem_008': {
        "corpus": 'math2001',
        "node_id": '06_Induction#theorem-008',
        "text_sha256": '3a6de2f4f6d7cf32b90aeff3ae9c30966a78affe8685324e27f8b4df7e530568',
    },
    '118_06_induction_theorem_009': {
        "corpus": 'math2001',
        "node_id": '06_Induction#theorem-009',
        "text_sha256": 'bb5ba3906257a8c6f8b8285104fbaa968effe00743a434b160fbe4ba023163a0',
    },
    '119_07_number_theory_theorem_002': {
        "corpus": 'math2001',
        "node_id": '07_Number_Theory#theorem-002',
        "text_sha256": '6178de2ca8f319f61fd9cdff9028ce197cab730e07c51b32642452ed9aa78461',
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

# --- DRIVER AUTHORS BELOW (one reading per source) ------------------
# The corpus's first sources to use the already-admitted `mod` operator word
# at SYMBOLIC arguments, plus its first parity DISJUNCTION and its first
# irrationality subject.  Nothing is purchased here: `mod`, `even`, `odd`,
# the `or` connective and the `^` builtin at a LITERAL exponent were all
# already in the fragment.  Every reading was box-verified TRUE before being
# written.

# 115  <- 06_Induction theorem-001: every natural number is even or odd.
# The corpus's first parity DISJUNCTION: both already-admitted arity-1
# predicate words (`even`, `odd`) under the `or` connective, over Nat.  The
# source says "either ... or", which is the inclusive disjunction the
# fragment has -- and nothing here weakens it to either half.
READINGS['115_06_induction_theorem_001'] = {
    "theorem": "even_or_odd",
    "statements": [
        _amb("Nat"),
        _obj("on", "n", r"Let \(n\) be a natural number", "Nat"),
        _q("q", ["n"], r"Let \(n\) be a natural number"),
        _con(op("or", op("even", r("n")), op("odd", r("n"))),
             r"Then \(n\) is either even or odd"),
    ]}

# 116  <- 06_Induction theorem-007: mod(n,d) is nonnegative for positive d.
# The corpus's first SYMBOLIC-argument use of the `mod` operator word (it had
# only ever appeared at literal moduli).  `d` positive is the source's own
# hypothesis, carried as the `0 < d` atom; "nonnegative" is the builtin
# `0 <= t` atom, the same orientation source 113 used.
READINGS['116_06_induction_theorem_007'] = {
    "theorem": "mod_nonneg",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"For any integers \(n\) and \(d\)", "Int"),
        _obj("od", "d", r"For any integers \(n\) and \(d\)", "Int"),
        _q("q", ["n", "d"], r"For any integers \(n\) and \(d\)"),
        _hyp("h", op("<", lit(0), r("d")), r"with \(d\) positive"),
        _con(op("<=", lit(0), op("mod", r("n"), r("d"))),
             r"\(\operatorname{mod}(n, d)\) is nonnegative"),
    ]}

# 117  <- 06_Induction theorem-008: mod(n,d) < d for positive d.  The upper
# half of the division-algorithm remainder bound, sibling to 116's lower
# half; `<` is the builtin atom, so this is coverage, not vocabulary.
READINGS['117_06_induction_theorem_008'] = {
    "theorem": "mod_lt_of_pos",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"For any integers \(n\) and \(d\)", "Int"),
        _obj("od", "d", r"For any integers \(n\) and \(d\)", "Int"),
        _q("q", ["n", "d"], r"For any integers \(n\) and \(d\)"),
        _hyp("h", op("<", lit(0), r("d")), r"with \(d\) positive"),
        _con(op("<", op("mod", r("n"), r("d")), r("d")),
             r"\(\operatorname{mod}(n, d)<d\)"),
    ]}

# 118  <- 06_Induction theorem-009: there EXISTS an integer r with 0 <= r < b
# and a = r (mod b).  Discharged constructively by the sanctioned WITNESS-TERM
# pattern (sources 84/85/87/107; tests/test_t6b_predecessor_int.py: "the
# committed reading of an exists-claim is a forall with the witness supplied
# as a term, no exists binder").  The witness is r := mod(a,b), substituted at
# every occurrence -- so the reading asserts exactly what the source's
# existential asserts about that witness, and the three conjuncts are the
# source's own three conditions, none dropped:
#   0 <= mod(a,b)                      <- `0 \le r`
#   mod(a,b) < b                       <- `r < b`
#   mod(a,b) = mod(mod(a,b), b)        <- `a \equiv r \mod b`
# The congruence is rendered as equality of residues, which is what the
# `mod` term word gives the fragment; at the witness both sides reduce to the
# same residue precisely because b is positive (the source's hypothesis).
READINGS['118_06_induction_theorem_009'] = {
    "theorem": "exists_mod_rep",
    "statements": [
        _amb("Int"),
        _obj("oa", "a", r"Let \(a\) and \(b\) be integers", "Int"),
        _obj("ob", "b", r"Let \(a\) and \(b\) be integers", "Int"),
        _q("q", ["a", "b"], r"Let \(a\) and \(b\) be integers"),
        _hyp("h", op("<", lit(0), r("b")), r"with \(b\) positive"),
        _con(op("and",
                op("and", op("<=", lit(0), op("mod", r("a"), r("b"))),
                          op("<", op("mod", r("a"), r("b")), r("b"))),
                op("=", op("mod", r("a"), r("b")),
                        op("mod", op("mod", r("a"), r("b")), r("b")))),
             r"There exists an integer \(r\) , with \(0 \le r < b\) , such that \(a \equiv r\mod b\)"),
    ]}

# 119  <- 07_Number_Theory theorem-002: no naturals a,b with b != 0 and
# a^2 = 2 b^2 (the irrationality of sqrt 2, in its Diophantine form).  The
# corpus's first source from 07_Number_Theory.  A NON-EXISTENCE claim is
# universally quantified without any exists binder at all -- `not exists x, P`
# is `forall x, not P`, and with P a conjunction the fragment renders the
# negation as the source's own side condition carried as a HYPOTHESIS and the
# equation NEGATED in the conclusion (`!=`, a builtin atom).  Nothing is
# weakened: b != 0 -> a^2 != 2 b^2 is equivalent to the source's claim, not a
# consequence of it.  `^` appears only at the LITERAL exponent 2.
READINGS['119_07_number_theory_theorem_002'] = {
    "theorem": "no_nat_sqrt_two",
    "statements": [
        _amb("Nat"),
        _obj("oa", "a", r"natural numbers \(a\) and \(b\)", "Nat"),
        _obj("ob", "b", r"natural numbers \(a\) and \(b\)", "Nat"),
        _q("q", ["a", "b"], r"natural numbers \(a\) and \(b\)"),
        _hyp("h", op("!=", r("b"), lit(0)), r"with \(b\ne 0\)"),
        _con(op("!=", op("^", r("a"), lit(2)),
                      op("*", lit(2), op("^", r("b"), lit(2)))),
             r"for which \(a^2=2b^2\)"),
    ]}
