# PLAN_FORMALIZE_INTEGRATION.md — Zone F-INT: wiring the formalization extension into the active machinery

FORMALIZATION.md landed the math fragment, the fidelity pipeline, the
governor, and the Lean kernel seam. A two-agent integration audit (file:line
evidence throughout this document) found the extension is integrated only
where a subsystem is **corpus/ledger-generic**: macro mining shares the
corpus and table (`loop.py:313` has no kind filter), the examiner is a shared
module wired into `certify_statement` (`run/formalize.py:367`), the trust
tiers landed (`kernel/certs.py:135`), and the CI lean job runs the real
positive path (`ci.yml:183-189`). Every subsystem that embeds a
*service-shaped model* never sees math:

- **G1** the scheduler prices `math-source` rows (`dl.py:280-291,335-338`)
  but has **no move** to serve one (`loop.py` move generators filter to
  `spec-file` / `nl-request` / readings / `caged-incumbent`;
  `DEFAULT_DISPATCH` has no math entry) — an unserved exogenous math row is
  a permanent, un-retirable `UNCOVERED_PENALTY`, served only by the one-shot
  seed path (`cgb.py:482-536`).
- **G2** `metrics/`, `milestones.py`, and `metrics/plots.py` contain zero
  formalization logging — no milestone, no CSV, no reach-vs-cost curve for
  the math corpus (`metrics/__init__.py:14-58` counts only live generators).
- **G3** the SMT nonvacuity and instance-enumeration gates recompute
  uncached on every run (`run/formalize.py:124-125,177-195` never touch
  `cache_get`/`cache_put`; only the Lean kernel stage caches per L2,
  `kernel/__init__.py:454-463,563-573`).
- **G4** `bench_formalize.py` cannot measure what F5.2 specifies: every
  authored reading is tagged `origin:"exogenous"` and the dream corpus
  (`specs/mathsources/dream/d01–d08`) is never loaded, so both arms see
  identical inputs (a tie by construction); the macro table never reaches a
  prompt (`_author_reading(src, {})`); no checkpointing; the CSV lacks the
  F5.2 cost tuple; the bench is wired into neither `run_regression.py` nor CI.
- **G5** Zone-3 speculation (`buildloop/speculate.py:30-34,204`) fans out
  service Readings only; MathReadings have no speculative path.
- **G6** carrier (ℕ-vs-ℤ) and operator binding are represented as
  choice-force statements (FORMALIZATION.md:288-292) but nothing searches
  that residue; `planner/choices.py` searches only the service lifecycle
  family, `planner/lookahead.py` is ksy-only.

This plan closes G1–G6. It is written to be executed by a **swarm of Opus
builder agents without access to the conversation that produced it**, with
**maximum parallel fan-out at all times**: every cross-package interface is
frozen in §2 before any builder starts, every file is owned by exactly one
work package (§4), and six of the seven packages start simultaneously at
wave 0 with no merge ordering between them.

Out of scope, unchanged from FORMALIZATION.md: autonomous fragment growth,
new certificate tiers, Mathlib contribution, proof-search research,
mathematical-importance claims. No existing certificate schema changes; no
`CERTS_VERSION` bump is needed by any package (a package that discovers it
needs one must STOP and report — that is a plan defect, not a decision a
builder may take alone).

---

## 1. Swarm execution protocol

- **Builders:** one Opus agent per work package (WP-A…WP-F), plus a
  merge-owner (WP-G) that lands last. Within a package, the builder is
  encouraged to fan out further sub-agents in parallel (impl / tests /
  fixtures are separable everywhere below; per-wave LLM authoring in WP-D is
  embarrassingly parallel by design).
- **Wave 0 (parallel):** WP-A, WP-B, WP-C, WP-D, WP-E, WP-F all start
  simultaneously. Their file sets are disjoint (§4). None may edit a file
  owned by another package; a needed change in a foreign file is expressed
  against the frozen interface in §2 or reported as a plan defect.
- **Wave 1 (serial, last):** WP-G (harness + docs). The ONLY ordered merge.
- **Interfaces are frozen, not negotiated.** §2 is the contract. A builder
  who believes a frozen interface is wrong reports it and stops that
  sub-task; it does not improvise a variant (the X14 lesson: cross-WP
  knowledge with no freeze is how parallel swarms deadlock or fork).
