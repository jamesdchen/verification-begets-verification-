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

- **CYCLE 29 — the derived route could not clear itself, and the ready list
  ran out of fragment** (`results/c3_cycle_29.md`).  ZERO certifications;
  corpus unchanged at **125**.  Two findings.  (1) `NEXT-SELECTION` branched
  on `refill_projection.awaiting_unblock_run`, a documented UPPER BOUND that
  does NOT model already-intaken subjects — and **all 11** awaiting subjects
  were already corpus sources, so all six printed `--unblocked` commands
  selected zero, retired nothing, and the route would have re-printed them
  every cycle forever.  `_next_selection` now branches on
  `selectable_awaiting_subjects` (the bound MINUS what the selector would
  skip), reports both numbers, and IMPORTS the already-intaken predicate from
  `intake_from_frontier` so branch and selector cannot drift; an unreadable
  subject list falls back to the bound, because failing safe here means DO NOT
  NARROW.  (2) `--ready --take 8` then took eight
  `prime_number_theorem_and` subjects and **all eight refused**, under four
  blockers: `prime-predicate` (3), `integral-operator` (2),
  `complex-carrier` (2), `uninterpreted-function-symbol` (1) — none a rung the
  ladder reaches by widening, and two of them carrier/analysis demand this
  fragment has never priced.  Ready **11 → 3**; refused subjects 61 → 70.
  (2b) `sigmaR_natCast` was first filed under the coarse `function-symbol`,
  a signal a LANDED purchase meets, and the regenerated route immediately
  named it the one selectable subject — cycle 30 would have re-measured a
  refusal cycle 29 had just measured.  The append-only correction adds
  `uninterpreted-function-symbol` beside it (the `definition` route was
  authored and gated too, and refuses identically: the source gives σ^R no
  body).  **The cycle-26/27/28 finding a third time — a refusal group coarser
  than its blocker — caught by the instrument built in the same cycle.**
  (2c) the append then reddened
  `test_the_eleven_subjects_are_exactly_the_refusal_ledger_rows`, as that
  tooth is built to: `sigmaR_natCast` is classified `needs-mechanism`
  (`returned_by_p8` False, measured via the `definition` route, not inferred),
  the `needs-mechanism` pin moves 5 → 6 because the slice moved, and
  **`P8_CEILING` stays 5**.
