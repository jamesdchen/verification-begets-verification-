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

## Reproducing

```sh
export CGB_ARTIFACTS=$PWD/artifacts
python3 milestones.py m5   # corpus off: frequency + closure, plot
python3 milestones.py m8   # corpus on:  frequency + closure, plot + replay report
```
