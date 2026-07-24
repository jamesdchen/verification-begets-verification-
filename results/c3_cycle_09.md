# C3 cycle 09 — the first batch through the un-wedged window (source 86)

**Axis:** corpus (Lean-free). The first cycle to consume the intake window
cycle 08's park ledger opened. **Batch: source 86** — math2001 ch.4
Proofs-with-Structure-II problem-007, the corpus's first *"sufficiently
large"* source. **Seven of the eight previewed entries were measured as
refusals** and demoted; four refusal signals were appended to the vocabulary.

## The window opened where cycle 08 said it would

Cycle 08 demoted the parked ch3 parity block, moving the `ready` head to
`04_Proofs_with_Structure_II#definition-001`. This cycle previewed
`--ready --take 8` from exactly there. No parked material was reached, no cap
was widened, and the freshness guard passed (no open `C3 cycle…` PR; the one
open PR, #48, is a governance-lane PR on a different title).

## Every entry MEASURED — the gate's verdict, verbatim

Signals order the window; **certification measures**. Each entry got a
*faithful* reading attempt — never a distortion to force a green — and the
`math-reading-gate` verdict is recorded as-is:

| # | node | faithful form needs | gate verdict |
|---|---|---|---|
| — | ch4 definition-001 | a **property variable** (2nd order) | `unknown atom/connective 'property'` → **refuse** |
| — | ch4 lemma-003 | `iff` + `not` | `unknown atom/connective 'iff'` → **refuse** |
| — | ch4 lemma-004 | `iff` + `not` | `unknown atom/connective 'iff'` → **refuse** |
| — | ch4 problem-002 | a binder **inside the hypothesis** | `unknown atom/connective 'forall'` → **refuse** |
| **86** | **ch4 problem-007** | exists-then-forall (already carried) | **`ok=True` — certifies** |
| — | ch4 problem-011 | `iff` | `unknown atom/connective 'iff'` → **refuse** |
| — | ch4 problem-012 | `iff` | `unknown atom/connective 'iff'` → **refuse** |
| — | ch4 problem-013 | `iff` | `unknown atom/connective 'iff'` → **refuse** |

Two measurements worth keeping because they *corrected* a plausible guess:

- **`%` is expressible.** Problems 012/013 say "congruent to 1 modulo 2", and
  the obvious call is a `mod-operator` refusal (cycle 06 recorded one for the
  ch3 congruence *definition*). Probed directly: `n % 2 = 1` certifies. So
  `iff` **alone** is their miss, and no mod refusal was recorded. Recompute
  beat recollection.
- **Two entries first failed for a shallow reason** — object names must match
  `[a-z][a-zA-Z0-9_]*`, so the analyst's `N` was rejected before the gate ever
  reached the real question. Re-measured with `nbig`; only then did
  definition-001's true miss (`property`) appear, and only then did
  problem-007 certify. A naming rejection is not a fragment miss, and
  recording it as one would have been false demand data.

## The one source that ships

`86_04_proofs_with_structure_ii_problem_007` — *"Show that for all
sufficiently large integers n, it is true that n³ ≥ 4n² + 7."*

    exists nbig, forall n,  nbig <= n  ->  4*n^2 + 7 <= n^3

**"Sufficiently large" is unfolded by the same chapter's own definition** —
04#definition-001, the very entry that refuses one row above — so the
unfolding is the source's, not a convenience. `n³ ≥ …` is written as `… ≤ n³`
because `>=` is not a builtin atom; flipping the sides of an inequality is a
notational identity, not a weakening.

**The pairing is the interesting result.** The fragment expresses every
*instance* of "sufficiently large" and not the *definition* of it: the
definition quantifies over a property, and there is no predicate-variable
sort. A purchase that adds one would convert a whole family at once — that is
what `refused:property-quantification` now names.

Only builtin ops appear (`+ * ^` at literal exponents 2 and 3, `<=`,
`implies`), so **no operator word, macro, or trust root grows** — the
admitted-operator set is byte-identical (6 words; `n_admitted` stays 5, an
honest no-delta on the admission axis), and no parity or divisibility
structure appears, so the arity-1 even/odd op-slot and the dvd macros are
untouched.

Certified **TRUE in both bench arms** via the inline-author checkpoint resume
(joins wave 9). Governed exogenous coverage **70 → 71**; governed reported DL
**4620** ≤ ungoverned **4963**.

## Four refusal signals appended (vocabulary grows by appending, never renaming)

- **`biconditional-claim`** — a *claim* (lemma/problem) whose faithful form is
  a biconditional. Deliberately kept **distinct from `definition-biconditional`**:
  the missing primitive is the same (`iff`), the demand source is not, and the
  split is what shows iff-demand is broader than definitions. Five of this
  cycle's seven refusals land here.
- **`negation-connective`** — the connective set is exactly
  `{and, or, implies}`; `not` is absent (measured, not assumed).
- **`property-quantification`** — quantification over a property; no
  predicate-variable sort.
- **`hypothesis-scoped-quantifier`** — the binder sits inside the antecedent
  ("a factor of **every** natural number m"). Flattening it to a top-level
  `forall` is a *different and false* claim (n=2, m=4 refutes it), so the
  faithful reading has nowhere to go.

Ledger rows: 15 → 24. Frontier `ready` **53 → 45**; blocked groups 20 → 24.

## Re-baseline

`specs/mathsources/registration.json` re-baselined live with a lineage entry
(78 sources, 74 governed readings, 71 certified). Four corpus-era micro-pins
that live next to their harnesses moved with the corpus and were re-baselined
against freshly regenerated artifacts — `tests/test_entropy_refs.py`
(order-0 4704.304 → **4738.51**, LZ77 z 491 → **504**, order-1/2 context
stats) and `tests/test_c2_report.py` (headline C2 numbers). **The C2 finding
itself is unchanged**: the vocabulary still does not pay under C2, and the
governed/ungoverned ranking is as before — only the magnitudes moved.

## Status

- Corpus **77 → 78 sources**; governed readings 73 → 74; certified **70 → 71**.
- **Carried-over demand: 45 ready entries** (cap never widened).
- Regen chain re-run in full after the re-baseline; `cluster_key_measure`
  reproduces `governed 4620.0 -> 4005.0, all_pass=True`.
- No trust-root edits (`kernel/certs.py`, `TRUST.md`, escape-gate blocklist
  untouched); no Lean-touching files — Lean-free cycle, no `[lean-fast]`.
- P5 not executed, not touched.
- Full suite: **1234 passed, 35 skipped**.
- The ch3 parity ship/exclude decision remains **open and unblocking** — this
  cycle ran past it, which is exactly what the park ledger was for.
