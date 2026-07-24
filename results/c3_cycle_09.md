# C3 cycle 09 — seventh census-sourced corpus batch (PLAN_FRAGMENT §3.1)

**Axis:** corpus (Lean-free; `results/frontier.json` listed 53 ready entries, so
the flywheel turned on the corpus axis per the driver rule). **Batch:** sources
**86–90** — math2001 chapter-4 "Proofs with Structure II" problems **007**,
**023**, **025**, **029** and **030**. Scheduled firing; freshness guard passed
(no open `C3 cycle…` PR; the one open PR, #49, is a `C3 purchase…` PR on the
independent purchase loop, which never blocks this one).

## The batch's finding: the ch4 residue that *looks* out of reach and is not

Cycle 08 un-wedged the intake window and left the ch4 block at the head. Read by
its census signals, that block looks like a wall of un-transcribable shapes:
eventually-quantifiers, "if and only if", "there does not exist", "congruent
modulo". **Measurement splits it cleanly in two.** Three of those shapes are
already in the fragment once the reading is faithful; one genuinely is not:

| shape | in the fragment? | how |
|---|---|---|
| eventually-claim ("for all sufficiently large *n*") | **yes** | supply the THRESHOLD as a term — the T6b witness-term move sources 84–85 made for existence (86) |
| negated existential ("there does not exist *n* with…") | **yes** | it is a universal **inequality**; the frozen `!=` atom states it with no negation connective and no exists binder (89, 90) |
| modular residue ("≡ 1 mod 3") | **yes** | `mod` is an already-admitted operator word (87, 90) |
| biconditional ("if and only if") | **no** | one direction certifies, so shipping it would silently drop the converse — 6 subjects refused |

That distinction is the cycle's product: **5 sources shipped, 11 subjects
refused across 5 newly-named signals, 1 parked** — and the intake window can
never re-wedge on any of them.

## The chain, end to end

1. **Orient**: brief first (`tools/session_brief.py`); lane clean (newest
   `main` runs green: `regression` success, `lean-hammer` skipped — no
   `[lean-fast]` tag); `origin/main` at `d007049`. Frontier had **53 ready**.

2. **Measured the whole `--take 8` window** with `run.formalize.certify_statement`
   before writing one ledger row (signals order the frontier; certification
   MEASURES — never distort a reading to force a green):

   | # | source | measured verdict |
   |---|---|---|
   | ch4 def-001 | "true for all sufficiently large *n*" (a **definition**) | refuse — quantifies over a **property**: `'Prop' is outside the carrier whitelist` |
   | ch4 lemma-003 | `even(n) ↔ ¬odd(n)` | refuse — biconditional **and** negation |
   | ch4 lemma-004 | `odd(n) ↔ ¬even(n)` | refuse — same |
   | ch4 problem-002 | "a factor of **every** natural *m*" ⟹ `n=1` | refuse — the binder is **inside the hypothesis**; hoisting it is **REFUTED**, witness `n=0, m=0` |
   | ch4 problem-007 | `n³ ≥ 4n²+7` eventually | **certifies** via witness threshold `5 ≤ n` → **source 86** |
   | ch4 problem-011 | `8 ∣ 5n ↔ 8 ∣ n` | refuse — biconditional |
   | ch4 problem-012 | `odd(n) ↔ n ≡ 1 (mod 2)` | refuse — biconditional |
   | ch4 problem-013 | `even(n) ↔ n ≡ 0 (mod 2)` | refuse — biconditional |

   Recording those refusals and regenerating advanced the head by exactly the
   refused subjects — the mechanism cycle 05 bought and cycle 08 completed —
   so the next `--take 8` window was measured on the same terms:

   | # | source | measured verdict |
   |---|---|---|
   | ch4 problem-015 | `a²−5a+5 ≤ −1 ↔ a ∈ {2,3}` | refuse — biconditional |
   | ch4 problem-016 | `n²−10n+24=0 ⟹ even(n)` | **certifies** — **PARKED** (see below) |
   | ch4 problem-021 | a **unique** `r` with `0≤r<5`, `14≡r (mod 5)` | refuse — witness-term gives existence; uniqueness needs a second, universally-quantified claim |
   | ch4 problem-022 | `t<3` and `t−1=6` ⟹ `t=13` | refuse — **the gate named this one itself**: "the hypothesis set is contradictory … would certify VACUOUSLY" |
   | ch4 problem-023 | `n²+n+1 ≡ 1 (mod 3)` ⟹ `n ≡ 0` or `2 (mod 3)` | **certifies** → **source 87** |
   | ch4 problem-025 | positive `a,b,c` with `a²+b²=c²` ⟹ `3 ≤ a` | **certifies** → **source 88** |
   | ch4 problem-029 | no natural `n` with `n²=2` | **certifies** → **source 89** |
   | ch4 problem-030 | `n² ≢ 2 (mod 3)` | **certifies** → **source 90** |

