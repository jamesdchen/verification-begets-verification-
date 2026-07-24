# FORMALIZATION.md — the mathematical Reading fragment and the governed formalization flywheel

README.md says what the system is. TRUST.md says what is trusted.
LINGUISTICS.md says what is meant. SPECULATION.md says how the planner spends.
This document specifies the **formalization extension**: the same
analysis-vs-proof split, the same demand ledger, the same MDL governor —
re-targeted from "vague request → certified service" to "mathematical text →
certified formal statement (and, where cheap, a kernel-checked proof)".

It is written to be executed by a swarm of builder agents **without access to
the conversations that produced it**. Provenance: (1) drafted against
main @ `b89becd`; (2) **hardened by a five-lens adversarial sweep** —
anchoring (A1–A10), trust-boundary (T1–T10), Lean-domain (D1–D17),
economics (E1–E7), swarm-executability (X1–X18) — every repo claim verified
by file:line evidence or by executing an experiment against the live modules;
Lean-ecosystem claims tagged `[domain-knowledge]` where this container cannot
run the toolchain. The sweep found **eleven blocking defects** in the draft
(two verdict-forgery holes, a silently-unpersistable demand kind, a
service-welded certificate channel, an unfrozen load-bearing AST seam, a
grammar/tooth contradiction, an unearned headline claim, and four
depends-on-unlanded-work errors); all are folded below and listed in the
hazards ledger. (3) **Re-anchored to the unified tree** (main @ `89e9852`,
which merged the whole of Zone 3): the four seams the sweep flagged as
depends-on-unlanded-Zone-3 — `ledger seed-readings`, the Z-E
`witness_filter` threading, the S1.2 uniform-(force, quote) window
widening, and the S1.7 ledger macro-cost term — **all landed and were
verified by grep/execution**, so the land-or-build contingencies below
resolve to "extend the landed code"; line anchors are updated to the
unified tree; ⚠E1 was re-verified and **still stands** (no macro table
reaches any prompt on this tree — F1.3's mechanism is still required work).
One genuinely new thing is built (the mathematical Reading fragment, F1);
the rest re-instantiates machinery the tree already has — the
checker-outsourcing rule (F0), the entailed-scenario discipline (F2), the
demand ledger and MDL gate (F3), the W5 growth checklist (F4), and the
teeth-per-increment demo idiom (F5).

The claim being bought, stated once: **autoformalization's classic silent
failure is the statement that compiles, proves, and means nothing** — the
omitted side condition, the fabricated hypothesis, the silently chosen
carrier. This repo already names that failure class: it is `demos/demo_reading.py`
B5 (the omitted presupposition that certifies vacuously and only the examiner
catches) wearing a different domain. The force trichotomy maps onto it
exactly: **demand** = the theorem's asserted content, quote-grounded;
**presupposition** = the implicit hypotheses ("n positive", nonzero divisor,
nonempty domain) — first-class, quoted at their trigger, and targeted by
their own gates; **choice** = formalization freedom (which structure, what
generality) — ledgered, empty-quoted, and subordinated to the text. Proof
checking verifies proof-vs-statement; this plan builds the layer nobody
ships: **statement-vs-text**, with certificates where checkers exist and
honestly-labeled evidence where they don't.

## Trust posture (read this before writing any code)

House rules of ROADMAP.md bind unchanged (dual-checker, teeth-per-increment,
honest tiers, five-touchpoint contracts, byte-identity, LLM-authors-only-specs).
Zone-3 rules Z1–Z3 bind for any planner involvement. Five
formalization-specific rules:

- **L1 — the LLM never authors Lean.** It authors **MathReadings** (JSON, a
  pure spec gated like every other) and, on the proof path only, **tactic
  scripts**. A tactic script is *not* shipped code and is not an exception to
  house rule 5: it is a **checked certificate candidate** — its only
  execution is elaboration inside the OS sandbox, and the artifact trusted
  afterward is the kernel-checked proof term, never the script. Because Lean
  elaboration is metaprogramming-complete (a tactic block can execute
  arbitrary code at elaboration time), three containments are mandatory and
  review-blocking: (i) elaboration runs **only** under `sandbox/__init__.py`
  (network off — `unshare --net`, verified at `sandbox/__init__.py:95` —
  tmpfs, rlimits: the same rule as every emitted artifact, TRUST 1.2);
  (ii) the **two-run adjudication rule L5** below — the sandbox contains
  *escape*, not *lying to the parser*; (iii) the **lexical escape gate**
  (F0.4), which is **defense-in-depth and cheap-fast-reject, never the trust
  boundary** (⚠T7 — a lexical gate over a metaprogramming-complete surface
  is bypassable by construction; the trust boundary is (i) + (ii)).
- **L2 — statements are specs, and the checking apparatus is part of the
  identity.** Cache identity for the new contracts = (statement bytes,
  **proof-artifact bytes** where applicable, import set, toolchain hash,
  Mathlib commit, **escape-gate source hash**, **runner/driver +
  adjudication source hash**, contract) — the cage-hash discipline
  (TRUST 1.2i folds the `sandbox._INNER` template hash into identity for
  exactly this reason; ⚠T6). A changed gate, driver, or pin is a clean
  cache miss, never a stale false-green. The two source-hash pins are
  single-sourced functions (the `derivers.lowering_pipeline_hash()`
  pattern), and landing the contracts bumps `CERTS_VERSION`.
- **L3 — fidelity gates are refusals, tripwires are events.** Non-vacuity
  and entailed-instance failures **refuse** (like B2's dual-solver unsat);
  the triviality tripwire and the examiner **log first-class events and
  claims** but never issue or block a certificate by themselves — they are
  evidence, tier-labeled, exactly as TRUST 3.4 labels intent scenarios.
- **L4 — the kernel-independence honesty note (sharpened, ⚠D6).** Lean's
  elaborator+kernel (channel 1) and `lean4checker` (channel 2) are NOT
  independent implementations: lean4checker links **Lean's own kernel as a
  library** and replays the exported environment through it — it defends
  against *elaboration-time environment manipulation*, not kernel defects.
  Genuinely independent kernel checking is `lean4lean` (a reimplementation),
  run as an additional channel **when pinned**. Every statement-cert /
  proof-cert certificate carries `independence="kernel-family"` (or
  `"kernel-independent"` when lean4lean participates) machine-readably —
  weaker than Z3-vs-CVC5 and never claimed otherwise, the TRUST 3.4 honesty
  move. Imported Mathlib oleans are recertified **once per pin**
  (`lean4checker --fresh` at setup, a long many-core job), and per-statement
  runs recheck only the scratch module; the certificate names which.
- **L5 — the two-run adjudication rule (⚠T1/T2, review-blocking).** No
  verdict-bearing fact may originate from a process in which untrusted bytes
  executed. The repo already legislates this for incumbents ("the
  adjudication must be external", ROADMAP.md:266-272; TRUST 1.2i's three
  one-shot runs; TRUST 1.2h's "by AST literal parse, never executed").
  Applied here: **run 1 (untrusted)** — elaboration of the subject in its
  own sandbox; its outputs (`.olean`, transcripts) are *artifacts, not
  evidence*, and its exit code is a liveness signal only, because
  elaboration-time code can write any file in the scratch dir including a
  forged driver result (`sandbox/__init__.py:84-96` — the payload owns the
  only writable path). **Run 2 (trusted)** — a fresh sandbox in which no
  untrusted bytes are loaded as code: `lean4checker` replays the exported
  environment *as data*, and the **axiom audit is enumerated from the
  exported environment by this trusted pass** (never from `#print axioms`
  output produced in the elaboration session, which the subject could have
  forged or shadowed — ⚠T2; format note ⚠D5: the trusted driver uses
  `Lean.collectAxioms` and emits canonical JSON; `#print axioms` text is
  never parsed). Every claim on the certificate — build success, axiom set,
  statement identity, instance results (⚠T8) — is extracted by run 2 or by
  trusted code outside the sandbox.

What is deliberately **out of scope**, stated here and tier-labeled in the
TRUST amendment (WP-L's final commit), because no checker exists:

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
landing per house rule 6 as ONE commit. ⚠A8 corrects the draft's touchpoint
list: these are **non-pooled, direct-path contracts** (the `monitor-cert` /
`tier-classification` pattern — `kernel/__init__.py:881,920`), so they do
NOT touch `channel_specs`/`run_channel`; the five points that actually
change are `_subject_and_cdesc` · `_dispatch` ·
**`IMPLEMENTED_CONTRACT_TYPES` (`kernel/__init__.py:545-554`) plus the
allowlist re-pin in `tests/test_contract_allowlist.py`** (whose `_FROZEN`
set and dispatch-literal scan both fail otherwise — a deliberate
frozen-vocabulary amendment, named in the commit) · the check methods in
`kernel/backends.py` · the TRUST entry. `POOL_SUPPORTED` and the
channel-parity tripwire are untouched.

- **F0.1 Toolchain pins** (`setup.sh --with-lean`, the flloat discipline).
  ⚠D1: the **Mathlib commit is the single primary pin**; the toolchain is
  *derived* by reading `lean-toolchain` from that commit — setup asserts
  equality and refuses on mismatch (independent pins that drift = a silent
  hours-long Mathlib source build). The pinned commit is chosen so its
  toolchain is a **release/rc** with a matching `lean4checker` tag. ⚠D2:
  lean4checker ships no binaries — setup clones it at the tag equal to the
  derived toolchain version and builds it from source with that toolchain;
  build failure = setup failure, never a soft skip. `lake exe cache get`
  fetches Mathlib's prebuilt oleans at setup (network on); certification
  runs never resolve dependencies (⚠D3, F0.5). All pins are single-sourced
  in `common.py` (env-overridable) and their joint sha —
  `lean_toolchain_hash()` — enters every cache key (L2), alongside the
  **pinned narrow import set** (⚠D15: importing all of Mathlib costs
  30–60 s per process; the fragment touches a handful of Nat/Int modules —
  the import list is a `common.py` constant and part of cache identity).
  Budget honesty (⚠D4): ~8–10 GB disk at setup, ~4–6 GB RAM per
  full-Mathlib elaboration; sandbox rlimits sized accordingly.
  `run_regression.py --fast` stays < 90 s, LLM-free *and Lean-free*.
- **F0.2 `statement-cert`** — subject: a compiled Lean statement (from F1)
  with `:= sorry` as its placeholder proof. Tier: **`emit-check`** (⚠A9/T5
  — the draft's free-standing `kernel-checked` string would raise
  `ValueError` at `library/__init__.py:216-218` against the frozen `TIERS`
  vocabulary, `kernel/certs.py:113-123`; see the F-C freeze for the owned
  amendment). Channels, honestly stated (⚠T3 — lean4checker on a `sorry`
  term re-typechecks what channel 1 typechecked, so bare
  elaboration+replay is NOT two independent evidence channels):
  - channel 1 (run 1 + run 2 per L5): sandboxed elaboration succeeds AND
    the run-2 trusted audit shows `sorryAx` present and any other axiom ∈
    {`propext`, `Classical.choice`, `Quot.sound`} (⚠D5: in practice a
    bare-`sorry` statement over this fragment shows `sorryAx` alone — the
    standard three arrive with real proofs at proof-cert; builders must not
    write an equality test expecting four) — plus the **pp-roundtrip
    sub-check** (⚠D6): the elaborated statement pretty-printed under
    `pp.all` re-elaborates to a definitionally-equal term, catching the
    silent-coercion / wrong-instance class, which is this plan's whole
    mission;
  - channel 2: the **tool-independent fidelity refusal gates** — F2.1
    non-vacuity (Z3∧CVC5+`decide`) and F2.2 entailed instances — whose
    passage is a precondition for issuing the certificate (⚠T3 option (b):
    this is what makes the dual-checker rule genuinely met by disjoint
    evidence rather than by two kernel-family passes; the kernel replay
    still runs and is recorded, labeled per L4).
  Claims: `{statement_hash, mathlib_commit, toolchain, axioms,
  independence, trivially_closed, boundary_behavior}`. Non-claims:
  fidelity-to-text beyond the named gates (the examiner is evidence, not a
  claim — ⚠T10), provability, novelty; "the kernel replay re-typechecks;
  it does not corroborate meaning."
- **F0.3 `proof-cert`** — subject: statement + proof artifact (tactic
  script or term). Tier: **`kernel-checked`**, added to
  `kernel/certs.py:TIERS` by WP-G as an explicit interface-freeze amendment
  (one line + definition comment + a test that the new tier is accepted and
  old certificates still load; CERTS_VERSION bumped — ⚠T5). Channel 1:
  sandboxed `lake` build accepts (run 1). Channel 2 (run 2, trusted): the
  exported environment replays under lean4checker, the trusted audit shows
  **no `sorryAx`** and axioms ⊆ the standard three (⚠T2: this catches an
  axiom smuggled via `Lean.addDecl` metaprogramming with no `axiom` token —
  the escape gate is NOT the axiom defense, the environment audit is;
  there is a tooth for exactly this). `lean4lean` participates as an
  additional run-2 channel when pinned, upgrading the independence claim
  (L4).
- **F0.4 The lexical escape gate** (`buildloop/validate_lean.py`) —
  defense-in-depth, cheap-fast-reject, never the trust boundary (⚠T7).
  Blocklist: `native_decide`, `unsafe`, `axiom`, `@[extern]`, `macro`,
  `elab`, `initialize`, `run_cmd`, `deriving`, `notation`, `syntax`,
  `attribute`, `#eval`, `#check`, `#print`, any `import` outside the pinned
  set. Whitelisted options with lexically-enforced numeric caps (⚠D12):
  `set_option maxHeartbeats N` with `0 < N ≤ H_pin`, `set_option
  maxRecDepth N ≤ R_pin` (`maxHeartbeats 0` = unlimited, refused).
  Identifiers are **NFKC-normalized before matching** and non-ASCII
  identifiers are rejected (guillemet/homoglyph bypasses, ⚠T7). Applied to
  every LLM-authored proof script AND (defense in depth) to the
  deterministic compiler's own output. Its source hash is
  `validate_lean_hash()`, part of cache identity (L2). Teeth: a planted
  `native_decide` proof and a planted `macro_rules` escape, both refused
  pre-sandbox — plus the L5 teeth below, which prove the gate is not
  load-bearing.
- **F0.5 The runner** (`kernel/backends.py: LeanBackend`, API frozen as
  F-H): builds a one-file scratch package that `require`s Mathlib **by
  local path** against the setup-time checkout, with a committed
  `lake-manifest.json` and no-update semantics — no lake invocation in any
  sandbox may resolve dependencies or touch the network (⚠D3; ⚠T9: every
  network-touching `lake`/`elan` operation is setup-time-only, and
  cert-time invocation is sandbox-only where `unshare --net` enforces it).
  Channel-1 builds go through `lake build` because channel 2 needs the
  **olean** (plain `lake env lean file.lean` produces none); instance and
  probe checks (F2.2/F2.3), which need no olean, use the narrow header via
  `lake env lean` (⚠D15). Adjudication follows L5: run-1 outputs are
  artifacts; every verdict-bearing fact is extracted by the trusted run-2
  pass. Content-addressed caching via the existing `kernel_cache`.
- **Done when:** both contracts land five-touchpoint-clean (⚠A8 list) with
  TRUST entries **inside the same commits** (house rule 6 takes precedence
  over docs-merge-ownership for these lines — ⚠X13); the `TIERS` amendment
  + test land in WP-G; a hand-written true statement certifies at both
  contracts; **L5 teeth**: (i) a planted proof script that writes a forged
  driver-result file and exits 0 is refused (⚠T1), (ii) a planted
  `addDecl`-smuggled axiom (no `axiom` token) is caught by the run-2
  environment audit (⚠T2), (iii) a planted `sorry`-smuggling proof is
  refused; escape-gate teeth green; Lean-requiring pytest tests carry
  `pytest.mark.skipif(not common.lean_available(), ...)` — skip-with-
  reason, never fail (⚠X7: no such convention exists in `tests/` today and
  `--fast` runs `pytest tests/` wholesale, `run_regression.py:107-110`);
  Lean demos are `REQUIRES_LEAN = True`, **never** added to `FAST_DEMOS`,
  and skipped-with-note under `--full` when the toolchain is absent — which
  requires the WP-A owned-lines exception on `run_regression.py`
  (⚠A7/X6: `REQUIRES_LLM` does NOT gate collection today — it only picks
  timeout and label at `run_regression.py:74-80,126`; the draft's "gate it
  the way REQUIRES_LLM gates it" described machinery that doesn't exist).

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
  | `object` | `name, type` (type ∈ the carrier whitelist: `Nat`, `Int`) | any force | typed discourse referent |
  | `operator` | `word, carrier` (resolved against `MATH_OPERATORS`, the frozen carrier-indexed table — F-G) | presupposition (quotes the word it construes) or choice | lexicon binding |
  | `hypothesis` | `pred` | **demand or presupposition; never choice** | side conditions — the killer feature: "n > 0", nonzero divisors, the things autoformalization silently drops |
  | `conclusion` | `pred` | **demand only** | the asserted content, quote-grounded verbatim |
  | `quantifier` | `binder ∈ {forall, exists}, objects` | demand or presupposition | binding of declared referents |
  | `ambient` | `carrier` | **choice only** | formalization freedom made legible: which structure the statement is stated over |

  The `pred` grammar (AST frozen as **F-G** — ⚠X2, it is the most
  load-bearing seam in the plan, consumed concurrently by the validator,
  the SMT mirror, and the compiler): terms over declared objects, integer
  literals, `+ * - % ^`, with `-` **carrier-resolved** (⚠D8 — the draft
  omitted `-` while tooth T4 required it: `Nat` ↦ truncated `Nat.sub`,
  `Int` ↦ `Int.sub`; the SMT mirror renders Nat subtraction as
  `(ite (>= x y) (- x y) 0)` over ℤ, because a bare `-` would silently
  reintroduce the very ℕ/ℤ divergence T4 exists to catch) and `^`
  restricted to **literal exponents**, unfolded to `*` in the SMT rendering
  (⚠D10 — SMT-LIB integers have no exponentiation; a variable exponent
  routes the hypothesis set to the decidable-enumeration channel with the
  honest-tier note). Atoms: `= ≠ ≤ <`, `∣`, and the `MATH_OPERATORS`
  words; connectives: `∧ ∨ →`. `%` on ℤ is pinned to `Int.emod`, whose
  in-`[0,|b|)` convention agrees with SMT-LIB `mod` (⚠D9). The gate
  `parse_math_reading` mirrors `parse_reading`: demand quotes verbatim in
  the source text (string containment, not judgment), presupposition quotes
  its trigger, **choice quotes nothing**, fields exact-match `_MLF_FIELDS`,
  statements may reference only declared referents, and a (word, carrier)
  pair absent from `MATH_OPERATORS` is refused as a first-class
  fragment-miss feeding F4 (⚠D9).
- **F1.2 The compiler** (`generators/math_compile.py`): deterministic,
  LLM-free MathReading → Lean statement text, trusted by fiat exactly as
  `reading_compile.py` is (TRUST 1.2e — same two damage bounds: its output
  is fully checked by F0's contracts, and F2 replays meaning-level
  instances against it). Canonical emission (objects sorted, hypotheses in
  id order, fixed pretty-printing) so statement bytes are content-stable.
  Output per the F-B freeze: `{lean_text, statement_hash, provenance}`
  where provenance maps every Lean binder/hypothesis/conclusion subterm to
  the statement ids that produced it — the chain *quoted span → force → LF
  → Lean term*, written beside every artifact like `provenance.json` today.
- **F1.3 Prompt + validator single-sourcing**: the Reading prompt's grammar
  block is rendered from `MATH_LF_KINDS` exactly as
  `buildloop/service_loop.py:185-187` renders it from `LF_KINDS` (the
  P0.5.8 discipline; prompt tests included) — **and the prompt additionally
  renders the live definition table** (name, params, one-line gloss per
  admitted macro), which today's service prompt does NOT do (⚠E1, verified:
  zero `macro` references in `service_loop.py`'s prompt path). This is the
  causal mechanism by which admitted vocabulary changes LLM cost at all —
  without it, definitions are accounting fictions and the F5 benchmark
  measures a coin flip.
- **Done when:** the ten hand-written MathReadings in
  `tests/fixtures_math_readings.py` (⚠X16 — one owned fixture home,
  imported by the parser, compiler, and pipeline tests) parse, compile
  byte-stably (same reading → identical `statement_hash` across runs), and
  a fabricated-quote reading, a choice-with-quote reading, and an
  undeclared-referent reading are each refused at stage
  `math-reading-gate`; their elaboration under F0.2 is verified by the
  WP-H builder (who has the toolchain) and evidenced by the committed
  capture (⚠X7).

### F2 — statement-fidelity gates (the analog of entailed scenarios)

Proof checking verifies proof-vs-statement. Nothing in any pipeline verifies
statement-vs-text. The repo's existing answer generalizes gate by gate; the
pipeline module is `run/formalize.py: certify_statement(source_text,
math_reading_json)` — the staged-refusal shape of
`run/semantic.py: certify_reading`, stage labels pinned as the F-F freeze:
`math-reading-gate → nonvacuity → compile → statement-cert → instances →
examiner → (proof)`.

- **F2.1 Non-vacuity** (the B2 analog, refusal): a statement whose
  hypothesis set is unsatisfiable is refused **before anyone proves it** —
  it would certify vacuously. Mechanism: `generators/math_smt.py` renders
  the hypothesis set to SMT (the `demands_smt` pattern). ⚠T4 states the
  trust relationship precisely: **the mirror and the compiler are two
  hand-written translations of one source that must AGREE — this is not an
  independence differential** (house rule 7 does not apply; the
  two-translations-of-one-text hazard does, TRUST 1.2e's compiler-bug
  class). Discipline, by direction:
  - **sat**: Z3 ∧ CVC5 agree `sat` AND the witness model, instantiated
    into the **actual compiled Lean hypotheses**, is confirmed by `decide`
    in the sandbox (extraction per L5). The Lean confirmation is the
    trusted tie-break — a divergent mirror cannot fake this.
  - **unsat**: dual-solver `unsat` alone does NOT refuse (the unsat
    direction has no witness to cross-check — a divergent mirror would
    produce a false refusal blamed on the source). Refusal at stage
    `nonvacuity` additionally requires Lean-side corroboration on the
    compiled hypotheses (bounded-domain enumeration by `decide` finds no
    satisfying instance up to the named bound). Dual-unsat WITHOUT Lean
    corroboration = a `nonvacuity-inconclusive` outcome: a first-class
    **`mirror-divergence` event** (F-I), never a silent refusal — and a
    tooth plants exactly such a divergence.
  - **`unknown`** from either solver (nonlinear `*`/`%` hypotheses can
    produce it — ⚠D10) = fall back to the decidable-enumeration channel,
    named on the certificate; only corroborated unsat refuses. `gcd` /
    `coprime` atoms have **no SMT rendering** (F-G table) and route to
    enumeration directly.
- **F2.2 Entailed instances** (the entailed-scenarios analog, refusal):
  each demand generates its own concrete tests, mechanically. From the
  quantifier structure and the SMT/enumeration models: (i) the k smallest
  hypothesis-satisfying instances (k pinned, default 5) — the instantiated
  statement **must hold**; a false instance refutes the formalization
  before proof search (this catches wrong operator binding and wrong
  carrier: "for all n > 2" entails checking n = 3, and rejecting a
  construal that makes n = 2 a claim); (ii) boundary probes just OUTSIDE
  each hypothesis (n = 2 for "n > 2") — evaluated and **recorded on the
  certificate** as `boundary_behavior` claims, never auto-refused (a
  statement may be true beyond its stated hypotheses; that is information,
  not error). Discharge is a fixed ladder (⚠D7): `decide → omega →
  norm_num → simp`, each under a pinned `maxHeartbeats` (driver-set,
  whitelisted) with the **sandbox wall-clock/rlimit as the authoritative
  bound** — kernel reduction ignores heartbeats, and `Nat.gcd`
  (well-founded recursion) and large `^` are expected to fall through
  `decide` to `norm_num`/`simp`; the certificate records which rung closed
  each instance. A ladder-exhausted instance falls to the dual-SMT mirror
  or is named-skipped (bounded honesty, the `bounded-K` discipline).
  Results are extracted per L5, and instances are constructed against the
  **compiled** statement, closing the ⚠T4 loop. Plausible (né
  `slim_check`; ⚠D16 — it ships with the Mathlib pin via Mathlib's own
  manifest, no separate line item) runs as an additional refutation
  channel: only its *failure-with-counterexample* is signal; it never
  appears on the proof path (a goal it "closes" is not a kernel proof —
  the F0.3 audit would catch it regardless).
- **F2.3 Triviality tripwire** (event, never a verdict — L3): the probe
  ladder `decide → omega → norm_num → simp → exact?`, each under a pinned
  budget, cheapest first (⚠D11 — `exact?` needs the premise index over the
  loaded environment and is the expensive rung: ~1 min wall / peak-GBs per
  statement; for this micro-domain `omega` and `norm_num` will catch most
  collapsed statements first). Any closure ⇒ first-class `triviality`
  event (F-I payload) and `trivially_closed: true` on the statement-cert
  claims — **logged, not celebrated**: evidence of misformalization (the
  statement collapsed to something the library already knows) or of an
  unambitious corpus entry. The claim is scoped honestly: "trivial
  relative to the pinned import set" (⚠D11 — `exact?` searches only what
  is imported, and the import set is deliberately narrow per D15). The
  benchmark reports the rate.
- **F2.4 The examiner = auto-informalization** (evidence, tier-labeled —
  the founding move: two derivations of one text). Two sub-channels, both
  wired by WP-H (⚠X9 — the draft left this homeless):
  - **(a) instance expectations (mechanical replay, the B5 analog):** an
    independent, semantics-blind pass reads ONLY the source text (never the
    Reading, never the Lean) and authors expected concrete instances —
    "at n = 3 this should hold", "the divisor 0 case is outside the
    claim" — pure JSON, gated by `validate_expectations` (≥1 positive and
    ≥1 boundary expectation, the non-vacuous-expectations rule of
    `validate_scenarios`). Blindness is enforced as a **call signature**
    — the examiner entry point accepts only `source_text`, with a test
    asserting no Reading/Lean bytes reach its prompt (the `CGB_TASK_TIME`
    precedent; ⚠T9) — and remains prompt-level independence, TRUST 3.4's
    caveat verbatim (correlated misreadings survive). Expectations replay
    against the compiled statement by the F2.2 machinery. Divergence =
    first-class `formalization-divergence` event (F-I) driving
    re-authoring; convergence = `intent-admission`-tier evidence.
  - **(b) back-translation:** a second blind pass renders the compiled
    Lean statement back to English; the transcript (source,
    back-translation) is a committed artifact on the run record for human
    audit. **No mechanical agreement claim is made** — text-vs-text
    similarity is not a checker, and pretending otherwise would violate
    house rule 4 (⚠FH10). (expMath lists auto-informalization as a
    deliverable; here it is a trust mechanism with an honest tier.)
- **Done when:** the five-teeth demo (`demos/demo_formalize.py`, the
  `demos/demo_reading.py` analog — LLM-free: T5's examiner expectations are
  **hand-written JSON** through `validate_expectations` + F2.2 replay,
  exactly the demos/demo_reading.py:156-171 B5 pattern; LLM authorship of
  expectations is exercised only in the skippable bench — ⚠X8) is green,
  each tooth caught at its OWN stage:
  - T1 fabricated conclusion (quote not in source) → `math-reading-gate`;
  - T2 contradictory hypotheses (n > 5 ∧ n < 3) → `nonvacuity`
    (dual-solver unsat, Lean-corroborated);
  - T3 wrong operator binding (`∣` construed as `/`) → `instances`
    (smallest witness refutes by `decide`);
  - T4 silently narrowed carrier (a subtraction statement stated over `Nat`
    where the text says integers — ℕ-truncation flips an instance) →
    `instances`;
  - T5 **omitted presupposition, the honest one**: the analyst drops
    "nonzero divisor"; Lean's totalized division (`x / 0 = 0`) makes the
    weakened statement still elaborate and still prove — it is exactly
    Mathlib's `Nat.div_mul_cancel`, no nonzero hypothesis required (⚠D13
    verified the arithmetic: `0 ∣ m ↔ m = 0`, and `0/0*0 = 0 = m`) — so it
    certifies fully and means nothing. Only the examiner's expectation
    about what the sentence MEANS catches it; corroborating detail: the
    F2.2 boundary probe at n = 0 records `boundary_behavior: holds` on the
    same certificate. The demo prints, exactly as B5 does, that fidelity
    to the written formalization and coverage of the unwritten meaning are
    different properties — this tooth is the plan's reason to exist.

### F3 — the governor, re-targeted (small new code, honestly enumerated)

Demand-ledger rows become source texts; coverage = statement certified;
definition admission goes through the MDL gate. This is the piece whose
absence the skill-library literature documents (bloat as the death mode —
METRICS.md already names it); "useful abstractions" gets the operational
meaning nobody ships: **priced compression over real, witnessed demand,
with per-use certification.** The sweep struck the draft's "near-zero new
code" framing (⚠A1/A2/A3/A4/A6): the reuse is real but four seams need
owned edits. The re-anchor resolved the sweep's other worry — the two
dependencies that were unlanded Zone-3 deliverables at sweep time
(seed-readings, witness discipline) **are now landed code**, consumed
as-is below.

- **F3.1 The demand kind** `math-source`: committed files under
  `specs/mathsources/` (one English statement each, the exogenous ground
  truth), ingested by `cgb.py ledger sync` with the byte-match discipline
  (`demand_id = sha256("math-source:" + relpath)`, `origin = "exogenous"` —
  the `_ledger_sync` pattern at `cgb.py:474`, whose per-kind glob+counts
  structure admits a new kind cleanly, ⚠A6 confirmation). **⚠A1
  (blocking, verified by experiment): the `demand` table's schema CHECK
  (`kind IN ('spec-file','nl-request','caged-incumbent')`,
  `library/__init__.py:73`) rejects `math-source`, and `demand_upsert`'s
  `INSERT OR IGNORE` swallows the violation — the sync would
  print success while persisting zero rows.** WP-I therefore carries an
  **escalated owned-lines exception on `library/__init__.py`**: widen the
  CHECK in `_SCHEMA` plus a demand-table rebuild migration on the
  `_migrate_generators` 12-step pattern (SQLite cannot ALTER a
  CHECK), and the done-when includes a **read-back tooth** (after sync, a
  `math-source` row is present-asserted in the DB — the failure mode is
  silent, so presence is the test). Pricing: ⚠A6 — **two** dl.py sites,
  not one: a `math-source` branch in `_demand_cost` (`dl.py:250`,
  following the nl-request shape: served =
  `READING_CHAIN_COST + dl_reading(math_reading, snap.macro_table)`;
  unserved = `UNCOVERED_PENALTY`) AND the per-kind coverage counters in
  `_ledger_total` (:277, which would otherwise never count the new
  kind); the same owned-lines edit converts the silent `return 0.0`
  unknown-kind fallback (:274) into a hard error. ⚠E3 (verified: +400.0
  ledger_dl from 8 unserved system-origin rows — `_demand_cost` never
  reads `origin`): **unserved `origin=="system"` rows price at 0 — dreams
  propose, they must not bill** — and ledger status reports them as a
  separate `dream_rows` column. `cgb.py`'s counts/print lines (:391-392,
  :411) join the owned set. **Coverage** (⚠T10): covered = statement-cert
  issued, whose preconditions are the *refusal* gates (non-vacuity,
  entailed instances — witness/decide-backed); examiner **convergence is a
  separate evidence-tier annotation on the row, never a coverage
  precondition** — the proof-vs-evidence line the `intent-admission` label
  exists to keep visible. `proof-cert` upgrades a row's status metadata;
  coverage never requires it.
- **F3.2 Persistence**: MathReadings live in the existing `readings` table
  (`library/__init__.py:88-93`, verified fit — ⚠A10) keyed by `demand_id`,
  `cert_id` = the composed statement-cert id — the H48 lesson (never
  duplicate live machinery under a second name). ⚠A3/X1 is **resolved by
  the tree**: `cgb.py ledger seed-readings` landed (`cgb.py:364-367`,
  choices at :610) with the S0.2 bridge + certify-at-seed discipline —
  WP-I extends it to the new kind (branch (a) of the sweep's contingency,
  no longer a choice). Certify-at-seed's dependency on
  `certify_statement` keeps WP-G/WP-H in WP-I's needs.
- **F3.3 Definitions are macros** — v1 scope, stated honestly: a minted
  "definition" is a **Reading-layer abbreviation** (the W5.2 macro
  machinery): mined by `buildloop/recurrence.py`'s LGG anti-unification
  over MathReading statement windows — which the sweep proved generic over
  math-shaped statements by execution (⚠A5: `mine` → 1 candidate, admit
  delta −33.0 on planted math readings). The two window/witness seams the
  sweep flagged are **resolved by the tree**: `_demand_windows` now mines
  **uniform-(force, quote)** windows (`recurrence.py:49-70` — the S1.2/H2
  widening, so presupposition-force math idioms are minable), and the Z-E
  `witness_filter` param landed on all three functions
  (`recurrence.mine` :168, `gc_macros` :217,
  `mdl_macros.macro_admission_decision` :180) — WP-J consumes them as-is
  (⚠A4/A5/X11 closed). The residual window-floor fact stands: windows are
  length ≥ 2, so a single-statement idiom is unminable — F5.1's
  ≥ 2-contiguous idiom design rule remains load-bearing (⚠E2). Admission:
  `mdl_macros.macro_admission_decision` — strictly-DL-reducing AND **≥ 2
  witnesses among exogenous-origin readings**, in the landed convention
  `witness_filter=lambda r: r.get("origin") == "exogenous"` — the live
  path already threads exactly this via
  `loop.py:_exogenous_witness_filter` (:298, consumed at :313/:513-517),
  which the math path reuses unchanged. Every
  actual use is certified per-emission by
  `translation-cert(anchor="reference-lowering")` with the trusted
  lowering = the F1.2 compiler: the macro-expanded reading must compile to
  the **byte-identical Lean statement** of its retained inlined baseline
  (channel 1 — verified to fit the landed seam: the cdesc hashing at
  `kernel/__init__.py:338-342` and `check_macro_compile_identity` take a
  math entry unchanged, ⚠A10), plus entailed-instance replay as channel 2.
  **⚠A2 (blocking, corrected): the draft's "no kernel edit" was false** —
  the landed channel-2 replay is welded to service dispatchers
  (`kernel/__init__.py:954-959` → `check_macro_scenario_replay` →
  `build_scenario_dispatcher_harness`, which emits `from service import
  Service`); a math emission has no dispatcher. WP-J carries a **small
  escalated owned-lines kernel edit** making the channel-2 replay
  pluggable per LOWERINGS entry (`spec.get("replay", default_service_
  replay)` at the :957 dispatch), with the math replay = F2.2 instance
  replay. One `LOWERINGS` entry + one TRUST line + that one owned seam.
  What v1 does NOT do: mint Lean-side `def`s that shorten *proof terms* —
  that changes proof identity and belongs to a later phase; dreams may
  propose it, nothing admits it.
- **F3.4 Dreams under witness discipline**: LLM-generated paraphrases and
  domain-variant statements enter as `origin = "system"` rows
  (`specs/mathsources/dream/`, seeded system-origin; a dream seeded as real
  with no committed byte-match is a hard error — S5.1 verbatim). Dreams
  propose vocabulary; **only exogenous witnesses admit it** — in the gate
  and in every DL objective, where "the DL objective" is pinned as
  **`mdl_macros.corpus_dl` over the exogenous sub-corpus**. ⚠E7b is
  **resolved by the tree**: Zone-3 S1.7 landed the ledger macro-cost term
  (`dl.py:280-286` charges `dl_macro` per stored definition), so
  `ledger_dl` and the mining objective now agree and the ledger-side
  assertion is live. Retirement: `gc_macros` applies unchanged; searched
  admission (S1.3, landed flag-gated) applies unchanged — F3 requires
  only the greedy gate.
- **Done when:** `demos/demo_formalize_governor.py` (LLM-free, planted corpora —
  determinism verified: `recurrence.py`/`mdl_macros.py` are clock- and
  random-free with sorted iteration, ⚠E7c) is green: (i) a recurring
  ≥ 2-contiguous-statement idiom with 3 exogenous witnesses is mined,
  admitted, and its uses certify per-emission against retained baselines;
  (ii) the same idiom appearing only in dreams is mined and **refused**;
  (iii) a planted lossy abbreviation (drops a hypothesis) gets **no
  certificate** — compile-hash divergence, the `tests/test_rung.py`
  pattern; (iv) ledger status shows `math-source` rows covered/uncovered
  (the A1 read-back tooth) with **both `corpus_dl` (exogenous) and
  `ledger_dl`** moving the right way on admission (⚠E7b resolved: S1.7's
  macro-cost term is live at `dl.py:286`).

### F4 — fragment-miss machinery (frontier growth as a first-class loop)

When a source sentence does not transcribe into the F1 fragment, that is
not a failure to hide — it is demand data.

- **F4.1** `fragment-miss` events: `certify_statement` stage
  `math-reading-gate` failures and explicit analyst declarations log
  `{source_id, span, missing_kind_guess}` (F-I) via `registry.log_event`;
  a synthesis attempt that exhausts rounds on a gate-refused kind logs one
  automatically (the `exhausted`-is-honest rule, LINGUISTICS §7).
- **F4.2** The ranking report (`cgb.py fragment report`): group misses by
  `missing_kind_guess`, and for each candidate LF-kind extension report
  **demand unlocked per kernel surface added** — pending `math-source`
  rows whose sentences would transcribe, counted from the corpus
  manifest's `expect_transcribes` tags (⚠X14 — the draft's "span-tag
  replay" named a tag source that existed nowhere; the manifest is it),
  labeled as an accounting estimate — against the surface cost (new
  compile rule + SMT/decidable mirror + prompt lines). This is the S2
  lookahead one rung up, v1 as a *report*: the system prices, a person
  decides.
- **F4.3** Admission is human-gated through the **W5 checklist, math
  instance** (ROADMAP briefing item 11, verbatim analog): `MATH_LF_KINDS`
  entry (validator + prompt) · compile rule + provenance ·
  entailed-instance derivation · `math_smt`/decidable coverage (or an
  honest named gap) · ≥ 1 tooth. Dual-checked semantics for the new kind
  or it does not land. No autonomous growth (out-of-scope item 2) —
  permanently.
- **Done when:** the three corpus sentences the manifest marks
  non-transcribable produce logged misses and appear in the report with
  nonzero unlock counts; the report is deterministic over a fixed events
  table; the checklist is committed as
  `specs/mathsources/FRAGMENT_GROWTH.md`.

### F5 — the micro-domain and the governed-vs-ungoverned tooth

Do not launch at research math. The micro-domain is chosen so Mathlib's span
already covers every definition and instances are decidable — frontier-2
pressure near zero, every layer certifying end-to-end. ⚠E1 re-scoped the
headline honestly: the **asserted, certificate-backed win lives in the
LLM-free planted tooth (F5.3)**, where the mechanism provably exists; the
LLM bench (F5.2) **reports** cost-per-certified-statement under the E1
prompt-rendering mechanism, and **an honest tie is an admissible finding**
(the H24 lesson) — the draft's promise of a bench win was unearned on a
tree where the macro table never reached a prompt.

- **F5.1 The corpus** (`specs/mathsources/`, 40 hand-committed English
  statements, elementary number theory + integer inequalities —
  divisibility, parity, gcd/lcm, modular arithmetic, order bounds).
  Composition is engineered pressure, one axis per gate, **declared in
  `specs/mathsources/manifest.json`** (⚠X14 — per-file `{file, axes:
  [side-condition | ambient-ambiguity | idiom:<name> | non-transcribable |
  plain], expect_transcribes, miss_kind_guess?}`; a WP-C test asserts the
  quotas *from the manifest*; F4's teeth, F4.2's report, and F5.3's plant
  selection read it — the manifest IS the cross-WP freeze, an F-D
  extension):
  - ≥ 8 entries with **implicit side conditions** (nonzero divisors,
    positivity, nonemptiness) — presupposition pressure (F2's reason);
  - ≥ 5 with **ambient ambiguity** (ℕ-vs-ℤ, where truncated subtraction or
    negativity changes truth) — choice pressure;
  - ≥ 6 sharing **recurring idioms**, each realized as a **contiguous
    cluster of ≥ 2 statements of a minable force** (⚠E2 — the window floor
    and force restrictions are real; an idiom the miner cannot see is not
    pressure) in ≥ 3 distinct statements each — definition-mining pressure;
  - exactly 3 that **do not transcribe**, each naming its intended miss in
    the manifest (⚠D14): infinitude → `Prime` absent from
    `MATH_OPERATORS`; real-valued → carrier whitelist;
    existence-of-minimum → no set/predicate objects;
  - the remainder straightforward, so coverage numbers mean something.
  Every entry is exogenous ground truth: committed text, byte-matched at
  sync, no LLM in its provenance.
- **F5.2 The benchmark** (`bench/bench_formalize.py`, LLM-requiring, skippable
  with honest note — the ⚠H43 discipline; the teeth live in the LLM-free
  demos). Two arms on identical corpus, model, prompt scaffold, and spend
  cap — **implemented as the same code path over different inputs, not a
  miner fork** (⚠E4, verified: `mine` refuses DL-raising candidates
  inline at `recurrence.py:149`, so "admit everything" is not a flag; and
  origin-blind witnessing is today's *default*, so it is the governed arm
  that needs Z-E):
  - **governed**: mining/admission/gc over **exogenous-origin readings
    only** (Z-E filter), retirement on, per-use translation-cert on;
  - **ungoverned**: the identical calls over **all readings including
    dreams** (the literature's default), retirement off, per-use certs
    off.
  **Reported DL for BOTH arms = `mdl_macros.corpus_dl` over the exogenous
  sub-corpus** — a dream-witnessed macro is admitted by the ungoverned arm
  (it compresses its dream-inflated view) and raises the *reported*
  exogenous DL by exactly its `dl_macro`: real junk, same code path,
  honest mechanism (⚠E4, measured: `dl_macro = 24.0` on the planted idiom
  shape). Cost accounting (⚠E6 — never sum tokens with seconds; wall-clock
  in a DL-adjacent number violates the house's own rule, `dl.py:15-17`):
  per arm `{ktokens_in, ktokens_out, prompt_bytes_mean, refinement_rounds_
  mean, lean_seconds_total, lean_seconds_cold, cache_hit_rate,
  smt_seconds, translation_cert_count, per_use_cert_failures, live_macros,
  retired_macros, triviality_rate, proof_rate (reported, never asserted —
  ⚠D17), certified_exogenous_statements}`. The FH7 anti-gaming
  denominator, exact rule (⚠E3): `cost_per_certified_statement` divides by
  `|{exogenous-origin entries with statement-cert green AND
  trivially_closed == false}|`, with the inclusive variant and the
  trivially-closed count reported beside it so the exclusion is auditable;
  system-origin certifications enter neither numerator context nor
  denominator. Pinned and committed (⚠E5, the S2.3 lesson): model id +
  sampling params, prompt scaffold hashes, both arm configs, spend cap,
  Lean/Mathlib pins; fresh numbers in `results/formalize_governed.csv`;
  relational asserts only.
- **F5.3 The acceptance tooth** (LLM-free, planted —
  `demos/demo_formalize_governor.py` part (v)): a paraphrase-flood plant (one
  idiom, eight system-origin restatements, two exogenous) where the
  ungoverned arm mints junk vocabulary that RAISES the reported exogenous
  `corpus_dl` and the governed arm admits exactly the two-witness
  abbreviation — asserted relationally as a **conjunction with equal
  coverage** (⚠E5: `covered_governed == covered_ungoverned AND
  dl_governed < dl_ungoverned`), no absolute constants (the ⚠H52 lesson).
- **F5.4 Docs, merge-owned final commit** (WP-L): README section; TRUST
  amendments beyond WP-G's in-commit contract entries (⚠X13 — house rule 6
  puts each contract's TRUST entry INSIDE its five-touchpoint commit;
  WP-L owns every *other* TRUST/README/LINGUISTICS edit: the
  `kernel-checked` tier note, L4, out-of-scope items tier-labeled);
  LINGUISTICS gains a §8-style coverage table for the math fragment. One
  commit, after every other phase merge (briefing item 12).
- **Done when:** the ≥ 30/40 certified-statement criterion is read from
  the committed governed-arm CSV — **if the bench is skipped, this
  criterion is explicitly deferred in the skip note and F5's done-when
  reduces to the LLM-free items** (⚠X15); the three planted
  non-transcribables show as fragment-misses, not failures; F5.3's
  conjunction green; docs landed.

## Cross-plan serialization (FORMALIZATION × SPECULATION/Zone 3)

⚠X12, re-anchored: at sweep time no Zone-3 code had landed and this section
carried a seven-row collision table with land-or-build contingencies. **The
re-anchor collapses it: Zone 3 landed whole** (main @ `89e9852` — Stages
A–D plus the live witness discipline). What remains is consumption, not
coordination:

- WP-I **extends** the landed `cgb.py ledger seed-readings` (:364) and adds
  its dl.py/cgb.py owned lines against the landed S1.7-bearing `dl.py` —
  ordinary owned-line merges inside FORMALIZATION's own swarm now.
- WP-J **consumes** the landed uniform-(force, quote) windows
  (`recurrence.py:49-70`) and `witness_filter` params (:168, :217;
  `mdl_macros.py:180`) — its recurrence.py "math windows" write from the
  draft matrix is **withdrawn**: the landed widening already covers math
  forces, so WP-J writes no miner code at all (the H48/H47 lesson landing
  a second time).
- `specs/readings/` vs `specs/mathsources/`, nl-request vs math-source
  rows: disjoint namespaces, genuinely independent (unchanged).
- A future Zone-3 follow-up swarm (if any) coordinates through the same
  ONE shared integrator for `cgb.py`/`dl.py`/`recurrence.py` owned lines.

## Parallel execution plan

One WP = one agent = one worktree = one exclusive file (or owned-line) set;
freezes below let consumers code against signatures — a pattern that is
safe **only when the freeze carries the complete signature** (⚠X18b), which
is why F-G/F-H/F-I exist. The shared integrator owns nothing, serializes
every owned-line merge (both plans' — see above), and runs
`run_regression.py --fast` at every merge.

### Wave 0 — six packages, no cross-dependencies

| WP | scope | exclusive files / owned lines |
|---|---|---|
| **A** toolchain | F0.1 pins + `LeanBackend` (F-H) + escape gate F0.4 + the `REQUIRES_LEAN` skip semantics | `setup.sh` (lean lines), `common.py` (pin lines), `kernel/backends.py` (LeanBackend only), `buildloop/validate_lean.py`, `tests/test_lean_backend.py`, **`run_regression.py` (escalated owned lines, `_build_items`/`_requires_llm` region ~:74-129 — ⚠X6)** |
| **B** fragment | F1.1 + F1.3 + `MATH_OPERATORS` (single-source home) + fixtures | `generators/math_reading.py`, `tests/test_math_reading.py`, `tests/fixtures_math_readings.py` (⚠X16) |
| **C** corpus | F5.1: 40 source files + `manifest.json` + quota test + `FRAGMENT_GROWTH.md` | `specs/mathsources/**` |
| **D** smt-mirror | F2.1's renderer against the F-G freeze | `generators/math_smt.py`, `tests/test_math_smt.py` |
| **E** examiner-gate | F2.4a's `validate_expectations` | `buildloop/validate_expectations.py`, `tests/test_expectations.py` |
| **F** compiler | F1.2 against the F-G/F-A freezes | `generators/math_compile.py`, `tests/test_math_compile.py` |

### Wave 1 — three packages

| WP | scope | needs |
|---|---|---|
| **G** contracts | F0.2/F0.3 five-touchpoint commits (⚠A8 list, incl. `TIERS` + allowlist re-pin + in-commit TRUST entries) + L5 teeth | A only (⚠X10 — fixtures are hand-written Lean texts; F-B consumption is first exercised in WP-H) |
| **H** pipeline | `run/formalize.py` staged pipeline + **F2.1–F2.4** wiring (⚠X9; LLM sub-channels flag-gated) + `demos/demo_formalize.py` five teeth + F1's elaboration done-when + committed captures | B, D, E, F, G |
| **I** ledger | F3.1/F3.2: library migration (⚠A1), extend the landed seed-readings, dl branches (⚠A6) | B, C, F, G, H(partial: `certify_statement` callable) |

### Wave 2 — serialized tail

| WP | scope | needs |
|---|---|---|
| **J** governor | F3.3/F3.4: wire the landed miner/witness machinery to math readings, pluggable-replay kernel seam (⚠A2), `LOWERINGS` entry, `demos/demo_formalize_governor.py` incl. F5.3 | H, I |
| **K** fragment-miss | F4: events + report (manifest-driven); ownership of `run/formalize.py` transfers H → K for the miss-logging hook only (⚠X17) | H, I, C |
| **L** bench + docs | F5.2 bench (skippable) then F5.4 one docs commit | all |

Critical path: A → G → H → J → L. Peak width 6.

Swarm rules: exclusive file (or line-range) lists are review-blocking;
README/TRUST/LINGUISTICS only in WP-L **except WP-G's in-commit contract
entries** (⚠X13); a builder that finds this spec wrong against the tree
**stops and escalates** — never improvises across a freeze.

## Interface freezes

- **F-A MathReading envelope**: `{source: str, reading: {theorem: str,
  statements: [...]}}`; statement = `{id, force, quote, lf}` exactly as the
  Reading's (ROADMAP freeze #3 shape); LF kinds per the F1.1 table.
- **F-B compiled artifact**: `{lean_text: str, statement_hash: sha256,
  provenance: {lean_element: [statement_ids]}}`; canonical emission;
  `statement_hash` is over `lean_text` bytes only (pins live in the cache
  key, not the hash). The pipeline result dataclass mirrors
  `SemanticResult` (`run/semantic.py:45-54`) by **extension with new
  fields** `lean_text`/`statement_hash` — existing field names are never
  repurposed (⚠A10 note: `spec_text := lean_text` would be a rename
  hazard).
- **F-C contract identities**: `statement-cert` (tier `emit-check`) /
  `proof-cert` (tier `kernel-checked`), claims tuples as in F0.2/F0.3,
  cache identity per L2 (statement bytes, proof bytes, import set,
  toolchain hash, Mathlib commit, `validate_lean_hash()`, runner/driver
  source hash, contract). **`kernel-checked` is a one-line owned amendment
  to `kernel/certs.py:TIERS` landing in WP-G with CERTS_VERSION bump and a
  load-compatibility test** (⚠T5/A9); `kernel/certs.py` enters the
  ownership matrix. Non-pooled, direct-path.
- **F-D corpus files**: plain UTF-8 text, one statement (+ optional one
  context sentence), filename `NN_slug.txt`; dreams under
  `mathsources/dream/`; **plus `manifest.json`** with per-file
  `{file, axes, expect_transcribes, miss_kind_guess?}` (⚠X14).
- **F-E vocabulary store**: the registry `macros` table, accessor
  `registry.macro_table()`, names `m_<sha12>` — Z-C verbatim; no new store.
- **F-F pipeline stages**: `math-reading-gate → nonvacuity → compile →
  statement-cert → instances → examiner → proof`; result dataclass per F-B.
- **F-G pred AST + operator table** (⚠X2/X3 — the load-bearing seam):
  ```
  pred := {"op": <connective|atom-op>, "args": [pred|term, ...]}
  term := {"ref": <declared object name>}
        | {"lit": <int>}
        | {"op": <"+"|"*"|"-"|"%"|"^">, "args": [term, ...]}
  connectives: "and" | "or" | "implies"     atoms: "=" | "!=" | "<=" | "<"
        | "dvd" | <MATH_OPERATORS word>
  ```
  Args keep written order (the compiler never reorders); `^` args =
  [base, literal]. Worked examples: "a divides b·c" →
  `{"op":"dvd","args":[{"ref":"a"},{"op":"*","args":[{"ref":"b"},
  {"ref":"c"}]}]}`; "n > 2" is authored as `{"op":"<","args":[{"lit":2},
  {"ref":"n"}]}` (only `<`/`<=` exist; the prompt says so).
  **`MATH_OPERATORS`** — single-source home `generators/math_reading.py`
  (WP-B's file), imported by the mirror and the compiler; v1 content,
  frozen (word → Lean by carrier → SMT rendering → fallback):

  | word | Nat | Int | SMT | no-SMT fallback |
  |---|---|---|---|---|
  | dvd (`∣`) | `Dvd.dvd` | `Dvd.dvd` | `(ite (= a 0) (= b 0) (= (mod b a) 0))` — the a=0 arm matches Lean's convention; SMT mod-by-zero is underspecified, so the special-case is mandatory (⚠D9) | — |
  | even | `Even` | `Even` | `(= (mod n 2) 0)` | — |
  | odd | `Odd` | `Odd` | `(= (mod n 2) 1)` (emod convention, ⚠D9) | — |
  | gcd | `Nat.gcd` | `Int.gcd` (returns `Nat` — the typing rule notes it) | **none** | decidable enumeration |
  | coprime | `Nat.Coprime` | — (v1: Nat-only) | **none** | decidable enumeration |
  | mod (`%`) | `HMod.hMod` (`Nat.mod`) | `HMod.hMod` (`Int.emod`, pinned) | `mod` | — |

  A (word, carrier) pair outside this table refuses at the gate as a
  fragment-miss (⚠D9).
- **F-H LeanBackend API** (⚠X4): `LeanBackend.elaborate(lean_text: str, *,
  expect_sorry: bool) -> {ok, olean_path, transcript_path}` (run 1 —
  artifacts only); `LeanBackend.recheck(olean_path) -> {ok, axioms:
  [str], transcript}` (run 2 — trusted; the only source of verdict-bearing
  facts); `LeanBackend.eval_props(header: str, props: [str]) ->
  [{prop, closed_by, value}]` (the F2.2/F2.3 ladder, two-run). Caching via
  `kernel_cache`, keyed per L2.
- **F-I events** (⚠X5, the Z-D pattern): `fragment-miss {source_id, span,
  missing_kind_guess}`; `triviality {statement_hash, closer ∈ {decide,
  omega, norm_num, simp, exact?}, budget}`; `formalization-divergence
  {source_id, expectation_sha, instance, expected, got}`;
  `mirror-divergence {statement_hash, pred_sha, smt_verdict,
  lean_verdict}` (⚠T4). All via `registry.log_event`
  (`library/__init__.py:319`).

## File-ownership matrix (W = writes, N = new, r = reads)

| file | F0 | F1 | F2 | F3 | F4 | F5 |
|---|---|---|---|---|---|---|
| `setup.sh` / `common.py` (pin lines) | W | | | | | |
| `kernel/backends.py` (`LeanBackend` only) | W | | | | | |
| `kernel/__init__.py` (two five-touchpoint commits; F3's pluggable-replay seam, escalated ⚠A2) | W | | | W | | |
| `kernel/certs.py` (`TIERS` one line, ⚠T5) | W | | | | | |
| `tests/test_contract_allowlist.py` (re-pin, ⚠A8) | W | | | | | |
| `run_regression.py` (escalated owned lines, ⚠X6) | W | | | | | |
| `buildloop/validate_lean.py` | **N** | | | | | |
| `generators/math_reading.py` (incl. `MATH_OPERATORS`) | | **N** | r | r | W (F4 kinds, human-gated) | r |
| `generators/math_compile.py` | | **N** | r | r | W (F4 rules, human-gated) | r |
| `generators/math_smt.py` | | | **N** | | W (F4 mirrors) | r |
| `run/formalize.py` (ownership H → K at Wave 2, ⚠X17) | | | **N** | r | W (miss hook only) | r |
| `buildloop/validate_expectations.py` | | | **N** | | | r |
| `library/__init__.py` (CHECK widening + demand-table migration, escalated ⚠A1) | | | | W | | |
| `buildloop/dl.py` (`_demand_cost` branch + `_ledger_total` counters, escalated ⚠A6) | | | | W | | |
| `cgb.py` (sync/seed + counts/print; `fragment report`) | | | | W | W | |
| `buildloop/recurrence.py`, `buildloop/mdl_macros.py` (landed windows + Z-E consumed, never written) | | | | r | | |
| `generators/derivers.py` (one `LOWERINGS` entry) | | | | W | | |
| `specs/mathsources/**` (incl. `manifest.json`) | | | | r | r | **N** |
| demos/tests/results (each phase's own) | N | N | N | N | N | N |
| README / TRUST / LINGUISTICS (WP-L, except WP-G's in-commit TRUST lines ⚠X13) | W (G) | | | | | W |
| `generators/reading.py`, `generators/reading_compile.py`, `run/semantic.py`, `sandbox/*`, `planner/__init__.py` | r | r | r | r | r | r |

## Builder briefing addendum

1. ROADMAP briefing items 1–3 and 5–12 bind verbatim; item 4 (branch) is
   overridden: push ONLY to the branch your task designates.
2. L1–L5 are review-blocking. No Lean text is LLM-authored, ever; the
   compiler emits it, the escape gate re-checks it, the sandbox runs it,
   and **no verdict-bearing fact leaves a process where untrusted bytes
   executed** (L5).
3. `run_regression.py --fast` stays Lean-free: Lean demos are
   `REQUIRES_LEAN = True` and never enter `FAST_DEMOS`; Lean-touching
   pytest tests self-skip on `not common.lean_available()`; `--full`
   skip-with-note semantics land via WP-A's owned lines (⚠X6). Lean
   demos/captures follow the LLM-capture discipline: builder runs after
   `./setup.sh --with-lean`, capture committed under `results/`.
4. Treat `buildloop/dl.py`, `planner/__init__.py`, `library/__init__.py` as
   frozen interfaces (SPECULATION briefing item 6); the escalated
   exceptions, each owned for named lines only: F3.1's dl.py branches
   (⚠A6), F3.1's library migration (⚠A1), F3.3's kernel replay seam
   (⚠A2), F0's run_regression lines (⚠X6).
5. Zone 3 is landed code, not a concurrent plan: consume
   `ledger seed-readings`, the uniform-(force, quote) windows, the
   `witness_filter` params, and `_exogenous_witness_filter` as-is;
   `recurrence.py`/`mdl_macros.py` are read-only for this plan (⚠X12
   re-anchored). Owned-line merges in `cgb.py`/`dl.py` still serialize
   through the one integrator.
6. Determinism everywhere: no clocks, no `random`, canonical JSON,
   canonical Lean emission. Toolchain pins single-sourced from `common.py`
   and derived per ⚠D1.

## Hazards ledger

Five-lens sweep of the pre-sweep draft (`79c6549`), tree @ `b89becd`;
re-anchored to the unified tree @ `89e9852` (see the block after the
table). Every finding verified by file:line evidence or executed experiment
except those tagged `[dk]` = Lean-ecosystem domain knowledge (toolchain
absent here).
Confirmations the sweep established are folded silently (⚠A10/E7/X18: the
`readings`-table fit, `mdl_macros` genericity over math statements —
proven by execution, admit delta −33.0 — the macros-table freeze, the
`_ledger_sync` shape, LGG miner genericity, F5.3 determinism, the
five-touchpoint anchors, and demos/demo_reading.py B5 as T5's LLM-free
precedent).

| # | finding | evidence | folded into |
|---|---|---|---|
| A1 | `math-source` violates the demand-table CHECK and `INSERT OR IGNORE` swallows it — sync reports success, persists nothing | experiment: upsert returned id, table empty; `library/__init__.py:71-77,414-429` | F3.1 migration + read-back tooth; matrix |
| A2 | translation-cert channel 2 is welded to service dispatchers — "no kernel edit" was false | `kernel/__init__.py:954-959`; `service_gen.py:913-920` | F3.3 pluggable-replay owned seam |
| A3/X1 | `ledger seed-readings` does not exist; it is unlanded Zone-3 WP-A work | grep: SPECULATION.md only; `reading_add` has no live caller | F3.2 land-or-build branch; WP-I needs; cross-plan table |
| A4/X11 | `witness_filter` exists nowhere in code — "reused" reused a plan | grep; `mdl_macros.py:178` signature | F3.3/F3.4 land-or-implement rule |
| A5/E2 | the miner sees only all-demand windows of length ≥ 2 — math idiom forces are invisible; single-statement idioms unminable | `recurrence.py:41-58`; executed: demand-force mine=1 candidate, presupposition mine=0 | F3.3 window dependency; F5.1 idiom design rule |
| A6 | dl.py needs TWO sites (`_demand_cost` + `_ledger_total` counters); unknown kinds silently price 0.0 | `dl.py:238-286` | F3.1; briefing 4 |
| A7/X6 | `REQUIRES_LLM` never gated collection — the cited mechanism didn't exist; `--full` runs everything | `run_regression.py:74-80,121-129` | F0 done-when; WP-A owned lines; briefing 3 |
| A8 | wrong five touchpoints: non-pooled contracts skip `channel_specs`/`run_channel` but MUST touch `IMPLEMENTED_CONTRACT_TYPES` + the allowlist test | `kernel/__init__.py:545-554,881,920`; `tests/test_contract_allowlist.py` | F0 preamble |
| A9/T5 | `kernel-checked` absent from frozen `TIERS`; `register` raises on unknown tiers | `kernel/certs.py:113-123`; `library/__init__.py:216-218` | F-C owned amendment; F0.2 tier = emit-check |
| T1 | elaboration-time code can forge channel-1 verdicts by writing the driver files the runner parses — the scratch dir is the payload's own writable path | `sandbox/__init__.py:84-96`; precedent ROADMAP.md:266-272, TRUST 1.2i | L5; F0.5; L5 tooth (i) |
| T2 | the in-session axiom audit is forgeable and lean4checker does not reject axioms — `addDecl` smuggles one with no `axiom` token | attack analysis; TRUST 1.2h precedent | L5 run-2 audit; L5 tooth (ii) |
| T3 | statement-cert's elaboration+replay is not two independent channels — replay of a `sorry` term re-typechecks channel 1's work | analysis vs TRUST 1.2h's disjoint channels | F0.2 channel restructure (fidelity gates as channel 2) |
| T4 | the SMT mirror is a second translation of one source: the unsat direction has no witness cross-check — false refusals blamed on the source | house rule 7 contrast; TRUST 1.2e class | F2.1 direction-split discipline; `mirror-divergence` event + tooth |
| T6 | cache identity omitted proof bytes, gate hash, driver hash — the stale-false-green class the cage hash exists for | TRUST 1.2i/1.2l; ROADMAP risk table (CERTS_VERSION) | L2; F-C |
| T7 | the lexical gate is bypassable by construction (qualified `Lean.Elab` names, `run_cmd`, homoglyphs, `maxHeartbeats 0`) — it must not be the trust boundary | attack enumeration | L1(iii); F0.4 reframe + expanded list + NFKC |
| T8 | `decide`/tripwire results reach claims through the same forgeable parsing surface | T1 corollary | F2.2/F2.3 extraction per L5 |
| T9 | examiner blindness and network-off were asserted without enforcement points | `sandbox/__init__.py:95` (net-off verified); TRUST 3.4 | F2.4a call-signature test; F0.5 setup-only-network line |
| T10 | coverage conflated kernel certificates with evidence-tier examiner convergence | TRUST 3.4 / `intent-admission` | F3.1 coverage definition |
| D1 | independent toolchain+Mathlib pins drift into hours-long source builds — derive the toolchain from the Mathlib commit `[dk]` | Mathlib pins `lean-toolchain` per commit | F0.1 |
| D2 | lean4checker has no released binaries; build from source at the toolchain-matching tag `[dk]` | — | F0.1 |
| D3 | offline builds need local-path `require` + committed manifest + olean-producing `lake build`; naive shapes fetch at build time `[dk]` | — | F0.5 |
| D5 | a `sorry` statement audits to `sorryAx` alone — the standard three arrive with proofs; parse `collectAxioms` JSON, never `#print` text `[dk]` | — | F0.2/F0.3 wording; L5 |
| D6 | lean4checker = same kernel code as a library; default mode trusts imported oleans; add the `pp.all` round-trip for the silent-coercion class `[dk]` | — | L4; F0.2 pp-roundtrip |
| D7 | kernel reduction ignores heartbeats; `gcd` (well-founded recursion) and big `^` are `decide` cliffs — ladder + wall-clock as the authoritative bound `[dk]` | — | F2.2 |
| D8 | the draft's grammar had no `-` but tooth T4 requires subtraction — internal contradiction, builder deadlock | FORMALIZATION draft internal | F1.1 grammar + mirror `ite` rule |
| D9 | operator table must be carrier-indexed (`Nat.gcd`≠`Int.gcd`); `%`-on-ℤ pinned to `Int.emod`; SMT dvd needs the a=0 special case `[dk]` | — | F-G table |
| D10 | SMT-LIB has no `^`; nonlinear hypotheses yield `unknown`, which the draft never handled `[dk]` | — | F1.1 literal-exponent rule; F2.1 unknown rule |
| D11 | `exact?` costs ~1 min/GBs per statement and only searches the imported set — budget, ladder, and scope the claim `[dk]` | — | F2.3 |
| D12 | legitimate proofs need capped `maxHeartbeats`/`maxRecDepth`; `0` = unlimited must be refused `[dk]` | — | F0.4 |
| D13 | T5's arithmetic verified: the weakened statement is exactly `Nat.div_mul_cancel` — the tooth is sound `[dk]` | — | F2 T5 (citation) |
| D14 | the three non-transcribables should name their intended miss; coprime needs a table entry; abs dropped from v1 | — | F5.1 manifest; F-G table |
| D15 | full-Mathlib import is 30–60 s/process; pin a narrow import set in `common.py`, in every cache key `[dk]` | — | F0.1/F0.5; F2.3 scope note |
| D16 | slim_check is now Plausible, arrives via Mathlib's manifest; refutation-only, never a proof `[dk]` | — | F2.2 |
| D17 | report `proof_rate`, never assert it (60–85% first-pass prior for this domain) `[dk]` | — | F5.2 metrics |
| E1 | the headline had NO causal mechanism: the macro table never reaches any prompt on this tree — identical prompts ⇒ expected token tie; governed arm pays extra cert work | grep `service_loop.py`: zero macro refs in the prompt path | F1.3 prompt rendering; F5 re-scope; Acceptance 5 |
| E3 | dreams bill as real demand: 8 unserved system rows = +400.0 ledger_dl; `_demand_cost` never reads `origin` | executed: 100.0 → 500.0; `dl.py:238-262` | F3.1 zero-pricing rule; F5.2 denominator rule |
| E4 | "ungoverned = flags" was unimplementable: `mine` refuses DL-raising candidates inline; origin-blind witnessing is the DEFAULT | `recurrence.py:149,138` | F5.2 arm re-scope (same calls, different reading sets) |
| E5 | equal coverage must be asserted, not assumed; pin list was incomplete | — | F5.3 conjunction; F5.2 pin list |
| E6 | k-tokens + verifier-seconds in one number breaks with a Lean kernel (seconds swamp tokens; wall-clock in DL violates `dl.py:15-17`) | METRICS.md unit; dl.py house rule 13 | F5.2 split addends |
| E7b | `ledger_dl` charges no macro cost until Zone-3 S1.7 — junk is free-or-winning in that series | executed: admission moved ledger_dl 240.0→50.0, `dl_macro=24.0` never charged | F3.4 objective pin = `corpus_dl` (exogenous); F3 done-when (iv) |
| X2 | the pred AST — the plan's most load-bearing seam, three concurrent consumers — was unfrozen | draft F-A gap | F-G |
| X3 | one operator table, three consumers, no frozen content or home | — | F-G table; WP-B home |
| X4 | the LeanBackend API seam was behavioral prose, not a signature | contrast Z-A/Z-F | F-H |
| X5 | events vocabulary unfrozen (Zone 3 froze Z-D) | SPECULATION Z-D | F-I |
| X7 | Lean-requiring done-whens had no execution venue; `--fast` runs `pytest tests/` wholesale | `run_regression.py:107-110` | F0/F1 done-when; briefing 3 |
| X8 | T5 contradicted the demo's LLM-free declaration absent the B5 precedent | `demos/demo_reading.py:156-171` | F2 done-when |
| X9 | F2.4's wiring was assigned to nobody | draft WP-H scope | WP-H |
| X10 | WP-G's needs over-constrained (F unneeded — hand-written fixtures suffice) | F0 done-when | Wave 1 |
| X12 | no cross-plan collision table or precedence existed anywhere | both plans read | Cross-plan section |
| X13 | TRUST had two owners under contradictory rules (house rule 6 vs docs-merge-ownership) | ROADMAP:625 vs briefing 12 | F5.4; swarm rules |
| X14 | corpus quotas/plants were cross-WP knowledge with no freeze; "span-tag replay" named a nonexistent tag source | draft F4.2/F5.1 | manifest.json (F-D) |
| X15 | F5's headline done-when rested on a skippable component | draft F5 | F5 done-when deferral |
| X16 | the ten fixture MathReadings had no owned home | Zone-3 fixtures precedent | WP-B |
| X17 | `run/formalize.py` quietly had two writers | draft matrix | WP-K ownership transfer |

**Re-anchor (tree @ `89e9852`, Zone 3 merged).** Resolved by the tree:
A3/X1 (`ledger seed-readings` landed, `cgb.py:364`), A4/X11
(`witness_filter` landed on all three functions plus the live
`_exogenous_witness_filter`, `loop.py:298`), A5's window half (uniform-
(force, quote) windows landed, `recurrence.py:49-70` — the ≥ 2 floor and
therefore the F5.1 idiom rule still stand), E7b (`ledger_dl` charges
`dl_macro`, `dl.py:280-286` — the deferred done-when assertion is live).
Re-verified standing: E1 (still zero macro references in any prompt path —
F1.3 remains required work), A1 (the demand-kind CHECK, now
`library/__init__.py:73`), A2 (the service-welded replay,
`kernel/__init__.py:925-957/1295`), A6 (both dl.py sites, `_demand_cost`
:250 with the 0.0 fallbacks :253/:274, `_ledger_total` :277). WP-J's
recurrence.py write is withdrawn (the landed widening covers math forces).
Line-drift-only updates: `_ledger_sync` cgb.py:474,
`macro_admission_decision` mdl_macros.py:180, `mine`/`gc_macros`
recurrence.py:168/:217. Zone-3 S5.1 (`dream.py`) did not land (skippable
by its own plan) — F3.4's hand-planted dream files follow the landed
`specs/readings/dream/` precedent, unaffected.

## Acceptance, restated (post-sweep)

1. A mathematical sentence becomes a certified formal statement whose every
   Lean element traces to a quoted span, a force, and a logical form — with
   fabrication, contradiction, wrong construal, and carrier-narrowing each
   refused at its OWN stage, and the omitted-presupposition residue caught
   by the examiner and demonstrated honestly (five teeth, F2).
2. Both new contracts satisfy the dual-checker rule with genuinely disjoint
   evidence (kernel channel + tool-independent fidelity gates), an honest
   machine-readable independence tier, and **verdict integrity under L5**:
   the three planted forgeries (driver-file, smuggled axiom, smuggled
   sorry) are refused, and no certificate hides what was not checked.
3. Vocabulary grows only under priced compression over exogenous-witnessed
   demand — in the objective actually charged (`corpus_dl`, exogenous
   sub-corpus) — every use certified per-emission against a retained
   baseline; dreams propose, never witness, and never bill (F3).
4. Fragment growth is demand-accounted, validation-harnessed, and
   permanently human-gated (F4).
5. On the fixed micro-domain corpus: the **planted, LLM-free tooth**
   proves governed-vs-ungoverned divergence with certificates (equal
   coverage ∧ strictly lower exogenous corpus DL); the **LLM bench
   reports** cost-per-certified-statement under the prompt-rendered
   vocabulary mechanism with split cost addends and the anti-gaming
   denominator — and an honest tie there is an admissible, publishable
   finding, not a failure (F5).
6. Zero changes to existing contracts' semantics; the named owned-line
   seams (`TIERS`, allowlist re-pin, replay plug, demand-kind migration,
   dl branches, regression skip) are each one commit, each tested; the
   existing regression stays green, fast, and Lean-free.

## Addendum — the F-INT integration layer (`PLAN_FORMALIZE_INTEGRATION.md`)

The phases above landed the fragment, the fidelity pipeline, the governor, and
the Lean seam, and integrated them wherever a subsystem is *corpus/ledger-
generic*. Every subsystem that embeds a **service-shaped model** — the
scheduler, the metrics ledger, the fidelity-gate cache, the bench, Zone-3
speculation, the choice-space search — did **not** yet see math.
**`PLAN_FORMALIZE_INTEGRATION.md`** closes those six seams under the same
honesty disciplines (relational asserts only; never token-seconds sums;
LLM-requiring paths skip with a note; every demo tooth LLM-free and Lean-free;
deferred layers record `deferred`):

- **G1** — the scheduler's fifth `math` move (net score + DL price gate +
  refusal, mark-don't-omit suppression); see README §F-INT.
- **G2** — exogenous-scoped math metrics (`math_total`, `math_covered`,
  `math_dream_rows`, `tier_kernel_checked`) and the `m9_planted` reach curve;
  see METRICS.md, "Math reach vs. cost (F-INT-3)".
- **G3** — the Lean-free fidelity gates (nonvacuity, instances) cached in a
  `formalize_cache` side-store keyed by `(reading_sha, bound)`.
- **G4** — a wave-parallel governed-vs-ungoverned bench that can actually
  diverge, with a frozen append-only CSV and a ktokens-only cost numerator.
- **G5** — a math speculative fan-out (`pre_gate_math`/`fan_out_math`), losers
  uncertified, divergence logged.
- **G6** — a deterministic carrier-**assignment** search
  (`planner/math_choices.py`), examiner-grade evidence (L3), no new cert type.

No existing certificate schema changes and no `CERTS_VERSION` bump is required
by the integration; nothing above is a promised win — only what each teeth
package asserts.
