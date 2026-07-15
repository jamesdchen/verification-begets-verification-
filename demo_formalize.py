#!/usr/bin/env python3
"""The statement-fidelity path: autoformalization with teeth.

Proof checking verifies proof-vs-statement.  NOTHING in a bare proof pipeline
verifies statement-vs-text -- the classic silent failure of autoformalization is
the statement that compiles, proves, and MEANS NOTHING (the omitted side
condition, the fabricated hypothesis, the silently-narrowed carrier).  This demo
builds that missing layer and shows it catching five distinct kinds of
misformalization, each at its OWN stage.

Part A -- a hand-written MathReading of a mathematical sentence goes down the
deterministic pipeline (run/formalize.py): groundedness gate, dual-solver
non-vacuity, compositional compile to a Lean `theorem ... := sorry` with
per-element provenance, entailed-instance replay, and the source-blind examiner.
The provenance chain is printed: quoted span -> speech-act force -> logical form
-> Lean term.

Part B -- five teeth, each a distinct kind of misreading:
  T1 a FABRICATED conclusion (quote not in the source)   -> math-reading-gate
  T2 CONTRADICTORY hypotheses (5<n and n<3)              -> nonvacuity
     (dual-solver unsat, enumeration-corroborated)
  T3 a WRONG operator binding (a|b construed as b|a)     -> instances
     (the smallest witness a=2,b=4 refutes: 2|4 holds, 4|2 fails)
  T4 a SILENTLY NARROWED carrier (a-b+b=a stated over Nat where the text says
     the integers -- N-truncation flips an instance)     -> instances
  T5 an OMITTED PRESUPPOSITION -- the honest one: the analyst drops "n positive"
     from "for positive n, n divides n*k".  The weakened statement `n | n*k` is
     STILL TRUE for every n (including n=0, since 0 | 0), so every fidelity gate
     PASSES and it certifies.  It means less than intended, and ONLY the
     examiner's expectation about what the sentence MEANS ("n=0 is outside the
     claim") catches the gap.  Fidelity to the written formalization and coverage
     of the unwritten meaning are DIFFERENT properties -- this tooth is why the
     examiner channel exists.

LLM-free (the teeth are hand-written, exactly the demo_reading.py Part-B idiom).
Every fidelity gate is decidable arithmetic over the F-G fragment, so the teeth
are caught WITHOUT a Lean toolchain; the F0 kernel statement-cert is the
stronger, deferred layer (recorded honestly as `deferred: lean toolchain absent`,
never a pipeline failure and never a false green).
"""
from __future__ import annotations

import json
import sys

from run.formalize import certify_statement

REQUIRES_LLM = False
REQUIRES_LEAN = False        # teeth are caught via Lean-free channels; the F0
                             # kernel cert is deferred, never required here.


def _mk(theorem, statements):
    return json.dumps({"theorem": theorem, "statements": statements})


# --- Part A: a valid formalization, end to end, with provenance --------------
A_SOURCE = ("for every positive n and every k, n divides the product n times k")
A_READING = _mk("dvd_self_mul", [
    {"id": "amb", "force": "choice", "quote": "",
     "lf": {"kind": "ambient", "carrier": "Int"}},
    {"id": "on", "force": "demand", "quote": "every positive n",
     "lf": {"kind": "object", "name": "n", "type": "Int"}},
    {"id": "ok", "force": "demand", "quote": "every k",
     "lf": {"kind": "object", "name": "k", "type": "Int"}},
    {"id": "q", "force": "demand", "quote": "for every positive n and every k",
     "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n", "k"]}},
    {"id": "h", "force": "presupposition", "quote": "positive n",
     "lf": {"kind": "hypothesis",
            "pred": {"op": "<", "args": [{"lit": 0}, {"ref": "n"}]}}},
    {"id": "c", "force": "demand", "quote": "n divides the product n times k",
     "lf": {"kind": "conclusion",
            "pred": {"op": "dvd", "args": [
                {"ref": "n"},
                {"op": "*", "args": [{"ref": "n"}, {"ref": "k"}]}]}}},
])


def part_a():
    print("== Part A: MathReading -> certified statement, with provenance ==")
    stmts = {s["id"]: s for s in json.loads(A_READING)["statements"]}
    r = certify_statement(A_SOURCE, A_READING)
    for name, ok, ch in r.layers:
        mark = "OK" if ok else ("--" if ok is None else "XX")
        print(f"  {mark} {name:<20} {ch}")
    print(f"  fidelity certified: {r.ok}   "
          f"statement-cert: {'issued' if r.statement_cert else 'deferred (lean absent)'}")
    print(f"  compiled Lean statement:\n    {r.lean_text}")
    print("  provenance chain (Lean element <- statements <- quotes):")
    for element, sids in sorted(r.provenance.items()):
        srcs = "; ".join(
            f"{sid}[{stmts[sid]['force']}]"
            + (f" {stmts[sid]['quote']!r}" if stmts[sid].get("quote") else "")
            for sid in sids if sid in stmts)
        print(f"    {element:<22} <- {srcs}")
    return r.ok


