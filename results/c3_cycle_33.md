# C3 cycle 33 — the declared corpus is not published, and the intake could not say so without a curl session

**Product: one measured corpus refusal, and the fetch-failure READING made
derived so the next one costs nothing to diagnose.**  Zero certifications;
corpus unchanged at **125** sources and 8 corpora, every DL byte-identical.
Ready stays 0.

Probe verdict (RUN here, not read off disk): **`lean-local`**.  No Lean
touched; per-commit gate `CGB_LEAN=0 python3 -m pytest tests/ -q`.

## The route read `refill`, and the selector picked `flt`

The brief opened `NEXT-SELECTION: refill (ready empty, nothing awaiting
unblock)` — cycle 32 having consumed the last five ready entries.  So §3.2
path (c), and its first act is the selector, not a choice:

```
$ python3 tools/corpus_candidates.py
reason: candidate-available
declared: candidate=2, example=1, intaken=8, refused=0
SELECTED: flt  (adapter blueprint)
  run: python3 tools/intake_corpus.py --name flt --source
       https://imperialcollegelondon.github.io/FLT/blueprint/ --adapter blueprint …
```

The printed command was run **verbatim**.  It failed.

## The measurement: a 404 is a fact about the DECLARATION, not about the wire

Cycle 31's lesson binds here — a transport error is not a reading, so the
failure was diagnosed before anything was recorded.  What the wire says:

| URL | status |
|---|---|
| `…/FLT/blueprint/` (declared) | **404**, stable across three attempts |
| `…/FLT/blueprint`, `…/blueprint/index.html`, `…/blueprint/sect0001.html` | 404 |
| `…/FLT/blueprint.pdf` | 404 |
| `…/FLT/` (project root) | **200** |
| `…/FLT/docs` | 301 |

The 404 body is the **project's own themed error page**, so the origin
answered and the egress reached it.  This is **not** the carleson shape: the
declaring row's rationale forecast "this container's egress returns 403 to
every host", and that premise was already retired by cycle 31 and does not
apply — the host serves 200.  The site's index links to `blueprint` and
`blueprint.pdf` and **both 404**, so the HTML blueprint is simply not
deployed at this host.

**No URL was substituted.**  The declaration point is where a human decides
once, and guessing a source URL is exactly what the honesty bounds forbid; a
neighbouring path that happened to serve HTML would be shopping wearing a
diagnosis's clothes.  The row is marked `refused` with the reason above, and
the registry keeps it as evidence rather than deleting it.

**One intake per corpus cycle.**  The registry now selects `lean_cam_combi`
(`candidate=1` still declared).  Taking it in this firing to make the cycle
look productive is precisely what the prompt forbids, so it is the NEXT
cycle's work.

## The defect this cycle measured: the intake could not say which act it was in

Cycle 31 fixed one wire artifact (urllib's default UA tripping a bot fence)
and left the general defect standing: **`_fetch` re-raised whatever urllib
threw**, so the driver got a bare traceback ending in `HTTPError: HTTP Error
404: Not Found` and had to hand-diagnose the wire with `curl` before it could
record anything.  That is the same hazard cycle 31 named, one level up — the
failure does not carry HOW TO READ IT, and the three readings are genuinely
different acts:

| status | reading | the act |
|---|---|---|
| 404, 410 | `resource-absent` | a decided fact about the DECLARATION — record `--mark NAME refused`, retrying cannot change it |
| 401, 403, 429 | `origin-refused-us` | the origin refused the CLIENT — **diagnose before recording**; the carleson shape |
| 5xx / transport | `transport` | WEATHER — retry under the hiccup protocol, and **never** record a ledger row from it |

`FETCH_READINGS` + `IntakeFetchError` + `classify_fetch_failure` make that
derived rather than remembered, and `main()` now prints the reading and exits
2 instead of raising — a stack trace says only "the fetch died".  The failure
this cycle hit now reads:

```
IntakeFetchError: intake fetch RESOURCE-ABSENT (HTTP 404): https://…/FLT/blueprint/
  how to read it: the origin ANSWERED and says this resource does not exist -- a
  decided fact about the DECLARATION, not about the wire.  Retrying cannot change
  it: record it with `corpus_candidates.py --mark NAME refused --reason ...`
```

**5 teeth, network-free** (`urlopen` stubbed, no socket), **mutation-verified
in both directions**:

* folding 403 into the `resource-absent` class reds
  `test_a_403_stays_DIAGNOSE_FIRST_and_is_never_the_same_act_as_a_404`
  **and only that test** — the mutation is the exact wrong call cycle 31 was
  about, and the tooth catches it;
* removing the CLI's `except IntakeFetchError` reds
  `test_the_cli_reports_the_reading_instead_of_a_traceback` and only that.

The overlap canary (`test_every_reading_is_distinct_and_the_status_classes_never_overlap`)
is the dead-branch tooth: a status resolving to two readings is two answers to
one question.

## What moved, and what did not

* Corpus **unchanged**: 125 sources, 8 corpora, 2132 nodes; governed readings
  121, certified 118; every DL byte-identical.  **No lineage entry** — nothing
  grew.
* `specs/mathsources/corpus_candidates.json`: `flt` `candidate → refused`
  with the measured reason.  Declared counts `candidate 2 → 1`,
  `refused 0 → 1`.
* Supply verdict **unchanged** — `intake-work-available: new-corpus-intake`,
  `declaration: candidate-available`, route `refill`.  A refused candidate did
  not blind the loop: there is still a declared row to take.
* No refusal-ledger row, no park, no purchase.  A wire reading is not a
  reading about a corpus SUBJECT, so nothing went into
  `results/frontier_refusals.jsonl`.

## What this says about the declaration point

Three of the four rows in the registry were declared in one attended sitting
with **URL NOT VERIFIED** written into each rationale, on a premise — "this
container's egress returns 403 to every host" — that cycle 31 measured false.
Cycle 31 took `carleson` and it landed; cycle 33 took `flt` and its URL does
not exist.  That is one confirmation and one refutation out of two attempts,
which is what an unverified declaration is worth, and it is the registry
working as designed: the driver's fetch **is** the measurement, and the
refused row is now evidence a re-declaration can be written against.  Whether
to re-declare `flt` at a verified location is a maintainer call — this cycle
does not reorder, delete, or rewrite a declared row.

## Bounds

No ceremony-reserved surface in the diff — `kernel/certs.py`, `TRUST.md`,
`buildloop/growth_protocol.py`, `setup.sh`, `ci/`, `.claude/`, `.github/`
untouched.  `tools/FgReflect.lean` untouched; Lean-free cycle, no
`[lean-fast]`.  P5 not promoted.  Network-at-intake only, and the only
networked step here was the declared fetch plus its diagnosis; every tooth
added is socket-free.  No purchase priced.  Registry is evidence, not
inventory: the refused row stands.

**Gate**: `CGB_LEAN=0 python3 -m pytest tests/ -q` → **1953 passed, 42
skipped** (1948 + 5 new teeth).
