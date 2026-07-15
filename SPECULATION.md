# SPECULATION.md — Zone 3: the speculative planner (post-sweep)

README.md says what the system is. TRUST.md says what is trusted. ROADMAP.md
says what gets built toward the two-zone economy. This document specifies a
third zone: **the speculative planner** — the layer that decides what the
expensive machinery spends itself on, by consulting the system's exact
description-length accounting *before* paying for LLM calls and kernel
invocations rather than after.

It is written to be executed by a swarm of builder agents **without access to
the conversation that produced it**. It carries the interface freezes, the
file-ownership rules, the teeth criteria per phase, and a hazards section
(marked ⚠) populated by a **five-agent adversarial sweep** of the draft
against the actual codebase (lenses: codebase reality, algorithmic
feasibility, trust/Goodhart, economics/measurement, builder-executability).
Every ⚠ below was verified by the sweep with file:line evidence or by
executing an experiment against the live modules; findings are folded into
the phase text and cross-referenced in the Hazards ledger at the end.

## What the system does (behavioral description)

Today every scarce resource is spent reactively:

- the build loop (`buildloop/loop.py:run_iteration`, line 166) picks one
  coverage-miss group by `frequency` or one-step `closure`, asks the LLM for
  one candidate, and submits it to the full admission stack — up to
  `MAX_ROUNDS = 5` serial round-trips;
- the synthesis loops (`buildloop/service_loop.py:synthesize_semantic` at
  252 / `synthesize_service` at 306) do the same at the service rung: one
  Reading or meta-spec per round, full certification stack per round;
- macro admission (`buildloop/mdl_macros.py:macro_admission_decision`, line
  178) is *reactive*: it evaluates one already-proposed macro against the
  corpus, greedily, in arrival order.

The speculative planner replaces "spend, then observe the price" with
"simulate the price, then spend". Concretely, after all phases land:

1. **Given a corpus of Readings**, the planner *mines* candidate macros
   mechanically (anti-unification over statement windows — no LLM) and
   *searches* over admission sequences, scoring each future with the exact
   `corpus_dl` function, then admits the best sequence — each step still
   passing the unchanged per-macro MDL gate. Compression of the Reading
   vocabulary stops being hostage to what happens to get proposed, in the
   order it happens to arrive. ⚠H1: mined macros are **accounting-only**
   vocabulary (they compress the ledger, not any certified artifact) until a
   future reading actually *invokes* them — see S1.3.
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
   design that entails every demanded ordering — Occam applied to the
   pragmatic residue, mechanically forbidden from overriding the text.
4. **Given a request**, the synthesis loop fans out K candidate Readings,
   runs cheap deterministic pre-gates on all of them, and submits only the
   best-scoring survivor to the expensive dual-checker stack. ⚠H8: the
   repo's own captures show most requests certify in 1–3 rounds and the one
   documented hard failure is invisible to every pre-gate, so K-wide fan-out
   is expected **flat-to-worse on LLM calls** — S4 is specified as a
   *measured trade* (wall-clock and verifier-seconds vs. LLM spend) with the
   divergence ledger quantifying pre-gate blindness, not as a promised
   saving.
5. **Between requests**, a dream loop generates synthetic requests
   (paraphrases and domain variants of `specs/requests/`), synthesizes
   Readings for them offline, and feeds the *mining* stage — under a strict
   witness discipline: dreamed readings may propose macros; only real
   readings witness them, and (⚠H6) only real readings may appear in any
   admission *objective*, not just the gate.

## Trust posture (read this before writing any code)

The planner is **untrusted-by-construction, exactly like the LLM**. Every
house rule of ROADMAP.md binds here; three planner-specific rules are added:

- **Z1 — proposals only.** No planner output is ever a certificate or a
  verdict, and no cache entry read by a verdict may exist unless it was
  computed **by the unchanged kernel on the identical (artifact, contract)
  identity** that the non-speculative path would have used. (⚠H9: the
  draft's stronger wording — "no cache entry that a verdict reads" — was
  violated by its own S4.3 warming; this is the honest restatement. Warmed
  entries are kernel-computed and content-addressed, so the served verdict
  equals the fresh one; what warming changes is *when* the kernel ran, never
  *what it concluded*.)
- **Z2 — exact objectives first.** Phases S1–S3 may only score with the
  exact pure functions (`mdl.total_dl`, `mdl.chain_length_for`,
  `mdl_macros.corpus_dl`, deterministic compile + reference replay). Learned
  or heuristic scores are confined to S4/S5 and must ship with the
  divergence ledger in the same commit. ⚠H2: "exact" means exact *as
  bookkeeping*: `corpus_dl`'s matcher is force/quote-blind, so a simulated
  compression is not always realizable as a legal macro invocation — S1
  restricts what the miner may count (uniform-(force, quote) windows) so
  that the simulated price never claims savings no certified reading could
  realize.
- **Z3 — measured fidelity.** Any component that *predicts* a kernel or gate
  verdict (S4 pre-gates) logs prediction-vs-actual as a first-class
  `speculation-divergence` event via the existing `registry.log_event`
  mechanism (`library/__init__.py:208`; queryable with `cgb.py events`,
  `cgb.py:359`). A rising divergence rate is a defect, not a tuning knob.

No phase in this document adds a kernel contract. House rule 6 (five
touchpoints) never fires. `kernel/__init__.py`, `kernel/backends.py`,
`generators/service_gen.py`, `generators/reading.py`,
`generators/reading_compile.py`, and `run/semantic.py` are **read-only** for
all of Zone 3 — but *calling* kernel-backend machinery read-only
(`SmtBackend.run_z3`, `HypothesisBackend.check_intent_reference`) for
pre-gate predictions is permitted and is the intended route (⚠H12).

