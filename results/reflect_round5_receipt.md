# Authoring round 5 for `refusal-symbolic-exponent` — the `check`/`decDenote` case

*(the second route to tower-class capability, PLAN_HAMMER.md H1.3; a
purchase-driver firing that YIELDED the bill and took the ride instead)*

## The probe, run rather than read — and it MOVED

`python3 tools/lean_env_probe.py`, run in this container, read

    lean-absent:not-installed

The committed artifact this session started from read

    lean-absent:policy-denied:elan.lean-lang.org,lakecache.blob.core.windows.net,
                              release.lean-lang.org,releases.lean-lang.org

**Four hosts that answered 403 to CONNECT when the committed reading was
taken answer 200 now.** All six enumerated hosts read `reachable`; the
verdict is `not-installed` purely because setup.sh has not been run with
`--with-lean` in this container. That is a change of KIND, not of degree,
and it is the one reading in this session a maintainer should not have to
dig for: `docs/lean-capable-environment.md` treats a policy denial as
needing a human to edit the environment's network policy, and *that* is no
longer the blocker on this container class. Whether an install would
SUCCEED is a different question this probe does not answer and does not
pretend to — its own honesty note says a reachable host never predicts a
successful install, and the Mathlib olean CDN is not enumerated.

The rule did not change, so neither did the decision. PLAN_FRAGMENT §3.1
rule 3 gates tower-class work on `lean-local` and on nothing else;
`lean-absent:not-installed` is not `lean-local`, so this unattended session
**YIELDED** the tower-class purchase. Recorded as a reading, never widened
into a licence.

## The purchase that was not made

`python3 tools/purchase_frontier.py` derives 13 rows, 3 open, **0 ready**:

| row | class | blocking refusals | returns to ready |
|---|---|---|---|
| `refusal-symbolic-exponent` | iteration-class | symbolic-exponent ×12 | 5 |
| `refusal-function-symbol` | definitional-extension | function-symbol ×11 | 5 |
| `refusal-set-carrier` | tower-class | set-membership ×4 | 0 |

Not one is additive-class, so the yield is total rather than partial: there
is no "strictly-first fully-verifiable Lean-free half" to ship here, because
no open row has one. No purchase was made; no flywheel slot was spent.

## The ride: what round 5 adds, and why r4 was not the last round

Round 4 (`p7-parallel-tower-r4`, PR #145) **PASSED** — `detail` is null by
design, and the pass is consumed in `results/hammer_verdicts.json` on main.
Its origin note declared itself the last round for this row. That was one
reading short, and this receipt says so plainly rather than quietly
authoring a sixth thing.

`tests/test_symbolic_exponent_class.py` names the tower **twice, at two
granularities**:

* the executable assertion
  `test_the_reflect_slice_has_no_term_level_exponent` enumerates **five**
  walkers — `evalTm`, `evalTmN`, `substTm`, `evalTm_subst`, `evalTmN_subst`
  — and r1..r4 met all five;
* the same file's module docstring enumerates **six** — "a new `evalTm`
  case, a new `evalTmN` case, a new `substTm` case, a new
  `substTm_evalTm` case, a new `check`/`decDenote` case".

r4 read the narrower enumeration and stopped. The sixth item — the
`check`/`decDenote` case — is the one the prototype had **no answer for at
all**: r4's parallel tower is TERMS ONLY, so nothing over it was ever
decided, checked, or proven sound, and "decidability INHERITED from
decDenote" (§3.1 rule 3's third additive criterion) stayed an untested
claim where `powp` is concerned.

Round 5 carries r4 verbatim and adds exactly that layer:

| declaration | mirrors | line |
|---|---|---|
| `PdP` (4 ctors: 2 atoms + `pand`/`pimp`) | `Pd` | `tools/FgReflect.lean:52-65` |
| `denoteP` | `denote` | `:77-92` |
| `decDenoteP` | `decDenote` | `:98-121` |
| `checkP` | `check` | `:123` |
| `checkP_sound` | `check_sound` | `:127-129` |
| `checkP_sound_powp` | — the tooth | new |

The two connectives are in because their recursion is what actually
exercises inherited decidability; the atoms alone would not.

`checkP_sound_powp` is what makes the round about THIS row rather than about
predicates in general: a `true` from the checker on an equation whose left
side carries the new `powp` constructor is a proof about the power itself.
It is stated against `TmP.lit 0` so the conclusion is a closed arithmetic
fact rather than a tautology, and it is discharged by `checkP_sound` alone —
no arm reasons about `^` specially, so `powp` reaches `decDenoteP` only
through `evalTmP`, exactly as `Tm.mul` reaches `decDenote` through `evalTm`.
That is the inheritance claim cashed out, or refuted, by the lane.

Pre-flight, locally and Lean-free: `declares_missing` is `[]` (all six names
appear in the candidate's own text) and `buildloop/validate_lean.py` returns
`ok` over the COMPOSED bytes.

## Bounds held, restated because they are the point

* The candidate is **appended** text re-entering `namespace FgReflect`, so
  `Tm` and `Pd` cannot be extended — hence a PARALLEL tower, which is what
  prototyping tower-class material at a session boundary means.
* A candidate is a **PROPOSAL**. `tools/FgReflect.lean` is untouched and has
  no write path from `results/reflect_candidates.json`. Adopting a passed
  prototype is an attended purchase decision under the ordinary bill
  discipline.
* "It elaborated in the batch ride" is a reason to keep authoring and never
  a done-predicate; the CI lane verdict stays final.
* If round 5 passes, the prototype answers BOTH enumerations the measurement
  carries and the row's authoring queue is **complete** — at which point the
  honest next act is to stop authoring and hand the adoption to an attended
  session, not to invent a seventh requirement.
