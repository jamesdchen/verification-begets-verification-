# SPECULATION.md — Zone 3: the speculative planner

README.md says what the system is. TRUST.md says what is trusted. ROADMAP.md
says what gets built toward the two-zone economy. This document specifies a
third zone: **the speculative planner** — the layer that decides what the
expensive machinery spends itself on, by consulting the system's exact
description-length accounting *before* paying for LLM calls and kernel
invocations rather than after.

It is written to be executed by a swarm of builder agents **without access to
the conversation that produced it**. It carries the interface freezes, the
file-ownership rules, the teeth criteria per phase, and a hazards section
(marked ⚠) populated by an adversarial review sweep of this plan against the
actual codebase.

## What the system does (behavioral description)

Today every scarce resource is spent reactively:

- the build loop (`buildloop/loop.py:run_iteration`) picks one coverage-miss
  group by `frequency` or one-step `closure`, asks the LLM for one candidate,
  and submits it to the full admission stack — up to `MAX_ROUNDS = 5` serial
  round-trips;
- the synthesis loops (`buildloop/service_loop.py:synthesize_semantic` /
  `synthesize_service`) do the same at the service rung: one Reading or
  meta-spec per round, full certification stack per round;
- macro admission (`buildloop/mdl_macros.py:macro_admission_decision`) is
  *reactive*: it evaluates one already-proposed macro against the corpus,
  greedily, in arrival order.

The speculative planner replaces "spend, then observe the price" with
"simulate the price, then spend". Concretely, after all phases land:

1. **Given a corpus of Readings**, the planner *mines* candidate macros
   mechanically (anti-unification over statement windows — no LLM) and
   *searches* over admission sequences, scoring each future with the exact
   `corpus_dl` function, then admits the best sequence — each step still
   passing the unchanged per-macro MDL gate. Compression of the Reading
   vocabulary stops being hostage to what happens to get proposed, in the
   order it happens to arrive.
2. **Given the codec backlog**, the planner rolls out multi-step futures —
   "if a generator with atoms X were admitted, which chains open, which
   misses become one-hop, what is `total_dl` after two more admissions?" —
   using the pure functions in `buildloop/mdl.py`, and steers the build loop
   toward the miss with the best *downstream* DL reduction, not the best
   immediate one.
3. **Given a Reading whose `choice` statements leave design freedom**, the
   planner enumerates alternative choices consistent with the demands,
   compiles each through the deterministic compiler, replays entailed
   scenarios through the reference interpreter, and selects the minimum-DL
   design that entails every demand — Occam applied to the pragmatic residue.
4. **Given a request**, the synthesis loop fans out K candidate Readings,
   runs only the cheap deterministic pre-gates on all of them (spec-shape
   validation, groundedness, quick-SMT consistency, reference-interpreter
   scenario replay), and submits only the best-scoring survivor to the
   expensive dual-checker stack — warming the content-addressed certificate
   cache with sub-obligations shared across candidates while it decides.
5. **Between requests**, a dream loop generates synthetic requests
   (paraphrases and domain variants of `specs/requests/`), synthesizes
   Readings for them offline, and feeds the *mining* stage — under a strict
   witness discipline: dreamed readings may propose macros; only real
   readings witness them.

## Trust posture (read this before writing any code)

The planner is **untrusted-by-construction, exactly like the LLM**. Every
house rule of ROADMAP.md binds here; three planner-specific rules are added:

- **Z1 — proposals only.** No planner output is ever a certificate, a
  verdict, or a cache entry that a verdict reads. The planner reorders and
  prunes what gets *submitted* to the kernel and the admission gates; the
  gates themselves are not modified (S1 explicitly does NOT change
  `macro_admission_decision`'s semantics — it searches over admission
  *sequences*, each step of which must still pass the unchanged gate).
- **Z2 — exact objectives first.** Phases S1–S3 may only score with the
  exact pure functions (`mdl.total_dl`, `mdl.chain_length_for`,
  `mdl_macros.corpus_dl`, deterministic compile + reference replay). Learned
  or heuristic scores are confined to S4/S5 and must ship with the
  divergence ledger in the same commit.
- **Z3 — measured fidelity.** Any component that *predicts* a kernel or gate
  verdict (S4 pre-gates) logs prediction-vs-actual as a first-class
  `speculation-divergence` event via the existing `registry.log_event`
  mechanism (same shape as `dual-checker-disagreement`,
  cf. `cgb.py events`). A rising divergence rate is a defect, not a tuning
  knob.

