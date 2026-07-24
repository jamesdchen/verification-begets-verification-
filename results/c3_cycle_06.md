# C3 cycle 06 — sixth census-sourced corpus batch (PLAN_FRAGMENT §3.1)

**Axis:** corpus (Lean-free; `results/frontier.json` listed ready entries, so the
flywheel turned on the corpus axis per the driver rule). **Batch:** sources
**84–85** — math2001 chapter-2 "Proofs with Structure" problems **026** and
**028**, the **FIRST existential-conclusion sources** shipped in the corpus,
each discharged by the sanctioned **witness-term** form. Scheduled firing;
freshness guard passed (no open `C3 cycle…` PR; the one open PR, #41, is a
`C3 purchase…` PR on the independent purchase loop).

## The chain, end to end

1. **Orient**: brief first (`tools/session_brief.py`), lane clean, `origin/main`
   at `1a26023`. Frontier had **80 ready**; `--take 8` previewed the head.
2. **Measured every leading ready entry** with `run.formalize.certify_statement`
   (signals → verdicts; never distort a reading to force a green):

   | # | source | measured verdict |
   |---|---|---|
   | 84 | ch2 026 `∃m,n. m²−n²=2a+1` | **certifies** via witness-term `m=a+1,n=a` |
   | 85 | ch2 028 taxicab `∃a,b,c,d. a³+b³=1729=c³+d³, a≠c, a≠d` | **certifies** via witness-term `1,12,9,10` |
   | 86 | ch3 def-001 `a odd if ∃k a=2k+1` | refuse — definitional biconditional |
   | 87 | ch3 def-002 `a even if ∃k a=2k` | refuse — definitional biconditional |
   | 88 | ch3 def-003 `b dvd a (nat) if ∃c b=ac` | refuse — definitional biconditional |
   | 89 | ch3 def-004 `b dvd a (int) if ∃c b=ac` | refuse — definitional biconditional |
   | 90 | ch3 def-005 `a≡b mod n if n∣(a−b)` | refuse — definitional biconditional + mod |
   | 91 | ch3 problem-001 `7 is odd` | certifies as `odd(7)` — **PARKED** (see below) |

3. **Sources 84–85**: top-level `.txt` (verbatim, byte-checked against
   `math2001/nodes.jsonl`) + `manifest.json` entries (both `plain`,
   `expect_transcribes: true`). Top-level source count **75 → 77**
   (single-sourced from `registration.json`).
     * 84_02_proofs_with_structure_problem_026  ⟵ ch2 026
     * 85_02_proofs_with_structure_problem_028  ⟵ ch2 028

