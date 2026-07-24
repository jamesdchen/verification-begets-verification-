"""WP-LI1 (PLAN_LEAN_IMPORT.md §3/§4): the budget-bounded Mathlib import
driver -- the outer loop that converts an authorized token budget into ONE
authoring wave over the declaration queue.

    grant (specs/ops/spend_grant.json, USER-GATED)
      -> cgb import --budget-ktokens B --confirm-spend      (this module)
           -> consumes specs/mathsources/mathlib/queue.jsonl (WP-LI0 schema)
           -> appends results/import_ledger.jsonl            (append-only)
           -> persists specs/mathsources/mathlib/readings/<decl>.json

Phase A ONLY (the two-phase split, plan §3): authoring is token-heavy and
Lean-FREE.  Per frontier item the LLM authors a MathReading of the FORMAL
pretty-printed statement (`math_prompt.render_import_reading_prompt` -- the
direction flip, plan §2), the Lean-free gates of
`run.formalize.certify_statement` run (the kernel statement-cert is DEFERRED
in a Lean-absent container -- run/formalize.py's honest-deferral branch; that
deferral is correct behaviour here, Phase B upgrades it), the outcome is
classified {authored | refused | fragment-miss}, a ledger item row is
appended, and tokens are billed.

BINDING RULES (matched to bench_metered / bench_formalize, plan §7):
  * tokens are counted ONLY from `call_llm` returned usage metadata (F1.2);
    never estimated.  Kilotokens are the ONLY cost currency (E6); anything
    else (seconds) is reported beside, never summed in.
  * no wall-clock enters any LOOP decision.  Timestamps are RECORDED on every
    row, never compared.  The single calendar comparison in this module is the
    grant EXPIRY gate -- a startup governance check on the USER-GATED grant
    artifact demanded by plan §5, evaluated once before any spend, with the
    date injected (`today=`) so it is a pure function in tests.
  * the spend interlock is bench_metered's, verbatim: `--confirm-spend` or
    CGB_METERED_CONFIRM_SPEND=1.  Confirmation AND a valid grant -- both,
    not either.
  * halts are RECORDED VERDICTS in the ledger (wave-row `halt_reason` +
    breaker verdict rows), never exceptions.  Quota/rate-limit errors from
    the CLI are a GRACEFUL wave halt (grant mode `weekly-quota-exhaustion`:
    the subscription itself is the total budget), never a crash.
  * checkpoint: `bench_formalize._Checkpoint` (single-writer JSONL, keyed on
    (decl_name, arm), line order insignificant, `--fresh` truncates the STATE
    file only -- the ledger is append-only and is NEVER truncated).
  * the LLM authors reading JSON ONLY; everything else is fixed code (the
    `buildloop/validate.py` discipline: validation happens inside
    `certify_statement` exactly as bench_formalize uses it).

Registered breakers (plan §6), evaluated per item inside the wave:
  P-LI1-REFUSAL  trailing-20 refusal rate > 60%  -> halt wave (recorded).
  P-LI1-COST     wave cost_per_certified_statement > 3x the trailing median
                 across ledger history            -> halt wave (flagged).

Encoding lock-in scaffolding (plan §2.5, T-LI-ENC): this module declares
READING_ENCODING_VERSION and stamps it into every ledger item row and every
authored reading artifact; a version bump without a universal-tier migrator
or a USER-GATED write-off is the CI tooth's business, not this driver's.

INLINE VOCABULARY MINING (B2, plan §8.2; results/import_findings.md Finding 2
item 7 -- RULED: compression co-evolves with the corpus DURING import, not
after).  On the GOVERNED arm the driver runs the SAME mine -> price -> admit
discipline the bench runs (recurrence.mine + mdl_macros.macro_admission_
decision -- the exact machinery behind bench_formalize._greedy_grow; the
pricing is NEVER forked) over the ACCUMULATED authored readings persisted
under specs/mathsources/mathlib/readings/, at wave end and every
MINE_EVERY_K_AUTHORED authored rows within a wave.  Admissions require strict
corpus-DL descent AND >= 2 EXOGENOUS witnesses (NOTE, explicit: every authored
import reading IS exogenous by construction -- the corpus is real Mathlib
statements, the driver has no dream lane -- so the bench's exogenous witness
filter is applied for discipline parity and is satisfied trivially), and
per-use translation-certs against the retained inlined baseline are RECORDED
(bench_formalize._per_use_cert_counts, counts never gates).  Admitted macros
persist append-only to specs/mathsources/mathlib/import_macros.json; the LIVE
table is loaded from there at wave start and threaded into every author call
(the E1 seam).  Mining is CPU, never tokens: every mining ledger row records
ktokens 0.0 -- RECORDED zero, never estimated (E6/F1.2).  A mining exception
can NEVER lose authored work: readings and item rows are on disk before
mining runs, and the failure lands as a first-class kind:"mining-error"
ledger row while the wave still completes.  The per-wave DL instrumentation
(corpus_dl_before/corpus_dl_after over the accumulated corpus, recoded with
the wave-start vs post-mining table, plus macros_admitted_this_wave /
macro_table_size) is the compounding instrument the experiment exists to
measure.  The UNGOVERNED arm's mining is OFF: its macro table stays empty.
"""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common

REQUIRES_LLM = True

# T-LI-ENC scaffolding (plan §2.5): the explicit reading-encoding version.
# Stamped into every ledger ITEM row and every authored reading artifact so a
# future encoding change is visible per-row and migratable per R4 (a
# universal-tier migrator or an explicit USER-GATED write-off; never silent).
READING_ENCODING_VERSION = 1

# ---------------------------------------------------------------- paths ----
_ROOT = pathlib.Path(__file__).resolve().parent.parent
QUEUE_PATH = _ROOT / "specs" / "mathsources" / "mathlib" / "queue.jsonl.gz"
READINGS_DIR = _ROOT / "specs" / "mathsources" / "mathlib" / "readings"
LEDGER_PATH = _ROOT / "results" / "import_ledger.jsonl"
STATE_PATH = _ROOT / "results" / "import_state.jsonl"
GRANT_PATH = _ROOT / "specs" / "ops" / "spend_grant.json"
# B2: the committed append-only admission-record artifact the LIVE macro
# table is loaded from at wave start (governed arm only).
MACROS_PATH = _ROOT / "specs" / "mathsources" / "mathlib" / "import_macros.json"

# ------------------------------------------------- spend interlock (§12.5) --
# bench_metered's interlock, verbatim (same flag, SAME env var): an endpoint
# merely existing is not consent; a metered wave is real spend and must be a
# deliberate act.  Both the interlock AND a valid grant are required.
_CONFIRM_SPEND_FLAG = "--confirm-spend"
_CONFIRM_SPEND_ENV = "CGB_METERED_CONFIRM_SPEND"


