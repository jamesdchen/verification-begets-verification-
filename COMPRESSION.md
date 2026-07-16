# COMPRESSION.md — pushing corpus DL toward the floor: the tower, the ladder, the plan

The bench's DL panel measures one number: `corpus_dl` — the description
length of the exogenous corpus under the live vocabulary, in the counting
currency of `mdl_macros`. Its slope is the marginal cost per new statement.
"Compressing further" means slope reduction. The floors, in order: order-0
token entropy (measured and already beaten — 2139 < 2450 on the 37-source
run; a memoryless code cannot see the recurring windows the macros
compress), order-k entropies (computable, unbeaten, unmeasured), and
Kolmogorov (uncomputable). The measured fact that the flat macro coder
beats the memoryless bound is this document's license: the headroom is in
*structure*, and structure is what this system certifies.

Everything below is bounded by the house constraints, restated once: ≥ 2
exogenous witnesses at every rung (dreams propose, never witness — the
bench measured why: governed 2139 < ungoverned 2371 at equal coverage);
admission = strict DL decrease in the named currency, never a tuned λ
(E5/H52); one currency (`dl.py`'s law) — a new metric gets a new name and
is REPORTED beside the old before anything gates on it; every rung lands
with its own planted tooth and a rung-free byte-identity pin.

## 1. The tower is the compressor

The repo already contains a tower — the spec-to-code vagueness tower
(`demo_tower.py`): rungs of increasingly short, vague expressions, each
lowered to the layer below by certified machinery. Read it as compression:
a rung is a codebook over the layer beneath, and the description length of
any artifact is |its top-rung expression| + the amortized model bits of
the rungs it rides through. That is a two-part MDL code with the tower as
the model.

This yields the central distinction:

- **Within-rung compression** (the coder ladder, §2) shaves the marginal
  cost of statements at a fixed layer. For a stream of genuinely novel
  statements it can never beat linear-at-entropy — total DL is Θ(n·H) at
  that layer, and the flattest achievable curve is a line of slope H.
- **Across-rung compression** (climbing, §5–§7) moves the *description
  itself* up a layer. Each admitted rung's model bits are paid once and
  amortize toward zero per-artifact; the per-artifact cost approaches the
  entropy of the choices made at the top rung. This is the only mechanism
  that beats a fixed layer's floor — and it is the system's main
  compression tool.

The governing law (the repo's name as an engineering theorem): **tower
height ≤ certification reach.** A rung without a checker is an unearned
claim — the artifact's trust collapses to its weakest uncertified
lowering. Definitions climb freely (translation-certs exist); derived
operators climb freely (the gate-correctness battery exists); rungs of
machinery climb exactly as far as §6–§7 extend the anchors.

## 2. The coder ladder (within-rung; currency unchanged)

Ordered by engineering risk. Landed rungs first, for orientation:

- **L0 (landed):** flat contiguous uniform-(force,quote) windows, len 2–4,
  LGG anti-unification, ≥ 2 exogenous witnesses, greedy strict-DL
  admission; searched admission (beam; math-exercised, 82→65 on the trap
  corpus); the derived-operator tower (`generators/operator_growth.py`:
  definitional extensions stack inductively under the battery).
- **T1 — the macro tower (macros-over-macros):** the idiom layer is flat
  *by construction* — `_demand_windows` returns raw statements, so a macro
  can never abstract over macro invocations, and recurrence *among* macro
  uses is invisible. Fix: mine over the REWRITTEN corpus; allow macro
  bodies to carry macro refs with transitive expansion at pricing and use;
  dependency-aware GC (a macro referenced by a live macro cannot silently
  retire). Tooth: two co-occurring flat idioms whose co-occurrence no flat
  table compresses; a level-2 macro strictly lowers `corpus_dl`.
- **T3 — operator-parameterized (higher-order) macros:** LGG abstracts
  terms, not operators. The congruence triple (`33/34/35_cong_add/mul/sub`)
  is byte-identical up to the lifted operator: one body + an operator-kind
  slot + three one-token bindings. Higher-order anti-unification is
  intractable in general; the operator-slot fragment (slots range over the
  frozen `MATH_OPERATORS`/kernel ops only) stays finite and minable.
  Tooth: the congruence triple itself.
- **T4 — subtree mining → derived-operator proposals (auto-R2):** the
  miner sees statement windows; recurring PRED SUBTREES (e.g.
  `mod(x,m) = mod(y,m)`) are invisible until a human proposes an operator.
  A subtree miner emitting candidate rows into
  `specs/mathsources/operators/proposed/` — with the battery as the SOLE
  admitter — closes the loop: autonomous vocabulary growth at the operator
  layer, certificate-gated. This is the cheapest *rung-climbing
  automation* available, not merely another vocabulary widget.
- **T2 (deferred) — gapped windows:** idioms with holes; contiguity is an
  artifact of the window walk. Candidate space grows combinatorially;
  defer until T1/T3 measurements say the contiguous space is mined out.
- **T5 (deferred) — grammar induction as untrusted GENERATOR:** run a
  smallest-grammar approximator over the structure stream purely to
  *propose* candidates; every production still enters through the same
  witness + strict-DL gate. The generator is untrusted by construction, so
  a heuristic compressor cannot smuggle an unsound or unwitnessed
  abstraction. Defer until the ladder below it saturates.

## 3. Currency upgrades (the code, not the codebook) — reported-first

- **C1 — `prequential_dl` (build first):** charge each statement −log p
  under the model as it stood BEFORE that statement, then update. Online,
  hindsight-free, self-regularizing: junk vocabulary pays its bits upfront
  and never recoups. Computable from the existing wave protocol. Expected
  to rank governed < ungoverned with NO knowledge of origins — an
  origin-blind detector of dream-flood poisoning, worth landing for that
  demonstration alone. This is the principled version of "H as a
  regularizer": H used causally, no tuned constant anywhere.
- **C2 — two-part entropy-coded DL:** model bits (bodies, as now) + data
  bits entropy-coded over token/production frequencies; converges toward
  achievable H as the class widens; subsumes the order-0 reference line.
- **C3 — order-k / context models on the structure stream:** the
  computable reference ladder above order-0, worth plotting even if never
  adopted as currency.
- **C4 — NML** where sub-models are small enough for it to be tractable.

The anti-pattern, named so it is never built: `admit iff ΔDL < −λ·H` with
a tuned λ — an absolute constant in the admission inequality.

## 4. Canonicalization (recurrence you cannot currently see)

Commutativity, variable naming, hypothesis order: meaning-preserving
variation that defeats byte-level window matching. A deterministic
normal-form pass before mining raises visible recurrence — but it changes
statement bytes, so it needs its own certificate (**norm-cert**: compiled-
statement equivalence via the existing dual channels — solver equivalence
+ entailed-instance replay) and a documented, frozen normal form.
Canonicalization is itself a *lowering* (a rewrite over the fragment's own
ASTs) — which makes it the pilot rung-spec for §6.

## 5. Scheduling: compression progress as the mining prior

The gap between current `corpus_dl` and the best computable reference
(order-k over the window stream) is the remaining *visible* headroom; a
candidate admission's expected reduction of that gap is its compression
progress. Price recurrence moves by expected progress; stop mining when
the gap's slope flattens. The current max-marginal-saving greedy pick is
the one-step special case. (Literature anchor: Schmidhuber's
compression-progress framing — §10.)

## 6. Climbing methods — the preference law, and the minimal meta-interpreter

Three ways to add a rung, ranked. The law: **data over code, kernel over
gates; generate code only under measured speed pressure, and then
translation-validate every lowering.**

1. **Climb as data (the default):** rungs are declarative *rung-specs* —
   pattern-rewrite rules over the existing LF/pred ASTs, pure data,
   authored the way everything here is authored (an LLM may propose; gates
   admit) — executed by ONE fixed meta-interpreter. No code is generated;
   the tower is data over a single trusted engine.
2. **Climb by codegen + translation validation (when speed forces):** the
   compiled form of (1). The generated lowering code is *cargo below the
   validation line* — never trusted, every lowering it performs checked by
   rung-below certifiers (the emitted-codec pattern the service side
   already runs; eBPF's verifier discipline is the industrial precedent).
   Futamura's projections say (1) and (2) are interconvertible; the
   certificates are what make every projection admissible.
3. **Climb inside the kernel (highest trust, highest cost):** define the
   new rung's constructs as Lean definitions; lowering IS kernel-checked
   definitional unfolding. Zero new trust, ever — this is how mathlib
   itself grows; the fast-gate architecture is a deliberate speed fork of
   it, and remains available for any rung that justifies the cost.

**Why climb-by-data is rare elsewhere, and why the economics invert here**
(recorded so the failure modes stay named): in open-ended, low-assurance,
performance-bound settings, data towers die of (a) compounded interpretive
overhead (the tower-of-interpreters problem; partial evaluation stayed
hard for decades), (b) the expressiveness death spiral (config → DSL →
accidental bad programming language; yacc's own semantic-action escape
hatch; the commercial failure of 2000s model-driven architecture), (c) the
meta-interpreter becoming the hairball, and (d) tooling gravity. The
survivors are narrow-domain systems: SQL/Datalog, the K framework, Lean's
own macro/elaborator layer, eBPF. Here the economics invert point by
point: lowering runs at build time and certification dominates cost, so
(a) does not bind; the honesty rules make (b) structurally impossible — a
rung-spec that cannot express something logs a **fragment-miss priced as
demand**, never a hack (the spiral's first symptom, an escape hatch, is
refused by law below); auditability — worthless in most markets — is the
entire product; and LLM authoring removed the historical spec-writing
pain that killed MDA.

**The minimal meta-interpreter law** (the new trusted surface, kept
brutally small; every clause below is load-bearing):

- **Pure and total:** structural recursion over the input AST only; no
  I/O, no clock, no randomness; termination by a required decreasing
  measure per rule set (checked at rung admission, not trusted).
- **Zero escape hatches:** no eval, no imports, no callbacks into
  spec-carried code, no string-to-code paths. A rung-spec that needs one
  has hit the fragment boundary: log the miss, price the demand, grow
  through the gate. This clause is the anti-spiral, and it is absolute.
- **Small enough to review in one sitting**, and frozen: every change to
  the interpreter is a plan-level event with its own adversarial review —
  it is `kernel/`-class code, not `buildloop/`-class.
- **Never the judge:** the interpreter executes lowerings; it certifies
  nothing. Every lowering's output is validated by rung-below checkers
  (norm-cert equivalence channels, compile round-trip, dual solver,
  instance replay). One engine + per-use validation IS the two-channel
  story; the interpreter needs no twin.
- **Spec admission is battery-gated** like R2 rows: well-formedness (rules
  are pattern→template over known AST kinds; measure decreases),
  per-lowering differential validation on an instance battery, vacuity
  refusal (a rung that rewrites nothing on the corpus is not admitted),
  and the MDL gate — a rung is admitted when its model bits pay for
  themselves in corpus DL. Semantics in; code never above the line.

## 7. Dissolving the human gate (anchor extension)

The residual human gate guards semantic extensions — new LF kinds whose
outputs existing checkers cannot judge. Three repo-native mechanisms
shrink that residue:

1. **The kernel is the anchor.** Any semantics *definable in Lean*
   inherits the kernel as its checker: the new fast gates are
   approximations, differentially validated per-use against kernel
   evaluation (`LeanBackend.eval_props` / `elaborate` are the existing
   oracle seam). The checker-of-checkers regress terminates where the
   repo already terminates trust.
2. **Grow anchors by conservative laddering.** Admit the *finitized*
   shadow first — bounded `exists` is a finite disjunction, checkable by
   today's enumeration gate — accumulate corpus and expectations under
   it, then extend to the unbounded semantics keeping the bounded version
   as a permanent differential channel on the overlap. Anchors are grown,
   not found.
3. **Manufacture independence** for the thin remainder: N independently
   derived checker implementations (different backends, twin-reading
   derivations), examiner-style source-blind expectation batteries, and
   perpetual mirror-divergence tripwires. Agreement never proves
   soundness; it is the same epistemics the dual-solver verdicts already
   carry.

What remains human is exactly the extra-logical (importance, intent,
aesthetics) — the category FORMALIZATION.md excludes by design — plus an
audit function over divergence logs. The human gate is not a permanent
architectural feature; it is the current radius of the kernel's reach,
plus an auditor.

## 8. The plan (swarm-executable; house rules as in PLAN_FORMALIZE_INTEGRATION.md)

Phase ordering is by measurement dependency, not preference. Wave-0
packages are file-disjoint and parallel; every package: capture-before-edit
pins, relational asserts, own teeth, suite validation in CI only.

- **WP-P1 — `prequential_dl` (C1).** Reported column in the bench CSV
  (append-only) + the m9 metrics: per wave/iteration, cost the new
  statements under the PRE-wave model, then update. Teeth: prequential
  ranks governed < ungoverned on the committed run with origins hidden;
  hindsight DL ≤ prequential DL (relational, by construction). Files:
  `bench_formalize.py`, `metrics/`, own tests. No currency change.
- **WP-T1 — the macro tower.** `recurrence.mine` over the rewritten
  corpus; bodies may reference macros; transitive expansion in
  `mdl_macros`; dependency-aware `gc_macros`. Teeth: the co-occurrence
  plant (level-2 macro strictly lowers DL where no flat table can); flat
  corpora byte-identical (pin); GC never retires a referenced macro.
- **WP-T3 — operator-slot macros.** AU extended with ONE slot kind:
  operator positions may generalize to a slot ranging over the frozen op
  vocabulary; invocation binds the op. Teeth: the congruence triple
  compresses to one body + three bindings with strict DL drop; term-only
  corpora byte-identical (pin).
- **WP-T4 — subtree miner → operator proposals.** Mine recurring pred
  subtrees (≥ 2 exogenous witnesses); emit candidate rows to
  `specs/mathsources/operators/proposed/`; the R2 battery remains the
  sole admitter; admitted rows feed T1/T3 vocabulary on the next pass.
  Teeth: the `mod(x,m)=mod(y,m)` subtree yields a `cong`-like proposed
  row that the battery admits; a planted unsound subtree row is refused;
  nothing writes `admitted.json` but the battery.
- **WP-T6a — rung-spec fragment + minimal meta-interpreter.** The §6
  interpreter under its law (pure, total, escape-free, reviewed as
  kernel-class) + the rung-spec schema (pattern→template rules, decreasing
  measure, battery-gated admission). Pilot rung: **canonicalization**
  (§4) — commutativity ordering + hypothesis sort as rewrite rules, every
  lowering norm-cert-validated; tooth: mining the canonicalized corpus
  finds a planted recurrence the raw corpus hides, at strict DL profit
  net of rung model bits.
- **WP-T6b — second rung: `exists`-finitization.** Bounded existentials
  as finite disjunctions (the conservative-laddering demonstration, §7.2)
  — dissolving the `28_predecessor` authoring workaround honestly. Tooth:
  an exists-reading certifies via the finitized lowering with the
  disjunction checked by today's gates; the finitized channel is retained
  as differential when/if unbounded semantics later lands via the kernel
  anchor.
- **Wave 1 (measure, then decide):** with P1/T1/T3/T4/T6 landed, re-run
  the bench + m9; the measurements gate the deferred tail (T2, T5,
  C2–C4, in-kernel rungs). No deferred item proceeds without a number
  from this wave arguing for it.

Global acceptance: every tooth green in CI; all byte-identity pins hold;
the DL panel gains the order-k reference line(s) beside order-0; the plan
is re-ranked against §10 when the literature synthesis lands.

## 9. What we deliberately will not do

Compress dreams (system-origin text is pressure, not signal). Change
fragment semantics to make statements more compressible. Introduce tuned
regularization constants. Adopt any currency the teeth cannot audit. Add
an escape hatch to the meta-interpreter — under any pressure, ever; that
pressure is a fragment-miss and it gets priced like one.

## 10. Literature (pending)

A deep-research synthesis (smallest-grammar hardness and approximation
bounds; MDL/prequential/NML theory; DreamCoder/Stitch/babble library
learning; LEGO-Prover-class skill libraries for ITPs; anti-unification
complexity; the Solomonoff–Schmidhuber lineage; order-k entropy floors;
translation validation and verified-compiler-vs-validated-lowering) is in
flight and lands here as an amendment, with the plan in §8 re-ranked
against it. Claims above that lean on the literature are provisional until
then; the distinctive claim we expect to survive contact: library-learning
systems admit abstractions by *score*, this system admits them by
*certificate* — slower climbing that never falls over.
