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

*(Amended by §11.5: the floor as stated has two verified defects. A
global inversion-count measure makes commutativity-sort NON-CONFLUENT —
an inner swap can be refused because it creates offsetting inversions at
the parent, so one commutativity class reaches two normal forms; the
measure's sort keys must be order-invariant (multiset-canonical), which
knowingly bakes the normalizer into the measure and is accepted
explicitly. And linear pattern→template rules cannot sort n-ary argument
lists or reorder statement lists at all — sorting enters as TWO frozen
engine primitives, `sort-children(op, key)` and `sort-statements(kind,
key)`, with keys drawn from the measure-key vocabulary; rules select
where they apply, the engine sorts. The floor is therefore three
functions, two primitives, one whitelist.)*

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

Phase ordering is by measurement dependency, not preference. Every
package: capture-before-edit pins, relational asserts, own teeth, suite
validation in CI only. *(Amended by §11: the original "file-disjoint and
parallel" claim for wave 0 is false against the real files — true wave-0
width is ~3 (P1, T1, T6a), with T6a→T6b, T1→T3, and T4-after-T6a ordering
edges; an F-INT-style ownership matrix is a precondition, not an option.
Each package below carries a §11 verdict; the §11 re-specs are binding.)*

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
  corpora byte-identical (pin). *(§11 verdict: three blockers found;
  measurement-gated — run the §11.2 census before building.)*
- **WP-T3 — operator-slot macros.** *(§11 verdict: premise FALSE — plain
  first-order LGG already mines operator slots, and the shipped 2139
  table contains one. Re-scoped in §11.3 to the real blockers: window
  quote-uniformity and the absence of any math macro invocation surface;
  slot typing survives as an honesty restriction, not a compression
  feature. The §10.7 anti-unification citation gap is closed by
  representation, not literature.)*
- **WP-T4 — subtree miner → operator proposals.** Mine recurring pred
  subtrees (≥ 2 exogenous witnesses); emit candidate rows to
  `specs/mathsources/operators/proposed/`; the R2 battery remains the
  sole admitter; admitted rows feed T1/T3 vocabulary on the next pass.
  Teeth: the `mod(x,m)=mod(y,m)` subtree yields a `cong`-like proposed
  row that the battery admits; a planted unsound subtree row is refused;
  nothing writes `admitted.json` but the battery. *(§11 verdict: two
  criticals — the battery admits unpriced aliases, and this tooth is red
  on day one via a real mod-by-zero mirror gap; re-specs in §11.4.)*
- **WP-T6a — rung-spec fragment + minimal meta-interpreter.** The §6
  interpreter under its law (pure, total, escape-free, reviewed as
  kernel-class) + the rung-spec schema (pattern→template rules, decreasing
  measure, battery-gated admission). Pilot rung: **canonicalization**
  (§4) — commutativity ordering + hypothesis sort as rewrite rules, every
  lowering norm-cert-validated; tooth: mining the canonicalized corpus
  finds a planted recurrence the raw corpus hides, at strict DL profit
  net of rung model bits. *(§11 verdict: measure design and rule-fragment
  expressiveness both fail as specified; a pre-existing carrier bug must
  land first; re-specs in §11.5.)*
- **WP-T6b — second rung: `exists`-finitization.** Bounded existentials
  as finite disjunctions (the conservative-laddering demonstration, §7.2)
  — dissolving the `28_predecessor` authoring workaround honestly. Tooth:
  an exists-reading certifies via the finitized lowering with the
  disjunction checked by today's gates; the finitized channel is retained
  as differential when/if unbounded semantics later lands via the kernel
  anchor. *(§11 verdict: UNSOUND as written — rewriting compiled bytes
  certifies a false statement green under the k-smallest instance mask.
  Finitize the eval channel only; re-specs in §11.6.)*
- **Wave 1 (measure, then decide):** with P1/T1/T3/T4/T6 landed, re-run
  the bench + m9; the measurements gate the deferred tail (T2, T5,
  C2–C4, in-kernel rungs). No deferred item proceeds without a number
  from this wave arguing for it. *(§11 verdict: predicates must be
  pre-registered and the cost axis is VOID on the committed run —
  §11.7.)*

