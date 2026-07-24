# C3 cycle 16 — the corpus reaches 09_Sets and measures it out of fragment

**Axis:** corpus. **Shipped: 2 sources (120–121). Refusals: 6 subjects / 10
ledger rows. Parks: 0.** Corpus **111 → 113**; governed exogenous coverage
**104 → 106**; ready **9 → 1**. Full suite **1234 passed, 35 skipped**.

## The headline: the set block is almost entirely out of fragment

This is the cycle where the intake window reached `09_Sets`, and the answer is
blunt. Of the seven set subjects selected, **one** shipped — and it shipped
only because its set structure *vanishes*. The other six refused, on ten rows,
against vocabulary the fragment simply does not have: propositional negation,
the biconditional, an existential inside a comprehension body, and — twice —
the membership atom over a set object.

That is the product of this cycle. A refusal-heavy cycle is a real cycle whose
output is demand data, and this one names the `09_Sets` demand precisely.

## The batch — sources 120–121

| src | subject | what it adds |
|---|---|---|
| 120 | no **integers** `a,b`, `b ≠ 0`, `a² = 2b²` | the Int sibling of cycle 15's 119 |
| 121 | `1 ∈ {n : ℤ ∣ n ≤ 3}` | the set block's degenerate case |

### 120 is the carrier sibling, with cycle 15's caveat re-measured

The book states the irrationality of √2 over **both** Nat (theorem-002, shipped
last cycle as 119) and Int (theorem-003, here). The corpus now carries both,
read the same way: `¬∃` as the equivalent `∀¬`, side condition as hypothesis,
equation negated with the builtin `!=` atom.

The honesty caveat from cycle 15 **applies here too and was re-measured**:
this green is **coverage, not a refutation-backed verdict**. The nearest false
variant (`a² ≠ 4b²`, refuted at `a=2, b=1`) is not caught, because the instance
box does not reach `a=2` and the nonlinear conclusion leaves the SMT arm at
`nonvacuity: sat`. Shipped as honest coverage, said plainly rather than
implied by a green.

### 121 is the degenerate case, and is not evidence of set coverage

`1 ∈ {n : ℤ ∣ n ≤ 3}` **is** `1 ≤ 3`. Membership in a comprehension unfolds
definitionally to its own body at the element, with nothing left unexpressed
and no corpus definition to relocate onto — contrast `defined-predicate`
(cycle 12), where unfolding *moves* the demand rather than discharging it. The
unfolding is an **equivalence**, by exactly the standard that let cycle 12
flatten an exists-in-hypothesis and ship source 112.

So it ships. What it is **not**:

- it is a **ground atom** — no binder, no objects (the source-85 taxicab
  precedent for ground readings);
- it carries **no set structure whatever**, because this subject's
  comprehension body is decidable arithmetic at a literal element;
- it is therefore **not** evidence that the fragment covers sets. Every other
  set subject in the window refused.

Recording that boundary is the point. A reader scanning coverage counts would
otherwise see "09_Sets: 1 covered" and conclude the block had begun to fall.

## Six refusals, ten rows

| subject | gate verdict | signal |
|---|---|---|
| `09_Sets#definition-003` (intersection) | `unknown atom/connective 'iff'` | `definition-biconditional` |
| ↳ probed past `iff` | `unknown atom/connective 'mem'` | **`set-membership`** (new) |
| `09_Sets#problem-002` (`10 ∉ {n ∣ n odd}`) | `unknown atom/connective 'not'` | `not-connective` |
| `09_Sets#problem-005` (set equality) | `unknown atom/connective 'iff'` | `iff-connective` |
| ↳ probed past `iff` | flattened `∃k` **refuted** at `{k:0, x:0}` | `exists-only-shape` |
| `09_Sets#problem-014` (complement) | `unknown atom/connective 'iff'` | `iff-connective` |
| ↳ probed past `iff` | `unknown atom/connective 'not'` | `not-connective` |
| `09_Sets#problem-015` (empty intersection) | `unknown atom/connective 'not'` | `not-connective` |
| `09_Sets#problem-017` (powerset) | `unknown atom/connective 'not'` | `not-connective` |
| ↳ probed past `not` | `unknown atom/connective 'mem'` | **`set-membership`** |

