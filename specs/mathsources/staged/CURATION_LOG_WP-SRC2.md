# WP-SRC2 curation log — the second staged exogenous batch (sources 52–62)

This batch re-populates `specs/mathsources/staged/` (empty since the WP-SRC
promotion, COMPRESSION.md §11.12) with **11 new exogenous, human-authored
mathematical statements** selected from public CC BY-SA references. It is
**STAGED, not promoted**: the files live under `staged/`, their entries live in
the manifest's `staged` array (never `files`), and every top-level glob
(`bench_formalize.py`, `cgb.py` `_ledger_sync`, `tests/test_mathsources_manifest.py`)
is top-level-only, so this batch is inert with respect to the frozen 40-source
bench, the ledger DL base, and the pinned `EXPECTED_TOTAL = 51` bijection.
Promotion (move to top level, `staged` → `files`, bump `EXPECTED_TOTAL`,
re-baseline bench) is the separate reviewer-gated step — **not performed here.**

## Why this batch exists

COMPRESSION.md §11.6 (WP-T6b) and §11.11 ("the 28_predecessor dissolution now
waits only on promoted existential sources"): the reach-rung needs genuine
exogenous `exists`-sources so its vacuity/witness clauses are satisfied from
files, never manufactured from `28_predecessor`'s own re-authoring. §11.12 set
the bar for a staged batch: **every source carries a genuine, verifiable
citation to one primary/standard source; ZERO waivers is the bar** (the prior
batch's only blockers were citation defects — a composed paraphrase and an
NC-licensed source — both since fixed by re-pinning, the proper path).

## Selection rules (binding, as executed)

1. **In-fragment only.** Elementary number theory over Nat/Int — divisibility,
   parity, mod/congruence, gcd, ordering, +, −, ×. Every statement's operators
   are already in the corpus's vocabulary (mirroring the live 51), so each is
   tagged `expect_transcribes: true`; the batch adds **no** `non-transcribable`
   entries (the quota is not a target).
2. **≥ 3 on the existential axis.** Five sources (52, 53, 54, 55, 56) are
   genuine `∃` statements (Archimedean-type, existence of divisors/multiples,
   Bezout/solvability-type existence), tagged `existential` + `binder_hint:
   "exists"` — the T6b witnesses §11.11 waits on.
3. **One primary/standard citation each, verified.** Every citation was checked
   against its source before staging (canonical named results / definitions on
   ProofWiki and Wikipedia, both CC BY-SA 4.0 — no NC licenses). The upstream
   statement is recorded verbatim in each manifest `staged` entry's `provenance`
   block with URL, license, and a `rendering_note` for any specialization.
4. **No duplication of the live 51 or the holdout.** Each statement is distinct
   in content from the committed corpus (checked pairwise). In particular
   `28_predecessor` already carries the `∃`-predecessor statement, so this batch
   deliberately does **not** re-state it. **No statement is drawn from or
   paraphrases Euclid's *Elements* Books VII–IX** (the `holdout/` set); the
   holdout was left byte-untouched.

## The batch

| id | statement | axis | citation (CC BY-SA) |
|----|-----------|------|---------------------|
| 52_archimedean | ∃ positive n: n·a > b (a>0) | existential, side-condition | Archimedean property — Wikipedia |
| 53_additive_inverse | ∃ m: n + m = 0 | existential | Integers under Addition form Abelian Group (inverse) — ProofWiki |
| 54_common_multiple | ∃ positive m: a\|m ∧ b\|m (a,b>0) | existential, side-condition | Least Common Multiple — Wikipedia |
| 55_solvable_addition | ∃ x: a + x = b | existential, ambient-ambiguity | Group has Latin Square Property — ProofWiki |
| 56_parity_dichotomy | ∃ k: n = 2k ∨ n = 2k+1 | existential | Integer is Even or Odd — ProofWiki |
| 57_cong_divides_diff | a≡b (mod m) → m \| (a−b) | side-condition, idiom:congruent-mod | Definition:Congruence (Number Theory)/Integers — ProofWiki |
| 58_divides_zero | n \| 0 | plain | Integer Divides Zero — ProofWiki |
| 59_gcd_commutative | gcd(a,b) = gcd(b,a) | idiom:common-divisor | Greatest Common Divisor (commutativity) — Wikipedia |
| 60_gcd_zero | gcd(a,0) = a (a≥0) | side-condition, idiom:common-divisor | GCD with Zero — ProofWiki |
| 61_square_mod_four | n·n ≡ 0 ∨ 1 (mod 4) | idiom:congruent-mod | Square Modulo 4 — ProofWiki |
| 62_gcd_divides | gcd(a,b) \| a | idiom:common-divisor | Definition:Greatest Common Divisor — ProofWiki |

Existential-axis sources: **5 of 11** (52, 53, 54, 55, 56).

## Validation performed (staging only)

* `tools/promote_sources.py --all-staged` (dry-run): all 11 selected, **"blockers:
  none recorded"** on every source, exit 0 — **zero waivers would be needed.**
* `tests/test_mathsources_staged.py` residual-staged schema/bijection/no-collision
  validators: PASS (entries well-shaped, `staged`↔`staged/*.txt` bijection holds,
  no staged id collides with a top-level slot).
* `tests/test_mathsources_manifest.py`: 9/9 PASS over the unchanged 51 top-level
  sources — the manifest `files` array, `flood_idiom`, `staged_note`, and
  `holdout` array are byte-identical to HEAD; only the `staged` array grew.

Nothing promoted; the live corpus, ledger, bench artifacts, and holdout are
byte-untouched.
