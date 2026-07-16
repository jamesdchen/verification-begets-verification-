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

The floor this law bottoms out at is three functions and one whitelist:
`match` (linear structural patterns), `subst` (template splicing), and a
fixpoint driver that accepts a rewrite iff a whitelisted well-founded
measure strictly drops. Rules carry **no guards** — the measure check IS
the guard (a commutativity swap on an already-sorted term fails to
decrease `disorder` and is refused by the same check that enforces
totality), so there is one enforcement mechanism and one whitelist to
review, not two. The cost lands where it should: measures carry the
semantic weight and some rungs need lexicographic ones (`exists`-
finitization grows the tree, so its measure is `(quantifier_count, size)`)
— that is the single place review attention concentrates. Below this
floor each remaining piece buys a law clause outright: drop match/subst
and rungs stop being data; drop the fixpoint and normal forms stop being
normal; drop the per-step measure check and totality becomes trusted
rather than enforced; drop the frozen traversal/rule order and the byte-
stable pins die. The one genuinely smaller alternative — hardcoding each
rung as kernel-class Python with no engine — is acknowledged and priced:
it wins iff the wave-1 measurement says canonicalization is the only rung
that will ever pay.

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
  *Literature re-rank (§10):* prequential's role here is permanently
  diagnostic, not a future gate currency — Grünwald & de Rooij (COLT
  2005) prove prequential plug-in codes lose the c=1 redundancy constant
  under misspecification while two-part/NML/Bayes codes keep it, and a
  vocabulary-admission gate is exactly a model-selection comparison. The
  repo's existing counting currency is two-part-shaped; the verified
  result says that is the right shape. If a currency migration is ever
  argued for, it points at C2/C4 (two-part entropy-coded / NML), never
  at C1.
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
the DL panel gains the order-k reference line(s) beside order-0 — and,
per §10.1, the LZ77-parse proxy line, which carries an actual
approximation theorem. Literature re-ranks now folded in: WP-P1
diagnostic-only (§10.3); WP-T4's flood economics precedented by Krimp's
seven-orders collapse (§10.3); WP-T3 is the plan's highest-uncertainty
item — its tractability note failed to attract verified citations
(§10.7) and it does not proceed before that follow-up pass returns.

## 9. What we deliberately will not do

Compress dreams (system-origin text is pressure, not signal). Change
fragment semantics to make statements more compressible. Introduce tuned
regularization constants. Adopt any currency the teeth cannot audit. Add
an escape hatch to the meta-interpreter — under any pressure, ever; that
pressure is a fragment-miss and it gets priced like one.

## 10. Literature (verified synthesis)

**Method and epistemic status.** Two adversarial passes: a deep-research
sweep (24 sources fetched, 81 claims extracted, top 25 verified by
3-vote refutation panels: 23 confirmed, 2 refuted) plus a gap-fill pass
on the areas the sweep's verify budget dropped (8 claim bundles × 2
independent refuters each, one 3rd-vote tiebreak). Publisher domains
(arXiv, ACM, Springer, IEEE, OpenReview, Semantic Scholar) are
proxy-blocked in this environment, so confirmations route through
concordant verbatim copies — author-hosted camera-ready PDFs, official
companion-repo READMEs reproducing abstracts, convergent search-indexed
text across independent mirrors. That is strong but not first-hand for
some quotes; entries below note where it matters. Everything that failed
verification is either dropped or listed under 10.7.

### 10.1 Hardness: vocabulary minimization is approximation, by theorem

- **Charikar, Lehman, Liu, Panigrahy, Prabhakaran, Sahai, Shelat, "The
  Smallest Grammar Problem" (IEEE TIT 51(7), 2005).** No poly-time
  algorithm approximates the smallest grammar within 8569/8568 unless
  P=NP. Practical compressors carry large worst-case ratios (best proven
  heuristic upper bound O(√n)); the LZ77 route gives exponentially
  better O(log(n/m*)) — and the LZ77 parse length is a *computable
  lower-bound proxy* for smallest-grammar size.
- **Bannai, Hucke, Jeż, Lohrey et al., "The Smallest Grammar Problem
  Revisited" (SPIRE 2016 / IEEE TIT 2021).** LZ78 is exactly
  Θ((n/log n)^(2/3)), BISECTION Θ(√(n/log n)); RePair's lower bound
  improves to Ω(log n / log log n), exact ratio open.
- **Casel, Fernau, Gaspers, Gras, Schmid (Theory Comput. Syst., 2021).**
  NP-complete/APX-hard even over fixed alphabets ≥ 17; the smallest
  **1-level grammar** — structurally, a flat macro table over a base
  vocabulary, i.e. R0 — is NP-hard even at alphabet size 5.

