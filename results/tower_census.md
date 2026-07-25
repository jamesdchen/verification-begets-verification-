# Tower census (WP-CENSUS)

Measurement artifact for the §11 pre-registered gates. This file REPORTS numbers; the plan's predicates and humans decide. Reconstructed by replaying the committed checkpoint's waves through today's miner (greedy grow + re-mine-time GC) in the **refined** census-of-record mode (WP-FLIP §12.1). The wave hash lineage below is a SEPARATE legacy reconstruction: the recorded hashes pin the legacy miner of the frozen bench run, so it is the checkpoint-faithfulness tooth, not the census-of-record.

- checkpoint: `results/formalize_bench_state.jsonl` (236 records, waves [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])
- census-of-record miner mode: **refined**
- wave table-hash verification (legacy lineage): **ALL MATCH**
- governed final table: 11 macros, corpus_dl 5946.0
- ungoverned final table: 12 macros, corpus_dl 5835.0

## 1. Tower census -- gates WP-T1 (§11.2)

Adjacent invocation-pair recurrences in the governed corpus rewritten with the final flat table, over 107 certified readings. Witnesses = distinct exogenous readings.

**Gate metric = REALIZABLE adjacent witnesses.** A pair witnesses a reading only where its covered statements are uniform in (force, quote) across the union of both invocations -- the H2 constraint `buildloop/recurrence.py:_demand_windows` enforces (a macro invocation expands with ONE inherited force+quote, so a level-2 body spanning a force/quote boundary is unrealizable). Pass 3 already honors this rule; pass 2 now matches it. The pre-gate `raw_adjacent_witnesses` count is reported as a secondary column and is **NOT the gate metric**.

Pre-registered context (§11.2, reported not applied): a level-2 macro needs roughly **>= 7 witnesses** to pay under the current currency.

- distinct adjacent pairs: 31
- **[GATE] max REALIZABLE witnesses, macro-macro (MM) pair: 0**  (bar: 7)
- **[GATE] MM pairs at/above the bar (realizable): 0**; any-macro pairs at/above the bar: 0
- max realizable witnesses, any macro-involving pair (MM or MS): 0

