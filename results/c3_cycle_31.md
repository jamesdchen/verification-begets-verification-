# C3 cycle 31 — the refill lever was never blocked by egress; it was blocked by a User-Agent

**Product: SUPPLY.**  The `carleson` corpus is intaken (180 nodes, 12 pages),
the portfolio grows **7 → 8 corpora, 1952 → 2132 nodes**, and the frontier's
ready list goes **0 → 5**.  The supply verdict turns
`supply-blocked: tower-class-only` → **`ready-work-available`**.  Zero
readings authored, so the corpus of record stays at **125** sources and every
DL is byte-unchanged — a corpus-intake cycle buys supply, not readings, and
the five ready entries belong to the NEXT cycle.

Probe verdict (RUN here, not read off disk): **`lean-local`**.  No Lean
touched; gate `CGB_LEAN=0 python3 -m pytest tests/ -q`.

## The route, read rather than recalled

`NEXT-SELECTION: refill` — §3.2 path (c).  `tools/corpus_candidates.py`
printed `candidate-available` and selected **`carleson`** in declaration
order, yield-blind, with the command to run verbatim.  #205 had refilled the
registry one commit earlier; this is the first firing to consume it.

## THE FINDING: a 403 that was not the egress policy

The printed command failed on its first page with `HTTP Error 403:
Forbidden`.  That is exactly the shape the declaring session forecast — its
rationale says *"this container's egress returns 403 to every host (even to
already-intaken blueprints)"* — and recording `carleson` as a refusal on it
would have been the obvious, fast, and **wrong** move.  Diagnosed before
recording, per the honesty rule that a transport error is not a reading:

| request | result |
|---|---|
| `curl` (default UA) → `florisvandoorn.com/carleson/blueprint/` | **200** |
| `curl -A "Python-urllib/3.11"` → same URL | **403** |
| `urllib`, default UA → same URL | **403** |
| `urllib`, `User-Agent: Mozilla/5.0` → same URL | **200** |
| `urllib`, default UA → `teorth.github.io/pfr/blueprint/` | **200** |

Same URL, same egress proxy, same second, opposite answers keyed on nothing
but the User-Agent.  So:

* **It is not an org network-policy denial.**  `/root/.ccr/README.md` says a
  proxy 403 means the host is blocked and must be reported, not routed
  around — that rule is right and it does not apply here, because the host
  answers 200 through the same proxy.  The 403 is a CDN bot fence at the
  ORIGIN, refusing `Python-urllib/3.11` before the origin is reached.
* **The declaring session's premise is retired.**  Egress does not 403 every
  host from this container; it 403s nothing.  What 403s is one UA at one CDN.
* **Seven prior intakes never surfaced it** because every one of them sits on
  GitHub Pages, which does not fence.  `teorth.github.io` serves the default
  UA fine — measured above, in the same run.

The defect is therefore in `tools/intake_corpus.py::_fetch`, which shipped
urllib's default UA, and its consequence was worse than a failed fetch: read
through the intake, that 403 is **indistinguishable from a corpus refusing**,
so a driver obeying its own prompt would have filed a wire-side bot fence as
demand data.

**Fix**: an explicit `USER_AGENT` that identifies the crawler honestly
(`cgb-corpus-intake/1.0` plus the repo URL) rather than impersonating a
browser.  Tooth
`test_the_fetch_identifies_itself_and_never_ships_the_urllib_default`
stubs `urlopen`, so it opens no socket, and pins both directions: a
`Request` must be built (a bare URL string cannot carry headers) and the UA
must not be the default the fence rejects.  **Mutation-verified**: restoring
the one-line original reds that tooth and only that tooth.

## What the intake bought, stated at its real size

The declaration was written with eyes open about yield — *"a similar or lower
rate is the expectation"* against `prime_number_theorem_and`'s 2.9%.  It
landed at **2.8%**: of 180 nodes, **5 attempt-candidates**, 44 no-signal, 131
out-of-fragment.  Portfolio verdicts move 135 → **140** attempt-candidates,
1521 → 1652 out-of-fragment, 296 → 340 no-signal.

**And the demand it prices is mostly demand already on the board**, which is
the reading that matters and is not the one the declaration predicted.  It
was declared for *"measure/integral rather than sums over primes"*.  Its
actual miss histogram contribution:

| miss cluster | delta |
|---|---|
| rational-arithmetic | +55 |
| maps-functions | +44 |
| sequences-sums | +39 |
| real-analysis | +35 |
| sets-cardinality | +35 |
| geometry-topology | +10 |
| polynomials-fields | +3 |
| primality | +1 |

`real-analysis` is fourth, not first, and `entropy-log` gains **zero**.  An
analytic corpus asked this fragment for arithmetic, functions and sets before
it asked for analysis.  That is worth exactly one line in the next purchase
pricing and no more: it is a signal count, not a fidelity verdict.

## Ledger and state

No refusal recorded (nothing here is a reading about a corpus subject — the
403 was transport, and the honesty rule forbids filing it).  No park recorded
or lifted.  The candidate row is marked on the registry as the prompt
requires: `corpus_candidates.py --mark carleson intaken` (registry now
candidate=2, example=1, intaken=8, refused=0).

Re-baselined off `tools/measure_cluster_key.py --print-reregistration`:
baseline governed 7195.0, census-of-record 6536.0, accept_max_dl 7166.0,
max_macros 26 — **all unchanged**, because no reading was authored.
`n_top_level_sources` stays 125 and the lineage entry records the corpus-side
growth that did happen.

Frontier: **ready 0 → 5** (all five `carleson`), 49 blocked groups, 73
refused subjects.  Supply paths now `census-signal-ungating=0`,
`new-corpus-intake=8`, `park-lifts=0`, `refusal-retirement=72`.  The five
ready entries are the NEXT cycle's material; this cycle did not widen to
consume them.

## The canary fired, which is the intake being audited

`tests/test_blueprint_census.py::test_no_dead_signal_terms` went red on the
regenerated corpus — its THIRD arm, the one that asks whether a term declared
`FORWARD_LOOKING` has started matching.  `covering` had: the `carleson`
intake puts **one** committed node behind it.

One node is a thin reading and it is still a reading.  The arm asks whether a
term MATCHES, not whether it matches often, and re-declaring a matched term
as forward-looking to keep the count comfortable is exactly the
measurement-wearing-an-intention's-label confusion the set exists to prevent.
So `covering` graduates out of `FORWARD_LOOKING` with the reason recorded
beside the C3-cycle-22 graduation that established the pattern.  This is a
tooth doing its job on the first corpus that could trip it, not a defect.

One stale premise corrected in passing: `tools/blueprint_census.py`'s
docstring still asserted *"this container's egress policy denies the fetch"*.
Measured false this cycle, and it is the same inherited-premise class as the
candidate row's rationale, so it is fixed rather than left to be re-read as
fact by the next session.

## Bounds

No ceremony-reserved surface in the diff — `kernel/certs.py`, `TRUST.md`,
`buildloop/growth_protocol.py`, `setup.sh`, `ci/`, `.claude/`, `.github/`
untouched.  `tools/FgReflect.lean` untouched.  P5 not promoted.  Intake is
network-at-intake only: the fetch is the only networked step, and
`nodes.jsonl` + `fetch_meta.json` with per-page SHA-256 are committed as the
provenance; every downstream step is offline, deterministic and LLM-free.
One intake this cycle.
