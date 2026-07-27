# Entropy reference floors (C3) — committed governed corpus

Computable reference lines for the structure-token stream the counting DL implicitly uniform-codes. Orientation references, **not floors** for the macro coder (§10.2).

## Stream

| quantity | value |
| --- | --- |
| certified governed exogenous readings | 120 |
| stream length N | 3264 |
| alphabet size \|A\| | 71 |
| uniform bits/token log2\|A\| | 6.149747 |
| naive counting DL (empty table) | 8830.0 |

## Scaling convention

> DL_ref = naive_counting_dl * (bits_per_token_ref / log2|A|); order-k uses bits_per_token = H_k, LZ77 uses bits_per_token = z*(log2 N + log2|A|)/N. Ratio-reconciled, no tuned constants (mirrors bench_formalize._order0_entropy_dl_est).

## The measured stack

| reference | bits/token | DL (counting units) |
| --- | --- | --- |
| corpus_dl (reported, learned macro table) | — | 7152.0 |
| order-0 (memoryless) | 5.054122 | 7256.868 |
| order-1 | 1.998266 | 2869.174 |
| order-2 | 1.061796 | 1524.56 |
| LZ77 parse proxy (z = 792) | 4.324498 | 6209.25 |

**Residual gap (T2, §11.8):** corpus_dl − LZ77_proxy = 7152.0 − 6209.25 = **942.75** (13.182% of corpus_dl).

## Context-count statistics (small-sample hazard)

Order-k plug-in entropy is optimistically low where contexts are seen rarely: a context observed once predicts its successor with probability 1 (0 bits). These counts let the order-k lines above be read for what they are.

| order k | distinct contexts | singleton contexts | singleton fraction | predictions from singletons |
| --- | --- | --- | --- | --- |
| 1 | 71 | 6 | 0.0845 | 6 / 3263 (0.0018) |
| 2 | 476 | 194 | 0.4076 | 194 / 3262 (0.0595) |

> IN-SAMPLE PLUG-IN ESTIMATE. H_k (k >= 1) are empirical maximum-likelihood conditional entropies with NO smoothing; the plug-in estimator is downward-biased (optimistic) at N = 3264 tokens. A context seen once predicts its successor with probability 1 (0 bits): here 194/476 (40.8%) of order-2 contexts are singletons, so DL2 in particular is an OPTIMISTIC orientation line, NOT an achievable floor. Per §10.2 the achievable dictionary/grammar-coder cost carries an additive Omega(|S| k log sigma / log_sigma|S|) redundancy term absent from these plug-in lines. The T2 gate (§11.8) reads against the LZ77 proxy, never against the order-k lines.

## Order-0 consistency check

Committed CSV order0_entropy_dl_est = 7256.868; recomputed = 7256.868; match = **True**.

## Caveat

> References, not floors. Per COMPRESSION.md §10.2: on highly repetitive corpora (plausibly ours) grammar coders can encode far *below* nH_k -- which is exactly what the bench measured (2139 < 2450 order-0). A corpus_dl below an order-k line is expected. In-sample, hindsight, zero generalization power on a 37-reading corpus (§11.7).
