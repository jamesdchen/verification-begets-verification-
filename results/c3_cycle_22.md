# C3 cycle 22 — path (c) reached the wire and answered, and the two tool defects standing behind it

**Axis:** corpus. **Shipped: 0 sources. Refusals: 0 new rows. Parks: 0.**
Portfolio **6 corpora / 1008 nodes → 7 / 1952**.  Frontier ready **0 → 27**.
Supply verdict **`supply-blocked: tower-class-only` → `ready-work-available`**.
Corpus top-level sources **121 → 121** (no reading authored).  Full suite green.

This cycle's product is **SUPPLY**.  The 27 ready entries it created belong to
cycle 23; widening this cycle to consume them is exactly what the DRIVER prompt
forbids.

## Where this sits: cycle 21 measured the door shut, and it is now open

Cycle 21 walked this same path to this same corpus and recorded a **registry
refusal**: `alexkontorovich.github.io` answered `403 Forbidden` to CONNECT — an
organization egress-policy denial, correctly not retried.  #178 then
**re-declared** the row after the policy widened to full access, with the
honest caveat that the URL remained unverified from the declaring container.

This cycle is that re-attempt.  **The fetch answered: 15 pages, no 403.**  The
recorded `prior_refusals` entry stands as the pre-policy reading it was; this
is a new measurement, not a re-measurement staged to force a green.

## The intake, and the two defects it exposed

The command `corpus_candidates.py` printed was run verbatim.  It reported:

```
intake prime_number_theorem_and: 0 nodes, 15 pages
```

**Zero nodes from a site carrying 945 theorem wrappers.**  Two defects, both in
our tooling and neither a property of the corpus — which is why this cycle
records an INTAKE and not a second refusal.  Filing a refusal against a corpus
for our own glob bug would have been demand data that lied.

### 1. The blueprint default glob could not see the site

`intake_corpus.py` defaulted blueprint intakes to `sect*.html`.  This blueprint
renders its chapters to **named pages**:

| page | thmwrappers |
|---|---|
| `index.html`, `sect0001.html`, `sect0002.html` | **0** (front matter) |
| `secondary-chapter.html` | 300 |
| `primary-chapter.html` | 134 |
| `second-approach-chapter.html` | 131 |
| `tertiary-chapter.html` / `IK-chapter.html` / `zeta-chapter.html` / … | 88 / 77 / 54 / … |

The glob matched exactly the three node-free pages.  Three things say the narrow
default was wrong rather than a judgement worth preserving:
`blueprint_extract.extract_site`'s own docstring already documented `*.html` for
named-chapter sites, its CLI already offered the flag, and **all six
previously-intaken corpora record `pages_glob: *.html`**.  The default was the
outlier.  Fixed at both layers.

### 2. A zero-node extraction reported SUCCESS

`intake_corpus.py`'s module docstring promises a blocked host surfaces as an
error and "**never a silent empty corpus**".  An adapter matching no page breaks
that promise as thoroughly as a 403 does — and it did: the driver wrote a
0-byte `nodes.jsonl` plus a `fetch_meta.json` claiming `n_nodes: 0`, printed a
success line, and exited 0.  An unattended cycle that trusted the exit code
would have committed an empty corpus as its product.  Now a pages-present /
zero-node extraction **refuses before writing anything**, naming the glob and
the pages it saw, and leaves no directory behind.

Note what makes this the more dangerous of the two: defect 1 alone is visible
the moment anyone looks at the count.  Defect 2 is what let the count go
unlooked-at.

### The hazard the wider glob introduces, closed

A wide glob can double-count a node a site renders on two pages, and this site
does exactly that: `Meissel-Mertens-constant` is rendered **identically** in
both `explicit-chapter.html` and `secondary-chapter.html`.  Naively widening
would have inflated the corpus to 945.

