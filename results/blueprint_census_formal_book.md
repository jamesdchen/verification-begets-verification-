# Blueprint fragment census

nodes: 192  ·  verdicts: attempt-candidate=1, no-signal=39, out-of-fragment=152

**lexical census, deterministic, LLM-free, Lean-free; REPORTS signals -- never a fidelity verdict.  An attempt-candidate still needs the full statement pipeline (metered) + the Lean RT lane.**

## Miss histogram (the vocabulary-growth price list)

- rational-arithmetic: 51
- graphs-combinatorics: 36
- geometry-topology: 31
- real-analysis: 29
- polynomials-fields: 26
- sequences-sums: 24
- primality: 20
- sets-cardinality: 16
- maps-functions: 9
- algebra-structures: 7
- probability-mass: 5

## Nodes

| label | kind | verdict | miss signals | lean |
|---|---|---|---|---|
| ch20theoremI | theorem | out-of-fragment | algebra-structures; geometry-topology; polynomials-fields | cauchy_schwarz_inequality |
| ch20theoremIIproof1 | theorem | out-of-fragment | real-analysis; rational-arithmetic | harmonic_geometric_arithmetic₁ |
| ch20theoremIIproof2 | theorem | out-of-fragment | real-analysis; rational-arithmetic | harmonic_geometric_arithmetic₂ |
| ch20theoremIIproof3 | theorem | out-of-fragment | real-analysis; rational-arithmetic | harmonic_geometric_arithmetic₃ |
| ch20theorem1 | theorem | out-of-fragment | real-analysis; polynomials-fields; rational-arithmetic | — |
| ch20theorem2 | theorem | out-of-fragment | polynomials-fields; rational-arithmetic | — |
| ch20theorem3proof1 | theorem | out-of-fragment | geometry-topology; graphs-combinatorics; rational-arithmetic | mantel |
| ch20theorem3proof2 | theorem | out-of-fragment | geometry-topology; graphs-combinatorics; rational-arithmetic | — |
| pigeon_hole_principle | theorem | no-signal | — | chapter28.pigeon_hole_principle |
| ch28claim1 | theorem | out-of-fragment | primality | chapter28.claim1_coprime |
| ch28claim2 | theorem | out-of-fragment | sets-cardinality | chapter28.claim2_divisible |
| ch28claim3 | theorem | out-of-fragment | real-analysis; sequences-sums | chapter28.claim3_erdos_szekeres |
| ch28claim4 | theorem | out-of-fragment | sequences-sums | chapter28.claim4_contiguous_sum |
| double_counting | theorem | out-of-fragment | sets-cardinality; sequences-sums | chapter28.double_counting |
| ch28_avg_divisors | theorem | out-of-fragment | real-analysis; sequences-sums; rational-arithmetic | chapter28.sum_divisor_count |
| handshaking | lemma | out-of-fragment | sequences-sums; graphs-combinatorics | chapter28.handshaking |
| ch28theorem | theorem | out-of-fragment | graphs-combinatorics; rational-arithmetic | chapter28.c4_free_edge_bound |
| ch28_sum_choose | theorem | out-of-fragment | sequences-sums; graphs-combinatorics | chapter28.sum_choose_deg_le_choose_card |
| sperner | lemma | out-of-fragment | geometry-topology; graphs-combinatorics | chapter28.sperner_lemma |
| brouwer | theorem | out-of-fragment | real-analysis; maps-functions | chapter28.brouwer_fixed_point_2d |
| ch30theorem1 | theorem | out-of-fragment | graphs-combinatorics | chapter30.sperner |
| ch30lemma | lemma | out-of-fragment | geometry-topology | — |
| ch30theorem2 | theorem | out-of-fragment | sets-cardinality; graphs-combinatorics | chapter30.erdos_ko_rado |
| ch30theorem3 | theorem | out-of-fragment | sets-cardinality | chapter30.hall_marriage |
| ch30corollary | corollary | no-signal | — | — |
| thm:euclids_proof | theorem | out-of-fragment | sets-cardinality; primality | infinity_of_primes₁ |
| thm:second_proof | theorem | out-of-fragment | primality | infinity_of_primes₂ |
| thm:third_proof | theorem | out-of-fragment | primality | infinity_of_primes₃ |
| thm:fourth_proof | theorem | out-of-fragment | primality; maps-functions | infinity_of_primes₄ |
| thm:fifth_proof | theorem | out-of-fragment | primality | infinity_of_primes₅ |
| thm:sixth_proof | theorem | out-of-fragment | sequences-sums; rational-arithmetic | infinity_of_primes₆ |
| thm:infty_proof | theorem | out-of-fragment | sequences-sums; primality; maps-functions | Asymptotics.infinitely_many_more_proofs |
| thm:infinity_of_primes | theorem | out-of-fragment | primality | — |
| thm:bertrands_postulate | theorem | out-of-fragment | primality | chapter2.exists_prime_lt_and_le_two_mul |
| thm:estimate_integral | theorem | out-of-fragment | real-analysis; rational-arithmetic | chapter2.harmonic_number_bounds |
| thm:estimate_factorials | theorem | out-of-fragment | rational-arithmetic | chapter2.bound_factorial |
| thm:estimate_binomial_coefficient | theorem | out-of-fragment | graphs-combinatorics; rational-arithmetic | chapter2.bound_binomial_coeff |
| sylvester | theorem | out-of-fragment | primality; graphs-combinatorics | chapter3.sylvester |
| binomial_never_powers | theorem | out-of-fragment | graphs-combinatorics | chapter3.binomials_coefficients_never_powers |
| ch04.lemma₁ | lemma | out-of-fragment | primality | ch04.lemma₁ |
| ch04.lemma2 | lemma | no-signal | — | ch04.lemma₂ |
| ch04.proposition1 | proposition | out-of-fragment | primality | ch04.theorem₁ |
| ch04.proposition2 | proposition | out-of-fragment | primality | ch04.theorem₂ |
| ch04.proposition3 | proposition | out-of-fragment | primality | — |
| sum_of_two_squares | theorem | out-of-fragment | primality; geometry-topology | — |
| fermats_little | theorem | attempt-candidate | — | book.quadratic_reciprocity.fermat_little |
| euler_criterion | theorem | out-of-fragment | rational-arithmetic | book.quadratic_reciprocity.euler_criterion |
| product_rule | theorem | out-of-fragment | rational-arithmetic | book.quadratic_reciprocity.product_rule |
| gauss_lemma | theorem | out-of-fragment | real-analysis; rational-arithmetic | book.quadratic_reciprocity.lemma_of_Gauss |
| quadratic_reciprocity1 | theorem | out-of-fragment | primality; rational-arithmetic | book.quadratic_reciprocity.quadratic_reciprocity_1 |
| mult_cyclic | theorem | out-of-fragment | algebra-structures | book.quadratic_reciprocity.mult_cyclic |
| fact_A | theorem | out-of-fragment | algebra-structures; primality | book.quadratic_reciprocity.fact_A |
| fact_B | theorem | out-of-fragment | algebra-structures; geometry-topology; polynomials-fields | book.quadratic_reciprocity.fact_B |
| quadratic_reciprocity2 | theorem | out-of-fragment | primality; rational-arithmetic | book.quadratic_reciprocity.quadratic_reciprocity_2 |
| root_of_unity | theorem | out-of-fragment | rational-arithmetic | — |
| wedderburn | theorem | no-signal | — | wedderburn |
| ch7.lemma | lemma | out-of-fragment | polynomials-fields | — |
| diagonalize_real_symmetric | theorem | out-of-fragment | polynomials-fields | chapter7.Theorem₁ |
| thm:hadamard_inequality | theorem | out-of-fragment | polynomials-fields | chapter7.Theorem₂ |
| thm:hadamard_order | theorem | out-of-fragment | polynomials-fields | — |
| thm:hadamard_existence | theorem | out-of-fragment | polynomials-fields | — |
| thm:det_greater_n_fact | theorem | out-of-fragment | polynomials-fields | chapter7.Theorem₂ |
| e_irrational | theorem | out-of-fragment | real-analysis | book.irrational.e_irrational |
| e_pow_2_irrational | theorem | out-of-fragment | real-analysis | book.irrational.e_pow_2_irrational |
| little_lemma | theorem | out-of-fragment | primality | book.irrational.little_lemma |
| e_pow_4_irrational | theorem | out-of-fragment | real-analysis | book.irrational.e_pow_4_irrational |
| lem_aux_i | lemma | out-of-fragment | sequences-sums; polynomials-fields; maps-functions; rational-arithmetic | book.irrational.lem_aux_i |
| lem_aux_ii | lemma | out-of-fragment | rational-arithmetic | book.irrational.lem_aux_ii |
| lem_aux_iii | lemma | out-of-fragment | real-analysis | book.irrational.lem_aux_iii |
| book.irrational.Theorem_1 | theorem | out-of-fragment | real-analysis | — |
| book.irrational.Theorem_2 | theorem | out-of-fragment | real-analysis | — |
| book.irrational.Theorem_3 | theorem | out-of-fragment | real-analysis; rational-arithmetic | — |
| euler_series | theorem | out-of-fragment | sequences-sums; rational-arithmetic | euler_series |
| euler_series_2 | theorem | out-of-fragment | sequences-sums; rational-arithmetic | euler_series' |
| euler_series_3 | theorem | out-of-fragment | sequences-sums; rational-arithmetic | euler_series_3 |
| euler_series_4 | theorem | out-of-fragment | sequences-sums; rational-arithmetic | euler_series_4 |
| four_proofs_euler_series | theorem | no-signal | — | — |
| pearl_lemma | lemma | out-of-fragment | geometry-topology | — |
| cone_lemma | lemma | out-of-fragment | polynomials-fields | — |
| bricard_condition | theorem | no-signal | — | — |
| example1 | theorem | no-signal | — | — |
| example2 | theorem | no-signal | — | — |
| example3 | theorem | no-signal | — | — |
| hilberts_third | theorem | no-signal | — | — |
| ch11_theorem1 | theorem | out-of-fragment | geometry-topology | — |
| ch11_theorem2 | theorem | out-of-fragment | geometry-topology | — |
| ch11_theorem3 | theorem | out-of-fragment | sets-cardinality | — |
| ch11_theorem4 | theorem | out-of-fragment | geometry-topology; graphs-combinatorics | — |
| slope_problem | theorem | out-of-fragment | geometry-topology | — |
| euler_formula | theorem | out-of-fragment | graphs-combinatorics | — |
| euler_consequence_a | proposition | out-of-fragment | graphs-combinatorics | — |
| euler_consequence_b | proposition | out-of-fragment | graphs-combinatorics | — |
| euler_consequence_c | proposition | out-of-fragment | graphs-combinatorics | — |
| sylvester_gallai2 | theorem | out-of-fragment | geometry-topology | — |
| monochromatic_lines | theorem | out-of-fragment | geometry-topology; graphs-combinatorics | — |
| pick_lemma | lemma | out-of-fragment | sets-cardinality; geometry-topology | — |
| pick_theorem | theorem | out-of-fragment | sets-cardinality; geometry-topology; graphs-combinatorics; rational-arithmetic | — |
| arm_lemma | lemma | no-signal | — | — |
| cauchy_rigidity | theorem | out-of-fragment | geometry-topology | — |
| ch14theorem1 | theorem | out-of-fragment | geometry-topology | — |
| borromean_nontrivial | theorem | no-signal | — | — |
| borromean | theorem | out-of-fragment | geometry-topology | — |
| ch16theorem1 | theorem | out-of-fragment | geometry-topology | — |
| ch16theorem2 | theorem | no-signal | — | — |
| ch17theorem1 | theorem | out-of-fragment | sets-cardinality; geometry-topology; rational-arithmetic | — |
| ch17theorem2 | theorem | out-of-fragment | sets-cardinality; graphs-combinatorics; rational-arithmetic | — |
| borsuk_conjecture | theorem | out-of-fragment | sets-cardinality; sequences-sums; primality; graphs-combinatorics; rational-arithmetic | — |
| ch19theorem1 | theorem | out-of-fragment | rational-arithmetic | — |
| ch19theorem2 | theorem | out-of-fragment | real-analysis | — |
| ch19theorem3 | theorem | out-of-fragment | real-analysis | — |
| ch19theorem4 | theorem | out-of-fragment | maps-functions | — |
| ch19theorem5 | theorem | no-signal | — | — |
| ch19proposition1 | proposition | no-signal | — | — |
| ch19proposition2 | proposition | no-signal | — | — |
| ch19proposition3 | proposition | no-signal | — | — |
| ch19proposition4 | proposition | no-signal | — | — |
| ch19proposition5 | proposition | out-of-fragment | sets-cardinality | — |
| ch19proposition6 | proposition | no-signal | — | — |
| argand_inequality | lemma | out-of-fragment | sequences-sums; polynomials-fields | — |
| fundamental_theorem_of_algbra | theorem | out-of-fragment | algebra-structures; polynomials-fields | fundamental_theorem_of_algebra |
| valuation | definition | no-signal | — | — |
| three_coloring | definition | no-signal | — | — |
| rainbow_triangle | definition | no-signal | — | — |
| ch22lemma1 | lemma | out-of-fragment | polynomials-fields | — |
| ch22corollary | corollary | out-of-fragment | geometry-topology; rational-arithmetic | — |
| ch22lemma2 | lemma | out-of-fragment | geometry-topology | — |
| monsky_theorem | theorem | out-of-fragment | geometry-topology | — |
| valuation_lemma | lemma | out-of-fragment | algebra-structures; sets-cardinality | — |
| valuation_on_reals | theorem | out-of-fragment | real-analysis; algebra-structures; rational-arithmetic | — |
| ch23theorem1 | theorem | out-of-fragment | real-analysis; polynomials-fields | — |
| ch23theorem2 | theorem | out-of-fragment | real-analysis; polynomials-fields | — |
| ch23corollary | corollary | out-of-fragment | real-analysis; polynomials-fields | — |
| chebyshev | theorem | out-of-fragment | polynomials-fields; rational-arithmetic | — |
| ch23fact1 | theorem | no-signal | — | — |
| ch23fact2 | theorem | no-signal | — | — |
| vanderwaerden | theorem | out-of-fragment | polynomials-fields; rational-arithmetic | Matrix.permanent_conjecture |
| gurvit | proposition | no-signal | — | — |
| ch25theorem | theorem | out-of-fragment | real-analysis; sequences-sums; graphs-combinatorics; polynomials-fields | — |
| ch26lemma_a | lemma | out-of-fragment | real-analysis; maps-functions | — |
| ch26lemma_b | lemma | no-signal | — | — |
| ch26lemma_c | lemma | out-of-fragment | maps-functions | — |
| ch26lemma_d | lemma | out-of-fragment | maps-functions; rational-arithmetic | — |
| ch26lemma_e | lemma | out-of-fragment | real-analysis; maps-functions | — |
| ch26 | theorem | out-of-fragment | sequences-sums; rational-arithmetic | — |
| buffon_needle | theorem | out-of-fragment | probability-mass; rational-arithmetic | — |
| tiling_rectangles1 | theorem | out-of-fragment | geometry-topology | — |
| tiling_rectangles2 | theorem | out-of-fragment | geometry-topology | — |
| tiling_rectangles3 | theorem | out-of-fragment | geometry-topology | — |
| ch31lemma | lemma | out-of-fragment | probability-mass | — |
| ch31theorem1 | theorem | out-of-fragment | real-analysis; probability-mass | — |
| ch31theorem2 | theorem | out-of-fragment | probability-mass; sequences-sums; rational-arithmetic | — |
| ch32lemma | lemma | out-of-fragment | sequences-sums; graphs-combinatorics; polynomials-fields | — |
| ch32theorem | theorem | out-of-fragment | sequences-sums; graphs-combinatorics; polynomials-fields | — |
| cayley_formala_proof1 | theorem | no-signal | — | — |
| cayley_formala_proof2 | theorem | no-signal | — | — |
| cayley_formala_proof3 | theorem | no-signal | — | — |
| cayley_formala_proof4 | theorem | no-signal | — | — |
| ch34theorem | theorem | out-of-fragment | sequences-sums; rational-arithmetic | — |
| ch35lemma1 | lemma | out-of-fragment | polynomials-fields | — |
| ch35lemma2 | lemma | out-of-fragment | sets-cardinality; graphs-combinatorics; polynomials-fields | — |
| kakeya | theorem | out-of-fragment | sets-cardinality; graphs-combinatorics; rational-arithmetic | — |
| ch36lemma1 | lemma | out-of-fragment | geometry-topology | — |
| ch36lemma2 | lemma | out-of-fragment | rational-arithmetic | — |
| smetaniuk_theorem | theorem | no-signal | — | — |
| ch37theorem1 | theorem | out-of-fragment | sequences-sums; polynomials-fields | — |
| ch37theorem2 | theorem | out-of-fragment | sequences-sums; rational-arithmetic | — |
| ch37fact_a | theorem | out-of-fragment | real-analysis | — |
| ch37fact_b | theorem | no-signal | — | — |
| ch37fact_c | theorem | out-of-fragment | real-analysis; sequences-sums | — |
| ch38definition1 | definition | out-of-fragment | probability-mass; sets-cardinality; graphs-combinatorics | — |
| ch38lemma1 | lemma | out-of-fragment | graphs-combinatorics | — |
| ch38definition2 | definition | no-signal | — | — |
| ch38lemma2 | lemma | no-signal | — | — |
| ch38theorem | theorem | no-signal | — | — |
| five_colorable | theorem | out-of-fragment | graphs-combinatorics | — |
| museum_guards | theorem | out-of-fragment | rational-arithmetic | — |
| ch41proof1 | theorem | out-of-fragment | graphs-combinatorics; rational-arithmetic | — |
| ch41proof2 | theorem | out-of-fragment | graphs-combinatorics; rational-arithmetic | — |
| ch41proof3 | theorem | out-of-fragment | graphs-combinatorics; rational-arithmetic | — |
| ch41proof4 | theorem | out-of-fragment | graphs-combinatorics; rational-arithmetic | — |
| ch41proof5 | theorem | out-of-fragment | graphs-combinatorics; rational-arithmetic | — |
| turan_graph | theorem | no-signal | — | — |
| ch42theorem | theorem | out-of-fragment | rational-arithmetic | — |
| lyusternik_shnirelman | theorem | out-of-fragment | geometry-topology | — |
| gale_theorem | theorem | out-of-fragment | geometry-topology | — |
| kneser_conjecture | theorem | no-signal | — | — |
| borsuk_ulam | theorem | out-of-fragment | real-analysis; geometry-topology | — |
| friendship | theorem | out-of-fragment | graphs-combinatorics | chapter44.friendship_theorem |
| ch45theorem1 | theorem | no-signal | — | chapter45.theorem_1 |
| ch45theorem2 | theorem | no-signal | — | chapter45.ramsey_exists |
| ch45theorem3 | theorem | out-of-fragment | graphs-combinatorics | — |
| ch45theorem4 | theorem | out-of-fragment | graphs-combinatorics; rational-arithmetic | — |