⚠H5 (TRUST.md lane): TRUST 1.2k classifies the macro table as "a checker
input, like the reference codec" — i.e. by-fiat: small, fixed, audited,
hand-written. S1 mints tables *mechanically from corpus data* (and after S5,
from a corpus partially authored by the LLM). S1's final commit therefore
lands a TRUST.md amendment: **a mined macro table is NOT a by-fiat checker
input; it is untrusted, data-derived vocabulary whose every actual use is
certified per-reading by `macro-expansion-cert`, with the inlined comparand
required to originate independently of the table (hand-written or
pre-macro-form) — never derived by expanding the invocation under test**
(that derivation would make channel 1's compile-identity a tautology).
TRUST.md joins the ownership matrix (merge-owned).

## Phases

Logical dependencies (⚠H13 — corrected by the sweep: S2 depends on S1.1,
not merely S0, because it consumes `planner/search.py`):

```
S0 (corpus provisioning) ──▶ S1.1 (search skeleton, freezes Z-A) ──▶ S2
                                 └──▶ S1.2–S1.6 ──▶ S3 ──▶ S4 ──▶ S5
S1.2–S1.6 ∥ S2 (disjoint files after S1.1 lands)
```

The phases define WHAT lands and its acceptance. The **Parallel execution
plan** section below decomposes them into work packages so a builder swarm
runs at maximum width — the phase graph above is the *logical* order;
almost none of it is a *scheduling* order once the interface freezes are
fixed, because consumers code against frozen signatures, not against the
producer's landed code.

### S0 — Reading-corpus provisioning (small; land alone, first)

⚠ There is no persisted Reading corpus: `specs/` has no `readings/`
directory; `demo_macros.py:108` (`CORPUS`) holds *parameter dicts*, not
Readings — the actual readings come from `_reading(**c)` at
`demo_macros.py:68`. `specs/requests/` holds 20 raw request texts.

- **S0.1** New directory `specs/readings/`: one JSON file per corpus entry,
  `{request: str, reading: {service, statements: [...]}}`. Bootstrap:
  - the three `demo_macros.py` corpus entries in **inlined form** —
    `_reading(**c)[0]` paired with `c["request"]` (⚠H14: the macro form
    does not even parse without a table; export the inlined form only);
  - hand-written Readings for the **named faithful set**: requests 01, 02,
    03, 04, 05, 06, 09, 14, 15, 17, 18 (⚠H15 — the sweep checked all 20:
    these 11 transcribe faithfully within the frozen fragment; the temporal
    LF kinds needed by 03/09/17 already exist in `reading.LF_KINDS`).
    Requests 07, 08, 10, 11, 16, 19 are **excluded or explicitly marked
    lossy**: the fragment cannot express disjunctive eventuality (07/16/19),
    trigger-relative deadlines (08 — LF `within` is session-start-relative,
    `reading.py:112`), or sub-case nesting (10/11). A lossy transcription
    bakes in a dodge, and S1 would then mine the transcriber's dodges as
    "idioms" — exclude by default. Vague requests 12/13/20 are excluded:
    hand-writing their Readings bakes in choices S3 exists to search.
  - Every entry must pass `parse_reading` (`generators/reading.py:264` —
    which enforces groundedness, one-lifecycle, one-transition-per-action,
    and the ≥1-demanded-obligation rule) with **no LLM** involved. Corpus
    entries are required to parse and ground only; the three demo exports
    must additionally certify (they are S3 part_a's raw material).
- **S0.2** `buildloop/reading_corpus.py` (⚠H16: NOT `corpus.py` — "corpus"
  already means the failing-input corpus throughout the codebase, cf.
  `registry.corpus_inputs`, `use_corpus`, M8):
  `load_readings(dir) -> list[CorpusEntry]` where `CorpusEntry` is a **new
  dataclass `(request, statements, source)`** — ⚠H17: do NOT return
  `reading.Reading` objects; `Reading.source` already holds the raw JSON
  text (`reading.py:495`), and reusing it would silently zero every S5
  witness count. `source ∈ {real, dream}` is **inferred solely from path**
  (`specs/readings/*.json` = real; `specs/readings/dream/*.json` = dream;
  loader recurses exactly one level); no `source` key appears in files.
  The loader validates every entry through `parse_reading` at load time — a
  non-parsing entry is a hard error, not a skip.
  **Single-writer rule:** this module is written ONCE, complete, by its
  work package — no later phase edits it. That means it ships from the
  start with: the dream-directory recursion; the H44 provenance enforcement
  (a real-classified entry whose request text does not byte-match a file
  committed under `specs/requests/` is a hard error); and `load_macros()`
  (the accessor for S1's persisted table, see S1.3) which reads
  `specs/macros.json`, returns `{}` when the file is absent, and excludes
  entries flagged `"retired": true`.
- **Done when:** the loader returns ≥ 14 readings; `tests/test_reading_corpus.py`
  asserts every entry parses and grounds; `run_regression.py --fast` stays
  < 90 s (new tests are auto-collected — `run_regression.py:106` runs
  `pytest tests/` wholesale; do NOT touch `FAST_DEMOS`, ⚠H18).

### S1 — Macro mining + admission-sequence search (the core)

New files: `planner/search.py`, `buildloop/macro_mine.py`,
`specs/macros.json`, `demo_macro_search.py`, `tests/test_macro_search.py`,
`results/macro_search.csv`, `results/macro_search_demo.txt`.

- **S1.1 Search skeleton** (`planner/search.py`). One generic beam search:
  `beam_search(initial, expand, score, *, beam_width, max_depth) -> best`
  where `expand(state) -> [state]`, `score(state) -> float` (lower better),
  fully deterministic (ties broken by canonical-JSON of the state — mirror
  the planner's hash tie-break discipline, `planner/__init__.py:10`). No
  randomness, no clocks. ⚠H19: `beam_search` returns the best state **ever
  visited**, not the best at max depth — both DL objectives are
  non-monotone in admissions (every admission adds a definition/generator
  cost), so the optimum within "≤ depth" steps may be at depth < max.
  Frozen after landing (Z-A); S2 starts here.
- **S1.2 Anti-unification miner** (`buildloop/macro_mine.py`).
  `mine(readings, *, max_body=3, max_params=4) -> [candidate macro dicts]`.
  For every pair of same-length statement windows (length 1..max_body)
  across the corpus, compute the least-general anti-unifier of their lf
  sequences: structurally equal nodes stay concrete; mismatched positions
  become `"$p<i>"` placeholders (consistent: the same concrete pair maps to
  the same placeholder). Because `_unify` requires equal dict key-sets and
  list lengths (`mdl_macros.py:88,92`), generalization happens only at
  whole-subtree positions — dicts with different key-sets collapse to one
  placeholder. Dedup by canonical JSON; names are `mined_<sha8>`
  (content-addressed).
  **Candidate filters (⚠H3 — load-bearing, sweep-verified):**
  - reject any candidate in which **any body statement is a bare
    placeholder**, and require each body template to keep ≥ 60% concrete
    nodes (a minimum concrete/placeholder ratio). Verified failure without
    this: the wildcard `["$p0", "$p1"]` matches every length-2 window, and
    because `dl_invocation` prices an argument at 1 token regardless of the
    bound subtree's size, the real gate admits it on an **all-distinct**
    corpus (measured: `dl_before=144.0, dl_after=31.0, delta=-113.0`) —
    wildcards would dominate every search and falsify part_c.
  - mine only windows with **uniform (force, quote)** (⚠H2/H4): an actual
    macro invocation is ONE statement whose expansion stamps a single
    inherited force+quote on every body statement
    (`generators/reading.py:183-205`); a mixed-force or mixed-quote window
    "compresses" in the arithmetic but is unrealizable as a legal macro-form
    reading (choice must quote nothing, `reading.py:328`; obligations may
    not be choices). The simulated price must never count savings no
    certified reading could realize.
  - Round-trip regression: for every mined candidate, `_match_at`
    (`mdl_macros.py:98`) matches it back against BOTH source windows with
    full bindings.
- **S1.3 Admission-sequence search.** State = (macro table so far, admission
  sequence); expand = admit any mined candidate that **passes the unchanged
  `macro_admission_decision` against the table-so-far**; score = final
  `corpus_dl(readings, table)["total"]`. Defaults beam 8, depth ≤ 5,
  overridable via `demo_macro_search.py --beam/--depth` only (no `cgb.py`
  subcommand, ⚠H20). The gate is the arbiter at every step (Z1); the search
  only chooses *which* admissible sequence to take.
  **Persistence (⚠H21 — the draft left the table homeless):** the winning
  table is written to `specs/macros.json` as `{name: {name, params, body}}`
  in canonical JSON — owned N by S1, read-only for S3/S4/S5;
  `reading_corpus.load_macros()` is the single accessor.
  **Certification status (⚠H1):** mined macros are accounting-only.
  `_reading_stats` rewrites the statement stream *virtually, for DL
  bookkeeping* — corpus files stay inlined and no certified artifact
  changes, so admission itself creates nothing to certify. The
  `macro-expansion-cert` obligation attaches when a future reading is
  *authored in invocation form* (the existing, unchanged path — obtained
  explicitly by the caller as `demo_macros.py` part B does; ⚠H22: nothing
  in `certify_reading` auto-enforces it, so the demo must invoke
  `kernel.check(..., {"type": "macro-expansion-cert", ...})` itself), with
  the inlined comparand originating independently of the table (H5).
- **S1.4 Teeth** (`demo_macro_search.py`, `REQUIRES_LLM = False`, captured
  to `results/macro_search_demo.txt`):
  - *part_a*: greedy arrival-order baseline vs searched sequence on the S0
    corpus; searched final DL ≤ greedy under every tested arrival order —
    the sorted candidate-name order, its reverse, and the N rotations of the
    sorted order (⚠H23: an enumerated, deterministic sample; `random` is
    banned). ⚠H24 (honesty): on a natural corpus of mostly disjoint idioms,
    searched == greedy is the *likely* outcome; the CSV records whether
    strict divergence occurred, and an honest tie here is a finding, not a
    failure — strictness is guaranteed only by part_b.
  - *part_b (the trap — sweep-verified constructible)*: a planted corpus
    where greedy admission of macro A (arrives first, passes the gate)
    makes the strictly-better pair {B, C} inadmissible, while the searched
    sequence admits {B, C}. Executed against the real module during the
    sweep: `none=78.0, greedy/{A}=55.0, searched/{B,C}=35.0`, with B and C
    each individually refused given {A} (`uses=0` — A's longest-body-first
    rewrite consumes their windows, `mdl_macros.py:126-127`). ⚠H25 (design
    constraint): the trap needs pairwise **non-generalizable residual
    windows** (different key-sets, so their only anti-unifier is the
    rejected bare placeholder); with homogeneous residuals, greedy
    self-rescues and the final DLs tie exactly. The wildcard filter (H3) is
    a prerequisite — without it the wildcard scores 31 and hijacks the demo.
  - *part_c*: on a corpus with nothing to compress (all-distinct
    statements), mining returns candidates but search admits **nothing**.
    Only true once H3's filters are in place.
- **S1.5 Measurement**: `results/macro_search.csv` — columns
  `corpus, strategy ∈ {none, greedy, search}, macros_admitted,
  corpus_dl_total, mean_statements, strict_divergence` (⚠H26: named
  `corpus_dl_total`, not `total_dl` — that column name already means the
  codec economy's `mdl.total_dl` in `results/metrics_*.csv`).
- **S1.6 Ablation/retirement pass (⚠H27 — no retirement exists for
  macros):** after each corpus growth, re-run `corpus_dl` with each admitted
  macro ablated; a macro whose removal lowers total DL is retired (kept in
  `specs/macros.json` under a `"retired": true` flag for provenance,
  excluded from rewriting — mirroring `mdl.find_subsumed` + registry
  retirement on the codec side). Without this, a stale macro can
  permanently shadow a better later vocabulary via longest-body-first
  rewriting — the part_b trap re-created by the search's own past output.
- **Done when:** all demo parts pass; round-trip and trap regression tests
  green; CSV committed; the TRUST.md amendment (H5) and a short README
  Zone-3/S1 subsection land as the phase's final serialized commit.

### S2 — Lookahead steering for the build loop (after S1.1; ∥ S1.2–S1.6)

New files: `planner/lookahead.py`, `tests/test_lookahead.py`,
`demo_lookahead.py`. Edits: `buildloop/loop.py:pick_group` gains policy
`"lookahead"` (additive); ⚠H28: `milestones.py:_metrics_run`'s hardcoded
policy tuple (`milestones.py:81`) and `cgb.py build --policy` choices
(`cgb.py:411`) each gain `"lookahead"` — the draft wrongly located the
policy loop in `metrics/run_experiment.py` (which is already
policy-generic); both files are S2-owned **for those lines only**.

- **S2.1** `planner/lookahead.py`:
  `rollout_value(generators, backlog, group, depth) -> float` over **plain
  lists of generator dicts** (`registry.live_generators()` output), never a
  Registry. ⚠H29 (sweep-pinned constraints):
  - **ksy groups only**; abnf groups score +∞ (never preferred). The abnf
    hypothetical needs a `spec_grammar.output` sub-dict and an LLM-authored
    `grammar_js` — not mechanically constructible; ksy is
    `emit_entrypoint={"kind": "ksc-python-rw"}` verbatim from
    `admission.candidate_entry_from_spec` (`buildloop/admission.py:35-72`),
    whose field shapes the hypothetical must copy exactly so
    `generator_dl` prices what the eventual real candidate would cost.
  - `atoms_union` is a set and `common.canonical_json` is bare `json.dumps`
    (`common.py:64`) — **`sorted(...)` before constructing** the
    hypothetical (as `admission.py:41` does).
  - Miss-set recomputation after a hypothetical admission is a **plain-dict
    mirror of `group_misses` + the min-remainder rule** using
    `mdl.chain_length_for(gens, s.language, s.atoms) is None` for
    coverage — never `planner.plan`, whose candidate sort reads
    `l["tier"]`/`l["generator_hash"]` and would KeyError on a hypothetical
    entry (`planner/__init__.py:108-111`).
  - Value = best `total_dl` ever visited within `depth` hypothetical
    admissions (H19), searched with `planner/search.py`.
- **S2.2** Steering: groups are dicts (`g["atoms_union"]`, not attribute
  access); rank with
  `min(groups, key=lambda g: (rollout_value(...), "".join(g["missing"])))`
  (⚠H30 — the existing line 133 is a `max` comparator; lower-DL-wins needs
  `min` with the same tie string).
- **S2.3 Teeth** (`demo_lookahead.py`, `REQUIRES_LLM = False`):
  - *part_a (planted)*: a backlog constructed in the demo where `closure`
    picks a dominated miss while depth-2 lookahead picks the group whose
    resolution makes one follow-up admission cover everything; assert final
    `total_dl` (lookahead) < final `total_dl` (closure). ⚠H31 (replay
    semantics pinned): both futures are replayed with
    `mdl.total_dl`/`chain_length_for` over plain generator-dict lists; the
    closure future's picks re-run `closure_gain`'s formula against those
    lists, not against a Registry.
  - *part_b (real backlog, sweep-measured)*: hypothetical replay on the
    actual 185-spec M5 ksy backlog. The sweep ran this economy: closure and
    depth-2 lookahead pick the **same first group**; closure reaches full
    coverage in 11 hypothetical admissions (final DL 318.8), lookahead in
    10 (316.6); at an equal 10-admission budget: 316.6/185-covered vs
    461.6/182-covered. The demo reproduces these numbers as the honest
    natural-corpus signal: a ~1-admission, ~0.7%-DL late-trajectory edge,
    no first-move divergence.
- **S2.4 Measurement**: third policy curve via the (already policy-generic)
  `metrics/run_experiment.py:run_config` + `metrics/plots.py:reach_vs_cost`
  over all CSVs; outputs generated under `artifacts/` (`CGB_ARTIFACTS`) and
  copies committed to `results/` per METRICS.md convention (⚠H32 — nothing
  currently regenerates `results/reach_vs_cost_all.png`; the "all" plot is
  produced by calling `metrics.plots.reach_vs_cost` with all curve CSVs).
  ⚠H33 (expectation set honestly, sweep-measured): in live M5 runs the LLM
  overshoots the group union and closure saturates in ~2 admissions
  (`results/metrics_closure_corpus.csv`), so the live third curve is
  **expected to coincide with closure** — it is captured as an honesty
  result; the tooth is part_a, the natural-corpus signal is part_b. Live
  runs need the claude CLI and are the phase's last, skippable-with-honest-
  note step; the demo teeth are not skippable.
- **Done when:** demo parts a+b green (strict inequality in part_a; the
  measured 10-vs-11 replay in part_b); `pick_group` policy test green; no
  change to `frequency`/`closure` picks on the existing recorded backlogs
  (regression-compared).

### S3 — Choice-space search (min-DL design that entails the demands)

New files: `planner/choices.py`, `demo_choice_search.py`,
`tests/test_choice_search.py`. Calls (never edits)
`generators/reading_compile.py`, `generators/service_gen.py`,
`kernel/backends.py`.

- **S3.1** `planner/choices.py`: `enumerate_choices(reading, *, budget) ->
  [reading]`. Vary ONLY statements with `force == "choice"` — the
  choice-only LF kinds are exactly `lifecycle`, `transition`, `input`, plus
  choice-force `action` (`reading.py:116-128`). ⚠H34 (pinned constants):
  template family = lifecycles `{[open, closed], [open, active, closed]}`
  with transitions restricted to forward/self edges; auxiliary actions
  on/off. Demands and presuppositions are copied byte-identically
  (test-pinned). Every variant must (a) pass `parse_reading`, (b) survive
  the **order-entailment check** in `compile_reading`
  (`generators/reading_compile.py:100-120` — ⚠H35: this is the real,
  narrower name of the draft's "choice⊨demand gate": it checks demanded
  `order` statements against the chosen transition graph and raises
  `CompileError`; other choice-vs-demand conflicts surface later, in the
  expensive stack). Variants refused by (b) are counted, then discarded.
  ⚠H36 (non-vacuity filter): discard variants whose
  `reading_compile.entailed_scenarios(model, reading)` returns `[]` — a
  transition graph with no legal golden run passes replay vacuously and
  would tie the DL of sound designs, letting the tie-break crown a dead
  service.
- **S3.2** Scoring: compile each surviving variant
  (`compile_reading`, returns `(spec_text, provenance)`), replay its
  entailed scenarios through the reference interpreter — ⚠H12: composed
  from `service_gen.emit_service` + `build_scenario_reference_harness`
  (`service_gen.py:954`) + `HypothesisBackend.check_intent_reference`
  (`kernel/backends.py:243`), NOT `run/semantic.py`, which has no
  reference-only path; this costs compile + emit + one sandbox run per
  variant (the most expensive pre-certification step, still ≪ the full
  stack) — and score by `mdl_macros.dl_reading(reading, table)` with the
  admitted table from `reading_corpus.load_macros()`, plus the compiled
  spec's size proxy `len(common.canonical_json(spec)) / 64.0` (H34).
  Deterministic tie-break by compile-hash (⚠H37, honesty: transition-target
  choices are DL-invariant — same leaf count regardless of targets — so the
  argmin is a tie class resolved by hash; the demo states this rather than
  pretending the objective discriminates them). When dream entries are
  loaded, the DL score uses the real-only sub-corpus (H6).
- **S3.3 Teeth** (`demo_choice_search.py`):
  - *part_a* — ⚠H4 (the draft's version was **analytically impossible**:
    with demands copied byte-identically and a demand-cluster macro, the
    macro-aware score equals the flat score minus a constant, so the argmin
    cannot move). Respecified: the admitted idiom is a **structural
    choice-tail macro** (the `close_out`/`open→closed` tail that recurs
    modulo one name across the corpus — uniform force=choice, empty quote,
    so invocation form is coherent per H2). Flat scoring picks the minimal
    bare tail; macro-aware scoring picks the idiomatic tail (collapsed to
    one cheap invocation). Assert the two argmins differ, the macro-aware
    winner uses the idiom, and both winners certify — the demonstration
    that admitted vocabulary genuinely reshapes design preference.
  - *part_b*: a planted variant family where the globally minimum-DL design
    violates a demanded **ordering** (an `order` demand must be planted —
    `12_venue_vague.txt` yields none, H35); assert it is refused by the
    order-entailment check and the search returns the best *admissible*
    design. Occam never overrides the text.
- **Done when:** both parts green; `tests/test_choice_search.py` pins that
  `enumerate_choices` never mutates demand/presupposition statements
  (byte-compare) and that empty-scenario variants are discarded.

### S4 — Speculative synthesis executor + divergence ledger

New files: `buildloop/speculate.py`, `demo_speculate.py`,
`tests/test_speculate.py`, `bench_speculate.py`. Edits:
`buildloop/service_loop.py` (fan-out entry point, additive flag).
⚠H38: the divergence ledger is **events-table-only**
(`registry.events("speculation-divergence")`); `library/__init__.py`'s
`_SCHEMA` and the `metrics_log` columns are untouched. ⚠H39: `metrics/`
edits are serialized with S2's — S4 rebases on S2's landed changes, never
concurrent.

**Premise, restated honestly (⚠H8, sweep-measured):**
`results/synthesize_demo.txt` certifies in 1 round; `results/semantic_synth.txt`
in 3; the temporal run never certifies and fails at the protocol-cert
stranding check — a stage all four pre-gates are blind to. Therefore: k>1 is
pure LLM cost on 1-round requests; fan-out converts serial rounds to
parallel ones only when failures are pre-gate-visible; and no k rescues
pre-gate-invisible failures. S4's deliverable is the **measured trade** —
`llm_calls_to_certify` (expected flat-to-worse), `rounds_to_certify` and
wall-clock (possibly better), per-stage failure attribution of losers — plus
the ledger that quantifies pre-gate blindness. The cache-warming latency win
stands on its own.

- **S4.1** `speculate.fan_out(request, k, *, model) -> [candidate]`: k
  LLM-authored Readings per round; `llm.call_llm(prompt, model, timeout)`
  has no temperature knob (`buildloop/llm.py:41`), so diversity comes from a
  per-candidate "consider an alternative design" preamble indexed by
  candidate number. `--spend` caps total LLM calls per request; k=1
  preserves today's behavior. ⚠H40 (k=1 regression pinned): monkeypatch
  `buildloop.llm.call_llm` with a canned Reading transcript and assert the
  sequence of (prompt, kernel cache_key, event) tuples is identical between
  `synthesize_semantic` and the flagged path.
- **S4.2** Pre-gates, cheapest first, composed from real machinery (⚠H12):
  1. `reading-gate` — `parse_reading` (groundedness is inside it; one
     stage, matching `run/semantic.py`'s stage labels, ⚠H41);
  2. quick-SMT demand-consistency —
     `SmtBackend().run_z3(reading_compile.demands_smt(r), expect="sat")`
     under `common.SMT_LOCK` (there is no pre-existing "quick" helper; the
     full contract is the dual-solver `reading-consistency`);
  3. compile (`compile_reading`; `CompileError` = refused);
  4. entailed-scenario replay on the reference interpreter only (the H12
     composition).
  Score = (stage reached, then the Z-F scorer — `speculate.py` ships with
  the flat-score fallback and gains the real S3 scorer at the WP-L seam
  swap, so S3 and S4 never block each other). The winner goes to the full
  stack. ⚠H10 (Goodhart on the reference channel — sweep finding): stage 4
  replays through the SAME reference that later serves as one channel of
  the `intent-scenarios` and composition differentials
  (`run/semantic.py:150-167`, TRUST 1.2d) — selecting BY reference
  agreement makes that channel pass by construction for winners and
  converts reference bugs from logged disagreements into silent pre-gate
  rejections, eroding the N-version evidence exactly as TRUST 3.4 warns.
  Mitigations, all three mandatory:
  (a) stage 4 is **rank-only, never reject** — a candidate never dies by
  reference replay; the ledger records what it *would* have rejected;
  (b) a deterministic every-Nth-loser audit (by candidate_sha) runs the
  full stack **on by default**, so reference-vs-dispatcher splits on losers
  keep feeding `dual-checker-disagreement`;
  (c) the run record carries a claim
  `("selection", "reference-replay-ranked, k=N")`, and S4's final commit
  adds the corresponding TRUST 3.4 caveat.
- **S4.3** Cache warming, redefined post-sweep (⚠H9): warming begins only
  **after a candidate compiles** (post-stage-3) and runs on the main thread
  through the real `certify_service`/`_build_jobs` path
  (`run/service.py:54,90-160`) — the registry's SQLite handle is
  single-threaded, and there is no per-obligation entry point to
  reimplement (house rule 8: reuse the exact job-construction path, never a
  copy). Warmed sub-certificates (per-tool, per-constraint) are REAL
  kernel-computed, content-addressed cache entries; if the warmed candidate
  loses, they persist. Accordingly the loser claim is scoped: **no composed
  service/semantic certificate is ever minted for a loser**; warmed
  sub-certificates are inventoried in the divergence ledger. Warming may
  also surface `dual-checker-disagreement` events on artifacts the
  non-speculative path would never have checked — the ledger records which
  events arose under warming so the two paths' event streams stay
  comparable.
- **S4.4** Divergence ledger: log `speculation-divergence`
  `{stage, direction ∈ {false-accept, false-reject}, candidate_sha,
  request_sha}` for (i) every winner that passed all pre-gates then failed
  the full stack, (ii) every audited loser that passes the full stack.
  `cgb.py events speculation-divergence` lists them.
- **S4.5 Teeth** (`demo_speculate.py`, `REQUIRES_LLM = False`, captured to
  `results/speculate_demo.txt` — planted candidates are hand-written, like
  `demo_reading.py`'s misreadings): a planted Reading that satisfies
  pre-gates 1–3 but fails the dual-BMC stack — the inverted-verb-effect
  class, which the committed capture shows is caught at
  `stage='protocol'` by the BMC's unconstrained-argument adversary
  (`results/reading_demo.txt:30`). ⚠H42 (verify before promising): whether
  stage-4 replay *also* catches an inverted effect is untested — entailed
  scenarios plausibly lack the adversarial negative argument, but the demo
  must first assert stage 4 misses it (if replay catches it, pick a
  temporal-stranding-class plant instead, which no pre-gate can see).
  Assert: the divergence event is logged; no composed certificate exists
  for the plant.
- **Bench** (`bench_speculate.py` → `results/speculate_bench.txt`):
  `llm_calls_to_certify`, `rounds_to_certify`, wall-clock, and per-stage
  loser attribution for k ∈ {1, 3, 5} on ≥ 3 requests from
  `specs/requests/`. ⚠H43: requires the claude CLI and a real token budget
  (worst case ≈ 3 × 5 × 5 × ~35k ≈ 2–3M tokens + audited losers); it is
  the phase's **last, skippable-with-honest-note step** — the teeth and the
  k=1 regression are not skippable.
- **Done when:** k=1 regression green; teeth green with the H42 check;
  ledger queryable; bench captured or honestly skipped.

### S5 — Dream corpus under witness discipline

New file: `buildloop/dream.py`, `demo_dream.py`,
`tests/test_witness_filter.py`. Edits: `buildloop/mdl_macros.py` gains
OPTIONAL `witness_filter=None` (Z-E; default-`None` behavior
regression-pinned). The dream-directory handling and H44 enforcement
already live in the S0 loader (single-writer rule) — S5 only *writes
files* into `specs/readings/dream/`, never the loader.

- **S5.1** `dream.py`: LLM paraphrases/domain-variants of `specs/requests/`
  texts → synthesized Readings via the S4 executor → stored in
  `specs/readings/dream/` (source inferred from path, H17). Dreams are
  *data with provenance*, like incumbent input — the LLM authors
  requests-as-text and Readings-as-specs, never code (house rule 5 intact).
  ⚠H44 (provenance is fiat-by-directory — hardened): the loader enforces
  that a `real` entry's request text matches a file committed under
  `specs/requests/` byte-for-byte; a real-classified entry with no matching
  committed request is a hard error. (A dreamed reading later duplicated by
  a genuine committed request legitimately becomes real evidence.)
- **S5.2** Witness discipline (the honesty core), extended by the sweep from
  the gate to the **objectives** (⚠H6 — ordering contamination): with
  `witness_filter=lambda e: e.source == "real"`, BOTH gate conditions
  (`uses >= 2` and `dl_after < dl_before`) are computed over real readings
  only — AND the S1.3 search score and S3.2 DL score also use the real-only
  sub-corpus whenever dream entries are loaded. Without the objective-side
  rule, dreams still choose *which* admissible sequence wins (greedy
  rewriting makes admissions order-dependent — the part_b mechanism), and
  the final vocabulary becomes a function of LLM taste while every step
  "passes" the real-only gate. Mining (`mine`) runs over real ∪ dream —
  proposing is exactly what dreams are for. Witnesses are counted by
  **distinct real request** (⚠H7); readings authored by S3's own search
  are excluded from witness counts and logged as `self-witness` events —
  the system must not manufacture its own witnesses via the S3 idiom
  feedback loop.
- **S5.3 Teeth** (`demo_dream.py`): (i) a macro pattern planted in 3 dream
  readings and 0 real ones is mined but REFUSED (uses=0 over real); the
  same pattern hand-added to 2 real corpus entries flips to admitted;
  (ii) ⚠H6's tooth: with the objective-side rule active, perturbing the
  dream corpus (add/remove dream entries) leaves the admitted sequence
  unchanged; (iii) the loader hard-errors on a dream file copied into the
  real directory (no matching committed request).
- **Done when:** all three teeth green; `tests/test_witness_filter.py`
  proves default-`None` byte-identical behavior for non-dream callers.

## Parallel execution plan (maximum-width schedule for the builder swarm)

The unit of work is the **work package (WP)**: one agent, one git worktree,
one **exclusive file set** — two packages never write the same file, so
single-writer holds by construction and merges are textual no-ops. The
interface freezes Z-A..Z-F are fully specified in this document, which is
what buys the width: a consumer codes against the frozen signature, not
against the producer's landed code. A builder that believes a freeze must
change **stops and escalates**; it does not edit across the freeze.

### Wave 0 — nine packages, no cross-dependencies (all start simultaneously)

| WP | scope | exclusive files | notes |
|---|---|---|---|
| **A** loader | S0.2 complete (loader + dream recursion + H44 + `load_macros`) + the 3 demo-export readings | `buildloop/reading_corpus.py`, `tests/test_reading_corpus.py`, `specs/readings/{tickets,inventory,booking}.json` | single-writer; ships final interface on day one |
| **B** readings-bounds | 8 hand-written Readings: requests 01, 02, 04, 05, 06, 14, 15, 18 | `specs/readings/<those 8>.json` | validates with `parse_reading` directly — no dependency on A |
| **C** readings-temporal | 3 hand-written Readings: requests 03, 09, 17 (temporal LF kinds) | `specs/readings/<those 3>.json` | the harder transcriptions; same validator |
| **D** search-skeleton | S1.1 (`beam_search`, Z-A) | `planner/search.py`, `tests/test_search.py` | tiny; lands early so G can test |
| **E** miner | S1.2 (anti-unification + H3 filters + round-trip test) | `buildloop/macro_mine.py`, `tests/test_macro_mine.py` | tests on synthetic corpora — no dependency on A/B/C |
| **F** fixtures | the trap corpus (H11/H25 recipe: verified numbers 78.0/55.0/35.0) + the incompressible corpus, as importable test fixtures | `tests/fixtures_macro_corpora.py` | pure data + assertions against the live gate |
| **G** lookahead | all of S2 except the live third curve | `planner/lookahead.py`, `buildloop/loop.py` (`pick_group`), `milestones.py` (policy tuple), `cgb.py` (`--policy` choices), `demo_lookahead.py`, `tests/test_lookahead.py` | codes against frozen Z-A; its test run awaits D's merge (hours, not days) |
| **H** choices-core | S3 minus part_a: enumerator, flat scoring, H12 replay composition, non-vacuity filter, part_b tooth; provides the Z-F scorer | `planner/choices.py`, `demo_choice_search.py`, `tests/test_choice_search.py` | macro-aware behavior enters only at WP-M |
| **I** speculate-core | S4 minus the bench and minus the real scorer: fan-out, pre-gates, rank-only stage 4 (H10 mitigations), warming, ledger, k=1 regression, S4.5 teeth | `buildloop/speculate.py`, `buildloop/service_loop.py` (additive flag), `demo_speculate.py`, `tests/test_speculate.py` | consumes Z-F via the flat fallback; fully self-testable |

**Wave-0 merge order** (one integrator agent, serialized,
`run_regression.py --fast` between each): A, B, C first (corpus), then D,
E, F (pure additions), then G, H, I (rebase onto the corpus+skeleton).
The integrator owns no files.

### Wave 1 — three packages, pairwise file-disjoint (after wave-0 integration)

| WP | scope | needs |
|---|---|---|
| **J** macro-search | S1.3–S1.6: admission-sequence search, `specs/macros.json` persistence, demo parts a–c, `results/macro_search.csv`, ablation/retirement pass | A+B+C (corpus), D (search), E (miner), F (fixtures) |
| **K** witness | S5.2–S5.3 with **hand-planted** dream files (no LLM): the Z-E edit, the objective-side real-only rule, `demo_dream.py` teeth (i)–(iii), `tests/test_witness_filter.py` | A (loader), E (miner) |
| **L** scorer-swap | replace I's flat fallback with H's Z-F scorer (one seam line) + the H42 verification of the S4.5 plant | H, I |

### Wave 2 — the serialized tail

| WP | scope | needs |
|---|---|---|
| **M** choices-integration | S3 part_a against the real `specs/macros.json` (the argmin-flip tooth) | J, L |
| **N** dream-live | S5.1: LLM-generated dreams via the S4 executor (**LLM; skippable with honest note**) | I, K |
| **O** docs+captures | ONE commit touching the merge-owned files: README Zone-3 section, TRUST amendments (H5 + the H10 caveat), committed demo captures; then the LLM benches (S4 bench, S2 live curve — both skippable, H33/H43) | everything prior |

### Critical path and width

```
critical path:  {A, D, E, F} ──▶ J ──▶ M ──▶ O     (4 sequential slots)
peak width:     9 agents (wave 0) · 3 (wave 1) · 2 (wave 2: M ∥ N) · 1 (O)
off-path:       B, C, G, H, I, K, N and both benches all hang off in parallel
total:          15 packages, 3 integration points
```

### Swarm rules (on top of the briefing addendum)

1. One WP = one agent = one worktree = the exclusive file list above.
   Touching a file outside the list is a review-blocking defect.
2. Merge-owned files (README, TRUST.md) are written ONLY by WP-O.
3. Package branches merge into the designated Zone-3 branch in the stated
   wave order; the integrator runs the fast regression at every merge.
4. A package that discovers its spec is wrong (an H-finding the sweep
   missed) stops and reports; it does not improvise across a freeze — a
   freeze change is a serialized cross-package commit, exactly like
   ROADMAP's interface-freeze rule.

## Interface freezes (agree before parallel work)

- **Z-A `planner/search.py`**: `beam_search(initial, expand, score, *,
  beam_width: int, max_depth: int)`; `expand` pure, `score` pure, ties by
  canonical JSON; returns best state ever visited (H19); NO other exports.
- **Z-B corpus entry**: file shape `{request: str, reading: {service,
  statements}}`; loader yields `CorpusEntry(request, statements, source)`
  — a new dataclass, never `reading.Reading` (H17); `source ∈ {real,
  dream}` inferred from path only; statements exactly the frozen
  Reading-statement shape (ROADMAP freeze #3).
- **Z-C macro candidate**: exactly `{name, params, body}` as consumed by
  `mdl_macros`; miner names `mined_<sha8>`; persisted table
  `specs/macros.json` `{name: candidate}` + optional `"retired": true`
  (H21/H27); accessor `reading_corpus.load_macros()`.
- **Z-D events**: `speculation-divergence` payload `{stage, direction ∈
  {false-accept, false-reject}, candidate_sha, request_sha}`;
  `self-witness` payload `{macro, reading_sha}`; both via
  `registry.log_event`, listed by `cgb.py events`.
- **Z-E** `macro_admission_decision(readings, candidate, macro_table=None,
  witness_filter=None)` — the ONLY signature change to an existing module,
  additive with a `None` default; when set, the filter restricts the
  readings used for BOTH `corpus_dl` computations inside the gate.
- **Z-F scorer**: `score_reading(reading, macro_table) -> float` — lower is
  better; with `macro_table == {}` it MUST equal the flat score
  (`mdl_macros.dl_reading(r, {})` + the compiled-spec size proxy of H34).
  Provided by `planner/choices.py` (WP-H); consumed by
  `buildloop/speculate.py` (WP-I), which ships with a flat-score fallback
  until the WP-L seam swap. This freeze is what lets S3 and S4 build in
  parallel.

## File-ownership matrix (W = writes, N = new, r = reads)

| file | S0 | S1 | S2 | S3 | S4 | S5 |
|---|---|---|---|---|---|---|
| `specs/readings/` | **N** | r | | r | r | W |
| `buildloop/reading_corpus.py` (single-writer) | **N** | r | | r | r | r |
| `planner/search.py` | | **N** | r | r | | |
| `buildloop/macro_mine.py` | | **N** | | | | r |
| `specs/macros.json` | | **N** | | r | r | r |
| `planner/lookahead.py` | | | **N** | | | |
| `buildloop/loop.py` (`pick_group` only) | | | W | | | |
| `milestones.py` (policy tuple only) | | | W | | | |
| `cgb.py` (`--policy` choices only) | | | W | | | |
| `planner/choices.py` | | | | **N** | r | |
| `buildloop/speculate.py` | | | | | **N** | r |
| `buildloop/service_loop.py` (additive flag) | | | | | W | |
| `buildloop/mdl_macros.py` (Z-E only) | | | | | | W |
| `buildloop/dream.py` | | | | | | **N** |
| `metrics/` (serialized S2 → S4, H39) | | | W | | W | |
| demos/tests/results (each phase's own) | N | N | N | N | N | N |
| README (Zone-3 section; merge-owned) | | W | W | W | W | W |
| TRUST.md (H5/H10 entries; merge-owned) | | W | | | W | |
| `kernel/*`, `generators/*`, `run/*` | r | r | r | r | r | r |

`kernel/__init__.py`, `kernel/backends.py`, `generators/service_gen.py`,
`generators/reading.py`, `generators/reading_compile.py`, `run/semantic.py`,
`library/__init__.py`, `run_regression.py` are **read-only for every Zone-3
phase** (calling backend machinery is permitted, H12). If a phase believes
it needs to edit one, the plan is wrong — stop and escalate, do not edit.

## Builder briefing addendum (on top of ROADMAP.md's briefing)

1. Zone-3 rules Z1–Z3 are review-blocking, same standing as house rules.
2. Every search/miner/enumerator must be deterministic: no `random`, no
   clocks, no dict-order dependence (sort or canonical-JSON everywhere).
3. Every phase's demo follows the repo demo convention (docstring naming
   each part and its failure class; per-part booleans; `REQUIRES_LLM`
   constant; `summary:` JSON line; `sys.exit`); capture with
   `python3 demo_X.py | tee results/X_demo.txt` and commit the capture.
4. Regression: `run_regression.py --fast` green before every push. New
   tests are auto-collected from `tests/`; do NOT edit `FAST_DEMOS` (H18).
5. **This addendum overrides ROADMAP briefing item 4** (⚠H45): Zone-3 work
   commits and pushes ONLY to the branch its task assignment designates —
   never to `main`.

## Hazards ledger (the five-lens sweep, condensed)

| # | finding | evidence | folded into |
|---|---|---|---|
| H1 | mined macros have no invocation anywhere; "per-use cert" was vacuous — they are accounting-only until genuinely invoked | `mdl_macros.py:120-141` rewrites virtually; cert path in `demo_macros.py` part B | S1.3 |
| H2 | `_match_at` is force/quote-blind; mixed windows "compress" but are unrealizable as legal invocations | `reading.py:183-205` (single inherited force+quote), `reading.py:328` | Z2, S1.2 |
| H3 | wildcard bodies dominate every search: real gate admits `["$p0","$p1"]` on an all-distinct corpus (Δ=−113.0) — falsified part_c as drafted | executed vs live module; `dl_invocation` size-blind (`mdl_macros.py:62`) | S1.2 filters |
| H4 | draft S3 part_a analytically impossible: demand-cluster macro ⇒ macro-aware = flat − constant ⇒ argmin fixed | proof over `_reading_stats`; demands copied byte-identically | S3.3 respec |
| H5 | mined tables falsify TRUST 1.2k's by-fiat "fixed, audited" status; expand-vs-expand comparand would be tautological | `kernel/__init__.py` parses `contract["macro_table"]` inside the trusted adapter | trust posture, S1 final commit |
| H6 | witness rule leaked through the *objective*: dreams could still pick which admissible sequence wins | greedy order-dependence (`mdl_macros.py:126-127`) | S5.2, S3.2 |
| H7 | self-witnessing loop: S3 authors macro-using readings that then count as witnesses | S3.2 scores by admitted-table DL | S5.2 |
| H8 | fan-out premise: real captures show 1–3 rounds or pre-gate-invisible failure; k>1 flat-to-worse on LLM calls | `results/synthesize_demo.txt:1`, `semantic_synth.txt:1`, `semantic_synth_temporal.txt` | S4 premise |
| H9 | acceptance "byte-identical certificates" impossible (`created_at` wall clock); warming contradicted Z1's letter and "losers never certified" | `kernel/certs.py:81`, `common.py:76`, `library/__init__.py:286` | Z1, S4.3, acceptance |
| H10 | pre-gating by reference replay Goodharts the reference channel of the intent/composition differentials | `run/semantic.py:150-167`, TRUST 1.2d/3.4 | S4.2 mitigations |
| H11 | trap corpus verified constructible: greedy 55.0 vs searched 35.0, B and C individually refused after A | executed vs live module | S1.4 part_b |
| H12 | "reference-only replay in run/semantic.py" and "quick-SMT helper" don't exist; compose from `kernel/backends.py:243`, `service_gen.py:954`, `SmtBackend.run_z3` | codebase audit | S3.2, S4.2 |
| H13 | S2∥S1 contradicted by the plan's own matrix (S2 reads `planner/search.py`) | matrix vs draft graph | dependency graph |
| H14 | `demo_macros.CORPUS` entries are parameter dicts, not Readings; macro form doesn't parse without a table | `demo_macros.py:68,108` | S0.1 |
| H15 | only 11 of 17 non-vague requests transcribe faithfully; 07/08/10/11/16/19 need dodges the fragment can't express | `reading.py:100-115` LF semantics vs request texts | S0.1 |
| H16 | "corpus" name collision with the failing-input corpus | `library/__init__.py:236`, M8 | S0.2 rename |
| H17 | `.source` collision with `Reading.source` (raw text) would silently zero witness counts | `reading.py:495` | S0.2, Z-B |
| H18 | fast tier auto-collects `tests/` but demos are hardcoded in unowned `run_regression.py` | `run_regression.py:40,106` | briefing #4 |
| H19 | DL non-monotone in admissions ⇒ best-ever-visited, not best-at-depth | `generator_dl`/`dl_macro` per-admission cost | Z-A |
| H20–H45 | executability pins: table persistence (H21), cert-invocation wording (H22), permutation sampling (H23), honest-tie CSV row (H24), trap residual heterogeneity (H25), CSV column rename (H26), macro retirement (H27), `milestones.py`/`cgb.py` ownership (H28), hypothetical-entry shapes + sorted atoms + plan()-KeyError (H29), min-vs-max ranking (H30), replay semantics (H31), `_all` plot path (H32), live-curve expectation (H33), S3 constants (H34), gate's real name/scope (H35), non-vacuity filter (H36), DL-invariant tie class (H37), events-table-only ledger (H38), metrics serialization (H39), k=1 regression mechanism (H40), one reading-gate stage (H41), verify-the-plant (H42), bench budget + skippability (H43), provenance hardening (H44), briefing precedence (H45) | per-phase citations above | in place |

## Acceptance, restated (post-sweep)

1. Macro vocabulary growth is search-driven: **never worse than greedy on
   the committed corpus across the tested arrival orders; strictly better
   on the trap corpus; admits nothing on the incompressible corpus** (H24 —
   the draft's "strictly beats on the committed corpus" contradicted its
   own part_a and is withdrawn); wildcard and mixed-force candidates are
   structurally excluded from mining.
2. Build-loop steering is lookahead-driven: strictly better on the planted
   backlog, and reproduces the measured 10-vs-11-admission /
   316.6-vs-318.8-DL edge on the real backlog in hypothetical replay,
   without changing the existing policies.
3. Design choice is an optimization with a stated objective — minimum
   macro-aware DL subject to demanded-order entailment — the entailment
   gate demonstrably overrides Occam, and admitted vocabulary demonstrably
   reshapes the chosen design (via a structural choice-tail idiom, H4).
4. Synthesis spends LLM calls K-wide against cheap exact gates, certifies
   only through the unchanged kernel, reports the measured trade honestly
   (H8), never rejects by reference-replay ranking (H10), and every
   prediction miss is a logged, queryable event.
5. Dreamed data can propose but never witness — in the gate AND in every
   search objective (H6); witnesses are distinct real requests; the system
   cannot manufacture its own witnesses (H7).
6. Zero new kernel contracts; zero edits to kernel, emitters, compiler, or
   reference; every certificate carries the **identical `cert_id`,
   `subject_hash`, `contract_hash`, and channel list** the non-speculative
   path would have produced (`created_at` excluded — H9), pinned by test.
