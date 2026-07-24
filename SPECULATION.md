# SPECULATION.md — Zone 3: the speculative planner (re-anchored to the unified tree)

README.md says what the system is. TRUST.md says what is trusted. ROADMAP.md
says what got built. PLAN_COMBINED_LOOP.md unified breadth/height/intake into
one demand ledger. This document specifies **Zone 3: the speculative
planner** — the layer that decides what the expensive machinery (LLM calls,
kernel invocations) spends itself on, by consulting the system's exact
description-length accounting *before* paying rather than after.

It is written to be executed by a swarm of builder agents **without access to
the conversations that produced it**. Provenance: (1) drafted against
pre-Combined-Loop main; (2) hardened by a five-lens adversarial sweep (45
findings, H1–H45); (3) **re-anchored by a three-agent sweep against the
unified tree** (main @ `abad328`, which merged Combined Loop v2.1) — that
sweep found the Combined Loop had independently landed *greedy* versions of
several Zone-3 components, so this revision re-scopes Zone 3 from
"build the planner" to **"upgrade the landed greedy machinery to searched,
and make its honesty disciplines explicit"** (findings H46–H58). Every ⚠ was
verified with file:line evidence or by executing an experiment against the
live modules.

## What the tree already does (the re-anchored premise)

The Combined Loop replaced the old reactive loop with a **miss-typed
scheduler**: `buildloop/loop.py:run_iteration` (now line 480) takes one
frozen `dl.snapshot(registry)`, scores four move kinds — coverage / request /
recurrence / toll — via `score_moves` (:321, pure over the snapshot, wall
clock banned by house rule 13), picks the argmax, logs a
`scheduler-decision` with `snapshot_hash`, and dispatches. Inside it:

- **Coverage** moves are priced with `planner.plan_for_features`
  (`planner/__init__.py:182` — N-link chains to `MAX_CHAIN = 4`,
  hypothetical-safe: unregistered candidates get default tier/hash) and
  `dl.generator_dl`; when coverage wins, `_dispatch_coverage` (:425)
  re-derives miss groups and calls the surviving
  `pick_group(groups, policy, ...)` (:120–140, `frequency`/`closure`).
- **Recurrence** moves ARE macro mining: `buildloop/recurrence.py` does real
  LGG anti-unification over demand-force statement windows (len 2–4,
  kind-tuple clustering, `_match_at` round-trip verification, ≥2 distinct
  readings, priced against the live table with `mdl_macros.corpus_dl`),
  stores winners in the registry **`macros` table** (`m_<sha12>` names,
  `retired` column), and runs `gc_macros` retirement after every admission.
  Admission is **greedy**: one max-marginal-saving macro per iteration.
- A **`readings` table** persists certified Readings keyed by `demand_id`,
  joined to the **`demand` ledger** whose `origin ∈ {exogenous, system}`
  column is provenance (exogenous rows are byte-matched against committed
  `specs/requests/` files at `cgb.py ledger sync`).
- **`ledger_dl`** (`buildloop/dl.py`) is the loop's declared one currency;
  the old `mdl.total_dl` series is frozen legacy (but still enforced by the
  per-candidate gate at `buildloop/admission.py:202` and recorded by the
  legacy metrics — an honest residue this plan states rather than hides).

Zone 3's thesis is unchanged: **simulate the price, then spend.** What
changed is that the greedy baseline now exists in the tree, which makes the
searched upgrade *measurable against a live opponent* rather than a
synthetic one.

After all phases land:

1. **Macro vocabulary is searched, not greedy** (S1): beam search over
   admission *sequences*, each step still passing the unchanged per-macro
   MDL gate, replacing the scheduler's one-max-saving-macro-per-iteration
   behavior — plus the miner filters (wildcards, mixed force/quote) the
   landed miner lacks.
2. **Coverage steering is lookahead-driven** (S2): multi-step rollouts of
   hypothetical admissions, priced through `plan_for_features`, as an
   additive `pick_group` policy.
3. **Design choices are optimized** (S3): enumerate the choice-residue,
   select the minimum macro-aware-DL design that entails every demanded
   ordering — Occam mechanically forbidden from overriding the text.
4. **Synthesis fans out K-wide against cheap pre-gates** (S4), certifies
   only through the unchanged kernel, and logs every prediction miss.
   ⚠H8 stands: the repo's own captures show 1–3 rounds or
   pre-gate-invisible failure, so S4 is a *measured trade*, not a promised
   saving.
5. **Dreams propose, real witnesses decide** (S5): the real/dream partition
   rides the ledger's own `demand.origin` provenance — a strictly stronger
   foundation than the draft's path inference (⚠H55).

## Trust posture (read this before writing any code)

The planner is **untrusted-by-construction, exactly like the LLM**. House
rules of ROADMAP.md and PLAN_COMBINED_LOOP.md bind here; three
planner-specific rules:

- **Z1 — proposals only.** No planner output is ever a certificate or a
  verdict, and no cache entry read by a verdict may exist unless it was
  computed **by the unchanged kernel on the identical (artifact, contract)
  identity** the non-speculative path would have used (⚠H9: warmed entries
  change *when* the kernel ran, never *what it concluded*).