Global acceptance: every tooth green in CI; all byte-identity pins hold;
the DL panel gains the order-k reference line(s) beside order-0 — and,
per §10.1, the LZ77-parse proxy line, which carries an actual
approximation theorem. Literature re-ranks now folded in: WP-P1
diagnostic-only (§10.3); WP-T4's flood economics precedented by Krimp's
seven-orders collapse (§10.3). *(The earlier T3 literature gate is
superseded: §11.3 closes the tractability question by representation —
one-slot operator generalization over this AST shape IS first-order
Plotkin LGG, no higher-order machinery involved.)*

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
  criterion (the "evolver" is LLM-driven generalization). **The critique (now verified, 2-0):**
  Berlot-Attwell, Rudzicz & Si, "LLM Library Learning Fails: A
  LEGO-Prover Case Study" (arXiv:2504.03048; expanded and peer-reviewed
  as "Is This LLM Library Learning? Evaluation Must Account For Compute
  and Behaviour", EACL 2026) — log-verified evidence that retrieved
  skills are almost never reused (of >20,000 lemmas, ~6% ever reached a
  solving prompt; exactly one verbatim reuse found), and that
  LEGO-Prover burns 5.8–14.2× the per-attempt compute of
  Draft-Sketch-Prove, against which its accuracy edge washes out when
  cost-matched. Calibration: the reuse finding is solid; the "gains
  vanish" claim compares a cost-matched external baseline, not
  LEGO-Prover's own internal ablation, so it reframes the 47.1→50.4
  number's cause (hidden inference-time scaling) rather than directly
  refuting it. No rebuttal from the original authors found. For this
  repo the moral is §10.8's, sharpened: a certificate gate without a DL
  discipline can grow a large, sound, and *useless* library —
  admission-by-strict-DL-decrease is exactly the mechanism that would
  have refused those 20,000 unpaying skills.
  *The second data point (single-pass verified):* Sesterhenn,
  Berlot-Attwell, Zenkner & Bartelt, "A Compute-Matched Re-Evaluation
  of TroVE on MATH" (arXiv:2507.22069; AI4MATH Workshop @ ICML 2025 —
  workshop preprint, not full peer review) re-ran TroVE against a
  compute-matched PRIMITIVE baseline (CodeLlama-7b-Instruct, 5 vs 15
  samples) and found the toolbox edge collapses to "a marginal
  improvement of 1%" once compute is equalized, with tool reuse
  reported as vanishingly rare and gains attributed to sampling budget.
  Calibration: NOT independent — Berlot-Attwell co-authors this, the
  2410.20274 precursor, and the EACL 2026 LEGO paper, so this is one
  critic lineage spanning two systems, uncontested so far, rather than
  replication by a separate lab. The DreamCoder-line linkage lives in
  the EACL paper's framing (whether these LLM systems merit the
  "library learning" label at all), not in the TroVE paper's own text.
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
  by random testing — stability mechanics settled from the paper's own
  LaTeX source (the author repo carries it): run 200 tests, stable iff
  nothing changed in the last 100, else DOUBLE the test count until
  stable. (Verification lineage kept honestly: the first extraction
  said "doubling", a gap-fill vote "refuted" that in favor of
  200-consecutive, and the primary-source vote overturned the
  refutation — the doubling schedule is verbatim in the paper.)
  Admission gate: every conjecture is re-proved through Isabelle's LCF
  kernel; external evidence is never trusted. Interestingness = proof
  effort (routine reasoning filtered out), not description length. The
  compiler case-study lemmas take ~20s, and "None of our examples takes
  more than twenty seconds to run" is verbatim in the paper (previously
  marked unverifiable; now primary-source confirmed).
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
variants) produced no surviving verified claims. *(Subsequently closed
by §11.3 without literature: in this repo's representation operators are
scalar leaves under an `"op"` key, so "one operator slot" IS first-order
Plotkin LGG — unique, linear per node pair; no higher-order machinery is
involved and no citation is required. The general higher-order question
remains uncited and unneeded.)*

**MDL under greedy minimization (the §10.7 open question, now
answered — against us, and recorded).** Single-pass verified sweep:
Grünwald's crude-two-part consistency requires only a FIXED hypothesis
code (any code, sample-size-independent) — code optimality is not the
load-bearing condition, but neither is search addressed. Barron & Cover
(1991) prove risk bounds for the estimator that ACHIEVES the two-part
minimum (with slack entering the bound quantitatively; resolvability
bounds do not in general imply consistency). Most directly, **Adriaans
& Vitányi, "Approximation of the Two-Part MDL Code" (IEEE TIT 55(1),
2009)**: a successively monotonically length-decreasing sequence of
two-part codes — exactly a strict-DL-decrease admission trajectory —
need NOT monotonically improve goodness of fit, and the property that
would rescue it (each step using the genuinely shortest model code)
"cannot be guaranteed by any effective method." A 2026 preprint
(arXiv:2606.04834, thinly verified — abstract only) formalizes the
positive shape: approximate MDL keeps its prediction guarantees iff the
optimization slack is a FIXED additive bound independent of n. Krimp
offers no consistency theorem for its greedy search; its justification
is empirical. Consequence, stated plainly: **this repo's strict-
decrease gate is an objective, not a statistical guarantee** — the
actual overfitting protections are the exogenous-witness floor, the
per-rung certificate batteries, and the REPORTED prequential column
(which empirically monitors exactly the failure the theory says is
possible), and the doc must never claim the DL gate alone inherits
MDL's protection. If a bounded-slack argument for the beam search is
ever wanted, 2606.04834's condition is the shape it must take.