- **P9 PURCHASED — named sets by COMPREHENSION + the membership atom, and
  the row split in two** (`results/p9_delta.md`).  A `setdef` statement names
  a set by an explicit comprehension over one parameter and
  `{"op":"mem","args":[<term>,{"set":s}]}` takes membership in it.  THE
  FINDING, and it is P8's a second time: `set-membership` was **two rungs
  wearing one name**.  `e ∈ {x | φ(x)}` IS `φ(e)`, so the comprehension half
  is ELIMINABLE — the gate desugars every membership by capture-free
  substitution (the pred layer of `_unfold_term`) and `math_eval.py`,
  `math_smt.py`, `math_compile.py` and `tools/FgReflect.lean` are ALL FOUR
  byte-unchanged, so `Tm`/`Pd` take no constructor and §3.1 rule 3(a) is not
  reached.  Landed **additive-desugaring**, not the tower-class the row
  declared.  Set ALGEBRA is deliberately not new vocabulary: union,
  intersection, complement, ∅ and set equality are stated EXTENSIONALLY with
  P6's connectives.  Conservativity is executable — every reading is measured
  against a HAND-UNFOLDED twin at all four consumers (same eval verdict on a
  box, byte-identical SMT with z3 AND cvc5 unsat on the negated
  biconditional, byte-identical `lean_text` and `statement_hash`) with the
  wrong-comprehension divergence tooth (`tests/test_setdef_battery.py`).
  WHAT WAS NOT BOUGHT is the headline: a set the source gives NO
  comprehension for.  `set:free-set-variable` (an arbitrary `U` — membership
  in it SURVIVES unfolding) and `set:set-valued-param` (a comprehension
  binding a set, the powerset shape) are first-class refusals with their own
  ledger signals, and `refusal-set-carrier` stays OPEN and tower-class,
  re-titled to exactly that residue.  `tests/test_set_object_class.py`
  measures the row's real price: of its four subjects ONE needs the residue,
  TWO carry a ℤ/ℕ carrier mismatch in their own prose (`#problem-015` is
  REFUTED outright once collapsed to one carrier — a truth fact, demand for
  no primitive), and the fourth is reachable only by the degenerate cycle-16
  unfolding.  Re-census delta honestly **ZERO** (byte-identical, 135/1521/296)
  — the P4/P8 shape.  Refill projection **+4** (23 → 27 at this purchase's
  base `d889c54`; cycle 26 merged concurrently and moved the ABSOLUTE figure,
  so read the derived artifact, never this number);
  the number of record is the next corpus cycle's `--unblocked
  refused:set-membership`, never the receipt.  Taken by an unattended firing
  under a MEASURED `lean-local` verdict (corroborated by direct elaboration,
  `test_reflect_shadow` 24 passed in 427.6 s) — and the receipt separates that
  from the bill, because the measurement then said this half is not
  tower-class, so it was takeable in a Lean-absent container too.
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
- **BOTH LOOPS IDLE — the measured standstill** (cycle 17 consumed the last
  ready subject; the C3 watchdog reading at PR #77 found no corrective action
  to take).  `results/frontier.json` reports **0 ready** and 28 blocked
  groups, so every corpus firing exits on an empty window, and no §4 row was
  pointed at, so every purchase firing found nothing claimed.  Neither loop is
  broken: both are STARVED, and starvation is a SUPPLY reading.  Say the
  reading plainly, because the wrong one is easy: **an empty ready list is NOT
  evidence the corpus is exhausted — it is evidence the FRAGMENT cannot yet
  speak what the corpus asked for.**  1008 census nodes are still out there
  and 61 subject-rows sit in `refused:` groups having already passed
  selection.  §3.2 names the four refill paths; their MEASURED state today:
  - (a) **a purchase un-gates a CENSUS signal — measured EMPTY, and now
    explained.** P3 (`Rat`) and P4 (`ZMod n`) each returned a ZERO portfolio
    delta.  The reason is structural, not bad luck: the portfolio census is
    LEXICAL (fragment words and miss-signal substrings over the node text),
    and a CARRIER moves no vocabulary — `ZMod` adds no census word at all, and
    `Rat`'s 22 word-gains changed no verdict because signals dominate.  A
    carrier is therefore never to be BOUGHT for a ready-list delta again; the
    purchases that can move this census are the ones that retire a miss
    SIGNAL, and the census is where that is measured, not argued.
  - (b) **a decision PR lifts PARKS — structurally EMPTY.**
    `results/frontier_parks.jsonl` has **ZERO rows**: no cycle has ever parked
    a subject, so the decision lane has nothing to lift and can supply nothing
    until a future cycle parks something.  (`derived_from.frontier_parks_rows`
    in the frontier says 0 — this is derived, not recalled.)
  - (c) **NEW-CORPUS INTAKE — AVAILABLE, and the only lever that has ever
    moved the ready list** (`tools/intake_corpus.py`; the math2001 intake of
    C2 is the worked example, and every ready entry the loop has ever consumed
    came from it).  It was NOT automated until now: §3.1's driver protocol
    exited on an empty window, so no Routine could reach the one working
    lever.  The DRIVER prompt in `C3_PROMPTS.md` now tries intake BEFORE
    exiting, and the path is **mechanically runnable unattended**: the driver
    consults `tools/corpus_candidates.py`, which takes the first row still
    marked `candidate` from `specs/mathsources/corpus_candidates.json` in
    DECLARATION ORDER and consults nothing yield-shaped to do it.  A corpus is
    still chosen NEAR THE FRAGMENT by a human, never to manufacture a green —
    that judgment moved from per-cycle to PER-CANDIDATE (§3.2 (c)), it did not
    disappear.  MEASURED: the registry declares **zero `candidate` rows**
    today, so the selector answers `registry-exhausted` and the loop still
    waits — but it now waits on one appended ROW rather than on a human being
    awake during a firing.
  - (d) **retiring a measured REFUSAL signal — 61 subject-rows waiting, the
    highest-quality demand the system has.**  15 `refused:` groups hold 61
    rows over **45 distinct subjects** (a subject blocked by two signals
    appears under each, and returns only when ALL of its signals are met).
    These subjects already PASSED SELECTION — they are measured demand from
    certification, not lexical predictions — and `tools/frontier.py`'s
    precedence (refused beats ready) is the only thing holding them out.  The
    route back is `intake_from_frontier --unblocked refused:<signal>` on the
    cycle after the signal is met; the ledger rows STAY as pre-purchase
    evidence.  §4's new P6–P9 rows price the four largest groups.  **The
    zero-cost inventory is now ZERO, measured** (C3 cycle 20,
    `results/c3_cycle_20.md`): every remaining refused subject is held by at
    least one signal no LANDED purchase meets.  The last exception was
    `cmp-outside-lexicon`, which this §1 read as "mintable by the
    operator-words grower" and named as what path (d) could test TODAY at no
    purchase cost — **and the measurement refused it.**  Its 2 subjects (3
    nodes, one subject verbatim-equal across two) were probed through
    `certify_statement` at the live fragment: the source's own relation is
    rejected at the reading gate (`unknown atom/connective '>'` / `'>='`,
    because `_BUILTIN_ATOM_OPS` is `{=, !=, <=, <}`), and the operator mint
    can never reach it — the grower mines TEMPLATES over readings, and the
    gate forbids the reading that would carry the word.  The CONVERSE reading
    (`b < a` for the source's `a > b`) certifies fully and is DECLINED on
    fidelity: it reverses the source's written order, the rewriting the
    readings discipline refuses when it keeps a quadratic in the source's own
    spelling, and of 121 intaken sources ZERO carry `>`/`>=` prose.  The
    honest home is an atom-lexicon purchase, unpriced as yet.  `mod-operator`
    is unchanged and was never zero-cost: both its subjects also carry a live
    signal (`definition-biconditional`, `symbolic-exponent`).  No ledger row
    was appended for the re-measurement — the fragment did not grow for this
    signal, so the cycle-05 rows STAND as the reading and a duplicate would
    flatter the loop with demand it did not newly measure.
- **The measured 8-hour idle after cycle 20 was a REPORTING defect, not a
  loop defect.** Cycle 20 shipped 08:14Z with batch=0; the next three
  watchdog firings (09:46/12:50/15:50Z) each reported "both loops healthy"
  over a machine that could not move.  Both loops were CORRECT to stop: the
  frontier's ready list was empty with all four §3.2 supply paths dry, and
  all three OPEN purchase rows (`refusal-symbolic-exponent`
  iteration-class, `refusal-function-symbol` definitional-extension,
  `refusal-set-carrier` tower-class) sit outside the additive family, so
  §3.1 rule 3 makes an unattended session yield on every one of them.  What
  failed was the instrumentation above them: `tools/supply_status.py` — the
  tool built precisely so a wedged machine SAYS SO — counted census DEMAND
  and never read `bill_class`, so it computed `purchase-work-available` for
  three rows no driver firing may start; and the WATCHDOG prompt's corpus
  predicate read an empty ready list as healthy without consulting the
  supply reading at all.  Both are now closed: the attendance filter gates
  `machine_actionable` on `UNATTENDED_BILL_CLASSES` and the verdict
  vocabulary carries a distinct `supply-blocked: tower-class-only (…)`
  shape naming the routes that would unblock it (attendance, a `lean-local`
  probe RUN in-session, or the `[lean-hammer]` authoring ride landed by
  `a0ed559`), and the watchdog regenerates and QUOTES that verdict every
  firing.  Blocked is not dead, and the prompt says so in those words: the
  drivers are firing correctly and the defect is supply-and-attendance, so
  no rescue cycle follows a blocked reading.
- **The authoring ride shipped complete and no firing walked it.**  The
  `[lean-hammer]` AUTHORING kind landed toothed end to end (queue → batch →
  ride → verdicts → readout), and rule 3 above names it as the SECOND route
  to the capability — but the gap was in the DRIVERS: the purchase prompt's
  lean-absent branch ended at a bare YIELD, and the watchdog only NAMED the
  ride in its reporting vocabulary.  An exit no firing walks is not an exit,
  and a machine that reports a correct yield and stops is the no-op measured
  above wearing better prose.  Both prompts now route: the purchase driver
  CONSUMES pending verdicts, AUTHORS the next round from the previous
  round's transcript tail, and RIDES under a `C3 authoring` title that the
  in-flight guard cannot see (an authoring ride buys nothing and must not
  spend the flywheel slot); the watchdog knows the fourth PR kind, refuses
  to merge the lane's zero-check commit-back tip, and will not read a
  correctly-riding purchase loop as DEAD.  `tests/test_authoring_route.py`
  is the tooth, and it is deliberately NOT prose-pinning: every command the
  route names is EXECUTED there (the script must exist and argparse must
  accept the exact flags quoted), the marker quoted as the trigger is
  checked against the workflow's own branch condition and bound to the
  COMMIT INSTRUCTION rather than to the section, the schema named is checked
  against the queue's declared schema, and the no-write-path-to-the-slice
  bound is checked in the ride's CODE rather than promised in its prose.
  Mutation-verified on three edits: a dead-ended route, a drifted marker and
  a purchase-titled ride each redden it.  The first version of the marker
  tooth did NOT bite — it matched the lane's name in surrounding prose — and
  that near-miss is recorded because it is the same defect this file has now
  logged three times: a check that stopped tracking its evidence.
- **The lane marker is a TRIGGER, and the commit that shipped the route
  fired it.**  `.github/workflows/lean-hammer.yml` matches the literal
  bracketed marker ANYWHERE in the head commit message, so the commit whose
  message DESCRIBED the instruction ("commit under the literal … marker")
  dispatched a real ride.  Nothing was lost — the batch carried no
  `authoring` key, so it was an ordinary goal-shaped ride, and the
  consume-before-merge protocol is exactly what handles the zero-check tip it
  commits back — but the failure mode is live and general: any session that
  QUOTES the marker into a commit message fires a ride it did not intend, and
  the drivers are now instructed to write about that marker.  The fence
  cannot be the workflow: `.github/` is trust-surface PROTECTED, and
  narrowing the match there would turn this into a maintainer-merged ceremony
  for a defect the text can fix.  So the fence is the TEXT — exactly ONE
  bracketed occurrence in `C3_PROMPTS.md` (the commit instruction itself),
  none in the artifacts a driver is told to quote (`supply_status`'s
  `attendance_routes` is unbracketed for precisely this reason), and the rule
  stated where a driver reads it and in CLAUDE.md's invariants.  Both halves
  are toothed in `tests/test_authoring_route.py` by COUNTING occurrences, not
  by asserting the rule is written down.  Recorded because the near-miss is
  instructive twice over: the trigger was discovered by tripping it, and the
  first marker tooth in that same file had already failed to bite for the
  mirror-image reason — it matched the lane's name in surrounding prose.
- **C3 cycle 21 — path (c) was walked unattended for the first time, and it
  refused AT THE WIRE** (`results/c3_cycle_21.md`).  The declared row cycle 20
  waited for existed (merged as #140), the selector answered
  `candidate-available`, and the driver ran the printed
  `intake_corpus.py` command verbatim — and the fetch was **refused by egress
  policy**: `Tunnel connection failed: 403 Forbidden`, recorded proxy-side as
  `connect_rejected` for `alexkontorovich.github.io:443`.  NOT retried: the
  hiccup protocol's backoff is for 5xx and timeouts, and the proxy runbook
  says in its own words not to retry a policy denial — the same rule
  `lean_env_probe` states one layer up and PR #142 one layer down.  The row is
  marked `refused` with the reason and STANDS as evidence.  **What it measures
  is REACHABILITY, not distance from the fragment**: the adapter never ran and
  not one page was fetched, so nothing whatever was learned about the corpus,
  and the two kinds of no must stay distinguishable.  The declaring session
  named this outcome in advance and took the trade deliberately — a refusal
  costs one cycle and buys a measurement; declaring nothing costs every cycle
  and buys none.  **So path (c) now needs something the last row did not have:
  a host this container's egress policy ALLOWS.**  Declaring a second row
  against an unknown host buys the same measurement again; establishing which
  corpus hosts are reachable at all is the cheaper next move, and it is a
  question no session can answer for itself.
- **The walk exposed an instrument defect, and it is the attendance filter's
  defect one path over** (same cycle).  `tools/supply_status.py` computed
  `machine_actionable: true` for `new-corpus-intake` from a LEXICAL grep of
  `C3_PROMPTS.md` for `intake_corpus` — which says the driver KNOWS the
  command, never that it has a row to run it on.  On the very firing whose
  selector answered `registry-exhausted`, the verdict still named that path as
  an exit, and the watchdog quotes the verdict VERBATIM as the sole alarm
  channel.  Closed by THE DECLARATION FILTER: `machine_actionable` now needs
  BOTH halves, and the declaration state is **asked of
  `tools/corpus_candidates.select`** rather than re-derived — two
  implementations of one rule drift, and that drift is the defect.  A dry
  registry stays `available` (the supply is outside the tree; an attended
  session may name any corpus, and it is what keeps a blocked verdict from
  degenerating into a bare word) and is NOT machine-actionable; an absent or
  unreadable registry reads as its own named reason, never as "no candidates".
  The reason rides in the verdict string itself
  (`declaration: registry-exhausted -- NOT unattended-takeable`).  Five teeth
  in `tests/test_supply_status.py` pin it in both directions, one of them over
  the COMMITTED tree; mutation-verified twice.
- **The authoring ride is OUT OF ROUNDS — all three open rows, measured**
  (`results/reflect_channel_exhausted.md`).  The second route rule 3 names for
  a policy-denied container ran five rounds on `refusal-symbolic-exponent`, two
  on `refusal-function-symbol` and two on `refusal-set-carrier`, every one
  PASSED, and each row's queue then closed on ITS OWN committed class
  measurement: `tests/test_symbolic_exponent_class.py` (the `evalTm`,
  `substTm`, `evalTmN`, `substTm_evalTm`, `evalTmN_subst` and `check`/
  `decDenote` cases), `tests/test_function_symbol_class.py` finding (4) (which
  prices the rung at EXACTLY TWO costs in its own docstring — an application
  node and a new `Decidable` story), and `results/c3_cycle_16.md` line 93 (a
  set can be counted but never **inhabited**, **named** or **compared**).  Each
  closure was re-verified against the measurement rather than taken from the
  receipt's word, because the reading had been living in three per-row receipts
  and a firing does not start by reading those — it starts at the brief, which
  quotes THIS section.  So it is written here: the unattended authoring channel
  has NO further round on any currently open row, and extending it needs either
  a NEW class measurement naming a construct no prototype has taken or a NEW
  open row, neither of which is an unattended session's to manufacture.  The
  standing consequence: with the probe reading `lean-absent` and no open row
  additive-class, the purchase axis's yield is TOTAL and its own fallback is
  now empty too — every remaining exit on both axes is a maintainer's.
- **And `attendance_routes` still names that exhausted ride as an exit** (same
  receipt) — the LEXICAL-GREP defect cycle 21 closed for `new-corpus-intake`,
  recurring one path over: `tools/supply_status.py` reports that the driver
  KNOWS the route, never that the route has a round left, and the watchdog
  quotes that verdict VERBATIM as the sole alarm channel.  Recorded and NOT
  fixed, deliberately.  The declaration filter worked because
  `corpus_candidates.select` could be ASKED — the state was mechanically
  derivable from a committed registry.  Here it is not: "does this row's class
  measurement name anything still unmet?" is a judgment recorded in receipt
  prose, and grepping those receipts for it would re-commit the very defect it
  means to close.  A mechanical route would need the queue rows to carry their
  own terminal flag — a schema change, and an ATTENDED call.
- **P8 PURCHASED — named function symbols, and the row SPLIT in two**
  (`results/p8_delta.md`).  A `definition` statement now lets a source NAME a
  function with an EXPLICIT body over its own parameters, and `{"app": f,
  "args": [...]}` applies it — **at a SYMBOLIC argument**, which is exactly
  what the literal-index unfolding could never reach
  (`tests/test_function_symbol_class.py` test (8): dropping the index leaves
  the object unconstrained and the reading asserts something WEAKER than the
  source).  **The row answered its own design question rather than assuming
  it, and this is the third time that has paid.**  Finding (4) priced the rung
  at an application node in `Tm` PLUS a new `Decidable` story, on the argument
  that "an uninterpreted symbol constrained only by axioms has no computable
  interpretation" — correct about an UNINTERPRETED symbol, and the reason this
  row bought a DEFINED one instead.  An explicit non-recursive body is
  ELIMINABLE: the gate desugars every application by capture-free substitution
  (`_unfold_term`), so `generators/math_eval.py`, `math_smt.py`,
  `math_compile.py` and `tools/FgReflect.lean` are **all four byte-unchanged**,
  `decDenote` keeps deciding by computation, and §3.1 rule 3(a) is not reached.
  Landed **additive-desugaring**, P6's shape; the class measurement's own test
  still passes unchanged, because every word of it stays true of the slice.
  Conservativity is executable rather than argued: every definition reading is
  measured against a HAND-UNFOLDED twin at all four consumers
  (`tests/test_funcdef_battery.py`) — same eval verdict on a box, byte-identical
  SMT rendering with **z3 and cvc5 both returning `unsat` on the negated
  biconditional** (equivalence for all n, not just the box), byte-identical
  `lean_text` and `statement_hash`.  **What was NOT bought is the headline:
  the RECURRENCES.**  A body applying itself has no finite unfolding at a
  symbolic index, and it refuses by name as `funcdef:recursive-body`, joined by
  `funcdef:binder-body` (which makes the substitution capture-free BY
  CONSTRUCTION) and `funcdef:open-body`.  So `definitional-extension` was **two
  rungs wearing one name**; the non-recursive one is bought and the recursive
  one is what the new refusal prices.  The refill is honestly expected to be
  SMALL OR ZERO — the class measurement had already capped this row at five of
  eleven subjects, and nine of the eleven are recurrences — and the number of
  record is the next corpus cycle's `intake_from_frontier --unblocked
  refused:function-symbol`, never this bullet.  Re-census delta **ZERO,
  byte-identical and structurally so** (the P4 shape: the portfolio census is
  lexical and a mechanism moves no vocabulary) — and measured TWICE, because
  cycle 22 (#184) merged mid-session and moved the portfolio from 6 corpora /
  1008 nodes to **7 / 1952**, and cycle 23 (#187) then recorded the analytic
  corpus's refusals: byte-identical at all three readings, and the last is the
  one of record because it is the tree the purchase lands on.  **A second
  instrument defect fell out of it**: the refill projection totalled OPEN rows
  only, so a purchase's subjects vanished from it the moment it landed while
  still sitting demoted in the append-only ledger — the artifact read `0 ready,
  nothing would refill it` over supply already paid for.  Closed by
  `awaiting_unblock_run`, which measures **23 subjects** — the accumulated
  P6+P7+P8 backlog awaiting a corpus cycle's `--unblocked` run, NOT P8's alone,
  and an upper bound on the projection's usual terms.  Taken by an unattended firing
  under a MEASURED `lean-local` verdict corroborated by direct elaboration —
  and worth separating, because the two facts are independent: that permission
  licenses tower-class work, and the measurement then said this row is not
  tower-class, so the bill would have been takeable in a Lean-absent container
  too.
- Next actions, honestly stated: **(c), then a purchase** — and after cycle 20
  those are the ONLY two, because path (d)'s zero-cost inventory measured out
  at zero.  A corpus DRIVER firing can reach exactly one lever unattended:
  (c), which needs a **declared near-fragment corpus** and nothing else — one
  appended row in `specs/mathsources/corpus_candidates.json`, whose URL and
  rationale a human writes before any yield is known, and (cycle 21) whose
  HOST the egress policy must permit.  Until one is declared, every corpus
  firing will guard-pass, find no ready entry, no met refusal
  group and no declared candidate, and exit — a starved loop with a healthy
  heartbeat, which is a SUPPLY reading and not a dead chain, and which the
  supply verdict now says in the words `declaration: registry-exhausted --
  NOT unattended-takeable` instead of naming an exit nobody can walk.  (d) is
  now wholly purchase-gated: `results/purchase_frontier.json` prices it, the
  open rows are `refusal-symbolic-exponent` (12 memberships),
  `refusal-function-symbol` (11) and `refusal-set-carrier` (4), and cycle 20
  names one more the queue does not yet carry — an **atom-lexicon** row for
  `>`/`>=`, the cheapest-looking of the four and the only one whose whole
  demand is 3 nodes.  Path (a) stays open but is no longer a reason to buy a
  carrier, and path (b) supplies nothing until something is parked.  The
  **mathlib import waves the Rat unlock opened** (+27 `in_fragment`, `Field`
  0→9 / `Ring` +10 / `Coe` +9 in `unlock_counts`) remain the measurable
  blocker-behind-the-blocker on the tower side.  The ℚ reflect tower
  (`evalTmQ/denoteQ/…`) stays the named CI-lane follow-up, as does the
  elaboration of the `zmodEq` image.  **P5 is NEVER a next action**: the
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

Driver sessions run in remote containers where the Lean toolchain is not
local — MEASURED, not assumed: `tools/lean_env_probe.py` reads this
container and, today, reports
`lean-absent:policy-denied:elan.lean-lang.org,release.lean-lang.org`, i.e.
the egress gateway answers 403 to CONNECT for exactly the two hosts that
serve the toolchain BINARIES (the git hosts answer fine, so it is the
binaries and nothing else).  That is an environment setting rather than a
law of the loop; `docs/lean-capable-environment.md` is the runbook for
changing it, and rule 3 below is written so that changing it changes what
an unattended session may do.  While it holds, every Lean-touching step
pays a CI round-trip — commit → `[lean-fast]`/`[lean-ci]` lane → verdict — and
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
   these two clauses are what replaces the breaker.)  The COUNT clause is
   MECHANIZED as far as the ledger can see it: `tests/test_wake_budget.py`
   reds when one branch — the ledger's name for a session — carries more
   than two wake-bearing telemetry rows (one row per push, per the purchase
   prompt's RECORD EVERY WAKE clause), and skips BY NAME until the first
   cycle logs a `wake` stage, since a silent pass over an empty ledger would
   read exactly like a satisfied cap.  The distinct-root-cause half is NOT
   checkable against the current schema — the ledger records seconds, not
   causes — and the test says so in writing rather than faking it; an
   optional `wake_cause` slug on the row is the minimal change that would
   close it, and adding one is its own writer purchase.
3. **Two tracks, one Lean dependency.**  The corpus axis (intake →
   census → sources → readings → bench → mine → regenerate) is Lean-free
   and fully verifiable in-container — it NEVER blocks on the lane.  The
   two tracks are independent in EXECUTION only; in SUPPLY each is the
   other's feedstock, and neither runs forever alone: the corpus track's
   ready list refills by exactly FOUR paths — §3.2 states all four with
   their measured state, and an earlier reading of this rule named only
   the first two — while the purchase track prices its next bill from what
   the corpus track measured, the refusal ledger and the frontier's blocked
   groups, which name their unblocking purchases.  So an idle corpus track
   is a reading about SUPPLY, not an idle loop, and the first question it
   asks is which of §3.2's four paths is available.  A
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
   attendance buys.  The STRUCTURALLY CHECKABLE half of this rule —
   (a), (c) and (d), which are facts about the slice's text rather than
   judgements — is MECHANIZED, not prose: `tests/test_fg_reflect_shape.py`
   pins the slice's constructor, instance and import surface as tuples in
   `kernel/certs.py`'s idiom, so a purchase that leaves the additive class
   reds the suite in the container that authored it instead of in the
   maintainer's reading, and growing a pin becomes a deliberate, reviewable
   line of the same diff.  (No done-condition of this loop may live only as
   prose — that is the defect that let the census's dead terms sit
   unmeasured.)
   **The capability condition (what makes the rule above conditional at
   all).**  The reason an unattended session does not take tower-class work
   was never governance: it is that a container with no toolchain authors
   Lean BLIND, one CI round-trip per iteration, and cannot converge inside
   a session.  That is a claim about a CAPABILITY — and this rule used to
   spell the capability as permanently absent, because on the day it was
   written it was.  A condition written as a constant is a measurement
   nobody takes again, so it is measured now: `tools/lean_env_probe.py`
   writes `results/lean_env.json` carrying a verdict from a tiny fixed
   vocabulary (`lean-local` / `lean-absent:policy-denied:<hosts>` /
   `lean-absent:not-installed` / `lean-unknown:<why>`), checking the two
   directories `kernel/backends.py`'s `_lean_mounts` actually mounts and,
   on an absence, WHY — separating an egress POLICY DENIAL (which no re-run
   of `setup.sh --with-lean` can fix; `docs/lean-capable-environment.md` is
   the operator runbook) from a plain not-installed, since those two have
   opposite fixes and conflating them wastes the reader's next move.  When
   the probe RUN IN THIS SESSION reads `lean-local`, an UNATTENDED session
   MAY take tower-class work: it can iterate to green locally, which is the
   thing attendance was buying.  On ANY other verdict — `lean-unknown`
   included — the additive-only rule above binds UNCHANGED; an unreadable
   measurement is not a permission.  There is a SECOND route to the same
   capability when the probe reads lean-absent — the `[lean-hammer]` batch
   ride's AUTHORING kind (`results/reflect_candidates.json` →
   `run/reflect_ride.py`, PLAN_HAMMER.md H-H1.3), which elaborates proposed
   slice text spliced into `tools/FgReflect.lean` under the same
   two-run/fail-closed discipline and so lets an unattended session iterate on
   tower-class material at all, with the honest bound that it iterates at a
   SESSION BOUNDARY per ride — one round-trip per push, not per minute — and
   that the lane verdict remains FINAL exactly as in clause (i), so a passed
   candidate is a reason to keep authoring and never a done-predicate.  Two
   clauses keep this from softening into a loophole.  (i) A local green is
   NECESSARY, never SUFFICIENT: the
   CI Lean lane remains the FINAL verdict exactly as before, rule 2's
   Lean-last batching is untouched, and "it elaborates here" is a reason to
   push, never a done-predicate.  (ii) The probe is a reading of the
   CONTAINER that ran it, so it must be RUN, never read off disk — a
   committed `results/lean_env.json` saying `lean-local` is evidence about
   the machine that wrote it and licenses nothing for the machine reading
   it.  The trust surface is untouched, deliberately: a local toolchain
   changes NOTHING about P5 or the anti-list
   (`buildloop/growth_protocol.py::ANTI_LIST`, §5).  Those are GOVERNANCE,
   not infrastructure — they never move on capability, only through the
   PLAN_REFLECT S4a→S4a′→S4b ceremony with explicit maintainer sign-off,
   and a session that can elaborate locally has bought exactly one thing:
   faster iteration inside the fence.  The mechanism is named here on
   purpose (`tools/lean_env_probe.py`, teeth in
   `tests/test_lean_env_probe.py`) so the rule and its measurement cannot
   drift apart.
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
   prose is a number that will rot.  One amendment there IS worth recording
   here, because it moved a trust boundary rather than a schedule: a
   purchase whose only ceremony touch is a GROWERS-row addition to the
   growth registry now reads GREEN on `trust-surface` and SELF-MERGES
   behind a mechanical proof —
   `tools/purchase_bill_manifest.py::conforming_registry_diff`, an excision
   predicate demanding everything outside the GROWERS/`SIGNATURE_PINS`
   spans be byte-identical, so `ANTI_LIST` stays fenced by default — a
   narrowing that landed as a maintainer-signed ceremony PR and green-lights
   only what the machine can prove, leaving every other ceremony match red
   for the human.  The one figure worth keeping is the
   retired chain's **+75 min** Lean delay: a session that pushed Lean-tagged
   work scheduled the next cycle over an hour out purely so the lane verdict
   would exist by then.  Wake-on-red (rules 1 and 2) deletes that wait —
   the verdict comes to the session that caused it, ~2 min after the push
   (`results/latency_baseline.md`), rather than the session paying an hour
   to meet it.  The canonical prompt texts for both Routines live in
   `C3_PROMPTS.md` (versioned; each Routine's stored Instructions are only a
   pointer at this file, so prompt fixes ship by git merge instead of
   freezing into the chain).

### 3.2 SUPPLY — the four paths that refill the ready list

The corpus loop consumes `results/frontier.json`'s `ready` list and nothing
else, so SUPPLY is the loop's only real failure mode: it does not crash, it
STARVES.  This subsection exists because the loop starved once already with
two of its four refill paths undocumented, and a path nobody has written down
is a path no Routine can run.  **An empty ready list is NOT evidence the
corpus is exhausted.  It is evidence the FRAGMENT cannot yet speak what the
corpus asked for** — the census still holds 1008 nodes and the frontier still
holds 28 blocked groups; what is missing is vocabulary, not material.  There
are exactly four ways material re-enters `ready`, and each has a MECHANISM
that runs it and a MEASURED state that says whether it can supply anything
today (live numbers: the brief and §1, never this paragraph):

- **(a) A purchase un-gates a CENSUS signal.**  Mechanism: a §4 purchase
  retires a miss signal, the re-census moves out-of-fragment nodes to
  attempt-candidate, and the next cycle runs `python3
  tools/intake_from_frontier.py --unblocked SIGNAL --take N` before the
  frontier is regenerated.  MEASURED EMPTY: P3 and P4 both returned a ZERO
  portfolio delta.  The reason is structural and worth stating once, so no
  future session re-buys a carrier expecting a refill — **the portfolio census
  is LEXICAL.**  It matches fragment words and miss-signal substrings against
  node TEXT; a carrier moves no vocabulary, so `ZMod n` added no census word
  at all, and `Rat`'s 22 word-gains flipped no verdict because signals
  dominate a node's classification.  This path supplies only when a purchase
  retires a SIGNAL, and the census is where that is measured, never argued.
- **(b) A decision PR lifts PARKS.**  Mechanism: the decision lane
  (`C3 decision:` PRs, whose maintainer MERGE is the sign-off, fenced by the
  un-park check) removes rows from `results/frontier_parks.jsonl` and the
  regenerated frontier returns those subjects to ready.  MEASURED EMPTY, and
  structurally so: **the park ledger has ZERO rows.**  No cycle has ever
  parked a subject, so there is nothing to lift.  The lane is built and
  tested; it simply has no inventory, and it acquires some only when a future
  cycle parks a certifying subject behind a governance decision.
- **(c) NEW-CORPUS INTAKE — the only lever that has ever moved the ready
  list.**  Mechanism: `python3 tools/intake_corpus.py --name X --source URL
  --adapter blueprint|sphinx`, then `tools/census_portfolio.py` +
  `tools/regen_downstream.py`, then a `registration.json` lineage entry — one
  command and the standard regen chain, with the intake discipline unchanged
  (`nodes.jsonl` + `fetch_meta.json`, per-page SHA-256, NETWORK-AT-INTAKE
  ONLY; everything downstream stays offline and deterministic).  Every ready
  entry the loop has ever consumed traces back to this path (the math2001
  intake of C2 is the worked example).  It was NOT AUTOMATED: the tool existed
  from §3.1 rule 4 onward but the driver prompt exited on an empty window, so
  no Routine could reach it — the gap that let a working lever sit unused
  while both loops idled.  **It is now MECHANICALLY RUNNABLE by an unattended
  Routine**, and the way that was made honest is worth stating in full,
  because the obvious automation is the forbidden one.  One rule binds this
  path: a corpus is chosen NEAR THE FRAGMENT, never picked to manufacture a
  green — a corpus intaken because it would certify is the census lying to
  itself.  A session that picks its own corpus picks the one that looks like
  it would certify, so the refusal to pick was load-bearing and is NOT
  deleted.  What changed is WHERE the judgment sits.  Draw the line:
  **SHOPPING** is choosing a corpus BECAUSE it would certify or move a number
  — outcome-driven selection, forbidden forever, because it distorts the
  measurement this whole system exists to protect.  **SELECTION** is
  consuming a PRE-DECLARED list in a fixed order — mechanical, and carrying
  no such distortion.  The DECLARATION POINT is
  `specs/mathsources/corpus_candidates.json`: a human writes one row per
  corpus (name, source URL, adapter, project, `declared_by` provenance, and a
  written `rationale` saying why it is near the fragment) BEFORE any yield is
  known, and `tools/corpus_candidates.py` then returns the first row still
  marked `candidate` in DECLARATION ORDER.  That selector is yield-blind BY
  CONSTRUCTION, not by good intentions: it reads the registry and nothing
  else — no census, no frontier, no queue — and `tests/test_corpus_candidates.py`
  inspects its source to assert that no such artifact is named anywhere in
  it, because a selector that cannot see yield cannot rank by it.  Ordering
  is therefore the maintainer's declared priority, and reordering a row to
  put a more promising corpus first IS the shopping above, spelled as a diff.
  Outcomes are recorded ON the row (`--mark NAME intaken`, or
  `--mark NAME refused --reason TEXT` when the fetch or adapter refuses or
  the re-census reads the corpus as far from the fragment) and the row STAYS:
  evidence, never inventory, and a refusal is data rather than a silent retry
  with a different corpus.  Say the net effect plainly, so no later session
  mistakes it for a relaxation: **the human judgment moved from per-cycle to
  per-candidate.  It did not disappear.**  MEASURED TODAY: the registry
  declares ZERO `candidate` rows (six retrospective `intaken` rows recording
  the corpora already consumed, plus one documentation row the selector
  skips), so the selector answers `registry-exhausted` — a NAMED reason, not
  a crash — and the first row a maintainer appends turns this path on with no
  further code.
- **(d) Retiring a measured REFUSAL signal — the fourth path, and the one
  with inventory today.**  Mechanism: the fragment gains the primitive a
  named refusal signal demands, and the next cycle pulls the group back with
  `tools/intake_from_frontier.py --unblocked refused:<signal> --take N` (the
  tool takes ANY blocked group, `refused:` groups included).  The ledger stays
  APPEND-ONLY: rows are evidence and stand as the pre-purchase reading — a
  later measurement of the same subject at a grown fragment is a NEW reading,
  not a re-measurement to force a green, and it may refuse again.  Why this is
  the best demand the system has: a `refused:` subject **already passed
  selection** and was then demoted by a MEASURED certification failure, so it
  is demand the machine proved, where a census signal is a lexical prediction.
  Precedence is what holds them out — `tools/frontier.py` applies refused
  before ready — and 61 subject-rows across 15 groups (45 distinct subjects; a
  subject under two signals returns only when both are met) are waiting behind
  it.  §4's P6–P9 price the four largest groups.

Two properties of this list are worth keeping in writing.  First, it is
EXHAUSTIVE by construction: `tools/frontier.py` demotes a candidate for
exactly three reasons (already intaken, refused, parked) and admits new
candidates only from a re-census, so (a)–(d) enumerate the ways the
projection can change.  Second, paths (a) and (d) are BOTH purchase-driven
but priced differently — (a) is priced by census vocabulary and (d) by
measured refusals — which is why `results/purchase_frontier.json` carries
both prices per row and why a queue entry that names one must never be read
as promising the other.

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

- **P1 — bounded big-operators — PURCHASED** (`results/p1_delta.md`; prices
  sequences-sums: 45 in PFR; high
  frequency in every corpus).  A binding AST node CLASS — Σ/Π with an
  explicit literal bound — not an operator word: F-G is first-order today,
  so this is the one structural extension.  Bounded iteration is exactly
  what the repo already trusts: decidable by exhaustive computation, SMT
  by unrolling, Lean via `Finset.range`.  Largest single ROI; everything
  later rides its binding machinery.
- **P2 — bounded Finset carrier + card — PURCHASED**
  (`results/p2_delta.md`; sets-cardinality: 24).  Rides
  P1's binding machinery; same bill.
- **P3 — ℚ carrier — PURCHASED** (`results/p3_delta.md`; the
  mass-arithmetic slice of probability-entropy's
  111).  Rational arithmetic is decidable for the fragment's relations;
  finite distributions with rational masses become expressible WITHOUT
  touching `log`.  Requires a census signal split (probability-mass vs
  entropy-log) so the delta is honestly attributable, plus the D8-class
  divergence battery against Nat/Int.
- **P4 — concrete algebra: `ZMod n` carrier — PURCHASED**
  (`results/p4_delta.md`; algebra-structures: 49,
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
- **The REFUSAL-PRICED rows (P6–P9), and what makes them different.**
  P1–P4 were priced by CENSUS vocabulary; the four rows below are priced by
  MEASURED REFUSALS — §3.2 path (d) — i.e. by subjects that already passed
  selection and were then demoted when certification failed on a named
  missing primitive.  Nothing else changes: the same full bill above, the
  same done-predicates, and strict tractability order among themselves.  What
  changes is how the delta is READ.  A census-priced purchase owes a census
  delta; a refusal-priced purchase owes its `refused:<signal>` group returning
  to the intake window (`intake_from_frontier --unblocked refused:<signal>`,
  measured the cycle AFTER it lands) — and it may still measure zero, because
  a subject blocked by two signals returns only when both are met.  Neither
  price is a fidelity claim, and a subject RETURNING to ready is a selection
  fact, never a prediction that it will certify.  Counts below are group
  MEMBERSHIPS at the cycle-17 standstill; the derived queue
  (`results/purchase_frontier.json`) is what projects how many distinct
  SUBJECTS each row would actually return, and those two numbers are never
  the same one.  Live numbers come from there and from
  `results/frontier.json`, never from this paragraph.
- **P6 — propositional connectives: `not` and `iff` — PURCHASED**
  (`results/p6_delta.md`; refusal-priced: 21 subject-rows — `not-connective`
  6, `iff-connective` 8, `definition-biconditional` 7 — the largest single
  demand on the board, and the one cycle 16's `09_Sets` block named three
  times over).  The full bill, paid: validator + lexicon, eval, SMT mirror,
  Lean rendering, differential + symbolic batteries, growth-registry row
  (`connective-node-class`), teeth.  **The DESIGN QUESTION this row declared
  it would MEASURE rather than assume, and its answer.**  The row was
  declared tower-class because a `not` CONSTRUCTOR in `Pd` is a new
  constructor plus a new `Decidable` instance (both pinned by
  `tests/test_fg_reflect_shape.py`) and therefore ATTENDED-ONLY.  The
  measurement says negation needs no constructor: every atom the fragment
  carries has its dual IN the fragment (`=`/`!=`, `<=`/`<` **with the
  arguments swapped**, `even`/`odd`), so negation-normal form pushes `not`
  down to an atom, and `iff` unfolds to the `and` of two `implies`.  Nothing
  enters `Tm`/`Pd`; §3.1 rule 3(a) is not reached at all.  Landed
  **additive-desugaring** — a bill class the queue had no name for, because
  no earlier row grew vocabulary without growing something that represents
  it.  The atoms with NO dual are `dvd` **and** `coprime` (the design note
  named only `dvd`, which is the answer for `Pd`; at the level the GATE
  freezes there are two), so a negation reaching either is
  `not:<op>-no-dual` — first-class demand for the negation-constructor
  purchase this row declared and deliberately did not make.  Declaring the
  larger bill is what kept the smaller from being claimed before it was
  shown, and the row did not soften §3.1 rule 3 to fit.  The reflect slice's
  QUOTING of the two words rides a later commit; until it lands, a reading
  using them keeps the existing fail-closed `op-out-of-reflect-slice:` skip.
  `definition-biconditional`'s 7 rows are counted here because `iff` is their
  FIRST blocker, and kept named apart because a DEFINITION may still need
  P8's mechanism underneath.  The refill this buys — **13 distinct subjects**
  by the derived queue's projection — is realized by the NEXT corpus cycle
  through `intake_from_frontier --unblocked`, and that cycle's measurement,
  not this projection, is the number of record.
- **P7 — symbolic exponent** (refusal-priced: 12 subject-rows,
  `refused:symbolic-exponent`; measured repeatedly in cycles 12–15 on `2^n`,
  `4^n`, `3^n`, `(n+1)! >= 2^n`, where `^` refuses anything but a
  non-negative LITERAL exponent).  **P1's receipt already named this class**:
  `results/p1_delta.md` recorded P1's zero re-census delta with its cause —
  the corpus's sums are symbolic-bound — named the refusal
  `bigop:symbolic-bound`, and stated that the next iteration-class purchase
  targets symbolic bounds.  Two receipts now point at the same missing thing
  from opposite directions: a BOUND that is a variable and an EXPONENT that
  is a variable are one demand.  Ranked below P6 because it reaches past
  vocabulary into PROOF SHAPE — no literal box unrolls a symbolic exponent —
  so an honest bill includes whatever discharges it (an induction principle,
  or an exponent-bounded sweep carrying its own divergence teeth), and it is
  tower-class until argued otherwise.  Same full bill.
- **P8 — function symbols — PURCHASED, and SPLIT** (`results/p8_delta.md`).
  The declaration below stands as written, and the measurement split it: the
  NON-RECURSIVE half is bought (an explicit body is eliminable, so the gate
  desugars every application and all four consumers plus the reflect slice are
  byte-unchanged — landed additive-desugaring, P6's shape), and the RECURSIVE
  half is not, refused by name as `funcdef:recursive-body`.  "An extension
  mechanism must be CONSERVATIVE, and arguing that is the purchase's real
  cost" — the paragraph below called that correctly, and the answer was to
  make it EXECUTABLE rather than argued: every definition reading is measured
  against a hand-unfolded twin at all four consumers, dual-solver included.
  The overlap with `defined-predicate` and `definition-biconditional` the row
  said to MEASURE afterward is still unmeasured and still belongs to a corpus
  cycle.  Original declaration, unedited:
- **P8 — function symbols** (refusal-priced: 11 subject-rows,
  `refused:function-symbol` — factorial, the sequences `a_n`/`d_n`/`F_n`, the
  Bezout coefficients).  The missing thing is a DEFINITIONAL-EXTENSION
  mechanism: a way for a source to NAME a function and for the reading to
  carry that definition with it.  No carrier and no bounded node class
  supplies one, which is why the signal has sat at `None` in
  `tools/purchase_frontier.py::SIGNAL_UNBLOCKED_BY` — an honest statement
  that the queue could not meet the demand, and the gap this row closes.
  Same full bill, plus the part that is genuinely hard: an extension
  mechanism must be CONSERVATIVE, and arguing that is the purchase's real
  cost.  Ranked below P7 because it grows a MECHANISM rather than a
  vocabulary; its overlap with `defined-predicate` (1) and
  `definition-biconditional` (7) is a thing to MEASURE afterward, never to
  claim in the bill.
- **P9 — SPLIT AND HALF-PURCHASED** (`results/p9_delta.md`).  The row below
  billed two rungs as one, and the measurement
  (`tests/test_set_object_class.py`) drew the line its own prose had already
  drawn: a set the source GIVES A COMPREHENSION FOR is eliminable
  (`e ∈ {x | φ(x)}` IS `φ(e)`), and a set it does not is not eliminable at any
  price.  The first half is PURCHASED as `refusal-set-comprehension`
  (definitional-extension, all four consumers byte-unchanged).  The second is
  what `refusal-set-carrier` now names and still costs: an uninterpreted
  predicate in the SMT mirror and a `Pd` constructor plus its `Decidable`
  story in the reflect slice, priced under two signals kept APART
  (`free-set-variable`, `set-valued-param`) because retiring either leaves the
  other refusing.  MEASURED against the row's own inventory: of the four
  subjects only `09_Sets#definition-003` needs the residue,
  `#problem-014`/`#problem-015` carry a ℤ/ℕ carrier mismatch in the prose (the
  second REFUTED at a single carrier — a truth fact no purchase returns), and
  `#problem-017` is reachable only by the degenerate unfolding cycle 16
  already recorded as coverage-not-set-coverage.  So "a large purchase against
  a small measured demand" was right, and the honest demand is smaller still.
  Original declaration, unedited:
- **P9 — set carrier + membership** (refusal-priced: 2 subject-rows,
  `refused:set-membership`, plus the cycle-16 measurement that produced them,
  `results/c3_cycle_16.md`).  P2 bought `setbuild` only as `card`'s ARGUMENT,
  so a set can be counted but never inhabited, named, or compared; membership
  over a set OBJECT is a different purchase, and the census-priced
  sets-cardinality count must never be re-read as its price.  Cycle 16
  measured both sides of the boundary in one cycle: source 121
  (`1 ∈ {n : ℤ ∣ n ≤ 3}`) SHIPPED precisely because its membership unfolds
  definitionally to `1 ≤ 3` — which is why that green is NOT evidence of set
  coverage — while every other `09_Sets` subject refused.  The signal is for
  set objects that SURVIVE unfolding.  Ranked last on both counts: it needs
  set objects as first-class carrier values (tower-class), and 2 rows is the
  smallest inventory on the board — smaller still once read honestly, because
  BOTH of those subjects also carry a connective refusal, so on today's
  ledger this row on its own returns ZERO subjects to ready (the derived
  queue projects exactly that) and only lands material behind P6.  A large
  purchase against a small measured demand is the reading this row should
  carry rather than bury.  Same full bill.
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