- **Z2 — exact objectives first (re-anchored, ⚠H49/H50/H51).** Phases S1–S3
  may only score with the exact pure functions **of the live economy**:
  `dl._ledger_total` over `dl.LedgerSnapshot` (hypotheticals via
  `dl._with`), `planner.plan_for_features` (the declared single chain-cost
  source, `dl.py:11-13`), `mdl_macros.corpus_dl`/`dl_reading`, and
  deterministic compile + reference replay. `mdl.total_dl` /
  `mdl.chain_length_for` are **struck as objectives** — frozen legacy,
  verified divergent from the planner (blind to `kind=="pass"` and to
  3–4-link chains); they may appear only as *reported* legacy series for
  continuity with recorded metrics. Learned/heuristic scores stay confined
  to S4/S5 and ship with the divergence ledger in the same commit.
- **Z3 — measured fidelity.** Any component that *predicts* a kernel or
  gate verdict logs prediction-vs-actual as a first-class
  `speculation-divergence` event (`registry.log_event`,
  `library/__init__.py:319`; `cgb.py events`, cmd at `cgb.py:459`).

No phase adds a kernel contract; `kernel/*`, `generators/service_gen.py`,
`generators/reading.py`, `generators/reading_compile.py`, `run/semantic.py`,
and `library/__init__.py` are read-only (calling backend machinery —
`SmtBackend.run_z3` at `kernel/backends.py:487`,
`HypothesisBackend.check_intent_reference` at `:243` — is permitted, ⚠H12).

⚠H58 (supersedes the draft's H1/H5 wording): mined macros are **no longer
accounting-only-forever** — the Combined Loop landed the W5.2 macro-reading
rung. Every *actual* macro use is certified per-emission by
`translation-cert(anchor="reference-lowering")` whose channel 1 is
compile-hash identity against the **retained original baseline reading**
(`kernel/__init__.py:321-348`; teeth in `tests/test_rung.py` prove a lossy
rewrite is refused), and the macro table enters cache identity as
`expansion_context` (`kernel/__init__.py:329-330`). This *already
implements* H5's anti-tautology rule (the comparand originates independently
of the table). The S1 TRUST amendment therefore documents rather than
invents: a mined table is untrusted, data-derived vocabulary; the rung is
what makes its uses safe; `macro-expansion-cert` remains the P5.2 alias.

## Phases

Logical order: S0 → S1.1 → {S1 rest ∥ S2} → S3 → S4 → S5. Scheduling is by
the work packages below.

### S0 — Reading-corpus provisioning (content + bridge, not persistence)

⚠H46 (re-anchored premise): a persisted corpus store **exists** — the
`readings` table (`library/__init__.py:88-93`:
`readings(demand_id PK, reading_json, cert_id, admitted_at)`, accessors
`reading_add`/`reading_get`/`readings_all` at :478-499) with provenance on
the joined `demand` row (`origin ∈ {exogenous, system}`, `payload_ref` =
committed request path). But it is **empty on a fresh checkout and its live
fill path is broken**: `_dispatch_request` (`buildloop/loop.py:446-452`)
passes `payload_ref` (a *path string*) where request *text* belongs, and
gates persistence on a `"reading"` key that `synthesize_service` never
returns (only `synthesize_semantic` does, `service_loop.py:296-301`) — so
`reading_add` is unreachable live and recurrence mining has nothing to mine.
S0's job is therefore: **committed content + the file→table bridge**, and
the fill-path fix is assigned to S4 (which owns the synthesis path).

- **S0.1** New directory `specs/readings/`: one JSON file per entry,
  `{request: str, reading: {service, statements: [...]}}`. Bootstrap:
  - the three `demos/demo_macros.py` corpus entries in **inlined form** —
    `_reading(**c)[0]` paired with `c["request"]` (⚠H14);
  - hand-written Readings for the **named faithful set**: requests 01, 02,
    03, 04, 05, 06, 09, 14, 15, 17, 18 (⚠H15: the other six need dodges the
    frozen fragment cannot express — disjunctive eventuality 07/16/19,
    trigger-relative `within` 08, nesting 10/11; vague 12/13/20 are S3's
    search space, not transcription targets). Every entry passes
    `parse_reading` (`generators/reading.py:264`) with no LLM.
- **S0.2** `buildloop/reading_corpus.py` (⚠H16: not "corpus" — that name
  means the failing-input corpus) — re-scoped as the **file→table bridge**:
  - `load_readings(dir) -> list[CorpusEntry]`, `CorpusEntry(request,
    statements, source)` a new dataclass — never `reading.Reading`, whose
    `.source` field holds raw JSON text (`reading.py:495`, ⚠H17). Used by
    tests and miner fixtures; **runtime consumers read the snapshot, never
    the files**.
  - a seed step `cgb.py ledger seed-readings` (same family as `ledger
    sync`): for each file, byte-match `request` against a committed
    `specs/requests/` file (⚠H44 — enforcement lives at seed time, where
    `ledger sync` already byte-matches payloads), resolve
    `demand_id = sha256("nl-request:"+relpath)`, **certify** the reading via
    the LLM-free `certify_reading` (which now takes `macro_table=` and
    `on_certified=`, `run/semantic.py:70-72`), and persist with
    `registry.reading_add`. Seeds are certified with real `cert_id`s — the
    corpus is small and `dl.py:247-251` treats any readings row as
    coverage, so uncertified seeds would silently improve `ledger_dl`
    (⚠H46b: the honest default is certify-at-seed).
  - **`source` is derived, not inferred from paths** (⚠H55): real ⇔ joined
    `demand.origin == "exogenous"`, dream ⇔ `"system"`. Files under
    `specs/readings/dream/` are seeded with system-origin demand rows; a
    real-classified seed with no committed request byte-match is a hard
    error at seed time. No `source` key in files. No `load_macros()` — the
    macro accessor is `registry.macro_table()` (⚠H48).
