# PLAN: The Combined Loop (v2.1, swarm-hardened and re-verified)

Refactor of this repository to unify the two axes it currently pursues
separately — **breadth** (more certifiable behavior at a fixed spec level;
ROADMAP.md's archipelago) and **height** (higher-level spec languages via
certified translators; the bootstrap tower) — plus the **intake** (cage →
lift → certified replacement) that converts world-code into demand, and a
**full decomposition of the service monolith into certified compiler
passes**. One loop, one currency, four move types.

How this document was produced, and how to read it: a v1 draft was attacked
by an adversarial review swarm — six independent critic lenses
(codebase-reality, trust-soundness, economics, migration, implementability,
scope), a completeness pass over the seams between them, an adversarial
verifier that attempted to refute every single-source finding, and a
decomposition scout that mapped `generators/service_gen.py` line-by-line.
Every hazard below marked ⚠ was **verified against the actual code** with
the cited evidence; findings the verifier refuted are listed in §8 so
builders do not re-litigate them. This version incorporates every confirmed
finding. The plan assumes ROADMAP.md has been executed through P5 (verified:
all Phase-0–P5 files exist with the shapes cited below; `demos/demo_macros.py`
passes; `CERTS_VERSION` mechanics are live in `kernel/certs.py`).

---

## 0. Framing: the tier lattice is the loop's gradient

The trust tiers are an amortization lattice:

| tier | marginal cost | who pays |
|---|---|---|
| universal | zero, forever | paid once at promotion |
| emit-check | per emission | paid at every build |
| conformance-relative(n) | per emission + inherited non_claims | paid at every build, honesty permanent |
| monitored (caged) | per call, permanently | paid at every task-time invocation |
| uncovered | penalty (finite, capped) | unserved demand |

The loop's objective is to minimize the total cost of serving all demand,
creating pressure to push artifacts UP this lattice:

- **breadth move**: uncovered → emit-check (new generator/fragment)
- **height move**: shrinks the authored-spec cost of covered demand
  (macro / translator / notation)
- **request move**: uncovered nl-request → certified Reading (the existing
  semantic pipeline, wired into the loop for the first time)
- **conversion move**: monitored → conformance-relative(n) (cage → lift →
  certified replacement; the toll retires, the honesty ledger persists)
- **promotion move**: emit-check → universal (per-emission cost retires)

All moves are admitted through ONE gate (W0) and certified through the same
kernel discipline. The **anchor rule** (house rule 11, new) governs every
translation certificate: no `translation-cert` without a named independent
anchor.

---

## 1. Verified current-state facts (all checked by the swarm; do not re-derive)

1. Translators are already representable: the abnf→ksy entry declares
   `spec_grammar.output` (`buildloop/admission.py:66`); the planner unifies
   on it (`planner/__init__.py:98-105`) but hardcodes 1- and 2-link chains
   (`planner/__init__.py:89-105`).
2. `buildloop/mdl.py:26` (`chain_length_for`) is a hand-kept mirror of the
   planner's coverage rule — a latent divergence.
3. `macro-expansion-cert` is a translation-validation certificate anchored
   on a trusted reference lowering: the kernel compiles the hand-INLINED
   reading and derives entailed scenarios from **that**, never from the
   artifact under test (`kernel/__init__.py:761-766`). This anchor pattern
   is what the generic contract must generalize, not discard.
4. The codec emit-check harness properties are fixed trusted code, not
   spec-derived (`generators/harness_gen.py:10-18`).
5. `buildloop/promote.py` promotes only `universal-fixed-uint` (`:60`) and
   sets `tier="universal"` unconditionally on any Certificate (`:74`).
   ⚠ The planner recognizes **only** `tier=="universal"`
   (`planner/__init__.py:33,109`) — there is no bounded-tier routing.
6. The DL objective prices only generator descriptions
   (`canonical_json({spec_grammar, emit_entrypoint})/64`, `mdl.py:47-51`)
   and codec backlog specs. ⚠ LLM-authored `grammar_js` payloads (up to
   20,000 chars) are popped before pricing (`admission.py:122`) — unpriced
   authored content. NL requests, Readings, and incumbents are invisible.
7. ⚠ Readings are persisted ONLY as per-run artifact files
   (`run/semantic.py:170-174`, `write_output`-gated); the registry has no
   readings or macros table (`library/__init__.py:17-72`). The recurrence
   corpus does not exist yet as a queryable store.
8. The cage writes nothing to the registry (grep `run/guarded.py`: zero
   `counter_add`/`log_event` calls); cage-conformance claims/non_claims are
   assembled **inside the kernel** (`kernel/__init__.py:185-227`), not in
   `run/guarded.py`.
9. The task-time path ALREADY invokes `kernel.check` for emit-check-tier
   links inside the task-time guard (`run/__init__.py:91-96`), and
   `abnf_to_ksy_via_parser` already runs at task time (`run/__init__.py:53`).
   The `CGB_TASK_TIME` guard forbids exactly one thing: LLM calls
   (`buildloop/llm.py:43`). Per-stage kernel checks at task time are an
   ordinary edit, not a rewiring.
10. `CERTS_VERSION` is live (currently v6, `kernel/certs.py:40`); one bump
    voids the ENTIRE verdict cache for all contract types
    (`kernel/__init__.py:307-312,332`; `library/__init__.py:277-278`).
    The cache is ephemeral per checkout (no .db files committed), so a bump
    costs one full re-verify — what every fresh run does anyway. Aliases
    therefore buy dispatch back-compat only, never cache back-compat.
11. ⚠ `library/__init__.py:128-154`: generators-table reads use `SELECT *`
    zipped positionally against a hardcoded 15-name column list; `_migrate`
    handles only the certificates table.
12. ⚠ `run_regression.py:40-42`: `--fast` runs a HARDCODED demo list;
    `--full` auto-discovers with `REQUIRES_LLM` defaulting to True and a
    900 s cap (`:50`); `_requires_llm()` imports demo modules in the parent
    process env (`:71-77`) — new demos must not touch the registry at
    import time.
13. The monolith (`generators/service_gen.py`, 961 lines) interleaves five
    concerns as f-string placeholders whose ordering IS the runtime
    enforcement semantics (`:177-199`); the `_EVAL` predicate interpreter is
    byte-shared between dispatcher and reference (`:19-44` → `:170` and
    `:753`) — the symmetric rule is already qualified there today. Three
    external consumers reach into six private helpers
    (`generators/reading_compile.py:309-401`, `run/guarded.py:378,393`,
    `kernel/backends.py:216-253`).
14. Existing lift prompts embed the incumbent's SOURCE verbatim and echo
    incumbent-influenced transcripts into retries
    (`buildloop/schema_lift.py:25-38,48-53,71-74`); `buildloop/validate.py`
    gates output shape only. `buildloop/lstar.py:41-44` already canonicalizes
    outputs into a finite hash-class alphabet — the pattern to mandate.
15. All demand sources are static and committed: ~200 backlog specs
    (`metrics/backlog.py`), 20 NL requests (`specs/requests/`), 2 incumbents
    (`specs/incumbent/`). The loop as planned reaches a fixed point on this
    corpus; that is acknowledged and scoped, not hidden (§7).