Realizable-witness distribution (witnesses: #pairs): 0:27, 1:2, 5:1, 11:1

Secondary (NOT the gate metric) -- pre-H2 raw adjacency: max raw MM = 32, raw MM pairs >= bar = 1; raw distribution: 1:9, 2:3, 4:1, 5:4, 7:1, 9:1, 10:1, 12:1, 17:1, 20:1, 21:1, 25:2, 26:2, 32:1, 36:1, 47:1

Macro-macro (MM) pairs -- the level-2 target:

```
  MM  M:m_94849d65514b + M:m_1c486950ad4c  ->  0 realizable witnesses (raw 32)
  MM  M:m_1c486950ad4c + M:m_68f950843f5c  ->  0 realizable witnesses (raw 5)
  MM  M:m_1c486950ad4c + M:m_f3a9880f19ae  ->  0 realizable witnesses (raw 5)
  MM  M:m_1c486950ad4c + M:m_4bc48ef89944  ->  0 realizable witnesses (raw 1)
  MM  M:m_1c486950ad4c + M:m_d7321a30cf1c  ->  0 realizable witnesses (raw 1)
  MM  M:m_94849d65514b + M:m_89d2d329d7bc  ->  0 realizable witnesses (raw 1)
  MM  M:m_94849d65514b + M:m_8bd1f00a3e05  ->  0 realizable witnesses (raw 1)
```

Macro+statement (MS) pairs:

```
  MS  M:m_1c486950ad4c + S:hypothesis  ->  0 realizable witnesses (raw 36)
  MS  M:m_94849d65514b + S:object  ->  0 realizable witnesses (raw 26)
  MS  M:m_94849d65514b + S:quantifier  ->  0 realizable witnesses (raw 25)
  MS  S:object + M:m_1c486950ad4c  ->  0 realizable witnesses (raw 25)
  MS  S:hypothesis + M:m_0332cec30208  ->  0 realizable witnesses (raw 7)
  MS  M:m_1c486950ad4c + S:conclusion  ->  0 realizable witnesses (raw 5)
  MS  M:m_f3a9880f19ae + S:conclusion  ->  0 realizable witnesses (raw 5)
  MS  M:m_1c486950ad4c + S:quantifier  ->  0 realizable witnesses (raw 4)
  MS  S:object + M:m_8bd1f00a3e05  ->  0 realizable witnesses (raw 2)
  MS  S:quantifier + M:m_42eaac6c6001  ->  0 realizable witnesses (raw 2)
  MS  M:m_8605d9a87859 + S:conclusion  ->  0 realizable witnesses (raw 1)
  MS  S:object + M:m_8605d9a87859  ->  0 realizable witnesses (raw 1)
  MS  S:object + M:m_89d2d329d7bc  ->  0 realizable witnesses (raw 1)
  MS  S:quantifier + M:m_4bc48ef89944  ->  0 realizable witnesses (raw 1)
```

## 2. Slot measurement -- WP-T3 (§11.3)

Congruence triple ['33_cong_add', '34_cong_mul', '35_cong_sub'], window ['h1', 'h2', 'c'], anti-unified via recurrence and priced against the final governed table. Post-WP-FLIP the census-of-record is **refined**: the congruence body is realized by the greedy path and the final-table GC then adjudicates it, so it is priced here against the refined+GC table (the macro retired for its non-negative marginal) -- the delta is the realized cost of RE-adding it:

- **delta: 7.0** (dl_before 5946.0 -> dl_after 5953.0); admit: **False**; uses: 3
- slot params: ['p0'] (one operator slot at the conclusion op position)

Per-op flat variants (no slot):

- 33_cong_add: admit False, delta 65.0, uses 1
- 34_cong_mul: admit False, delta 65.0, uses 1
- 35_cong_sub: admit False, delta 65.0, uses 1

`_demand_windows` on the triple (the §11.3 zero-window blocker, now lifted by force-only math windows): total windows covering the [h1,h2,c] cluster = **3** (refined mode -- legacy strict-quote windows reported 0):

- 33_cong_add: 12 demand windows, 1 covering the cluster
- 34_cong_mul: 12 demand windows, 1 covering the cluster
- 35_cong_sub: 12 demand windows, 1 covering the cluster

## 3. Subtree census -- WP-T4 (§11.4)

Recurring `pred` subtrees across 107 certified governed readings, three abstraction levels. Single-kernel-atom-alias = one kernel operator over bare leaves (a trivial alias, §11.4 Critical 1).

| level | abstraction | distinct | >=2 wit | alias >=2 | **non-alias >=2** |
|---|---|---|---|---|---|
| 0 | exact-bytes | 362 | 70 | 54 | **16** |
| 1 | refs-abstracted | 242 | 53 | 28 | **25** |
| 2 | refs+lits-abstracted | 179 | 60 | 28 | **32** |

Non-alias candidates at >= 2 witnesses (exact-bytes level):

```
  7w  {"args":[{"args":[{"ref":"a"},{"ref":"m"}],"op":"mod"},{"args":[{"ref":"b"},{"ref":"m"}],"op":"mod"}],"op":"="}
  3w  {"args":[{"args":[{"ref":"c"},{"ref":"m"}],"op":"mod"},{"args":[{"ref":"d"},{"ref":"m"}],"op":"mod"}],"op":"="}
  3w  {"args":[{"args":[{"ref":"n"},{"lit":2}],"op":"^"},{"lit":2}],"op":"!="}
  3w  {"args":[{"lit":2},{"args":[{"ref":"b"},{"lit":2}],"op":"^"}],"op":"*"}
  2w  {"args":[{"args":[{"args":[{"ref":"a"},{"ref":"b"}],"op":"gcd"},{"ref":"a"}],"op":"dvd"},{"args":[{"args":[{"ref":"a"},{"ref":"b"}],"op":"gcd"},{"ref":"b"}],"op":"dvd"}],"op":"and"}
  2w  {"args":[{"args":[{"ref":"a"},{"lit":0}],"op":"!="},{"args":[{"ref":"b"},{"lit":0}],"op":"!="}],"op":"or"}
  2w  {"args":[{"args":[{"ref":"a"},{"lit":2}],"op":"^"},{"args":[{"lit":2},{"args":[{"ref":"b"},{"lit":2}],"op":"^"}],"op":"*"}],"op":"!="}
  2w  {"args":[{"args":[{"ref":"a"},{"ref":"b"}],"op":"*"}],"op":"even"}
  2w  {"args":[{"args":[{"ref":"a"},{"ref":"b"}],"op":"+"}],"op":"even"}
  2w  {"args":[{"args":[{"ref":"a"},{"ref":"b"}],"op":"gcd"},{"ref":"a"}],"op":"dvd"}
  2w  {"args":[{"args":[{"ref":"a"},{"ref":"b"}],"op":"gcd"},{"ref":"b"}],"op":"dvd"}
  2w  {"args":[{"args":[{"ref":"a"},{"ref":"c"}],"op":"*"},{"ref":"m"}],"op":"mod"}
  2w  {"args":[{"args":[{"ref":"a"},{"ref":"c"}],"op":"+"},{"ref":"m"}],"op":"mod"}
  2w  {"args":[{"args":[{"ref":"a"},{"ref":"x"}],"op":"*"},{"args":[{"ref":"b"},{"ref":"y"}],"op":"*"}],"op":"+"}
  2w  {"args":[{"args":[{"ref":"n"},{"lit":2}],"op":"^"},{"ref":"n"}],"op":"+"}
  2w  {"args":[{"args":[{"ref":"n"}],"op":"even"},{"args":[{"ref":"n"}],"op":"odd"}],"op":"or"}
```

---

Generated by `tools/tower_census.py` from the committed checkpoint; deterministic (no timestamps, no randomness).
