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

/-- Fragment predicates, v0: the three order/equality atoms and the three
connectives the reading grammar admits. -/
inductive Pd where
  | peq : Tm -> Tm -> Pd
  | ple : Tm -> Tm -> Pd
  | plt : Tm -> Tm -> Pd
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

/-- The denotation: what a predicate MEANS at an environment, as a Prop.
This is the ground truth the checker is proven against. -/
def denote (env : Nat -> Int) : Pd -> Prop
  | Pd.peq a b => evalTm env a = evalTm env b
  | Pd.ple a b => evalTm env a <= evalTm env b
  | Pd.plt a b => evalTm env a < evalTm env b
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

/-- Reflection demo: the entire proof is `rfl` -- the kernel evaluates the
checker and the soundness theorem does the rest.  (1 < 3 at env 0 = 3.) -/
example : denote (fun _ => 3) (Pd.plt (Tm.lit 1) (Tm.tvar 0)) :=
  check_sound _ _ rfl

/-- And at the box layer: 0 <= x * x checked over a tiny explicit box. -/
example :
    forall env, env ∈ [fun _ => (-2 : Int), fun _ => 0, fun _ => 2] ->
      denote env (Pd.ple (Tm.lit 0) (Tm.mul (Tm.tvar 0) (Tm.tvar 0))) :=
  checkAll_sound _ _ rfl

end FgReflect
