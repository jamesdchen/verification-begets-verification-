# C3 cycle 14 — the induction block ships after all: gcd at symbolic arguments

**Axis:** corpus. **Shipped: 2 sources (113–114). Refusals: 6 subjects / 10
ledger rows. Parks: 0.** Corpus **104 → 106**; governed exogenous coverage
**97 → 99**; ready **25 → 17**. Full suite **1234 passed, 35 skipped**.

## The headline is that cycle 13's honest expectation was wrong

Cycle 13 measured `06_Induction`'s first eight subjects, refused every one, and
wrote down the expectation that *"the rest of `06_Induction` is likely to refuse
on the same two signals."* It also said what to do about it: if the block
wedges the corpus loop, the answer lives on the purchase axis.

Measurement disconfirmed that. Two of this cycle's eight shipped, and **nothing
was purchased to ship them.** That is worth stating plainly, because the
expectation was reasonable and still wrong: a block's first eight subjects do
not predict its next eight, and the only way to find out is to measure each one.

## The batch — sources 113–114 (math2001 ch.6)

The corpus's **first sources from the induction chapter**, and the first to use
the `gcd` operator word at **symbolic** arguments.

| src | subject | what it adds |
|---|---|---|
| 113 | `gcd(a,b)` is nonnegative | first symbolic-argument `gcd`; `nonnegative` as the builtin `0 <= t` atom |
| 114 | `gcd(a,b)` is a factor of **both** `a` and `b` | the corpus's first `dvd` atom at a **compound** first argument, conjoined |

**Why these were available without a purchase.** `gcd` is an
*already-admitted* `MATH_OPERATORS` word (arity 2, role term) carrying
`enum_only: True` — it has **no sound SMT rendering**, so a reading that uses
it is carried by the **enumeration arm's instance replay** rather than by the
dual-solver mirror. The word, the Int carrier and the `dvd` atom were all
already in the fragment. Cycle 13 could not have predicted this from its own
eight subjects, because none of them touched `gcd`.

**114 is not weakened.** "is a factor of both `a` and `b`" is the **conjunction**
of two `dvd` atoms in the divisor-first orientation (the source-100/101
reading), not either half alone.

### The greens are not rubber stamps

Both readings were box-verified TRUE before being written, and — because
`enum_only` routes these past the SMT mirror — a deliberately **FALSE** variant
of each was also handed to the gate to confirm it still has teeth:

- `1 <= gcd(a,b)` (false at `a = b = 0`, where `gcd(0,0) = 0`) is **refused** at
  stage `instances`, with the gate naming the witness `{'a': 0, 'b': 0}`.

Both real readings pass `math-reading-gate` (groundedness + trichotomy),
`nonvacuity` (z3 sat, cvc5 sat, enum-nonvacuous), `compile` (escape-gate), and
`instances` (smallest-instances, 5 checked). The kernel statement-cert is
**deferred** in-container (Lean absent) and recorded as deferred, never as a
pass.

## Six refusals, ten rows — measured one at a time

Every row is the gate's own words.

| src | subject | gate verdict | signal |
|---|---|---|---|
| — | `(n+1)! ≥ 2^n` | `^ requires a non-negative LITERAL exponent` | `symbolic-exponent` |
| — | (same, probed past `^`) | `unknown term operator 'factorial'` | `function-symbol` |
| — | `a_n = 2^n+(-1)^n` | `unknown term operator 'a'` | `function-symbol` |
| — | (same, probed past `a`) | `^ requires a non-negative LITERAL exponent` | `symbolic-exponent` |
| — | `a_m ≡ 1 or 5 mod 6` | `unknown term operator 'a'` | `function-symbol` |
| — | `d_n ≥ 4^n` | `^ requires a non-negative LITERAL exponent` | `symbolic-exponent` |
| — | (same, probed past `^`) | `unknown term operator 'd'` | `function-symbol` |
| — | `F_n ≤ 2^n` | `unknown term operator 'F'` | `function-symbol` |
| — | (same, probed past `F`) | `^ requires a non-negative LITERAL exponent` | `symbolic-exponent` |
| — | `The recursive definition gcd is well-founded` | `unknown atom/connective 'well_founded'` | **`metatheoretic-subject`** (new) |

**Four subjects earned a second row**, each by a **separate probe** that
replaces the first blocker with in-fragment vocabulary so the gate can reach
the second. This is the cycle-13 discipline for source 119, applied
consistently: the gate stops at the first miss, so a second signal is only
earned when a probe actually reaches it. No third row was written for any
subject.

