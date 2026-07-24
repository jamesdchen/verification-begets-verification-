# Entropy reference floors (C3) — committed governed corpus

Computable reference lines for the structure-token stream the counting DL implicitly uniform-codes. Orientation references, **not floors** for the macro coder (§10.2).

## Stream

| quantity | value |
| --- | --- |
| certified governed exogenous readings | 110 |
| stream length N | 3065 |
| alphabet size \|A\| | 67 |
| uniform bits/token log2\|A\| | 6.066089 |
| naive counting DL (empty table) | 8287.0 |

## Scaling convention

> DL_ref = naive_counting_dl * (bits_per_token_ref / log2|A|); order-k uses bits_per_token = H_k, LZ77 uses bits_per_token = z*(log2 N + log2|A|)/N. Ratio-reconciled, no tuned constants (mirrors bench_formalize._order0_entropy_dl_est).

## The measured stack

| reference | bits/token | DL (counting units) |
| --- | --- | --- |
| corpus_dl (reported, learned macro table) | — | 6663.0 |
| order-0 (memoryless) | 5.019249 | 6856.892 |
| order-1 | 1.966557 | 2686.551 |
| order-2 | 1.046587 | 1429.762 |
| LZ77 parse proxy (z = 739) | 4.255039 | 5812.89 |

**Residual gap (T2, §11.8):** corpus_dl − LZ77_proxy = 6663.0 − 5812.89 = **850.11** (12.759% of corpus_dl).

## Context-count statistics (small-sample hazard)

Order-k plug-in entropy is optimistically low where contexts are seen rarely: a context observed once predicts its successor with probability 1 (0 bits). These counts let the order-k lines above be read for what they are.

| order k | distinct contexts | singleton contexts | singleton fraction | predictions from singletons |
| --- | --- | --- | --- | --- |
| 1 | 67 | 5 | 0.0746 | 5 / 3064 (0.0016) |
| 2 | 447 | 185 | 0.4139 | 185 / 3063 (0.0604) |

> IN-SAMPLE PLUG-IN ESTIMATE. H_k (k >= 1) are empirical maximum-likelihood conditional entropies with NO smoothing; the plug-in estimator is downward-biased (optimistic) at N = 3065 tokens. A context seen once predicts its successor with probability 1 (0 bits): here 185/447 (41.4%) of order-2 contexts are singletons, so DL2 in particular is an OPTIMISTIC orientation line, NOT an achievable floor. Per §10.2 the achievable dictionary/grammar-coder cost carries an additive Omega(|S| k log sigma / log_sigma|S|) redundancy term absent from these plug-in lines. The T2 gate (§11.8) reads against the LZ77 proxy, never against the order-k lines.

## Order-0 consistency check

Committed CSV order0_entropy_dl_est = 6856.892; recomputed = 6856.892; match = **True**.

## Caveat

> References, not floors. Per COMPRESSION.md §10.2: on highly repetitive corpora (plausibly ours) grammar coders can encode far *below* nH_k -- which is exactly what the bench measured (2139 < 2450 order-0). A corpus_dl below an order-k line is expected. In-sample, hindsight, zero generalization power on a 37-reading corpus (§11.7).
