"""Parity teeth for the algebra shadow channel (the S4b-readiness gap:
agreement must mean "the probe asserts the RIGHT proposition", not merely
"the probe elaborated").

The differential records agreement when a probe elaborates -- but a probe
that quietly asserted a DIFFERENT (true) proposition would accumulate
agreement rows that mean nothing.  These teeth close that hole from two
sides, exactly as the quoter-parity file does for the reflection channel:

  * ROUND-TRIP: the proposition text is read back OUT of the probe the
    builder emitted, by an independent slicing here, and compared -- modulo
    whitespace -- against the proposition the compiler emits for the reading
    behind the queue row's ``subject``, whose sha256 is the queue's own
    pinned ``subject.sha256``.  The chain therefore closes on the committed
    hash, not on a re-run of the builder's own code.
  * PLANTED PERTURBATION: mutating the proposition (or the emitted probe)
    must make the round-trip FAIL -- proving the parity check has teeth,
    not just luck.

LLM-free, Lean-free, deterministic.
"""
import hashlib
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.math_compile import compile_math_reading
from run.anchor import _load_reading
from run import algebra_shadow

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _norm(text: str) -> str:
    """Whitespace-normalized proposition text (there is no AST on this
    route -- the probe carries the compiler's own rendered prop -- so string
    normalization is the parity currency, and it is deliberately blind to
    layout ONLY)."""
    return " ".join(text.split())


def prop_of_probe(lean: str) -> str:
    """The proposition the probe actually asserts, sliced back out of the
    emitted text by an INDEPENDENT reader (the builder's own regex is not
    reused; a shared slicer would agree with itself by construction)."""
    head, body = lean.split("example : ", 1)
    prop, tail = body.rsplit(" := by ", 1)
    assert tail.strip() == algebra_shadow.TACTIC, tail
    return prop


def _committed_prop(goal):
    """The proposition for a queue row, recomputed from the committed
    reading -- and pinned by re-deriving the queue's own subject hash."""
    readings = algebra_shadow.bench_readings(ROOT)
    reading = _load_reading(json.loads(readings[goal["subject"]["ref"]]),
                            goal["subject"]["ref"])
    lean_text = compile_math_reading(reading)["lean_text"]
    prop = lean_text.split(" : ", 1)[1].rsplit(" := sorry", 1)[0]
    return prop, lean_text


def _probe_rows():
    rep = algebra_shadow.run_shadow(ROOT)
    goals = {g["subject"]["ref"]: g
             for g in algebra_shadow.load_queue(ROOT)["goals"]}
    return [(goals[r["source"]], r)
            for r in rep["rows"] if r["status"] == "probe"]


def test_every_probe_asserts_the_committed_proposition():
    rows = _probe_rows()
    assert len(rows) >= 8, len(rows)
    for goal, r in rows:
        prop, lean_text = _committed_prop(goal)
        assert _norm(prop_of_probe(r["lean"])) == _norm(prop), goal["goal_id"]
        # and the proposition IS the goal the queue pins, by hash.
        assert hashlib.sha256(lean_text.encode()).hexdigest() \
            == goal["subject"]["sha256"] == r["statement_hash"]


def test_parity_is_blind_to_layout_only():
    # the normalization is whitespace-only: respacing the proposition keeps
    # parity (formatting churn cannot red this file), while any token change
    # survives normalization and reds it.
    goal, r = _probe_rows()[0]
    prop, _ = _committed_prop(goal)
    respaced = r["lean"].replace(prop, prop.replace(" ", "   "))
    assert respaced != r["lean"]
    assert _norm(prop_of_probe(respaced)) == _norm(prop)
    assert _norm("  a  +\n b ") == _norm("a + b")
    assert _norm("a + b") != _norm("a - b")


def test_planted_prop_perturbation_fails_parity(monkeypatch):
    # PLANT 1: the builder emits a proposition one token off.  Parity must
    # catch it -- otherwise this file is decoration, not a tooth.
    goal = _probe_rows()[0][0]
    prop, _ = _committed_prop(goal)
    good = algebra_shadow.algebra_probe(goal, root=ROOT)
    assert _norm(prop_of_probe(good["lean"])) == _norm(prop)

    real = algebra_shadow._prop_of

    def perturbed(reading):
        p, h = real(reading)
        return "(0 = 0)", h            # a TRUE but different proposition

    monkeypatch.setattr(algebra_shadow, "_prop_of", perturbed)
    bad = algebra_shadow.algebra_probe(goal, root=ROOT)
    assert bad["status"] == "probe"
    assert _norm(prop_of_probe(bad["lean"])) != _norm(prop)


def test_planted_operator_swap_fails_parity():
    # PLANT 2: a subtler mutation -- one operator swapped inside the emitted
    # probe text, layout untouched.  Whitespace normalization must NOT
    # absorb it.
    for goal, r in _probe_rows():
        prop, _ = _committed_prop(goal)
        if " + " not in prop:
            continue
        tampered = r["lean"].replace(" + ", " - ", 1)
        assert _norm(prop_of_probe(tampered)) != _norm(prop), goal["goal_id"]
        return
    pytest.fail("no committed probe carries a '+' to perturb")


def test_planted_hash_reaim_fails_parity():
    # PLANT 3: a probe re-aimed at ANOTHER queued goal's proposition -- the
    # most dangerous silent failure, since the re-aimed probe is perfectly
    # well-formed and may well elaborate.  Both parity legs must red: the
    # text against the row's own committed prop, and the hash chain.
    rows = _probe_rows()
    (g0, r0), (g1, _r1) = rows[0], rows[1]
    prop0, lean0 = _committed_prop(g0)
    prop1, lean1 = _committed_prop(g1)
    assert _norm(prop0) != _norm(prop1)
    reaimed = r0["lean"].replace(prop0, prop1)
    assert _norm(prop_of_probe(reaimed)) != _norm(prop0)
    assert hashlib.sha256(lean1.encode()).hexdigest() \
        != g0["subject"]["sha256"]
