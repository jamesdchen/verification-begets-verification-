# Hammer readout (UNBOUNDED-statement close-rate)

- verdicts status: **complete**  (lean_available=True)
- goals: 24  |  closed: 6  |  statement-cert demand: 1  |  tactic (H3) refused: 17  |  not-run: 0

## Per-rung closure

| rung | closed |
|---|---|
| decide | 0 |
| omega | 4 |
| norm_num | 2 |
| simp | 0 |
| unknown | 0 |

## Per-family closure

| family | closed | stmt-cert demand | tactic refused | not-run | total |
|---|---|---|---|---|---|
| dvd | 3 | 0 | 4 | 0 | 7 |
| gcd | 0 | 1 | 2 | 0 | 3 |
| linear | 3 | 0 | 5 | 0 | 8 |
| parity | 0 | 0 | 6 | 0 | 6 |

## Statement-cert demand (elaborated=false -- statement stage)

- 21_gcd_largest

## Tactic / H3 refusals (elaborated, ladder closed nothing)

- 03_dvd_transitive, 04_even_plus_even, 05_odd_plus_odd, 06_odd_times_odd, 07_even_plus_odd, 08_even_step, 10_gcd_self, 14_even_times_any, 15_dvd_scales, 16_square_nonneg, 17_cancel_c, 18_cancel_k, 19_mod_less_m, 20_mod_upper, 22_largest_divisor, 23_divisor_bound, 24_gcd_positive

## Tokens (LLM off)

| prompt | completion | total |
|---|---|---|
| 0 | 0 | 0 |

> rows are lane evidence toward a future kernel statement-cert / proof-cert mint, NEVER certificates (the run/import_rt.py precedent); no per-row wall time -- byte-stability law
