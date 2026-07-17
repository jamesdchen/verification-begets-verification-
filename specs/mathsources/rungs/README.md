# The rung registry (WP-T6a-INTEGRATE; COMPRESSION.md §11.5 / §11.9)

This directory is the RUNG analogue of `specs/mathsources/operators/` (T4a). It
holds the meta-interpreter's *lowering vocabulary* as pure data:

```
rungs/
  admitted.json         append-only, sole-admitter-by-construction; the only
                        rungs canon(reading) applies.  ABSENT / empty ⇒ empty
                        registry ⇒ canon is the IDENTITY (the rung-free pin).
  proposed/*.json       staged rung-specs.  A dream may PROPOSE a rung as data;
                        only buildloop.rung_registry.admit_rung admits it.
```

A rung ROW is a validated rung-spec `{rung, over, measure, rules}`
(`kernel.rung.validate_rung` is the schema source of truth). The loader
(`load_admitted`), digest verification (`_verify_entry` — a post-admission edit
of a rule refuses to lower), and the append-only `save_admitted` (re-runs
`admit_rung`; refuses a forged / stale / non-re-admitting cert) mirror
`generators/operator_growth.py`.

## `canon(reading)` — the view (FI-W1-2) and its composition

`canon` applies the admitted rung pipeline to a COPY of each statement's `pred`.
The composition (frozen here, per §11.5):

- rungs apply in **admission order** (the `seq` the cert stamps);
- `kernel.rung.lower` runs **each rung to its own fixpoint with root-restart**;
- the **full sequence is iterated to a JOINT fixpoint** — a pass that changes
  nothing halts it;
- **NOT-LOWERED discipline** (FI-W1-1 channel 2): an enum-only pred (gcd/coprime,
  no sound SMT rendering) is **skipped**, stays raw, and mints no norm-cert;
- a global **finitize-then-canonicalize** order under one lexicographic measure
  `(quantifier_count, disorder)` is RESERVED for the T6b exists-finitization
  rung; today the registry holds at most the single canonicalization rung, so the
  reserved seam is marked but unexercised.

Store, certs, goldens, authored bytes, prompts stay **raw, always**. `canon` is
applied at exactly four call sites (`mdl_macros._reading_stats`,
`recurrence.mine`, `recurrence.gc_macros`, the loop's FI-2 serve-price). Empty
registry ⇒ `canon` returns the input object unchanged ⇒ mining and pricing are
byte-identical.

## The pilot rung — PROPOSED, refused, and correctly staying proposed

`proposed/canon_commsort.json` is the §11.5 pilot: `sort-children` over
`{+,*,and,or,=,!=}` plus same-op flatten rules for nested `+`/`*`, under the
lexicographic measure `["size","inversions"]` (66 rules; row digest
`84f83c9d…`). Run against the **real committed corpus** (the 37 governed,
certified exogenous readings in `results/formalize_bench_state.jsonl`), the gate
**REFUSES** — by BOTH teeth independently:

1. **Per-rule vacuity** (first gate): **64 of 66 rules fire on < 2 exogenous
   readings.** The nested-`+`/`*` flatten rules almost never occur in this corpus
   (its terms are shallow); only two `sort-children` rules reach two witnesses.
   Most of the pilot's fragment is dead vocabulary here.
2. **Counterfactual MDL gate** (computed unconditionally for the record):

   | quantity                         | value |
   |----------------------------------|-------|
   | searched DL, raw view            | 2641.0 |
   | searched DL, canon view          | 2641.0 |
   | profit (canon − raw)             | **0.0** |
   | rung model bits (`_leaf_count` over 66 rules) | 2748.0 |
   | net (canon + rung_bits − raw)    | **+2748.0** |

   Canonicalization reorders 9 of 89 preds but yields **zero** searched-DL
   improvement: `mdl_macros`'s token proxy is order-blind and the mining cluster
   key is by LF-kind tuple, not arg order, so reordering `=`/`!=`/`and`/`or` args
   creates no new mineable recurrence on the greedy/searched path. profit = 0 ⇒
   the anti-gaming tooth fires (raw mining already captures whatever the rung
   would); even were profit negative, the 2748 model bits dwarf it.

This is the **correct outcome**. §11.10 recorded that the T3 window rule was
HELD, leaving canonicalization's profit on this corpus an open empirical
question; the answer here is that the pilot does **not** pay for itself, so it
STAYS proposed. It is not forced in. `admitted.json` remains absent ⇒ the view is
the identity ⇒ every downstream number is byte-identical to the committed
checkpoint.
