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

/-- Reflection demo: the entire proof is `rfl` -- the kernel evaluates the
checker and the soundness theorem does the rest.  (1 < 3 at env 0 = 3.) -/
example : denote (fun _ => 3) (Pd.plt (Tm.lit 1) (Tm.tvar 0)) :=
  check_sound _ _ rfl

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

end FgReflect