Consequence here: greedy/searched admission (R0.5's beam) is not a
compromise awaiting a better algorithm; it is the only shape the problem
permits. And the LZ77-parse proxy is a near-free candidate for a bench
reference line with an actual theorem behind it.

### 10.2 Entropy floors: what the reference lines can and cannot promise

- **Navarro & Russo (DCC 2008):** RePair ≤ 2nH_k + o(n log σ) for
  k = o(log_σ n) — first high-order bound for greedy pair replacement.
- **Ochoa & Navarro (IEEE TIT 65(5), 2019):** coefficient tightened to 1
  for ANY irreducible grammar under the Kieffer–Yang code.
- **Gańczorz (CPM 2019):** RePair's standard practical encoding
  ≈ 1.5|S|H_k; and a matching lower bound — dictionary/grammar coders
  need |S|H_k + Ω(|S| k log σ / log_σ|S|) bits worst-case, and at high
  orders k = α·log_σ|S| they output ≥ (1/(1−α))|S|H_k, a regime where
  context models (PPM/BWT-class) provably win.

Caveats that keep us honest: these are worst-case bounds over adversarial
string families; on highly repetitive corpora (plausibly ours) grammar
coders can encode far *below* nH_k — which is exactly what the bench
measured (2139 < 2450 order-0). Two adjacent claims FAILED verification
and must not be relied on: "early-stopped RePair reaches |S|H_k" (1-2)
and "too many nonterminals provably grows bit-size" (0-3). Consequence:
C3's order-k reference lines have theoretical teeth; the theory does NOT
hand us a proof that vocabulary growth must be regularized — the MDL gate
earns that on measurement, not on a theorem.

### 10.3 MDL: the gate's code-shape is now a literature-backed choice

- **Grünwald & Roos, "Minimum Description Length Revisited" (2019).**
  The canonical modern reference; NML/Shtarkov attains minimax pointwise
  regret and defines parametric complexity (infinite for some classes —
  conditional/luckiness variants exist).
- **Grünwald & de Rooij (COLT 2005).** Under misspecification (data from
  arbitrary P, one-parameter exponential families), prequential plug-in
  codes have redundancy (c/2)·ln n with c = var(P)/var(m*) — while
  two-part, NML, and Bayes codes all keep c = 1. The paper flags this as
  "undesirable in an MDL model selection setting" — and a
  vocabulary-admission gate IS model selection. (The 2010
  "flattened-leader" follow-up restores c = 1 for a modified plug-in
  code.) This is the theorem behind §8's WP-P1 re-rank: prequential is
  a diagnostic, never the gate.
- **Vitányi & Li (IEEE TIT 46(2), 2000).** Ideal MDL from Bayes's rule
  under the algorithmic universal prior: two-part MDL coincides with MAP.
  Compression is "almost always" the best strategy for identification
  and prediction — where "almost always" is load-bearing and technical
  (the Fundamental Inequality: data individually random w.r.t. the
  hypotheses; a measure-one class, not all inputs).
- **Vreeken, van Leeuwen & Siebes, "Krimp" (DMKD 23(1), 2011).** The
  closest empirical precedent for strict-DL-decrease admission: code-table
  candidates admitted only if total two-part DL strictly drops. Collapses
  millions-to-billions of frequent itemsets to *hundreds* — up to seven
  orders of magnitude — with no global-optimality guarantee (consistent
  with 10.1). This is WP-T4's economics argument in someone else's data.

### 10.4 Library learning in program synthesis (gap-fill, 2-0 each)

- **Stitch (Bowers et al., POPL 2023).** Corpus-guided top-down
  branch-and-bound on a compression utility; 3–4 orders faster and 2
  orders less memory than DreamCoder's deductive compression at
  comparable-or-better compressivity; scales to corpora of hundreds of
  complex programs. Admission nuance (split vote, resolved): utility is
  the only *objective*, but structural well-formedness is enforced first
  (free-variable capture analysis, internal cost-consistency assertions,
  a Coq proof about the matching procedure) — engineering invariants,
  not a per-abstraction semantic certificate.
- **babble (Cao et al., POPL 2023).** Library learning modulo theory:
  e-graphs + equality saturation over a USER-SUPPLIED equational theory;
  anti-unification lifted from terms to e-graphs; beats DreamCoder's
  compression on its own benchmarks orders of magnitude faster; scales
  to 2D CAD corpora beyond DreamCoder's reach. Soundness story: one
  meta-theorem (Thm 3.1) conditioned on the supplied theory being sound
  — an unsound rewrite rule propagates into abstractions undetected.

### 10.5 Formal-math library growth (gap-fill, 2-0 unless noted)

- **LEGO-Prover (Wang et al., ICLR 2024).** Every skill is an
  Isabelle-verified lemma before admission; >20,000 skills accumulated;
  miniF2F-valid 48.0%→57.0%, miniF2F-test 45.5%→**50.0%** (camera-ready,
  OpenReview, and the authors' README; the stale arXiv-preprint abstract
  says 47.1% — a real divergence, resolved by 3rd-vote tiebreak with a
  direct fetch of the camera-ready). Ablation: 47.1%→50.4% with newly
  added skills. Admission is checker-gated with NO description-length
  criterion (the "evolver" is LLM-driven generalization). A 2025
  critique exists — "LLM Library Learning Fails: A LEGO-Prover Case
  Study" (arXiv:2504.03048), questioning where the gains come from —
  surfaced but not verified this pass; cite as caution, not as fact.
- **REFACTOR (Zhou, Wu, Li, Grosse, ICLR 2024).** Learned theorem
  extraction from Metamath proofs: run on set.mm it extracts 16 new
  theorems; after refactoring they average 733.5 uses each and shorten
  proofs (corpus compression, kernel-checked artifacts); a
  Holophrasm-based prover retrained on the refactored corpus proves
  relatively 14–30% more test theorems. The nearest neighbor to
  compression-driven lemma mining with checked artifacts.
- **Hipster (Johansson, Rosén, Smallbone, Claessen, CICM 2014).**
  Theory exploration for Isabelle/HOL: QuickSpec enumerates type-correct
  terms to depth 3 (~3 vars/type, equational only), equivalence classes
  by random testing — stability = 200 *consecutive* split-free tests
  (an earlier extraction said "doubling"; refuted). Admission gate:
  every conjecture is re-proved through Isabelle's LCF kernel; external
  evidence is never trusted. Interestingness = proof effort (routine
  reasoning filtered out), not description length. The compiler
  case-study lemmas take ~20s ("nothing exceeds 20s" — unverifiable).
- **DL4TP survey (Li et al., COLM 2024).** Field taxonomy (five task +
  two dataset categories); the premise-selection lineage
  DeepMath (2016) → HolStep (2017) → GNN/transformer work →
  LeanDojo (NeurIPS 2023) → Magnushammer (ICLR 2024); LEGO-Prover as
  the recurring growing-library entry. Verified against the authors'
  companion repo verbatim.

### 10.6 Compression-progress scheduling (2-0)

**Schmidhuber (IEEE TAMD 2(3), 2010; arXiv:0812.4360).** Intrinsic
reward = the FIRST DERIVATIVE of compression of the agent's history
(improvement, not level — else the agent idles in front of noise); seek
regularities that are learnable but not yet known; stated for
resource-bounded compressors, not ideal Kolmogorov; implementations
1991–2002, other groups' variants 2005–2010. This is §5's anchor: the
gap-derivative mining prior is this frame as a scheduler heuristic.

### 10.7 What did not survive, and what stays open

Refuted (do not cite): early-stopped RePair achieving |S|H_k (1-2);
"too many nonterminals provably grows bit-size" (0-3). Unresolved after
both passes: **anti-unification complexity** (Plotkin LGG, higher-order
variants) produced no surviving verified claims — §2's T3 risk note
("restricted pattern fragments stay tractable") currently rests on
training knowledge, not verified citations, and is flagged for a
follow-up pass before WP-T3 lands. Open questions worth a future sweep:
MDL consistency under *approximate* (greedy) codelength minimization;
empirical dictionary-vs-PPM behavior on repetitive formal corpora; the
2504.03048 critique's substance.

### 10.8 The verdict on the distinctive claim

It survives contact, sharpened into a 2×2 the literature fills out
three cells of. Soundness-gated admission exists (LEGO-Prover, Hipster,
REFACTOR — checker-certified, no DL criterion). DL-gated admission
exists (Krimp, Stitch, babble — strict compression objectives, no
semantic certificate; babble's soundness is one trusted-theory
meta-theorem, Stitch's is structural invariants). **The fourth cell —
admission requiring BOTH a certificate battery AND a strict DL decrease
in an audited currency — is unoccupied in everything verified across
both passes.** That is this repo's position, now stated with the
literature rather than against it. The cost side is also confirmed by
the same table: the certificate systems report proof-rate gains, the
compression systems report DL gains, and nobody reports both — which is
exactly the bench's two-panel design (reach + DL) arguing that the
combination is measurable at all.
