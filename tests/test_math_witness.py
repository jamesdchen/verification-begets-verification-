"""FI-KA-1 -- the witness-template emitter (generators/math_witness.py).

Pins the frozen interface (KA_INTERFACES.md FI-KA-1) plus its failure-mode teeth:

  * the source-43 walkthrough (difference-intersection {1} -> ``m := n + 1``,
    surviving the full check at the edge point n=8 out of the box);
  * the bound-in-bytes dual-bound tooth (B=8 and B=12 emit BYTE-IDENTICAL proofs;
    the bound rides only in ``search`` / cache key);
  * ``statement_lean_text`` byte-identical to ``compile_math_reading``;
  * the data-derived candidate family equals the derived intersection EXACTLY
    (no tuned constants -- no offset menu, no fresh ceiling);
  * the EXHAUSTIVE full check (never a k-smallest sample over admitted points):
    the edge-fit literal ``m := 8`` is rejected at n=8, recomputed independently;
  * the frozen skip vocabulary and honest-skip semantics;
  * no-mint / Lean-free (the module imports no kernel / LeanBackend and proposes,
    never certifies);
  * escape-gate self-validation (the emitter refuses its OWN gate-failing output).

Lean-free: this exercises only the deterministic emitter (no LeanBackend).
"""
import json
import pathlib

from generators.math_reading import parse_math_reading
from generators.math_compile import compile_math_reading
from generators import math_witness as mw
from buildloop.validate_lean import validate_lean


# ------------------------------------------------------------------- builders
def _reading(statements, source, theorem="t"):
    return parse_math_reading(
        json.dumps({"theorem": theorem, "statements": statements}), source)


def _amb():
    return {"id": "amb", "force": "choice", "quote": "",
            "lf": {"kind": "ambient", "carrier": "Int"}}


def _obj(oid, name, quote, ty="Int"):
    return {"id": oid, "force": "demand", "quote": quote,
            "lf": {"kind": "object", "name": name, "type": ty}}


def _q(qid, binder, objs, quote):
    return {"id": qid, "force": "demand", "quote": quote,
            "lf": {"kind": "quantifier", "binder": binder, "objects": objs}}


def _hyp(hid, pred, quote):
    return {"id": hid, "force": "presupposition", "quote": quote,
            "lf": {"kind": "hypothesis", "pred": pred}}


def _con(pred, quote):
    return {"id": "c", "force": "demand", "quote": quote,
            "lf": {"kind": "conclusion", "pred": pred}}


def _lt(a, b):
    return {"op": "<", "args": [a, b]}


def _eq(a, b):
    return {"op": "=", "args": [a, b]}


def _ref(n):
    return {"ref": n}


def _lit(v):
    return {"lit": v}


# The committed source 43: ∀ n:Int, ∃ m:Int, n < m (bound-edge REFUTING; the
# emitter proposes the unbounded witness the shadow conservatively refuses).
def _source43():
    src = "for every integer n there exists an integer m with n less than m"
    stmts = [
        _amb(),
        _obj("on", "n", "every integer n"),
        _obj("om", "m", "an integer m"),
        _q("qf", "forall", ["n"], "for every integer n"),
        _q("qx", "exists", ["m"], "there exists an integer m"),
        _con(_lt(_ref("n"), _ref("m")), "n less than m"),
    ]
    return _reading(stmts, src, "larger_integer_exists")


# ============================================================ the 43 walkthrough
def test_source43_walkthrough_emits_n_plus_one():
    # The frozen walkthrough: at B=8 the difference-intersection is {1}, so the
    # survivor is m := n + 1; it passes at the edge point n=8 (m=9, out of box).
    out = mw.emit_witness_proofs(_source43(), bound=8)
    assert out["status"] == "emitted"
    assert out["template"] == {"m": {"op": "+", "args": [_ref("n"), _lit(1)]}}
    s = out["search"]
    assert s["bound"] == 8 and s["rung"] == "exists-anchor/v1"
    # 17 admitted outer points (n in [-8,8], no hypotheses); 16 witnessed (n=8
    # has NO in-box witness -- the deliberate bound-edge refusal).
    assert s["n_outer_admitted"] == 17
    assert s["n_witnessed"] == 16
    # the data-fit literal m := 8 is tried (and rejected at the edge) before the
    # surviving m := n + 1 -- the exhaustive full check is what discriminates them.
    assert s["candidates_tried"] == 2


