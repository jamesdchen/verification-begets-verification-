# Tower census (WP-CENSUS)

Measurement artifact for the §11 pre-registered gates. This file REPORTS numbers; the plan's predicates and humans decide. Reconstructed by replaying the committed checkpoint's waves through today's miner (greedy grow, same code path as the bench).

- checkpoint: `results/formalize_bench_state.jsonl` (110 records, waves [0, 1, 2, 3, 4, 5, 6])
- wave table-hash verification: **ALL MATCH**
- governed final table: 5 macros, corpus_dl 2920.0
- ungoverned final table: 6 macros, corpus_dl 3208.0

## 1. Tower census -- gates WP-T1 (§11.2)

Adjacent invocation-pair recurrences in the governed corpus rewritten with the final flat table, over 46 certified readings. Witnesses = distinct exogenous readings.

**Gate metric = REALIZABLE adjacent witnesses.** A pair witnesses a reading only where its covered statements are uniform in (force, quote) across the union of both invocations -- the H2 constraint `buildloop/recurrence.py:_demand_windows` enforces (a macro invocation expands with ONE inherited force+quote, so a level-2 body spanning a force/quote boundary is unrealizable). Pass 3 already honors this rule; pass 2 now matches it. The pre-gate `raw_adjacent_witnesses` count is reported as a secondary column and is **NOT the gate metric**.

Pre-registered context (§11.2, reported not applied): a level-2 macro needs roughly **>= 7 witnesses** to pay under the current currency.

- distinct adjacent pairs: 24
- **[GATE] max REALIZABLE witnesses, macro-macro (MM) pair: 2**  (bar: 7)
- **[GATE] MM pairs at/above the bar (realizable): 0**; any-macro pairs at/above the bar: 0
- max realizable witnesses, any macro-involving pair (MM or MS): 2

Realizable-witness distribution (witnesses: #pairs): 0:20, 1:1, 2:2, 4:1

Secondary (NOT the gate metric) -- pre-H2 raw adjacency: max raw MM = 17, raw MM pairs >= bar = 2; raw distribution: 1:3, 2:6, 4:3, 5:2, 7:1, 8:2, 10:1, 11:1, 17:2, 23:1, 25:1, 30:1

Macro-macro (MM) pairs -- the level-2 target:

```
  MM  M:m_5cfe6695215f + M:m_5cfe6695215f  ->  2 realizable witnesses (raw 10)
  MM  M:m_5cfe6695215f + M:m_1c486950ad4c  ->  0 realizable witnesses (raw 17)
  MM  M:m_27c1366afd78 + M:m_83b0ad76bcb0  ->  0 realizable witnesses (raw 4)
```

Macro+statement (MS) pairs:

```
  MS  S:ambient + M:m_5cfe6695215f  ->  0 realizable witnesses (raw 25)
  MS  M:m_1c486950ad4c + S:hypothesis  ->  0 realizable witnesses (raw 17)
  MS  S:ambient + M:m_27c1366afd78  ->  0 realizable witnesses (raw 11)
  MS  M:m_5cfe6695215f + S:quantifier  ->  0 realizable witnesses (raw 8)
  MS  S:ambient + M:m_1065efaf6ad8  ->  0 realizable witnesses (raw 7)
  MS  M:m_1065efaf6ad8 + S:conclusion  ->  0 realizable witnesses (raw 5)
  MS  M:m_27c1366afd78 + S:hypothesis  ->  0 realizable witnesses (raw 5)
  MS  M:m_83b0ad76bcb0 + S:conclusion  ->  0 realizable witnesses (raw 4)
  MS  M:m_1065efaf6ad8 + S:hypothesis  ->  0 realizable witnesses (raw 2)
  MS  M:m_27c1366afd78 + S:conclusion  ->  0 realizable witnesses (raw 2)
  MS  M:m_1c486950ad4c + S:conclusion  ->  0 realizable witnesses (raw 1)
  MS  S:ambient + M:m_1c486950ad4c  ->  0 realizable witnesses (raw 1)
```

## 2. Slot measurement -- WP-T3 (§11.3)

Congruence triple ['33_cong_add', '34_cong_mul', '35_cong_sub'], window ['h1', 'h2', 'c'], anti-unified via recurrence and priced against the final governed table:

- **delta: -179.0** (dl_before 2920.0 -> dl_after 2741.0); admit: **True**; uses: 3
- slot params: ['p0'] (one operator slot at the conclusion op position)

Per-op flat variants (no slot):

- 33_cong_add: admit False, delta 3.0, uses 1
- 34_cong_mul: admit False, delta 3.0, uses 1
- 35_cong_sub: admit False, delta 3.0, uses 1

`_demand_windows` on the triple (the blocker as a committed number): total windows covering the [h1,h2,c] cluster = **0** (quotes are non-uniform, so no window is proposed):

- 33_cong_add: 0 demand windows, 0 covering the cluster
- 34_cong_mul: 0 demand windows, 0 covering the cluster
- 35_cong_sub: 0 demand windows, 0 covering the cluster

## 3. Subtree census -- WP-T4 (§11.4)

Recurring `pred` subtrees across 46 certified governed readings, three abstraction levels. Single-kernel-atom-alias = one kernel operator over bare leaves (a trivial alias, §11.4 Critical 1).

| level | abstraction | distinct | >=2 wit | alias >=2 | **non-alias >=2** |
|---|---|---|---|---|---|
| 0 | exact-bytes | 119 | 39 | 31 | **8** |
| 1 | refs-abstracted | 65 | 27 | 14 | **13** |
| 2 | refs+lits-abstracted | 65 | 27 | 14 | **13** |

Non-alias candidates at >= 2 witnesses (exact-bytes level):

```
  7w  {"args":[{"args":[{"ref":"a"},{"ref":"m"}],"op":"mod"},{"args":[{"ref":"b"},{"ref":"m"}],"op":"mod"}],"op":"="}
  3w  {"args":[{"args":[{"ref":"c"},{"ref":"m"}],"op":"mod"},{"args":[{"ref":"d"},{"ref":"m"}],"op":"mod"}],"op":"="}
  2w  {"args":[{"args":[{"ref":"a"},{"lit":0}],"op":"!="},{"args":[{"ref":"b"},{"lit":0}],"op":"!="}],"op":"or"}
  2w  {"args":[{"args":[{"ref":"a"},{"ref":"b"}],"op":"*"}],"op":"even"}
  2w  {"args":[{"args":[{"ref":"a"},{"ref":"b"}],"op":"+"}],"op":"even"}
  2w  {"args":[{"args":[{"ref":"a"},{"ref":"c"}],"op":"*"},{"ref":"m"}],"op":"mod"}
  2w  {"args":[{"args":[{"ref":"a"},{"ref":"c"}],"op":"+"},{"ref":"m"}],"op":"mod"}
  2w  {"args":[{"args":[{"ref":"a"},{"ref":"x"}],"op":"*"},{"args":[{"ref":"b"},{"ref":"y"}],"op":"*"}],"op":"+"}
```

---

Generated by `tools/tower_census.py` from the committed checkpoint; deterministic (no timestamps, no randomness).
