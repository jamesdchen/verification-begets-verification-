# C3 cycle 13 — the induction block, measured: eight subjects, eight refusals

**Axis:** corpus. **Shipped: 0 sources. Refusals: 8 subjects / 9 ledger rows.
Parks: 0.** Corpus unchanged at **104**; coverage unchanged at **97**; ready
**33 → 25**. Full suite **1234 passed, 35 skipped**.

A refusal-only cycle is a real cycle whose product is demand data (the cycle-05
lesson). This is that cycle, and it is the most informative one in a while:
`06_Induction` was the largest remaining block (23 subjects) and the ready
head, and its first eight subjects name **exactly two purchases** between them.

## What was measured

Every subject got a faithful reading constructed and handed to
`run.formalize.certify_statement`. Each row below is the gate's own words, not
a pattern match:

| src | subject | gate verdict | signal |
|---|---|---|---|
| 113 | `2^n ≥ n+1` | `^ requires a non-negative LITERAL exponent` | `symbolic-exponent` |
| 114 | `4^n ≡ 1 or 4 mod 15` | same | `symbolic-exponent` |
| 115 | `n ≥ 2 ⟹ 3^n ≥ 2^n+5` | same | `symbolic-exponent` |
| 116 | for sufficiently large `n`, `2^n ≥ n²` | same | `symbolic-exponent` |
| 117 | `b_n` is odd | `unknown term operator 'b'` | `function-symbol` |
| 118 | `x_n ≡ 1 mod 4` | `unknown term operator 'x'` | `function-symbol` |
| 119 | `x_n = 2^{n+2}+1` | `unknown term operator 'x'` | `function-symbol` + `symbolic-exponent` |
| 120 | every `d` with `1≤d≤n` divides `n!` | `unknown term operator 'factorial'` | `function-symbol` |

Nothing was bent to force a green, and nothing was silently dropped. The eight
laid-down source files were **removed** — a refused subject is demand data,
never a corpus source — and the intake tool's readings-module skeleton was
deleted rather than committed with an empty `READINGS` dict.

### 119 carries two rows, and why that is a measurement

The gate stopped at `x` and never reached the exponent, so on the cycle-12
discipline (*rows record measurements, not expectations*) a `symbolic-exponent`
row would be unearned. It was **earned by a separate probe**: replacing the
unknown sequence name with a builtin head lets the gate reach the closed form,
and it then refuses `2^{n+2}` in the same words as 113–116. That is a
measurement of this subject's own content, not an inference from its shape, so
both rows stand. No third row was written for any subject on the same grounds
that cycle 12 declined its extra rows.

## What the block actually demands

The two signals are not a grab-bag — they are two coherent purchases, and both
are already named elsewhere in the ledger:

**1. Symbolic exponents (113–116, 119).** `^` takes a literal exponent because
SMT-LIB has no exponentiation. This is the *same* demand P1's re-census already
recorded as `bigop:symbolic-bound` — the iteration class. Half the induction
head is blocked on it alone.

**2. Recurrence-defined functions (117–120).** Sharper than the
`function-symbol` name suggests, and worth stating precisely: these are not
free/uninterpreted symbols. `b_n`, `x_n` and `n!` are *defined*, each by a
recurrence — and for `b_n`/`x_n` **the defining recurrence is not even present
in the corpus**: the Sphinx intake captured the problem prose but not the
display blocks that define the sequences. So the subject as intaken is
strictly unstatable, twice over. Recorded under `function-symbol` because that
is what the gate said; the sharper reading is here in prose rather than in a
new signal, since no gate response distinguishes the two and inventing
vocabulary ahead of measurement is how ledgers rot.

**What was NOT measured, and is worth saying plainly:** the fragment has no
induction principle, and this chapter's *method* is induction. But that is not
what refused these eight — every one of them died on **vocabulary**, before any
proof method came into it. Whether the fragment can carry induction is a
question this cycle did not reach and does not answer. Stating the block's
demand as "induction" would be exactly the kind of tidy story the honesty rules
exist to prevent.

## No re-baseline

The corpus did not grow, so `registration.json` is **untouched** and carries no
cycle-13 lineage entry — there is no new number to register. The regen chain
moved exactly two files, `results/frontier.json` and
`results/frontier_refusals.jsonl`, with **zero drift** anywhere else: no DL
moved, no macro moved, no operator word moved, no micro-pin moved. That is the
correct signature of a refusal-only cycle, and it is worth having as a
reference: the suite passed with no test edits at all.

## Carried-over demand

Ready **25**, all still `06_Induction` at the head (`problem-010` onward),
then 09_Sets 7, 07_Number_Theory 2, 10_Relations 1. The intake window did
**not** wedge — the eight measured refusals left `ready` and joined
`refused:symbolic-exponent` / `refused:function-symbol`, so the next cycle sees
new material rather than re-selecting these (the cycle-05 lesson holding).

The honest expectation for the next cycle: the rest of `06_Induction` is likely
to refuse on the same two signals. If it does, that is a **stronger** demand
measurement, not a wasted cycle — but if it wedges the corpus loop on a block
that cannot ship at all, the purchase axis is where the answer lives, and the
two signals above are what it should be pointed at.

## Honesty notes

- **Zero shipped is a measurement, not a failure.** Eight subjects were
  selected in listed order, measured one at a time, and every one refused on
  what the gate actually said.
- **The cap was not widened.** `--take 8` was the window; 25 ready entries
  remain unconsumed and are recorded as carried-over demand.
- No trust-root edits (`kernel/certs.py`, `TRUST.md`, escape-gate blocklist,
  `ANTI_LIST` untouched); **P5 not executed, not touched.**
- Lean-free cycle (no `[lean-fast]`); the kernel statement-cert is deferred
  in-container and recorded as deferred, never as a pass.
- The park ledger stays **empty**; nothing parked, nothing lifted.