- **Done when:** ≥ 14 entries seed and certify on a fresh DB;
  `tests/test_reading_corpus.py` green; `run_regression.py --fast` < 90 s
  (tests auto-collect, `run_regression.py:108`; never touch `FAST_DEMOS`,
  ⚠H18).

### S1 — Searched macro admission (upgrade the landed greedy miner)

⚠H47: `buildloop/recurrence.py` already implements most of the draft's
S1.2 — real anti-unification (`_antiunify` :62, memoized `$pN`
placeholders), `_match_at` round-trip verification (`_verifies` :105),
two-witness + strictly-positive-saving admission priced against the live
table (`mine` :116-154), content-addressed names (`m_<sha12>` :100),
registry `macros` table storage, and `gc_macros` retirement (:158 — ⚠H27 is
resolved by the tree). What it does NOT have: the H2/H3 candidate filters,
choice-force windows, and — the core of S1 — **sequence search** (the
scheduler admits greedily, one max-marginal-saving macro per iteration via
`_recurrence_moves` `loop.py:282` / `_dispatch_recurrence` :456, which also
skips the explicit `macro_admission_decision` gate call). The draft's
`buildloop/macro_mine.py` and `specs/macros.json` are **dead** — they would
duplicate live machinery under second names (⚠H48).

- **S1.1 Search skeleton** (`planner/search.py`, unchanged from the draft,
  Z-A): `beam_search(initial, expand, score, *, beam_width, max_depth)`,
  deterministic, ties by canonical JSON, returns best state **ever visited**
  (⚠H19 — both DL objectives are non-monotone in admissions).
- **S1.2 Miner filters** — a patch to `recurrence.py`, not a new module:
  - ⚠H3 (verified: the live gate admits the pure wildcard `["$p0","$p1"]`
    on an all-distinct corpus, Δ = −113.0, because `dl_invocation`
    (`mdl_macros.py:62`) prices args size-blind): reject any candidate with
    a bare-placeholder body statement; require ≥ 60% concrete nodes per
    body template.
  - ⚠H2: widen `_demand_windows`'s demand-only restriction to **uniform
    (force, quote)** windows — required both for honesty (mixed windows
    "compress" but are unrealizable as legal invocations,
    `reading.py:183-206`, choice-must-quote-nothing :329) and for S3
    part_a's choice-tail idiom, which is unmineable under demand-only
    windows.