def _spend_confirmed(argv) -> bool:
    return (_CONFIRM_SPEND_FLAG in argv
            or os.environ.get(_CONFIRM_SPEND_ENV) == "1")


# ------------------------------------------------------------- constants ----
ARMS = ("governed", "ungoverned")

# B2 (plan §8.2): within a governed wave the mining stage also runs every
# this-many AUTHORED rows (in addition to the unconditional wave-end pass), so
# a long wave's later prompts see vocabulary admitted from its earlier
# readings -- compression co-evolving WITHIN the wave, not only between waves.
# A pure item-count constant, never wall-clock.
MINE_EVERY_K_AUTHORED = 8

# The ab-pilot-then-cheaper ruling (plan §5), arms made REAL by B2: the arm is
# RECORDED per row AND selects the mining discipline.  governed = inline
# mining ON with the full admission discipline (strict DL descent, >= 2
# exogenous witnesses -- trivially satisfied: every import reading is
# exogenous -- and recorded per-use translation-certs); ungoverned = mining
# OFF, macro table empty on every call.  Recorded here so ledger rows are
# self-describing.
ARM_CONFIGS = {
    "governed": {"authoring_vocabulary": "exogenous-only (admitted operator "
                                         "registry -- the E1 seam) + the live "
                                         "import macro table",
                 "mining": "inline (mine->price->admit over the accumulated "
                           "authored readings, wave-end + every %d authored "
                           "rows; strict DL descent, >=2 exogenous witnesses, "
                           "per-use translation-certs recorded; table "
                           "persisted to specs/mathsources/mathlib/"
                           "import_macros.json)" % MINE_EVERY_K_AUTHORED,
                 "per_emission_certs": True},
    "ungoverned": {"authoring_vocabulary": "all-origins",
                   "mining": "off (macro table stays empty)",
                   "per_emission_certs": False},
}


def _mining_enabled(arm) -> bool:
    """B2 arm semantics: inline mining runs on the governed arm only."""
    return arm == "governed"

# P-LI1-REFUSAL (plan §6): trailing-20 refusal rate > 60% halts the wave.
REFUSAL_WINDOW = 20
REFUSAL_RATE_MAX = 0.60
# P-LI1-COST (plan §6): wave cost/certified > 3x trailing median halts.
COST_BLOWOUT_FACTOR = 3.0
# Evaluation hygiene for P-LI1-COST inside a running wave: with < this many
# items the wave-so-far ratio is mostly noise (a single early refusal would
# read as infinite cost), so the breaker arms only once the wave has a
# minimal sample.  A pure item-count constant -- never wall-clock.
COST_BREAKER_MIN_ITEMS = 5

# Queue statuses (WP-LI0 schema).  The driver only ever writes the first four;
# `imported`/`divergent` are Phase-B (Lean lane) verdicts.
QUEUE_STATUSES = ("pending", "authored", "imported", "refused",
                  "fragment-miss", "divergent")

# CLI quota / rate-limit markers (plan §5, RULED weekly-quota-exhaustion):
# an LLMError whose message carries one of these is the subscription quota
# signalling exhaustion -- a GRACEFUL wave halt recorded in the ledger,
# never a crash.  Substring match over the lowercased message.
QUOTA_ERROR_MARKERS = (
    "rate limit", "rate_limit", "rate-limit", "quota", "usage limit",
    "out of tokens", "insufficient credit", "429",
)


class QuotaExhausted(Exception):
    """The CLI reported a quota / rate-limit condition.  Raised by the author
    and caught by the wave loop, which converts it into a recorded graceful
    halt (`halt_reason="quota-exhausted"`) -- never propagated further."""


def _is_quota_error(message: str) -> bool:
    m = (message or "").lower()
    return any(marker in m for marker in QUOTA_ERROR_MARKERS)


