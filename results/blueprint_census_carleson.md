# Blueprint fragment census

nodes: 180  ·  verdicts: attempt-candidate=5, no-signal=44, out-of-fragment=131

**lexical census, deterministic, LLM-free, Lean-free; REPORTS signals -- never a fidelity verdict.  An attempt-candidate still needs the full statement pipeline (metered) + the Lean RT lane.**

## Miss histogram (the vocabulary-growth price list)

- rational-arithmetic: 55
- maps-functions: 44
- sequences-sums: 39
- real-analysis: 35
- sets-cardinality: 35
- geometry-topology: 10
- polynomials-fields: 3
- primality: 1

## Nodes

| label | kind | verdict | miss signals | lean |
|---|---|---|---|---|
| tile-disjointness | lemma | no-signal | — | tile_disjointness |
| maximal-bound-antichain | lemma | out-of-fragment | sequences-sums | maximal_bound_antichain |
| dens2-antichain | lemma | out-of-fragment | sequences-sums; rational-arithmetic | dens2_antichain |
| dens1-antichain | lemma | out-of-fragment | sequences-sums; rational-arithmetic | dens1_antichain |
| tile-correlation | lemma | out-of-fragment | sets-cardinality; rational-arithmetic | Tile.correlation_le, Tile.correlation_zero_of_ne_subset |
| antichain-tile-count | lemma | out-of-fragment | sequences-sums; rational-arithmetic | Antichain.tile_count |
| correlation-kernel-bound | lemma | out-of-fragment | rational-arithmetic | Tile.correlation, Tile.mem_ball_of_correlation_ne_zero, Tile.correlation_kernel_bound |
| tile-range-support | lemma | no-signal | — | Tile.range_support |
| tile-uncertainty | lemma | no-signal | — | Tile.uncertainty |
| tile-reach | lemma | out-of-fragment | sets-cardinality | Antichain.tile_reach |
| stack-density | lemma | out-of-fragment | sequences-sums | Antichain.stack_density |
| local-antichain-density | lemma | out-of-fragment | sequences-sums | Antichain.local_antichain_density, Antichain.Ep_inter_G_inter_Ip'_subset_E2 |
| global-antichain-density | lemma | out-of-fragment | sequences-sums | Antichain.global_antichain_density |
| grid-existence | lemma | no-signal | — | grid_existence |
| tile-structure | lemma | no-signal | — | tile_existence |
| tile-sum-operator | lemma | out-of-fragment | sequences-sums | tile_sum_operator, integrable_tile_sum_operator |
| counting-balls | lemma | out-of-fragment | sets-cardinality | counting_balls |
| cover-big-ball | lemma | no-signal | — | cover_big_ball |
| basic-grid-structure | lemma | out-of-fragment | sets-cardinality; rational-arithmetic | I1_prop_1, I3_prop_1, I2_prop_2, I3_prop_2, I3_prop_3_1, I3_prop_3_2 |
| cover-by-cubes | lemma | out-of-fragment | sets-cardinality | cover_by_cubes |
| dyadic-property | lemma | out-of-fragment | sets-cardinality | dyadic_property |
| transitive-boundary | lemma | no-signal | — | transitive_boundary |
| small-boundary | lemma | out-of-fragment | sequences-sums; rational-arithmetic | small_boundary |
| smaller-boundary | lemma | out-of-fragment | sequences-sums | smaller_boundary |
| boundary-measure | lemma | no-signal | — | boundary_measure |
| frequency-ball-cover | lemma | out-of-fragment | sets-cardinality | frequency_ball_cover |
| disjoint-frequency-cubes | lemma | no-signal | — | Construction.disjoint_frequency_cubes |
| frequency-cube-cover | lemma | out-of-fragment | sets-cardinality | Construction.iUnion_ball_subset_iUnion_Ω₁, Construction.ball_subset_Ω₁, Construction.Ω₁_subset_ball |
| Lipschitz-Holder-approximation | lemma | out-of-fragment | maps-functions | support_holderApprox_subset, enorm_holderApprox_sub_le, iLipENorm_holderApprox_le |
| finitary-Carleson | proposition | out-of-fragment | sequences-sums; polynomials-fields; maps-functions; rational-arithmetic | finitary_carleson |
| discrete-Carleson | proposition | out-of-fragment | sequences-sums; maps-functions; rational-arithmetic | discrete_carleson |
| antichain-operator | proposition | out-of-fragment | sequences-sums; rational-arithmetic | antichain_operator |
| forest-operator | proposition | out-of-fragment | sequences-sums; rational-arithmetic | forest_operator |
| Holder-van-der-Corput | proposition | out-of-fragment | rational-arithmetic | holder_van_der_corput |
| Hardy-Littlewood | proposition | out-of-fragment | sets-cardinality; maps-functions; rational-arithmetic | measure_biUnion_le_lintegral, hasStrongType_maximalFunction, measurable_maximalFunction, laverage_le_globalMaximalFunction |
| ball-metric-entropy | lemma | out-of-fragment | sets-cardinality | Θ.finite_and_mk_le_of_le_dist |
| monotone-cube-metrics | lemma | out-of-fragment | sets-cardinality; rational-arithmetic | Grid.dist_mono, Grid.dist_strictMono |
| kernel-summand | lemma | out-of-fragment | rational-arithmetic | dist_mem_Icc_of_Ks_ne_zero, enorm_Ks_le, enorm_Ks_sub_Ks_le |
| exceptional-set | lemma | no-signal | — | exceptional_set |
| forest-union | lemma | out-of-fragment | sequences-sums; rational-arithmetic | forest_union |
| forest-complement | lemma | out-of-fragment | sequences-sums; rational-arithmetic | forest_complement |
| first-exception | lemma | no-signal | — | first_exception |
| dense-cover | lemma | no-signal | — | dense_cover |
| pairwise-disjoint | lemma | attempt-candidate | — | pairwiseDisjoint_E1 |
| dyadic-union | lemma | out-of-fragment | sets-cardinality | dyadic_union |
| John-Nirenberg | lemma | attempt-candidate | — | john_nirenberg |
| second-exception | lemma | no-signal | — | second_exception |
| top-tiles | lemma | out-of-fragment | sequences-sums | top_tiles |
| tree-count | lemma | out-of-fragment | sequences-sums | tree_count |
| boundary-exception | lemma | no-signal | — | boundary_exception |
| third-exception | lemma | no-signal | — | third_exception |
| wiggle-order-1 | lemma | no-signal | — | smul_mono |
| wiggle-order-2 | lemma | no-signal | — | smul_C2_1_2 |
| wiggle-order-3 | lemma | no-signal | — | wiggle_order_11_10, wiggle_order_100, wiggle_order_500 |
| P-convex | lemma | out-of-fragment | geometry-topology | ordConnected_tilesAt |
| C-convex | lemma | out-of-fragment | geometry-topology | ordConnected_C |
| C1-convex | lemma | out-of-fragment | geometry-topology | ordConnected_C1 |
| C2-convex | lemma | out-of-fragment | geometry-topology | ordConnected_C2 |
| C3-convex | lemma | out-of-fragment | geometry-topology | ordConnected_C3 |
| C4-convex | lemma | out-of-fragment | geometry-topology | ordConnected_C4 |
| C5-convex | lemma | out-of-fragment | geometry-topology | ordConnected_C5 |
| dens-compare | lemma | out-of-fragment | sets-cardinality | dens1_le_dens' |
| C-dens1 | lemma | out-of-fragment | sets-cardinality | dens1_le |
| relation-geometry | lemma | no-signal | — | URel.eq, URel.not_disjoint |
| equivalence-relation | lemma | no-signal | — | equivalenceOn_urel |
| C6-forest | lemma | no-signal | — | C6_forest |
| forest-geometry | lemma | no-signal | — | forest_geometry |
| forest-convex | lemma | out-of-fragment | geometry-topology | forest_convex |
| forest-separation | lemma | out-of-fragment | sets-cardinality | forest_separation |
| forest-inner | lemma | out-of-fragment | sets-cardinality | forest_inner |
| forest-stacking | lemma | out-of-fragment | sequences-sums | forest_stacking |
| antichain-decomposition | lemma | out-of-fragment | geometry-topology | antichain_decomposition |
| L0-antichain | lemma | no-signal | — | iUnion_L0', pairwiseDisjoint_L0', antichain_L0' |
| L2-antichain | lemma | no-signal | — | antichain_L2 |
| L1-L3-antichain | lemma | no-signal | — | antichain_L1, antichain_L3 |
| layer-cake-representation | lemma | out-of-fragment | maps-functions | MeasureTheory.eLpNorm_pow_eq_distribution |
| covering-separable-space | lemma | out-of-fragment | sets-cardinality | Metric.dense_iff_iUnion_ball, TopologicalSpace.exists_countable_dense |
| classical-carleson | theorem | out-of-fragment | real-analysis; polynomials-fields; maps-functions | classical_carleson |
| metric-space-Carleson | theorem | out-of-fragment | real-analysis; sets-cardinality; maps-functions; rational-arithmetic | metric_carleson |
| linearised-metric-Carleson | theorem | out-of-fragment | real-analysis; sets-cardinality; maps-functions; rational-arithmetic | linearized_metric_carleson |
| a0000000013 | remark | attempt-candidate | — | — |
| two-sided-metric-space-Carleson | theorem | out-of-fragment | real-analysis; sets-cardinality; maps-functions; rational-arithmetic | two_sided_metric_carleson |
| nontangential-from-simple | lemma | out-of-fragment | maps-functions | nontangential_from_simple |
| calderon-zygmund-weak-1-1 | lemma | out-of-fragment | maps-functions; rational-arithmetic | czOperator_weak_1_1 |
| geometric-series-estimate | lemma | out-of-fragment | real-analysis; sequences-sums; rational-arithmetic | geometric_series_estimate |
| estimate-x-shift | lemma | out-of-fragment | maps-functions | estimate_x_shift |
| Cotlar-control | lemma | out-of-fragment | maps-functions; rational-arithmetic | cotlar_control |
| Cotlar-sets | lemma | out-of-fragment | maps-functions; rational-arithmetic | cotlar_set_F₁, cotlar_set_F₂ |
| Cotlar-estimate | lemma | out-of-fragment | maps-functions | cotlar_estimate |
| simple-nontangential-operator | lemma | out-of-fragment | real-analysis; maps-functions | simple_nontangential_operator, lowerSemicontinuous_simpleNontangentialOperator |
| small-annulus | lemma | out-of-fragment | real-analysis; maps-functions | small_annulus_right, small_annulus_left |
| nontangential-operator-boundary | lemma | out-of-fragment | maps-functions | nontangential_operator_boundary |
| maximal-theorem | lemma | out-of-fragment | rational-arithmetic | maximal_theorem |
| Lebesgue-differentiation | lemma | out-of-fragment | sequences-sums; maps-functions; rational-arithmetic | lebesgue_differentiation |
| disjoint-family-countable | lemma | out-of-fragment | sets-cardinality | Pairwise.countable_of_isOpen_disjoint |
| ball-covering | lemma | out-of-fragment | sets-cardinality | ball_covering |
| Calderon-Zygmund-decomposition | lemma | out-of-fragment | sets-cardinality; sequences-sums; maps-functions; rational-arithmetic | encard_czBall3_le, tsum_czRemainder', aemeasurable_czApproximation, czApproximation_add_czRemainder, enorm_czApproximation_le, enorm_czApproximation_le_infinite, eLpNorm_czApproximation_le, support_czRemainder'_subset, integral_czRemainder', integral_czRemainder, eLpNorm_czRemainder'_le, eLpNorm_czRemainder_le, tsum_volume_czBall3_le, volume_univ_le, tsum_eLpNorm_czRemainder'_le, tsum_eLpNorm_czRemainder_le |
| estimate-good | lemma | out-of-fragment | rational-arithmetic | estimate_good |
| estimate-bad-partial | lemma | out-of-fragment | sequences-sums; rational-arithmetic | estimate_bad_partial |
| estimate-F-set | lemma | out-of-fragment | rational-arithmetic | distribution_czOperatorBound |
| estimate-bad | lemma | out-of-fragment | rational-arithmetic | estimate_bad |
| smooth-approximation | lemma | out-of-fragment | real-analysis; maps-functions | close_smooth_approx_periodic |
| convergence-for-smooth | lemma | out-of-fragment | real-analysis; rational-arithmetic | fourierConv_ofTwiceDifferentiable |
| control-approximation-effect | lemma | out-of-fragment | real-analysis; sets-cardinality; rational-arithmetic | control_approximation_effect |
| exceptional-set-carleson | theorem | out-of-fragment | real-analysis; sets-cardinality; polynomials-fields; maps-functions | exceptional_set_carleson |
| real-Carleson | lemma | out-of-fragment | real-analysis; sets-cardinality; maps-functions; rational-arithmetic | rcarleson |
| Hilbert-strong-2-2 | lemma | out-of-fragment | real-analysis; maps-functions | Hilbert_strong_2_2 |
| van-der-Corput | lemma | out-of-fragment | real-analysis; maps-functions; rational-arithmetic | van_der_Corput |
| Dirichlet-kernel | lemma | out-of-fragment | real-analysis; sequences-sums; maps-functions; rational-arithmetic | dirichletKernel_eq, partialFourierSum_eq_conv_dirichletKernel |
| lower-secant-bound | lemma | out-of-fragment | rational-arithmetic | lower_secant_bound' |
| spectral-projection-bound | lemma | out-of-fragment | maps-functions | spectral_projection_bound |
| Hilbert-kernel-bound | lemma | out-of-fragment | real-analysis | Hilbert_kernel_bound |
| Hilbert-kernel-regularity | lemma | out-of-fragment | real-analysis; rational-arithmetic | Hilbert_kernel_regularity |
| fourier-coeff-derivative | lemma | out-of-fragment | real-analysis; rational-arithmetic | fourierCoeffOn_of_hasDerivAt |
| convergence-of-coeffs-summable | lemma | out-of-fragment | real-analysis; sequences-sums | hasSum_fourier_series_of_summable |
| convergence-for-twice-contdiff | lemma | out-of-fragment | real-analysis | fourierConv_ofTwiceDifferentiable |
| modulated-averaged-projection | lemma | out-of-fragment | maps-functions | modulated_averaged_projection |
| periodic-domain-shift | lemma | out-of-fragment | maps-functions | Function.Periodic.intervalIntegral_add_eq, intervalIntegral.integral_comp_sub_right |
| Young-convolution | lemma | out-of-fragment | real-analysis; maps-functions; rational-arithmetic | young_convolution |
| integrable-bump-convolution | lemma | out-of-fragment | maps-functions | integrable_bump_convolution |
| Dirichlet-approximation | lemma | out-of-fragment | real-analysis; primality; maps-functions; rational-arithmetic | continuous_dirichletApprox, periodic_dirichletApprox, approxHilbertTransform_eq_dirichletApprox, dist_dirichletApprox_le |
| Dirichlet-Hilbert | lemma | no-signal | — | Dirichlet_Hilbert_diff |
| partial-Fourier-sum-bound | lemma | out-of-fragment | real-analysis; maps-functions; rational-arithmetic | partialFourierSum_bound |
| real-Carleson-operator-measurable | lemma | out-of-fragment | real-analysis; maps-functions | carlesonOperatorReal_measurable |
| partial-Fourier-sums-of-small | lemma | out-of-fragment | real-analysis; sets-cardinality; maps-functions; rational-arithmetic | control_approximation_effect |
| real-line-metric | lemma | out-of-fragment | real-analysis | instProperSpaceReal, locallyCompact_of_proper, Real.instCompleteSpace |
| real-line-ball | lemma | out-of-fragment | real-analysis | Real.ball_eq_Ioo |
| real-line-measure | lemma | out-of-fragment | real-analysis | instIsAddHaarMeasureVolume |
| real-line-ball-measure | lemma | out-of-fragment | real-analysis | Real.volume_ball |
| real-line-doubling | lemma | out-of-fragment | real-analysis | MeasureTheory.InnerProductSpace.IsDoubling |
| frequency-metric | lemma | out-of-fragment | maps-functions | instFunctionDistancesReal |
| oscillation-control | lemma | no-signal | — | oscillation_control |
| frequency-monotone | lemma | out-of-fragment | sets-cardinality | frequency_monotone |
| frequency-ball-doubling | lemma | out-of-fragment | real-analysis | frequency_ball_doubling |
| frequency-ball-growth | lemma | out-of-fragment | real-analysis; sets-cardinality | frequency_ball_growth |
| integer-ball-cover | lemma | out-of-fragment | real-analysis; sets-cardinality | integer_ball_cover |
| real-van-der-Corput | lemma | out-of-fragment | real-analysis; maps-functions; rational-arithmetic | real_van_der_Corput |
| int-continuous | lemma | out-of-fragment | real-analysis; maps-functions | continuous_carlesonOperatorIntegrand, rightContinuous_carlesonOperatorIntegrand, leftContinuous_carlesonOperatorIntegrand, measurable_carlesonOperatorIntegrand, enorm_carlesonOperatorIntegrand_le |
| R-truncation | lemma | out-of-fragment | maps-functions; rational-arithmetic | R_truncation |
| S-truncation | lemma | out-of-fragment | sequences-sums; maps-functions; rational-arithmetic | S_truncation |
| linearized-truncation | lemma | out-of-fragment | sequences-sums; maps-functions; rational-arithmetic | linearized_truncation |
| convex-scales | lemma | no-signal | — | TileStructure.Forest.convex_scales |
| dyadic-partitions | lemma | out-of-fragment | sets-cardinality | TileStructure.Forest.biUnion_𝓙, TileStructure.Forest.pairwiseDisjoint_𝓙, TileStructure.Forest.biUnion_𝓛, TileStructure.Forest.pairwiseDisjoint_𝓛 |
| pointwise-tree-estimate | lemma | out-of-fragment | sequences-sums; maps-functions | TileStructure.Forest.pointwise_tree_estimate |
| first-tree-pointwise | lemma | no-signal | — | TileStructure.Forest.first_tree_pointwise |
| second-tree-pointwise | lemma | out-of-fragment | sequences-sums | TileStructure.Forest.second_tree_pointwise |
| third-tree-pointwise | lemma | out-of-fragment | sequences-sums | TileStructure.Forest.third_tree_pointwise |
| tree-projection-estimate | lemma | out-of-fragment | sequences-sums | TileStructure.Forest.tree_projection_estimate |
| nontangential-operator-bound | lemma | no-signal | — | TileStructure.Forest.nontangential_operator_bound |
| boundary-operator-bound | lemma | out-of-fragment | maps-functions | TileStructure.Forest.boundary_operator_bound |
| boundary-overlap | lemma | no-signal | — | TileStructure.Forest.boundary_overlap |
| densities-tree-bound | lemma | out-of-fragment | sets-cardinality; sequences-sums | TileStructure.Forest.density_tree_bound1, TileStructure.Forest.density_tree_bound2 |
| local-dens1-tree-bound | lemma | no-signal | — | TileStructure.Forest.local_dens1_tree_bound |
| local-dens2-tree-bound | lemma | no-signal | — | TileStructure.Forest.local_dens2_tree_bound |
| adjoint-tile-support | lemma | no-signal | — | TileStructure.Forest.adjoint_tile_support1, TileStructure.Forest.adjoint_tile_support2 |
| adjoint-tree-estimate | lemma | out-of-fragment | sequences-sums | TileStructure.Forest.adjoint_tree_estimate, TileStructure.Forest.indicator_adjoint_tree_estimate |
| adjoint-tree-control | lemma | no-signal | — | TileStructure.Forest.adjoint_tree_control |
| correlation-separated-trees | lemma | out-of-fragment | sequences-sums | TileStructure.Forest.correlation_separated_trees |
| correlation-distant-tree-parts | lemma | out-of-fragment | sets-cardinality; sequences-sums | TileStructure.Forest.correlation_distant_tree_parts |
| correlation-near-tree-parts | lemma | out-of-fragment | sets-cardinality; sequences-sums; rational-arithmetic | TileStructure.Forest.correlation_near_tree_parts |
| overlap-implies-distance | lemma | out-of-fragment | sets-cardinality | TileStructure.Forest.𝔗_subset_𝔖₀, TileStructure.Forest.overlap_implies_distance |
| dyadic-partition-1 | lemma | no-signal | — | TileStructure.Forest.union_𝓙₅, TileStructure.Forest.pairwiseDisjoint_𝓙₅ |
| Lipschitz-partition-unity | lemma | out-of-fragment | sequences-sums; maps-functions; rational-arithmetic | TileStructure.Forest.sum_χ, TileStructure.Forest.χ_le_indicator, TileStructure.Forest.dist_χ_le |
| moderate-scale-change | lemma | no-signal | — | TileStructure.Forest.moderate_scale_change |
| Holder-correlation-tree | lemma | out-of-fragment | sequences-sums; rational-arithmetic | TileStructure.Forest.holder_correlation_tree |
| Holder-correlation-tile | lemma | out-of-fragment | rational-arithmetic | TileStructure.Forest.holder_correlation_tile |
| limited-scale-impact | lemma | no-signal | — | TileStructure.Forest.limited_scale_impact |
| local-tree-control | lemma | no-signal | — | TileStructure.Forest.local_tree_control |
| scales-impacting-interval | lemma | no-signal | — | TileStructure.Forest.scales_impacting_interval |
| global-tree-control-1 | lemma | out-of-fragment | rational-arithmetic | TileStructure.Forest.global_tree_control1_edist_left, TileStructure.Forest.global_tree_control1_edist_right, TileStructure.Forest.global_tree_control1_supbound |
| global-tree-control-2 | lemma | no-signal | — | TileStructure.Forest.global_tree_control2 |
| lower-oscillation-bound | lemma | no-signal | — | TileStructure.Forest.lower_oscillation_bound |
| dyadic-partition-2 | lemma | no-signal | — | TileStructure.Forest.union_𝓙₆, TileStructure.Forest.pairwiseDisjoint_𝓙₆ |
| bound-for-tree-projection | lemma | out-of-fragment | rational-arithmetic | TileStructure.Forest.bound_for_tree_projection |
| thin-scale-impact | lemma | out-of-fragment | rational-arithmetic | TileStructure.Forest.thin_scale_impact |
| square-function-count | lemma | out-of-fragment | sequences-sums; rational-arithmetic | TileStructure.Forest.square_function_count |
| forest-row-decomposition | lemma | out-of-fragment | geometry-topology | TileStructure.Forest.rowDecomp, TileStructure.Forest.biUnion_rowDecomp, TileStructure.Forest.pairwiseDisjoint_rowDecomp |
| row-bound | lemma | no-signal | — | TileStructure.Forest.row_bound, TileStructure.Forest.indicator_row_bound |
| row-correlation | lemma | attempt-candidate | — | TileStructure.Forest.row_correlation |
| disjoint-row-support | lemma | attempt-candidate | — | TileStructure.Forest.pairwiseDisjoint_rowSupport |
