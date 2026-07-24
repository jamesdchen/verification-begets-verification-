# C3 cycle 02 — third census-sourced corpus batch (PLAN_FRAGMENT §3.1)

**Axis:** corpus (Lean-free; the C2 queue has transcribable math2001
candidates, so the flywheel turned on the corpus axis this cycle, per the
driver rule).  **Batch:** sources 75–78, the chapter-1 linear-calculation
family.

## The chain, end to end

1. **Corpus** (unchanged): `specs/mathsources/math2001/` — 260 nodes,
   106 attempt-candidates.  Consumed this cycle: chapter-1 "Proofs by
   Calculation" problems **007/010/011/022** (verbatim prose, byte-checked
   against `nodes.jsonl`; provenance docstring in `wp_c4_readings.py`).
   Deliberately **leaves the divisibility family (67–74) for the linear
   `+ - * = <=` calculation family**: the ch3 `dvd`-forall census candidates
   are exhausted (only ground facts 010/011/015 remain, non-forall), and a
   linear-arithmetic cluster cannot perturb the even/odd macro coverage
   invariant the `dvd` batches were shaped around — it touches neither the
   parity op-slot nor the `dvd` macros.
2. **Sources 75–78**: top-level `.txt` (verbatim) + `manifest.json` entries
   (all `plain`, `expect_transcribes: true`).  Top-level source count
   **66 → 70** (single-sourced from `registration.json`).
     * 75_solve_shift   ⟵ 007  `x+4=2 → x=-2`               (Int; solve a linear equation)
     * 76_solve_halve   ⟵ 010  `2x+3=x → x=-3`              (Int; solve a linear equation)
     * 77_solve_system  ⟵ 011  `2x-y=4, y-x+1=2 → x=5`      (Int; solve a linear system)
     * 78_square_bound  ⟵ 022  `m²+n ≤ 2 → n ≤ 2`           (Int; square-nonnegativity bound)
3. **Readings**: authored session-inline (unmetered, cost columns 0,
   `wp_c4_readings.py`), and verified TRUE by `run.formalize.certify_statement`
   over the B=8 box BEFORE authoring (never distort a reading to force a green).
   The `>`/`>=` candidates 016/021 were MEASURED to fall outside the `< <=`
   reading-gate lexicon and were NOT shipped.
4. **Certification**: `bench_formalize.run_bench` with the inline author,
   checkpoint RESUME (nothing re-authored; only the 4 new source_ids entered,
   joining the existing wave 8).  **All four certify in both bench arms.**
   Governed exogenous coverage **59 → 63**; arms reach equal coverage; governed
   reported DL 4037 ≤ ungoverned 4373.
5. **Mining**: `tools/subtree_mine.py` over the grown corpus stages **1 new
   proposal** (30 → 31; `op_6e1f7068f05d`).
6. **Admission**: `tools/admit_proposals.py` re-priced the staged pool on the
   grown corpus.  The five priced payers re-admit; **no NEW operator word
   crossed the admission bar this cycle** — recorded as honest no-delta on the
   admission axis, never silently retried or widened.  The corpus growth still
   registers as coverage (59 → 63) and as the re-priced macro economy below.

## The measured re-census delta (committed this session)

- Governed corpus DL **3801 → 4037** legacy replay / **census-of-record
  3186 → 3422** (refined+GC; the GC pass retires the congruence macro at +7,
  gc_delta −7.0: governed_dl_before_gc 3429 → after 3422).  Refined final
  table **11 macros** (governed), **9** (ungoverned); still ≤ the `max_macros`
  bar (14 = round(8/37·63)).
- Even/odd macro **survives and still covers {04_even_plus_even,
  05_odd_plus_odd}** (uses 5) — the linear-calculation batch does not perturb
  the arity-1 op-slot cluster (this is exactly why the linear-calculation
  family was chosen; it introduces no parity or `dvd` structure at all).
- Entropy references re-baselined over the grown 66-reading stream
  (order-0 DL 4085.105 → 4291.843; stream_length 1841 → 1946; alphabet
  50 → 53).  C2 report headline re-baselined (governed C2 2848.811 →
  3024.077; the honest "vocabulary does not pay under C2" finding holds:
  governed C2 3024.077 > empty-table C2 2585.837).
- `specs/mathsources/registration.json`: the ONE re-baseline point, with a
  new lineage entry (n_top_level_sources 70, governed_legacy_dl 4037).  Every
  number is reproduced live by `tests/test_corpus_registration.py`.

## Honesty notes

- No trust-root edits: `kernel/certs.py`, `TRUST.md`, the escape-gate
  blocklist, and the `.lean-pins` are untouched.  **No Lean-touching files
  changed** — this is a Lean-free corpus cycle (no `[lean-fast]` tag needed;
  the reflect/kernel layer does not move).
- The census stays a signal instrument: 106 math2001 attempt-candidates are
  candidates, nothing more; 4 more were taken through the full pipeline this
  cycle, and the queue remains open for the 24/7 cadence.
- The committed-artifact number pins that re-baseline with any corpus growth
  (entropy references + lz77/context-stats, C2 headline, cluster-key
  acceptance bars, the mined-proposal count, the shifted-KT figure fixture)
  were updated to the regenerated artifacts — measured values, no law or
  relational guarantee weakened.
- Full suite before commit: **1121 passed, 35 skipped**.
