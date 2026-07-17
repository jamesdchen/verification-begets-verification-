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

# The ab-pilot-then-cheaper ruling (plan §5): the arm is RECORDED per row and
# selects the authoring-variant flag; v1 authoring is otherwise identical
# (straight authoring, NO macro mining in the driver -- mining/per-emission
# certs are the arms' downstream discipline, mirrored from bench_metered's
# ARMS configs and recorded here so the ledger rows are self-describing).
ARM_CONFIGS = {
    "governed": {"authoring_vocabulary": "exogenous-only (admitted operator "
                                         "registry -- the E1 seam)",
                 "mining": "none-in-driver (per-emission certs discipline "
                           "downstream)",
                 "per_emission_certs": True},
    "ungoverned": {"authoring_vocabulary": "all-origins",
                   "mining": "none-in-driver",
                   "per_emission_certs": False},
}

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
    try:
        # slim session: the authoring call needs text completion only.  The
        # C5 readout measured 98.5% of wave spend as prompt-side input, and
        # ~26 of ~29 ktok/call was CLI session overhead (default system
        # prompt + tool schemas) -- the flags below cut a probe call from
        # 25,858 to 164 input tokens.  The E6 currency is unchanged; the
        # reality it measures shrank.
        out = llm.call_llm(prompt, model=model,
                           system_prompt=(
                               "You transcribe formal Lean statements into "
                               "MathReading JSON specifications. Reply with "
                               "the JSON document only -- no prose, no "
                               "markdown fences."),
                           no_tools=True)
    except llm.LLMError as e:
        if _is_quota_error(str(e)):
            raise QuotaExhausted(str(e)[:500])
        return None
    except OSError:                                   # missing binary
        return None
    text = out["text"] if isinstance(out, dict) else out
    return {"reading_json": llm.strip_fences(text),
            "tokens_in": out.get("input_tokens", 0)
            if isinstance(out, dict) else 0,
            "tokens_out": out.get("output_tokens", 0)
            if isinstance(out, dict) else 0,
            "model": out.get("model") if isinstance(out, dict) else None}


def _default_author(arm, model):
    """Bind the real author for `arm`: the admitted-operator registry is the
    prompt vocabulary (the E1 seam); the macro table is EMPTY in v1 (straight
    authoring -- no mining in the driver, plan WP-LI1)."""
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
    import bench_formalize as bench
    if authored is None:
        return "refused", "author-failed", [], "", 0.0
    reading_json = authored.get("reading_json") or ""
    declared = _declared_fragment_miss(reading_json)
    if declared is not None:
        return ("fragment-miss", "declared-by-author", declared,
                common.sha256_bytes(reading_json.encode("utf-8")), 0.0)

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


# ================================================================ the wave ==
def run_wave(*, budget_ktokens, arm="ungoverned", author=None, model=None,
             queue_path=None, ledger_path=None, readings_dir=None,
             state_path=None, fresh=False, grant_path=None, grant=None,
             today=None, event_sink=None):
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
    with this signature."""
    import bench_formalize as bench

    if arm not in ARMS:
        return {"status": "refused", "reason": "unknown-arm:%s" % arm}
    queue_path = pathlib.Path(queue_path) if queue_path else QUEUE_PATH
    ledger_path = pathlib.Path(ledger_path) if ledger_path else LEDGER_PATH
    readings_dir = pathlib.Path(readings_dir) if readings_dir else READINGS_DIR
    state_path = pathlib.Path(state_path) if state_path else STATE_PATH
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

    def _bill(rec):
        nonlocal spent_kt_in, spent_kt_out
        spent_kt_in += rec["ktokens_in"]
        spent_kt_out += rec["ktokens_out"]

    def _apply_outcome(qrow, outcome):
        qrow["status"] = outcome            # authored | refused | fragment-miss

    for qrow in frontier:
        decl = qrow["decl_name"]

        # ---- resume: a checkpointed decl is NEVER re-authored ---------------
        if checkpoint.has(decl, arm):
            rec = checkpoint.get(decl, arm)
            _apply_outcome(by_decl[decl], rec["outcome"])
            if (decl, arm) not in ledger_seen:
                # crash window replay: checkpoint written, ledger append lost
                # -- re-append the recorded row (append-only stays honest;
                # its tokens re-enter the grant decrement naturally).
                ledger.append(rec["ledger_row"])
                ledger_seen.add((decl, arm))
            continue

        # ---- stop condition (a): budget, usage-metadata-derived only --------
        if (spent_kt_in + spent_kt_out) >= budget:
            halt_reason = "budget-exhausted"
            break

        # ---- author (stop condition (d): quota -> graceful halt) ------------
        try:
            authored = author(decl, qrow.get("statement_pp", ""), {}, None)
        except QuotaExhausted as e:
            # RULED weekly-quota-exhaustion (plan §5): the quota signal is a
            # graceful wave halt RECORDED in the ledger, never a crash.  The
            # decl stays pending for the next wave (quota resets weekly).
            halt_reason = "quota-exhausted"
            breakers.append({"name": "quota-signal",
                             "expected": "no CLI quota/rate-limit error",
                             "observed": str(e)[:300],
                             "fired": True, "pass": False})
            break

        outcome, stage, miss_bins, reading_hash, secs = _classify(
            qrow.get("statement_pp", ""), authored, event_sink)
        seconds_total += secs
        tin = int(authored["tokens_in"]) if authored else 0
        tout = int(authored["tokens_out"]) if authored else 0
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
            persist_reading(readings_dir, qrow, authored["reading_json"],
                            model_id)
        _apply_outcome(by_decl[decl], outcome)

        # ---- stop condition (c): registered breakers (recorded verdicts) ----
        certified = sum(1 for o in outcomes if o == "authored")
        breakers = [
            refusal_breaker_verdict(outcomes),
            cost_breaker_verdict(spent_kt_in + spent_kt_out, certified,
                                 cost_history, wave_items=len(outcomes)),
        ]
        fired = next((b for b in breakers if b["fired"]), None)
        if fired is not None:
            halt_reason = "breaker:" + fired["name"]
            break

    checkpoint.close()

    # ---- stop condition (b): frontier empty (nothing halted us earlier) -----
    if halt_reason is None:
        halt_reason = "frontier-empty"

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
        "ts": _ts(),                            # recorded, never compared
    }
    ledger.append(wave_row)
    ledger.close()
    write_queue(queue_path, queue)

    return {"status": "completed", "halt_reason": halt_reason,
            "wave_id": wave_id, "arm": arm, "totals": totals,
            "breakers": breakers, "items": items, "wave_row": wave_row,
            "spent_ktokens": kt_total, "frontier_remaining": frontier_remaining,
            "queue_path": str(queue_path), "ledger_path": str(ledger_path),
            "readings_dir": str(readings_dir), "state_path": str(state_path),
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
    print(json.dumps({k: summary[k] for k in (
        "status", "halt_reason", "wave_id", "arm", "totals",
        "frontier_remaining", "spent_ktokens", "ledger_path")}, indent=2))
    print("\nbreaker verdicts:")
    for b in summary["breakers"]:
        print(f"  [{'FIRED' if b['fired'] else 'ok   '}] {b['name']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