# --- Part B: five teeth, five distinct catches -------------------------------
def part_b():
    print("\n== Part B: five kinds of misformalization, five distinct catches ==")
    ok = []

    # T1: a fabricated conclusion (quote not in the source).
    doc = json.loads(A_READING)
    doc["statements"][-1]["quote"] = "n is prime"
    r = certify_statement(A_SOURCE, _mk("t1", doc["statements"]))
    print(f"  T1 fabricated conclusion  caught={not r.ok} stage={r.stage!r}")
    print(f"     {r.error[:100]}")
    ok.append(not r.ok and r.stage == "math-reading-gate")

    # T2: contradictory hypotheses (5 < n and n < 3).
    src2 = "for every n greater than five and less than three, n is even"
    t2 = _mk("t2", [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "o", "force": "demand", "quote": "every n",
         "lf": {"kind": "object", "name": "n", "type": "Int"}},
        {"id": "q", "force": "demand", "quote": "for every n",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["n"]}},
        {"id": "h1", "force": "presupposition", "quote": "greater than five",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "<", "args": [{"lit": 5}, {"ref": "n"}]}}},
        {"id": "h2", "force": "presupposition", "quote": "less than three",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "<", "args": [{"ref": "n"}, {"lit": 3}]}}},
        {"id": "c", "force": "demand", "quote": "n is even",
         "lf": {"kind": "conclusion",
                "pred": {"op": "even", "args": [{"ref": "n"}]}}},
    ])
    r = certify_statement(src2, t2)
    print(f"  T2 contradictory hyps     caught={not r.ok} stage={r.stage!r}")
    ok.append(not r.ok and r.stage == "nonvacuity")

    # T3: wrong operator binding -- source says "a divides b", reading binds b|a.
    src3 = "for all a and b, if a divides b then a divides b"
    t3 = _mk("t3", [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        {"id": "oa", "force": "demand", "quote": "all a",
         "lf": {"kind": "object", "name": "a", "type": "Int"}},
        {"id": "ob", "force": "demand", "quote": "b",
         "lf": {"kind": "object", "name": "b", "type": "Int"}},
        {"id": "q", "force": "demand", "quote": "for all a and b",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["a", "b"]}},
        {"id": "h", "force": "presupposition", "quote": "a divides b",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "dvd", "args": [{"ref": "a"}, {"ref": "b"}]}}},
        {"id": "c", "force": "demand", "quote": "a divides b",   # bound WRONG:
         "lf": {"kind": "conclusion",                            # b | a
                "pred": {"op": "dvd", "args": [{"ref": "b"}, {"ref": "a"}]}}},
    ])
    r = certify_statement(src3, t3)
    print(f"  T3 wrong operator binding caught={not r.ok} stage={r.stage!r}")
    print(f"     {r.error[:100]}")
    ok.append(not r.ok and r.stage == "instances")

    # T4: silently narrowed carrier -- "a - b + b = a" over the integers, but the
    # reading declares the objects `: Nat`; N-truncation (1-3=0) flips an instance.
    src4 = "for all integers a and b, a minus b plus b equals a"
    t4 = _mk("t4", [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Nat"}},          # narrowed!
        {"id": "oa", "force": "demand", "quote": "integers a",
         "lf": {"kind": "object", "name": "a", "type": "Nat"}},
        {"id": "ob", "force": "demand", "quote": "b",
         "lf": {"kind": "object", "name": "b", "type": "Nat"}},
        {"id": "q", "force": "demand", "quote": "for all integers a and b",
         "lf": {"kind": "quantifier", "binder": "forall", "objects": ["a", "b"]}},
        {"id": "c", "force": "demand", "quote": "a minus b plus b equals a",
         "lf": {"kind": "conclusion", "pred": {"op": "=", "args": [
             {"op": "+", "args": [
                 {"op": "-", "args": [{"ref": "a"}, {"ref": "b"}]},
                 {"ref": "b"}]},
             {"ref": "a"}]}}},
    ])
    r = certify_statement(src4, t4)
    print(f"  T4 narrowed carrier (N/Z) caught={not r.ok} stage={r.stage!r}")
    print(f"     {r.error[:100]}")
    ok.append(not r.ok and r.stage == "instances")

    # T5: the omitted presupposition -- the honest one.  Drop "0 < n" from
    # "for positive n, n divides n*k".  `n | n*k` is TRUE for every n (0 | 0),
    # so every fidelity gate PASSES and the statement certifies.  Only the
    # examiner's expectation about the MEANING ("n=0 is outside the claim")
    # catches the gap.
    doc5 = json.loads(A_READING)
    doc5["statements"] = [s for s in doc5["statements"] if s["id"] != "h"]
    expectations = json.dumps({"expectations": [
        {"kind": "positive", "assignment": {"n": 3, "k": 2}, "expect": "holds",
         "why": "3 divides 3*2 = 6"},
        {"kind": "boundary", "assignment": {"n": 0, "k": 5}, "expect": "outside",
         "why": "n = 0 is not positive; outside the intended claim"},
    ]})
    r = certify_statement(A_SOURCE, _mk("t5", doc5["statements"]),
                          expectations_json=expectations)
    caught = r.ok and not r.examiner.get("converged")
    print(f"  T5 omitted presupposition: fidelity certifies={r.ok} "
          f"(every gate green -- the honest gap)")
    print(f"     examiner catches the meaning gap: {caught}")
    for d in r.examiner.get("diverged", []):
        print(f"     witness: at {d['assignment']} the statement HOLDS "
              f"(conclusion_holds={d['conclusion_holds']}) but the source MEANS "
              f"this point is {d['expect']!r} -- {d['why']}")
    print("     -> fidelity to the written formalization and coverage of the "
          "unwritten meaning are DIFFERENT properties.")
    ok.append(caught)

    return all(ok)


