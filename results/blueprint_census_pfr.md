# Blueprint fragment census

nodes: 218  ·  verdicts: no-signal=59, out-of-fragment=159

**lexical census, deterministic, LLM-free, Lean-free; REPORTS signals -- never a fidelity verdict.  An attempt-candidate still needs the full statement pipeline (metered) + the Lean RT lane.**

## Miss histogram (the vocabulary-growth price list)

- probability-entropy: 111
- algebra-structures: 49
- sequences-sums: 45
- sets-cardinality: 24
- real-analysis: 18

## Nodes

| label | kind | verdict | miss signals | lean |
|---|---|---|---|---|
| concave | lemma | no-signal | — | Real.strictConcaveOn_negMulLog |
| log-sum | lemma | out-of-fragment | real-analysis; sets-cardinality; sequences-sums | Real.sum_mul_log_div_leq |
| converse-log-sum | lemma | no-signal | — | Real.sum_mul_log_div_eq_iff |
| entropy-def | definition | out-of-fragment | real-analysis; probability-entropy; sequences-sums | ProbabilityTheory.entropy |
| relabeled-entropy | lemma | out-of-fragment | probability-entropy | ProbabilityTheory.entropy_comp_of_injective, ProbabilityTheory.entropy_of_comp_eq_of_comp |
| jensen-bound | lemma | out-of-fragment | real-analysis; probability-entropy | ProbabilityTheory.entropy_le_log_card, ProbabilityTheory.entropy_le_log_card_of_mem |
| uniform-def | definition | out-of-fragment | probability-entropy; sets-cardinality | ProbabilityTheory.IsUniform |
| unif-exist | lemma | out-of-fragment | probability-entropy; sets-cardinality | ProbabilityTheory.exists_isUniform, ProbabilityTheory.exists_isUniform_measureSpace |
| uniform-entropy | lemma | out-of-fragment | real-analysis; probability-entropy | ProbabilityTheory.IsUniform.entropy_eq |
| uniform-entropy-II | lemma | out-of-fragment | real-analysis | ProbabilityTheory.IsUniform.entropy_eq |
| bound-conc | lemma | out-of-fragment | probability-entropy | ProbabilityTheory.prob_ge_exp_neg_entropy |
| entropy-comm | lemma | out-of-fragment | probability-entropy | ProbabilityTheory.entropy_comm, ProbabilityTheory.entropy_assoc |
| condition-event-def | definition | out-of-fragment | probability-entropy | ProbabilityTheory.cond |
| conditional-entropy-def | definition | out-of-fragment | probability-entropy; sequences-sums | ProbabilityTheory.condEntropy |
| relabeled-entropy-cond | lemma | out-of-fragment | probability-entropy | ProbabilityTheory.condEntropy_comp_of_injective, ProbabilityTheory.condEntropy_of_injective' |
| chain-rule | lemma | out-of-fragment | probability-entropy | ProbabilityTheory.chain_rule, ProbabilityTheory.chain_rule' |
| conditional-chain-rule | lemma | out-of-fragment | probability-entropy | ProbabilityTheory.cond_chain_rule, ProbabilityTheory.cond_chain_rule' |
| information-def | definition | out-of-fragment | probability-entropy | ProbabilityTheory.mutualInfo, ProbabilityTheory.mutualInfo_def |
| alternative-mutual | lemma | no-signal | — | ProbabilityTheory.mutualInfo_comm, ProbabilityTheory.mutualInfo_eq_entropy_sub_condEntropy |
| mutual-nonneg | lemma | no-signal | — | ProbabilityTheory.mutualInfo_nonneg |
| subadditive | corollary | no-signal | — | ProbabilityTheory.entropy_pair_le_add |
| cond-reduce | corollary | no-signal | — | ProbabilityTheory.condEntropy_le_entropy |
| submodularity | corollary | out-of-fragment | probability-entropy | ProbabilityTheory.entropy_submodular, ProbabilityTheory.condEntropy_comp_ge |
| alt-submodularity | corollary | out-of-fragment | probability-entropy | ProbabilityTheory.entropy_triple_add_entropy_le |
| independent-def | definition | out-of-fragment | probability-entropy | ProbabilityTheory.IndepFun |
| vanish-entropy | lemma | out-of-fragment | probability-entropy | ProbabilityTheory.mutualInfo_eq_zero |
| add-entropy | corollary | out-of-fragment | probability-entropy | ProbabilityTheory.entropy_pair_eq_add |
| conditional-mutual-def | definition | out-of-fragment | probability-entropy; sequences-sums | ProbabilityTheory.condMutualInfo |
| conditional-mutual-alt | lemma | no-signal | — | ProbabilityTheory.condMutualInfo_eq, ProbabilityTheory.condMutualInfo_eq' |
| conditional-nonneg | lemma | out-of-fragment | probability-entropy | ProbabilityTheory.condMutualInfo_nonneg |
| conditional-independent-def | definition | out-of-fragment | probability-entropy | ProbabilityTheory.CondIndepFun |
| conditional-vanish | lemma | out-of-fragment | probability-entropy | ProbabilityTheory.condMutualInfo_eq_zero |
| cond-trial-ent | corollary | out-of-fragment | probability-entropy | ProbabilityTheory.ent_of_cond_indep |
| neg-ent | lemma | no-signal | — | ProbabilityTheory.entropy_neg |
| shear-ent | lemma | no-signal | — | ProbabilityTheory.condEntropy_add_right, ProbabilityTheory.condEntropy_add_left, ProbabilityTheory.condEntropy_sub_right, ProbabilityTheory.condEntropy_sub_left |
| sumset-lower-gen | lemma | out-of-fragment | probability-entropy | ProbabilityTheory.max_entropy_sub_mutualInfo_le_entropy_add, ProbabilityTheory.max_entropy_sub_mutualInfo_le_entropy_sub |
| sumset-lower-gen-cond | corollary | out-of-fragment | probability-entropy | ProbabilityTheory.max_condEntropy_sub_condMutualInfo_le_condEntropy_mul, ProbabilityTheory.max_condEntropy_sub_condMutualInfo_le_condEntropy_div |
| sumset-lower | corollary | out-of-fragment | probability-entropy | ProbabilityTheory.max_entropy_le_entropy_add, ProbabilityTheory.max_entropy_le_entropy_sub |
| copy-ent | lemma | no-signal | — | ProbabilityTheory.IdentDistrib.entropy_congr |
| independent-exist | lemma | out-of-fragment | probability-entropy; sequences-sums | ProbabilityTheory.independent_copies, ProbabilityTheory.independent_copies', ProbabilityTheory.independent_copies_two, ProbabilityTheory.independent_copies3_nondep |
| ruz-dist-def | definition | out-of-fragment | probability-entropy | rdist_def |
| dist-zero | lemma | out-of-fragment | probability-entropy | rdist_zero_eq_half_ent |
| ruz-copy | lemma | no-signal | — | ProbabilityTheory.IdentDistrib.rdist_congr |
| ruz-indep | lemma | out-of-fragment | probability-entropy | ProbabilityTheory.IndepFun.rdist_eq |
| ruzsa-symm | lemma | out-of-fragment | probability-entropy | rdist_symm |
| ruzsa-diff | lemma | out-of-fragment | probability-entropy | diff_ent_le_rdist |
| ruzsa-growth | lemma | out-of-fragment | probability-entropy | diff_ent_le_rdist', diff_ent_le_rdist'' |
| ruzsa-nonneg | lemma | out-of-fragment | probability-entropy | rdist_nonneg |
| dist-projection | lemma | out-of-fragment | probability-entropy; algebra-structures | ent_of_proj_le |
| ruzsa-triangle-improved | lemma | out-of-fragment | probability-entropy | ent_of_diff_le |
| ruzsa-triangle | lemma | out-of-fragment | probability-entropy | rdist_triangle |
| cond-dist-def | definition | out-of-fragment | probability-entropy; sequences-sums | condRuzsaDist |
| cond-dist-alt | lemma | out-of-fragment | probability-entropy | condRuzsaDist_of_copy, condRuzsaDist'_of_copy, condRuzsaDist_of_indep, condRuzsaDist'_of_indep |
| kv | lemma | out-of-fragment | probability-entropy | kaimanovich_vershik |
| cond-indep-exist | lemma | out-of-fragment | probability-entropy | ProbabilityTheory.condIndep_copies |
| entropic-bsg | lemma | out-of-fragment | probability-entropy; sets-cardinality; sequences-sums | ent_bsg |
| cond-dist-fact | lemma | out-of-fragment | probability-entropy; algebra-structures | condRuzsaDist_le, condRuzsaDist_le' |
| first-useful | lemma | out-of-fragment | probability-entropy; algebra-structures | condRuzsaDist_diff_le, condRuzsaDist_diff_le', condRuzsaDist_diff_le'', condRuzsaDist_diff_le''' |
| second-useful | lemma | out-of-fragment | probability-entropy; algebra-structures | condRuzsaDist_diff_ofsum_le |
| sym-group-def | definition | out-of-fragment | probability-entropy; algebra-structures | symmGroup |
| sym-group | lemma | out-of-fragment | probability-entropy; algebra-structures | symmGroup |
| zero-large | lemma | out-of-fragment | probability-entropy | sub_mem_symmGroup |
| sym-zero | lemma | out-of-fragment | probability-entropy | isUniform_sub_const_of_rdist_eq_zero |
| lem:100pc-self | lemma | out-of-fragment | probability-entropy; algebra-structures | exists_isUniform_of_rdist_self_eq_zero |
| lem:100pc | corollary | out-of-fragment | probability-entropy; algebra-structures | exists_isUniform_of_rdist_eq_zero |
| fibring-ident | proposition | out-of-fragment | probability-entropy; algebra-structures | rdist_of_indep_eq_sum_fibre, rdist_le_sum_fibre |
| fibring-ineq | corollary | out-of-fragment | probability-entropy; algebra-structures | rdist_of_hom_le |
| cor-fibre | corollary | out-of-fragment | probability-entropy | sum_of_rdist_eq |
| eta-def | definition | no-signal | — | — |
| tau-def | definition | out-of-fragment | probability-entropy | tau |
| tau-copy | lemma | no-signal | — | ProbabilityTheory.IdentDistrib.tau_eq |
| tau-min-def | definition | out-of-fragment | probability-entropy | tau_minimizes |
| tau-min | proposition | no-signal | — | tau_minimizer_exists |
| distance-lower | lemma | out-of-fragment | probability-entropy | distance_ge_of_min |
| cond-distance-lower | lemma | out-of-fragment | probability-entropy | condRuzsaDistance_ge_of_min |
| first-fibre | lemma | no-signal | — | rdist_add_rdist_add_condMutual_eq |
| first-dist-sum | lemma | no-signal | — | rdist_of_sums_ge |
| first-cond | lemma | no-signal | — | condRuzsaDist_of_sums_ge |
| first-upper | lemma | no-signal | — | diff_rdist_le_1, diff_rdist_le_2, diff_rdist_le_3, diff_rdist_le_4 |
| first-estimate | lemma | no-signal | — | first_estimate |
| foursum-bound | lemma | no-signal | — | ent_ofsum_le |
| dist-sums | lemma | no-signal | — | rdist_of_sums_ge' |
| second-estimate-aux | lemma | no-signal | — | second_estimate_aux |
| second-estimate | lemma | no-signal | — | second_estimate |
| symm-lemma | lemma | no-signal | — | I₃_eq |
| uvw-s | lemma | no-signal | — | I₃_eq, sum_condMutual_le |
| total-dist | lemma | out-of-fragment | sequences-sums | sum_dist_diff_le |
| key-ident | lemma | no-signal | — | sum_uvw_eq_zero |
| construct-good-prelim | lemma | no-signal | — | construct_good_prelim |
| construct-good | lemma | out-of-fragment | sequences-sums | construct_good |
| de-prop | theorem | no-signal | — | tau_strictly_decreases |
| entropy-pfr | theorem | out-of-fragment | probability-entropy; algebra-structures | entropic_PFR_conjecture |
| ruz-cov | lemma | out-of-fragment | algebra-structures; sets-cardinality | Finset.ruzsa_covering_mul |
| pfr_aux | lemma | out-of-fragment | sets-cardinality | PFR_conjecture_aux |
| pfr | theorem | out-of-fragment | sets-cardinality | PFR_conjecture |
| pfr-cor | corollary | out-of-fragment | algebra-structures; sets-cardinality | PFR_conjecture' |
| eta-def-new | definition | no-signal | — | — |
| construct-good-prelim-improv | lemma | no-signal | — | construct_good_prelim' |
| construct-good-improv | lemma | out-of-fragment | sequences-sums | construct_good_improved' |
| averaged-construct-good | lemma | out-of-fragment | sequences-sums | averaged_construct_good |
| gen-ineq | lemma | out-of-fragment | probability-entropy | gen_ineq_00 |
| dist-diff-bound | lemma | out-of-fragment | sequences-sums | dist_diff_bound_1, dist_diff_bound_2 |
| de-prop-improv | theorem | no-signal | — | tau_strictly_decreases' |
| de-prop-lim-improv | theorem | no-signal | — | tau_minimizer_exists_rdist_eq_zero |
| entropy-pfr-improv | theorem | out-of-fragment | probability-entropy; algebra-structures | entropic_PFR_conjecture_improv |
| pfr_aux-improv | lemma | out-of-fragment | sets-cardinality | PFR_conjecture_improv_aux |
| pfr-improv | theorem | out-of-fragment | sets-cardinality | PFR_conjecture_improv |
| hb-thm | lemma | out-of-fragment | algebra-structures | hahn_banach |
| goursat | lemma | out-of-fragment | algebra-structures | goursat |
| hom-pfr | theorem | out-of-fragment | algebra-structures | homomorphism_pfr |
| energy-def | definition | out-of-fragment | algebra-structures; sets-cardinality | Finset.addEnergy' |
| cs-bound | lemma | out-of-fragment | algebra-structures; sets-cardinality | Finset.card_sq_le_card_mul_addEnergy' |
| bsg | lemma | out-of-fragment | algebra-structures; sets-cardinality | BSG |
| approx-hom-pfr | theorem | out-of-fragment | algebra-structures | approx_hom_pfr |
| gdual | lemma | out-of-fragment | algebra-structures | card_of_dual |
| gcount | lemma | out-of-fragment | algebra-structures | card_of_dual_constrained |
| gslice | lemma | out-of-fragment | algebra-structures; sets-cardinality | card_of_slice |
| approx-hom-pfr-no-const | corollary | out-of-fragment | algebra-structures | approx_hom_pfr' |
| torsion-free-doubling | lemma | out-of-fragment | probability-entropy; algebra-structures | torsion_free_doubling |
| torsion-dist-shrinking | lemma | out-of-fragment | probability-entropy; algebra-structures | torsion_dist_shrinking |
| app-ent-pfr | lemma | out-of-fragment | real-analysis; probability-entropy; algebra-structures | app_ent_PFR |
| pfr-projection' | lemma | out-of-fragment | real-analysis; probability-entropy; algebra-structures | PFR_projection' |
| pfr-projection | lemma | out-of-fragment | real-analysis; probability-entropy; algebra-structures | PFR_projection |
| single-fibres | lemma | out-of-fragment | real-analysis; algebra-structures; sets-cardinality | single_fibres |
| dimension-def | definition | out-of-fragment | real-analysis; algebra-structures; sets-cardinality | AffineSpace.finrank |
| weak-pfr-asymm | theorem | out-of-fragment | real-analysis; sets-cardinality | weak_PFR_asymm |
| weak-pfr-symm | theorem | out-of-fragment | real-analysis; sets-cardinality | weak_PFR |
| weak-pfr-int | theorem | out-of-fragment | real-analysis; sets-cardinality | weak_PFR_int |
| data-process-single | lemma | out-of-fragment | probability-entropy | ProbabilityTheory.entropy_comp_le |
| data-process-unc-one | lemma | out-of-fragment | probability-entropy | ProbabilityTheory.mutual_comp_le |
| data-process-unc | lemma | out-of-fragment | probability-entropy | ProbabilityTheory.mutual_comp_comp_le |
| data-process | lemma | no-signal | — | ProbabilityTheory.condMutual_comp_comp_le |
| sign-flip | lemma | no-signal | — | rdist_of_neg_le |
| klm-1 | lemma | out-of-fragment | probability-entropy; sequences-sums | kvm_ineq_I |
| klm-2 | lemma | out-of-fragment | probability-entropy; sequences-sums | kvm_ineq_II |
| klm-3 | lemma | out-of-fragment | probability-entropy; sequences-sums | kvm_ineq_III |
| compare-sums | lemma | out-of-fragment | probability-entropy; sequences-sums | ent_of_sum_le_ent_of_sum |
| sum-dilate-I | lemma | out-of-fragment | probability-entropy | ent_sub_nsmul_le, ent_of_sub_smul' |
| sum-dilate-II | lemma | out-of-fragment | probability-entropy | ent_sub_zsmul_sub_ent_le |
| multidist-def | definition | out-of-fragment | probability-entropy; sequences-sums | multiDist |
| multidist-copy | lemma | out-of-fragment | probability-entropy | multiDist_copy |
| multidist-indep | lemma | out-of-fragment | probability-entropy; sequences-sums | multiDist_indep |
| multidist-nonneg | lemma | no-signal | — | multiDist_nonneg |
| multidist-perm | lemma | no-signal | — | multiDist_of_perm |
| multidist-ruzsa-I | lemma | out-of-fragment | probability-entropy; sequences-sums | multidist_ruzsa_I |
| multidist-ruzsa-II | lemma | out-of-fragment | probability-entropy; sequences-sums | multidist_ruzsa_II |
| multidist-ruzsa-III | lemma | out-of-fragment | probability-entropy | multidist_ruzsa_III |
| multidist-ruzsa-IV | lemma | out-of-fragment | probability-entropy; sequences-sums | multidist_ruzsa_IV |
| multi-zero | proposition | out-of-fragment | algebra-structures | multidist_eq_zero |
| eta-def-multi | definition | no-signal | — | multiRefPackage |
| tau-def-multi | definition | out-of-fragment | sequences-sums | multiTau |
| tau-min-multi | definition | out-of-fragment | probability-entropy | multiTauMinimizes |
| tau-min-exist-multi | proposition | no-signal | — | multiTau_continuous, multiTau_min_exists |
| tau-ref | proposition | out-of-fragment | sequences-sums | multiTau_min_sum_le |
| multidist-lower | lemma | out-of-fragment | sequences-sums | sub_multiDistance_le |
| cond-multidist-def | definition | out-of-fragment | probability-entropy; sequences-sums | condMultiDist |
| cond-multidist-alt | lemma | out-of-fragment | probability-entropy; sequences-sums | condMultiDist_eq |
| cond-multidist-nonneg | lemma | out-of-fragment | probability-entropy | condMultiDist_nonneg |
| cond-multidist-lower | lemma | out-of-fragment | sequences-sums | sub_condMultiDistance_le |
| cond-multidist-lower-II | corollary | out-of-fragment | sequences-sums | sub_condMultiDistance_le' |
| multidist-chain-rule | lemma | out-of-fragment | probability-entropy; algebra-structures; sequences-sums | multiDist_chainRule |
| multidist-chain-rule-cond | lemma | out-of-fragment | probability-entropy; algebra-structures; sequences-sums | cond_multiDist_chainRule |
| multidist-chain-rule-iter | lemma | out-of-fragment | probability-entropy; algebra-structures; sequences-sums | iter_multiDist_chainRule, iter_multiDist_chainRule' |
| cor-multid | corollary | out-of-fragment | probability-entropy; algebra-structures; sequences-sums | cor_multiDist_chainRule |
| key | proposition | out-of-fragment | probability-entropy; sequences-sums | mutual_information_le |
| more-random | definition | out-of-fragment | probability-entropy; algebra-structures; sequences-sums | — |
| Zero-sum | lemma | no-signal | — | sum_of_z_eq_zero |
| prop:52 | proposition | no-signal | — | mutual_information_le_t_12, mutual_information_le_t_13, mutual_information_le_t_23 |
| ent-w | lemma | out-of-fragment | sequences-sums | entropy_of_W_le |
| ent-z2 | lemma | out-of-fragment | sequences-sums | entropy_of_Z_two_le |
| mutual-w-z2 | lemma | no-signal | — | mutual_of_W_Z_two_le |
| xi-z2-w-dist | lemma | out-of-fragment | sequences-sums | sum_of_conditional_distance_le |
| lem:get-better | lemma | out-of-fragment | probability-entropy; algebra-structures; sequences-sums | dist_of_U_add_le |
| k-vanish | proposition | no-signal | — | k_eq_zero |
| main-entropy | theorem | out-of-fragment | probability-entropy; algebra-structures | dist_of_X_U_H_le |
| pfr_aux_torsion | lemma | out-of-fragment | algebra-structures; sets-cardinality | torsion_PFR_conjecture_aux |
| pfr-torsion | theorem | out-of-fragment | algebra-structures; sets-cardinality | torsion_PFR |
| kl-div | definition | out-of-fragment | real-analysis; probability-entropy; sequences-sums | KLDiv |
| kl-div-copy | lemma | no-signal | — | ProbabilityTheory.IdentDistrib.KLDiv_eq |
| Gibbs | lemma | no-signal | — | KLDiv_nonneg |
| Gibbs-converse | lemma | no-signal | — | KLDiv_eq_zero_iff_identDistrib |
| kl-div-convex | lemma | out-of-fragment | sets-cardinality; sequences-sums | KLDiv_of_convex |
| kl-div-inj | lemma | no-signal | — | KLDiv_of_comp_inj |
| kl-sums | lemma | out-of-fragment | probability-entropy | KLDiv_add_le_KLDiv_of_indep |
| ckl-div | definition | out-of-fragment | probability-entropy; sequences-sums | — |
| kl-cond | lemma | out-of-fragment | probability-entropy | condKLDiv_eq |
| Conditional-Gibbs | lemma | no-signal | — | condKLDiv_nonneg |
| rhominus-def | definition | out-of-fragment | real-analysis; probability-entropy | rhoMinus |
| rhoplus-def | definition | out-of-fragment | probability-entropy | rhoPlus |
| rhoMinus_nonneg | lemma | no-signal | — | — |
| rhominus-subgroup | lemma | out-of-fragment | real-analysis; algebra-structures | rhoMinus_of_subgroup |
| rhoplus-subgroup | corollary | out-of-fragment | real-analysis; algebra-structures | rhoPlus_of_subgroup |
| rho-def | definition | no-signal | — | rho |
| rho_of_uniform | lemma | no-signal | — | — |
| rho-subgroup | lemma | out-of-fragment | algebra-structures | rho_of_subgroup |
| rho-invariant | lemma | no-signal | — | rho_of_translate |
| rho-cts | lemma | out-of-fragment | real-analysis; probability-entropy | rho_continuous |
| rho-sums | lemma | out-of-fragment | probability-entropy | rhoMinus_of_sum, rhoPlus_of_sum, rho_of_sum |
| rho-cond-def | definition | out-of-fragment | sequences-sums | condRho |
| rho-cond-invariant | lemma | no-signal | — | condRho_of_translate |
| rho-cond-relabeled | lemma | no-signal | — | condRho_of_injective |
| rho-cond | lemma | no-signal | — | condRhoMinus_le, condRhoPlus_le, condRho_le |
| rho-sums-sym | lemma | out-of-fragment | probability-entropy | rho_of_sum_le |
| rho-cond-sym | lemma | out-of-fragment | probability-entropy | condRho_of_sum_le |
| phi-min-def | definition | out-of-fragment | probability-entropy | phiMinimizes |
| phi-min-exist | lemma | no-signal | — | phi_min_exists |
| phi-first-estimate | lemma | no-signal | — | I_one_le |
| I1-I2-diff | lemma | no-signal | — | rdist_add_rdist_eq |
| phi-second-estimate | lemma | no-signal | — | I_two_le |
| rho-BSG-triplet | lemma | out-of-fragment | probability-entropy | dist_le_of_sum_zero |
| rho-BSG-triplet-symmetrized | lemma | out-of-fragment | probability-entropy; sequences-sums | dist_le_of_sum_zero' |
| rho-increase | lemma | out-of-fragment | probability-entropy; sequences-sums | condRho_sum_le |
| rho-increase-symmetrized | lemma | out-of-fragment | probability-entropy; sequences-sums | condRho_sum_le' |
| phi-minimizer-zero-distance | proposition | no-signal | — | dist_of_min_eq_zero |
| pfr-rho | proposition | out-of-fragment | probability-entropy; algebra-structures | rho_PFR_conjecture |
| pfr-9-aux | corollary | out-of-fragment | algebra-structures | better_PFR_conjecture_aux0 |
| pfr-9-aux' | corollary | out-of-fragment | algebra-structures; sets-cardinality | better_PFR_conjecture_aux |
| pfr-9 | theorem | out-of-fragment | algebra-structures; sets-cardinality | better_PFR_conjecture |
