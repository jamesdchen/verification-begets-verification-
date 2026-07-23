# Fragment mining triage — portfolio cycle 1 (PLAN_FRAGMENT §3 C2)

**Honesty header.** This is a judgment triage of the census's attempt-candidate
queue against the frozen F-G lexicon (`generators/math_reading.py`: carriers
Nat/Int; operator words dvd/even/odd/gcd/coprime/mod; builtins `+ * - % ^`
with `^` literal-exponent only; first-order quantifiers).  The census reports
lexical signals; the reasons below are human-class judgments recorded so the
flywheel can act on them — nothing here is a fidelity verdict, and nothing
here admits anything.

## What this cycle did

1. **C1 landed the portfolio** — 5 corpora, 748 nodes
   (pfr 218, unit_fractions 52, formal_book 192, flt_regular 45,
   equational_theories 241), intake + census committed
   (`results/census_portfolio.json`, per-corpus
   `results/blueprint_census_*.json`).
2. **First-wave census over the portfolio produced 61 attempt-candidates**
   (formal_book 37, equational_theories 20, flt_regular 3, unit_fractions 1).
   Triage found the queue dominated by classes the first-wave signals could
   not see: plane geometry, graph theory, magma/equational metatheory,
   polynomials and field theory, function objects, and fractions.
3. **The census grew a second wave of miss-signal categories**
   (geometry-topology, graphs-combinatorics, magmas-equational,
   polynomials-fields, maps-functions, rational-arithmetic — the last is the
   start of the §4 P3 signal split), plus term additions to real-analysis and
   sets-cardinality.  Re-census of the full portfolio: **61 → 2**
   attempt-candidates, no-signal 328 → 156.

## The surviving queue (2), triaged

### `fermats_little` — formal_book, theorem, Lean `book.quadratic_reciprocity.fermat_little`

> For \(a \not\equiv 0 \pmod{p}\), \(a^{p-1} \equiv 1 \pmod{p}\)

The genuinely near candidate.  The congruence itself is fragment-shaped —
`mod` is an operator word, so `a^(p-1) mod p = 1 mod p` is one `=` atom over
`mod` terms — but the exponent `p − 1` is **symbolic**, and F-G's `^` takes a
literal exponent only (the D10 unfolding rule).  Recorded miss:
`operator:pow-symbolic-exponent` — bounded iteration, i.e. exactly the
binding machinery §4 **P1** purchases (a symbolic-exponent power is a bounded
Π).  Secondary miss: the ambient hypothesis "p prime" lives in chapter
context, sharing `operator:prime` with sources 38/51.

**Not intaken as a source this cycle**: adding a 5th manifest-declared
non-transcribable touches the F5.1 corpus freeze
(`tests/test_mathsources_manifest.py` pins EXACTLY 4), which is bench-frozen
state, not this packet's to grow casually.  It is the named first intake for
the cycle after P1 lands (at which point it may transcribe rather than
refuse).

### `edge-disjoint` — equational_theories, corollary

> For any integer \(n\), \(L_y x = L_z x \implies L_y^{n} x = L_z^{n} x\)

A false candidate the lexical census cannot see: \(L_y\) is magma
left-multiplication, so the statement is carrier-magma, out-of-fragment.
Recorded census blind spot: **subscripted operator notation carries no
lexical signal**.  Not worth a signal term (the notation is corpus-specific);
recorded here so the blind spot is owned, not hidden.

## Verdict for the flywheel

- **Zero of 61 candidates transcribe into F-G today.**  The C2 done-predicate
  (first mined template sourced from a census attempt-candidate) stays
  **open** — honestly, not silently.
- The demand data from the corpus side now **agrees with the price list**:
  the one near-candidate is blocked on P1-class binding machinery, and
  sequences-sums prices at 109 portfolio-wide.  Both ends of the gap point at
  **P1 (bounded big-operators)** as the next purchase.
- Instrument note: the second-wave categories changed the committed
  histograms (that re-census is this cycle's delta, committed in the same
  session per §2).  Future purchase deltas are measured against THIS
  instrument; any further signal change must re-baseline in the same session.
