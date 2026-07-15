"""LAT-B teeth: speculative K-wide authoring for the scheduler `math` move.

All LLM-free and (Lean-free) hand-planted.  `buildloop.llm.call_llm` is
monkeypatched to an injected author -- the loop's real `_dispatch_math` runs
end to end, the fan-out threads around the injected author, and the WP-E
Lean-free pre-gate ladder (`speculate.pre_gate_math`) grades each candidate for
real.  `run.formalize.certify_statement` is stubbed where the (cvc5-requiring)
kernel would otherwise gate a tooth; the DL price gate always runs on real
fixture bytes.

The four teeth (frozen by the LAT-B design):
  (i)  K=1 default byte-path: with CGB_MATH_FANOUT unset, EXACTLY ONE call_llm
       invocation, behavior identical to the F-INT-1 single-serve expectation
       (no threads, no pre-gate, no divergence ledger);
  (ii) K=3 with one certifying / one fabricating / one contradictory candidate:
       the certifying one is served, EXACTLY 3 call_llm invocations, the losers
       carry no certificate, and ALL 3 calls' tokens are billed;
  (iii) zero survivors -> math-refused (staged at the pre-gate);
  (iv) a planted pre-gate-pass / certify-fail winner logs exactly one
       speculation-divergence.

The candidate MathReadings and their SOURCE are imported from the WP-E teeth
(`tests/test_speculate_math.py`) so the fan-out exercises the SAME fixtures the
pre-gate ladder is pinned against: CERTIFYING clears every rung (and prices at
43.0 < 50.0, so it serves), FABRICATING dies at parse-math-reading,
CONTRADICTORY dies at math-smt, CARRIER_NARROWED reaches the terminal rung but
its instance replay refutes it (a survivor that ranks below CERTIFYING).
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import threading

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from buildloop import dl, loop
from library import Registry

# Reuse the WP-E planted fixtures.  Importing the module ALSO runs its
# cvc5-absent honest-degradation shim (a no-op when cvc5 is present, so a real
# dual-solver is never weakened); that shim is what makes CONTRADICTORY refuse
# at math-smt in a thin environment.
from tests.test_speculate_math import (  # noqa: F401 (import side-effect: cvc5 shim)
    SOURCE, CERTIFYING, FABRICATING, CONTRADICTORY, CARRIER_NARROWED)

from run.formalize import FormalizeResult


def _reg():
    tmp = tempfile.mkdtemp()
    return Registry(db_path=f"{tmp}/reg.sqlite")


def _math_row(did, *, payload_ref=None):
    # payload_ref is a non-existent path -> _dispatch_math's fallback returns the
    # literal string, so payload_ref=SOURCE makes source==SOURCE (no temp file).
    return {"demand_id": did, "kind": "math-source", "origin": "exogenous",
            "status": "open", "language": None, "features": None,
            "payload_ref": payload_ref or SOURCE, "size_bytes": 100,
            "covered_via": None}


def _t(doc):
    return json.dumps(doc)


class _Author:
    """A thread-safe injected `call_llm`: hands out one planted candidate per
    invocation (round-robin over `docs`), counting total calls.  Used to drive
    the loop's real fan-out without touching an LLM."""

    def __init__(self, docs, in_toks=100, out_toks=40):
        self._docs = list(docs)
        self._in, self._out = in_toks, out_toks
        self._lock = threading.Lock()
        self.calls = 0

    def __call__(self, prompt, model=None):
        with self._lock:
            i = self.calls
            self.calls += 1
        doc = self._docs[i % len(self._docs)]
        return {"text": _t(doc), "input_tokens": self._in,
                "output_tokens": self._out, "model": "planted"}