def _ts() -> str:
    """A recorded timestamp (UTC, ISO).  RECORDED ONLY -- nothing in this
    module ever compares two of these (the no-wall-clock house rule)."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat(
        timespec="seconds")


# ================================================================= author ===
def _llm_author(decl_name, statement_pp, macro_table, operator_registry, *,
                model=None):
    """The real author: render the import prompt (the direction-flip analogue
    of bench_formalize._llm_author), call the model once, return the reading
    JSON + the RETURNED usage token counts.  Returns None on an ordinary LLM
    error (an author failure -> the item is refused); raises QuotaExhausted
    when the CLI error is a quota/rate-limit signal (a graceful wave halt).

    A FAKE author with this identical signature is injected by the LLM-free
    tooth; nothing below this line ever imports an LLM module."""
    from buildloop import llm, math_prompt
    prompt = math_prompt.render_import_reading_prompt(
        decl_name, statement_pp, operator_registry, macro_table)
    # C6-v3 residual: ~15/wave author failures were transport-class (the
    # author returned None and the ledger lost the WHY).  One immediate
    # retry on a non-quota LLMError (a count, never wall-clock), and the
    # last error string rides back for the ledger row.
    last_err = None
    for attempt in (1, 2):
        try:
            # slim session: the authoring call needs text completion only.
            # The C5 readout measured 98.5% of wave spend as prompt-side
            # input, and ~26 of ~29 ktok/call was CLI session overhead
            # (default system prompt + tool schemas) -- the flags below cut
            # a probe call from 25,858 to 164 input tokens.  The E6 currency
            # is unchanged; the reality it measures shrank.
            out = llm.call_llm(prompt, model=model,
                               system_prompt=(
                                   "You transcribe formal Lean statements "
                                   "into MathReading JSON specifications. "
                                   "Reply with the JSON document only -- no "
                                   "prose, no markdown fences."),
                               no_tools=True)
            break
        except llm.LLMError as e:
            if _is_quota_error(str(e)):
                raise QuotaExhausted(str(e)[:500])
            last_err = f"LLMError (attempt {attempt}): {str(e)[:300]}"
            out = None
        except OSError as e:                          # missing binary
            return {"author_error": f"OSError: {str(e)[:200]}"}
    if out is None:
        return {"author_error": last_err or "author failed"}
    text = out["text"] if isinstance(out, dict) else out
    return {"reading_json": llm.strip_fences(text),
            "author_retries": 0 if last_err is None else 1,
            "tokens_in": out.get("input_tokens", 0)
            if isinstance(out, dict) else 0,
            "tokens_out": out.get("output_tokens", 0)
            if isinstance(out, dict) else 0,
            "model": out.get("model") if isinstance(out, dict) else None}


def _default_author(arm, model):
    """Bind the real author for `arm`: the admitted-operator registry is the
    prompt vocabulary (the E1 seam).  The macro table is threaded per call by
    run_wave -- the LIVE import table on the governed arm (B2 inline mining),
    always empty on the ungoverned arm."""
    from generators import operator_growth as _og
    registry = _og.load_admitted()

    def author(decl_name, statement_pp, macro_table, operator_registry,
               _m=model, _reg=registry):
        return _llm_author(decl_name, statement_pp, macro_table,
                           operator_registry if operator_registry is not None
                           else _reg, model=_m)
    return author


# ============================================================ grant check ===
def load_grant(path=None):
    """Read the USER-GATED grant artifact.  Missing / unparseable -> None."""
    p = pathlib.Path(path) if path else GRANT_PATH
    if not p.exists():
        return None
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return None
    return doc if isinstance(doc, dict) else None


def check_grant(grant, ledger_rows, *, today):
    """The plan-§6 grant check, as a PURE function of (grant, ledger, today).

    Refuses when: no grant; no/blank expiry; expired (ISO date-string
    comparison -- `today` is injected by the caller, captured ONCE at startup
    and recorded in the verdict; this is the single calendar gate the grant
    contract demands, never a loop decision); mode "fixed" with the
    ledger-decremented budget spent.  Mode "weekly-quota-exhaustion" has NO
    fixed total (RULED 2026-07-17) -- the quota signal is the stop."""
    if grant is None:
        return {"ok": False, "reason": "missing-grant", "today": today}
    expires = grant.get("expires")
    if not expires:
        return {"ok": False, "reason": "grant-has-no-expiry", "today": today}
    if str(today) > str(expires):
        return {"ok": False, "reason": "grant-expired",
                "expires": expires, "today": today}
    mode = grant.get("mode")
    if mode == "fixed":
        granted = float(grant.get("granted_ktokens") or 0.0)
        spent = ledger_spent_ktokens(ledger_rows)
        if spent >= granted:
            return {"ok": False, "reason": "grant-exhausted",
                    "granted_ktokens": granted, "ledger_spent_ktokens": spent,
                    "today": today}
        return {"ok": True, "mode": mode, "today": today,
                "remaining_ktokens": granted - spent}
    if mode == "weekly-quota-exhaustion":
        return {"ok": True, "mode": mode, "today": today,
                "remaining_ktokens": None}
    return {"ok": False, "reason": "unknown-grant-mode:%s" % mode,
            "today": today}


# ================================================================= ledger ===
def load_ledger(path):
    """Parse the append-only ledger.  Returns [] for a missing file."""
    p = pathlib.Path(path)
    rows = []
    if p.exists():
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


def ledger_spent_ktokens(ledger_rows) -> float:
    """Cumulative spend, from ITEM rows only (wave rows carry totals of the
    same item rows -- summing both would double-count)."""
    return sum(float(r.get("ktokens_in", 0.0)) + float(r.get("ktokens_out", 0.0))
               for r in ledger_rows if r.get("kind") == "item")


def ledger_wave_cost_history(ledger_rows):
    """The trailing cost history for P-LI1-COST: every prior wave row's
    positive `cost_per_certified_statement` (a wave with zero certified rows
    records no cost and contributes nothing to the median)."""
    out = []
    for r in ledger_rows:
        if r.get("kind") != "wave":
            continue
        c = (r.get("totals") or {}).get("cost_per_certified_statement")
        if isinstance(c, (int, float)) and c > 0:
            out.append(float(c))
    return out


class _Ledger:
    """Append-only single-writer JSONL ledger.  One canonical line per row,
    flushed per append (a kill loses at most the in-flight row).  There is NO
    truncate path -- `--fresh` re-keys the CHECKPOINT, never this file."""

    def __init__(self, path):
        self.path = str(path)
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self._fh = open(self.path, "a", encoding="utf-8")

    def append(self, row):
        self._fh.write(common.canonical_json(row) + "\n")
        self._fh.flush()

    def close(self):
        self._fh.close()


# ================================================================== queue ===
def load_queue(path):
    """Read the WP-LI0 queue (one row per declaration, frontier-ordered by
    P-LI0-ORDER at build time -- the driver TRUSTS the file order)."""
    p = pathlib.Path(path)
    rows = []
    for line in common.read_text_auto(p).splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_queue(path, rows):
    """Rewrite the queue with updated statuses, atomically (temp + rename) so
    a kill mid-write can never leave a torn queue.  Single-writer (plan §7:
    no concurrent authoring sessions in v1).  Deterministically gzipped when
    the path ends in .gz (common.encode_text_auto)."""
    p = pathlib.Path(path)
    tmp = p.with_suffix(p.suffix + ".tmp")
    text = "".join(common.canonical_json(r) + "\n" for r in rows)
    with open(tmp, "wb") as fh:
        fh.write(common.encode_text_auto(p, text))
    os.replace(tmp, p)
    return p


# =============================================================== breakers ===
def refusal_breaker_verdict(outcomes):
    """P-LI1-REFUSAL as a recorded verdict over this wave's outcome sequence:
    fires iff the trailing-REFUSAL_WINDOW refusal rate exceeds
    REFUSAL_RATE_MAX (and only once the window is full -- a 3-item wave
    cannot spike).  Verdict shape mirrors bench_metered's `_verdict` rows."""
    window = outcomes[-REFUSAL_WINDOW:]
    if len(window) < REFUSAL_WINDOW:
        rate = None
        fired = False
    else:
        rate = sum(1 for o in window if o == "refused") / float(len(window))
        fired = rate > REFUSAL_RATE_MAX
    return {"name": "P-LI1-REFUSAL",
            "expected": "trailing-%d refusal rate <= %s"
                        % (REFUSAL_WINDOW, REFUSAL_RATE_MAX),
            "observed": {"window": len(window), "refusal_rate": rate},
            "fired": fired, "pass": not fired}


def cost_breaker_verdict(wave_ktokens, wave_certified, history_costs,
                         wave_items=None):
    """P-LI1-COST as a recorded verdict: fires iff the wave-so-far
    cost_per_certified_statement exceeds COST_BLOWOUT_FACTOR x the median of
    the ledger's prior wave costs.  Kilotokens are the only currency (E6).
    With no history there is no median and the breaker cannot fire (the first
    wave defines the baseline).  `wave_items` (when given) arms the breaker
    only past COST_BREAKER_MIN_ITEMS -- in-wave evaluation hygiene."""
    med = statistics.median(history_costs) if history_costs else None
    cost = (wave_ktokens / wave_certified) if wave_certified > 0 else (
        float("inf") if wave_ktokens > 0 else 0.0)
    armed = (med is not None
             and (wave_items is None or wave_items >= COST_BREAKER_MIN_ITEMS))
    fired = bool(armed and cost > COST_BLOWOUT_FACTOR * med)
    return {"name": "P-LI1-COST",
            "expected": "wave cost_per_certified_statement <= %sx trailing "
                        "median" % COST_BLOWOUT_FACTOR,
            "observed": {"wave_cost": (None if cost == float("inf") else
                                       round(cost, 6)),
                         "wave_certified": wave_certified,
                         "trailing_median": med},
            "fired": fired, "pass": not fired}


