# Metrics & Findings

All numbers below are produced by `python3 milestones.py m5` (corpus off) and
`m8` (corpus on), which run the build loop from a fresh registry under each
steering policy against the ksy families of the fixed 200-spec backlog (185
ksy specs; the 15 ABNF specs are covered by the milestone-4 chain, exercised
separately). Cost is `LLM kilotokens (in+out) + verifier seconds`.

Artifacts: `artifacts/metrics_{policy}_{nocorpus,corpus}.csv`,
`artifacts/reach_vs_cost_{nocorpus,corpus,all}.png`.

## Reach vs. cost, by steering policy

| policy | admissions to full reach | cost at full reach | shape |
|---|---|---|---|
| **frequency** (most recurrent miss) | 5 | ~198 (k-tokens + s) | gradual, family-by-family |
| **closure** (miss covering most specs via unification lookahead) | 1 | ~56 | one broad grammar, immediate saturation |

`closure` reaches 100% backlog coverage roughly **3.5× cheaper** than
`frequency`. The mechanism: `closure` attacks the miss whose resolution
newly covers the most specs, which steers the LLM toward proposing one broad
Kaitai grammar that subsumes every remaining family in a single admission.
`frequency` instead resolves the largest *recurring* miss each round,
admitting a sequence of narrower generators, each of which then subsumes its
predecessor.

The curve is monotone and saturating for both policies (see
`reach_vs_cost_all.png`). Coverage saturates well before 20 iterations
because the backlog has a small number of feature families; the loop then
reports `no-misses` and stops.

## Description length (MDL) trends down as reach rises

Total description length falls from **7555 → ~298** over a run under both
policies, even as reach climbs from 0.19 (seed) to 1.0. This is the library
compression discipline working: each broad admission subsumes narrower
entries (marked retired, kept for provenance), so the **live** library stays
at size 1 while its reach expands. Bloat — the documented death mode of prior
skill libraries — does not occur here; the MDL admission gate refuses any
candidate that would raise total description length without new coverage.

## Tier mix and composition depth

- The seed generator is promoted to the **universal** tier (Dafny proof over
  the generator + Hypothesis spec-fuzz); its outputs then need no emission
  check and the planner prefers it.
- Composition depth reaches **2** for ABNF task specs, routed through the
  two-link chain `abnf-record-emitter → kaitai-struct-rw` (a tree-sitter
  generator emitting the input-stage parser for a Kaitai generator).

## Counterexample corpus: caught-by-replay fraction

With `--corpus` on, the metrics log records how many kernel rejections were
caught by corpus replay vs. fresh adversarial generation:

| policy | rejections caught by replay | by fresh generation | replay fraction |
|---|---|---|---|
| frequency (corpus on) | 0 | 0 | — |
| closure (corpus on) | 0 | 0 | — |

**Finding:** in these runs the corpus caught nothing, because the LLM's
proposals were almost always admitted on the first round — there were no
kernel rejections for replay to accelerate. This is the honest, instrumented
answer to the open question the corpus was built to probe: its value hinges
on LLM candidates sharing *systematic* blind spots that produce repeated
rejections on similar inputs. In this seed domain, with a small, well-modeled
spec vocabulary and a strong proposal model, that condition does not arise, so
corpus replay is inert. It would be expected to pay off in a domain where the
proposal engine repeatedly proposes subtly-wrong specs against overlapping
inputs (e.g. checksum/framing families with off-by-one length handling); the
instrumentation is in place to measure it there.

The corpus flag does not change the reach-vs-cost curves here (the corpus-on
and corpus-off curves for a given policy differ only by LLM-proposal
nondeterminism, not by any replay effect).

## Two DL series: legacy `total_dl` vs. `ledger_dl` (Combined-Loop W0)

There are now **two distinct description-length series**, and they must never
be confused:

- **`total_dl`** (legacy, `buildloop/mdl.py` → `metrics_log`) is the
  codec-only series described above: live-generator descriptions plus the
  codec backlog. `milestones.py` `m5`/`m7`/`m8` read this series and are
  labeled as such. It is **frozen** — no new demand kinds enter it.
