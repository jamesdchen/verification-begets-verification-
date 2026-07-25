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
- **C3 cycle 01 — second census-sourced batch** (`results/c3_cycle_01.md`):
  sources 71-74 are the verbatim prose of four more math2001 chapter-3
  divisibility attempt-candidates (017/026/027/028; provenance
  `wp_c3_readings.py`), certified via the inline-author checkpoint resume in
  both arms (a new wave 8).  **66 top-level sources, 62 governed readings,
  59 certified** (coverage 55->59).  Batch stayed in the arity-2 `dvd` family
  (sibling to 67-70) precisely so the arity-1 even/odd macro coverage
  invariant survives -- the parity candidates were MEASURED to displace it and
  were NOT shipped (honesty: never distort a reading to force a green).  The
  miner staged 2 new proposals (28->30); no NEW operator word crossed the
  admission bar (honest no-delta on the admission axis, recorded).  The
  registration carries a C3 lineage entry; a Lean-free cycle (no `[lean-fast]`).
- **P2 PURCHASED — bounded Finset carrier + cardinality, full bill paid**
  (`results/p2_delta.md`): `setbuild` (a bounded, filtered literal interval
  `{i ∈ Icc lo hi | filter}` -- a SET node) and `card` (its cardinality, a Nat
  term) landed through the full admission bill, riding P1's binding machinery.
  Validator+scope (`_check_setbuild`/`_check_card`, the set index Nat-carrier
  and scoped into the filter, `setbuild` admissible only as `card`'s argument),
  eval exhaustive COUNT, SMT unroll to a sum of `(ite filter 1 0)` indicators
  (QF_NIA only on a nonlinear filter), Lean `Finset.card (Finset.filter …
  (Finset.Icc lo hi))`, dual-solver differential+symbolic batteries with the
  filter-dropping divergence tooth (`tests/test_finset_battery.py`), growth-
  registry row `finset-card-node-class` (canary green), prompt grammar, and the
  FgReflect slice `cardTm`/`countTrue` (`evalTm_cardTm`/`substTm_cardTm` -- the
  indicator unroll, no new `Tm` binder, substitution unconditional).  Re-census
  delta on the portfolio: **zero, recorded** -- the portfolio's cardinalities
  are symbolic-bound, so `card:object-filter` (the reflect skip) and a
  symbolic-bound cardinality are the named demand the next iteration-class
  purchase targets.
- **P3 PURCHASED — the ℚ carrier, both clauses of the §4 bill paid**
  (`results/p3_delta.md`): the census signal split (probability-mass vs
  entropy-log) shipped first so the delta would be attributable, then `Rat`
  landed as the third entry in `CARRIERS` -- the ASCII Lean type name, since
  the `ℚ` glyph is escape-gate refused.  Validator (`_check_carrier_ops`, the
  carrier-admissibility walk, and the new Rat-ONLY builtin `/`), eval over
  exact `Fraction`s on a Farey-style sweep with Lean's own totalisation
  `q/0 = 0`, SMT mirror over a single `Real` sort with the `ite` guard
  mirroring eval cell for cell and a `QF_LRA`/`QF_NRA` split (cvc5 enforces
  it), Lean `(x : Rat)` binders, dual-solver differential+symbolic+
  carrier-stability batteries with the lossy-division divergence tooth
  (`tests/test_rat_battery.py`, 35 teeth), growth-registry row `rat-carrier`
  (canary green), prompt grammar, and the reflect fail-OPEN sites CLOSED.
  Named limits, in writing: `rat:no-coercion` (a Rat/integer mix refuses, no
  ambient rescues it), no `%`/`mod`/`dvd`/`gcd`/`coprime`/`even`/`odd` at Rat,
  no Nat-indexed binder inside a Rat reading, and `/` refused at ℕ/ℤ where
  Lean's division floors -- each a first-class `FragmentMiss` carrying demand
  data.  Re-census delta, split by census: the **mathlib-side** census moved
  (the `carrier:Rat` blocker retired -- 1487 rows unblocked, `in_fragment`
  537→**564**, and `Field` **0→9** in `unlock_counts`, the blocker behind the
  blocker becoming visible for the first time); the **portfolio** census
  returned **byte-identical verdicts** (108/169/731) -- 22 nodes gained the
  `rational` fragment word but none changed verdict, because signals dominate
  and all 22 already carried a miss signal.  Recorded as the no-delta reading
  it is, never widened until it moved.  The probability-mass nodes stay
  out-of-fragment CORRECTLY: they carry probability *vocabulary* a ℚ carrier
  alone cannot express.  The ℚ reflect tower (`evalTmQ/denoteQ/…`) is the
  named attended follow-up, with `carrier-out-of-reflect-slice:Rat` firing
  until it lands.
- **P4 PURCHASED — the `ZMod n` residue carrier, the full §4 P4 bill paid**
  (`results/p4_delta.md`): the first PARAMETRIC carrier, carried by a
  predicate (`_zmod_modulus`) rather than by a row in `CARRIERS` -- which
  stays `(Nat, Int, Rat)`, so every consumer that ENUMERATES carriers (the
  census aliases, the miner's op-slot typing, the admitted-operator cert rows,
  the tower census) is byte-unchanged.  Validator (`_check_zmod_ops`, the
  reading-wide one-modulus rule `_check_zmod_carrier`), eval reducing `% n` at
  each `=`/`!=` ATOM over exact integer arithmetic (so `-` is real subtraction,
  never Nat truncation), SMT declaring `Int` with a representative-range assert
  and wrapping both sides of every atom in `(mod _ n)` (a `mod` by a LITERAL is
  linear, so linear residue readings stay `QF_LIA`), Lean `(x : ZMod 7)`
  binders emitted verbatim, dual-solver differential+symbolic+carrier-
  divergence batteries with the lossy-mod-drop tooth
  (`tests/test_zmod_battery.py`, 18 rows / 27 teeth), growth-registry row
  `zmod-carrier` (canary green), prompt grammar, and P3's fail-CLOSED reflect
  layer choice covering the residue family with no new code.  What it BUYS
  that no earlier carrier does: a pure-residue sweep is `range(0, n)` -- the
  WHOLE carrier -- so `bounded_nonvacuous` and the ∃-shadow become **complete
  decisions** rather than bound-relative evidence.  Named limits, in writing:
  `carrier:zmod-symbolic-modulus` and `carrier:zmod-zero-modulus` (split, so
  neither masquerades as evidence for the other), non-canonical spellings
  (`ZMod 07`, `ZMod -1`) left at the generic `carrier:<ty>` miss rather than
  normalized, no order and no divisibility family at a residue carrier, no
  binder inside one (`zmod:binder-index-carrier`), one modulus per reading,
  `zmod:unit-inverse`, and `zmod:carrier-type` -- ZMod is outside the pinned
  `common.MATHLIB_IMPORTS` whitelist, so a residue statement RENDERS but its
  ELABORATION is deferred at the pin (P2's `Finset.card` precedent; widening
  the pin is cert-identity surgery, its own ceremony).  Re-census delta:
  **ZERO, predicted and confirmed** -- `ZMod` adds no fragment word and no
  census pattern row, so the portfolio (1008 nodes, 108/169/731) and the
  mathlib census are byte-identical.  The honest reading: the corpus states
  modular arithmetic at a SYMBOLIC modulus, which is exactly the demand class
  this purchase names and does not buy; of the 97 `algebra-structures` nodes,
  45 are parametric-typeclass (`algebra-abstract`, the P3-cycle instrument)
  and no concrete node reduces to a literal modulus today.  Reflect takes NO
  third tower: riding this cycle's Lean commit, a residue `=` atom is quoted
  through its CONGRUENCE IMAGE over the proven Int layer (`FgReflect.zmodEq`
  -- equality in `ZMod n` IS divisibility of the difference by the literal
  modulus), with named edges rather than widenings where the image does not
  reach (`zmod:negated-congruence` for `!=`, `zmod:atom-out-of-image:<op>`
  fail-closed, and route 2's box sweep keeping
  `carrier-out-of-reflect-slice:ZMod <n>` outright).
- Next flywheel actions, honestly stated: **the corpus ready list does NOT
  refill from P3 or P4** -- both re-census deltas on the portfolio were zero,
  so neither purchase converted an out-of-fragment node into an
  attempt-candidate, and `results/frontier.json` still reports 0 ready.  The
  next supplies are therefore (a) NEW CORPUS INTAKE on the free axis -- more
  near-fragment corpora via either intake adapter, which is the only lever
  that has ever moved the ready list; (b) the **cycle-16 connective demands**
  (`not`, `iff`, set-membership) -- grammar the corpus asks for repeatedly and
  the fragment does not speak, and unlike a carrier they are node-class
  purchases with a known bill shape; (c) the **mathlib import waves the Rat
  unlock opened** (+27 `in_fragment`, and `Field` 0→9 / `Ring` +10 / `Coe` +9
  in `unlock_counts` -- the blocker behind the blocker, now measurable).  The
  ℚ reflect tower (`evalTmQ/denoteQ/…`) stays the named CI-lane follow-up, as
  does the elaboration of the `zmodEq` image.  **P5 is NEVER a next action**: the
  abstract-algebra discharge route touches `ANCHOR_DISCHARGE_RUNGS`, i.e. the
  ANTI_LIST clause "primitive ladder rungs", and is user-gated behind the
  S4a→S4a′→S4b ceremony whatever the census prices it at.

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
   branch pushes at all (CI dedup runs it via pull_request only).  The
   subscription rides the claude-code-remote meta server (the same one as
   list_triggers), NOT the GitHub MCP connector — so it works even in
   trigger-fired sessions where the Actions REST API is blocked; when the
   lane verdict is unreadable that way, say so and proceed Lean-free (the
   wake-on-red subscription is then the ONLY verdict channel — never skip
   it).
2. **Lean-last.**  All Lean-touching edits of a cycle batch into the
   session's FINAL commit, tagged `[lean-fast]` (reflection/shadow inner
   loop) or `[lean-ci]` (kernel-adjacent steps), so the lane runs while no
   session is live and the NEXT session starts from a verdict, not a wait.
   The lane budget is one round PER PUSH, not per session: a session
   subscribed to its own PR's CI activity (rule 1's event-driven upgrade)
   is WOKEN by a red verdict, and the fix it then takes is a wake-driven
   FIX round, still inside budget — drive-to-green continues where the
   context is warmest instead of paying a whole cadence interval to
   re-derive it cold.  What makes that affordable is the gate itself:
   `results/latency_baseline.md` measures the CI lane at ~2 min typical,
   so the wake arrives while the session that caused the red is still the
   cheapest place to fix it.  The original intent survives intact on the
   authoring side — a DESIGN that needs a second AUTHORED round (new
   material, not a fix to material already pushed) is still two sessions'
   work.  Two bounds keep the per-push budget from becoming no budget at
   all.  SCOPE: only a LEAN-LANE or fast-gate red is the woken session's
   work; the `trust-surface` red a full-bill purchase earns by touching
   the growth registry is the DESIGNED maintainer handoff, it arrives
   first on essentially every purchase PR, and the only ways to "green"
   it are gutting the purchase or editing the fence — so that wake is
   noted and stopped on, never worked.  COUNT: at most two wake-driven
   fix rounds per session, each naming a root cause distinct from the
   last; a red that repeats for the same reason is environment or
   design, and it yields with the cause named.  (The old
   one-round-per-session cap was a circuit breaker as well as a budget;
   these two clauses are what replaces the breaker.)
