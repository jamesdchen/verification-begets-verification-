# Adaptive context-model reference (C3) — committed governed corpus

The **honest (adaptive) context-model** complement to the plug-in H_k lines in `entropy_refs`. Answers §10.7's open empirical question — dictionary vs context models on a repetitive symbolic stream — on **this** corpus. Orientation reference, **not a floor** (§10.2).

## What is charged

Sequential order-k coding of the committed structure-token stream. Token x_i in its order-k context c = x_{i-k..i-1} is charged −log2 p(x_i | c), with p estimated from the counts accumulated **so far** in context c (a prequential / adaptive plug-in code). The **full stream is charged — including every context's first occurrences** — which is the whole point: adaptive coding pays for learning, unlike the plug-in H_k lines that get the corpus for free. For i < k the available prefix is used as the context (order-2 opens with an empty then a length-1 context).

Two standard, tuned-constant-free estimators over the fixed |A|-symbol alphabet:

| estimator | formula |
| --- | --- |
| KT (Krichevsky–Trofimov, add-1/2) | p(s|c) = (n_c(s) + 1/2) / (N_c + |A|/2) |
| Laplace (add-1) | p(s|c) = (n_c(s) + 1) / (N_c + |A|) |

n_c(s) = times s has already followed c; N_c = times c already seen; |A| = fixed alphabet size (not the running distinct count).

## Stream

| quantity | value |
| --- | --- |
| certified governed exogenous readings | 62 |
| stream length N | 1841 |
| alphabet size \|A\| | 50 |

## Scaling convention

> DL_ref = naive_counting_dl * (bits_per_token_ref / log2|A|), bits_per_token_ref = total_adaptive_bits / N. naive_counting_dl and log2|A| are READ from results/entropy_refs.json (no recomputation); identical ratio convention to entropy_refs and bench_formalize._order0_entropy_dl_est. No tuned constants.

Read from `entropy_refs.json`: naive_counting_dl = 4894.0, log2\|A\| = 5.643856, corpus_dl = 3801.0.

## Plug-in vs adaptive, per order k (DL in counting units)

| k | plug-in H_k (b/tok) | plug-in DL_k | KT b/tok | **KT DL** | Laplace b/tok | **Laplace DL** | corpus_dl |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 4.711023 | 4085.105 | 4.79997 | **4162.235** | 4.800424 | **4162.629** | 3801.0 |
| 1 | 1.638743 | 1421.016 | 2.817296 | **2442.983** | 3.143709 | **2726.028** | 3801.0 |
| 2 | 0.907239 | 786.701 | 3.101174 | **2689.145** | 3.493768 | **3029.577** | 3801.0 |

(Adaptive DL > plug-in DL_k at every k is expected and correct — the plug-in line does not pay the learning cost the adaptive coder does.)

## Headline — the §10.7 question, answered on this corpus

**Does ANY honest adaptive order-k coder (either estimator) beat corpus_dl = 3801.0? YES.**

The best adaptive coder is **KT order-1** at DL = **2442.983** — that is -1358.017 vs corpus_dl (3801.0). So on this corpus an honest adaptive context model DOES beat the macro/grammar coder.

> §10.2-consistent: adaptive order-0 pays a pure learning cost with no context and loses (DL ~2511 > corpus_dl 2139); order-1 hits the sweet spot -- only 41 contexts, each seen often enough to converge, so it captures the corpus's sequential structure and comes in WELL under corpus_dl despite paying full learning cost (KT DL ~1515); order-2 splits N over ~164 mostly-rare contexts, so its learning cost rises again and it regresses relative to order-1 (still under corpus_dl). So on THIS repetitive small-N corpus an honest adaptive context model does beat the macro coder at orders 1-2 -- but note the plug-in H_k lines remain far below the adaptive DLs (the learning cost the plug-in never pays is exactly the §10.7 point), and this says nothing about generalization (§11.7) or about optimal context models (no PPM/CTW here).

## Prequential trajectory

Cumulative adaptive bits at each of the 37 reading boundaries (in author order) are emitted in `ppm_ref.json` under `prequential` for every (estimator, k), so the bench's prequential column gains a context-model comparator. Endpoints (KT):

| k | cumulative bits at final reading |
| --- | --- |
| 0 | 8836.746 |
| 1 | 5186.641 |
| 2 | 5709.262 |

## Caveats

> IN-SAMPLE, single 37-reading corpus, hindsight; zero generalization power (§11.7).

> KT / Laplace are STANDARD estimators but NOT the best possible context model: no PPM escape, no cross-order back-off/mixing, no CTW. This is a REFERENCE -- the numbers say nothing about optimal context modeling.

> The §10.2 REFUTED claims stay refuted and are NOT relied on: 'early-stopped RePair reaches |S|H_k' (1-2) and 'too many nonterminals provably grows bit-size' (0-3).
