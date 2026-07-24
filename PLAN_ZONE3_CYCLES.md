# PLAN_ZONE3_CYCLES.md — Zone 3 as driver-cycle work packages

SPECULATION.md specifies Zone 3 (the speculative planner) as a
**maximum-width swarm schedule** — nine Wave-0 packages, three Wave-1, three
Wave-2, one agent per worktree per exclusive file set. That schedule assumes
many hands at once. This document re-slices the *same* phases (S0→S5, no new
scope) into **serial, cycle-sized work packages** that the recurring driver
Routine consumes one at a time, where every package:

- **(a)** has an **entry predicate** checkable from committed state alone
  (file existence, a symbol grep, a test node, a bench/CSV row) — the driver
  runs the check before spending anything;
- **(b)** names its **exit teeth**: the committed test file that must stay
  green, or the exact new test a package must add;
- **(c)** names **which committed measurement records the payoff** — and for
  speculation packages that is `bench/bench_speculate.py`, the speculation
  bench, which **measures the trade and never asserts it pays**
  (SPECULATION.md S4, ⚠H8/H43); for non-synthesis phases the payoff lives in
  the phase's own committed CSV/demo capture, likewise measured never
  asserted;
- **(d)** cites the **hazards-ledger items that bind it** by their SPECULATION
  identifiers (`H2…H58`, freezes `Z-A…Z-F`), the load-bearing ones quoted.

**Ordering law (invariant for the driver).** Packages are ordered so each
cycle leaves the tree **green and shippable**: **full suite green
(`python3 -m pytest tests/ -q -n auto`) is part of every package's exit**, no
cycle depends on an unmerged sibling, and no exclusive file is left
half-written across a cycle boundary. The critical path is SPECULATION's own:
`{Z3-01, Z3-04, Z3-05, Z3-06} → Z3-10 → Z3-13 → Z3-15`.

**This is documentation only.** It adds nothing to the trusted surface. Per
CLAUDE.md the anti-list (`buildloop/growth_protocol.py::ANTI_LIST`) and
`TRUST.md`/`kernel/certs.py` pins change only through the PLAN_REFLECT
ceremony; no cycle below touches them.

---

## Trust posture — quoted verbatim, binding on every package

SPECULATION.md §"Trust posture" is reproduced here without alteration; it is
the frame every package below inherits.

> The planner is **untrusted-by-construction, exactly like the LLM**. House
> rules of ROADMAP.md and PLAN_COMBINED_LOOP.md bind here; three
> planner-specific rules:
>
> - **Z1 — proposals only.** No planner output is ever a certificate or a
>   verdict, and no cache entry read by a verdict may exist unless it was
>   computed **by the unchanged kernel on the identical (artifact, contract)
>   identity** the non-speculative path would have used (⚠H9: warmed entries
>   change *when* the kernel ran, never *what it concluded*).
> - **Z2 — exact objectives first (re-anchored, ⚠H49/H50/H51).** Phases S1–S3
>   may only score with the exact pure functions **of the live economy**:
>   `dl._ledger_total` over `dl.LedgerSnapshot` (hypotheticals via
>   `dl._with`), `planner.plan_for_features` (the declared single chain-cost
>   source, `dl.py:11-13`), `mdl_macros.corpus_dl`/`dl_reading`, and
>   deterministic compile + reference replay. `mdl.total_dl` /
>   `mdl.chain_length_for` are **struck as objectives** — frozen legacy,
>   verified divergent from the planner (blind to `kind=="pass"` and to
>   3–4-link chains); they may appear only as *reported* legacy series for
>   continuity with recorded metrics. Learned/heuristic scores stay confined
>   to S4/S5 and ship with the divergence ledger in the same commit.
> - **Z3 — measured fidelity.** Any component that *predicts* a kernel or
>   gate verdict logs prediction-vs-actual as a first-class
>   `speculation-divergence` event (`registry.log_event`,
>   `library/__init__.py:319`; `cgb.py events`, cmd at `cgb.py:459`).
>
> No phase adds a kernel contract; `kernel/*`, `generators/service_gen.py`,
> `generators/reading.py`, `generators/reading_compile.py`, `run/semantic.py`,
> and `library/__init__.py` are read-only (calling backend machinery —
> `SmtBackend.run_z3` at `kernel/backends.py:487`,
> `HypothesisBackend.check_intent_reference` at `:243` — is permitted, ⚠H12).

And the H58 rung premise, quoted because it is what makes mined-macro uses
safe and therefore recurs in Z3-05/Z3-10/Z3-11/Z3-13:

> ⚠H58 … mined macros are **no longer accounting-only-forever** … Every
> *actual* macro use is certified per-emission by
> `translation-cert(anchor="reference-lowering")` whose channel 1 is
> compile-hash identity against the **retained original baseline reading**
> (`kernel/__init__.py:321-348`; teeth in `tests/test_rung.py` prove a lossy
> rewrite is refused) … a mined table is untrusted, data-derived vocabulary;
> the rung is what makes its uses safe.

**Z1, restated for the driver and repeated in every speculation-output
package below:** a mined macro table, a lookahead rollout value, a
choice-space design, a fanned-out Reading, and a dream corpus are **all
proposals**. None is a certificate. Each becomes trustworthy only by passing
the *unchanged* kernel/gate on the identity the non-speculative path would
use. A cycle that produces a speculative output and cannot show that gate is
**red**, not shippable.

---

## Current-tree premise (why most entry predicates already hold)

Unlike SPECULATION.md's fresh-checkout premise, **this tree has already
landed Zone 3 end to end.** Verified committed state at slicing time:

- `buildloop/reading_corpus.py`, `planner/search.py`, `planner/lookahead.py`,
  `planner/choices.py`, `buildloop/speculate.py`, `buildloop/dream.py` all
  exist.
- `specs/readings/` holds 11 hand-written bounds/temporal Readings
  (`01,02,03,04,05,06,09,14,15,17,18`) plus `specs/readings/dream/` (3 files).
- `cgb.py` has `seed-readings` (`cgb.py:365`, `_seed_readings` at `:394`).
- The S1.7 seam is closed: `dl.py:339`
  `macro_cost = sum(mdl_macros.dl_macro(m) for m in snap.macro_table.values())`.
- `witness_filter=` threads `recurrence.mine` (`:403/:434`),
  `gc_macros` (`:480/:501`), `gc_table` (`:536`).
- The S4.0 fill-path fix is in place: `loop.py:564-578` reads request *text*,
  calls `synthesize_semantic`, persists via `registry.reading_add`.
- `speculate.fan_out` (`:180`) and `pre_gate` (`:48`) exist; `bench/bench_speculate.py`
  exists.
- Committed measurements: `results/macro_search.csv`
  (`natural,none,0,87.0…` / `natural,greedy,1,52.0…`),
  `results/lookahead_ranking.csv`, `results/metrics_closure_corpus.csv`,
  `results/reach_vs_cost_all.png`.
- Teeth present: `tests/test_reading_corpus.py`, `test_search.py`,
  `test_search_props.py`, `test_macro_mine.py`, `test_searched_recurrence_flag.py`,
  `test_lookahead.py`, `test_lookahead_policy.py`, `test_choice_search.py`,
  `test_speculate.py`, `test_witness_filter.py`, `test_witness_live.py`,
  `test_rung.py`.

**Consequence for the driver.** Most packages below have their entry
predicate **and** their exit teeth already satisfied on the committed tree.
For those, one driver cycle is a **verify-and-record no-op**: run the entry
check, run the exit teeth, confirm green, record the evidence, ship nothing
new. The genuinely-open queue is small and is called out per package under
**Status**: the two LLM-requiring benches (S4/S5, skippable by design), and
the spec-ambiguity items collected in the final section. This is stated, not
papered over — it is the honest state of the tree.

---

## S0 — Reading-corpus provisioning (content + file→table bridge)

### Z3-01 — S0.2 bridge + seed step (SPECULATION WP-A)

- **Entry predicate:** `specs/requests/` populated (the byte-match targets
  exist); `library/__init__.py` exposes `reading_add`/`reading_get`/
  `readings_all`. Check: `grep -n "def reading_add" library/__init__.py`.
- **Work:** `buildloop/reading_corpus.py` = the file→table bridge
  (`load_readings(dir) -> list[CorpusEntry]`, `CorpusEntry(request,
  statements, source)` — a **new dataclass, never `reading.Reading`**, ⚠H16/H17);
  `cgb.py ledger seed-readings` byte-matches `request` against a committed
  `specs/requests/` file (⚠H44 enforcement at seed time), resolves
  `demand_id = sha256("nl-request:"+relpath)`, **certifies** via LLM-free
  `certify_reading(macro_table=, on_certified=)`, persists with
  `registry.reading_add`.
- **Exit teeth:** `tests/test_reading_corpus.py` green (loader + seed
  round-trip); full suite green.
- **Payoff measurement:** none is a bench — S0 buys *inputs*, not speed. The
  measured done-when is operational: **≥14 entries seed and certify on a
  fresh DB**, and `run_regression.py --fast < 90 s` (⚠H18: never touch
  `FAST_DEMOS`). No payoff is asserted; a seed that certifies fewer than 14 is
  a red cycle.
- **Hazards bound:** H46 (the fill path is broken; **S0 owns only the
  file→table bridge, the live fill-path fix is S4.0/Z3-09** — do not conflate);
  H46b — *"the honest default is certify-at-seed"* because `dl.py:247-251`
  treats any readings row as coverage, so an uncertified seed would silently
  improve `ledger_dl`; H55 — **`source` is derived from `demand.origin`, not
  path-inferred**: real ⇔ `origin=="exogenous"`, dream ⇔ `"system"`, no
  `source` key in files, a real-classified seed with no committed byte-match
  is a hard error; H48 — no `load_macros()`, the accessor is
  `registry.macro_table()`; H14/H15/H17; freeze **Z-B**.
- **Z1:** a seeded Reading is a proposal until `certify_reading` returns a real
  `cert_id`; the seed persists the cert, not a bare reading.
- **Status on tree:** **Satisfied.** `reading_corpus.py`, `cgb.py:365
  seed-readings`/`:394 _seed_readings`, `tests/test_reading_corpus.py` all
  committed. Driver cycle = verify-and-record.

### Z3-02 — S0.1 bounds Readings (SPECULATION WP-B)

- **Entry predicate:** Z3-01 shipped (`reading_corpus.load_readings` importable);
  the eight request files exist: `ls specs/requests/0{1,2,4,5,6}_*.txt
  specs/requests/1{4,5,8}_*.txt`.
- **Work:** hand-written Readings for requests **01,02,04,05,06,14,15,18** as
  `specs/readings/NN_*.json`, each `{request, reading:{service, statements}}`,
  each passing `parse_reading` (`generators/reading.py:264`) with **no LLM**.
- **Exit teeth:** the eight files load and certify under
  `tests/test_reading_corpus.py`'s corpus scan; full suite green.