3. **Sources 86–90**: top-level `.txt` (verbatim prose, laid down by
   `tools/intake_from_frontier.py --ready --take 5 --apply`) + `manifest.json`
   entries (all `plain`, `expect_transcribes: true`). Top-level source count
   **77 → 82** (single-sourced from `registration.json`). Readings authored in
   `wp_c8_readings.py` (the tool's emitted skeleton), each box-verified TRUE
   **before** it was written there.

4. **What is genuinely new — and what is NOT.** The batch grows **coverage
   only**. It uses builtin term ops (`+ − * ^` at literal exponents), the
   builtin atoms (`= != <= <`), the frozen connectives (`and/or/implies`), and
   **one already-admitted operator word, `mod`**. **No operator word, macro,
   carrier, or trust root is added** — the `admitted.json` word set is
   unchanged (6 words; only re-priced metadata moved). **No reading has a
   parity or divisibility conclusion**, so the arity-1 **even/odd op-slot** and
   the **dvd macros are UNTOUCHED**: cluster-key **`b_evenodd_survives = True`**,
   `m_f3a9880f19ae` intact at `op_slot_arities [1]`.

   Two details worth keeping:
   * **86's threshold is TIGHT and the certifier says so.** `boundary_behavior`
     reports `n = 4` failing the hypothesis — and `n = 4` is exactly where the
     conclusion fails (`64 < 71`). The witness is minimal, not padded.
   * **89's subject text is verbatim-identical to `05_Logic#problem-009`.**
     Intake keys on subject text, as refusals and parks do, so shipping it
     retired **both** ready entries.

5. **Certification**: `bench_formalize.run_bench` with the session-inline
   author (unmetered, cost columns 0), checkpoint **RESUME** (nothing prior
   re-authored; only the five new source_ids entered, all joining a new
   **wave 10**). **All five certify in both bench arms.** Governed exogenous
   coverage **70 → 75**; governed reported DL **4897** ≤ ungoverned **5240**.
   The kernel statement-cert stays **deferred** (no Lean toolchain in a remote
   container — recorded honestly, not failed).

6. **Mining / admission**: `tools/subtree_mine.py` re-priced the staged pool on
   the grown corpus (75 certified readings, 32 proposals emitted — 11
   non-alias). **No NEW operator word crossed the admission bar**; the staged
   pool stays at 33. Honest no-delta on the admission axis, recorded.

## MEASURED refusals — first-class demand data (committed to the ledger)

Eleven subjects, **13 rows** (a multi-signal refusal is one row per signal),
each verdict box-checked before it was ledgered. Five signals are **new**, and
the vocabulary grew by appending only:

| new signal | what it names | why it is not an existing signal |
|---|---|---|
| `iff-connective` | a **biconditional between two already-expressible predicates** ("5n is a multiple of 8 iff n is") | `definition-biconditional` INTRODUCES a predicate name and wants a definitional-extension mechanism; this one wants a **connective** beside `and/or/implies` |
| `negation-connective` | a negated in-fragment **predicate** ("even iff **not** odd") | a negated **existential** is *not* this signal — sources 89/90 show it is a universal inequality the `!=` atom already states |
| `property-quantifier` | quantification over a **property**, not a value | measured, not assumed: `'Prop' is outside the carrier whitelist` |
| `hypothesis-quantifier` | the faithful hypothesis **binds** a variable | hoisting the binder to the prefix is **refuted by instances**, not merely weaker |
| `unique-existence` | a **unique** witness demanded | existence discharges by witness-term; uniqueness needs a second, universally-quantified claim conjoined to a ground one |

Recorded (`results/frontier_refusals.jsonl`, all `--by` the cycle-09 receipt):
def-001 → `property-quantifier` + `definition-biconditional`; lemma-003 and
lemma-004 → `iff-connective` + `negation-connective`; problem-002 →
`hypothesis-quantifier`; problems 011/012/013/015 → `iff-connective`;
problem-021 → `unique-existence`; problem-022 → `nonvacuity`.

Each names its unblocking purchase. Six subjects now sit under
`refused:iff-connective` — after one cycle it is the **largest single measured
demand class on the corpus axis**, and the biconditional is the primitive the
next connective-class purchase should price.

## PARKED, not refused — ch4 problem-016

`n²−10n+24=0 ⟹ n is even` **CERTIFIES in the fragment as it stands**. It is
held under the standing **`evenodd-coverage-decision`** — the same governance
hold cycle 06 placed on the ch3 parity block and cycle 08 moved out of prose
and into machinery. A park is a **decision**, never a fidelity verdict, and the
two ledgers stay disjoint by a tooth.

This is the **first parity-conclusion source measured outside ch3**, so the
park reason's clause was widened **in wording only** — the key is frozen, the
rows are untouched — to say what the decision has always been about: the
**class** (any source whose demand lands in the arity-1 even/odd op-slot), not
the chapter. Stated plainly: **the mechanical displacement was NOT re-measured
for this source**; only the standing decision's scope was applied. The
ship-or-exclude call remains **OPEN** and is the maintainer's, exactly as
cycles 06–08 left it. `parked:evenodd-coverage-decision` now holds **21**
subjects.

## Re-baseline (the ONE file) and the pins that moved with it

`specs/mathsources/registration.json` carries a cycle-09 lineage entry and the
new era numbers: **82** sources, waves **0–10**, governed exogenous
**78 readings / 75 certified**, stream **2297** over alphabet **62**, counting
DLs **naive 6156 / governed 4897 / ungoverned 5240**, census-of-record
**governed 11 macros @ 4282** and **ungoverned 9 @ 4301**, cluster-key
re-registration `baseline 4897 / census-of-record 4282 / accept_max_dl 4868 /
max_macros 16` (the block's own law, verified by its tooth). Cluster key
re-measures **`all_pass = True`** on the new bars.

Four harness-local micro-pins moved with the corpus (they live next to their
harness by design, not in the registration): `test_entropy_refs.py` (order-0
**5050.197**, LZ77 phrases **533**, order-1/2 context stats),
`test_c2_report.py` (the C2 headline five), `test_dl_trajectories_fig.py`
(final wave 9 → 10).

**One pin moved for a reason worth naming.** `test_rung_registry.py`'s pilot
commutativity-sort rung was pinned at "canonicalization saves nothing"
(`profit ≥ 0`). On the grown corpus it saves its **first 4 bits** (searched DL
raw 5758 → canon 5754). The rung is **still refused, on the same ground**: its
own model cost (2748 bits) dwarfs the saving, so the net stays positive at
+2744. The tooth was rewritten to bite on that **dominance** rather than on the
sign of a saving corpus growth is free to flip — the refusal is the invariant,
the sign was never the claim.

## Honesty ledger

* The census reported **signals**; certification issued every **verdict** here,
  and each was box-checked before it was written down.
* Eleven subjects refused, one parked, five shipped — **a refusal is a real
  product**, and this cycle's refusals outnumber its sources.
* No reading was bent to certify. The five biconditional subjects each have a
  one-directional rendering that the fragment accepts; **that is exactly why
  they were refused** rather than shipped.
* The park makes no claim about fidelity, and says in writing what it did not
  measure.
* No trust root touched: `kernel/certs.py`, `TRUST.md`, the escape-gate
  blocklist and `buildloop/growth_protocol.py::ANTI_LIST` are all unchanged.
  **P5 untouched** — no promotion executed, no entrance predicate claimed.
* Lean-free cycle (no `[lean-fast]` tag); the kernel statement-cert is deferred
  in-container and recorded as deferred, never as a pass.
* Full suite: **1234 passed, 35 skipped**.

## Carried-over demand

**36 ready entries remain** (53 → 36: 5 shipped, 1 duplicate retired with 89,
11 refused, 1 parked). The head is now `04#theorem-001` ("Every integer is
either even or odd" — parity again, so the standing decision meets the intake
window directly on the next cycle), then `04#theorem-003`, `05_Logic`, and the
**`06_Induction`** block, which is where the corpus axis will start asking for
an induction primitive.