**The dictionary-vs-context question, answered empirically on our own
corpus (reviewer-reproduced to the last digit).** `tools/ppm_ref.py`
runs honest ADAPTIVE order-k coders (KT and Laplace — sequential,
paying full learning cost; the prequential version of the order-k
lines) on the committed structure stream. Result: adaptive order-0
loses to the macro coder (2511 > 2139 — pure learning cost), but
**adaptive KT order-1 codes the stream at 1514.5 — beating corpus_dl
2139 by 624 units** (order-2 regresses to 1647.6 under context-learning
costs but still wins). So the plug-in mirage was real (800/409 are not
achievable), yet genuine order-1 sequential structure exists that the
macro vocabulary leaves on the table. Consequences: (i) the corpus's
statement-internal token SEQUENCE carries structure that
window-recurrence mining does not capture — this is the first measured
argument FOR C2 (an entropy-coded data-bits currency would harvest it)
and it upgrades C2 from "deferred pending a mispricing instance" to
"deferred with a measured 624-unit exhibit on file"; (ii) per §10.2's
verified theory this is the expected regime interaction — context
models win where sequential predictability dominates; the macro coder's
edge is the certified, reusable, semantic vocabulary, which a context
model cannot provide; (iii) the admission gate does NOT change — the
exhibit argues for a reported C2 experiment, nothing more.

Open questions worth a future sweep:
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

## 11. The sweep (adversarial pre-implementation review; binding re-specs)

Six independent reviewers, one failure axis each, all grounded in the
shipped tree — several reproduced the committed run wave-by-wave
(369/744/1238/1646/2139 replayed exactly) or executed the real battery
in a scratch registry before claiming anything. What follows is the
consolidated verdict; where §8's text and this section disagree, this
section wins.

### 11.0 Pre-existing repo bugs the sweep surfaced (independent of the plan)

These exist today and should land as their own small fixes before any
rung work:

- **B1 — `-`-carrier divergence between mirrors.** `math_eval`'s
  subtraction carrier is decided by the FIRST ref in pre-order
  (`math_eval.py:86-92` + `:117-121`), so it is argument-ORDER-sensitive;
  `math_smt._minus_carrier` is any-Nat-operand ⇒ Nat — order-insensitive.
  On mixed-carrier readings with no ambient the two channels can
  disagree today (`(n + b) - 5 = 0` at `n=0,b=0`: eval True via Nat
  truncation, reorder the sum and it turns Int/False), and the validator
  does not enforce the docstring's shared-carrier assumption. Fix: gate-
  time refusal of mixed-carrier `-` without ambient, or align the eval
  carrier rule with the mirror. *(Landed as gate-time refusal; 0
  committed readings affected. The reviewer then falsified this entry's
  own premise: declaring an ambient does NOT align the eval carrier —
  eval falls back to ambient only when no ref carries a type, while the
  SMT mirror lets ambient win unconditionally, so the with-ambient
  mixed-carrier case is a LIVE residual divergence (confirmed: n:Nat,
  b:Int, ambient Int, `n − b` → eval Nat-truncates, SMT computes Int).
  Follow-up **B1-A**: align eval's ambient precedence with the mirror,
  or extend the refusal to first-ref-carrier ≠ ambient.)*
- **B2 — term-level mod-by-zero mirror gap.** `math_eval` totalizes
  `x % 0 = x` (Lean convention, `math_eval.py:123-127`); `math_smt`
  renders raw `(mod x y)` (`math_smt.py:124-126`) where SMT-LIB behavior
  at 0 is unconstrained — the module already guards `dvd` with an `ite`
  but not term `mod`. Reproduced: the battery refuses a sound
  `congm(a,b,m)` row with `enum=False but z3=sat` at `m=0`. Fix: emit
  `(ite (= y 0) x (mod x y))` in the ground SMT. *(Landed; every
  emission seam covered; the congm refusal reason is gone. Reviewer
  residual **B2-A**: the NEGATIVE-divisor convention gap (Python `%`
  sign-follows-divisor vs SMT-LIB Euclidean; 16 divergent cells on the
  [−4,4]² grid) remains — masked in same-divisor congruence equalities
  (48-instance battery: 0 disagreements incl. 6 negative-m), live for
  raw `mod(x,y)`-vs-literal readings with variable negative divisors.
  Close or document before any reading of that shape enters the
  corpus.)*
- **B3 — `exists` is silently evaluated universally.** The compiler
  emits a real `∃` (`math_compile.py:242`) but `math_eval` and
  `math_smt` have no quantifier handling at all — an exists-bound
  object is enumerated like any other. Compiled-Lean and the eval
  mirror already diverge on any exists-reading, with no tripwire on
  that axis. (This is why the `28_predecessor` workaround exists.)

### 11.1 WP-P1 — proceed, re-specified

- The column is **counting prequential**: per wave, the sum of
  `dl_reading` for the wave's new exogenous readings under the PRE-wave
  frozen table, snapshotted before `_greedy_grow` runs (the natural
  implementation site receives the post-mine table and silently yields
  hindsight — a vacuous column both planned teeth pass). It is NOT
  −log p; that name stays reserved for C2. Consider
  `prequential_counting_dl` as the column name.
