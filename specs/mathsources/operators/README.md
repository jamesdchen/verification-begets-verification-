# Autonomous operator-table growth (R2)

**Semantics in, never code in.** A new operator *word* is a DEFINITIONAL
EXTENSION over the frozen kernel fragment (the F-G pred/term AST in
`generators/math_reading.py`). A row is pure data:

```json
{"word": "multiple_of", "arity": 2, "params": ["a", "b"],
 "definition": {"op": "dvd", "args": [{"ref": "b"}, {"ref": "a"}]}}
```

`definition` is a **pred AST over the existing fragment**, referring to the
`params` by `{"ref": <param>}`. No new kernel operator, no engine change: the
word is EXPANDED at the reading layer (like the governor's reference-lowering)
before `math_compile` / `math_eval` / `math_smt` ever see a statement. All
three backends' semantics for the word therefore DERIVE from the one
definition, so the gate-correctness certificate is their differential
agreement.

## Files

- `admitted.json` — committed `{word: {row, cert}}`, loaded lazily. **Absent /
  empty ⇒ the expansion hook is a pure no-op** (byte-identical to a tree with
  no operator growth). Nothing autonomous ever writes this without a green
  cert.
- `proposed/*.json` — proposed-but-unadmitted rows (mirrors the dream-staging
  pattern). An LLM may PROPOSE rows as data; only `admit_operator`'s battery
  admits them.

## Admission (the gate-correctness certificate — LLM-free / Lean-free)

`generators/operator_growth.admit_operator(row)` runs a battery:

  (a) **well-formedness** — arity matches params; the definition parses as a
      valid pred in the existing fragment (through the real `_check_pred`
      machinery on a synthetic reading); every operator inside the definition
      is kernel or already-admitted (no forward refs, no self-reference /
      recursion).
  (b) **differential instance battery** — on generated instances over small
      ints (both Nat and Int carriers), the expanded form's z3 verdict, cvc5
      verdict (honest absence tolerated) and decidable-enumeration verdict all
      AGREE. Disagreement or all-unknown ⇒ refusal, never admission.
  (c) **compile round-trip** — a synthetic statement using the word compiles
      through `math_compile` via expansion and passes the `validate_lean`
      escape gate; two expansions are byte-identical.
  (d) **nonvacuity sanity** — the definition is satisfiable AND refutable on
      the battery domain. A tautology / contradiction is refused as vacuous
      vocabulary.

The certificate is an **L3 evidence JSON** (`id = sha256(canonical row +
battery digest)`) persisted next to the row in `admitted.json`. It is NOT a
kernel cert tier: `kernel/certs.py` and `CERTS_VERSION` are untouched.

## Tamper safety

Every per-use expansion recomputes the row hash and checks it against the
stored `cert.id`. A stale or tampered row (definition edited after admission)
fails the check and REFUSES to lower — it can never silently reach the engines.
