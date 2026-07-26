# Blueprint fragment census

nodes: 944  ·  verdicts: attempt-candidate=27, no-signal=127, out-of-fragment=790

**lexical census, deterministic, LLM-free, Lean-free; REPORTS signals -- never a fidelity verdict.  An attempt-candidate still needs the full statement pipeline (metered) + the Lean RT lane.**

## Miss histogram (the vocabulary-growth price list)

- real-analysis: 523
- rational-arithmetic: 409
- entropy-log: 388
- sequences-sums: 234
- polynomials-fields: 130
- maps-functions: 113
- primality: 101
- geometry-topology: 20
- algebra-structures: 6
- sets-cardinality: 5
- algebra-abstract: 2
- probability-mass: 1

## Nodes

| label | kind | verdict | miss signals | lean |
|---|---|---|---|---|
| IsAdditive | definition | out-of-fragment | primality; maps-functions | ArithmeticFunction.IsAdditive |
| IsCompletelyAdditive | definition | out-of-fragment | maps-functions | ArithmeticFunction.IsCompletelyAdditive |
| IsCompletelyAdditive.isAdditive | theorem | out-of-fragment | maps-functions | ArithmeticFunction.IsCompletelyAdditive.isAdditive |
| unique_divisor_decomposition | theorem | out-of-fragment | primality | ArithmeticFunction.unique_divisor_decomposition |
| sum_divisors_mul_of_coprime | theorem | out-of-fragment | sequences-sums; primality; maps-functions | ArithmeticFunction.sum_divisors_mul_of_coprime |
| sum_moebius_pmul_eq_prod_one_sub | theorem | out-of-fragment | sequences-sums; maps-functions | ArithmeticFunction.sum_moebius_pmul_eq_prod_one_sub |
| zeta_mul_zeta | theorem | out-of-fragment | polynomials-fields; maps-functions | ArithmeticFunction.zeta_mul_zeta |
| LSeries_tau_eq_riemannZeta_sq | theorem | out-of-fragment | sequences-sums; maps-functions | ArithmeticFunction.LSeries_tau_eq_riemannZeta_sq |
| d | definition | out-of-fragment | polynomials-fields; maps-functions | ArithmeticFunction.d |
| d_zero | theorem | no-signal | — | ArithmeticFunction.d_zero |
| d_one | theorem | out-of-fragment | polynomials-fields | ArithmeticFunction.d_one |
| d_two | theorem | out-of-fragment | maps-functions | ArithmeticFunction.d_two |
| d_succ | theorem | out-of-fragment | polynomials-fields | ArithmeticFunction.d_succ |
| LSeries_d_summable | theorem | out-of-fragment | sequences-sums | ArithmeticFunction.LSeries_d_summable |
| LSeries_d_eq_riemannZeta_pow | theorem | out-of-fragment | sequences-sums; polynomials-fields | ArithmeticFunction.LSeries_d_eq_riemannZeta_pow |
| d_isMultiplicative | theorem | no-signal | — | ArithmeticFunction.d_isMultiplicative |
| d_apply_prime_pow | theorem | out-of-fragment | primality | ArithmeticFunction.d_apply_prime_pow |
| d_apply | theorem | no-signal | — | ArithmeticFunction.d_apply |
| sigmaR | definition | out-of-fragment | polynomials-fields | ArithmeticFunction.sigmaR |
| sigmaR_natCast | theorem | attempt-candidate | — | ArithmeticFunction.sigmaR_natCast |
| sigmaR_apply | theorem | out-of-fragment | sequences-sums | ArithmeticFunction.sigmaR_apply |
| sigmaR_natCast' | theorem | no-signal | — | ArithmeticFunction.sigmaR_natCast' |
| sigmaR_apply_prime_pow | theorem | out-of-fragment | sequences-sums; primality | ArithmeticFunction.sigmaR_apply_prime_pow |
| sigmaR_one_apply | theorem | no-signal | — | ArithmeticFunction.sigmaR_one_apply |
| sigmaR_one_apply_prime_pow | theorem | no-signal | — | ArithmeticFunction.sigmaR_one_apply_prime_pow |
| sigmaR_eq_sum_div | theorem | out-of-fragment | sequences-sums | ArithmeticFunction.sigmaR_eq_sum_div |
| sigmaR_zero_apply | theorem | no-signal | — | ArithmeticFunction.sigmaR_zero_apply |
| sigmaR_zero_apply_prime_pow | theorem | no-signal | — | ArithmeticFunction.sigmaR_zero_apply_prime_pow |
| sigmaR_one | theorem | no-signal | — | ArithmeticFunction.sigmaR_one |
| powR | definition | out-of-fragment | polynomials-fields; maps-functions | ArithmeticFunction.powR |
| isMultiplicative_powR | theorem | out-of-fragment | maps-functions | ArithmeticFunction.isMultiplicative_powR |
| sigmaR_eq_zeta_mul_powR | theorem | out-of-fragment | polynomials-fields; maps-functions | ArithmeticFunction.sigmaR_eq_zeta_mul_powR |
| isMultiplicative_sigmaR | theorem | out-of-fragment | maps-functions | ArithmeticFunction.isMultiplicative_sigmaR |
| sigmaR_eq_prod_primeFactors_sum_range_factorization_pow_mul | theorem | out-of-fragment | sequences-sums | ArithmeticFunction.sigmaR_eq_prod_primeFactors_sum_range_factorization_pow_mul |
| LSeries_powR_eq | theorem | out-of-fragment | polynomials-fields | ArithmeticFunction.LSeries_powR_eq |
| abscissa_powR_le | theorem | no-signal | — | ArithmeticFunction.abscissa_powR_le |
| LSeries_sigma_eq_riemannZeta_mul | theorem | out-of-fragment | sequences-sums; polynomials-fields | ArithmeticFunction.LSeries_sigma_eq_riemannZeta_mul |
| zeta_mul_zeta_mul_zeta_mul_zeta_eq | theorem | out-of-fragment | sequences-sums; polynomials-fields | ArithmeticFunction.zeta_mul_zeta_mul_zeta_mul_zeta_eq |
| zeta_pow_four_eq | theorem | out-of-fragment | sequences-sums; polynomials-fields | ArithmeticFunction.zeta_pow_four_eq |
| zeta_mul_tau_square_eq | theorem | out-of-fragment | sequences-sums; polynomials-fields | ArithmeticFunction.zeta_mul_tau_square_eq |
| zeta_pow_three_eq | theorem | out-of-fragment | sequences-sums; polynomials-fields | ArithmeticFunction.zeta_pow_three_eq |
| zeta_pow_three_eq_alt | theorem | out-of-fragment | sequences-sums; polynomials-fields; maps-functions | ArithmeticFunction.zeta_pow_three_eq_alt |
| two_pow_omega_le_sigma_zero | theorem | no-signal | — | ArithmeticFunction.two_pow_omega_le_sigma_zero |
| LSeriesSummable_two_pow_omega | theorem | out-of-fragment | real-analysis; sequences-sums | ArithmeticFunction.LSeriesSummable.of_norm_le_norm, ArithmeticFunction.LSeriesSummable_two_pow_omega |
| LSeries.term_isMultiplicative_if_fun_isMultiplicative | theorem | out-of-fragment | maps-functions | ArithmeticFunction.LSeries.term_isMultiplicative_if_fun_isMultiplicative |
| powOfAdditive_isMultiplicative | theorem | out-of-fragment | maps-functions | ArithmeticFunction.powOfAdditive_isMultiplicative |
| two_pow_omega_isMultiplicative | theorem | out-of-fragment | maps-functions | ArithmeticFunction.two_pow_omega_isMultiplicative |
| two_pow_omega_LSeries.term_isMultiplicative | theorem | out-of-fragment | maps-functions | ArithmeticFunction.two_pow_omega_LSeries.term_isMultiplicative |
| sumOnPrimePows | definition | out-of-fragment | primality; maps-functions | ArithmeticFunction.sumOnPrimePows |
| sumOnPrimePows_apply | theorem | out-of-fragment | primality | ArithmeticFunction.sumOnPrimePows_apply |
| two_pow_omega_tsum_prime_pow | theorem | out-of-fragment | sequences-sums; primality; rational-arithmetic | ArithmeticFunction.two_pow_omega_tsum_prime_pow |
| Complex.one_add_prime_cpow_ne_zero | theorem | out-of-fragment | primality; polynomials-fields | ArithmeticFunction.Complex.one_add_prime_cpow_ne_zero |
| two_pow_omega_LSeries_eulerProduct_tprod | theorem | out-of-fragment | sequences-sums; rational-arithmetic | ArithmeticFunction.two_pow_omega_LSeries_eulerProduct_tprod |
| two_pow_omega_LSeries_eulerProduct_hasProd | theorem | out-of-fragment | sequences-sums; rational-arithmetic | ArithmeticFunction.two_pow_omega_LSeries_eulerProduct_hasProd |
| zeta_pow_two | theorem | out-of-fragment | sequences-sums; polynomials-fields | ArithmeticFunction.zeta_pow_two |
| LSeriesSummable_moebius_sq | theorem | out-of-fragment | sequences-sums | ArithmeticFunction.LSeriesSummable_moebius_sq |
| powOfMultiplicative_isMultiplicative | theorem | out-of-fragment | maps-functions | ArithmeticFunction.powOfMultiplicative_isMultiplicative |
| moebius_sq_LSeries.term_isMultiplicative | theorem | out-of-fragment | maps-functions | ArithmeticFunction.moebius_sq_LSeries.term_isMultiplicative |
| moebius_sq_tsum_prime_pow | theorem | out-of-fragment | sequences-sums; primality | ArithmeticFunction.moebius_sq_tsum_prime_pow |
| moebius_sq_LSeries_eulerProduct_tprod | theorem | out-of-fragment | sequences-sums | ArithmeticFunction.moebius_sq_LSeries_eulerProduct_tprod |
| moebius_sq_LSeries_eulerProduct_hasProd | theorem | out-of-fragment | sequences-sums | ArithmeticFunction.moebius_sq_LSeries_eulerProduct_hasProd |
| zeta_alt | theorem | out-of-fragment | sequences-sums; polynomials-fields | ArithmeticFunction.zeta_alt |
| pow_divisors_mul | theorem | out-of-fragment | primality | ArithmeticFunction.pow_divisors_mul |
| divisors_mul_injective | theorem | out-of-fragment | primality; maps-functions | ArithmeticFunction.divisors_mul_injective |
| pow_divisors_mul_injective | theorem | out-of-fragment | primality; maps-functions | ArithmeticFunction.pow_divisors_mul_injective |
| sum_moebius_sq_divisors | definition | out-of-fragment | sequences-sums; maps-functions | ArithmeticFunction.sum_moebius_sq_divisors |
| sum_moebius_sq_divisors_apply | theorem | no-signal | — | ArithmeticFunction.sum_moebius_sq_divisors_apply |
| sum_moebius_sq_divisors_IsMultiplicative | theorem | out-of-fragment | sequences-sums; maps-functions | ArithmeticFunction.sum_moebius_sq_divisors_IsMultiplicative |
| sum_moebius_sq_divisors_apply_prime_pow | theorem | out-of-fragment | primality | ArithmeticFunction.sum_moebius_sq_divisors_apply_prime_pow |
| moebius_sq_eq | theorem | out-of-fragment | sequences-sums | ArithmeticFunction.moebius_sq_eq |
| liouville | theorem | out-of-fragment | maps-functions | ArithmeticFunction.liouville |
| IsCompletelyMultiplicative | definition | out-of-fragment | maps-functions | ArithmeticFunction.IsCompletelyMultiplicative |
| IsCompletelyMultiplicative.isMultiplicative | theorem | out-of-fragment | maps-functions | ArithmeticFunction.IsCompletelyMultiplicative.isMultiplicative |
| isCompletelyMultiplicative_liouville | theorem | out-of-fragment | maps-functions | ArithmeticFunction.isCompletelyMultiplicative_liouville |
| LSeries_liouville_eq | theorem | out-of-fragment | sequences-sums; polynomials-fields; maps-functions | ArithmeticFunction.LSeries_liouville_eq |
| liouville_eq_moebius_on_squarefree | theorem | out-of-fragment | maps-functions | ArithmeticFunction.liouville_eq_moebius_on_squarefree |
| LSeries_totient_eq | theorem | out-of-fragment | sequences-sums; polynomials-fields | ArithmeticFunction.LSeries_totient_eq |
| finsum_range_eq_sum_range | lemma | out-of-fragment | real-analysis; sequences-sums; maps-functions | finsum_range_eq_sum_range |
| chebyshev-asymptotic | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums | chebyshev_asymptotic |
| primorial_bounds | corollary | out-of-fragment | sequences-sums | primorial_bounds |
| pi_asymp | theorem | out-of-fragment | real-analysis; entropy-log; maps-functions; rational-arithmetic | pi_asymp |
| pi_alt | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | pi_alt |
| pn_asymptotic | proposition | out-of-fragment | real-analysis; entropy-log | pn_asymptotic |
| pn_pn_plus_one | corollary | no-signal | — | pn_pn_plus_one |
| prime_between | corollary | out-of-fragment | real-analysis; primality | prime_between |
| mun | proposition | out-of-fragment | sequences-sums; rational-arithmetic | sum_mobius_div_self_le |
| mu-pnt | proposition | out-of-fragment | sequences-sums | mu_pnt |
| lambda-pnt | proposition | out-of-fragment | sequences-sums | lambda_pnt |
| mu-pnt-alt | proposition | out-of-fragment | sequences-sums | mu_pnt_alt |
| chebyshev-asymptotic-pnt | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | chebyshev_asymptotic_pnt |
| dirichlet_thm | corollary | out-of-fragment | primality | dirichlet_thm |
| Chebotarev-cyclic | lemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; primality; rational-arithmetic | — |
| first-gap-def | definition | out-of-fragment | primality | first_gap |
| pi-def | definition | out-of-fragment | primality | pi |
| pi-star-def | definition | out-of-fragment | sequences-sums | pi_star |
| li-def | definition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | li, Li |
| Epsi-def | definition | no-signal | — | Eψ |
| classical-bound-psi | definition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Eψ.classicalBound |
| Epi-def | definition | out-of-fragment | real-analysis; entropy-log | Eπ |
| Etheta-def | definition | no-signal | — | Eθ |
| classical-bound-theta | definition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Eθ.classicalBound |
| classical-bound-pi | definition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Eπ.classicalBound |
| admissible-bound-monotone | lemma | no-signal | — | admissible_bound.mono |
| classical-to-numeric | lemma | no-signal | — | Eψ.classicalBound.to_numericalBound, Eθ.classicalBound.to_numericalBound, Eπ.classicalBound.to_numericalBound |
| Mertens-sum-log | lemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Mertens.sum_log_eq |
| Mertens-sum-log-le | lemma | out-of-fragment | real-analysis; entropy-log; sequences-sums | Mertens.sum_log_le |
| Mertens-sum-log-ge | corollary | out-of-fragment | real-analysis; entropy-log; sequences-sums | Mertens.sum_log_ge |
| Mertens-sum-log-eq-log-factorial | proposition | out-of-fragment | real-analysis; entropy-log; sequences-sums | Mertens.sum_log_eq_log_factorial |
| Mertens-sum-log-eq-sum-mangoldt | lemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Mertens.sum_log_eq_sum_mangoldt |
| Mertens-first-error-mangoldt | definition | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Mertens.E₁Λ, Mertens.E₁Λ.bounded, Mertens.sum_mangoldt_div_eq_log' |
| Mertens-first-error-mangoldt-ge | corollary | no-signal | — | Mertens.E₁Λ.ge |
| Mertens-first-error-mangoldt-le | corollary | out-of-fragment | real-analysis; entropy-log | Mertens.E₁Λ.le |
| Mertens-first-theorem-mangoldt | corollary | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Mertens.sum_mangoldt_div_eq_log |
| Mertens-first-error-prime | definition | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Mertens.E₁p |
| Mertens-first-error-prime-le-mangoldt | corollary | no-signal | — | Mertens.E₁p.le_E₁Λ |
| Mertens-first-error-prime-le | corollary | out-of-fragment | real-analysis; entropy-log | Mertens.E₁p.le |
| E1_summable | proposition | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Mertens.E₁.summable |
| E1_bound | proposition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Mertens.E₁.le |
| Mertens-first-error-prime-ge | corollary | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Mertens.E₁Λ.le_E₁p_add_E₁ |
| Mertens-first-theorem-prime-bounded | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Mertens.sum_log_prime_div_eq_log, Mertens.sum_log_prime_div_eq_log', Mertens.sum_log_prime_div_eq_log'' |
| Euler-Mascheroni-const-alt | definition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Mertens.γ |
| Mertens-second-error-mangoldt | definition | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Mertens.E₂Λ, Mertens.E₂p |
| Mertens-integral-ident | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | _private.PrimeNumberTheoremAnd.IEANTN.Mertens.0.Mertens.sum_div_log_eq |
| Mertens-second-error-mangoldt-eq | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Mertens.E₂Λ.eq |
| Mertens-second-error-mangoldt-bound | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Mertens.E₂Λ.abs_le, Mertens.E₂Λ.bound, Mertens.E₂Λ.bound' |
| log-zeta-eq-1 | sublemma | out-of-fragment | real-analysis; entropy-log; polynomials-fields | Mertens.log_zeta_eq_sum |
| log-zeta-eq-2 | sublemma | out-of-fragment | real-analysis; entropy-log; polynomials-fields | _private.PrimeNumberTheoremAnd.IEANTN.Mertens.0.Mertens.log_zeta_eq_integ |
| log-zeta-eq-3 | sublemma | out-of-fragment | real-analysis; entropy-log | _private.PrimeNumberTheoremAnd.IEANTN.Mertens.0.Mertens.mul_integ_log_log_eq |
| log-zeta-eq-4 | sublemma | attempt-candidate | — | _private.PrimeNumberTheoremAnd.IEANTN.Mertens.0.Mertens.mul_integ_gamma_eq |
| log-zeta-eq | theorem | out-of-fragment | real-analysis; entropy-log; polynomials-fields | _private.PrimeNumberTheoremAnd.IEANTN.Mertens.0.Mertens.log_zeta_eq |
| log-zeta-limit | sublemma | out-of-fragment | real-analysis; entropy-log; polynomials-fields | _private.PrimeNumberTheoremAnd.IEANTN.Mertens.0.Mertens.log_zeta_limit |
| Euler-Mascheroni-eq | theorem | no-signal | — | Mertens.deriv_gamma_add_γ_eq_zero |
| Mertens-second-theorem-mangoldt-weak | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Mertens.sum_mangoldt_div_log_eq_log_log, Mertens.sum_mangoldt_div_log_eq_log_log', Mertens.sum_mangoldt_div_log_eq_log_log'' |
| Meissel-Mertens-constant | definition | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Mertens.M, meisselMertensConstant |
| Mertens-second-constant-prime-le | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Mertens.M.le |
| Mertens-second-constant-prime-ge | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Mertens.M.ge |
| Mertens-second-error-prime-eq | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Mertens.E₂p.eq |
| Mertens-second-error-prime-abs-le | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Mertens.E₂p.abs_le, Mertens.E₂p.bound, Mertens.E₂p.bound' |
| Mertens-second-theorem-prime-weak | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Mertens.sum_prime_div_eq_log_log, Mertens.sum_prime_div_eq_log_log', Mertens.sum_prime_div_eq_log_log'' |
| Meissel-Mertens-eq | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Mertens.M.eq |
| Mertens-third-error | definition | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Mertens.E₃ |
| Mertens-third-theorem-error | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Mertens.prod_one_minus_div_prime_eq |
| Mertens-third-theorem-error-le | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Mertens.E₃.abs_le, Mertens.E₃.bound, Mertens.E₃.bound', Mertens.E₃.bound'', Mertens.E₃.bound''' |
| Q-def | definition | attempt-candidate | — | MobiusLemma.Q |
| R-def | definition | out-of-fragment | polynomials-fields | MobiusLemma.R |
| M-def | definition | out-of-fragment | maps-functions | MobiusLemma.M |
| mobius-lemma-1-sub | sublemma | out-of-fragment | sequences-sums; rational-arithmetic | MobiusLemma.mobius_lemma_1_sub |
| mobius-lemma-1 | lemma | out-of-fragment | sequences-sums; rational-arithmetic | MobiusLemma.mobius_lemma_1 |
| mobius-lemma-2-sub-1 | sublemma | out-of-fragment | sequences-sums; rational-arithmetic | MobiusLemma.mobius_lemma_2_sub_1 |
| mobius-lemma-2-sub-2 | sublemma | out-of-fragment | sequences-sums; rational-arithmetic | MobiusLemma.mobius_lemma_2_sub_2 |
| mobius-lemma-2 | lemma | out-of-fragment | sequences-sums; rational-arithmetic | MobiusLemma.mobius_lemma_2 |
| fks-theorem-2-7 | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | FKS.theorem_2_7 |
| fks-remark-2-8 | definition | no-signal | — | FKS.theorem_2_7_holds |
| fks-corollary-2-9 | definition | out-of-fragment | real-analysis; entropy-log | FKS.corollary_2_9 |
| fks-lemma-2-1 | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums | FKS.lemma_2_1 |
| fks-corollary_2_3 | theorem | out-of-fragment | sequences-sums | FKS.corollary_2_3 |
| fks-lemma-2-5 | theorem | no-signal | — | FKS.lemma_2_5 |
| fks-remark-2-6-a | theorem | no-signal | — | FKS.remark_2_6_a |
| fks-remark-2-6-b | theorem | no-signal | — | FKS.remark_2_6_b |
| fks-theorem-3-1 | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums | FKS.theorem_3_1 |
| fks-theorem-3-2 | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums | FKS.theorem_3_2 |
| fks-proposition-3-4 | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums | FKS.proposition_3_4 |
| fks-proposition-3-6 | theorem | no-signal | — | FKS.proposition_3_6 |
| fks-eq13 | theorem | out-of-fragment | sequences-sums; rational-arithmetic | FKS.eq_13 |
| fks-remark-3-7 | theorem | out-of-fragment | real-analysis; entropy-log | FKS.remark_3_7 |
| fks-proposition-3-8 | theorem | out-of-fragment | sequences-sums | FKS.proposition_3_8 |
| fks-corollary-3-10 | theorem | no-signal | — | FKS.corollary_3_10 |
| fks-proposition-3-11 | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums | FKS.proposition_3_11 |
| fks-corollary-3-12 | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | FKS.corollary_3_12 |
| fks-proposition-3-14 | theorem | out-of-fragment | real-analysis; entropy-log; maps-functions; rational-arithmetic | FKS.proposition_3_14 |
| fks-theorem-1-1 | theorem | out-of-fragment | real-analysis; entropy-log | FKS.theorem_1_1 |
| fks-theorem-1-1b | theorem | out-of-fragment | real-analysis | FKS.theorem_1_1b |
| fks-lemma-5-2 | theorem | out-of-fragment | real-analysis; entropy-log | FKS.lemma_5_2 |
| fks-lemma-5-3 | theorem | out-of-fragment | real-analysis; entropy-log | FKS.lemma_5_3 |
| fks-theorem-1-2b | theorem | out-of-fragment | real-analysis; entropy-log | FKS.theorem_1_2b |
| fks_cor_14 | theorem | out-of-fragment | real-analysis; entropy-log | FKS.FKS_corollary_1_4 |
| fks_cor_14' | theorem | out-of-fragment | real-analysis; entropy-log | FKS.FKS_corollary_1_3 |
| bklnw-table-8-compat | sublemma | out-of-fragment | real-analysis | BKLNW_app.table_8_ε.le_simp |
| bklnw-eq_A_7 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | BKLNW_app.bklnw_eq_A_7 |
| bklnw-eq_A_8 | definition | out-of-fragment | rational-arithmetic | BKLNW_app.bklnw_eq_A_8 |
| bklnw-sigma_1_def | definition | out-of-fragment | sequences-sums; rational-arithmetic | BKLNW_app.Sigma₁ |
| bklnw-sigma_2_def | definition | out-of-fragment | sequences-sums; rational-arithmetic | BKLNW_app.Sigma₂ |
| bklnw-eq_A_9 | sublemma | out-of-fragment | sequences-sums; rational-arithmetic | BKLNW_app.bklnw_eq_A_9 |
| bklnw-eq_A_10 | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW_app.bklnw_eq_A_10 |
| bklnw-eq_A_11 | definition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW_app.s₁ |
| bklnw-eq_A_12 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | BKLNW_app.bklnw_eq_A_12 |
| bklnw-eq_A_13 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | BKLNW_app.bklnw_eq_A_13 |
| bklnw-eq_A_14 | definition | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | BKLNW_app.Inputs.s₂ |
| bklnw-thm-13 | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW_app.bklnw_thm_15 |
| bklnw-eq_A_16 | definition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW_app.Inputs.k |
| bklnw-eq_A_17 | definition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW_app.Inputs.c3 |
| bklnw-eq_A_18 | definition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW_app.Inputs.c4 |
| bklnw-eq_A_19 | definition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW_app.Inputs.c5 |
| bklnw-eq_A_20 | definition | no-signal | — | BKLNW_app.Inputs.A |
| bklnw-eq_A_21 | definition | out-of-fragment | rational-arithmetic | BKLNW_app.Inputs.B, BKLNW_app.Inputs.C |
| bklnw-thm-14 | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW_app.thm_14 |
| bklnw-eq_A_26 | theorem | no-signal | — | BKLNW_app.bklnw_eq_A_26 |
| bklnw-lemma_15 | lemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW_app.bklnw_lemma_15 |
| bklnw-cor_15_1 | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW_app.bklnw_cor_15_1 |
| logan-function | definition | out-of-fragment | real-analysis; maps-functions; rational-arithmetic | BKLNW_app.ℓ |
| logan-function-ft | definition | out-of-fragment | real-analysis; maps-functions; rational-arithmetic | BKLNW_app.η |
| buthe-mu-def | definition | out-of-fragment | real-analysis; maps-functions | BKLNW_app.μ |
| bklnw-thm_16 | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; maps-functions; rational-arithmetic | BKLNW_app.bklnw_thm_16 |
| bknlw-theorem-2 | theorem | out-of-fragment | real-analysis | BKLNW_app.theorem_2 |
| bklnw-cor_15_1_alt | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW_app.bklnw_cor_15_1' |
| ch2-prop-2-3-1 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | CH2.prop_2_3_1 |
| ch2-prop-2-3 | proposition | out-of-fragment | real-analysis; entropy-log; sequences-sums; maps-functions; rational-arithmetic | CH2.prop_2_3 |
| ch2-S-def | definition | out-of-fragment | sequences-sums | CH2.S |
| ch2-I-def | definition | no-signal | — | CH2.I' |
| ch2-2-10 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | CH2.S_eq_I |
| ch2-prop-2-4-plus | proposition | out-of-fragment | real-analysis; entropy-log; sequences-sums; maps-functions; rational-arithmetic | CH2.prop_2_4_plus |
| ch2-prop-2-4-minus | proposition | out-of-fragment | real-analysis; entropy-log; sequences-sums; maps-functions; rational-arithmetic | CH2.prop_2_4_minus |
| Phi-circ-def | definition | out-of-fragment | rational-arithmetic | CH2.Phi_circ |
| Phi-circ-mero | theorem | no-signal | — | CH2.Phi_circ.meromorphic |
| Phi-circ-poles | lemma | no-signal | — | CH2.Phi_circ.poles |
| Phi-circ-residues | lemma | no-signal | — | CH2.Phi_circ.residue |
| Phi-circ-poles-simple | lemma | no-signal | — | CH2.Phi_circ.poles_simple |
| B-def | definition | no-signal | — | CH2.B |
| B-cts | lemma | out-of-fragment | real-analysis | CH2.B.continuous_zero |
| Phi-star-def | definition | no-signal | — | CH2.Phi_star |
| Phi-star-zero | theorem | no-signal | — | CH2.Phi_star_zero |
| Phi-star-mero | theorem | no-signal | — | CH2.Phi_star.meromorphic |
| Phi-star-poles | lemma | no-signal | — | CH2.Phi_star.poles |
| Phi-star-residues | lemma | no-signal | — | CH2.Phi_star.residue |
| Phi-star-poles-simple | lemma | no-signal | — | CH2.Phi_star.poles_simple |
| Phi-cancel | lemma | no-signal | — | CH2.Phi_cancel |
| phi-pm-def | definition | no-signal | — | CH2.ϕ_pm |
| phi-c2-left | lemma | no-signal | — | CH2.ϕ_c2_left |
| phi-c2-right | lemma | no-signal | — | CH2.ϕ_c2_right |
| phi-cts | lemma | out-of-fragment | real-analysis | CH2.ϕ_continuous |
| phi-circ-bound-right | lemma | no-signal | — | CH2.ϕ_circ_bound_right |
| phi-circ-bound-left | lemma | no-signal | — | CH2.ϕ_circ_bound_left |
| phi-star-bound-right | lemma | no-signal | — | CH2.ϕ_star_bound_right |
| phi-star-bound-left | lemma | no-signal | — | CH2.ϕ_star_bound_left |
| B-plus-mono | lemma | no-signal | — | CH2.B_plus_mono |
| B-minus-mono | lemma | no-signal | — | CH2.B_minus_mono |
| varphi-fourier-ident | sublemma | attempt-candidate | — | CH2.varphi_fourier_ident |
| shift-upwards | sublemma | attempt-candidate | — | CH2.shift_upwards |
| B-affine-periodic | sublemma | attempt-candidate | — | CH2.B_affine_periodic |
| phi_star-affine-periodic | sublemma | attempt-candidate | — | CH2.phi_star_affine_periodic |
| shift-upwards-simplified | sublemma | out-of-fragment | rational-arithmetic | CH2.shift_upwards_simplified |
| shift-downwards | sublemma | out-of-fragment | rational-arithmetic | CH2.shift_downwards |
| first-contour-limit | sublemma | out-of-fragment | rational-arithmetic | CH2.first_contour_limit |
| second-contour-limit | sublemma | out-of-fragment | rational-arithmetic | CH2.second_contour_limit |
| third-contour-limit | sublemma | out-of-fragment | rational-arithmetic | CH2.third_contour_limit |
| shift-downwards-simplified | sublemma | out-of-fragment | rational-arithmetic | CH2.shift_downwards_simplified |
| fourier-formula-neg | lemma | out-of-fragment | rational-arithmetic | CH2.fourier_formula_neg |
| fourier-formula-pos | lemma | out-of-fragment | rational-arithmetic | CH2.fourier_formula_pos |
| fourier-real | lemma | no-signal | — | CH2.fourier_real |
| varphi-integ | lemma | out-of-fragment | maps-functions | CH2.varphi_integ |
| Inu_def | definition | no-signal | — | CH2.Inu |
| Inu_bounds | corollary | out-of-fragment | real-analysis | CH2.Inu_bounds |
| varphi-deriv-integ | lemma | out-of-fragment | maps-functions | CH2.varphi_deriv_integ |
| varphi-abs | lemma | out-of-fragment | real-analysis; maps-functions | CH2.varphi_abs |
| varphi-deriv-tv | lemma | out-of-fragment | maps-functions | CH2.varphi_deriv_tv |
| varphi-fourier-decay | corollary | no-signal | — | CH2.varphi_fourier_decay |
| varphi-fourier-minus-error | proposition | out-of-fragment | rational-arithmetic | CH2.varphi_fourier_minus_error |
| varphi-fourier-plus-error | proposition | out-of-fragment | rational-arithmetic | CH2.varphi_fourier_plus_error |
| CH2-lemma-4-2a | sublemma | out-of-fragment | rational-arithmetic | CH2.CH2_lemma_4_2a |
| CH2-lemma-4-2b | sublemma | out-of-fragment | rational-arithmetic | CH2.CH2_lemma_4_2b |
| ch2-lemma-5-1-a | sublemma | out-of-fragment | sequences-sums; rational-arithmetic | CH2.lemma_5_1_a |
| ch2-lemma-5-1-b | sublemma | out-of-fragment | sequences-sums; rational-arithmetic | CH2.lemma_5_1_b |
| ch2-lemma-5-1-c | sublemma | out-of-fragment | sequences-sums; rational-arithmetic | CH2.lemma_5_1_c |
| ch2-lemma-5-1-d | sublemma | out-of-fragment | polynomials-fields | CH2.lemma_5_1_d |
| ch2-lemma-5-1-e | sublemma | attempt-candidate | — | CH2.lemma_5_1_e |
| ch2-lemma-5-1-f | sublemma | attempt-candidate | — | CH2.lemma_5_1_f |
| ch2-lemma-5-1-g | sublemma | out-of-fragment | sequences-sums | CH2.lemma_5_1_g |
| ch2-lemma-5-1-h | sublemma | attempt-candidate | — | CH2.lemma_5_1_h |
| ch2-lemma-5-1 | lemma | out-of-fragment | real-analysis; sequences-sums; polynomials-fields; rational-arithmetic | CH2.lemma_5_1 |
| ch2-prop-5-2-a | sublemma | out-of-fragment | sequences-sums; geometry-topology; rational-arithmetic | CH2.prop_5_2_a |
| ch2-prop-5-2-b | sublemma | out-of-fragment | real-analysis; sequences-sums; rational-arithmetic | CH2.prop_5_2_b |
| ch2-prop-5-2-c | sublemma | out-of-fragment | real-analysis; rational-arithmetic | CH2.prop_5_2_c |
| ch2-prop-5-2 | proposition | out-of-fragment | real-analysis; sequences-sums; rational-arithmetic | CH2.prop_5_2 |
| CH2-cor-1-2-a | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | CH2.cor_1_2_a |
| CH2-cor-1-2-b | corollary | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | CH2.cor_1_2_b |
| CH2-cor-1-3-a | corollary | out-of-fragment | maps-functions | CH2.cor_1_3_a |
| CH2-cor-1-3-b | corollary | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | CH2.cor_1_3_b |
| RectangleBorder | definition | out-of-fragment | geometry-topology | RectangleBorder |
| RectangleIntegral | definition | out-of-fragment | primality; geometry-topology; maps-functions | RectangleIntegral |
| UpperUIntegral | definition | out-of-fragment | maps-functions | UpperUIntegral |
| LowerUIntegral | definition | out-of-fragment | maps-functions | LowerUIntegral |
| VerticalIntegral | definition | out-of-fragment | real-analysis; maps-functions | VerticalIntegral |
| DiffVertRect_eq_UpperLowerUs | lemma | out-of-fragment | geometry-topology | DiffVertRect_eq_UpperLowerUs |
| existsDifferentiableOn_of_bddAbove | theorem | out-of-fragment | maps-functions | existsDifferentiableOn_of_bddAbove |
| HolomorphicOn.vanishesOnRectangle | theorem | out-of-fragment | geometry-topology | HolomorphicOn.vanishesOnRectangle |
| RectanglePullToNhdOfPole | lemma | out-of-fragment | geometry-topology | RectanglePullToNhdOfPole |
| ResidueTheoremAtOrigin | lemma | out-of-fragment | geometry-topology | ResidueTheoremAtOrigin |
| ResidueTheoremOnRectangleWithSimplePole | lemma | out-of-fragment | geometry-topology; maps-functions | ResidueTheoremOnRectangleWithSimplePole |
| zeroTendstoDiff | lemma | out-of-fragment | real-analysis | zeroTendstoDiff |
| RectangleIntegral_tendsTo_VerticalIntegral | lemma | out-of-fragment | real-analysis; geometry-topology | RectangleIntegral_tendsTo_VerticalIntegral |
| RectangleIntegral_tendsTo_UpperU | lemma | out-of-fragment | real-analysis; geometry-topology | RectangleIntegral_tendsTo_UpperU |
| RectangleIntegral_tendsTo_LowerU | lemma | out-of-fragment | real-analysis; geometry-topology | RectangleIntegral_tendsTo_LowerU |
| limitOfConstant | lemma | out-of-fragment | real-analysis; maps-functions | limitOfConstant |
| limitOfConstantLeft | lemma | out-of-fragment | real-analysis; maps-functions | limitOfConstantLeft |
| tendsto_rpow_atTop_nhds_zero_of_norm_lt_one | lemma | no-signal | — | tendsto_rpow_atTop_nhds_zero_of_norm_lt_one |
| tendsto_rpow_atTop_nhds_zero_of_norm_gt_one | lemma | no-signal | — | tendsto_rpow_atTop_nhds_zero_of_norm_gt_one |
| isHolomorphicOn | lemma | out-of-fragment | maps-functions | Perron.isHolomorphicOn |
| integralPosAux | lemma | out-of-fragment | real-analysis; rational-arithmetic | Perron.integralPosAux |
| vertIntBound | lemma | out-of-fragment | real-analysis; rational-arithmetic | Perron.vertIntBound |
| vertIntBoundLeft | lemma | out-of-fragment | real-analysis; rational-arithmetic | Perron.vertIntBoundLeft |
| isIntegrable | lemma | out-of-fragment | real-analysis; rational-arithmetic | Perron.isIntegrable |
| tendsto_zero_Lower | lemma | out-of-fragment | real-analysis; rational-arithmetic | Perron.tendsto_zero_Lower |
| Perron.tendsto_zero_Upper | lemma | out-of-fragment | real-analysis; rational-arithmetic | Perron.tendsto_zero_Upper |
| formulaLtOne | lemma | out-of-fragment | rational-arithmetic | Perron.formulaLtOne |
| keyIdentity | lemma | out-of-fragment | real-analysis; rational-arithmetic | Perron.keyIdentity |
| diffBddAtZero | lemma | out-of-fragment | geometry-topology; maps-functions; rational-arithmetic | Perron.diffBddAtZero |
| diffBddAtNegOne | lemma | out-of-fragment | geometry-topology; maps-functions; rational-arithmetic | Perron.diffBddAtNegOne |
| residueAtZero | lemma | out-of-fragment | rational-arithmetic | Perron.residueAtZero |
| residueAtNegOne | lemma | out-of-fragment | rational-arithmetic | Perron.residueAtNegOne |
| residuePull1 | lemma | out-of-fragment | rational-arithmetic | Perron.residuePull1 |
| residuePull2 | lemma | out-of-fragment | rational-arithmetic | Perron.residuePull2 |
| contourPull3 | lemma | out-of-fragment | rational-arithmetic | Perron.contourPull3 |
| formulaGtOne | lemma | out-of-fragment | rational-arithmetic | Perron.formulaGtOne |
| PartialIntegration | lemma | out-of-fragment | real-analysis; maps-functions | PartialIntegration |
| MellinConvolution | definition | out-of-fragment | real-analysis; maps-functions; rational-arithmetic | MellinConvolution |
| MellinConvolutionSymmetric | lemma | out-of-fragment | real-analysis; maps-functions | MellinConvolutionSymmetric |
| MellinConvolutionTransform | theorem | out-of-fragment | real-analysis; maps-functions; rational-arithmetic | MellinConvolutionTransform |
| MellinOfPsi | theorem | out-of-fragment | rational-arithmetic | MellinOfPsi |
| DeltaSpike | definition | out-of-fragment | real-analysis; maps-functions; rational-arithmetic | DeltaSpike |
| DeltaSpikeMass | lemma | out-of-fragment | real-analysis; rational-arithmetic | DeltaSpikeMass |
| MellinOfDeltaSpike | theorem | out-of-fragment | real-analysis | MellinOfDeltaSpike |
| MellinOfDeltaSpikeAt1 | corollary | out-of-fragment | real-analysis | MellinOfDeltaSpikeAt1 |
| MellinOfDeltaSpikeAt1_asymp | lemma | out-of-fragment | real-analysis | MellinOfDeltaSpikeAt1_asymp |
| MellinOf1 | theorem | out-of-fragment | rational-arithmetic | MellinOf1 |
| Smooth1 | definition | out-of-fragment | real-analysis; maps-functions | Smooth1 |
| Smooth1Properties_below | lemma | out-of-fragment | real-analysis | Smooth1Properties_below |
| Smooth1Properties_above | lemma | out-of-fragment | real-analysis | Smooth1Properties_above |
| Smooth1Nonneg | lemma | out-of-fragment | real-analysis | Smooth1Nonneg |
| Smooth1LeOne | lemma | out-of-fragment | real-analysis | Smooth1LeOne |
| MellinOfSmooth1a | lemma | out-of-fragment | real-analysis; rational-arithmetic | MellinOfSmooth1a |
| MellinOfSmooth1b | lemma | out-of-fragment | real-analysis; rational-arithmetic | MellinOfSmooth1b |
| MellinOfSmooth1c | lemma | out-of-fragment | real-analysis | MellinOfSmooth1c |
| Smooth1ContinuousAt | lemma | out-of-fragment | real-analysis; maps-functions | Smooth1ContinuousAt |
| SmoothExistence | theorem | out-of-fragment | maps-functions; rational-arithmetic | SmoothExistence |
| deriv_conj_conj' | theorem | out-of-fragment | real-analysis; maps-functions | deriv_conj_conj' |
| deriv_riemannZeta_conj | theorem | out-of-fragment | real-analysis; polynomials-fields; maps-functions | deriv_riemannZeta_conj |
| intervalIntegral_conj | theorem | out-of-fragment | real-analysis; maps-functions | intervalIntegral_conj |
| ResidueOfTendsTo | theorem | out-of-fragment | maps-functions; rational-arithmetic | ResidueOfTendsTo |
| riemannZetaResidue | theorem | out-of-fragment | polynomials-fields; maps-functions; rational-arithmetic | riemannZetaResidue |
| nonZeroOfBddAbove | theorem | out-of-fragment | maps-functions | nonZeroOfBddAbove |
| logDerivResidue | theorem | out-of-fragment | rational-arithmetic | logDerivResidue |
| BddAbove_to_IsBigO | theorem | no-signal | — | BddAbove_to_IsBigO |
| ResidueMult | theorem | out-of-fragment | rational-arithmetic | ResidueMult |
| riemannZetaLogDerivResidue | theorem | out-of-fragment | real-analysis; polynomials-fields; maps-functions; rational-arithmetic | riemannZetaLogDerivResidue |
| riemannZeta0 | definition | out-of-fragment | sequences-sums; polynomials-fields; rational-arithmetic | riemannZeta0 |
| sum_eq_int_deriv | lemma | out-of-fragment | real-analysis; sequences-sums; rational-arithmetic | sum_eq_int_deriv |
| ZetaSum_aux1 | lemma | out-of-fragment | sequences-sums; rational-arithmetic | ZetaSum_aux1 |
| ZetaBnd_aux1a | lemma | out-of-fragment | rational-arithmetic | ZetaBnd_aux1a |
| ZetaSum_aux2 | lemma | out-of-fragment | sequences-sums; rational-arithmetic | ZetaSum_aux2 |
| ZetaBnd_aux1b | lemma | out-of-fragment | rational-arithmetic | ZetaBnd_aux1b |
| ZetaBnd_aux1 | lemma | out-of-fragment | rational-arithmetic | ZetaBnd_aux1 |
| ZetaBnd_aux1p | lemma | out-of-fragment | rational-arithmetic | ZetaBnd_aux1p |
| HolomorphicOn_riemannZeta0 | theorem | out-of-fragment | polynomials-fields; maps-functions | HolomorphicOn_riemannZeta0 |
| isPathConnected_aux | lemma | no-signal | — | isPathConnected_aux |
| Zeta0EqZeta | lemma | out-of-fragment | polynomials-fields | Zeta0EqZeta |
| ZetaBnd_aux2 | lemma | out-of-fragment | real-analysis; entropy-log | ZetaBnd_aux2 |
| ZetaUpperBnd | lemma | out-of-fragment | real-analysis; entropy-log; polynomials-fields | ZetaUpperBnd |
| DerivUpperBnd_aux7 | lemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | DerivUpperBnd_aux7 |
| ZetaDerivUpperBnd | lemma | out-of-fragment | real-analysis; entropy-log; polynomials-fields | ZetaDerivUpperBnd |
| ZetaNear1BndFilter | lemma | out-of-fragment | polynomials-fields | ZetaNear1BndFilter |
| ZetaNear1BndExact | lemma | out-of-fragment | polynomials-fields | ZetaNear1BndExact |
| ZetaLowerBound3 | lemma | out-of-fragment | real-analysis; entropy-log; polynomials-fields; rational-arithmetic | ZetaLowerBound3 |
| ZetaInvBound1 | lemma | out-of-fragment | polynomials-fields | ZetaInvBound1 |
| ZetaInvBound2 | lemma | out-of-fragment | real-analysis; entropy-log; polynomials-fields | ZetaInvBound2 |
| Zeta_eq_int_derivZeta | lemma | out-of-fragment | polynomials-fields | Zeta_eq_int_derivZeta |
| Zeta_diff_Bnd | lemma | out-of-fragment | real-analysis; entropy-log; polynomials-fields | Zeta_diff_Bnd |
| ZetaInvBnd | lemma | out-of-fragment | real-analysis; entropy-log; polynomials-fields | ZetaInvBnd |
| ZetaLowerBnd | lemma | out-of-fragment | real-analysis; entropy-log; polynomials-fields | ZetaLowerBnd |
| ZetaZeroFree | lemma | out-of-fragment | real-analysis; entropy-log; polynomials-fields | ZetaZeroFree |
| LogDerivZetaBnd | lemma | out-of-fragment | real-analysis; entropy-log; polynomials-fields; rational-arithmetic | LogDerivZetaBnd |
| ZetaNoZerosOn1Line | theorem | out-of-fragment | maps-functions | ZetaNoZerosOn1Line |
| ZetaNoZerosInBox | lemma | out-of-fragment | polynomials-fields | ZetaNoZerosInBox |
| LogDerivZetaHolcSmallT | lemma | out-of-fragment | polynomials-fields; maps-functions; rational-arithmetic | LogDerivZetaHolcSmallT |
| LogDerivZetaHolcLargeT | lemma | out-of-fragment | real-analysis; entropy-log; polynomials-fields; maps-functions; rational-arithmetic | LogDerivZetaHolcLargeT |
| LogDerivZetaBndUnif | lemma | out-of-fragment | real-analysis; entropy-log; polynomials-fields; rational-arithmetic | LogDerivZetaBndUnif |
| ChebyshevPsi | definition | out-of-fragment | sequences-sums; maps-functions | ChebyshevPsi |
| LogDerivativeDirichlet | theorem | out-of-fragment | sequences-sums; polynomials-fields; rational-arithmetic | LogDerivativeDirichlet |
| SmoothedChebyshev | definition | out-of-fragment | real-analysis; entropy-log; polynomials-fields; maps-functions; rational-arithmetic | SmoothedChebyshev |
| SmoothedChebyshevDirichlet_aux_integrable | lemma | out-of-fragment | real-analysis; maps-functions | SmoothedChebyshevDirichlet_aux_integrable |
| SmoothedChebyshevDirichlet_aux_tsum_integral | lemma | out-of-fragment | real-analysis; sequences-sums; maps-functions; rational-arithmetic | SmoothedChebyshevDirichlet_aux_tsum_integral |
| SmoothedChebyshevDirichlet | theorem | out-of-fragment | real-analysis; sequences-sums | SmoothedChebyshevDirichlet |
| SmoothedChebyshevClose | theorem | out-of-fragment | real-analysis; entropy-log | SmoothedChebyshevClose |
| I1 | definition | out-of-fragment | real-analysis; polynomials-fields; rational-arithmetic | I₁ |
| I2 | definition | out-of-fragment | real-analysis; polynomials-fields; rational-arithmetic | I₂ |
| I37 | definition | out-of-fragment | real-analysis; polynomials-fields; rational-arithmetic | I₃₇ |
| I8 | definition | out-of-fragment | real-analysis; polynomials-fields; rational-arithmetic | I₈ |
| I9 | definition | out-of-fragment | real-analysis; polynomials-fields; rational-arithmetic | I₉ |
| I3 | definition | out-of-fragment | real-analysis; polynomials-fields; rational-arithmetic | I₃ |
| I7 | definition | out-of-fragment | real-analysis; polynomials-fields; rational-arithmetic | I₇ |
| I4 | definition | out-of-fragment | real-analysis; polynomials-fields; rational-arithmetic | I₄ |
| I6 | definition | out-of-fragment | real-analysis; polynomials-fields; rational-arithmetic | I₆ |
| I5 | definition | out-of-fragment | real-analysis; polynomials-fields; rational-arithmetic | I₅ |
| dlog_riemannZeta_bdd_on_vertical_lines | lemma | out-of-fragment | real-analysis; polynomials-fields; rational-arithmetic | dlog_riemannZeta_bdd_on_vertical_lines |
| SmoothedChebyshevPull1_aux_integrable | lemma | out-of-fragment | real-analysis; polynomials-fields | SmoothedChebyshevPull1_aux_integrable |
| BddAboveOnRect | lemma | out-of-fragment | geometry-topology; maps-functions | BddAboveOnRect |
| SmoothedChebyshevPull1 | theorem | out-of-fragment | real-analysis | SmoothedChebyshevPull1 |
| SmoothedChebyshevPull2 | lemma | no-signal | — | SmoothedChebyshevPull2 |
| ZetaBoxEval | theorem | out-of-fragment | real-analysis; probability-mass; geometry-topology; rational-arithmetic | ZetaBoxEval |
| IBound_aux1 | lemma | out-of-fragment | real-analysis; entropy-log | IBound_aux1 |
| I1Bound | lemma | out-of-fragment | real-analysis; rational-arithmetic | I1Bound |
| I2Bound | lemma | out-of-fragment | real-analysis; rational-arithmetic | I2Bound |
| I8I2 | lemma | out-of-fragment | real-analysis | I8I2 |
| I8Bound | lemma | out-of-fragment | real-analysis; rational-arithmetic | I8Bound |
| log_pow_over_xsq_integral_bounded | lemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | log_pow_over_xsq_integral_bounded |
| I3Bound | lemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | I3Bound |
| I4Bound | lemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | I4Bound |
| I5Bound | lemma | out-of-fragment | real-analysis; rational-arithmetic | I5Bound |
| MediumPNT | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums | MediumPNT |
| li2-lower | theorem | no-signal | — | Li2Bounds.li2_symmetric_lower |
| li2-upper | theorem | no-signal | — | Li2Bounds.li2_symmetric_upper |
| li2-bounds | theorem | no-signal | — | Li2Bounds.li2_symmetric_bounds |
| li2-eq | theorem | attempt-candidate | — | Li2Bounds.li2_symmetric_eq_li2 |
| log_upper | sublemma | out-of-fragment | real-analysis; entropy-log | log_le |
| log_lower_1 | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | log_ge |
| log_lower_2 | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | log_ge' |
| symm_inv_log | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | symm_inv_log |
| li_minus_Li | remark | no-signal | — | — |
| Ramanujan-Soldner-constant | lemma | no-signal | — | li.two_approx |
| li2-bounds-weak | sublemma | no-signal | — | li.two_approx_weak |
| li2-symmetric-eq | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | li2_symmetric_eq_li2 |
| cheby-def-T | definition | out-of-fragment | real-analysis; entropy-log; sequences-sums | Chebyshev.T |
| cheby-T-upper | lemma | out-of-fragment | real-analysis; entropy-log | Chebyshev.T.le |
| cheby-T-lower | lemma | out-of-fragment | real-analysis; entropy-log | Chebyshev.T.ge |
| cheby-T-Lambda | lemma | out-of-fragment | sequences-sums | Chebyshev.T.eq_sum_Lambda |
| cheby-E | definition | out-of-fragment | real-analysis; sequences-sums; maps-functions | Chebyshev.E |
| cheby-T-E | lemma | out-of-fragment | real-analysis; sequences-sums | Chebyshev.T.weighted_eq_sum |
| cheby-nu | definition | no-signal | — | Chebyshev.ν |
| cheby-nu-cancel | lemma | out-of-fragment | sequences-sums | Chebyshev.nu_sum_div_eq_zero |
| cheby-E-1 | lemma | no-signal | — | Chebyshev.E_nu_eq_one |
| cheby-E-periodic | lemma | no-signal | — | Chebyshev.E_nu_period |
| cheby-E-val | lemma | no-signal | — | Chebyshev.E_nu_bound |
| cheby-U-def | definition | out-of-fragment | sequences-sums | Chebyshev.U |
| cheby-psi-lower | proposition | no-signal | — | Chebyshev.psi_ge_weighted |
| cheby-psi-diff | proposition | no-signal | — | Chebyshev.psi_diff_le_weighted |
| a-def | definition | out-of-fragment | real-analysis; entropy-log; sequences-sums | Chebyshev.a |
| a-val | lemma | no-signal | — | Chebyshev.a_bound |
| U-bounds | lemma | out-of-fragment | real-analysis; entropy-log | Chebyshev.U_bound |
| psi-lower | theorem | out-of-fragment | real-analysis; entropy-log | Chebyshev.psi_lower |
| psi-diff-upper | proposition | out-of-fragment | real-analysis; entropy-log | Chebyshev.psi_diff_upper |
| psi-num | sublemma | no-signal | — | Chebyshev.psi_num |
| psi-upper | theorem | out-of-fragment | real-analysis; entropy-log | Chebyshev.psi_upper |
| psi-num-2 | sublemma | no-signal | — | Chebyshev.psi_num_2 |
| psi-upper-clean | theorem | no-signal | — | Chebyshev.psi_upper_clean |
| pi-inc | lemma | out-of-fragment | primality | HasPrimeInInterval.iff_pi_ge |
| theta-inc | lemma | out-of-fragment | primality | HasPrimeInInterval.iff_theta_ge |
| etheta-pi | lemma | out-of-fragment | primality | Eθ.hasPrimeInInterval |
| etheta-num-pi | lemma | out-of-fragment | real-analysis; primality | Eθ.numericalBound.hasPrimeInInterval |
| etheta-classical-pi | lemma | out-of-fragment | real-analysis; entropy-log; primality; rational-arithmetic | Eθ.classicalBound.hasPrimeInInterval |
| prime-gap-record-interval | lemma | out-of-fragment | primality | prime_gap_record.hasPrimeInInterval |
| rs-pnt | theorem | out-of-fragment | real-analysis; entropy-log | RS_prime.pnt |
| theta-stieltjes | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; maps-functions | RS_prime.θ.Stieltjes |
| rs-pre-413 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | RS_prime.pre_413 |
| rs-413 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | RS_prime.eq_413 |
| rs-414 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | RS_prime.eq_414 |
| rs-416 | definition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | RS_prime.L |
| rs-415 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | RS_prime.eq_415 |
| rs-417 | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | RS_prime.eq_417 |
| rs-418 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | RS_prime.eq_418 |
| rs-419 | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | RS_prime.mertens_second_theorem, RS_prime.eq_419, RS_prime.mertens_second_theorem' |
| Mertens-constant | definition | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | mertensConstant |
| rs-420 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | RS_prime.eq_420, RS_prime.mertens_first_theorem, RS_prime.mertens_first_theorem' |
| rs-psi-upper | theorem | no-signal | — | RS_prime.theorem_12 |
| buthe-eq-1-4 | definition | out-of-fragment | sequences-sums | Buthe.pi_star |
| buthe-theorem-2a | theorem | no-signal | — | Buthe.theorem_2a |
| buthe-theorem-2b | theorem | no-signal | — | Buthe.theorem_2b |
| buthe-theorem-2c | theorem | no-signal | — | Buthe.theorem_2c |
| buthe-theorem-2d | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Buthe.theorem_2d |
| buthe-theorem-2e | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Buthe.theorem_2e |
| buthe-theorem-2f | theorem | no-signal | — | Buthe.theorem_2f |
| buthe-sieve-bound | lemma | no-signal | — | Buthe.sieve_bound |
| buthe-eq-6-2 | lemma | out-of-fragment | rational-arithmetic | Buthe.eq_6_2 |
| buthe-table-1-to-32e12 | lemma | no-signal | — | Buthe.table_1_to_32e12 |
| buthe-theorem-2a-normalized | lemma | no-signal | — | Buthe.theorem_2a_normalized |
| bklnw-table-14-check | sublemma | no-signal | — | BKLNW.table_14_check |
| from-buthe-eq-1-7 | sublemma | no-signal | — | BKLNW.buthe_eq_1_7 |
| bklnw-pre-inputs | definition | out-of-fragment | real-analysis | BKLNW.Pre_inputs.default |
| bklnw-lemma-11a | lemma | out-of-fragment | real-analysis; entropy-log | BKLNW.lemma_11a |
| bklnw-lemma-11b | lemma | out-of-fragment | real-analysis | BKLNW.lemma_11b |
| bklnw-thm-1a | theorem | out-of-fragment | real-analysis; entropy-log | BKLNW.thm_1a |
| bklnw-thm-1a-checked | theorem | out-of-fragment | real-analysis | BKLNW.thm_1a_crit |
| bklnw-thm-1a-table | theorem | no-signal | — | BKLNW.thm_1a_table |
| bklnw-cor-2-1 | corollary | no-signal | — | BKLNW.cor_2_1 |
| bklnw-inputs | definition | no-signal | — | BKLNW.Inputs.default |
| bklnw-eq-2-4 | definition | out-of-fragment | real-analysis; entropy-log; sequences-sums | BKLNW.f |
| bklnw-prop-3-sub-1 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | BKLNW.prop_3_sub_1 |
| bklnw-prop-3-sub-2 | sublemma | no-signal | — | BKLNW.prop_3_sub_2 |
| bklnw-prop-3-sub-3 | sublemma | no-signal | — | BKLNW.prop_3_sub_3 |
| bklnw-prop-3-sub-4 | sublemma | no-signal | — | BKLNW.prop_3_sub_4 |
| bklnw-prop-3-sub-5 | sublemma | no-signal | — | BKLNW.prop_3_sub_5 |
| bklnw-prop-3-sub-6 | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW.prop_3_sub_6 |
| bklnw-prop-3-sub-7 | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW.prop_3_sub_7 |
| bklnw-prop-3-sub-8 | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW.prop_3_sub_8 |
| bklnw-prop-3 | proposition | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | BKLNW.prop_3 |
| bklnw-cor-3-1 | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW.cor_3_1 |
| bklnw-prop-4-a | proposition | out-of-fragment | real-analysis; entropy-log | BKLNW.prop_4_a |
| bklnw-prop-4-b | proposition | out-of-fragment | real-analysis; entropy-log | BKLNW.prop_4_b |
| bklnw-def-a-1 | definition | out-of-fragment | real-analysis; entropy-log | BKLNW.Inputs.a₁ |
| bklnw-def-a-2 | definition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW.Inputs.a₂ |
| bklnw-thm-5 | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW.thm_5 |
| bklnw-cor-5-1 | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW.cor_5_1 |
| bklnw-lem-6 | lemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW.lem_6 |
| bklnw-cor-14-1 | corollary | out-of-fragment | rational-arithmetic | BKLNW.cor_14_1 |
| bklnw-lemma-8 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | BKLNW.bklnw_lemma_8 |
| bklnw-eq-3-11 | sublemma | out-of-fragment | real-analysis; sequences-sums; rational-arithmetic | BKLNW.bklnw_eq_3_11 |
| bklnw-cor-8-1a | sublemma | out-of-fragment | real-analysis; entropy-log; primality; rational-arithmetic | BKLNW.bklnw_cor_8_1a |
| bklnw-cor-8-1b | sublemma | out-of-fragment | real-analysis; entropy-log; primality; rational-arithmetic | BKLNW.bklnw_cor_8_1b |
| bklnw-table-11-verification | proposition | no-signal | — | BKLNW.bklnw_table_11_verification |
| bklnw-eq-3-17 | lemma | no-signal | — | BKLNW.bklnw_eq_3_17 |
| bklnw-eq-3-18 | corollary | out-of-fragment | real-analysis; entropy-log | BKLNW.bklnw_eq_3_18 |
| bklnw-lemma-9 | lemma | out-of-fragment | rational-arithmetic | BKLNW.bklnw_lemma_9 |
| bklnw-table_from_buthe | lemma | no-signal | — | BKLNW.bklnw_table_from_buthe |
| bklnw-corollary-9-1 | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW.bklnw_corollary_9_1 |
| bklnw-table-12-verification | proposition | no-signal | — | BKLNW.bklnw_table_12_verification |
| bklnw-corollary-9-1-explicit | corollary | out-of-fragment | real-analysis; entropy-log | BKLNW.bklnw_corollary_9_1_explicit |
| bklnw-thm-1b-table | theorem | out-of-fragment | real-analysis; entropy-log | BKLNW.thm_1b_table |
| bklnw-thm-1b | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | BKLNW.thm_1b |
| fks2-eq-16 | definition | out-of-fragment | real-analysis; entropy-log | FKS2.g_bound |
| fks2-lemma-10-substep | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | FKS2.lemma_10_substep |
| fks2-lemma-10-substep-2 | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | FKS2.lemma_10_substep_2 |
| fks2-lemma-10a | lemma | no-signal | — | FKS2.lemma_10a |
| fks2-lemma-10b | lemma | out-of-fragment | rational-arithmetic | FKS2.lemma_10b |
| fks2-lemma-10c | lemma | out-of-fragment | real-analysis; entropy-log | FKS2.lemma_10c |
| fks2-corollary-11 | corollary | no-signal | — | FKS2.corollary_11 |
| fks2-eq-19 | definition | out-of-fragment | real-analysis; maps-functions | FKS2.dawson |
| fks2-remark-after-corollary-11 | remark | out-of-fragment | maps-functions | — |
| fks2-proposition-13 | proposition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | FKS2.proposition_13 |
| fks2-corollary-14 | corollary | no-signal | — | FKS2.corollary_14 |
| fks2-remark-15 | remark | out-of-fragment | real-analysis; entropy-log | — |
| fks2-eq-17 | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | FKS2.eq_17 |
| fks2-error-def | definition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | FKS2.δ |
| fks2-eq-30 | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | FKS2.eq_30 |
| fks2-lemma-12 | lemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | FKS2.lemma_12 |
| fks2-eq-9 | definition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | FKS2.μ_asymp |
| fks2-theorem-3 | theorem | out-of-fragment | real-analysis; rational-arithmetic | FKS2.theorem_3 |
| fks2-proposition-17 | proposition | out-of-fragment | real-analysis; rational-arithmetic | FKS2.proposition_17 |
| fks2-lemma-19 | lemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | FKS2.lemma_19 |
| fks2-lemma-20a | lemma | out-of-fragment | real-analysis; entropy-log; maps-functions; rational-arithmetic | FKS2.lemma_20_a |
| fks2-lemma-20b | lemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | FKS2.lemma_20_b |
| fks2-theorem-6-1 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | FKS2.theorem_6_1 |
| fks2-theorem-6-2 | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | FKS2.theorem_6_2 |
| fks2-theorem-6-3 | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | FKS2.theorem_6_3 |
| fks2-eq-11 | definition | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | FKS2.μ_num_1 |
| fks2-eq-12 | definition | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | FKS2.μ_num_2 |
| fks2-mu-def | definition | out-of-fragment | real-analysis; entropy-log | FKS2.μ_num |
| fks2-eq-13 | definition | out-of-fragment | real-analysis | FKS2.επ_num |
| fks2-remark-7 | remark | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | — |
| fks2-theorem-6 | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | FKS2.theorem_6, FKS2.theorem_6_alt |
| fks2-corollary-8 | corollary | out-of-fragment | real-analysis; entropy-log | FKS2.corollary_8 |
| fks2-corollary-21 | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | FKS2.corollary_21 |
| fks2-corollary-23 | corollary | out-of-fragment | real-analysis; entropy-log | FKS2.corollary_23 |
| fks2-corollary-24 | corollary | no-signal | — | FKS2.corollary_24 |
| fks2-corollary-26 | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | FKS2.corollary_26 |
| table-8-prime-gap-test | proposition | out-of-fragment | primality | eSHP.table_8_prime_gap_test |
| table-8-prime-gap | proposition | out-of-fragment | primality | eSHP.table_8_prime_gap |
| table-8-prime-gap-complete-test | proposition | out-of-fragment | primality | eSHP.table_8_prime_gap_complete_test |
| table-8-prime-gap-complete | proposition | out-of-fragment | primality | eSHP.table_8_prime_gap_complete |
| max-prime-gap | proposition | out-of-fragment | primality | eSHP.max_prime_gap |
| table-9-prime-gap-test | proposition | out-of-fragment | primality | eSHP.table_9_prime_gap_test |
| table-9-prime-gap | proposition | out-of-fragment | primality | eSHP.table_9_prime_gap |
| table-9-prime-gap-complete-test | proposition | no-signal | — | eSHP.table_9_prime_gap_complete_test |
| table-9-prime-gap-complete | proposition | no-signal | — | eSHP.table_9_prime_gap_complete |
| exists-prime-gap | proposition | out-of-fragment | primality | eSHP.exists_prime_gap |
| Dusart_prop_3_2 | proposition | out-of-fragment | real-analysis | Dusart.proposition_3_2 |
| Dusart_thm_3_3 | theorem | out-of-fragment | real-analysis; entropy-log | Dusart.theorem_3_3 |
| Dusart_lemma_4_1 | lemma | no-signal | — | Dusart.lemma_4_1 |
| Dusart_thm_4_2 | theorem | out-of-fragment | real-analysis; entropy-log | Dusart.theorem_4_2 |
| Dusart_prop_4_3 | proposition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.proposition_4_3 |
| Dusart_prop_4_4 | proposition | no-signal | — | Dusart.proposition_4_4 |
| Dusart_corollary_4_5 | corollary | no-signal | — | Dusart.corollary_4_5 |
| Dusart_thm_5_1 | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.theorem_5_1 |
| Dusart_cor_5_2_a | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.corollary_5_2_a |
| Dusart_cor_5_2_b | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.corollary_5_2_b |
| Dusart_cor_5_2_c | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.corollary_5_2_c |
| Dusart_cor_5_2_d | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.corollary_5_2_d |
| Dusart_cor_5_2_e | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.corollary_5_2_e |
| Dusart_cor_5_2_f | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.corollary_5_2_f |
| Dusart_cor_5_3_a | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.corollary_5_3_a |
| Dusart_cor_5_3_b | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.corollary_5_3_b |
| Dusart_cor_5_3_c | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.corollary_5_3_c |
| Dusart_cor_5_3_d | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.corollary_5_3_d |
| Dusart_prop_5_4a | sublemma | out-of-fragment | real-analysis; entropy-log; primality; rational-arithmetic | Dusart.proposition_5_4a |
| Dusart_prop_5_4b | sublemma | out-of-fragment | real-analysis; entropy-log; primality; rational-arithmetic | Dusart.proposition_5_4b |
| Dusart_prop_5_4c | sublemma | out-of-fragment | real-analysis; entropy-log; primality; rational-arithmetic | Dusart.proposition_5_4c |
| Dusart_prop_5_4 | proposition | out-of-fragment | real-analysis; entropy-log; primality; rational-arithmetic | Dusart.proposition_5_4 |
| Dusart_cor_5_5 | corollary | out-of-fragment | real-analysis; entropy-log; primality; rational-arithmetic | Dusart.corollary_5_5 |
| Dusart_thm_5_6 | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Dusart.theorem_5_6 |
| Dusart_thm_5_7 | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Dusart.theorem_5_7 |
| Dusart_thm_5_9a | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Dusart.theorem_5_9a |
| Dusart_thm_5_9b | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Dusart.theorem_5_9b |
| Dusart_lemma_5_10a | lemma | out-of-fragment | real-analysis; entropy-log | Dusart.lemma_5_10a |
| Dusart_lemma_5_10b | lemma | out-of-fragment | real-analysis; entropy-log | Dusart.lemma_5_10b |
| Massias_Robin_thm_Bv | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.massias_robin_thm_Bv |
| Dusart_prop_5_11a | proposition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.proposition_5_11a |
| Dusart_prop_5_11b | proposition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.proposition_5_11b |
| Dusart_prop_5_12 | proposition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.proposition_5_12 |
| Dusart_lemma_5_14 | lemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.lemma_5_14 |
| Dusart_prop_5_15 | proposition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.proposition_5_15 |
| Dusart_prop_5_16 | proposition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.proposition_5_16 |
| buthe2-buthe-chi-star-icc | definition | attempt-candidate | — | Buthe2.Buthe_chiStarIcc |
| buthe2-buthe-psi | definition | out-of-fragment | sequences-sums | Buthe2.Buthe_psi |
| buthe2-buthe-theta | definition | out-of-fragment | real-analysis; entropy-log; sequences-sums | Buthe2.Buthe_theta |
| buthe2-buthe-pi | definition | out-of-fragment | sequences-sums | Buthe2.Buthe_pi |
| buthe2-buthe-pi-star | definition | out-of-fragment | sequences-sums | Buthe2.Buthe_pi_star |
| thm:buthe-2a | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Buthe2.theorem_2a |
| thm:buthe-2b | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Buthe2.theorem_2b |
| thm:buthe-2c | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Buthe2.theorem_2c |
| thm:buthe-2d | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Buthe2.theorem_2d |
| thm:buthe-a | theorem | no-signal | — | Buthe.theorem_a |
| thm:buthe-b | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Buthe.theorem_b |
| thm:rs-1962-a | theorem | no-signal | — | RS_prime.theorem_a |
| thm:rs-1962-b | theorem | out-of-fragment | real-analysis; entropy-log | RS_prime.theorem_b |
| thm:rs-1962-c | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | RS_prime.theorem_c |
| thm:rs-1962-d | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | RS_prime.theorem_d |
| thm:dusart1999-pi | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart1999.pi_inequality |
| thm:dusart1999-a | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart1999.theorem_a |
| thm:dusart1999-b | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart1999.theorem_b |
| thm:dusart1999-c | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart1999.theorem_c |
| thm:dusart1999-d | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart1999.theorem_d |
| thm:dusart2018-theta-improv-1 | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.theta_improv_1 |
| thm:dusart2018-theta-improv-2 | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Dusart.theta_improv_2 |
| thm:faber-kadiri-psi | theorem | attempt-candidate | — | FaberKadiri.psi_bound |
| thm:jy-psi-1 | theorem | no-signal | — | JY.psi_bound_1 |
| thm:jy-psi-2 | theorem | out-of-fragment | real-analysis; entropy-log | JY.psi_bound_2 |
| thm:jy-psi-3 | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | JY.psi_bound_3 |
| thm:pt2021-psi | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | PT.psi_bound |
| thm:fks-psi | theorem | out-of-fragment | real-analysis; entropy-log | FKS.psi_bound |
| thm:ramare2013-vms-1a | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums | Ramare2013.von_mangoldt_sum_1a |
| thm:ramare2013-vms-1b | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums | Ramare2013.von_mangoldt_sum_1b |
| thm:ramare2013-vms-1c | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums | Ramare2013.von_mangoldt_sum_1c |
| thm:ramare2013-vms-1e | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums | Ramare2013.von_mangoldt_sum_1e |
| thm:ramare2013-vms-1d | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums | Ramare2013.von_mangoldt_sum_1d |
| thm:ramare2013-vms-2 | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums | Ramare2013.von_mangoldt_sum_2 |
| thm:mawia-spi-a | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums | Mawia.sum_p_inv_a |
| thm:mawia-spi-b | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums | Mawia.sum_p_inv_b |
| thm:mawia-spi-c | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums | Mawia.sum_p_inv_c |
| thm:mawia-spi-d | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums | Mawia.sum_p_inv_d |
| thm:ramare2016-3-2-a | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Ramare2016.lemma_3_2_a |
| thm:ramare2016-3-2-b | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Ramare2016.lemma_3_2_b |
| thm:ramare2016-3-2-c | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Ramare2016.lemma_3_2_c |
| thm:trevino-sum-prime | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Trevino.sum_prime_bound |
| thm:dn-pi1-lower | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | DelegliseNicolas.theorem_a |
| thm:dn-pi1-upper | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | DelegliseNicolas.theorem_b |
| thm:dn-pi2-lower | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | DelegliseNicolas.theorem_c |
| thm:dn-pi2-upper | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | DelegliseNicolas.theorem_d |
| thm:dn-pi3-upper | theorem | out-of-fragment | real-analysis; entropy-log | DelegliseNicolas.theorem_e |
| thm:dn-pi4-upper | theorem | out-of-fragment | real-analysis; entropy-log | DelegliseNicolas.theorem_f |
| thm:dn-pi5-upper | theorem | out-of-fragment | real-analysis; entropy-log | DelegliseNicolas.theorem_g |
| thm:dn-pir-general | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | DelegliseNicolas.theorem_h |
| thm:rosser1938-pn-gt-nlogn | theorem | out-of-fragment | real-analysis; entropy-log | Rosser1938.p_n_gt_1 |
| thm:rosser1938-pn-lower | theorem | out-of-fragment | real-analysis; entropy-log | Rosser1938.p_n_gt_2 |
| thm:rosser1938-pn-upper | theorem | out-of-fragment | real-analysis; entropy-log | Rosser1938.p_n_lt_2 |
| thm:cipolla-pn-asym | theorem | out-of-fragment | real-analysis; entropy-log; primality; rational-arithmetic | Cipolla.p_n_asym |
| thm:rosser1941-pn-lower | theorem | out-of-fragment | real-analysis; entropy-log | Rosser1941.p_n_lower |
| thm:rosser1941-pn-upper | theorem | out-of-fragment | real-analysis; entropy-log | Rosser1941.p_n_upper |
| thm:rs-1962-pn-lower | theorem | out-of-fragment | real-analysis; entropy-log | RS_prime.p_n_lower |
| thm:rs-1962-pn-upper | theorem | out-of-fragment | real-analysis; entropy-log | RS_prime.p_n_upper |
| thm:robin1983-pn-lower | theorem | out-of-fragment | real-analysis; entropy-log | Robin.p_n_lower |
| thm:robin1983-pn-lower-const1 | theorem | out-of-fragment | real-analysis; entropy-log | Robin.p_n_lower_const1 |
| thm:massias-robin1996-pn-lower | theorem | out-of-fragment | real-analysis; entropy-log | MassiasRobin.p_n_lower |
| thm:dusart1999-pn-lower | theorem | out-of-fragment | real-analysis; entropy-log | Dusart1999.p_n_lower |
| thm:dusart1999-pn-upper | theorem | out-of-fragment | real-analysis; entropy-log | Dusart1999.p_n_upper |
| thm:cms2019-prime-gap | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | CMS.prime_gap |
| thm:axler2019-mandlB-lower | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Axler.mandlB_lower |
| thm:axler2019-mandlB-upper | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Axler.mandlB_upper |
| thm:dekoninck-letendre2020-sum-log-prime | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums | DeKoninckLetendre.sum_log_prime |
| thm:dekoninck-letendre2020-sum-loglog-prime | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | DeKoninckLetendre.sum_loglog_prime |
| thm:schoenfeld1976 | theorem | out-of-fragment | real-analysis; primality; rational-arithmetic | Schoenfeld1976.has_prime_in_interval |
| thm:ramare-saouter2003 | theorem | out-of-fragment | real-analysis; primality | RamareSaouter2003.has_prime_in_interval |
| thm:gourdon-demichel2004 | theorem | out-of-fragment | real-analysis; primality; rational-arithmetic | GourdonDemichel2004.has_prime_in_interval |
| thm:prime_gaps_2014 | theorem | out-of-fragment | real-analysis; primality; rational-arithmetic | PrimeGaps2014.has_prime_in_interval |
| thm:prime_gaps_2024 | theorem | out-of-fragment | real-analysis; primality; rational-arithmetic | PrimeGaps2024.has_prime_in_interval |
| thm:axler2018_1 | theorem | out-of-fragment | real-analysis; entropy-log; primality; rational-arithmetic | Axler2018.has_prime_in_interval_1 |
| thm:axler2018_2 | theorem | out-of-fragment | real-analysis; entropy-log; primality; rational-arithmetic | Axler2018.has_prime_in_interval_2 |
| thm:dudek2014 | theorem | out-of-fragment | real-analysis; primality | Dudek2014.has_prime_in_interval |
| thm:cully-hugill2021 | theorem | out-of-fragment | real-analysis; primality | CullyHugill2021.has_prime_in_interval |
| thm:rh_prime_interval_2002 | theorem | out-of-fragment | real-analysis; entropy-log; primality; rational-arithmetic | RHPrimeInterval2002.has_prime_in_interval |
| thm:dudek2015_rh | theorem | out-of-fragment | real-analysis; entropy-log; primality; rational-arithmetic | Dudek2015RH.has_prime_in_interval |
| thm:carneiroetal_2019_rh | theorem | out-of-fragment | real-analysis; entropy-log; primality; rational-arithmetic | CarneiroEtAl2019RH.has_prime_in_interval |
| thm:prime_gaps_KL | theorem | out-of-fragment | real-analysis; entropy-log; primality | KadiriLumley.has_prime_in_interval |
| thm:ramare_saouter2003-2 | theorem | out-of-fragment | real-analysis; primality; rational-arithmetic | RamareSaouter2003.has_prime_in_interval_2 |
| art06-lehman-zeta-half | theorem | out-of-fragment | polynomials-fields | Lehman1970.zeta_half_bound |
| art06-cheng-graham-zeta-half-small | theorem | out-of-fragment | polynomials-fields | ChengGraham2004.zeta_half_bound_small |
| art06-cheng-graham-zeta-half-large | theorem | out-of-fragment | real-analysis; entropy-log; polynomials-fields | ChengGraham2004.zeta_half_bound_large |
| art06-hiary-zeta-half | theorem | out-of-fragment | real-analysis; entropy-log; polynomials-fields | HiaryPatelYang2022.zeta_half_bound |
| art06-backlund-strip-1 | theorem | out-of-fragment | real-analysis; entropy-log; polynomials-fields | Backlund1918.zeta_strip_bound_1 |
| art06-backlund-strip-2 | theorem | out-of-fragment | real-analysis; entropy-log; polynomials-fields | Backlund1918.zeta_strip_bound_2 |
| art06-backlund-strip-3 | theorem | out-of-fragment | real-analysis; entropy-log; polynomials-fields | Backlund1918.zeta_strip_bound_3 |
| art06-trudgian-zeta-1-plus-it | theorem | out-of-fragment | real-analysis; entropy-log; polynomials-fields | Trudgian2014_zeta.zeta_one_plus_bound |
| art06-patel-zeta-1-plus-it | theorem | out-of-fragment | real-analysis; entropy-log; polynomials-fields | Patel2022.zeta_one_plus_bound |
| art06-ford-zeta-strip | theorem | out-of-fragment | real-analysis; entropy-log; polynomials-fields | Ford2002.zeta_strip_bound |
| art06-rosser-N | theorem | out-of-fragment | real-analysis; entropy-log | Rosser1941.N_bound |
| art06-trudgian-argument-N | theorem | out-of-fragment | real-analysis; entropy-log | Trudgian2014_argument.N_bound |
| art06-hsw-N-v1 | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | HSW2022.N_bound_v1 |
| art06-hsw-N-v2 | theorem | no-signal | — | HSW2022.N_bound_v2 |
| art06-ramare-real-line | theorem | out-of-fragment | polynomials-fields | Ramare2016.zeta_bound |
| art06-delange | theorem | out-of-fragment | polynomials-fields | Delange1987.zeta_log_deriv_bound |
| pt_thm_1 | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | PT.theorem_1 |
| pt_cor_1 | corollary | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | PT.corollary_1 |
| thm:pt_2 | theorem | out-of-fragment | real-analysis; entropy-log | PT.corollary_2 |
| trudgian:eps_0-def | definition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Trudgian2016.eps_0 |
| trudgian:theorem 1-theta | theorem | out-of-fragment | real-analysis | Trudgian2016.theorem_1_theta |
| trudgian:theorem 1-psi | theorem | out-of-fragment | real-analysis | Trudgian2016.theorem_1_psi |
| trudgian:lemma 1 | lemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Trudgian2016.lemma_1 |
| trudgian:theorem 2 | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Trudgian2016.theorem_2 |
| thm:trudgian2016 | theorem | out-of-fragment | real-analysis; entropy-log; primality; rational-arithmetic | Trudgian2016.has_prime_in_interval |
| thm:jy_13 | theorem | out-of-fragment | real-analysis; entropy-log | JY.corollary_1_3 |
| thm:jy_14 | theorem | out-of-fragment | real-analysis; entropy-log | JY.theorem_1_4 |
| sigma-def | definition | no-signal | — | Lcm.σ |
| highlyabundant-def | definition | attempt-candidate | — | Lcm.HighlyAbundant |
| Ln-def | definition | out-of-fragment | sequences-sums | Lcm.L |
| lcm-criterion | definition | out-of-fragment | sequences-sums; primality; rational-arithmetic | Lcm.Criterion |
| lem:4p3q3 | lemma | no-signal | — | Lcm.Criterion.prod_p_le_prod_q |
| lem:Lprime-def | lemma | out-of-fragment | primality | Lcm.Criterion.ln_eq, Lcm.Criterion.q_not_dvd_L' |
| lem:sigmaLn | lemma | out-of-fragment | sequences-sums; rational-arithmetic | Lcm.Criterion.σnorm_ln_eq |
| div-remainder | lemma | attempt-candidate | — | Lcm.Criterion.r_ge, Lcm.Criterion.r_le, Lcm.Criterion.prod_q_eq |
| lcm-M-def | definition | no-signal | — | Lcm.Criterion.M |
| lem:M-basic | lemma | out-of-fragment | rational-arithmetic | Lcm.Criterion.M_lt, Lcm.Criterion.Ln_div_M_gt, Lcm.Criterion.Ln_div_M_lt |
| lem:criterion-sufficient | lemma | out-of-fragment | rational-arithmetic | Lcm.Criterion.not_highlyAbundant_1 |
| lem:criterion-reduced | lemma | out-of-fragment | sequences-sums; rational-arithmetic | Lcm.Criterion.not_highlyAbundant_2 |
| lem:sigmaM-lower-final | lemma | out-of-fragment | sequences-sums; rational-arithmetic | Lcm.Criterion.σnorm_M_ge_σnorm_L'_mul |
| thm:criterion | theorem | out-of-fragment | primality | Lcm.Criterion.not_highlyAbundant |
| a0000001569 | remark | out-of-fragment | primality | — |
| lem:choose-pi | lemma | out-of-fragment | real-analysis; entropy-log; primality; rational-arithmetic | Lcm.exists_p_primes |
| lem:choose-qi | lemma | out-of-fragment | real-analysis; entropy-log; primality; rational-arithmetic | Lcm.exists_q_primes |
| lem:qi-product | lemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Lcm.prod_q_ge |
| lem:pi-product | lemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Lcm.prod_p_ge |
| lem:pq-ratio | lemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Lcm.pq_ratio_ge |
| lem:eps-bounds | lemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Lcm.inv_cube_log_sqrt_le, Lcm.inv_n_pow_3_div_2_le, Lcm.inv_n_add_sqrt_ge |
| lem:poly-ineq | lemma | out-of-fragment | real-analysis; sequences-sums; rational-arithmetic | Lcm.prod_epsilon_le, Lcm.prod_epsilon_ge |
| lem:final-comparison | lemma | out-of-fragment | real-analysis | Lcm.final_comparison |
| prop:ineq-holds-large-n | proposition | out-of-fragment | primality | Lcm.Criterion.mk' |
| thm:large-n-final | theorem | attempt-candidate | — | Lcm.L_not_HA_of_ge |
| thm:lcm-eq | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums | Lcm.L_eq_prod |
| thm:psi-eq | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; maps-functions | Lcm.psi_eq_prod |
| thm:lcm-psi | proposition | out-of-fragment | real-analysis; entropy-log; maps-functions | Lcm.log_L_eq_psi |
| factorization-def | definition | out-of-fragment | primality | Erdos392.Factorization |
| waste-def | definition | out-of-fragment | real-analysis; entropy-log; sequences-sums; primality | Erdos392.Factorization.waste |
| balance-def | definition | out-of-fragment | primality | Erdos392.Factorization.balance, Erdos392.Factorization.total_imbalance |
| balance-zero | lemma | out-of-fragment | primality | Erdos392.Factorization.zero_total_imbalance |
| waste-eq | lemma | out-of-fragment | real-analysis; entropy-log; primality | Erdos392.Factorization.waste_eq |
| score-def | definition | out-of-fragment | real-analysis; entropy-log; primality | Erdos392.Factorization.score |
| score-eq | lemma | no-signal | — | Erdos392.Factorization.score_eq |
| score-lower-1 | sublemma | out-of-fragment | primality | Erdos392.Factorization.lower_score_1 |
| score-lower-2 | sublemma | out-of-fragment | primality | Erdos392.Factorization.lower_score_2 |
| score-lower-3 | sublemma | out-of-fragment | primality | Erdos392.Factorization.lower_score_3 |
| score-lowest | lemma | out-of-fragment | primality | Erdos392.Factorization.lowest_score |
| card-bound | proposition | out-of-fragment | real-analysis; entropy-log; sets-cardinality; primality | Erdos392.Factorization.card_bound |
| params-set | definition | no-signal | — | Erdos392.Params |
| initial-factorization-def | definition | out-of-fragment | primality | Erdos392.Params.initial |
| initial-factorization-card | sublemma | out-of-fragment | primality | Erdos392.Params.initial.card |
| initial-factorization-waste | lemma | out-of-fragment | real-analysis; entropy-log; primality; rational-arithmetic | Erdos392.Params.initial.waste |
| initial-factorization-large-prime-le | sublemma | out-of-fragment | primality | Erdos392.Params.initial.balance_large_prime_le |
| initial-factorization-large-prime-ge | sublemma | out-of-fragment | primality | Erdos392.Params.initial.balance_large_prime_ge |
| initial-factorization-medium-prime-le | sublemma | out-of-fragment | primality | Erdos392.Params.initial.balance_medium_prime_le |
| initial-factorization-medium-prime-ge | sublemma | out-of-fragment | primality | Erdos392.Params.initial.balance_medium_prime_ge |
| initial-factorization-small-prime-le | sublemma | out-of-fragment | real-analysis; entropy-log; primality | Erdos392.Params.initial.balance_small_prime_le |
| initial-factorization-small-prime-ge | sublemma | out-of-fragment | real-analysis; entropy-log; primality | Erdos392.Params.initial.balance_small_prime_ge |
| initial-factorization-tiny-prime-ge | sublemma | out-of-fragment | real-analysis; entropy-log; primality | Erdos392.Params.initial.balance_tiny_prime_ge |
| initial-score-bound | proposition | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Erdos392.Params.initial.score_bound |
| bound-score-1 | sublemma | out-of-fragment | real-analysis; entropy-log | Erdos392.Params.initial.bound_score_1 |
| bound-score-2 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums | Erdos392.Params.initial.bound_score_2 |
| bound-score-3 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums | Erdos392.Params.initial.bound_score_3 |
| primeCounting-is-o-id | lemma | no-signal | — | Erdos392.primeCounting_is_o_id |
| bound-score-4 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Erdos392.Params.initial.bound_score_4 |
| primeCounting-le-bound | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Erdos392.primeCounting_le_bound |
| bound-score-5 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums | Erdos392.Params.initial.bound_score_5 |
| initial-score | proposition | out-of-fragment | primality | Erdos392.Params.initial.score |
| erdos-sol-1 | theorem | out-of-fragment | real-analysis; entropy-log; sets-cardinality; primality | Erdos392.Solution_1 |
| erdos-sol-2 | theorem | out-of-fragment | real-analysis; entropy-log | Erdos392.Solution_2 |
| even-goldbach | definition | out-of-fragment | primality | Goldbach.even_conjecture |
| even-goldbach-test | proposition | attempt-candidate | — | Goldbach.even_goldbach_test |
| odd-goldbach | definition | out-of-fragment | primality | Goldbach.odd_conjecture |
| even-to-odd-goldbach-triv | proposition | attempt-candidate | — | Goldbach.even_to_odd_goldbach_triv |
| even-to-odd-goldbach | proposition | out-of-fragment | real-analysis; primality | Goldbach.even_to_odd_goldbach |
| richstein-even-goldbach | proposition | attempt-candidate | — | Goldbach.richstein_goldbach |
| ramare-saouter-odd-goldbach | proposition | attempt-candidate | — | Goldbach.ramare_saouter_odd_goldbach |
| e-silva-herzog-piranian-even-goldbach | proposition | attempt-candidate | — | Goldbach.e_silva_herzog_piranian_goldbach |
| helfgott-odd-goldbach-finite | proposition | attempt-candidate | — | Goldbach.helfgott_odd_goldbach_finite |
| e-silva-herzog-piranian-even-goldbach-ext | proposition | attempt-candidate | — | Goldbach.e_silva_herzog_piranian_goldbach_ext |
| kl-odd-goldbach-finite | proposition | attempt-candidate | — | Goldbach.kadiri_lumley_odd_goldbach_finite |
| ramanujan-criterion-1 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Ramanujan.sq_pi_lt |
| ramanujan-criterion-2 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Ramanujan.ex_pi_gt |
| ramanujan-criterion | proposition | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Ramanujan.criterion |
| ramanujan-pibound-1 | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Ramanujan.pi_bound_1 |
| ramanujan-pibound-2 | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Ramanujan.pi_bound_2 |
| ramanujan-pibound-3 | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Ramanujan.pi_bound_3 |
| ramanujan-pibound-4 | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Ramanujan.pi_bound_4 |
| ramanujan-pibound-5 | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Ramanujan.pi_bound_5 |
| ramanujan-pibound-6 | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Ramanujan.pi_bound_6 |
| pt_eq_18 | proposition | out-of-fragment | real-analysis; entropy-log | Ramanujan.pi_bound |
| a-mono | lemma | out-of-fragment | maps-functions | Ramanujan.a_mono |
| pi-upper-specific | lemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Ramanujan.pi_upper_specific |
| pi-lower-specific | lemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | Ramanujan.pi_lower_specific |
| epsilon-bound | lemma | out-of-fragment | real-analysis; entropy-log | Ramanujan.epsilon_bound |
| ramanujan-final | theorem | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Ramanujan.ramanujan_final |
| thm:HLineq | theorem | out-of-fragment | real-analysis | — |
| FsigmaDef | definition | out-of-fragment | real-analysis; polynomials-fields | — |
| FsigmaThm | theorem | no-signal | — | — |
| thm:StrongZeroFree | theorem | out-of-fragment | real-analysis; entropy-log; polynomials-fields; rational-arithmetic | — |
| AnalyticOn.norm_le_of_norm_le_on_sphere | lemma | attempt-candidate | — | AnalyticOn.norm_le_of_norm_le_on_sphere |
| borelCaratheodory' | theorem | out-of-fragment | polynomials-fields | borelCaratheodory' |
| cauchy_formula_deriv | lemma | out-of-fragment | rational-arithmetic | cauchy_formula_deriv |
| DerivativeBound | lemma | out-of-fragment | rational-arithmetic | DerivativeBound |
| BorelCaratheodoryDeriv | theorem | out-of-fragment | rational-arithmetic | BorelCaratheodoryDeriv |
| TaxicabIntegral | definition | attempt-candidate | — | — |
| LogOfAnalyticFunction | theorem | out-of-fragment | real-analysis; entropy-log | LogOfAnalyticFunction |
| LogOfAnalyticFunction' | theorem | no-signal | — | LogOfAnalyticFunction' |
| SetOfZeros | definition | no-signal | — | SetOfZeros |
| ZeroOrder | definition | no-signal | — | — |
| ZeroFactor | definition | no-signal | — | ZeroFactor |
| ZeroFactorization | lemma | no-signal | — | ZeroFactorization |
| CFunction | definition | out-of-fragment | sequences-sums; polynomials-fields; maps-functions; rational-arithmetic | Cf |
| CfAnalytic | lemma | no-signal | — | CfAnalytic |
| BlaschkeB | definition | out-of-fragment | sequences-sums; maps-functions; rational-arithmetic | BlaschkeB |
| BlaschkeAnalytic | lemma | no-signal | — | BlaschkeAnalytic |
| BlaschkeOfZero | lemma | out-of-fragment | sequences-sums; rational-arithmetic | BlaschkeOfZero |
| norm_fOfZero_le_norm_BlaschkeOfZero | lemma | no-signal | — | norm_fOfZero_le_norm_BlaschkeOfZero |
| DiskBound | lemma | out-of-fragment | maps-functions | DiskBound |
| BlaschkeNonZero | lemma | attempt-candidate | — | BlaschkeNonzero |
| ZerosBound | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; maps-functions; rational-arithmetic | ZerosBound |
| JBlaschke | definition | out-of-fragment | maps-functions | JBlaschke |
| JBlaschkeDerivBound | theorem | out-of-fragment | real-analysis; entropy-log; maps-functions; rational-arithmetic | JBlaschkeDerivBound |
| FinalBound | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; maps-functions; rational-arithmetic | FinalBound |
| ZetaFixedLowerBound | theorem | out-of-fragment | real-analysis; polynomials-fields; rational-arithmetic | ZetaFixedLowerBound |
| riemannZeta1 | definition | out-of-fragment | polynomials-fields; rational-arithmetic | riemannZeta1 |
| Zeta1AltFormula | theorem | out-of-fragment | polynomials-fields | Zeta1AltFormula |
| ZetaAltFormula | theorem | out-of-fragment | polynomials-fields | ZetaAltFormula |
| GlobalBound | theorem | out-of-fragment | real-analysis; polynomials-fields | GlobalBound |
| LogDerivZetaFinalBound | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; polynomials-fields; rational-arithmetic | — |
| ZeroWindows | definition | out-of-fragment | polynomials-fields | — |
| SumBoundI | lemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; polynomials-fields; rational-arithmetic | — |
| ShiftTwoBound | lemma | out-of-fragment | real-analysis; entropy-log; polynomials-fields; rational-arithmetic | — |
| ShiftOneBound | lemma | out-of-fragment | real-analysis; entropy-log; polynomials-fields; rational-arithmetic | — |
| ShiftZeroBound | lemma | out-of-fragment | polynomials-fields; rational-arithmetic | — |
| ZeroInequality | theorem | out-of-fragment | real-analysis; entropy-log; polynomials-fields; rational-arithmetic | ZeroInequality |
| DeltaT | definition | out-of-fragment | real-analysis; entropy-log | DeltaT |
| DeltaRange | lemma | out-of-fragment | real-analysis | DeltaRange |
| SumBoundII | lemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; polynomials-fields; rational-arithmetic | — |
| GapSize | lemma | out-of-fragment | real-analysis | — |
| LogDerivZetaUniformLogSquaredBoundStrip | lemma | out-of-fragment | real-analysis; entropy-log; polynomials-fields; rational-arithmetic | LogDerivZetaUniformLogSquaredBoundStrip |
| LogDerivZetaUniformLogSquaredBound | theorem | out-of-fragment | real-analysis; entropy-log; polynomials-fields; rational-arithmetic | LogDerivZetaUniformLogSquaredBound |
| LogDerivZetaLogSquaredBoundSmallt | theorem | out-of-fragment | real-analysis; entropy-log; polynomials-fields; rational-arithmetic | LogDerivZetaLogSquaredBoundSmallt |
| I1New | definition | out-of-fragment | real-analysis; polynomials-fields; rational-arithmetic | I1New |
| I5New | definition | out-of-fragment | real-analysis; polynomials-fields; rational-arithmetic | I5New |
| I1NewBound | lemma | out-of-fragment | real-analysis; rational-arithmetic | I1NewBound |
| I5NewBound | lemma | out-of-fragment | real-analysis; rational-arithmetic | I5NewBound |
| I2New | definition | out-of-fragment | real-analysis; polynomials-fields; rational-arithmetic | I2New |
| I4New | definition | out-of-fragment | real-analysis; polynomials-fields; rational-arithmetic | I4New |
| I2NewBound | lemma | out-of-fragment | real-analysis; rational-arithmetic | I2NewBound |
| I4NewBound | lemma | out-of-fragment | real-analysis; rational-arithmetic | I4NewBound |
| I3New | definition | out-of-fragment | real-analysis; polynomials-fields; rational-arithmetic | I3New |
| I3NewBound | lemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | I3NewBound |
| SmoothedChebyshevPull3 | theorem | out-of-fragment | real-analysis | SmoothedChebyshevPull3 |
| StrongPNT | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums | — |
| first-fourier | lemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | first_fourier |
| second-fourier | lemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | second_fourier |
| prelim-decay | lemma | out-of-fragment | real-analysis | prelim_decay |
| prelim-decay-2 | lemma | out-of-fragment | real-analysis | prelim_decay_2 |
| prelim-decay-3 | lemma | out-of-fragment | real-analysis | prelim_decay_3 |
| decay-alt | lemma | out-of-fragment | real-analysis | decay_alt |
| decay | lemma | out-of-fragment | real-analysis | decay_bounds |
| limiting | lemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | limiting_fourier |
| limiting-cor | corollary | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | limiting_cor |
| smooth-ury | lemma | out-of-fragment | real-analysis; maps-functions | smooth_urysohn |
| schwarz-id | lemma | out-of-fragment | maps-functions | limiting_cor_schwartz |
| bij | lemma | out-of-fragment | maps-functions | fourier_surjection_on_schwartz |
| WienerIkeharaSmooth | corollary | out-of-fragment | sequences-sums; rational-arithmetic | wiener_ikehara_smooth |
| WienerIkeharaInterval | proposition | out-of-fragment | real-analysis; sets-cardinality; sequences-sums; rational-arithmetic | WienerIkeharaInterval |
| WienerIkehara | corollary | out-of-fragment | sequences-sums | WienerIkeharaTheorem' |
| WeakPNT | theorem | out-of-fragment | sequences-sums | WeakPNT |
| limiting-fourier-variant | lemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | limiting_fourier_variant |
| crude-upper-bound | corollary | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | crude_upper_bound |
| auto-cheby | corollary | out-of-fragment | sequences-sums | auto_cheby |
| WienerIkehara2 | theorem | out-of-fragment | sequences-sums | WienerIkeharaTheorem'' |
| WeakPNT-character | lemma | out-of-fragment | sequences-sums; primality; rational-arithmetic | WeakPNT_character |
| WeakPNT-AP-prelim | proposition | out-of-fragment | real-analysis; sequences-sums; primality; rational-arithmetic | WeakPNT_AP_prelim |
| WeakPNT-AP | theorem | out-of-fragment | sequences-sums; primality; rational-arithmetic | WeakPNT_AP |
| Artin-L-euler | lemma | out-of-fragment | algebra-structures; sets-cardinality; sequences-sums; primality | — |
| Dedekind-factor | lemma | out-of-fragment | sequences-sums; primality; polynomials-fields | — |
| Dedekind-pole | lemma | out-of-fragment | real-analysis; entropy-log; polynomials-fields; maps-functions | — |
| Artin-L-continuation | lemma | out-of-fragment | maps-functions; rational-arithmetic | — |
| Dedekind-nonvanishing | lemma | no-signal | — | — |
| Chebotarev-orthogonality | lemma | out-of-fragment | sequences-sums; primality; polynomials-fields | — |
| Chebotarev-cyclotomic-density | proposition | out-of-fragment | primality | — |
| Dedekind-PNT | lemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | — |
| Chebotarev-abelian-crossing | lemma | out-of-fragment | sequences-sums; primality; polynomials-fields | — |
| Chebotarev-abelian-density | lemma | out-of-fragment | algebra-structures; geometry-topology; polynomials-fields | — |
| Chebotarev-abelian | proposition | out-of-fragment | algebra-structures; algebra-abstract; primality | — |
| Chebotarev-reduction | lemma | out-of-fragment | algebra-structures; primality; geometry-topology; rational-arithmetic | — |
| Chebotarev-general | theorem | out-of-fragment | algebra-structures; algebra-abstract; sets-cardinality; primality | — |
| zeroes-of-riemann-zeta | definition | out-of-fragment | sequences-sums; geometry-topology; polynomials-fields | riemannZeta.zeroes, riemannZeta.zeroes_rect, riemannZeta.order, riemannZeta.zeroes_sum |
| RH-up-to | definition | out-of-fragment | geometry-topology | riemannZeta.RH_up_to |
| classical-zero-free-region | definition | out-of-fragment | real-analysis; entropy-log; polynomials-fields | riemannZeta.classicalZeroFree |
| zero-counting-function | definition | no-signal | — | riemannZeta.N, riemannZeta.N' |
| Riemann-von-Mangoldt-estimate | definition | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | riemannZeta.RvM, riemannZeta.Riemann_vonMangoldt_bound |
| zero-density-bound | definition | out-of-fragment | real-analysis; entropy-log | zero_density_bound, zero_density_bound.N |
| RS_theorem_19 | theorem | out-of-fragment | real-analysis; entropy-log | RS.theorem_19 |
| e-def | definition | no-signal | — | ZetaAppendix.e |
| lem:aachIBP | lemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | ZetaAppendix.lemma_aachIBP |
| lem:aachra | lemma | out-of-fragment | real-analysis | ZetaAppendix.lemma_aachra |
| lem:aachmonophase | lemma | out-of-fragment | real-analysis; rational-arithmetic | ZetaAppendix.lemma_aachmonophase |
| lem:aachdecre | lemma | out-of-fragment | real-analysis; rational-arithmetic | ZetaAppendix.lemma_aachdecre |
| lem:aachfour | lemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | ZetaAppendix.deriv_e |
| lem:aachcanc | lemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; rational-arithmetic | ZetaAppendix.lemma_aachcanc |
| prop:applem | proposition | out-of-fragment | real-analysis; rational-arithmetic | ZetaAppendix.proposition_applem |
| lem:abadeulmac' | lemma | out-of-fragment | sequences-sums; polynomials-fields; rational-arithmetic | ZetaAppendix.lemma_abadeulmac' |
| lem:abadeulmac | lemma | out-of-fragment | sequences-sums; polynomials-fields; rational-arithmetic | ZetaAppendix.lemma_abadeulmac |
| lem:abadtoabsum | lemma | out-of-fragment | sequences-sums; polynomials-fields; rational-arithmetic | ZetaAppendix.lemma_abadtoabsum |
| lem:abadusepoisson | lemma | out-of-fragment | real-analysis; sequences-sums; rational-arithmetic | ZetaAppendix.lemma_abadusepoisson |
| lem:abadeulmit1 | lemma | out-of-fragment | sequences-sums; rational-arithmetic | ZetaAppendix.lemma_abadeuleulmit1 |
| lem:abadeulmit2 | lemma | out-of-fragment | sequences-sums; rational-arithmetic | ZetaAppendix.lemma_abadeulmit2 |
| lem:abadimpseri | lemma | out-of-fragment | real-analysis; sequences-sums; polynomials-fields; rational-arithmetic | ZetaAppendix.lemma_abadimpseri |
| lem:abadsumas | lemma | out-of-fragment | real-analysis; sequences-sums; polynomials-fields; rational-arithmetic | ZetaAppendix.lemma_abadsumas |
| prop:dadaro | proposition | out-of-fragment | real-analysis; sequences-sums; polynomials-fields; rational-arithmetic | ZetaAppendix.proposition_dadaro |
| a0000000786 | remark | no-signal | — | — |
| kadiri-hadamard-B | definition | out-of-fragment | real-analysis; entropy-log; sequences-sums; polynomials-fields; maps-functions | Kadiri.hadamardB |
| kadiri-hadamard-identity | lemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; polynomials-fields; rational-arithmetic | Kadiri.hadamard_identity |
| kadiri-thm-3-1-q1-laplace-inversion | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Kadiri.kadiri_thm_3_1_q1_laplace_inversion |
| kadiri-thm-3-1-q1-eq-11 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums | Kadiri.kadiri_thm_3_1_q1_eq_11 |
| kadiri-thm-3-1-q1-eq-12 | sublemma | out-of-fragment | sequences-sums; geometry-topology; polynomials-fields; rational-arithmetic | Kadiri.kadiri_thm_3_1_q1_eq_12 |
| kadiri-thm-3-1-q1-top-horizontal-vanishes | sublemma | out-of-fragment | polynomials-fields; rational-arithmetic | Kadiri.kadiri_thm_3_1_q1_top_horizontal_vanishes |
| kadiri-thm-3-1-q1-bot-horizontal-vanishes | sublemma | out-of-fragment | polynomials-fields; rational-arithmetic | Kadiri.kadiri_thm_3_1_q1_bot_horizontal_vanishes |
| kadiri-thm-3-1-q1-functional-eq | sublemma | out-of-fragment | real-analysis; entropy-log; polynomials-fields; maps-functions; rational-arithmetic | Kadiri.kadiri_thm_3_1_q1_functional_eq |
| kadiri-thm-3-1-q1-I-3 | definition | out-of-fragment | real-analysis; maps-functions; rational-arithmetic | Kadiri.kadiri_thm_3_1_q1_I_3 |
| kadiri-thm-3-1-q1-shifted-eq-I123 | sublemma | out-of-fragment | polynomials-fields; rational-arithmetic | Kadiri.kadiri_thm_3_1_q1_shifted_eq_I123 |
| kadiri-thm-3-1-q1-eq-13 | sublemma | out-of-fragment | real-analysis; entropy-log; rational-arithmetic | Kadiri.kadiri_thm_3_1_q1_eq_13 |
| kadiri-thm-3-1-q1-eq-14 | sublemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; polynomials-fields; maps-functions; rational-arithmetic | Kadiri.kadiri_thm_3_1_q1_eq_14 |
| kadiri-thm-3-1-q1-gamma-symmetrization | sublemma | out-of-fragment | rational-arithmetic | Kadiri.kadiri_thm_3_1_q1_gamma_symmetrization |
| kadiri-thm-3-1-q1-eq-15 | sublemma | out-of-fragment | rational-arithmetic | Kadiri.kadiri_thm_3_1_q1_eq_15 |
| kadiri-thm-3-1-q1 | theorem | out-of-fragment | real-analysis; entropy-log; sequences-sums; polynomials-fields; maps-functions | Kadiri.kadiri_thm_3_1_q1 |
| kadiri-laplace-ibp | lemma | out-of-fragment | rational-arithmetic | _private.PrimeNumberTheoremAnd.IEANTN.Kadiri.0.Kadiri.laplaceKernel_hasDerivAt |
| kadiri-test-fn | definition | out-of-fragment | maps-functions | Kadiri.kadiriTestFn |
| kadiri-test-fn-contDiff | lemma | out-of-fragment | real-analysis; maps-functions | Kadiri.kadiriTestFn_contDiff |
| kadiri-test-fn-decay | lemma | out-of-fragment | maps-functions | Kadiri.kadiriTestFn_decay |
| kadiri-test-fn-laplace | lemma | out-of-fragment | rational-arithmetic | Kadiri.kadiriTestFn_laplaceTransform |
| kadiri-re-hadamardB-eq | lemma | out-of-fragment | sequences-sums; polynomials-fields | Kadiri.re_hadamardB_eq |
| kadiri-backlund-bound | lemma | out-of-fragment | real-analysis; entropy-log | Kadiri.backlund_bound |
| kadiri-laplace-re-decay | lemma | out-of-fragment | rational-arithmetic | _private.PrimeNumberTheoremAnd.IEANTN.Kadiri.0.Kadiri.deriv_deriv_eq_derivWithin_derivWithin_of_mem_Ioo |
| kadiri-summable-lap-at-zeros | lemma | out-of-fragment | sequences-sums; polynomials-fields | Kadiri.summable_lap_re_at_zeros |
| kadiri-identity-16-complex | sublemma | out-of-fragment | real-analysis; entropy-log; algebra-structures; sequences-sums; polynomials-fields; maps-functions; rational-arithmetic | Kadiri.identity_16_complex |
| kadiri-identity-16 | lemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; polynomials-fields; maps-functions; rational-arithmetic | Kadiri.identity_16 |
| kadiri-re-inner-eq | lemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; polynomials-fields; rational-arithmetic | Kadiri.re_inner_eq |
| kadiri-prop-2-1 | proposition | out-of-fragment | real-analysis; entropy-log; sequences-sums; polynomials-fields; maps-functions; rational-arithmetic | Kadiri.prop_2_1 |
| kadiri-eq-5 | lemma | out-of-fragment | real-analysis; entropy-log; sequences-sums; polynomials-fields; rational-arithmetic | Kadiri.eq_5 |
