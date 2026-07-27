# P9 delta — named sets by comprehension, and the row that was two rows

*(P9 purchase receipt.)*

**Axis:** purchase. **Row:** `refusal-set-carrier` (PLAN_FRAGMENT §4 P9,
refusal-priced, 4 subject-rows). **Outcome: the row SPLIT.** The eliminable
half is PURCHASED as `refusal-set-comprehension`; the tower-class half stays
OPEN as `refusal-set-carrier`, re-titled to what it actually is.

Probe verdict, run in this container and quoted verbatim: **`lean-local`** —
corroborated by direct elaboration (`tests/test_reflect_shadow.py`, 24 passed
in 427.6 s, real Mathlib elaboration). Under PLAN_FRAGMENT §3.1 rule 3 that
verdict is what licensed an unattended session to open a tower-class row at
all. **The bill it then wrote is not tower-class**, and that is the finding.

## The finding: eliminable and non-eliminable were priced as one thing

The row's own prose already drew the line and then billed across it:

> "membership in a COMPREHENSION at a literal element unfolds definitionally
> and SHIPS (source 121), so this row is for set objects that survive
> unfolding, not for every appearance of the membership sign."

Right — and the four subjects it prices are **not** all on the far side of
that line. `tests/test_set_object_class.py` measures which are, against the
gate and the evaluator rather than against a re-implementation:

| subject | what it actually needs | reachable by this bill? |
|---|---|---|
| `09_Sets#definition-003` (intersection of `U`, `V`) | arbitrary sets, no comprehension anywhere | **no** — `set:free-set-variable` |
| `09_Sets#problem-014` (complement equality) | ℤ/ℕ **carrier mismatch in the prose** | not a vocabulary block |
| `09_Sets#problem-015` (empty intersection) | same mismatch, and **FALSE at one carrier** | not a vocabulary block |
| `09_Sets#problem-017` (powerset non-membership) | faithfully `set:set-valued-param`; degenerately unfolds | **degenerately** |

So `set-membership` was **two rungs wearing one name**, exactly as
`definitional-extension` was for P8.

## What was bought

A `setdef` statement names a set by an **explicit comprehension over one
parameter**, and `{"op":"mem","args":[<term>,{"set":s}]}` takes membership in
it. `e ∈ {x | φ(x)}` **is** `φ(e)`, so the gate desugars every membership by
capture-free substitution — the pred layer of P8's `_unfold_term`.

