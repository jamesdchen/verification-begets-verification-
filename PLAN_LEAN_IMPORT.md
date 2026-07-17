# PLAN_LEAN_IMPORT.md — converting token spend into importing+translating the Lean library

Status: DRAFT — design for the standing operation that turns an authorized
token budget into machine-spun import/translation waves over Mathlib at the
pinned commit. Spend is USER-GATED throughout (house rule carried from
§12.5/§12.8/§13.8 of COMPRESSION.md). Nothing in this document authorizes a
single metered token.

House rules as in PLAN_COMBINED_LOOP.md §2, plus the COMPRESSION.md §13.6
discipline: every gate below is a registered predicate a tool evaluates or a
tooth CI runs — none exists only as prose.

---

## 0. What "the entire Lean library" honestly means here

Mathlib at the pin (`.lean-pins`: mathlib4 `9837ca9d…`, Lean `v4.15.0`) is on
the order of 5,000 modules and 10^5 declarations. The current fragment (F-G:
Nat/Int arithmetic, dvd/even/odd/gcd/coprime/mod, ∀, bounded-shadow ∃ —
`generators/math_reading.py`) can hold a sliver of it; `Prime` and `Real` are
*deliberately* absent from the import surface (`common.MATHLIB_IMPORTS`).

So "import the entire library" is not a finish line, it is a **frontier
operation**: enumerate the whole library once (cheap, deterministic), translate
the slice the fragment can hold (metered), let the misses — first-class
`fragment-miss` data, never bugs — drive priced vocabulary growth
(`generators/operator_growth.py`), and re-attempt as the fragment expands.
Success is measured as frontier progress per kilotoken, never as "percent of
Mathlib done." The arithmetic that forbids the naive reading: at the measured
ungoverned rate (~55 ktok/certified statement, `results/metered_evidence/
metered_run.json`) 10^5 declarations is ~5.5×10^9 tokens. No grant of that
size will be requested; the frontier framing is the honest one.

## 1. Verified current-state facts (what exists / what is missing)

Facts checked in-repo; the operation builds only what is actually missing.

**Exists:**
- F1.1 A 6-stage fidelity pipeline per statement:
  `run/formalize.py::certify_statement` (groundedness gate → dual-solver
  nonvacuity → compile to Lean `:= sorry` → deferred statement-cert →
  instance replay → optional examiner). Deterministic, resumable use in
  `bench_formalize.py` (`_Checkpoint`, single-writer JSONL, `--fresh`).
- F1.2 Real token accounting at the only LLM chokepoint:
  `buildloop/llm.py::call_llm` returns `input_tokens`/`output_tokens` from
  usage metadata; `buildloop/loop.py` bills them into registry counters
  (`llm_input_tokens`, `llm_output_tokens`). Headline cost metric exists:
  `cost_per_certified_statement` (`bench_metered.py`, E6 rule: kilotokens
  only, verifier seconds reported beside, never summed).
- F1.3 A spend interlock: `bench_metered.py` skips unless `--confirm-spend`
  or `CGB_METERED_CONFIRM_SPEND=1` — consent is explicit, per-invocation.
- F1.4 The Lean kernel legs, gated: statement-cert / proof-cert /
  exists-anchor-cert mint only under `common.lean_available()`; CI lanes
  `[lean-ci]` / `[lean-smoke]` / `[lean-fresh]` carry the ~5 GB toolchain
  keyed on `.lean-pins`; weekly cron recertifies the pin.
- F1.5 Priced vocabulary growth: `operator_growth.admit_operator` with the
  2-exogenous-witness + strict-DL-descent gate; admitted rows persist to
  `specs/mathsources/operators/admitted.json` (currently 5 admitted).

**Missing (the four gaps this plan fills):**
- G1 **No budget primitive.** Nothing converts "N tokens" into "run until
  spent." No code reads the cumulative token counters to stop.
- G2 **No outer driver.** `cgb build` = one iteration; `run_experiment` =
  fixed iteration cap. No `while under_budget and queue nonempty` loop.
- G3 **No declaration intake.** The unit of work is a `MathReading` authored
  from a natural-language sentence. There is no path that ingests a Mathlib
  declaration.
- G4 **No standing operation.** The only cron is the weekly Lean recert.
  Nothing spins the machine up on a schedule against a queue.

## 2. The direction flip, and why import is the *better*-anchored problem

The existing corpus runs NL → reading → compiled Lean, and fidelity is argued
by gates because no formal ground truth exists for an English sentence.
Mathlib import runs the other way: the **source object is already formal**.
Per declaration `d` the LLM authors a `MathReading` *of d's statement*, and
the oracle is a **round-trip differential** no NL source can offer:

