# Proposal admissions (WP-T4-WIRE)

The staged `proposed/` operator rows run through the R2 battery + pricing gate (`admit_operator`), priced against the real certified governed corpus from the committed checkpoint. Passers are persisted via the sole-admitter `save_admitted` path (append-only); refusals stay in `proposed/`.

- pricing corpus: 52 readings (digest `3de879c2e165f3c9`)
- proposed rows: 27
- admitted: 5

| word | arity | verdict | stage | arithmetic |
|------|------:|---------|-------|------------|
| `multiple_of` | 2 | refuse | trivial-alias | model_bits=12.0, saving=0.0 over 47 uses in 21 witnesses (dl 1926.0 -> 1938.0, delta=12.0) |
| `op_04436b0a49d9` | 1 | refuse | trivial-alias | model_bits=8.0, saving=0.0 over 7 uses in 3 witnesses (dl 1926.0 -> 1934.0, delta=8.0) |
| `op_050a84ca1e83` | 2 | refuse | trivial-alias | model_bits=12.0, saving=0.0 over 47 uses in 21 witnesses (dl 1926.0 -> 1938.0, delta=12.0) |
| `op_0cb6456a29eb` | 2 | refuse | pricing | model_bits=16.0, saving=8.0 over 2 uses in 2 witnesses (dl 1926.0 -> 1934.0, delta=8.0) |
| `op_0f7b72077fa3` | 3 | refuse | well-formedness | model_bits=20.0, saving=16.0 over 4 uses in 2 witnesses (dl 1926.0 -> 1930.0, delta=4.0) |
| `op_0fb148eb491c` | 2 | refuse | trivial-alias | model_bits=12.0, saving=0.0 over 10 uses in 10 witnesses (dl 1926.0 -> 1938.0, delta=12.0) |
| `op_12e68ccd223a` | 1 | refuse | trivial-alias | model_bits=8.0, saving=0.0 over 12 uses in 6 witnesses (dl 1926.0 -> 1934.0, delta=8.0) |
| `op_34e1b706c47c` | 1 | refuse | well-formedness | model_bits=11.0, saving=12.0 over 4 uses in 3 witnesses (dl 1926.0 -> 1925.0, delta=-1.0) |
| `op_3c0de4c8920b` | 1 | ADMIT | admitted | model_bits=11.0, saving=15.0 over 5 uses in 5 witnesses (dl 1926.0 -> 1922.0, delta=-4.0) |
| `op_580885f772c7` | 3 | ADMIT | admitted | model_bits=27.0, saving=220.0 over 20 uses in 9 witnesses (dl 1926.0 -> 1733.0, delta=-193.0) |
| `op_5f64949e9cda` | 3 | refuse | pricing | model_bits=20.0, saving=16.0 over 4 uses in 4 witnesses (dl 1926.0 -> 1930.0, delta=4.0) |
| `op_600a6c7b92c4` | 2 | ADMIT | admitted | model_bits=26.0, saving=28.0 over 2 uses in 2 witnesses (dl 1926.0 -> 1924.0, delta=-2.0) |
| `op_736608f44f38` | 2 | refuse | pricing | model_bits=16.0, saving=12.0 over 3 uses in 3 witnesses (dl 1926.0 -> 1930.0, delta=4.0) |
| `op_a1af410b393e` | 2 | refuse | well-formedness | model_bits=12.0, saving=0.0 over 23 uses in 16 witnesses (dl 1926.0 -> 1938.0, delta=12.0) |
| `op_a2d50e96a175` | 3 | refuse | well-formedness | model_bits=20.0, saving=16.0 over 4 uses in 2 witnesses (dl 1926.0 -> 1930.0, delta=4.0) |
| `op_a7da9abc6817` | 3 | refuse | pricing | model_bits=20.0, saving=12.0 over 3 uses in 3 witnesses (dl 1926.0 -> 1934.0, delta=8.0) |
| `op_a98168fda376` | 2 | refuse | trivial-alias | model_bits=12.0, saving=0.0 over 32 uses in 19 witnesses (dl 1926.0 -> 1938.0, delta=12.0) |
| `op_b041a5af8887` | 2 | refuse | well-formedness | model_bits=12.0, saving=0.0 over 7 uses in 5 witnesses (dl 1926.0 -> 1938.0, delta=12.0) |
| `op_b5f98a12fb89` | 1 | refuse | nonvacuity | model_bits=11.0, saving=6.0 over 2 uses in 2 witnesses (dl 1926.0 -> 1931.0, delta=5.0) |
| `op_c7e5b035d6b3` | 1 | ADMIT | admitted | model_bits=11.0, saving=21.0 over 7 uses in 5 witnesses (dl 1926.0 -> 1916.0, delta=-10.0) |
| `op_cf1624a1ec0e` | 2 | refuse | well-formedness | model_bits=12.0, saving=0.0 over 10 uses in 9 witnesses (dl 1926.0 -> 1938.0, delta=12.0) |
| `op_d1e41a716e7a` | 2 | refuse | trivial-alias | model_bits=12.0, saving=0.0 over 20 uses in 17 witnesses (dl 1926.0 -> 1938.0, delta=12.0) |
| `op_dd25497d9c4f` | 1 | refuse | well-formedness | model_bits=11.0, saving=9.0 over 3 uses in 3 witnesses (dl 1926.0 -> 1928.0, delta=2.0) |
| `op_eba00915e85b` | 2 | refuse | well-formedness | model_bits=12.0, saving=0.0 over 42 uses in 11 witnesses (dl 1926.0 -> 1938.0, delta=12.0) |
| `op_ec9ef222c885` | 2 | refuse | well-formedness | model_bits=12.0, saving=0.0 over 18 uses in 15 witnesses (dl 1926.0 -> 1938.0, delta=12.0) |
| `op_f39960716d99` | 1 | ADMIT | admitted | model_bits=11.0, saving=48.0 over 16 uses in 16 witnesses (dl 1926.0 -> 1889.0, delta=-37.0) |
| `op_f9b6fe265b07` | 4 | refuse | well-formedness | model_bits=28.0, saving=16.0 over 2 uses in 2 witnesses (dl 1926.0 -> 1938.0, delta=12.0) |