# ======================================================== classification ====
def _declared_fragment_miss(reading_json):
    """The LLM's structured miss declaration (the import prompt's rule):
    {"fragment_miss": {"missing": [...]}} -> the missing-constant bins, or
    None when the payload is not a declared miss."""
    try:
        doc = json.loads(reading_json)
    except (ValueError, TypeError):
        return None
    if not isinstance(doc, dict):
        return None
    fm = doc.get("fragment_miss")
    if isinstance(fm, dict) and isinstance(fm.get("missing"), list):
        return [str(m) for m in fm["missing"]]
    return None


def _slug_theorem_name(decl_name):
    """Deterministic F-G-legal name for a Lean declaration: lowercase, dots
    and primes to underscores, must match math_reading's `_ID` rule
    (``[a-z][a-zA-Z0-9_]*``).  C6 root cause: the gate's FIRST check is the
    theorem-name rule, and raw Lean names (capitals, dots, primes) fail it
    before any quote is examined -- 22/22 pilot refusals were this, not
    groundedness (quotes of formal substrings pass verbatim)."""
    s = []
    for ch in decl_name:
        if ch.isalnum() and ch.isascii():
            s.append(ch.lower())
        else:
            s.append("_")
    slug = "".join(s).strip("_") or "imported"
    while "__" in slug:
        slug = slug.replace("__", "_")
    if not slug[0].isalpha():
        slug = "t_" + slug
    return slug


def _normalize_theorem_name(reading_json, statement_pp, decl_name=None):
    """Overwrite the reading's `theorem` field with the deterministic slug.
    The name is a LABEL (provenance lives in the ledger row's decl_name and
    statement_hash) -- normalizing it driver-side is metadata hygiene, never
    semantic repair: quotes, forces, and logical forms pass through
    untouched.  Unparseable JSON passes through for the gate to refuse."""
    try:
        doc = json.loads(reading_json)
    except (ValueError, TypeError):
        return reading_json
    if not isinstance(doc, dict):
        return reading_json
    doc["theorem"] = _slug_theorem_name(
        decl_name or str(doc.get("theorem") or "imported"))
    return common.canonical_json(doc)


def _classify(statement_pp, authored, event_sink=None):
    """Author result -> (outcome, stage, miss_bins, reading_hash, seconds).

    authored is None            -> refused (author failure).
    declared fragment_miss JSON -> fragment-miss with the declared bins.
    otherwise: the Lean-free gates of `certify_statement` run via
    bench_formalize._timed_certify (the fidelity pipeline is NEVER forked;
    the kernel statement-cert defers honestly in a Lean-absent container):
      ok            -> authored
      fragment-miss event fired -> fragment-miss, binned by the gate's
                                    missing_kind_guess (feeds WP-LI4)
      any other red -> refused."""
    from bench import bench_formalize as bench
    if authored is None or "reading_json" not in authored:
        return "refused", "author-failed", [], "", 0.0
    reading_json = authored.get("reading_json") or ""
    declared = _declared_fragment_miss(reading_json)
    if declared is not None:
        return ("fragment-miss", "declared-by-author", declared,
                common.sha256_bytes(reading_json.encode("utf-8")), 0.0)
    reading_json = _normalize_theorem_name(reading_json, statement_pp)

    miss_events = []

    def sink(kind, payload):
        if kind == "fragment-miss":
            miss_events.append(payload or {})
        if event_sink:
            event_sink(kind, payload)

    certified, stage, seconds = bench._timed_certify(
        statement_pp, reading_json, sink)
    rh = common.sha256_bytes(reading_json.encode("utf-8"))
    if certified:
        return "authored", stage or "fidelity-green", [], rh, seconds
    if miss_events:
        bins = sorted({str(e.get("missing_kind_guess"))
                       for e in miss_events if e.get("missing_kind_guess")})
        return "fragment-miss", stage, bins, rh, seconds
    return "refused", stage, [], rh, seconds


# ===================================================== reading persistence ==
def persist_reading(readings_dir, queue_row, reading_json, model_id,
                    gloss=None):
    """R2 (plan §2.5): provenance is the asset.  Persist the authored reading
    with its full chain {decl_name, statement_hash (the R1 anchor), gloss,
    reading, model_id, encoding_version}.  Returns the artifact path."""
    d = pathlib.Path(readings_dir)
    d.mkdir(parents=True, exist_ok=True)
    decl = queue_row["decl_name"]
    fname = decl.replace(os.sep, "_").replace("/", "_") + ".json"
    doc = {
        "decl_name": decl,
        "statement_hash": queue_row.get("statement_hash"),
        "gloss": gloss if gloss is not None else queue_row.get("gloss"),
        "reading": json.loads(reading_json),
        "model_id": model_id,
        "encoding_version": READING_ENCODING_VERSION,
    }
    p = d / fname
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(common.canonical_json(doc))
    return p


# ================================================ inline vocabulary mining ==
# B2 (plan §8.2).  The stage reuses the bench's machinery verbatim --
# recurrence.mine to propose, mdl_macros.macro_admission_decision to price and
# admit (the exact loop inside bench_formalize._greedy_grow, here unrolled so
# each admission's dl_before/dl_after/witnesses can be RECORDED), and
# bench_formalize._per_use_cert_counts for the governed per-use translation-
# cert counts.  Nothing about the pricing is forked.  All CPU, zero tokens.

def load_import_macros(path=None) -> list:
    """Read the append-only admission records from import_macros.json.
    Missing / unparseable -> [] (an empty table, never an error)."""
    p = pathlib.Path(path) if path else MACROS_PATH
    if not p.exists():
        return []
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return []
    recs = doc.get("admissions") if isinstance(doc, dict) else None
    return [r for r in recs if isinstance(r, dict)] \
        if isinstance(recs, list) else []


def macro_table_from_records(records) -> dict:
    """Rebuild the LIVE macro table {name: {name, params, body}} from the
    persisted admission records (record shape: `word` is the macro name)."""
    table = {}
    for rec in records:
        if rec.get("word") and isinstance(rec.get("body"), list):
            table[rec["word"]] = {"name": rec["word"],
                                  "params": list(rec.get("params") or []),
                                  "body": rec["body"]}
    return table


