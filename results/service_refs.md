# Service-domain reference stack (C3) — committed service readings

The measured compression story for the SECOND domain the shared miner/macro-table serves: the hand-authored **service** readings under `specs/readings/`. The math-domain stack lives in `entropy_refs` / `ppm_ref`; this is its service twin. Orientation references, **not floors** (§10.2).

## Corpus & token stream

> **Corpus.** The 11 top-level specs/readings/*.json readings are the REAL, exogenous (request-byte-matched) service Readings cgb._seed_readings certifies — the service analogue of the math stack's governed/certified/exogenous filter. dream/ anchors are SYSTEM-origin (S5) and excluded, as the math stack excludes the dream arm.

> **Tokens.** Per statement: ('kind', lf.kind), ('force', force), then a sorted-key tree walk of the rest of the lf emitting one token per scalar leaf tagged by its reaching field key (dict recurses over sorted keys; list emits each element under the same tag). The faithful service adaptation of bench_formalize._structure_tokens' philosophy over the DISJOINT service LF fragment (which that math-tuned extractor would silently drop). Deterministic.

> **Macro table.** FRESH mine via recurrence.searched_macro_sequence (no committed artifact carries a live service macro table; registry.sqlite has zero macros). The reported corpus_dl is recomputed here, not a frozen checkpoint value.

| quantity | value |
| --- | --- |
| real exogenous service readings | 11 |
| stream length N | 418 |
| alphabet size \|A\| | 144 |
| uniform bits/token log2\|A\| | 7.169925 |
| naive counting DL (empty table) | 770.0 |
| corpus_dl (fresh mine, 1 macro) | 691.0 |

## Scaling convention

> DL_ref = naive_counting_dl * (bits_per_token_ref / log2|A|); order-k uses H_k, adaptive uses total_adaptive_bits/N, LZ77 uses z*(log2 N + log2|A|)/N. Ratio-reconciled, no tuned constants (identical to entropy_refs / ppm_ref / _order0_entropy_dl_est).

## The measured service stack

| reference | bits/token | DL (counting units) |
| --- | --- | --- |
| corpus_dl (fresh macro table) | — | 691.0 |
| order-0 plug-in (memoryless) | 6.097047 | 654.78 |
| order-1 plug-in | 1.319526 | 141.708 |
| order-2 plug-in | 0.68639 | 73.714 |
| **adaptive KT order-0** | 6.642561 | **713.365** |
| **adaptive KT order-1** | 6.147861 | **660.237** |
| **adaptive KT order-2** | 6.697828 | **719.3** |
| adaptive Laplace order-1 | 6.396991 | 686.992 |
| LZ77 parse proxy (z = 263) | 9.989774 | 1072.832 |

(Adaptive DL > plug-in DL_k at each k is expected — the plug-in line does not pay the learning cost the adaptive coder does.)

## Context-count statistics (small-sample hazard)

| order k | distinct contexts | singleton contexts | singleton fraction |
| --- | --- | --- | --- |
| 1 | 144 | 98 | 0.6806 |
| 2 | 261 | 230 | 0.8812 |

## Math ↔ service, side by side (DL in counting units)

| line | MATH (number theory) | SERVICE |
| --- | --- | --- |
| readings / N / \|A\| | 78 / 2297 / 62 | 11 / 418 / 144 |
| naive counting DL | 6156.0 | 770.0 |
| corpus_dl (macro coder) | 4897.0 | 691.0 |
| plug-in DL0 / DL1 / DL2 | 5050.197 / 1875.532 / 1001.987 | 654.78 / 141.708 / 73.714 |
| adaptive KT DL0 / DL1 / DL2 | 5142.172 / 3174.836 / 3543.057 | 713.365 / 660.237 / 719.3 |
| LZ77 proxy DL | 4107.132 | 1072.832 |

## Headline — the profile question

**Does the service domain show the same order-1-sequential-structure surplus math did?**

Best honest adaptive coder: **KT order-1** at DL = **660.237** (-30.763 vs corpus_dl 691.0). Any adaptive order-k beats corpus_dl: **YES**.

Order-1 surplus (how far the best adaptive order-1 coder undercuts corpus_dl): **service 4.452%** vs **math 35.168%**.

> Service shows a DIFFERENT profile: the best honest adaptive order-1 coder undercuts the macro coder's corpus_dl by only 4.452% vs the math domain's 35.168% — no large order-1 sequential-structure surplus. The service stream's large, sparse alphabet (many per-service referent names/literals) leaves order-1 contexts mostly singleton, so the adaptive context model pays heavy learning cost and barely improves on the macro/grammar coder.

## Caveats

> IN-SAMPLE, single 11-reading corpus, hindsight; zero generalization power (§11.7).

> The plug-in H_k lines are maximum-likelihood entropies that pay NO learning cost and are downward-biased. Here 98/144 (68.1%) order-1 and 230/261 (88.1%) order-2 contexts are singletons (predict their successor at 0 bits), so DL1/DL2 are OPTIMISTIC orientation lines, NOT floors.

> KT / Laplace are STANDARD estimators, not the best possible context model (no PPM escape, no cross-order mixing, no CTW). References, never floors (§10.2).