- **Honesty disciplines inherited whole:** relational asserts only, never
  absolute constants (E5/H52); never sum tokens with seconds (E6); no wall
  clock in any DL-adjacent number (house rule 13); LLM-requiring paths skip
  with an honest note (H43/X15); every demo tooth must be LLM-free and
  Lean-free; deferred layers record `deferred`, never fake `pass`.
- **Byte-identity pins:** WP-A and WP-C explicitly promise byte-identical
  behavior on the pre-existing surface (zero math rows / cache-miss paths).
  Each carries a regression tooth asserting it. Any package that breaks a
  committed fixture must treat that as its own bug.
- **Every package lands:** implementation + tests + (where stated) an
  LLM-free demo tooth + a five-line summary in its final commit message of
  what is claimed and at what strength.

## 2. Frozen interfaces (the cross-WP contract)

**F-INT-1 — the `math` move (WP-A produces, WP-B/WP-G consume).**
Move dict, mirroring `_request_moves` (`loop.py:284-296`):

```python
{"kind": "math", "candidate_key": "math:%s" % demand_id,
 "score": dl.UNCOVERED_PENALTY,          # upper bound; row's penalty retired
 "demand_id": demand_id, "row": row}
```

Generated by `_math_moves(snap)` for every demand row with
`kind == "math-source"`, `status != "retired"`, `origin == "exogenous"`
(system-origin dream rows price at 0 — `dl.py:289-291` — and MUST NOT
generate moves), and no reading in `snap.readings[demand_id]`. Dispatch
executor signature identical to the other four:

```python
_dispatch_math(move, snap, registry, backlog, policy, use_corpus, model)
```

Behavior: read the source text via the row's `payload_ref` (same resolution
as `_dispatch_request`, `loop.py:~480`), render the prompt with
`buildloop.math_prompt.render_math_reading_prompt(source, snap.macro_table)`
(the E1 seam — the LIVE table reaches the prompt), author via
`buildloop.llm.call_llm`, certify via `run.formalize.certify_statement`
passing `event_sink=registry.log_event`-adapter, `cache_get/cache_put` from
the registry, and `source_id=demand_id`; on `res.ok`, persist with
`registry.reading_add(demand_id, common.canonical_json(reading_doc),
cert_id)` where `reading_doc` carries top-level `statements` and
`origin:"exogenous"` (byte-compatible with what `cgb._seed_math_readings`
persists at `cgb.py:533`, so recurrence mining sees one uniform corpus).
Return `{"status": "math-certified"|"math-refused", "demand_id": ...,
"stage": <failing stage or None>}`. Registered as
`DEFAULT_DISPATCH["math"]`. Tests inject `dispatch={"math": fake}` exactly
like the existing LLM-free loop tests.

**F-INT-2 — fidelity-gate cache keys (WP-C produces; WP-A/WP-D benefit
transparently).** New module-level constant in `run/formalize.py`:
`FORMALIZE_CACHE_VERSION = 1`. Two cache entries, threaded through the
EXISTING `cache_get`/`cache_put` parameters of `certify_statement` (no
signature change):

```python
key_nonvacuity = common.sha256_json({
    "kind": "formalize-nonvacuity", "v": FORMALIZE_CACHE_VERSION,
    "reading_sha": common.sha256_json(reading_canonical), "bound": bound})
key_instances = common.sha256_json({
    "kind": "formalize-instances", "v": FORMALIZE_CACHE_VERSION,
    "reading_sha": common.sha256_json(reading_canonical), "bound": bound})
```

`reading_canonical` is the parsed reading's canonical JSON (post-gate, so a
cache entry can never mask a groundedness failure — stage 1 always runs).
Cached value = the full stage result dict, JSON-round-trippable. A cache hit
MUST be verdict-byte-identical to recompute (tooth). SMT solver identity is
NOT in the key for v1 (the solvers are pinned by the container); if that pin
ever moves, bump `FORMALIZE_CACHE_VERSION` — note this in the module
docstring.

