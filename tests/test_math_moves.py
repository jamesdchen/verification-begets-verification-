"""WP-A teeth for the scheduler `math` move (F-INT-1 / G1).

All LLM-free and Lean-free (house rules 5/13; the cvc5/z3 pipeline is stubbed
or bypassed where it would otherwise gate the tooth).  Every DL assertion is
RELATIONAL (E5/H52) -- no absolute constant is asserted.  MathReading fixtures
are authored INLINE here (the plan forbids touching specs/mathsources/** and
tests/fixtures_math_readings.py); the two inline readings are byte-equivalent
to the committed specs/mathsources/readings/01 and 04 (their prices are what
⚠FI-2 turns on: 01 serves at 35.0 < 50.0 -> DL drops; 04 serves at
68.0 > 50.0 -> the price gate refuses).
"""
import json
import pathlib
import tempfile

import common
from buildloop import dl, loop
from library import Registry

_ROOT = pathlib.Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- fixtures
# Inline MathReadings (bespoke, byte-equivalent to the committed corpus).
READING_01 = {                                   # dvd_reflexive; dl_reading 33.0
    "theorem": "dvd_reflexive",
    "statements": [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "on", "force": "demand", "quote": "Every integer n",
         "lf": {"kind": "object", "name": "n", "type": "Int"}},
        {"id": "q", "force": "demand", "quote": "Every integer n",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n"]}},
        {"id": "c", "force": "demand", "quote": "divides itself",
         "lf": {"kind": "conclusion",
                "pred": {"op": "dvd", "args": [{"ref": "n"}, {"ref": "n"}]}}},
    ],
}

READING_04 = {                                   # even_plus_even; dl_reading 66.0
    "theorem": "even_plus_even",
    "statements": [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "oa", "force": "presupposition", "quote": "two even integers",
         "lf": {"kind": "object", "name": "a", "type": "Int"}},
        {"id": "ob", "force": "presupposition", "quote": "two even integers",
         "lf": {"kind": "object", "name": "b", "type": "Int"}},
        {"id": "q", "force": "demand", "quote": "two even integers",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["a", "b"]}},
        {"id": "h1", "force": "presupposition", "quote": "two even integers",
         "lf": {"kind": "hypothesis", "pred": {"op": "even", "args": [{"ref": "a"}]}}},
        {"id": "h2", "force": "presupposition", "quote": "two even integers",
         "lf": {"kind": "hypothesis", "pred": {"op": "even", "args": [{"ref": "b"}]}}},
        {"id": "c", "force": "demand",
         "quote": "The sum of two even integers is even",
         "lf": {"kind": "conclusion",
                "pred": {"op": "even", "args": [
                    {"op": "+", "args": [{"ref": "a"}, {"ref": "b"}]}]}}},
    ],
}


# ------------------------------------------------------------------ helpers
def _reg():
    tmp = tempfile.mkdtemp()
    return Registry(db_path=f"{tmp}/reg.sqlite")


def _math_row(did, *, origin="exogenous", status="open", size_bytes=100,
              payload_ref=None):
    return {"demand_id": did, "kind": "math-source", "origin": origin,
            "status": status, "language": None, "features": None,
            "payload_ref": payload_ref or did, "size_bytes": size_bytes,
            "covered_via": None}


def _math_move(moves, did):
    return next((m for m in moves
                 if m["kind"] == "math" and m["demand_id"] == did), None)


def _served_price(reading):
    return dl.READING_CHAIN_COST + dl.dl_reading(reading, {})


# --------------------------------------------------------------- tooth (1)
def test_unserved_exogenous_row_proposed_and_argmax():
    """A planted unserved exogenous math row is proposed by `_math_moves` and,
    with no cheaper move present, is the argmax pick."""
    reg = _reg()
    reg.demand_upsert(_math_row("m-1"))
    snap = dl.snapshot(reg)
    moves, _log, picked = loop.score_moves(snap, reg)
    mv = _math_move(moves, "m-1")
    assert mv is not None, "math move must be generated for an unserved exo row"
    assert mv["score"] > 0
    assert picked is mv, "the only positive move must be the argmax pick"
    assert picked["candidate_key"] == "math:m-1"


# --------------------------------------------------------------- tooth (2)
def test_planted_serve_covers_row_and_lowers_ledger():
    """An injected fake dispatch that persists the (cheap) reading 01 covers the
    row and STRICTLY lowers ledger_dl (relational; 01 serves below the penalty).
    This is global acceptance item 6."""
    reg = _reg()
    reg.demand_upsert(_math_row("m-1"))
    before = dl.ledger_dl(reg)["ledger_dl"]

    def fake(move, snap, registry, backlog, policy, use_corpus, model):
        registry.reading_add(move["demand_id"],
                             common.canonical_json(READING_01), "cert-01")
        return {"status": "math-certified", "demand_id": move["demand_id"]}

    out = loop.run_iteration(reg, [], dispatch={"math": fake})
    assert out["picked"] == "math"
    after_snap = dl.snapshot(reg)
    assert after_snap.readings.get("m-1") is not None, "row must now be covered"
    after = dl.ledger_dl(reg)["ledger_dl"]
    assert after < before, "serving a cheap reading must strictly drop ledger_dl"
    # sanity on the direction the realized delta records (relational, not const).
    assert out["realized_dl_delta"] < 0


