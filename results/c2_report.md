# C2 — two-part entropy-coded DL (REPORTED experiment)

COMPRESSION.md **§3 C2** made concrete, under the **§11.8** gate. This is a **reporting experiment**: the admission currency stays the counting one (`mdl_macros`), **the gates are unchanged, and nothing gates on any number below**. C2 only measures and reports.

> REPORTED experiment. Gates are UNCHANGED: admission stays the counting currency (mdl_macros strict-DL-decrease + the certificate batteries). Nothing gates on any number here (§11.8: C2/C4 stay reporting experiments).

## The question

> How much of KT order-1's 624-unit advantage over the counting corpus_dl (2139 -> 1514.5, the §10.7 exhibit) does a two-part macro+entropy-coded currency recover while KEEPING the vocabulary? And does the certified macro vocabulary even PAY under entropy coding?

## The currency

`c2_dl = model_bits + data_bits`, where

- **model bits** — the macro table priced EXACTLY as mdl_macros prices it (leaf counting, dl_macro); one source of truth.
- **data bits** — adaptive KT order-1 (ppm_ref's coder) over the macro-REWRITTEN token stream, scaled bits->counting at the fixed raw-stream exchange rate.

## The token mapping (design decision)

**Headline mapping: `canonical`.** greedy rewrite via mdl_macros._match_at; a macro invocation = 1 ('macro', name) symbol + 1 symbol per bound argument (('argval', canonical-json) in the canonical mapping). Mirrors dl_invocation(k) = base + name + k exactly. Unmatched statements keep their raw _structure_tokens.

- **Sensitivity mapping** — 'structural': bound arguments walked into the raw op/ref/lit token space (recurring args reuse the existing alphabet). Reported to show the verdict is not a mapping artifact.
- **No-vocabulary anchor** — empty table => rewritten stream == raw stream, 0 model bits, data bits == ppm_ref KT order-1. Asserted equal.

## Scaling

> data_bits = naive_counting_dl * (total_kt_bits / N_raw) / log2|A|; naive_counting_dl and log2|A| READ from entropy_refs.json, N_raw the raw (empty-table) stream length. Fixed exchange-rate; empty table reproduces ppm_ref's DL_1 exactly. No tuned constants.

Read from `entropy_refs.json`: naive_counting_dl = 3856.0, log2\|A\| = 5.459432, counting corpus_dl = 2920.0; N_raw (raw stream length) = 1439.

## Consistency anchor (must reconcile with `ppm_ref`)

Empty table => 0 model bits + KT order-1 over the raw stream. `ppm_ref` KT order-1 adaptive_DL = **1918.678**; C2 empty-table data bits = **1918.678**, total = **1918.678**. RECONCILES.

## The decomposition — both arms, both mappings

| mapping | arm | model bits | data bits | **C2 total** | counting corpus_dl | stream len | \|A\| |
| --- | --- | --- | --- | --- | --- | --- | --- |
| canonical | empty (no vocab) | 0.0 | 1918.678 | **1918.678** | 3856.0 | 1439 | 44 |
| canonical | governed | 98.0 | 2186.451 | **2284.451** | 2920.0 | 1141 | 71 |
| canonical | ungoverned | 146.0 | 2068.507 | **2214.507** | 3208.0 | 1160 | 60 |
| structural | empty (no vocab) | 0.0 | 1918.678 | **1918.678** | 3856.0 | 1439 | 44 |
| structural | governed | 98.0 | 2075.357 | **2173.357** | 2920.0 | 1184 | 50 |
| structural | ungoverned | 146.0 | 1974.034 | **2120.034** | 3208.0 | 1160 | 49 |

## Verdict — does the vocabulary PAY under C2?

**The certified macro vocabulary does NOT pay under C2: governed C2 = 2284.451 > empty-table C2 (pure KT) = 1918.678, i.e. the vocabulary COSTS 365.773 units under entropy coding. Keeping the vocabulary, C2 recovers 635.549 of the 1001.322-unit KT order-1 advantage (63.5%); the full advantage is available only by ABANDONING the vocabulary. This is the honest finding: adaptive order-1 already harvests the sequential recurrence the macros deduplicate, so under entropy coding the vocabulary's value is certification structure, not compression. Under C2 the governance ranking also does not hold (governed C2 > ungoverned C2 2214.507) — driven by the DATA bits, not the model table: the governed arm's macro-rewritten stream costs more entropy-coded data bits, which outweighs governed's SMALLER model table (the ungoverned arm carries the larger paid-for vocabulary yet lands lower under C2).**

| mapping | governed C2 | empty (pure KT) C2 | vocab pays? | vocab cost | KT-1 advantage | C2 recovers | % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| canonical | 2284.451 | 1918.678 | **NO** | 365.773 | 1001.322 | 635.549 | 63.5 |
| structural | 2173.357 | 1918.678 | **NO** | 254.679 | 1001.322 | 746.643 | 74.6 |

### The governance question in the new currency

The counting currency ranks governed (2139) below ungoverned (2371); the origin-blind question is whether C2 does too. Under C2 (canonical mapping) governed = 2284.451, ungoverned = 2214.507: C2 **does NOT** rank governed below ungoverned (gap -69.944). Honest reading: the inversion is driven by the DATA bits, not the model table — the governed arm's macro-rewritten stream costs more entropy-coded data bits (2186.451 vs 2068.507, a larger symbol alphabet 71 vs 60), and that outweighs governed's SMALLER model table (98.0 vs 146.0 bits) — i.e. the arm with the LARGER paid-for vocabulary (ungoverned) actually lands lower under C2. So C2 is not, as constructed, an origin-blind governance detector; the counting and prequential currencies are where governance shows up.

## Pre-registered future predicate (stated, not armed)

> C2 (or C4/NML) replaces the counting currency as the ADMISSION gate ONLY IF, on the committed HOLDOUT source set (>=20 readings, §11.7 — in-sample deltas have zero generalization power), the two-part entropy-coded DL WITH the governed vocabulary is strictly lower than BOTH (a) the counting corpus_dl AND (b) the empty-table C2 (pure KT) by a margin exceeding the vocabulary's model bits — i.e. the certified vocabulary must PAY under C2 out-of-sample. STATED, NOT ARMED. On the committed in-sample corpus the predicate is FALSE by 365.773 units (the vocabulary COSTS bits under C2), so migration is not merely unarmed but counter-indicated: the §11.8 gate ('a recorded instance of the counting currency MISPRICING an admitted structure') is not met — C2 does not show the counting gate admitting a net-negative macro; it shows the opposite, that the vocabulary's value is certification structure, not entropy-coding compression.

## Caveats

> IN-SAMPLE, single frozen governed corpus, hindsight; zero generalization power (§11.7).

> KT is a STANDARD but not optimal context model (no PPM escape, no cross-order mixing, no CTW). C2 here is a two-part code built on that reference coder, reported for orientation only.

> The absolute data-bits depend on the token mapping; the VERDICT (vocabulary does not pay under C2) holds under both the canonical and structural mappings (see the arms table).
