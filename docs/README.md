# Documentation guide — start here

This repository's documentation grew alongside a running research program,
and it reads that way: dense, jargon-heavy, and written for sessions that
already know the vocabulary.  This page is the entry point for a human who
does not.  It explains the project in plain language, gives a reading order,
defines the jargon, and maps every document to its purpose.

One rule to know before reading anything: **live state is never in prose.**
Corpus counts, queue contents, and "what to do next" are all derived from
committed artifacts by `python3 tools/session_brief.py`.  If a document and
the brief disagree, the brief wins.  Documents here describe *design and
law*, not current state — except `PLAN_FRAGMENT.md` §1, which is rewritten
every cycle and is the one prose section that tracks the loop.

## What this project is, in plain English

The project is an experiment in using an LLM to build software — and now
formal mathematics — **without ever trusting the LLM**.  The rules:

1. The LLM may only write *declarative specifications* (pure data, no
   code).  A lexical gate rejects anything else before it goes further.
2. Deterministic, non-LLM machinery turns each spec into an artifact
   (a codec, a Lean statement, a proof attempt).
3. Every artifact runs sandboxed and is judged by a small, fixed **kernel**
   against a declared contract, using two independent evidence channels
   (e.g. Z3 *and* CVC5, or a Dafny proof *and* Hypothesis fuzzing).
   Nothing is trusted for who produced it — only for what checked it.

The pattern was first proven on a deliberately simple domain: **binary
format codecs**, where the contract `decode(encode(x)) == x` is total and
mechanical.  The pattern — not the codecs — is what transferred to the real
target: **certified translation between natural-language mathematics and
the Lean proof assistant** ("autoformalization").  An English theorem
statement becomes a machine-checked Lean statement, with every step either
deterministic or kernel-verified, and every failure recorded as a named,
honest refusal rather than papered over.

Since mid-2026 the mining loop **runs itself**: recurring cloud sessions
(fired by scheduled "Routines") pick math sources off a committed frontier,
author and certify readings, and ship pull requests that self-merge when
every check is green.  A "trust-surface" fence forces a human merge for any
change that touches the trusted base — capability grows automatically,
trust never does.

## Reading order

For a first pass, read in this order and skip the rest until needed:

1. **[../README.md](../README.md)** — what the system is: the five hard
   constraints, the two-tier trust model, the build philosophy.
2. **[architecture.md](architecture.md)** — the one-page visual map of the
   Lean effort: the trust spine, both translation directions, the growth
   lanes, and the automated flywheel.
3. **[../TRUST.md](../TRUST.md)** — exactly what is trusted, enumerated
   line by line.
4. **[../FORMALIZATION.md](../FORMALIZATION.md)** — the specification of
   the math-reading fragment: how English becomes a checked Lean statement.
5. **[../PLAN_FRAGMENT.md](../PLAN_FRAGMENT.md)** — the live operating
   plan.  §0 is the program in one paragraph; §1 is the always-current
   state; §3.1 is the protocol the automated sessions follow.
6. **[../CLAUDE.md](../CLAUDE.md)** — the session router: the invariants
   and the command index.  Short, and everything in it is load-bearing.

## Glossary

The project's working vocabulary, in dependency order — later entries build
on earlier ones.

**kernel / TCB** — the trusted computing base: the small fixed component
(`kernel/`) that adjudicates artifacts against contracts, plus the
outsourced checkers it wraps (Z3, CVC5, Dafny, Hypothesis, the Lean
toolchain).  Enumerated in `TRUST.md`.  The only thing trusted by fiat.

**trust root** — anything whose verdict is believed without further
checking: the kernel checkers, the contract types, the escape-gate
blocklist.  The cardinal law: *trust roots never grow by purchase or
economics* — only through an explicit human-signed ceremony.

**spec / reading / MathReading** — the only artifact class the LLM may
produce.  For math, a *reading* is a JSON spec of one English statement
whose quoted demands must appear verbatim in the source text.  Authored in
one LLM call, never re-rolled.

**fragment** — the subset of mathematical language the deterministic
machinery can translate: its carriers (ℤ, ℕ…), operator words, and
quantifier shapes.  Statements outside it get a *named refusal*, not a
guess.

**refusal** — a first-class failure: a gate says exactly why a statement
cannot be handled (e.g. `carrier:Real`).  Refusals are demand data — they
name what the fragment is missing and thereby what to buy next.