- Teeth are per-arm: governed `hindsight ≤ prequential` is genuinely
  by-construction; on the ungoverned arm the inequality is FALSE in
  general (a dream-witnessed macro charges exogenous model bits with
  zero exogenous savings) — reported only, with the divergence named in
  the honesty block as the governance effect itself. Add an
  anti-vacuity tooth: strict `>` on a multi-wave fixture where mining
  admits mid-run. The existing flood fixture is single-wave —
  prequential provably ties on it; a ≥2-wave planted fixture is required.
- Persist per-wave frozen TABLES (bodies, not the names-only
  `table_hash`) so the committed-run tooth survives WP-T1/T3 changing
  the miner; backfill the committed checkpoint once, verified against
  the recorded hashes.
- Reword C1's "origin-blind": the scorer is blind over a fixed
  exogenous stream; corpus membership is origin-aware by design.
- Mechanical: CSV column appended at END + schema test updated in the
  same change; m9 sqlite needs an idempotent `ALTER TABLE` guard; the
  m9 iteration snapshot already exists (`LedgerSnapshot.macro_table`).

### 11.2 WP-T1 — measurement-gated; three blockers before any build

- **Blockers:** (i) `_expand_macros` is single-pass — a level-2 body's
  invocations reach the LF-kind gates unexpanded and throw BadReading;
  needs recursive expansion + cycle/depth guard at `macro_add`, and the
  1..60 statement cap re-pinned as transitive. (ii) Pricing's greedy
  rewrite cannot match tower bodies at all (uses=0 forever) — and fixing
  it changes `dl_reading`, which is simultaneously the ledger law, the
  FI-2 serve gate, and the mining objective; the flat-table equivalence
  pin must land before the rewrite does. (iii) The H3 concreteness
  filter rejects invocation templates by construction (concrete-leaf
  fraction 2/(2+k) < 0.6) — tower LGGs are filtered before pricing.
- **Economics:** under the real currency a level-2 macro needs ~7–10
  witnesses to pay, not 2. GATE: run the one-script census (adjacent
  invocation-pair recurrences on the rewritten committed corpus with
  witness counts) FIRST; if nothing clears the bar, the rung has no
  admissible occupant on live data and the package is deferred, tooth
  and all.
- Also binding: fold the invoked name into the cluster key and
  hard-reject `$` in name position (else LGG mints callee-as-argument
  macros — dynamic dispatch, unpriceable); mine BOTH raw and rewritten
  streams and let the gate arbitrate (else admitted macros permanently
  blind the miner to better flat candidates); GC ablation trials become
  dependency-closed groups; the byte-identity pin re-scopes to (admitted
  set, DL trajectory, ledger CSV).

### 11.3 WP-T3 — premise false; re-scoped

- Operators are scalar leaves under an `"op"` key, so plain first-order
  LGG already generalizes them: the committed 2139 table contains
  `m_83b0ad76bcb0` with `$p0` bound to `even`/`odd` AT the op position.
  "Higher-order AU" was a phantom requirement; §10.7's citation gap is
  closed by representation.
- The real blockers the package re-scopes to: (i) the congruence triple
  yields ZERO windows — `_demand_windows` requires uniform (force,
  quote) and the three readings differ in quote text; relaxing this
  touches the H2 realizability rule and must be its own designed,
  priced decision. (ii) Math readings have NO macro invocation syntax
  (`parse_math_reading` never expands macros) — every mined math macro
  is today a pricing fiction with no authorable surface; either land the
  surface or state the fiction openly in the currency's docs.
- Measured: with windows fixed, today's AU admits the slotted
  congruence body at **−179** (2139 → 1960); the per-op flat variants
  are inadmissible (uses=1). The gain books to window relaxation, not to
  any new AU machinery — split the teeth accordingly.
- What survives as T3 proper: slot TYPING as an honesty restriction —
  slots ranging only over (role, arity, carrier-support)-compatible ops
  (an Int-mined body must not match Nat where `-` flips meaning; today
  macro admission runs no semantic battery). Slot pricing beyond 1
  token (log₂|vocab|) is a currency change → reported-first discipline.

### 11.4 WP-T4 — proceed after two criticals and one resequencing

- **Critical 1:** the battery admits pure aliases (`divides_alias :=
  dvd(a,b)` gets a green cert) and operator rows are priced NOWHERE
  (neither `ledger_dl` nor `corpus_dl` knows them) — unbounded free
  vocabulary, against the admission law. Fix: an operator analogue of
  `macro_admission_decision` (strict corpus-DL drop, model bits charged)
  plus trivial-alias refusal, both inside `admit_operator`.
