# PLAN_FRAGMENT.md — closing the corpus↔fragment gap

Status: ACTIVE — sibling packet to `PLAN_REFLECT.md` (which stays scoped to
the reflection program T1–T3).  A fresh session picking up FRAGMENT GROWTH
reads this file first, then the census results, then acts.  House rules
carry over verbatim: every done-condition below is a predicate a test, the
census, or the Lean lane evaluates — none exists only as prose.

## 0. The program in one paragraph

The FRAGMENT is the language the machine speaks (carriers, operator words,
quantifier shapes — defined by the validators/lexicon, changed only through
admission ceremonies).  A CORPUS is a body of math humans wrote (blueprint
sites, the committed readings), taken as found.  The census
(`tools/blueprint_extract.py` + `tools/blueprint_census.py`) measures their
intersection per corpus.  The gap closes from BOTH ends: purchases grow the
fragment toward math (expensive, battery-gated); corpus selection brings
math toward the fragment (free).  One law overrides all economics: TRUST
ROOTS NEVER GROW BY PURCHASE — anything touching a discharge route goes
through the shadow→evidence→promotion pattern PLAN_REFLECT S4a→S4a′→S4b
rehearses.

## 1. Verified current state (update every cycle)

- **C1 done — the corpus portfolio: 5 corpora, 748 nodes** (pfr 218,
  unit_fractions 52, formal_book 192, flt_regular 45, equational_theories
  241), each intaken under `specs/mathsources/<name>/` as `nodes.jsonl` +
  `fetch_meta.json` with per-page SHA-256.  The done-predicate is a test:
  `tests/test_census_portfolio.py` (≥5 corpora, committed censuses in sync).
  `tools/census_portfolio.py` is the §2 re-census instrument (one command,
  per-corpus reports + the rollup in `results/census_portfolio.json`).
- Census instrument: **second-wave miss signals** landed after the first
  mining triage (geometry-topology, graphs-combinatorics, magmas-equational,
  polynomials-fields, maps-functions, rational-arithmetic — the start of
  P3's signal split).  Portfolio now **6 corpora, 1008 nodes** (the sixth:
  math2001, 260 nodes via the Sphinx intake adapter
  `tools/sphinx_extract.py`): **108 attempt-candidates** (106 in math2001 —
  the first corpus whose candidates genuinely transcribe), 711
  out-of-fragment, 189 no-signal (`results/census_portfolio.json`).
- **P1 PURCHASED — bounded big-operators (bigsum/bigprod), full bill paid**
  (`results/p1_delta.md`): validator+scope, eval, SMT unroll, Lean
  `Finset.Icc` rendering, dual-solver differential+symbolic batteries with
  the lossy-unroll divergence tooth (`tests/test_bigop_battery.py`),
  growth-registry row `bigop-node-class` (canary green), prompt grammar,
  FgReflect slice (`sumTm`/`prodTm` folds — the literal-bound unroll).
  Re-census delta on the blueprint portfolio: **zero, recorded** — its
  sums are symbolic-bound (`bigop:symbolic-bound` is now the named
  refusal), evidence that the next iteration-class purchase targets
  symbolic bounds.
- **C2 DONE — done-predicate MET** (`results/c2_closure.md`): sources 67-70
  are the verbatim prose of four math2001 census attempt-candidates
  (provenance in `wp_c2_readings.py`); their readings certify in both bench
  arms; the miner emits **`op_34e1b706c47c` — the squaring template
  `^(v0,2)`** — whose two-of-three witnesses are census-sourced and which
  crossed the two-witness bar ONLY because of them.  The flywheel then
  admitted a fifth operator word (`op_3c0de4c8920b`, nonnegativity) through
  the full R2 batteries on the grown corpus.
- Fragment today: carriers Nat/Int; operator words + the ONE binding node
  class (literal-bound bigsum/bigprod); reflect slice = Int v0.1 + the
  bigop fold layer (PLAN_REFLECT §1).
