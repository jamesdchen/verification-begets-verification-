# Blueprint fragment census

nodes: 241  ·  verdicts: attempt-candidate=1, no-signal=66, out-of-fragment=174

**lexical census, deterministic, LLM-free, Lean-free; REPORTS signals -- never a fidelity verdict.  An attempt-candidate still needs the full statement pipeline (metered) + the Lean RT lane.**

## Miss histogram (the vocabulary-growth price list)

- magmas-equational: 154
- algebra-structures: 21
- maps-functions: 17
- sets-cardinality: 12
- graphs-combinatorics: 5
- sequences-sums: 5
- polynomials-fields: 4
- primality: 4
- geometry-topology: 2

## Nodes

| label | kind | verdict | miss signals | lean |
|---|---|---|---|---|
| 1323-construct | lemma | out-of-fragment | magmas-equational | Eq1323.eq1323_if_conditions |
| bij | lemma | out-of-fragment | algebra-structures; sets-cardinality; maps-functions | Eq1323.ϕ |
| build-magma | lemma | out-of-fragment | algebra-structures; sets-cardinality | Eq1323.op_Ly_Ry_eq_LSy |
| partial-1323 | definition | no-signal | — | — |
| partial-1323-sound | lemma | no-signal | — | — |
| greedy-1323 | lemma | no-signal | — | Eq1323.extend |
| greedy-iterate | corollary | no-signal | — | Eq1323.exists_complete_function |
| 1323-refute-2744 | corollary | out-of-fragment | magmas-equational | Eq1323.Equation1323_not_implies_Equation2744 |
| 1516-seed | definition | no-signal | — | — |
| 1516-ext | lemma | no-signal | — | — |
| 1516-ext-var | lemma | no-signal | — | — |
| 1516-base | corollary | out-of-fragment | magmas-equational | — |
| aux | lemma | out-of-fragment | maps-functions | — |
| part-exist | lemma | no-signal | — | — |
| first-ext | lemma | no-signal | — | — |
| second-ext | lemma | no-signal | — | — |
| axiom-b | proposition | no-signal | — | — |
| axiom-c | proposition | no-signal | — | — |
| 1516-no-255 | corollary | out-of-fragment | magmas-equational | — |
| mag | theorem | out-of-fragment | magmas-equational; maps-functions | — |
| sm-def | definition | out-of-fragment | algebra-structures | Eq1729.SM |
| sm-1729 | lemma | out-of-fragment | sets-cardinality; magmas-equational | Eq1729.SM_square_eq_double, Eq1729.SM_square_square_eq_zero, Eq1729.SM_satisfies_1729 |
| n-def | definition | out-of-fragment | algebra-structures; graphs-combinatorics; magmas-equational | Eq1729.N, Eq1729.N_order, Eq1729.parent |
| n-prop | lemma | no-signal | — | Eq1729.N_countable, Eq1729.N_order |
| ra-defn | definition | no-signal | — | Eq1729.R' |
| ra-prop | lemma | no-signal | — | Eq1729.R'_axiom_iia, Eq1729.R'_axiom_iib |
| l0-la | lemma | out-of-fragment | maps-functions | Eq1729.L', Eq1729.L'_0_eq_L₀' |
| Eq1729.reduce_to_new_axioms | lemma | out-of-fragment | magmas-equational; maps-functions | — |
| part-sol | definition | out-of-fragment | sets-cardinality; geometry-topology; maps-functions | Eq1729.PartialSolution |
| partial-exist | lemma | no-signal | — | Eq1729.TrivialPartialSolution |
| chain | lemma | out-of-fragment | sequences-sums; magmas-equational | Eq1729.use_chain |
| enlarge-l0 | proposition | no-signal | — | Eq1729.enlarge_L₀' |
| enlarge-l0-many | proposition | out-of-fragment | sets-cardinality | Eq1729.enlarge_L₀'_multiple |
| enlarge-S-induct-axioms | proposition | no-signal | — | Eq1729.enlarge_S'_induction_with_axioms |
| enlarge-S-induct | proposition | no-signal | — | Eq1729.enlarge_S'_induction |
| enlarge-S | proposition | no-signal | — | Eq1729.enlarge_S' |
| enlarge-op | proposition | no-signal | — | Eq1729.enlarge_op |
| 1729_refute_817 | theorem | out-of-fragment | magmas-equational | Eq1729.not_817 |
| 677-basic | lemma | out-of-fragment | magmas-equational | — |
| 255-equiv | lemma | out-of-fragment | magmas-equational | — |
| linear-obstruction | lemma | out-of-fragment | algebra-structures; magmas-equational; polynomials-fields | — |
| linear-2 | lemma | out-of-fragment | algebra-structures; magmas-equational | — |
| op-prop | lemma | no-signal | — | — |
| op-2-677 | lemma | no-signal | — | — |
| 677-satisfy | corollary | no-signal | — | — |
| a0000000397 | corollary | out-of-fragment | magmas-equational | — |
| irred-desc | theorem | out-of-fragment | primality | — |
| unique-factorization | corollary | out-of-fragment | primality | Refutation_854.unique_factorization |
| graph-desc | corollary | no-signal | — | — |
| 854-anti | theorem | out-of-fragment | magmas-equational | Refutation_854.not_3316_3925 |
| 854-equiv | lemma | out-of-fragment | magmas-equational | — |
| 854-equiv-2 | lemma | out-of-fragment | magmas-equational | — |
| a0000000429 | corollary | no-signal | — | — |
| 854-extend | proposition | out-of-fragment | magmas-equational | Refutation_854.Greedy.Extension1.next_ok |
| extend-854 | corollary | out-of-fragment | primality; magmas-equational | Refutation_854.Greedy.exists_extension |
| 854-413 | corollary | out-of-fragment | magmas-equational | Refutation_854.not_413_1045 |
| 854-1045 | corollary | out-of-fragment | magmas-equational | Refutation_854.not_413_1045 |
| 854-relation | lemma | out-of-fragment | magmas-equational | — |
| free-relate | definition | no-signal | — | — |
| free-854 | theorem | out-of-fragment | magmas-equational | — |
| edge-disjoint | corollary | attempt-candidate | — | — |
| 906-3862 | theorem | out-of-fragment | magmas-equational | Eq906.Finite.Equation906_implies_Equation3862 |
| free-theory | definition | out-of-fragment | algebra-structures; magmas-equational; maps-functions | FreeMagmaWithLaws |
| freemag-exist | theorem | out-of-fragment | magmas-equational | FreeMagma.EvalFreeMagmaWithLawsUniversalProperty |
| a0000000306 | example | out-of-fragment | magmas-equational | — |
| facm | example | out-of-fragment | algebra-structures; magmas-equational | — |
| freeleft | example | out-of-fragment | magmas-equational | — |
| freeconst | example | out-of-fragment | magmas-equational | — |
| canonical-invariant | theorem | out-of-fragment | magmas-equational | — |
| anti-impl | corollary | out-of-fragment | magmas-equational | — |
| a0000000312 | example | out-of-fragment | magmas-equational | — |
| a0000000313 | example | no-signal | — | — |
| a0000000314 | example | out-of-fragment | magmas-equational | — |
| a0000000315 | example | out-of-fragment | magmas-equational | — |
| confluent-theory | definition | out-of-fragment | sequences-sums; graphs-combinatorics; magmas-equational | — |
| a0000000316 | example | no-signal | — | — |
| a0000000317 | example | out-of-fragment | magmas-equational | — |
| a0000000318 | example | no-signal | — | — |
| free-confluent | theorem | out-of-fragment | magmas-equational | — |
| confluent-anti-impl | corollary | out-of-fragment | sequences-sums; magmas-equational | — |
| 477-confl | theorem | no-signal | — | — |
| 477-lemma | lemma | no-signal | — | — |
| magma-def | definition | out-of-fragment | algebra-structures; magmas-equational | Magma |
| free-magma-def | definition | out-of-fragment | magmas-equational | FreeMagma |
| a0000000006 | lemma | out-of-fragment | sets-cardinality; magmas-equational | FreeMagma.elementsOfNumNodesEq_card_eq_catalan_mul_pow |
| induced-def | definition | out-of-fragment | algebra-structures; magmas-equational; maps-functions | — |
| law-def | definition | out-of-fragment | magmas-equational | Law.MagmaLaw |
| models-def | definition | out-of-fragment | magmas-equational | models |
| derivation-def | definition | out-of-fragment | magmas-equational | derive |
| sound-complete | theorem | out-of-fragment | magmas-equational | Completeness |
| compactness-thm | corollary | out-of-fragment | sets-cardinality | — |
| push | lemma | out-of-fragment | magmas-equational; maps-functions | — |
| equiv | lemma | out-of-fragment | magmas-equational | — |
| law-count | lemma | out-of-fragment | magmas-equational | — |
| law-count-sym | lemma | out-of-fragment | magmas-equational | — |
| law-count-triv | lemma | out-of-fragment | magmas-equational | — |
| a0000000345 | remark | out-of-fragment | algebra-structures; magmas-equational | — |
| a0000000347 | remark | out-of-fragment | algebra-structures; sequences-sums; magmas-equational; polynomials-fields | — |
| a0000000352 | remark | out-of-fragment | algebra-structures; sets-cardinality; primality; geometry-topology; magmas-equational; polynomials-fields | — |
| 14_implies_23 | theorem | no-signal | — | Subgraph.Equation14_implies_Equation23 |
| impl | definition | out-of-fragment | magmas-equational | — |
| pre-order | lemma | out-of-fragment | magmas-equational | — |
| maximal | lemma | out-of-fragment | magmas-equational | Law.MagmaLaw.Equation1_maximal |
| minimal | lemma | out-of-fragment | magmas-equational | Law.MagmaLaw.Equation2_minimal |
| duality | lemma | out-of-fragment | magmas-equational | Law.MagmaLaw.implies_iff_dual |
| diag | theorem | out-of-fragment | magmas-equational | — |
| constant-impl | theorem | out-of-fragment | magmas-equational | — |
| variable-impl | theorem | out-of-fragment | magmas-equational | Law.MagmaLaw.SameCount.derive |
| 387_implies_43 | theorem | no-signal | — | Subgraph.Equation387_implies_Equation43 |
| 29_equiv_14 | theorem | no-signal | — | Subgraph.Equation29_implies_Equation14 |
| 14_implies_29 | theorem | no-signal | — | Subgraph.Equation14_implies_Equation29 |
| 3744_implies_3722_381 | theorem | no-signal | — | Subgraph.Equation3744_implies_Equation3722, Subgraph.Equation3744_implies_Equation381 |
| 1689_equiv_2 | theorem | no-signal | — | Subgraph.Equation1689_implies_Equation2, Subgraph.Equation2_implies_Equation1689 |
| 1571_impl | theorem | out-of-fragment | algebra-structures; magmas-equational | Subgraph.Equation1571_implies_Equation2662, Subgraph.Equation1571_implies_Equation40, Subgraph.Equation1571_implies_Equation23, Subgraph.Equation1571_implies_Equation8, Subgraph.Equation1571_implies_Equation16, Subgraph.Equation1571_implies_Equation43, Subgraph.Equation1571_implies_Equation4512 |
| 953_equiv_2 | theorem | no-signal | — | Subgraph.Equation953_implies_Equation2 |
| sheffer | theorem | no-signal | — | Sheffer.Equation345169_is_Boolean |
| natural-central-groupoid | theorem | out-of-fragment | algebra-structures | — |
| a0000000165 | example | out-of-fragment | algebra-structures; magmas-equational | — |
| a0000000166 | example | out-of-fragment | algebra-structures; magmas-equational; polynomials-fields | — |
| partial-solution | definition | out-of-fragment | sets-cardinality; maps-functions | — |
| iteration | lemma | no-signal | — | — |
| extend | corollary | no-signal | — | — |
| no-inject | corollary | out-of-fragment | maps-functions | — |
| asterix-obelix | corollary | out-of-fragment | magmas-equational; maps-functions | — |
| asterix-obelix-finite | proposition | out-of-fragment | magmas-equational | — |
| partial-solution2 | definition | out-of-fragment | maps-functions | — |
| obelix-extend | lemma | out-of-fragment | sets-cardinality; maps-functions | — |
| a0000000191 | corollary | out-of-fragment | magmas-equational | — |
| 1722-extension | lemma | no-signal | — | Eq1722.Greedy.lift |
| 713-extension | lemma | no-signal | — | Eq1722.Greedy.lift |
| 1289-extension | lemma | no-signal | — | Eq1289.Greedy.lift |
| 73-extension | lemma | no-signal | — | — |
| 63-extension | lemma | no-signal | — | — |
| 1076-extension | lemma | no-signal | — | Eq1076.Greedy.lift |
| non_imp_1648_206_thm | theorem | out-of-fragment | magmas-equational | Equation1648_not_implies_Equation206 |
| non_imp_1659_4315_thm | theorem | out-of-fragment | magmas-equational | Equation1659_facts |
| add-E1 | lemma | no-signal | — | — |
| add-E2 | lemma | no-signal | — | — |
| finite-check | lemma | no-signal | — | — |
| extension-lemma | lemma | no-signal | — | Eq63.Greedy.Extension.next |
| dupont-iter | corollary | no-signal | — | Eq63.Greedy.exists_extension |
| non-inject | corollary | out-of-fragment | maps-functions | Eq63.Equation63_not_implies_Equation1692 |
| a0000000265 | theorem | out-of-fragment | magmas-equational | — |
| 1437-thm | theorem | out-of-fragment | magmas-equational | — |
| kis-thm | theorem | no-signal | — | InfModel.Finite.Equation374794_implies_Equation2, InfModel.Equation374794_not_implies_Equation2 |
| kis-thm2 | theorem | no-signal | — | InfModel.Equation28770_not_implies_Equation2 |
| 5093-nontrivial | theorem | out-of-fragment | magmas-equational | InfModel.Finite.Equation5093_implies_Equation2 |
| austin-two | theorem | out-of-fragment | magmas-equational | InfModel.Finite.two_variable_laws |
| ffg | lemma | no-signal | — | FiniteModel.Finite.f_ffg_implies_f_fgf |
| gff | lemma | no-signal | — | FiniteModel.Finite.f_gff_implies_f_fgf |
| period | lemma | no-signal | — | FiniteModel.Finite.fn_eventually_periodic' |
| finite_imp_3994_3588 | proposition | out-of-fragment | magmas-equational | InfModel.Finite.Equation3994_implies_Equation3588 |
| non_imp_3994_3588_thm | proposition | out-of-fragment | magmas-equational | InfModel.Equation3994_not_implies_Equation3588 |
| 3342 | proposition | out-of-fragment | magmas-equational | Eq3342.Finite.Equation3342_implies_Equation3522, Eq3342.Finite.Equation3342_implies_Equation4118 |
| 1167-1096 | proposition | out-of-fragment | magmas-equational | Eq1133.Finite.Equation1167_implies_Equation1096 |
| 1133-1167 | proposition | out-of-fragment | magmas-equational | Eq1133.Finite.Equation1133_implies_Equation1167 |
| 1441-4067-1443-3055 | proposition | out-of-fragment | magmas-equational | Eq1441.Finite.Equation1441_implies_Equation4067, Eq1441.Finite.Equation1443_implies_Equation3055 |
| 1681-3877-1701-1035 | proposition | out-of-fragment | magmas-equational | Eq1441.Finite.Equation1681_implies_Equation3877, Eq1441.Finite.Equation1701_implies_Equation1035 |
| a0000000279 | metametatheorem | no-signal | — | — |
| a0000000285 | metatheorem | no-signal | — | — |
| a0000000288 | metatheorem | out-of-fragment | magmas-equational | — |
| a0000000291 | metatheorem | out-of-fragment | magmas-equational | — |
| a0000000293 | metatheorem | out-of-fragment | magmas-equational | — |
| a0000000296 | metatheorem | out-of-fragment | magmas-equational | — |
| lifting-magma-family | definition | out-of-fragment | algebra-structures; magmas-equational; maps-functions | LiftingMagmaFamily |
| a0000000297 | example | out-of-fragment | algebra-structures; magmas-equational | — |
| a0000000298 | example | out-of-fragment | magmas-equational | — |
| lifting-magma-basis-evaluation | theorem | out-of-fragment | magmas-equational | MagmaLaw.models_iff_satisfies_ι |
| fundamental-property-of-invariants | theorem | out-of-fragment | magmas-equational | — |
| a0000000301 | remark | out-of-fragment | algebra-structures; magmas-equational; maps-functions | — |
| a0000000302 | remark | out-of-fragment | magmas-equational | — |
| a0000000303 | remark | out-of-fragment | sets-cardinality; magmas-equational | — |
| compatibility-between-magma-laws | lemma | out-of-fragment | sets-cardinality; magmas-equational | Law.satisfies_fin_satisfies_nat |
| a0000000525 | definition | no-signal | — | — |
| a0000000526 | definition | out-of-fragment | sequences-sums | — |
| a0000000528 | lemma | no-signal | — | — |
| a0000000529 | theorem | no-signal | — | — |
| a0000000531 | definition | no-signal | — | — |
| a0000000532 | theorem | no-signal | — | — |
| eq1 | definition | out-of-fragment | magmas-equational | Equation1 |
| eq2 | definition | out-of-fragment | magmas-equational | Equation2 |
| eq3 | definition | out-of-fragment | magmas-equational | Equation3 |
| eq4 | definition | out-of-fragment | magmas-equational | Equation4 |
| eq5 | definition | out-of-fragment | magmas-equational | Equation5 |
| eq6 | definition | out-of-fragment | magmas-equational | Equation6 |
| eq7 | definition | out-of-fragment | magmas-equational | Equation7 |
| eq8 | definition | out-of-fragment | magmas-equational | Equation8 |
| eq14 | definition | out-of-fragment | magmas-equational | Equation14 |
| eq16 | definition | out-of-fragment | magmas-equational | Equation16 |
| eq23 | definition | out-of-fragment | magmas-equational | Equation23 |
| eq29 | definition | out-of-fragment | magmas-equational | Equation29 |
| eq38 | definition | out-of-fragment | magmas-equational | Equation38 |
| eq39 | definition | out-of-fragment | magmas-equational | Equation39 |
| eq40 | definition | out-of-fragment | magmas-equational | Equation40 |
| eq41 | definition | out-of-fragment | magmas-equational | Equation41 |
| eq42 | definition | out-of-fragment | magmas-equational | Equation42 |
| eq43 | definition | out-of-fragment | magmas-equational | Equation43 |
| eq45 | definition | out-of-fragment | magmas-equational | Equation45 |
| eq46 | definition | out-of-fragment | magmas-equational | Equation46 |
| eq63 | definition | out-of-fragment | magmas-equational | Equation63 |
| eq65 | definition | out-of-fragment | magmas-equational | Equation65 |
| eq168 | definition | out-of-fragment | magmas-equational | Equation168 |
| eq206 | definition | out-of-fragment | magmas-equational | Equation206 |
| eq381 | definition | out-of-fragment | magmas-equational | Equation381 |
| eq387 | definition | out-of-fragment | magmas-equational | Equation387 |
| eq477 | definition | out-of-fragment | magmas-equational | Equation477 |
| eq854 | definition | out-of-fragment | magmas-equational | Equation953 |
| eq953 | definition | out-of-fragment | magmas-equational | Equation953 |
| eq1485 | definition | out-of-fragment | magmas-equational | Equation1491 |
| eq1491 | definition | out-of-fragment | magmas-equational | Equation1491 |
| eq1571 | definition | out-of-fragment | magmas-equational | Equation1571 |
| eq1648 | definition | out-of-fragment | magmas-equational | Equation1648 |
| eq1657 | definition | out-of-fragment | magmas-equational | Equation1657 |
| eq1659 | definition | out-of-fragment | magmas-equational | Equation1659 |
| eq1661 | definition | out-of-fragment | magmas-equational | Equation1661 |
| eq1689 | definition | out-of-fragment | magmas-equational | Equation1689 |
| eq1701 | definition | out-of-fragment | magmas-equational | Equation1701 |
| eq2662 | definition | out-of-fragment | magmas-equational | Equation2662 |
| eq3167 | definition | out-of-fragment | magmas-equational | Equation3167 |
| eq3588 | definition | out-of-fragment | magmas-equational | Equation3588 |
| eq3722 | definition | out-of-fragment | magmas-equational | Equation3722 |
| eq3744 | definition | out-of-fragment | magmas-equational | Equation3744 |
| eq3994 | definition | out-of-fragment | magmas-equational | — |
| eq4315 | definition | out-of-fragment | magmas-equational | Equation4315 |
| eq4512 | definition | out-of-fragment | magmas-equational | Equation4512 |
| eq4513 | definition | out-of-fragment | magmas-equational | Equation4513 |
| eq4522 | definition | out-of-fragment | magmas-equational | Equation4522 |
| eq4564 | definition | out-of-fragment | magmas-equational | Equation4564 |
| eq4579 | definition | out-of-fragment | magmas-equational | Equation4579 |
| eq4582 | definition | out-of-fragment | magmas-equational | Equation4582 |
| eq5093 | definition | out-of-fragment | magmas-equational | Equation5093 |
| eq26302 | definition | out-of-fragment | magmas-equational | — |
| eq28770 | definition | out-of-fragment | magmas-equational | Equation28770 |
| eq345169 | definition | out-of-fragment | magmas-equational | — |
| eq374794 | definition | out-of-fragment | magmas-equational | Equation374794 |
| 1485-dual | lemma | out-of-fragment | magmas-equational | WeakCentralGroupoid.dual_eqn |
| graph-dual | lemma | no-signal | — | WeakCentralGroupoid.Path.def' |
| claim-4 | lemma | out-of-fragment | graphs-combinatorics | WeakCentralGroupoid.isGood_five |
| rev-claim | lemma | out-of-fragment | algebra-structures; graphs-combinatorics | RelaxedWeakCentralGroupoid.strictify |
| greedy-prop | proposition | out-of-fragment | graphs-combinatorics | RelaxedVeryWeakCentralGroupoid.Greedy.exists_extension |
| 1485-refutes | theorem | out-of-fragment | magmas-equational | Refutation_1485.not_3457, Refutation_1485.not_3511, Refutation_1485.not_2087_2124 |
