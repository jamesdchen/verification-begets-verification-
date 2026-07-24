# C3 cycle 03 — fourth census-sourced corpus batch (PLAN_FRAGMENT §3.1)

**Axis:** corpus (Lean-free; the C2 queue has transcribable math2001
candidates, so the flywheel turned on the corpus axis this cycle, per the
driver rule).  **Batch:** sources 79–81, continuing the chapter-1/2
linear-calculation family.

## The chain, end to end

1. **Corpus** (unchanged): `specs/mathsources/math2001/` — 260 nodes,
   106 attempt-candidates.  Consumed this cycle: chapter-1 "Proofs by
   Calculation" problems **006/004** and chapter-2 "Proofs with Structure"
   problem **002** (verbatim prose, byte-checked against `nodes.jsonl`;
   provenance docstring in `wp_c5_readings.py`).  **CONTINUES the
   linear-calculation family (75–78) and nearly EXHAUSTS it** — these three
   are the remaining in-lexicon `+ - * = <=` calculation candidates; a
   linear/product cluster touches neither the parity op-slot nor the `dvd`
   macros, so the even/odd macro coverage invariant survives untouched.
2. **Sources 79–81**: top-level `.txt` (verbatim) + `manifest.json` entries
   (all `plain`, `expect_transcribes: true`).  Top-level source count
   **70 → 73** (single-sourced from `registration.json`).
     * 79_solve_subst   ⟵ 006  `a=2b+5, b=3 → a=11`          (Int; linear substitution)
     * 80_linear_le     ⟵ 002  `m+3≤2n-1, n≤5 → m≤6`         (Int; linear ≤ chaining)
     * 81_product_zero  ⟵ 004  `ad=bc, cf=de → d(af-be)=0`   (Int; product identity)
3. **Readings**: authored session-inline (unmetered, cost columns 0,
   `wp_c5_readings.py`), and verified TRUE by `run.formalize.certify_statement`
   over the B=8 box BEFORE authoring (never distort a reading to force a green).
   MEASURED and NOT shipped, recorded as first-class demand data:
     * **ch1 003** (`b²=2a², am+bn=1 → (2an+bm)²=2`): TRUE but **VACUOUS** —
       `b²=2a²` forces `a=b=0` over the integers, then `am+bn=0≠1`, so the
       hypothesis has no integer witness and the F2.1 nonvacuity gate refuses
       it (never universalised into a green).
     * **ch1 016/021, ch2 006**: `>`/`≥` conclusions outside the `< <=`
       reading-gate lexicon (same refusal class as cycle-02's 016/021).
     * **ch1 026, ch2 017**: verbatim DUPLICATES of already-shipped
       75_solve_shift / 77_solve_system.
     * **ch2 023/025/026/028, ch4/05/07 exists-class**: `there exist …`
       binders — the fragment is forall-class; existential shapes honest-skip.
4. **Certification**: `bench_formalize.run_bench` with the inline author,
   checkpoint RESUME (nothing re-authored; only the 3 new source_ids entered —
   79/80 join wave 8, 81 opens a new wave 9).  **All three certify in both
   bench arms.**  Governed exogenous coverage **63 → 66**; arms reach equal
   coverage; governed reported DL 4307 ≤ ungoverned 4639.
5. **Mining**: `tools/subtree_mine.py` over the grown corpus stages **1 new
   proposal** (31 → 32; `op_2b754c1a6cee`).
6. **Admission**: `tools/admit_proposals.py` re-priced the staged pool on the
   grown corpus.  The five priced payers re-admit; **no NEW operator word
   crossed the admission bar this cycle** — recorded as honest no-delta on the
   admission axis, never silently retried or widened.  The corpus growth still
   registers as coverage (63 → 66) and as the re-priced macro economy below.

## The measured re-census delta (committed this session)

- Governed corpus DL **4037 → 4307** legacy replay / **census-of-record
  3422 → 3692** (refined+GC; the GC pass retires one macro at +7,
  refined-greedy 3699 → after-gc 3692).  Refined final table **11 macros**
  (governed), **9** (ungoverned); still ≤ the `max_macros` bar (14 =
  round(8/37·66)).
- Even/odd macro **survives and still covers {04_even_plus_even,
  05_odd_plus_odd}** (uses 5) — the linear/product batch does not perturb the
  arity-1 op-slot cluster (this is exactly why the linear-calculation family
  was chosen; it introduces no parity or `dvd` structure at all).  The
  cluster-key measurement's six verdicts are byte-identical to the committed
  baseline (`a_beats_baseline`, `a_reproduces_census_of_record`,
  `b_evenodd_survives`, `c_no_macro_explosion`, `d_service_byte_identical`,
  `e_ungoverned_reported` all True).
- Tower census: governed max realizable macro-macro witness pair **2 → 3**,
  STILL ZERO pairs at/above the ≥7 bar — the T1 gate stays correctly deferred.
- Entropy references re-baselined over the grown 69-reading stream
  (order-0 DL 4291.843 → 4507.805; stream_length 1946 → 2065; alphabet
  53 → 57).  C2 report headline re-baselined (governed C2 3024.077 →
  3227.587; the honest "vocabulary does not pay under C2" finding holds:
  governed C2 3227.587 > empty-table C2 2756.948).
- `specs/mathsources/registration.json`: the ONE re-baseline point, with a
  new lineage entry (n_top_level_sources 73, governed_legacy_dl 4307).  Every
  number is reproduced live by `tests/test_corpus_registration.py`.

## Honesty notes

- No trust-root edits: `kernel/certs.py`, `TRUST.md`, the escape-gate
  blocklist, and the `.lean-pins` are untouched.  **No Lean-touching files
  changed** — this is a Lean-free corpus cycle (no `[lean-fast]` tag needed;
  the reflect/kernel layer does not move).
- P5 is a trust root: not executed, not touched (no promotion, no numeric
  entrance-predicate change — the cluster-key all-pass verdicts match the
  committed baseline).
- The census stays a signal instrument: 106 math2001 attempt-candidates are
  candidates, nothing more; 3 more were taken through the full pipeline this
  cycle, and the queue remains open for the 24/7 cadence.
- 81_product_zero (the 6-variable product identity) certifies TRUE over the
  B=8 box at a one-time ~130 s authoring cost; that cost is borne ONCE, into
  the committed checkpoint (regen and CI never re-certify corpus readings),
  so it is not a recurring CI burden.
- The committed-artifact number pins that re-baseline with any corpus growth
  (entropy references + lz77/context-stats, C2 headline, cluster-key baseline,
  the mined-proposal count, the tower MM-witness count, the shifted-CSV
  figure fixture's final-wave index 8 → 9) were updated to the regenerated
  artifacts — measured values, no law or relational guarantee weakened.
- Full suite before commit: **1121 passed, 35 skipped**.
