# PLAN_REFLECT.md — driving the reflection program to completion

Status: ACTIVE — the standing packet for any session (human-started or
Routine-fired) that picks up the reflection program.  A fresh session should
read this file FIRST, then `git log --oneline -10` on the working branch,
then act.  House rules: every done-condition below is a predicate a test or
the Lean lane evaluates — none exists only as prose.

## 0. The program in one paragraph

Proof by reflection: represent a checkable problem as data inside Lean, give
it a computable checker and a Prop denotation, prove the checker sound ONCE
(kernel-checked), and thereafter its verdicts are theorems by computation.
Targets, in dependency order: **T1** the F-G fragment's decidable layers
(`tools/FgReflect.lean`), **T2** the verified witness-template checker,
**T3** the verified reading→Lean compiler.  Each target's formalization is
the next one's foundation.

Sibling packet: `PLAN_FRAGMENT.md` drives corpus↔fragment gap closure (the
census flywheel + the vocabulary purchase queue).  The coupling runs both
ways: every fragment purchase there must extend the reflect slice here (a
constructor + Decidable instance, lane-checked), and any new discharge
route it wants reuses THIS packet's S4a→S4a′→S4b shadow→promotion pattern.

## 1. Verified current state (update this ledger every iteration)

- T1 v0 (Int slice: = <= < over lit/var/+/-/*; check/denote/Decidable;
  `check_sound`/`check_complete`/`checkAll_sound`): **kernel-checked green**
  (lean lane, run 29992746291, commit 703e7eb).
- T1 v0.1 (tmod; pne/pdvd/peven/podd) + **T2 core** (subst machinery,
  `witness_of_check`, `checkAll_witness`) + **S2 dvd bridge** + **S5 Stmt
  layer**: **kernel-checked green** (lean lane run 29997957079,
  2026-07-23 10:09 — `test_elaborates_under_lean` passed on the full
  module).
- Flywheel probe: **live** — same run closed all 9 typed corpus props
  through the ladder (`test_probe_closes_ground_props_under_lean` green).
- S4a shadow probe: first lane run RED (namespace scoping: the quoter's
  unqualified constructors appended outside `namespace FgReflect`); fix
  = re-enter the namespace around the example — **verdict GREEN** (lean
  lane run 29998311090 on d002e78, 2026-07-23 10:15: full lean job
  passed, so the probe elaborates = agreement row #1).  The follow-up CI
  commit 33c605e also ran the lean job green (run 29998949426).  PR #17
  merged all of the above into main (0b0444b).
- S5 COMPLETE + S6 first shape: **kernel-checked green** (lean lane run
  30000411679, commit 2d13b43, 2026-07-23 10:48).  S5 = the box layer
  over full quantifier prefixes (`denoteStmtBox`/`checkStmtBox`,
  `checkStmtBox_sound`, the `exOnly` bridge landing ∃-only prefixes in
  the true denotation, `checkAll_sound_stmt`/`checkAll_witness_stmt`
  lifts).  S6 shape 1 = guard-shape preservation (`sall_guard_iff`,
  `compile_guard_shape`, `sall_guard_of_check`).  One lane iteration was
  red first (run 29999849337: instance search cannot unfold
  denoteStmtBox to reach decDenote; fixed by routing the base case
  through `check_sound`).
- The lean job's pytest list lives in `.github/workflows/ci.yml` (search
  `test_fg_reflect_lean`); the lane fires on commits whose message carries
  `[lean-ci]`.
- S4a′ first evidence (lane run 30032983482, [lean-fast], commit
  4c50204): the 5 committed ∃-class readings all emitted probes; ledger
  seeded (artifact sha256 d86c6202…, committed back verbatim): **3
  agree** (43_larger_integer_exists, 53_pos_pred_witness,
  54_double_witness), **2 disagree** (52_gap_witness, 55_sum_exists).
  Root-cause HYPOTHESIS for both disagreements (unconfirmed — the
  transcripts died with the runner): they are exactly the two largest
  boxes (153 and 289 envs vs 8–17 for the agreeing three), so the Lean
  DEFAULT elaboration budget (200000 heartbeats) starves the full-box
  `rfl` evaluation.  Fix iteration: whitelisted
  `set_option maxHeartbeats` cap in the probe + the sweep report joins
  the CI artifact so transcripts survive.  NOTE: the four new sources
  were renumbered 52-55 → **63-66** after the first ledger rows were
  written (slots 52-62 are reserved by the WP-SRC2 staged batch; the
  fast-lane manifest/promotion teeth caught the collision), so ledger
  rows from run 30032983482 name the OLD files; statement_hash is the
  stable join key.
- Disagreement root-cause **CONFIRMED** (runs 30033836721 / 30034226779,
  both lean-green; ledger at 15 rows over 3 runs, 11 agree / 4
  disagree): the surviving transcript reads "(deterministic) timeout at
  whnf, maximum number of heartbeats (400000) has been reached" — a
  BUDGET refusal, not a reflection/ladder divergence.  The 400000 cap
  rescued the 153-env box (gap_witness now agrees); the 289-env box
  (sum_exists) exceeds even the whitelisted cap.  ALL four disagreement
  rows carry this root-cause; none is unexplained; S4b is unblocked on
  this axis.  Structural fix authored: the probe now emits ONE example
  PER box point (Lean's budget is per declaration; the conjunction of
  pointwise claims IS the box claim), and ledger disagreement rows carry
  a data-derived `reason` field so the zero-unexplained predicate is
  ledger-measurable — **verdict GREEN** (run 30034874109: 5/5 probes
  agree, sum_exists included; the budget-refusal class is closed by
  construction).
- S6 SHAPES 2-5: **kernel-checked green** (same run 30034874109, commit
  a28d5b6): `compile_hyp_chain_shape`/`hyp_chain_of_check` (chains),
  `compile_foralls_shape` (∀ segments + leading ∀),
  `compile_prefix_shape` (mixed ∀*∃*; shape 3 is its ∃-free special
  case), `compile_conj_shape`/`conj_of_check` (conjoined conclusions) —
  list-structured folds, one lemma per shape at every arity.  Shape 6
  stays a named skip pinned per op; the schema↔bytes parity tooth
  (`tests/test_compile_shape_parity.py`) round-trips every committed
  reading.  Ledger: 20 rows over 4 lane runs — 16 agree, 4 disagree all
  carrying the confirmed budget root-cause.  S4b entrance progress:
  runs ≥3 ✓, multi-var ≥2 ✓, hyp-bearing ≥2 ✓, zero unexplained ✓;
  still short: agreement rows (16 of ≥25) and distinct readings (5 of
  ≥8) — corpus growth is the remaining lever.
- S6-carrier + entrance-mix growth AUTHORED (commits d89f5c0/718af60/
  e9625c9, lane verdict pending): the Nat layer (evalTmN/denoteN/checkN
  chain, truncated sub proven, D8 demos on both carriers), the nat-sub
  skip retired on proof (Nat readings probe via checkAllN_witness;
  mixed-carriers is the new named skip), and readings 67-69 (67 Nat with
  the truncated-sub template; corpus pins 55→58; probing readings now
  8).  Measured novelty: proof_mine's first cross-program regularity,
  `(ref a)` at transfer 0.5, pinned.  Two green lane runs from here
  reach the S4b row threshold (16 + 8 + 8 ≥ 25).
- Post-merge audit (2026-07-23, after PR #18 landed on main as 9afb63f),
  two measured facts the queue below now encodes: (a) agreement row #1
  came from the TEST FIXTURE reading, not the committed corpus — the
  committed corpus's readings emit ZERO witness templates, so the S4b
  evidence gate is structurally starved until the corpus grows ∃-class
  readings; (b) shadow reports live only inside ephemeral lane runners —
  no agreement row survives a run, so "accumulated agreement across lane
  runs" is currently unmeasurable.  Both are S4a′'s job.

## 2. The iteration protocol (the ONLY loop; one concern per commit)

1. Edit `tools/FgReflect.lean` (or a sibling module) INSIDE the escape-gate
   envelope: run
   `python3 -c "from buildloop.validate_lean import validate_lean as v; print(v(open('tools/FgReflect.lean').read()))"`
   before every commit.  The gate is lexical over the WHOLE file, comments
   included — no blocklisted word may appear even as prose (this has bitten
   once already; the gate tooth in `tests/test_fg_reflect_lean.py` catches
   it locally).
2. Extend the interface tooth (`test_soundness_theorems_present`) with any
   new load-bearing theorem name.
3. Commit with `[lean-ci]` in the message; push to the working branch.
4. The lean lane is the checker.  On failure: fetch the `lean` job log,
   find the first Lean error, fix ONLY that, repeat.  On success: update
   the §1 ledger in the same session and move to the next step.
5. NEVER claim a Lean artifact is checked until the lane says so.  This
   container class has no toolchain; local green means gate + interface
   teeth only.

## 3. The step queue (strict order; each step is one lane iteration or less)

- **S1 — confirm/absorb the pending run** (§1 first act).  If red: fix per
  §2.4 (likeliest culprits: the `by_cases`/`simp` interplay in
  `evalTm_subst`'s tvar case; `simp` closing `denote_subst`'s pimp case).
- **S2 — v0.2 dvd bridge**: AUTHORED (`dvd_iff_emod_eq_zero` +
  `pdvd_denote_iff_dvd`, core lemmas only, with the 3 ∣ 9 rfl demo) —
  lane verdict pending with S1's run.
- **S3 — typed rendering**: AUTHORED (binder-shell props
  `forall (n : Carrier), n = v -> concl`; the committed corpus now yields
  9 props, 0 skips) — done when the Lean-gated probe tooth closes them.
- **S4a — reflection as a paired SHADOW channel**: DONE (lane run
  29998311090 — the probe elaborated; agreement row #1).
  (`run/reflect_shadow.py`: AST→FgReflect quoter, checkAll_witness probe
  per emitted template, agreement/disagreement rows; cert surfaces
  untouched — the pinned-vocabulary tooth asserts it.)
- **S4a′ — the agreement evidence store + ∃-class corpus** (NEW, from the
  post-PR#18 audit; prerequisite for S4b's gate to be measurable at all):
  - (i) DURABLE LEDGER: agreement/disagreement rows must outlive the lane
    runner.  Add an append-only `results/reflect_agreement.jsonl` — one
    row per probe per lane run (module_sha, statement_hash, source
    reading, verdict, lane run id) — written by the shadow sweep in the
    lean job and persisted (uploaded as a CI artifact whose digest is
    recorded, or committed back by the driver session in the same
    iteration that reads the lane verdict).  Done-predicate: two
    successive lane runs each append rows, and a tooth in
    `tests/test_reflect_shadow.py` asserts the ledger is append-only
    (byte-prefix discipline, the update_ledger convention).
  - (ii) CORPUS: add ∃-class readings (existential conclusions inside the
    v0.1 reflect slice; include ≥2 multi-variable and ≥2
    hypothesis-bearing statements) under `specs/mathsources/readings/`
    until the shadow sweep emits probes from the COMMITTED corpus, not
    just the fixture.  Done-predicate: `run_shadow` reports ≥5 probe rows
    with zero rows sourced from test fixtures.
- **S4b — the promotion ceremony (EVIDENCE-GATED, USER-GATED)**: flips
  `discharge: reflection` into the cert vocabulary ONLY after the
  ENTRANCE PREDICATE holds — all measured from the S4a′ ledger, none from
  prose: ≥25 agreement rows, across ≥3 distinct lane runs, over ≥8
  distinct committed readings, including ≥2 multi-variable and ≥2
  hypothesis-bearing statements, with ZERO unexplained disagreement rows
  (every disagreement row must carry a written root-cause before it stops
  blocking).  The cert claims tuple must name the discharge ROUTE, not
  just the channel: `reflection/<theorem>` (checkAll_witness vs
  checkStmtBox_sound_exOnly vs sall_guard_of_check) — PR #18 created a
  second discharge route (template-free exhaustive search), so
  `discharge: reflection` alone is too coarse to replay.  Five
  touchpoints, ONE commit: (1) kernel/certs.py —
  extend the pinned discharge vocabulary; (2) run/anchor.py — the runner
  path that discharges via the reflection theorem; (3) teeth — planted
  disagreement + ladder/reflection parity tests; (4) TRUST.md — the
  honestly-labelled contract entry (FgReflect.lean joins the enumerated
  trusted surface AS A PROVEN artifact, citing its lane-checked
  soundness); (5) KA_INTERFACES.md — the FI-KA-1/4 amendment.  TRUST.md
  is maintainer property: this commit ships only with explicit user
  sign-off.
- **S5 — T3 groundwork, binder layer**: DONE (lane run 30000411679).
  `Stmt` + `denoteStmt` + `sex_of_template`, the box layer
  (`denoteStmtBox`/`checkStmtBox` + soundness), the `exOnly` ∃-only
  bridge, and the Stmt lifts of the box theorems are all kernel-checked;
  done-predicates live in `test_soundness_theorems_present`.  Unbounded
  ∀ is handled by RELATIVIZATION (the box layer) -- the honest decidable
  reach.  Original spec: extend FgReflect with `Stmt` =
  quantifier-prefixed Pd (forall/exists over indexed vars, the ∀*∃* shapes
  the fragment admits), `denoteStmt`, and the box-soundness theorems lifted
  to `Stmt`.  T2's `update` machinery is the substrate.  One lane iteration
  per binder form; done-predicates are the theorem names in the tooth.
- **S6 — T3 core**: IN PROGRESS — shape 1 green (lane run 30000411679):
  `compile_guard_shape` is its preservation theorem,
  `sall_guard_of_check` its one-check discharge.  THE SHAPE QUEUE is now
  enumerated from `generators/math_compile.py`'s emission grammar (the
  binder-prefix/body spec in its module docstring), so "T3 done" is a
  checkable predicate — every shape below has its preservation lemma
  accepted by the lane, or a named out-of-slice skip:
  1. single-∀ guard `forall (n : C), n = c -> concl` — **DONE**
     (`compile_guard_shape`).
  2. hypothesis CHAINS — **DONE** (`compile_hyp_chain_shape`, run
     30034874109).
  3. multi-binder ∀ segments + leading ∀ — **DONE**
     (`compile_foralls_shape`, same run).
  4. mixed ∀*∃* prefixes — **DONE** (`compile_prefix_shape`; shape 3 is
     its ∃-free special case).
  5. conjoined conclusions — **DONE** (`compile_conj_shape`).
  6. out-of-slice ops `^` / `gcd` / `coprime`: honest named skips until
     the reflect slice grows those constructors — the skip vocabulary in
     `run/reflect_shadow.py` is the naming convention, pinned per op in
     `test_out_of_slice_ops_all_named_skips`; retires only with the
     PLAN_FRAGMENT purchases.
  Each shape is one lane iteration (or less); preservation lemmas are
  hand-written symbolic proofs — if a shape stalls past ~3 red lane
  iterations, the named fallback is proof search via recorded replay
  (mine the goal with the smt/hammer probes, replay the recorded script
  in the lane) BEFORE weakening the shape's statement.
  PARITY TOOTH (schema↔bytes, from the audit): `compile_guard_shape`
  proves the SCHEMA, but nothing yet ties the actual emitted bytes of
  `compile_math_reading` to that schema — the chain today is
  emitted text -(unverified)-> schema -(proven)-> Stmt.  Per shape, add a
  Python-side tooth that parses the emitted `lean_text` back into the
  shape's schema instance and asserts round-trip equality (byte-identity
  teeth already pin the emission; this pins the SCHEMA READING of it).
- **S6-carrier — the Nat layer** (NEW, from the audit): FgReflect's
  slice is Int-only, but `math_compile` emits `∀ (n : Nat)` binders for
  2 of the 3 committed readings, and D8's truncated `Nat.sub` is exactly
  the divergence class the battery exists to catch.  Extend FgReflect
  with a Nat carrier (either a second Tm evaluation at `Nat` with its
  own decDenote, or the box layer relativized over `Int` nonnegativity
  — pick whichever keeps `check_sound`'s statement unchanged), including
  truncated subtraction's honest semantics.  Done-predicates: the Nat
  variants of `check_sound`/`checkAll_witness` in the interface tooth,
  green in the lane; `nat-sub-out-of-reflect-slice` retires from the
  skip vocabulary only when the truncation semantics is actually proven,
  never by fiat.

## 4. Guardrails (non-negotiable)

- Branch discipline: work on the designated `claude/...` branch of the
  session; never push elsewhere.  If PR #17 has merged, restart the branch
  from origin/main and stack there.
- The escape-gate envelope (§2.1) and the `[lean-ci]` tag are mandatory.
- No TRUST.md/kernel/cert-shape edits outside S4's explicit ceremony.
- Honesty rules carry: refusals/skips are named outcomes; a red lane is
  reported as red; this ledger is updated in the same session that learns
  a verdict.
- Spend: everything in this plan is CPU/lane work — token-free by design;
  run tools under `buildloop.lanes.token_free` where applicable.
