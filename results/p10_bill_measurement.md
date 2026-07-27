# P10 bill measurement — `refusal-set-carrier`, priced by attempt rather than by estimate

**Session**: C3 purchase driver firing, 2026-07-27T03:05Z, branch
`claude/adoring-meitner-mrsgdh`, PR #203.
**Probe verdict**: `lean-local` (RUN in this container, not read off disk).
**Purchase priced**: NONE.  This is a measurement of the bill, not the bill.

## Why a measurement and not a purchase

`refusal-set-carrier` is the one open row (`bill_class: tower-class`), and
under PLAN_FRAGMENT §3.1 rule 3 a `lean-local` container is licensed to take
tower-class work — the yield clause does not fire.  So this firing tried to
take it.  What it found is that the row's cost is **not** where the row's
prose puts it, and the cheap route is closed by a trust root.  Both halves
are recorded here so the next session starts from the reading instead of
re-deriving it.

## Finding 1 — the semantic core is CHEAP, and it elaborates

§4 prices the row as "an uninterpreted predicate in the SMT mirror and a
`Pd` constructor plus its `Decidable` story in the reflect slice".  The
`Decidable` story was the part expected to hurt: a `Prop`-valued membership
in an arbitrary set forces a `DecidablePred` hypothesis, which would make
the substitution lemma CONDITIONAL and trip §3.1 rule 3(b).

It does not have to be `Prop`-valued.  Modelling the set assignment as
`Nat -> Int -> Bool` makes `mem s v = true` an ordinary `Bool` equality, so
`decDenote` discharges it with the same `inferInstanceAs` every other atom
uses — **decidability stays INHERITED and the substitution lemma stays
UNCONDITIONAL**.  Measured, not argued: with

* `Pd.pmem : Tm -> Nat -> Pd` (the set named by an INDEX — a set is still not
  a term, so the constructor is the only place a set name may appear),
* the `denote` / `decDenote` / `substPd` / `denote_subst` cases, and
* the same four cases on the `Nat` layer (`denoteN`, `decDenoteN`,
  `denoteN_subst`),

`tools/FgReflect.lean` elaborated in this container with **zero errors**.
The substitution cases discharge by `simp [substPd, denote, evalTm_subst]` —
the element is substituted, the set index is a name substitution cannot
reach, which is exactly what keeps the lemma unconditional.

So the constructor plus its Decidable story is a ~20-line edit, and the
`Pd`-side of this row is de-risked.

## Finding 2 — the cost is the SET ENVIRONMENT, and the cheap way to carry it is FENCED

An arbitrary set has no definition, so the honest reading of a theorem about
one is "for EVERY assignment of sets to the reading's set names".  Something
must carry that assignment into `denote`, and there are two ways:

1. **A typeclass** (`class SetEnv where mem : Nat -> Int -> Bool`) plus
   `variable [SetEnv]`.  Lean auto-binds it only where used, so **call sites
   stay unchanged** and ~60 signatures never move.  This is the zero-churn
   route, and it is the one this firing tried first.
2. **An explicit parameter** threaded through `denote`, `decDenote`, `check`,
   `checkAll`, `denoteStmt`, the shape theorems and the whole `Nat` layer —
   every call site updated.

**Route 1 is closed, and by a trust root.**  Lean auto-includes an *instance*
section variable into every theorem in scope and then lints the ones that did
not use it; the slice's arithmetic lemmas (`substTm_sumTm`, `substTm_prodTm`,
`evalTm_cardTm`, `substPd_zmodEq`, `denote_zmodEq`, …) never mention
membership, so each emits `unused section variable`.  `LeanBackend.elaborate`
requires a warning-free elaboration, so the warnings are fatal.  The two ways
out both fail:

* `omit [SetEnv] in` — **syntactically unavailable here**.  `omit ... in` may
  not follow a doc comment (`unexpected token 'omit'; expected 'lemma'`), and
  every one of these theorems carries one; placed *above* the doc comment it
  parses but does not associate, and the warning stands.
* `set_option linter.unusedSectionVars false` — refused by the escape gate:
  `non-whitelisted set_option 'linter.unusedSectionVars'`.
  `buildloop/validate_lean.py` (⚠D12) whitelists exactly `maxHeartbeats` and
  `maxRecDepth`.

