"""C12 (PLAN_FRAGMENT §3.1 cadence): session-inline MathReadings for the
census-sourced corpus additions below -- skeleton emitted by
tools/intake_from_frontier.py, then cut down by the driver session to the
sources that actually certified.  Sibling of wp_c2/c3/c4_readings.py; same
discipline, next batch.

PROVENANCE.  Each source's text is the VERBATIM prose of a census
attempt-candidate node (NOT a sentence a maintainer authored):

    113_06_induction_proposition_002 <- math2001 06_Induction#proposition-002
    114_06_induction_proposition_003 <- math2001 06_Induction#proposition-003

SIX OF THE EIGHT SELECTED SUBJECTS ARE NOT HERE.  06_Induction problems
010/011/012/015/016 and proposition-001 have no faithful in-fragment reading;
each was measured one at a time and recorded as a first-class REFUSAL in
results/frontier_refusals.jsonl, never bent into a reading and never silently
dropped.  Their laid-down source files were removed (a refused subject is
demand data, never a corpus source) and the two survivors were renumbered
113/114 so the corpus numbering stays tight.  See results/c3_cycle_14.md.

The READINGS below were authored by the driver session (UNMETERED; reused
identically by both arms), gate-checked, and box-verified TRUE via
run.formalize.certify_statement BEFORE they were written.
"""


PROVENANCE = {
    '113_06_induction_proposition_002': {
        "corpus": 'math2001',
        "node_id": '06_Induction#proposition-002',
        "text_sha256": '6be719aafa51ce8121f71abbbfaed26bc13b84043690f529e2ce8fd6a490b6b8',
    },
    '114_06_induction_proposition_003': {
        "corpus": 'math2001',
        "node_id": '06_Induction#proposition-003',
        "text_sha256": 'd6aade02ea1dd170534b34abd2d1b4276adca689c23baaa2f1f600217f691463',
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
# The first sources the corpus has ever taken from 06_Induction, and the first
# to use the `gcd` operator word at SYMBOLIC arguments.  `gcd` is an
# already-admitted MATH_OPERATORS word (arity 2, role term) marked
# `enum_only` -- it has NO sound SMT rendering, so a reading that uses it is
# carried by the enumeration arm (instance replay over the smallest box)
# rather than by the dual-solver mirror.  Nothing is purchased here: the word,
# the carrier and the `dvd` atom were all already in the fragment.  Both
# readings were box-verified TRUE before being written, and a deliberately
# FALSE variant of each was checked to refute (see the cycle receipt).

# 113  <- 06_Induction proposition-002: gcd(a,b) is nonnegative, over Int.
# The nonnegativity is stated with the builtin `<=` atom in the `0 <= t`
# orientation that the already-admitted arity-1 nonnegativity template
# (op_3c0de4c8920b) also uses -- no new vocabulary, and the subject's own
# word "nonnegative" is exactly this atom.
READINGS['113_06_induction_proposition_002'] = {
    "theorem": "gcd_nonneg",
    "statements": [
        _amb("Int"),
        _obj("oa", "a", r"For all integers \(a\) and \(b\)", "Int"),
        _obj("ob", "b", r"For all integers \(a\) and \(b\)", "Int"),
        _q("q", ["a", "b"], r"For all integers \(a\) and \(b\)"),
        _con(op("<=", lit(0), op("gcd", r("a"), r("b"))),
             r"the integer \(\operatorname{gcd}(a,b)\) is nonnegative"),
    ]}

# 114  <- 06_Induction proposition-003: gcd(a,b) is a factor of BOTH a and b.
# "is a factor of" is the already-admitted arity-2 `dvd` atom in its
# divisor-first orientation (the source-100/101 reading), and "both" is the
# `and` connective -- so the conclusion is the conjunction of the two
# divisibilities the source names, not a weakening to either one.  This is
# the corpus's first source whose `dvd` arguments are a COMPOUND term.
READINGS['114_06_induction_proposition_003'] = {
    "theorem": "gcd_dvd_both",
    "statements": [
        _amb("Int"),
        _obj("oa", "a", r"For all integers \(a\) and \(b\)", "Int"),
        _obj("ob", "b", r"For all integers \(a\) and \(b\)", "Int"),
        _q("q", ["a", "b"], r"For all integers \(a\) and \(b\)"),
        _con(op("and", op("dvd", op("gcd", r("a"), r("b")), r("a")),
                       op("dvd", op("gcd", r("a"), r("b")), r("b"))),
             r"is a factor of both \(a\) and \(b\)"),
    ]}