No phase in this document adds a kernel contract. House rule 6 (five
touchpoints) never fires. `kernel/__init__.py` and `kernel/backends.py` are
read-only for all of Zone 3.

## Phases

Dependency graph:

```
S0 (corpus provisioning) ──▶ S1 ──▶ S3 ──▶ S4 ──▶ S5
S2 ─ parallel with S1/S3 after S0 (disjoint files, disjoint DL accounting)
```

### S0 — Reading-corpus provisioning (small; land alone, first)

⚠ **There is no persisted Reading corpus.** `demo_macros.py` hand-writes its
3-reading corpus inline (`demo_macros.py:108`); `specs/requests/` holds 20 raw
request texts, not Readings. Macro mining is corpus-starved before it starts.

- **S0.1** New directory `specs/readings/`: one JSON file per corpus entry,
  `{request: str, reading: {service, statements: [...]}}`. Bootstrap with
  (a) the three `demo_macros.py` corpus entries, exported verbatim, and
  (b) hand-written Readings for at least 10 of the 20 `specs/requests/`
  texts — every one passing `generators.reading.parse_reading` + the
  groundedness gate (quotes verbatim from the request) with **no LLM**
  involved. Vague requests (`12_venue_vague.txt`, `13_subscription_vague.txt`,
  `20_clinic_combo_vague.txt`) may be skipped — hand-writing a Reading for a
  vague request bakes in choices this document's S3 exists to search.
- **S0.2** `buildloop/corpus.py`: `load_readings(dir) -> list` returning
  objects with `.statements` (the shape `mdl_macros._statements` already
  accepts) plus `.source ∈ {real, dream}` provenance (default `real`;
  `dream` unused until S5). Loader validates every entry through
  `parse_reading` at load time — a corpus entry that no longer parses is a
  hard error, not a skip.
- **Done when:** `python3 -c "from buildloop import corpus; ..."` loads ≥ 13
  readings; a regression test asserts the corpus parses and the groundedness
  gate passes on every entry; `run_regression.py --fast` stays < 90 s.

### S1 — Macro mining + admission-sequence search (the core)

New files only: `planner/search.py`, `buildloop/macro_mine.py`,
`demo_macro_search.py`, `tests/test_macro_search.py`,
`results/macro_search.csv`.