- **Payoff measurement:** none directly — these are corpus inputs; their
  compression payoff is realized downstream and measured by
  `results/macro_search.csv` (Z3-10). Not `bench_speculate`.
- **Hazards bound:** H15 (**only the faithful set is transcribable**; the
  disjunctive-eventuality / trigger-`within` / nesting requests are *not*
  targets); freeze **Z-B** (statements per ROADMAP freeze #3).
- **Status on tree:** **Satisfied** — `01,02,04,05,06,14,15,18` committed
  under `specs/readings/`.

### Z3-03 — S0.1 temporal Readings (SPECULATION WP-C)

- **Entry predicate:** Z3-01 shipped; request files `03,09,17` exist.
- **Work:** hand-written Readings for **03, 09, 17** (the temporal-but-frozen-
  fragment-expressible members).
- **Exit teeth:** files load+certify under `tests/test_reading_corpus.py`;
  full suite green. **Now the ≥14-entry seed check of Z3-01 is fully covered**
  (11 files here + inlined `demos/demo_macros.py` entries).
- **Payoff measurement:** as Z3-02 — downstream, via `macro_search.csv`.
- **Hazards bound:** H15; H56 (temporal readings route through stage 3.5
  `monitor-cert` in `certify_reading` — the seed must tolerate that stage).
- **Status on tree:** **Satisfied** — `03,09,17` committed.

---

## S1 — Searched macro admission (upgrade the landed greedy miner)

### Z3-04 — S1.1 search skeleton (SPECULATION WP-D)

- **Entry predicate:** none beyond the repo — `planner/` importable. Check:
  `test ! -e planner/search.py` would mean unlanded.
- **Work:** `planner/search.py`::`beam_search(initial, expand, score, *,
  beam_width, max_depth)` — deterministic, ties by canonical JSON, returns
  **best state ever visited** (freeze **Z-A**), no other exports.
- **Exit teeth:** `tests/test_search.py` + `tests/test_search_props.py`
  (property tests for best-ever-visited and tie determinism); full suite
  green.
- **Payoff measurement:** none — a pure combinator; its payoff is realized by
  its consumers (Z3-07/Z3-10) and measured there.
- **Hazards bound:** H19 — *"best state ever visited (⚠H19 — both DL
  objectives are non-monotone in admissions)"*: the skeleton **must** return
  the best-ever, not the terminal, state, or the non-monotone objective
  silently regresses; freeze **Z-A**.
- **Status on tree:** **Satisfied** — `planner/search.py`, `test_search.py`,
  `test_search_props.py` committed.

### Z3-05 — S1.2 miner filters (SPECULATION WP-E)

- **Entry predicate:** `buildloop/recurrence.py` present with `_demand_windows`
  and `mine`. Check: `grep -n "_demand_windows\|def mine" buildloop/recurrence.py`.
- **Work:** a **patch to `recurrence.py`** (not a new module, ⚠H48):
  reject any candidate with a bare-placeholder body statement / require ≥60%
  concrete nodes per body template (H3); widen `_demand_windows` to **uniform
  `(force, quote)`** windows (H2).
- **Exit teeth:** `tests/test_macro_mine.py` — must include a node proving the
  **pure wildcard `["$p0","$p1"]` is now rejected** (pre-patch it admitted at
  Δ=−113.0) and a node proving mixed-`(force,quote)` windows are excluded;
  full suite green.
- **Payoff measurement:** the filters are a **correctness** guard, not a
  speed payoff — the measured effect is "nothing admitted on the
  incompressible corpus" recorded by `results/macro_search.csv` row
  `…,search,0,…` (Z3-10). Not `bench_speculate`.
- **Hazards bound:** H3 (quoted) — *"the live gate admits the pure wildcard
  `["$p0","$p1"]` on an all-distinct corpus, Δ = −113.0, because
  `dl_invocation` (`mdl_macros.py:62`) prices args size-blind"*; H2 — mixed
  windows *"'compress' but are unrealizable as legal invocations"*
  (`reading.py:183-206`, choice-must-quote-nothing `:329`) and block S3's
  choice-tail idiom; H47 (the landed miner already has anti-unification /
  2-witness / gc — **do not re-add**).
- **Z1:** a mined candidate is a proposal; the filters remove candidates that
  "compress" only by pricing artifacts, never by shrinking real emissions.
- **Status on tree:** **Satisfied** — `recurrence.py` carries the filters;
  `tests/test_macro_mine.py` committed.

### Z3-06 — S1 fixtures: trap + incompressible corpora (SPECULATION WP-F)

- **Entry predicate:** Z3-05 shipped (the trap only reproduces with H3
  filters in place, ⚠H25).
- **Work:** `tests/fixtures_macro_corpora.py` — the planted trap corpus where
  greedy admission of A blocks the strictly better `{B,C}`, and the
  incompressible corpus.
- **Exit teeth:** fixtures import clean and are referenced by `test_macro_mine.py`
  / the Z3-10 demo; full suite green.
- **Payoff measurement:** the fixtures *are* the measuring instrument for
  Z3-10's `part_b` — the executed numbers **none=78.0, greedy/{A}=55.0,
  searched/{B,C}=35.0** land in `results/macro_search.csv`. Not
  `bench_speculate`.
- **Hazards bound:** H11/H25 — *"Residual-heterogeneity proviso"*: the trap's
  53→35 win survives only when residual heterogeneity is controlled and the
  H3 filters are in place; the fixture recipe must pin both.
