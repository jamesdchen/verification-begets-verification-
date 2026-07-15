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

import json

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


# =========================================================================== #
# F-INT-5 -- the MATH speculative pre-gate ladder (WP-E, closes G5).
#
# The mathematical analogue of `pre_gate`/`fan_out` above, and deliberately
# built on the SAME two load-bearing invariants (Z1 no-laundering; stage 4 is
# RANK-ONLY, never a rejection).  It SHARES the ledger plumbing -- divergences
# route through the one `log_divergence` above and carry the identical Z-D
# payload shape -- and it does NOT touch the service ladder, so every existing
# speculation fixture is byte-unchanged.
#
# Cheapest-first, all Lean-free (F-INT-5):
#     1. "parse-math-reading"          parse_math_reading (groundedness gate).
#                                      Catches FABRICATION.               [exact]
#     2. "math-smt"                    hypothesis-set satisfiability via the
#                                      SHARED dual-solver non-vacuity check
#                                      (`run.formalize._nonvacuity`, T4 split);
#                                      cvc5 absent -> the enumeration channel
#                                      still decides.  Catches CONTRADICTORY
#                                      hypotheses.                      [proved]
#     3. "compile-math"                compile_math_reading + validate_lean
#                                      escape gate (defense in depth). [checked]
#     4. "entailed-instance-replay"    the k smallest hypothesis-satisfying
#                                      instances, replayed against the compiled
#                                      statement -- RANK ONLY, never a rejection
#                                      (the S4 discipline verbatim).  A refuting
#                                      instance REORDERS the candidate below a
#                                      clean one; the full pipeline is what
#                                      rejects it.  Catches WRONG BINDING /
#                                      SILENT CARRIER NARROWING as a rank signal.
#
# Only the first three rungs can REJECT (ok=False); the fourth only ever sets
# the rank-only `replay_ok` flag.  Nothing here mints a certificate (Z1); the
# ONLY certificate-issuing call in this module's math path is the ground-truth
# `certify_math` below, which is the REAL pipeline the speculation is measured
# against -- exactly as the service pre_gate is measured against run/semantic.

MATH_STAGES = ("parse-math-reading", "math-smt", "compile-math",
               "entailed-instance-replay")


def pre_gate_math(source_text: str, math_reading_json: str, *, bound: int = 8,
                  event_sink=None) -> dict:
    """Run the F-INT-5 math speculative pre-gates on one candidate MathReading,
    cheapest first, and RANK it -- never certify it (Z1).

    Returns ``{"stage_reached", "ok", "detail", "replay_ok", "n_instances",
    "statement_hash", "statement_dl"}``.  ``ok`` is True iff the candidate
    cleared the three rejecting pre-gates and REACHED entailed-instance-replay;
    ``replay_ok`` is the rank-only signal (True = every entailed instance makes
    the conclusion hold, False = some instance refutes it, None = not reached or
    replay skipped).  No certificate is issued and nothing is persisted (Z1).

    ``event_sink`` is None during speculation by design: the shared non-vacuity
    check would otherwise emit pipeline events (mirror-divergence) from a
    RANKING pass, which is not a certification -- speculation stays side-effect
    free apart from the caller's own `log_divergence`."""
    # Deferred imports: keep the deterministic SERVICE core's import graph
    # unchanged (and free of any cycle); the math path pulls these in lazily.
    from generators.math_reading import parse_math_reading, BadMathReading
    from generators.math_compile import compile_math_reading, CompileError
    from generators import math_eval
    from buildloop.validate_lean import validate_lean
    from run import formalize as _formalize

    def _rej(stage, detail):
        return {"stage_reached": stage, "ok": False, "detail": detail,
                "replay_ok": None, "n_instances": 0,
                "statement_hash": "", "statement_dl": 0}

    # stage 1: parse-math-reading -- groundedness + trichotomy (catches fab).
    try:
        reading = parse_math_reading(math_reading_json, source_text)
    except BadMathReading as e:            # FragmentMiss is a BadMathReading
        return _rej("parse-math-reading", f"parse-math-reading: {e}")
    except Exception as e:                 # a malformed candidate is a gate fail
        return _rej("parse-math-reading",
                    f"parse-math-reading: {type(e).__name__}: {e}")

    # stage 2: math-smt -- hypothesis-set satisfiability (SHARED dual-solver
    # non-vacuity; degrades honestly when cvc5 is absent).
    try:
        nv = _formalize._nonvacuity(reading, bound, event_sink)
    except Exception as e:
        return _rej("math-smt", f"math-smt: {type(e).__name__}: {e}")
    if not nv["ok"]:
        return _rej("math-smt", f"math-smt: {nv['error']}")

    # stage 3: compile-math -- compile + the lexical escape gate (defense in
    # depth on the compiler's OWN output, exactly as certify_statement does).
    try:
        compiled = compile_math_reading(reading)
    except CompileError as e:
        return _rej("compile-math", f"compile-math: {e}")
    except Exception as e:
        return _rej("compile-math", f"compile-math: {type(e).__name__}: {e}")
    lean_text = compiled["lean_text"]
    gate_ok, gate_reason = validate_lean(lean_text)
    if not gate_ok:
        return _rej("compile-math",
                    f"compile-math: escape-gate refusal: {gate_reason}")

    # stage 4: entailed-instance-replay -- RANK ONLY (never a rejection, S4).
    replay_ok = True
    n_instances = 0
    try:
        insts = math_eval.satisfying_instances(reading, k=5, bound=bound)
        n_instances = len(insts)
        for a in insts:
            if not math_eval.conclusion_holds(reading, a):
                replay_ok = False
                break
        detail = (f"entailed-instance-replay: reached (rank-only); "
                  f"{n_instances} entailed instance(s), replay_ok={replay_ok}")
    except Exception as e:
        replay_ok = None
        detail = (f"entailed-instance-replay: rank-only; replay skipped "
                  f"({type(e).__name__}: {e})")
    return {"stage_reached": "entailed-instance-replay", "ok": True,
            "detail": detail, "replay_ok": replay_ok,
            "n_instances": n_instances,
            "statement_hash": compiled["statement_hash"],
            "statement_dl": len(lean_text)}


