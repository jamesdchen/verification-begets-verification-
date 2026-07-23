# P1 purchase receipt — bounded big-operators (PLAN_FRAGMENT §2/§4)

**The purchase.** `bigsum`/`bigprod` — the one structural (binding) AST node
class — landed through the full admission bill:

- validator + scope (`generators/math_reading.py`: `_check_bigop`, scoped
  `-`-carrier walk; symbolic bound and nesting are first-class
  FragmentMisses `bigop:symbolic-bound` / `bigop:nested`);
- eval semantics (`generators/math_eval.py`: exact exhaustive fold, index at
  carrier Nat);
- SMT mirror (`generators/math_smt.py`: unrolling with index substitution --
  the D10 `^` discipline -- plus honest QF_NIA classification for
  object-dependent `bigprod`);
- Lean rendering (`generators/math_compile.py`: `Finset.sum/prod` over
  `Finset.Icc lo hi`, prefix form, escape-gate clean);
- differential + symbolic batteries (`tests/test_bigop_battery.py`:
  dual-solver ground-equation agreement over planted closed forms on both
  carriers; free-param symbolic distinctness; the planted LOSSY unroll is
  refused -- the divergence tooth);
- growth-protocol registry row (`bigop-node-class` in
  `buildloop/growth_protocol.py`, completeness canary green);
- prompt grammar (`_PRED_AST_NOTE` + regenerated golden);
- FgReflect slice extension (`sumTm`/`prodTm` folds with preservation and
  substitution theorems -- the literal-bound unroll, so the substitution
  lemma stays unconditional; decidability inherited; Lean-lane checked).

**The §2 re-census delta: ZERO, recorded.**  Portfolio verdicts are
byte-identical before and after the purchase (2 attempt-candidates,
sequences-sums 109).  This is expected and honest: the census is lexical and
cannot see bound literalness, and the portfolio's real `\sum`/`\prod` nodes
are SYMBOLIC-bound (`\sum_{n\le X}`, `\sum_{i=1}^{n}`) -- exactly the
`bigop:symbolic-bound` demand class the gate now names at refusal time.  Per
§2 this no-delta is **evidence to buy differently**: the next iteration-class
purchase should target symbolic bounds (a genuinely harder certifying story:
no SMT unroll, a true binding constructor in the reflect slice), not more
literal-bound machinery.  What the purchase DOES buy now: P2 rides this
binding machinery, and every literal-bound fold (concrete sums/products in
census candidates and hand corpora) is expressible, decidable, and
kernel-checkable end to end.