- **Status on tree:** **Partially — verify at cycle.** No
  `tests/fixtures_macro_corpora.py` was observed in the tree listing; the
  trap numbers appear folded into `results/macro_search.csv` and the demo. If
  the fixture file is absent, this cycle's exit tooth is "add
  `fixtures_macro_corpora.py` and reference it"; if the demo already inlines
  the corpora, the cycle records that and ships nothing. **Named as an
  open-verify item, not assumed satisfied.**

### Z3-10 — S1.3–S1.7 searched recurrence + demo/CSV + gc widening + ledger term (SPECULATION WP-J)

> Placed here in cycle order (after S0/S1.1/S1.2/fixtures) even though it is
> SPECULATION Wave-1: it is **the critical-path package**
> (`{A,D,E,F}→J→M→O`). It is **irreducibly one cycle** — S1.3, S1.6, and
> S1.7 all edit shared owned surfaces (`_dispatch_recurrence`, `gc_macros`,
> `dl._ledger_total`); splitting them across cycles would leave the tree red
> mid-flight, which the ordering law forbids.

- **Entry predicate:** Z3-01/02/03 (corpus seeds), Z3-04 (`beam_search`),
  Z3-05 (filters), Z3-06 (fixtures) all shipped. Check:
  `grep -n "def beam_search" planner/search.py` and the ≥14-entry seed.
- **Work:** (S1.3) `_dispatch_recurrence` gains a **flag-gated searched mode**,
  default greedy and regression-pinned; state=(table-so-far, sequence),
  expand=`recurrence.mine(readings, table)` candidates passing the
  **explicitly restored `macro_admission_decision` gate call** (the arbiter,
  Z1), score=`corpus_dl(readings, table)["total"]`, winner admitted step by
  step via `registry.macro_add`. (S1.6) widen `gc_macros` to retire **any**
  macro whose ablation strictly reduces total DL (keep the `uses<2` fast
  path). (S1.7) add
  `sum(dl_macro(m) for m in snap.macro_table.values())` to
  `dl._ledger_total` (one-line-owned) so search objective and ledger agree.
- **Exit teeth:** `tests/test_searched_recurrence_flag.py` — **greedy-default
  byte-identical to recorded scheduler fixtures** (searched mode off ⇒ no
  change); `tests/test_macro_mine.py` for the gc widening; a `dl.py` test
  pinning the macro-cost term; `demos/demo_macro_search.py`
  (`REQUIRES_LLM=False`) parts **a/b/c** green; full suite green.
- **Payoff measurement:** **`results/macro_search.csv`** — columns
  `corpus, strategy∈{none,greedy,search}, macros_admitted, corpus_dl_total,
  mean_statements, strict_divergence` (⚠H26). This CSV *measures* searched ≤
  greedy on every arrival order and the trap's 78→55→35; it **never asserts**
  the search wins on the natural corpus — an honest tie there is recorded via
  `strict_divergence=False` (⚠H24), not forced. This is **not**
  `bench_speculate`: S1 payoff is a compression CSV, not a token-trade bench.
- **Hazards bound:** H47 (re-scope: filters+sequence-search only); H49
  (quoted) — *"`_ledger_total` charges no macro-definition cost … realized
  deltas systematically beat expected by exactly `dl_macro(candidate)`"* →
  S1.7 closes it; H23 (tested orders: sorted/reversed/N rotations); H24
  (natural-corpus tie is a finding); H25/H11; H26; H58 (macro uses safe via
  the rung); freeze **Z-A**, **Z-C** (macro store = the registry `macros`
  table, names `m_<sha12>`, retirement = `retired` column + `macro-retired`
  events, **no file store**).
- **Z1:** the searched table is a **proposal**; its home is the existing
  `macros` table; every *use* is certified per-emission by the W5.2 rung
  (H58) with the retained-original comparand — the table's admission never
  certifies its own uses.
- **Status on tree:** **Largely satisfied.** `dl.py:339` macro-cost term
  present; `test_searched_recurrence_flag.py` and `results/macro_search.csv`
  committed. Verify at cycle that the demo emits all three
  `strategy` rows and the gc widening test exists.

---

## S2 — Lookahead steering

### Z3-07 — all of S2: lookahead policy + H53 demand-seed (SPECULATION WP-G)

> **Irreducibly one cycle:** S2.1–S2.4 touch `planner/lookahead.py` (new),
> `loop.py::pick_group`, `milestones.py:81`, `cgb.py:511`, and
> `metrics/run_experiment.py::run_config` — the H53 fix and the policy wiring
> must land together or `pick_group` references a policy the CLI cannot pass.

- **Entry predicate:** `beam_search` present (Z3-04); `pick_group` present at
  `loop.py:120-140`. Check: `grep -n "def pick_group" buildloop/loop.py`.