3. **Two tracks, one Lean dependency.**  The corpus axis (intake →
   census → sources → readings → bench → mine → regenerate) is Lean-free
   and fully verifiable in-container — it NEVER blocks on the lane.  The
   two tracks are independent in EXECUTION only; in SUPPLY each is the
   other's feedstock, and neither runs forever alone: the corpus track's
   ready list refills only when a purchase un-gates a signal
   (`intake_from_frontier --unblocked`) or a decision PR lifts a park,
   while the purchase track prices its next bill from what the corpus
   track measured — the refusal ledger and the frontier's blocked groups,
   which name their unblocking purchases.  So an idle corpus track is a
   reading about purchase supply, not an idle loop.  A
   purchase stages its Lean-free bill first (validator, eval, SMT,
   compile-text, batteries, registry — all locally green), and its
   reflect-slice/Lean commit rides last under rule 2.  **The additive-class
   rule (binding for UNATTENDED sessions).**  Additive proofs are the
   low-red-risk class, and an unattended purchase ships ONLY reflect
   extensions inside it.  A slice extension is ADDITIVE-CLASS when all five
   hold: (a) no new `Tm`/`Pd` constructor; (b) the substitution lemma stays
   UNCONDITIONAL (nothing is bound, so there is no capture story); (c)
   decidability is INHERITED — `decDenote` already decides the predicates
   over the new terms; these three are exactly the P1 and P2 dispositions,
   stated in the slice itself at `tools/FgReflect.lean:1157-1172` (the
   unrolled fold) and `:1246-1261` (the unrolled cardinality); plus (d) no
   new import (`common.MATHLIB_IMPORTS` is a pin, and widening it is its own
   purchase); and (e) carrier checks that fail CLOSED — `results/p3_delta.md`
   names the hazard measured on the ℚ signal, where the silent `else → Int`
   sites let a non-Int reading fail OPEN into the Int reflect tower.
   Anything else is TOWER-class — a new evaluation tower, a genuinely new
   constructor, an import-pin widening — and an unattended session does not
   take it: it splits out as a NAMED attended follow-up, the disposition
   both the P1 and P2 comments already use ("a SEPARATE purchase, not a
   widening of this one").  An ATTENDED session (a maintainer present to
   read the red) may take tower-class work deliberately; that is what
   attendance buys.
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
5. **Cadence: recurring Routines, event-chained.**  The original C3 was a
   self-arming chain — each driver session ended by creating exactly ONE
   one-shot trigger for the next cycle, sized to its own state.  That model
   is RETIRED: session-created triggers carry neither the repo attachment
   nor the connectors, so the sessions they fire get read-only git and no
   GitHub tools (cycle 02 stranded exactly that way and had to be recovered
   by bundle).  Sessions therefore create NO triggers.  The cadence is now
   three mechanisms, none of them a session's own arithmetic: recurring
   Routines as the heartbeat (one per axis, corpus and purchase, each with
   an in-flight guard so an off-cycle firing exits cheaply), a merge-event
   trigger that chains cycle N+1 off cycle N's merge (a bonus, measured NOT
   to fire for a Claude-performed merge — hence the watchdog's REARM rule),
   and a WATCHDOG whose cron tightened from every 12 h to every 3 h, since
   a dead loop's cost is bounded by how long it goes unnoticed.  Exact
   schedules, guards and the DEAD predicates live in `C3_PROMPTS.md`
   ("Architecture" + the Schedule-metadata table) — authoritative there,
   deliberately not restated here, because a schedule number copied into
   prose is a number that will rot.  The one figure worth keeping is the
   retired chain's **+75 min** Lean delay: a session that pushed Lean-tagged
   work scheduled the next cycle over an hour out purely so the lane verdict
   would exist by then.  Wake-on-red (rules 1 and 2) deletes that wait —
   the verdict comes to the session that caused it, ~2 min after the push
   (`results/latency_baseline.md`), rather than the session paying an hour
   to meet it.  The canonical prompt texts for both Routines live in
   `C3_PROMPTS.md` (versioned; each Routine's stored Instructions are only a
   pointer at this file, so prompt fixes ship by git merge instead of
   freezing into the chain).

## 4. The purchase queue (strict tractability order; each battery-gated)

Every purchase pays the SAME full bill: validator + lexicon entry, eval
semantics, SMT mirror, Lean rendering table, differential + symbolic
batteries (b/b2), growth-protocol registry row (extend `operator-words` or
register a new grower — the completeness canary must stay green), teeth,
AND a FgReflect slice extension (lane-checked) so reflection keeps pace with
the fragment — additive-class by default under §3.1 rule 3, a new
constructor + Decidable instance only when the purchase is attended.  Done-predicates for
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