def load_macro_table(path=None) -> dict:
    """The wave-start table load: import_macros.json -> live macro table."""
    return macro_table_from_records(load_import_macros(path))


def _write_import_macros(path, records):
    """Persist the admission records, atomically (temp + rename) and
    deterministically (canonical JSON).  Append-only by CONTRACT: callers only
    ever pass the existing records plus new ones; nothing edits or removes a
    record."""
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    doc = {"note": "B2 (PLAN_LEAN_IMPORT.md §8.2): append-only admission "
                   "records for the import driver's inline vocabulary mining. "
                   "`word` is the macro name; the live table is rebuilt from "
                   "these records at wave start (import_driver."
                   "load_macro_table). dl_before/dl_after are "
                   "mdl_macros.macro_admission_decision's corpus-DL currency "
                   "at admission time; witnesses are authored Mathlib "
                   "declarations (every import reading is exogenous).",
           "admissions": records}
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(common.canonical_json(doc))
    os.replace(tmp, p)
    return p


def load_authored_readings(readings_dir, source_lookup=None) -> list:
    """The mining corpus: every persisted authored reading under
    `readings_dir` (the accumulated cross-wave corpus), as mining/pricing docs
    {theorem, statements, origin, decl_name, _source}.  origin is
    "exogenous" for ALL of them -- explicit B2 note: import readings are real
    Mathlib statements, there is no dream lane in this driver, so the bench's
    exogenous witness discipline is satisfied by construction.  `_source`
    (the formal statement_pp, via `source_lookup`) feeds the per-use
    translation-cert's request field.  Deterministic: sorted filenames;
    unparseable artifacts are skipped, never fatal."""
    d = pathlib.Path(readings_dir)
    docs = []
    if not d.is_dir():
        return docs
    for p in sorted(d.glob("*.json")):
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if not isinstance(doc, dict):
            continue
        reading = doc.get("reading")
        if not isinstance(reading, dict) \
                or not isinstance(reading.get("statements"), list):
            continue
        decl = doc.get("decl_name") or p.stem
        docs.append({"theorem": reading.get("theorem", "t"),
                     "statements": reading["statements"],
                     "origin": "exogenous",
                     "decl_name": decl,
                     "_source": (source_lookup or {}).get(decl, "")})
    return docs


def mine_admit_macros(corpus, table, *, wave_id):
    """Greedy mine -> price -> admit over `corpus` starting from `table` --
    bench_formalize._greedy_grow's loop with each admission RECORDED.  Returns
    (new_records, grown_table); `table` is not mutated.  Every admitted record
    carries the plan's admission-record fields: word, params, body,
    dl_before/dl_after/delta (the corpus-DL currency at admission time), uses,
    witness_decl_names, encoding_version, wave_id."""
    from bench import bench_formalize as bench
    from buildloop import recurrence, mdl_macros
    wfilter = bench._EXO           # trivially true here; discipline parity
    table = dict(table)
    records = []
    while True:
        cands = recurrence.mine(corpus, table, witness_filter=wfilter)
        chosen = decision = None
        for c in cands:
            cand = c["candidate"]
            if cand["name"] in table:
                continue
            d = mdl_macros.macro_admission_decision(
                corpus, cand, table, witness_filter=wfilter)
            if d["admit"]:
                chosen, decision = cand, d
                break
        if chosen is None:
            return records, table
        table[chosen["name"]] = chosen
        # witness decl_names: the readings that actually USE the macro under
        # the grown table (public corpus_dl reading_uses; greedy rewrite).
        witnesses = sorted(
            str(r.get("decl_name") or r.get("theorem"))
            for r in corpus
            if mdl_macros.corpus_dl([r], table)["reading_uses"]
                                    .get(chosen["name"], 0) > 0)
        records.append({
            "word": chosen["name"],
            "params": list(chosen.get("params") or []),
            "body": chosen["body"],
            "dl_before": decision["dl_before"],
            "dl_after": decision["dl_after"],
            "delta": decision["delta"],
            "uses": decision["uses"],
            "witness_decl_names": witnesses,
            "encoding_version": READING_ENCODING_VERSION,
            "wave_id": wave_id,
        })


def run_import_mining(readings_dir, macros_path, *, wave_id,
                      source_lookup=None, dl_baseline_table=None) -> dict:
    """ONE mining stage: load the accumulated corpus + persisted table, grow
    it greedily, persist new admissions (append-only), record the governed
    per-use translation-cert counts.  When `dl_baseline_table` is given (the
    wave-end call passes the WAVE-START table) the result also carries the
    per-wave DL instrumentation: corpus_dl_before/after = the mdl currency
    over the accumulated corpus recoded with the baseline vs the post-mining
    table.  Raises on internal failure -- the caller (run_wave) contains it
    as a kind:"mining-error" ledger row; authored work is already on disk."""
    from buildloop import mdl_macros
    corpus = load_authored_readings(readings_dir, source_lookup)
    records = load_import_macros(macros_path)
    table = macro_table_from_records(records)
    new_records, table = mine_admit_macros(corpus, table, wave_id=wave_id)
    if new_records:
        _write_import_macros(macros_path, records + new_records)
    if table:
        try:
            from bench import bench_formalize as bench
            tcert, tfail = bench._per_use_cert_counts(corpus, table)
        except Exception:            # cert pass unmeasurable, never fatal --
            tcert = tfail = None     # admissions above are already persisted
    else:
        tcert = tfail = 0
    out = {"corpus_readings": len(corpus),
           "admitted": new_records,
           "table": table,
           "macro_table_size": len(table),
           "translation_cert_count": tcert,
           "per_use_cert_failures": tfail}
    if dl_baseline_table is not None:
        out["corpus_dl_before"] = round(
            mdl_macros.corpus_dl(corpus, dl_baseline_table)["total"], 3)
        out["corpus_dl_after"] = round(
            mdl_macros.corpus_dl(corpus, table)["total"], 3)
    return out


