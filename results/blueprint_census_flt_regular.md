# Blueprint fragment census

nodes: 45  ·  verdicts: out-of-fragment=45

**lexical census, deterministic, LLM-free, Lean-free; REPORTS signals -- never a fidelity verdict.  An attempt-candidate still needs the full statement pipeline (metered) + the Lean RT lane.**

## Miss histogram (the vocabulary-growth price list)

- polynomials-fields: 30
- primality: 23
- algebra-structures: 20
- real-analysis: 7
- sequences-sums: 5
- rational-arithmetic: 3
- maps-functions: 1
- sets-cardinality: 1

## Nodes

| label | kind | verdict | miss signals | lean |
|---|---|---|---|---|
| lemma:alt_definition_of_norm | lemma | out-of-fragment | algebra-structures; sequences-sums | Algebra.norm_eq_prod_embeddings |
| lemma:alt_definition_of_trace | lemma | out-of-fragment | algebra-structures; sequences-sums | trace_eq_sum_embeddings |
| defn_of_disc | definition | out-of-fragment | polynomials-fields | Algebra.discr |
| lem:lin_indep_iff_disc_ne_zero | lemma | out-of-fragment | algebra-structures | Algebra.discr_not_zero_of_basis |
| lem:disc_change_of_basis | lemma | out-of-fragment | algebra-structures; polynomials-fields | Algebra.discr_of_matrix_mulVec |
| lemma:disc_via_embs | lemma | out-of-fragment | algebra-structures; polynomials-fields | Algebra.discr_eq_det_embeddingsMatrixReindex_pow_two |
| lemma:disc_of_prim_elt_basis | lemma | out-of-fragment | algebra-structures; sequences-sums | Algebra.discr_powerBasis_eq_prod |
| lemma:diff_of_irr_pol | lemma | out-of-fragment | algebra-structures; sequences-sums; primality; polynomials-fields | Polynomial.aeval_root_derivative_of_splits |
| lemma:num_field_disc_in_terms_of_norm | lemma | out-of-fragment | real-analysis; algebra-structures; polynomials-fields; rational-arithmetic | Algebra.discr_powerBasis_eq_norm |
| lemma:norm_of_alg_int_is_int | lemma | out-of-fragment | algebra-structures | Algebra.isIntegral_norm |
| lemma:trace_of_alg_int_is_int | lemma | out-of-fragment | algebra-structures | Algebra.isIntegral_trace |
| lemma:int_basis_int_disc | lemma | out-of-fragment | algebra-structures | Algebra.discr_isIntegral |
| lemma:disc_int_basis | lemma | out-of-fragment | algebra-structures; polynomials-fields | Algebra.discr_mul_isIntegral_mem_adjoin |
| lemma:eis_crit_and_alg_ints | lemma | out-of-fragment | algebra-structures; polynomials-fields | mem_adjoin_of_smul_prime_pow_smul_of_minpoly_isEisensteinAt |
| lemma:cyclo_poly_deg | lemma | out-of-fragment | polynomials-fields; maps-functions | Polynomial.degree_cyclotomic |
| lemma:cyclo_poly_irr | lemma | out-of-fragment | primality; polynomials-fields | Polynomial.cyclotomic.irreducible |
| lem:discr_of_cyclo | lemma | out-of-fragment | primality; polynomials-fields; rational-arithmetic | IsCyclotomicExtension.Rat.discr_prime_pow' |
| theorem:ring_of_ints_of_cyclo | theorem | out-of-fragment | primality; polynomials-fields | IsCyclotomicExtension.Rat.isIntegralClosure_adjoin_singleton_of_prime_pow |
| lemma:alg_int_abs_val_one | lemma | out-of-fragment | real-analysis; polynomials-fields | mem_roots_of_unity_of_abs_eq_one |
| lem:roots_of_unity_in_cyclo | lemma | out-of-fragment | primality; polynomials-fields | roots_of_unity_in_cyclo |
| lemma:unit_lemma | lemma | out-of-fragment | polynomials-fields | unit_lemma_gal_conj |
| lemma:zeta_pow_sub_eq_unit_zeta_sub_one | lemma | out-of-fragment | primality; polynomials-fields | is_primitive_root.zeta_pow_sub_eq_unit_zeta_sub_one |
| lemma:ideals_mult_to_power | lemma | out-of-fragment | primality | ideal.exists_eq_pow_of_mul_eq_pow |
| lem:flt_ideals_coprime | lemma | out-of-fragment | primality; polynomials-fields | fltIdeals_coprime |
| lem:exists_int_sub_pow_prime_dvd | lemma | out-of-fragment | primality; polynomials-fields | exists_int_sub_pow_prime_dvd |
| lem:dvd_coeff_cycl_integer | lemma | out-of-fragment | sequences-sums; primality; polynomials-fields | dvd_coeff_cycl_integer |
| lem:exists_int_sum_eq_zero | lemma | out-of-fragment | primality; polynomials-fields | FltRegular.CaseI.exists_int_sum_eq_zero |
| lemma:may_assume_coprime | lemma | out-of-fragment | primality; polynomials-fields | FltRegular.CaseI.may_assume |
| defn:is_regular_number | definition | out-of-fragment | primality; polynomials-fields | IsRegularNumber |
| theorem:FLT_case_one | theorem | out-of-fragment | primality | FltRegular.caseI |
| thm:Kummers_lemma | theorem | out-of-fragment | primality; polynomials-fields | eq_pow_prime_of_unit_of_congruent |
| lem:gen_dvd_by_frak_p | lemma | out-of-fragment | real-analysis; primality; polynomials-fields | — |
| lem:gen_ideal_coprimality | lemma | out-of-fragment | real-analysis; primality; polynomials-fields; rational-arithmetic | — |
| thm:gen_flt_eqn | theorem | out-of-fragment | real-analysis; primality; polynomials-fields | — |
| theorem:FLT_case_two | theorem | out-of-fragment | primality | FltRegular.caseII |
| FLT_regular | theorem | out-of-fragment | primality | flt_regular |
| lem:exists_alg_int | lemma | out-of-fragment | algebra-structures; polynomials-fields | exists_alg_int |
| Hilbert90 | theorem | out-of-fragment | algebra-structures | Hilbert90 |
| lem:Hilbert92 | theorem | out-of-fragment | real-analysis; algebra-structures; polynomials-fields | Hilbert92 |
| def:rel_different | definition | out-of-fragment | algebra-structures; sets-cardinality | — |
| lem:diff_ideal_eqn | lemma | out-of-fragment | algebra-structures; polynomials-fields | — |
| lem:diff_ram | lemma | out-of-fragment | algebra-structures; primality | — |
| lem:loc_ramification | lemma | out-of-fragment | algebra-structures; primality | — |
| lem:ramification_lem | lemma | out-of-fragment | primality; polynomials-fields | — |
| Kummer_alt | lemma | out-of-fragment | real-analysis; polynomials-fields | — |
