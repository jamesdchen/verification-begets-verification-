/-
FgReflect.lean -- proof-by-reflection for the F-G fragment, v0 SLICE.

THE SCHEMA (growth lane 3, made concrete): represent the fragment as DATA
inside Lean, give it a computable checker and a Prop-level denotation, and
prove ONCE that the checker is sound.  The kernel checks that proof one time;
thereafter every checker verdict is a THEOREM obtained by computation
(`check_sound _ _ rfl`), never a trusted claim -- capability grows, the
trusted base does not.  This is the repo's thesis running natively inside the
proof assistant: the same one-proof-then-amortize move as promote.py's
universal tier and the R4 migrator rule.

HONEST SCOPE (v0).  Full F-G truth over unbounded Nat/Int is arithmetic and
therefore UNDECIDABLE -- no verified decision procedure for it can exist.
What reflection soundly delivers is the fragment's decidable layers, and v0
takes the smallest honest slice:

  * Int carrier only.  The D8/D9 carrier rules (Nat truncated sub, mod
    totalisation, dvd's zero case) are v0.1: each is an `if`-totalised
    computable atom plus one lemma, the exact pattern math_smt already uses.
  * atoms = / <= / < over terms built from lit / var / + / - / *.
  * the BOUNDED layer: `checkAll` over an explicit environment list mirrors
    the bounded shadow (math_eval's exhaustive box sweep); its soundness
    theorem is what turns a shadow verdict into kernel-grade evidence.
  * the WITNESS layer: `check_sound` at one environment is the discharge a
    Skolem-template instantiation needs (generators/math_witness.py).

CONSTRAINTS.  This file must survive the F0.4 escape gate
(buildloop/validate_lean.py) because the Lean backend re-gates everything it
elaborates -- and the gate is LEXICAL over the WHOLE file, comments included,
so no word on its blocklist may appear here even as prose (this comment
deliberately does not name them; see the gate's own source for the list).
Practically: no metaprogramming surface of any kind, ASCII identifiers only
(math symbols are fine), core Lean only -- no Mathlib import, so the trusted
surface is the Lean kernel and nothing else.  tests/test_fg_reflect_lean.py
holds the teeth: the gate check runs everywhere; elaboration runs in the
Lean lane.
-/

namespace FgReflect

/-- Fragment terms, v0: integer literals, variables (indexed into an
environment), and + - * .  Mirrors the term layer of the F-G pred/term AST
(generators/math_reading.py). -/
inductive Tm where
  | lit : Int -> Tm
  | tvar : Nat -> Tm
  | add : Tm -> Tm -> Tm
  | sub : Tm -> Tm -> Tm
  | mul : Tm -> Tm -> Tm
  | tmod : Tm -> Tm -> Tm

/-- Fragment predicates, v0: the three order/equality atoms and the three
connectives the reading grammar admits. -/
inductive Pd where
  | peq : Tm -> Tm -> Pd
  | ple : Tm -> Tm -> Pd
  | plt : Tm -> Tm -> Pd
  | pne : Tm -> Tm -> Pd
  | pdvd : Tm -> Tm -> Pd
  | peven : Tm -> Pd
  | podd : Tm -> Pd
  | pand : Pd -> Pd -> Pd
  | por : Pd -> Pd -> Pd
  | pimp : Pd -> Pd -> Pd

/-- The evaluator: the Lean-side sibling of math_eval.eval_term (Int slice). -/
def evalTm (env : Nat -> Int) : Tm -> Int
  | Tm.lit k => k
  | Tm.tvar i => env i
  | Tm.add a b => evalTm env a + evalTm env b
  | Tm.sub a b => evalTm env a - evalTm env b
  | Tm.mul a b => evalTm env a * evalTm env b
  | Tm.tmod a b => evalTm env a % evalTm env b

/-- The denotation: what a predicate MEANS at an environment, as a Prop.
This is the ground truth the checker is proven against. -/
def denote (env : Nat -> Int) : Pd -> Prop
  | Pd.peq a b => evalTm env a = evalTm env b
  | Pd.ple a b => evalTm env a <= evalTm env b
  | Pd.plt a b => evalTm env a < evalTm env b
  | Pd.pne a b => Not (evalTm env a = evalTm env b)
  -- dvd, even, odd carry the fragment's D9 characterizations (the a = 0 arm
  -- matching the library convention 0 dvd b iff b = 0); the bridge lemma to
  -- the library's divisibility relation is v0.2, Lean-lane work.
  | Pd.pdvd a b => (evalTm env a = 0 /\ evalTm env b = 0) \/
      (Not (evalTm env a = 0) /\ evalTm env b % evalTm env a = 0)
  | Pd.peven a => evalTm env a % 2 = 0
  | Pd.podd a => evalTm env a % 2 = 1
  | Pd.pand p q => denote env p /\ denote env q
  | Pd.por p q => denote env p \/ denote env q
  | Pd.pimp p q => denote env p -> denote env q

/-- Denotations are decidable, by structural recursion: every atom is a
decidable Int comparison and the connectives preserve decidability.  This
instance IS the decision procedure; its construction is checked by the
kernel like any other term. -/
instance decDenote (env : Nat -> Int) : (p : Pd) -> Decidable (denote env p)
  | Pd.peq a b => inferInstanceAs (Decidable (evalTm env a = evalTm env b))
  | Pd.ple a b => inferInstanceAs (Decidable (evalTm env a <= evalTm env b))
  | Pd.plt a b => inferInstanceAs (Decidable (evalTm env a < evalTm env b))
  | Pd.pne a b =>
      inferInstanceAs (Decidable (Not (evalTm env a = evalTm env b)))
  | Pd.pdvd a b =>
      inferInstanceAs (Decidable ((evalTm env a = 0 /\ evalTm env b = 0) \/
        (Not (evalTm env a = 0) /\ evalTm env b % evalTm env a = 0)))
  | Pd.peven a => inferInstanceAs (Decidable (evalTm env a % 2 = 0))
  | Pd.podd a => inferInstanceAs (Decidable (evalTm env a % 2 = 1))
  | Pd.pand p q => by
      haveI := decDenote env p
      haveI := decDenote env q
      exact inferInstanceAs (Decidable (denote env p /\ denote env q))
  | Pd.por p q => by
      haveI := decDenote env p
      haveI := decDenote env q
      exact inferInstanceAs (Decidable (denote env p \/ denote env q))
  | Pd.pimp p q => by
      haveI := decDenote env p
      haveI := decDenote env q
      exact inferInstanceAs (Decidable (denote env p -> denote env q))

/-- The computable checker: run the decision procedure to a Bool. -/
def check (env : Nat -> Int) (p : Pd) : Bool := decide (denote env p)

/-- SOUNDNESS, proven once: a `true` from the checker is a proof of the
denotation.  After the kernel accepts this file, `check_sound _ _ rfl` turns
computation into theorems. -/
theorem check_sound (env : Nat -> Int) (p : Pd)
    (h : check env p = true) : denote env p :=
  of_decide_eq_true h

/-- Completeness (the fragment is decidable at a point, so we get both
directions): a true denotation always computes to `true`. -/
theorem check_complete (env : Nat -> Int) (p : Pd)
    (h : denote env p) : check env p = true :=
  decide_eq_true h

/-- The BOUNDED layer: the shadow's exhaustive box sweep as one Bool. -/
def checkAll (envs : List (Nat -> Int)) (p : Pd) : Bool :=
  envs.all (fun env => check env p)

/-- Bounded-shadow soundness: one `true` certifies the whole box.  This is
the theorem that upgrades a math_eval shadow verdict from cross-checked
evidence to kernel-grade fact. -/
theorem checkAll_sound (envs : List (Nat -> Int)) (p : Pd)
    (h : checkAll envs p = true) :
    forall env, env ∈ envs -> denote env p := by
  intro env hmem
  simp only [checkAll, List.all_eq_true] at h
  exact of_decide_eq_true (h env hmem)

/-
TARGET 2 CORE: the verified witness-template checker.  A Skolem template is
a term ``tau`` standing in for a bound variable ``k``; the emitter's whole
claim is "substituting tau closes the statement at every box point".  The
theorems below make that claim kernel-grade: substitution machinery, the
substitution lemma, and ``checkAll_witness`` -- a template that CHECKS
across the box PROVES the existential at every box point.
-/

/-- Point update of an environment. -/
def update (env : Nat -> Int) (k : Nat) (v : Int) : Nat -> Int :=
  fun i => if i = k then v else env i

/-- Substitute term ``t`` for variable ``k``. -/
def substTm (k : Nat) (t : Tm) : Tm -> Tm
  | Tm.lit c => Tm.lit c
  | Tm.tvar i => if i = k then t else Tm.tvar i
  | Tm.add a b => Tm.add (substTm k t a) (substTm k t b)
  | Tm.sub a b => Tm.sub (substTm k t a) (substTm k t b)
  | Tm.mul a b => Tm.mul (substTm k t a) (substTm k t b)
  | Tm.tmod a b => Tm.tmod (substTm k t a) (substTm k t b)

def substPd (k : Nat) (t : Tm) : Pd -> Pd
  | Pd.peq a b => Pd.peq (substTm k t a) (substTm k t b)
  | Pd.ple a b => Pd.ple (substTm k t a) (substTm k t b)
  | Pd.plt a b => Pd.plt (substTm k t a) (substTm k t b)
  | Pd.pne a b => Pd.pne (substTm k t a) (substTm k t b)
  | Pd.pdvd a b => Pd.pdvd (substTm k t a) (substTm k t b)
  | Pd.peven a => Pd.peven (substTm k t a)
  | Pd.podd a => Pd.podd (substTm k t a)
  | Pd.pand p q => Pd.pand (substPd k t p) (substPd k t q)
  | Pd.por p q => Pd.por (substPd k t p) (substPd k t q)
  | Pd.pimp p q => Pd.pimp (substPd k t p) (substPd k t q)

/-- The substitution lemma: evaluating after substitution equals evaluating
under the updated environment. -/
theorem evalTm_subst (env : Nat -> Int) (k : Nat) (t : Tm) :
    (a : Tm) ->
      evalTm env (substTm k t a) = evalTm (update env k (evalTm env t)) a
  | Tm.lit c => rfl
  | Tm.tvar i => by
      by_cases h : i = k
      · simp [substTm, evalTm, update, h]
      · simp [substTm, evalTm, update, h]
  | Tm.add a b => by
      simp [substTm, evalTm, evalTm_subst env k t a, evalTm_subst env k t b]
  | Tm.sub a b => by
      simp [substTm, evalTm, evalTm_subst env k t a, evalTm_subst env k t b]
  | Tm.mul a b => by
      simp [substTm, evalTm, evalTm_subst env k t a, evalTm_subst env k t b]
  | Tm.tmod a b => by
      simp [substTm, evalTm, evalTm_subst env k t a, evalTm_subst env k t b]

/-- Substitution lemma at the predicate layer, as an iff. -/
theorem denote_subst (env : Nat -> Int) (k : Nat) (t : Tm) :
    (p : Pd) ->
      (denote env (substPd k t p) <->
       denote (update env k (evalTm env t)) p)
  | Pd.peq a b => by simp [substPd, denote, evalTm_subst]
  | Pd.ple a b => by simp [substPd, denote, evalTm_subst]
  | Pd.plt a b => by simp [substPd, denote, evalTm_subst]
  | Pd.pne a b => by simp [substPd, denote, evalTm_subst]
  | Pd.pdvd a b => by simp [substPd, denote, evalTm_subst]
  | Pd.peven a => by simp [substPd, denote, evalTm_subst]
  | Pd.podd a => by simp [substPd, denote, evalTm_subst]
  | Pd.pand p q => by
      simp [substPd, denote, denote_subst env k t p, denote_subst env k t q]
  | Pd.por p q => by
      simp [substPd, denote, denote_subst env k t p, denote_subst env k t q]
  | Pd.pimp p q => by
      simp [substPd, denote, denote_subst env k t p, denote_subst env k t q]

/-- ONE template check yields the existential at one point: tau's value is
the witness. -/
theorem witness_of_check (env : Nat -> Int) (k : Nat) (tau : Tm) (p : Pd)
    (h : check env (substPd k tau p) = true) :
    Exists (fun v => denote (update env k v) p) :=
  Exists.intro (evalTm env tau)
    ((denote_subst env k tau p).mp (of_decide_eq_true h))

/-- TARGET 2's theorem: a template that checks across the whole box proves
the existential at EVERY box point -- the witness emitter's claim, made
kernel-grade once and for all templates. -/
theorem checkAll_witness (envs : List (Nat -> Int)) (k : Nat) (tau : Tm)
    (p : Pd) (h : checkAll envs (substPd k tau p) = true) :
    forall env, env ∈ envs -> Exists (fun v => denote (update env k v) p) :=
  fun env hmem => witness_of_check env k tau p
    (by
      simp only [checkAll, List.all_eq_true] at h
      exact h env hmem)

/-
V0.2: the dvd BRIDGE.  The pdvd atom carries the fragment's D9
characterization; these lemmas connect it to the library's own
divisibility relation, so reflection verdicts about pdvd are verdicts
about the real `∣` -- proven once, from core lemmas only.
-/

/-- Divisibility is exactly emod-vanishing, over ALL of Int: the a = 0 case
works because b % 0 = b, matching 0 ∣ b <-> b = 0. -/
theorem dvd_iff_emod_eq_zero (a b : Int) : a ∣ b <-> b % a = 0 := by
  constructor
  · intro h
    cases h with
    | intro c hc => simp [hc, Int.mul_emod_right]
  · intro h
    refine Exists.intro (b / a) ?_
    have h2 := Int.ediv_add_emod b a
    rw [h] at h2
    simpa using h2.symm

/-- The bridge: the pdvd atom's denotation IS library divisibility. -/
theorem pdvd_denote_iff_dvd (env : Nat -> Int) (a b : Tm) :
    denote env (Pd.pdvd a b) <-> evalTm env a ∣ evalTm env b := by
  by_cases h : evalTm env a = 0
  · simp [denote, h, dvd_iff_emod_eq_zero, Int.emod_zero]
  · simp [denote, h, dvd_iff_emod_eq_zero]

/-
T3 GROUNDWORK (the binder layer): statements as quantifier-prefixed
predicates, with binders naming their variable index -- the ∀*∃* shapes the
fragment admits.  The decidable reach stops at unbounded ∀ (arithmetic is
undecidable); what reflection soundly delivers here is the EXISTENTIAL
discharge: a checked template proves an ∃-statement outright.
-/

inductive Stmt where
  | base : Pd -> Stmt
  | sall : Nat -> Stmt -> Stmt
  | sex : Nat -> Stmt -> Stmt

def denoteStmt (env : Nat -> Int) : Stmt -> Prop
  | Stmt.base p => denote env p
  | Stmt.sall k s => forall v : Int, denoteStmt (update env k v) s
  | Stmt.sex k s => Exists (fun v : Int => denoteStmt (update env k v) s)

/-- Template discharge at the statement layer: one checked substitution
proves the existential statement at this environment. -/
theorem sex_of_template (env : Nat -> Int) (k : Nat) (tau : Tm) (p : Pd)
    (h : check env (substPd k tau p) = true) :
    denoteStmt env (Stmt.sex k (Stmt.base p)) :=
  witness_of_check env k tau p h

/-- Reflection demo: the entire proof is `rfl` -- the kernel evaluates the
checker and the soundness theorem does the rest.  (1 < 3 at env 0 = 3.) -/
example : denote (fun _ => 3) (Pd.plt (Tm.lit 1) (Tm.tvar 0)) :=
  check_sound _ _ rfl

/-- The bridge in action: 3 dvd 9, decided by computation, delivered as a
statement about the library's own relation. -/
example : (3 : Int) ∣ 9 :=
  (pdvd_denote_iff_dvd (fun _ => 0) (Tm.lit 3) (Tm.lit 9)).mp
    (check_sound _ _ rfl)

/-- Statement-layer demo: the ∃-statement discharged by the emitter's
template shape. -/
example : denoteStmt (fun _ => 41)
    (Stmt.sex 0 (Stmt.base (Pd.plt (Tm.tvar 1) (Tm.tvar 0)))) :=
  sex_of_template _ 0 (Tm.add (Tm.tvar 1) (Tm.lit 1)) _ rfl

/-- The emitter's own survivor, verified: template m := n + 1 (variable 1 is
the outer n, variable 0 the witness slot) checks across a box, so EVERY box
point has a witness for n < m -- with `rfl` as the entire computation. -/
example :
    forall env, env ∈ [fun _ => (0 : Int), fun _ => 5, fun _ => 100] ->
      Exists (fun v => denote (update env 0 v)
        (Pd.plt (Tm.tvar 1) (Tm.tvar 0))) :=
  checkAll_witness _ 0 (Tm.add (Tm.tvar 1) (Tm.lit 1)) _ rfl

/-- And at the box layer: 0 <= x * x checked over a tiny explicit box. -/
example :
    forall env, env ∈ [fun _ => (-2 : Int), fun _ => 0, fun _ => 2] ->
      denote env (Pd.ple (Tm.lit 0) (Tm.mul (Tm.tvar 0) (Tm.tvar 0))) :=
  checkAll_sound _ _ rfl

/-
S5 COMPLETION (the ∀-handling interface + box-soundness lifted to Stmt).
Unbounded ∀ over Int is out of decidable reach, so the honest interface is
RELATIVIZATION: `denoteStmtBox` reads every binder over an explicit finite
box, and `checkStmtBox` decides THAT by exhaustive sweep -- the bounded
shadow's semantics, now covering full quantifier prefixes.  Two soundness
theorems then say exactly what a sweep verdict is worth:

  * `checkStmtBox_sound` -- a true sweep proves the box-relativized
    statement (every binder form, ∀ and ∃ alike);
  * `checkStmtBox_sound_exOnly` -- for ∃-only prefixes the box witness IS a
    real witness, so the sweep proves the statement's TRUE denotation.
    (For ∀ no finite sweep can reach the real semantics; that direction is
    deliberately absent, and `exOnly` names the boundary.)

Finally the existing box theorems are lifted to the Stmt layer, so the
Python side cites one vocabulary for both.
-/

/-- Box-relativized statement semantics: every binder ranges over the
explicit finite box instead of all of Int. -/
def denoteStmtBox (box : List Int) (env : Nat -> Int) : Stmt -> Prop
  | Stmt.base p => denote env p
  | Stmt.sall k s => forall v, v ∈ box -> denoteStmtBox box (update env k v) s
  | Stmt.sex k s =>
      Exists (fun v => v ∈ box /\ denoteStmtBox box (update env k v) s)

/-- The exhaustive sweep, as one Bool: ∀ binders fold with all, ∃ binders
with any, atoms with the point checker. -/
def checkStmtBox (box : List Int) (env : Nat -> Int) : Stmt -> Bool
  | Stmt.base p => check env p
  | Stmt.sall k s => box.all (fun v => checkStmtBox box (update env k v) s)
  | Stmt.sex k s => box.any (fun v => checkStmtBox box (update env k v) s)

/-- Sweep soundness over full quantifier prefixes: a true sweep is a proof
of the box-relativized statement. -/
theorem checkStmtBox_sound (box : List Int) :
    (s : Stmt) -> (env : Nat -> Int) ->
      checkStmtBox box env s = true -> denoteStmtBox box env s
  -- via check_sound, not of_decide_eq_true: the target is only
  -- DEFINITIONALLY `denote env p`, and instance search will not unfold
  -- denoteStmtBox to find decDenote (first lane red, run 29999849337).
  | Stmt.base p, env, h => check_sound env p h
  | Stmt.sall k s, env, h => by
      simp only [checkStmtBox, List.all_eq_true] at h
      intro v hv
      exact checkStmtBox_sound box s (update env k v) (h v hv)
  | Stmt.sex k s, env, h => by
      simp only [checkStmtBox, List.any_eq_true] at h
      cases h with
      | intro v hv =>
        exact Exists.intro v (And.intro hv.1
          (checkStmtBox_sound box s (update env k v) hv.2))

/-- The boundary marker: statements whose quantifier prefix is ∃-only. -/
def exOnly : Stmt -> Bool
  | Stmt.base _ => true
  | Stmt.sall _ _ => false
  | Stmt.sex _ s => exOnly s

/-- For ∃-only prefixes, a box witness is a real witness: box-relativized
truth implies the true denotation. -/
theorem denoteStmt_of_box (box : List Int) :
    (s : Stmt) -> (env : Nat -> Int) -> exOnly s = true ->
      denoteStmtBox box env s -> denoteStmt env s
  | Stmt.base _, _, _, h => h
  | Stmt.sall _ _, _, hex, _ => nomatch hex
  | Stmt.sex k s, env, hex, h => by
      cases h with
      | intro v hv =>
        exact Exists.intro v
          (denoteStmt_of_box box s (update env k v) hex hv.2)

/-- The ∃-only discharge, end to end: one true sweep proves the statement's
TRUE denotation -- finite search as a second, template-free route beside
`sex_of_template`. -/
theorem checkStmtBox_sound_exOnly (box : List Int) (env : Nat -> Int)
    (s : Stmt) (hex : exOnly s = true)
    (h : checkStmtBox box env s = true) : denoteStmt env s :=
  denoteStmt_of_box box s env hex (checkStmtBox_sound box s env h)

/-- Box soundness lifted to the Stmt layer (base form). -/
theorem checkAll_sound_stmt (envs : List (Nat -> Int)) (p : Pd)
    (h : checkAll envs p = true) :
    forall env, env ∈ envs -> denoteStmt env (Stmt.base p) :=
  checkAll_sound envs p h

/-- Witness-template box soundness lifted to the Stmt layer: a checked
template proves the ∃-statement at every box point. -/
theorem checkAll_witness_stmt (envs : List (Nat -> Int)) (k : Nat) (tau : Tm)
    (p : Pd) (h : checkAll envs (substPd k tau p) = true) :
    forall env, env ∈ envs -> denoteStmt env (Stmt.sex k (Stmt.base p)) :=
  checkAll_witness envs k tau p h

/-- Sweep demo, ∀∃ prefix: over the box [-1, 0, 1] every u has a v with
u <= v -- decided by exhaustive search, `rfl` is the whole computation. -/
example : denoteStmtBox [-1, 0, 1] (fun _ => 0)
    (Stmt.sall 0 (Stmt.sex 1 (Stmt.base (Pd.ple (Tm.tvar 0) (Tm.tvar 1))))) :=
  checkStmtBox_sound _ _ _ rfl

/-- ∃-only demo landing in the REAL semantics: some v has v * v = 9, found
by box search, no template needed. -/
example : denoteStmt (fun _ => 0)
    (Stmt.sex 0 (Stmt.base
      (Pd.peq (Tm.mul (Tm.tvar 0) (Tm.tvar 0)) (Tm.lit 9)))) :=
  checkStmtBox_sound_exOnly [3] (fun _ => 0) _ rfl rfl

/-
S6, FIRST SHAPE (T3 core): preservation for the GUARD SHAPE -- the exact
statement form the typed rendering emits for the ground corpus,
`forall (n : C), n = c -> concl`.  Its reflected mirror is
`Stmt.sall k (Stmt.base (Pd.pimp (Pd.peq (Tm.tvar k) (Tm.lit c)) q))`.
`sall_guard_iff` collapses the guarded ∀ to instantiation at c;
`compile_guard_shape` is the preservation theorem proper: the emitted
binder-shell Prop and the reflected statement are equivalent, proven once
per SHAPE (not per instance).  `sall_guard_of_check` then discharges any
instance of the shape with a single checker run.  Later shapes (hypothesis
chains, multi-binder prefixes) iterate this pattern, one lane round each.
-/

/-- The guarded ∀ collapses to instantiation: binding n, assuming n = c and
concluding q is exactly q at c. -/
theorem sall_guard_iff (env : Nat -> Int) (k : Nat) (c : Int) (q : Pd) :
    denoteStmt env (Stmt.sall k (Stmt.base
      (Pd.pimp (Pd.peq (Tm.tvar k) (Tm.lit c)) q))) <->
    denote (update env k c) q := by
  constructor
  · intro h
    exact h c (by simp [denote, evalTm, update])
  · intro h v hv
    have hv2 : v = c := by simpa [denote, evalTm, update] using hv
    rw [hv2]
    exact h

/-- PRESERVATION (first compiled shape): the binder-shell Prop the compiler
emits for a guarded ground fact means exactly what its reflected statement
means. -/
theorem compile_guard_shape (env : Nat -> Int) (k : Nat) (c : Int) (q : Pd) :
    (forall n : Int, n = c -> denote (update env k n) q) <->
      denoteStmt env (Stmt.sall k (Stmt.base
        (Pd.pimp (Pd.peq (Tm.tvar k) (Tm.lit c)) q))) := by
  constructor
  · intro h
    exact (sall_guard_iff env k c q).mpr (h c rfl)
  · intro h n hn
    rw [hn]
    exact (sall_guard_iff env k c q).mp h

/-- One checker run discharges any instance of the shape. -/
theorem sall_guard_of_check (env : Nat -> Int) (k : Nat) (c : Int) (q : Pd)
    (h : check (update env k c) q = true) :
    denoteStmt env (Stmt.sall k (Stmt.base
      (Pd.pimp (Pd.peq (Tm.tvar k) (Tm.lit c)) q))) :=
  (sall_guard_iff env k c q).mpr (check_sound _ _ h)

/-- The compiled shape end to end: the emitted binder-shell prop for
"n = 7 -> 3 < n", proven by one checker run through the preservation
theorem. -/
example : forall n : Int, n = 7 -> denote (update (fun _ => 0) 0 n)
    (Pd.plt (Tm.lit 3) (Tm.tvar 0)) :=
  (compile_guard_shape (fun _ => 0) 0 7 (Pd.plt (Tm.lit 3) (Tm.tvar 0))).mpr
    (sall_guard_of_check _ 0 7 _ rfl)

/-
S6, SHAPES 2-5: the rest of the compiler's emission grammar, as
LIST-STRUCTURED folds so every arity is covered by one lemma (never a
fixed-arity special case).  Shape 2 = hypothesis chains
`H1 -> H2 -> ... -> C` (right-associated, ids in order); shape 3 =
multi-binder ∀ segments plus the leading ∀; shape 4 = mixed ∀*∃*
prefixes; shape 5 = conjoined conclusions `C1 ∧ C2` in id order.  Each
shape gets its fold, its emitted-form denotation, and the preservation
theorem tying the two -- proven once per SHAPE.  Shape 6 (the `^` /
gcd / coprime slice misses) stays a NAMED skip on the Python side; its
tooth pins the skip vocabulary, and it retires only when the slice
grows those constructors.
-/

/-- Shape 2 fold: the hypothesis chain, right-associated, ids in order. -/
def pimps : List Pd -> Pd -> Pd
  | [], c => c
  | h :: hs, c => Pd.pimp h (pimps hs c)

/-- The emitted chain's meaning: hypotheses peel off left to right. -/
def denoteChain (env : Nat -> Int) : List Pd -> Pd -> Prop
  | [], c => denote env c
  | h :: hs, c => denote env h -> denoteChain env hs c

/-- PRESERVATION, shape 2: the emitted chain form means exactly the folded
predicate's denotation, at every chain length. -/
theorem compile_hyp_chain_shape (env : Nat -> Int) :
    (hs : List Pd) -> (c : Pd) ->
      (denoteChain env hs c <-> denote env (pimps hs c))
  | [], _ => Iff.rfl
  | h :: hs, c => by
      constructor
      · intro f hh
        exact (compile_hyp_chain_shape env hs c).mp (f hh)
      · intro f hh
        exact (compile_hyp_chain_shape env hs c).mpr (f hh)

/-- One checker run discharges any instance of the chain shape. -/
theorem hyp_chain_of_check (env : Nat -> Int) (hs : List Pd) (c : Pd)
    (h : check env (pimps hs c) = true) : denoteChain env hs c :=
  (compile_hyp_chain_shape env hs c).mpr (check_sound env (pimps hs c) h)

/-- Shape 3 fold: a ∀ segment binding several indices in listed order --
also the leading ∀ over unbound refs (sorted-name canonical order). -/
def salls : List Nat -> Stmt -> Stmt
  | [], s => s
  | k :: ks, s => Stmt.sall k (salls ks s)

/-- The emitted multi-binder form: nested real ∀s over Int. -/
def denoteForalls (env : Nat -> Int) : List Nat -> Stmt -> Prop
  | [], s => denoteStmt env s
  | k :: ks, s => forall v : Int, denoteForalls (update env k v) ks s

/-- PRESERVATION, shape 3: the emitted ∀-segment form means exactly the
folded statement's denotation, for every segment length. -/
theorem compile_foralls_shape :
    (ks : List Nat) -> (env : Nat -> Int) -> (s : Stmt) ->
      (denoteForalls env ks s <-> denoteStmt env (salls ks s))
  | [], _, _ => Iff.rfl
  | k :: ks, env, s => by
      constructor
      · intro f v
        exact (compile_foralls_shape ks (update env k v) s).mp (f v)
      · intro f v
        exact (compile_foralls_shape ks (update env k v) s).mpr (f v)

/-- Shape 4: one binder-prefix entry -- a ∀ or an ∃ over one index. -/
inductive Bnd where
  | all : Nat -> Bnd
  | ex : Nat -> Bnd

/-- Shape 4 fold: the full mixed ∀*∃* prefix in emission order. -/
def prefixStmt : List Bnd -> Stmt -> Stmt
  | [], s => s
  | Bnd.all k :: bs, s => Stmt.sall k (prefixStmt bs s)
  | Bnd.ex k :: bs, s => Stmt.sex k (prefixStmt bs s)

/-- The emitted mixed-prefix form: nested real ∀s and ∃s over Int. -/
def denotePrefix (env : Nat -> Int) : List Bnd -> Stmt -> Prop
  | [], s => denoteStmt env s
  | Bnd.all k :: bs, s =>
      forall v : Int, denotePrefix (update env k v) bs s
  | Bnd.ex k :: bs, s =>
      Exists (fun v : Int => denotePrefix (update env k v) bs s)

/-- PRESERVATION, shape 4: the emitted mixed-prefix form means exactly the
folded statement's denotation -- shape 3 is the ∃-free special case. -/
theorem compile_prefix_shape :
    (bs : List Bnd) -> (env : Nat -> Int) -> (s : Stmt) ->
      (denotePrefix env bs s <-> denoteStmt env (prefixStmt bs s))
  | [], _, _ => Iff.rfl
  | Bnd.all k :: bs, env, s => by
      constructor
      · intro f v
        exact (compile_prefix_shape bs (update env k v) s).mp (f v)
      · intro f v
        exact (compile_prefix_shape bs (update env k v) s).mpr (f v)
  | Bnd.ex k :: bs, env, s => by
      constructor
      · intro h
        cases h with
        | intro v hv =>
          exact Exists.intro v
            ((compile_prefix_shape bs (update env k v) s).mp hv)
      · intro h
        cases h with
        | intro v hv =>
          exact Exists.intro v
            ((compile_prefix_shape bs (update env k v) s).mpr hv)

/-- Shape 5 fold: conjoined conclusions, id order (nonempty by
construction: the compiler conjoins only when >= 2 demands exist, and a
head + tail list is exactly that). -/
def pands : Pd -> List Pd -> Pd
  | c, [] => c
  | c, d :: ds => Pd.pand c (pands d ds)

/-- The emitted conjunction's meaning, conclusion by conclusion. -/
def denoteAll (env : Nat -> Int) : Pd -> List Pd -> Prop
  | c, [] => denote env c
  | c, d :: ds => denote env c /\ denoteAll env d ds

/-- PRESERVATION, shape 5: the emitted conjoined form means exactly the
folded predicate's denotation, at every width. -/
theorem compile_conj_shape (env : Nat -> Int) :
    (c : Pd) -> (ds : List Pd) ->
      (denoteAll env c ds <-> denote env (pands c ds))
  | _, [] => Iff.rfl
  | c, d :: ds => by
      constructor
      · intro h
        exact And.intro h.1 ((compile_conj_shape env d ds).mp h.2)
      · intro h
        exact And.intro h.1 ((compile_conj_shape env d ds).mpr h.2)

/-- One checker run discharges any instance of the conjoined shape. -/
theorem conj_of_check (env : Nat -> Int) (c : Pd) (ds : List Pd)
    (h : check env (pands c ds) = true) : denoteAll env c ds :=
  (compile_conj_shape env c ds).mpr (check_sound env (pands c ds) h)

/-- Chain demo: 0 < x -> 1 <= x at x = 3, one checker run. -/
example : denoteChain (fun _ => 3)
    [Pd.plt (Tm.lit 0) (Tm.tvar 0)] (Pd.ple (Tm.lit 1) (Tm.tvar 0)) :=
  hyp_chain_of_check _ _ _ rfl

/-- Conjunction demo: 0 <= 2 and 2 <= 4, one checker run. -/
example : denoteAll (fun _ => 2)
    (Pd.ple (Tm.lit 0) (Tm.tvar 0)) [Pd.ple (Tm.tvar 0) (Tm.lit 4)] :=
  conj_of_check _ _ _ rfl

/-- Mixed-prefix demo: the ∃ segment discharged through the preservation
theorem by the emitter's template shape. -/
example : denotePrefix (fun _ => 41) [Bnd.ex 0]
    (Stmt.base (Pd.plt (Tm.tvar 1) (Tm.tvar 0))) :=
  (compile_prefix_shape [Bnd.ex 0] (fun _ => 41) _).mpr
    (sex_of_template _ 0 (Tm.add (Tm.tvar 1) (Tm.lit 1)) _ rfl)

/-
S6-CARRIER: the Nat layer.  The compiler emits `∀ (n : Nat)` binders, and
D8's truncated subtraction is exactly the divergence class the battery
exists to catch -- so the Nat semantics must be PROVEN, never assumed from
the Int layer.  The term/predicate GRAMMAR is shared (Tm/Pd and the subst
machinery are carrier-neutral); evaluation, denotation, decidability and
the soundness chain get honest Nat mirrors: `-` is Nat's truncated sub,
`%` is Nat.mod, and an Int literal reads through `Int.toNat` (readings
over Nat carry only non-negative literals; toNat is the total reading).
The Int-layer statements are UNTOUCHED.
-/

/-- The Nat evaluator: truncated sub, Nat mod. -/
def evalTmN (env : Nat -> Nat) : Tm -> Nat
  | Tm.lit k => k.toNat
  | Tm.tvar i => env i
  | Tm.add a b => evalTmN env a + evalTmN env b
  | Tm.sub a b => evalTmN env a - evalTmN env b
  | Tm.mul a b => evalTmN env a * evalTmN env b
  | Tm.tmod a b => evalTmN env a % evalTmN env b

/-- The Nat denotation, atom for atom the D8/D9 semantics. -/
def denoteN (env : Nat -> Nat) : Pd -> Prop
  | Pd.peq a b => evalTmN env a = evalTmN env b
  | Pd.ple a b => evalTmN env a <= evalTmN env b
  | Pd.plt a b => evalTmN env a < evalTmN env b
  | Pd.pne a b => Not (evalTmN env a = evalTmN env b)
  | Pd.pdvd a b => (evalTmN env a = 0 /\ evalTmN env b = 0) \/
      (Not (evalTmN env a = 0) /\ evalTmN env b % evalTmN env a = 0)
  | Pd.peven a => evalTmN env a % 2 = 0
  | Pd.podd a => evalTmN env a % 2 = 1
  | Pd.pand p q => denoteN env p /\ denoteN env q
  | Pd.por p q => denoteN env p \/ denoteN env q
  | Pd.pimp p q => denoteN env p -> denoteN env q

instance decDenoteN (env : Nat -> Nat) :
    (p : Pd) -> Decidable (denoteN env p)
  | Pd.peq a b => inferInstanceAs (Decidable (evalTmN env a = evalTmN env b))
  | Pd.ple a b =>
      inferInstanceAs (Decidable (evalTmN env a <= evalTmN env b))
  | Pd.plt a b => inferInstanceAs (Decidable (evalTmN env a < evalTmN env b))
  | Pd.pne a b =>
      inferInstanceAs (Decidable (Not (evalTmN env a = evalTmN env b)))
  | Pd.pdvd a b =>
      inferInstanceAs (Decidable ((evalTmN env a = 0 /\ evalTmN env b = 0) \/
        (Not (evalTmN env a = 0) /\ evalTmN env b % evalTmN env a = 0)))
  | Pd.peven a => inferInstanceAs (Decidable (evalTmN env a % 2 = 0))
  | Pd.podd a => inferInstanceAs (Decidable (evalTmN env a % 2 = 1))
  | Pd.pand p q => by
      haveI := decDenoteN env p
      haveI := decDenoteN env q
      exact inferInstanceAs (Decidable (denoteN env p /\ denoteN env q))
  | Pd.por p q => by
      haveI := decDenoteN env p
      haveI := decDenoteN env q
      exact inferInstanceAs (Decidable (denoteN env p \/ denoteN env q))
  | Pd.pimp p q => by
      haveI := decDenoteN env p
      haveI := decDenoteN env q
      exact inferInstanceAs (Decidable (denoteN env p -> denoteN env q))

def checkN (env : Nat -> Nat) (p : Pd) : Bool := decide (denoteN env p)

theorem checkN_sound (env : Nat -> Nat) (p : Pd)
    (h : checkN env p = true) : denoteN env p :=
  of_decide_eq_true h

theorem checkN_complete (env : Nat -> Nat) (p : Pd)
    (h : denoteN env p) : checkN env p = true :=
  decide_eq_true h

def updateN (env : Nat -> Nat) (k : Nat) (v : Nat) : Nat -> Nat :=
  fun i => if i = k then v else env i

theorem evalTmN_subst (env : Nat -> Nat) (k : Nat) (t : Tm) :
    (a : Tm) ->
      evalTmN env (substTm k t a)
        = evalTmN (updateN env k (evalTmN env t)) a
  | Tm.lit c => rfl
  | Tm.tvar i => by
      by_cases h : i = k
      · simp [substTm, evalTmN, updateN, h]
      · simp [substTm, evalTmN, updateN, h]
  | Tm.add a b => by
      simp [substTm, evalTmN, evalTmN_subst env k t a,
            evalTmN_subst env k t b]
  | Tm.sub a b => by
      simp [substTm, evalTmN, evalTmN_subst env k t a,
            evalTmN_subst env k t b]
  | Tm.mul a b => by
      simp [substTm, evalTmN, evalTmN_subst env k t a,
            evalTmN_subst env k t b]
  | Tm.tmod a b => by
      simp [substTm, evalTmN, evalTmN_subst env k t a,
            evalTmN_subst env k t b]

theorem denoteN_subst (env : Nat -> Nat) (k : Nat) (t : Tm) :
    (p : Pd) ->
      (denoteN env (substPd k t p) <->
       denoteN (updateN env k (evalTmN env t)) p)
  | Pd.peq a b => by simp [substPd, denoteN, evalTmN_subst]
  | Pd.ple a b => by simp [substPd, denoteN, evalTmN_subst]
  | Pd.plt a b => by simp [substPd, denoteN, evalTmN_subst]
  | Pd.pne a b => by simp [substPd, denoteN, evalTmN_subst]
  | Pd.pdvd a b => by simp [substPd, denoteN, evalTmN_subst]
  | Pd.peven a => by simp [substPd, denoteN, evalTmN_subst]
  | Pd.podd a => by simp [substPd, denoteN, evalTmN_subst]
  | Pd.pand p q => by
      simp [substPd, denoteN, denoteN_subst env k t p,
            denoteN_subst env k t q]
  | Pd.por p q => by
      simp [substPd, denoteN, denoteN_subst env k t p,
            denoteN_subst env k t q]
  | Pd.pimp p q => by
      simp [substPd, denoteN, denoteN_subst env k t p,
            denoteN_subst env k t q]

theorem witness_of_checkN (env : Nat -> Nat) (k : Nat) (tau : Tm) (p : Pd)
    (h : checkN env (substPd k tau p) = true) :
    Exists (fun v => denoteN (updateN env k v) p) :=
  Exists.intro (evalTmN env tau)
    ((denoteN_subst env k tau p).mp (of_decide_eq_true h))

def checkAllN (envs : List (Nat -> Nat)) (p : Pd) : Bool :=
  envs.all (fun env => checkN env p)

theorem checkAllN_sound (envs : List (Nat -> Nat)) (p : Pd)
    (h : checkAllN envs p = true) :
    forall env, env ∈ envs -> denoteN env p := by
  intro env hmem
  simp only [checkAllN, List.all_eq_true] at h
  exact of_decide_eq_true (h env hmem)

theorem checkAllN_witness (envs : List (Nat -> Nat)) (k : Nat) (tau : Tm)
    (p : Pd) (h : checkAllN envs (substPd k tau p) = true) :
    forall env, env ∈ envs ->
      Exists (fun v => denoteN (updateN env k v) p) :=
  fun env hmem => witness_of_checkN env k tau p
    (by
      simp only [checkAllN, List.all_eq_true] at h
      exact h env hmem)

/-- D8, kernel-checked: over Nat, 3 - 5 IS 0 (truncation is the honest
semantics, proven, never assumed). -/
example : denoteN (fun _ => 0)
    (Pd.peq (Tm.sub (Tm.lit 3) (Tm.lit 5)) (Tm.lit 0)) :=
  checkN_sound _ _ rfl

/-- ...and the SAME term over Int is NOT zero -- the divergence class
made visible on both sides of the carrier split. -/
example : denote (fun _ => 0)
    (Pd.pne (Tm.sub (Tm.lit 3) (Tm.lit 5)) (Tm.lit 0)) :=
  check_sound _ _ rfl

/-- Nat witness demo: template m := n - 1 (truncated!) discharges the
∃-claim at n = 4. -/
example : Exists (fun v => denoteN (updateN (fun _ => 4) 0 v)
    (Pd.peq (Tm.add (Tm.tvar 0) (Tm.lit 1)) (Tm.tvar 1))) :=
  witness_of_checkN (fun _ => 4) 0 (Tm.sub (Tm.tvar 1) (Tm.lit 1)) _ rfl

/-
SHAPE-6 RETIREMENT, first op: `^`.  D10 pins the exponent to a
NON-NEGATIVE LITERAL, so pow reflects through its UNROLL, the same
argument as the bounded-fold class: powTm builds the k-fold product, no
constructor enters Tm, the substitution lemma stays UNCONDITIONAL, and
decidability is inherited by decDenote over the unrolled terms.  The
quoter maps literal-exponent `^` here, so squaring templates discharge
end to end; gcd/coprime remain named skips (carrier-indexed Lean names
are a different purchase).
-/

/-- The unrolled power: k-fold product, left-nested like the quoter's
fold. -/
def powTm (a : Tm) : Nat -> Tm
  | 0 => Tm.lit 1
  | Nat.succ n => Tm.mul (powTm a n) a

/-- The mathematical fold the unroll must mean. -/
def powVals (v : Int) : Nat -> Int
  | 0 => 1
  | Nat.succ n => powVals v n * v

/-- PRESERVATION: the unrolled power evaluates to the fold of the
evaluated base, at every exponent. -/
theorem evalTm_powTm (env : Nat -> Int) (a : Tm) :
    (k : Nat) -> evalTm env (powTm a k) = powVals (evalTm env a) k
  | 0 => rfl
  | Nat.succ n => by simp [powTm, evalTm, powVals, evalTm_powTm env a n]

/-- Substitution distributes over the unroll -- the witness layer keeps
pace for free. -/
theorem substTm_powTm (i : Nat) (t : Tm) (a : Tm) :
    (k : Nat) -> substTm i t (powTm a k) = powTm (substTm i t a) k
  | 0 => rfl
  | Nat.succ n => by simp [powTm, substTm, substTm_powTm i t a n]

/-- Squaring demo: 3^2 = 9 by computation. -/
example : denote (fun _ => 3)
    (Pd.peq (powTm (Tm.tvar 0) 2) (Tm.lit 9)) :=
  check_sound _ _ rfl

/-- Source-16's shape through the unroll: 0 <= x^2 over a box. -/
example :
    forall env, env ∈ [fun _ => (-3 : Int), fun _ => 0, fun _ => 3] ->
      denote env (Pd.ple (Tm.lit 0) (powTm (Tm.tvar 0) 2)) :=
  checkAll_sound _ _ rfl

/-
NAT STMT LAYER: the box relativization crosses the carrier split, so the
template-free search route reaches Nat readings -- the
route-not-applicable skip for single-carrier Nat retires the same way
nat-sub did: ON PROOF, never by fiat.  exOnly is carrier-neutral and is
reused as-is.
-/

def denoteStmtN (env : Nat -> Nat) : Stmt -> Prop
  | Stmt.base p => denoteN env p
  | Stmt.sall k s => forall v : Nat, denoteStmtN (updateN env k v) s
  | Stmt.sex k s => Exists (fun v : Nat => denoteStmtN (updateN env k v) s)

def denoteStmtBoxN (box : List Nat) (env : Nat -> Nat) : Stmt -> Prop
  | Stmt.base p => denoteN env p
  | Stmt.sall k s =>
      forall v, v ∈ box -> denoteStmtBoxN box (updateN env k v) s
  | Stmt.sex k s =>
      Exists (fun v => v ∈ box /\ denoteStmtBoxN box (updateN env k v) s)

def checkStmtBoxN (box : List Nat) (env : Nat -> Nat) : Stmt -> Bool
  | Stmt.base p => checkN env p
  | Stmt.sall k s => box.all (fun v => checkStmtBoxN box (updateN env k v) s)
  | Stmt.sex k s => box.any (fun v => checkStmtBoxN box (updateN env k v) s)

theorem checkStmtBoxN_sound (box : List Nat) :
    (s : Stmt) -> (env : Nat -> Nat) ->
      checkStmtBoxN box env s = true -> denoteStmtBoxN box env s
  | Stmt.base p, env, h => checkN_sound env p h
  | Stmt.sall k s, env, h => by
      simp only [checkStmtBoxN, List.all_eq_true] at h
      intro v hv
      exact checkStmtBoxN_sound box s (updateN env k v) (h v hv)
  | Stmt.sex k s, env, h => by
      simp only [checkStmtBoxN, List.any_eq_true] at h
      cases h with
      | intro v hv =>
        exact Exists.intro v (And.intro hv.1
          (checkStmtBoxN_sound box s (updateN env k v) hv.2))

theorem denoteStmtN_of_box (box : List Nat) :
    (s : Stmt) -> (env : Nat -> Nat) -> exOnly s = true ->
      denoteStmtBoxN box env s -> denoteStmtN env s
  | Stmt.base _, _, _, h => h
  | Stmt.sall _ _, _, hex, _ => nomatch hex
  | Stmt.sex k s, env, hex, h => by
      cases h with
      | intro v hv =>
        exact Exists.intro v
          (denoteStmtN_of_box box s (updateN env k v) hex hv.2)

theorem checkStmtBoxN_sound_exOnly (box : List Nat) (env : Nat -> Nat)
    (s : Stmt) (hex : exOnly s = true)
    (h : checkStmtBoxN box env s = true) : denoteStmtN env s :=
  denoteStmtN_of_box box s env hex (checkStmtBoxN_sound box s env h)

/-- Nat search demo: some m has m + 1 = 4, by finite sweep, landing in the
true Nat denotation. -/
example : denoteStmtN (fun _ => 0)
    (Stmt.sex 0 (Stmt.base
      (Pd.peq (Tm.add (Tm.tvar 0) (Tm.lit 1)) (Tm.lit 4)))) :=
  checkStmtBoxN_sound_exOnly [0, 1, 2, 3] (fun _ => 0) _ rfl rfl

/-
T3 SUMMIT (level A): the compiled reading as ONE object and ONE
preservation theorem.  A `Reading` is the compiler's whole subject --
binder prefix in emission order, hypotheses in id order, conclusions in
id order -- and `compile_preserves` states, once, that its independent
denotation (real binders over an implication chain over a conjunction)
is exactly the reflected statement's denotation.  The proof COMPOSES the
per-shape lemmas; they remain the named rungs (and the guard route stays
its own theorem: per-box-point ground emission is a sibling of the
Reading grammar, not a child).
-/

structure Reading where
  binders : List Bnd
  hyps : List Pd
  concl : Pd
  concls : List Pd

/-- The whole compiler, one function: prefix fold over chain fold over
conjunction fold. -/
def compileR (r : Reading) : Stmt :=
  prefixStmt r.binders (Stmt.base (pimps r.hyps (pands r.concl r.concls)))

/-- The emitted body's independent meaning: hypotheses peel left to
right into the conjunction of conclusions. -/
def denoteChainAll (env : Nat -> Int) : List Pd -> Pd -> List Pd -> Prop
  | [], c, ds => denoteAll env c ds
  | h :: hs, c, ds => denote env h -> denoteChainAll env hs c ds

/-- A binder-prefix fold over an ARBITRARY env-indexed body -- the shape
of the emitted prop with real ∀/∃ binders. -/
def denotePrefixP (P : (Nat -> Int) -> Prop) : List Bnd -> (Nat -> Int) -> Prop
  | [], env => P env
  | Bnd.all k :: bs, env =>
      forall v : Int, denotePrefixP P bs (update env k v)
  | Bnd.ex k :: bs, env =>
      Exists (fun v : Int => denotePrefixP P bs (update env k v))

/-- The reading's independent denotation: the emitted form's meaning,
built WITHOUT compileR. -/
def readingDenote (r : Reading) (env : Nat -> Int) : Prop :=
  denotePrefixP (fun e => denoteChainAll e r.hyps r.concl r.concls)
    r.binders env

/-- Body composition: chain-over-conjunction equals the folded predicate
(the shape-2 and shape-5 lemmas, composed). -/
theorem chainAll_iff (env : Nat -> Int) :
    (hs : List Pd) -> (c : Pd) -> (ds : List Pd) ->
      (denoteChainAll env hs c ds <-> denote env (pimps hs (pands c ds)))
  | [], c, ds => compile_conj_shape env c ds
  | h :: hs, c, ds => by
      constructor
      · intro f hh
        exact (chainAll_iff env hs c ds).mp (f hh)
      · intro f hh
        exact (chainAll_iff env hs c ds).mpr (f hh)

/-- Prefix composition: any body equivalence lifts through the binder
prefix (the shape-3/4 lemma, generalized to an arbitrary body). -/
theorem prefixP_iff (P : (Nat -> Int) -> Prop) (s : Stmt)
    (h : forall env, P env <-> denoteStmt env s) :
    (bs : List Bnd) -> (env : Nat -> Int) ->
      (denotePrefixP P bs env <-> denoteStmt env (prefixStmt bs s))
  | [], env => h env
  | Bnd.all k :: bs, env => by
      constructor
      · intro f v
        exact (prefixP_iff P s h bs (update env k v)).mp (f v)
      · intro f v
        exact (prefixP_iff P s h bs (update env k v)).mpr (f v)
  | Bnd.ex k :: bs, env => by
      constructor
      · intro f
        cases f with
        | intro v hv =>
          exact Exists.intro v
            ((prefixP_iff P s h bs (update env k v)).mp hv)
      · intro f
        cases f with
        | intro v hv =>
          exact Exists.intro v
            ((prefixP_iff P s h bs (update env k v)).mpr hv)

/-- THE SUMMIT: one theorem, every reading -- the emitted form's meaning
is exactly the reflected statement's. -/
theorem compile_preserves (r : Reading) (env : Nat -> Int) :
    readingDenote r env <-> denoteStmt env (compileR r) :=
  prefixP_iff _ _
    (fun e => chainAll_iff e r.hyps r.concl r.concls) r.binders env

/-- Summit demo: a two-binder, one-hypothesis, one-conclusion reading
(the 68-between shape), equivalent to its reflected statement -- and the
∃-only body then discharges by search through the same statement. -/
example :
    readingDenote
      { binders := [Bnd.all 0, Bnd.all 1, Bnd.ex 2],
        hyps := [Pd.ple (Tm.tvar 0) (Tm.tvar 1)],
        concl := Pd.ple (Tm.tvar 0) (Tm.tvar 2),
        concls := [Pd.ple (Tm.tvar 2) (Tm.tvar 1)] }
      (fun _ => 0) <->
    denoteStmt (fun _ => 0)
      (Stmt.sall 0 (Stmt.sall 1 (Stmt.sex 2 (Stmt.base
        (Pd.pimp (Pd.ple (Tm.tvar 0) (Tm.tvar 1))
          (Pd.pand (Pd.ple (Tm.tvar 0) (Tm.tvar 2))
            (Pd.ple (Tm.tvar 2) (Tm.tvar 1)))))))) :=
  compile_preserves _ _

/-
T3 SUMMIT (level B): the reference emitter.  `emitProp` renders an
`EReading` -- the compiler's whole subject carrying its surface names
and carriers -- to the EXACT proposition text the shipped Python
compiler (generators/math_compile.py) emits, theorem wrapper aside.
The generated pin file (tools/fg_emit_pins.lean) holds kernel-checked
byte equalities between this emitter and live compiler output for
transcribed corpus readings, and `toReading` ties the SAME datum to
level A: one EReading yields both the pinned bytes and the statement
`compile_preserves` speaks about.  Scope: the binary-argument slice
(the shipped compiler flattens list-shaped + / * and renders pow with
`^`; the pin generator names every such skip).
-/

/-- One binder segment as emitted: quantifier flavor and its
(name, carrier) columns in listed order. -/
structure Seg where
  ex : Bool
  vars : List (String × String)

/-- A reading with its surface data: segments in emission order, the
index -> name table (sorted-name order, the quoter's convention), and
the body parts in id order. -/
structure EReading where
  segs : List Seg
  names : List String
  hyps : List Pd
  concl : Pd
  concls : List Pd

/-- Literal rendering: non-negative bare, negative wrapped `(-k)`. -/
def emitInt (k : Int) : String :=
  if k < 0 then "(" ++ toString k ++ ")" else toString k

/-- Term rendering: one parenthesized group per compound node, args
never reordered (F-G discipline, mirrored). -/
def emitTm (names : List String) : Tm -> String
  | Tm.lit k => emitInt k
  | Tm.tvar i => names.getD i "_"
  | Tm.add a b => "(" ++ emitTm names a ++ " + " ++ emitTm names b ++ ")"
  | Tm.sub a b => "(" ++ emitTm names a ++ " - " ++ emitTm names b ++ ")"
  | Tm.mul a b => "(" ++ emitTm names a ++ " * " ++ emitTm names b ++ ")"
  | Tm.tmod a b => "(" ++ emitTm names a ++ " % " ++ emitTm names b ++ ")"

/-- Predicate rendering: comparison atoms, the Dvd/Even/Odd forms, and
the binary connectives, each fully parenthesized. -/
def emitPd (names : List String) : Pd -> String
  | Pd.peq a b => "(" ++ emitTm names a ++ " = " ++ emitTm names b ++ ")"
  | Pd.ple a b => "(" ++ emitTm names a ++ " ≤ " ++ emitTm names b ++ ")"
  | Pd.plt a b => "(" ++ emitTm names a ++ " < " ++ emitTm names b ++ ")"
  | Pd.pne a b => "(" ++ emitTm names a ++ " ≠ " ++ emitTm names b ++ ")"
  | Pd.pdvd a b => "(" ++ emitTm names a ++ " ∣ " ++ emitTm names b ++ ")"
  | Pd.peven a => "(Even " ++ emitTm names a ++ ")"
  | Pd.podd a => "(Odd " ++ emitTm names a ++ ")"
  | Pd.pand p q => "(" ++ emitPd names p ++ " ∧ " ++ emitPd names q ++ ")"
  | Pd.por p q => "(" ++ emitPd names p ++ " ∨ " ++ emitPd names q ++ ")"
  | Pd.pimp p q => "(" ++ emitPd names p ++ " → " ++ emitPd names q ++ ")"

/-- Binder columns: `(x : C)`, space-separated. -/
def emitVars : List (String × String) -> String
  | [] => ""
  | [(n, c)] => "(" ++ n ++ " : " ++ c ++ ")"
  | (n, c) :: vs => "(" ++ n ++ " : " ++ c ++ ") " ++ emitVars vs

/-- One segment: quantifier symbol, space, columns. -/
def emitSeg (s : Seg) : String :=
  (if s.ex then "∃" else "∀") ++ " " ++ emitVars s.vars

/-- All segments, each closed by `, ` (the compiler's prefix build). -/
def emitSegs : List Seg -> String
  | [] => ""
  | s :: ss => emitSeg s ++ ", " ++ emitSegs ss

/-- Conjoined-conclusion tail, flat at the top level. -/
def emitConjTail (names : List String) : List Pd -> String
  | [] => ""
  | d :: ds => " ∧ " ++ emitPd names d ++ emitConjTail names ds

/-- The conclusion: bare when single; one wrapped FLAT conjunction when
several demands exist (the compiler joins n-ary at the top level only,
unlike the binarized Pd.pand fold underneath). -/
def emitConcl (names : List String) (c : Pd) : List Pd -> String
  | [] => emitPd names c
  | d :: ds => "(" ++ emitPd names c ++ emitConjTail names (d :: ds) ++ ")"

/-- The body: hypotheses peel with ` → ` into the conclusion. -/
def emitBody (names : List String) (c : Pd) (ds : List Pd) : List Pd -> String
  | [] => emitConcl names c ds
  | h :: hs => emitPd names h ++ " → " ++ emitBody names c ds hs

/-- The whole proposition: segment prefix then body -- byte-for-byte
the shipped compiler's `<prop>`. -/
def emitProp (e : EReading) : String :=
  emitSegs e.segs ++ emitBody e.names e.concl e.concls e.hyps

/-- Name -> index in the sorted-name table (total; a miss runs off the
end and renders `_`, which can never byte-match a pin). -/
def idxOf (n : String) : List String -> Nat
  | [] => 0
  | m :: ms => if m = n then 0 else idxOf n ms + 1

/-- A segment's binder entries, level-A shaped (hand recursion: a
library map would specialize its closure into an opaque `_spec_`
constant and fail the audited-environment whitelist). -/
def segBnds (names : List String) (ex : Bool) : List (String × String) -> List Bnd
  | [] => []
  | v :: vs =>
      (if ex then Bnd.ex (idxOf v.1 names) else Bnd.all (idxOf v.1 names))
        :: segBnds names ex vs

/-- All segments' binder entries in emission order. -/
def segsBnds (names : List String) : List Seg -> List Bnd
  | [] => []
  | s :: ss => segBnds names s.ex s.vars ++ segsBnds names ss

/-- The level-A tie: the SAME datum that pins bytes also names the
statement `compile_preserves` speaks about. -/
def toReading (e : EReading) : Reading :=
  { binders := segsBnds e.names e.segs,
    hyps := e.hyps, concl := e.concl, concls := e.concls }

/-- Emitter demo: the 68-between shape renders to its exact surface. -/
example :
    emitProp
      { segs := [{ ex := false, vars := [("a", "Int"), ("b", "Int")] },
                 { ex := true, vars := [("c", "Int")] }],
        names := ["a", "b", "c"],
        hyps := [Pd.ple (Tm.tvar 0) (Tm.tvar 1)],
        concl := Pd.ple (Tm.tvar 0) (Tm.tvar 2),
        concls := [Pd.ple (Tm.tvar 2) (Tm.tvar 1)] } =
    "∀ (a : Int) (b : Int), ∃ (c : Int), (a ≤ b) → ((a ≤ c) ∧ (c ≤ b))" :=
  rfl

/-
P1 (the bounded big-operator class): bigsum/bigprod reflect through their
UNROLL.  The fragment admits the class precisely because its bounds are
NON-NEGATIVE LITERALS -- the fold is finitely and exactly expandable -- and
the reflect slice uses the SAME argument: the Python-side builder
(run/reflect_shadow.quote_term) instantiates the bound index and emits
`sumTm`/`prodTm` over the concrete body list, in the S6 fold idiom (one
lemma per shape, every width covered).  So no binding constructor enters
`Tm`, the substitution lemma stays UNCONDITIONAL (substTm_sumTm /
substTm_prodTm below show it covers unrolled folds verbatim -- no capture,
because nothing is bound), and decidability is inherited: `decDenote`
already decides every predicate over the unrolled terms.  A future
symbolic-bound purchase is exactly the point where a true binder (and a
conditional substitution story) becomes unavoidable -- which is why it is
a SEPARATE purchase, not a widening of this one.
-/

/-- The unrolled sum: the reflect form of bigsum, one Tm per index value. -/
def sumTm : List Tm -> Tm
  | [] => Tm.lit 0
  | t :: ts => Tm.add t (sumTm ts)

/-- The unrolled product: the reflect form of bigprod. -/
def prodTm : List Tm -> Tm
  | [] => Tm.lit 1
  | t :: ts => Tm.mul t (prodTm ts)

/-- The mathematical fold the unroll must mean: sum of a value list. -/
def sumVals : List Int -> Int
  | [] => 0
  | v :: vs => v + sumVals vs

/-- Product of a value list. -/
def prodVals : List Int -> Int
  | [] => 1
  | v :: vs => v * prodVals vs

/-- PRESERVATION: the unrolled sum evaluates to the fold of the evaluated
bodies, at every width -- the reflect-side sibling of eval/SMT agreement. -/
theorem evalTm_sumTm (env : Nat -> Int) :
    (ts : List Tm) -> evalTm env (sumTm ts) = sumVals (ts.map (evalTm env))
  | [] => rfl
  | t :: ts => by
      simp [sumTm, evalTm, sumVals, evalTm_sumTm env ts]

/-- PRESERVATION for the product fold. -/
theorem evalTm_prodTm (env : Nat -> Int) :
    (ts : List Tm) -> evalTm env (prodTm ts) = prodVals (ts.map (evalTm env))
  | [] => rfl
  | t :: ts => by
      simp [prodTm, evalTm, prodVals, evalTm_prodTm env ts]

/-- The witness layer keeps pace for free: substitution distributes over the
unrolled sum, so the UNCONDITIONAL substitution lemma covers it verbatim. -/
theorem substTm_sumTm (k : Nat) (t : Tm) :
    (ts : List Tm) -> substTm k t (sumTm ts) = sumTm (ts.map (substTm k t))
  | [] => rfl
  | a :: as => by
      simp [sumTm, substTm, substTm_sumTm k t as]

/-- And over the unrolled product. -/
theorem substTm_prodTm (k : Nat) (t : Tm) :
    (ts : List Tm) -> substTm k t (prodTm ts) = prodTm (ts.map (substTm k t))
  | [] => rfl
  | a :: as => by
      simp [prodTm, substTm, substTm_prodTm k t as]

/-- Reflection demo: the sum of 1..4 is 10, decided by computation. -/
example : denote (fun _ => 0)
    (Pd.peq (sumTm [Tm.lit 1, Tm.lit 2, Tm.lit 3, Tm.lit 4]) (Tm.lit 10)) :=
  check_sound _ _ rfl

/-- With an outer variable in the body (the unroll of bigsum i 1 3 (i * x)
at slot 0): 1x + 2x + 3x = 6x, over the whole box. -/
example :
    forall env, env ∈ [fun _ => (-2 : Int), fun _ => 0, fun _ => 7] ->
      denote env (Pd.peq
        (sumTm [Tm.mul (Tm.lit 1) (Tm.tvar 0),
                Tm.mul (Tm.lit 2) (Tm.tvar 0),
                Tm.mul (Tm.lit 3) (Tm.tvar 0)])
        (Tm.mul (Tm.lit 6) (Tm.tvar 0))) :=
  checkAll_sound _ _ rfl

/-- Product demo: 5 factorial by computation. -/
example : denote (fun _ => 0)
    (Pd.peq (prodTm [Tm.lit 1, Tm.lit 2, Tm.lit 3, Tm.lit 4, Tm.lit 5])
      (Tm.lit 120)) :=
  check_sound _ _ rfl

/-
P2 (the bounded Finset carrier + cardinality): `card {i in Icc lo hi | P i}`
reflects through the SAME unroll as the fold.  NON-NEGATIVE LITERAL bounds make
the set finite and exactly enumerable, so cardinality is a sum of 0/1
indicators, one per index value.  The reflect `Tm` has no term-level
conditional, so the builder (run/reflect_shadow.quote_term) covers the
INDEX-ONLY filter: with the index substituted to a literal the filter is
closed, so each indicator is a decided literal.  `cardTm` below is that
unrolled indicator sum -- shaped exactly like `sumTm`, so it adds NO binding
constructor to `Tm`, the substitution lemma stays UNCONDITIONAL
(`substTm_cardTm`), and decidability is inherited: `decDenote` already decides
every predicate over the unrolled terms.  An object-dependent filter is the
point where a term-level conditional (a genuine branching constructor) becomes
unavoidable -- which is why it is a SEPARATE purchase and a NAMED reflect skip
(`card:object-filter`), not a widening of this one.
-/

/-- The unrolled cardinality: the sum of 0/1 indicators, one per index value
(true = the filter holds there).  Shaped like sumTm so its lemmas mirror it. -/
def cardTm : List Bool -> Tm
  | [] => Tm.lit 0
  | b :: bs => Tm.add (Tm.lit (if b then 1 else 0)) (cardTm bs)

/-- The mathematical count the unroll must mean: the number of true bits. -/
def countTrue : List Bool -> Int
  | [] => 0
  | b :: bs => (if b then 1 else 0) + countTrue bs

/-- PRESERVATION: the unrolled cardinality evaluates to the count of true bits,
at every width -- the reflect-side sibling of eval/SMT counting agreement. -/
theorem evalTm_cardTm (env : Nat -> Int) :
    (bits : List Bool) -> evalTm env (cardTm bits) = countTrue bits
  | [] => rfl
  | b :: bs => by
      simp [cardTm, evalTm, countTrue, evalTm_cardTm env bs]

/-- The witness layer keeps pace for free: the unrolled cardinality has no free
index, so substitution leaves it verbatim -- the UNCONDITIONAL lemma. -/
theorem substTm_cardTm (k : Nat) (t : Tm) :
    (bits : List Bool) -> substTm k t (cardTm bits) = cardTm bits
  | [] => rfl
  | b :: bs => by
      simp [cardTm, substTm, substTm_cardTm k t bs]

/-- Reflection demo: exactly 3 of the integers 1..6 are even (bits are the
even-ness of 1,2,3,4,5,6), decided by computation. -/
example : denote (fun _ => 0)
    (Pd.peq (cardTm [false, true, false, true, false, true]) (Tm.lit 3)) :=
  check_sound _ _ rfl

/-- Cardinality demo: the empty set has cardinality 0. -/
example : denote (fun _ => 0) (Pd.peq (cardTm []) (Tm.lit 0)) :=
  check_sound _ _ rfl

/-- The count identity used everywhere: cardinality is at most the width. -/
example : denote (fun _ => 0)
    (Pd.ple (cardTm [true, false, true, true]) (Tm.lit 4)) :=
  check_sound _ _ rfl

end FgReflect
