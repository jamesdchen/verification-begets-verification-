# Tower census (WP-CENSUS)

Measurement artifact for the §11 pre-registered gates. This file REPORTS numbers; the plan's predicates and humans decide. Reconstructed by replaying the committed checkpoint's waves through today's miner (greedy grow + re-mine-time GC) in the **refined** census-of-record mode (WP-FLIP §12.1). The wave hash lineage below is a SEPARATE legacy reconstruction: the recorded hashes pin the legacy miner of the frozen bench run, so it is the checkpoint-faithfulness tooth, not the census-of-record.

- checkpoint: `results/formalize_bench_state.jsonl` (172 records, waves [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
- census-of-record miner mode: **refined**
- wave table-hash verification (legacy lineage): **ALL MATCH**
- governed final table: 12 macros, corpus_dl 4380.0
- ungoverned final table: 10 macros, corpus_dl 4252.0

## 1. Tower census -- gates WP-T1 (§11.2)

Adjacent invocation-pair recurrences in the governed corpus rewritten with the final flat table, over 75 certified readings. Witnesses = distinct exogenous readings.

**Gate metric = REALIZABLE adjacent witnesses.** A pair witnesses a reading only where its covered statements are uniform in (force, quote) across the union of both invocations -- the H2 constraint `buildloop/recurrence.py:_demand_windows` enforces (a macro invocation expands with ONE inherited force+quote, so a level-2 body spanning a force/quote boundary is unrealizable). Pass 3 already honors this rule; pass 2 now matches it. The pre-gate `raw_adjacent_witnesses` count is reported as a secondary column and is **NOT the gate metric**.

Pre-registered context (§11.2, reported not applied): a level-2 macro needs roughly **>= 7 witnesses** to pay under the current currency.

- distinct adjacent pairs: 35
- **[GATE] max REALIZABLE witnesses, macro-macro (MM) pair: 3**  (bar: 7)
- **[GATE] MM pairs at/above the bar (realizable): 0**; any-macro pairs at/above the bar: 0
- max realizable witnesses, any macro-involving pair (MM or MS): 3

Realizable-witness distribution (witnesses: #pairs): 0:31, 1:1, 2:1, 3:1, 6:1

Secondary (NOT the gate metric) -- pre-H2 raw adjacency: max raw MM = 17, raw MM pairs >= bar = 2; raw distribution: 1:5, 2:5, 3:3, 4:2, 5:3, 6:3, 7:2, 8:1, 10:1, 11:2, 12:1, 13:1, 14:1, 17:2, 22:1, 33:1, 34:1

Macro-macro (MM) pairs -- the level-2 target:

```
  MM  M:m_5cfe6695215f + M:m_5cfe6695215f  ->  3 realizable witnesses (raw 11)
  MM  M:m_5cfe6695215f + M:m_1c486950ad4c  ->  0 realizable witnesses (raw 17)
  MM  M:m_1c486950ad4c + M:m_68f950843f5c  ->  0 realizable witnesses (raw 5)
  MM  M:m_27c1366afd78 + M:m_f3a9880f19ae  ->  0 realizable witnesses (raw 5)
  MM  M:m_5cfe6695215f + M:m_dcb7cd3bfa01  ->  0 realizable witnesses (raw 4)
  MM  M:m_1065efaf6ad8 + M:m_42eaac6c6001  ->  0 realizable witnesses (raw 2)
  MM  M:m_1c486950ad4c + M:m_d7321a30cf1c  ->  0 realizable witnesses (raw 1)
  MM  M:m_5cfe6695215f + M:m_8605d9a87859  ->  0 realizable witnesses (raw 1)
```

Macro+statement (MS) pairs:

```
  MS  S:ambient + M:m_5cfe6695215f  ->  0 realizable witnesses (raw 33)
  MS  M:m_1c486950ad4c + S:hypothesis  ->  0 realizable witnesses (raw 14)
  MS  S:ambient + M:m_27c1366afd78  ->  0 realizable witnesses (raw 13)
  MS  S:ambient + M:m_1065efaf6ad8  ->  0 realizable witnesses (raw 12)
  MS  M:m_5cfe6695215f + S:quantifier  ->  0 realizable witnesses (raw 11)
  MS  S:hypothesis + M:m_0332cec30208  ->  0 realizable witnesses (raw 7)
  MS  M:m_1065efaf6ad8 + S:conclusion  ->  0 realizable witnesses (raw 6)
  MS  M:m_27c1366afd78 + S:hypothesis  ->  0 realizable witnesses (raw 6)
  MS  S:ambient + M:m_1c486950ad4c  ->  0 realizable witnesses (raw 6)
  MS  M:m_f3a9880f19ae + S:conclusion  ->  0 realizable witnesses (raw 5)
  MS  M:m_1065efaf6ad8 + S:hypothesis  ->  0 realizable witnesses (raw 4)
  MS  M:m_1c486950ad4c + S:conclusion  ->  0 realizable witnesses (raw 3)
  MS  M:m_dcb7cd3bfa01 + S:conclusion  ->  0 realizable witnesses (raw 3)
  MS  M:m_27c1366afd78 + S:conclusion  ->  0 realizable witnesses (raw 2)
  MS  M:m_dcb7cd3bfa01 + S:hypothesis  ->  0 realizable witnesses (raw 2)
  MS  S:object + M:m_8bd1f00a3e05  ->  0 realizable witnesses (raw 2)
  MS  M:m_8605d9a87859 + S:conclusion  ->  0 realizable witnesses (raw 1)
  MS  S:object + M:m_dcb7cd3bfa01  ->  0 realizable witnesses (raw 1)
```

## 2. Slot measurement -- WP-T3 (§11.3)

Congruence triple ['33_cong_add', '34_cong_mul', '35_cong_sub'], window ['h1', 'h2', 'c'], anti-unified via recurrence and priced against the final governed table. Post-WP-FLIP the census-of-record is **refined**: the congruence body is realized by the greedy path and the final-table GC then adjudicates it, so it is priced here against the refined+GC table (the macro retired for its non-negative marginal) -- the delta is the realized cost of RE-adding it:

- **delta: 7.0** (dl_before 4380.0 -> dl_after 4387.0); admit: **False**; uses: 3
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

Recurring `pred` subtrees across 75 certified governed readings, three abstraction levels. Single-kernel-atom-alias = one kernel operator over bare leaves (a trivial alias, §11.4 Critical 1).

| level | abstraction | distinct | >=2 wit | alias >=2 | **non-alias >=2** |
|---|---|---|---|---|---|
| 0 | exact-bytes | 253 | 48 | 39 | **9** |
| 1 | refs-abstracted | 163 | 37 | 21 | **16** |
| 2 | refs+lits-abstracted | 127 | 42 | 23 | **19** |

Non-alias candidates at >= 2 witnesses (exact-bytes level):

```
  7w  {"args":[{"args":[{"ref":"a"},{"ref":"m"}],"op":"mod"},{"args":[{"ref":"b"},{"ref":"m"}],"op":"mod"}],"op":"="}
  3w  {"args":[{"args":[{"ref":"c"},{"ref":"m"}],"op":"mod"},{"args":[{"ref":"d"},{"ref":"m"}],"op":"mod"}],"op":"="}
  3w  {"args":[{"args":[{"ref":"n"},{"lit":2}],"op":"^"},{"lit":2}],"op":"!="}
  2w  {"args":[{"args":[{"ref":"a"},{"lit":0}],"op":"!="},{"args":[{"ref":"b"},{"lit":0}],"op":"!="}],"op":"or"}
  2w  {"args":[{"args":[{"ref":"a"},{"ref":"b"}],"op":"*"}],"op":"even"}
  2w  {"args":[{"args":[{"ref":"a"},{"ref":"b"}],"op":"+"}],"op":"even"}
  2w  {"args":[{"args":[{"ref":"a"},{"ref":"c"}],"op":"*"},{"ref":"m"}],"op":"mod"}
  2w  {"args":[{"args":[{"ref":"a"},{"ref":"c"}],"op":"+"},{"ref":"m"}],"op":"mod"}
  2w  {"args":[{"args":[{"ref":"a"},{"ref":"x"}],"op":"*"},{"args":[{"ref":"b"},{"ref":"y"}],"op":"*"}],"op":"+"}
```

---

Generated by `tools/tower_census.py` from the committed checkpoint; deterministic (no timestamps, no randomness).
