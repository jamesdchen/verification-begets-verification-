# specs/mathsources/staged/ — quarantined exogenous sources (WP-SRC)

These are **exogenous, human-authored** mathematical statements selected from
public references to grow the corpus — in particular to satisfy COMPRESSION.md
§11.6 (WP-T6b), which observes that the certified corpus has **82 `forall` and
ZERO `exists` binders** and asks for "1–2 exogenous exists-sources committed to
`specs/mathsources/` before the wave, or the rung cannot satisfy vacuity/witness
clauses without manufacturing its own evidence."

## Why they are STAGED, not top-level

They are held in this subdirectory (and in the manifest's separate `staged`
array, not `files`) **on purpose**. Promoting them to top-level `.txt` would
change committed-results semantics without a reviewer's sign-off:

* `bench_formalize.py` (`_CORPUS.glob("*.txt")`, line ~585) enumerates every
  top-level source; the committed `results/formalize_bench_state.jsonl` records
  `ungoverned:40` / `governed:40` — moving these files up would shift those
  denominators (and the "≥ 30/40 certified" headline, `bench_formalize.py` ~807).
* `cgb.py` `_ledger_sync` (`ms.glob("*.txt")`) bills every top-level source as a
  `math-source` demand row — top-level placement would change the corpus DL base.
* `tests/test_mathsources_manifest.py` pins `EXPECTED_TOTAL = 40` **and** a strict
  top-level `.txt` ↔ `manifest["files"]` bijection.

None of those globs scan this subdirectory (they scan top level and `dream/`
only), so staging here is inert with respect to bench denominators, the ledger,
and the pinned manifest test. This mirrors the existing `dream/` convention: a
sibling directory with its own README and its own manifest treatment, deliberately
outside the top-level bijection.

## Promotion (reviewer-gated)

A reviewer promotes a file by (1) moving it to top level, (2) moving its entry
from `manifest.staged` into `manifest.files`, (3) bumping `EXPECTED_TOTAL` in
`tests/test_mathsources_manifest.py`, and (4) re-baselining the bench state so
the new denominator is intended, not accidental. Authoring the **reading** for
each source is a separate, later, gated step (not done here — house rule).

Note for promotion: entries tagged with the ad-hoc `existential` axis and the
`binder_hint` field below must reconcile with the frozen test's `VALID_AXES`
set at promotion time (either add `existential` to `VALID_AXES` or retag as
`plain`); `binder_hint` / `provenance` / `staged_reason` are staging-only
metadata that the frozen `files`-schema does not carry.

## Provenance (public-domain / CC-licensed references)

Each statement is a standard, long-established theorem or definition; the file
text renders it in this corpus's plain-English convention (spelled-out
operators; ASCII). The upstream statement each renders is recorded verbatim in
the manifest `staged` entry's `provenance` block, with a URL. References used
are CC BY-SA (ProofWiki, Wikipedia) or standard public educational texts.