- **Work:** `planner/lookahead.py`::`rollout_value(generators, backlog, group,
  depth) -> float`, pure over the iteration's frozen `dl.LedgerSnapshot`;
  coverage rule = **`plan_for_features(...) is None`** (NOT
  `mdl.chain_length_for`); hypothetical entry = ksy branch of
  `candidate_entry_from_spec` **plus `"authored_bytes": 0`** (H54); ksy-only
  (abnf and `json-subset` score +∞, H57); value =
  `dl._ledger_total(dl._with(snap, hyp))["ledger_dl"]` best-ever within
  `depth`, via `beam_search`. Add `"lookahead"` to `pick_group` as an
  **additive** policy using `min(...)` (H30), to `milestones.py:81`'s tuple,
  and to `cgb.py:511`'s `--policy` choices. Add the H53 demand-seed to
  `run_config` (one exogenous `spec-file` row per backlog entry, mirroring
  `_ledger_sync`'s shape).
- **Exit teeth:** `tests/test_lookahead.py` + `tests/test_lookahead_policy.py`;
  `demos/demo_lookahead.py` (`REQUIRES_LLM=False`) **part_a strict** (depth-2
  picks the enabling miss, strict inequality on replayed final cost) and
  **part_b relational** (lookahead admissions ≤ closure, dominating at equal
  budget — **no absolute constants in asserts**, H52); a test proving a
  **fresh-DB metrics run admits >0 under `closure`** (the H53 coverage tooth);
  existing `frequency`/`closure` picks and `scheduler-decision` logs unchanged
  on recorded fixtures; full suite green.
- **Payoff measurement:** `results/lookahead_ranking.csv` +
  `results/metrics_closure_corpus.csv` + `results/reach_vs_cost_all.png`
  (⚠H32: produced by calling `metrics/plots.py:reach_vs_cost` over **every**
  curve). The relational teeth are measured against these; **no absolute
  constant is asserted** (H52). Not `bench_speculate`.
- **Hazards bound:** H50 (quoted) — *"`mdl.chain_length_for` no longer
  mirrors the planner (kind=='pass': 185-vs-0 covered; 3-link: None-vs-3) —
  verified divergent"* → coverage must use `plan_for_features` (Z2); H51 (the
  plain-dict mirror is the *forbidden* pattern; `plan_for_features` prices
  hypotheticals natively); H54 (`authored_bytes:0` or underprice by ~0.3 DL);
  H57 (`json-subset` excluded); H52 (old 10-vs-11/316.6-vs-318.8 numbers
  **do not reproduce**; pin the recipe in code, relational asserts only);
  H53 (quoted) — *"the live M5 path is broken: `run_config` never seeds the
  demand ledger → every policy 'converges' at iteration 1"*; H28/H29/H30;
  H33 (recorded artifact residue).
- **Z1:** a `rollout_value` is a **proposal score** over hypothetical
  admissions; the scheduler's actual dispatch still certifies through the
  unchanged gate — the rollout never authorizes an admission by itself.
- **Integrator note (from the spec):** `metrics/run_experiment.py` was
  declared **unowned** in the draft; the H53 seed edit carries an explicit
  escalation flag — a driver cycle that touches it must record the
  escalation, per SPECULATION S2.4.
- **Status on tree:** **Satisfied.** `planner/lookahead.py`,
  `loop.py:163-167` lookahead branch, `run_config` at
  `metrics/run_experiment.py:57`, both lookahead tests, and the result CSVs
  all committed. Verify the H53 fresh-DB `>0`-admit test exists as a named
  node.

---

## S3 — Choice-space search

### Z3-08 — S3 core: variant enumeration + scoring (SPECULATION WP-H, provides Z-F)

- **Entry predicate:** `planner/` importable; `compile_reading` present
  (`reading_compile.py:100-121`). Check: `grep -n "def compile_reading"
  generators/reading_compile.py`.
- **Work:** `planner/choices.py` — vary **only** choice-force statements
  (lifecycle/transition/input/choice-`action`, `reading.py:116-128`); template
  family `{[open,closed],[open,active,closed]}`, forward/self edges;
  demands/presuppositions copied **byte-identically** (test-pinned). Gate (b) =
  the **order-entailment check** in `compile_reading` (`CompileError` at :116)
  — refused variants counted then discarded (H35); non-vacuity filter (H36).
  Scoring = compile + reference replay composed from
  `service_gen.emit_service` + `build_scenario_reference_harness`
  (`service_gen.py:923`) + `HypothesisBackend.check_intent_reference`
  (`kernel/backends.py:243`), score =
  `mdl_macros.dl_reading(reading, table)` with
  **`table = registry.macro_table()`** (H48) + size proxy. Exports **Z-F**
  `score_reading(reading, macro_table) -> float` (with `{}` = flat score).
- **Exit teeth:** `tests/test_choice_search.py` — **byte-compare test pinning
  demand/presupposition immutability**, empty-scenario variants discarded;
  `demos/demo_choice_search.py` **part_b** (planted `order` demand: globally
  minimal design that violates it is **refused**, best admissible returned);
  full suite green.
- **Payoff measurement:** `demos/demo_choice_search.py` capture — the
  flat/macro-aware DL argmins. Measured, not asserted-positive; **H37 states
  the argmin is a tie class** (transition targets are DL-invariant), so the
  capture records a tie class, it does not claim a unique strict winner. Not
  `bench_speculate`.
- **Hazards bound:** H35 (entailment gate **overrides Occam** — refused
  variants discarded, never scored around); H36 (discard empty-scenario
  variants); H37 (quoted-in-spirit: *"transition targets are DL-invariant,
  the argmin is a tie class"* — the exit tooth cannot demand a unique
  winner); H48 (`registry.macro_table()`, not a file accessor); H6/H55 (when
  dream entries exist, DL uses the **exogenous-origin sub-corpus**); freeze
  **Z-F**.
- **Z1:** a choice-space variant is a **proposed design**; both the flat and
  macro-aware winners must **certify through the unchanged compile+kernel
  path** before they mean anything.
- **Status on tree:** **Satisfied** — `planner/choices.py`
  (`enumerate_variants`, `score_reading`, `search_design`),
  `demos/demo_choice_search.py`, `tests/test_choice_search.py` committed.

### Z3-13 — S3 part_a: choice-tail macro against the live table (SPECULATION WP-M)

