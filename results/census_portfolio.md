# Corpus portfolio census

corpora: 5  ·  nodes: 748  ·  verdicts: attempt-candidate=61, no-signal=328, out-of-fragment=359

**rollup of lexical censuses, deterministic, LLM-free, Lean-free; REPORTS signals -- never a fidelity verdict. attempt_candidates is the C2 mining queue, not a claim any node certifies.**

## Portfolio miss histogram (the price list)

- probability-entropy: 116
- sequences-sums: 109
- algebra-structures: 97
- sets-cardinality: 89
- real-analysis: 68
- primality: 57

## Per corpus

| corpus | nodes | attempt-candidates | out-of-fragment | no-signal | top miss |
|---|---|---|---|---|---|
| equational_theories | 241 | 20 | 37 | 184 | algebra-structures |
| flt_regular | 45 | 3 | 41 | 1 | primality |
| formal_book | 192 | 37 | 73 | 82 | sequences-sums |
| pfr | 218 | 0 | 159 | 59 | probability-entropy |
| unit_fractions | 52 | 1 | 49 | 2 | sets-cardinality |

## C2 mining queue (attempt-candidate labels)

- **equational_theories** (20): mag, edge-disjoint, a0000000306, freeconst, canonical-invariant, a0000000315, law-def, models-def, sound-complete, push, equiv, law-count-sym, law-count-triv, impl, 5093-nontrivial, austin-two, a0000000288, a0000000293, a0000000296, a0000000302
- **flt_regular** (3): lemma:cyclo_poly_deg, lemma:alg_int_abs_val_one, lemma:unit_lemma
- **formal_book** (37): ch20theorem1, ch20theorem3proof1, ch20theorem3proof2, sperner, ch30lemma, ch30theorem2, binomial_never_powers, fermats_little, euler_criterion, gauss_lemma, lem_aux_iii, book.irrational.Theorem_3, pearl_lemma, cone_lemma, ch11_theorem1, ch11_theorem2, ch11_theorem4, slope_problem, sylvester_gallai2, monochromatic_lines, cauchy_rigidity, ch14theorem1, ch16theorem1, ch19theorem4, ch22lemma1, ch22corollary, ch22lemma2, monsky_theorem, ch23theorem1, ch23theorem2, ch23corollary, ch26lemma_c, tiling_rectangles1, tiling_rectangles2, tiling_rectangles3, lyusternik_shnirelman, gale_theorem
- **unit_fractions** (1): def:minor_arcs