- **`ledger_dl`** (`buildloop/dl.py` → the separate `ledger_metrics` table,
  exported by `metrics.export_ledger_csv`) is the one currency of the combined
  loop. It prices **every** demand kind in the one ledger:

  | demand kind | cost when served | cost when unserved |
  |---|---|---|
  | `spec-file` | chain-length + size/256 | `UNCOVERED_PENALTY` (50) |
  | `nl-request` | `READING_CHAIN_COST` (2) + reading DL | `UNCOVERED_PENALTY` |
  | `caged-incumbent` | `min(TOLL_RATE·calls, UNCOVERED_PENALTY)` | — (toll *is* the pressure) |

  Generators are priced over their **full authored artifact** — the canonical
  body *plus* any LLM-authored `_grammar_js` payload the legacy series popped
  before pricing. The dashboard row per epoch is `{ledger_dl, covered/total by
  kind, tier_mix, toll_paid, toll_retired, max_chain_depth_used
  (exogenous-serving only), kernel_loc}`.

  Policy constants (by-fiat inputs to admission, all in `buildloop/dl.py`):
  `UNCOVERED_PENALTY=50`, `READING_CHAIN_COST=2`, `TOLL_RATE=0.05`,
  `HORIZON_H=1000` (unit = sync epochs, never wall-clock), `MONITOR_RATE=0.01`,
  `MONITOR_CAP=25`, with the ratio rule `MONITOR_RATE ≤ TOLL_RATE/2`.

Record and export the ledger series with:

```sh
python3 cgb.py ledger sync      # ingest committed demand as exogenous rows
python3 cgb.py ledger status    # ledger_dl + covered/total by kind
```

`demos/demo_ledger.py` (LLM-free) exercises the gate's four teeth: expansion refused
when a cheaper covering candidate exists, the `_grammar_js` payload priced, a
system-origin row unable to trigger expansion, and a zero-traffic incumbent
contributing zero toll pressure.

## Math reach vs. cost (F-INT-3)

The formalization extension now logs its own reach-vs-cost series, scoped to the
**exogenous** math corpus. `metrics.snapshot()` gains four fields, persisted in
a metrics-owned `math_metrics` side table (created from `metrics/` code and
JOINed into `export_csv` on `seq` — the fixed-column `metrics_log` schema in the
unowned `library/__init__.py` is **not** touched):

| field | definition |
|---|---|
| `math_total` | count of **exogenous-origin** `math-source` demand rows |
| `math_covered` | count of exogenous-origin `math-source` rows with a persisted reading (so `math_covered ≤ math_total` holds by construction) |
| `math_dream_rows` | count of **system-origin** (dream) `math-source` rows |
| `tier_kernel_checked` | count of `proof-cert` certificates in the registry (0 in Lean-absent containers) |

**These are new, scoped names — they deliberately differ from `dl.py`'s
all-rows ledger counters.** `buildloop/dl.py` prices *every* `math-source` row,
system-origin dreams included, in its `total_math`/`covered_math` ledger
counters; those names are **untouched** (the dl.py same-name rule). The metrics
`math_total`/`math_covered` are **exogenous-scoped** because reach is a property
of the demand the loop is charged to serve — dreams propose vocabulary, they are
never exogenous demand, so they are counted only in `math_dream_rows` and never
inflate the denominator. A mixed (exogenous + dream) registry therefore never
shows `math_covered > math_total`. (The v1 `math_certified` field was **dropped**:
both persistence paths write only on `res.ok`, so it was definitionally
identical to `math_covered`.)

The math reach series is `math_covered / math_total`, plotted through the
established `milestones.py` shim: an intermediate CSV with `reach`, the
cumulative token columns, and `verifier_seconds = 0`, handed to the existing
`reach_vs_cost`. With seconds pinned to 0 the cost axis is **kilotokens only**,
so tokens and seconds are never summed into one number (E6); the residual
axis-label imprecision is accepted and noted in the plot title. Milestone
`m9_planted` (LLM-free, Lean-free, fast tier) produces this curve
deterministically from the committed reading fixtures, with synthetic
per-serve token increments (labeled synthetic in the plot title) so the x-axis
is non-degenerate; monotonicity is asserted over both axes. The live `m9`
variant is LLM-requiring and skips with an honest note.

## Reproducing

```sh
export CGB_ARTIFACTS=$PWD/artifacts
python3 milestones.py m5   # corpus off: frequency + closure, plot
python3 milestones.py m8   # corpus on:  frequency + closure, plot + replay report
python3 milestones.py m9_planted   # F-INT: LLM-free planted math reach-vs-cost curve
```
