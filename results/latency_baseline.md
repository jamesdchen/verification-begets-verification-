# Corpus-cycle latency baseline (measured evidence)

Where a corpus (C3) cycle's wall-clock goes today. Numbers tagged
**[measured here]** were timed in this checkout on 2026-07-24
(Linux x86_64, 4 vCPU); everything else states its provenance honestly.
This is a baseline for the latency work, not a target — the point is to
show that the measurable in-checkout steps are seconds-to-minutes and are
dwarfed by the **inter-cycle gap** (the merge→next-start dead time), which
is why `merge_to_next_start_s` is the field the telemetry ledger exists to
capture.

## The stage breakdown

| stage | wall-clock | provenance |
|---|---|---|
| orient (`tools/session_brief.py`) | ~0.03 s | **[measured here]** stdlib-only, reads committed artifacts |
| select (census read / frontier) | seconds | **[measured here, proxy]** re-census inside regen below; selection itself is a read over `results/census_portfolio.json` |
| author (driver LLM authoring) | minutes | **unmeasured here** (LLM, network) — plausibly 2–10 min of model time per batch, dominated by token latency not compute |
| certify (per-source replay) | ~seconds/source | **derived** from bench replay cost; see WS2-deferral note |
| regen (`tools/regen_downstream.py`) | ~7.7 s | **[measured here]** full DAG, `-n auto`; `git status` stayed clean afterward (no artifact drift) |
| suite (`pytest tests/ -q -n auto`) | ~64.8 s (1 m 05 s) | **[measured here]** 1140 passed, 35 skipped, 4 vCPU; serial CI runs longer |
| gate (CI lane, Lean-last) | ~2 min typical | **observed from Actions history** — N-way sharded; serial pre-shard runs were longer |
| ship (commit + PR + merge) | seconds of machine time | **unmeasured** — human/merge-bot latency dominates, not compute |

### The number that actually dominates: merge → next session start

The measurable machine work above sums to **single-digit minutes**. The
committed cycle-to-cycle gap is **hours**:

- C3 cycle-01 commit `cd6391c` at `2026-07-24T03:04:51+00:00`
- C3 cycle-02 commit `6262f73` at `2026-07-24T09:32:12+00:00`
- **measured gap: 6.46 h** commit-to-commit (23 241 s); ~6.07 h measured
  from the cycle-01 merge (PR #28, `244dc65`) to the cycle-02 commit.

**Provenance correction (honesty):** the shared plan cited a "4.2 h
measured cycle-01→cycle-02 gap." Verified against `git log` here, the two
committed C3-cycle timestamps are **6.46 h apart, not 4.2 h.** Recorded as
the measured value; the 4.2 h figure could not be reproduced from git
history in this checkout. Either way the conclusion is unchanged and
stronger: the inter-cycle dead time (merge event not chaining promptly into
the next session start) is the single largest latency term by a wide
margin — larger than orient + regen + suite + gate combined — which is
exactly why the telemetry ledger's `merge_to_next_start_s` field is called
out as its most important number.

## WS2 deferral verdict (recorded so it is not re-attempted without numbers)

Per-source certification replay measures **~seconds against a multi-hour
cycle**, so parallelizing it cannot move the cycle wall-clock. Bench
authoring is **already wave-concurrent** (`bench/bench_formalize.py`,
LAT-A), so there is no serial authoring bottleneck left there to split.
Adding further parallelism at this layer therefore cannot pay, and it
carries a concrete correctness risk: the sqlite formalize-cache under
multiple concurrent process writers turns transient `database is locked`
errors into **permanently checkpointed false `uncertified` verdicts** —
i.e. it corrupts the certification evidence it was meant to speed up.
(The suite run above reproduces the benign single-process degradation path:
`formalize_cache: CGB_DB=... unopenable ... degrading to the in-process
dict` — harmless read-only, but the multi-writer version is not.) WS2 is
deferred: do not re-open it without new measured numbers showing a
seconds-scale saving that clears this risk.