**F-INT-3 — metrics fields (WP-B produces, WP-D/WP-G consume).**
`metrics.snapshot()` gains four keys, append-only (A10 — never rename
existing keys): `math_total`, `math_covered` (rows with a persisted
reading), `math_certified` (readings whose seed/loop certification recorded
`ok=True`), `tier_kernel_checked` (count of `proof-cert` certificates in the
registry, 0 in Lean-absent containers). The metrics CSV appends the same
four columns after all existing columns. `metrics/plots.py:reach_vs_cost` is
reused as-is; the math reach series is `math_covered / math_total`.

**F-INT-4 — bench wave protocol + artifacts (WP-D produces, WP-G consumes).**
Wave-parallel speculation against a frozen snapshot (the `run_iteration`
discipline): with wave size `K = 8`, freeze `table_hash =
common.sha256_json(sorted(macro_table))`, author the wave's K statements
concurrently (each call stamped with `table_hash`), then run the LLM-free
tail serially: certify each, mine/admit greedily (`recurrence.mine` +
`mdl_macros.macro_admission_decision`, arm's witness filter), advance to the
next wave with the grown table. Dream inputs: `specs/mathsources/dream/*.txt`
enter the UNGOVERNED arm's reading set as `origin:"system"` rows (authored
once, shared across arms for cost parity — dreams are corpus pressure, not a
second spend). Checkpoint file `results/formalize_bench_state.jsonl`, one
JSON object per authored reading:

```
{"source_id", "arm", "wave", "table_hash", "reading_json",
 "tokens_in", "tokens_out", "certified", "stage"}
```

Resume = skip any (source_id, arm) already present. Final CSV
`results/formalize_governed.csv`, columns frozen (append-only forever):

```
arm, wave, certified_exogenous_statements, cumulative_ktokens_in,
cumulative_ktokens_out, prompt_bytes_mean, live_macros, retired_macros,
reported_exogenous_dl, translation_cert_count, per_use_cert_failures,
trivially_closed_count, cost_per_certified_statement,
cost_per_certified_statement_inclusive, lean_seconds_total, smt_seconds
```

`cost_per_certified_statement` uses the FH7 denominator (E3): exogenous
entries with statement-cert green AND `trivially_closed == false`; the
inclusive variant and the excluded count sit beside it. Token columns and
second columns are never combined (E6). Per-wave rows ARE the reach-vs-cost
curve; the plot is one `reach_vs_cost`-style figure with one curve per arm,
written to `results/formalize_reach_vs_cost.png`. Pins recorded in a
header comment row: model id, sampling params, prompt scaffold hash
(`sha256` of `math_prompt` source), both arm configs, spend cap,
`MATHLIB_COMMIT`, `LEAN_TOOLCHAIN`.

**F-INT-5 — the math speculative pre-gate ladder (WP-E).** Cheapest-first,
mirroring `speculate.pre_gate`'s service ladder, all Lean-free:
`parse_math_reading` (gate) → `math_smt` hypothesis-sat (dual-solver) →
`compile_math_reading` + `validate_lean` escape gate → entailed-instance
replay (**rank-only, never a rejection** — the S4 discipline verbatim).
Fan-out authors K candidate MathReadings via
`math_prompt.render_math_reading_prompt`; losers get **no composed
certificate**; divergence between speculated and certified verdicts logs a
`speculation-divergence` event with the same payload shape as Z3.

**F-INT-6 — formalization choice search (WP-F).** New module
`planner/math_choices.py`, deterministic and LLM-free:
`search_carrier(reading, *, bound=8) -> [{"carrier", "certifies",
"witness", "boundary_behavior", "statement_hash"}, ...]` — enumerate the
admissible ambient carriers for the reading's operator set from the frozen
`MATH_OPERATORS` table (a (word, carrier) pair outside the table is a
fragment-miss, not a candidate), re-run the LLM-free gates per candidate,
and rank: certifying candidates first, then by compiled-statement DL. The
search NEVER overrides a demanded carrier (choice-force only — trichotomy
is load-bearing); it returns evidence, it does not mutate the reading. No
new certificate type: the result is examiner-grade evidence (L3), consumed
by callers as ranking.

## 3. Work packages

### WP-A — the scheduler `math` move (closes G1)

