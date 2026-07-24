# C3 cycle 08 — the park ledger: the corpus loop, un-wedged

**Product: the missing demotion mechanism.  No corpus batch shipped; the
intake window is open again and cycle 09 consumes it in listed order.**

## What cycle 07 left

Cycle 07 measured the wedge and named the fix it could not itself justify
shipping.  Its finding, verbatim in outcome: the frontier's `ready` head was
**19 consecutive ch3 Parity-and-Divisibility problems** — the block cycle 06
**parked in writing** pending an explicit even/odd coverage decision — and
**all 19 certify**.  That is precisely why the existing machinery could not
help: `frontier_refusals.jsonl` demotes subjects that *fail to certify*, and
demoting a faithful reading through it would have been a false refusal, a
fidelity verdict the measurement does not support.

So the park lived only in PROSE, in a sentence the frontier cannot read.
Every unattended cycle re-previewed the same block and could not proceed in
listed order.  Cycle 07's own words: *"the frontier needs a **park ledger** —
the sibling of `frontier_refusals.jsonl` — or the wedge recurs."*

It recurred.  This cycle fired onto a byte-identical ready head.

## What this cycle shipped

`tools/frontier_parks.py` + `results/frontier_parks.jsonl`, consumed by
`tools/frontier.py`: parked subjects leave `ready` and join `blocked` under
`parked:<reason>` groups, exactly as refused subjects join `refused:<signal>`.

**A park is not a refusal, and the whole design turns on the distinction:**

| | refusal | park |
|---|---|---|
| what it is | a **measurement** — the reading did not certify | a **decision** — the reading certifies; a hold says not yet |
| what it names | the **purchase** that would unblock it | the **decision** that would lift it |
| claims about fidelity | yes, a measured one | **none** |
| reversible | no (rows are evidence) | **yes, by design** (`--lift`, then regen) |

The ledgers are kept disjoint by a tooth: a subject is either measured
refused or held parked, never recorded as both — conflating them would let a
governance hold masquerade as a fidelity verdict, or the reverse.

**Recording a park does not make the decision it waits on.**  This cycle
moved an already-written hold out of prose and into machinery; it did not
overturn, pre-empt, or narrow it.  The rows carry cycle 06 as the parking
authority and cycle 07 as the measurement, and the reason
`evenodd-coverage-decision` names its own lift in
`frontier_parks.REASONS` — a park with no stated way out is an indefinite
hold, which house law forbids, so a tooth requires every reason to state one.

## Effect on the frontier

- `ready` **73 → 53**; head moves from `03_Parity_and_Divisibility#problem-001`
  to `04_Proofs_with_Structure_II#definition-001`.
- **20** nodes demoted into `parked:evenodd-coverage-decision` — the 19 ch3
  entries, **plus one ch4 entry**: `04_Proofs_with_Structure_II#problem-017`
  is verbatim-identical prose to ch3 `problem-005`
  (`42c61654…`).  Parking keys on the SUBJECT TEXT hash, as refusals do, so
  the restatement demotes with its twin — intaking it would have intaken a
  parked statement under a different label.  18 distinct subject hashes, 19
  ch3 + 1 ch4 = 20 demoted nodes.
- `derived_from` gains `frontier_parks_rows: 18`.

## Teeth

Seven new, beside their refusal siblings in `tests/test_frontier.py`:
parked-never-in-ready; groups reconcile to the ledger; rows canonical and
provenanced; reasons in vocabulary **and naming their lift**; parked ∩
intaken = ∅ (you cannot hold back what has shipped); the two ledgers
disjoint; and **the reversibility tooth** — rebuilding the frontier against
an emptied park ledger restores exactly the parked subjects to `ready` and
nothing else moves.  That last one is what makes ledgering a park an honest
recording of a hold rather than a silent exclusion.

## The decision is STILL OPEN — and it is still the only thing blocking

This cycle changed **nothing** about the substance of the question cycle 07
raised.  Restated so it needs no scrollback:

> **Should census-sourced ch3 parity material enter the main corpus?**
> The *mechanical* objection is retired — cycle 07 re-measured it at today's
> corpus size and the even/odd macro is **not** displaced (`a_beats_baseline`,
> `b_evenodd_survives`, `c_no_macro_explosion`, `d_service_byte_identical`
> all PASS with the block).  The *governance* question is untouched.

Either answer is now cheap to execute:

- **ship it** — `python3 tools/frontier_parks.py --lift <sha> evenodd-coverage-decision`
  for the block (or truncate the ledger), rerun the regen chain; all 20
  subjects return to the head of `ready` and the next cycle intakes them;
- **exclude it** — the rows stay exactly as they are and become the standing
  exclusion, already machine-readable, already named, already reversible if
  the call changes later.

What is no longer true is that *not answering* stalls the corpus axis.  It
does not, as of this commit.  The loop runs on ch4 material; the parked block
waits in `blocked` where a hold belongs.

## Status

- Corpus **unchanged**: 77 sources, 73 governed readings, 70 certified.
  `registration.json` **not** re-baselined — no corpus growth to re-baseline.
- **Carried-over demand: 53 ready entries unconsumed** (cap never widened;
  no batch attempted this cycle — the window opened as a product OF this
  cycle's work, and one cycle ships one product).
- Regen chain re-run in full: **only `results/frontier.json` changed**; every
  other downstream artifact byte-identical.
- No trust-root edits (`kernel/certs.py`, `TRUST.md`, escape-gate blocklist
  untouched); no Lean-touching files — Lean-free cycle, no `[lean-fast]`.
- P5 not executed, not touched.
- Full suite: **1217 passed, 35 skipped** (1210 + the 7 new park teeth).
- `merge_to_next_start_s = 46` — cycle 07 merged 18:31:25Z, this session
  started 18:32:11Z.  Merge-event chaining fires.