- **Union era (merge of PR #23)**: the PLAN_REFLECT program completed in
  parallel (S4b promotion ceremony; reflection joined the discharge
  vocabulary) and added entrance-predicate sources 67-69 beside this
  branch's census-sourced 67-70 — slot numbers collide, filenames stay
  unique, both sets certify; 62 top-level sources, 55 certified.  All
  downstream artifacts regenerated; the registration carries the union
  lineage entry.  (Live counts: the session brief, always.)
- Next flywheel actions: **P2** (bounded Finset carrier + card, riding P1's
  binding machinery) on the purchase axis; C3 (the 24/7 cadence,
  USER-GATED) on the corpus axis; more near-fragment corpora via either
  intake adapter.

## 2. The flywheel (the ONLY loop; one purchase per cycle)

census → miss histogram = price list → ONE purchase through the admission
batteries → re-census the full corpus portfolio → the measured delta
(attempt-candidate count + histogram shift, per corpus) is committed to
`results/` in the same session that learns it.  A purchase whose re-census
shows no delta across ≥2 corpora is recorded evidence to buy differently —
never silently retried, never quietly widened.

## 3. The corpus axis (free; runs first and continuously)

- **C1 — corpus portfolio: DONE** (cycle 1): intake + census of 4 more
  blueprint corpora chosen near the fragment — unit_fractions, formal_book,
  flt_regular, equational_theories — beside pfr.  The done-predicate
  (≥5 corpora under `specs/mathsources/` with committed census results) is
  evaluated by `tests/test_census_portfolio.py`.  Further corpora stay
  welcome under the same intake discipline (`nodes.jsonl` + `fetch_meta.json`
  with source URL, date, per-page SHA-256; network-at-intake only).
- **C2 — mine where candidates exist today: DONE** (cycle 2): the blueprint
  queue triage (`results/fragment_mining_triage.md`) showed zero
  transcribable candidates, so the corpus axis fetched math toward the
  fragment — the math2001 intake — and its candidates fed the full chain:
  census node → verbatim source → inline reading → certification → miner.
  The done-predicate (first mined template whose source is a census
  attempt-candidate) is met by `op_34e1b706c47c` (`results/c2_closure.md`).
  The mining loop stays live: 102 math2001 candidates remain unqueued, and
  `fermats_little` (formal_book) stays the named intake for a
  symbolic-bound/primality future.
- **C3 — the 24/7 cadence**: continuous mining = a Routine firing driver
  sessions on a schedule, each running one census/mine/ledger cycle and
  committing results back.  Creating the Routine is USER-GATED (recurring
  scheduling is the maintainer's to authorize); this packet — §3.1's
  protocol specifically — is the prompt such a session follows.

### 3.1 The driver-session protocol (pipelining around the Lean lane)

Driver sessions run in Claude Code remote containers where the Lean
toolchain is NOT local (the proxy blocks toolchain hosts; elaborating in
the container is not an option).  Every Lean-touching step therefore pays
a CI round-trip — commit → `[lean-fast]`/`[lean-ci]` lane → verdict — and
the cadence is designed so that round-trip overlaps the idle gap BETWEEN
sessions instead of blocking a live one:

0. **Orient from the derived brief, never from recollection.**  First
   command: `python3 tools/session_brief.py` — era, portfolio, queue,
   operator counts, lane state, PLAN §1 verbatim, all DERIVED from
   committed artifacts (a prose snapshot of a moving loop decays; the
   brief is computed, so it cannot).  CLAUDE.md is the stable router: it
   holds only invariants and points here.
1. **Lane-verdict first.**  A driver session's next act is reading the
   previous head commit's CI conclusion (GitHub Actions on this branch —
   ONE minimal query: newest run, this branch; full listings overflow a
   session's context).  Green → proceed.  Red on a Lean lane → the fix IS
   this cycle's work: nothing new starts until the lane is green
   (drive-to-green, one concern at a time).  Still running → do only
   Lean-free work; never idle-wait on a lane.  EVENT-DRIVEN UPGRADE: with
   an open PR for the cadence branch, a session that pushes a lane-tagged
   commit subscribes to the PR's CI activity, so a red verdict WAKES the
   session that caused it instead of waiting a full cadence interval for
   the next firing — and the PR is what turns the fast Python gate on for
   branch pushes at all (CI dedup runs it via pull_request only).
2. **Lean-last.**  All Lean-touching edits of a cycle batch into the
   session's FINAL commit, tagged `[lean-fast]` (reflection/shadow inner
   loop) or `[lean-ci]` (kernel-adjacent steps), so the lane runs while no
   session is live and the NEXT session starts from a verdict, not a wait.
   One lane round per session, maximum — a design that needs two rounds is
   two sessions' work.
3. **Two tracks, one Lean dependency.**  The corpus axis (intake →
   census → sources → readings → bench → mine → regenerate) is Lean-free
   and fully verifiable in-container — it NEVER blocks on the lane.  A
   purchase stages its Lean-free bill first (validator, eval, SMT,
   compile-text, batteries, registry — all locally green), and its
   reflect-slice/Lean commit rides last under rule 2.  Prefer designs that
   keep the reflect extension additive (the P1 unroll precedent: no
   existing lemma restated, no capture story) — additive proofs are the
   low-red-risk class.
4. **The latency toolkit** (all committed; a driver session should never
   rebuild them): `tools/session_brief.py` (rule 0),
   `tools/intake_corpus.py` (one-command corpus intake),
   `tools/regen_downstream.py` (the full downstream artifact DAG,
   concurrent chains where no edge exists, resumable with `--from`,
   `--serial` for readable runs; whole DAG ≈ 15s),
   `specs/mathsources/registration.json` (the ONE re-baseline point for
   corpus-growth pins; `tools/measure_cluster_key.py
   --print-reregistration` computes the next era's block), the
   SessionStart hook (`.claude/hooks/session-start.sh`) that installs the
   pinned Python closure before the session's first command, and the
   CLAUDE.md test-subset index (fast loops ~10s; `pytest -n auto` cuts
   the full gate ~3x in-session — CI stays serial).
5. **Adaptive cadence (the optimized C3): a chain, not a clock.**  A fixed
   cron either wastes firings (idle ticks) or adds dead time (a verdict
   waiting for the next tick).  Instead each driver session ends by
   creating exactly ONE one-shot fresh-session trigger for the next cycle,
   sized to its own state: **+75 min** after pushing Lean-tagged work (the
   `[lean-fast]` lane completes well within that on a warm cache;
   `[lean-fresh]` re-keys the ~5GB cache and is never for cadence
   sessions), **+15 min** when Lean-free work remains queued, **+6 h**
   when the queue is empty or blocked on the user (say why in the session
   summary).  Duplicate-firing guard: a session that finds another pending
   C3 one-shot exits immediately.  A low-frequency WATCHDOG cron (every
   12 h) revives the chain: it exits at once if a driver committed
   recently or a one-shot is pending, else it runs a normal cycle and
   re-arms the chain.  Base-freshness guard: a driver whose base branch
   lacks `tools/session_brief.py` is running before the toolkit PR merged
   -- reschedule one one-shot +6 h and exit.

## 4. The purchase queue (strict tractability order; each battery-gated)

Every purchase pays the SAME full bill: validator + lexicon entry, eval
semantics, SMT mirror, Lean rendering table, differential + symbolic
batteries (b/b2), growth-protocol registry row (extend `operator-words` or
register a new grower — the completeness canary must stay green), teeth,
AND a FgReflect slice extension (constructor + Decidable instance, lane-
checked) so reflection keeps pace with the fragment.  Done-predicates for
every purchase: admission batteries green; reflect-slice lane green; the
§2 re-census delta committed.

- **P1 — bounded big-operators** (prices sequences-sums: 45 in PFR; high
  frequency in every corpus).  A binding AST node CLASS — Σ/Π with an
  explicit literal bound — not an operator word: F-G is first-order today,
  so this is the one structural extension.  Bounded iteration is exactly
  what the repo already trusts: decidable by exhaustive computation, SMT
  by unrolling, Lean via `Finset.range`.  Largest single ROI; everything
  later rides its binding machinery.
- **P2 — bounded Finset carrier + card** (sets-cardinality: 24).  Rides
  P1's binding machinery; same bill.
- **P3 — ℚ carrier** (the mass-arithmetic slice of probability-entropy's
  111).  Rational arithmetic is decidable for the fragment's relations;
  finite distributions with rational masses become expressible WITHOUT
  touching `log`.  Requires a census signal split (probability-mass vs
  entropy-log) so the delta is honestly attributable, plus the D8-class
  divergence battery against Nat/Int.
- **P4 — concrete algebra: `ZMod n` carrier** (algebra-structures: 49,
  PARTIAL).  Finite carriers are per-instance decidable; typeclass-
  parametric statements (`∀ G [Group G]`) stay out-of-fragment under an
  honest sub-signal (algebra-abstract), never silently claimed.
- **P5 — abstract algebra discharge route: TRUST ROOT, NOT A PURCHASE.**
  A new rung (a group-tactic class) touches `ANCHOR_DISCHARGE_RUNGS`
  (PINNED, kernel/certs.py, FI-KA-1/4).  The ONLY route: shadow channel
  beside the ladder → durable agreement ledger → numeric entrance
  predicate → ONE-commit ceremony with explicit user sign-off — the
  PLAN_REFLECT S4a→S4a′→S4b pattern verbatim.  No queue entry may
  shortcut this, whatever the census prices it at.
- **PARKED (named, never promised)**: entropy proper (`log` is
  transcendental) and real-analysis (limits/continuity are undecidable).
  These need a DIFFERENT certifying story (interval-arithmetic or
  polyrith-class routes), i.e. a research program, not a queue entry.
  The census keeps measuring them; any future attempt starts with its own
  packet and its own shadow ceremony.

## 5. Guardrails (non-negotiable)

- The anti-list overrides the price list: trust roots never grow by
  economics (§4 P5 is the worked example).
- No kernel/cert/TRUST.md edits outside a PLAN_REFLECT-S4b-style ceremony.
- Census intake is network-at-intake only (committed SHA-256 per page);
  everything downstream is offline, deterministic, LLM-free, and runs
  under `buildloop.lanes.token_free`.
- One purchase per flywheel cycle; the delta is committed before the next
  purchase begins.
- Branch discipline, the escape-gate envelope, and the `[lean-ci]` tag
  carry over from PLAN_REFLECT §4 for every Lean-touching step.
- Honesty rules carry: the census reports signals, never fidelity
  verdicts; parked items stay parked in writing; a no-delta purchase is
  recorded, not hidden.