The single highest-leverage seam: make `run_iteration` able to spend on
math demand, converting formalization from a seed-time artifact into a
governed loop participant.

- **A1** `_math_moves(snap)` per F-INT-1; wired into `score_moves`
  alongside the existing four (the docstring's "four typed misses" becomes
  five — update it; the decision log gains `kind:"math"` rows, an
  append-only event payload change, no schema break).
- **A2** `_dispatch_math` per F-INT-1; `DEFAULT_DISPATCH["math"]` entry.
  LLM use at loop time is the established pattern (`_dispatch_request`
  calls `service_loop.synthesize_semantic`); the `CGB_TASK_TIME` guard is
  untouched — it protects `run/`-executing-a-spec, not the build loop.
- **A3** Refusal memory: a math row whose authoring+certification fails
  logs a `math-refused` event carrying the failing stage; `_math_moves`
  suppresses a row after `MATH_MAX_ATTEMPTS = 2` failed attempts (counted
  from the event log, the W3.2 pattern) so a hard row cannot livelock the
  argmax. The suppressed row's penalty honestly persists in the ledger.
- **A4** Teeth (all LLM-free, injected dispatch):
  - planted unserved exogenous math row → `_math_moves` proposes it, and
    with no cheaper move present it is argmax;
  - injected fake dispatch persists a planted reading → next snapshot shows
    the row covered and `ledger_dl` strictly lower (relational);
  - dream (system-origin) rows generate NO move;
  - **byte-identity pin**: on a registry with zero math-source rows,
    `score_moves` output (moves, log_moves, picked) is byte-identical to
    pre-WP-A (fixture);
  - two failed attempts → suppressed, third iteration never proposes it.
- **Done when:** teeth green; `run_regression --fast` green; the loop
  docstrings and `scheduler-decision` log mention the fifth kind.

### WP-B — metrics, milestone m9, the formalization curve (closes G2)

- **B1** `metrics.snapshot()` + CSV columns per F-INT-3.
- **B2** Milestone `m9` in `milestones.py`: run the combined loop over a
  seeded registry whose backlog is the `specs/mathsources` corpus, N=20
  iterations, logging per-iteration `math_covered`, `math_total`,
  cumulative `llm_input_tokens`/`llm_output_tokens` (from `call_llm`'s
  usage), producing `results/math_reach_vs_cost.png` via the existing
  `plots.reach_vs_cost`. LLM-requiring → `REQUIRES_LLM = True`, honest
  skip note when no endpoint (H43).
- **B3** The LLM-free variant `m9_planted`: identical loop mechanics with
  an injected dispatch that serves rows from the committed
  `specs/mathsources/readings/` fixtures — deterministic, runs in the fast
  tier, and IS the tooth that the curve machinery works (the plot from
  planted data is still a real monotone curve).
- **B4** Teeth: snapshot fields correct on a mixed registry (relational:
  covered ≤ total, dream rows excluded from `math_total`'s exogenous
  count... math_total counts ALL math rows; add `math_dream_rows` if the
  distinction is needed — frozen: `math_total` = exogenous only, dreams are
  never "backlog"); CSV column append verified against a committed header
  fixture; `m9_planted` produces a monotone nondecreasing reach series.
- **Done when:** `m9_planted` in the fast tier, green, plot file written;
  `m9` skips honestly without an LLM.
- **Merge note:** B2/B3 *call* the loop; if WP-A has not merged yet the
  planted dispatch serves rows through the same injected-dispatch seam the
  loop already exposes (`dispatch=` override), so WP-B has **no merge
  dependency on WP-A** — the live `m9` run simply gets better once WP-A
  lands (it can retire real rows via the math move).

### WP-C — cache the Lean-free fidelity gates (closes G3)

- **C1** Thread the existing `cache_get`/`cache_put` params into
  `_nonvacuity` and `_instances` per F-INT-2. Stage-1 parse always runs
  (groundedness is never cached). On hit, append the cached channels with
  a `("cache", "hit")` channel marker appended to the layer detail (visible
  honesty; verdict content otherwise byte-identical).
