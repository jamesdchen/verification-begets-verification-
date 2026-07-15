#!/usr/bin/env python3
"""WP-E demo (F-INT-5): LLM-free planted speculative fan-out for MathReadings.

REQUIRES_LLM = False   # first line after the docstring (the --full glob reads it)

K=4 planted candidate MathReadings for ONE source sentence, each killed at its
OWN rung of the cheapest-first Lean-free ladder, exactly one certified:

    [0] certifying     -> clears every rung; reached entailed-instance-replay
                          with replay_ok=True.  THE WINNER: certify_statement
                          returns ok=True (statement_cert deferred, Lean absent).
    [1] fabricating    -> a demanded conclusion whose quote is NOT in the source
                          dies at the PARSE gate (groundedness) -- and, because
                          the ladder is cheapest-first, spends ZERO SMT calls.
    [2] contradictory  -> two grounded but jointly-unsatisfiable presupposition
                          hypotheses die at MATH-SMT (dual-solver non-vacuity;
                          the dual-solver degrades honestly when cvc5 is absent,
                          the enumeration channel still refuses).
    [3] carrier-narrow -> ⚠FI-6: DECLARED OBJECT TYPES (Nat, not the ambient)
                          decide truncated subtraction.  It CLEARS parse + smt +
                          compile and REACHES entailed-instance-replay -- stage 4
                          is RANK-ONLY and never rejects -- but its replay is
                          refuted (a=0,b=1: (0-1)+1 = 1 over truncated Nat.sub),
                          so it REORDERS below the certifying candidate and never
                          becomes the winner.  The full pipeline is what rejects
                          it (certify_statement refuses at `instances`), and the
                          gap between the speculated PASS and the certified FAIL
                          is logged as one `speculation-divergence` event.

Losers get NO composed certificate (Z1).  Deterministic: no LLM, no Lean, no
clocks in any verdict; the same run prints the same bytes.
"""
REQUIRES_LLM = False

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from buildloop import speculate
from kernel.certs import Certificate
from library import Registry


# --------------------------------------------------------------------------- #
def _ensure_cvc5_degrades() -> bool:
    """cvc5 may be WHOLLY absent in a thin environment (CI installs it).  The
    SmtBackend imports cvc5 OUTSIDE its try, so `run_cvc5` would RAISE rather
    than return the honest ``{"result": "error"}`` a present-but-failing solver
    yields.  When the module is genuinely unavailable, install exactly that
    honest degradation, so the dual-solver falls to the z3 + enumeration channel
    -- the documented cvc5-absent behavior (F-INT-5).  A no-op when cvc5
    imports (CI), so this NEVER weakens a dual-solver that is really present."""
    try:
        import cvc5  # noqa: F401
        return False
    except Exception:
        from kernel.backends import SmtBackend

        def _degraded(self, smtlib, timeout_ms=15000, expect="unsat"):
            return {"backend": "cvc5", "result": "error",
                    "detail": "cvc5 module absent (honest dual-solver "
                              "degradation to z3 + enumeration)"}

        SmtBackend.run_cvc5 = _degraded
        return True


# --------------------------------------------------------------------------- #
# ONE source sentence; the K=4 planted readings are distinct construals OF IT.
SOURCE = ("For all integers a and b, if b is positive and b is at most zero, "
          "then a minus b plus b equals a.")
CONCL_QUOTE = "a minus b plus b equals a"


def _obj(sid, name, ty):                 # a declared object referent (a choice)
    return {"id": sid, "force": "choice", "quote": "",
            "lf": {"kind": "object", "name": name, "type": ty}}


def _concl(sid, pred, quote):            # the demanded, quote-grounded content
    return {"id": sid, "force": "demand", "quote": quote,
            "lf": {"kind": "conclusion", "pred": pred}}


def _hyp(sid, pred, quote):              # a quote-grounded presupposition
    return {"id": sid, "force": "presupposition", "quote": quote,
            "lf": {"kind": "hypothesis", "pred": pred}}


def _ap(op, *args):
    return {"op": op, "args": list(args)}


def _ref(n):
    return {"ref": n}


def _lit(v):
    return {"lit": v}