> Wave-2, on the critical path (`…→J→M→O`). Depends on Z3-10 (searched
> recurrence) **and** Z3-12 (scorer swap): part_a's idiom is a **structural
> choice-tail macro** mineable **only after** S1.2 widened windows to
> uniform-`(force,quote)` (H2) — before that it is hand-planted.
- **Entry predicate:** Z3-05 shipped (uniform-`(force,quote)` windows) **and**
  Z3-10 shipped (`registry.macro_table()` populated by the searched miner).
- **Work:** S3 part_a — the flat vs macro-aware argmins differ; both winners
  certify; the macro-aware branch prices against the **live
  `registry.macro_table()`**.
- **Exit teeth:** `demos/demo_choice_search.py` part_a green (both winners
  certify); `tests/test_choice_search.py` extended if a live-table node is
  added; full suite green.
- **Payoff measurement:** the same `demo_choice_search.py` capture — the
  flat/macro-aware argmin **divergence** is the measured payoff; still a tie
  class within each (H37). Not `bench_speculate`.
- **Hazards bound:** H4 (the idiom is a structural choice-tail macro —
  respec'd, **dependency on S1.2 stated**, not assumed); H2 (window widening
  prerequisite); H48.
- **Z1:** proposed designs; both certify through the unchanged path.
- **Status on tree:** **Verify at cycle** — `demo_choice_search.py` and
  `test_choice_tail.py` exist; confirm part_a runs against the live
  `macro_table()` rather than a hand-planted table.

---

## S4 — Speculative synthesis executor + divergence ledger + fill-path fix

### Z3-09 — S4 core: fill-path fix + fan-out + pre-gates + divergence ledger (SPECULATION WP-I)

> **Irreducibly one cycle:** S4.0–S4.4 co-edit `buildloop/speculate.py` (new),
> `service_loop.py` (flag), and `loop.py::_dispatch_request`. The fill-path
> fix and the fan-out share the persistence seam.

- **Entry predicate:** `reading_add` reachable (Z3-01); `_dispatch_request`
  present at `loop.py:446-452`. Check: `grep -n "_dispatch_request"
  buildloop/loop.py`.
- **Work:** (S4.0) repair `_dispatch_request` — read request *text* from
  `payload_ref`, call `synthesize_semantic`, persist via `registry.reading_add`
  with the composed cert id (**the single highest-value small fix in Zone 3**).
  (S4.1) `speculate.fan_out(request, k, *, model)` — k LLM-authored Readings,
  `--spend` cap, **k=1 preserves today's behavior**. (S4.2) pre-gates cheapest
  first: `reading-gate`=`parse_reading`; quick-SMT under `common.SMT_LOCK`;
  compile; **entailed-scenario replay rank-only, never reject** (H10 — all
  three mitigations mandatory). (S4.4) divergence ledger = events-table only,
  payload `{stage, direction, candidate_sha, request_sha}`.
- **Exit teeth:** `tests/test_speculate.py` — **k=1 regression** monkeypatches
  `call_llm` with a canned transcript and asserts **identical (prompt,
  cache_key, event) sequences** against the *current* stage labels (including
  stage 3.5 `monitor-cert`, H56); **S4.0 covered by a test** — a request-miss
  dispatch on a fresh DB yields a `readings` row; `demos/demo_speculate.py`
  (LLM-free, hand-planted) — the inverted-verb-effect plant caught at
  `stage='protocol'`, **divergence event logged, no composed certificate
  exists**; full suite green.
- **Payoff measurement:** **`bench/bench_speculate.py`** — **the speculation
  bench.** k∈{1,3,5}, ≥3 requests; metrics `llm_calls_to_certify` (**expected
  flat-to-worse**), `rounds_to_certify`, wall-clock, per-stage loser
  attribution → `results/speculate_bench.csv`. Per its own docstring it
  **"never asserts the trade pays off"** (H8/H43); **LLM-requiring, last and
  skippable** — on any LLM failure it prints SKIPPED and exits 0, so a
  no-key driver cycle records SKIPPED as a **green** exit.
- **Hazards bound:** H46/H46-fill (the broken path-vs-text + never-returned
  `"reading"` key); H8 (quoted) — *"the repo's own captures show 1–3 rounds
  or pre-gate-invisible failure, so S4 is a *measured trade*, not a promised
  saving"*; H10 (rank-only stage 4 + every-Nth loser audit ON + run-record
  claim + TRUST 3.4 caveat — **all mandatory**); H12 (composing backend
  machinery is permitted); H40/H41 (updated pre-gate/regression targets); H56
  (stage 3.5 `monitor-cert`, new kwargs); H42 (first **verify** stage-4 replay
  misses the plant, else switch plant); freeze **Z-D**.
- **Z1 (explicit — this package produces speculative outputs):** a fanned-out
  Reading is a **proposal**; **no *composed* certificate exists for a loser**;
  warmed sub-certificates are real, content-addressed, and computed by the
  **unchanged kernel on the identical (artifact, contract) identity** (H9) —
  the demo's exit tooth *asserts no composed certificate exists* precisely to
  keep Z1 visible.
- **Z3 (explicit):** every prediction miss logs a
  `speculation-divergence` event (`registry.log_event`, `library:319`).
- **Status on tree:** **Satisfied** (code path). `speculate.fan_out`
  (`:180`), `pre_gate` (`:48`), `loop.py:564-578` S4.0 fix,
  `tests/test_speculate.py`, `demos/demo_speculate.py` committed. **Open:**
  `bench/bench_speculate.py` is LLM-requiring — its live capture is the honest
  residual (skippable).