def test_source43_proof_shape_and_ladder():
    out = mw.emit_witness_proofs(_source43(), bound=8)
    # the four eval_props rungs, in the frozen order.
    assert [p["discharge"] for p in out["proofs"]] == list(mw.RUNGS)
    assert mw.RUNGS == ("decide", "omega", "norm_num", "simp")
    first = out["proofs"][0]["lean_text"]
    assert first == (
        "theorem larger_integer_exists : ∀ (n : Int), ∃ (m : Int), (n < m) := by\n"
        "  intro n\n"
        "  refine ⟨(n + 1), ?_⟩\n"
        "  decide")
    # no hypotheses => no `intro hyp_...` line.
    assert "intro hyp_" not in first
    # every emitted proof passes the escape gate and never uses native_decide.
    for p in out["proofs"]:
        ok, why = validate_lean(p["lean_text"])
        assert ok, why
        assert "native_decide" not in p["lean_text"]
        # differs from `first` only in the final rung line.
        assert p["lean_text"].rsplit("\n", 1)[0] == first.rsplit("\n", 1)[0]


# ================================================ bound-in-bytes (dual-bound tooth)
def test_dual_bound_proofs_byte_identical():
    r = _source43()
    out8 = mw.emit_witness_proofs(r, bound=8)
    out12 = mw.emit_witness_proofs(r, bound=12)
    # THE tooth: emitting at two bounds yields byte-identical proofs and template.
    assert out8["proofs"] == out12["proofs"]
    assert out8["template"] == out12["template"]
    assert out8["statement_lean_text"] == out12["statement_lean_text"]
    assert out8["statement_hash"] == out12["statement_hash"]
    # the bound rides ONLY in search provenance, never in bytes.
    assert out8["search"]["bound"] == 8 and out12["search"]["bound"] == 12
    for p in out12["proofs"]:
        assert "12" not in p["lean_text"]
    for p in out8["proofs"]:
        assert "8" not in p["lean_text"]


def test_statement_lean_text_byte_identical_to_compiler():
    r = _source43()
    out = mw.emit_witness_proofs(r, bound=8)
    compiled = compile_math_reading(r)
    assert out["statement_lean_text"] == compiled["lean_text"]
    assert out["statement_lean_text"].endswith(":= sorry")  # still the subject
    assert out["statement_hash"] == compiled["statement_hash"]


# ============================================== data-derived family (no tuned const)
def test_candidate_family_is_exactly_the_derived_intersection():
    # The candidate set for m is EXACTLY the observed-data intersection -- no
    # offset menu, no constant not drawn from the record (E5/H52).
    r = _source43()
    _, wit8 = mw._collect_witnesses(r, ["n"], ["m"], 8)
    cands8 = {json.dumps(c, sort_keys=True)
              for c in mw._object_candidates(0, ["n"], wit8)}
    assert cands8 == {json.dumps({"lit": 8}, sort_keys=True),
                      json.dumps({"op": "+", "args": [_ref("n"), _lit(1)]},
                                 sort_keys=True)}
    # at B=12 the literal intersection tracks the data ({12}); the difference
    # intersection stays {1}.  No constant is bound-tuned -- each is the record.
    _, wit12 = mw._collect_witnesses(r, ["n"], ["m"], 12)
    cands12 = {json.dumps(c, sort_keys=True)
               for c in mw._object_candidates(0, ["n"], wit12)}
    assert cands12 == {json.dumps({"lit": 12}, sort_keys=True),
                       json.dumps({"op": "+", "args": [_ref("n"), _lit(1)]},
                                  sort_keys=True)}