# --------------------------------------------------------------- tooth (i)
def test_k1_default_is_single_call_byte_path(monkeypatch):
    """CGB_MATH_FANOUT unset -> K=1: EXACTLY ONE call_llm, the F-INT-1 single
    serve.  The certifying reading (priced 43.0 < 50.0) is served; the fan-out
    machinery (threads / pre-gate / divergence ledger) is never entered."""
    monkeypatch.delenv(loop.MATH_FANOUT_ENV, raising=False)
    author = _Author([CERTIFYING])
    monkeypatch.setattr("buildloop.llm.call_llm", author)
    monkeypatch.setattr(
        "run.formalize.certify_statement",
        lambda *a, **k: FormalizeResult(ok=True, statement_hash="beef01"))

    reg = _reg()
    reg.demand_upsert(_math_row("m-1"))
    out = loop.run_iteration(reg, [], model="fake-model")

    assert out["picked"] == "math"
    assert out["status"] == "math-certified"
    assert author.calls == 1, "K=1 must make exactly one authoring call"
    assert dl.snapshot(reg).readings.get("m-1") is not None, "row served"
    # a single serve counts the one call's tokens only.
    assert reg.counter_get("llm_input_tokens") == 100
    # K=1 takes the single-call path: no speculation-divergence ledger entry.
    assert reg.events("speculation-divergence") == []


def test_k1_price_gate_still_refuses_dl_raising(monkeypatch):
    """K=1 keeps the ⚠FI-2 price gate verbatim: a reading that prices at/above
    the penalty is refused `dl-raising` and NOT persisted -- identical to the
    F-INT-1 tooth, proving the byte-path is unchanged."""
    from tests.test_math_moves import READING_04
    assert dl.READING_CHAIN_COST + dl.dl_reading(READING_04, {}) >= \
        dl.UNCOVERED_PENALTY
    monkeypatch.delenv(loop.MATH_FANOUT_ENV, raising=False)
    author = _Author([READING_04])
    monkeypatch.setattr("buildloop.llm.call_llm", author)
    monkeypatch.setattr(
        "run.formalize.certify_statement",
        lambda *a, **k: FormalizeResult(ok=True, statement_hash="cafe02"))
    reg = _reg()
    reg.demand_upsert(_math_row("m-4", payload_ref="m-4"))
    out = loop.run_iteration(reg, [], model="fake-model")
    assert out["status"] == "math-refused"
    assert author.calls == 1
    assert dl.snapshot(reg).readings.get("m-4") is None


# -------------------------------------------------------------- tooth (ii)
def test_k3_certifying_wins_losers_uncertified(monkeypatch):
    """K=3 over {certifying, fabricating, contradictory}: the certifying
    candidate alone survives the pre-gate ladder and is served; EXACTLY 3
    call_llm invocations; the losers are never certified (Z1); ALL 3 calls'
    tokens are billed."""
    monkeypatch.setenv(loop.MATH_FANOUT_ENV, "3")
    author = _Author([CERTIFYING, FABRICATING, CONTRADICTORY],
                     in_toks=100, out_toks=40)
    monkeypatch.setattr("buildloop.llm.call_llm", author)

    certified_texts = []

    def cert(source, reading_text, *a, **k):
        certified_texts.append(reading_text)
        return FormalizeResult(ok=True, statement_hash="beef03")

    monkeypatch.setattr("run.formalize.certify_statement", cert)

    reg = _reg()
    reg.demand_upsert(_math_row("m-1"))
    out = loop.run_iteration(reg, [], model="fake-model")

    assert out["status"] == "math-certified", out
    assert author.calls == 3, "K=3 must make exactly three authoring calls"
    # only the winner (certifying) is ever certified -- losers get no cert (Z1).
    assert certified_texts == [_t(CERTIFYING)], certified_texts
    # the served reading is the certifying one (snapshot.readings holds the
    # already-parsed reading dict).
    served = dl.snapshot(reg).readings.get("m-1")
    assert served is not None
    assert served["theorem"] == CERTIFYING["theorem"]
    # honest cost: ALL 3 calls' tokens are billed (3 * (100 in, 40 out)).
    assert reg.counter_get("llm_input_tokens") == 300
    assert reg.counter_get("llm_output_tokens") == 120


