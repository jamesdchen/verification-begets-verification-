# C3 cycle 04 — fifth census-sourced corpus batch (PLAN_FRAGMENT §3.1)

**Axis:** corpus (Lean-free; `results/frontier.json` lists ready entries, so the
flywheel turned on the corpus axis this cycle per the driver rule).  **Batch:**
sources 82–83 — the identical surface sentence **`n^2 != 2`** over the **Nat**
carrier (82) and the **Int** carrier (83).  **FORCE** firing: the freshness
guard was skipped by payload override; the lane was independently clean (no open
`C3 cycle…` PR, main CI green).

## The chain, end to end

1. **Corpus** (unchanged): `specs/mathsources/math2001/` — 260 nodes,
   106 attempt-candidates.  Consumed this cycle: chapter-2 "Proofs with
   Structure" problems **013** (natural-number `n`) and **016** (integer `n`),
   verbatim prose byte-checked against `nodes.jsonl`
   (`sha256 bfff5a8…` / `1b7065…`; provenance docstring in `wp_c6_readings.py`).
2. **Sources 82–83**: top-level `.txt` (verbatim) + `manifest.json` entries
   (both `plain`, `expect_transcribes: true`).  Top-level source count
   **73 → 75** (single-sourced from `registration.json`).
     * 82_sq_ne_two_nat  ⟵ ch2 013  `n : Nat, n^2 != 2`
     * 83_sq_ne_two_int  ⟵ ch2 016  `n : Int, n^2 != 2`
3. **What is genuinely new — and what is NOT.**  This batch ships the **FIRST
   `!=` (`\ne`) conclusion** to certify in the corpus.  It grows COVERAGE only,
   not the fragment: `!=` is already a **builtin atom**
   (`generators/math_reading.py::_BUILTIN_ATOM_OPS = {"=", "!=", "<=", "<"}`,
   compiled to `≠`, mirrored by eval/SMT), and the squared term is the
   **already-admitted squaring template** `^(v0, 2)` (op_34e1b706c47c, the C2
   closure).  **No operator word, macro, or trust root is added.**  The Nat/Int
   pair deliberately exercises the ambient-carrier axis on one sentence — the
   exact Nat-vs-Int contrast the fragment is built to keep honest — and carries
   no parity or divisibility structure, so the arity-1 even/odd op-slot and the
   `dvd` macros are UNTOUCHED.
4. **Certification**: `bench_formalize.run_bench` with the inline author
   (unmetered, cost columns 0), checkpoint RESUME (nothing prior re-authored;
   only the 2 new source_ids enter, both joining wave 9).  Both were verified
   TRUE over the B=8 box by `run.formalize.certify_statement` before authoring
   (never distort a reading to force a green).  **Both certify in both bench
   arms.**  Governed exogenous coverage **66 → 68**; arms reach equal coverage;
   governed reported DL **4374** ≤ ungoverned **4706**.
5. **Mining**: `tools/subtree_mine.py` over the grown corpus stages **1 new
   proposal** (32 → 33; `op_567f9f98659b`).
6. **Admission**: `tools/admit_proposals.py` re-priced the staged pool on the
   grown corpus.  The five priced payers re-admit; **no NEW operator word
   crossed the admission bar** — the `admitted.json` word set is byte-identical
   (honest no-delta on the admission axis, never retried or widened; the trust
   anti-list never grows by economics).

## MEASURED and NOT shipped (first-class demand data)

