# C3 cycle 15 — the division-algorithm block, and the first operator word to admit since cycle 12

**Axis:** corpus. **Shipped: 5 sources (115–119). Refusals: 3 subjects / 3
ledger rows. Parks: 0.** Corpus **106 → 111**; governed exogenous coverage
**99 → 104**; ready **17 → 9**. Full suite **1234 passed, 35 skipped**.

## The headline: corpus growth admitted a new operator word

Cycles 13 and 14 both recorded an honest **no-delta** on the admission axis —
proposals staged, nothing crossed the bar. This cycle the bar was crossed:

**`op_e17bf0d665cf` — the remainder bound `mod(v0, v1) < v1`** (arity 2, Int).

It crossed the two-witness bar **only because of this cycle's sources**. Its
three witnesses are `117_06_induction_theorem_008`,
`118_06_induction_theorem_009` — both new here — and the pre-existing
`19_mod_less_m`, which had been sitting as a lone witness with nothing to pair
with. This is the C2-closure pattern repeating on the `mod` family: the corpus
grew, the miner found a template that now had enough witnesses, and the priced
R2 batteries admitted it.

It is a genuine admission, not a bookkeeping one: **48 SMT confirmations**
across Nat and Int at bound 4 with cvc5 present, and it **pays** —
`delta = -2.0` (dl 3964 → 3962), saving 21.0 bits against 19.0 model bits, 3
uses. Admitted words **6 → 7** (plus the grandfathered `multiple_of`).
`ANTI_LIST`, `kernel/certs.py`, `TRUST.md` and the escape-gate blocklist are
untouched — an operator **word** admitting through the priced batteries is the
flywheel working as designed, not a trust-root change.

## The batch — sources 115–119

| src | subject | what it adds |
|---|---|---|
| 115 | every natural number is even or odd | the corpus's first parity **disjunction** |
| 116 | `0 <= mod(n,d)` for positive `d` | first **symbolic-argument** `mod` |
| 117 | `mod(n,d) < d` for positive `d` | the other half of the remainder bound |
| 118 | ∃ `r`, `0 <= r < b` and `a ≡ r mod b` | witness-term discharge at `r := mod(a,b)` |
| 119 | no naturals `a,b`, `b ≠ 0`, `a² = 2b²` | first **07_Number_Theory** source |

Nothing was purchased. `even`, `odd`, `mod`, the `or` connective and `^` at a
literal exponent were all already in the fragment; `mod` had simply never been
used at a symbolic argument before.

### 115 retires a cycle-01 avoidance by measurement

Cycle 01 **measured** that parity candidates displaced the arity-1 even/odd
macro `m_f3a9880f19ae` and declined to ship them, staying in the `dvd` family
to protect the coverage invariant. That was the right call **on that corpus**.
Measured again here on the grown corpus, the macro **survives**:
`b_evenodd_survives = True`, `m_f3a9880f19ae` undisplaced. The old avoidance
was era-specific, and it is now retired by a measurement rather than carried
forward as an assumption.

### 118 is the witness-term pattern, not a weakening

The source claims an existence. The reading is the sanctioned ∀-with-witness
form (sources 84/85/87/107; `tests/test_t6b_predecessor_int.py`), with
`r := mod(a,b)` substituted at every occurrence and **all three** of the
source's conditions conjoined — `0 <= r`, `r < b`, and `a ≡ r mod b` — none
dropped. Cycle 14 flagged this subject as *"the shape of a witness-term
discharge"*; that hypothesis is now measured true.

### 119 is honest coverage, and its green is weaker than its siblings'

This must be said plainly rather than buried. **A deliberately FALSE variant of
119 also certifies.** `a² ≠ 4b²` (refuted by `a=2, b=1`) passes the same gate
the true reading passes, because:

- the five smallest hypothesis-satisfying instances are
  `{a:0,b:1}, {0,2}, {1,1}, {0,3}, {1,2}` — the box **never reaches `a=2`**; and
- the conclusion is nonlinear, so the SMT arm contributes `nonvacuity: sat`
  and no refutation.

So 119's certificate is **coverage, not a refutation-backed verdict**, and its
layer list (`instances: pass, n_checked 5`) looks identical to a source where
the box does have teeth. The reading itself is faithful and true — `¬∃` read as
the equivalent `∀¬`, the side condition carried as a hypothesis and the equation
negated with the builtin `!=` atom — and it is shipped as such. What is recorded
here is the **gate's** limit at nonlinear Diophantine subjects, which is demand
data for a wider instance box, not a reason to pretend the green is stronger
than it is.

### The teeth did hold for the other three

Each was checked against a deliberately false variant, and each refused:

