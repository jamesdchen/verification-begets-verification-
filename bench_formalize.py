#!/usr/bin/env python3
"""F-INT-4 / F5.2: the wave-parallel, dream-wired, checkpointed, cost-accounted
governed-vs-ungoverned formalization benchmark (LLM-requiring for a real run).

Two arms over an IDENTICAL source corpus, model, prompt scaffold and spend cap --
the SAME code path over different READING SETS, never a miner fork (⚠E4: `mine`
refuses DL-raising candidates inline, so "admit everything" is not a flag; and
origin-blind witnessing is today's default, so it is the GOVERNED arm that needs
the exogenous witness filter):

  * governed   -- mining / admission over EXOGENOUS-origin readings only,
                  per-use translation-cert ON;
  * ungoverned -- the identical calls over ALL readings INCLUDING dreams (the
                  literature's default), per-use certs OFF.

WAVE PROTOCOL (F-INT-4).  Speculation against a frozen snapshot, mirroring
`run_iteration`.  With wave size ``K = 8``:

  1. freeze ``table_hash = common.sha256_json(sorted(macro_table))`` (macro names
     are content-addressed body hashes -- recurrence.py:151-153 -- so the name
     digest is faithful);
  2. author the wave's K statements CONCURRENTLY (threads around ``call_llm``, a
     subprocess -- thread-safe), each call stamped with ``table_hash``;
  3. run the LLM-FREE tail SERIALLY after the wave barrier: certify each,
     CHECKPOINT each (single writer -- the record carries post-certify fields, so
     it cannot be written from an authoring thread), mine + admit greedily
     (`recurrence.mine` + `mdl_macros.macro_admission_decision`, the arm's witness
     filter), then advance to the next wave with the GROWN table.

A kill mid-wave re-spends at most the un-checkpointed in-flight wave -- standard
checkpoint semantics.  Resume keys on the ``(source_id, arm)`` set; line order is
explicitly insignificant.  ``--fresh`` ignores any existing state.

CONCURRENT ARMS (LAT-A).  After the shared dream wave (authored once) the
GOVERNED and UNGOVERNED wave sequences are INDEPENDENT, so they run
CONCURRENTLY on two threads -- each arm still drives its OWN wave loop with its
OWN K=8 authoring pool and its OWN frozen per-wave ``table_hash`` (nothing about
a single arm's protocol changes).  Because both arms author at once, the GLOBAL
ceiling on concurrent LLM subprocesses DOUBLES to ``2 * K = 16`` (the per-arm
cap stays K=8).  The single JSONL checkpoint is appended from both arm threads
under a module-level lock so each one-line record append is atomic; the arms
never share a ``(source_id, arm)`` key.  Per-arm rows are gathered and the CSV /
sidecar / plot are written in a FIXED order (dream, governed waves, ungoverned
waves) regardless of thread finish order, so the artifacts are byte-deterministic
given the same authored readings.  ``CGB_BENCH_SERIAL=1`` restores the serial arm
order and is byte-identical (the concurrency-equivalence tooth pins this).

DREAMS (F-INT-4 / E3).  ``specs/mathsources/dream/*.txt`` are authored ONCE
(single wave, empty table) and enter ONLY the ungoverned arm's mining corpus as
``origin:"system"`` readings -- governance is enforced by corpus MEMBERSHIP (the
shipped `_arm` pattern), the Z-E witness filter is belt-and-suspenders.  Dream
authoring spend is recorded as a CSV row ``arm="dream"`` and charged to NEITHER
arm's ``cost_per_certified_statement``.

COST (⚠E6 / ⚠E3 / ⚠FH7 / ⚠FI-22).  The numerator is FROZEN:

    cost_per_certified_statement = (cumulative_ktokens_in + cumulative_ktokens_out)
                                   / FH7-denominator

-- kilotokens ONLY.  The seconds columns (``lean_seconds_total``, ``smt_seconds``)
are REPORTED beside it and NEVER divided in (tokens are never summed with
seconds).  FH7 denominator: exogenous entries with statement-cert green AND
``trivially_closed == false``; the ``_inclusive`` variant (green regardless of
triviality) and the excluded count sit beside it.  In a Lean-ABSENT container the
kernel proof-cert is deferred, so "statement-cert green" is read as the Lean-free
statement-FIDELITY verdict (``FormalizeResult.ok``); ``trivially_closed`` is
``false`` for ALL entries (no Lean triviality event fires), so the two cost
variants COINCIDE -- recorded honestly in the sidecar.

DEFERRED (Lean-toolchain run only).  The four Lean-internal F5.2 tuple fields --
``refinement_rounds_mean``, ``lean_seconds_cold``, ``cache_hit_rate``,
``proof_rate`` -- are DEFERRED to a real Lean run and named here so they are not
silently omitted; they are absent from the frozen CSV by design.

ARTIFACTS.  Per-wave rows ARE the reach-vs-cost curve; ``run_bench`` writes:
  * ``results/formalize_bench_state.jsonl`` -- the checkpoint (one object per
    authored reading);
  * ``results/formalize_governed.csv``      -- the frozen per-wave rows;
  * ``results/formalize_governed.meta.json``-- the pins sidecar (CSV stays pure);
  * ``results/formalize_reach_vs_cost.png`` -- the two-curve figure (tokens-only
    x-axis, so ⚠E6 holds).

Skippable with an honest note (⚠H43 / X15): with no LLM endpoint ``main`` skips,
and the certificate-backed MECHANISM lives in the LLM-FREE tooth
``tests/test_bench_formalize.py`` (an injected deterministic fake author) and in
``demo_formalize_governor.py`` part (v).  A REAL run (``python3
bench_formalize.py``) costs ~= 2 * (|sources| + |dreams|/2) authoring calls at the
pinned model; it resumes from ``formalize_bench_state.jsonl`` and re-spends at
most the un-checkpointed in-flight wave.  ``cvc5`` may be absent -- the bench
degrades honestly (a certify exception counts the reading uncertified).
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import pathlib
import shutil
import sys
import threading
import time

REQUIRES_LLM = True

_ROOT = pathlib.Path(__file__).resolve().parent
_CORPUS = _ROOT / "specs" / "mathsources"
_DREAMS = _CORPUS / "dream"
_RESULTS = _ROOT / "results"

WAVE_SIZE = 8                       # F-INT-4 K (per-arm authoring pool)
_SPEND_CAP_CALLS = int(os.environ.get("CGB_FORMALIZE_SPEND_CAP", "0")) or None

# LAT-A: after the shared dream wave, the two arms' wave sequences are
# INDEPENDENT (F-INT-4: "per-arm wave sequences over the same sources"), so we
# run them CONCURRENTLY on two threads.  Each arm keeps its own K=8 authoring
# pool, so the GLOBAL concurrent-LLM-subprocess ceiling is 2 * K = 16 (it
# DOUBLES vs the serial engine's K=8); the per-arm cap is unchanged.  Set
# ``CGB_BENCH_SERIAL=1`` to fall back to the serial arm order (byte-identical
# CSV -- the concurrency-equivalence tooth pins this).
def _serial_arms() -> bool:
    return os.environ.get("CGB_BENCH_SERIAL") == "1"


# The single JSONL checkpoint is now appended from two arm threads.  This
# module-level lock makes each record append (one canonical line + flush)
# ATOMIC; resume stays keyed on ``(source_id, arm)`` with line order explicitly
# insignificant (F-INT-4), and the arms never share a ``(source_id, arm)`` key,
# so only the shared file handle + records dict need guarding.
_CHECKPOINT_LOCK = threading.Lock()

# The frozen CSV header (append-only; F-INT-4).  Order is load-bearing.
CSV_COLUMNS = [
    "arm", "wave", "certified_exogenous_statements",
    "cumulative_ktokens_in", "cumulative_ktokens_out", "prompt_bytes_mean",
    "live_macros", "retired_macros", "reported_exogenous_dl",
    "translation_cert_count", "per_use_cert_failures", "trivially_closed_count",
    "cost_per_certified_statement", "cost_per_certified_statement_inclusive",
    "lean_seconds_total", "smt_seconds",
]

# The four Lean-internal F5.2 tuple fields, DEFERRED to a Lean-toolchain run.
DEFERRED_F52_FIELDS = (
    "refinement_rounds_mean", "lean_seconds_cold", "cache_hit_rate",
    "proof_rate")

_EXO = lambda r: r.get("origin") == "exogenous"


# ============================================================ LLM availability
def _llm_available() -> bool:
    import common
    return bool(shutil.which(os.path.basename(common.CLAUDE_CLI))
                or os.path.exists(common.CLAUDE_CLI)
                or os.environ.get("ANTHROPIC_API_KEY"))


# ================================================================= the author
def _llm_author(source_id, source_text, macro_table, table_hash, *, model=None):
    """The real author: render the prompt with the LIVE macro table (the E1 seam
    by which admitted vocabulary changes prompt bytes and thus cost), call the
    model, return the reading JSON + token usage.  Returns None on an LLM error.

    A FAKE author with this identical signature is injected by the LLM-free
    tooth; nothing below this line ever imports an LLM module."""
    from buildloop import llm, math_prompt
    prompt = math_prompt.render_math_reading_prompt(source_text, macro_table)
    try:
        out = llm.call_llm(prompt, model=model)
    except (llm.LLMError, OSError):               # LLM error OR missing binary
        return None
    text = out["text"] if isinstance(out, dict) else out
    return {"reading_json": llm.strip_fences(text),
            "tokens_in": out.get("input_tokens", 0) if isinstance(out, dict) else 0,
            "tokens_out": out.get("output_tokens", 0) if isinstance(out, dict) else 0}


# =============================================================== checkpointing
class _Checkpoint:
    """Single-writer JSONL checkpoint over ``(source_id, arm)``.  Resume skips
    pairs already present (line order insignificant); ``--fresh`` truncates."""

    def __init__(self, path, *, fresh=False):
        self.path = str(path)
        self.records = {}
        if not fresh and os.path.exists(self.path):
            with open(self.path) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    self.records[(rec["source_id"], rec["arm"])] = rec
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self._fh = open(self.path, "w" if fresh else "a")

    def has(self, source_id, arm):
        return (source_id, arm) in self.records

    def get(self, source_id, arm):
        return self.records[(source_id, arm)]

    def write(self, rec):
        import common
        line = common.canonical_json(rec) + "\n"   # pure; built off-lock
        # Atomic append from either arm thread: the dict update and the single
        # line write + flush happen under the module lock, so a concurrent
        # append can never interleave a partial line into the JSONL.
        with _CHECKPOINT_LOCK:
            self.records[(rec["source_id"], rec["arm"])] = rec
            self._fh.write(line)
            self._fh.flush()

    def close(self):
        self._fh.close()


# ============================================================ certify (timed)
def _timed_certify(source_text, reading_json, event_sink=None):
    """Run the Lean-free statement-fidelity pipeline, timing the call (the work
    is SMT-dominated in a Lean-absent container).  ``cvc5`` absence raises inside
    ``certify_statement``; we degrade honestly -- an exception counts the reading
    UNCERTIFIED.  Returns (certified: bool, stage: str, smt_seconds: float)."""
    from run.formalize import certify_statement
    t0 = time.monotonic()
    try:
        res = certify_statement(source_text, reading_json, event_sink=event_sink)
        certified, stage = bool(res.ok), (res.stage or "")
    except Exception as e:                       # cvc5 absent / bad reading
        certified, stage = False, "certify-error:" + type(e).__name__
    return certified, stage, time.monotonic() - t0


# ============================================================= greedy mining
def _greedy_grow(table, corpus, witness_filter):
    """Grow ``table`` in place: repeatedly mine + admit the best candidate that
    still clears ``macro_admission_decision`` under the witness filter.  Mirrors
    the shipped `_arm` / demo_formalize_governor `_greedy_admit`."""
    from buildloop import recurrence, mdl_macros
    while True:
        cands = recurrence.mine(corpus, table, witness_filter=witness_filter)
        chosen = None
        for c in cands:
            cand = c["candidate"]
            if cand["name"] in table:
                continue
            if mdl_macros.macro_admission_decision(
                    corpus, cand, table, witness_filter=witness_filter)["admit"]:
                chosen = cand
                break
        if chosen is None:
            return
        table[chosen["name"]] = chosen


# ==================================================== per-use translation certs
def _macro_uses(stmts, table):
    """Greedy (longest-body-first, then name) scan of a statement stream for
    macro invocations, mirroring ``mdl_macros._reading_stats``.  Returns a list
    of (macro, index, binding) per use."""
    from buildloop import mdl_macros
    macros = sorted(table.values(), key=lambda m: (-len(m["body"]), m["name"]))
    uses, i = [], 0
    while i < len(stmts):
        hit = binding = None
        for m in macros:
            b = mdl_macros._match_at(stmts, i, m)
            if b is not None:
                hit, binding = m, b
                break
        if hit is not None:
            uses.append((hit, i, binding))
            i += len(hit["body"])
        else:
            i += 1
    return uses


def _per_use_cert_counts(exo_readings, table):
    """Per-emission translation-cert(reference-lowering) for every macro use in
    the GOVERNED arm's exogenous corpus, generalizing demo_formalize_governor's
    ``_per_emission_cert``: channel 1 = compile-hash identity of the
    macro-expanded reading vs its retained inlined baseline; channel 2 =
    entailed-instance replay (both Lean-free).  Returns (cert_count, failures)."""
    import kernel
    from kernel.certs import Certificate
    count = fails = 0
    for r in exo_readings:
        stmts = r["statements"]
        src = r.get("_source", "")
        theorem = r.get("theorem", "t")
        for macro, i, binding in _macro_uses(stmts, table):
            inv = {"id": "inv", "force": stmts[i].get("force"),
                   "quote": stmts[i].get("quote", ""),
                   "lf": {"kind": "macro", "name": macro["name"], "args": binding}}
            expanded = {"theorem": theorem,
                        "statements": stmts[:i] + [inv]
                        + stmts[i + len(macro["body"]):]}
            inlined = {"theorem": theorem, "statements": stmts}
            contract = {"type": "translation-cert",
                        "anchor": "reference-lowering",
                        "high_language": "math-macro-reading",
                        "high_spec_text": json.dumps(expanded),
                        "reference_lowering": json.dumps(inlined),
                        "request": src,
                        "expansion_context": {"macro_table": {macro["name"]: macro}}}
            try:
                v = kernel.check({"kind": "math", "files": {}}, contract)
            except Exception:
                v = None
            if isinstance(v, Certificate):
                count += 1
            else:
                fails += 1
    return count, fails


# ==================================================================== one arm
def _run_arm(arm, sources, author, *, governed, dream_readings, checkpoint,
             model, event_sink, prompt_bytes_of):
    """Run one arm's wave sequence over ``sources`` and return its per-wave CSV
    row dicts.  ``dream_readings`` (system-origin) join ONLY an ungoverned arm's
    mining corpus.  ``sources`` is a list of (source_id, source_text)."""
    table = {}
    exo_readings = []            # authored exogenous readings, in author order
    cum_tin = cum_tout = 0
    prompt_byte_samples = []
    smt_seconds = 0.0
    rows = []
    wfilter = _EXO if governed else None
    waves = [sources[i:i + WAVE_SIZE] for i in range(0, len(sources), WAVE_SIZE)]

    for wi, wave in enumerate(waves):
        frozen_table = dict(table)                          # the wave snapshot
        table_hash = _table_hash(frozen_table)

        # -- parallel authoring around the barrier (fresh pairs only) ----------
        to_author = [(sid, txt) for sid, txt in wave
                     if not checkpoint.has(sid, arm)]
        authored = {}
        if to_author:
            with concurrent.futures.ThreadPoolExecutor(
                    max_workers=max(1, len(to_author))) as pool:
                futs = {pool.submit(author, sid, txt, frozen_table, table_hash):
                        sid for sid, txt in to_author}
                for fut in concurrent.futures.as_completed(futs):
                    authored[futs[fut]] = fut.result()

        # -- serial LLM-free tail after the barrier ---------------------------
        for sid, txt in wave:
            prompt_bytes = prompt_bytes_of(txt, frozen_table)
            if checkpoint.has(sid, arm):                    # resumed: no re-work
                rec = checkpoint.get(sid, arm)
            else:
                res = authored.get(sid)
                if res is None:                             # LLM failure
                    rec = {"source_id": sid, "arm": arm, "wave": wi,
                           "table_hash": table_hash, "reading_json": "",
                           "tokens_in": 0, "tokens_out": 0,
                           "certified": False, "stage": "author-failed"}
                else:
                    certified, stage, dt = _timed_certify(
                        txt, res["reading_json"], event_sink)
                    smt_seconds += dt
                    rec = {"source_id": sid, "arm": arm, "wave": wi,
                           "table_hash": table_hash,
                           "reading_json": res["reading_json"],
                           "tokens_in": int(res["tokens_in"]),
                           "tokens_out": int(res["tokens_out"]),
                           "certified": certified, "stage": stage}
                checkpoint.write(rec)

            cum_tin += rec["tokens_in"]
            cum_tout += rec["tokens_out"]
            prompt_byte_samples.append(prompt_bytes)
            doc = _reading_doc(rec, txt, origin="exogenous")
            if doc is not None:
                exo_readings.append(doc)

        # -- mine + admit greedily, advance with the grown table --------------
        corpus = exo_readings + (dream_readings if not governed else [])
        _greedy_grow(table, corpus, wfilter)

        rows.append(_arm_row(arm, wi, exo_readings, table, cum_tin, cum_tout,
                             prompt_byte_samples, smt_seconds, governed))
    return rows


# ------------------------------------------------------------- row assembly
def _arm_row(arm, wave, exo_readings, table, cum_tin, cum_tout,
             prompt_byte_samples, smt_seconds, governed):
    from buildloop import mdl_macros
    reported_dl = round(mdl_macros.corpus_dl(exo_readings, table)["total"], 3) \
        if exo_readings else 0.0
    # FH7 (⚠E3): green statement-fidelity AND trivially_closed == false.
    # Lean absent -> trivially_closed is false for ALL, so the two variants agree.
    denom_excl = sum(1 for r in exo_readings
                     if r["_certified"] and not r["_trivial"])
    denom_incl = sum(1 for r in exo_readings if r["_certified"])
    trivially_closed_count = sum(1 for r in exo_readings if r["_trivial"])
    ktin, ktout = cum_tin / 1000.0, cum_tout / 1000.0
    cps = round((ktin + ktout) / denom_excl, 6) if denom_excl else 0.0
    cps_incl = round((ktin + ktout) / denom_incl, 6) if denom_incl else 0.0
    tcert, tfail = _per_use_cert_counts(exo_readings, table) if governed else (0, 0)
    pmean = round(sum(prompt_byte_samples) / len(prompt_byte_samples), 3) \
        if prompt_byte_samples else 0.0
    return {
        "arm": arm, "wave": wave,
        "certified_exogenous_statements": denom_incl,
        "cumulative_ktokens_in": round(ktin, 6),
        "cumulative_ktokens_out": round(ktout, 6),
        "prompt_bytes_mean": pmean,
        "live_macros": len(table),
        "retired_macros": 0,          # no GC pass in this bench (documented)
        "reported_exogenous_dl": reported_dl,
        "translation_cert_count": tcert,
        "per_use_cert_failures": tfail,
        "trivially_closed_count": trivially_closed_count,
        "cost_per_certified_statement": cps,
        "cost_per_certified_statement_inclusive": cps_incl,
        "lean_seconds_total": 0.0,    # Lean absent (recorded in sidecar)
        "smt_seconds": round(smt_seconds, 6),
    }


# ------------------------------------------------------------------- helpers
def _table_hash(macro_table):
    import common
    return common.sha256_json(sorted(macro_table))


def _reading_doc(rec, source_text, *, origin):
    """Build the mining/pricing doc from a checkpoint record.  The persisted
    reading is exactly ``{theorem, statements}`` (⚠FI-13); origin and the
    certify markers live only on this in-memory bench doc."""
    rj = rec.get("reading_json") or ""
    if not rj:
        return None
    try:
        doc = json.loads(rj)
    except ValueError:
        return None
    if not isinstance(doc, dict) or "statements" not in doc:
        return None
    return {"theorem": doc.get("theorem", "t"),
            "statements": doc["statements"],
            "origin": origin, "_source": source_text,
            "_certified": bool(rec.get("certified")),
            "_trivial": False}          # Lean absent -> false for all


def _author_dreams(dream_sources, author, checkpoint, model, event_sink,
                   prompt_bytes_of):
    """Author the dream corpus ONCE (single wave, empty table).  Returns
    (dream_readings, dream_row) -- the readings join only the ungoverned arm's
    mining corpus; the row carries the spend, charged to neither arm (⚠E3)."""
    empty_table = {}
    table_hash = _table_hash(empty_table)
    to_author = [(sid, txt) for sid, txt in dream_sources
                 if not checkpoint.has(sid, "dream")]
    authored = {}
    if to_author:
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=max(1, len(to_author))) as pool:
            futs = {pool.submit(author, sid, txt, empty_table, table_hash): sid
                    for sid, txt in to_author}
            for fut in concurrent.futures.as_completed(futs):
                authored[futs[fut]] = fut.result()

    dream_readings, cum_tin, cum_tout, certified = [], 0, 0, 0
    smt_seconds = 0.0
    for sid, txt in dream_sources:
        if checkpoint.has(sid, "dream"):
            rec = checkpoint.get(sid, "dream")
        else:
            res = authored.get(sid)
            if res is None:
                rec = {"source_id": sid, "arm": "dream", "wave": 0,
                       "table_hash": table_hash, "reading_json": "",
                       "tokens_in": 0, "tokens_out": 0,
                       "certified": False, "stage": "author-failed"}
            else:
                cok, stage, dt = _timed_certify(txt, res["reading_json"],
                                                event_sink)
                smt_seconds += dt
                rec = {"source_id": sid, "arm": "dream", "wave": 0,
                       "table_hash": table_hash,
                       "reading_json": res["reading_json"],
                       "tokens_in": int(res["tokens_in"]),
                       "tokens_out": int(res["tokens_out"]),
                       "certified": cok, "stage": stage}
            checkpoint.write(rec)
        cum_tin += rec["tokens_in"]
        cum_tout += rec["tokens_out"]
        if rec.get("certified"):
            certified += 1
        doc = _reading_doc(rec, txt, origin="system")
        if doc is not None:
            dream_readings.append(doc)

    dream_row = {c: 0 for c in CSV_COLUMNS}
    dream_row.update({
        "arm": "dream", "wave": 0,
        "certified_exogenous_statements": 0,     # dreams are system-origin
        "cumulative_ktokens_in": round(cum_tin / 1000.0, 6),
        "cumulative_ktokens_out": round(cum_tout / 1000.0, 6),
        "reported_exogenous_dl": 0.0,
        "smt_seconds": round(smt_seconds, 6),
        "lean_seconds_total": 0.0})
    return dream_readings, dream_row


# ===================================================== corpus / dream loading
def _corpus_sources():
    return [(p.stem, p.read_text().strip())
            for p in sorted(_CORPUS.glob("*.txt"))]


def _dream_sources():
    return [(p.stem, p.read_text().strip())
            for p in sorted(_DREAMS.glob("*.txt"))
            if p.name.lower() != "readme.txt"]


# ==================================================================== outputs
def _write_csv(rows, path):
    import csv
    os.makedirs(os.path.dirname(str(path)) or ".", exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in CSV_COLUMNS})
    return path


def _write_meta(path, *, model, arm_configs):
    """The pins sidecar (⚠E-pins).  The CSV stays pure rows; every verdict-
    flipping pin lives here."""
    import common
    from buildloop import llm
    scaffold_src = (_ROOT / "buildloop" / "math_prompt.py").read_bytes()
    meta = {
        "model_id": model or llm.DEFAULT_MODEL,
        "sampling_params": {"note": "claude CLI headless defaults "
                            "(temperature not overridden)"},
        "prompt_scaffold_sha256": common.sha256_bytes(scaffold_src),
        "arm_configs": arm_configs,
        "spend_cap_calls": _SPEND_CAP_CALLS,
        "wave_size": WAVE_SIZE,
        "mathlib_commit": common.MATHLIB_COMMIT,
        "lean_toolchain": common.LEAN_TOOLCHAIN,
        "lean_available": bool(getattr(common, "lean_available", lambda: False)()),
        "honesty_notes": {
            "trivially_closed": "false for ALL entries -- no Lean toolchain, so "
                                "no triviality event fires; the two cost variants "
                                "coincide.",
            "lean_seconds_total": "0.0 -- Lean absent; reported, never divided in "
                                  "(⚠E6).",
            "smt_seconds": "wall-time of the Lean-free fidelity certification "
                           "(SMT-dominated); reported, never divided in (⚠E6).",
            "cost_numerator": "(cumulative_ktokens_in + cumulative_ktokens_out) "
                              "/ FH7-denominator -- kilotokens only (⚠FI-22).",
            "deferred_f52_fields": list(DEFERRED_F52_FIELDS),
        },
    }
    with open(path, "w") as fh:
        fh.write(common.canonical_json(meta))
    return path


def _write_plot(rows, path):
    """The two-curve reach-vs-cost figure: cumulative tokens (x, kilotokens ONLY
    -- ⚠E6) vs certified exogenous statements (y), one curve per governed/
    ungoverned arm.  The dream row is cost-only and excluded."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None
    # An UNMETERED run (session-inline authoring, every token count 0) would
    # collapse the tokens-only x-axis to a single vertical line -- honest but
    # unreadable.  Fall back to the wave index as x, SAYING SO on the axis and
    # title; the tokens axis is used whenever any real spend was metered.
    arm_rows = [r for r in rows if r["arm"] in ("governed", "ungoverned")]
    metered = any((r["cumulative_ktokens_in"] + r["cumulative_ktokens_out"]) > 0
                  for r in arm_rows)
    # Two panels: reach (where equal coverage makes the arms COINCIDE -- that
    # overlap is the F5.2 equal-coverage guarantee, not a plotting accident)
    # and reported exogenous corpus DL (where the arms actually separate --
    # the governance effect).
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=140)
    for arm in ("governed", "ungoverned"):
        rs = sorted((r for r in arm_rows if r["arm"] == arm),
                    key=lambda r: r["wave"])
        xs = [((r["cumulative_ktokens_in"] + r["cumulative_ktokens_out"])
               if metered else r["wave"]) for r in rs]
        style = dict(marker="o", markersize=4, linewidth=1.5, label=arm)
        if arm == "governed":
            style.update(linestyle="--", linewidth=2.5)   # visible under overlap
        ax.plot(xs, [r["certified_exogenous_statements"] for r in rs], **style)
        ax2.plot(xs, [float(r["reported_exogenous_dl"]) for r in rs], **style)
    if metered:
        xlabel = "cumulative cost (LLM kilotokens in+out; seconds NOT summed)"
        suffix = "(tokens-only x-axis)"
    else:
        xlabel = ("wave index (UNMETERED run: cost columns are void, "
                  "so the tokens axis carries no information)")
        suffix = "(unmetered run: x = wave index)"
    ax.set_xlabel(xlabel)
    ax.set_ylabel("certified exogenous statements (reach)")
    ax.set_title("reach (arms coincide: equal coverage)")
    ax2.set_xlabel(xlabel)
    ax2.set_ylabel("reported exogenous corpus DL (lower = better vocabulary)")
    ax2.set_title("exogenous DL (the governance effect)")
    for a in (ax, ax2):
        a.grid(True, alpha=0.3)
        a.legend()
    fig.suptitle("Formalization bench -- governed vs ungoverned " + suffix)
    fig.tight_layout()
    os.makedirs(os.path.dirname(str(path)) or ".", exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path


# ================================================================= the bench
def run_bench(model=None, *, author=None, sources=None, dream_sources=None,
              out_dir=None, fresh=False, event_sink=None):
    """Run the two-arm wave bench and write the four artifacts.

    ``author`` (default the real LLM author) has signature
    ``author(source_id, source_text, macro_table, table_hash) -> {"reading_json",
    "tokens_in", "tokens_out"} | None`` -- the LLM-free tooth injects a
    deterministic fake with this signature.  ``sources`` / ``dream_sources``
    default to ``specs/mathsources``; ``out_dir`` defaults to ``results/``.
    Returns a summary dict (also usable as the assertion substrate)."""
    from buildloop import math_prompt

    if author is None:
        author = lambda sid, txt, mt, th, _m=model: _llm_author(
            sid, txt, mt, th, model=_m)
    if sources is None:
        sources = _corpus_sources()
    if dream_sources is None:
        dream_sources = _dream_sources()
    out_dir = pathlib.Path(out_dir) if out_dir else _RESULTS
    state_path = out_dir / "formalize_bench_state.jsonl"
    checkpoint = _Checkpoint(state_path, fresh=fresh)

    def prompt_bytes_of(text, table):
        return len(math_prompt.render_math_reading_prompt(text, table))

    # dreams authored ONCE; only the ungoverned arm mines them.
    dream_readings, dream_row = _author_dreams(
        dream_sources, author, checkpoint, model, event_sink, prompt_bytes_of)

    # The two arms' wave sequences are independent after the shared dream wave,
    # so run them CONCURRENTLY (each on its own thread, each with its own K=8
    # authoring pool -> global ceiling 2*K=16).  The checkpoint append is
    # lock-atomic; the per-arm rows are gathered and assembled in a FIXED order
    # below, so the artifacts are byte-deterministic regardless of finish order.
    def _gov():
        return _run_arm("governed", sources, author, governed=True,
                        dream_readings=dream_readings, checkpoint=checkpoint,
                        model=model, event_sink=event_sink,
                        prompt_bytes_of=prompt_bytes_of)

    def _ung():
        return _run_arm("ungoverned", sources, author, governed=False,
                        dream_readings=dream_readings, checkpoint=checkpoint,
                        model=model, event_sink=event_sink,
                        prompt_bytes_of=prompt_bytes_of)

    if _serial_arms():                       # byte-identical serial fallback
        gov_rows, ung_rows = _gov(), _ung()
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as arms:
            gov_fut, ung_fut = arms.submit(_gov), arms.submit(_ung)
            gov_rows, ung_rows = gov_fut.result(), ung_fut.result()
    checkpoint.close()

    # FIXED artifact order (dream, then governed waves, then ungoverned waves),
    # independent of which arm thread finished first -- byte-determinism (E5).
    all_rows = [dream_row] + gov_rows + ung_rows
    csv_path = _write_csv(all_rows, out_dir / "formalize_governed.csv")
    meta_path = _write_meta(out_dir / "formalize_governed.meta.json",
                            model=model,
                            arm_configs={
                                "governed": {"mining_corpus": "exogenous-only",
                                             "witness_filter": "exogenous",
                                             "per_use_certs": True},
                                "ungoverned": {"mining_corpus": "exogenous+dreams",
                                               "witness_filter": None,
                                               "per_use_certs": False}})
    plot_path = _write_plot(all_rows, out_dir / "formalize_reach_vs_cost.png")

    gov_final, ung_final = gov_rows[-1], ung_rows[-1]
    summary = {
        "csv": str(csv_path), "meta": str(meta_path),
        "plot": str(plot_path) if plot_path else None,
        "state": str(state_path),
        "governed": gov_final, "ungoverned": ung_final, "dream": dream_row,
        "rows": all_rows,
        "covered_governed": gov_final["certified_exogenous_statements"],
        "covered_ungoverned": ung_final["certified_exogenous_statements"],
        "dl_governed": gov_final["reported_exogenous_dl"],
        "dl_ungoverned": ung_final["reported_exogenous_dl"],
    }
    return summary


# ====================================================================== main
def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    fresh = "--fresh" in argv
    if not _llm_available():
        print("SKIP bench_formalize: no LLM endpoint (REQUIRES_LLM).")
        print("  The wave/checkpoint/cost MECHANISM and the F5.3 conjunction "
              "(equal exogenous coverage AND governed reported exogenous DL <= "
              "ungoverned, strict under the planted dream flood) are proven "
              "LLM-free in tests/test_bench_formalize.py and "
              "demo_formalize_governor.py part (v).")
        print("  Per X15, F5's '>= 30/40 certified' headline is DEFERRED to a "
              "run with a model + Lean toolchain; an honest tie is admissible.")
        return 0
    summary = run_bench(fresh=fresh)
    # Relational assert only (⚠E5): equal exogenous coverage, governed DL no worse.
    assert (summary["covered_governed"] == summary["covered_ungoverned"]), \
        "arms must reach equal exogenous coverage"
    assert summary["dl_governed"] <= summary["dl_ungoverned"], \
        "governed reported exogenous DL must not exceed ungoverned"
    print(json.dumps({k: summary[k] for k in (
        "csv", "meta", "plot", "covered_governed", "covered_ungoverned",
        "dl_governed", "dl_ungoverned")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