So `extract_site` now treats a repeated label whose record is identical in every
field as **one node** (first in sorted-page order), and a repeated label whose
content **differs** as an ambiguity no machine may resolve —
`RestatementConflict`, raised rather than picking a side.  Both branches are
**no-ops on all six previously-intaken corpora** (measured: zero repeated labels
in any of them), so nothing already committed moves.

Final count: **944 nodes** = 945 wrappers − 1 identical restatement.

## Teeth (four new, each mutation-verified in both directions)

| tooth | mutation that reds it |
|---|---|
| `test_default_glob_reaches_named_chapter_pages` | default back to `sect*.html` |
| `test_zero_extracted_nodes_refuses_and_writes_nothing` | drop the refusal branch |
| `test_identical_restatement_across_pages_counts_once` | drop the dedupe |
| `test_conflicting_restatement_raises_rather_than_picking_a_side` | silently keep the first |

The tooth these replace, `test_default_glob_follows_adapter`, asserted only that
the string `"sect*.html"` appeared somewhere in the driver's source.  It would
have passed against all four mutations above, and it passed while the defect it
named was live.  Decoration replaced with measurement.

`test_empty_labels_are_never_deduplicated` guards the dedupe's own edge: an
absent `id` is no identifier, so two anonymous nodes stay two nodes.

## What the census says — including where it says the intake bought little

**Recorded as measured, not as hoped.**  The declared rationale predicted this
corpus would be dominated by analytic material outside the fragment.  It is:

| verdict | count | share |
|---|---|---|
| out-of-fragment | 790 | 83.7% |
| no-signal | 127 | 13.5% |
| **attempt-candidate** | **27** | **2.9%** |

944 nodes bought **27** attempt-candidates — a yield an order of magnitude below
math2001's (106 of 260).  The rationale said the early elementary chapters were
the reason to intake and the analytic bulk was not an argument for it; the
reading confirms both halves.  Portfolio-wide, `real-analysis` enters as the
largest miss signal (675), ahead of `rational-arithmetic` (565).

The 27 ready entries are **all** from this corpus.  They are LEXICAL
attempt-candidates — the census reports signals, never fidelity verdicts — and
the first of them (`AnalyticOn.norm_le_of_norm_le_on_sphere`) is plainly
analytic.  Cycle 23 should expect refusals among them and record each as
first-class demand data.  **Nothing here promises that 27 readings certify.**

## Five signal terms graduated, by the canary's own third arm

`test_no_dead_signal_terms` reds in both directions, and this cycle tripped the
direction that fires on GROWTH: `limit`, `logarithm`, `product over`,
`remainder` and `sum over` were declared `FORWARD_LOOKING` — demand named ahead
of its corpus — and the intake put committed nodes behind all five.  They are
removed from the set, because their counts are evidence now and a
forward-looking declaration would understate what the corpus holds.  A term
leaves that set the cycle it goes live and is never re-added to keep a canary
quiet.  `FORWARD_LOOKING` feeds no artifact — it is read only by the canary — so
no committed reading moves with it.

## Bounds held

* **Network at intake only.**  The fetch was the only networked step; the re-run
  that produced the 944 nodes was `--pages-dir` over the already-fetched pages,
  so the corpus is byte-derived from the SHA-256'd page set recorded in
  `fetch_meta.json`.  Everything downstream is offline, deterministic, LLM-free.
* **No shopping.**  The candidate was taken in declaration order from the
  registry, yield-blind; no row was reordered, skipped or substituted, and no
  second candidate was taken to make the cycle look more productive.
* **One intake.**  Row marked `intaken`; the registry is evidence, not
  inventory, and the cycle-21 refusal row stands unedited.
* **The ready list is not consumed here.**  Cycle 23 gets it.
* No carrier, node class, operator word or trust root grows.  `kernel/certs.py`,
  `TRUST.md`, the escape-gate blocklist and `ANTI_LIST` are untouched; P5 not
  executed.  No Lean-touching edit, so no lane tag.
