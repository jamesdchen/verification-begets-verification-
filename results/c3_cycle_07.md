# C3 cycle 07 — the parked parity block, MEASURED (PLAN_FRAGMENT §3.1)

**Axis:** corpus. **Batch shipped: NONE.** This cycle's product is **decision
data**: the leading 19-entry ch3 Parity-and-Divisibility **problem** block —
which cycle 06 parked in writing — was measured end to end, and the mechanical
objection recorded against it in cycle 01 **no longer holds at today's corpus
size**. The block is still **PARKED**: the hold is a maintainer decision, and an
unattended cycle does not overturn it. What changed is that the decision is now
**informed by numbers instead of by a stale measurement**.

Scheduled firing; freshness guard passed (no open `C3 cycle…` PR; the one open
PR, #41, is a `C3 purchase…` PR on the independent purchase loop). Lane clean:
`origin/main` at `f38ef82`, `regression` green, `lean-hammer` skipped (no lane
tag). Ready list non-empty (**73**), so the flywheel turned on the corpus axis.

## Why this cycle could not simply intake in listed order

The frontier's `ready` head is now **19 consecutive ch3 Parity-and-Divisibility
problems** (the whole chapter's problem cluster), and cycle 06 **parked** the
first of them:

> 91 ch3 problem-001 "Show that 7 is odd" certifies faithfully as the ground
> atom `odd(7)`. … Cycles 02–04 deliberately kept the arity-1 even/odd op-slot
> out of the main corpus; rather than open that door **unilaterally** in an
> unattended cycle, 91 is **parked in writing** pending an explicit even/odd
> coverage decision.

Cycle 06 could ship anyway because ch2 entries still sat ahead of the parity
block. **They are gone.** From this cycle on, the corpus loop's intake window
opens directly onto parked material.

This is the **cycle-05 re-wedge failure in a new guise**. The refusal ledger
(`tools/frontier_refusals.py`) demotes sources that **fail to certify**. These
certify. There is **no demotion mechanism for a parked-but-certifying source**,
so every future unattended cycle will re-preview the same 19 entries and be
unable to proceed in listed order. The loop is **wedged pending a decision**.

## What was measured (the honest part)

All eight leading entries were laid down in the working tree, authored, and
box-verified — then **reverted, not committed**.

### 1. Every one of the eight certifies — none is a refusal

`run.formalize.certify_statement` on each authored reading:

| # | source | prose | reading | verdict |
|---|---|---|---|---|
| 86 | ch3 problem-001 | `\(7\) is odd` | `odd(7)` | **certifies** |
| 87 | ch3 problem-002 | `\(-3\) is odd` | `odd(0-3)` | **certifies** |
| 88 | ch3 problem-003 | `n` odd → `3n+2` odd | `odd(n) → odd(3n+2)` | **certifies** |
| 89 | ch3 problem-004 | `n` odd → `7n-4` odd | `odd(n) → odd(7n-4)` | **certifies** |
| 90 | ch3 problem-005 | `x,y` odd → `x+y+1` odd | `odd(x)∧odd(y) → odd(x+y+1)` | **certifies** |
| 91 | ch3 problem-006 | `x,y` odd → `xy+2y` odd | `odd(x)∧odd(y) → odd(xy+2y)` | **certifies** |
| 92 | ch3 problem-007 | `m` odd → `3m-5` even | `odd(m) → even(3m-5)` | **certifies** |
| 93 | ch3 problem-008 | `n` even → `n²+2n-5` odd | `even(n) → odd(n²+2n-5)` | **certifies** |

Under the full two-arm bench (inline author, checkpoint resume) **all eight
certify in BOTH arms**; governed certified exogenous coverage **70 → 78**
(86/87/88 join wave 9, 89–93 open wave 10).

**They are therefore NOT refusals and were NOT recorded as such.** Writing them
into the refusal ledger would demote faithful readings on a false pretext — the
ledger records *measured* refusals, and there is nothing here to refuse.

Every reading uses only the even/odd **pred/1 op-slot already present in the
corpus** (sources 04–08) plus builtin term ops (`+ - * ^` at literal exponent 2).
**No operator word, macro, or trust root grows.**

### 2. The cycle-01 objection is void at today's corpus size

Cycle 01 recorded the reason the parity family was passed over:

> …the arity-1 parity candidates, whose batch was **measured to displace that
> coverage** and was NOT shipped.

That measurement was taken at **62 readings**. Re-measured now at **73 → 81**
(`tools/measure_cluster_key.py`, full block applied):

| verdict | committed (77 sources) | **with the parity block (85)** |
|---|---|---|
| `a_beats_baseline` | PASS | **PASS** |
| `b_evenodd_survives` | PASS | **PASS** |
| `c_no_macro_explosion` | PASS | **PASS** (11 macros, bar 15) |
| `d_service_byte_identical` | PASS | **PASS** |
| `e_ungoverned_reported` | PASS | **PASS** |
| `a_reproduces_census_of_record` | PASS | FAIL — *the ordinary re-baseline point* |

The even/odd macro is **byte-for-byte the same macro**, undisplaced:

    m_f3a9880f19ae  op_slot_arities=[1]  uses=5  covers=['04_even_plus_even', '05_odd_plus_odd']

— identical in both runs. The lone FAIL, `a_reproduces_census_of_record`, is the
re-pin that **every** growth cycle performs (cycle 06 recorded the same, "True
after the re-baseline"); it is not an objection to this batch.

Measured DL effect of the block: governed legacy replay **4540 → 4890**;
census-of-record (refined+GC) **3925 → 4275**; refined macro count **11 → 11**.

**Recompute beat recollection.** The mechanical risk the park was protecting
against is not present today.

## The decision this cycle escalates rather than takes

Two things are now separable, and only the second is still open:

* **Mechanical**: *does census-sourced parity displace the even/odd coverage
  invariant?* — **Measured: no.** Retired as an objection.
* **Governance**: *should census-sourced parity readings enter the main
  corpus at all?* — **Still open.** Cycles 02–04 held this deliberately; cycle
  06 parked it "pending an explicit even/odd coverage decision". No such
  decision has been made, so **the park stands** and nothing was shipped.

An unattended cycle that shipped here would be taking a maintainer's decision on
the strength of having found the mechanical coast clear. That is exactly the
unilateral move cycle 06 declined to make, and CLAUDE.md's honesty rule —
*parked items stay parked in writing* — is not conditioned on the mechanical
risk being real.

**What the maintainer needs to decide:** ship the ch3 parity problem block
(19 entries) into the main corpus, or record it as a standing exclusion. Either
answer un-wedges the loop; no answer leaves the corpus axis stalled at the head
of its own ready list. If the answer is *exclude*, the frontier needs a **park
ledger** — a demotion mechanism for certifying-but-held sources, the sibling of
`frontier_refusals.jsonl` — or the wedge simply recurs.

## Carried-over demand

The full ready list (**73**, unchanged — no demotions this cycle) with the ch3
problem block (19) at its head; behind it 04_Proofs_with_Structure_II (19),
06_Induction (23), 09_Sets (7), 05_Logic (2), 07_Number_Theory (2),
10_Relations (1). **Zero ready entries were consumed.**

## Honesty notes

- **Nothing was shipped and nothing was reverted silently**: the eight sources,
  the manifest entries, the authored readings module, and every regenerated
  artifact were laid down **only to measure**, then reverted. The committed tree
  is unchanged apart from this report. `registration.json` is **not**
  re-baselined — there was no corpus growth to re-baseline.
- **No refusals recorded.** All eight certify; the ledger is untouched.
- **No trust-root edits**: `kernel/certs.py`, `TRUST.md`, the escape-gate
  blocklist and the `.lean-pins` are untouched. No Lean-touching files changed —
  a Lean-free cycle (no `[lean-fast]` tag).
- **P5 is a trust root**: not executed, not touched.
- The cycle-01 finding is **not** called wrong — it was correct when taken, at a
  smaller corpus. It is **superseded by re-measurement**, which is what the
  protocol asks for.
