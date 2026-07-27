# C3 cycle 29 — the derived route could not clear itself, and the ready list ran out of fragment

**Product: eight measured refusals and a routing fix.**  Zero certifications.
The corpus stays at **125** top-level sources, governed readings **121**,
certified **118** — nothing was added, and that is the honest outcome of
measuring what the ready list actually held.  Two findings, and the second was
caught by the first.

Probe verdict (RUN here, not read off disk): **`lean-local`**.  No Lean was
touched this cycle; the gate was `CGB_LEAN=0 python3 -m pytest tests/ -q`.

## Finding 1 — `NEXT-SELECTION: unblocked` was a permanent directive

The brief opened with the derived route saying `unblocked` over **six**
signals and **11 paid subjects awaiting the unblock run**.  Running all six,
in the order printed, before any `--ready` consumption:

| printed signal | selected |
|---|---|
| `refused:definition-biconditional` | 0 |
| `refused:function-symbol` | 0 |
| `refused:iff-connective` | 0 |
| `refused:not-connective` | 0 |
| `refused:set-membership` | 0 |
| `refused:symbolic-exponent` | 0 |

**All six selected nothing**, and the reason is not that the groups are empty.
Every one of the 11 awaiting subjects is **already a corpus source**, measured
against the selector's own skip notes:

```
awaiting_unblock_run     : 11
of those already-intaken : 11
of those NOT intaken     : []
```

The route branched on `refill_projection.awaiting_unblock_run`.  That field is
an **upper bound**, and its own honesty note says so in writing: *"a returning
subject still has to clear the ready computation's other demotions — already
intaken, or independently parked — which this projection does not model."*
Honest for a projection; **wrong for a branch**.

`tools/supply_status.py` carried this promise beside the route:

> it clears itself only when the unblock run actually happens (the run
> retires the ledger rows this reads)

**That promise is false for a subject that is already a source.**  The
selector skips those — `skipping already-intaken node` — so it retires
nothing, so the route re-prints the same six commands next cycle.  And the
next.  A self-clearing directive that cannot clear is a permanent no-op
wearing a correct-looking line: every future cycle pays six no-op runs, and
the brief's header reports 11 subjects pending that no cycle can ever consume.

### The fix

`_next_selection` now branches on `selectable_awaiting_subjects` — the
projection's count **minus** the subjects already laid down — and reports
**both** numbers, so the bound stays auditable rather than hidden.  The
already-intaken predicate is **imported from the selector**
(`intake_from_frontier._existing_sources`) rather than restated, so the branch
and the tool it routes to cannot drift: the number that decides the route is
computed by the code that acts on it.

`READS FAIL SAFE` here means **do not narrow**: a projection reporting a count
but no subject list is an input we could not read, and it falls back to the
bound.  Narrowing on an unread input would re-open the cycle-23 miss (ready
consumed over paid unblock supply) that this route exists to prevent.

Teeth, **mutation-verified in both directions**:

* `test_an_already_intaken_awaiting_subject_never_routes_to_unblocked` — the
  cycle-29 shape.  Restoring the pre-fix branch (`awaiting > 0`) reds this and
  the byte-identical regen tooth, and nothing else.
* `test_a_not_yet_intaken_awaiting_subject_still_routes_to_unblocked` and
  `test_a_partly_intaken_awaiting_set_counts_only_what_is_selectable` — the
  other direction, so a `return 0` rubber stamp cannot pass as the fix; it
  reds five teeth including both cycle-23 protections.
* `test_an_unreadable_subject_list_falls_back_to_the_projection_bound`.
* `test_the_branch_uses_the_selectors_own_intaken_predicate` — pinned against
  the import, because a restated predicate would pass every behavioural tooth
  above while still being a second copy free to drift.

## Finding 2 — the ready list had run out of fragment, and all eight refused

With the unblock route measured empty, the cycle consumed `--ready --take 8`
in listed order.  All eight are `prime_number_theorem_and`, and **all eight
refused**.  Each verdict is the gate's own, on the most faithful reading this
session could author:

| src | node | gate verdict (verbatim) | signal |
|---|---|---|---|
| 134 | `kl-odd-goldbach-finite` | `unknown atom/connective 'prime'` | `prime-predicate` |
| 135 | `li2-eq` | `unknown term operator 'integral'` | `integral-operator` |
| 136 | `log-zeta-eq-4` | `unknown term operator 'integral'` | `integral-operator` |
| 137 | `phi_star-affine-periodic` | `FragmentMiss[carrier:Complex]: amb: ambient carrier 'Complex' is outside ('Nat', 'Int', 'Rat')` | `complex-carrier` |
| 138 | `ramare-saouter-odd-goldbach` | `unknown atom/connective 'prime'` | `prime-predicate` |
| 139 | `richstein-even-goldbach` | `unknown atom/connective 'prime'` | `prime-predicate` |
| 140 | `shift-upwards` | `FragmentMiss[carrier:Complex]: amb: ambient carrier 'Complex' is outside ('Nat', 'Int', 'Rat')` | `complex-carrier` |
| 141 | `sigmaR_natCast` | `unknown term operator 'sigmaR'` | `uninterpreted-function-symbol` |