- **S1.3 Admission-sequence search** — the **RecurrenceMiss handler
  upgrade**: `_dispatch_recurrence` gains a searched mode (flag-gated;
  default preserves today's greedy, regression-pinned). State =
  (table-so-far, sequence); expand = candidates from
  `recurrence.mine(readings, table_so_far)` that pass the **explicitly
  restored** `macro_admission_decision` gate call (the current dispatcher
  trusts `mine`'s inline check, `loop.py:456-463` — the gate is the arbiter,
  Z1); score = `corpus_dl(readings, table)["total"]`; winner admitted step
  by step via `registry.macro_add`. ⚠H21 dissolves: the searched table's
  home is the existing `macros` table; the accessor is
  `registry.macro_table()` (`library/__init__.py:522`) / the frozen
  `snap.macro_table`.
- **S1.4 Teeth** (`demos/demo_macro_search.py`, `REQUIRES_LLM = False`):
  - *part_a*: the greedy baseline is now **the live scheduler behavior**
    (one mine-ranked admission per iteration) — measured against the
    searched sequence on the seeded corpus; searched ≤ greedy on every
    tested arrival order (sorted, reversed, N rotations, ⚠H23); the CSV
    records whether strict divergence occurred (⚠H24 — an honest tie on the
    natural corpus is a finding).
  - *part_b (the trap — still valid)*: the planted corpus where greedy
    admission of A blocks the strictly better {B, C}. The sweep's executed
    numbers (none = 78.0, greedy/{A} = 55.0, searched/{B,C} = 35.0)
    **still reproduce** — every priced function is byte-identical on this
    tree. Residual-heterogeneity proviso (⚠H25) and the H3-filters
    prerequisite stand.
  - *part_c*: nothing admitted on the incompressible corpus (true only
    with H3 filters in place).
- **S1.5 Measurement**: `results/macro_search.csv` — columns `corpus,
  strategy ∈ {none, greedy, search}, macros_admitted, corpus_dl_total,
  mean_statements, strict_divergence` (⚠H26).
- **S1.6 Retirement widening**: `gc_macros` currently retires only
  `uses < 2` victims; widen to *any* macro whose ablation strictly reduces
  total DL (keep the uses<2 fast path) — closing the stale-vocabulary
  shadowing hazard the greedy-by-past-output trap creates.
- **S1.7 Ledger seam (⚠H49, verified)**: `dl._ledger_total`
  (`dl.py:265-286`) charges **no macro-definition cost** — a macro
  admission is free in `ledger_dl` while `mine` gates it on `corpus_dl`
  (which charges `dl_macro`), so realized deltas systematically beat
  expected by exactly `dl_macro(candidate)`. S1 adds the
  `sum(dl_macro(m) for m in snap.macro_table.values())` term to
  `_ledger_total` (one-line dl.py edit, owned for that line), making the
  search objective and the ledger agree.
- **Done when:** demo parts a–c green; greedy-default regression green
  (searched mode off ⇒ byte-identical scheduler decisions on recorded
  fixtures); CSV committed; TRUST amendment (H58 wording) + README Zone-3
  section as the phase's final serialized commit.

### S2 — Lookahead steering (re-seamed; sweep-measured on this tree)

The seam survives: kind-selection (scheduler) and group-selection
(`pick_group`) are separate stages, and S2 only ever claimed the second.
`pick_group` at `loop.py:120-140` (comparators at :128 and :140) gains an
additive `"lookahead"` policy; `milestones.py:81`'s tuple and `cgb.py:511`'s
`--policy` choices gain the string (⚠H28, both owned for those lines only).

- **S2.1** `planner/lookahead.py`:
  `rollout_value(generators, backlog, group, depth) -> float`, pure over
  inputs read once from the iteration's frozen state (house rule 13 is now
  structural — `dl.LedgerSnapshot` + `snapshot_hash`, `dl.py:123-152`).
  Pinned (⚠H29 revised, ⚠H50/H51/H54/H57):
  - **Coverage rule = `planner.plan_for_features(gens, language, atoms,
    target_language="python-codec") is None`** — NOT `mdl.chain_length_for`.
    H29 is inverted on this tree: `plan_for_features` accepts unregistered
    hypotheticals natively (defaults tier/hash, `planner/__init__.py:182-199`)
    and is the declared single chain-cost source; the mdl mirror is
    verified divergent (blind to `kind=="pass"` — counts 185 covered where
    the planner counts 0 — and to 3-link chains).
  - Hypothetical entry = the ksy branch of `candidate_entry_from_spec`
    (`admission.py:37-45`) **plus `"authored_bytes": 0` in
    `emit_entrypoint`** (⚠H54: `admission.admit` stamps that field at
    :128; omitting it underprices the eventual real entry by ~0.3
    DL/generator — verified 325.6 vs 330.4 over a 15-admission replay).
    `sorted(atoms)`. **ksy groups only; abnf AND the new `json-subset`
    branch score +∞** (⚠H57: both need an LLM-authored payload).
  - Value = best `dl._ledger_total(dl._with(snap, hyp))["ledger_dl"]` ever
    visited within `depth` admissions (Z2 — the live currency), searched
    with Z-A `beam_search`; the demo *also prints* the legacy `total_dl`
    series for continuity with recorded metrics, labeled as legacy.
- **S2.2** In `pick_group`: `min(groups, key=lambda g:
  (rollout_value(...), "".join(g["missing"])))` (⚠H30 — the existing
  comparators are `max`; lower-cost-wins needs `min`).
- **S2.3 Teeth** (`demos/demo_lookahead.py`, `REQUIRES_LLM = False`):
  - *part_a (planted)*: closure picks a dominated miss, depth-2 lookahead
    picks the enabling one; strict inequality on the replayed final cost.
  - *part_b (real backlog)* — ⚠H52 (verified by execution): the previous
    sweep's numbers (10-vs-11 admissions, 316.6-vs-318.8) **do not
    reproduce on this tree**; the re-run measured closure = 15 admissions /
    323.8–325.6 and frequency = 14 / 320.2–324.0 under a pinned recipe, and
    the recipe itself was underdetermined by the old text. Therefore: the
    demo pins the replay recipe **in code** (min-remainder grouping,
    atoms_union hypothetical with `authored_bytes: 0`, subsumption
    retirement mirrored, coverage via `plan_for_features`), records fresh
    numbers in the capture, and **asserts only the relational teeth**:
    lookahead admissions ≤ closure admissions, and at the equal smaller
    budget lookahead's `(covered, −cost)` strictly dominates. No absolute
    constants in asserts.
