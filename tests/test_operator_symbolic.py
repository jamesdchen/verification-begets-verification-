"""Teeth for the SYMBOLIC operator battery (b2) -- operator_growth.py.

All LLM-free and Lean-free, relational asserts only (the test_operator_growth
discipline).  Z3 is a hard dependency of the battery (all-unknown refuses), so
asserting a definite z3 verdict is fair; cvc5 absence is tolerated honestly,
so no assert here requires it.

The four teeth, one per designed behaviour:
  (i)   a carrier-stable word gets a definite z3 ``unsat`` on the stability
        obligation and a ``stable-*`` verdict recorded in the battery;
  (ii)  a carrier-DIVERGENT word (the truncated-``-`` T4 class) is still
        admitted -- divergence is recorded evidence, never a refusal -- with
        the eval-corroborated witness point in the record;
  (iii) a definite solver ``unsat`` contradicting an eval-witnessed box point
        refuses as an engine disagreement (wiring tooth, planted verdicts);
  (iv)  a box-vacuous but solver-satisfiable word still refuses (v1: the box
        refusal stands) and the refusal NAMES the outside-the-box evidence.
"""
import copy

import pytest

from generators import operator_growth as og

# congm(a,b,m) := (a mod m) = (b mod m): the standing non-alias fixture; no
# ``-`` anywhere, so its Nat and Int renderings agree on the shared domain.
CONGM = {"word": "congm", "arity": 3, "params": ["a", "b", "m"],
         "definition": {"op": "=", "args": [
             {"op": "mod", "args": [{"ref": "a"}, {"ref": "m"}]},
             {"op": "mod", "args": [{"ref": "b"}, {"ref": "m"}]}]}}

# zero_diff(a,b) := (a - b) = 0: carrier-DIVERGENT by construction -- Nat
# ``-`` truncates (0 - 1 = 0, so the pred HOLDS at a=0,b=1) while Int ``-``
# is real (-1 != 0, so it FAILS there).  Exactly the T4 tooth class.
ZERO_DIFF = {"word": "zero_diff", "arity": 2, "params": ["a", "b"],
             "definition": {"op": "=", "args": [
                 {"op": "-", "args": [{"ref": "a"}, {"ref": "b"}]},
                 {"lit": 0}]}}

# beyond(a) := 4 < a: a contradiction on the default battery box (Nat values
# 0..4 never exceed 4; Int values -4..4 neither) yet trivially satisfiable at
# a=5 -- the box-vacuous / solver-satisfiable seam of tooth (iv).
BEYOND = {"word": "beyond", "arity": 1, "params": ["a"],
          "definition": {"op": "<", "args": [{"lit": 4}, {"ref": "a"}]}}


def _battery(row):
    return og._run_battery(row, {}, og.DEFAULT_BATTERY_BOUND,
                           og.DEFAULT_MAX_INSTANCES)


# ------------------------------------------------------- (i) stable, proved
def test_congm_symbolic_channels_recorded_and_stable():
    ok, reason, battery = _battery(CONGM)
    assert ok, reason
    sym = battery["symbolic"]
    # per-carrier existence verdicts recorded for both directions.
    for carrier in og.CARRIERS:
        ch = sym["carriers"][carrier]
        assert ch["satisfiable"]["z3"] == "sat"
        assert ch["refutable"]["z3"] == "sat"
    # stability: z3 proves the xor obligation unsat (identical semantics on
    # the shared domain); the verdict is stable-proved when cvc5 corroborates,
    # stable-z3-only when cvc5 is honestly absent -- never anything weaker.
    stab = sym["carrier_stability"]
    assert stab["z3"] == "unsat"
    assert stab["verdict"] in ("stable-proved", "stable-z3-only")


# --------------------------------------- (ii) divergent: recorded, admitted
def test_zero_diff_divergence_is_recorded_never_refused():
    ok, reason, battery = _battery(ZERO_DIFF)
    assert ok, reason                       # divergence must NOT refuse
    stab = battery["symbolic"]["carrier_stability"]
    assert stab["z3"] == "sat"              # a divergence point exists
    assert stab["verdict"] == "divergent"   # ...and the box corroborates it
    w = stab["witness"]
    assert w is not None
    assert w["nat"] != w["int"]             # a genuine cross-carrier flip
    # the recorded point really is a witness: re-evaluate both carriers.
    params = ZERO_DIFF["params"]
    kd = og._expand_definition_to_kernel(ZERO_DIFF, {})
    from generators import math_eval as _eval
    nat_v = bool(_eval.eval_pred(kd, w["assignment"],
                                 {p: "Nat" for p in params}, None))
    int_v = bool(_eval.eval_pred(kd, w["assignment"],
                                 {p: "Int" for p in params}, None))
    assert (nat_v, int_v) == (w["nat"], w["int"])


# ------------------------- (iii) engine contradiction refuses (wiring tooth)
def test_planted_universal_unsat_refuses_as_engine_disagreement(monkeypatch):
    # Plant a symbolic result claiming z3 PROVED congm universally
    # unsatisfiable on Nat -- while the box holds eval-witnessed true points.
    # The wiring must refuse and name the contradiction; nothing real is
    # mutated (the plant lives only in this monkeypatch).
    real = og._symbolic_battery

    def planted(kernel_def, params, be, bound, max_instances):
        out = real(kernel_def, params, be, bound, max_instances)
        out = copy.deepcopy(out)
        out["carriers"]["Nat"]["satisfiable"]["z3"] = "unsat"
        return out

    monkeypatch.setattr(og, "_symbolic_battery", planted)
    ok, reason, battery = _battery(CONGM)
    assert ok is False
    assert battery is None
    assert "symbolic disagreement" in reason
    assert "Nat" in reason and "z3" in reason


# ------------------- (iv) box-vacuous, solver-satisfiable: named in refusal
def test_box_vacuous_refusal_names_outside_box_satisfiability():
    ok, reason, battery = _battery(BEYOND)
    assert ok is False                      # v1: the box refusal stands
    assert "CONTRADICTION on the battery domain" in reason
    assert "OUTSIDE the battery box" in reason


# ---------------------------------------- symbolic block rides into the cert
def test_admitted_cert_carries_symbolic_block():
    # congm admitted end-to-end (the test_operator_growth pricing fixture):
    # the cert's battery must carry the symbolic block, so carrier behaviour
    # is auditable from the persisted record alone.
    def _congsub(x, y, m):
        return {"op": "=", "args": [
            {"op": "mod", "args": [{"ref": x}, {"ref": m}]},
            {"op": "mod", "args": [{"ref": y}, {"ref": m}]}]}

    def _reading(n):
        pairs = [("a", "b"), ("c", "d")][:n]
        return {"theorem": "witness", "statements": [
            {"id": f"h{i}", "force": "presupposition", "quote": "q",
             "lf": {"kind": "hypothesis", "pred": _congsub(x, y, "m")}}
            for i, (x, y) in enumerate(pairs)]}

    corpus = [_reading(2), _reading(2)]
    res = og.admit_operator(CONGM, pricing_corpus=corpus, registry={})
    assert res["admitted"], res
    sym = res["cert"]["battery"]["symbolic"]
    assert sym["carrier_stability"]["verdict"] in (
        "stable-proved", "stable-z3-only")
