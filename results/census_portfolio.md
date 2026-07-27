# Corpus portfolio census

corpora: 8  ·  nodes: 2132  ·  verdicts: attempt-candidate=140, no-signal=340, out-of-fragment=1652

**rollup of lexical censuses, deterministic, LLM-free, Lean-free; REPORTS signals -- never a fidelity verdict. attempt_candidates is the C2 mining queue, not a claim any node certifies.**

## Portfolio miss histogram (the price list)

- real-analysis: 710
- rational-arithmetic: 620
- entropy-log: 511
- sequences-sums: 384
- maps-functions: 242
- polynomials-fields: 193
- primality: 171
- magmas-equational: 156
- sets-cardinality: 142
- probability-mass: 117
- algebra-structures: 103
- geometry-topology: 63
- algebra-abstract: 47
- graphs-combinatorics: 41

## Per corpus

| corpus | nodes | attempt-candidates | out-of-fragment | no-signal | top miss |
|---|---|---|---|---|---|
| carleson | 180 | 5 | 131 | 44 | rational-arithmetic |
| equational_theories | 241 | 1 | 176 | 64 | magmas-equational |
| flt_regular | 45 | 0 | 45 | 0 | polynomials-fields |
| formal_book | 192 | 1 | 155 | 36 | rational-arithmetic |
| math2001 | 260 | 106 | 121 | 33 | real-analysis |
| pfr | 218 | 0 | 184 | 34 | probability-mass |
| prime_number_theorem_and | 944 | 27 | 790 | 127 | real-analysis |
| unit_fractions | 52 | 0 | 50 | 2 | sets-cardinality |

## C2 mining queue (attempt-candidate labels)

- **carleson** (5): pairwise-disjoint, John-Nirenberg, a0000000013, row-correlation, disjoint-row-support
- **equational_theories** (1): edge-disjoint
- **formal_book** (1): fermats_little
- **math2001** (106): 01_Proofs_by_Calculation#problem-003, 01_Proofs_by_Calculation#problem-004, 01_Proofs_by_Calculation#problem-006, 01_Proofs_by_Calculation#problem-007, 01_Proofs_by_Calculation#problem-010, 01_Proofs_by_Calculation#problem-011, 01_Proofs_by_Calculation#problem-016, 01_Proofs_by_Calculation#problem-021, 01_Proofs_by_Calculation#problem-022, 01_Proofs_by_Calculation#problem-026, 02_Proofs_with_Structure#problem-002, 02_Proofs_with_Structure#problem-006, 02_Proofs_with_Structure#problem-013, 02_Proofs_with_Structure#problem-016, 02_Proofs_with_Structure#problem-017, 02_Proofs_with_Structure#problem-023, 02_Proofs_with_Structure#problem-025, 02_Proofs_with_Structure#problem-026, 02_Proofs_with_Structure#problem-028, 03_Parity_and_Divisibility#definition-001, 03_Parity_and_Divisibility#problem-001, 03_Parity_and_Divisibility#problem-002, 03_Parity_and_Divisibility#problem-003, 03_Parity_and_Divisibility#problem-004, 03_Parity_and_Divisibility#problem-005, 03_Parity_and_Divisibility#problem-006, 03_Parity_and_Divisibility#definition-002, 03_Parity_and_Divisibility#problem-007, 03_Parity_and_Divisibility#problem-008, 03_Parity_and_Divisibility#problem-009, 03_Parity_and_Divisibility#definition-003, 03_Parity_and_Divisibility#problem-010, 03_Parity_and_Divisibility#definition-004, 03_Parity_and_Divisibility#problem-011, 03_Parity_and_Divisibility#problem-012, 03_Parity_and_Divisibility#problem-013, 03_Parity_and_Divisibility#problem-014, 03_Parity_and_Divisibility#problem-015, 03_Parity_and_Divisibility#problem-016, 03_Parity_and_Divisibility#problem-017, 03_Parity_and_Divisibility#definition-005, 03_Parity_and_Divisibility#problem-018, 03_Parity_and_Divisibility#problem-019, 03_Parity_and_Divisibility#problem-021, 03_Parity_and_Divisibility#problem-022, 03_Parity_and_Divisibility#problem-023, 03_Parity_and_Divisibility#problem-024, 03_Parity_and_Divisibility#problem-025, 03_Parity_and_Divisibility#problem-026, 03_Parity_and_Divisibility#problem-027, 03_Parity_and_Divisibility#problem-028, 04_Proofs_with_Structure_II#problem-002, 04_Proofs_with_Structure_II#definition-001, 04_Proofs_with_Structure_II#problem-007, 04_Proofs_with_Structure_II#problem-011, 04_Proofs_with_Structure_II#problem-012, 04_Proofs_with_Structure_II#problem-013, 04_Proofs_with_Structure_II#problem-015, 04_Proofs_with_Structure_II#problem-016, 04_Proofs_with_Structure_II#problem-017, 04_Proofs_with_Structure_II#theorem-001, 04_Proofs_with_Structure_II#problem-021, 04_Proofs_with_Structure_II#problem-022, 04_Proofs_with_Structure_II#problem-023, 04_Proofs_with_Structure_II#problem-025, 04_Proofs_with_Structure_II#problem-029, 04_Proofs_with_Structure_II#lemma-003, 04_Proofs_with_Structure_II#lemma-004, 04_Proofs_with_Structure_II#problem-030, 04_Proofs_with_Structure_II#theorem-003, 05_Logic#problem-005, 05_Logic#problem-009, 05_Logic#problem-010, 06_Induction#problem-001, 06_Induction#theorem-001, 06_Induction#theorem-002, 06_Induction#problem-002, 06_Induction#problem-003, 06_Induction#problem-004, 06_Induction#problem-005, 06_Induction#problem-006, 06_Induction#problem-007, 06_Induction#problem-009, 06_Induction#problem-010, 06_Induction#problem-011, 06_Induction#problem-012, 06_Induction#problem-015, 06_Induction#problem-016, 06_Induction#theorem-006, 06_Induction#theorem-007, 06_Induction#theorem-008, 06_Induction#theorem-009, 06_Induction#proposition-001, 06_Induction#proposition-002, 06_Induction#proposition-003, 06_Induction#theorem-010, 07_Number_Theory#theorem-002, 07_Number_Theory#theorem-003, 09_Sets#problem-001, 09_Sets#problem-002, 09_Sets#problem-005, 09_Sets#definition-003, 09_Sets#problem-014, 09_Sets#problem-015, 09_Sets#problem-017, 10_Relations#problem-008
- **prime_number_theorem_and** (27): sigmaR_natCast, log-zeta-eq-4, Q-def, varphi-fourier-ident, shift-upwards, B-affine-periodic, phi_star-affine-periodic, ch2-lemma-5-1-e, ch2-lemma-5-1-f, ch2-lemma-5-1-h, li2-eq, buthe2-buthe-chi-star-icc, thm:faber-kadiri-psi, highlyabundant-def, div-remainder, thm:large-n-final, even-goldbach-test, even-to-odd-goldbach-triv, richstein-even-goldbach, ramare-saouter-odd-goldbach, e-silva-herzog-piranian-even-goldbach, helfgott-odd-goldbach-finite, e-silva-herzog-piranian-even-goldbach-ext, kl-odd-goldbach-finite, AnalyticOn.norm_le_of_norm_le_on_sphere, TaxicabIntegral, BlaschkeNonZero
