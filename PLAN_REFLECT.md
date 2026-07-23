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
  = re-enter the namespace around the example, pushed — verdict pending.
- The lean job's pytest list lives in `.github/workflows/ci.yml` (search
  `test_fg_reflect_lean`); the lane fires on commits whose message carries
  `[lean-ci]`.

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
- **S4a — reflection as a paired SHADOW channel**: AUTHORED
  (`run/reflect_shadow.py`: AST→FgReflect quoter, checkAll_witness probe
  per emitted template, agreement/disagreement rows; cert surfaces
  untouched — the pinned-vocabulary tooth asserts it).  Done when the
  Lean-gated tooth shows the probe elaborating (agreement) in the lane.
- **S4b — the promotion ceremony (EVIDENCE-GATED, USER-GATED)**: flips
  `discharge: reflection` into the cert vocabulary ONLY after S4a has
  accumulated agreement rows across lane runs with zero unexplained
  disagreements.  Five touchpoints, ONE commit: (1) kernel/certs.py —
  extend the pinned discharge vocabulary; (2) run/anchor.py — the runner
  path that discharges via the reflection theorem; (3) teeth — planted
  disagreement + ladder/reflection parity tests; (4) TRUST.md — the
  honestly-labelled contract entry (FgReflect.lean joins the enumerated
  trusted surface AS A PROVEN artifact, citing its lane-checked
  soundness); (5) KA_INTERFACES.md — the FI-KA-1/4 amendment.  TRUST.md
  is maintainer property: this commit ships only with explicit user
  sign-off.
- **S5 — T3 groundwork, binder layer**: PARTIALLY AUTHORED (`Stmt` +
  `denoteStmt` + `sex_of_template` + demo are in; box-soundness lifts and
  the ∀-handling interface remain).  Original spec: extend FgReflect with `Stmt` =
  quantifier-prefixed Pd (forall/exists over indexed vars, the ∀*∃* shapes
  the fragment admits), `denoteStmt`, and the box-soundness theorems lifted
  to `Stmt`.  T2's `update` machinery is the substrate.  One lane iteration
  per binder form; done-predicates are the theorem names in the tooth.
- **S6 — T3 core**: a Lean-side `compile : Stmt -> (the statement forms
  math_compile emits)` mirror + the preservation theorem, iterated shape by
  shape (start: forall-only Nat-free statements).  This is the long haul;
  each shape's done-predicate is its preservation lemma accepted by the
  lane.  Parity teeth: the Python side already asserts byte-identity of
  `compile_math_reading` output; add cross-checks per shape.

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