> RT(d): `math_compile(reading)` elaborates, and the compiled statement is
> provably equivalent to `d`'s statement — checked in the Lean lane by
> elaborating `theorem rt : (compiled) ↔ (d.statement) := Iff.rfl` (defeq
> fast path) with an `exact?`-free constant-unfold fallback; failure of both
> is a refusal, never a warning.

This makes every imported row *stronger* evidence than the NL corpus rows:
the translation is certified against the library's own statement, under the
same dual-channel discipline (fidelity gates ∧ kernel leg). Informalization
(decl → English gloss) is recorded as provenance for the reading prompt, but
the cert subject is the Lean statement hash — the gloss is never load-bearing.

## 3. The operation, defined

Token spend converts to work through four layers, each independently
auditable:

```
 spend grant (USER-GATED artifact)            specs/ops/spend_grant.json
   └─ spins up → sessions (Routine/cron)      one wave per firing
        └─ each runs → the budgeted driver    cgb import --budget-ktokens B
             └─ which consumes → the queue    specs/mathsources/mathlib/queue.jsonl
                  └─ and appends → the ledger results/import_ledger.jsonl (append-only)
```

**Two-phase split (matches the repo's existing seam).** Authoring is
token-heavy and Lean-free; kernel certification is token-free and Lean-heavy.
So:
- **Phase A (authoring wave, any container):** driver pops frontier items,
  LLM authors readings, runs the Lean-free fidelity gates
  (`certify_statement` stages 1–2, 4; statement-cert deferred), writes
  candidate rows + witness ladders, bills tokens, stops at budget.
- **Phase B (certification wave, Lean lane only):** a `[lean-ci]`-marked
  commit (or the weekly cron extended) replays candidate rows through the
  kernel legs — statement-cert, RT(d) differential, proof-cert where the
  witness ladder closes — and flips row status. Zero LLM calls (the
  `CGB_TASK_TIME` guard is set for the whole phase; certification is
  task-time).

A row is **imported** only when both phases agree — the same dual-channel
rule as everywhere else in the repo.

## 4. Work packages

### WP-LI0 — the queue (deterministic, one-time per pin)
A Lean meta-program run at setup time in the Lean lane enumerates
declarations of the import surface (start: the 6 pinned modules in
`common.MATHLIB_IMPORTS`; widen module-by-module later — widening is a
`.lean-pins`-adjacent, cache-rekeying event and is USER-GATED). Output:
`specs/mathsources/mathlib/queue.jsonl`, one row per decl:
`{decl_name, module, statement_pp, statement_hash, status}` with
`status ∈ {pending, authored, imported, refused, fragment-miss, divergent}`.
Frontier order is a registered predicate (`P-LI0-ORDER`): rows whose
pretty-printed statement mentions only F-G-resident constants sort first;
the order is a pure function of the queue file, so any two runs agree.
Tooth: queue regeneration at the same pin is byte-identical.

### WP-LI1 — the budget primitive + outer driver (fills G1, G2)
New `cgb import` subcommand:
`python3 cgb.py import --budget-ktokens B --confirm-spend [--fresh]`.
Loop: `while spent < B and frontier nonempty:` pop → author → gate → record.
- Spend is measured ONLY from `call_llm` returned usage (F1.2); no estimates.
- Interlock: refuses without `--confirm-spend`/`CGB_METERED_CONFIRM_SPEND=1`
  AND a valid, unexhausted `specs/ops/spend_grant.json` (§5). Both, not either.
- Checkpoint: `bench_formalize._Checkpoint`-style single-writer JSONL keyed
  on `decl_name`; resumable; `--fresh` re-keys.
- Circuit breakers (registered predicates, evaluated per wave):
  `P-LI1-REFUSAL`: trailing-20 refusal rate > 60% → halt wave, bin misses.
  `P-LI1-COST`: wave `cost_per_certified_statement` > 3× trailing median →
  halt wave, flag for readout. Halts are recorded verdicts, not crashes.
- House-rule compliance: no wall-clock enters any decision (budget is
  tokens); the driver is fixed code (LLM authors readings only — the
  `buildloop/validate.py` discipline unchanged).

### WP-LI2 — the RT differential oracle (fills G3's trust half)
The Lean-lane check from §2. Subject = `(reading_hash, statement_hash)`;
cert = the existing statement-cert contract extended with a third recorded
channel `rt-differential ∈ {defeq, proved, failed, deferred}`. `failed` is a
refusal that flips the row to `refused` with the transcript. A reading that
passes fidelity gates but fails RT is the most valuable failure class in the
whole operation (it is a *measured* mistranslation) — it is logged as a
first-class event, mirroring the disagreement rule.

### WP-LI3 — session orchestration (fills G4)
The "spin the machine up" layer. Two lanes, both consent-first:
- **Sessions lane (Phase A):** a scheduled Routine fires a fresh remote
  session per wave with a fixed prompt: sync the branch, run `cgb import
  --budget-ktokens <per_wave_cap>`, commit queue+ledger deltas, push. One
  wave per firing; the session's own agent overhead is part of the metered
  reality and is recorded in the ledger row (`session_overhead_note`), kept
  *beside* the driver's ktokens (E6 discipline: one currency in the
  headline, everything else reported beside).