**Four of the six earned a second row**, each from a probe that genuinely
reached past the first blocker. Two did not: problem-002's probe past `not`
reaches only the positive atom (refuted at instances — a truth fact, not a
missing kind), and problem-015's probe past `not` reaches a conjunction that
is entirely in fragment. No third row anywhere.

Note the `exists-only-shape` row is earned by a **refutation**, not by an
unknown-word message: flattening the comprehension's `∃k` into a top-level
`∀k` passes the gate and is then refuted at a witness — which is exactly what
demonstrates the flattening is *not* an equivalence here, unlike cycle 12's
supported case.

## The new signal, and the boundary recorded with it

`set-membership`: **the subject needs the `∈` atom over a set OBJECT, and the
fragment has no set objects.** P2 bought `setbuild` only as `card`'s argument —
a bounded, filtered literal interval — so a set can be **counted** but never
inhabited, named, or compared.

Kept apart from the connective signals because it names a **different
purchase**: `iff` and `not` are propositional primitives; this one needs a set
carrier and its membership atom.

And the boundary is recorded **with** the signal, because this cycle measured
both sides of it: source 121 shows that membership which *unfolds* is not this
signal. The signal is for set objects that **survive** unfolding.

## A second consecutive operator-word admission — read narrowly

`op_a59eb3ce175d` — the irrationality template `v0² != 2·v1²` (arity 2) —
crossed the bar, following cycle 15's `op_e17bf0d665cf`. It prices honestly:
`delta = -9.0` (4012 → 4003), saving 42.0 bits against 33.0 model bits, 2 uses,
48 SMT confirmations across Nat/Int at bound 4.

It should be read **narrowly**, and this receipt says so rather than
celebrating a second admission. Its two witnesses are sources **119 and 120** —
the Nat and Int forms of the *same book theorem*. So the template abstracts a
**carrier pair**, not a family observed across independent subjects. The bar it
cleared is the committed two-witness bar, untouched here; whether that bar
should distinguish "two carriers of one statement" from "two statements" is a
question for the maintainer and the growth protocol, not something a driver
cycle decides. Recorded as a measurement, flagged, and left alone.

Admitted words **7 → 8** (plus the grandfathered `multiple_of`). `ANTI_LIST`,
`kernel/certs.py`, `TRUST.md` and the escape-gate blocklist untouched.

## Re-baseline and state

`registration.json` carries a cycle-16 lineage entry: **113** sources, waves
**0–14** (a new wave 14), **109 readings / 106 certified**, stream **3011** over
alphabet 67, governed DL **6531** vs ungoverned **6941** (naive 8119),
census-of-record governed 13 @ **5878**, ungoverned 12 @ 5705, refined-greedy
5885. Final-wave gaps: hindsight **−410**, prequential **−290**. Cluster key
**`all_pass = True`**, `b_evenodd_survives = True`.

Proposals **50 → 51**. Ordinary corpus-growth pins moved: `test_c2_report`,
`test_entropy_refs`, `test_operator_prompt_seam`. The cycle-15 re-anchored
`test_entropy_stack_fig` fixture (7200.5) still sits inside the current
order-0 / naive bracket (6696.006 / 8119.0) and needed no further change —
which is what a correctly re-anchored fixture should do.

## Carried-over demand

**Ready 1** — the intake window is nearly exhausted. Twenty-eight blocked
groups now, including the new `refused:set-membership`. The remaining ready
entry is a single `10_Relations` subject.

This is worth flagging plainly for whoever reads next: **the corpus axis is
running out of ready material at the current fragment**. The `09_Sets` block
that would have carried the next several cycles is blocked behind
propositional negation, the biconditional, and a set carrier — three named
demands, each of which is a **purchase-axis** call, not a corpus-axis one. The
corpus loop will keep measuring what remains, but the flywheel's next turn
looks like it belongs to the purchase driver.

No trust-root edits; **P5 not executed**. Lean-free cycle; statement-cert
deferred in-container and recorded as deferred, never as a pass.
