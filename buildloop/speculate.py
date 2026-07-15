"""S4 speculative synthesis executor + divergence ledger -- the LLM-free core.

Zone 3's speculation is a MEASURED TRADE, never a promised saving.  The repo's
own captures show synthesis converging in 1-3 rounds, so fanning K readings out
per round buys diversity at a real token cost that is only sometimes repaid; the
bench (`bench_speculate.py`) measures whether it paid off, this module never
asserts that it does.  The one thing speculation must NOT do is dilute the proof
obligation, so two invariants are load-bearing here:

  * Z1 (no laundering): NO speculative output is ever a certificate.  A losing
    candidate gets NO composed certificate -- `pre_gate` returns a rank record,
    not a verdict, and this module never mints a cert, never calls
    `reading_add`, never writes an artifact.  Only the real, LLM-free pipeline
    (`run/semantic.py`) issues certificates, and only for the winner it actually
    certifies end to end.
  * stage 4 is RANK-ONLY (never reject): the entailed-scenario replay orders
    survivors, it does not gate them.  A candidate that clears the three real
    pre-gates (reading-gate, consistency, compile) but strands at scenario
    replay is still a legitimate candidate -- its failure (if any) is the full
    pipeline's to find, not the speculative pre-gate's to pre-judge.

The pre-gate runs the three cheapest deterministic checks the semantic pipeline
runs, in the SAME order (cheapest first), so a candidate that cannot possibly
certify is discarded before any LLM-free proof work or cache warming is spent on
it.  `fan_out` is the ONLY function here that touches the LLM, and it is
exercised only by the LLM bench, never by CI.
"""
from __future__ import annotations

import common
from generators import reading as reading_mod
from generators import reading_compile as rc
from generators import service_model
from kernel.backends import SmtBackend

# The divergence directions a prediction miss can take (frozen as Z-D): the
# speculative pre-gate PREDICTED one outcome and the real pipeline OBSERVED the
# other.  A tie or an agreeing prediction is NOT a divergence and is not logged.
DIVERGENCE_DIRECTIONS = ("predicted-pass-actual-fail", "predicted-fail-actual-pass")

# The pre-gate stages, cheapest-first.  Only the first three can REJECT; the
# fourth (entailed-replay) is rank-only and can only ever be *reached*.
STAGES = ("reading-gate", "consistency", "compile", "entailed-replay")


def pre_gate(request: str, reading_text: str, *, macro_table=None) -> dict:
    """Run the S4.2 speculative pre-gates on one candidate Reading, cheapest
    first, and RANK it -- never certify it (Z1).

    Stages, in order (each in its own try/except so a failure is attributed to
    the stage that actually raised it):

      1. "reading-gate"    -- parse_reading (groundedness + trichotomy).  A
                              BadReading stops here with ok=False.
      2. "consistency"     -- the demand set must be satisfiable: run the quick
                              SMT obligation `demands_smt(r)` through Z3 with
                              expect="sat" under common.SMT_LOCK.  Anything but a
                              confirmed sat stops here with ok=False.
      3. "compile"         -- compile_reading: a chosen structure must entail
                              every demanded ordering.  A CompileError stops here
                              with ok=False.
      4. "entailed-replay" -- the solver-entailed scenario count, RANK ONLY.
                              This stage NEVER sets ok=False; a reading that
                              reaches it has cleared every real pre-gate, and its
                              scenario count is a ranking signal, not a verdict.

    Returns {"stage_reached": str, "ok": bool, "detail": str, "scenarios": int}.
    `ok` is True iff the candidate cleared the three rejecting pre-gates and
    reached entailed-replay; `scenarios` is 0 unless entailed-replay was reached.
    No certificate is issued and nothing is persisted (Z1)."""
    # stage 1: reading-gate -- groundedness is checked here (exact containment).
    try:
        r = reading_mod.parse_reading(reading_text, request,
                                      macro_table=macro_table)
    except reading_mod.BadReading as e:
        return {"stage_reached": "reading-gate", "ok": False,
                "detail": f"reading-gate: {e}", "scenarios": 0}
    except Exception as e:  # a malformed candidate is a reading-gate failure
        return {"stage_reached": "reading-gate", "ok": False,
                "detail": f"reading-gate: {type(e).__name__}: {e}",
                "scenarios": 0}

    # stage 2: consistency -- the demand set must be satisfiable (expect sat).
    # The z3/cvc5 bindings share process-global state, so serialize under the
    # module lock (SmtBackend also takes it internally; SMT_LOCK is re-entrant).
    try:
        smtlib = rc.demands_smt(r)
        with common.SMT_LOCK:
            v = SmtBackend().run_z3(smtlib, expect="sat")
        if v.get("result") != "pass":
            return {"stage_reached": "consistency", "ok": False,
                    "detail": f"consistency: the demand set is not "
                              f"satisfiable ({v.get('detail', '')})",
                    "scenarios": 0}
    except Exception as e:
        return {"stage_reached": "consistency", "ok": False,
                "detail": f"consistency: {type(e).__name__}: {e}",
                "scenarios": 0}

    # stage 3: compile -- a choice may never silently override a demanded order.
    try:
        spec_text, _prov = rc.compile_reading(r)
    except rc.CompileError as e:
        return {"stage_reached": "compile", "ok": False,
                "detail": f"compile: {e}", "scenarios": 0}
    except Exception as e:
        return {"stage_reached": "compile", "ok": False,
                "detail": f"compile: {type(e).__name__}: {e}", "scenarios": 0}

    # stage 4: entailed-replay -- RANK ONLY.  We count the scenarios the demands
    # solver-entail; we NEVER turn a derivation hiccup into a rejection, because
    # this stage is a ranking signal, not a gate (⚠H10 mitigation).
    scenarios = 0
    detail = "entailed-replay: reached (rank-only)"
    try:
        model = service_model.parse_service_spec(spec_text)
        scs = rc.entailed_scenarios(model, r)
        scenarios = len(scs)
        detail = f"entailed-replay: {scenarios} solver-entailed scenario(s) " \
                 f"(rank-only, not a gate)"
    except Exception as e:
        detail = f"entailed-replay: rank-only; scenario derivation skipped " \
                 f"({type(e).__name__}: {e})"
    return {"stage_reached": "entailed-replay", "ok": True,
            "detail": detail, "scenarios": scenarios}


