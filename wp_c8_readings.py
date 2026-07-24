"""C8 (PLAN_FRAGMENT §3.1 cadence): session-inline MathReadings for the
census-sourced corpus additions below -- scaffold emitted by
tools/intake_from_frontier.py, then curated by the C3 cycle-09 driver.
Sibling of wp_c2/c3/c4_readings.py; same discipline, next batch.

PROVENANCE.  Each source's text is the VERBATIM prose of a census
attempt-candidate node (NOT a sentence a maintainer authored):

    86_04_proofs_with_structure_ii_problem_007 <- math2001 04_Proofs_with_Structure_II#problem-007

The intake window opened on EIGHT ch4 entries; SEVEN were measured as
refusals and demoted through results/frontier_refusals.jsonl (see
results/c3_cycle_09.md for the per-source verdict table).  Only the
source above transcribes, so only it is authored here -- intake moves
signals, never verdicts, and a source that fails to certify is recorded
as first-class demand data, never silently dropped or read loosely.

THE ONE READING.  "for all sufficiently large integers n" is unfolded by
the SAME CHAPTER'S OWN definition (04#definition-001: a property holds
for all sufficiently large n iff there exists N such that it holds for
all n >= N) into the exists-then-forall shape the fragment already
carries -- so the unfolding is the source's own, not a convenience:

    exists nbig, forall n,  nbig <= n  ->  4*n^2 + 7 <= n^3

`n^3 >= 4n^2 + 7` is written with the argument order flipped into `<=`
because `>=` is not a builtin atom (atoms: =, !=, <=, <); flipping the
sides of an inequality is a notational identity, not a weakening.  Only
builtin term ops appear (`+ * ^` at literal exponents 2 and 3), so no
operator word, macro, or trust root grows.

Recorded honestly: definition-001 -- the DEFINITION of "sufficiently
large" -- is one of this cycle's seven refusals (it quantifies over a
property; the gate says `unknown atom/connective 'property'`), while
this INSTANCE of that definition at a concrete property certifies.  The
fragment expresses every instance of the definition and not the
definition itself.
"""


PROVENANCE = {
    '86_04_proofs_with_structure_ii_problem_007': {
        "corpus": 'math2001',
        "node_id": '04_Proofs_with_Structure_II#problem-007',
        "text_sha256": '5b1c98e4b8d227871261a3d6d8b866c1ba612bc7dd58b4c362abfd451b7cb0a0',
    },
}


def _amb(carrier):
    return {"id": "amb", "force": "choice", "quote": "",
            "lf": {"kind": "ambient", "carrier": carrier}}


def _obj(i, name, quote, typ):
    return {"id": i, "force": "demand", "quote": quote,
            "lf": {"kind": "object", "name": name, "type": typ}}


def _q(sid, objects, quote, binder="forall"):
    return {"id": sid, "force": "demand", "quote": quote,
            "lf": {"kind": "quantifier", "binder": binder,
                   "objects": objects}}


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

READINGS["86_04_proofs_with_structure_ii_problem_007"] = {
    "theorem": "cubic_dominates_eventually",
    "statements": [
        _amb("Int"),
        # the bound whose existence "sufficiently large" asserts
        _obj("ob", "nbig", r"for all sufficiently large integers \(n\)", "Int"),
        _obj("on", "n", r"sufficiently large integers \(n\)", "Int"),
        _q("qx", ["nbig"], r"for all sufficiently large integers \(n\)",
           binder="exists"),
        _q("qf", ["n"], r"sufficiently large integers \(n\)"),
        _con(op("implies",
                op("<=", r("nbig"), r("n")),
                op("<=",
                   op("+", op("*", lit(4), op("^", r("n"), lit(2))), lit(7)),
                   op("^", r("n"), lit(3)))),
             r"\(n ^ 3 ≥ 4n ^ 2 + 7\)"),
    ]}
