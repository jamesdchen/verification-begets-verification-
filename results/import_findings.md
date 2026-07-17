# Import findings — the C6 wall and the macro-tower verdict (2026-07-17)

Two questions were put to the operation this session: *can it author the
Mathlib frontier?* (C6) and *is the repo actually compressing up the macro
tower?* Both were answered against committed evidence, not the docs'
self-description. Recorded here as first-class findings (record discipline;
cf. the §13 sweep's BUG-S1 on record/verdict divergence).

## Finding 1 — C6: the frontier does not author (stage-1 groundedness wall)

The A/B pilot ran the census frontier through the real metered path, both
arms. Result across 29 attempts: **0 authored, 22 refused, 7 fragment-miss**,
~64 ktok, halted by P-LI1-REFUSAL (the breaker working).

**Root cause (structural, arm-independent):** all 22 refusals are at
`run/formalize.py` stage 1, the groundedness gate, which requires every
demand/presupposition to *quote a span that literally occurs in the source
verbatim* (`generators/math_reading.py:11-12,410`). The import driver passes
`statement_pp` — a Lean formal string — as `source_text`
(`buildloop/import_driver.py:435`). That gate was designed for the NL corpus
("quote the English phrase that asserts this"); verbatim-quoting a *formal*
statement systematically fails. It is upstream of vocabulary, arm, and
mining. So §2's "direction flip" — meant to make import *stronger*-anchored
than NL — breaks the fidelity pipeline's first gate. Design-premise miss.

**Fix (tractable, trust-critical):** a formal-source groundedness variant —
the reading's atoms must correspond to *subterms of the Lean statement*
(a stronger, well-defined check) rather than verbatim NL spans. Touches a
trusted gate; must not be done unilaterally.

## Finding 2 — the macro tower has never compounded, and does not pay off

Verdict: **mechanism-only-no-payoff** generally; **not-even-attempted** on
imports. The machinery (mine → price → admit → reuse) runs and can lower an
in-sample counting-DL number, but:

1. **Depth-1 everywhere.** All 4 DL-admitted operators are priced against the
   *same* baseline `dl_before:1285.0` (`specs/mathsources/operators/admitted.json`;
   `results/proposal_admissions.json` `n_proposed:19 n_admitted:4`). A climbing
   tower would price operator *n*+1 against operator *n*'s `dl_after`. These are
   four parallel flat admissions, not a descending stack. No operator is
   defined in terms of another (depth>1 is buildable — `operator_growth.py:26,417`
   — never exercised).
2. **Level-2 measured and refused.** `results/tower_census.json`:
   `level2_witness_bar:7`, `macro_macro_pairs_at_or_above_bar:0`,
   `max_witness_macro_macro_pair:2`. The anti-unified congruence slot prices at
   **+7.0 bits**, `admit:False`.
3. **Unpriceable by construction.** `_expand_macros` is single-pass, so a
   level-2 body's invocations reach the gates unexpanded and throw; the greedy
   rewrite matches tower bodies with `uses=0` forever (`COMPRESSION.md:712-716`).
4. **Admissions cannibalize.** The one big win (congruence macro) flipped its
   marginal **−179 → +7** because later admissions stole its occurrences
   (`COMPRESSION.md:1123-1128`). New structure competes with old, not compounds.
5. **The honest currency says vocab costs bits.** `results/c2_report.md`:
   governed C2 = **2284.451** vs empty-table (no vocab) = **1918.678** → the
   vocabulary **costs +365.773 bits**. An adaptive KT order-1 coder codes the
   stream at **1514.5, beating corpus_dl 2139 by 624** (`COMPRESSION.md:591`).
6. **The one metered run lost.** `results/metered_evidence/`: governed DL
   **854 > 689** ungoverned; coverage **3 vs 8**; cost/certified **484 vs 55
   ktok** (~9×); `all_pass:false`. Real tokens spent → the vocabulary hurt.
7. **Import does no mining.** `import_driver.py:101,204` — straight authoring,
   empty macro table, `mining:none-in-driver` for both arms. Neither tower
   grows during import.

**The repo already knows this and says so.** §10.8 states the distinctive
claim is *not* "we compress best." §11.11's title is the accurate summary:
*"the machinery is in; the corpus said no."* This is the redeeming fact —
the instruments refuse to flatter the thesis.

## What this means for scaling to Mathlib

Even granting the tractable fixes (formal-source groundedness + wiring
mining), the repo's own math is discouraging: greedy vocabulary minimization
is NP-hard with no consistency guarantee (`COMPRESSION.md:387-389,576`), and
the well-formedness gate rejects the actual arithmetic — `+ - * mod gcd` as
top-level predicates are "unknown atom/connective"
(`results/proposal_admissions.json`) — so much of the shared structure in the
537 in-fragment statements is not even expressible as vocabulary. The
scaling premise (import → give the compressor room → the tower climbs) is not
supported by the evidence available before spending at scale.

**The import machinery still has standalone value** independent of the tower
claim: certified *translation* (the RT differential + kernel statement/proof
certs) is real, and does not depend on compression compounding. That is a
deliverable the evidence does support.
