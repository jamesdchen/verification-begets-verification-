# C3 cycle 12 — two refused shapes re-measured, and one genuinely refused (106–112)

**Axis:** corpus. **Shipped: 7 sources (106–112). Refusals: 1 (one row, one new
signal). Parks: 0.** Corpus **97 → 104**; coverage **90 → 97**; ready **41 → 33**.
Full suite **1234 passed, 35 skipped**.

Chained off the merge-event trigger; freshness guard passed with no open PRs.

## The batch

| src | subject | what it adds |
|---|---|---|
| 106 | `a≡4, b≡3 mod 5 ⟹ ab+b³+3 ≡ 2 mod 5` | first source with **two** congruence hypotheses |
| 107 | `∃a. 6a ≡ 4 mod 11` | an existential discharged in the **witness-term** form, `a := 8` |
| 108 | `x³ ≡ x mod 3` | Fermat's little theorem at p = 3 |
| 109 | `n²−10n+24=0 ⟹ n even` | **the last subject the evenodd park was holding** |
| 110 | `n² ≢ 2 mod 3` | a negated **congruence** via the frozen disequality |
| 111 | every integer is even or odd | the corpus's first parity **disjunction** |
| 112 | between consecutive multiples ⟹ not a multiple | exists-in-hypothesis **+** negated divisibility at a symbolic divisor |

All seven certify in **both** bench arms (all in wave 12 — the cycle-11 ordering
fix holding). Every reading was box-verified before it was written.

**Vocabulary frozen:** builtin term ops, the `and`/`or`/`implies` connectives,
the admitted words `even`/`odd`/`dvd`, and the `mod` term word. The even/odd
macro `m_f3a9880f19ae` is undisplaced again (`b_evenodd_survives = True`).
Mining staged five more proposals (38 → 43); **no new operator word crossed the
admission bar** — honest no-delta.

**109 closes the park's story.** ch4 problem-016 was parked by cycle 09 under
the then-open evenodd-coverage-decision, and released by the maintainer's merge
of #50. It enters here as ordinary material — the last held subject.

## Two previously-refused shapes, re-measured rather than assumed

This is the substance of the cycle. Both shapes already have refusal signals in
the ledger, so the cheap move was available twice and taken neither time.

### Negation (110, 112) — the frozen-atom move, and its limit

110 negates a congruence, 112 negates a divisibility. Both are stated with the
**frozen disequality atom** rather than the `not` connective the fragment lacks
— the source-90 move, extended by cycle 11's source 102.

112 is the interesting one, because cycle 11 shipped `12 mod 5 != 0` and
explicitly **declined to generalise it to symbolic divisors**. 112's conclusion
is `a mod b != 0` at a *symbolic* `b`. It is faithful here for a reason the
source itself supplies: `b = 0` makes the hypothesis `0 < a < 0`
unsatisfiable, so the implication is vacuously true at `b = 0` under **both**
the source's reading and this one. They agree on every model. That is a
per-subject argument, **not** the general extension cycle 11 refused to make.

### Exists-in-hypothesis (112) — not `hypothesis-quantifier`

112's hypothesis carries its own `there exists an integer q`. Cycle 09 refused
exactly that shape (`refused:hypothesis-quantifier`, ch4 problem-002) because
flattening the binder to the top level stated a **different and false** theorem
— and recorded a refuting witness (`n=0, m=0`).

Here it does not. `(∃q. P(q)) → Q` is logically `∀q. (P(q) → Q)` whenever `Q`
does not mention `q`, and this conclusion speaks only of `a` and `b`. The
flattening is an **equivalence**, so the reading is faithful and the signal does
not apply.

**The distinguishing property is the conclusion's dependence on the binder, not
the presence of the words "there exists."** The signal's docstring now records
that boundary, so a future cycle reads the distinction instead of re-deriving
it — or worse, refusing on pattern match.

## The refusal — 05_Logic#problem-005, a new signal

`Prove that there exists a natural number k, such that k is superpowered and
k+1 is not.`

**Measured, in the gate's own words**, not assumed:

- using the defined name → `unknown atom/connective 'superpowered'`
- **unfolding** `05_Logic#definition-001` (*k is superpowered if for every
  natural n, k^{k^n}+1 is prime*) does not rescue it, it **relocates** the
  demand → `unknown atom/connective 'prime'`

Recorded under a newly appended signal, **`defined-predicate`**: the source
states its subject through a predicate name the corpus defines *elsewhere*, and
the fragment has no definitional-extension mechanism. It is kept distinct from
`definition-biconditional`, which is reserved for the **definition itself**;
this names a subject that merely **uses** one — the same split that keeps
`iff-connective` apart from `definition-biconditional`. Unfolding lands the
demand on `prime`, which the census already names as the **`primality`** miss
signal (69 nodes), so the two axes agree on what would unblock it.

**What was deliberately *not* recorded.** The subject's symbolic exponent
`k^{k^n}` is plainly visible in the definition, and `symbolic-exponent` is an
existing signal — but the gate never reached it, failing on `prime` first. No
`symbolic-exponent` row was written. Rows record measurements, not expectations.
Likewise no `not-connective` or `exists-only-shape` row: those blockers are
untestable while the predicate itself is unstatable.

Its laid-down source file was **removed** — a refused subject is demand data,
never a corpus source.

## Re-baseline and state

`registration.json` carries a cycle-12 lineage entry: **104** sources, waves
0–12, **100 readings / 97 certified**, stream 2799 over alphabet 67, governed DL
**6091** vs ungoverned **6473** (naive 7547), census-of-record governed 12 @
**5452**. Cluster key: every bar **PASS** except `a_reproduces_census_of_record`,
the ordinary re-baseline point.

Micro-pins that moved with the corpus: `test_entropy_refs`, `test_c2_report`,
`test_operator_prompt_seam` (38 → 43 staged proposals), `test_tower_census`
(top raw MM adjacency 17 → 18 — re-pinned **and** re-commented, since the raw
count is a moving corpus measurement while the tooth's real content is the
collapse to realizable 2), plus `results/hammer_readout.json` regenerated from
its committed inputs.

## Carried-over demand

Ready **33**: **06_Induction 23** — now overwhelmingly the largest block and the
next real frontier — 09_Sets 7, 07_Number_Theory 2, 10_Relations 1. The ch3
Parity-and-Divisibility block and the ch4 residue are **exhausted**; the ready
head is `06_Induction#problem-001`. Induction is a genuinely different shape
from anything measured so far, and the next cycle is where that gets tested.

## Honesty notes

- **One refusal is a measurement, not a quota.** Seven of eight shipped because
  seven of eight had faithful in-fragment readings; the eighth was measured
  twice and refused on what the gate actually said.
- **Two refusal signals were declined**, each with a stated reason — that is the
  cycle's main product, more than the seven sources.
- **No trust-root edits**: `kernel/certs.py`, `TRUST.md`, the escape-gate
  blocklist and `ANTI_LIST` untouched. **P5 not executed, not touched.**
- Lean-free cycle (no `[lean-fast]` tag); the kernel statement-cert is deferred
  in-container and recorded as deferred, never as a pass.
- The park ledger stays **empty**; nothing parked, nothing lifted.