- **S2.4 Measurement** — ⚠H53 (new, verified): the live M5 path is
  currently **broken on this tree** — `run_experiment.run_config` creates a
  fresh Registry and never populates the demand ledger, so `score_moves`
  finds no moves and `run_iteration` returns `converged` on iteration 1 for
  every policy. WP-G adds a minimal demand-seed to `run_config` (one
  exogenous `spec-file` row per backlog entry, mirroring `_ledger_sync`'s
  shape) — owned for those lines only, with an integrator escalation note
  since the draft declared that file unowned. Then: third curve via
  `run_config` + `metrics/plots.py:reach_vs_cost` over all CSVs, generated
  under `artifacts/`, copies committed to `results/` (⚠H32: nothing
  regenerates `reach_vs_cost_all.png` — produce it by calling the plotter
  with every curve). ⚠H33 survives as a recorded artifact
  (`results/metrics_closure_corpus.csv`: seed + 2 admissions → reach 1.0);
  the live rerun is contingent on the H53 fix, last and skippable with an
  honest note.
- **Done when:** part_a strict; part_b relational teeth green with fresh
  pinned numbers committed; `frequency`/`closure` picks and
  scheduler-decision logs unchanged on recorded fixtures; the H53 seed
  covered by a test proving a fresh-DB metrics run admits > 0 under
  `closure`.

### S3 — Choice-space search (min-DL design that entails the demands)

Unchanged in substance from the post-sweep revision; re-anchored details:

- **S3.1** `planner/choices.py`: vary ONLY choice-force statements
  (lifecycle/transition/input/choice-`action`, `reading.py:116-128`);
  template family `{[open,closed], [open,active,closed]}`,
  forward/self edges; demands/presuppositions copied byte-identically
  (test-pinned). Gate (b) = the **order-entailment check** in
  `compile_reading` (`reading_compile.py:100-121`, `CompileError` at :116)
  — refused variants counted then discarded (⚠H35). Non-vacuity filter
  (⚠H36): discard variants with `entailed_scenarios(model, reading) == []`.
- **S3.2** Scoring: compile; replay entailed scenarios through the
  reference interpreter — composed (⚠H12) from `service_gen.emit_service` +
  `build_scenario_reference_harness` (`service_gen.py:923`) +
  `HypothesisBackend.check_intent_reference` (`kernel/backends.py:243`);
  score = `mdl_macros.dl_reading(reading, table)` with
  **`table = registry.macro_table()` / `snap.macro_table`** (⚠H48 — not a
  file accessor) + the size proxy `len(common.canonical_json(spec))/64.0`;
  tie-break by compile-hash (⚠H37 stated honestly: transition targets are
  DL-invariant, the argmin is a tie class). When dream entries exist, the
  DL score uses the exogenous-origin sub-corpus (⚠H6/H55). Providing Z-F.
- **S3.3 Teeth**: *part_a* — the ⚠H4 respec stands: the idiom is a
  **structural choice-tail macro**; note the dependency: it is mineable
  only after S1.2 widens windows to uniform-(force, quote) — until then it
  is hand-planted. Flat and macro-aware argmins differ; both winners
  certify. *part_b* — a planted `order` demand (12_venue_vague yields
  none); the globally minimal design violating it is refused; best
  admissible design returned.
- **Done when:** both parts green; byte-compare test pins
  demand/presupposition immutability; empty-scenario variants discarded.

### S4 — Speculative synthesis executor + divergence ledger + fill-path fix

Premise (⚠H8, unchanged, still capture-backed): a measured trade, not a
promised saving. Re-anchored details:

- **S4.0 Fill-path fix (⚠H46)**: repair `_dispatch_request`
  (`loop.py:446-452`): read the request *text* from `payload_ref`, call
  `synthesize_semantic` (the path that returns a reading), persist via
  `registry.reading_add` with the composed cert id. This makes the live
  loop actually grow the corpus recurrence mines — the single highest-value
  small fix in Zone 3.
- **S4.1** `speculate.fan_out(request, k, *, model)`: k LLM-authored
  Readings per round (prompt-variation diversity; `llm.call_llm` has no
  temperature knob, `llm.py:41`); `--spend` cap; k=1 preserves today's
  behavior. ⚠H40 revised: the k=1 regression monkeypatches `call_llm` with
  a canned transcript and asserts identical (prompt, cache_key, event)
  sequences — noting `certify_reading`'s stage list now includes **stage
  3.5 `monitor-cert`** for temporal readings and the new
  `macro_table`/`on_certified` kwargs (⚠H56): pin the tuple sequence
  against the *current* stage labels, not the draft's four.
- **S4.2** Pre-gates, cheapest first (⚠H12/H41): (1) `reading-gate` =
  `parse_reading`; (2) quick-SMT =
  `SmtBackend().run_z3(demands_smt(r), expect="sat")` under
  `common.SMT_LOCK`; (3) compile; (4) entailed-scenario replay on the
  reference only — **rank-only, never reject** (⚠H10, all three
  mitigations mandatory: rank-only stage 4; deterministic every-Nth loser
  audit ON by default; run-record selection claim + TRUST 3.4 caveat).
  Score = (stage reached, then the Z-F scorer — flat fallback until WP-L).
- **S4.3** Cache warming: post-compile only, main thread, through the real
  `certify_service`/`_build_jobs` path (`run/service.py:54, 90-160`).
  Loser claim scoped: no *composed* certificate for losers; warmed
  sub-certificates are real, content-addressed, inventoried in the ledger
  (`cache_put` now at `library/__init__.py:584` — versioned-JSON envelope).