def rank_score_math(result: dict) -> tuple:
    """RANKING KEY for one math candidate from its `pre_gate_math` result --
    ASCENDING (the best candidate sorts FIRST), mirroring `rank_score`'s
    "(stage reached, then a scorer)" shape:

      * survivors (reached entailed-instance-replay, ok=True) before losers;
      * then the RANK-ONLY replay signal: replay_ok True before False/None -- a
        candidate whose entailed instances all hold outranks one an instance
        refutes.  This is the S4 REORDER, never a rejection (a refuted candidate
        still ranks, it just ranks lower);
      * then the compiled-statement DL proxy (shorter statement first), then the
        statement hash as a final deterministic tie-break.

    Deterministic and LLM-free; touches ONLY ranking, never the verdict."""
    ok = bool(result.get("ok"))
    replay_ok = result.get("replay_ok")
    return (0 if ok else 1,
            0 if replay_ok else 1,
            result.get("statement_dl", 0),
            result.get("statement_hash", ""))


def certify_math(source_text: str, math_reading_json: str, *, bound: int = 8,
                 event_sink=None, cache_get=None, cache_put=None,
                 source_id=None):
    """The GROUND-TRUTH the math pre-gate is measured against: the real,
    Lean-free statement-fidelity pipeline (`run.formalize.certify_statement`).

    This is NOT the speculative path; it is the only math entry point here that
    can compose a certificate, and it does so ONLY for the candidate the caller
    actually certifies (the winner).  Returns the `FormalizeResult`."""
    from run import formalize as _formalize
    return _formalize.certify_statement(
        source_text, math_reading_json, event_sink=event_sink,
        cache_get=cache_get, cache_put=cache_put, bound=bound,
        source_id=source_id)


def log_math_divergence(registry, source_text: str, math_reading_json: str,
                        pre_result: dict, certified_ok: bool, *,
                        request_sha=None):
    """Compare the SPECULATED verdict (``pre_result['ok']``) with the CERTIFIED
    verdict (``certified_ok``) and, on a PREDICTION MISS, record a
    ``speculation-divergence`` event -- routed through the SHARED
    `log_divergence`, so the payload shape is byte-identical to the service
    path's ({stage, direction, candidate_sha, request_sha}).

    Returns the payload dict, or None when the two agree (Z-D: a tie/agreement
    is never logged).  Because stage 4 is rank-only, a carrier-narrowed
    candidate the pre-gate PREDICTED would pass (it reached the terminal rung)
    but the real pipeline REFUTES at ``instances`` is the canonical
    predicted-pass / actual-fail miss."""
    predicted = bool(pre_result["ok"])
    observed = bool(certified_ok)
    if predicted == observed:
        return None
    direction = ("predicted-pass-actual-fail" if predicted and not observed
                 else "predicted-fail-actual-pass")
    candidate_sha = common.sha256_json(json.loads(math_reading_json))
    if request_sha is None:
        request_sha = common.sha256_bytes(source_text.encode())
    return log_divergence(registry, stage=pre_result["stage_reached"],
                          direction=direction, candidate_sha=candidate_sha,
                          request_sha=request_sha)


def fan_out_math(source_text: str, k: int, *, macro_table=None, model=None,
                 author=None, spend=None) -> list:
    """F-INT-5 fan-out: author k candidate MathReadings for ONE source, each
    prompt rendered by ``math_prompt.render_math_reading_prompt`` (the E1 seam --
    the LIVE macro table reaches the prompt), diversified by deterministic prompt
    VARIATION exactly as `fan_out`.

    Author selection (fully injectable for LLM-free use):
      * ``author`` given   -> call ``author(prompt, variation)`` for each
        candidate (the LLM-free planted path -- CI, demos, teeth);
      * else ``model``     -> call ``buildloop.llm.call_llm(prompt, model)``;
      * else (both None)   -> return [] (every deterministic / CI caller uses
        `pre_gate_math` directly and never touches the LLM).

    Each author returns a dict with at least ``{"text"}`` and optionally
    ``{"model", "input_tokens", "output_tokens"}``.  Returns a list of dicts
    ``{"text","model","variation","input_tokens","output_tokens"}``.  No
    candidate returned here is a certificate (Z1); ranking/certification is the
    caller's job via `pre_gate_math`, `rank_score_math` and `certify_math`."""
    if author is None and model is None:
        return []
    from buildloop import math_prompt
    base = math_prompt.render_math_reading_prompt(source_text, macro_table)
    out, spent = [], 0
    for i in range(int(k)):
        if spend is not None and spent >= spend:
            break
        prompt = base if i == 0 else (
            base + f"\n\n(variation {i}: author a DIFFERENT but equally "
                   f"faithful reading of the same source -- a distinct choice "
                   f"of carriers/object types/structure, never a different "
                   f"demand.)")
        if author is not None:
            resp = author(prompt, i)
        else:
            from buildloop import llm
            resp = llm.call_llm(prompt, model=model)
        spent += resp.get("input_tokens", 0) + resp.get("output_tokens", 0)
        out.append({"text": resp["text"], "model": resp.get("model", model),
                    "variation": i,
                    "input_tokens": resp.get("input_tokens", 0),
                    "output_tokens": resp.get("output_tokens", 0)})
    return out
