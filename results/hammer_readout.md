# Hammer readout (UNBOUNDED-statement close-rate)

- verdicts status: **complete**  (lean_available=True)
- goals: 24  |  closed: 10  |  statement-cert demand: 0  |  tactic (H3) refused: 14  |  not-run: 0

## Per-rung closure

| rung | closed |
|---|---|
| decide | 6 |
| omega | 2 |
| norm_num | 2 |
| simp | 0 |
| unknown | 0 |

## Per-family closure

| family | closed | stmt-cert demand | tactic refused | not-run | total |
|---|---|---|---|---|---|
| dvd | 5 | 0 | 1 | 0 | 6 |
| gcd | 1 | 0 | 1 | 0 | 2 |
| linear | 4 | 0 | 5 | 0 | 9 |
| parity | 0 | 0 | 7 | 0 | 7 |

## Statement-cert demand (elaborated=false -- statement stage)

- (none)

## Tactic / H3 refusals (elaborated, ladder closed nothing)

- 03_dvd_transitive, 04_even_plus_even, 05_odd_plus_odd, 06_odd_times_odd, 07_even_plus_odd, 08_even_step, 105_03_parity_and_divisibility_problem_021, 106_03_parity_and_divisibility_problem_023, 108_03_parity_and_divisibility_problem_025, 109_04_proofs_with_structure_ii_problem_016, 10_gcd_self, 110_04_proofs_with_structure_ii_problem_030, 111_04_proofs_with_structure_ii_theorem_001, 112_04_proofs_with_structure_ii_theorem_003

## Tokens (LLM off)

| prompt | completion | total |
|---|---|---|
| 0 | 0 | 0 |

## Authoring candidates (H1.3 -- FgReflect module proposals)

- candidates: 1  |  passed: 1  |  failed: 0  |  not-run: 0

| candidate | status | declares | why |
|---|---|---|---|
| p9-parallel-tower-r5 | PASSED | PdS, denoteS, denoteS_psub, denoteS_pseteq, boolS_ext, pseteq_iff_mutual_psub, psub_sinter_left, checkPdS, denotePdBoxS, checkPdS_sound, StmtS, updEnvS, memL, updSenvS, denoteStmtBoxS, checkStmtBoxS, checkStmtBoxS_sound, consL, subsetsOfS, consL_length, subsetsOfS_length, ssall_two_binder_cost, costStmtS, inBudgetS, checkStmtFuelS, checkStmtFuelS_sound, checkStmtFuelS_none_of_over_budget, checkStmtFuelS_ne_pass_of_over_budget, lead_subject_cost_is_the_squared_powerset, lead_subject_is_over_any_budget_below_its_domain |  |

> candidate FgReflect module text spliced inside `namespace FgReflect` the way run/reflect_shadow.py composes its probes; a row is lane evidence about ELABORATION, never a certificate and never a slice edit -- adopting a passed candidate is an ordinary authored edit in a later session

> rows are lane evidence toward a future kernel statement-cert / proof-cert mint, NEVER certificates (the run/import_rt.py precedent); no per-row wall time -- byte-stability law