def test_module_has_no_tuned_numeric_constant():
    # The ONLY ceiling in the module is the imported T6b constant; there is no
    # freshly-minted numeric ceiling / offset cap.
    src = pathlib.Path(mw.__file__).read_text()
    assert "EXISTS_SHADOW_MAX_ASSIGNMENTS" in src
    assert "= 2_000_000" not in src and "= 2000000" not in src


# ============================================ exhaustive full check (k-smallest tooth)
def _admitted_and_concl(r, bound):
    from generators import math_eval as me
    carrier = r.objects()
    ambient = r.ambient_carrier()
    concl = me.conclusions_of(r)
    hyps = me.hypotheses_of(r)
    adm = [o for o in me._canonical_assignments(["n"], carrier, bound)
           if all(me.eval_pred(p, o, carrier, ambient) for p in hyps)]
    return adm, concl, carrier, ambient


def test_full_check_is_exhaustive_rejects_edge_fit():
    # Recompute the eval-replay INDEPENDENTLY (channel-2 discipline: never trust
    # the emitter's own claim).  The data-fit literal m := 8 holds at every LOW
    # shell but FAILS at the highest admitted point n=8 (8 < 8 is False) -- a
    # k-smallest sample would accept it; the exhaustive check rejects it.
    r = _source43()
    adm, concl, carrier, ambient = _admitted_and_concl(r, 8)
    lit8 = {"m": {"lit": 8}}
    nplus1 = {"m": {"op": "+", "args": [_ref("n"), _lit(1)]}}
    # holds on the small shells (|n| <= 7) ...
    small = [o for o in adm if abs(o["n"]) <= 7]
    assert mw._template_passes(lit8, small, concl, carrier, ambient)
    # ... but NOT on the full admitted box (the n=8 edge kills it).
    assert not mw._template_passes(lit8, adm, concl, carrier, ambient)
    assert mw._template_passes(nplus1, adm, concl, carrier, ambient)
    # so the emitter must NOT emit m := 8; it emits the survivor m := n + 1.
    out = mw.emit_witness_proofs(r, bound=8)
    assert out["template"] == nplus1


def test_planted_capped_fixture_yields_no_template():
    # A planted fixture whose bounded conclusion (n < m AND m <= 7) is satisfiable
    # on the low outer points but has NO witness for large n: candidates fit the
    # first shells yet the exhaustive full check rejects every one at the interior
    # admitted point n=7 -- honest `no-template-found`, never a laundered green.
    src = ("for every integer n there exists an integer m with n less than m "
           "and m at most 7")
    stmts = [
        _amb(),
        _obj("on", "n", "every integer n"),
        _obj("om", "m", "an integer m"),
        _q("qf", "forall", ["n"], "for every integer n"),
        _q("qx", "exists", ["m"], "there exists an integer m"),
        _con({"op": "and", "args": [_lt(_ref("n"), _ref("m")),
                                    {"op": "<=", "args": [_ref("m"), _lit(7)]}]},
             "n less than m and m at most 7"),
    ]
    out = mw.emit_witness_proofs(_reading(stmts, src, "capped"), bound=8)
    assert out == {"status": "skip", "reason": "no-template-found"}