- **C2** `cgb._seed_math_readings` already passes the registry hooks
  (`cgb.py:523-524`) — verify they now reach the new keys; add the same
  hooks to `demo_formalize.py`'s pipeline calls behind a keyword so the
  demo output stays byte-identical (the demo runs cache-less by default;
  its committed transcript must not change).
- **C3** Teeth: (i) monkeypatched `SmtBackend.run_z3` call-counter — second
  `certify_statement` over the same reading+bound performs zero solver
  calls; (ii) hit and miss produce byte-identical `FormalizeResult` fields
  except the honesty channel marker; (iii) a changed `bound` misses; (iv) a
  version bump misses; (v) cache never serves across a failed stage-1 parse.
- **Done when:** teeth green; committed demo transcripts byte-unchanged;
  regression fast tier green.

### WP-D — the bench that can actually diverge (closes G4)

Rebuild `run_bench` per F-INT-4. Sub-tasks parallelize internally
(checkpoint/resume machinery, cost accounting, wave engine, dream wiring,
plotting are five separable seams).

- **D1** Wave engine: waves of K=8 authored in parallel (threads around
  `call_llm` — it is a subprocess call, safely concurrent), frozen
  `table_hash` per wave, LLM-free tail (certify → mine → admit) serialized
  after the wave barrier. Per-arm sequencing: the arms run their OWN wave
  sequences over the same sources (they must — their tables diverge, so
  their prompts diverge; that IS the E1 measurement).
- **D2** Dream wiring: `specs/mathsources/dream/*.txt` authored ONCE
  (single wave, empty table), entering only the ungoverned arm's mining
  corpus as `origin:"system"`. The governed arm's witness filter excludes
  them (Z-E); the ungoverned arm's does not. Dream authoring cost is
  reported in a separate `dream_ktokens` line, charged to neither arm's
  `cost_per_certified_statement` (E3: system-origin enters neither
  numerator context nor denominator).
- **D3** Checkpoint/resume per F-INT-4; a killed run resumes without
  re-spending; `--fresh` flag to ignore state.
- **D4** Cost columns + FH7 denominator + pins per F-INT-4. `triviality`
  detection for `trivially_closed`: reuse the `triviality` event kind
  (F-I) — in a Lean-absent container the flag is `false` for all and the
  inclusive/exclusive variants coincide (recorded honestly in the header).
- **D5** Per-wave CSV rows + the two-curve plot
  (`results/formalize_reach_vs_cost.png`).
- **D6** Teeth (LLM-free): the wave engine, checkpointing, cost accounting,
  and CSV/plot rendering all run with an injected fake author function
  (deterministic canned readings, including the dream paraphrases) —
  committed as `tests/test_bench_formalize.py`; asserts include the
  relational pair (equal coverage; governed DL ≤ ungoverned) AND that with
  the planted dream flood the ungoverned arm's reported exogenous DL is
  STRICTLY higher (the F5.3 conjunction reproduced through the bench path).
- **Done when:** fake-author bench end-to-end green in the fast tier; a
  real run documented in the module docstring (spend estimate, resume
  semantics, skip note per X15 unchanged).

### WP-E — speculative fan-out for MathReadings (closes G5)

- **E1** `speculate.py` gains the math path per F-INT-5: `pre_gate_math`
  (ladder) + `fan_out_math` (K-wide, `math_prompt`, losers uncertified,
  divergence events). Shares the ranking/ledger plumbing with the service
  path; does NOT touch the service ladder (byte-identity of existing
  fixtures).
- **E2** `demo_speculate_math.py`: LLM-free planted fan-out — K=4 planted
  candidate readings for one source (one certifying, one fabricating, one
  contradictory, one carrier-narrowed), pre-gates kill each loser at its
  own rung (cheapest first), the winner alone reaches certification, the
  divergence ledger records one planted speculation-divergence.
- **E3** Teeth: rung-order assertion (a fabrication never reaches SMT);
  loser-has-no-cert assertion; replay stage rank-only assertion (a replay
  mismatch reorders, never rejects); service-path fixtures byte-unchanged.
- **Done when:** demo + teeth in the fast tier, green.

### WP-F — searched formalization choices (closes G6)