- **Critical 2:** the plan's headline tooth is red on day one — the
  mechanical lift of `mod(x,m)=mod(y,m)` is REFUSED via B2 (mod-by-zero
  mirror gap). Land B2's fix first; separately the corpus's guard
  convention (`0 < m` as a sibling statement) means mechanical lifts
  can't import guards — the miner lifts only self-contained subtrees.
- Same-word re-admission is last-writer-wins and rewrites the meaning of
  already-certified corpus bytes with no re-certification: the
  autonomous path must be append-only (refuse existing word with
  different digest), and the operator-registry digest joins the wave
  provenance (`table_hash` covers macros only today).
- `save_admitted` trusts its caller (docstring-enforced): make it re-run
  `admit_operator` and require cert-id equality — admission is
  deterministic and costs 0.06–4.6s, so sole-admitter becomes a
  property, not a convention.
- **Measured yield:** after alias-exclusion the real corpus offers ~1
  non-trivial candidate; the valuable recurrences are cross-statement
  (macro-layer territory) or hidden by byte variation. RESEQUENCE:
  T4 lands after T6a canonicalization raises visible recurrence, and
  the census re-runs then. The feed-to-T1/T3 loop needs its mechanism
  named: prompt-side operator vocabulary (deferred-DL, priced as prompt
  bytes) or a corpus rewriter — which is a T6a-class lowering.
- Flood economics at this scale are benign (≤21 proposals × ≤5s); no
  budget needed yet — the unpriced-admission hole (Critical 1) is the
  real economics gap.

### 11.5 WP-T6a — redesign the measure and the pilot before building

- Measure keys must be order-invariant (multiset-canonical child keys):
  the naive global inversion count makes commutativity-sort
  non-confluent (§6 amendment). Property test: random ASTs × random arg
  permutations → identical normal forms across each orbit.
- The rule fragment cannot express the pilot: n-ary arg sorting and
  hypothesis reordering enter as the two frozen engine primitives
  (§6 amendment); hypothesis-sort additionally is NOT a pred rewrite —
  it permutes the statements list and would drag statement ids,
  provenance keys, and probe ids with it; the pilot descopes it to
  compiled-order only or defines an id-stable list sort.
- B1 lands before the rung (else every mixed-carrier lowering is a
  mirror-divergence storm) and pilot rules restrict to the syntactic
  class with a META-equivalence argument (arg permutations of
  {+,*,and,or,=,!=}), because the per-lowering channels are weak
  exactly here: instance replay is vacuous for permutations (the
  evaluator is symmetric by construction) and the solver channel is
  absent for the enum-only gcd/coprime cluster — the pilot's
  motivating statements. Unknown/timeout ⇒ not lowered, tier recorded.
- Canonicalization is a VIEW: store, certs, goldens, authored bytes stay
  raw; `canon(reading)` applies inside `_reading_stats`/`mine`/
  `gc_macros`/the FI-2 price only. The rung-free pin becomes "empty
  registry ⇒ view = identity". Norm-cert subject = RAW statement hash,
  claims carry `canonical_form`; new contract stanza + allowlist entry
  before code.
- The rung MDL gate needs a pinned counterfactual: profit = [searched
  DL on canon view] − [searched DL on raw], same initial table, rung
  bits (priced via `_leaf_count` over rules) charged to the canon side.
  Second tooth: a rung over a recurrence raw mining already finds is
  REFUSED (anti-gaming). Vacuity is per-RULE with the 2-exogenous-
  witness discipline; rung-GC mirrors `gc_macros`.
- Composition: rungs apply in admission order, full sequence iterated
  to joint fixpoint, driver restarts at root after every accepted
  rewrite; global order finitize-then-canonicalize under one global
  lexicographic measure `(quantifier_count, disorder)`; a
  `rung_pipeline_hash` stamps statement provenance and the
  formalize-cache key. Include flatten rules in the pilot and make the
  tooth's plant use mixed nesting + mixed arg order.

### 11.6 WP-T6b — unsound as written; re-specified as an eval-channel rung

- NEVER rewrite the compiled statement: `∀n:Int, ⋁_{m=-B..B}(m+1=n)` is
  FALSE (n = −8 at B = 8), yet the k=5-smallest instance mask samples
  {0,−1,1,−2,2} and the cert goes green with the bound recorded nowhere
  — a silent redefinition of "certified". The rung finitizes the EVAL
  channel only: `∃` stays in `lean_text`; `satisfying_instances` gains
  an ∃-aware mode (disjunct over the bounded range per outer
  assignment); the cert gains a declared
  `{"backend": "exists-finitized-enum", "bound": B, "role":
  "bounded-shadow"}` fidelity channel. B ≡ the runtime `bound`
  parameter — never baked into bytes; the rung-spec hash joins the
  cache key.
- §6 gains a second rung class: **reach-rungs**, admitted on a coverage
  tooth + witnesses + vacuity, with corpus-DL effect reported beside —
  finitization strictly INCREASES corpus DL (~17× on the conclusion's
  leaves), so pushing it through the compression gate is either
  auto-refusal or currency mixing; naming the class resolves the
  plan-internal contradiction.