### Z3-12 — S4 scorer swap: Z-F into speculate + H42 verification (SPECULATION WP-L)

- **Entry predicate:** Z3-08 shipped (`choices.score_reading`, freeze Z-F)
  **and** Z3-09 shipped (`speculate.pre_gate` flat fallback in place).
- **Work:** swap the **Z-F seam** in `speculate.py` — replace the flat
  fallback score with `score_reading(reading, macro_table)`; **verify H42**
  (stage-4 replay misses the plant) as a code check, not an assumption.
- **Exit teeth:** `tests/test_speculate.py` extended with a Z-F node
  (macro-aware ranking, `{}`=flat identity); the H42 verification recorded;
  full suite green.
- **Payoff measurement:** `bench/bench_speculate.py` (same bench, now with the
  real scorer ranking survivors); measured, not asserted (H8/H43); skippable.
- **Hazards bound:** H42 (quoted intent: *"first verify stage-4 replay misses
  it (else switch to a temporal-stranding plant)"*); freeze **Z-F** (`{}`
  equals the flat score).
- **Z1 (explicit):** the scorer only **ranks proposals**; ranking never
  certifies and never rejects a candidate the kernel would accept (H10
  rank-only).
- **Status on tree:** **Verify at cycle** — `choices.score_reading` exists;
  confirm `speculate.py` consumes it rather than the flat fallback, and that
  the H42 check is committed.

---

## S5 — Dream corpus under witness discipline (origin-based)

### Z3-11 — S5.2/S5.3 witness discipline, hand-planted dreams (SPECULATION WP-K)

- **Entry predicate:** Z3-01 (seed step) **and** Z3-05 (filters) shipped;
  `recurrence.mine`/`gc_macros` present. Check:
  `grep -n "witness_filter" buildloop/recurrence.py`.
- **Work:** thread additive `witness_filter=None` into
  `macro_admission_decision` **and** `recurrence.mine` **and** `gc_macros`
  (**and** `gc_table`, `mdl_macros.py` for the corpus-DL restriction) —
  `witness_filter=lambda e: e.origin == "exogenous"`; witnesses count per
  **distinct real request**; S1.3/S3.2 scores compute over the
  exogenous-origin sub-corpus when system-origin readings exist. Hand-planted
  dream files under `specs/readings/dream/` (no LLM).
- **Exit teeth:** `tests/test_witness_filter.py` — **default-`None`
  byte-identical behavior in all three functions**; `demos/demo_dream.py` —
  (i) a pattern in 3 dream/0 real is **mined but REFUSED**, then flips to
  admitted when hand-added to 2 real; (ii) perturbing the dream corpus leaves
  the admitted sequence **unchanged**; (iii) a dream file seeded as real with
  no committed byte-match **hard-errors** at `ledger seed-readings`; full
  suite green.
- **Payoff measurement:** the witness teeth are **correctness/soundness**
  measurements (refusal is the payoff), recorded by `demo_dream.py`'s capture
  — a dream-only pattern that stays refused is the measured property. The
  fan-out cost of the *dream-live* variant is measured by
  `bench/bench_speculate.py` (Z3-14). Not asserted.
- **Hazards bound:** H6 (witness discipline is **gate AND objectives**); H55
  (provenance is `demand.origin`, **not the path**); H44 (enforcement at the
  seed step — dream-as-real without byte-match hard-errors); H7
  (self-witness residue: S3-authored variants have no demand row, so log
  `self-witness` if any path ever mints one); freeze **Z-E** (scope widened
  to all three functions), **Z-D** (`self-witness {macro, reading_sha}`
  event).
- **Z1 (explicit):** a dream Reading is a **proposal that may not witness**;
  only exogenous-origin readings enter any objective — dreams can *propose*
  vocabulary but never *justify* its admission.
- **Status on tree:** **Satisfied** — `witness_filter` in `recurrence.py`
  (mine/gc_macros/gc_table), `tests/test_witness_filter.py`,
  `tests/test_witness_live.py`, `demos/demo_dream.py`, `specs/readings/dream/`
  committed.

### Z3-14 — S5.1 dream-live (SPECULATION WP-N; LLM, skippable)

- **Entry predicate:** Z3-09 (speculate executor) **and** Z3-11 (witness)
  shipped.
- **Work:** `buildloop/dream.py` — LLM paraphrases/domain-variants → Readings
  via the S4 executor → files in `specs/readings/dream/`, **seeded with
  system-origin demand rows** (H55).
- **Exit teeth:** `tests/test_witness_filter.py`/`test_witness_live.py` remain
  green with real dream files; full suite green. **LLM-requiring → skippable
  with an honest SKIPPED note when no key.**
- **Payoff measurement:** `bench/bench_speculate.py` (the fan-out that
  authored the dreams) — measured, not asserted; skippable.
- **Hazards bound:** H55 (system-origin seed); H44 (seed-time enforcement);
  freeze **Z-E**.
- **Z1 (explicit):** dreams **propose**; the witness filter (Z3-11) already
  guarantees they never witness.
- **Status on tree:** **Satisfied** (code) — `buildloop/dream.py` committed;
  the **live** LLM generation is the honest skippable residual.

### Z3-15 — S5/S4 docs + captures + benches (SPECULATION WP-O)

