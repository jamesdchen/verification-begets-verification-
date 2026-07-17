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

### 2.5 Encoding lock-in and the migration contract

The economic risk of importing at scale is not a wrong kernel — it is a
kernel that is *expensive to be wrong about*: 10^5 rows bound to an encoding
that later changes means re-paying the entire authoring spend. The kernel
cannot be "gotten right" before contact with the library (the miss histogram
is the instrument that reveals what it needs), so the design goal is that
being wrong costs one proof, not the corpus. Four rules, all mechanized:

- **R1 — anchor identity.** A row's identity is `(decl_name,
  statement_hash at the pin)` — representation-invariant because Mathlib
  itself is the ground truth. Readings are derived views (caches of
  translation work), never identity; certs cite the anchor. Consequence:
  after any encoding change, re-validating a migrated row is RT(d) again —
  Lean-lane compute, zero tokens — even in worlds where re-*deriving* it
  is not free.
- **R2 — provenance is the asset.** Tokens buy disambiguation decisions
  (operator bindings, quantifier structure, side conditions), not reading
  bytes. Every row retains its full chain (decl → gloss → reading →
  decisions) so no migration restarts from zero; and because the source is
  formal, the worst case is bounded — re-authored rows re-validate against
  the anchor automatically, so a write-off costs tokens but never trust.
- **R3 — the kernel basis is the normal form.** The kernel fragment grows
  only by census-priced primitive/carrier additions (WP-LI0), never by
  macro drift. Every layer above the basis is eliminable by construction —
  the existing per-emission-cert-against-retained-inlined-baseline
  discipline, held as invariant — so the corpus is always deterministically
  rewritable down to the basis. Recompression sweeps (re-run vocabulary
  admission from scratch against the grown corpus) are therefore CPU-only,
  and they undo import-order entrenchment of the macro layer; without
  eliminability, the DL pricing gate itself becomes the lock-in mechanism
  (incumbent macros price every alternative as expensive).
- **R4 — migration is certified translation.** An encoding change v1→v2
  ships with a migrator `reading_v1 → reading_v2` promoted to **universal
  tier** (the existing `buildloop/promote.py` contract, applied to time):
  proved once, then batch re-emit + batch RT(d) re-check. Cost of a
  breaking change: one proof + CPU. Cost without R4: the corpus.

**Tooth T-LI-ENC (registered, CI-checkable):** the reading encoding carries
an explicit version constant; no version bump lands without either (a) a
universal-tier migrator cert for v(n)→v(n+1), or (b) an explicit USER-GATED
corpus write-off decision on file. A bump satisfying neither fails CI.

**Refusal (carried to §7):** no speculative generality in the reading AST.
Invariance comes from anchors, eliminability, and migrators — not from a
"future-proof" representation, which is its own lock-in.

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

### WP-LI0 — the queue + fragment-fit census (deterministic, one-time per pin)
Two surfaces, deliberately distinct:
- **Enumeration surface — the whole library, read-only.** A Lean
  meta-program in the Lean lane enumerates ALL declarations of Mathlib at
  the pin into `specs/mathsources/mathlib/queue.jsonl`, one row per decl:
  `{decl_name, module, statement_pp, statement_hash, status}` with
  `status ∈ {pending, authored, imported, refused, fragment-miss,
  divergent}`. Enumeration never touches `common.MATHLIB_IMPORTS` or the
  certification cache key; it is authorized once (USER-GATED: one-time
  whole-library elaboration compute).
- **Certification surface — the pinned modules, unchanged.** Widening it
  remains a `.lean-pins`-adjacent, cache-rekeying, USER-GATED event.

**The census (the kernel-design instrument).** A deterministic classifier
over `statement_pp` bins every queue row by the constants/carriers it
needs, producing `specs/mathsources/mathlib/census.json` with unlock
counts per candidate primitive addition ("adding `Prime` unlocks N rows,
`Real` unlocks M"). Kernel/fragment decisions are priced against this —
the real distribution of the library — never against whichever slice
happened to be imported first. The census is also the pre-spend answer to
"get the kernel right before importing": measurement, not speculation.

`P-LI0-ORDER` (v2, census-derived): frontier order = in-fragment rows
first, then by census unlock-weight; a pure function of (queue, census),
so any two runs agree. Tooth: queue AND census regeneration at the same
pin are byte-identical.

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
The "spin the machine up" layer. Two lanes, both consent-first.

**Binding execution substrate (verified 2026-07-17, remote container):**
the operation runs on remote subscription-funded Claude Code sessions.
Checked facts, not assumptions:
- The headless CLI is present and authenticated in these containers
  (`claude` 2.1.212 at the path `common.CLAUDE_CLI` resolves), and a
  `claude -p … --output-format json` call returns full usage metadata
  (`input_tokens`, `output_tokens`, cache-token splits) — the exact shape
  `buildloop/llm.call_llm` parses. Phase A therefore runs the existing
  metered path **unmodified**, and F1.2 (usage-metadata-only accounting)
  survives the substrate.
- Disk headroom in a fresh container (~30 GB observed) admits the ~5–8 GB
  Lean toolchain, so an in-session Phase B is *possible* — but fresh
  sessions start clean, so every Lean session re-pays the ~5 GB fetch.
  Phase B therefore defaults to the CI lane (cache already keyed on
  `.lean-pins`); dedicated in-session Lean waves are the fallback if CI
  capacity becomes the constraint, batching many rows per setup cost.

Lanes:
- **Sessions lane (Phase A):** a scheduled Routine (fresh session per
  firing; minimum interval hourly, expected cadence nightly over the
  ~month-long grant window) with a fixed prompt: sync the branch, run
  `cgb import --budget-ktokens <per_wave_cap> --confirm-spend`, commit
  queue+ledger deltas, push. One wave per firing; the session's own agent
  overhead is part of the metered reality and is recorded in the ledger row
  (`session_overhead_note`), kept *beside* the driver's ktokens (E6
  discipline: one currency in the headline, everything else reported
  beside).
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
  "mode": "fixed | weekly-quota-exhaustion",
  "granted_ktokens": 0,
  "per_wave_cap_ktokens": 0,
  "arm": "ungoverned-authoring+per-emission-certs",
  "granted_by": "<user>",
  "granted_on": "<date>",
  "expires": "<date>"
}
```