# ============================================= hypothesis + multi-exists emission
def test_hypothesis_intro_line_after_exists_binder():
    # A reading WITH a hypothesis: the hyp chain sits AFTER the ∃ binder in the
    # compiled prop, so `intro hyp_h1` follows the anonymous constructor.
    src = "for every positive integer n there exists an integer m with m equal to n"
    stmts = [
        _amb(),
        _obj("on", "n", "integer n"),
        _obj("om", "m", "integer m"),
        _q("qf", "forall", ["n"], "for every positive integer n"),
        _hyp("h1", _lt(_lit(0), _ref("n")), "positive"),
        _q("qx", "exists", ["m"], "there exists an integer m"),
        _con(_eq(_ref("m"), _ref("n")), "m equal to n"),
    ]
    out = mw.emit_witness_proofs(_reading(stmts, src, "hyp_single"), bound=8)
    assert out["status"] == "emitted"
    assert out["template"] == {"m": {"ref": "n"}}
    body = out["proofs"][1]["lean_text"]      # omega rung
    assert body == (
        "theorem hyp_single : ∀ (n : Int), ∃ (m : Int), (0 < n) → (m = n) := by\n"
        "  intro n\n"
        "  refine ⟨n, ?_⟩\n"
        "  intro hyp_h1\n"
        "  omega")


def test_multi_exists_refine_in_binder_order():
    # Two ∃ objects -> the anonymous constructor carries one component per object
    # in emitted binder order, before the single `?_`.
    src = ("for every integer n there exist integers p and q with p equal to n "
           "and q equal to n")
    stmts = [
        _amb(),
        _obj("on", "n", "integer n"),
        _obj("op", "p", "integers p and q"),
        _obj("oq", "q", "integers p and q"),
        _q("qf", "forall", ["n"], "for every integer n"),
        _q("qx", "exists", ["p", "q"], "there exist integers p and q"),
        _con({"op": "and", "args": [_eq(_ref("p"), _ref("n")),
                                    _eq(_ref("q"), _ref("n"))]},
             "p equal to n and q equal to n"),
    ]
    out = mw.emit_witness_proofs(_reading(stmts, src, "multi_exists"), bound=8)
    assert out["status"] == "emitted"
    assert out["template"] == {"p": {"ref": "n"}, "q": {"ref": "n"}}
    assert "refine ⟨n, n, ?_⟩" in out["proofs"][0]["lean_text"]


# ==================================================== frozen skip vocabulary
_SKIP_VOCAB = {"no-exists-binder", "witness-search-domain-too-large",
               "no-template-found"}


def test_skip_no_exists_binder():
    # A forall-only reading has no ∃ to anchor -> honest skip, never ok=False.
    src = "for every integer n, n equals n"
    stmts = [
        _obj("on", "n", "every integer n"),
        _q("qf", "forall", ["n"], "for every integer n"),
        _con(_eq(_ref("n"), _ref("n")), "n equals n"),
    ]
    out = mw.emit_witness_proofs(_reading(stmts, src, "refl"), bound=8)
    assert out == {"status": "skip", "reason": "no-exists-binder"}


def test_skip_shape_unsupported_carries_shape_reason():
    # ∃-only (no outer scope): out of the ∀-outer/∃-inner mode -> the skip reason
    # is `shape-unsupported:` + the exists_shadow_shape reason (verbatim).
    src = "there exists an integer m with m equal to m"
    stmts = [
        _obj("om", "m", "an integer m"),
        _q("qx", "exists", ["m"], "there exists an integer m"),
        _con(_eq(_ref("m"), _ref("m")), "m equal to m"),
    ]
    out = mw.emit_witness_proofs(_reading(stmts, src, "selfref"), bound=8)
    assert out["status"] == "skip"
    assert out["reason"].startswith("shape-unsupported:")
    assert "exists-only" in out["reason"]


def test_skip_witness_search_domain_too_large():
    # 3-outer / 3-inner Int at B=8 is 17^6 ~ 24M evaluations -- over the reused
    # T6b ceiling -> honest skip (no new ceiling; the shape stays supported at
    # bound=None, only the SEARCH is capped).
    onames = ["o0", "o1", "o2"]
    enames = ["e0", "e1", "e2"]
    stmts = [_amb()]
    for nm in onames + enames:
        stmts.append(_obj("d" + nm, nm, "integers"))
    stmts.append(_q("qf", "forall", onames, "for all integers"))
    stmts.append(_q("qx", "exists", enames, "there exist integers"))
    stmts.append(_con(_eq(_ref("e0"), _ref("e0")), "something equal"))
    src = "for all integers there exist integers with something equal"
    out = mw.emit_witness_proofs(_reading(stmts, src, "wide"), bound=8)
    assert out == {"status": "skip", "reason": "witness-search-domain-too-large"}