16. ⚠ The generators table's tier column is
    `CHECK(tier IN ('emit-check','universal'))` (`library/__init__.py:21`);
    SQLite cannot alter a CHECK — widening the tier vocabulary requires a
    table-rebuild migration (owned by W2.1, vocabulary frozen in §4.12).
    The planner terminates chains only at `output_language ==
    "python-codec"`, hardcoded in three places
    (`planner/__init__.py:92,99,104`) — chain targets must be a parameter
    (§4.5).

---

## 2. House rules (1–10 inherited from ROADMAP.md and restated there; 11–14 new)

1. Outsource every checker that exists; new code is wiring, ledger,
   measurement.
2. Dual-checker rule everywhere; disagreement is a first-class logged event.
3. Teeth per increment; every demo ships a planted defect it catches.
4. Honest tiers; claims/non_claims name exactly what is and is not shown.
5. The LLM authors only specs (generator specs, translator specs, macro
   specs, Readings). The recurrence miner, toll meter, derivers, and
   registry adapters are fixed code.
6. New kernel contract = five touchpoints + TRUST entry. This plan adds
   exactly TWO contract types: `translation-cert` (W1) and
   `universal-translation` (W5). `replacement-cert` is an oracle-mode of
   `translation-cert`, not a type. A permanent test freezes the
   contract-type allowlist (pre-existing set + these two); it lands in W1
   and every later workpackage keeps it green.
7. Symmetric-implementation rule wherever a dispatcher/reference
   differential is a channel — including per compiler pass (W6): the
   reference stays monolithic and code-disjoint; the shared `_EVAL`
   interpreter is duplicated into an independently-written reference
   interpreter as part of W6.
8. `CERTS_VERSION` bumps whenever verdict content or obligation generation
   changes. Bumps are cheap (fact 10) — bump per workpackage that needs
   one; never claim cache back-compat from aliasing.
9. One writer per DB file; `CGB_DB` set pre-import; WAL + timeouts as
   today. Task-time components never write the ledger DB directly (W4.1's
   ingest path is the only bridge).
10. Regression gate before every push: `run_regression.py --fast` green;
    `--full` per workpackage. **Every workpackage's done-when names its
    regression wiring** (which demos join `FAST_DEMOS`, `REQUIRES_LLM`
    flags, measured runtime vs the 900 s cap). New demos must not touch
    the registry at module import time (fact 12).
11. **Anchor rule** (new): every `translation-cert` names its independent
    anchor, one of: (a) `reference-lowering` — a trusted, fixed,
    LLM-free lowering of the high spec (hand-authored reference or the
    fixed compiler), the macro-cert pattern; (b) `fixed-deriver` — a
    per-language LLM-free obligation-deriver + harness-deriver registered
    in the deriver table, each with its own TRUST.md 1.2x entry; (c)
    `incumbent-differential` — the conversion oracle mode, which caps the
    resulting tier at `conformance-relative(n)`. **No anchor, no
    certificate.** Channel-2 harnesses are derived from the HIGH spec via
    a TRUSTED lowering, never via the translator under test.
12. **Exogeneity rule** (new): demand rows carry
    `origin ∈ {exogenous, system}`. Only exogenous demand can trigger the
    expansion exception; system-authored rewrites are priced against the
    retained original row as baseline. The height metric counts only
    chains serving exogenous demand. **Attribution** ⚠ (without it the
    depth-3 acceptance is unsatisfiable — the deep chain serves the
    system rewrite row, not the original): a chain *serves* an exogenous
    original when a system rewrite row whose `payload_ref` links to that
    original has a green equivalence anchor; the original then becomes
    `status=covered` with `covered_via=<rewrite demand_id>` and exactly
    ONE of the pair is priced (the rewrite's cost, attributed to the
    original — no double-counting). `ledger sync` never re-tags
    origin/status of existing rows and never creates a row whose payload
    hash matches an existing system rewrite's payload (a committed
    rewrite cannot launder itself into exogenous).
13. **Snapshot rule** (new): each loop iteration reads a frozen
    ledger/counter snapshot taken at iteration start. Wall-clock values
    (`wall_ms`) are reporting-only and never enter DL, scores, or
    tie-breaks. Two runs over the same snapshot produce byte-identical
    ranked-move logs.
14. **Evidence-sanitization rule** (new): lifted evidence enters LLM
    prompts only as canonical JSON of the learned machine / lifted schema
    with hash-classed outputs — never raw incumbent source or raw result
    strings. Prompt hashes are logged in the events that consume them.

---

## 3. Workpackages

Order and parallelism (§5 has the file matrix):

```
W0 (ledger+gate) ∥ W1 (translation-cert)     — disjoint files (W0's
                                                planner wrapper is additive,
                                                see W0.3); W1 is the
                                                cheapest falsifier of the
                                                central bet, do not queue it
   → W2 (planner + registry hardening)
   → W6 (monolith decomposition)              — user-directed, early: it
                                                validates the N-link planner
                                                on a real family before W5
   → W3 (scheduler) ∥ W4.1 (toll meter)
   → W4.2 (conversion)
   → W5 (promotion + the rung)
```

### W0 — One demand ledger, one currency, one gate

**Objective.** Every demand kind is a row in one ledger, priced in one
unit (`ledger_dl`), admitted through one gate with bounded, logged
exceptions.

- **W0.1 Demand table** (`library/__init__.py`, additive migration):
  DDL frozen in §4. Kinds: `spec-file`, `nl-request`, `caged-incumbent`.
  Columns include `origin` (house rule 12) and
  `status ∈ {open, covered, converted, retired}` — conversion is a status
  transition, never a kind mutation. `cgb.py ledger sync` (idempotent)
  ingests `specs/backlog/`, `specs/requests/`, `specs/incumbent/` as
  exogenous rows. Pins (builder dry-run): `payload_ref` = repo-relative
  path; `demand_id = sha256(kind + ":" + relpath)`; `features` = the
  atoms list via `planner.load_spec` for spec-files, NULL for an open
  nl-request (backfilled from the Reading by the W0.2 hook), and NULL
  for a caged-incumbent ⚠ (the tool alphabet is only observable by
  executing/learning the incumbent — fixed sync code cannot derive it;
  the W4 lift backfills it, and toll pricing never reads features).
  Demand-kind → chain target language: spec-file → `python-codec`,
  nl-request → `python-service`. Sync respects existing rows per house
  rule 12, and pre-lands the toll-counter INGEST path reading the §4.8
  JSONL format ⚠ (so W4.1 touches only the cage-side emitter — no
  shared `cgb.py` edit inside the W3 ∥ W4.1 parallel window).
- **W0.2 Readings/macros stores** ⚠ (fact 7 — the corpus must exist before
  anything prices or mines it): registry tables `readings`
  (`demand_id, reading_json, cert_id, admitted_at`) and `macros`
  (`name, template_json, admitted_at, cert_id, retired`). `certify_reading`
  gains an optional `on_certified` callable keyword invoked only on
  success; `run/semantic.py` never imports the registry — the caller
  closes over it (house rule 9). Pin ⚠ (`SemanticResult` exposes no
  single cert id and a run issues many certificates):
  `readings.cert_id` = sha256 of the canonical JSON of the successful
  layer list. `demo_ledger` seeds hand-written Readings (the
  `demos/demo_macros.py` corpus pattern) — no LLM on this path.