That gate is the escape-gate blocklist, which CLAUDE.md names as a trust root:
it changes only through the PLAN_REFLECT S4a→S4a′→S4b ceremony with explicit
user sign-off, **never as part of ordinary work**.  So no session may buy this
row by widening it.  The fence did exactly what it exists to do, and the
correct outcome is that the cheap route is unavailable rather than that the
gate is inconvenient.

**Therefore the real bill is route 2**: threading a set environment through
the tower — mechanical, but ~40–60 signatures plus their in-file call sites,
each round gated on an ~83-second local elaboration.  That is the honest cost
of this row, and it is a cost this firing measured rather than estimated.

## What this changes about the row

Nothing about its *status*: `refusal-set-carrier` stays OPEN and tower-class.
What moves is the SHAPE of its price.  The row's prose bills the `Pd`
constructor and the `Decidable` story as the expensive part; measured, those
are the cheap part and they work.  The expensive part is the environment
plumbing the row never names — and it is expensive in a way that is
mechanical rather than uncertain, which is a better position to be in than
the row currently describes.

Unchanged and worth restating: this row still returns **zero** subjects to
ready (`purchase_frontier`: "open rows would return 0 one at a time, 0 if all
land"), and its whole measured inventory is one subject
(`09_Sets#definition-003`, `free-set-variable: 1`, `set-valued-param: 0`).
A large bill against a small demand, exactly as
`tests/test_set_object_class.py` and PLAN_FRAGMENT §4 already say.

## Bounds

`tools/FgReflect.lean` was edited during the measurement and is **reverted to
pristine** in this diff — a half-threaded tower is never shipped into a
certified slice, and `git status` on that path is clean.  No ceremony-reserved
surface in the diff: `kernel/certs.py`, `TRUST.md`,
`buildloop/growth_protocol.py`, `buildloop/validate_lean.py`, `setup.sh`,
`ci/`, `.claude/`, `.github/` all untouched — in particular the escape gate
that refused route 1 was READ and not widened.  P5 not promoted.  No park
recorded or lifted.  No refusal recorded: nothing here is a reading about a
corpus subject.  Ledgers append-only.  No purchase priced, so no flywheel slot
spent and no re-census delta is owed.

## The loop state this firing also measured

Recorded here because it is the reason a purchase-axis reader should look at
the board before pricing anything:

* **The purchase loop is wedged shut at `main`.**  `tools/loop_guard.py`'s
  `purchase` branch returns before the `mine_created_at` block, so the
  post-claim tie-break the PURCHASE DRIVER prompt mandates is unreachable and
  answers `EXIT` on the session's OWN claim.  Reproduced live this firing:
  pre-claim `CLAIM: no open purchase PR`, post-claim
  `EXIT (PR #203): an open C3 purchase PR exists`.
* **PR #198 fixes it, is fully green (including `trust-surface` and
  `bill-manifest`), and is stuck**: `mergeable_state: dirty` — conflicted with
  `main` since #201 landed, so its green is stale.  It is titled `C3 guard:`,
  which no self-merge or watchdog rule covers, and #200 fences the watchdog
  from rebasing another session's branch.  Nothing on the board will pick it
  up; it needs a maintainer.
* This firing proceeded past its own spurious `EXIT` deliberately: its claim
  was the only open `C3 purchase` PR, so the true post-claim answer is `CLAIM`,
  and the prompt names exit-on-own-claim as the defect it is
  (`test_a_session_never_exits_on_its_own_claim`).

## A stale premise retired

PR #181 argues this image's Mathlib is only partly built and that `lean-local`
is therefore a false reading.  **That is no longer true of this image.**
Measured here: `mathlib` 5527 oleans, `batteries` 157, `aesop` 110, `Qq` 11,
`plausible` 8, `proofwidgets` 11, `LeanSearchClient` 4, `importGraph` 2; only
`Cli` is absent.  `tests/test_fg_reflect_lean.py` — which really elaborates
the slice — passes locally in 83 s.  `lean-local` is a TRUE reading in this
container, and the local elaboration loop this measurement ran on is the
capability rule 3 says it is.