def test_skip_no_template_when_no_witness_anywhere():
    # ∀ n:Int, ∃ m:Int, (m = n+1 ∧ m = n+2): contradictory, no witness at any
    # outer point -> no data to derive from -> no-template-found (never false).
    src = ("for every integer n there exists an integer m with m equal to n plus "
           "one and m equal to n plus two")
    np1 = {"op": "+", "args": [_ref("n"), _lit(1)]}
    np2 = {"op": "+", "args": [_ref("n"), _lit(2)]}
    stmts = [
        _amb(),
        _obj("on", "n", "every integer n"),
        _obj("om", "m", "an integer m"),
        _q("qf", "forall", ["n"], "for every integer n"),
        _q("qx", "exists", ["m"], "there exists an integer m"),
        _con({"op": "and", "args": [_eq(_ref("m"), np1), _eq(_ref("m"), np2)]},
             "m equal to n plus one and m equal to n plus two"),
    ]
    out = mw.emit_witness_proofs(_reading(stmts, src, "contra"), bound=8)
    assert out == {"status": "skip", "reason": "no-template-found"}


def test_every_skip_reason_is_in_the_frozen_vocabulary():
    # A skip is NEVER an ok=False refutation and its reason is always in the
    # frozen vocabulary (`shape-unsupported:<reason>` is a family, checked above).
    for r, bound in [(_source43(), 8)]:
        out = mw.emit_witness_proofs(r, bound=bound)
        assert out["status"] in ("emitted", "skip")
        if out["status"] == "skip":
            reason = out["reason"]
            assert (reason in _SKIP_VOCAB
                    or reason.startswith("shape-unsupported:"))


# ============================================ no-mint / Lean-free (the emitter dreams)
def test_module_is_lean_free_and_never_mints():
    # generators/ stays Lean-free: the emitter imports no kernel / LeanBackend and
    # its output is a PROPOSAL, never a Certificate (E3/L1: dreams propose, the
    # kernel is the sole certifier -- Lean-absent still yields only proposals).
    src = pathlib.Path(mw.__file__).read_text()
    # no kernel / LeanBackend import (the prose may NAME them to say they are out
    # of scope; what matters is that nothing here actually imports or calls them).
    for forbidden in ("LeanBackend", "import kernel", "from kernel",
                      "kernel.check("):
        assert forbidden not in src, forbidden
    out = mw.emit_witness_proofs(_source43(), bound=8)
    assert out["status"] == "emitted"
    assert "cert" not in out and "certificate" not in out
    # the proposal never carries native_decide (gate-forbidden) in any proof.
    for p in out["proofs"]:
        assert "native_decide" not in p["lean_text"]
    # `_render_term` is IMPORTED from the compiler, never re-defined here.
    assert "def _render_term" not in src
    assert "from .math_compile import" in src


# ================================================= escape-gate self-validation
def test_emitter_refuses_its_own_gate_failing_output(monkeypatch):
    # If the deterministic emitter ever produced gate-failing Lean it must REFUSE
    # its own output (an internal invariant violation), never launder it into a
    # skip.  Force the gate to fail and assert the emit raises WitnessEmitError.
    monkeypatch.setattr(mw, "validate_lean", lambda text: (False, "forced"))
    try:
        mw.emit_witness_proofs(_source43(), bound=8)
    except mw.WitnessEmitError as e:
        assert "escape gate" in str(e)
    else:
        raise AssertionError("emitter did not refuse gate-failing output")
