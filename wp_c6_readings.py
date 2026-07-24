"""C3 cycle-04 (PLAN_FRAGMENT §3.1 cadence): session-inline MathReadings for the
FIFTH census-sourced corpus additions -- sources 82-83.

Sibling of wp_c5_readings.py (79-81), wp_c4_readings.py (75-78),
wp_c3_readings.py (71-74) and wp_c2_readings.py (67-70); same discipline, next
batch.  PROVENANCE.  Each source's text is the VERBATIM prose of a
blueprint-census attempt-candidate from the math2001 corpus
(`specs/mathsources/math2001/nodes.jsonl`; The Mechanics of Proof, H. Macbeth),
NOT a sentence a maintainer authored:

    82_sq_ne_two_nat  <- math2001 02_Proofs_with_Structure#problem-013
    83_sq_ne_two_int  <- math2001 02_Proofs_with_Structure#problem-016

Authoring mirrors wp_c5_readings.py EXACTLY: one reading per source, authored by
the orchestrating session (UNMETERED -- cost columns VOID), reused identically by
both arms.  Quotes are LITERAL source substrings (whitespace/case-normalized),
which for this corpus means quoting the sentence's LaTeX spans verbatim.

The batch OPENS a NEW reading-conclusion shape for the shipped corpus: the FIRST
`!=` (`\\ne`) conclusion to certify.  `!=` is already a BUILTIN atom op in the
fragment (`generators/math_reading.py::_BUILTIN_ATOM_OPS = {"=", "!=", "<=",
"<"}`, compiled to `≠` by math_compile and mirrored by math_eval/math_smt);
this cycle is the first census candidate whose in-lexicon conclusion USES it, so
no operator word, macro, or trust root grows -- only shipped COVERAGE of an
already-admitted atom.  The squared term is the ALREADY-ADMITTED squaring
template `^(v0, 2)` (op_34e1b706c47c, the C2 closure).  Both readings are
forall-class, in-fragment, and TRUE over the B=8 box (checked before authoring by
`run.formalize.certify_statement`; never distort a reading to force a green):
  * 82  n : Nat,  n^2 != 2       (no n in {0..8} squares to 2)
  * 83  n : Int,  n^2 != 2       (the same statement over the Int carrier)

The Nat/Int pair is deliberate: it exercises the ambient-carrier axis on an
identical surface sentence (the census emitted both as distinct nodes), the exact
Nat-vs-Int contrast the fragment is built to keep honest.  Neither carries any
parity or divisibility structure, so the arity-1 even/odd op-slot and the `dvd`
macros are UNTOUCHED -- the even/odd macro coverage invariant survives exactly as
in 67-81.

MEASURED-and-NOT-shipped this cycle (honesty; the census reports signals, never
fidelity verdicts, and a refusal is first-class demand data).  The frontier's
`ready` list is ordered by census signal, NOT by transcribability, so the first
six ready entries this cycle are all refusals; they are recorded here, not
written as sources (the manifest partition pins EXACTLY 4 `non-transcribable`
files to named miss-kinds, and a refused candidate is not silently minted into a
green):
  * 82_edge_disjoint (equational_theories `L_y x = L_z x => L_y^n x = L_z^n x`):
    a free function symbol L and a SYMBOLIC iteration exponent n -- out of the
    Nat/Int arithmetic fragment (no function carriers, no symbolic-bound power).
  * 83_fermats_little (formal_book `a^{p-1} \\equiv 1 \\pmod p`): modular
    congruence AND a symbolic exponent p-1 -- neither `mod` nor symbolic-bound
    `^` is in the fragment (the same `bigop:symbolic-bound` frontier the P1
    delta named for iteration-class purchases).
  * ch1 003 (`b^2=2a^2, am+bn=1 -> (2an+bm)^2=2`): TRUE but VACUOUS over the
    integers -- b^2=2a^2 forces a=b=0, then am+bn=0!=1, so the hypothesis has no
    integer witness and the F2.1 nonvacuity gate refuses it (recorded, never
    universalised into a green; same verdict cycle-03 measured).
  * ch1 016/021, ch2 006: `>`/`>=` conclusions outside the `< <=` atom lexicon
    (`_BUILTIN_ATOM_OPS` has `<`,`<=` and NOT `>`,`>=`) -- same refusal class as
    cycle-02/03's 016/021.

This file is the provenance record; the inline author reads READINGS[sid] and
returns the compiled reading to `bench_formalize.run_bench` on checkpoint resume
(only the 2 new source_ids enter; nothing prior is re-authored).
"""


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

READINGS["82_sq_ne_two_nat"] = {"theorem": "sq_ne_two_nat",
    "statements": [
        _amb("Nat"),
        _obj("on", "n", r"\(n\) be any natural number", "Nat"),
        _q("q", ["n"], r"Let \(n\) be any natural number"),
        _con(op("!=", op("^", r("n"), lit(2)), lit(2)),
             r"\(n ^ 2 \ne 2\)")]}

READINGS["83_sq_ne_two_int"] = {"theorem": "sq_ne_two_int",
    "statements": [
        _amb("Int"),
        _obj("on", "n", r"\(n\) be any integer", "Int"),
        _q("q", ["n"], r"Let \(n\) be any integer"),
        _con(op("!=", op("^", r("n"), lit(2)), lit(2)),
             r"\(n ^ 2 \ne 2\)")]}