# --------------------------------------------------------------- tooth (3)
def test_price_gate_refuses_dl_raising_reading(monkeypatch):
    """The ⚠FI-2 price gate: an authored reading whose real served price is NOT
    below the penalty (reading 04) is REFUSED `dl-raising` and the row stays
    uncovered.  Exercised through the REAL `_dispatch_math` with the LLM author
    and the (cvc5-requiring) certifier stubbed -- the gate itself runs on real
    fixture-04 bytes, so nothing about the price arithmetic is faked."""
    # relational precondition: 04 prices at/above the penalty, 01 below it.
    assert _served_price(READING_04) >= dl.UNCOVERED_PENALTY > \
        _served_price(READING_01)

    from run.formalize import FormalizeResult
    monkeypatch.setattr(
        "buildloop.llm.call_llm",
        lambda prompt, model=None: {
            "text": common.canonical_json(READING_04),
            "input_tokens": 10, "output_tokens": 20, "model": "fake"})
    # certification is not under test here; stub it to a clean pass so the price
    # gate is reached without the absent cvc5 backend.
    monkeypatch.setattr(
        "run.formalize.certify_statement",
        lambda *a, **k: FormalizeResult(ok=True, statement_hash="deadbeef"))

    reg = _reg()
    reg.demand_upsert(_math_row("m-4"))
    out = loop.run_iteration(reg, [], model="fake-model")
    assert out["picked"] == "math"
    assert out["status"] == "math-refused"
    # the frozen refusal reason for the price gate.
    assert reg.events("scheduler-decision")            # decision still logged
    row_reading = dl.snapshot(reg).readings.get("m-4")
    assert row_reading is None, "a dl-raising reading must NOT be persisted"
    # the refusal is remembered (A3 counting substrate).
    refused = reg.events("math-refused")
    assert refused and refused[-1]["payload"]["demand_id"] == "m-4"


def test_price_gate_reason_is_dl_raising(monkeypatch):
    """Same path, asserting the refusal REASON is exactly `dl-raising` (the
    frozen F-INT-1 value), distinguishing it from a fidelity refusal."""
    from run.formalize import FormalizeResult
    monkeypatch.setattr(
        "buildloop.llm.call_llm",
        lambda prompt, model=None: {
            "text": common.canonical_json(READING_04),
            "input_tokens": 1, "output_tokens": 1, "model": "fake"})
    monkeypatch.setattr(
        "run.formalize.certify_statement",
        lambda *a, **k: FormalizeResult(ok=True, statement_hash="cafef00d"))
    reg = _reg()
    reg.demand_upsert(_math_row("m-4"))
    move = {"kind": "math", "candidate_key": "math:m-4", "demand_id": "m-4",
            "row": reg.demand_get("m-4"), "score": 30.0}
    res = loop._dispatch_math(move, dl.snapshot(reg), reg, [], "frequency",
                              False, "fake-model")
    assert res["status"] == "math-refused"
    assert res["reason"] == "dl-raising"


# --------------------------------------------------------------- tooth (4)
def test_dream_rows_generate_no_move():
    """A system-origin (dream) math row prices at 0 in dl.py and MUST NOT
    generate a move (E3)."""
    reg = _reg()
    reg.demand_upsert(_math_row("dream-1", origin="system"))
    snap = dl.snapshot(reg)
    moves, _log, _picked = loop.score_moves(snap, reg)
    assert _math_move(moves, "dream-1") is None
    assert not any(m["kind"] == "math" for m in moves)


def test_retired_row_generates_no_move():
    reg = _reg()
    reg.demand_upsert(_math_row("m-r", status="retired"))
    moves, _l, _p = loop.score_moves(dl.snapshot(reg), reg)
    assert _math_move(moves, "m-r") is None


def test_covered_row_generates_no_move():
    reg = _reg()
    reg.demand_upsert(_math_row("m-c"))
    reg.reading_add("m-c", common.canonical_json(READING_01), "cert-01")
    moves, _l, _p = loop.score_moves(dl.snapshot(reg), reg)
    assert _math_move(moves, "m-c") is None