- **S1.1 Search skeleton** (`planner/search.py`). One generic beam search:
  `beam_search(initial, expand, score, *, beam_width, max_depth) -> best`
  where `expand(state) -> [state]`, `score(state) -> float` (lower better),
  fully deterministic (ties broken by canonical-JSON of the state — mirror
  the planner's hash tie-break discipline, `planner/__init__.py:10`). No
  randomness, no clocks. This module is shared by S1.3 and S2 and frozen
  after S1 (interface-freeze Z-A below).
- **S1.2 Anti-unification miner** (`buildloop/macro_mine.py`).
  `mine(readings, *, max_body=3, max_params=4) -> [candidate macro dicts]`.
  For every pair of same-length statement windows (length 1..max_body)
  across the corpus, compute the least-general anti-unifier of their lf
  sequences: structurally equal nodes stay concrete; mismatched positions
  become `"$p<i>"` placeholders (consistent: the same concrete pair maps to
  the same placeholder). Reject candidates whose placeholder count exceeds
  `max_params` or whose body is a single bare placeholder. Dedup by
  canonical JSON. This is the dual of `mdl_macros._unify`
  (`buildloop/mdl_macros.py:75`) and must round-trip with it: a regression
  test asserts that for every mined candidate, `_match_at` matches it back
  against BOTH source windows with full bindings.
- **S1.3 Admission-sequence search.** State = (macro table so far, admission
  sequence); expand = admit any mined candidate that **passes the unchanged
  `macro_admission_decision` against the table-so-far**; score = final
  `corpus_dl(readings, table)["total"]`. Beam width 8, depth ≤ 5 (defaults;
  CLI-overridable). Output: the best admission sequence, executed for real
  by calling the gate step by step. The gate is the arbiter at every step
  (planner rule Z1); the search only chooses *which* admissible sequence to
  take. A macro admitted here still requires its `macro-expansion-cert`
  (existing kernel contract, `demo_macros.py` part B) on every reading that
  uses it — certification is per-use and unchanged.
- **S1.4 Teeth** (`demo_macro_search.py`, capture to
  `results/macro_search_demo.txt`):
  - *part_a*: greedy arrival-order baseline vs searched sequence on the S0
    corpus; searched final DL ≤ greedy for every arrival permutation tested
    (sample the permutations deterministically by sorting candidate names).
  - *part_b (the trap)*: a planted corpus where greedy admission of macro A
    (arrives first, passes the gate) makes the strictly-better pair {B, C}
    inadmissible (each fails `dl_after < dl_before` once A occupies their
    windows under the longest-body-first rewrite,
    `buildloop/mdl_macros.py:127`), while the searched sequence admits
    {B, C} and lands a strictly lower corpus DL. Assert the searched DL is
    strictly lower — this is the demo that the local optimum is real.
  - *part_c (honesty)*: on a corpus with nothing to compress (all-distinct
    statements), mining returns candidates but search admits **nothing**
    (every sequence scores worse than empty) — the machinery declines to
    mint vocabulary when it does not pay.
- **S1.5 Measurement**: `results/macro_search.csv` — columns
  `corpus, strategy ∈ {none, greedy, search}, macros_admitted, total_dl,
  mean_statements`; rows for the S0 corpus and the part_b trap corpus.
- **Done when:** all demo parts pass; the round-trip regression test is
  green; CSV committed; README gains a short Zone-3/S1 subsection (docs are
  merge-owned — final serialized commit of the phase).

### S2 — Lookahead steering for the build loop (parallel with S1 after S0)

New files only: `planner/lookahead.py`, `tests/test_lookahead.py`,
`demo_lookahead.py`; one edit: `buildloop/loop.py:pick_group` gains policy
`"lookahead"` (additive — `frequency` and `closure` untouched).

- **S2.1** `planner/lookahead.py`:
  `rollout_value(registry_snapshot, backlog, group, depth) -> float`.
  A hypothetical admission for miss-group g is the candidate dict
  `{spec_grammar: {atoms: g.atoms_union, ...}, emit_entrypoint: <the
  emitter the group's language implies>, spec_language, output_language}` —
  constructible without any LLM because `mdl.generator_dl`
  (`buildloop/mdl.py:47`) prices exactly those declared fields. Value =
  best `total_dl` reachable within `depth` further hypothetical admissions
  (depth ≤ 3 default), searched with `planner/search.py`. Never mutates the
  registry: operates on plain lists of generator dicts.
- **S2.2** Steering: `pick_group(..., policy="lookahead")` ranks groups by
  `rollout_value` (lower final DL wins; tie-break lexicographic missing-atom
  string, as today at `buildloop/loop.py:133`).
- **S2.3 Teeth** (`demo_lookahead.py`): a planted backlog (constructed in the
  demo, not committed to `specs/backlog/`) where `closure` picks a dominated
  miss — resolving it covers 3 specs now but strands the rest behind two more
  admissions — while depth-2 lookahead picks the group whose resolution makes
  a single follow-up admission cover everything; assert final `total_dl`
  (lookahead) < final `total_dl` (closure) when both futures are replayed
  hypothetically.
- **S2.4 Measurement**: extend the M5 machinery
  (`metrics/run_experiment.py`) with the third policy curve; regenerate
  `results/reach_vs_cost_all.png` and CSVs. ⚠ Live M5 runs need the claude
  CLI (`buildloop/llm.py`); the *demo* must stay `REQUIRES_LLM = False` by
  replaying hypothetical admissions only. The live third-curve capture is
  the phase's last, LLM-requiring step — skippable in constrained
  environments with an honest note in the commit message, but the demo teeth
  are not skippable.
- **Done when:** demo green with the strict inequality; `pick_group` policy
  test green; no change to `frequency`/`closure` behavior (regression
  compares picks on the existing recorded backlogs).

### S3 — Choice-space search (min-DL design that entails the demands)

New files only: `planner/choices.py`, `demo_choice_search.py`,
`tests/test_choice_search.py`. Reads (never writes)
`generators/reading_compile.py`, `run/semantic.py`.

- **S3.1** `planner/choices.py`: `enumerate_choices(reading, *, budget) ->
  [reading]`. Vary ONLY statements with `force == "choice"`: lifecycle
  shapes (2–3 states from a fixed template family), transition targets, and
  optional auxiliary actions; demands and presuppositions are copied
  byte-identically. Every variant must (a) pass `parse_reading`, (b) pass
  the existing choice⊨demand entailment gate in the compiler — variants that
  fail (b) are *counted* (they are the search saying "that design would
  override the text") but discarded.
- **S3.2** Scoring: compile each surviving variant
  (`reading_compile.compile_reading`), replay its entailed scenarios through
  the reference interpreter (the `run/semantic.py` machinery), and score by
  macro-aware DL of the *reading* (`mdl_macros.dl_reading` with the current
  admitted table) plus the compiled spec's size proxy. Lowest wins;
  deterministic tie-break by compile-hash.
- **S3.3 Teeth** (`demo_choice_search.py`):
  - *part_a*: on a vague request (reuse `12_venue_vague.txt`), flat scoring
    (macro table empty) and macro-aware scoring pick different designs; the
    macro-aware winner uses the admitted `no_oversell`-style idiom; both
    certify.
  - *part_b*: a planted variant family where the *globally* minimum-DL
    design violates a demanded ordering — assert it is refused by the
    entailment gate and the search returns the best *admissible* design
    (Occam never overrides the text).
- **Done when:** both parts green; a test pins that enumerate_choices never
  mutates demand/presupposition statements (byte-compare).

### S4 — Speculative synthesis executor + divergence ledger

New file: `buildloop/speculate.py`; edits: `buildloop/service_loop.py`
(fan-out entry point, additive flag), `metrics/` (ledger columns);
`bench_speculate.py`.

- **S4.1** `speculate.fan_out(request, k, *, model) -> [candidate]`: k
  LLM-authored Readings per round (temperature via prompt variation — the
  candidate index seeds a "consider an alternative design" preamble, since
  `llm.py` is a headless CLI wrapper). Cost knob: `--spend` caps total LLM
  calls per request; default preserves today's budget (k=1 ⇒ byte-identical
  behavior to the current loop — regression-tested).
- **S4.2** Pre-gates, in order, cheapest first, all existing machinery:
  parse/validate → groundedness → quick-SMT demand-consistency
  (`with common.SMT_LOCK:`) → entailed-scenario replay on the *reference
  interpreter only*. Score = (stage reached, then S3's DL score). Winner
  goes to the full stack; losers are logged, never certified.
- **S4.3** Cache warming: while pre-gates run, submit the winner-so-far's
  per-tool and per-constraint obligations to the kernel in the existing
  channel-parallel path. Sound because certificates are content-addressed
  and per-artifact: a warmed cert for an artifact later discarded is wasted
  compute, never wasted trust. ⚠ Byte-identity rule (house rule 8) binds:
  warming must reuse the exact existing job-construction path
  (`run/service.py:_build_jobs`), never a reimplementation.
- **S4.4** Divergence ledger: for every candidate that passes ALL pre-gates
  and then fails the full stack, and every candidate rejected by a pre-gate
  whose full-stack verdict is later observed to pass (only measurable when
  `--audit-losers` runs losers through the full stack — off by default,
  on in the bench), log `speculation-divergence` with stage, direction, and
  hashes. `cgb.py events speculation-divergence` must list them.
- **S4.5 Teeth**: a planted Reading that satisfies every pre-gate but fails
  the dual-BMC stack (use the inverted-verb-effect misreading class from
  `demo_reading.py` — pre-gates cannot see it, the BMC adversary can);
  assert the divergence event is logged and no certificate exists for it.
- **Done when:** k=1 byte-identity regression green; teeth green; bench
  (`bench_speculate.py`, `bench_latency.py`-style) reports rounds-to-certify
  and LLM-calls-to-certify for k ∈ {1, 3, 5} on ≥ 3 requests from
  `specs/requests/`, captured to `results/speculate_bench.txt`.

### S5 — Dream corpus under witness discipline

New file: `buildloop/dream.py`; edits: `buildloop/corpus.py` (the `dream`
provenance tag becomes live), `buildloop/mdl_macros.py` gains an OPTIONAL
`witness_filter` parameter (default `None` = today's behavior, regression-
pinned byte-identical).

- **S5.1** `dream.py`: LLM paraphrases/domain-variants of `specs/requests/`
  texts → synthesized Readings via the S4 executor → stored in
  `specs/readings/dream/` with `source: dream`. Dreams are *data with
  provenance*, like incumbent input — the LLM authors requests-as-text and
  Readings-as-specs, never code (house rule 5 intact).
- **S5.2** Witness discipline (the honesty core): mining (`macro_mine.mine`)
  runs over real ∪ dream; `macro_admission_decision`'s `uses >= 2` count and
  its `dl_after < dl_before` are computed **over real readings only**
  (`witness_filter=lambda r: r.source == "real"`). A macro no real reading
  uses cannot be admitted, no matter how much dream-DL it saves.
- **S5.3 Teeth**: a macro pattern planted in 3 dream readings and 0 real
  ones is mined but REFUSED (uses=0 over real); the same pattern then
  hand-added to 2 real corpus entries flips to admitted. Both directions in
  one demo (`demo_dream.py`).
- **Done when:** teeth green; the default-`None` regression proves S5
  changed nothing for non-dream callers.

## Interface freezes (agree before parallel work)

- **Z-A `planner/search.py`**: `beam_search(initial, expand, score, *,
  beam_width: int, max_depth: int)`; `expand` pure, `score` pure, ties by
  canonical JSON; NO other exports.
- **Z-B corpus entry**: `{request: str, reading: {service, statements}}` +
  loader-added `source ∈ {real, dream}`; statements exactly the frozen
  Reading-statement shape (ROADMAP freeze #3).
- **Z-C macro candidate**: exactly `{name, params, body}` as consumed by
  `mdl_macros` today; miner-generated names are `mined_<sha8>` (content-
  addressed, deterministic).
- **Z-D events**: `speculation-divergence` payload `{stage, direction ∈
  {false-accept, false-reject}, candidate_sha, request_sha}`; logged via
  `registry.log_event`, listed by `cgb.py events`.
- **Z-E** `macro_admission_decision(readings, candidate, macro_table=None,
  witness_filter=None)` — the ONLY signature change this plan makes to an
  existing module, additive with a `None` default.

## File-ownership matrix (W = writes, N = new, r = reads)

| file | S0 | S1 | S2 | S3 | S4 | S5 |
|---|---|---|---|---|---|---|
| `specs/readings/` | **N** | r | | r | r | W |
| `buildloop/corpus.py` | **N** | r | | r | r | W |
| `planner/search.py` | | **N** | r | r | | |
| `buildloop/macro_mine.py` | | **N** | | | | r |
| `planner/lookahead.py` | | | **N** | | | |
| `buildloop/loop.py` (`pick_group` only) | | | W | | | |
| `planner/choices.py` | | | | **N** | r | |
| `buildloop/speculate.py` | | | | | **N** | r |
| `buildloop/service_loop.py` (additive flag) | | | | | W | |
| `buildloop/mdl_macros.py` (Z-E only) | | | | | | W |
| `buildloop/dream.py` | | | | | | **N** |
| `metrics/` | | | W | | W | |
| demos/tests/results (each phase's own) | N | N | N | N | N | N |
| README (Zone-3 section; merge-owned) | | W | W | W | W | W |
| `kernel/*` | r | r | r | r | r | r |

`kernel/__init__.py`, `kernel/backends.py`, `generators/service_gen.py`,
`generators/reading.py`, `generators/reading_compile.py`, `run/semantic.py`
are **read-only for every Zone-3 phase**. If a phase believes it needs to
edit one, the plan is wrong — stop and escalate, do not edit.

## Builder briefing addendum (on top of ROADMAP.md's briefing)

1. Zone-3 rules Z1–Z3 are review-blocking, same standing as house rules.
2. Every search/miner/enumerator must be deterministic: no `random`, no
   clocks, no dict-order dependence (sort or canonical-JSON everywhere).
3. Every phase's demo follows the repo demo convention (docstring naming
   each part and its failure class; per-part booleans; `REQUIRES_LLM`
   constant; `summary:` JSON line; `sys.exit`); capture with
   `python3 demo_X.py | tee results/X_demo.txt` and commit the capture.
4. Regression: `run_regression.py --fast` green before every push; add each
   phase's LLM-free tests to the fast tier.
5. Commit to the branch your task assignment designates; never push to
   `main` from a Zone-3 task.

## Hazards (⚠ = verified against the codebase by the review sweep)

*Populated by the adversarial review swarm; each finding carries file:line
evidence or an experiment. Findings that invalidate part of the plan are
folded back into the phase text above and cross-referenced here.*

## Acceptance, restated

1. Macro vocabulary growth is search-driven: on the committed corpus, the
   searched admission sequence strictly beats greedy arrival order on total
   DL, and declines to admit on incompressible corpora (S1).
2. Build-loop steering is lookahead-driven and measurably better on the
   reach-vs-cost curve than both existing policies on at least the planted
   backlog, without changing them (S2).
3. Design choice is an optimization with a stated objective — minimum
   macro-aware DL subject to demand entailment — and the entailment gate
   demonstrably overrides Occam (S3).
4. Synthesis spends LLM calls K-wide against cheap exact gates, certifies
   only through the unchanged kernel, and every prediction miss is a logged,
   queryable event (S4).
5. Dreamed data can propose but never witness; both directions are
   demonstrated (S5).
6. Zero new kernel contracts; zero edits to kernel, emitters, compiler, or
   reference; every certificate byte-identical to what the non-speculative
   path would have produced.
