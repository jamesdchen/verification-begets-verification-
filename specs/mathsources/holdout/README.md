# specs/mathsources/holdout/ — the contamination-resistant held-out set (WP-HOLDOUT)

These are **exogenous, human-authored** mathematical statements held out from the
main corpus to satisfy COMPRESSION.md **§11.7** (and §12's cross-cutting
precondition): *"claims [of generalization] need the committed holdout source set
(~20 readings) or stay unmade"* and *"the §11.7 holdout set (~20 readings) must be
committed before WP-MET or any generalization claim."*

On the committed 51-source corpus every ΔDL is exact **in-sample** arithmetic with
zero generalization power. A holdout set that was itself chosen to flatter the
miner would inherit that defect. The point of this directory is a set selected by
rules designed to make it **independent of the miner** — so that a later
measurement over it can honestly speak to out-of-sample cost and description
length. The rules below are **binding**; they were followed to produce this set
and any addition must follow them too.

## Why they are held out (INERT, like `staged/` and `dream/`)

They live in this subdirectory and in the manifest's separate **`holdout`** array
(never `files`). Every corpus/ledger/bench glob over `specs/mathsources` is
**top-level only** and does not descend here:

* `bench_formalize.py` — `_CORPUS.glob("*.txt")` (line ~673) and `_DREAMS`
  (`dream/`) only; the committed `ungoverned:40 / governed:40` denominators are
  untouched.
* `cgb.py` `_ledger_sync` — `ms.glob("*.txt")` + `dream.glob("d*.txt")` only; the
  corpus-DL base is untouched. `_seed_math_readings` reads `mathsources/readings/`
  only.
* `demo_ledger.py` (`.glob("*.txt")`) and `tests/test_mathsources_manifest.py`
  (top-level `*.txt` ↔ `manifest["files"]` bijection, `EXPECTED_TOTAL = 51`) — both
  top-level only.

None of these is recursive (`rglob`/`**` appear nowhere over `specs/mathsources`),
so `holdout/` is inert with respect to bench denominators, the ledger, and the
pinned manifest test — exactly as `staged/` was before promotion.
`tests/test_mathsources_holdout.py` pins this inertness so a future recursive glob
that reached in here fails CI.

## 1. Curation-independence rules (binding)

The generalization claims §11.7 gates need a set that was **not chosen to flatter
the miner**. Three rules enforce that:

**(a) Different reference works than the main corpus.** The main corpus draws on
ProofWiki / Wikipedia / LibreTexts(-swapped). This holdout draws on a **disjoint,
public-domain** source: **Euclid's *Elements*, the number-theoretic books**, in
**T. L. Heath's 1908 public-domain translation**, presented in the **David E.
Joyce edition** (Clark University, `mathcs.clarku.edu/~djoyce/elements`). No
ProofWiki / Wikipedia / LibreTexts statement is used.

**(b) No idiom-family targeting — selection by a stated neutral rule.** Sources
are selected by **sequential coverage in canonical order**, never by recurrence
with the existing corpus:

> **Neutral rule (as executed).** Walk Euclid's number-theoretic material in its
> fixed canonical order — **Book VII, Definitions 1–22**, then **Book IX,
> Propositions 21–36** (the classical even-and-odd block) — and take **each
> statement whose content lies in the Nat/Int fragment, in encounter order**,
> until **20** are taken. A statement outside the fragment's *domain* (geometry,
> ratio/proportion, the unit/number meta-primitives, or an operator the fragment
> intends not to have) is either **skipped** (out of domain — logged) or **taken
> and marked `non-transcribable`** (a genuine integer statement that hits a named
> fragment boundary, e.g. `prime`). The stopping rule is the count 20, not any
> property of the statement.

The canonical numbering is **public and fixed** — an auditor does not depend on
this file to know that Euclid VII.Def 6 is *even* or IX.21 is *sum-of-evens*.
That is the property that makes the walk independently checkable. Overlap with the
main corpus's idiom families (even/odd, divisibility, common-divisor) is **not
avoided and not sought** — it is whatever the neutral walk produces. (It is in
fact useful: a same-idiom statement from a *different source* is the cleanest test
of whether a learned macro transfers out-of-sample.)

**(c) The selection log is committed here (auditable curation).** §2 below records
**every** item the walk considered — taken, skipped, or marked non-transcribable —
with its disposition and reason. Nothing was silently dropped.