**`generators/math_eval.py`, `generators/math_smt.py`,
`generators/math_compile.py` and `tools/FgReflect.lean` are ALL FOUR
byte-unchanged.** Nothing enters `Tm`/`Pd`, `decDenote` keeps deciding by
computation, and §3.1 rule 3(a) is not reached. Landed
**additive-desugaring** (P6/P8's shape), not tower-class.

Set **algebra** is deliberately not new vocabulary: union, intersection,
complement, the empty set and set equality are stated **extensionally** with
the connectives P6 bought. Adding algebra nodes would buy a second spelling of
preds the fragment can already write — and would then have to survive
unfolding, which is the tower-class purchase again.

One ordering is load-bearing rather than tidy: **membership is eliminated
before the NNF walk.** A negated membership (`10 ∉ {n | n odd}`, the
`09_Sets#problem-002` shape) has an NNF dual only *after* substitution,
because what carries the dual is the body's atom and not the membership.
Unfolding second would refuse the very readings this row buys; pinned by
`test_a_negated_membership_reaches_the_bodys_own_dual`.

## Conservativity is executable, not argued

Every admitted reading is measured against its **hand-unfolded twin** — a
reading written longhand in the pre-P9 fragment — at all four consumers
(`tests/test_setdef_battery.py`, 24 teeth):

* **eval**: same verdict at every point of a box sweep;
* **SMT**: byte-identical rendering, and both solvers (z3 4.16.0, cvc5
  1.3.4) independently return `unsat` on the negated biconditional;
* **Lean**: byte-identical `lean_text` **and** `statement_hash`;
* **reflect**: nothing to compare — `Tm`/`Pd` are byte-unchanged.

The divergence tooth is what makes those agreements evidence:
`test_unfolding_a_wrong_comprehension_gets_no_certificate` plants `{k | k odd}`
where the source declared `{k | k even}`, and all three channels witness it
(evaluator refutes pointwise, both solvers refute symbolically, Lean hash
differs).

## What was NOT bought, refused by name

Three freezes keep the elimination **total**, mirroring P8's one for one:
`setdef:recursive-body`, `setdef:binder-body` (capture-freedom by
construction, not by argument), `setdef:open-body`.

Two more are the **tower-class residue**, and they are the reason the row
stays open:

* **`set:free-set-variable`** — an arbitrary set the source gives no
  comprehension for. No body to substitute, so membership **survives
  unfolding**: it needs an uninterpreted predicate in the mirror and a `Pd`
  constructor plus its `Decidable` story in the slice. Refused under one
  signal however the source spells it (as a bare name, or by declaring the
  object at type `Set Nat`), so the frontier never splits one demand into a
  row per element type.
* **`set:set-valued-param`** — a comprehension whose parameter ranges over
  sets (the powerset shape). Priced **apart**, because the two are separate
  checks in the gate and retiring one leaves the other refusing.

Both are now first-class gate refusals with ledger signals
(`free-set-variable`, `set-valued-param`), so the residue's demand **accrues
to the ledger** as corpus cycles meet it instead of sitting on a projection.

## The sharpest measurement: one subject is refuted, not blocked

`09_Sets#problem-015` states
`{n:ℤ | n≡1 mod 5} ∩ {n:ℕ | n≡1 mod 5} = ∅`. Its two comprehension bodies are
the **same congruence, verbatim** (asserted against the committed prose). A
reading uses one carrier, so collapsing the ℤ/ℕ mismatch makes the two sets
identical and the claimed empty intersection **false** — the evaluator refutes
it at n = 1, 6, 11, … A subject whose blocker is a **truth fact** is demand for
no primitive, and no purchase on the board returns it. Recording that here is
what stops a later cycle spending a purchase on it.

`09_Sets#problem-014` carries the same ℤ/ℕ mismatch. Whether that is an
extraction artifact worth reading at a single carrier is a **choice a corpus
cycle must make and defend**, not something this purchase decides.

## Re-census delta: honestly ZERO

`results/census_portfolio.json` is **byte-identical** after the purchase
(7 corpora, 1952 nodes; 135 / 1521 / 296). The P4/P8 shape: a mechanism moves
no lexical vocabulary. The `sets-cardinality` signal stands unchanged at 107,
and it is **not** this row's price — the row prices the four measured
`refused:set-membership` rows, and the census number is the whole signal of
which P2 already bought the counting slice.

## Refill

`refill_projection.awaiting_unblock_run` **23 → 27**, *measured against this
purchase's base `d889c54`*: the four subjects return to the intake window,
where they are candidates again exactly as they were before.

**That pair is this purchase's ISOLATED effect, and it is NOT the number on the
merged tree** — stated here because a reader who checks will find a different
one and deserves to know why rather than to discover a receipt that stopped
tracking its evidence. C3 cycle 26 (`#193`) merged while this bill was being
written; it consumed part of the backlog and filed sixteen refusal rows of its
own, so the figure on the tree that carries both is **19**. Both readings are
true of different trees and neither corrects the other: the delta this row is
responsible for is **+4**, and the absolute number belongs to whatever tree you
read it on. Recompute beats recollection — `results/purchase_frontier.json` is
derived, so read it rather than this sentence.

That the four return at all is a **selection** fact and never a promise they
certify — the
class measurement above says the honest expectation is small or zero, and the
**number of record is the next corpus cycle's `--unblocked
refused:set-membership` run**, never this receipt.

The refusal ledger stays append-only: cycle 16's rows **stand** as the
pre-purchase reading. A subject that refuses again at the grown fragment is a
NEW measurement recorded as such.

## Bounds

Gate: `CGB_LEAN=0 python3 -m pytest tests/ -q`. Lean-free purchase — no
`lean-fast` tag, `tools/FgReflect.lean` untouched (asserted mechanically by
`test_the_eliminable_half_adds_no_constructor_to_the_reflect_slice`). P5 not
promoted; `kernel/certs.py`, `TRUST.md` and the escape-gate blocklist
untouched. `buildloop/growth_protocol.py` is touched in exactly two spans —
`SIGNATURE_PINS` and `GROWERS` — which is the conforming-bill route the
`trust-surface` check decides mechanically.