def test_k3_ranks_survivor_over_refuted_replay(monkeypatch):
    """K=3 over {carrier-narrowed, certifying, fabricating}: BOTH the carrier-
    narrowed and the certifying candidate reach the terminal rung (survivors),
    but the WP-E ranking puts the clean-replay certifying candidate first, so it
    is the one served -- a REORDER, never a rejection of the refuted one."""
    monkeypatch.setenv(loop.MATH_FANOUT_ENV, "3")
    author = _Author([CARRIER_NARROWED, CERTIFYING, FABRICATING])
    monkeypatch.setattr("buildloop.llm.call_llm", author)
    monkeypatch.setattr(
        "run.formalize.certify_statement",
        lambda source, txt, *a, **k: FormalizeResult(
            ok=(json.loads(txt)["statements"][0]["lf"]["type"] == "Int"),
            statement_hash="beef04", stage="instances"))
    reg = _reg()
    reg.demand_upsert(_math_row("m-1"))
    out = loop.run_iteration(reg, [], model="fake-model")
    assert out["status"] == "math-certified", out
    served = dl.snapshot(reg).readings.get("m-1")
    # the certifying (Int) reading won the rank, not the narrowed (Nat) one.
    assert served["statements"][0]["lf"]["type"] == "Int"


# ------------------------------------------------------------- tooth (iii)
def test_zero_survivors_math_refused(monkeypatch):
    """K=3 where EVERY candidate dies in the pre-gate ladder -> zero survivors
    -> math-refused, staged at `pre-gate`; nothing is certified or persisted, and
    the refusal is remembered (A3 counting substrate)."""
    monkeypatch.setenv(loop.MATH_FANOUT_ENV, "3")
    author = _Author([FABRICATING, CONTRADICTORY, FABRICATING])
    monkeypatch.setattr("buildloop.llm.call_llm", author)

    called = {"cert": False}

    def cert(*a, **k):
        called["cert"] = True
        return FormalizeResult(ok=True)

    monkeypatch.setattr("run.formalize.certify_statement", cert)

    reg = _reg()
    reg.demand_upsert(_math_row("m-1"))
    out = loop.run_iteration(reg, [], model="fake-model")

    assert out["status"] == "math-refused", out
    assert out["stage"] == "pre-gate", out
    assert author.calls == 3
    assert called["cert"] is False, "no survivor -> certify_statement never runs"
    assert dl.snapshot(reg).readings.get("m-1") is None
    # A3: the refusal is logged (so MATH_MAX_ATTEMPTS suppression can accrue).
    refused = reg.events("math-refused")
    assert refused and refused[-1]["payload"]["stage"] == "pre-gate"


def test_all_calls_fail_is_refused_no_crash(monkeypatch):
    """Every candidate call RAISING is not a crash: zero candidates -> math-
    refused (stage pre-gate).  A failed call is no candidate."""
    monkeypatch.setenv(loop.MATH_FANOUT_ENV, "3")

    def boom(prompt, model=None):
        raise RuntimeError("planted authoring failure")

    monkeypatch.setattr("buildloop.llm.call_llm", boom)
    reg = _reg()
    reg.demand_upsert(_math_row("m-1"))
    out = loop.run_iteration(reg, [], model="fake-model")
    assert out["status"] == "math-refused" and out["stage"] == "pre-gate"
    assert dl.snapshot(reg).readings.get("m-1") is None