- **CI lane (Phase B):** extend the weekly `[lean-ci]` cron job with a
  certification step over rows with `status=authored`. No new
  infrastructure: the ~5 GB cache, the sudo/sandbox arrangement, and the
  once-per-pin `[lean-fresh]` debt all already exist.
Serialization: sessions never run concurrently (Routine minimum interval ≥
wave duration; the ledger is append-only and the queue single-writer, so a
violated assumption is detectable as a non-fast-forward push, which aborts
the wave rather than merging).

### WP-LI4 — the fragment-growth outer loop
Per wave, `fragment-miss` rows are binned by missing constant (the existing
`miss_kind_guess` vocabulary). The bins are demand: operators with ≥2
would-be witnesses enter the existing proposal → priced-admission path
(F1.5). Admission re-flips matching `fragment-miss` rows to `pending` for
the next wave. Carrier-level growth (`Real`, sets, higher-order) is NOT
operator growth — it is fragment design work, out of scope for the driver
and USER-GATED as its own plan when the miss histogram justifies it.

### WP-LI5 — metrics, readout, and stopping
Per wave, appended to the ledger: ktokens in/out, rows imported / refused /
fragment-missed, `cost_per_certified_statement` (imported rows only),
frontier depth remaining. Standing readout: frontier progress per kilotoken,
plotted per wave. **Stopping rule (registered):** `P-LI5-STOP` — three
consecutive waves with zero imported rows and zero operator admissions →
the operation halts itself and demands a human readout; it never idles
against a spent grant.

## 5. Spend governance (USER-GATED — the actual token-spend conversion)

`specs/ops/spend_grant.json`, committed by a human, checked by the driver:

```json
{
  "granted_ktokens": 0,
  "per_wave_cap_ktokens": 0,
  "arm": "ungoverned-authoring+per-emission-certs",
  "granted_by": "<user>",
  "granted_on": "<date>",
  "expires": "<date>"
}
```

- The driver refuses when `sum(ledger ktokens) ≥ granted_ktokens` — the
  grant decrements against the append-only ledger, so cumulative spend is
  auditable from the repo alone.
- **Arm choice is registered, not assumed.** The metered evidence
  (`results/metered_evidence/`, verdicts honest-red) showed governed
  authoring at ~484 ktok/statement vs ungoverned ~55 on the Euclid holdout
  with confounded mechanism verdicts. Default arm: ungoverned authoring with
  per-emission certification; the governor question re-enters only via its
  own predicate on import-corpus data, not by fiat.
- Template values are zero: committing this plan authorizes nothing.

## 6. Registered predicates (summary)

| Predicate | Where evaluated | Effect |
|---|---|---|
| P-LI0-ORDER | queue build | deterministic frontier order |
| P-LI1-REFUSAL | per wave | halt on refusal spike |
| P-LI1-COST | per wave | halt on cost blowout |
| P-LI5-STOP | per 3 waves | self-terminate, demand readout |
| grant check | every driver start | no spend beyond ledger-decremented grant |
| RT(d) | Lean lane, per row | imported only on differential pass |

## 7. Pre-registered refusals

- No estimate-based token accounting; usage metadata only (F1.2).
- No wall-clock in any decision (house rule 13 carried).
- No concurrent authoring sessions in v1; a non-ff push aborts, never merges.
- No fragment widening (carriers, higher-order) inside the driver; misses
  are data for a separately gated design, never silently "handled."
- No claim of "percent of Mathlib imported" in any readout; frontier
  progress per kilotoken is the only headline.
- The English gloss of a declaration is provenance, never a cert subject.

## 8. Build order

LI0 → LI1 (with LI5's ledger from day one) → LI2 → one hand-driven pilot
wave on the 6-module surface (grant: pilot-sized) → LI3 (the Routine + CI
extension) only after the pilot's readout → LI4 as soon as the first miss
histogram exists. The pilot is deliberately before any scheduling: the
operation earns its cron with one honest wave.
