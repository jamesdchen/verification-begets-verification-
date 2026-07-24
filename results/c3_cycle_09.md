# C3 cycle 09 — the ch4 head, measured: five shipped, nine refused, one parked

**Axis:** corpus (Lean-free). **Batch:** sources **86–90** — math2001 chapter-4
"Proofs with Structure II" problems **007 / 021 / 023 / 025 / 029**. The window
cycle 08 opened was consumed in listed order; the intake window did **not**
re-wedge.

Scheduled firing; freshness guard passed (no open `C3 cycle…` PR — the one open
PR, #48, is a governance/decision-lane PR, not a cycle PR).

## What the window actually contained

Cycle 08's product was the park ledger, which moved the ch3 parity block out of
`ready` and put **`04_Proofs_with_Structure_II#definition-001`** at the head. So
this cycle is the first to measure ch4 — and ch4's head is **dominated by one
missing primitive**. Thirteen candidates were measured one at a time with
`run.formalize.certify_statement` (signals → verdicts; never distort a reading
to force a green):

| subject | measured verdict |
|---|---|
| definition-001 `sufficiently large` | refuse — definitional biconditional **over a property variable** |
| lemma-003 `even iff not odd` | refuse — `iff`, and `not` |
| lemma-004 `odd iff not even` | refuse — `iff`, and `not` |
| problem-002 `factor of every m ⟹ n=1` | refuse — the hypothesis carries its own binder |
| **problem-007** `eventually n³ ≥ 4n²+7` | **certifies** (witness N=5) |
| problem-011 `8∣5n iff 8∣n` | refuse — `iff` |
| problem-012 `odd iff ≡1 mod 2` | refuse — `iff` |
| problem-013 `even iff ≡0 mod 2` | refuse — `iff` |
| problem-015 `a²−5a+5 ≤ −1 iff a ∈ {2,3}` | refuse — `iff` |
| problem-016 `n²−10n+24=0 ⟹ n even` | certifies — **PARKED** (see below) |
| **problem-021** `∃! r. 0≤r<5 ∧ 14≡r mod 5` | **certifies** (witness 4 + uniqueness) |
| problem-022 `t<3 ∧ t−1=6 ⟹ t=13` | refuse — nonvacuity gate: hypotheses contradictory |
| **problem-023 / 025 / 029** | **certify** |

**The headline demand signal: `iff`.** Six of thirteen ch4 subjects are blocked
by the biconditional alone, and the fragment's `_CONNECTIVES` is exactly
`{and, or, implies}`. That is the single largest named demand this corpus has
produced in one cycle, and it now sits in the frontier as
`refused:iff-connective` (6 nodes) where a purchase can find it.

## What shipped (sources 86–90)

* **86 ← problem-007.** "For all *sufficiently large* integers n, n³ ≥ 4n²+7."
  `sufficiently large` is ch4 definition-001 — which this same cycle refused.
  The reading does not need it: the outer existential is discharged
  **constructively in the sanctioned witness-term form** (T6b), supplying
  **N := 5**, leaving the pure ∀ statement `5 ≤ n → 4n²+7 ≤ n³`. N=5 is tight
  (at n=4, 4·16+7 = 71 > 64). `≥` is written as the `≤` the atom lexicon has,
  arguments swapped — notation, not semantics.
* **87 ← problem-021.** The corpus's **first exists-unique source**. Both halves
  are stated, and that is the whole point: existence as the ground conjunction
  at the supplied witness `r := 4`, uniqueness as the universally-quantified
  `implies`. A uniqueness half alone would hold **vacuously** and would be the
  distortion.
* **88 ← problem-023.** A mod-3 congruence case split — the source's own `or`,
  in fragment. Each congruence is residue equality via the grammar's `mod` term
  word (the reading `wp_auth_readings.py` already uses).
* **89 ← problem-025.** A genuinely **nonlinear Nat** theorem with no witness and
  no case split: the smallest leg of a Pythagorean triple is at least 3.
* **90 ← problem-029.** "There does **not** exist a natural n with n²=2" read as
  the De Morgan dual `∀n. n² ≠ 2` — the one negation shape statable **without**
  the `not` connective the fragment lacks. Faithful, not a workaround: the two
  are the same proposition.

All five were box-verified TRUE **before** authoring, and **all five certify in
both bench arms** via the inline-author checkpoint resume (all join a new
**wave 10**). Governed exogenous coverage **70 → 75**; readings **73 → 78**.

## MEASURED — a new operator word admitted itself

**`op_952a9f1c65b2` — the arity-1 positivity template `1 ≤ v0` — crossed the
two-witness admission bar and admitted through the priced R2 batteries.** Its
two witnesses are `67_nat_pred_witness` and the **new** source 89, whose
"positive natural numbers" is read as `1 ≤ a/b/c`. It is the sibling of
`op_3c0de4c8920b` (nonnegativity, `0 ≤ v0`), which admitted the same way at
cycle 06.

Stated plainly, because it is the flywheel's whole thesis and also its sharpest
honesty test: **the corpus batch is what admitted the word.** Had 89 been
written `0 < a` instead of `1 ≤ a` — equivalent over Nat — the template would
have stayed at one witness. `1 ≤ a` is the faithful reading of "positive", so it
is what was authored; the admission is the *measured consequence*, not an
engineered one, and it is recorded rather than avoided. An operator **word**
admitting through its batteries is not a trust-root change:
`buildloop/growth_protocol.py::ANTI_LIST` is untouched, as are `kernel/certs.py`,
`TRUST.md`, and the escape-gate blocklist. Proposals **33 → 34**, admitted
**5 → 6** payers (plus grandfathered `multiple_of`).

## MEASURED refusals — eleven rows, nine subjects, four new signals

Recorded in `results/frontier_refusals.jsonl` (rows 16 → 27) and demoted by the
regen chain into `refused:` groups:

| signal | subjects |
|---|---|
| `iff-connective` **(new)** | lemma-003, lemma-004, problems 011, 012, 013, 015 |
| `not-connective` **(new)** | lemma-003, lemma-004 |
| `predicate-variable` **(new)** | definition-001 |
| `hypothesis-quantifier` **(new)** | problem-002 |
| `definition-biconditional` | definition-001 |
| `nonvacuity` | problem-022 |

The four appended signals grow the vocabulary by **appending, never renaming**
(the cycle-06 precedent), and each names a **distinct** missing primitive rather
than being a synonym of an existing one:

* `iff-connective` is deliberately kept apart from `definition-biconditional`.
  The latter stays reserved for **definitions**, whose *content* is the
  biconditional; the new one names a lemma or problem that merely **states**
  one. Same purchase, different subject kind — the rows must never claim a
  definition where the source has a theorem.
* `hypothesis-quantifier` is not a stylistic complaint. Problem-002's faithful
  hypothesis is `∀m. n ∣ m`; the fragment's binders are top-level, and
  flattening it moves the binder out of the hypothesis and states a **false**
  theorem — measured, refuted at `n=0, m=0`.

**A refusal NOT recorded, and why:** `mod` was measured **in fragment** (it is a
`MATH_OPERATORS` term word, and the one-directional form of problem-012
certifies with it). So problems 012/013 are blocked by **`iff` alone** and carry
no `mod-operator` row. Two such rows were written earlier in this session on the
presumption and were **removed before commit** — a refusal signal that no
measurement supports is not evidence, it is noise.

## PARKED (certifies but not shipped)

**problem-016** — "`n²−10n+24 = 0` ⟹ `n` is even" — **certifies faithfully**.
Its conclusion is the arity-1 parity atom `even(n)`: exactly the material the
**still-open cycle-06 even/odd coverage decision** holds. It joins that park
(`results/frontier_parks.jsonl`, reason `evenodd-coverage-decision`, 18 → 19
subject rows / 20 → 21 nodes) rather than opening the deliberately-closed
op-slot unilaterally in an unattended cycle.

**The decision remains open and is unchanged by this cycle.** It now holds back
one more certifying source than it did yesterday — which is the honest cost of
leaving it open, stated so it is visible, not an argument for either answer.

## Re-census delta (committed this session)

- Counting: governed corpus DL **4540 → 5007** legacy replay / ungoverned
  **4883 → 5372**; naive **5760 → 6275**.
- Census-of-record (tower `final_tables`): governed **11 → 12** macros at
  **3925 → 4380**; ungoverned **9 → 10** at **3938 → 4252**; refined-greedy
  governed **3932 → 4387**. Still ≤ the `max_macros` bar (**16** = round(8/37·75)).
- **Even/odd macro survives** (`b_evenodd_survives = True`) — none of the five
  carries parity or divisibility structure. Cluster-key: **all six verdicts
  True** (`all_pass`) after the re-baseline.
- Governed exogenous stream: n_readings **73 → 78**, certified **70 → 75**,
  stream_length **2155 → 2331**, alphabet **61 → 64**.
- `specs/mathsources/registration.json`: the ONE re-baseline point, with a new
  cycle-09 lineage entry (n_top_level_sources **82**, governed_legacy_dl
  **5007**, census-of-record **4380**). Every number reproduced live by
  `tests/test_corpus_registration.py`.
- Frontier: **ready 43 → 37**, blocked groups **24**; `derived_from` now carries
  `frontier_refusals_rows: 27`, `frontier_parks_rows: 19`.

## A measured flip worth naming

`tests/test_rung_registry.py::test_pilot_rung_refused_on_real_corpus`: the §11.5
pilot commutativity-sort rung is **still refused**, and stays proposed. But on
this corpus its canonicalization **finally saves something — 4.0 bits** — where
on every smaller corpus it saved nothing at all. The refusal is untouched by
that: the rung's own model costs **2748.0** bits, so the net stays decisively
positive (+2744). Recorded because it moved, not because it decides. A primitive
ladder rung is on the ANTI_LIST; it was not admitted, promoted, or touched.

## Honesty notes

- **No trust-root edits**: `kernel/certs.py`, `TRUST.md`, the escape-gate
  blocklist, `buildloop/growth_protocol.py::ANTI_LIST`, and the `.lean-pins` are
  untouched. **No Lean-touching files changed** — a Lean-free corpus cycle (no
  `[lean-fast]` tag).
- **P5 is a trust root**: not executed, not touched.
- The park does not make the decision it waits on, and this cycle did not
  overturn, pre-empt, or narrow it.
- Source 90 (`∀n:Nat. n² ≠ 2`) restates content the maintainer-authored
  `83_sq_ne_two_int` already carries over Int. Different source text, different
  carrier, distinct census provenance — noted rather than hidden, since the
  miner will see the two as near-siblings.
- Committed-artifact number pins that re-baseline with corpus growth (entropy
  refs, C2 headline, cluster-key baseline, census-of-record, the two synthetic
  figure fixtures whose fabricated values are chosen *relative* to the real
  refs) were updated to the regenerated artifacts — measured values, no law or
  relational guarantee weakened.
- **Carried-over demand: 37 ready entries unconsumed.** The cap was never
  widened; 13 of the window's subjects were measured and 5 shipped, which is the
  batch ceiling doing its job, not a shortfall.

## Status

- Corpus **77 → 82 sources**, 78 governed readings, **75 certified**.
- Full suite: **1234 passed, 35 skipped**.
- `merge_to_next_start_s = 69` — cycle 08 merged 18:59:36Z, this session started
  19:00:45Z. Merge-event chaining fires.