def test_partial_call_failure_still_serves(monkeypatch):
    """One failing call degrades to no-candidate while the surviving certifying
    candidate is still served -- the round does not crash and only the completed
    calls' tokens are billed."""
    monkeypatch.setenv(loop.MATH_FANOUT_ENV, "3")
    lock = threading.Lock()
    state = {"n": 0}

    def author(prompt, model=None):
        with lock:
            i = state["n"]
            state["n"] += 1
        if i == 0:
            raise RuntimeError("planted failure")
        return {"text": _t(CERTIFYING), "input_tokens": 10, "output_tokens": 5,
                "model": "planted"}

    monkeypatch.setattr("buildloop.llm.call_llm", author)
    monkeypatch.setattr(
        "run.formalize.certify_statement",
        lambda *a, **k: FormalizeResult(ok=True, statement_hash="beef05"))
    reg = _reg()
    reg.demand_upsert(_math_row("m-1"))
    out = loop.run_iteration(reg, [], model="fake-model")
    assert out["status"] == "math-certified", out
    # two calls completed (one raised) -> only their tokens billed.
    assert reg.counter_get("llm_input_tokens") == 20


# -------------------------------------------------------------- tooth (iv)
def test_pregate_pass_certify_fail_logs_one_divergence(monkeypatch):
    """A winner that PASSES the pre-gate ladder but FAILS certification logs
    EXACTLY ONE speculation-divergence (predicted-pass / actual-fail), routed
    through the shared WP-E ledger.  The row is left uncovered."""
    monkeypatch.setenv(loop.MATH_FANOUT_ENV, "3")
    author = _Author([CERTIFYING, CARRIER_NARROWED, FABRICATING])
    monkeypatch.setattr("buildloop.llm.call_llm", author)
    # certification of the winner FAILS despite the pre-gate having passed it.
    monkeypatch.setattr(
        "run.formalize.certify_statement",
        lambda *a, **k: FormalizeResult(ok=False, stage="instances"))

    reg = _reg()
    reg.demand_upsert(_math_row("m-1"))
    out = loop.run_iteration(reg, [], model="fake-model")

    assert out["status"] == "math-refused", out
    assert dl.snapshot(reg).readings.get("m-1") is None
    rows = reg.events("speculation-divergence")
    assert len(rows) == 1, rows
    p = rows[0]["payload"]
    assert p["direction"] == "predicted-pass-actual-fail", p
    # the shared Z-D payload shape (identical to the service path's keys).
    assert set(p) == {"stage", "direction", "candidate_sha", "request_sha"}, p


def test_agreement_logs_no_divergence(monkeypatch):
    """When the winner's pre-gate PASS and certified PASS agree, no divergence is
    logged (Z-D: a tie/agreement is never recorded)."""
    monkeypatch.setenv(loop.MATH_FANOUT_ENV, "3")
    author = _Author([CERTIFYING, FABRICATING, CONTRADICTORY])
    monkeypatch.setattr("buildloop.llm.call_llm", author)
    monkeypatch.setattr(
        "run.formalize.certify_statement",
        lambda *a, **k: FormalizeResult(ok=True, statement_hash="beef06"))
    reg = _reg()
    reg.demand_upsert(_math_row("m-1"))
    out = loop.run_iteration(reg, [], model="fake-model")
    assert out["status"] == "math-certified", out
    assert reg.events("speculation-divergence") == []


# ---------------------------------------------------------- fanout-K helper
def test_math_fanout_k_env_parsing(monkeypatch):
    """`_math_fanout_k` degrades every non-positive / unparseable / missing value
    to 1 (the single-call path); only an explicit int > 1 fans out."""
    monkeypatch.delenv(loop.MATH_FANOUT_ENV, raising=False)
    assert loop._math_fanout_k() == 1
    for bad in ("0", "1", "-3", "", "  ", "nope", "2.5"):
        monkeypatch.setenv(loop.MATH_FANOUT_ENV, bad)
        assert loop._math_fanout_k() == 1, bad
    for good, want in (("2", 2), ("3", 3), ("7", 7)):
        monkeypatch.setenv(loop.MATH_FANOUT_ENV, good)
        assert loop._math_fanout_k() == want, good


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