**RULED 2026-07-17 (user, in-session):** grant mode is
`weekly-quota-exhaustion` — "I'm looking to spend all my tokens on this.
we will keep going until it's gone every week." The driver therefore has
no fixed total; it runs until the subscription quota signals exhaustion
(CLI quota/rate errors are a graceful wave-halt, recorded in the ledger,
never a crash), resuming when the quota resets. The per-wave cap survives
as checkpoint hygiene, and the P-LI1 circuit breakers become the primary
protection against *wasted* spend, since total spend is now bounded by
the subscription itself. Arm ruling delegated; decision:
`ab-pilot-then-cheaper` — the pilot wave runs both arms to de-confound
the n=1 metered cost ratio, then the operation continues on the cheaper
arm (re-evaluated per REG-COST-1-style discipline: ≥2 runs per arm before
the ratio is cited).

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
| P-LI0-ORDER | queue build | deterministic census-derived frontier order |
| P-LI0-CENSUS | queue build | queue+census byte-identical at same pin |
| P-LI1-REFUSAL | per wave | halt on refusal spike |
| P-LI1-COST | per wave | halt on cost blowout |
| P-LI5-STOP | per 3 waves | self-terminate, demand readout |
| grant check | every driver start | no spend beyond ledger-decremented grant |
| RT(d) | Lean lane, per row | imported only on differential pass |
| T-LI-ENC | CI, per encoding bump | no bump without universal migrator or USER-GATED write-off |

## 7. Pre-registered refusals

- No estimate-based token accounting; usage metadata only (F1.2).
- No wall-clock in any decision (house rule 13 carried).
- No concurrent authoring sessions in v1; a non-ff push aborts, never merges.
- No fragment widening (carriers, higher-order) inside the driver; misses
  are data for a separately gated design, never silently "handled."
- No claim of "percent of Mathlib imported" in any readout; frontier
  progress per kilotoken is the only headline.
- The English gloss of a declaration is provenance, never a cert subject.
- No speculative generality in the reading AST; representation resilience
  comes from §2.5's anchors + eliminability + certified migrators only.
- No kernel-fragment growth by macro drift; the basis grows only by
  census-priced primitive additions (R3).

## 8. Build order

LI0 (queue + census; the whole-library enumeration ruling comes first) →
**kernel-readiness review against the census** (primitive additions chosen
by unlock-count, encoding version stamped, T-LI-ENC registered — the gate
before any metered token) → LI1 (with LI5's ledger from day one) → LI2 →
one hand-driven pilot wave on the certification surface (grant:
pilot-sized) → LI3 (the Routine + CI extension) only after the pilot's
readout → LI4 as soon as the first miss histogram exists. The pilot is
deliberately before any scheduling: the operation earns its cron with one
honest wave.