def rank_score(reading, macro_table=None, *, stage="entailed-replay"):
    """S4.2 RANKING KEY for one candidate reading -- the tuple speculate sorts
    survivors by: "Score = (stage reached, then the Z-F scorer)".

    Returns ``(stage_rank, planner.choices.score_reading(reading, macro_table))``:

      * ``stage_rank`` -- the index in ``STAGES`` of the pre-gate stage the
        candidate reached (0 = reading-gate ... 3 = entailed-replay); a candidate
        that cleared more pre-gates ranks further along.  Pass the
        ``stage_reached`` a prior ``pre_gate`` call returned; the default is the
        terminal entailed-replay stage (a candidate already known to have cleared
        the three rejecting pre-gates).  An unknown stage maps to -1.
      * the second element is the FROZEN Z-F scorer (lower is better).  This is
        the sole scoring seam: it swaps the old flat/default score for the
        macro-aware reading DL WITH A FLAT FALLBACK -- with a `macro_table` it is
        ``score_reading``'s macro-aware DL, and with an empty/None table it falls
        back byte-for-byte to the flat reading DL (``score_reading({})`` IS the
        flat score, so the fallback is safe).

    This touches ONLY scoring: the pre_gate stage semantics and the S4.4
    divergence ledger (Z1 no-laundering, Z-D events-only) are untouched.
    Deterministic and LLM-free.  ``planner.choices`` is imported lazily so this
    module's import graph stays free of the planner (and any import cycle)."""
    from planner import choices  # lazy import: avoid an import cycle
    try:
        stage_rank = STAGES.index(stage)
    except ValueError:
        stage_rank = -1
    return (stage_rank, choices.score_reading(reading, macro_table))


def log_divergence(registry, *, stage, direction, candidate_sha, request_sha):
    """S4.4 divergence ledger -- events-table only (Z-D), touching NONE of the
    four Combined-Loop tables.  Record a PREDICTION MISS: the speculative
    pre-gate predicted one outcome for a candidate and the real pipeline observed
    the opposite.

    `direction` must be one of DIVERGENCE_DIRECTIONS.  The payload freezes the
    Z-D keys {stage, direction, candidate_sha, request_sha} so the ledger is
    queryable via `registry.events("speculation-divergence")`."""
    if direction not in DIVERGENCE_DIRECTIONS:
        raise ValueError(
            f"divergence direction {direction!r} must be one of "
            f"{DIVERGENCE_DIRECTIONS} (a prediction miss)")
    payload = {"stage": stage, "direction": direction,
               "candidate_sha": candidate_sha, "request_sha": request_sha}
    registry.log_event("speculation-divergence", payload)
    return payload


def fan_out(request: str, k: int, *, model=None, spend=None) -> list:
    """S4.1 -- author k candidate Readings for one request, one LLM call each,
    diversified by deterministic PROMPT VARIATION (`llm.call_llm` has no
    temperature knob, so diversity comes from the prompt text, not sampling).

    Contract:
      * model is None  -> return [] (LLM-free callers use `pre_gate` directly;
        this keeps CI and every deterministic path off the LLM entirely).
      * k == 1         -> exactly ONE call with today's single-call prompt
        (`service_loop.reading_prompt(request)`), so the k=1 path is
        byte-identical to the non-speculative loop's reading authoring.
      * k > 1          -> index 0 uses the base prompt; index i>0 appends a
        deterministic "(variation i ...)" suffix, so each call explores a
        different-but-faithful reading of the SAME request.
      * spend (optional) caps TOTAL tokens (input+output) across the round: once
        the running total reaches the cap no further call is made.

    Returns a list of dicts {"text","model","variation","input_tokens",
    "output_tokens"}.  This function is the ONLY LLM touchpoint in this module
    and is exercised solely by the LLM bench (`bench_speculate.py`), never CI.
    No candidate returned here is a certificate (Z1); ranking/certification is
    the caller's job via `pre_gate` and the real pipeline."""
    if model is None:
        return []
    # Deferred imports: keep the deterministic core (and its import graph)
    # LLM-free; only fan_out, an LLM-bench-only entry point, pulls these in.
    from buildloop import llm, service_loop
    base = service_loop.reading_prompt(request)
    out, spent = [], 0
    for i in range(int(k)):
        if spend is not None and spent >= spend:
            break
        prompt = base if i == 0 else (
            base + f"\n\n(variation {i}: author a DIFFERENT but equally "
                   f"faithful reading of the same request -- a distinct choice "
                   f"of lifecycle/decomposition, never a different demand.)")
        resp = llm.call_llm(prompt, model=model)
        spent += resp.get("input_tokens", 0) + resp.get("output_tokens", 0)
        out.append({"text": resp["text"], "model": resp.get("model", model),
                    "variation": i,
                    "input_tokens": resp.get("input_tokens", 0),
                    "output_tokens": resp.get("output_tokens", 0)})
    return out
