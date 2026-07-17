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
| 56_parity_dichotomy | ∃ k: n = 2k ∨ n = 2k+1 | existential | Even and Odd Integers form Partition of Integers — ProofWiki (re-cited by review; see below) |
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

## Adversarial review (WP-SRC2 reviewer, on branch `wp-src2`)

Citation integrity re-verified independently by web search (direct ProofWiki/
Wikipedia fetches are blocked by this session's egress policy, so existence and
content were confirmed through the search channel). Results:

* **10 of 11 verified as-cited** — the cited page exists, states the claimed
  result, and is CC BY-SA: 52 (Archimedean property, WP), 53 (Integers under
  Addition form Abelian Group, PW), 54 (Least common multiple, WP), 55 (Group
  has Latin Square Property, PW), 57 (Congruence (Number Theory)/Integers, PW),
  58 (Integer Divisor Results/Integer Divides Zero, PW), 59 (Greatest common
  divisor, WP), 60 (GCD with Zero, PW), 61 (Square Modulo 4, PW), 62
  (Definition:Greatest Common Divisor, PW).

* **56_parity_dichotomy — citation FIXED (re-cited, not dropped).** The staged
  reference `Integer is Even or Odd`
  (`proofwiki.org/wiki/Integer_is_Even_or_Odd`) could not be verified to exist:
  across repeated searches (including domain-restricted to proofwiki.org) that
  exact page title never surfaced while its sibling pages did. Per the §11.12
  "verifiable citation" bar, an unverifiable page is a blocker. Fixed the
  proper way — re-pinned to the verifiable canonical CC BY-SA source
  **`Even and Odd Integers form Partition of Integers`**
  (`proofwiki.org/wiki/Even_and_Odd_Integers_form_Partition_of_Integers`),
  which states "every integer is even or odd, and no integer is both"; the
  witness form `n = 2k` / `n = 2k + 1` is the unfolding of Definition:Even
  Integer / Definition:Odd Integer. `verbatim`, `rendering_note`, and a new
  `verified_via` field updated accordingly. The statement itself (parity
  dichotomy) is unchanged and remains true and in-fragment.

Mathematical truth and transcribability spot-checked on all 11 (side conditions
honoured — 52 needs a>0 with b any integer over the ordered carrier: true; 55
stated over Int not Nat: true; 54 needs a,b>0: true; 60 nonnegative a so
|a|=a: true; every operator is in `generators/math_reading.py`'s lexicon /
built-ins). No duplication of the live 51 or the Euclid VII-IX holdout: 58
(n | 0), 59 (gcd commutative), 60 (gcd(a,0)=a), 62 (gcd(a,b) | a) are each
absent from and distinct from the committed corpus (62 is the converse
direction of the live 36_db_gcd, not a restatement); 56 is a theorem, not a
paraphrase of the holdout even/odd *definitions*.

The §11.12 post-promotion emptiness pin (`test_mathsources_staged.py::
test_staged_is_empty_after_promotion`) failed by design once this batch
re-filled `staged`. Resolved honestly on the branch: converted to
`test_staged_pins_wp_src2_batch`, which pins the exact WP-SRC2 staged
membership (manifest + disk) and documents the empty set as the §11.12 base
case, so the next promotion fails the pin and must update it. The bijection and
no-collision invariants remain independently enforced by the sibling tests.

Post-fix validation: `promote_sources.py --all-staged` dry-run — all 11
selected, "blockers: none recorded", zero waivers, exit 0.
`test_mathsources_staged.py` 6/6 PASS; `test_mathsources_manifest.py` 9/9 PASS
over the unchanged 51.