# ================================================================ the wave ==
def run_wave(*, budget_ktokens, arm="ungoverned", author=None, model=None,
             queue_path=None, ledger_path=None, readings_dir=None,
             state_path=None, macros_path=None, fresh=False, grant_path=None,
             grant=None, today=None, event_sink=None, author_concurrency=1):
    """Run ONE authoring wave (Phase A).  Returns the summary dict; NEVER
    raises on budget / breaker / quota conditions -- those are recorded
    verdicts (`halt_reason` on the appended wave row).

    Loop (plan WP-LI1): while spent < B and frontier nonempty:
    pop -> author -> gate -> record.  Spend is measured ONLY from the
    author's returned usage-metadata token counts.  `author` (default the
    real LLM author) has signature
    ``author(decl_name, statement_pp, macro_table, operator_registry) ->
    {"reading_json", "tokens_in", "tokens_out"[, "model"]} | None`` and may
    raise QuotaExhausted -- the LLM-free tooth injects a deterministic fake
    with this signature.

    `author_concurrency` (latency lever, default 1 = the historical serial
    semantics byte-for-byte): author calls dispatch in batches of this size
    on a thread pool (each call is an independent subprocess), and results
    are recorded serially IN FRONTIER ORDER, so the ledger is deterministic
    given the same responses.  Consequences at >1, all recorded rather than
    estimated: the budget check runs per BATCH (overshoot bounded by one
    batch's spend); breaker/quota halts take effect at the batch boundary
    (every completed call's spend is recorded before the halt -- spend
    honesty over halt granularity); a batch's prompts all see the
    batch-start macro table (intra-wave mining applies between batches)."""
    from bench import bench_formalize as bench

    if arm not in ARMS:
        return {"status": "refused", "reason": "unknown-arm:%s" % arm}
    queue_path = pathlib.Path(queue_path) if queue_path else QUEUE_PATH
    ledger_path = pathlib.Path(ledger_path) if ledger_path else LEDGER_PATH
    readings_dir = pathlib.Path(readings_dir) if readings_dir else READINGS_DIR
    state_path = pathlib.Path(state_path) if state_path else STATE_PATH
    macros_path = pathlib.Path(macros_path) if macros_path else MACROS_PATH
    # `today` is captured ONCE, here, for the grant expiry gate only (plan §5)
    # -- recorded in the verdict, never consulted again.
    today = today or datetime.date.today().isoformat()

    ledger_rows = load_ledger(ledger_path)
    if grant is None:
        grant = load_grant(grant_path)
    grant_verdict = check_grant(grant, ledger_rows, today=today)
    if not grant_verdict["ok"]:
        return {"status": "refused", "reason": grant_verdict["reason"],
                "grant_verdict": grant_verdict}
    if not queue_path.exists():
        return {"status": "refused", "reason": "missing-queue",
                "queue_path": str(queue_path)}

    # Effective per-wave budget: the CLI budget, capped by the grant's
    # per-wave cap (checkpoint hygiene, plan §5) and -- in fixed mode -- by
    # the ledger-decremented remainder.  All kilotokens, nothing else (E6).
    budget = float(budget_ktokens)
    cap = grant.get("per_wave_cap_ktokens")
    if isinstance(cap, (int, float)) and cap > 0:
        budget = min(budget, float(cap))
    remaining = grant_verdict.get("remaining_ktokens")
    if remaining is not None:
        budget = min(budget, float(remaining))
    if budget <= 0:
        return {"status": "refused", "reason": "no-budget",
                "grant_verdict": grant_verdict}

    if author is None:
        author = _default_author(arm, model)

    queue = load_queue(queue_path)
    # P-LI0-ORDER: the CI-committed queue is enumerator-ordered (module,
    # decl_name); the frontier the wave consumes is the census-derived order
    # -- in-fragment rows first, then single-blocker by unlock weight.  A
    # pure function of (queue, census); applied at load, never persisted, so
    # the committed artifact stays byte-identical to the enumerator's output.
    # No census file -> file order stands (the dry/test fixtures' case).
    from buildloop import census as _census
    if _census.CENSUS_PATH.exists():
        queue = _census.frontier_order(
            queue, json.load(open(_census.CENSUS_PATH)))
    by_decl = {r["decl_name"]: r for r in queue}
    frontier = [r for r in queue if r.get("status") == "pending"]

    checkpoint = bench._Checkpoint(state_path, fresh=fresh)
    ledger = _Ledger(ledger_path)
    ledger_seen = {(r.get("decl_name"), r.get("arm"))
                   for r in ledger_rows if r.get("kind") == "item"}
    wave_id = sum(1 for r in ledger_rows if r.get("kind") == "wave")
    cost_history = ledger_wave_cost_history(ledger_rows)

    spent_kt_in = spent_kt_out = 0.0
    outcomes = []               # this wave's outcome sequence (breaker input)
    items = []                  # this wave's ledger item rows
    seconds_total = 0.0         # reported beside, never summed into cost (E6)
    miss_histogram = {}
    halt_reason = None
    breakers = [refusal_breaker_verdict([]),
                cost_breaker_verdict(0.0, 0, cost_history, wave_items=0)]

    # ---- B2 inline mining state (governed arm only) -------------------------
    mining_on = _mining_enabled(arm)
    live_table = load_macro_table(macros_path) if mining_on else {}
    table_at_wave_start = dict(live_table)      # the per-wave DL baseline
    source_pp = {r["decl_name"]: r.get("statement_pp", "") for r in queue}
    wave_admissions = []        # this wave's admission records (all stages)
    mining_info = None          # the LAST successful mining-stage result
    mining_errors = 0
    authored_since_mine = 0

    def _mining_stage(stage_label, *, dl_baseline=None):
        """Run one mining stage with FAILURE CONTAINMENT: an exception can
        never lose authored work (readings + item rows are already on disk);
        it lands as a first-class kind:"mining-error" ledger row and the wave
        completes.  Mining is CPU -- every row records ktokens 0.0 (never
        estimated)."""
        nonlocal live_table, mining_info, mining_errors
        try:
            res = run_import_mining(readings_dir, macros_path,
                                    wave_id=wave_id, source_lookup=source_pp,
                                    dl_baseline_table=dl_baseline)
        except Exception as e:
            mining_errors += 1
            ledger.append({"kind": "mining-error", "wave_id": wave_id,
                           "arm": arm, "stage": stage_label,
                           "error": "%s: %s" % (type(e).__name__,
                                                str(e)[:400]),
                           "ktokens_in": 0.0, "ktokens_out": 0.0,
                           "ts": _ts()})
            return None
        live_table = res["table"]
        for rec in res["admitted"]:
            wave_admissions.append(rec)
            row = {"kind": "admission", "arm": arm, "stage": stage_label,
                   "ktokens_in": 0.0, "ktokens_out": 0.0, "ts": _ts()}
            row.update(rec)     # word/params/body/dl_*/uses/witnesses/...
            ledger.append(row)
        mining_info = res
        return res

    def _bill(rec):
        nonlocal spent_kt_in, spent_kt_out
        spent_kt_in += rec["ktokens_in"]
        spent_kt_out += rec["ktokens_out"]

    def _apply_outcome(qrow, outcome):
        qrow["status"] = outcome            # authored | refused | fragment-miss

    def _record_item(qrow, authored):
        """The serial per-item recording path: classify -> checkpoint ->
        ledger -> bill -> mining trigger -> breaker evaluation.  Runs in
        FRONTIER ORDER regardless of dispatch concurrency, and sets
        halt_reason instead of breaking so a batch's remaining completed
        calls still record their spend (spend honesty over halt
        granularity; at author_concurrency=1 this is byte-identical to the
        historical immediate break -- a batch holds one item)."""
        nonlocal seconds_total, authored_since_mine, halt_reason, breakers
        decl = qrow["decl_name"]
        outcome, stage, miss_bins, reading_hash, secs = _classify(
            qrow.get("statement_pp", ""), authored, event_sink)
        seconds_total += secs
        tin = int((authored or {}).get("tokens_in", 0))
        tout = int((authored or {}).get("tokens_out", 0))
        model_id = (authored or {}).get("model") or model
        if model_id is None:
            from buildloop import llm as _llm
            model_id = _llm.DEFAULT_MODEL

        item_row = {
            "kind": "item",
            "decl_name": decl,
            "statement_hash": qrow.get("statement_hash"),   # the R1 anchor
            "arm": arm,
            "outcome": outcome,
            "stage": stage,
            "miss_bins": miss_bins,
            "ktokens_in": round(tin / 1000.0, 6),
            "ktokens_out": round(tout / 1000.0, 6),
            "reading_hash": reading_hash,
            "encoding_version": READING_ENCODING_VERSION,
            "wave_id": wave_id,
            "ts": _ts(),                    # recorded, never compared
        }
        if isinstance(authored, dict) and authored.get("author_error"):
            item_row["author_error"] = authored["author_error"]
        if isinstance(authored, dict) and authored.get("author_retries"):
            item_row["author_retries"] = authored["author_retries"]
        # checkpoint FIRST (single-writer resume key), ledger append second;
        # the resume path above replays a lost ledger append from this record.
        checkpoint.write({"source_id": decl, "arm": arm, "outcome": outcome,
                          "ledger_row": item_row})
        ledger.append(item_row)
        ledger_seen.add((decl, arm))
        items.append(item_row)
        outcomes.append(outcome)
        _bill(item_row)
        for b in miss_bins:
            miss_histogram[b] = miss_histogram.get(b, 0) + 1

        if outcome == "authored":
            # Persist EXACTLY what was certified: _classify normalizes the
            # theorem name before the gates run, so the artifact must carry
            # the same bytes (R2: the persisted reading IS the certified
            # reading).  First RT run failed 33/35 on this divergence -- the
            # raw pre-normalization bytes had been persisted.
            persist_reading(readings_dir, qrow,
                            _normalize_theorem_name(
                                authored["reading_json"],
                                qrow.get("statement_pp", "")),
                            model_id)
            # ---- B2 intra-wave mining: every K authored rows ----------------
            authored_since_mine += 1
            if mining_on and authored_since_mine >= MINE_EVERY_K_AUTHORED:
                authored_since_mine = 0
                _mining_stage("intra-wave")
        _apply_outcome(by_decl[decl], outcome)

        # ---- stop condition (c): registered breakers (recorded verdicts);
        # once halted, later batch-mates only record spend -- the verdict
        # list stays as of the halt moment ---------------------------------
        if halt_reason is None:
            certified = sum(1 for o in outcomes if o == "authored")
            breakers = [
                refusal_breaker_verdict(outcomes),
                cost_breaker_verdict(spent_kt_in + spent_kt_out, certified,
                                     cost_history, wave_items=len(outcomes)),
            ]
            fired = next((b for b in breakers if b["fired"]), None)
            if fired is not None:
                halt_reason = "breaker:" + fired["name"]

    def _author_one(qrow):
        """Thread-mapped author dispatch: (qrow, authored|None, quota|None).
        Each call is an independent `claude -p` subprocess; the thread pool
        only overlaps their wall-clock waits.  The macro table snapshot is
        taken per call exactly as the serial path did (dict copy)."""
        try:
            return (qrow, author(qrow["decl_name"],
                                 qrow.get("statement_pp", ""),
                                 dict(live_table), None), None)
        except QuotaExhausted as e:
            return (qrow, None, e)

    _idx = 0
    while _idx < len(frontier) and halt_reason is None:
        # ---- assemble the next dispatch batch (resume rows replay inline) ---
        batch = []
        while _idx < len(frontier) and len(batch) < max(1, author_concurrency):
            qrow = frontier[_idx]
            _idx += 1
            decl = qrow["decl_name"]
            # ---- resume: a checkpointed decl is NEVER re-authored -----------
            if checkpoint.has(decl, arm):
                rec = checkpoint.get(decl, arm)
                _apply_outcome(by_decl[decl], rec["outcome"])
                if (decl, arm) not in ledger_seen:
                    # crash window replay: checkpoint written, ledger append
                    # lost -- re-append the recorded row (append-only stays
                    # honest; its tokens re-enter the grant decrement
                    # naturally).
                    ledger.append(rec["ledger_row"])
                    ledger_seen.add((decl, arm))
                continue
            batch.append(qrow)
        if not batch:
            continue

        # ---- stop condition (a): budget, usage-metadata-derived only, per
        # batch (serial default = per item, the historical semantics) --------
        if (spent_kt_in + spent_kt_out) >= budget:
            halt_reason = "budget-exhausted"
            break

        # ---- author (stop condition (d): quota -> graceful halt) ------------
        # The LIVE macro table (B2, the E1 seam) enters the prompt on the
        # governed arm; the ungoverned arm always authors with an empty table.
        if len(batch) == 1:
            results = [_author_one(batch[0])]
        else:
            import concurrent.futures as _futures
            with _futures.ThreadPoolExecutor(
                    max_workers=max(1, author_concurrency)) as _pool:
                results = list(_pool.map(_author_one, batch))

        # ---- record IN FRONTIER ORDER; every completed call's spend lands
        # before any halt takes effect (spend honesty over halt granularity) --
        quota_exc = None
        for qrow, authored, qexc in results:
            decl = qrow["decl_name"]
            if qexc is not None:
                # RULED weekly-quota-exhaustion (plan §5): the quota signal is
                # a graceful wave halt RECORDED in the ledger, never a crash.
                # The decl stays pending for the next wave (quota resets
                # weekly).  No spend to record for this call.
                quota_exc = quota_exc or qexc
                continue
            _record_item(qrow, authored)

        if quota_exc is not None and halt_reason is None:
            halt_reason = "quota-exhausted"
            breakers.append({"name": "quota-signal",
                             "expected": "no CLI quota/rate-limit error",
                             "observed": str(quota_exc)[:300],
                             "fired": True, "pass": False})

    checkpoint.close()

    # ---- stop condition (b): frontier empty (nothing halted us earlier) -----
    if halt_reason is None:
        halt_reason = "frontier-empty"

    # ---- B2 wave-end mining (unconditional on the governed arm: it also
    # runs after a budget/breaker/quota halt -- mining is CPU, never spend).
    # The wave-start table is the DL baseline, so corpus_dl_before/after on
    # the wave row is the accumulated corpus recoded with the table as it
    # stood before vs after this wave's admissions.
    if mining_on:
        _mining_stage("wave-end", dl_baseline=table_at_wave_start)

    certified = sum(1 for o in outcomes if o == "authored")
    kt_total = round(spent_kt_in + spent_kt_out, 6)
    frontier_remaining = sum(1 for r in queue if r.get("status") == "pending")
    totals = {
        "items": len(items),
        "authored": certified,
        "refused": sum(1 for o in outcomes if o == "refused"),
        "fragment_miss": sum(1 for o in outcomes if o == "fragment-miss"),
        "ktokens_in": round(spent_kt_in, 6),
        "ktokens_out": round(spent_kt_out, 6),
        "ktokens_total": kt_total,
        # E6: kilotokens are the ONLY cost currency; seconds sit BESIDE.
        "cost_per_certified_statement": (round(kt_total / certified, 6)
                                         if certified else 0.0),
        "gate_seconds": round(seconds_total, 6),
    }
    # B2 per-wave DL instrumentation.  Across waves the (corpus_dl,
    # macro_table_size) series is the compounding trajectory the experiment
    # exists to measure.  Ungoverned: mining OFF, DL fields null, zero
    # admissions -- recorded truthfully, never estimated.
    corpus_dl_before = (mining_info or {}).get("corpus_dl_before")
    corpus_dl_after = (mining_info or {}).get("corpus_dl_after")
    macro_table_size = (mining_info["macro_table_size"] if mining_info
                        else (len(live_table) if mining_on else 0))
    wave_row = {
        "kind": "wave",
        "wave_id": wave_id,
        "arm": arm,
        "arm_config": ARM_CONFIGS[arm],
        "grant_mode": grant.get("mode"),
        "budget_ktokens_effective": budget,
        "totals": totals,
        "breaker_verdicts": breakers,       # the plan-§6 recorded verdicts
        "halt_reason": halt_reason,
        "miss_histogram": miss_histogram,       # feeds WP-LI4
        "frontier_remaining": frontier_remaining,
        "corpus_dl_before": corpus_dl_before,       # B2: the mdl currency over
        "corpus_dl_after": corpus_dl_after,         # the accumulated corpus
        "macros_admitted_this_wave": len(wave_admissions),
        "macro_table_size": macro_table_size,
        "mining": {
            "enabled": mining_on,
            "mine_every_k_authored": (MINE_EVERY_K_AUTHORED if mining_on
                                      else None),
            "corpus_readings": (mining_info or {}).get("corpus_readings"),
            "translation_cert_count":
                (mining_info or {}).get("translation_cert_count"),
            "per_use_cert_failures":
                (mining_info or {}).get("per_use_cert_failures"),
            "mining_errors": mining_errors,
            # mining is CPU; its spend is RECORDED zero, never estimated.
            "ktokens": 0.0,
        },
        "ts": _ts(),                            # recorded, never compared
    }
    ledger.append(wave_row)
    ledger.close()
    write_queue(queue_path, queue)

    return {"status": "completed", "halt_reason": halt_reason,
            "wave_id": wave_id, "arm": arm, "totals": totals,
            "breakers": breakers, "items": items, "wave_row": wave_row,
            "spent_ktokens": kt_total, "frontier_remaining": frontier_remaining,
            "corpus_dl_before": corpus_dl_before,
            "corpus_dl_after": corpus_dl_after,
            "macros_admitted": wave_admissions,
            "macro_table_size": macro_table_size,
            "queue_path": str(queue_path), "ledger_path": str(ledger_path),
            "readings_dir": str(readings_dir), "state_path": str(state_path),
            "macros_path": str(macros_path),
            "grant_verdict": grant_verdict}