# `(a - b) + b = a` -- true over Int, FALSE over truncated Nat (the ⚠FI-6 core).
_SUB_ADD = _ap("=", _ap("+", _ap("-", _ref("a"), _ref("b")), _ref("b")),
               _ref("a"))


def _candidates() -> list:
    """The K=4 planted readings, in fan-out order (index == variation)."""
    return [
        # [0] certifying: Int object types -> real subtraction -> conclusion holds.
        ("certifying", {"theorem": "sub_add_cancel", "statements": [
            _obj("o_a", "a", "Int"), _obj("o_b", "b", "Int"),
            _concl("c", _SUB_ADD, CONCL_QUOTE)]}),
        # [1] fabricating: a demanded conclusion whose quote is NOT in the source.
        ("fabricating", {"theorem": "sub_add_cancel", "statements": [
            _obj("o_a", "a", "Int"), _obj("o_b", "b", "Int"),
            _concl("c", _ap("=", _ap("+", _ref("a"), _ref("b")), _lit(0)),
                   "a plus b equals zero")]}),
        # [2] contradictory: 0 < b  AND  b <= 0 -- jointly unsatisfiable hyps.
        ("contradictory", {"theorem": "sub_add_cancel", "statements": [
            _obj("o_a", "a", "Int"), _obj("o_b", "b", "Int"),
            _hyp("h1", _ap("<", _lit(0), _ref("b")), "b is positive"),
            _hyp("h2", _ap("<=", _ref("b"), _lit(0)), "b is at most zero"),
            _concl("c", _SUB_ADD, CONCL_QUOTE)]}),
        # [3] carrier-narrowed VIA OBJECT TYPES (⚠FI-6): Nat -> truncated Nat.sub.
        ("carrier-narrowed", {"theorem": "sub_add_cancel", "statements": [
            _obj("o_a", "a", "Nat"), _obj("o_b", "b", "Nat"),
            _concl("c", _SUB_ADD, CONCL_QUOTE)]}),
    ]


def _planted_author(labelled):
    """An injectable, LLM-FREE author for `fan_out_math`: it renders the real
    prompt (so the E1 macro-table seam is exercised) but returns the pre-planted
    reading for each variation index -- deterministic, no LLM, no sampling."""
    docs = [json.dumps(doc) for _label, doc in labelled]

    def author(prompt, variation):
        # The prompt IS built by render_math_reading_prompt; a real analyst would
        # read it.  The planted author asserts it saw a well-formed prompt, then
        # returns its canned reading with synthetic (labelled) token counts.
        assert "SOURCE:" in prompt and SOURCE in prompt, "prompt not rendered"
        return {"text": docs[variation], "model": "planted-llm-free",
                "input_tokens": 100, "output_tokens": 40 + variation}

    return author