# --------------------------------------------------------------- tooth (5)
def test_byte_identity_zero_math_rows():
    """On a registry with zero math-source rows, score_moves output is
    byte-identical to the golden captured from the pre-swarm base BEFORE any
    loop.py edit (⚠FI-11)."""
    golden = json.loads(
        (_ROOT / "tests" / "golden" / "wpa_score_moves_golden.json").read_text())
    reg = _build_golden_registry()
    snap = dl.snapshot(reg)
    assert not any(r["kind"] == "math-source" for r in snap.demand)
    moves, log_moves, picked = loop.score_moves(snap, reg)
    got = {
        "log_moves": log_moves,
        "picked_kind": picked["kind"] if picked else None,
        "picked_key": picked["candidate_key"] if picked else None,
        "move_scores": {m["candidate_key"]: round(m["score"], 6)
                        for m in moves},
        "kinds_present": sorted({m["kind"] for m in moves}),
    }
    assert common.canonical_json(got) == common.canonical_json(golden)
    assert "math" not in got["kinds_present"]


def _build_golden_registry():
    """The exact registry the pre-edit golden was captured over (every EXISTING
    move kind, zero math rows)."""
    def bnd(a, l, c, r):
        return {"kind": "bound", "action": a, "left": l, "cmp": c, "right": r}

    def stmt(sid, lf, f="demand", q="span"):
        return {"id": sid, "force": f, "quote": q, "lf": lf}

    def tbr(r1, r2):
        return common.canonical_json({"service": "shop", "statements": [
            stmt("s1", bnd("sell", "n", "<=", r1)),
            stmt("s2", bnd("buy", "m", ">=", r2))]})

    def spec(did, atoms):
        return {"demand_id": did, "kind": "spec-file", "origin": "exogenous",
                "status": "open", "language": "ksy", "features": sorted(atoms),
                "payload_ref": did, "size_bytes": 64, "covered_via": None}

    reg = _reg()
    for i in range(3):
        reg.reading_add(f"req-{i}", tbr(5, 1), f"cert-{i}")
    reg.demand_upsert(spec("spec-a", ["uint:1", "uint:2"]))
    reg.demand_upsert(spec("spec-b", ["uint:1", "uint:2"]))
    reg.demand_upsert({"demand_id": "nl-1", "kind": "nl-request",
                       "origin": "exogenous", "status": "open",
                       "language": None, "features": None,
                       "payload_ref": "nl-1", "size_bytes": 40,
                       "covered_via": None})
    row = {"demand_id": "world-machine", "kind": "caged-incumbent",
           "origin": "exogenous", "status": "open", "language": None,
           "features": None, "payload_ref": "world-machine",
           "size_bytes": 500, "covered_via": None}
    reg.demand_upsert(row)
    reg.counter_add(f"toll:{dl.incumbent_hash_of(row)}:calls", 800.0)
    return reg


# --------------------------------------------------------------- tooth (6)
def test_two_failed_attempts_suppress_third(monkeypatch):
    """A3 mark-don't-omit: two `math-refused` attempts, then the third iteration
    STILL proposes the move (visible in log_moves and the miss log) but marks it
    `suppressed_by` and never picks it."""
    reg = _reg()
    reg.demand_upsert(_math_row("m-1"))

    def refuse(move, snap, registry, backlog, policy, use_corpus, model):
        return {"status": "math-refused", "demand_id": move["demand_id"],
                "reason": "nonvacuity", "stage": "nonvacuity"}

    # attempt 1: proposed, picked, refused (0 prior events).
    o1 = loop.run_iteration(reg, [], dispatch={"math": refuse})
    assert o1["picked"] == "math"
    # attempt 2: still proposed and picked (1 prior event < MATH_MAX_ATTEMPTS).
    o2 = loop.run_iteration(reg, [], dispatch={"math": refuse})
    assert o2["picked"] == "math"
    assert len(reg.events("math-refused")) == loop.MATH_MAX_ATTEMPTS

    # attempt 3: proposed but suppressed, NEVER picked.
    snap = dl.snapshot(reg)
    moves, log_moves, picked = loop.score_moves(snap, reg)
    mv = _math_move(moves, "m-1")
    assert mv is not None, "mark-don't-omit: the move must still be generated"
    assert "suppressed_by" in mv, "after MATH_MAX_ATTEMPTS it must be suppressed"
    assert picked is None or picked.get("demand_id") != "m-1"
    log = next(l for l in log_moves if l["candidate_key"] == "math:m-1")
    assert "suppressed_by" in log and log["picked"] is False

    # it stays ledger-priced and visible in the miss log (still-priced miss).
    o3 = loop.run_iteration(reg, [], dispatch={"math": refuse})
    assert o3["picked"] != "math"
    assert reg.events("math-miss"), "suppressed math miss must still be recorded"
    assert reg.events("math-miss")[-1]["payload"]["suppressed"] is True