**corpus / source / node** — a body of human-written math taken in
verbatim (a blueprint site, a textbook).  Intake is the *only* networked
step; each fetched page is hashed and everything downstream is offline and
deterministic.  A *node* is one statement in a corpus.

**census** — the measurement pass that classifies every node of every
corpus as *attempt-candidate* (inside the fragment), *out-of-fragment*
(with a named miss signal), or *no-signal*.  The census reports signals,
never fidelity verdicts.

**miss signal / miss histogram** — the named reason a node is out of
fragment.  Aggregated over the portfolio, the histogram is literally the
price list: the biggest bar names the purchase that unblocks the most math.

**frontier** — `results/frontier.json`: the committed queue of ready
sources (by prose-hash) and blocked groups (by miss signal) that each
automated cycle consumes.

**purchase** — one battery-gated expansion of the fragment (a new operator
family, a new carrier).  Strictly one per flywheel cycle; its measured
re-census delta is committed in the same session.  A purchase with no
delta is recorded evidence to buy differently, never retried silently.
The P1 purchase (commit `03e1a00`) is the worked template.

**battery** — the fixed suite of admission checks a purchase or new
vocabulary word must pass: well-formedness, non-triviality, differential
instance agreement, compile round-trip, symbolic all-values SMT verdicts.

**DL / MDL / pricing** — description length.  New vocabulary is admitted
only if it strictly shrinks the corpus's description length and is used by
at least two independent ("exogenous") sources.  Compression is the
currency that keeps growth honest; `COMPRESSION.md` is the program.

**cert / statement-cert / proof-cert** — the kernel's positive verdicts.
A statement-cert says a Lean statement elaborates (compiles) at the pinned
toolchain; a proof-cert says a proof of it was kernel-checked.  The ladder
is `nothing → statement-cert → proof-cert`.

**escape gate** — `buildloop/validate_lean.py`: the lexical blocklist that
keeps generated Lean inside a safe surface (no `axiom`, no metaprogramming
escape hatches) before anything is built.

**tooth / teeth / red / green** — a *tooth* is a test that bites: every
rule and done-condition in the plans exists as a predicate some test
evaluates, never only as prose.  *Red* = failing, *green* = passing.  The
full suite (~1150 teeth) is the per-commit gate.  "Declare-or-red": a
recorded lesson must cite the tooth that enforces it, or state why none
can exist.

**lane / ride / `[lean-fast]` / `[lean-ci]` / `[lean-hammer]`** — Lean
elaboration is slow, so it runs as a batched CI job (the *lane*), fired by
a bracketed marker in a commit message.  A Lean-touching change *rides*
the lane; the lane's verdict — not a local build — is the done-predicate.
Local Lean (where a container has it; see
[lean-capable-environment.md](lean-capable-environment.md)) is for
authoring iteration only.

**flywheel / cycle** — the one loop: census → miss histogram → one
purchase → re-census → committed delta.  A *cycle* is one automated
session's trip around it (or around the free corpus half of it).

**driver session / Routine** — a *Routine* is a scheduled cloud trigger;
the session it fires is a *driver session*, which follows the protocol in
`PLAN_FRAGMENT.md` §3.1 and the prompt text in `C3_PROMPTS.md`.  C1/C2/C3
name the eras of this automation (portfolio, mining, 24/7 cadence).

**self-merge / trust-surface fence** — a cycle PR merges itself when all
checks are green *and* the `trust-surface` check confirms the diff touches
no ceremony path (`kernel/certs.py`, `TRUST.md`, the growth registry, the
CI config).  Anything red waits for the maintainer.

**ceremony (S4a→S4a′→S4b)** — the explicit human-signed procedure
(rehearsed in `PLAN_REFLECT.md`) by which a trust root may change: shadow
mode first, then evidence, then promotion with sign-off.

**shadow mode** — how a new checker earns trust: it runs beside the
existing channels and its agreement is ledgered, but its verdict alone
admits nothing.  (CVC5 sits beside Z3 this way; reflection verdicts ride
the same pattern.)

**emit-check tier / universal tier** — the two trust tiers for
generators.  Emit-check: every individual output is checked at emission.
Universal: the generator itself is proven correct for all valid specs
(one proof, amortized over unbounded outputs), so outputs need no
per-emission check.