The eight laid-down source files were **removed**: a refused subject is demand
data, never a corpus source.  The corpus count is unchanged, so nothing is
re-baselined — `specs/mathsources/registration.json` takes no lineage entry
for a cycle that added no source.

**On 137 and 140 the carrier is the honest blocker, not the function symbol.**
An earlier draft read both with an `Int` ambient and got `unknown term
operator 'phistar'` / `'fourierhat'` — a verdict about the *abstraction the
draft chose*, not about the source.  Read faithfully, `z` traverses contours
in the complex plane and the whole identity lives there, so the gate refuses
at the carrier whitelist first.  The recorded signal is the one the faithful
reading earns.

**The demand this names is not a small step.**  Four blockers cover all eight:
a primality predicate, an integral operator, a complex carrier, and an
uninterpreted function symbol.  None is a rung the current ladder reaches by
widening; each is its own purchase, and two of them (`complex-carrier`,
`integral-operator`) are carrier/analysis demand this fragment has never
priced.  Ready falls **11 → 3**.

## Finding 2b — the coarse signal would have re-wedged the loop in one cycle

`sigmaR_natCast` was first recorded under `function-symbol`, and the
regenerated route immediately flagged it as the **one** selectable subject —
which is to say, it would have sent cycle 30 straight back to re-measure the
refusal cycle 29 had just measured.  `function-symbol` is a signal a **landed**
purchase meets (defined functions, with bodies), so filing σ^R there promises
a return the fragment cannot deliver.

Measured, not assumed: the `definition` route was authored and gated too, and
refuses identically — `unknown term operator 'sigmaR'` — because the source
gives σ^R **no body**, and a definition body may mention only its parameters.
The precise signal is `uninterpreted-function-symbol`, which no purchase on
the board meets.

The ledger is **append-only**, so the correction is an appended row, never an
edited one: the subject now carries both signals and returns only when both
are met, which holds it correctly.  The coarse row stands as the reading it
was.

This is the cycle-26/27/28 finding a third time, from a new side: **a refusal
group coarser than its blocker promises supply nobody bought.**  What is new
is how it was caught — the routing fix from Finding 1 printed a selectable
count of 1, and cross-checking that number against the selector is what
surfaced it.  The instrument found the defect in the cycle that built the
instrument.

## Finding 2c — the class measurement caught the ledger change, as designed

Appending the `function-symbol` row immediately reddened
`tests/test_function_symbol_class.py::test_the_eleven_subjects_are_exactly_the_refusal_ledger_rows`:

```
AssertionError: the classification covers 16 refusals; the ledger has 17
```

That is the tooth doing exactly what its docstring promises — *"a re-census
that retires a subject fails HERE rather than leaving the classification
quietly describing a slice that moved"* — and it is the reason the P8 row's
price cannot drift silently behind a ledger append.

`sigmaR_natCast` is classified **`needs-mechanism`**, and it is the sharpest
instance of that class in the table: sharper than `edge-disjoint`, which at
least has a carrier one could name.  The source gives **no definiens for
either symbol, anywhere**, so no unfolding reaches it at any index — the class
definition verbatim.  `returned_by_p8` is **False**, measured rather than
inferred: P8 buys a *definitional* extension whose body may mention only its
parameters, and the `definition` route was authored and gated here to check
rather than assert.  **`P8_CEILING` stays 5.**  The `needs-mechanism` count
pin moves 5 → 6 because the slice moved, never to keep a green.

## State

* corpus **125** sources (unchanged), governed readings **121**, certified **118**
* ready **11 → 3**; blocked groups **49**; refused subjects **61 → 70**,
  group memberships **122 → 131**
* census byte-identical: attempt-candidates **135**, out-of-fragment **1521**,
  no-signal **296** (no corpus growth, so no re-census delta)
* derived route now `ready` (bound 11, **selectable 0**); verdict
  `ready-work-available`
* gate: `CGB_LEAN=0 python3 -m pytest tests/ -q`

## Bounds

No ceremony-reserved path in the diff (`kernel/certs.py`, `TRUST.md`,
`buildloop/growth_protocol.py`, `setup.sh`, `ci/`, `.claude/`, `.github/` all
untouched).  P5 not promoted.  No park lifted, no park recorded.  Ledgers
append-only.  `tools/FgReflect.lean` and `results/reflect_candidates.json`
untouched; no Lean lane ridden.  No purchase priced — the four blockers named
above are purchase-axis demand for the purchase driver, not this loop's to
spend.