- **F1** `planner/math_choices.py` per F-INT-6.
- **F2** Teeth: the planted ℕ-vs-ℤ case (truncated subtraction flips
  truth): the wrong carrier is refuted by `_instances` and ranked below the
  certifying carrier; a demanded carrier is never overridden (attempting to
  search a demand-force ambient raises); a (word, carrier) pair outside
  `MATH_OPERATORS` yields a fragment-miss candidate entry, not a crash.
- **F3** One consumer wiring, evidence-only: `certify_statement` gains an
  OPTIONAL `choice_search=False` keyword; when true and the reading's
  ambient is choice-force, the result's examiner-grade evidence includes
  the ranking (never a refusal — L3). Default false: byte-identity of all
  existing outputs.
- **Done when:** teeth green; no behavior change with the flag off.

### WP-G — harness + docs, the merge-owner (wave 1, lands last)

- **G1** `run_regression.py`: `--full` adds `bench_formalize.py`
  (best-effort, honest-skip, like `bench_latency`); the fast tier gains
  WP-B's `m9_planted` and the new demos/tests (they are auto-discovered
  where the existing glob covers them — verify, don't duplicate).
- **G2** CI: NO new mandatory job (the bench never runs in CI — spend);
  the existing `lean` job's demo list gains `demo_speculate_math.py` only
  if it is Lean-free-green in that image (it is; it needs no toolchain —
  include it in the fast shard instead if the matrix split makes that the
  cheaper home).
- **G3** Docs, one commit: README (the F-INT section: five-move scheduler,
  math metrics, the bench protocol), METRICS.md (math reach-vs-cost),
  FORMALIZATION.md addendum pointer (G1–G6 closed, with the same honesty
  notes), TRUST.md ONLY if any package added an event kind (events are not
  certs; expected: no TRUST change).
- **Done when:** `run_regression --fast` < 90s target still holds
  (measure; if the new fast items break the budget, move the slowest to
  `--full` and record the decision), full tier discovers everything, docs
  landed, ownership matrix in this file updated to "landed" per row.

## 4. File ownership matrix (exactly one owner per file)

| file | owner |
|---|---|
| `buildloop/loop.py` | WP-A |
| `tests/test_math_moves.py` (new) | WP-A |
| `metrics/**`, `milestones.py` | WP-B |
| `tests/test_math_metrics.py` (new) | WP-B |
| `run/formalize.py` | WP-C (F-INT-2) **and** WP-F (F3 keyword) — CONFLICT: resolved by freeze: WP-C owns stages 2/4 internals; WP-F adds only the `choice_search` keyword + one evidence block in stage 5; they touch disjoint functions; WP-F rebases after WP-C if both edit the signature line — WP-C does NOT edit the signature, so no overlap |
| `tests/test_formalize_cache.py` (new) | WP-C |
| `bench_formalize.py`, `tests/test_bench_formalize.py` (new) | WP-D |
| `buildloop/speculate.py`, `demo_speculate_math.py` (new) | WP-E |
| `tests/test_speculate_math.py` (new) | WP-E |
| `planner/math_choices.py` (new), `tests/test_math_choices.py` (new) | WP-F |
| `run_regression.py`, `.github/workflows/ci.yml`, `README.md`, `METRICS.md`, `FORMALIZATION.md`, `TRUST.md` | WP-G |
| `cgb.py` | untouched (seed path already passes cache hooks) |
| `kernel/**`, `generators/**`, `buildloop/dl.py`, `buildloop/recurrence.py`, `buildloop/math_prompt.py` | untouched by ALL packages (frozen consumers) |

## 5. Global acceptance

1. `python3 run_regression.py --fast` green, within the wall-clock target.
2. All byte-identity pins hold: zero-math-row `score_moves`, service
   speculation fixtures, committed demo transcripts, cache-off demo output.
3. The planted curve exists: `m9_planted` writes a monotone math
   reach-vs-cost plot with no LLM and no Lean.
4. The bench, run with a fake author, reproduces the F5.3 conjunction
   through the full wave/checkpoint/cost path.
5. Relational asserts only; grep the diff for new absolute-constant
   assertions (reviewer step).
6. The G1 ledger claim is demonstrated: an unserved exogenous math row's
   penalty is retired by a loop iteration (planted dispatch) — the
   "priced but never actionable" defect is gone.
