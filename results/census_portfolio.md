# Corpus portfolio census

corpora: 5  ·  nodes: 748  ·  verdicts: attempt-candidate=2, no-signal=156, out-of-fragment=590

**rollup of lexical censuses, deterministic, LLM-free, Lean-free; REPORTS signals -- never a fidelity verdict. attempt_candidates is the C2 mining queue, not a claim any node certifies.**

## Portfolio miss histogram (the price list)

- magmas-equational: 156
- probability-entropy: 116
- rational-arithmetic: 115
- sequences-sums: 109
- algebra-structures: 97
- sets-cardinality: 90
- real-analysis: 84
- polynomials-fields: 60
- primality: 57
- maps-functions: 42
- graphs-combinatorics: 41
- geometry-topology: 33

## Per corpus

| corpus | nodes | attempt-candidates | out-of-fragment | no-signal | top miss |
|---|---|---|---|---|---|
| equational_theories | 241 | 1 | 174 | 66 | magmas-equational |
| flt_regular | 45 | 0 | 45 | 0 | polynomials-fields |
| formal_book | 192 | 1 | 152 | 39 | rational-arithmetic |
| pfr | 218 | 0 | 169 | 49 | probability-entropy |
| unit_fractions | 52 | 0 | 50 | 2 | sets-cardinality |

## C2 mining queue (attempt-candidate labels)

- **equational_theories** (1): edge-disjoint
- **formal_book** (1): fermats_little
