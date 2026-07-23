# Blueprint fragment census

nodes: 52  ·  verdicts: attempt-candidate=1, no-signal=2, out-of-fragment=49

**lexical census, deterministic, LLM-free, Lean-free; REPORTS signals -- never a fidelity verdict.  An attempt-candidate still needs the full statement pipeline (metered) + the Lean RT lane.**

## Miss histogram (the vocabulary-growth price list)

- sets-cardinality: 37
- sequences-sums: 30
- real-analysis: 28
- primality: 10

## Nodes

| label | kind | verdict | miss signals | lean |
|---|---|---|---|---|
| lem:omegasum | lemma | out-of-fragment | real-analysis; sequences-sums | — |
| lem:omegasquaredsum | lemma | out-of-fragment | real-analysis; sequences-sums | — |
| lem:turan | lemma | out-of-fragment | real-analysis; sequences-sums | — |
| lem:chebyshev | lemma | out-of-fragment | real-analysis | — |
| lem:divisor_bound | lemma | out-of-fragment | real-analysis | — |
| lem:mertens1 | lemma | out-of-fragment | real-analysis; sequences-sums; primality | — |
| lem:mertensprimes | lemma | out-of-fragment | real-analysis; sequences-sums; primality | — |
| lem:mertens2 | lemma | out-of-fragment | real-analysis; sequences-sums | — |
| lem:sieve_eratosthenes | lemma | out-of-fragment | sequences-sums | — |
| def:rec_sum | definition | out-of-fragment | sets-cardinality; sequences-sums | — |
| def:local_part | definition | out-of-fragment | sets-cardinality; primality | — |
| def:rec_sum_local | definition | out-of-fragment | sets-cardinality; sequences-sums; primality | — |
| def:interval_rare_ppowers | definition | out-of-fragment | sets-cardinality | — |
| def:integer_count | definition | out-of-fragment | sets-cardinality | — |
| def:j | definition | no-signal | — | — |
| def:cos_prod | definition | out-of-fragment | sets-cardinality; sequences-sums | — |
| def:major_arc | definition | out-of-fragment | sets-cardinality | — |
| def:minor_arcs | definition | attempt-candidate | — | — |
| lem:orthogonality | lemma | out-of-fragment | sequences-sums | — |
| lem:lcm_desc | lemma | out-of-fragment | sets-cardinality; sequences-sums; primality | — |
| lem:smooth_lcm | lemma | out-of-fragment | sets-cardinality | — |
| lem:cos_bound | lemma | no-signal | — | — |
| lem:triv_q_bound | lemma | out-of-fragment | real-analysis; sets-cardinality | — |
| lem:orthog_rat | lemma | out-of-fragment | sets-cardinality; sequences-sums | — |
| lem:orthog_simp | lemma | out-of-fragment | sets-cardinality; sequences-sums | — |
| lem:orthog_simp2 | lemma | out-of-fragment | sets-cardinality; sequences-sums | — |
| lem:majorarcs_disjoint | lemma | out-of-fragment | sets-cardinality | — |
| lem:useful_rewrite | lemma | out-of-fragment | sets-cardinality; sequences-sums | — |
| lem:majorarcs | lemma | out-of-fragment | sets-cardinality; sequences-sums | — |
| lem:minor_lbound | lemma | out-of-fragment | sets-cardinality; sequences-sums | — |
| lem:cos_prod_bound | lemma | out-of-fragment | sets-cardinality; sequences-sums | — |
| lem:minor1_bound | lemma | out-of-fragment | real-analysis; sets-cardinality; sequences-sums | — |
| lem:minor2_ind_bound | lemma | out-of-fragment | real-analysis; sets-cardinality | — |
| lem:minor2_bound | lemma | out-of-fragment | real-analysis; sets-cardinality; sequences-sums | — |
| prop:fourier | proposition | out-of-fragment | real-analysis; sets-cardinality | — |
| th:density_theorem | theorem | out-of-fragment | sets-cardinality; sequences-sums | — |
| th:log_density_theorem | theorem | out-of-fragment | real-analysis; sets-cardinality; sequences-sums | — |
| cor:tech_cor | corollary | out-of-fragment | real-analysis; sets-cardinality; primality | — |
| lem:sieve1 | lemma | out-of-fragment | real-analysis; primality | — |
| lem:sieve2 | lemma | out-of-fragment | real-analysis; sets-cardinality; primality | — |
| lem:basic | lemma | out-of-fragment | real-analysis; sequences-sums; primality | — |
| lem:rtop | lemma | out-of-fragment | real-analysis; sets-cardinality; sequences-sums | — |
| lem:smoothsum | lemma | out-of-fragment | real-analysis; sets-cardinality; sequences-sums | — |
| lem:usingq | lemma | out-of-fragment | real-analysis; sets-cardinality; sequences-sums | — |
| lem:pisqa | lemma | out-of-fragment | real-analysis; sets-cardinality | — |
| lem:pisq | lemma | out-of-fragment | real-analysis; sets-cardinality | — |
| lem:find_multiples | lemma | out-of-fragment | real-analysis; sets-cardinality; sequences-sums | — |
| lem:good_d | lemma | out-of-fragment | sets-cardinality | — |
| prop:tech_iterative | proposition | out-of-fragment | real-analysis; sets-cardinality; sequences-sums | — |
| prop:tech_iterative2 | proposition | out-of-fragment | real-analysis; sets-cardinality; sequences-sums | — |
| lem:techmainprec | lemma | out-of-fragment | real-analysis; sets-cardinality | — |
| prop:techmain | proposition | out-of-fragment | real-analysis; sets-cardinality; primality | — |
