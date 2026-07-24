# C3 cycle 01 — second census-sourced corpus batch (PLAN_FRAGMENT §3.1)

**Axis:** corpus (Lean-free; the C2 queue has transcribable math2001
candidates, so the flywheel turned on the corpus axis this cycle, per the
driver rule).  **Batch:** sources 71–74, the divisibility family.

## The chain, end to end

1. **Corpus** (unchanged): `specs/mathsources/math2001/` — 260 nodes,
   106 attempt-candidates.  Consumed this cycle: chapter-3 divisibility
   problems **017/026/027/028** (verbatim prose, byte-checked against
   `nodes.jsonl`; provenance docstring in `wp_c3_readings.py`).  Deliberately
   the **divisibility family** (arity-2 `dvd`), sibling to the C2 batch
   67–70 — NOT the arity-1 even/odd op-slot, so the census-of-record even/odd
   macro coverage invariant is left undisturbed.
2. **Sources 71–74**: top-level `.txt` (verbatim) + `manifest.json` entries
   (all `plain`, `expect_transcribes: true`).  Top-level source count
   **62 → 66** (single-sourced from `registration.json`).
     * 71_dvd_pos     ⟵ 017  `0<b, a∣b → 0<a`      (Nat; companion to 70)
     * 72_dvd_cancel8 ⟵ 026  `8∣5n → 8∣n`          (Int; coprime cancel)
     * 73_dvd_cancel5 ⟵ 027  `5∣3n → 5∣n`          (Int; coprime cancel)
     * 74_dvd_both    ⟵ 028  `8∣m, 5∣m → 40∣m`     (Int; divides-both / lcm)
3. **Readings**: authored session-inline (unmetered, cost columns 0,
   `wp_c3_readings.py`), and verified TRUE by `run.formalize.certify_statement`
   over the B=8 box BEFORE authoring (never distort a reading to force a green).
4. **Certification**: `bench_formalize.run_bench` with the inline author,
   checkpoint RESUME (nothing re-authored; only the 4 new source_ids entered,
   in a new wave 8).  **All four certify in both bench arms.**  Governed
   exogenous coverage **55 → 59**; arms reach equal coverage; governed
   reported DL 3801 ≤ ungoverned 4115.
5. **Mining**: `tools/subtree_mine.py` over the grown corpus stages **2 new
   proposals** (28 → 30).
6. **Admission**: `tools/admit_proposals.py` re-priced the staged pool on the
   grown corpus.  The five priced payers re-admit; **no NEW operator word
   crossed the admission bar this cycle** — recorded as honest no-delta on the
   admission axis, never silently retried or widened.  The corpus growth still
   registers as coverage (55 → 59) and as the re-priced macro economy below.

## The measured re-census delta (committed this session)

- Governed corpus DL **3417 → 3801** legacy replay / **census-of-record
  3010 → 3186** (refined+GC; the GC pass retires the congruence macro at +7,
  gc_delta −7.0).  Refined final table **9 → 11 macros** (governed),
  **8 → 9** (ungoverned); still ≤ the `max_macros` bar (13 = round(8/37·59)).
- Even/odd macro **survives and still covers {04_even_plus_even,
  05_odd_plus_odd}** (uses 5) — the divisibility batch does not perturb the
  arity-1 op-slot cluster (this is exactly why the divisibility family was
  chosen over the arity-1 parity candidates, whose batch was measured to
  displace that coverage and was NOT shipped).
- Entropy references re-baselined over the grown 62-reading stream
  (order-0 DL 3954.17 → 4085.105; stream_length 1748 → 1841; alphabet
  46 → 50).  C2 report headline re-baselined (governed C2 2737.614 →
  2848.811; the honest "vocabulary does not pay under C2" finding holds).
- `specs/mathsources/registration.json`: the ONE re-baseline point, with a
  new lineage entry (n_top_level_sources 66, governed_legacy_dl 3801).  Every
  number is reproduced live by `tests/test_corpus_registration.py`.

## Honesty notes

- No trust-root edits: `kernel/certs.py`, `TRUST.md`, the escape-gate
  blocklist, and the `.lean-pins` are untouched.  **No Lean-touching files
  changed** — this is a Lean-free corpus cycle (no `[lean-fast]` tag needed;
  the reflect/kernel layer does not move).
- The census stays a signal instrument: 106 math2001 attempt-candidates are
  candidates, nothing more; 4 were taken through the full pipeline this cycle,
  and the queue remains open for the 24/7 cadence.
- The committed-artifact number pins that re-baseline with any corpus growth
  (cluster-key gc magnitudes, entropy references, C2 headline, the final-wave
  index) were updated to the regenerated artifacts — measured values, no law
  or relational guarantee weakened.
- Full suite before commit: **1121 passed, 35 skipped**.
