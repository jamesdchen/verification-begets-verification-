# FRAGMENT_GROWTH.md — the W5 checklist, math instance (F4.3)

When a source sentence does not transcribe into the F1 fragment, that is not a
failure to hide — it is **demand data** (F4). The `cgb.py fragment report`
prices each candidate `MATH_LF_KINDS` extension: demand unlocked per kernel
surface added (F4.2). Pricing is mechanical; **admission is not**.

This file is the checklist a **person** works through to admit one new
`MATH_LF_KINDS` entry (the verbatim analog of ROADMAP briefing item 11 / the
W5 checklist). Nothing on this list happens autonomously. The system may
mine, price, and propose; a human is the admitting authority, and stays so
**permanently** (out-of-scope item 2). No box here is self-checkable by the
loop.

## When to open this checklist

A `fragment-miss` kind (F-I event `{source_id, span, missing_kind_guess}`) has
accumulated enough demand in the `fragment report` that a person judges the new
LF-kind worth its surface cost. The three planted non-transcribables in this
corpus each name their intended miss and will show up here first:

| source | miss_kind_guess | why it misses today |
|---|---|---|
| `38_infinitude_primes.txt` | `operator:prime` | `Prime` is absent from `MATH_OPERATORS`; also no "infinitely many" quantifier |
| `39_real_square_nonneg.txt` | `carrier:Real` | `Real` is outside the `Nat`/`Int` carrier whitelist |
| `40_least_element.txt` | `kind:set-object` | the fragment has no set / predicate objects |

## The checklist — every box is human-checked, dual-checked semantics or it does not land

- [ ] **(1) `MATH_LF_KINDS` entry — validator + prompt.**
      Add the kind to `MATH_LF_KINDS` and its fields to `_MLF_FIELDS` in
      `generators/math_reading.py`, in the single-source pattern so the
      import-time equality assert keeps prompt grammar and validator from
      drifting (F1.1). Force rule stated explicitly (which of
      demand / presupposition / choice the kind may carry). The Reading
      prompt's grammar block re-renders from `MATH_LF_KINDS` automatically
      (F1.3); confirm the rendered prompt and add a prompt test.

- [ ] **(2) Compile rule + provenance.**
      Add the deterministic, LLM-free lowering to Lean text in
      `generators/math_compile.py` (trusted by fiat, TRUST 1.2e). Canonical
      emission so `statement_hash` stays content-stable. Extend `provenance`
      so every new Lean subterm maps back to the statement ids that produced
      it — the *quoted span → force → LF → Lean term* chain, written beside
      the artifact.

- [ ] **(3) Entailed-instance derivation.**
      Provide the F2.2 meaning-level instance derivation for the new kind (the
      analog of entailed scenarios): a `LOWERINGS` rule so the pluggable
      channel-2 replay can check meaning-level instances of the new kind
      against the compiler output. Without an entailed-instance story the kind
      cannot be certified end-to-end.

- [ ] **(4) `math_smt` / decidable-enumeration coverage — or an honest named
      gap.**
      Add the SMT mirror rendering in `generators/math_smt.py`, OR route the
      kind to the decidable-enumeration channel, OR record an explicit,
      **named** gap with its honest tier note (the `exhausted`-is-honest rule,
      LINGUISTICS §7). A silent gap is not admissible; an owned one is.
      Guard against reintroducing a carrier divergence (e.g. bare `-`, `%`,
      or `^` conventions — ⚠D8/D9/D10) with a `mirror-divergence` check.

- [ ] **(5) >= 1 tooth.**
      At least one committed test that would fail if the new kind's semantics
      regressed — an LLM-free planted demo in the `demo_formalize_governor.py`
      / `test_rung.py` pattern. A lossy lowering must get **no certificate**
      (compile-hash divergence); a faithful one must certify per-emission.

## Non-negotiables

- **Dual-checked semantics or it does not land.** Two independent renderings of
  the new kind's meaning (compiler + SMT/decidable mirror) must agree on the
  planted instances before admission.
- **No autonomous growth — permanently.** The loop proposes; a person admits.
  This is out-of-scope item 2 and does not expire. There is no configuration,
  threshold, or budget that lets the system check its own boxes here. A dream
  may *propose* a new kind; only a human, working this list, admits it, and
  only an exogenous witness justifies the demand that opened it (S5.1 / F3.4).