| variant | gate verdict |
|---|---|
| 116 with its positivity hypothesis **dropped** | refused at `instances`, witness `{d: 0, n: -1}` |
| 118 with its positivity hypothesis **dropped** | refused at `instances`, witness `{a: 0, b: 0}` |
| 115 with `either…or` read as **`and`** | refused at `instances`, witness `{n: 0}` |

## Three refusals, three rows — and no second rows this time

| subject | gate verdict | signal |
|---|---|---|
| `a ≡ b mod d → aⁿ ≡ bⁿ mod d` | `^ requires a non-negative LITERAL exponent` | `symbolic-exponent` |
| `mod(n,d) + d·div(n,d) = n` | `unknown term operator 'div'` | **`div-operator`** (new) |
| `L(a,b)a + R(a,b)b = gcd(a,b)` | `unknown term operator 'l'` | `function-symbol` |

Every one was **also probed past its first blocker**, per the cycle-13/14
discipline. None of the probes reached a second missing kind:

- 116 past `^` (literal exponent 2 substituted): the congruence rendering
  itself is in fragment — the probe **certifies**.
- 117 past `div` (quotient replaced by a plain object variable): **certifies**.
- 121 past `L`/`R` (coefficients replaced by object variables): passes the gate
  and fails at `instances` — which confirms the missing kind is the function
  symbols and nothing behind them.

So each subject earned **exactly one row**, unlike cycle 14 where four subjects
earned two. The discipline is symmetric: it writes a second row when a probe
finds one, and refuses to when it does not.

## The new signal, and why it is not `function-symbol`

`div-operator`: **the source needs integer division (the quotient); the fragment
has the remainder but not the quotient.**

Filing it under `function-symbol` would have been the cheap move — the gate
response has the same shape (`unknown term operator …`). It is wrong for the
same reason cycle 14 kept `metatheoretic-subject` separate: the groups exist to
**name the purchase that unblocks them**.

- `function-symbol` rows need an arbitrary **named** function the corpus has no
  word for — `factorial`, the sequences `a_n`/`d_n`/`F_n`, the Bezout
  coefficients `L`/`R` — each needing its own definition mechanism.
- `div` is **one standard arithmetic operator word**, exactly the shape `mod`
  itself had when it was the named refusal `mod-operator` and a single purchase
  retired it.

Named narrowly on one measurement, following that sibling precedent.

## Re-baseline and state

`registration.json` carries a cycle-15 lineage entry: **111** sources, waves
**0–13** (the five new readings joined the existing wave 13, 99 → 104),
**107 readings / 104 certified**, stream **2975** over alphabet 67, governed DL
**6459** vs ungoverned **6868** (naive 8025), census-of-record governed 12 @
**5847**, ungoverned 11 @ 5675, refined-greedy 5854. Final-wave gaps: hindsight
**−409**, prequential **−289**. Cluster key **`all_pass = True`** on the
re-baselined bars, `b_evenodd_survives = True`.

Mining staged four more proposals (**46 → 50**), one of which admitted (above).

### Pins moved, and one fixture re-anchored

Ordinary corpus-growth value pins that simply moved: `test_c2_report`
(five headline numbers), `test_entropy_refs` (order-0 estimate, LZ77 tokens,
order-1/order-2 context columns), `test_operator_prompt_seam` (the admitted
list, `n_proposed` 46 → 50, `n_admitted` 6 → 7).

One was **not** a value pin.
`test_entropy_stack_fig::test_shifted_kt_values_change_adaptive_labels_and_c2_gap`
feeds the figure a fabricated `adaptive_DL` chosen to sit **between** the real
order-0 estimate and the real naive DL, then asserts the resulting bar
ordering. Corpus growth moved order-0 to 6618.462, so the old fixture value
6400.5 fell **below** it and the ordering the test sets up stopped being the
one it checks. Re-anchored to 7200.5 inside the current bracket — which is
exactly what the test's own comment instructs ("it has to be re-anchored
whenever corpus growth moves the real bracket it is chosen inside").

## Carried-over demand

**Ready 9**, in frontier order: 07_Number_Theory 1, 09_Sets 7, 10_Relations 1.
The 06_Induction block is now **exhausted** — every subject in it has either
shipped or carries a measured refusal row. The window did not wedge; the three
refusals joined their `refused:` groups (**27 blocked groups**, including the
new `refused:div-operator`). The cap was not widened.

Flagged for a later cycle without prejudging it: `div-operator` names a demand
that **one** purchase meets, and it is the closest sibling of a word the
fragment already carries — but that is a purchase-axis call for the purchase
driver, not this loop's.

No trust-root edits (`kernel/certs.py`, `TRUST.md`, escape-gate blocklist,
`ANTI_LIST` untouched); **P5 not executed**. Lean-free cycle; statement-cert
deferred in-container and recorded as deferred, never as a pass.
