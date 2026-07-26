# C3 cycle 23 — the analytic corpus answers, and every answer is a refusal

**Product: demand data.**  Eight subjects taken from the frontier's ready list
in listed order, all eight measured through `run.formalize.certify_statement`,
**zero certified**, fifteen refusal-ledger memberships recorded and five new
signals minted — each one gate-measured, none inferred from prose.  No corpus
source lands, so `specs/mathsources/registration.json` is untouched: the
numbers did not move, and a re-baseline that records no movement is decoration.

This is the first cycle whose take came from `prime_number_theorem_and`, the
944-node analytic-number-theory blueprint cycle 22 intaked under §3.2 path (c).
Cycle 22 flipped the supply verdict to `ready-work-available` and said those 27
ready entries belonged to cycle 23.  They did.  What they bought is a map of
where the fragment stops.

## The take, and what the gate said

Subjects 130–137 of the ready list, in the order `intake_from_frontier
--ready --take 8` emitted them.  Every verdict below is the gate's own text,
copied from the run, not a paraphrase.

| # | node | gate verdict (verbatim) | signals filed |
|---|---|---|---|
| 130 | `AnalyticOn.norm_le_of_norm_le_on_sphere` | *(see below — a vacuous stand-in **certifies**)* | `metatheoretic-subject` |
| 131 | `B-affine-periodic` | `amb: ambient carrier 'Complex' is outside ('Nat', 'Int', 'Rat') (+ the parametric ZMod <n>)` · `unknown term operator 'B'` | `complex-carrier`, `function-symbol` |
| 132 | `BlaschkeNonZero` | same carrier miss · `unknown term operator 'B'` | `complex-carrier`, `function-symbol` |
| 133 | `Q-def` | `unknown term operator 'Q'` · `setbuild: hi bound must be a LITERAL — bounded, exactly enumerable sets are what make cardinality decidable (eval counts, SMT unrolls the indicator sum); a symbolic bound is not in the fragment` | `function-symbol`, `set-symbolic-bound` |
| 134 | `TaxicabIntegral` | same carrier miss · `unknown term operator 'integral'` | `complex-carrier`, `integral-operator` |
| 135 | `buthe2-buthe-chi-star-icc` | `amb: ambient carrier 'Real' is outside (…)` · `unknown term operator 'chistar'` | `function-symbol`, `real-carrier` |
| 136 | `ch2-lemma-5-1-e` | same carrier miss · `unknown term operator 'lim'` | `complex-carrier`, `limit-operator` |
| 137 | `ch2-lemma-5-1-f` | same carrier miss · `unknown term operator 'lim'` | `complex-carrier`, `limit-operator` |

**Every second blocker was measured at an ADMISSIBLE carrier**, not inferred.
Filing `complex-carrier` alone on 134/136/137 would have promised that a
carrier purchase returns them to ready — where they would refuse again on the
integral or the limit.  That is the cycle-05 re-wedge, and the way to not
repeat it is to pay for the second measurement now: each of those subjects was
re-run at `Int` with the carrier refusal out of the way, and the gate named the
missing primitive directly.  Likewise 133's symbolic bound was isolated by
replacing the `squarefree` filter with `even`, so the *only* thing left
refusing is the bound itself.

## The finding this cycle exists to write down: 130 certifies, and must not

Source 130's entire text is:

> An application of the Maximum modulus principle.

There is no statement here.  It is a **proof remark** — the blueprint node
records how a result is proved, not what it says.  And the fragment has an
answer for it: a stand-in reading whose conclusion is `n = n` **passes every
gate, `ok=True`**, with no fabrication warning anywhere in the pipeline.

That green is available to any unattended session that treats "the gate went
green" as "the reading is faithful."  It was not shipped, and the reason is the
honesty rule rather than any machinery: *never distort a reading to force a
green.*  Recorded plainly here because the next firing should not have to
re-derive it — **a lexical census cannot tell a theorem from a proof remark**,
and this corpus contains both.  `prime_number_theorem_and`'s ready list was
computed by a census that reads words; 130 carries no fragment-foreign word, so
it read as an attempt-candidate.  It is not one.

Filed under `metatheoretic-subject` rather than a new signal.  Cycle 14 minted
that name for "the subject asserts a property of the apparatus rather than a
proposition about carrier values," and a node whose subject is *the proof* is
that case, not a new one.  It stays where the map already says it belongs:
**no purchase meets it** — and `test_metatheoretic_subject_is_still_met_by_no_purchase`
keeps that honest.

## Five new signals, and why they are five and not one

The vocabulary in `tools/frontier_refusals.py::SIGNALS` grew by
`complex-carrier`, `real-carrier`, `limit-operator`, `integral-operator`,
`set-symbolic-bound`; `tools/purchase_frontier.py::SIGNAL_UNBLOCKED_BY` maps
all five to `None` with the reason none is met, and the completeness teeth
(`test_signal_map_covers_the_whole_refusal_vocabulary_exactly`,
`test_no_measured_refusal_is_unmapped_without_a_stated_reason`) check both
halves agree.

Cramming them into one `analysis` signal would have been smaller and would have
lied.  A signal is a **promise about which purchase returns the subject**, so
one name covering a carrier, a limit and an integral promises that a single
purchase retires all three.  It would not.

