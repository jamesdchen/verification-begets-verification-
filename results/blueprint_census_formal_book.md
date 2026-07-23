# Blueprint fragment census

nodes: 192  ·  verdicts: attempt-candidate=37, no-signal=82, out-of-fragment=73

**lexical census, deterministic, LLM-free, Lean-free; REPORTS signals -- never a fidelity verdict.  An attempt-candidate still needs the full statement pipeline (metered) + the Lean RT lane.**

## Miss histogram (the vocabulary-growth price list)

- sequences-sums: 24
- primality: 20
- real-analysis: 17
- sets-cardinality: 15
- algebra-structures: 7
- probability-entropy: 5

## Nodes

| label | kind | verdict | miss signals | lean |
|---|---|---|---|---|
| ch20theoremI | theorem | out-of-fragment | algebra-structures | cauchy_schwarz_inequality |
| ch20theoremIIproof1 | theorem | out-of-fragment | real-analysis | harmonic_geometric_arithmetic₁ |
| ch20theoremIIproof2 | theorem | out-of-fragment | real-analysis | harmonic_geometric_arithmetic₂ |
| ch20theoremIIproof3 | theorem | out-of-fragment | real-analysis | harmonic_geometric_arithmetic₃ |
| ch20theorem1 | theorem | attempt-candidate | — | — |
| ch20theorem2 | theorem | no-signal | — | — |
| ch20theorem3proof1 | theorem | attempt-candidate | — | mantel |
| ch20theorem3proof2 | theorem | attempt-candidate | — | — |
| pigeon_hole_principle | theorem | no-signal | — | chapter28.pigeon_hole_principle |
| ch28claim1 | theorem | out-of-fragment | primality | chapter28.claim1_coprime |
| ch28claim2 | theorem | out-of-fragment | sets-cardinality | chapter28.claim2_divisible |
| ch28claim3 | theorem | out-of-fragment | real-analysis; sequences-sums | chapter28.claim3_erdos_szekeres |
| ch28claim4 | theorem | out-of-fragment | sequences-sums | chapter28.claim4_contiguous_sum |
| double_counting | theorem | out-of-fragment | sets-cardinality; sequences-sums | chapter28.double_counting |
| ch28_avg_divisors | theorem | out-of-fragment | real-analysis; sequences-sums | chapter28.sum_divisor_count |
| handshaking | lemma | out-of-fragment | sequences-sums | chapter28.handshaking |
| ch28theorem | theorem | no-signal | — | chapter28.c4_free_edge_bound |
| ch28_sum_choose | theorem | out-of-fragment | sequences-sums | chapter28.sum_choose_deg_le_choose_card |
| sperner | lemma | attempt-candidate | — | chapter28.sperner_lemma |
| brouwer | theorem | out-of-fragment | real-analysis | chapter28.brouwer_fixed_point_2d |
| ch30theorem1 | theorem | no-signal | — | chapter30.sperner |
| ch30lemma | lemma | attempt-candidate | — | — |
| ch30theorem2 | theorem | attempt-candidate | — | chapter30.erdos_ko_rado |
| ch30theorem3 | theorem | out-of-fragment | sets-cardinality | chapter30.hall_marriage |
| ch30corollary | corollary | no-signal | — | — |
| thm:euclids_proof | theorem | out-of-fragment | sets-cardinality; primality | infinity_of_primes₁ |
| thm:second_proof | theorem | out-of-fragment | primality | infinity_of_primes₂ |
| thm:third_proof | theorem | out-of-fragment | primality | infinity_of_primes₃ |
| thm:fourth_proof | theorem | out-of-fragment | primality | infinity_of_primes₄ |
| thm:fifth_proof | theorem | out-of-fragment | primality | infinity_of_primes₅ |
| thm:sixth_proof | theorem | out-of-fragment | sequences-sums | infinity_of_primes₆ |
| thm:infty_proof | theorem | out-of-fragment | sequences-sums; primality | Asymptotics.infinitely_many_more_proofs |
| thm:infinity_of_primes | theorem | out-of-fragment | primality | — |
| thm:bertrands_postulate | theorem | out-of-fragment | primality | chapter2.exists_prime_lt_and_le_two_mul |
| thm:estimate_integral | theorem | out-of-fragment | real-analysis | chapter2.harmonic_number_bounds |
| thm:estimate_factorials | theorem | no-signal | — | chapter2.bound_factorial |
| thm:estimate_binomial_coefficient | theorem | no-signal | — | chapter2.bound_binomial_coeff |
| sylvester | theorem | out-of-fragment | primality | chapter3.sylvester |
| binomial_never_powers | theorem | attempt-candidate | — | chapter3.binomials_coefficients_never_powers |
| ch04.lemma₁ | lemma | out-of-fragment | primality | ch04.lemma₁ |
| ch04.lemma2 | lemma | no-signal | — | ch04.lemma₂ |
| ch04.proposition1 | proposition | out-of-fragment | primality | ch04.theorem₁ |
| ch04.proposition2 | proposition | out-of-fragment | primality | ch04.theorem₂ |
| ch04.proposition3 | proposition | out-of-fragment | primality | — |
| sum_of_two_squares | theorem | out-of-fragment | primality | — |
| fermats_little | theorem | attempt-candidate | — | book.quadratic_reciprocity.fermat_little |
| euler_criterion | theorem | attempt-candidate | — | book.quadratic_reciprocity.euler_criterion |
| product_rule | theorem | no-signal | — | book.quadratic_reciprocity.product_rule |
| gauss_lemma | theorem | attempt-candidate | — | book.quadratic_reciprocity.lemma_of_Gauss |
| quadratic_reciprocity1 | theorem | out-of-fragment | primality | book.quadratic_reciprocity.quadratic_reciprocity_1 |
| mult_cyclic | theorem | out-of-fragment | algebra-structures | book.quadratic_reciprocity.mult_cyclic |
| fact_A | theorem | out-of-fragment | algebra-structures; primality | book.quadratic_reciprocity.fact_A |
| fact_B | theorem | out-of-fragment | algebra-structures | book.quadratic_reciprocity.fact_B |
| quadratic_reciprocity2 | theorem | out-of-fragment | primality | book.quadratic_reciprocity.quadratic_reciprocity_2 |
| root_of_unity | theorem | no-signal | — | — |
| wedderburn | theorem | no-signal | — | wedderburn |
| ch7.lemma | lemma | no-signal | — | — |
| diagonalize_real_symmetric | theorem | no-signal | — | chapter7.Theorem₁ |
| thm:hadamard_inequality | theorem | no-signal | — | chapter7.Theorem₂ |
| thm:hadamard_order | theorem | no-signal | — | — |
| thm:hadamard_existence | theorem | no-signal | — | — |
| thm:det_greater_n_fact | theorem | no-signal | — | chapter7.Theorem₂ |
| e_irrational | theorem | no-signal | — | book.irrational.e_irrational |
| e_pow_2_irrational | theorem | no-signal | — | book.irrational.e_pow_2_irrational |
| little_lemma | theorem | out-of-fragment | primality | book.irrational.little_lemma |
| e_pow_4_irrational | theorem | no-signal | — | book.irrational.e_pow_4_irrational |
| lem_aux_i | lemma | out-of-fragment | sequences-sums | book.irrational.lem_aux_i |
| lem_aux_ii | lemma | no-signal | — | book.irrational.lem_aux_ii |
| lem_aux_iii | lemma | attempt-candidate | — | book.irrational.lem_aux_iii |
| book.irrational.Theorem_1 | theorem | no-signal | — | — |
| book.irrational.Theorem_2 | theorem | no-signal | — | — |
| book.irrational.Theorem_3 | theorem | attempt-candidate | — | — |
| euler_series | theorem | out-of-fragment | sequences-sums | euler_series |
| euler_series_2 | theorem | out-of-fragment | sequences-sums | euler_series' |
| euler_series_3 | theorem | out-of-fragment | sequences-sums | euler_series_3 |
| euler_series_4 | theorem | out-of-fragment | sequences-sums | euler_series_4 |
| four_proofs_euler_series | theorem | no-signal | — | — |
| pearl_lemma | lemma | attempt-candidate | — | — |
| cone_lemma | lemma | attempt-candidate | — | — |
| bricard_condition | theorem | no-signal | — | — |
| example1 | theorem | no-signal | — | — |
| example2 | theorem | no-signal | — | — |
| example3 | theorem | no-signal | — | — |
| hilberts_third | theorem | no-signal | — | — |
| ch11_theorem1 | theorem | attempt-candidate | — | — |
| ch11_theorem2 | theorem | attempt-candidate | — | — |
| ch11_theorem3 | theorem | out-of-fragment | sets-cardinality | — |
| ch11_theorem4 | theorem | attempt-candidate | — | — |
| slope_problem | theorem | attempt-candidate | — | — |
| euler_formula | theorem | no-signal | — | — |
| euler_consequence_a | proposition | no-signal | — | — |
| euler_consequence_b | proposition | no-signal | — | — |
| euler_consequence_c | proposition | no-signal | — | — |
| sylvester_gallai2 | theorem | attempt-candidate | — | — |
| monochromatic_lines | theorem | attempt-candidate | — | — |
| pick_lemma | lemma | out-of-fragment | sets-cardinality | — |
| pick_theorem | theorem | out-of-fragment | sets-cardinality | — |
| arm_lemma | lemma | no-signal | — | — |
| cauchy_rigidity | theorem | attempt-candidate | — | — |
| ch14theorem1 | theorem | attempt-candidate | — | — |
| borromean_nontrivial | theorem | no-signal | — | — |
| borromean | theorem | no-signal | — | — |
| ch16theorem1 | theorem | attempt-candidate | — | — |
| ch16theorem2 | theorem | no-signal | — | — |
| ch17theorem1 | theorem | out-of-fragment | sets-cardinality | — |
| ch17theorem2 | theorem | out-of-fragment | sets-cardinality | — |
| borsuk_conjecture | theorem | out-of-fragment | sets-cardinality; sequences-sums; primality | — |
| ch19theorem1 | theorem | no-signal | — | — |
| ch19theorem2 | theorem | out-of-fragment | real-analysis | — |
| ch19theorem3 | theorem | out-of-fragment | real-analysis | — |
| ch19theorem4 | theorem | attempt-candidate | — | — |
| ch19theorem5 | theorem | no-signal | — | — |
| ch19proposition1 | proposition | no-signal | — | — |
| ch19proposition2 | proposition | no-signal | — | — |
| ch19proposition3 | proposition | no-signal | — | — |
| ch19proposition4 | proposition | no-signal | — | — |
| ch19proposition5 | proposition | out-of-fragment | sets-cardinality | — |
| ch19proposition6 | proposition | no-signal | — | — |
| argand_inequality | lemma | out-of-fragment | sequences-sums | — |
| fundamental_theorem_of_algbra | theorem | out-of-fragment | algebra-structures | fundamental_theorem_of_algebra |
| valuation | definition | no-signal | — | — |
| three_coloring | definition | no-signal | — | — |
| rainbow_triangle | definition | no-signal | — | — |
| ch22lemma1 | lemma | attempt-candidate | — | — |
| ch22corollary | corollary | attempt-candidate | — | — |
| ch22lemma2 | lemma | attempt-candidate | — | — |
| monsky_theorem | theorem | attempt-candidate | — | — |
| valuation_lemma | lemma | out-of-fragment | algebra-structures; sets-cardinality | — |
| valuation_on_reals | theorem | out-of-fragment | real-analysis; algebra-structures | — |
| ch23theorem1 | theorem | attempt-candidate | — | — |
| ch23theorem2 | theorem | attempt-candidate | — | — |
| ch23corollary | corollary | attempt-candidate | — | — |
| chebyshev | theorem | no-signal | — | — |
| ch23fact1 | theorem | no-signal | — | — |
| ch23fact2 | theorem | no-signal | — | — |
| vanderwaerden | theorem | no-signal | — | Matrix.permanent_conjecture |
| gurvit | proposition | no-signal | — | — |
| ch25theorem | theorem | out-of-fragment | real-analysis; sequences-sums | — |
| ch26lemma_a | lemma | out-of-fragment | real-analysis | — |
| ch26lemma_b | lemma | no-signal | — | — |
| ch26lemma_c | lemma | attempt-candidate | — | — |
| ch26lemma_d | lemma | no-signal | — | — |
| ch26lemma_e | lemma | out-of-fragment | real-analysis | — |
| ch26 | theorem | out-of-fragment | sequences-sums | — |
| buffon_needle | theorem | out-of-fragment | probability-entropy | — |
| tiling_rectangles1 | theorem | attempt-candidate | — | — |
| tiling_rectangles2 | theorem | attempt-candidate | — | — |
| tiling_rectangles3 | theorem | attempt-candidate | — | — |
| ch31lemma | lemma | out-of-fragment | probability-entropy | — |
| ch31theorem1 | theorem | out-of-fragment | real-analysis; probability-entropy | — |
| ch31theorem2 | theorem | out-of-fragment | probability-entropy; sequences-sums | — |
| ch32lemma | lemma | out-of-fragment | sequences-sums | — |
| ch32theorem | theorem | out-of-fragment | sequences-sums | — |
| cayley_formala_proof1 | theorem | no-signal | — | — |
| cayley_formala_proof2 | theorem | no-signal | — | — |
| cayley_formala_proof3 | theorem | no-signal | — | — |
| cayley_formala_proof4 | theorem | no-signal | — | — |
| ch34theorem | theorem | out-of-fragment | sequences-sums | — |
| ch35lemma1 | lemma | no-signal | — | — |
| ch35lemma2 | lemma | out-of-fragment | sets-cardinality | — |
| kakeya | theorem | out-of-fragment | sets-cardinality | — |
| ch36lemma1 | lemma | no-signal | — | — |
| ch36lemma2 | lemma | no-signal | — | — |
| smetaniuk_theorem | theorem | no-signal | — | — |
| ch37theorem1 | theorem | out-of-fragment | sequences-sums | — |
| ch37theorem2 | theorem | out-of-fragment | sequences-sums | — |
| ch37fact_a | theorem | out-of-fragment | real-analysis | — |
| ch37fact_b | theorem | no-signal | — | — |
| ch37fact_c | theorem | out-of-fragment | real-analysis; sequences-sums | — |
| ch38definition1 | definition | out-of-fragment | probability-entropy; sets-cardinality | — |
| ch38lemma1 | lemma | no-signal | — | — |
| ch38definition2 | definition | no-signal | — | — |
| ch38lemma2 | lemma | no-signal | — | — |
| ch38theorem | theorem | no-signal | — | — |
| five_colorable | theorem | no-signal | — | — |
| museum_guards | theorem | no-signal | — | — |
| ch41proof1 | theorem | no-signal | — | — |
| ch41proof2 | theorem | no-signal | — | — |
| ch41proof3 | theorem | no-signal | — | — |
| ch41proof4 | theorem | no-signal | — | — |
| ch41proof5 | theorem | no-signal | — | — |
| turan_graph | theorem | no-signal | — | — |
| ch42theorem | theorem | no-signal | — | — |
| lyusternik_shnirelman | theorem | attempt-candidate | — | — |
| gale_theorem | theorem | attempt-candidate | — | — |
| kneser_conjecture | theorem | no-signal | — | — |
| borsuk_ulam | theorem | out-of-fragment | real-analysis | — |
| friendship | theorem | no-signal | — | chapter44.friendship_theorem |
| ch45theorem1 | theorem | no-signal | — | chapter45.theorem_1 |
| ch45theorem2 | theorem | no-signal | — | chapter45.ramsey_exists |
| ch45theorem3 | theorem | no-signal | — | — |
| ch45theorem4 | theorem | no-signal | — | — |