# ==================================================================== main ==
def main(argv=None) -> int:
    """CLI entry (wired as `cgb import`).  Interlock first (bench_metered's,
    verbatim), grant + queue checks inside run_wave.  Exit 0 on a completed
    or deliberately skipped wave; exit 2 on a refusal AFTER the user
    confirmed spend (a confirmed run against an invalid grant / missing
    queue is a condition a scheduling lane must notice)."""
    import argparse
    argv = list(sys.argv[1:] if argv is None else argv)
    if not _spend_confirmed(argv):
        print("SKIP cgb import: spend NOT confirmed.")
        print("  An import wave is REAL SPEND.  Re-run with "
              f"{_CONFIRM_SPEND_FLAG} (or {_CONFIRM_SPEND_ENV}=1):")
        print(f"    python3 cgb.py import --budget-ktokens B "
              f"{_CONFIRM_SPEND_FLAG} [--fresh] [--arm ARM] [--queue PATH]")
        print("  The interlock AND a valid specs/ops/spend_grant.json are "
              "both required (plan §5) -- an accidental invocation can "
              "never spend.")
        return 0

    p = argparse.ArgumentParser(prog="cgb import")
    p.add_argument("--budget-ktokens", type=float, required=True,
                   dest="budget_ktokens")
    p.add_argument(_CONFIRM_SPEND_FLAG, action="store_true",
                   dest="confirm_spend")
    p.add_argument("--fresh", action="store_true")
    p.add_argument("--arm", choices=list(ARMS), default="ungoverned")
    p.add_argument("--queue", default=None)
    p.add_argument("--model", default=None)
    args = p.parse_args(argv)

    summary = run_wave(budget_ktokens=args.budget_ktokens, arm=args.arm,
                       queue_path=args.queue, fresh=args.fresh,
                       model=args.model)
    if summary.get("status") == "refused":
        print("REFUSED cgb import:", summary["reason"])
        print(json.dumps(summary, indent=2, default=str))
        return 2
    print(json.dumps({k: summary.get(k) for k in (
        "status", "halt_reason", "wave_id", "arm", "totals",
        "frontier_remaining", "spent_ktokens", "ledger_path",
        "corpus_dl_before", "corpus_dl_after", "macros_admitted",
        "macro_table_size", "macros_path")}, indent=2, default=str))
    print("\nbreaker verdicts:")
    for b in summary["breakers"]:
        print(f"  [{'FIRED' if b['fired'] else 'ok   '}] {b['name']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
