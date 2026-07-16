# Entropy reference floors (C3) — committed governed corpus

Computable reference lines for the structure-token stream the counting DL implicitly uniform-codes. Orientation references, **not floors** for the macro coder (§10.2).

## Stream

| quantity | value |
| --- | --- |
| certified governed exogenous readings | 37 |
| stream length N | 1067 |
| alphabet size \|A\| | 41 |
| uniform bits/token log2\|A\| | 5.357552 |
| naive counting DL (empty table) | 2840.0 |

## Scaling convention

> DL_ref = naive_counting_dl * (bits_per_token_ref / log2|A|); order-k uses bits_per_token = H_k, LZ77 uses bits_per_token = z*(log2 N + log2|A|)/N. Ratio-reconciled, no tuned constants (mirrors bench_formalize._order0_entropy_dl_est).

## The measured stack

| reference | bits/token | DL (counting units) |
| --- | --- | --- |
| corpus_dl (reported, learned macro table) | — | 2139.0 |
| order-0 (memoryless) | 4.621052 | 2449.587 |
| order-1 | 1.509636 | 800.247 |
| order-2 | 0.772277 | 409.378 |
| LZ77 parse proxy (z = 242) | 3.496616 | 1853.531 |

**Residual gap (T2, §11.8):** corpus_dl − LZ77_proxy = 2139.0 − 1853.531 = **285.469** (13.346% of corpus_dl).

## Order-0 consistency check

Committed CSV order0_entropy_dl_est = 2449.587; recomputed = 2449.587; match = **True**.

## Caveat

> References, not floors. Per COMPRESSION.md §10.2: on highly repetitive corpora (plausibly ours) grammar coders can encode far *below* nH_k -- which is exactly what the bench measured (2139 < 2450 order-0). A corpus_dl below an order-k line is expected. In-sample, hindsight, zero generalization power on a 37-reading corpus (§11.7).
