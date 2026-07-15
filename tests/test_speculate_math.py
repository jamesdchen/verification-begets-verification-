#!/usr/bin/env python3
"""WP-E: MathReading speculative fan-out TEETH -- LLM-free, hand-planted.

Runnable under pytest AND as a bare script
(`python3 tests/test_speculate_math.py` -> PASS lines, exit 0).

F-INT-5 adds a Lean-free math pre-gate ladder that mirrors the service ladder
(`speculate.pre_gate`) rung for rung, cheapest first:

    parse-math-reading (gate)      -> parse_math_reading groundedness/trichotomy
    math-smt (hypothesis-sat)      -> dual-solver non-vacuity (Z3 [AND cvc5])
    compile-math (escape gate)     -> compile_math_reading + validate_lean
    entailed-instance-replay       -> RANK-ONLY, never a rejection (S4)

These teeth pin (E3):

  * RUNG ORDER: a fabricating candidate dies at the parse gate and NO SMT
    backend call is ever spent on it (cheapest-first is real, not decorative);
  * a CONTRADICTORY hypothesis set dies at math-smt (dual-solver degrades
    honestly when cvc5 is absent -- the enumeration channel still refuses);
  * a CARRIER-NARROWED candidate (declared object types Nat where Int is
    needed -- ⚠FI-6) REACHES entailed-instance-replay (rank-only never rejects)
    but its replay refutes it, so it REORDERS below the certifying candidate;
  * LOSER-HAS-NO-CERT (Z1): no losing candidate mints a certificate;
  * a speculated-pass / certified-fail divergence logs the Z-D payload;
  * the SERVICE ladder is byte-unchanged (the pin below, captured from the
    frozen pre-swarm base BEFORE speculate.py was edited -- ⚠FI-11).
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))          # runnable as a bare script, not just -m pytest

from buildloop import speculate
from kernel.backends import SmtBackend
from kernel.certs import Certificate
from library import Registry


# --------------------------------------------------------------------------- #
def _ensure_cvc5_degrades() -> bool:
    """cvc5 may be WHOLLY absent in a thin environment (CI installs it).  The
    SmtBackend imports cvc5 OUTSIDE its try, so `run_cvc5` would RAISE rather
    than return the honest ``{"result": "error"}`` a present-but-failing solver
    yields.  When the module is genuinely unavailable, install that honest
    degradation so the dual-solver falls to the z3 + enumeration channel (the
    documented cvc5-absent behavior).  A no-op when cvc5 imports (CI), so a
    dual-solver that is really present is never weakened."""
    try:
        import cvc5  # noqa: F401
        return False
    except Exception:
        def _degraded(self, smtlib, timeout_ms=15000, expect="unsat"):
            return {"backend": "cvc5", "result": "error",
                    "detail": "cvc5 module absent (honest degradation)"}
        SmtBackend.run_cvc5 = _degraded
        return True


_CVC5_DEGRADED = _ensure_cvc5_degrades()


# --------------------------------------------------------------------------- #
# BYTE-IDENTITY PIN (⚠FI-11): the SERVICE ladder's structural verdicts on the
# four canonical scenarios of tests/test_speculate.py, captured from the FROZEN
# pre-swarm base before this package touched speculate.py.  WP-E adds functions;
# it never edits the service ladder, and this pin proves the service verdicts
# did not move.  Only the solver-version-STABLE fields are pinned (stage/ok/
# scenario count); `detail` carries a solver version string and is excluded by
# design -- pinning it would be a false byte-identity claim (E5 honesty).
_SERVICE_LADDER_GOLDEN = {
    "good":          {"stage_reached": "entailed-replay", "ok": True,  "scenarios": 3},
    "inverted":      {"stage_reached": "entailed-replay", "ok": True,  "scenarios": 3},
    "contradictory": {"stage_reached": "consistency",     "ok": False, "scenarios": 0},
    "ungrounded":    {"stage_reached": "reading-gate",    "ok": False, "scenarios": 0},
}

# The service request + planted readings (imported from the service teeth so the
# pin exercises the EXACT same fixtures the service path certifies).
import tests.test_speculate as _svc


def _service_scenarios() -> dict:
    out = {}
    out["good"] = speculate.pre_gate(_svc.REQUEST, _svc._text(_svc.GOOD))
    doc = _svc._clone(); doc["statements"][2]["lf"]["op"] = "inc"
    out["inverted"] = speculate.pre_gate(_svc.REQUEST, _svc._text(doc))
    doc = _svc._clone()
    doc["statements"].append(
        {"id": "sX", "force": "demand", "quote": "more than 8",
         "lf": {"kind": "bound", "action": "sell", "left": "count",
                "cmp": ">=", "right": 10}})
    out["contradictory"] = speculate.pre_gate(_svc.REQUEST, _svc._text(doc))
    doc = _svc._clone(); doc["statements"][3]["quote"] = "guarantee same-day refunds"
    out["ungrounded"] = speculate.pre_gate(_svc.REQUEST, _svc._text(doc))
    return out


def test_service_ladder_byte_unchanged():
    """The SERVICE ladder's structural verdicts are byte-identical to the frozen
    pre-swarm base -- WP-E added the math path without disturbing the service
    path (the E3 byte-identity requirement)."""
    got = _service_scenarios()
    stable = {k: {"stage_reached": v["stage_reached"], "ok": v["ok"],
                  "scenarios": v["scenarios"]} for k, v in got.items()}
    assert stable == _SERVICE_LADDER_GOLDEN, json.dumps(stable, indent=2)


# --------------------------------------------------------------------------- #
# The K=4 planted candidate MathReadings for ONE source (distinct construals).
SOURCE = ("For all integers a and b, if b is positive and b is at most zero, "
          "then a minus b plus b equals a.")
CONCL_QUOTE = "a minus b plus b equals a"


def _obj(sid, name, ty):
    return {"id": sid, "force": "choice", "quote": "",
            "lf": {"kind": "object", "name": name, "type": ty}}


def _concl(sid, pred, quote):
    return {"id": sid, "force": "demand", "quote": quote,
            "lf": {"kind": "conclusion", "pred": pred}}


def _hyp(sid, pred, quote):
    return {"id": sid, "force": "presupposition", "quote": quote,
            "lf": {"kind": "hypothesis", "pred": pred}}


def _ap(op, *args):
    return {"op": op, "args": list(args)}


def _ref(n):
    return {"ref": n}


def _lit(v):
    return {"lit": v}


# `(a - b) + b = a`: true over Int, FALSE over truncated Nat (the ⚠FI-6 core).
_SUB_ADD = _ap("=", _ap("+", _ap("-", _ref("a"), _ref("b")), _ref("b")),
               _ref("a"))

CERTIFYING = {"theorem": "sub_add_cancel", "statements": [
    _obj("o_a", "a", "Int"), _obj("o_b", "b", "Int"),
    _concl("c", _SUB_ADD, CONCL_QUOTE)]}

FABRICATING = {"theorem": "sub_add_cancel", "statements": [
    _obj("o_a", "a", "Int"), _obj("o_b", "b", "Int"),
    _concl("c", _ap("=", _ap("+", _ref("a"), _ref("b")), _lit(0)),
           "a plus b equals zero")]}          # quote absent from the source

CONTRADICTORY = {"theorem": "sub_add_cancel", "statements": [
    _obj("o_a", "a", "Int"), _obj("o_b", "b", "Int"),
    _hyp("h1", _ap("<", _lit(0), _ref("b")), "b is positive"),
    _hyp("h2", _ap("<=", _ref("b"), _lit(0)), "b is at most zero"),
    _concl("c", _SUB_ADD, CONCL_QUOTE)]}       # 0 < b AND b <= 0 is unsat

CARRIER_NARROWED = {"theorem": "sub_add_cancel", "statements": [
    _obj("o_a", "a", "Nat"), _obj("o_b", "b", "Nat"),   # ⚠FI-6 object types
    _concl("c", _SUB_ADD, CONCL_QUOTE)]}


def _t(doc):
    return json.dumps(doc)


# --------------------------------------------------------------------------- #
def test_stage_order_is_cheapest_first():
    """The frozen ladder order names the four rungs cheapest-first: parse before
    smt before compile before replay."""
    assert speculate.MATH_STAGES == (
        "parse-math-reading", "math-smt", "compile-math",
        "entailed-instance-replay"), speculate.MATH_STAGES


def test_fabrication_dies_at_parse_gate():
    """A demanded conclusion whose quote is not in the source is caught earliest,
    at parse-math-reading (fabrication), with ok False and no replay signal."""
    res = speculate.pre_gate_math(SOURCE, _t(FABRICATING))
    assert res["stage_reached"] == "parse-math-reading", res
    assert res["ok"] is False, res
    assert res["replay_ok"] is None and res["n_instances"] == 0, res


def test_rung_order_fabrication_spends_no_smt_call():
    """E3 rung-order tooth: the ladder is cheapest-first for real -- the
    fabricating candidate (killed at the parse gate) triggers ZERO SMT backend
    invocations, while a candidate that clears the parse gate DOES reach the
    solver.  Counted by wrapping BOTH solver entry points."""
    calls = {"n": 0}
    real_z3, real_cvc5 = SmtBackend.run_z3, SmtBackend.run_cvc5

    def _count(real):
        def wrapper(self, *a, **k):
            calls["n"] += 1
            return real(self, *a, **k)
        return wrapper

    SmtBackend.run_z3 = _count(real_z3)
    SmtBackend.run_cvc5 = _count(real_cvc5)
    try:
        calls["n"] = 0
        speculate.pre_gate_math(SOURCE, _t(FABRICATING))
        fab_calls = calls["n"]
        calls["n"] = 0
        speculate.pre_gate_math(SOURCE, _t(CERTIFYING))
        good_calls = calls["n"]
    finally:
        SmtBackend.run_z3 = real_z3
        SmtBackend.run_cvc5 = real_cvc5

    assert fab_calls == 0, ("fabrication reached the SMT rung -- the ladder is "
                            f"not cheapest-first: {fab_calls} calls")
    assert good_calls >= 1, ("a candidate that clears the parse gate must reach "
                             f"the solver: {good_calls} calls")


def test_contradictory_dies_at_math_smt():
    """Two grounded but jointly-unsatisfiable presupposition hypotheses die at
    math-smt (non-vacuity), never reaching compile/replay.  Honest with cvc5
    absent: the enumeration channel still refuses."""
    res = speculate.pre_gate_math(SOURCE, _t(CONTRADICTORY))
    assert res["stage_reached"] == "math-smt", res
    assert res["ok"] is False, res


def test_certifying_reaches_replay_and_holds():
    """The certifying reading clears every rung and reaches entailed-instance-
    replay with replay_ok True (every entailed instance makes the conclusion
    hold)."""
    res = speculate.pre_gate_math(SOURCE, _t(CERTIFYING))
    assert res["stage_reached"] == "entailed-instance-replay", res
    assert res["ok"] is True, res
    assert res["replay_ok"] is True, res
    assert res["n_instances"] >= 1, res
    # Z1: a pre-gate is a RANK, not a certificate.
    assert not (set(res) & {"cert", "cert_id", "certificate"}), res


def test_carrier_narrowed_reaches_replay_but_reorders_never_rejects():
    """⚠FI-6 + S4: the carrier-narrowed reading (declared Nat object types ->
    truncated Nat.sub) REACHES entailed-instance-replay -- stage 4 is rank-only
    and never rejects -- but its replay is refuted (replay_ok False), so it
    ranks BELOW the certifying reading.  A REORDER, not a rejection."""
    narrowed = speculate.pre_gate_math(SOURCE, _t(CARRIER_NARROWED))
    certifying = speculate.pre_gate_math(SOURCE, _t(CERTIFYING))
    # rank-only: never rejected, reached the terminal rung with ok True.
    assert narrowed["stage_reached"] == "entailed-instance-replay", narrowed
    assert narrowed["ok"] is True, narrowed
    assert narrowed["replay_ok"] is False, narrowed
    # reorder: the refuted candidate sorts strictly AFTER the clean one.
    assert speculate.rank_score_math(certifying) < \
        speculate.rank_score_math(narrowed), (certifying, narrowed)


def test_winner_certifies_losers_get_no_certificate():
    """E3 loser-has-no-cert: only the winner (certifying) reaches a passing
    certification; every loser's real-pipeline verdict is ok False, so no loser
    carries a Certificate (Z1)."""
    win = speculate.certify_math(SOURCE, _t(CERTIFYING))
    assert win.ok is True, win
    for doc in (FABRICATING, CONTRADICTORY, CARRIER_NARROWED):
        res = speculate.certify_math(SOURCE, _t(doc))
        assert res.ok is False, (doc, res)
        assert not isinstance(res.statement_cert, Certificate), res


def test_pre_gate_persists_nothing():
    """Z1: `pre_gate_math` ranks; it never calls reading_add or mints a cert, so
    a fresh registry stays empty after pre-gating every candidate."""
    reg = Registry(db_path=tempfile.mkdtemp() + "/r.sqlite")
    for doc in (CERTIFYING, FABRICATING, CONTRADICTORY, CARRIER_NARROWED):
        speculate.pre_gate_math(SOURCE, _t(doc))
    assert reg.readings_all() == [], reg.readings_all()
    assert reg.events("speculation-divergence") == []


def test_divergence_logged_predicted_pass_actual_fail():
    """The carrier-narrowed candidate: speculated PASS (rank-only replay reached
    the terminal rung) but the real pipeline REFUTES it -> exactly one
    `speculation-divergence` event with the shared Z-D payload shape."""
    reg = Registry(db_path=tempfile.mkdtemp() + "/r.sqlite")
    pre = speculate.pre_gate_math(SOURCE, _t(CARRIER_NARROWED))
    certified = speculate.certify_math(SOURCE, _t(CARRIER_NARROWED))
    assert pre["ok"] is True and certified.ok is False, (pre, certified)
    payload = speculate.log_math_divergence(
        reg, SOURCE, _t(CARRIER_NARROWED), pre, certified.ok,
        request_sha="req-sub-add")
    assert payload is not None, "the miss must log a divergence"
    assert payload["direction"] == "predicted-pass-actual-fail", payload
    # shared payload shape (identical to the service path's Z-D keys).
    assert set(payload) == {"stage", "direction", "candidate_sha",
                            "request_sha"}, payload
    rows = reg.events("speculation-divergence")
    assert len(rows) == 1, rows
    assert rows[0]["payload"] == payload


def test_agreement_logs_no_divergence():
    """A tie/agreement is never logged (Z-D): the winner's speculated PASS and
    certified PASS agree, so `log_math_divergence` returns None and writes
    nothing."""
    reg = Registry(db_path=tempfile.mkdtemp() + "/r.sqlite")
    pre = speculate.pre_gate_math(SOURCE, _t(CERTIFYING))
    certified = speculate.certify_math(SOURCE, _t(CERTIFYING))
    payload = speculate.log_math_divergence(reg, SOURCE, _t(CERTIFYING), pre,
                                            certified.ok)
    assert payload is None, payload
    assert reg.events("speculation-divergence") == []


def test_fan_out_math_is_llm_free_by_default():
    """With neither a model nor an injected author (every LLM-free / CI caller),
    fan_out_math makes no call and returns [] -- the deterministic path never
    touches the LLM."""
    assert speculate.fan_out_math(SOURCE, 4) == []
    assert speculate.fan_out_math(SOURCE, 4, model=None, author=None) == []


def test_fan_out_math_injected_author_renders_real_prompt():
    """fan_out_math authors K candidates via an injected author, feeding it the
    REAL prompt from render_math_reading_prompt (the E1 seam) -- LLM-free,
    deterministic, K-wide."""
    seen = []

    def author(prompt, i):
        seen.append(prompt)
        return {"text": _t(CERTIFYING), "input_tokens": 10, "output_tokens": i}

    out = speculate.fan_out_math(SOURCE, 4, author=author)
    assert len(out) == 4, out
    assert all("SOURCE:" in p and SOURCE in p for p in seen), "prompt not rendered"
    # index 0 uses the base prompt; i>0 append a deterministic variation suffix.
    assert seen[0] != seen[1], "variation suffix missing"
    assert [d["variation"] for d in out] == [0, 1, 2, 3], out


def test_end_to_end_one_winner_one_divergence():
    """The full planted fan-out: K=4 authored, each loser killed at its own rung,
    the winner alone certifies, exactly one speculation-divergence recorded."""
    reg = Registry(db_path=tempfile.mkdtemp() + "/r.sqlite")
    labelled = [("certifying", CERTIFYING), ("fabricating", FABRICATING),
                ("contradictory", CONTRADICTORY),
                ("carrier-narrowed", CARRIER_NARROWED)]
    docs = [_t(d) for _l, d in labelled]

    def author(prompt, i):
        return {"text": docs[i], "input_tokens": 100, "output_tokens": 40 + i}

    fan = speculate.fan_out_math(SOURCE, 4, author=author)
    results = [speculate.pre_gate_math(SOURCE, c["text"]) for c in fan]
    stages = [r["stage_reached"] for r in results]
    assert stages == ["entailed-instance-replay", "parse-math-reading",
                      "math-smt", "entailed-instance-replay"], stages

    survivors = sorted(
        [(labelled[i][0], fan[i], results[i]) for i in range(4)
         if results[i]["ok"]],
        key=lambda t: speculate.rank_score_math(t[2]))
    assert [s[0] for s in survivors] == ["certifying", "carrier-narrowed"], survivors

    winner_label, winner_cand, _wres = survivors[0]
    win = speculate.certify_math(SOURCE, winner_cand["text"])
    assert winner_label == "certifying" and win.ok is True, (winner_label, win)

    # the carrier-narrowed loser: speculated pass, certified fail -> divergence.
    n_label, n_cand, n_res = survivors[1]
    n_cert = speculate.certify_math(SOURCE, n_cand["text"])
    speculate.log_math_divergence(reg, SOURCE, n_cand["text"], n_res, n_cert.ok,
                                  request_sha="req-e2e")
    assert len(reg.events("speculation-divergence")) == 1, reg.events(
        "speculation-divergence")


if __name__ == "__main__":
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print("PASS", _name)
    print("speculate-math teeth hold (service ladder byte-unchanged; "
          "fabrication dies pre-SMT; contradiction at math-smt; carrier-narrow "
          "reorders never rejects; loser has no cert; one Z-D divergence)")