- Witnesses: the certified corpus has 82 `forall` and ZERO `exists`
  binders — commit 1–2 exogenous exists-sources to `specs/mathsources/`
  before the wave, or the rung cannot satisfy vacuity/witness clauses
  without manufacturing its own evidence.
- The tooth: re-author `28_predecessor` with `binder:"exists"`, assert
  it certifies AND its `lean_text` contains `∃` — that, not a byte
  rewrite, is what dissolves the workaround (whose witness-term version
  is extensionally TRUE everywhere; the finitized bytes would be false
  outside the bound — strictly worse). Note the workaround also
  silently resolved the manifest's ambient-ambiguity to Int; the
  re-authoring owes that decision explicitly.
- Tripwire: same-statement witness dedup in the miner (a finitized
  statement is B+1 near-identical disjuncts of fake recurrence);
  examiner divergences outside the bound bin separately.

### 11.7 Wave 1 and process — pre-registered or it is theater

- Pre-register the gate predicates NOW, per deferred item (e.g. "T2
  proceeds iff the post-T1/T3 residual gap to the LZ77-proxy line
  exceeds X% of corpus_dl"). On a 37-reading corpus every ΔDL is exact
  in-sample arithmetic with zero generalization power — fine for
  "is the window space mined out on THIS corpus", meaningless for
  anything meant to generalize; claims of the second kind need the
  committed holdout source set (~20 readings) or stay unmade. The cost
  axis is VOID on the committed run (unmetered inline authoring) and
  gates nothing until a metered run exists.
- Ownership matrix before any builder starts (the F-INT discipline §8
  cites and then skipped): true wave-0 width ~3 — P1 (bench), T1
  (miner/pricing), T6a (interpreter + view) — with T6a→T6b, T1→T3
  strictly serial, T4 after both the miner interface freeze and T6a.

### 11.8 Wave-1 gate predicates — pre-registered against the census

Registered BEFORE any wave-1 builder starts, per §11.7. The census
artifact (`results/tower_census.json`, byte-pinned, hash-verified
against the committed checkpoint) is the measurement of record; numbers
quoted here are its.

- **T1 (macro tower): DEFERRED** *(corrected after the census review
  round).* Predicate: ≥1 adjacent macro-macro pair with ≥7 exogenous
  witnesses on the rewritten governed corpus, counted under the miner's
  own H2 realizability rule (a level-2 body must span a uniform
  (force, quote) region — an invocation expands with one inherited
  force+quote). The tool's first release counted RAW adjacency and
  reported 14; the per-package review caught the metric as
  measurement-invalid — all 14 straddle a presupposition/demand
  boundary. Corrected: **realizable max = 1, zero pairs ≥ 7**. The
  rung has no admissible occupant on this corpus; T1 re-enters via a
  future census (e.g. post-canonicalization, or after the staged
  sources promote). The raw count is retained in the artifact as a
  labeled non-gate column, and the invalid-then-corrected sequence is
  kept in this entry deliberately — it is the review discipline's
  receipt.
- **T3 (window relaxation + slot honesty): PROCEEDS.** Predicate: the
  one-slot congruence body admissible with strict DL decrease against
  the final governed table. Measured: **−179** (2139 → 1960), admit
  True, uses 3; `_demand_windows` = 0 on all three readings (the
  blocker is the window rule, committed as a number). Design decision
  frozen in §11.9.
- **T4 (subtree → operator proposals): PROCEEDS AFTER B2 + pricing
  gate.** Predicate: ≥3 non-alias recurring subtrees at ≥2 exogenous
  witnesses. Measured: **4 exact-byte / 6 ref-abstracted** (top:
  `=(mod(a,m),mod(b,m))` at 4 witnesses — refused today only via the
  B2 mirror gap). Build order: after B2 merges and the §11.4 operator
  pricing gate is specced into `admit_operator`; re-census after T6a
  canonicalization before widening scope.
- **T6b: PROCEEDS** (eval-channel re-spec, §11.6) once WP-SRC lands
  ≥2 exogenous exists-sources — its witness clause is satisfied by
  corpus, never by manufactured readings.
- **T2 (gapped windows): DEFERRED** unless the post-T1/T3 re-census
  finds zero admissible contiguous candidates remaining AND ≥2 gapped
  idioms (one-statement interruptions) each with ≥2 exogenous
  witnesses in the real corpus. Both clauses relational, both from the
  re-census artifact.
- **T5 (grammar-induction generator): DEFERRED** until T2's predicate
  is even evaluable (it presupposes the contiguous space is mined out).
- **C3 (order-k reference lines): no gate** — reported plot lines, no
  machinery admitted; land with any bench change.
- **C2/C4 (entropy-coded / NML currency): DEFERRED** unless wave 1
  produces a recorded instance of the counting currency mispricing an
  admitted structure (a concrete case, in the honesty block, not a
  vibe). The §10.3 misspecification result already fixes the gate's
  SHAPE (two-part); these stay reporting experiments.
- **Cost headline: remains X15-deferred** until a metered authoring
  run exists; nothing in wave 1 may cite the VOID columns.

### 11.9 Wave-1 frozen interfaces (written before code, per §11.5)

**FI-W1-1 — norm-cert contract stanza.** Subject = the RAW statement's
hash (the store, ledger, and audit chain keep keying on raw bytes).
`claims` carries `("canonical_form", <canon_hash>)` plus the rung
pipeline identity `("rung_pipeline", <rung_pipeline_hash>)`. Channels,
in order: (1) meta-equivalence class tag — the pilot admits only
rewrites in the argued-safe syntactic class (arg permutations of
{+,*,and,or,=,!=} and same-op flatten), named in the cert; (2) solver
equivalence raw ≡ canon when the fragment supports it — `unknown`/
timeout/enum-only ⇒ the statement is NOT lowered (raw survives, tier
recorded honestly); (3) entailed-instance replay as corroboration,
recorded with the acknowledgment that it is vacuous-by-symmetry for
permutation rewrites. New contract type ⇒ `CERTS_VERSION` bump + the
contract-allowlist entry in the same commit as the schema, before any
producer code.

**FI-W1-2 — canonicalization is a view.** One pure function
`canon(reading) -> reading` (rung pipeline applied to a COPY). Exactly
four call sites: `_reading_stats`, `mine`, `gc_macros`, and the FI-2
serve-price computation. Store, certs, goldens, authored bytes,
prompts: raw, always. Pin: empty rung registry ⇒ `canon` is identity ⇒
miner/pricing byte-identical (this is the rung-free pin's concrete
form). `rung_pipeline_hash` joins the formalize-cache key and wave
provenance the moment the registry can be non-empty.

**FI-W1-3 — the T3 window decision.** The quote-uniformity rule splits
by domain, aligning mining with what pricing already does:
- Service readings (which have a real macro invocation surface and the
  H2 one-quote-per-invocation realizability constraint): windows keep
  uniform-(force, quote). Byte-identity pin on all service-side mining.
- Math readings (which have NO invocation surface — mined math macros
  are a codebook for pricing, not an authoring feature): windows
  require force-uniformity only; quotes are carried as per-statement
  metadata on the window, never matched on. Rationale: `mdl_macros`
  pricing is already force/quote-blind (the §11.2 review's F8
  asymmetry), so this makes the miner see exactly what the currency
  prices; H2 realizability is moot where invocations cannot be written.
  The codebook status must be stated in `dl.py`'s docs in the same
  commit ("math macros are a pricing vocabulary; no authoring surface
  exists" — the §11.3 honesty condition), and it is revisited if a math
  invocation surface ever lands.
- Slot typing rides the same package: a `$`-param at an op-key position
  is legal only when every witnessed binding shares (role, arity,
  carrier-support) per the `math_reading.py` single-source tables;
  slot pricing stays 1 token for now with the log₂|vocab| re-pricing
  registered as a reported-first experiment, not a change.

### 11.10 Wave-1 execution record (what actually happened)

Every §11 package above was built, adversarially reviewed, and merged
or held during wave 1; this is the record, kept because several §11
entries above describe intentions this section supersedes.

- **§11.0 residuals: ALL CLOSED.** B1/B2/B3 landed (WP-B), then the
  review-found residuals landed too (WP-B-RES): eval's `-` carrier is
  now ambient-wins, node-identical to the SMT mirror (the divergent
  no-ambient shape stays gate-refused; the Lean leg defers to the CI
  lean job); term mod implements Python's convention exactly for ALL
  divisors (formula independently re-derived, [-12,12]² zero
  mismatches, both solvers; 0 committed verdict changes). One named
  latent residual remains on file: ambient ≠ coercion-join shapes
  (0/17 committed nodes affected).
- **§11.1 (P1): LANDED as specced.** Headline: the origin-blind
  counting-prequential column ranks governed 2336 < ungoverned 2459 on
  data bits alone — the governance effect is not an accounting
  convention.
- **§11.2 (T1): DEFERRED by its own corrected gate** (realizable max
  MM pair = 1 vs the ≥7 bar; the raw-14 was H2-unrealizable inflation
  caught in review).
- **§11.3/FI-W1-3 (T3): SPLIT by adjudication.** Slot typing landed
  (role/arity/carrier-support admissibility via
  `math_reading.op_signature`; ±0 DL, service mining byte-identical).
  The force-only window rule was HELD: as built it REGRESSED governed
  DL 2139 → 2168 (force-only merges the (hyp,hyp) cluster 6→15 past
  the H3 concreteness floor, losing the even/odd macro; the −179 stays
  counterfactual on the greedy path). Follow-up package: a cluster-key
  design; starting evidence on file — a role-skeleton key prototype
  reached 2060 with 13 micro-macros, below baseline but short of the
  ~1989 counterfactual. Until then the zero-window blocker stands and
  the −179 remains unharvested.
- **§11.4 (T4): LANDED in two halves.** T4a: the pricing gate
  (admit iff saving > model_bits AND ≥2 witnesses; trivial-alias
  refused pre-battery; save_admitted re-runs admission — sole admitter
  by construction; append-only registry; pricing-corpus digest stamped
  as evidence). On the real corpus: congm ADMITS at Δ−116; even_sum
  honestly refuses at +4; the committed multiple_of row is
  grandfathered (re-batteries green, alias-refused under the new gate).
  T4b: the subtree miner — 18 deterministic, inert, provenance-stamped
  proposals staged (4 non-alias incl. the sharing-preserving congruence
  form at 4 witnesses; aliases emitted-with-flag). The proposed→admit
  wiring deliberately does not exist yet.
- **§11.5/§11.9 (T6a): CORE LANDED** (kernel/rung.py under the amended
  law, one-sitting kernel review + arity-validation fix, 25 property
  tests) and **FI-W1-1 LANDED** (norm-cert contract, CERTS_VERSION 11,
  schema-only, refuse-by-construction verified). Integration (canon
  view, norm-cert producer, the corpus_dl_canon reported-first column)
  is the wave's remaining serial package.
- **§11.6 (T6b): still gated** — the exists-sources are committed but
  STAGED; promotion needs two human waivers (43 provenance, 44 NC
  license) or citation fixes, via tools/promote_sources.py.
- **References landed beyond plan:** LZ77/order-k floors
  (tools/entropy_refs.py — T2's gate metric measured: gap 285.5,
  13.3%), the adaptive PPM comparator (tools/ppm_ref.py — KT order-1 at
  1514.5 beats corpus_dl: C2's measured exhibit), the deterministic
  entropy-stack figure, and the promotion tool.
- **Process receipts:** one CI-caught cross-package break (carrier
  search vs B1, fixed as evidence-entries); one review-caught
  measurement-invalid gate metric (census realizability); one
  adjudicated regression prevented from becoming the committed
  baseline (T3 window rule); one literature correction overturned by a
  primary-source second vote (Hipster doubling). The two-gate
  discipline caught every one of these before it shipped.

### 11.11 Wave-1 tail: the machinery is in; the corpus said no (for now)

- **T6a-INTEGRATE landed** (after its first builder died mid-package and
  a resumed builder inventoried, fixed one load-bearing half-wired seam,
  and finished it): the rung registry, the `canon()` view at exactly
  four seams (identity on the empty registry — pinned), the norm-cert
  producer with single-sourced dispatch identity, and the admission
  gate with the pinned counterfactual and anti-gaming teeth. **The
  pilot canonicalization rung was REFUSED on the real corpus**: 64/66
  rules fire on <2 readings, and the counterfactual profit is exactly
  0.0 against 2748 rung model bits — the counting currency is
  order-blind and the miner clusters by LF-kind, so commutativity
  normalization exposes no recurrence this coder can price. The rung
  stays proposed with the numbers as evidence; the engineered-rung test
  proves the gate can admit (net −61 on a planted corpus). Taken with
  the T3 window verdict (§11.10) and the KT order-1 exhibit (§10.7),
  the empirical picture is consistent: **this corpus's remaining
  headroom lives in sequential/statement-internal structure, not in
  window-visible or order-normalized recurrence** — the C2 experiment
  and corpus growth are the live leads; T2 remains correctly deferred.
- **T6b-MACHINERY landed** (review-fixed): honest bounded-shadow ∃
  evaluation — exhaustive hypothesis-admitted outer sweep, full bounded
  inner product (no k-smallest anywhere near a disjunction),
  conservative bound-edge policy (over-refuses, never false-greens),
  bound in the cache key never in bytes, a combinatorial ceiling with a
  named honest skip, SMT declared enum-only, real `∃` preserved in
  `lean_text`, committed corpus byte-inert. The 28_predecessor
  dissolution now waits only on promoted existential sources.
- **Figures are re-baseline-coupled artifacts**: `entropy_stack.png`
  (full reference stack incl. adaptive-KT bars and the C2-exhibit
  annotation) and `dl_trajectories.png` (the two-currency governance
  readout) regenerate from committed JSON/CSV with byte-determinism
  tests; a re-baseline that forgets them fails CI.

### 11.12 Promotion executed — the corpus is 51

All 11 staged sources promoted with ZERO waivers (both blockers had
been fixed by citation repinning, the proper path); the `existential`
axis joined VALID_AXES as a recorded pin change; the non-transcribable
quota moved 3→4 (Goldbach, sharing 38's `operator:prime` miss). The
committed 40-source run stays frozen and byte-identical; the live
corpus is 51 with 11 unauthored sources (live coverage 37/51 until the
next authoring run). T6b's witness clause (§11.6) is now satisfied from
`files[]`. The next authoring run — a separate, gated, priced step —
authors exactly the 11 new sources and resumes the frozen 40.
