# C3 cycle 28 — the corpus's first named set, and two subjects blocked by something no purchase can sell

**Product: one certified corpus source and three measured refusals.**  Four
subjects taken by `intake_from_frontier --unblocked refused:set-membership
--take 8` — every subject P9 paid for — every one measured, **one certified and
shipped**.  Corpus **124 → 125** top-level sources, governed readings **120 →
121**, certified **117 → 118**, governed DL **7152.0 → 7195.0**.

This is the first take against P9's row, and the first cycle to spend the
`refused:set-membership` supply that purchase bought.

## The selection was the whole returnable set, not a slice of it

The brief's derived `NEXT-SELECTION` printed `unblocked` with **six** signals.
Running each shows they name **four distinct subjects between them**, and one
command reaches all four:

| printed signal | selects | why |
|---|---|---|
| `refused:definition-biconditional` | 1 | `09_Sets#definition-003` (also in set-membership) |
| `refused:function-symbol` | 0 | *"refills NOTHING — all 16 nodes held by an unmet signal"* |
| `refused:iff-connective` | 1 | `09_Sets#problem-014`; its other 6 are already intaken (cycle 16) |
| `refused:not-connective` | 3 | subset of set-membership + one already intaken |
| **`refused:set-membership`** | **4** | **the superset — all four paid subjects** |
| `refused:symbolic-exponent` | 0 | its 3 returnable subjects are already intaken (cycle 27) |

So `--take 8` was never the binding constraint: **the paid supply is four**,
and the `awaiting_unblock_run` figure of 14 is an upper bound over subjects
that the already-intaken filter and the per-subject precedence then reduce.
That gap is the projection behaving exactly as its own honesty note says.

## What landed

Source 133 is the verbatim prose of `09_Sets#problem-017` and is **the
corpus's first reading to name a set**:

```
Show that \(\{n:\mathbb{N}\mid n\text{ is even}\}\notin\{s:\mathcal{P}(\mathbb{N})\mid 3 ∈s\}\).
```

read as a real `setdef` (`a := {k | even k}`) plus the `mem` atom:
`not (3 ∈ a)`.  Gate OK, box TRUE, non-vacuous; **certified in both bench
arms** via the inline-author checkpoint resume, joining wave 15.

**The one hand step is declared, not hidden.**  The source's OUTER set is a
powerset comprehension whose parameter ranges over sets — that is
`set:set-valued-param`, explicitly what P9 does *not* buy.  Its membership is
taken at a **literal** set, so it unfolds definitionally in one step
(`{n | even n} ∈ {s | 3 ∈ s}` **is** `3 ∈ {n | even n}`); the reading takes
that step by hand and states the remainder in the vocabulary P9 did buy.

**What the green is and is not.**  It is strictly more than source 125's fully
flattened `not (odd 10)` (cycle 16) — the inner comprehension survives as a
first-class `setdef`, which is the delta P9 bought.  It is **not** evidence of
set coverage: cycle 16 recorded that a green reached through a literal-set
unfolding is coverage, and `tests/test_set_object_class.py` (4) said the same
about this subject in advance.  The tower-class residue `refusal-set-carrier`
stays open and priced, untouched by this reading.

## The headline: a refusal group coarser than its blocker

The other three are where the cycle's real finding is, and **two of them are
not blocked by missing vocabulary at all**.

| node | verdict | measured by | signal |
|---|---|---|---|
| `09_Sets#definition-003` | `object type 'Set Int' is outside the carrier whitelist ('Nat', 'Int', 'Rat')` | the **gate** | `free-set-variable` |
| `09_Sets#problem-014` | gate OK; **REFUTED at n = −1, n = −3** | the **evaluator** | `carrier-mismatch` |
| `09_Sets#problem-015` | gate OK; **REFUTED at n = 1** | the **evaluator** | `refuted-as-stated` |

`#definition-003` is the row's own forecast landing correct: it defines
intersection over two *arbitrary* sets `U`, `V` with no comprehension to
substitute, so its membership survives unfolding.  That is the tower-class
residue, priced under `free-set-variable` before this cycle ran.

**The other two gate cleanly and are refused by the box.**  Both state a
relation between a comprehension over ℤ and one over ℕ, and the fragment reads
one carrier per reading.  Both in-fragment readings were written and run:

* **`#problem-014`** (`{n:ℤ | n even}ᶜ = {n:ℕ | n odd}`).  Read **faithfully**,
  with ℕ as the non-negative part of ℤ — the only way to keep both of the
  source's carriers in one reading — it is **REFUTED at n = −1 and n = −3**:
  −1 is a non-even integer that is not an odd *natural*.  Read **collapsed** to
  one carrier it is **TRUE**, but the collapse deletes the very ascription the
  source wrote.
* **`#problem-015`** (`{n:ℤ | n ≡ 1 mod 5} ∩ {n:ℕ | n ≡ 1 mod 5} = ∅`).
  **REFUTED at n = 1 under *both* readings** — 1 satisfies both comprehensions
  either way, so the intersection is inhabited and the claimed emptiness fails.

**`#problem-015` is what makes this a measurement rather than a preference.**
The two subjects carry the *identical* ℤ/ℕ mismatch, and the collapse that
rescues `#014` leaves `#015` refuted.  So the collapse is **not a safe
normalisation** — its truth-preservation is subject-dependent.
`tests/test_set_object_class.py` (3) had already named reading at a single
carrier as "a CHOICE a corpus cycle must make and defend"; cycle 28 declines to
make it, and files the demand instead of quietly normalising.

Two new signals, kept **apart** for that reason:

* **`carrier-mismatch`** — a **decision**, not a bill.  What stands between the
  subject and a reading is whether a carrier ascription in extracted prose may
  be normalised away.  Purchase-axis for nobody; decision-axis for the
  maintainer.
* **`refuted-as-stated`** — a **truth fact**, which is demand for no primitive.
  The claim is false under every in-fragment reading, so no purchase on this
  board or any future one returns the subject.

**This is cycle 26/27's finding from the other side.**  There a purchase *word*
was coarser than the purchase (`function-symbol` covered three rungs;
`symbolic-exponent` covered two carriers).  Here a **refusal group** was
coarser than its blocker: `set-membership` promised a return for two subjects
no set purchase was ever going to reach — one of which is simply false.  A
signal is a promise about which purchase returns a subject, and the promise is
only as good as the reason underneath it.

## Delta

* Corpus **124 → 125** sources; governed readings **120 → 121**, certified
  **117 → 118**.
* Governed DL **7152.0 → 7195.0**, ungoverned **7571.0 → 7614.0** — both
  reproduced live from `results/formalize_governed.csv`; governed ≤ ungoverned
  holds.  Final-wave gaps **unchanged** at hindsight −419.0 / prequential
  −299.0.
* Census of record re-registered off `tools/measure_cluster_key.py
  --print-reregistration`: governed **6493.0 → 6536.0** (13 macros), ungoverned
  **6274.0 → 6317.0** (14 macros), refined-greedy **6500.0 → 6543.0**,
  `accept_max_dl` **7166.0**, `max_macros` **26**.
* Ledger: blocked groups **46 → 49**, memberships **118 → 122**,
  `awaiting_unblock_run` **14 → 10**.  Ready stays **11**; supply verdict stays
  `ready-work-available`.
* Operator axis: the miner stages 54 proposals over the grown corpus; **no new
  word crossed the admission bar** — an honest no-delta, recorded.

## Bounds

* Probe verdict **`lean-local`**, run in this container, not read off disk.
  The cycle is **Lean-free** regardless: no `[lean-fast]` commit, no edit to
  `tools/FgReflect.lean`, `results/reflect_candidates.json` untouched.
* P5 not promoted; `kernel/certs.py`, `TRUST.md` and the escape-gate blocklist
  untouched; no park lifted and no park row removed; both ledgers append-only.
* The three refused subjects' laid-down source files were **removed** — a
  refused subject is demand data, never a corpus source.
* Gate: `CGB_LEAN=0 python3 -m pytest tests/ -q` → **1929 passed, 43 skipped**.
* Derived pins re-baselined from live artifacts, each with its finding
  re-asserted as a relation rather than left implicit in a moved number:
  registration (sources / DLs / stream shape / naive_dl / census-of-record),
  entropy order-0, LZ77 and context-stat columns, and the c2 headline (the
  vocabulary still does not pay under C2; the governance ranking still does not
  hold under C2).