Four of the five sit behind `parked-real-analysis` — limits and continuity are
undecidable, which is what that row is parked *for* — so they are demand whose
route is a governance decision, never a bill.  `complex-carrier` is filed apart
from `real-carrier` because ℂ is strictly past the park, not a smaller version
of it: every carrier the fragment owns (Nat, Int, Rat, ZMod n) is a decidable
arithmetic domain with an enumerable instance box, and ℂ has neither.

**`set-symbolic-bound` is the one that is genuinely purchasable**, and it is the
most useful thing this cycle bought.  The gate names it in its own vocabulary
(`missing_kind_guess: set:symbolic-bound`).  `results/p2_delta.md` predicted it
in prose when P2's re-census came back zero — *"a symbolic-bound cardinality is
the named demand the next iteration-class purchase targets"* — and it has had no
subject behind it until now.  `Q(x)` = the number of squarefree integers ≤ x is
that subject.  P7 bought iteration over a symbolic bound at the **exponent**;
this is the same shape one site over, at `setbuild`'s upper bound.  No queued
§4 row prices it, so **declaring one is a purchase-axis call**, not this loop's.

## The open purchase row's price moved, and the tooth is what said so

Four of the fifteen memberships land on `function-symbol`, and that signal is
not a free-floating label: `tests/test_function_symbol_class.py` is the
committed **class measurement** the open `refusal-function-symbol` row is
priced on, and it reds when the slice moves without the classification moving
with it — *"an unclassified subject is exactly the unpriced reach the row was
declared on."*  It went red on this cycle's first full-gate run, correctly.

The fix was to extend the measurement, not to withdraw the rows.  The gate said
`unknown term operator 'B'` / `'Q'` / `'chistar'`, so these ARE function-symbol
refusals by the vocabulary's own written definition, and dropping them to keep
a tooth green would be bending a measurement to fit a number.

All four are classified `needs-mechanism` with **`returned_by_p8: False`**, and
the file already had the precedent for exactly this shape: `edge-disjoint` is
*"filed under this signal by accident of vocabulary"* because its `L_y` needs a
magma carrier, not an arithmetic function.  `B^±` and `B_f` are ℂ→ℂ; `χ*` lives
on a real interval; and `Q` — the one genuinely arithmetic symbol of the four —
does not unfold at a literal index either, because its definiens needs both
`squarefree` (no word) and the symbolic-bound cardinality this cycle minted.

**So the slice is fifteen and `P8_CEILING` stays five.**  Raising it would be
the flattery the file's own P7 amendment forbids.  The two places that had the
number written by hand (`== 11`) now derive it from the tables, so the next
slice movement cannot pass by editing only one of them.

## Ready-list movement, measured

| | before | after |
|---|---|---|
| ready | 27 | **19** |
| blocked groups | 29 | **34** |
| refused **subjects** | 46 | **54** |
| refused group **memberships** | 68 | **83** |
| signals meeting no purchase | 9 | **14** |
| top-level sources | 121 | 121 |
| governed readings (certified) | 117 (114) | 117 (114) |

The supply verdict stays `ready-work-available` (ready 19), so cycle 24 has
work without needing a purchase, a park lift or a new corpus.  The 19 carried
entries are unmet demand from this window and are named as such: they are the
remainder of the same `prime_number_theorem_and` ready list, and on this
cycle's evidence a large share of them will refuse the same way.  **That is not
a reason to widen the cap or to skip them** — a measured refusal is the
product — but the next firing should expect a refusal-shaped cycle rather than
a certifying one, and should budget the second-blocker measurement that keeps
the ledger from re-wedging.

## Honesty notes

- Zero readings authored, so `wp_c18_readings.py` was **not** kept: an empty
  `READINGS` dict is dead code, and the provenance it would have carried is
  this receipt.  The eight laid-down `specs/mathsources/13*.txt` files were
  removed — a refused subject is demand data, never a corpus source (the
  cycle-19 precedent).
- `specs/mathsources/registration.json` is **unchanged and deliberately so**.
  No source landed; `n_top_level_sources` stays 121 and the governed DL stays
  6963.0.  `tests/test_corpus_registration.py` verifies that against the
  primary artifacts.
- One probe reached the kernel statement-cert and is reported rather than
  buried: 132's radius chain `0 < r < R < 1` at `Rat` elaborated
  (`lean-elaborate+lean4checker: pass`) and then **failed `entailed-instances`**,
  correctly — it is the source's *hypothesis* stated as a conclusion, false in
  general.  It was never a reading of 132, whose demand is the non-vanishing of
  `B_f`; measured only to show what a carrier purchase would and would not buy.
- `tools/lean_env_probe.py` was RUN in this container and read **`lean-local`**,
  so the per-commit gate was `CGB_LEAN=0 python3 -m pytest tests/ -q` per
  CLAUDE.md's full-gate row.  `results/lean_env.json` regenerated
  byte-identical to its committed state.
- No carrier, node class, operator word or trust root grows.  `kernel/certs.py`,
  `TRUST.md`, the escape-gate blocklist and `ANTI_LIST` are untouched;
  **P5 not executed**.  Lean-free cycle (no `lean-fast` tag).
