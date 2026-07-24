# P2 purchase receipt — bounded Finset carrier + cardinality (PLAN_FRAGMENT §2/§4)

**The purchase.** `setbuild`/`card` — the bounded Finset carrier and its
cardinality — landed through the full admission bill, riding P1's binding
machinery.  A `setbuild` is a bounded, filtered literal interval
`{ i ∈ Icc lo hi | filter }` (the second structural extension, a SET node, not
an operator word); `card` is the term operator that counts it back into the
arithmetic fragment as a Nat value.  The admissibility argument is P1's exactly:
NON-NEGATIVE LITERAL bounds make the set finite and exactly enumerable.

- validator + scope (`generators/math_reading.py`: `_check_setbuild`,
  `_check_card`, `_SETOPS`; the index Nat-carrier, collision-free, scoped into
  the filter pred; `setbuild` refused anywhere but as `card`'s argument -- the
  sort discipline, exactly as `{"var"}` may appear only as a big-operator's
  first arg.  Symbolic bound → `set:symbolic-bound`, any binder inside a
  filter / a set inside a binder body → `set:nested`, both first-class
  FragmentMisses);
- eval semantics (`generators/math_eval.py`: exact exhaustive COUNT over the
  literal index range, `eval_pred` deciding the filter at each index);
- SMT mirror (`generators/math_smt.py`: `card` unrolls to a sum of
  `(ite filter 1 0)` indicators -- the D10 `^`/bigop discipline again -- with
  the index numeral substituted through `env`; honest QF_NIA classification
  only when the FILTER is nonlinear, e.g. a mod/dvd by an object);
- Lean rendering (`generators/math_compile.py`:
  `Finset.card (Finset.filter (fun i => filter) (Finset.Icc lo hi))`, prefix
  form, escape-gate clean, the index carrier following the ambient just as the
  big-operator rendering rides);
- differential + symbolic batteries (`tests/test_finset_battery.py`:
  dual-solver ground-equation agreement over planted cards on both carriers
  including object-dependent and empty sets; free-param symbolic distinctness
  against independently-derived clamped-count closed forms; the planted
  FILTER-DROPPING lowering refused -- the divergence tooth);
- growth-protocol registry row (`finset-card-node-class` in
  `buildloop/growth_protocol.py`, completeness canary green; `_check_setbuild`
  / `_check_card` signature-pinned);
- prompt grammar (`_PRED_AST_NOTE` + regenerated golden);
- FgReflect slice extension (`cardTm`/`countTrue` with preservation
  `evalTm_cardTm` and substitution `substTm_cardTm` theorems -- the indicator
  unroll, shaped like `sumTm` so it adds NO binding constructor to `Tm`, the
  substitution lemma stays unconditional, decidability inherited; Lean-lane
  checked).  An object-dependent filter is the named reflect skip
  `card:object-filter` (it needs a term-level conditional -- a genuine
  branching constructor in `Tm` -- which is a SEPARATE future purchase, not a
  widening of this one).

**The §2 re-census delta: ZERO, recorded.**  Portfolio verdicts are
byte-identical before and after the purchase (`results/census_portfolio.json`
unchanged: 108 attempt-candidates, `sets-cardinality` miss class 102).  This is
expected and honest, and it is the SAME lesson P1 recorded for `sequences-sums`:
the census is lexical and cannot see bound literalness, while the portfolio's
real `card`/`|·|`/`#`/`Finset` nodes are SYMBOLIC-bound (`|{k ≤ n : P k}|`,
`Finset.range n`) — the demand class the next iteration-class purchase must
target with a true binding constructor (a term-level `ite` in the reflect
slice, an SMT story without unrolling).  Per §2 this no-delta is **evidence to
buy differently**, not hidden.  What the purchase DOES buy now: every
literal-bounded finite set and its cardinality (concrete counts in census
candidates and hand corpora) is expressible, decidable, and kernel-checkable
end to end, and P2's `Finset.filter`/`Finset.Icc` machinery is exactly the
binding surface a symbolic-bound cardinality purchase will extend.
