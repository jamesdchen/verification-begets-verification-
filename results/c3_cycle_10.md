# C3 cycle 10 — the parity block, released by decision (PLAN_FRAGMENT §3.1)

**Axis:** corpus (Lean-free). **Batch:** sources **91–98** — math2001 chapter-3
"Parity and Divisibility" problems **001–008**. This is the cycle the decision
lane was built to produce: the maintainer merged
`C3 decision: evenodd-coverage-decision` (#50), and under the decision-lane
design **merge is the sign-off** — the subjects return to `ready` and the next
cycle ships them through the normal flywheel. This is that cycle.

## Three cycles of holding, and what the measurement says

| cycle | what it did with the ch3 parity block |
|---|---|
| 06 | **parked** it in prose, pending an explicit even/odd coverage decision |
| 07 | **measured** it — all 19 certify; the park was a governance hold, never a fidelity verdict |
| 08 | **ledgered** the hold (`results/frontier_parks.jsonl`) so the corpus loop could proceed past it |
| #50 | the maintainer **merged the decision**; the park ledger emptied and 19 subjects returned to `ready` |
| **10** | **shipped the first eight**, and measured the objection that motivated the park |

**The measurement the decision was waiting for:** the arity-1 even/odd macro
`m_f3a9880f19ae` **survives the very block that motivated the park** —
cluster-key `b_evenodd_survives = True`, `op_slot_arities [1]` intact, covering
`04_even_plus_even` / `05_odd_plus_odd` unchanged at 5 uses. The mechanical
worry behind three cycles of holding does not hold on this block. That is worth
stating precisely, and just as precisely bounding: **eight of nineteen** are in,
so this is evidence about the head of the block, not a verdict on all of it.

## The batch

All eight are `odd`/`even` claims over the Int carrier — the first material in
the corpus whose demand lands squarely in the op-slot the park held closed.

| src | subject | what it adds |
|---|---|---|
| 91 | `7` is odd | a **ground** parity atom — no binder at all |
| 92 | `-3` is odd | the same at a **negative** literal; the Int carrier does real work (over Nat the subject would not exist) |
| 93 | `n` odd ⟹ `3n+2` odd | first parity-**preserving** affine implication |
| 94 | `n` odd ⟹ `7n-4` odd | sibling over Int **subtraction** (the D8 carrier rule) |
| 95 | `x,y` odd ⟹ `x+y+1` odd | first **two-object** parity hypothesis |
| 96 | `x,y` odd ⟹ `xy+2y` odd | conclusion **nonlinear** in the objects — a QF_NIA obligation |
| 97 | `m` odd ⟹ `3m-5` even | first parity-**flipping** claim (odd → even) |
| 98 | `n` even ⟹ `n²+2n-5` odd | the flip the other way, over a quadratic at literal exponent 2 |

Every reading was box-verified by `run.formalize.certify_statement` **before**
it was written into `wp_c9_readings.py`. Vocabulary is otherwise frozen: builtin
term ops plus the two **already-admitted** words `odd` and `even`. **No operator
word, macro, carrier, or trust root grows** — `admitted.json` is byte-identical
at 7 words. All eight certify in **both** bench arms via the inline-author
checkpoint resume (joining waves 10 and 11); governed exogenous coverage
**75 → 83**; governed reported DL **5340** ≤ ungoverned **5726**. The kernel
statement-cert stays **deferred** (no Lean toolchain in a remote container —
recorded as deferred, never as a pass).

## No refusals, no parks — and why that is not a softer standard

Every selected subject certified, so this cycle records **zero** refusal rows
and **zero** park rows, and the park ledger stands **empty** after the decision
landed. That is not the intake window being widened or a reading being bent: it
is what a *pre-measured* block looks like when the hold on it lifts. Cycle 07
had already measured these subjects; cycle 10 re-measured each one
independently before authoring rather than trusting that record.

The mining pass re-priced the staged pool on the grown corpus (83 certified
readings, 35 proposals — 12 non-alias, staged pool 34 → 36). **No new operator
word crossed the admission bar**: honest no-delta on the admission axis,
recorded.

## Re-baseline (the ONE file)

`specs/mathsources/registration.json` carries a cycle-10 lineage entry and the
new era numbers: **90** sources, waves **0–11**, governed exogenous
**86 readings / 83 certified**, stream **2491** over alphabet **64**, counting
DLs **naive 6688 / governed 5340 / ungoverned 5726**, census-of-record
**governed 12 macros @ 4723** and **ungoverned 10 @ 4585**, cluster-key
re-registration `baseline 5340 / census-of-record 4723 / accept_max_dl 5311 /
max_macros 18`. Cluster key re-measures **`all_pass = True`** on the new bars.

Harness-local micro-pins that moved with the corpus (they live next to their
harness by design): `test_entropy_refs.py` (order-0 **5517.19**, LZ77 phrases
**593**, order-1/2 context stats), `test_c2_report.py` (the C2 headline five),
`test_dl_trajectories_fig.py` (final wave 10 → 11),
`test_operator_prompt_seam.py` (staged proposals 34 → 36).

**One tooth was rewritten rather than re-pinned.** The pilot commutativity-sort
rung's canonicalization saving was pinned at exactly `-4.0` by cycle 09; this
cycle it **doubled to `-8.0`**. Pinning that figure exactly makes the tooth
re-break on every growth cycle without ever testing more, because it is a
moving corpus measurement and not a constant. The tooth now asserts what
actually decides the refusal — the rung's own model cost (2748 bits) dominating
the saving, net decisively positive — and records the saving as a direction
(`profit < 0`, `|profit| < rung_model_bits`). The rung is **still refused, on
the same ground**.

## A discrepancy worth recording

PR #51's receipt states it **parked** ch4 problem-016 under
`evenodd-coverage-decision`. That row is **not** in the committed ledger: #50
(which emptied the ledger) and #51 (which appended to it) landed in that order,
and the append did not survive. The committed state is nonetheless the
**correct** post-decision state — the decision released the parity class, so
problem-016 belonging in `ready` is right — but the receipt and the ledger
disagree about how it got there, and the ledger is the artifact that governs.
Recorded here rather than silently corrected, since a park row is evidence.

## Honesty ledger

* The census reported **signals**; certification issued every **verdict**, and
  each subject was re-measured this cycle rather than inherited from cycle 07.
* `b_evenodd_survives = True` is a measurement on **eight of nineteen**
  subjects — evidence about the head of the block, not a verdict on all of it.
* No trust root touched: `kernel/certs.py`, `TRUST.md`, the escape-gate
  blocklist and `buildloop/growth_protocol.py::ANTI_LIST` are unchanged.
  **P5 untouched** — no promotion executed, no entrance predicate claimed.
* Lean-free cycle (no `[lean-fast]`); statement-cert deferred and recorded so.
* Full suite: **1234 passed, 35 skipped**.

## Carried-over demand

**49 ready entries remain** (58 → 49). The head is the rest of the released
parity block — ch3 problems 009 onward — followed by the ch4 residue (including
**problem-016** and **problem-030**, which cycle 09 never reached) and the
`06_Induction` block, where the corpus axis will start asking for an induction
primitive. The cap was never widened.

## Provenance note

This cycle was originally authored as a second, concurrent "cycle 09": two
driver sessions passed their freshness guards minutes apart and consumed the
same ch4 window, and the sibling session's PR (#51) landed first. That prior
work is superseded, not merged — its five ch4 sources are #51's, under its
readings. The race window it exposed has since been closed by the claim-by-PR
pattern (#54). What this cycle ships is derived fresh from the post-#51,
post-#50 tree.