**dual-checker rule** — no single checker's verdict admits or promotes
anything; two independent evidence channels must agree, and disagreement
is logged as a first-class event.

**reflection** — proof by reflection: write a decision procedure *in
Lean*, prove it sound once, and its outputs become theorems rather than
trusted claims.  Capability grows; the TCB does not.  The first slice
(`FgReflect`) shipped via the S4b ceremony.

**era / registration / lineage** — corpus growth re-baselines exactly one
file, `specs/mathsources/registration.json`; each append is a lineage
entry whose numbers are verified by teeth against the primary artifacts.
An *era* is the corpus state a given registration block describes.

**brief** — the output of `python3 tools/session_brief.py`: era, counts,
queue, lane state, and `PLAN_FRAGMENT.md` §1 verbatim, all derived from
committed artifacts.  Recompute beats recollection.

## Map of the documents

### Root: what the system is

| document | in one line |
|---|---|
| `README.md` | The system itself: five hard constraints, two-tier trust model, dual-checker rule. |
| `TRUST.md` | The trusted computing base, enumerated line by line, with why each line is there. |
| `ARCHITECTURE.md` | Consolidated how-the-repo-works walkthrough (draft banner pending review). |
| `LINGUISTICS.md` | What the system captures of *meaning*, phenomenon by phenomenon — proved vs. grounded vs. honestly out of fragment. |
| `METRICS.md` | Measured numbers from the milestone runs (costs, pass rates, steering-policy comparisons). |

### Root: the programs (design documents)

| document | in one line |
|---|---|
| `FORMALIZATION.md` | The math-reading fragment and the governed formalization flywheel — the spec behind the Lean effort. |
| `COMPRESSION.md` | The description-length program: macro tower, admission pricing, the DL floor. |
| `SPECULATION.md` | Zone 3, the speculative planner: deciding what the expensive machinery spends itself on. |
| `ROADMAP.md` | Build order toward the two-zone economy, with adversarially-swept hazards inline. |
| `KA_INTERFACES.md` | Frozen interfaces for the WP-KA work package, committed before its builders started. |

### Root: the active plans (work packets)

Each `PLAN_*.md` is a self-contained packet a fresh session can execute.
Status lines at the top of each are authoritative.

| document | in one line |
|---|---|
| `PLAN_FRAGMENT.md` | **The live one.**  The corpus↔fragment flywheel, the driver-session protocol (§3.1), the purchase queue, the guardrails. |
| `PLAN_REFLECT.md` | The reflection program (verified decision procedures; the S4 promotion ceremony). |
| `PLAN_HAMMER.md` | The batched proof-search lane: driving measured demand up `nothing → statement-cert → proof-cert`. |
| `PLAN_ZONE3_CYCLES.md` | Zone 3 re-sliced into serial, cycle-sized work packages for the driver Routine. |
| `PLAN_LEAN_IMPORT.md` | Turning an authorized token budget into Mathlib import/translation waves (spend is user-gated). |
| `PLAN_FORMALIZE_INTEGRATION.md` | Wiring the formalization extension into the active machinery (frozen interfaces, ⚠FI markers). |
| `PLAN_COMBINED_LOOP.md` | The unification of breadth/height/intake into one demand ledger (v2.1, swarm-hardened). |
| `C3_PROMPTS.md` | The canonical prompt texts for the recurring Routines — the Routines store only pointers here. |

### This directory

| document | in one line |
|---|---|
| `README.md` | This page. |
| `architecture.md` | The one-page visual map of the certified-autoformalization machinery (mermaid diagrams; renders on GitHub). |
| `lean-capable-environment.md` | Operator runbook: making a driver container Lean-capable, and how to verify the probe agrees.  Its path and key phrases are pinned by `tests/test_lean_env_probe.py`. |

### Where everything else lives

- `CLAUDE.md` — the stable session router: invariants and the command
  index only; deliberately free of mutable state.
- `results/` — committed evidence: cycle reports, ledgers, the frontier,
  the RT report, receipts.  Written by tools, read by teeth.
- `specs/mathsources/` — the corpus itself plus `registration.json`, the
  single re-baselined file.
- `tools/` — the cycle instruments (`session_brief.py`,
  `purchase_frontier.py`, `intake_corpus.py`, …).  Each `--help` is
  authoritative; `CLAUDE.md` holds the index.
