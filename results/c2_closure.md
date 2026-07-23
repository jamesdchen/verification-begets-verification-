# C2 closure — the first census-sourced mined template (PLAN_FRAGMENT §3)

**Done-predicate:** *first mined template whose source is a census
attempt-candidate (not a hand-authored reading).*  **MET.**

## The chain, end to end

1. **Corpus** (C1 continuous): `specs/mathsources/math2001/` — The Mechanics
   of Proof (H. Macbeth), 260 nodes via the new Sphinx intake adapter
   (`tools/sphinx_extract.py`), per-page SHA-256 committed.  Census:
   **106 attempt-candidates** — the first corpus whose candidates genuinely
   transcribe (elementary parity/divisibility/congruence over Nat/Int).
2. **Sources 67-70**: the VERBATIM prose of four census attempt-candidates
   (chapter 3 divisibility problems 012/013/014/016 — provenance in
   `wp_c2_readings.py`), intaken as top-level corpus sources
   (`manifest.json`, quota test 55 → 59).
3. **Readings**: authored session-inline (unmetered, cost columns 0), gate-
   checked, and verified TRUE by exhaustive B=8 box sweep before authoring.
4. **Certification**: `bench_formalize.run_bench` with the inline author,
   checkpoint RESUME (nothing re-authored; the S4a' sources 63-66 entered in
   the same run — 64/65 certify, 63/66 refuse honestly at the bound edge).
   **All four census-sourced readings certify in both arms.**
5. **Mining**: `tools/subtree_mine.py` over the grown corpus (52 certified
   exogenous readings) emits 8 NEW proposals.  The headline:

   > **`op_34e1b706c47c` — the squaring template `^(v0, 2)`** — witnesses
   > `16_square_nonneg`, **`67_square_dvd_shift`**, **`68_square_dvd_chain`**.

   Before this cycle the shape had ONE witness (16, hand-authored) — below
   the miner's two-witness bar, never emitted.  The census-sourced readings
   are **load-bearing**: the template exists because real human math from
   the census crossed the threshold.  Two of its three witnesses are census
   attempt-candidates.
6. **The flywheel turned all the way**: the admission runner
   (`tools/admit_proposals.py`) re-priced the staged pool on the grown
   corpus and **admitted a fifth operator word** — `op_3c0de4c8920b`
   (nonnegativity, `0 <= v0`), itself one of the 8 newly mined proposals —
   through the full R2 batteries.  Census-sourced math grew the certified
   corpus, the corpus grew the mined vocabulary, the batteries admitted the
   payer.

## Honesty notes

- The downstream committed artifacts (tower census, entropy/ppm/C2-report
  references, cluster-key measure, figures, dashboard) were regenerated in
  this same session; number-pins re-baselined per each harness's own
  re-registration law (cluster-key: third re-registration, 46 → 52
  certified).  The §13.2 holdout-transfer experiment is PRE-registered and
  is NOT re-registered: its frozen-table reconstruction now replays the
  registered 51-source slice explicitly (`REGISTERED_MAX_STEM`).
- 63/66 refusing at the bound edge is the conservative over-refusal policy
  working, recorded not hidden.
- The census stays a signal instrument: 106 attempt-candidates in math2001
  are candidates, nothing more; 4 were taken through the full pipeline this
  cycle, and the queue remains open for the 24/7 cadence (C3).