# --- Part C: the fidelity-gate cache (F-INT-2), only with --cache ------------
def part_c_cache():
    """Exercise WP-C's Lean-free fidelity-gate side-store (F-INT-2).

    The store memoizes the stage-2 non-vacuity and stage-4 instance-replay
    gates keyed on (reading, bound).  With ``CGB_DB`` unset -- this demo -- the
    store is an in-process dict, so a re-certification of the SAME reading is
    served WITHOUT re-running any solver.  cvc5 is absent in this container, so
    the honest witness of "no work" is the z3 call count (F-INT-2: count z3
    calls).  A cache HIT appends a ``('cache', 'hit')`` marker to the gate's
    layer detail; every other FormalizeResult field is byte-identical to the
    cold (miss) run."""
    import run.formalize as F
    from kernel.backends import SmtBackend

    print("\n== Part C: the Lean-free fidelity-gate cache (F-INT-2, --cache) ==")
    F._formalize_cache_clear()                    # start cold (in-process store)

    calls = {"z3": 0}
    real_z3 = SmtBackend.run_z3

    def _counting_z3(self, *a, **k):
        calls["z3"] += 1
        return real_z3(self, *a, **k)

    SmtBackend.run_z3 = _counting_z3
    try:
        r_cold = certify_statement(A_SOURCE, A_READING)       # miss: solver runs
        cold = calls["z3"]
        r_warm = certify_statement(A_SOURCE, A_READING)       # hit: no solver
        warm = calls["z3"] - cold
    finally:
        SmtBackend.run_z3 = real_z3

    nv_cold = next(ch for name, _ok, ch in r_cold.layers if name == "nonvacuity")
    nv_warm = next(ch for name, _ok, ch in r_warm.layers if name == "nonvacuity")
    hit = ("cache", "hit") in [tuple(c) for c in nv_warm]
    print(f"  cold nonvacuity channels: {nv_cold}")
    print(f"  warm nonvacuity channels: {nv_warm}")
    print(f"  z3 solver calls: cold={cold} warm={warm}  "
          f"(the warm run is served entirely from the side-store)")
    # The two verdicts are byte-identical except the honesty marker: strip it.
    warm_stripped = [tuple(c) for c in nv_warm if tuple(c) != ("cache", "hit")]
    cold_pairs = [tuple(c) for c in nv_cold]
    same = warm_stripped == cold_pairs and r_cold.statement_hash == \
        r_warm.statement_hash
    print(f"  cache-hit marker present: {hit}   zero warm solver calls: "
          f"{warm == 0}   verdict byte-identical except marker: {same}")
    return hit and warm == 0 and same


if __name__ == "__main__":
    use_cache = "--cache" in sys.argv[1:]
    a = part_a()
    b = part_b()
    print("\nsummary:", json.dumps({"part_a_certified": a,
                                    "part_b_all_teeth": b}))
    if not REQUIRES_LEAN:
        print("note: the F0 kernel statement-cert is DEFERRED (no Lean toolchain "
              "in this container); every tooth above is caught by the Lean-free "
              "statement-fidelity gates -- the layer this plan exists to add.")
    # The cache is OFF by default: each reading above is certified exactly once,
    # so no hit occurs and the default stdout is byte-identical to the golden.
    c = part_c_cache() if use_cache else True
    sys.exit(0 if (a and b and c) else 1)