- **W0.3 The gate** (`buildloop/dl.py`, new; `buildloop/mdl.py` is FROZEN
  as the legacy codec-only series — no delegation, no byte-identity
  gymnastics; the loop switches to `dl.py` in W3, a deliberate,
  logged semantics change):
  - `cost(spec-file)` = chain cost + `size_bytes/256` if covered, else
    `UNCOVERED_PENALTY` (50.0). Chain cost comes from
    `plan_for_features`, which **W0 itself lands** in
    `planner/__init__.py` as a thin ADDITIVE wrapper over the existing
    1/2-link enumeration, behind the frozen §4.5 signature ⚠ (v2.0 had
    W0's done-when depending on a W2 API that did not yet exist, and
    forbade the only alternative — the mirror; W2.2 later replaces the
    wrapper's internals, signature unchanged). Never a re-implemented
    mirror. Interim: the nl-request compile-chain cost is the named
    constant `READING_CHAIN_COST = 2.0` in `dl.py` until W2.3 registers
    the reading language.
  - `cost(nl-request)` = compile-chain cost + `dl_reading(reading,
    macro_table)` if a certified Reading exists (W0.2 store), else
    `UNCOVERED_PENALTY`.
  - `cost(caged-incumbent)` = `min(TOLL_STOCK, UNCOVERED_PENALTY)` where
    `TOLL_STOCK = TOLL_RATE × calls_ingested_over_horizon(H)` ⚠ (the v1
    unbounded-toll defect: uncapped, high-traffic tolls made *un-serving*
    demand optimal; the cap guarantees caging ≥ uncovered never happens).
    `TOLL_RATE` and `H` are declared constants in `dl.py` with a
    commensurability docstring; both are named in every toll-bearing event
    and in TRUST.md (policy constants, by-fiat inputs to admission).
  - `generator_dl` prices the FULL authored artifact ⚠ (fact 6):
    `len(canonical body)/64 + len(grammar_js or payload)/64`.
  - **Admission**: admit iff `ledger_dl` strictly drops. Two bounded
    exceptions, each logged as its own event kind and never counted as a
    DL win: (a) *expansion* — admits a DL-inflating candidate only if it
    newly covers **exogenous** demand AND no already-admissible alternative
    covers the same rows ⚠ (the v1 OR-clause admitted the exact candidate
    the teeth required refusing — found independently by four lenses);
    (b) there is NO toll exception — ONE conversion admissibility
    formula, identical to the W4.2b post-state pricing ⚠ (v2.0 stated
    two different formulas; and with the retention monitor term
    uncapped, converting exactly the high-traffic incumbents the toll
    most targets was ledger_dl-INCREASING): admit iff
    `min(TOLL_STOCK, UNCOVERED_PENALTY) > replacement_chain_cost +
    replacement_size/256 + Δgenerator_dl +
    min(MONITOR_RATE × calls, MONITOR_CAP)`.
    Declared constants in `dl.py`, with defaults and constraints:
    `TOLL_RATE = 0.05` DL/ingested-call, `HORIZON_H = 1000` (unit =
    sync epochs, never wall-clock — house rule 13),
    `MONITOR_RATE = 0.01`, `MONITOR_CAP = 25.0`, ratio rule
    `MONITOR_RATE ≤ TOLL_RATE / 2`. Cheap-to-run incumbents honestly
    stay caged.
- **W0.4 Metrics**: the new series is named `ledger_dl` ⚠ (two same-named
  `total_dl` metrics otherwise coexist — `metrics/__init__.py:23,48-57`
  keeps emitting the legacy codec series) and lives in a NEW
  `ledger_metrics` table with its own CSV export — the fixed-column
  `metrics_log` INSERT is untouched (no unplanned migration); dashboard
  CSV per epoch:
  `{ledger_dl, covered/total by kind, tier mix, toll_paid, toll_retired,
  max_chain_depth_used (exogenous-serving only), kernel_loc}`.
  METRICS.md gains a section distinguishing the series; `milestones.py`
  m5/m7/m8 stay on the legacy series, labeled as such.

**Teeth.** (a) A synthetic generator covering one exogenous spec with a
huge `spec_grammar` is refused when a cheaper covering candidate exists,
admitted-as-expansion (logged, not a DL win) otherwise. (b) A candidate
with tiny atoms but a 20 KB `grammar_js` is refused (payload now priced).
(c) A system-origin rewrite row cannot trigger expansion. (d) A fake
incumbent with zero ingested calls contributes zero toll pressure.

**Done when:** `demos/demo_ledger.py` (LLM-free, joins `FAST_DEMOS`) exits 0
with all four teeth; `run_regression.py --fast` green; METRICS.md updated;
migration parity test (fresh vs migrated DB rows dict-equal) green.

### W1 — `translation-cert`: the generic rung contract

**Objective.** ONE kernel contract certifies any per-emission translation
`Spec_high → Spec_low`. New rungs become one deriver-table entry + one
TRUST entry — never a kernel edit. Lands in parallel with W0 (disjoint
files); its retrofit is the acceptance test of the whole plan's central
abstraction — if W1.3 fails, replan before building anything downstream.

- **W1.1 Contract shape** (five-touchpoint rule, once — concretely:
  `_subject_and_cdesc` branch, `_dispatch` branch, the declared pooling
  decision, the TRUST entry, demo teeth; `translation-cert` is NOT
  pooled, following the macro-cert precedent):
  `{type: "translation-cert", high_language, high_spec_text, low_language,
  low_spec_text, low_artifact_files, translator_hash,
  anchor ∈ {reference-lowering, fixed-deriver, incumbent-differential},
  reference_lowering?, expansion_context?, chain_links?,
  lowering_pipeline_hash?, oracle_ref?}`.
  `translator_hash` pin ⚠ (two builders would otherwise populate it
  differently, changing every cache key): the registry `generator_hash`
  when the translator is a registered entry; else sha256 of the fixed
  lowering module's source, named in the TRUST entry; the macro alias
  derives it compatibly with the existing `macro_table_hash` so
  `demo_macros` passes unchanged.
  - **Channel 1 (semantic):** obligations derived from the HIGH spec via
    the anchor — compile-hash identity against the reference lowering
    where one exists (macro pattern, fact 3), else solver obligations from
    the fixed deriver (Z3 ∧ CVC5 where both apply).
  - **Channel 2 (behavioral):** the LOW spec runs through the full
    existing chain below to an executable artifact, exercised by a harness
    derived from the HIGH spec **via a trusted lowering, never via the
    translator under test** (house rule 11; fact 3 shows the kernel
    already doing exactly this for macros).
  - **cdesc hashes** ⚠ (completeness-pass fatal: v1's cdesc omitted the
    channel-2 oracle — a deterministic lift means a trapdoor incumbent
    reproduces the honest incumbent's cache key and is served its PASS
    verdict; the trapdoor tooth never runs): high spec, low spec,
    translator hash, obligation set, `max_examples`, anchor,
    `reference_lowering`/`expansion_context` when present, and the chain
    below the low spec **per anchor** ⚠ (the kernel is stateless,
    `kernel/__init__.py:99-104` — callers supply these; and the macro
    retrofit's "chain below" is the fixed Reading compiler, which has no
    registry links, so a single planner-chain field has no denotation
    there): for `reference-lowering`/`fixed-deriver` anchors,
    `lowering_pipeline_hash` = sha256 over the fixed lowering module
    sources (kernel-computable); for contracts issued at emission time
    inside a planner plan, caller-supplied `chain_links =
    [{generator_hash, tier}]` (the caller has `plan.links` in hand at
    the emission site, `run/__init__.py`); `low_artifact_files` is the
    channel-2 subject; and for `incumbent-differential` the
    `oracle_ref = {incumbent_hash, cage_hash, sandbox_params}` (the
    cage-conformance CF3 pattern, `kernel/__init__.py:185-198`).
- **W1.2 Deriver table** ⚠ (v1 left the deriver architecture unspecified —
  builders would fork between kernel branches and a registry): fixed-code
  table in `generators/derivers.py`:
  `DERIVERS[high_language] = (derive_obligations(high_spec_text),
  derive_harness(high_spec_text))`. The kernel's `translation-cert`
  dispatch only looks up this table. Every new rung adds one entry + one
  TRUST.md 1.2x entry (amended acceptance: TRUST *grows* one honest entry
  per rung — the v1 "kernel gains nothing" grep pushed builders toward
  hiding trusted code in data).
- **W1.3 Retrofit (the acceptance test for generality):** (a)
  `macro-expansion-cert` re-expressed as `translation-cert` with
  `anchor=reference-lowering`, `reference_lowering=` the inlined reading,
  `expansion_context=` the macro table — all hashed into cdesc ⚠ (v1's
  shape could not express this instance: the existing cert binds four
  extra cache-identity inputs, `kernel/__init__.py:263-279`); old type
  string remains a dispatch alias (registry rows byte-frozen ⚠ — contract
  JSON folds into `generator_hash`, `library/__init__.py:107-110`;
  aliasing is kernel-dispatch-only). (b) The ABNF chain mapper cross-check
  becomes channel 1 of a `translation-cert` on the abnf→ksy stage; the
  per-stage check lands next to the existing emit-check block in
  `run/__init__.py` (fact 9 — ordinary edit; `run/__init__.py` is in this
  workpackage's file list). ABNF deriver pins: `anchor=fixed-deriver`
  with `DERIVERS["abnf"]` — `derive_obligations` returns the reference
  token list from `abnf_chain.tokenize` (the existing cross-check
  oracle), `derive_harness` a refcodec-differential harness built from
  `abnf_reference_fields`. `CERTS_VERSION` bump.
- **W1.4 TRUST.md**: the contract entry (what per-emission preservation
  claims relative to the named anchor and obligation set; what it never
  claims), plus the deriver-table section header under which per-rung
  entries accumulate. Contract-type allowlist test lands here (house
  rule 6) with SUBSET semantics: implemented dispatch types ⊆ frozen(the
  16 pre-existing types + `translation-cert` + `universal-translation`)
  AND `translation-cert` present — passes at W1 time
  (universal-translation allowed-but-absent) and at W5 time with zero
  edits; implemented types are extracted from a declared kernel constant
  added in W1's kernel window.

**Teeth.** (a) Planted lossy translator (drops a guard bound) refuted by
both channels. (b) Planted harness-from-low-spec wiring caught by the
provenance test (harness provenance hashes to the high spec / reference
lowering — scoped to anchors (a) and (b); oracle mode has its own tooth in
W4). (c) Cache-identity tooth: two contract instances identical except for
`oracle_ref` produce distinct cache keys (clean miss).

**Done when:** `demos/demo_macros.py` passes unchanged through the alias;
existing ABNF demos green; `demos/demo_translation_cert.py` (LLM-free, joins
`FAST_DEMOS`) exits 0 with all three teeth; allowlist test green;
`--fast` green.

### W2 — N-link planner; registry hardening; one chain-cost source

- **W2.1 Registry**: entries gain `kind ∈ {emitter, translator, pass}`
  (derived: translator iff `output_language` is a spec language; `pass`
  set explicitly by W6). ⚠ Fix the SELECT-*/positional-zip hazard first
  (fact 11): named-column SELECT (or `sqlite3.Row`) in `_row_to_dict`
  callers, `_migrate` extended to the generators table (ADD COLUMN at
  END matching `_SCHEMA` order), `register()` writes `kind`, backfill
  migration, and a parity test: pre-migration fixture DB and fresh DB
  produce dict-equal rows. ⚠ W2.1 also owns the **tier-vocabulary
  widening** (fact 16: the live CHECK admits only
  `{emit-check, universal}`; SQLite cannot alter a CHECK — table
  rebuild required, or W4.3's `conformance-relative(n)` and W5.1's
  honest bounded refusals hit the constraint at land time, with no
  workpackage allowed to touch the file by then). Vocabulary frozen in
  §4.12.
- **W2.2 Planner** (`planner/__init__.py`): replace the 1/2-link
  enumeration with **bounded exhaustive enumeration of simple chains**
  (no repeated generator hash) up to `MAX_CHAIN = 4`, then the existing
  sort key unchanged: `(-universal_links, len, lexicographic hash tuple)`.
  ⚠ Do NOT implement visited-set BFS: the universal-links preference is
  non-monotone under path extension (a longer all-universal chain must
  beat a shorter emit-check chain — the exact behavior W5's promotion
  flip relies on), and a visited set prunes precisely those chains; the
  defect would surface only after the first promotion (found independently
  by two lenses). Enumeration over registries this size is cheap and
  trivially deterministic.
- **W2.3 Language registry**: `planner.LANGUAGES[name] = load(text) ->
  atoms` with entries `ksy`, `abnf` (existing behavior preserved),
  `reading` (atoms = LF kinds from `reading.LF_KINDS`), `service-bundle`
  (atoms = bundle keys, W6), `macro-reading` (W5). ⚠ v1 had no owner for
  this and W6/W5 are unimplementable without it
  (`planner/__init__.py:62-67` hard-raises on unknown languages).
- **W2.4 One chain-cost source**: `planner.plan_for_features(entries,
  language, atoms, target_language="python-codec") -> chain | None` —
  takes an explicit entry list (registered + unregistered candidates;
  candidates get `tier="emit-check"` and a hash computed by the same
  canonical rule) ⚠ (v1's "delegate to the planner" was unimplementable:
  `plan()` demands spec text and candidates lack `tier`/`generator_hash`
  keys). The `target_language` parameter is required ⚠ (fact 16: today's
  terminal condition is hardcoded `python-codec` in three places, but W6
  needs chains ending at `python-service` — without the parameter two
  builders diverge on how a chain terminates); the demand-kind → target
  mapping is pinned in W0.1. The wrapper W0 landed keeps this exact
  signature; W2.2 replaces its internals. `dl.py` and `admission.py`
  call this; `mdl.chain_length_for` is frozen with the legacy series
  (W0.3). Depth-3+ coverage flipping old UNCOVERED decisions is an
  intended, logged semantics change of the NEW series only.

**Teeth.** (a) A 2-link all-universal chain beats a 1-link emit-check
chain to the same output. (b) A cyclic translator pair (A→B, B→A)
terminates with the right plan. (c) Serialized plans for every spec in the
live backlog (not just demo specs ⚠) are unchanged pre/post refactor, and
identical across two runs.

**Done when:** planner property tests green (incl. the whole-backlog plan
freeze); parity fixture test green; `--fast` green.

### W6 — Decompose the monolith into certified compiler passes

*(Numbered W6 for continuity with the critique; lands third, before the
scheduler and the rung — user-directed priority, and it validates the
N-link planner on a real family early.)*

**Objective.** `generators/service_gen.py` (fact 13) becomes a linear
pipeline of certified passes over a canonical-JSON **bundle**; each pass
is a translator entry with a `translation-cert` obligation; a fragment
addition becomes a pass insertion, never a monolith edit. The reference
implementation stays monolithic and code-disjoint (house rule 7).

- **W6.1 The bundle** (frozen in §4): canonical-JSON dict; keys are pass
  outputs (`spec_text, model, files, validators, constraints_table,
  transitions, initial, init_ctx, stack, monitor, golden_run, cases,
  order_contract`) — `order_contract` is produced by pass 1 from the
  model's frozen enforcement order and consumed by pass 7 ⚠ (v2.0 froze
  it in §4.6 but omitted it here; the two lists must agree). Pass
  entries register with `spec_language="service-bundle"`,
  `output_language="service-bundle"` (final pass `"python-service"`),
  and **accumulated** atom declarations ⚠ (the planner's
  subset-coverage semantics cannot unify per-pass-only declarations —
  pass 7 consumes keys produced by passes 2–6, so `produced(N) ⊄
  consumed(N+1)` under naive declarations): `spec_grammar.output.atoms`
  = the union of all upstream produced keys plus this pass's own;
  per-pass consumed keys live in a separate `consumes` metadata field
  used by tooth (a) for attribution. **Planner visibility** ⚠
  (`MAX_CHAIN = 4` cannot enumerate a 7-pass chain, and the sort key
  would always shadow it with the composite anyway): pass entries carry
  `kind="pass"` and are EXCLUDED from planning enumeration; the
  pipeline registers as ONE composite planner-visible entry (the
  planning and pricing unit, depth 1) whose `emit_entrypoint` records
  the pass sequence; the internal chain and its per-pass cert ids are
  reported by a registry introspection command
  (`cgb.py passes show <entry>`), not by the planner.
- **W6.2 The seven passes** (scout-verified boundaries, line evidence in
  the scout report; certificate obligations already latent in the kernel):
  1. **parse/normalize** — spec well-formedness (`service_model.py:201-217`).
  2. **tool/schema** — delegates `toolgen`; obligation: per-tool
     differential (`kernel/__init__.py:562-574`).
  3. **constraint** — delegates `constraint_gen`; obligation:
     constraint-cert dual-SMT (`kernel/__init__.py:613-631`).
  4. **protocol/stack** — absorbs `service_gen.py:47-68,115-143`;
     obligation: emitted `TRANSITIONS` conforms to the BMC model
     (`protocol_gen.py:193,292`).
  5. **obligation/monitor** — absorbs `:71-94,144-159`; obligation:
     monitor-cert per obligation + bundle tables ==
     `parse_monitor_module(monitor_gen output)`; MUST be a genuine no-op
     (empty keys, no flloat import) when `obligations == []` (fact 13's
     lazy-import gate, `:83-85`).
  6. **adversary/golden** — absorbs the ~490-line block (`:205-713`);
     obligation: every case is solver-witnessed (re-checkable dual-SMT);
     ⚠ exposes a PUBLIC API for the three external consumers that today
     reach into six private helpers (fact 13). The six helpers become
     thin deprecated SHIMS delegating to that API ⚠ (v2.0 demanded
     same-commit repoints of `run/guarded.py` and `reading_compile.py`,
     which §5 owns elsewhere — a builder honoring the matrix could not
     execute the instruction): `kernel/backends.py:216-253` repoints
     inside W6's own kernel window; `reading_compile.py:309-401` and
     `run/guarded.py:378,393` keep working through the shims and
     repoint later inside their owners' windows (shims stay until
     then).
  7. **assemble** — the template (`:160-200`) + harness builders
     (`:868-961`); obligation: service-conformance + liveness against the
     independent reference. ⚠ The runtime layer-ordering semantics
     (sequencing → stack-pre → schema → constraint → guard →
     obligation-check on PRE-advance monitor states → update → state
     advance → monitor advance) exist today only as interpolation
     positions (`:150-159,:177-199`); the assemble pass carries an
     explicit ORDER CONTRACT (a frozen list in the bundle) and its
     certificate obligation is exactly the ordering, probed by the
     existing stranding/isolating cases.