The refused subjects' laid-down source files were **removed** (a refusal is
demand data, never a corpus source), and the two survivors were **renumbered
113/114** so the corpus numbering stays tight rather than leaving a six-wide
hole.

## The new signal, and why it is not `defined-predicate`

`metatheoretic-subject` names one thing: **the source's subject is a property
OF A DEFINITION, not a proposition about carrier values.**

The gate response for `06_Induction#proposition-001` looks identical in shape
to cycle 12's `defined-predicate` measurement (`unknown atom/connective '…'`),
and filing it there would have been the cheap move. It is wrong, for a reason
that matters to what the ledger is *for*:

- `defined-predicate` names a subject that **uses** a predicate the corpus
  defines elsewhere; unfolding the definition **relocates** its demand onto
  ordinary vocabulary (cycle 12: onto `prime`, which the census already prices).
- Here there is nothing to unfold. `well-founded` is **not defined anywhere in
  the corpus**, and its argument is the recursive definition
  `06_Induction#definition-001` — not any integer.

So `metatheoretic-subject` names a demand that **no operator-word or carrier
purchase can ever meet**, which is exactly why it must not sit in a group that
names purchases which can. Recorded narrowly on the strength of **one**
measurement; if a later cycle finds internal structure, that is an append, not
a rename.

## Re-baseline and state

`registration.json` carries a cycle-14 lineage entry: **106** sources, waves
**0–13**, **102 readings / 99 certified**, stream 2843 over alphabet 67,
governed DL **6166** vs ungoverned **6550** (naive 7666), census-of-record
governed 12 @ **5529**, ungoverned 10 @ 5406. Final-wave gaps: hindsight
**−384**, prequential **−264**. Cluster key **`all_pass = True`** on the
re-baselined bars, including **`b_evenodd_survives = True`** — the arity-1
even/odd macro `m_f3a9880f19ae` is undisplaced again (`op_slot_arities=[1]`,
5 uses, same covers).

Mining staged three more proposals (**43 → 46**); **no new operator word
crossed the admission bar** — honest no-delta on the admission axis. No macro,
carrier, or trust root grows.

### Micro-pins that moved with the corpus

`test_c2_report`, `test_entropy_refs` (order-0 DL, LZ77 phrases, context
stats), `test_operator_prompt_seam` (proposal count), plus
`results/hammer_readout.json` regenerated from its committed inputs.

**One tooth was rewritten rather than re-pinned.**
`test_dl_trajectories_fig::test_shifted_csv_values_move_the_gap_annotations`
hardcoded the final wave as `"12"`. That is not a moving *pin* — it is a
fixture that selects **which rows to mutate**, so once the corpus grew to wave
13 the test would have mutated a **non-final** wave, leaving the real
annotations in place and **passing for the wrong reason**. It now derives the
final wave from the rows. This is the cycle-11 pattern (re-anchor a fixture and
flag it as one) applied to a case where the stale literal was silently
*weakening* a tooth rather than breaking it.

## Carried-over demand

**Ready 17**: the rest of `06_Induction` (7 — theorems 001/002/006/007/008/009/
010), then 07_Number_Theory 2, 09_Sets 7, 10_Relations 1. The window did **not**
wedge — the six refusals left `ready` for their `refused:` groups (26 blocked
groups now, including the new `refused:metatheoretic-subject`). The cap was
**not** widened; 17 ready entries remain unconsumed.

Worth flagging for the next cycle, without prejudging it: the remaining
induction head includes the `mod`/`div` block (theorems 006–009), and
`06_Induction#theorem-009` — "there exists an integer `r` with `0 ≤ r < b` and
`a ≡ r mod b`" — has the shape of a **witness-term** discharge at `r := mod(a,b)`,
the sanctioned 87/107 form. That is a *hypothesis about what to measure*, not a
prediction; this cycle is the standing reminder that the block's first eight
subjects did not predict its next eight.

## Honesty notes

- **Zero purchases.** Nothing was bought, widened, or bent to ship these two.
- The cap was `--take 8`, taken in listed order; **not widened**.
- No trust-root edits (`kernel/certs.py`, `TRUST.md`, escape-gate blocklist,
  `ANTI_LIST` untouched); **P5 not executed, not touched.**
- Lean-free cycle (no `[lean-fast]`); the kernel statement-cert is deferred
  in-container and recorded as deferred.
- The park ledger stays **empty**; nothing parked, nothing lifted.