**Honesty clauses.** Sources are **never composed**: each is a real Euclid
statement, quoted **verbatim** in the manifest `provenance.verbatim`, and rendered
into the corpus's plain-English convention (spelled-out operators, ASCII) with the
adaptation disclosed in `rendering_note`. Where Euclid says "measures" we render
"divides" (the universally documented equivalence, annotated by Heath himself);
that mapping is disclosed per entry. **Existential shapes are present because the
neutral rule produced them** (Euclid states even/odd/product classes existentially)
— they were not hunted for. Verification is **snippet-concordant, not
direct-fetch**: `mathcs.clarku.edu` is blocked for direct fetch by the session
egress policy (403), so each `verified_via` records that the statement was returned
concordantly by a `clarku.edu`-domain-restricted web search, and that Joyce's
edition lightly modernizes Heath's wording. This mirrors the citation-fix
package's honesty for the ProofWiki-blocked sources.

## 2. Selection log (what was considered / taken / skipped)

**Considered: 38** (VII Def 1–22 = 22; IX Prop 21–36 = 16, of which 21–28 were
reached before the quota closed).
**Taken: 20** (17 transcribable + 3 non-transcribable).
**Skipped (out of domain): 10** (all in Book VII).
**Not reached (quota met at IX.28): 8** (IX Prop 29–36).

### Book VII Definitions 1–22 (walked in order)

| # | Euclid VII Def | disposition | reason |
|---|----------------|-------------|--------|
| 1 | unit | **skip** | meta-primitive ("that by virtue of which each thing is one") — not a Nat/Int statement |
| 2 | number | **skip** | meta-definition of "number" — not a statement |
| 3 | part (divisor) | **skip** | names the measuring relation = the primitive `dvd`; no assertable content beyond the operator |
| 4 | parts | **skip** | the fraction/ratio notion ("parts when it does not measure") — out of the integer fragment |
| 5 | multiple | **skip** | names "multiple" = `dvd`; terminology, no assertable content |
| 6 | **even** | take-T → **h01** | `even` is a lexicon predicate; content = ∃k, n = k+k |
| 7 | **odd** | take-T → **h02** | `odd` lexicon predicate; content = ∃ even m, n = m+1 |
| 8 | **even-times-even** | take-T → **h03** | content = ∃ even a,b, n = a·b (name incidental) |
| 9 | **even-times-odd** | take-T → **h04** | content = ∃ a even, b odd, n = a·b |
| 10 | **odd-times-odd** | take-T → **h05** | content = ∃ odd a,b, n = a·b |
| 11 | **prime** | take-**NT** → **h06** | no `prime` operator; matches the repo's `operator:prime` boundary (38/51) |
| 12 | **prime to one another** (coprime) | take-T → **h07** | `coprime`/`gcd` lexicon (Nat-only); content = gcd(a,b)=1 |
| 13 | **composite** | take-**NT** → **h08** | no `composite` operator; same footing as prime |
| 14 | **composite to one another** | take-T → **h09** | plain binary common-divisor existential (∃ d>1, d\|a ∧ d\|b) — no absent operator |
| 15 | multiplication | **skip** | defines the `*` operator/procedure — meta |
| 16 | plane number | **skip** | geometric classification ("sides"); proper-factor reading not in the terse verbatim |
| 17 | solid number | **skip** | geometric (three "sides") |
| 18 | **square** | take-T → **h10** | content = ∃a, n = a·a |
| 19 | **cube** | take-T → **h11** | content = ∃a, n = a·a·a (variadic `*`) |
| 20 | proportional | **skip** | ratio/proportion — out of the integer fragment |
| 21 | similar plane/solid | **skip** | proportion of sides — geometric/out of domain |
| 22 | **perfect** | take-**NT** → **h12** | needs the sum of all proper divisors (unbounded aggregate); no unfold |

### Book IX Propositions 21–36 (walked in order; stop at 20 taken)

| # | Euclid IX Prop | disposition | reason |
|---|----------------|-------------|--------|
| 21 | sum of evens is even | take-T → **h13** | binary specialization; even(a)∧even(b)⇒even(a+b) |
| 22 | even-count of odds sums even | take-T → **h14** | two odds: odd(a)∧odd(b)⇒even(a+b) |
| 23 | odd-count of odds sums odd | take-T → **h15** | three odds (variadic `+`, width 3) — shape absent from the committed corpus |
| 24 | even − even = even | take-T → **h16** | ambient Int (subtraction totality) |
| 25 | even − odd = odd | take-T → **h17** | ambient Int |
| 26 | odd − odd = even | take-T → **h18** | ambient Int |
| 27 | odd − even = odd | take-T → **h19** | ambient Int |
| 28 | odd × even = even | take-T → **h20** | odd(a)∧even(b)⇒even(a·b) — **quota of 20 reached, walk stops** |
| 29 | odd × odd = odd | *not reached* | quota met at IX.28 |
| 30 | odd \| even ⇒ odd \| half | *not reached* | (would have been take-T, existential half) |
| 31 | odd coprime n ⇒ odd coprime 2n | *not reached* | (would have been take-T) |
| 32 | continually-doubled ⇒ even-times-even only | *not reached* | (out of domain: inductive "continually doubled") |
| 33 | half odd ⇒ even-times-odd only | *not reached* | (out of domain) |
| 34 | neither ⇒ both classes | *not reached* | (out of domain) |
| 35 | geometric-series sum | *not reached* | (out of domain: proportion) |
| 36 | Euclid–Euler perfect number | *not reached* | (out of domain: geometric series + prime + perfect) |