- **W6.3 Reference side**: `ref_service_source`/`_ref_accepts_src`/
  `_ref_run_body` (`:716-865`) move as-is into their own module,
  un-decomposed. ⚠ The byte-shared `_EVAL` interpreter (fact 13) is
  duplicated into an independently-written reference interpreter —
  the symmetric rule stops being qualified. Reference may read bundle
  DATA (tables), never pass code.
- **W6.4 Migration**: emitted bytes change — this workpackage retires the
  byte-identity golden for the service family in ONE conscious event:
  `CERTS_VERSION` bump, `tests/golden/byte_identity.json` regenerated,
  all demo specs re-certified (`orders, tickets, holds, nested_txn`),
  cage hashes recomputed. The conditional-emission discipline
  (`tests/test_byte_identity.py:104-122`) holds per-pass afterward: each
  pass emits empty fragments for unused features.
- **W6.5 Riskiest parts, in order** (scout): pass 7 (owns ordering
  semantics + symmetric boundary), pass 6 (three external consumers),
  the `_EVAL` duplication (flips `ref_service_source` bytes → cage_hash →
  every cage/intent cert re-binds — same bump window).

**Teeth.** (a) A planted defect in ONE pass (e.g. a dropped transition in
pass 4) is caught by THAT pass's certificate, not only by the end-to-end
differential. (b) A pass-order mutation (obligation-check moved after
monitor advance) is refused by the assemble pass's order contract.
(c) A service spec with no obligations produces a bundle with empty
monitor keys and imports no flloat (parity with today's gate).
(d) The fragment-insertion payoff demo: a toy pass inserted between 4 and
5 without touching any other pass's code.

**Done when:** `demos/demo_passes.py` (LLM-free, joins `FAST_DEMOS`) exits 0
with all four teeth; all existing service demos re-certify; the planner
shows the service family as a 2-link chain (reading → meta-spec via
`reading_compile`, meta-spec → code via the composite entry) and
`cgb.py passes show` reports the 7-pass internal chain with per-pass
cert ids ⚠ (v2.0 asked the PLANNER to show the internal chain — 
structurally impossible under `MAX_CHAIN = 4`); `--fast` green;
channel-parity test (`tests/test_channel_parity.py`) still green.

### W3 — The miss-typed scheduler (one loop, four signals)

- **W3.1 Miss taxonomy** (`buildloop/loop.py` refactor):
  - `coverage-miss` (exists): planner fails on a spec-file demand →
    breadth move (unchanged pipeline).
  - `request-miss` ⚠ (the v1 fatal gap: NL requests were priced but NO
    move could serve them — the height axis starved at 3 hand-written
    readings): an nl-request row with no certified Reading schedules the
    EXISTING semantic pipeline (`service_loop.synthesize_service` /
    `run/semantic.certify_reading`), recording the Reading in the W0.2
    store on success.
  - `recurrence-miss` (`buildloop/recurrence.py`, new, fixed code):
    deterministic mining over the W0.2 readings store — contiguous
    statement windows of length 2..L over demand-force statements,
    cluster key = LF-kind tuple, candidates = maximal clusters with ≥2
    occurrences unifiable under `mdl_macros._unify`, `dl_saving`
    computed **against the live macro table** ⚠ (table-blind mining
    double-counts savings already captured by admitted macros —
    `mdl_macros.py:120-141` rewrites greedily longest-first).
  - `toll-miss`: caged incumbents ranked by capped toll stock (W0.3),
    emitting conversion candidates (W4.2).
- **W3.2 Scheduler**: one `run_iteration(registry, ledger)` over a frozen
  snapshot (house rule 13). Scores are **declared optimistic upper
  bounds** with named deductions ⚠ (v1 compared gross coverage bounds to
  net recurrence savings): coverage = `UNCOVERED_PENALTY × |group| −
  median_live_generator_dl`; request = `UNCOVERED_PENALTY` per request;
  recurrence = live-table `dl_saving`; toll = capped stock − estimated
  replacement cost. Pick max; deterministic tie-break (kind order, then
  lexicographic). Every considered-but-not-picked move logged with its
  score (auditable, replayable from the snapshot). Realized ΔDL logged
  against expected after each move (systematic bias visible).
  **Refusal memory** ⚠ (verified livelock: a refused conversion's
  standing toll is monotone; once argmax, the scheduler re-runs the doomed
  pipeline forever): on refusal, record `(candidate_key, evidence_hash,
  reason)` and suppress the candidate until its evidence changes (for
  conversions: a larger lift bound or changed tool surface), logged as a
  first-class suppression event.
  **Terminal state**: `run_iteration` returns `converged` when no move
  scores positive and no misses remain (fact 15 — the corpus is finite;
  convergence is the honest outcome, stated in §7's acceptance).
  Existing callers (`cgb.py:117`, `metrics/run_experiment.py:48`) are
  updated in this workpackage (they are in §5's matrix ⚠ — v1 omitted
  them).
- **W3.3 Macro GC** ⚠ (verified: greedy longest-first rewriting lets a
  new macro strand an old one below 2 uses while its `dl_macro` is paid
  forever; generators retire via `find_subsumed`, macros had no path):
  after each macro admission, recompute `reading_uses` over the corpus
  against the live table; retire (provenance-kept, excluded from table
  and cost) any macro below 2 uses whose removal strictly reduces
  `corpus_dl`. Retirements are first-class events.

**Teeth.** (a) Ordering: with 3 clustered readings AND an uncovered
2-spec codec group on the same snapshot, coverage (2×50 upper bound) is
picked first; after it lands, recurrence — asserted from the decision
log. (b) A refused trapdoor conversion does NOT win the next round
(suppression). (c) Two runs over one snapshot: byte-identical ranked-move
logs. (d) Admit macro A (2 uses), then subsuming B: A retired,
`corpus_dl` drops by `dl_macro(A)`. (e) A one-off pattern (uses=1) never
becomes a candidate.

**Done when:** `demos/demo_scheduler.py` (LLM-free — request-miss exercised
with a pre-canned Reading fixture, joins `FAST_DEMOS`) exits 0 with all
five teeth; `run_regression.py --fast` green; live request-miss
synthesis goes through `--full` only.

### W4 — Cage as intake: meter, then conversion

- **W4.1 Toll meter**: the cage appends per-call records
  `{incumbent_hash, tool, verdict_layer, wall_ms}` to a task-time-local
  append-only JSONL (its OWN file, never the ledger DB ⚠ — the v1 design
  either violated one-writer or produced a toll signal the scheduler
  never sees); `cgb.py ledger sync` ingests counters at epoch start (the
  loop remains the ledger's sole writer). `wall_ms` is reporting-only
  (house rule 13). ⚠ Cage-certificate claims are assembled in the KERNEL
  (fact 8), so the toll-meter claim is one small kernel edit — it is
  scheduled HERE, serialized after W6's kernel window, not smuggled into
  a "parallel" track (v1's serialization self-contradiction).
  `CERTS_VERSION` bump; `results/cage_certificate.json` recaptured.
  TRUST.md: toll meter extends the cage section (1.2i) — a by-fiat
  counter input to admission; a meter bug can mis-prioritize conversions,
  never certify anything.
- **W4.2 Conversion move** (`buildloop/convert.py`, new), split in two:
  - **W4.2a lift → spec → replacement-cert**: schema-lift + protocol-lift
    (existing) → LLM authors the replacement spec from **sanitized
    evidence only** (house rule 14 ⚠ — today's lift embeds raw incumbent
    source in prompts; a malicious incumbent can steer the authored spec
    via comments/docstrings/output strings and the circular oracle would
    certify it) → replacement generated through the normal pipeline →
    `translation-cert` with `anchor=incumbent-differential`,
    `oracle_ref={incumbent_hash, cage_hash, sandbox_params}` hashed into
    cdesc (W1.1 ⚠), channels = W-suite + random-walk differential and
    containment respected.
  - **W4.2b swap + retirement**: defined mechanics ⚠ (v1's "swap cargo"
    had no referent): conversion is a LEDGER + REGISTRY transition — the
    demand row's `status` becomes `converted`, `payload_ref` points to
    the replacement's artifact/cert ids; the cage object is never
    mutated. Cost switches on status: a converted row is priced as a
    spec-file demand (replacement chain cost + size/256) plus, during
    retention, `min(MONITOR_RATE × calls, MONITOR_CAP)` — exactly the
    post-state side of W0.3's single conversion formula ⚠ (v2.0 stated
    two different formulas here and in W0.3; there is ONE, defined in
    W0.3, and this pricing is its right-hand side).
- **W4.3 Honesty and retention**: the replacement's tier is
  `conformance-relative(n)` — never plain emit-check ⚠ (both the lift's
  obligations and the differential oracle reduce to the same unverified
  incumbent; calling it emit-check inflates the tier ledger). The
  non_claims (state bound n, abstraction map, oracle circularity) are
  inherited PERMANENTLY by the replacement's registry entry and shown in
  the ledger tier mix. **Default retention = shadow mode**: monitors on,
  incumbent archived as the re-certification oracle ⚠ (non_claims are
  time-invariant — one clean epoch adds no coverage of future inputs;
  and dropping the incumbent destroys the only oracle, making the cert
  unrecoverable after any later `CERTS_VERSION` bump). Full drop only by
  an explicit policy decision logged with the surviving non_claims.

**Teeth.** (a) Honest incumbent: caged → toll ingested (synthetic
traffic, labeled synthetic in the event ⚠) → converted → toll retired →
`ledger_dl` strictly drops; the full arc in one demo. (b) Trapdoor
incumbent (the `demos/demo_protocol_lift.py` part-B machine): conversion
refused when the W-suite at larger n disagrees; the refusal event says
why; the toll keeps accruing, honestly; the scheduler suppresses the
candidate (W3 tooth b re-asserted here end-to-end). (c) Cache tooth ⚠:
two incumbents identical up to bound n, differing beyond it — clean
cache miss, independent verdicts (the completeness-pass fatal).
(d) Injection tooth ⚠: an incumbent whose docstrings/outputs embed an
instruction to widen the spec yields either a spec identical to the
uninjected run or a refusal. (e) A nondeterministic incumbent aborts with
the existing first-class event.

**Done when:** `demos/demo_conversion.py` (REQUIRES_LLM=True, `--full` only,
measured runtime budgeted vs the 900 s cap ⚠ — split the arc across two
demo parts if the measured time exceeds 700 s) exits 0 with all five
teeth; ledger shows the status transition; dashboard shows
`toll_retired > 0`; TRUST.md conversion section landed.

### W5 — Promotion generalized; the rung

- **W5.1 Promote translators** (`buildloop/promote.py`): dispatch on
  entry `kind`. Contract `universal-translation`: channel 1 = proof over
  the TRANSLATOR (Dafny model where the family has one; else
  bounded-exhaustive enumeration to size N adjudicated by Z3 ∧ CVC5),
  channel 2 = spec-level behavioral fuzz through the REAL pipeline —
  genuinely different procedures, never enumeration-vs-sampling of the
  same predicate ⚠. **Tier routing** ⚠ (verified: `promote.py:74` sets
  `universal` unconditionally and the planner recognizes only that tier —
  an implementer following v1 produced silently-universal behavior):
  per-emission checks stop and planner preference applies IFF
  `tier == "universal"`; a `complete-to-size(N)` outcome is an explicit
  promotion REFUSAL that retains emit-check duty (the certificate is
  kept as evidence only); `promote()` must never `set_tier` from a
  non-universal-tier certificate.
- **W5.2 The rung — macro-vocabulary notation over Readings** ⚠ (v1's
  either/or is resolved; the `logline` candidate is economically dead on
  the real backlog: ABNF specs are 28–47 bytes, so a third link's +1.0
  chain cost can never be repaid by ≤0.18 of size saving — verified
  arithmetic): once ≥3 macros are admitted (W3's mined path feeds this;
  request-miss feeds the mining corpus), mint `macro-reading` — a
  notation whose statements may be macro invocations, lowered by a fixed
  translator to plain Readings. 3-link exogenous-serving chain:
  `macro-reading → reading → meta-spec → service`. Per-emission
  `translation-cert` with `anchor=reference-lowering` (the expanded
  reading — the macro machinery is the trusted lowering, fact 3).
  **Equivalence anchor for rewrites** ⚠ (v1's acceptance rewarded lossy
  rewriting — the DL objective pays for deletion): every rewritten
  demand row keeps its original as baseline (house rule 12); the rewrite
  lowered through the chain must compile-hash-identical to the
  original's compiled spec, or it is refused; a planted lossy rewrite
  (dropped safety statement) is a tooth.
- **W5.3 Acceptance, quantitative and honest**: on the NL request corpus,
  rewritten items have strictly lower authored DL **with certified count
  unchanged and equivalence anchors green**; `max_chain_depth_used`
  (exogenous-serving) reaches 3; `ledger_dl` strictly below the pre-rung
  baseline on the same snapshot; a promotion attempt on the macro-reading
  translator succeeds as universal OR refuses honestly with
  `complete-to-size(N)` — both outcomes acceptable, mislabeling is not.

**Teeth.** (a) Planted lossy rewrite refused by the equivalence anchor.
(b) Planted unsound translator passes emission checks on sampled specs
but fails promotion (the tier lattice doing its job). (c) A
non-universal certificate never flips the tier (unit tooth on
`promote()`).

**Done when:** `demos/demo_rung3.py` (REQUIRES_LLM=True, `--full`, budgeted)
exits 0 with all three teeth; dashboard shows the height metric at 3 and
the DL drop; LINGUISTICS.md updated (the rung's place in the
analysis-vs-proof split ⚠ — v1 omitted LINGUISTICS.md entirely from the
docs set).

---

## 4. Interface-freeze list (agree before ANY parallel work; changes = serialized cross-workpackage commit)

1. **Demand table DDL** (W0.1):
   `CREATE TABLE demand (demand_id TEXT PRIMARY KEY, kind TEXT CHECK(kind
   IN ('spec-file','nl-request','caged-incumbent')), origin TEXT
   CHECK(origin IN ('exogenous','system')), status TEXT CHECK(status IN
   ('open','covered','converted','retired')), language TEXT, features
   TEXT /* canonical-JSON: atoms list | LF-kind multiset | tool alphabet */,
   payload_ref TEXT, size_bytes INTEGER, created_at TEXT)`.
2. **Readings/macros stores** (W0.2): `readings(demand_id, reading_json,
   cert_id, admitted_at)`; `macros(name, template_json, admitted_at,
   cert_id, retired INTEGER DEFAULT 0)`.
3. **translation-cert contract keys and cdesc fields** — exactly as W1.1
   (including `low_artifact_files`, `chain_links?`,
   `lowering_pipeline_hash?` and the per-anchor cdesc rule; the
   `translator_hash` pin); `anchor` vocabulary frozen:
   `{reference-lowering, fixed-deriver, incumbent-differential}`.
4. **Deriver table** (W1.2): `generators/derivers.py`,
   `DERIVERS[high_language] = (derive_obligations, derive_harness)`;
   signatures `derive_obligations(high_spec_text: str) -> list`,
   `derive_harness(high_spec_text: str) -> dict[filename, bytes]`.
5. **Planner** (W0.3 wrapper, W2 internals): `Plan`/`CoverageMiss`
   dataclass shapes unchanged; `MAX_CHAIN = 4` (pass entries excluded
   from enumeration, §W6.1); `planner.LANGUAGES` registry;
   `plan_for_features(entries, language, atoms,
   target_language="python-codec")` with candidate defaults
   `tier="emit-check"`, hash by the canonical rule.
6. **Bundle keys** (W6.1): `{spec_text, model, files, validators,
   constraints_table, transitions, initial, init_ctx, stack, monitor,
   golden_run, cases, order_contract}` — canonical-JSON;
   `order_contract` produced by pass 1, consumed by pass 7; pass
   entries declare ACCUMULATED `output.atoms` (union of upstream
   produced + own) with per-pass `consumes` metadata kept separately;
   pass entries are `kind="pass"`, planner-invisible.
7. **Miss records** (W3.1): four dataclasses
   `{CoverageMiss (existing), RequestMiss, RecurrenceMiss, TollMiss}`,
   each `to_dict()`-able, logged verbatim.
8. **Toll meter** (W4.1): JSONL records `{incumbent_hash, tool,
   verdict_layer, wall_ms}`; ingest key `toll:{incumbent_hash}:calls`;
   constants `TOLL_RATE`, `HORIZON_H`, `MONITOR_RATE` in
   `buildloop/dl.py` only.
9. **Conversion event** (W4.2b): `{demand_id, incumbent_hash,
   replacement_cert_id, dl_before, dl_after, toll_retired,
   synthetic_traffic: bool, prompt_hash}`.
10. **Scheduler decision log** (W3.2): per-iteration
    `{snapshot_hash, moves: [{kind, candidate_key, expected_dl_delta,
    picked: bool, suppressed_by?}], realized_dl_delta}`.
11. **Dispatcher `call()` / layer enum / Reading statements / kernel
    channel dicts / monitor module / incumbent interface**: unchanged
    from ROADMAP.md's freeze list.
12. **Tier vocabulary** (W2.1 owns the widening migration, fact 16):
    `{universal, emit-check, bounded-K, complete-to-depth(D),
    complete-to-size(N), conformance-relative(n), monitored,
    tier-unclassified}`. Only `universal` flips planner preference and
    stops per-emission checks (W5.1).
13. **`FAST_DEMOS` convention**: additions are one-line appends landing
    in each workpackage's own demo commit, append-only in workpackage
    order, union-merged — the only file two parallel tracks may both
    touch, by exactly this rule.

## 5. Ownership & serialization for the builder swarm

Hot files (strictly serialized, in landing order):
- `kernel/__init__.py`, `kernel/backends.py`, `kernel/certs.py`: W1 →
  W6 → W4.1 → W5.1. Nothing else touches them ⚠ (v1 said "R1/R5.1 only"
  while W4.1's claim edit and W6's contract re-binding both need the
  kernel — that contradiction is resolved by scheduling, not denial).
- `library/__init__.py`: W0.1/W0.2 → W2.1 → (W4.2b status columns ride
  W0.1's DDL, no later edit).
- `planner/__init__.py`: W0.3 (the additive `plan_for_features` wrapper
  ONLY — `plan()` and everything else untouched) → W2.
- `generators/service_gen.py` + new pass modules + reference module:
  W6 only. `generators/reading_compile.py`: untouched by this plan
  (pass-6 shims preserve its reach-ins; it repoints in a future window).
- `buildloop/loop.py`: W3 only (W4.2 plugs in via the frozen
  ConversionCandidate interface; W3 lands the registered-callable stub
  `run_move(kind, candidate, registry, ledger) -> admission_event`).
- `run/__init__.py`: W1.3(b) only. `run/guarded.py`: W4.1/W4.2 (W6
  leaves it untouched — the pass-6 shims). `run/semantic.py`: W0.2 hook
  only.
- ⚠ Files v1 omitted, now owned: `cgb.py` (W0.1 sync INCLUDING the
  toll-ingest path — pre-landed so the W3 ∥ W4.1 window has no shared
  edit; W3.2 caller), `metrics/run_experiment.py` +
  `metrics/__init__.py` (W0.4, W3.2), `milestones.py` (W0.4 labels),
  `run_regression.py` (every workpackage that adds a demo, under the
  §4.13 append-only convention).

Safe parallel tracks: **W0 ∥ W1** (disjoint); after both: W2; after W2:
W6; after W6: **W3 ∥ W4.1** (loop.py vs guarded.py + one serialized
kernel commit for W4.1's claim); then W4.2; then W5. Docs
(README / TRUST / **LINGUISTICS** ⚠ / METRICS) are merge-owned: each
workpackage's final serialized commit.

PR sizing ⚠: W1 lands as W1a (contract + touchpoints + teeth + TRUST)
then W1b (both retrofits + aliases + bump). W4.2 lands as W4.2a / W4.2b.
W6 lands pass-extraction-by-pass-extraction (7 commits minimum, each
keeping `--fast` green), with W6.4's bump + golden regeneration as the
final commit.

## 6. Out of scope (cut/frozen)

- `generators/monoid.py` / `demos/demo_tier.py`: frozen — kept green, no
  investment.
- No new logic fragments and no new seed domains until the loop converges
  once on the committed corpus. The W5 rung is a notation over the
  EXISTING Reading domain (not a new domain; the v1 `logline` candidate
  is dropped on verified economics).
- No EverParse; LTLf monitors, JSON codec, nested sessions kept as-is
  (certified assets; monitors are a cage dependency).

## 7. End state, restated as acceptance

1. One ledger prices all three demand kinds in `ledger_dl`; the dashboard
   shows the loop running to its **converged** terminal state on the
   committed corpus with `ledger_dl` strictly below the W0 baseline —
   convergence on finite demand is the honest claim, not an ever-falling
   curve (fact 15).
2. New rungs are deriver-table + registry data certified by
   `translation-cert`; the contract-type allowlist test pins exactly two
   new types; TRUST.md grows one honest entry per rung.
3. The planner composes chains to depth 4 with the universal-links
   preference intact; the whole-backlog plan freeze is green.
4. The monolith is seven certified passes + one disjoint monolithic
   reference; a fragment insertion demo touches exactly one pass.
5. The scheduler runs four move types from typed misses over frozen
   snapshots, with refusal memory, an auditable decision log, and
   realized-vs-expected ΔDL tracking.
6. A caged incumbent has been converted end-to-end (toll retired, tier
   honestly `conformance-relative(n)`, non_claims inherited); a trapdoor
   incumbent has been refused, suppressed, and kept honestly caged; the
   injection tooth is green.
7. The macro-reading rung serves exogenous NL demand at depth 3 with
   equivalence anchors green, and its promotion attempt resolved
   honestly (universal or explicit bounded refusal).
8. And the emit-check tier is still there — because it always will be.

## 8. Critique provenance (for the implementation swarm's calibration)

Confirmed and incorporated: 30+ findings across six lenses + completeness
pass; every ⚠ above cites its evidence. Highest-signal convergences: the
admission gate's OR-clauses (4 independent lenses), channel-2
independence/anchoring (3 lenses), the missing request-move (scope,
fatal), the cdesc/oracle cache collision (completeness, fatal), planner
BFS non-monotonicity (2 lenses).

Refuted by the adversarial verifier — do NOT re-litigate:
- "Cage cert_id drift breaks captures": nothing compares cage cert_ids;
  captures regenerate (recapture noted in W4.1).
- "ABNF retrofit forbidden at task time": task-time `kernel.check` for
  emit-check links already exists (`run/__init__.py:91-96`); the guard
  forbids LLM calls only.
- "entailed_scenarios makes channel 2 unimplementable": the kernel
  derives scenarios via the trusted reference lowering
  (`kernel/__init__.py:761-766`); the fix was tightening wording (house
  rule 11), not redesign.
Also cleared by the completeness pass: sandbox throughput (L* batching is
sound) and `CGB_TASK_TIME` guard reentrancy (depth-safe).

**v2 → v2.1 (this version):** v2 itself was then re-verified by a second
swarm round — a fix-coverage audit (39/40 v1 findings fully resolved,
none lost or regressed; the one partial was the `cgb.py` toll-ingest
ownership seam, fixed here), a fresh-eyes critique with no knowledge of
the v1 round (3 fatal: the W0→W2.4 dependency inversion, the
MAX_CHAIN-vs-7-pass contradiction, the tier CHECK constraint; 6 major:
per-anchor cdesc denotation, the two inconsistent conversion formulas +
uncapped retention term, W6 pass-6 cross-ownership edits,
exogenous-serving attribution, bundle atom threading under
subset-coverage, the missing `target_language` parameter; 1 minor:
`order_contract` list drift — all fixed here), and a builder dry-run of
W0+W1 (18 decisions specified, 12 latitude with recorded defaults, 5
blockers — all pinned here: the planner-wrapper interim, incumbent
`features=NULL` backfill, `readings.cert_id` derivation, the cdesc
chain-field sources, the `translator_hash` rule; parallelism verdict:
W0 ∥ W1 holds at file level given §4.13). No unaddressed findings
remain from any round.