- **S4.4** Divergence ledger: events-table only (⚠H38 — the schema gained
  the four Combined-Loop tables, but Zone 3 still touches none of it);
  payload `{stage, direction, candidate_sha, request_sha}`.
- **S4.5 Teeth** (`demos/demo_speculate.py`, LLM-free, hand-planted): the
  inverted-verb-effect plant caught at `stage='protocol'`
  (`results/reading_demo.txt:30`); ⚠H42 first verify stage-4 replay misses
  it (else switch to a temporal-stranding plant). Assert: divergence event
  logged; no composed certificate exists.
- **Bench** (`bench/bench_speculate.py`): k ∈ {1,3,5}, ≥3 requests; ⚠H43 —
  LLM-requiring, 2–3M-token worst case, last and skippable with honest
  note. Metrics: `llm_calls_to_certify` (expected flat-to-worse),
  `rounds_to_certify`, wall-clock, per-stage loser attribution.
- **Done when:** k=1 regression green; S4.0 fix covered by a test (a
  request-miss dispatch on a fresh DB yields a readings row); teeth green
  with the H42 check; ledger queryable; bench captured or honestly skipped.

### S5 — Dream corpus under witness discipline (origin-based)

- **S5.1** `dream.py`: LLM paraphrases/domain-variants → Readings via the
  S4 executor → files in `specs/readings/dream/`, seeded with
  **system-origin demand rows** (⚠H55: provenance is the ledger's `origin`
  column, not the path; H44 enforcement lives in the seed step — a dream
  seeded as real with no committed request byte-match is a hard error).
