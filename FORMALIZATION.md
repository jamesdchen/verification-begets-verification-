# FORMALIZATION.md — the mathematical Reading fragment and the governed formalization flywheel

README.md says what the system is. TRUST.md says what is trusted.
LINGUISTICS.md says what is meant. SPECULATION.md says how the planner spends.
This document specifies the **formalization extension**: the same
analysis-vs-proof split, the same demand ledger, the same MDL governor —
re-targeted from "vague request → certified service" to "mathematical text →
certified formal statement (and, where cheap, a kernel-checked proof)".

It is written to be executed by a swarm of builder agents **without access to
the conversations that produced it**. Provenance: (1) drafted against the
unified tree (main @ `b89becd`); (2) hardened by a five-lens adversarial
sweep (findings FH1–FH38, folded below; every ⚠ verified by file:line
evidence, by executing an experiment against the live modules, or — for
Lean-ecosystem claims — flagged `unverified-here` where this container cannot
run the toolchain). One genuinely new thing is built (the mathematical
Reading fragment, F1); everything else is a re-instantiation of machinery the
tree already has: the checker-outsourcing rule (F0), the entailed-scenario
discipline (F2), the demand ledger and MDL gate (F3), the W5 growth checklist
(F4), and the teeth-per-increment demo idiom (F5).

The claim being bought, stated once: **autoformalization's classic silent
failure is the statement that compiles, proves, and means nothing** — the
omitted side condition, the fabricated hypothesis, the silently chosen
carrier. This repo already names that failure class: it is `demo_reading.py`
B5 (the omitted presupposition that certifies vacuously and only the examiner
catches) wearing a different domain. The force trichotomy maps onto it
exactly: **demand** = the theorem's asserted content, quote-grounded;
**presupposition** = the implicit hypotheses ("n positive", nonzero divisor,
nonempty domain) — first-class, quoted at their trigger, and targeted by
their own gates; **choice** = formalization freedom (which structure, what
generality) — ledgered, empty-quoted, and subordinated to the text. Proof
checking verifies proof-vs-statement; this plan builds the layer nobody
ships: **statement-vs-text**, with certificates.

## Trust posture (read this before writing any code)

House rules of ROADMAP.md bind unchanged (dual-checker, teeth-per-increment,
honest tiers, five-touchpoint contracts, byte-identity, LLM-authors-only-specs).
Zone-3 rules Z1–Z3 bind for any planner involvement. Four
formalization-specific rules:

- **L1 — the LLM never authors Lean.** It authors **MathReadings** (JSON, a
  pure spec gated like every other) and, on the proof path only, **tactic
  scripts**. A tactic script is *not* shipped code and is not an exception to
  house rule 5: it is a **checked certificate candidate** — its only
  execution is elaboration inside the OS sandbox, and the artifact trusted
  afterward is the kernel-checked proof term, never the script. Because Lean
  elaboration is metaprogramming-complete (a tactic block can execute
  arbitrary code at elaboration time), two containments are mandatory and
  review-blocking: (i) elaboration runs **only** under `sandbox/__init__.py`
  (network off, tmpfs, rlimits — the same rule as every emitted artifact,
  TRUST 1.2); (ii) every Lean subject passes the **lexical escape gate**
  (F0.4) that rejects `native_decide`, `unsafe`, `axiom`, `@[extern]`,
  `macro`, `elab`, `initialize`, `set_option` outside a whitelist, and any
  `import` outside the pinned set, before elaboration is attempted.
- **L2 — statements are specs.** A compiled Lean statement is
  content-addressed exactly like a spec: cache identity =
  (statement bytes, import set, toolchain hash, Mathlib commit, contract) —
  a toolchain or Mathlib bump is a clean cache miss, never a stale
  false-green (the `expansion_context` / `oracle_ref` discipline,
  TRUST 1.2l).