4. **What is genuinely new — and what is NOT.** This batch ships the **first
   existential-conclusion candidates** to certify, via the **witness-term**
   pattern already sanctioned by `tests/test_t6b_predecessor_int.py` ("the
   committed reading of an exists-claim is a forall with the witness supplied as
   a term, no exists binder"). The analyst discharges each existence claim
   **constructively**:
     * **84**: witnesses `m=a+1, n=a` reduce the claim to the pure ∀ identity
       `(a+1)²−a²=2a+1` over the Int carrier (true for every `a`).
     * **85**: the Hardy–Ramanujan taxicab witnesses `1,12,9,10` reduce it to a
       **ground** in-fragment conjunction `1³+12³=1729 ∧ 1729=9³+10³ ∧ 1≠9 ∧ 1≠10`
       over Nat.
   It grows **coverage only**, not the fragment: only **builtin ops** appear
   (`+ − * ^ = != and`, `^` at literal exponents 2 and 3 — `^` is a builtin term
   op, so no operator word is introduced). **No operator word, macro, or trust
   root is added.** Neither source carries parity or divisibility structure, so
   the arity-1 **even/odd op-slot** and the **dvd macros are UNTOUCHED** — the
   cluster-key verdict **b_evenodd_survives = True** (`m_f3a9880f19ae` intact).

5. **Certification**: `bench_formalize.run_bench` with the inline author
   (unmetered, cost columns 0), checkpoint **RESUME** (nothing prior
   re-authored; only the 2 new source_ids enter, both joining wave 9). Both were
   box-verified TRUE by `certify_statement` before authoring. **Both certify in
   both bench arms.** Governed exogenous coverage **68 → 70**; arms reach equal
   coverage; governed reported DL **4540** ≤ ungoverned **4883**.

6. **Mining / admission**: `tools/subtree_mine.py` + `tools/admit_proposals.py`
   re-priced the staged pool on the grown corpus. **No NEW operator word crossed
   the admission bar** — the trust anti-list never grows by economics (honest
   no-delta on the admission axis, recorded).

## MEASURED refusals — first-class demand data (committed to the ledger)

The frontier `ready` list is ordered by census signal, **not** by
transcribability. The **entire chapter-3 Parity-and-Divisibility DEFINITION
cluster** (definitions 001–005) leads the window and was **measured as refusals**
and recorded in `results/frontier_refusals.jsonl` (the cycle-05 demotion
mechanism), so the intake window can never re-wedge on them:

  * **86/87/88/89/90** → `refused:definition-biconditional`. A definition
    ("`a` is odd, *if* ∃k `a`=2k+1") states its content as a **biconditional**;
    the `and/or/implies` fragment has no `iff`. These certify **only** under a
    one-directional trivial unfolding `(∃k a=2k+1)→odd(a)` — a distortion to
    force a green (the same Euclid VII parity **definitions** "did not certify"
    for the neutral metered author). Recorded faithfully as refusals; their
    unblocking primitive is a definitional-biconditional (`iff`) purchase.
  * **90** additionally → `refused:mod-operator` (congruent-modulo names the
    modular-congruence primitive, and presupposes a nonzero modulus the fragment
    cannot express).

After demotion the frontier is **73 ready / 19 blocked groups**; the ch3
definitions are demoted into their `refused:` groups.

## PARKED (certifies but not shipped)

  * **91** ch3 problem-001 **"Show that 7 is odd"** certifies faithfully as the
    ground atom `odd(7)`. It is the **first parity reading** that would enter the
    main corpus. Cycles 02–04 deliberately kept the arity-1 even/odd op-slot out
    of the main corpus; rather than open that door **unilaterally** in an
    unattended cycle, 91 is **parked in writing** pending an explicit even/odd
    coverage decision. It is NOT recorded as a refusal (it is not one) and stays
    on the frontier. Honesty: parked items stay parked in writing.

## The measured re-census delta (committed this session)

- Counting: governed corpus DL **4374 → 4540** legacy replay / ungoverned
  **4706 → 4883**; naive (empty-table) DL **5583 → 5760**.
- Census-of-record (tower `final_tables`): governed **3759 → 3925** (11 macros),
  ungoverned **3772 → 3938** (9 macros); refined-greedy governed **3766 → 3932**.
  Still ≤ the `max_macros` bar (**15** = round(8/37·70)).
- **Even/odd macro survives** (`m_f3a9880f19ae`) — the witness-term pair
  introduces no parity structure. Cluster-key six verdicts:
  `a_beats_baseline`, `b_evenodd_survives`, `c_no_macro_explosion`,
  `d_service_byte_identical`, `e_ungoverned_reported` all True;
  `a_reproduces_census_of_record` True after the re-baseline (`all_pass`).
- Governed exogenous stream: n_readings **71 → 73**, certified **68 → 70**,
  stream_length **2097 → 2155**, alphabet **57 → 61**.
- `specs/mathsources/registration.json`: the ONE re-baseline point, with a new
  cycle-06 lineage entry (n_top_level_sources 77, governed_legacy_dl 4540,
  census-of-record 3925). Every number reproduced live by
  `tests/test_corpus_registration.py`.

## Honesty notes

- **No trust-root edits**: `kernel/certs.py`, `TRUST.md`, the escape-gate
  blocklist, and the `.lean-pins` are untouched. **No Lean-touching files
  changed** — a Lean-free corpus cycle (no `[lean-fast]` tag).
- **P5 is a trust root**: not executed, not touched (the cluster-key all-pass
  verdicts hold).
- The witness-term readings are faithful constructive discharges of the two
  existence claims (each supplies the witnesses the source asks to "show"), not
  distortions — both were box-verified TRUE before authoring.
- The ch3 definition cluster is recorded as demand data, not silently dropped;
  91 is parked, not forced green. `tools/frontier_refusals.py` gained the
  appended signal `definition-biconditional` (grow by appending, never rename).
- Committed-artifact number pins that re-baseline with corpus growth (entropy
  refs, C2 headline, cluster-key baseline, census-of-record) were updated to the
  regenerated artifacts — measured values, no law or relational guarantee
  weakened.