# --------------------------------------------------------------------------- #
def main() -> int:
    degraded = _ensure_cvc5_degrades()
    labelled = _candidates()
    labels = [lab for lab, _ in labelled]

    reg = Registry(db_path=tempfile.mkdtemp() + "/speculate_math.sqlite")

    print("=" * 72)
    print("WP-E speculative fan-out for MathReadings (F-INT-5) -- LLM-free")
    print("=" * 72)
    print("SOURCE: " + SOURCE)
    print("dual-solver: " + ("z3 + enumeration (cvc5 absent -> honest "
                             "degradation)" if degraded
                             else "z3 + cvc5 (both present)"))
    print("ladder (cheapest-first): " + " -> ".join(speculate.MATH_STAGES))
    print()

    # ---- fan out K=4 candidate readings (injectable author; no LLM) ----------
    fan = speculate.fan_out_math(SOURCE, len(labelled), macro_table=None,
                                 author=_planted_author(labelled))
    assert len(fan) == len(labelled), fan

    # ---- pre-gate each candidate (rank, never certify -- Z1) -----------------
    results = []
    print("PRE-GATE (each candidate ranked, never certified):")
    for lab, cand in zip(labels, fan):
        res = speculate.pre_gate_math(SOURCE, cand["text"])
        results.append(res)
        mark = "reached" if res["ok"] else "KILLED "
        extra = ("" if res["replay_ok"] is None
                 else f"  replay_ok={res['replay_ok']}")
        print(f"  [{cand['variation']}] {lab:16s} {mark} @ "
              f"{res['stage_reached']:26s}{extra}")
    print()

    # ---- rank the survivors (S4: reorder, never reject) ----------------------
    survivors = [(lab, cand, res) for lab, cand, res
                 in zip(labels, fan, results) if res["ok"]]
    survivors.sort(key=lambda t: speculate.rank_score_math(t[2]))
    print("SURVIVORS ranked best-first (rank-only entailed-replay reorders "
          "the carrier-narrowed reading BELOW the clean one, never rejects it):")
    for lab, _c, res in survivors:
        print(f"  {lab:16s} replay_ok={res['replay_ok']!s:5s} "
              f"stmt_dl={res['statement_dl']}")
    print()

    winner_label, winner_cand, winner_res = survivors[0]

    # ---- certify the WINNER alone (the only composed certificate) ------------
    print(f"WINNER: {winner_label} -> certify_statement (the real pipeline):")
    wres = speculate.certify_math(SOURCE, winner_cand["text"], event_sink=None,
                                  source_id="demand:sub_add_cancel")
    wcert = "Certificate" if isinstance(wres.statement_cert, Certificate) \
        else "None (deferred: Lean toolchain absent)"
    print(f"  certified ok={wres.ok}  failing_stage={wres.stage or '(none)'}  "
          f"statement_cert={wcert}")
    print(f"  lean_text: {wres.lean_text}")
    assert wres.ok, wres
    print()

    # ---- divergence audit on the carrier-narrowed loser ----------------------
    # Its speculated verdict was PASS (rank-only stage 4 cannot reject); the real
    # pipeline REFUTES it.  That miss is the planted speculation-divergence.
    narrowed = next((lab, cand, res) for lab, cand, res
                    in zip(labels, fan, results)
                    if lab == "carrier-narrowed")
    _lab, ncand, nres = narrowed
    print("DIVERGENCE AUDIT: carrier-narrowed (speculated PASS via rank-only "
          "replay) vs the certified verdict:")
    ncertified = speculate.certify_math(SOURCE, ncand["text"], event_sink=None,
                                        source_id="demand:sub_add_cancel")
    print(f"  speculated: ok={nres['ok']} (reached "
          f"{nres['stage_reached']}, replay_ok={nres['replay_ok']})")
    print(f"  certified:  ok={ncertified.ok} (refused @ {ncertified.stage}; "
          f"{ncertified.error.split(':')[0]})")
    payload = speculate.log_math_divergence(
        reg, SOURCE, ncand["text"], nres, ncertified.ok,
        request_sha="req:sub_add_cancel")
    assert payload is not None, "the planted divergence must log"
    print(f"  -> speculation-divergence logged: direction="
          f"{payload['direction']}  stage={payload['stage']}")
    print()

    # ---- Z1: losers mint NO certificate --------------------------------------
    losers = [lab for lab, _c, res in zip(labels, fan, results)
              if not res["ok"] or lab != winner_label]
    # certify_statement is never called to COMPOSE a loser cert; the divergence
    # audit above ran the pipeline as an AUDIT and it refused (ok=False), so no
    # loser carries a certificate.  Assert the winner alone certified.
    assert not isinstance(ncertified.statement_cert, Certificate), ncertified

    div_events = reg.events("speculation-divergence")
    print("-" * 72)
    print("SUMMARY (deterministic, LLM-free, Lean-free):")
    print(f"  candidates fanned out ............ {len(fan)} (K=4)")
    print(f"  killed at parse-math-reading ..... "
          f"{sum(1 for r in results if r['stage_reached'] == 'parse-math-reading')}")
    print(f"  killed at math-smt ............... "
          f"{sum(1 for r in results if r['stage_reached'] == 'math-smt')}")
    print(f"  reached entailed-instance-replay . "
          f"{sum(1 for r in results if r['ok'])}")
    print(f"  winner (certifies, ok=True) ...... {winner_label}")
    print(f"  losers (no composed certificate) . {sorted(set(losers))}")
    print(f"  speculation-divergence events .... {len(div_events)}")
    print("-" * 72)

    assert len(div_events) == 1, div_events
    assert winner_label == "certifying", winner_label
    print("OK: one winner certified, three losers killed at their own rung, "
          "one planted speculation-divergence recorded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
