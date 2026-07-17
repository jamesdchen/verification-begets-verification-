"""WP-AUTH T6b corpus tooth: the 28_predecessor ∃-form dissolution over Int.

Source 28 ("For every number n there is a number m with m plus 1 equal to n.")
is the ambient-ambiguity source the frozen committed run transcribes with the
WITNESS-TERM workaround: it universalises `(n-1) + 1 = n` (an identity, no ∃),
which certifies over Int and REFUTES over truncated Nat at n=0 -- the ambient
CHOICE the source exists to exercise.  This tooth authors the GENUINE ∃ FORM
(`binder:"exists"` over Int) as a FIXTURE and records its HONEST bounded-shadow
behaviour.  It NEVER touches the frozen checkpoint's committed reading (asserted
below), and it never weakens the reading or the gate to force a green
(refusals are the gates working).

The honest outcome (empirically verified, mirrored in
generators/math_eval.py's bounded-shadow semantics):

  * the ∃ form routes through the MERGED bounded-shadow ∃ channel: the shape is
    a SUPPORTED ∀-outer(n)/∃-inner(m) split, and the compiled statement keeps
    the REAL `∃` in `lean_text` (the compiler is untouched; the eval channel is
    finitized) -- the workaround this machinery dissolves;
  * moving the carrier from Nat to Int DISSOLVES the n=0 refutation the Nat
    predecessor suffers: at n=0 the Int predecessor m=-1 is in-box and the
    conclusion HOLDS (contrast tests/test_formalize_pipeline.py
    ::test_t6b_false_exists_refutes_with_witness, which refutes the Nat form at
    n=0);
  * BUT the conservative bounded shadow still REFUTES at the lower bound EDGE
    n = -B: the predecessor of -B is -B-1, which lies OUTSIDE the box [-B,B], so
    no in-bound ∃ witness exists there.  This is the deliberate bound-edge
    honesty (§11.6): the shadow certifies only the BOUNDED claim, over-refuses a
    truly-true UNBOUNDED statement, and NEVER false-greens -- exactly symmetric
    to 43_larger_integer_exists' upper-edge refutation at n=+B (a +1 shift off
    the top edge; here a -1 shift off the bottom).  A -1/+1 shift is not a box
    bijection, unlike the additive-inverse m=-n
    (test_t6b_true_forall_exists_certifies_bounded_shadow), which is exactly why
    that one certifies and the predecessor does not.

So the genuine ∃ form does NOT certify at B=8; the frozen witness-term reading
(an identity, certifies unconditionally over Int) remains the certifying
transcription.  That contrast IS the dissolution tooth.
"""
import json

import sys
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from run.formalize import certify_statement            # noqa: E402
from generators.math_reading import parse_math_reading  # noqa: E402
from generators import math_eval                        # noqa: E402


_SRC = "For every number n there is a number m with m plus 1 equal to n."

# The GENUINE ∃ form over Int (a fixture -- NOT the committed 28 reading).  Every
# demand/presupposition quote is a literal substring of _SRC (groundedness).
_PRED_EXISTS_INT = {
    "theorem": "predecessor_exists",
    "statements": [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "on", "force": "demand", "quote": "every number n",
         "lf": {"kind": "object", "name": "n", "type": "Int"}},
        {"id": "om", "force": "demand", "quote": "there is a number m",
         "lf": {"kind": "object", "name": "m", "type": "Int"}},
        {"id": "q1", "force": "demand", "quote": "For every number n",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n"]}},
        {"id": "q2", "force": "demand", "quote": "there is a number m",
         "lf": {"kind": "quantifier", "binder": "exists", "objects": ["m"]}},
        {"id": "c", "force": "demand",
         "quote": "there is a number m with m plus 1 equal to n",
         "lf": {"kind": "conclusion", "pred": {"op": "=", "args": [
             {"op": "+", "args": [{"ref": "m"}, {"lit": 1}]}, {"ref": "n"}]}}},
    ],
}


def _reading():
    return parse_math_reading(json.dumps(_PRED_EXISTS_INT), _SRC)


def test_exists_form_routes_through_bounded_shadow_with_real_exists():
    # The reading is classified a SUPPORTED ∀-outer/∃-inner shape and compiles to
    # a REAL ∃ (the compiler is untouched; only the eval channel is finitized).
    reading = _reading()
    shape = math_eval.exists_shadow_shape(reading, bound=8)
    assert shape["mode"] == "supported"
    assert shape["outer"] == ["n"] and shape["exists"] == ["m"]
    r = certify_statement(_SRC, json.dumps(_PRED_EXISTS_INT), bound=8)
    assert "∃" in r.lean_text          # the workaround this machinery dissolves
    # the instances layer surfaces the bounded-shadow gate (Lean absent -> no
    # Certificate, so the channel is observable here).
    inst = dict((L[0], (L[1], L[2])) for L in r.layers)["instances"]
    detail = dict(inst[1])
    assert detail["backend"] == "exists-finitized-enum"
    assert detail["bound"] == "8"


def test_int_carrier_dissolves_the_nat_n0_refutation():
    # Over Int the n=0 point (where the truncated-Nat predecessor fails) HOLDS:
    # the predecessor m=-1 is in-box.  This is the ambient CHOICE 28 exercises.
    reading = _reading()
    assert math_eval.exists_conclusion_holds(reading, {"n": 0}, ["m"], bound=8) is True


def test_exists_form_honestly_refutes_at_lower_bound_edge():
    # The conservative bounded shadow refutes at the LOWER bound edge n=-B: the
    # predecessor -B-1 is out of [-B,B].  Honest, conservative, never a false
    # green -- symmetric to 43_larger_integer_exists at the UPPER edge n=+B.
    reading = _reading()
    shape = math_eval.exists_shadow_shape(reading, bound=8)
    ex = math_eval.exists_instances(reading, shape["outer"], shape["exists"], bound=8)
    assert ex["ok"] is False
    assert ex["witness"] == {"n": -8}          # the lower bound edge
    # the whole pipeline agrees: an honest refusal at stage `instances`.
    r = certify_statement(_SRC, json.dumps(_PRED_EXISTS_INT), bound=8)
    assert not r.ok and r.stage == "instances"
    assert "witness={'n': -8}" in r.error
    # the bound is data, never baked into the compiled bytes (B=5 refutes at -5).
    r5 = certify_statement(_SRC, json.dumps(_PRED_EXISTS_INT), bound=5)
    assert not r5.ok and "witness={'n': -5}" in r5.error
    assert r.statement_hash == r5.statement_hash


def test_frozen_committed_28_reading_is_untouched_and_certifies():
    # The FIXTURE above changes nothing about the committed 28 reading: the
    # frozen checkpoint still carries the witness-term transcription (no ∃), and
    # it still certifies (an identity over Int).
    state = os.path.join(_ROOT, "results", "formalize_bench_state.jsonl")
    committed = None
    with open(state) as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            rec = json.loads(raw)
            if rec["source_id"] == "28_predecessor" and rec["arm"] == "governed":
                committed = rec
                break
    assert committed is not None, "committed 28 record absent"
    assert committed["certified"] is True
    doc = json.loads(committed["reading_json"])
    # the committed reading is the witness-term form: a forall (no exists binder)
    # over the identity (n-1)+1 = n.
    binders = [s["lf"].get("binder") for s in doc["statements"]
               if s["lf"]["kind"] == "quantifier"]
    assert binders == ["forall"]
    r = certify_statement(_SRC, committed["reading_json"])
    assert r.ok and "∃" not in r.lean_text


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