- **S5.2** Witness discipline — gate AND objectives (⚠H6), origin-based:
  `witness_filter=lambda e: e.origin == "exogenous"`. ⚠Z-E scope widened
  (the anchor sweep confirmed the gate alone would not govern the
  scheduler's mining path): the filter threads into
  `macro_admission_decision` **and** `recurrence.mine` **and**
  `gc_macros` (additive `witness_filter=None` params; `recurrence.py`
  joins the ownership matrix for S5). Witnesses count per **distinct real
  request** — free by construction, the readings table is keyed by
  `demand_id` (⚠H7 half-dissolves; the S3 self-witness residue remains:
  S3-authored variants have no demand row, so they cannot witness without
  deliberately minting one — log `self-witness` if any path ever does).
  S1.3's search score and S3.2's score compute over the exogenous-origin
  sub-corpus whenever system-origin readings exist.
- **S5.3 Teeth** (`demos/demo_dream.py`): (i) a pattern in 3 dream readings and 0
  real is mined but REFUSED; hand-added to 2 real entries it flips to
  admitted; (ii) perturbing the dream corpus leaves the admitted sequence
  unchanged (objective-side rule); (iii) seeding a dream file as real with
  no committed request byte-match hard-errors at `ledger seed-readings`.
- **Done when:** all three teeth green; `tests/test_witness_filter.py`
  proves default-`None` byte-identical behavior in all three functions.

## Parallel execution plan (maximum-width schedule)

One WP = one agent = one worktree = one exclusive file set; freezes let
consumers code against signatures. ⚠ `buildloop/loop.py` now has three
writers in **disjoint functions** — G (`pick_group`), I
(`_dispatch_request`), J (`_dispatch_recurrence`): ownership is
function-level; the integrator serializes their merges.

### Wave 0 — nine packages, no cross-dependencies

| WP | scope | exclusive files |
|---|---|---|
| **A** bridge | S0.2: `reading_corpus.py` + `cgb.py ledger seed-readings` lines + 3 demo exports | `buildloop/reading_corpus.py`, `tests/test_reading_corpus.py`, `cgb.py` (seed-readings lines), 3 reading files |
| **B** readings-bounds | requests 01,02,04,05,06,14,15,18 | those 8 files under `specs/readings/` |
| **C** readings-temporal | requests 03,09,17 | those 3 files |
| **D** search-skeleton | S1.1 (Z-A) | `planner/search.py`, `tests/test_search.py` |
| **E** miner-filters | S1.2 patch: H3 + H2 window widening | `buildloop/recurrence.py` (`_demand_windows`/`mine` filters only), `tests/test_macro_mine.py` |
| **F** fixtures | trap + incompressible corpora (H11/H25 recipe, numbers still valid) | `tests/fixtures_macro_corpora.py` |
| **G** lookahead | all of S2 incl. the H53 demand-seed fix | `planner/lookahead.py`, `loop.py` (`pick_group`), `milestones.py` (:81 tuple), `cgb.py` (:511 choices), `metrics/run_experiment.py` (`run_config` seed lines), `demos/demo_lookahead.py`, `tests/test_lookahead.py` |
| **H** choices-core | S3 minus part_a; provides Z-F | `planner/choices.py`, `demos/demo_choice_search.py`, `tests/test_choice_search.py` |
| **I** speculate-core | S4 minus bench, minus real scorer; incl. **S4.0 fill-path fix** | `buildloop/speculate.py`, `service_loop.py` (flag), `loop.py` (`_dispatch_request`), `demos/demo_speculate.py`, `tests/test_speculate.py` |

`cgb.py` has two writers (A: seed-readings, G: policy choices) — disjoint
lines, integrator serializes. Merge order: A,B,C → D,E,F → G,H,I.

### Wave 1 — three packages, file-disjoint

| WP | scope | needs |
|---|---|---|
| **J** searched-recurrence | S1.3 (searched `_dispatch_recurrence`), S1.4/S1.5 demo+CSV, S1.6 gc widening, S1.7 `_ledger_total` macro-cost term | A+B+C, D, E, F |
| **K** witness | S5.2–S5.3 with hand-planted dreams (no LLM): Z-E threading into all three functions | A, E |
| **L** scorer-swap | Z-F seam swap in speculate.py + H42 verification | H, I |

### Wave 2 — serialized tail

| WP | scope | needs |
|---|---|---|
| **M** choices-integration | S3 part_a against the live `macro_table()` | J, L |
| **N** dream-live | S5.1 (LLM; skippable) | I, K |
| **O** docs+captures | ONE commit: README Zone-3, TRUST (H58 + H10 caveat), captures; then both benches (skippable) | all |

Critical path: {A, D, E, F} → J → M → O. Peak width 9.

Swarm rules: exclusive file (or function) lists are review-blocking;
merge-owned files only in WP-O; integrator owns nothing and runs the fast
regression at every merge; a builder that finds the spec wrong **stops and
escalates** — never improvises across a freeze.

## Interface freezes

- **Z-A** `beam_search(initial, expand, score, *, beam_width, max_depth)`;
  pure, ties by canonical JSON, best-ever-visited (H19); no other exports.
- **Z-B** corpus file `{request, reading:{service, statements}}`; loader
  yields `CorpusEntry(request, statements, source)`; `source` derived from
  `demand.origin` at seed time (exogenous=real, system=dream); statements
  per ROADMAP freeze #3.
- **Z-C (revised, ⚠H48)** macro store = the registry `macros` table;
  accessor `registry.macro_table()`; names `m_<sha12>` (the landed
  convention — the draft's `mined_<sha8>` is withdrawn); retirement = the
  `retired` column + `macro-retired` events. No file store.
- **Z-D** events: `speculation-divergence {stage, direction, candidate_sha,
  request_sha}`; `self-witness {macro, reading_sha}`; via
  `registry.log_event` (:319), listed by `cgb.py events` (:459).
- **Z-E (scope widened)** additive `witness_filter=None` on
  `macro_admission_decision` AND `recurrence.mine` AND `gc_macros`; when
  set, restricts the readings used in every `corpus_dl` computation inside
  each.
- **Z-F** `score_reading(reading, macro_table) -> float`; with `{}` equals
  the flat score; provided by WP-H, consumed by WP-I via flat fallback
  until WP-L.

## File-ownership matrix (W = writes, N = new, r = reads)

| file | S0 | S1 | S2 | S3 | S4 | S5 |
|---|---|---|---|---|---|---|
| `specs/readings/` | **N** | r | | r | r | W |
| `buildloop/reading_corpus.py` (single-writer) | **N** | r | | r | r | r |
| `planner/search.py` | | **N** | r | r | | |
| `buildloop/recurrence.py` | | W (filters, S1.2) | | | | W (Z-E params) — serialized after S1 |
| `planner/lookahead.py` | | | **N** | | | |
| `buildloop/loop.py` — function-level | | W `_dispatch_recurrence` | W `pick_group` | | W `_dispatch_request` | |
| `buildloop/dl.py` (`_ledger_total` macro term only) | | W | | | | |
| `milestones.py` (:81 tuple only) | | | W | | | |
| `cgb.py` (seed-readings / :511 choices) | W | | W | | | |
| `metrics/run_experiment.py` (`run_config` seed only) | | | W | | | |
| `planner/choices.py` | | | | **N** | r | |
| `buildloop/speculate.py` | | | | | **N** | r |
| `buildloop/service_loop.py` (additive flag) | | | | | W | |
| `buildloop/mdl_macros.py` (Z-E only) | | | | | | W |
| `buildloop/dream.py` | | | | | | **N** |
| `metrics/` (serialized S2 → S4) | | | W | | W | |
| demos/tests/results (each phase's own) | N | N | N | N | N | N |
| README (merge-owned) | | W | W | W | W | W |
| TRUST.md (merge-owned) | | W | | | W | |
| `kernel/*`, `generators/*`, `run/*`, `library/__init__.py`, `run_regression.py`, `buildloop/mdl.py` (frozen legacy), `buildloop/admission.py`, `planner/__init__.py` | r | r | r | r | r | r |

## Builder briefing addendum

1. Z1–Z3 are review-blocking. 2. Determinism everywhere (no `random`, no
clocks, canonical JSON). 3. Repo demo conventions + committed captures.
4. `run_regression.py --fast` green before every push; never edit
`FAST_DEMOS`. 5. **This addendum overrides ROADMAP briefing item 4**: push
ONLY to the branch your task designates. 6. New (re-anchor): treat
`buildloop/dl.py` and `planner/__init__.py` as frozen interfaces — consume
`plan_for_features`, `dl._with`, `_ledger_total`, `LedgerSnapshot`; never
re-implement a coverage or pricing mirror (`dl.py:11-16` is the house rule).

## Hazards ledger

H1–H45: the five-lens sweep of the draft (see git history for the full
table; superseded entries noted below). Re-anchor sweep (three agents,
tree @ `abad328`):

| # | finding | evidence | folded into |
|---|---|---|---|
| H46 | `readings` table exists but is empty with a **broken live fill path** (path-vs-text + never-returned key) | `loop.py:446-452`, `service_loop.py:296-301` | S0 premise, S4.0 |
| H47 | `recurrence.py` = a landed greedy S1.2 (LGG mining, 2-witness, gc retirement) — S1 re-scoped to filters + sequence search | `recurrence.py:62,105,116,158` | S1 |
| H48 | `specs/macros.json` + `load_macros()` would duplicate the live `macros` table — **dropped**; accessor = `registry.macro_table()` | `library/__init__.py:94-100,522` | S1.3, Z-C, S3.2 |
| H49 | `_ledger_total` charges no macro-definition cost — realized beats expected by exactly `dl_macro` | `dl.py:265-286` | S1.7 |
| H50 | `mdl.chain_length_for` no longer mirrors the planner (kind=="pass": 185-vs-0 covered; 3-link: None-vs-3) — verified divergent | probe runs; `planner/__init__.py:122-166` | Z2, S2.1 |
| H51 | H29 inverted: `plan_for_features` prices hypotheticals natively; the draft's plain-dict mirror is now the *forbidden* pattern | `planner/__init__.py:182-199`, `dl.py:11-13` | S2.1 |
| H52 | old S2 numbers (10-vs-11 / 316.6-vs-318.8) do **not** reproduce (measured: closure 15 / 323.8–325.6, frequency 14 / 320.2–324.0); recipe was underdetermined | replay runs on this tree | S2.3: recipe pinned in code, relational asserts only |
| H53 | the live M5 path is broken: `run_config` never seeds the demand ledger → every policy "converges" at iteration 1 | verified fresh-Registry run; `cgb.py:380` sole writer | S2.4, WP-G |
| H54 | persisted entries carry `emit_entrypoint.authored_bytes` (stamped at `admission.py:128`) — hypotheticals must include it or underprice by ~0.3 DL | 15-admission replay: 325.6 vs 330.4 | S2.1 |
| H55 | `demand.origin ∈ {exogenous, system}` supersedes path-inferred `source`; H44 enforcement moves to the seed step | `library/__init__.py:75`, `cgb.py:399-402` | S0.2, S5, Z-B |
| H56 | `certify_reading` gained `macro_table`/`on_certified`; pipeline gained stage 3.5 `monitor-cert` — H40/H41 targets updated | `run/semantic.py:70-72,~113-144` | S4.1/S4.2 |
| H57 | `candidate_entry_from_spec` gained a `json-subset` branch — also excluded from hypotheticals | `admission.py:46-60` | S2.1 |
| H58 | the W5.2 rung supersedes H1/H5's wording: per-use `translation-cert(reference-lowering)` against the retained original; table hash in cache identity | `kernel/__init__.py:321-348`, `tests/test_rung.py` | trust posture, S1 TRUST amendment |
| — | resolved by the tree: H21 (table home), H27 (retirement exists), H29 (inverted → H51); line-drift-only updates: `log_event`:319, `events`:324, `cmd_events`:459, choices:511, `corpus_inputs`:347, `cache_put`:584, `certs.py created_at`:70, `run_z3`:487, `build_scenario_reference_harness`:923, `pick_group`:120/:140, `MAX_ROUNDS`:18 | anchor sweep | in place |

## Acceptance, restated (re-anchored)

1. Macro vocabulary growth is **search-driven against the live greedy
   opponent**: never worse than the scheduler's greedy behavior on the
   seeded corpus across tested orders; strictly better on the trap corpus
   (numbers still valid: 55.0 → 35.0); nothing admitted on the
   incompressible corpus; wildcard and mixed-force candidates structurally
   excluded; expected and realized `ledger_dl` deltas agree (H49 closed).
2. Coverage steering is lookahead-driven in the **live currency**
   (`ledger_dl` via `plan_for_features`): strictly better on the planted
   backlog; relationally better (≤ admissions, dominating at equal budget)
   on the real backlog under a recipe pinned in code; existing policies
   and scheduler decisions unchanged; the M5 metrics path works again
   (H53).
3. Design choice is an optimization with a stated objective; the
   entailment gate overrides Occam; admitted vocabulary reshapes the chosen
   design.
4. Synthesis spends K-wide, certifies only through the unchanged kernel,
   reports the measured trade, never rejects by reference-replay ranking,
   logs every miss — and the live request path actually persists readings
   (S4.0).
5. Dreams propose; only exogenous-origin readings witness — in the gate and
   in every objective, enforced at seed time by the ledger's own
   provenance.
6. Zero new kernel contracts; kernel/compiler/reference/registry-schema
   untouched; certificates carry the identical `cert_id`/`subject_hash`/
   `contract_hash`/channels the non-speculative path would produce
   (`created_at` excluded, H9).