> The **merge-owned, single-commit** package: it is the only cycle permitted
> to touch merge-owned surfaces (README Zone-3 section, `TRUST.md`).
- **Entry predicate:** every prior package shipped and green.
- **Work:** ONE commit — README Zone-3 section; **TRUST amendment (H58
  wording + the H10 stage-4 rank-only caveat / TRUST 3.4)**; committed
  captures; then **both benches** (`bench/bench_speculate.py` and the S4
  bench capture), **skippable with an honest note**.
- **Exit teeth:** full suite green; README/TRUST edits are documentation
  (no trusted-surface growth — the H58 amendment **documents** the landed
  rung, it does not invent trust); benches captured or honestly SKIPPED.
- **Payoff measurement:** `bench/bench_speculate.py` final capture →
  `results/speculate_bench.csv`; **the whole point of the bench is to record
  the measured trade** (H8/H43), never to claim it pays.
- **Hazards bound:** H58 (TRUST amendment **documents rather than invents** —
  see the quoted rung premise above); H10 (TRUST 3.4 caveat); H43 (bench
  skippable). Per CLAUDE.md the TRUST edit here is the *documentation* half;
  any change to a `TRUST.md` **pin** or the anti-list is out of scope and
  requires the PLAN_REFLECT ceremony with user sign-off.
- **Z1 (explicit):** the captures record proposals-and-verdicts side by side;
  no capture is itself a certificate.
- **Status on tree:** **Open by design** — benches are LLM-requiring and
  skippable; the README/TRUST documentation is the shippable half and should
  be verified present.

---

## Cycle order (the driver's queue)

```
S0:  Z3-01 (WP-A) → Z3-02 (WP-B) → Z3-03 (WP-C)
S1:  Z3-04 (WP-D) → Z3-05 (WP-E) → Z3-06 (WP-F) → Z3-10 (WP-J)   ← critical path
S2:  Z3-07 (WP-G)
S3:  Z3-08 (WP-H) → Z3-13 (WP-M, needs Z3-10 + Z3-12)
S4:  Z3-09 (WP-I) → Z3-12 (WP-L, needs Z3-08)
S5:  Z3-11 (WP-K) → Z3-14 (WP-N) → Z3-15 (WP-O, needs all)
```

Critical path (SPECULATION's own): `{Z3-01,Z3-04,Z3-05,Z3-06} → Z3-10 →
Z3-13 → Z3-15`. Every arrow is a green, shippable boundary; full suite green
is the exit tooth of each node.

**Package count per phase:** S0 = 3 (Z3-01/02/03); S1 = 4 (Z3-04/05/06/10);
S2 = 1 (Z3-07); S3 = 2 (Z3-08/13); S4 = 2 (Z3-09/12); S5 = 3 (Z3-11/14/15).
**Total = 15**, one per SPECULATION WP A–O.

---

## Where the spec was too ambiguous to slice cleanly (named, not papered over)

1. **Wave→cycle granularity is lossy for the bundled WPs.** SPECULATION WP-G
   (all of S2), WP-I (all of S4-minus-bench), and WP-J (S1.3+1.6+1.7+demo)
   each bundle 3–5 sub-deliverables that **co-edit one exclusive file**. The
   green-tree + exclusive-file rules make them **irreducibly one driver
   cycle** — they cannot be sub-sliced without leaving `recurrence.py` /
   `loop.py` / `dl.py` half-written across a boundary. Z3-07, Z3-09, Z3-10 are
   therefore larger than a "minimal" cycle by necessity, stated rather than
   forced smaller.

2. **Payoff is a *tie class*, not a strict win, in two packages, and the spec
   says so.** S1.4 part_a: *"an honest tie on the natural corpus is a
   finding"* (H24) — Z3-10's exit tooth is relational (searched ≤ greedy) plus
   the recorded `strict_divergence` flag, **never a mandated strict win**.
   S3.2/S3 part_a: *"transition targets are DL-invariant, the argmin is a tie
   class"* (H37) — Z3-08/Z3-13 cannot demand a unique winner. Any slicing that
   asserted a strict payoff here would be dishonest; the packages record the
   tie.

3. **S2's absolute numbers were declared unreproducible by the spec itself.**
   H52: the old 10-vs-11 / 316.6-vs-318.8 figures *"do not reproduce on this
   tree"* and *"the recipe itself was underdetermined by the old text."*
   Z3-07 therefore pins the replay recipe **in code** and asserts **only
   relational teeth**. The exit tooth cannot be an absolute constant — this is
   the spec disowning its own earlier numbers, carried forward honestly.

4. **`metrics/run_experiment.py` ownership is contested.** H53's fix edits a
   file SPECULATION's draft declared **unowned**; the spec attaches an
   *"integrator escalation note"* to it. Z3-07 carries that escalation flag
   explicitly — a driver cycle touching `run_config` must record the
   escalation, because the file-ownership matrix does not cleanly grant it.

5. **Two packages have LLM-conditional exit teeth (S4/S5 benches, S5.1
   dream-live).** SPECULATION marks them *"last and skippable with an honest
   note."* A driver cycle with no API key records **SKIPPED as a green exit**
   — the plan cannot make these hard-green, and pretending otherwise would
   force a false red on every keyless CI run. Named as conditional, per H43.

6. **Fixture location (Z3-06) is under-pinned by the tree.** SPECULATION WP-F
   names `tests/fixtures_macro_corpora.py`, but on this tree the trap/
   incompressible corpora appear folded into `results/macro_search.csv` and
   the demo, with no standalone fixtures module observed. The package's exit
   tooth is stated conditionally — add the module if absent, else record the
   demo-inlined corpora — rather than assuming a satisfied state that the
   committed listing does not confirm.