The frontier's `ready` list is ordered by census signal, **not** by
transcribability, so the first six ready entries this cycle are all refusals.
They are recorded here, NOT minted as sources (the manifest partition pins
EXACTLY 4 `non-transcribable` files to named miss-kinds; a refused candidate is
never universalised into a green):

  * **82_edge_disjoint** (equational_theories, `L_y x = L_z x ⇒ L_y^n x =
    L_z^n x`): a free function symbol `L` and a symbolic iteration exponent `n`
    — out of the Nat/Int arithmetic fragment (no function carriers, no
    symbolic-bound power; the `bigop:symbolic-bound` frontier P1 named).
  * **83_fermats_little** (formal_book, `a^{p-1} ≡ 1 (mod p)`): modular
    congruence AND a symbolic exponent — neither `mod` nor symbolic-bound `^`
    is in the fragment.
  * **ch1 003** (`b²=2a², am+bn=1 → (2an+bm)²=2`): TRUE but **VACUOUS** over the
    integers — `b²=2a²` forces `a=b=0`, then `am+bn=0≠1`, so the hypothesis has
    no integer witness and the F2.1 nonvacuity gate refuses it (same verdict
    cycle-03 measured).
  * **ch1 016/021, ch2 006** (`y>3`, `n²>2n+11`): `>`/`≥` conclusions outside
    the `< <=` atom lexicon (`_BUILTIN_ATOM_OPS` has `<`,`<=` and NOT `>`,`≥`).

**Frontier-generation observation (carried, not fixed here):** because the ready
list is not ordered by transcribability and refusals are not fed back into
`blocked`, these six re-appear at the head of the ready list every cycle.  A
corpus cycle intakes only what transcribes; teaching the frontier to demote
measured refusals is a tooling change for a separate cycle, noted so the
recurrence is data, not a silent drop.

## The measured re-census delta (committed this session)

- Counting: governed corpus DL **4307 → 4374** legacy replay / ungoverned
  **4639 → 4706**; naive (empty-table) DL **5503 → 5583**.
- Census-of-record (tower `final_tables`): governed **3692 → 3759** (11 macros),
  ungoverned **3703 → 3772** (9 macros); refined-greedy governed **3699 →
  3766**.  Still ≤ the `max_macros` bar (now **15** = round(8/37·68)).
- **Even/odd macro survives** (`m_f3a9880f19ae`, uses 5, still covers
  {04_even_plus_even, 05_odd_plus_odd}) — the `n²≠2` pair introduces no parity
  structure.  The cluster-key six verdicts are all True
  (`a_beats_baseline`, `a_reproduces_census_of_record`, `b_evenodd_survives`,
  `c_no_macro_explosion`, `d_service_byte_identical`, `e_ungoverned_reported`);
  `all_pass=True` after re-baseline.
- Tower census: governed max realizable macro-macro witness pair still **3**,
  STILL ZERO pairs at/above the ≥7 bar — the T1 gate stays correctly deferred.
- Entropy references re-baselined over the grown 71-reading stream (order-0 DL
  **4507.805 → 4582.092**; stream_length **2065 → 2097**; alphabet 57;
  lz77 z-phrases **452 → 458**).  C2 report headline re-baselined (governed C2
  **3227.587 → 3271.986**); the honest "vocabulary does not pay under C2"
  finding holds (governed 3271.986 > empty-table 2797.880).
- `specs/mathsources/registration.json`: the ONE re-baseline point, with a new
  cycle-04 lineage entry (n_top_level_sources 75, governed_legacy_dl 4374,
  census-of-record 3759).  Every number is reproduced live by
  `tests/test_corpus_registration.py`.

## Honesty notes

- **No trust-root edits**: `kernel/certs.py`, `TRUST.md`, the escape-gate
  blocklist, and the `.lean-pins` are untouched.  **No Lean-touching files
  changed** — a Lean-free corpus cycle (no `[lean-fast]` tag; the reflect/kernel
  layer does not move).
- **P5 is a trust root**: not executed, not touched (no promotion, no numeric
  entrance-predicate change — the cluster-key all-pass verdicts hold).
- The census stays a signal instrument: 106 math2001 attempt-candidates are
  candidates, nothing more; 2 more were taken through the full pipeline this
  cycle and shipped, 6 were measured as refusals, the queue remains open for the
  24/7 cadence.
- Both `n²≠2` readings certify TRUE over the B=8 box at essentially zero
  authoring cost (simple atomic readings), borne once into the committed
  checkpoint (regen and CI never re-certify corpus readings).
- Committed-artifact number pins that re-baseline with corpus growth (entropy
  refs + lz77/context-stats, C2 headline, cluster-key baseline, the
  mined-proposal count) were updated to the regenerated artifacts — measured
  values, no law or relational guarantee weakened.
- Full suite before commit: **1159 passed, 35 skipped**.
