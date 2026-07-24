# C3 cycle 11 — the released block turns to divisibility (sources 99–105)

**Axis:** corpus. **Batch shipped: 7 sources (99–105), 8 ready entries retired.**
**Refusals: 0. Parks: 0.** Corpus **90 → 97**; governed exogenous coverage
**83 → 90**; ready **49 → 41**. Full suite **1234 passed, 35 skipped**.

## What this cycle is

The maintainer's merge of `C3 decision: evenodd-coverage-decision` (#50)
released the ch3 Parity-and-Divisibility block. Cycle 10 (#52) shipped its
head — the eight parity subjects, 91–98. This cycle takes the **rest of what
the decision released**, and it is where the block stops being about parity:
five of the seven sources are divisibility or congruence.

## The batch

| src | subject | what it adds |
|---|---|---|
| 99 | `n²+n+4` is even | an even conclusion with **no hypothesis** — the binder phrase is the whole antecedent |
| 100 | 88 divisible by 11 | the corpus's first **ground `dvd` atom** (divisor first: `dvd(11,88)`) |
| 101 | 6 divisible by −2 | the same atom at a **negative divisor** — why its source says *integer* where 100 says *natural number* |
| 102 | 12 **not** divisible by 5 | a negated divisibility, stated without a `not` connective — see below |
| 103 | `11 ≡ 3 mod 4` | a ground congruence as residue equality (the source-88 reading) |
| 104 | `−5 ≡ 1 mod 3` | the same at a **negative** residue; 103/104 pin congruence on both signs as 91/92 pinned parity |
| 105 | `a ≡ 2 mod 4 ⟹ ab²+a²b+3a ≡ 2b²+2²b+3·2 mod 4` | the first **hypothetical** and only **nonlinear** congruence |

Every reading was box-verified by `run.formalize.certify_statement` **before**
it was written, and all seven certify in **both** bench arms (99–104 in wave 11,
105 opening wave 12).

**Vocabulary is frozen.** Builtin term ops plus the already-admitted words
`even`/`odd`/`dvd` and the grammar's `mod` term word. `admitted.json`'s word
set is **unchanged at 7** — the only movement inside it is the ordinary
re-pricing of six entries against the grown corpus (`dl_before`/`dl_after` and
the corpus digest). Mining staged two more proposals (36 → 38); **no new
operator word crossed the admission bar** — honest no-delta, recorded.

The even/odd macro is again **undisplaced**: `m_f3a9880f19ae`,
`op_slot_arities=[1]`, `uses=5`, covering `04_even_plus_even` /
`05_odd_plus_odd` — identical to the cycle-07 and cycle-10 measurements.
Cluster-key `b_evenodd_survives = True`.

## Source 102 — a shipped source, deliberately not a refusal

`Show that 12 is not divisible by 5` is a **negated divisibility**, and the
fragment has no `not` connective. The refusal ledger already carries
`refused:not-connective`, so the lazy move was available and was **not** taken.

Instead, 102 is read the way source 90 read its negated existential: state the
proposition with a **frozen atom** rather than a missing connective. `5 does
not divide 12` is exactly `12 mod 5 ≠ 0`, built from the already-admitted `mod`
term word and the builtin disequality. For a nonzero modulus the two are the
same proposition — not a weakening, and no primitive smuggled in. It certifies
in both arms.

The honest boundary: this move works because the divisor is a **nonzero
literal**. A negated divisibility at a symbolic divisor is a different subject,
and when one appears it will be measured on its own terms, not waved through on
this precedent.

## Seven sources, eight ready entries

`03#problem-022`'s prose is **verbatim-identical** to `03#problem-021`'s, so
source 105 retired both ready entries. The intake preview offered them as two
selections; taking eight would have committed the same text twice under two
source numbers. The batch was cut to **seven** for that reason — the duplicate
is retired by the frontier, exactly as source 95 retired `04#problem-017` in
cycle 10.

## MEASURED INFRASTRUCTURE FINDING — the corpus crossed 100 sources

**Symptom.** The first bench run of this batch recorded **six of its seven new
sources in wave 1** — a batch intaken at corpus 97 filed among the earliest
material in the corpus.

**Cause.** `bench_formalize._corpus_sources` ordered its stream with a plain
**lexicographic** sort of source filenames. That carried the intended meaning
only while every source number was two digits. At three digits `100_…` sorts
between `10_…` and `11_…`, so the new sources were inserted near the **front**
of the stream, reshuffling the wave membership of sources committed cycles
earlier and breaking the append-only reading that makes `final_wave` mean *the
newest batch*. The boundary is permanent: every future cycle would scramble the
stream further.

**Fix.** `bench_formalize` now keys the corpus order on the integer prefix
(`_source_order_key`). This is a **provable no-op for every source committed to
date** — the pre-100 corpus is zero-padded to two digits, where lexicographic
and numeric order coincide, verified mechanically against `origin/main`'s 90
sources — and it puts this batch back at the end of the stream.

**What the fix did and did not move.** The headline DLs are **identical either
way** (governed 5666 / ungoverned 6049): the hindsight total is order-free.
What moved back is **wave membership** and the order-dependent **prequential**
column. The corrected run re-derived only the seven new checkpoint rows; the
188 committed rows were left byte-identical (verified: the checkpoint file
matched `origin/main` exactly before the re-run).

Scope was kept to the one site where order determines a number. `cgb.py`'s
ledger sync and `milestones.py` also sort this directory, but they ingest
per-source rows whose aggregate is order-independent, so they were left alone
rather than changed on speculation.

## Re-baseline and state

`registration.json` carries a cycle-11 lineage entry: **97** sources, waves
0–12, **93 readings / 90 certified**, stream 2618 over alphabet 66, governed DL
**5666** vs ungoverned **6049** (naive 7045), census-of-record governed 12 @
**5046**, refined-greedy 5053. Cluster key: `a_beats_baseline`,
`b_evenodd_survives`, `c_no_macro_explosion`, `d_service_byte_identical`,
`e_ungoverned_reported` all **PASS**; the lone FAIL is
`a_reproduces_census_of_record`, the ordinary re-baseline point every growth
cycle records.

Harness-local micro-pins that moved with the corpus: `test_entropy_refs`
(order-0 DL, LZ77 phrases, context stats), `test_c2_report` (five headline
numbers), `test_operator_prompt_seam` (36 → 38 staged proposals),
`test_dl_trajectories_fig` and `test_entropy_stack_fig` (final-wave index, and
a **fabricated fixture** re-anchored to the new order-0/naive bracket it is
chosen inside — flagged in the test as a fixture, not a measurement), plus
`results/hammer_readout.json` regenerated from its committed inputs.

## Carried-over demand

Ready **41**: ch3 Parity-and-Divisibility 3, ch4 Proofs-with-Structure-II 4
(including problem-016 and problem-030, which no cycle has reached yet),
**06_Induction 23** — now the largest single block and the next real frontier —
09_Sets 7, 05_Logic 1, 07_Number_Theory 2, 10_Relations 1. The ready head is
`03#problem-023`.

## Honesty notes

- **Zero refusals is a measurement, not a target.** Every selected subject
  certified. Source 102 was the one that could plausibly have been refused, and
  the receipt above states exactly why it was not.
- **This session's first cycle was superseded, not merged.** It ran the 91–98
  parity batch and had it fully built and green when PR #52 — a concurrent
  session that had re-derived the same batch — merged first. That work was
  **discarded, not rebased**: re-adding sources already at main is not a delta.
  This cycle was then derived fresh from the post-#52 tree.
- **No trust-root edits**: `kernel/certs.py`, `TRUST.md`, the escape-gate
  blocklist and `ANTI_LIST` are untouched. **P5 not executed, not touched.**
- Lean-free cycle (no `[lean-fast]` tag); the kernel statement-cert is deferred
  in-container and recorded as deferred, never as a pass.
- The park ledger stays **empty**; no park was recorded and none was lifted.