- **L3 — fidelity gates are refusals, tripwires are events.** Non-vacuity
  and entailed-instance failures **refuse** (like B2's dual-solver unsat);
  the triviality tripwire and the examiner **log first-class events and
  claims** but never issue or block a certificate by themselves — they are
  evidence, tier-labeled, exactly as TRUST 3.4 labels intent scenarios.
- **L4 — the kernel-independence honesty note.** Lean's kernel (channel 1)
  and the external re-checkers of exported environments (channel 2:
  `lean4checker`, plus `lean4lean` where pinned) are independent
  *implementations pass over the same exported terms*, but they share the
  kernel's design and, for `lean4checker`, some of its code lineage. That is
  **weaker independence than Z3-vs-CVC5** and every statement-cert /
  proof-cert certificate says so machine-readably
  (`claims: independence="kernel-family"`), the same honesty move as
  TRUST 3.4's "prompt-level, not model-level".

What is deliberately **out of scope**, stated here and tier-labeled in the
TRUST amendment (F5's final commit), because no checker exists:

1. **Mathematical importance.** The system prices *compression over
   witnessed demand* (the MDL gate); it does not and cannot judge
   significance. A certificate never claims a statement matters.
2. **Autonomous fragment growth.** New logical-form kinds are
   kernel-adjacent surface and land **only** through the human-gated F4
   checklist. The system automates the demand accounting and the validation
   harness for growth; a person stays the admitting authority, permanently
   and by design.
3. **Mathlib contribution.** Nothing here PRs to Mathlib; the library is a
   pinned, read-only checker input (the `flloat` discipline, TRUST 1.2h).
4. **Proof-search research.** Proofs arrive as untrusted tactic scripts or
   as `decide` on decidable instances; beating provers is not the thesis.
   The thesis is statement-fidelity plus governed vocabulary growth.

## Phases

Logical order: F0 → F1 → F2 → {F3 ∥ F4} → F5. Scheduling is by the work
packages below.

### F0 — the proof-assistant kernel backend (mechanical, fits the house rules)

"Outsource every checker that exists" already permits this: Lean 4 + a
pinned Mathlib join Dafny/Z3/CVC5/Hypothesis as vendored, unmodified checker
binaries (TRUST 1.3). No kernel philosophy changes — two new contracts, each
landing per house rule 6 as ONE commit touching FIVE points
(`_subject_and_cdesc`, `_dispatch`, `channel_specs`, `run_channel`,
a check method in `kernel/backends.py`) plus a TRUST entry. Both are
**non-pooled, direct-path contracts** (the `monitor-cert` /
`tier-classification` pattern) so `POOL_SUPPORTED` and the channel-parity
tripwire are untouched.

- **F0.1 Toolchain pins** (`setup.sh`, the flloat discipline): `elan`, ONE
  pinned Lean 4 toolchain, ONE pinned Mathlib commit, `lake exe cache get`
  for the prebuilt oleans, and the external checker (`lean4checker` at the
  matching tag). The pins are single-sourced in `common.py`
  (env-overridable, briefing item 2 pattern) and their joint sha —
  `lean_toolchain_hash()` — enters every cache key (L2). The Mathlib cache
  is fetched **at setup time only**; certification runs with network off
  (the sandbox guarantees it). Setup gains a `--with-lean` flag: the
  multi-GB fetch must not tax existing CI (`run_regression.py --fast` stays
  < 90 s and LLM-free *and Lean-free*).
- **F0.2 `statement-cert`** — subject: a compiled Lean statement (from F1)
  with `:= sorry` as its placeholder proof. Channel 1: sandboxed
  elaboration against the pinned Mathlib succeeds AND the axiom audit
  (`#print axioms` via a fixed driver, parsed — never trusted output of the
  subject itself) shows exactly `sorryAx` plus the standard three
  (`propext`, `Classical.choice`, `Quot.sound`) or fewer. Channel 2:
  `lean4checker` replays the exported environment. Claims:
  `{statement_hash, mathlib_commit, toolchain, axioms,
  independence="kernel-family", trivially_closed}` (the last from F2.3).
  Non-claims: fidelity to any text (that is F2's job), provability, novelty.
- **F0.3 `proof-cert`** — subject: statement + proof artifact (tactic
  script or term). Channel 1: sandboxed `lake` build accepts, **no
  `sorryAx` in the audit**, axioms ⊆ the standard three. Channel 2:
  `lean4checker` on the exported environment. Tier: this is the strongest
  tier in the repo's vocabulary for a per-artifact claim — but it is named
  honestly as `kernel-checked` (not `universal`; nothing is proved about
  any generator, only about THIS statement) with the L4 independence note.
- **F0.4 The lexical escape gate** (`buildloop/validate_lean.py`): the
  pure-spec gate for Lean subjects (L1). Token-level, whitelist-first,
  applied to every LLM-authored proof script AND (defense in depth) to the
  deterministic compiler's own output before any elaboration. Its teeth are
  a planted `native_decide` proof and a planted `macro_rules` escape, both
  refused pre-sandbox.
- **F0.5 The runner** (`kernel/backends.py: LeanBackend`): builds a
  one-file scratch package importing the pinned Mathlib snapshot, runs
  elaboration/build **inside the sandbox**, parses machine-readable results
  from fixed driver files (never from subject-controlled stdout formats
  alone), holds no state. Content-addressed caching via the existing
  `kernel_cache` — a statement is checked once per (pins, contract).
- **Done when:** both contracts land five-touchpoint-clean with TRUST
  entries; a hand-written true statement certifies at both contracts; a
  planted `sorry`-smuggling proof and a planted axiom-introducing proof are
  refused; escape-gate teeth green; `run_regression.py --fast` unchanged
  and Lean-free (Lean demos are `REQUIRES_LEAN = True`, a new marker
  parallel to `REQUIRES_LLM`, honored by `run_regression.py` collection).

### F1 — the mathematical Reading fragment (the one genuinely new build)

The current fragment (`generators/reading.py`) is deontic-temporal over
integer aggregates; mathematics needs typed objects, quantifiers, operators,
and an ambient structure. The architecture transfers whole: quote-grounded
statements, force trichotomy, deterministic compositional compiler,
per-element provenance. The LLM authors MathReadings, never Lean (L1).

- **F1.1 The fragment** (`generators/math_reading.py`): `MATH_LF_KINDS` +
  `_MLF_FIELDS` + the import-time equality assert — the single-source
  pattern copied from `reading.py:71/134/149` so prompt grammar and
  validator can never drift. First fragment, deliberately small:

  | kind | fields | force rule | role |
  |---|---|---|---|
  | `object` | `name, type` (type from the pinned carrier whitelist: `Nat`, `Int`) | any force | typed discourse referent |
  | `operator` | `word, mathlib` (from the pinned operator table) | presupposition (quotes the word it construes) or choice | lexicon: "divides" ↦ `Dvd.dvd`, "even" ↦ `Even`, "gcd" ↦ `Nat.gcd`, … |
  | `hypothesis` | `pred` | **demand or presupposition; never choice** | side conditions — the killer feature: "n > 0", nonzero divisors, the things autoformalization silently drops |
  | `conclusion` | `pred` | **demand only** | the asserted content, quote-grounded verbatim |
  | `quantifier` | `binder ∈ {forall, exists}, objects` | demand or presupposition | binding of declared referents |
  | `ambient` | `carrier` | **choice only** | formalization freedom made legible: which structure the statement is stated over |

  `pred` is a small first-order term grammar over declared objects, the
  whitelisted operators, integer literals, `+ * ^ % ∣ = ≠ ≤ <`, and
  conjunction/disjunction/implication — every construct with BOTH a Lean
  rendering and an SMT mirror (F2.1) or a decidable bounded evaluation.
  The gate `parse_math_reading` mirrors `parse_reading`: demand quotes
  verbatim in the source text (string containment, not judgment),
  presupposition quotes its trigger, **choice quotes nothing**, fields
  exact-match `_MLF_FIELDS`, statements may reference only declared
  referents (anaphora resolved by construction).
- **F1.2 The compiler** (`generators/math_compile.py`): deterministic,
  LLM-free MathReading → Lean statement text, trusted by fiat exactly as
  `reading_compile.py` is (TRUST 1.2e — same two damage bounds: its output
  is fully checked by F0's contracts, and F2 replays meaning-level
  instances against it). Canonical emission (objects sorted, hypotheses in
  id order, fixed pretty-printing) so statement bytes are content-stable.
  Output: `{lean_text, statement_hash, provenance}` where provenance maps
  every Lean binder/hypothesis/conclusion subterm to the statement ids that
  produced it — the chain *quoted span → force → LF → Lean term*, written
  beside every artifact like `provenance.json` today.
- **F1.3 Prompt + validator single-sourcing**: the Reading prompt's grammar
  block is rendered from `MATH_LF_KINDS` exactly as
  `buildloop/service_loop.py` renders it from `LF_KINDS` (the P0.5.8
  discipline; prompt tests included).
- **Done when:** ten hand-written MathReadings (no LLM) parse, compile, and
  their Lean texts elaborate under F0.2; a fabricated-quote reading, a
  choice-with-quote reading, and an undeclared-referent reading are each
  refused at the gate with stage `math-reading-gate`;
  byte-stability test: same reading → identical `statement_hash` across
  runs.

### F2 — statement-fidelity gates (the analog of entailed scenarios)

Proof checking verifies proof-vs-statement. Nothing in any pipeline verifies
statement-vs-text. The repo's existing answer generalizes gate by gate; the
pipeline module is `run/formalize.py: certify_statement(source_text,
math_reading_json)` — the staged-refusal shape of
`run/semantic.py: certify_reading`, stage labels pinned as an interface
freeze (F-F): `math-reading-gate → nonvacuity → compile → statement-cert →
instances → examiner → (proof)`.

- **F2.1 Non-vacuity** (the B2 analog, refusal): a statement whose
  hypothesis set is unsatisfiable is refused **before anyone proves it** —
  it would certify vacuously. Mechanism: `generators/math_smt.py` renders
  the hypothesis set to SMT (the `demands_smt` pattern) and **Z3 ∧ CVC5
  must agree on `sat`**, with the witness model instantiated back into the
  hypotheses and confirmed by Lean `decide` in the sandbox — three
  independent engines on one satisfiability question. Predicates outside
  the SMT mirror (none in the F1 fragment; F4 extensions may add them) run
  the decidable-enumeration channel only and the certificate says so
  (honest tier, house rule 4). Dual-solver `unsat` = stage-`nonvacuity`
  refusal, transcript attached.
- **F2.2 Entailed instances** (the entailed-scenarios analog, refusal):
  each demand generates its own concrete tests, mechanically. From the
  quantifier structure and the SMT model enumeration: (i) the k smallest
  hypothesis-satisfying instances (k pinned, default 5) — the instantiated
  statement is evaluated by `decide` in the sandbox and **must hold**; a
  false instance refutes the formalization before proof search (this
  catches wrong operator binding and wrong carrier: "for all n > 2" entails
  checking n = 3, and rejecting a construal that makes n = 2 a claim);
  (ii) boundary probes just OUTSIDE each hypothesis (n = 2 for "n > 2") —
  evaluated and **recorded on the certificate** as
  `boundary_behavior` claims, never auto-refused (a statement may be true
  beyond its stated hypotheses; that is information, not error). Where the
  statement's matrix is not decidable at an instance, the instance is
  discharged by the dual-SMT mirror instead; where neither applies it is
  skipped and **named on the certificate** (bounded honesty, the
  `bounded-K` discipline). Property-based search with Plausible
  (né `slim_check`) runs as an additional refutation channel when pinned —
  a counterexample refuses; absence of one claims nothing.
- **F2.3 Triviality tripwire** (event, never a verdict — L3): `exact?` and
  `simp` under a small fixed budget against the full statement. Instant
  closure ⇒ first-class `triviality` event (`registry.log_event`) and
  `trivially_closed: true` on the statement-cert claims — **logged, not
  celebrated**: it is evidence of misformalization (the statement collapsed
  to something Mathlib already knows) or of an unambitious corpus entry;
  the benchmark (F5) reports the rate.
- **F2.4 The examiner = auto-informalization** (evidence, tier-labeled —
  the founding move: two derivations of one text). Two sub-channels:
  - **(a) instance expectations (mechanical replay, the B5 analog):** an
    independent, semantics-blind LLM pass reads ONLY the source text (never
    the Reading, never the Lean) and authors expected concrete instances —
    "at n = 3 this should hold", "the divisor 0 case should be outside the
    claim" — pure JSON, gated by a `validate_expectations` that requires ≥1
    positive and ≥1 boundary expectation (the non-vacuous-expectations rule
    of `validate_scenarios`). They replay against the compiled statement by
    the F2.2 machinery. Divergence = first-class `formalization-divergence`
    event driving re-authoring; convergence = the `intent-admission`-tier
    evidence, with TRUST 3.4's caveat verbatim (prompt-level independence,
    correlated misreadings survive).
  - **(b) back-translation:** a second blind pass renders the compiled Lean
    statement back to English; the transcript (source, back-translation)
    is a committed artifact on the run record for human audit. No mechanical
    agreement claim is made — text-vs-text similarity is not a checker, and
    pretending otherwise would violate house rule 4. (expMath lists
    auto-informalization as a deliverable; here it is a trust mechanism
    with an honest tier.)
- **Done when:** the five-teeth demo (`demo_formalize.py`, the
  `demo_reading.py` analog — LLM-free, hand-written mutants) is green, each
  tooth caught at its OWN stage:
  - T1 fabricated conclusion (quote not in source) → `math-reading-gate`;
  - T2 contradictory hypotheses (n > 5 ∧ n < 3) → `nonvacuity`
    (dual-solver unsat);
  - T3 wrong operator binding (`∣` construed as `/`) → `instances`
    (smallest witness refutes by `decide`);
  - T4 silently narrowed carrier (a subtraction statement stated over `Nat`
    where the text says integers — ℕ-truncation flips an instance) →
    `instances`;
  - T5 **omitted presupposition, the honest one**: the analyst drops
    "nonzero divisor"; Lean's totalized division (`x / 0 = 0`) makes the
    weakened statement still elaborate and still prove — it certifies
    fully and means nothing. Only the examiner's expectation about what the
    sentence MEANS catches it. The demo prints, exactly as B5 does, that
    fidelity to the written formalization and coverage of the unwritten
    meaning are different properties — this tooth is the plan's reason to
    exist.

### F3 — the governor, re-targeted (near-zero new code)

Demand-ledger rows become source texts; coverage = statement certified;
definition admission goes through the MDL gate. This is the piece whose
absence the skill-library literature documents (bloat as the death mode —
METRICS.md already names it); "useful abstractions" gets the operational
meaning nobody ships: **priced compression over real, witnessed demand,
with per-use certification.**

- **F3.1 The demand kind** `math-source`: committed files under
  `specs/mathsources/` (one English statement each, the exogenous ground
  truth), ingested by `cgb.py ledger sync` with the byte-match discipline
  (`demand_id = sha256("math-source:" + relpath)`, `origin = "exogenous"` —
  the `_ledger_sync` pattern at `cgb.py:380`). Pricing branch in
  `buildloop/dl.py:_demand_cost`: served =
  `READING_CHAIN_COST + dl_reading(math_reading, snap.macro_table)`
  (the `nl-request` shape at `dl.py:247-251`, reused not duplicated);
  unserved = `UNCOVERED_PENALTY`. ⚠ `dl.py` is a frozen interface per the
  SPECULATION briefing (item 6) — this is an owned-lines exception with an
  integrator escalation note, exactly like S1.7's one-line seam.
  **Covered** = statement-cert + F2 gates green (fidelity is the product);
  `proof-cert` upgrades a row's `status` metadata but coverage never
  requires it — proving is priced work, not a coverage cliff.
- **F3.2 Persistence**: MathReadings live in the existing `readings` table
  (`library/__init__.py:88-93`) keyed by `demand_id`, `cert_id` = the
  composed statement-cert id — the H48 lesson applied (never duplicate live
  machinery under a second name). The seed step is `ledger seed-readings`
  extended to the new kind, certify-at-seed (the ⚠H46b honest default).
- **F3.3 Definitions are macros** — v1 scope, stated honestly: a minted
  "definition" is a **Reading-layer abbreviation** (the W5.2 macro
  machinery, verbatim): mined by `buildloop/recurrence.py`'s LGG
  anti-unification over MathReading statement windows, admitted **iff** it
  strictly reduces the corpus DL AND has **≥ 2 witnesses among
  exogenous-origin readings** (`mdl_macros.macro_admission_decision`,
  `witness_filter = origin == "exogenous"` — the S5/Z-E threading,
  reused). Every actual use is certified per-emission by
  `translation-cert(anchor="reference-lowering")` with the trusted lowering
  = the F1.2 compiler: the macro-expanded reading must compile to the
  **byte-identical Lean statement** of its retained inlined baseline, plus
  entailed-instance replay — one `LOWERINGS` entry in
  `generators/derivers.py` and one TRUST line, **no kernel edit**
  (TRUST 1.2l). What v1 does NOT do: mint Lean-side `def`s that shorten
  *proof terms* — that changes proof identity and belongs to a later phase;
  dreams may propose it, nothing admits it.
- **F3.4 Dreams under witness discipline**: LLM-generated paraphrases and
  domain-variant statements enter as `origin = "system"` rows
  (`specs/mathsources/dream/`, seeded system-origin; a dream seeded as real
  with no committed byte-match is a hard error — S5.1 verbatim). Dreams
  propose vocabulary; **only exogenous witnesses admit it** — in the gate
  and in every DL objective (⚠H6 discipline). Retirement: `gc_macros`
  applies unchanged; searched admission (S1.3) applies unchanged when Zone 3
  lands — F3 requires only the greedy gate.
- **Done when:** `demo_formalize_governor.py` (LLM-free, planted corpora)
  is green: (i) a recurring idiom with 3 exogenous witnesses is mined,
  admitted, and its uses certify per-emission against retained baselines;
  (ii) the same idiom appearing only in dreams is mined and **refused**;
  (iii) a planted lossy abbreviation (drops a hypothesis) gets **no
  certificate** — compile-hash divergence, the `tests/test_rung.py`
  pattern; (iv) ledger status shows `math-source` rows covered/uncovered
  with `ledger_dl` moving the right way on admission.

### F4 — fragment-miss machinery (frontier growth as a first-class loop)

When a source sentence does not transcribe into the F1 fragment, that is
not a failure to hide — it is demand data.

- **F4.1** `fragment-miss` events: `certify_statement` stage
  `math-reading-gate` failures and explicit analyst declarations log
  `{source_id, span, missing_kind_guess}` via `registry.log_event`; a
  synthesis attempt that exhausts rounds on a gate-refused kind logs one
  automatically (the `exhausted`-is-honest rule, LINGUISTICS §7).
- **F4.2** The ranking report (`cgb.py fragment report`): group misses by
  `missing_kind_guess`, and for each candidate LF-kind extension report
  **demand unlocked per kernel surface added** — pending `math-source`
  rows whose sentences would transcribe (counted by span-tag replay, an
  accounting estimate, labeled as such) against the surface cost (new
  compile rule + SMT/decidable mirror + prompt lines). This is the S2
  lookahead one rung up, v1 as a *report*: the system prices, a person
  decides.
- **F4.3** Admission is human-gated through the **W5 checklist, math
  instance** (ROADMAP briefing item 11, verbatim analog): `MATH_LF_KINDS`
  entry (validator + prompt) · compile rule + provenance · entailed-instance
  derivation · `math_smt`/decidable coverage (or an honest named gap) ·
  ≥ 1 tooth. Dual-checked semantics for the new kind or it does not land.
  No autonomous growth (out-of-scope item 2) — permanently.
- **Done when:** a corpus sentence chosen to be outside the fragment (F5
  plants three) produces a logged miss and appears in the report with a
  nonzero unlock count; the report is deterministic over a fixed events
  table; the checklist is committed as a PR template under
  `specs/mathsources/FRAGMENT_GROWTH.md`.

### F5 — the micro-domain and the governed-vs-ungoverned tooth

Do not launch at research math. The micro-domain is chosen so Mathlib's span
already covers every definition and instances are decidable — frontier-2
pressure near zero, every layer certifying end-to-end — because the fundable
claim is not "we formalized hard math"; it is: **on the same corpus and
compute, the governed flywheel beats the ungoverned one on
cost-per-certified-statement and library compression — with certificates,
not vibes.**

- **F5.1 The corpus** (`specs/mathsources/`, 40 hand-committed English
  statements, elementary number theory + integer inequalities —
  divisibility, parity, gcd/lcm, modular arithmetic, order/absolute-value
  bounds). Composition is engineered pressure, one axis per gate:
  - ≥ 8 entries with **implicit side conditions** (nonzero divisors,
    positivity, nonemptiness) — presupposition pressure (F2's reason);
  - ≥ 5 with **ambient ambiguity** (ℕ-vs-ℤ, where truncated subtraction or
    negativity changes truth) — choice pressure;
  - ≥ 6 sharing **recurring idioms** ("a divides b", "coprime", "even")
    in ≥ 3 distinct statements each — definition-mining pressure;
  - exactly 3 that **do not transcribe** (chosen from: infinitude
    quantification, real-valued content, existence-of-minimum arguments) —
    fragment-miss pressure, F4's teeth;
  - the remainder straightforward, so coverage numbers mean something.
  Every entry is exogenous ground truth: committed text, byte-matched at
  sync, no LLM in its provenance.
- **F5.2 The benchmark** (`bench_formalize.py`, LLM-requiring, skippable
  with honest note — the ⚠H43 discipline; the teeth live in the LLM-free
  demos): two arms on identical corpus, model, prompts, and spend cap —
  - **governed**: MDL gate + two-exogenous-witness discipline + per-use
    translation-cert + retirement, as landed;
  - **ungoverned**: every proposed abbreviation admitted, dreams count as
    witnesses, no retirement — the literature's default, implemented as
    flags on the same code path (never a fork of the miner).
  Metrics per arm, in the METRICS.md unit (LLM k-tokens + verifier
  seconds): `cost_per_certified_statement`, corpus-DL trajectory,
  live-vs-retired vocabulary counts, per-stage refusal counts, triviality
  rate, divergence counts. `results/formalize_governed.csv` committed.
- **F5.3 The acceptance tooth** (LLM-free, planted —
  `demo_formalize_governor.py` part (v)): a paraphrase-flood plant (one
  idiom, eight system-origin restatements, two exogenous) where the
  ungoverned arm mints junk vocabulary that RAISES corpus DL and the
  governed arm admits exactly the two-witness abbreviation — asserted
  relationally (governed DL < ungoverned DL at equal coverage), no absolute
  constants (the ⚠H52 lesson).
- **F5.4 Docs, merge-owned final commit**: README section; TRUST
  amendments (Lean checker-input entries, `kernel-checked` tier, L4
  independence note, out-of-scope items tier-labeled); LINGUISTICS gains a
  §8-style coverage table for the math fragment. One commit, after every
  other phase merge (briefing item 12).
- **Done when:** ≥ 30/40 corpus entries reach certified statements on a
  fresh DB without human edits to the readings; the three planted
  non-transcribables show as fragment-misses, not failures; F5.3
  relational tooth green; bench captured or honestly skipped; docs landed.

## Parallel execution plan

One WP = one agent = one worktree = one exclusive file set; freezes below
let consumers code against signatures. Integrator owns nothing, serializes
`cgb.py`/`dl.py` owned-line merges, runs `run_regression.py --fast` at every
merge.

### Wave 0 — six packages, no cross-dependencies

| WP | scope | exclusive files |
|---|---|---|
| **A** toolchain | F0.1 pins + `LeanBackend` runner + escape gate F0.4 | `setup.sh` (lean lines), `common.py` (pin lines), `kernel/backends.py` (LeanBackend only), `buildloop/validate_lean.py`, `tests/test_lean_backend.py` |
| **B** fragment | F1.1 + F1.3 | `generators/math_reading.py`, `tests/test_math_reading.py` |
| **C** corpus | F5.1: 40 source files + `FRAGMENT_GROWTH.md` | `specs/mathsources/**` |
| **D** smt-mirror | F2.1's renderer | `generators/math_smt.py`, `tests/test_math_smt.py` |
| **E** examiner-gate | F2.4a's `validate_expectations` | `buildloop/validate_expectations.py`, `tests/test_expectations.py` |
| **F** compiler | F1.2 against the B freeze | `generators/math_compile.py`, `tests/test_math_compile.py` |

### Wave 1 — three packages

| WP | scope | needs |
|---|---|---|
| **G** contracts | F0.2/F0.3 five-touchpoint commits + TRUST entries | A, F |
| **H** pipeline | `run/formalize.py` staged pipeline + F2.1–F2.3 wiring + `demo_formalize.py` five teeth | B, D, F, G |
| **I** ledger | F3.1/F3.2: sync + seed + dl branch | B, C, F |

### Wave 2 — serialized tail

| WP | scope | needs |
|---|---|---|
| **J** governor | F3.3/F3.4: miner over MathReadings, witness threading, `LOWERINGS` entry, `demo_formalize_governor.py` incl. F5.3 | H, I |
| **K** fragment-miss | F4: events + report | H, I |
| **L** bench + docs | F5.2 bench (skippable) then F5.4 one docs commit | all |

Critical path: A → G → H → J → L. Peak width 6.

Swarm rules: exclusive file (or line-range) lists are review-blocking;
README/TRUST/LINGUISTICS only in WP-L; a builder that finds this spec wrong
against the tree **stops and escalates** — never improvises across a freeze.

## Interface freezes

- **F-A MathReading envelope**: `{source: str, reading: {theorem:
  str, statements: [...]}}`; statement = `{id, force, quote, lf}` exactly as
  the Reading's (ROADMAP freeze #3 shape); LF kinds per the F1.1 table.
- **F-B compiled artifact**: `{lean_text: str, statement_hash: sha256,
  provenance: {lean_element: [statement_ids]}}`; canonical emission;
  `statement_hash` is over `lean_text` bytes only (pins live in the cache
  key, not the hash).
- **F-C contract identities**: `statement-cert` / `proof-cert` names,
  claims tuples as in F0.2/F0.3, tier strings `emit-check` /
  `kernel-checked`, cache identity per L2. Non-pooled, direct-path.
- **F-D corpus file**: plain UTF-8 text, one statement (+ optional one
  context sentence), filename `NN_slug.txt`; dreams under
  `mathsources/dream/`.
- **F-E vocabulary store**: the registry `macros` table, accessor
  `registry.macro_table()`, names `m_<sha12>` — Z-C verbatim; no new store.
- **F-F pipeline stages**: `math-reading-gate → nonvacuity → compile →
  statement-cert → instances → examiner → proof`; result dataclass mirrors
  `SemanticResult` (extend, never rename — ROADMAP freeze #8).

## File-ownership matrix (W = writes, N = new, r = reads)

| file | F0 | F1 | F2 | F3 | F4 | F5 |
|---|---|---|---|---|---|---|
| `setup.sh` / `common.py` (pin lines) | W | | | | | |
| `kernel/backends.py` (`LeanBackend` only) | W | | | | | |
| `kernel/__init__.py` (two five-touchpoint commits) | W | | | | | |
| `buildloop/validate_lean.py` | **N** | | | | | |
| `generators/math_reading.py` | | **N** | r | r | W (F4 kinds, human-gated) | r |
| `generators/math_compile.py` | | **N** | r | r | W (F4 rules, human-gated) | r |
| `generators/math_smt.py` | | | **N** | | W (F4 mirrors) | r |
| `run/formalize.py` | | | **N** | r | W (miss logging) | r |
| `buildloop/validate_expectations.py` | | | **N** | | | r |
| `buildloop/dl.py` (`_demand_cost` branch only, escalated) | | | | W | | |
| `cgb.py` (sync/seed lines; `fragment report` lines) | | | | W | W | |
| `buildloop/recurrence.py` (math windows; serialized after Zone-3 S1) | | | | W | | |
| `generators/derivers.py` (one `LOWERINGS` entry) | | | | W | | |
| `specs/mathsources/**` | | | | r | r | **N** |
| demos/tests/results (each phase's own) | N | N | N | N | N | N |
| README / TRUST / LINGUISTICS (merge-owned) | | | | | | W |
| `generators/reading.py`, `generators/reading_compile.py`, `run/semantic.py`, `library/__init__.py`, `sandbox/*`, `run_regression.py` | r | r | r | r | r | r |

## Builder briefing addendum

1. ROADMAP briefing items 1–3 and 5–12 bind verbatim; item 4 (branch) is
   overridden: push ONLY to the branch your task designates.
2. L1–L4 are review-blocking. No Lean text is LLM-authored, ever; the
   compiler emits it, the escape gate re-checks it, the sandbox runs it.
3. `run_regression.py --fast` stays Lean-free: mark Lean demos
   `REQUIRES_LEAN = True` and gate collection the way `REQUIRES_LLM` gates
   it today.
4. Treat `buildloop/dl.py`, `planner/__init__.py`, `library/__init__.py` as
   frozen interfaces (SPECULATION briefing item 6); F3.1's `_demand_cost`
   branch is the single escalated exception, owned for those lines.
5. Zone-3 coordination: `buildloop/recurrence.py` has a Zone-3 writer
   (S1.2/S5); the F3.3 math-window change merges AFTER Zone-3 S1 lands or
   through the integrator if concurrent.
6. Determinism everywhere: no clocks, no `random`, canonical JSON,
   canonical Lean emission. Toolchain pins single-sourced from `common.py`.

## Hazards ledger (pre-sweep seed)

The five-lens sweep appends FH findings here with evidence; these are the
hazards known at drafting time, named per house style:

| # | hazard | mitigation |
|---|---|---|
| FH1 | Lean elaboration is metaprogramming-complete — a "proof" can execute code at elaboration time | L1: sandbox-only elaboration + the F0.4 lexical escape gate; both have teeth |
| FH2 | `native_decide` / added axioms smuggle trust past the kernel | axiom audit on every certificate; `native_decide` lexically refused; audit tooth in F0 |
| FH3 | totalized operators (`x / 0 = 0`, ℕ-truncated `-`) make weakened statements provable — the silent-vacuity class | F2.2 boundary probes recorded as claims; T4/T5 teeth; corpus engineered with these plants |
| FH4 | kernel-family channels are weaker independence than Z3-vs-CVC5 | L4: named on every certificate; never claimed otherwise |
| FH5 | Mathlib pin drift invalidates everything silently | L2: pins in every cache identity; bump = clean miss; pins single-sourced |
| FH6 | statement certifies ⇏ statement faithful (the whole point) | F2 gates; coverage requires them; T5 demonstrates the residual gap honestly |
| FH7 | trivial statements game cost-per-certified-statement | F2.3 triviality rate is a first-class benchmark column |
| FH8 | ungoverned arm strawmanned to make the tooth pass | same code path, flags only; relational asserts; arm configs committed |
| FH9 | multi-GB Mathlib cache in CI | `--with-lean` setup flag; `REQUIRES_LEAN` collection gate |
| FH10 | examiner text-comparison pretending to be a checker | F2.4b makes no mechanical claim; F2.4a converges on replayable instances only |

## Acceptance, restated

1. A mathematical sentence becomes a certified formal statement whose every
   Lean element traces to a quoted span, a force, and a logical form — with
   fabrication, contradiction, wrong construal, and carrier-narrowing each
   refused at its OWN stage, and the omitted-presupposition residue caught
   by the examiner and demonstrated honestly (five teeth, F2).
2. Both new contracts satisfy the dual-checker rule with an honest,
   machine-readable independence tier; no certificate hides what was not
   checked (F0, L4).
3. Vocabulary grows only under priced compression over exogenous-witnessed
   demand, every use certified per-emission against a retained baseline;
   dreams propose and never witness (F3).
4. Fragment growth is demand-accounted, validation-harnessed, and
   permanently human-gated (F4).
5. On the fixed micro-domain corpus at equal spend, the governed flywheel
   beats the ungoverned one on cost-per-certified-statement and corpus DL —
   relationally asserted, certificate-backed, CSV-committed (F5).
6. Zero changes to the existing kernel contracts, compiler, references, or
   registry schema; the existing regression stays green, fast, and
   Lean-free.