## Refusal reasons

- `multiple_of` (trivial-alias): trivial alias: 'multiple_of' expands to a single kernel operator 'dvd' over distinct param refs -- a pure rename that adds no structure and can never lower the corpus DL; refused
- `op_04436b0a49d9` (trivial-alias): trivial alias: 'op_04436b0a49d9' expands to a single kernel operator 'odd' over distinct param refs -- a pure rename that adds no structure and can never lower the corpus DL; refused
- `op_050a84ca1e83` (trivial-alias): trivial alias: 'op_050a84ca1e83' expands to a single kernel operator 'dvd' over distinct param refs -- a pure rename that adds no structure and can never lower the corpus DL; refused
- `op_0cb6456a29eb` (pricing): no strict corpus-DL drop: the rewrite saving does not exceed the definition's model bits (model_bits=16.0, saving=8.0 over 2 uses in 2 witness readings (dl_before=1926.0 -> dl_after=1934.0)); saving must exceed model_bits for the word to pay for itself
- `op_0f7b72077fa3` (well-formedness): definition is not a valid pred over Nat: unknown atom/connective 'mod'
- `op_0fb148eb491c` (trivial-alias): trivial alias: 'op_0fb148eb491c' expands to a single kernel operator '<=' over distinct param refs -- a pure rename that adds no structure and can never lower the corpus DL; refused
- `op_12e68ccd223a` (trivial-alias): trivial alias: 'op_12e68ccd223a' expands to a single kernel operator 'even' over distinct param refs -- a pure rename that adds no structure and can never lower the corpus DL; refused
- `op_34e1b706c47c` (well-formedness): definition is not a valid pred over Nat: unknown atom/connective '^'
- `op_5f64949e9cda` (pricing): no strict corpus-DL drop: the rewrite saving does not exceed the definition's model bits (model_bits=20.0, saving=16.0 over 4 uses in 4 witness readings (dl_before=1926.0 -> dl_after=1930.0)); saving must exceed model_bits for the word to pay for itself
- `op_736608f44f38` (pricing): no strict corpus-DL drop: the rewrite saving does not exceed the definition's model bits (model_bits=16.0, saving=12.0 over 3 uses in 3 witness readings (dl_before=1926.0 -> dl_after=1930.0)); saving must exceed model_bits for the word to pay for itself
- `op_a1af410b393e` (well-formedness): definition is not a valid pred over Nat: unknown atom/connective '*'
- `op_a2d50e96a175` (well-formedness): definition is not a valid pred over Nat: unknown atom/connective 'mod'
- `op_a7da9abc6817` (pricing): no strict corpus-DL drop: the rewrite saving does not exceed the definition's model bits (model_bits=20.0, saving=12.0 over 3 uses in 3 witness readings (dl_before=1926.0 -> dl_after=1934.0)); saving must exceed model_bits for the word to pay for itself
- `op_a98168fda376` (trivial-alias): trivial alias: 'op_a98168fda376' expands to a single kernel operator '=' over distinct param refs -- a pure rename that adds no structure and can never lower the corpus DL; refused
- `op_b041a5af8887` (well-formedness): definition is not a valid pred over Nat: unknown atom/connective 'gcd'
- `op_b5f98a12fb89` (nonvacuity): vacuous vocabulary: the definition is a TAUTOLOGY on the battery domain (never refutable) -- refused
- `op_cf1624a1ec0e` (well-formedness): definition is not a valid pred over Nat: unknown atom/connective '-'
- `op_d1e41a716e7a` (trivial-alias): trivial alias: 'op_d1e41a716e7a' expands to a single kernel operator '<' over distinct param refs -- a pure rename that adds no structure and can never lower the corpus DL; refused
- `op_dd25497d9c4f` (well-formedness): definition is not a valid pred over Nat: unknown atom/connective '-'
- `op_eba00915e85b` (well-formedness): definition is not a valid pred over Nat: unknown atom/connective 'mod'
- `op_ec9ef222c885` (well-formedness): definition is not a valid pred over Nat: unknown atom/connective '+'
- `op_f9b6fe265b07` (well-formedness): definition is not a valid pred over Nat: unknown atom/connective '+'

## E1 note (prompt-side pricing)

The admitted rows carry a `pricing` cert block and therefore surface in the math authoring prompt's ADMITTED OPERATORS section (`buildloop/math_prompt.render_operator_table`), which adds prompt bytes -- the priced §11.4 mechanism (i). The grandfathered `multiple_of` row (no pricing block, alias-refused under the current gate) is NOT surfaced, so the committed-registry prompt stays byte-identical to the pre-seam prompt. The frozen bench artifacts are untouched (read-only); the committed sidecar's `prompt_scaffold_sha256` intentionally records the pre-seam scaffold that produced that frozen run.