## 3. Per-source summary

| id | gist | Euclid | in-fragment | axes |
|----|------|--------|-------------|------|
| h01 | n even ⇔ ∃k, n=k+k | VII.Def 6 | yes (∃) | existential |
| h02 | n odd ⇔ ∃ even m, n=m+1 | VII.Def 7 | yes (∃) | existential |
| h03 | even-times-even = ∃ even a,b, n=a·b | VII.Def 8 | yes (∃) | existential |
| h04 | even-times-odd = ∃ a even,b odd, n=a·b | VII.Def 9 | yes (∃) | existential |
| h05 | odd-times-odd = ∃ odd a,b, n=a·b | VII.Def 10 | yes (∃) | existential |
| h06 | prime = measured by a unit alone | VII.Def 11 | **no** (`operator:prime`) | non-transcribable |
| h07 | coprime a,b ⇔ gcd(a,b)=1 | VII.Def 12 | yes | side-condition |
| h08 | composite = has a non-unit divisor | VII.Def 13 | **no** (`operator:composite`) | non-transcribable |
| h09 | composite-to-one-another = ∃ d>1, d\|a∧d\|b | VII.Def 14 | yes (∃) | existential, idiom:common-divisor |
| h10 | square = ∃a, n=a·a | VII.Def 18 | yes (∃) | existential |
| h11 | cube = ∃a, n=a·a·a | VII.Def 19 | yes (∃) | existential |
| h12 | perfect = equals sum of proper divisors | VII.Def 22 | **no** (`operator:perfect`) | non-transcribable |
| h13 | even+even = even | IX.Prop 21 | yes | plain |
| h14 | odd+odd = even | IX.Prop 22 | yes | plain |
| h15 | odd+odd+odd = odd | IX.Prop 23 | yes | plain |
| h16 | even−even = even (Int) | IX.Prop 24 | yes | ambient-ambiguity |
| h17 | even−odd = odd (Int) | IX.Prop 25 | yes | ambient-ambiguity |
| h18 | odd−odd = even (Int) | IX.Prop 26 | yes | ambient-ambiguity |
| h19 | odd−even = odd (Int) | IX.Prop 27 | yes | ambient-ambiguity |
| h20 | odd×even = even | IX.Prop 28 | yes | plain |

References, verbatim quotes, licenses, and `verified_via` for every entry are in
`manifest.json`'s `holdout` array.

## 4. What this holdout can (and cannot) honestly support

* **CAN — cost measurement (WP-MET).** When a metered authoring run (the
  user-gated real-spend package) authors readings for these 20 sources, the
  per-statement authoring cost is measured on inputs the vocabulary was **not
  fit to**. This is the metered cost axis §11.7 calls VOID on the committed run.
* **CAN — out-of-sample DL, once readings exist.** After the readings are authored
  (a separate, gated step — **not done here**), pricing them under the
  main-corpus vocabulary yields a genuine **out-of-sample** `corpus_dl` slope: a
  first, honest generalization signal for the learned macros, on a
  differently-sourced, neutrally-selected set.
* **CANNOT — anything, yet.** **No readings exist for these sources.** Until they
  are authored and pass the gates, this directory supports **no** DL or reach
  claim. It is a committed, audited *input* to those future measurements, nothing
  more. Do not cite it as evidence of transfer before the metered run runs.
* **Scope caveat.** 20 readings is a small sample from a single (if canonical)
  source; a generalization claim should report it as such, and the 3
  non-transcribable entries (`prime`, `composite`, `perfect`) are part of the
  honest sample — they measure where the fragment ends, not miner failure.

## 5. Adding to the holdout (rules stay binding)

Append only (never mutate an existing `holdout` key or `.txt`). Continue the
**same neutral walk** (IX.29 onward, then the next canonical block) or open a new
source under rule (a) — a different reference work — walked by rule (b) with the
full disposition log added to §2. Every new entry carries `provenance`
(reference/url/license/verbatim/verified_via, + rendering_note if adapted) and a
`curation` block with the neutral-rule fields. Authoring readings is a separate,
later, gated step, never done in this directory.
