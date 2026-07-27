# C3 cycle 30 — the ready list is empty, and all four supply paths are measured shut

**Product: three measured refusals and a standstill reading.**  Zero
certifications; corpus unchanged at **125**.  This cycle consumed the last
three ready entries, every one refused, and the frontier now lists **0 ready**.
The supply verdict turned over to `supply-blocked` in the same regen.

Probe verdict (RUN here, not read off disk): **`lean-local`**.  No Lean
touched; gate `CGB_LEAN=0 python3 -m pytest tests/ -q`.

## The route read `ready`, which is the cycle-29 fix working

The brief opened `NEXT-SELECTION: ready (consume the ready list in frontier
order)` — not the stuck `unblocked` that cycle 29 measured and repaired one
cycle earlier.  The first thing this cycle did was confirm the fix holds in
production: no no-op unblock runs, straight to the ready list.

## The three refusals

All three are `prime_number_theorem_and`, taken in listed order.  Each verdict
is the gate's own, on the most faithful reading this session could author:

| src | node | gate verdict (verbatim) | signal |
|---|---|---|---|
| 134 | `thm:faber-kadiri-psi` | `unknown term operator 'psi'` | `uninterpreted-function-symbol` |
| 135 | `thm:large-n-final` | `unknown atom/connective 'highlyabundant'` | `defined-predicate` |
| 136 | `varphi-fourier-ident` | `FragmentMiss[carrier:Complex]: amb: ambient carrier 'Complex' is outside ('Nat', 'Int', 'Rat')` | `complex-carrier` |

**134 was authored so the recorded blocker is the real one.**  The source
states `|ψ(x) − x| ≤ 5.3688·10⁻⁴ x`, and a careless reading would have refused
on the absolute value or on the non-integer literal — verdicts about the
*reading's* shortcuts rather than about the source.  So the reading unfolds
`|·|` into the two-sided bound it abbreviates and scales both sides by 10⁴,
both faithful rearrangements, leaving ψ itself as the first thing the gate
cannot take.  ψ is the Chebyshev function: definable in principle, given **no
definiens by this source**, which is `uninterpreted-function-symbol` exactly.

**135 has a second blocker behind the recorded one.**  `highlyabundant` is
refused first, and it is a `defined-predicate` — the corpus does define it, at
`highlyabundant-def`, the subject cycle 24 measured.  Behind it sits `L_n`, an
uninterpreted sequence.  The ledger records the measured first blocker; the
second is named here rather than filed, because filing a signal the gate did
not reach would be a projection.

**Every signal was checked against the landed purchases before recording** —
the cycle-29 discipline, applied as routine.  None of
`uninterpreted-function-symbol`, `defined-predicate` or `complex-carrier` is
met by a landed purchase, so none of these three re-wedges the next cycle the
way the coarse `function-symbol` filing would have.

The three laid-down source files were removed: a refused subject is demand
data, never a corpus source.  No growth, so no lineage entry.

## The standstill, measured path by path

With ready at zero the prompt's order is to try new-corpus intake before
concluding anything.  Run, not recalled:

```
$ python3 tools/corpus_candidates.py
reason: registry-exhausted  (every declared row is already intaken, refused,
  or documentation -- the loop consumed the list.  UNBLOCKED BY: a maintainer
  appending one row (name, source, adapter, project, declared_by, rationale))
declared: candidate=0, example=1, intaken=7, refused=0
SELECTED: none -- path (c) has nothing declared to take.
```

The declared fallback is a corpus the maintainer has NAMED.  This firing's
payload names none (it is a `pull_request.closed` webhook context), there are
**zero open issues**, and PLAN_FRAGMENT §1 names no corpus.  So path (c) is
genuinely unavailable rather than merely unattempted.

All four paths, as the regenerated verdict states them:

```
supply-blocked: tower-class-only (1 open rows need attendance or lean-local:
  refusal-set-carrier [tower-class]);
new-corpus-intake (7 corpora already intaken,
  driver-automation: automates-new-corpus-intake,
  declaration: registry-exhausted -- NOT unattended-takeable);
refusal-retirement (72 distinct subjects in refused:* groups)
```

* **(a) census-signal-ungating** — one open row, `refusal-set-carrier`, and it
  is **tower-class**.
* **(b) park-lifts** — zero rows in the park ledger.
* **(c) new-corpus-intake** — `registry-exhausted`, quoted above.
* **(d) refusal-retirement** — 72 subjects, but retiring any signal is a
  **PURCHASE-axis call** and belongs to the purchase driver, never here.

**This is BLOCKED, not DEAD.**  Both drivers are firing and correctly finding
nothing they may take; the heartbeat is healthy and this cycle shipped a real
delta.  What is blocked is SUPPLY, and it clears only by a maintainer decision
or a purchase.

## The demand, named

The largest `refused:` groups, which is where the next purchase should be
priced from:

| nodes | signal |
|---|---|
| 17 | `refused:function-symbol` |
| 12 | `refused:symbolic-exponent` |
| **9** | **`refused:complex-carrier`** |
| 8 | `refused:iff-connective` |
| 8 | `refused:prime-predicate` |
| 8 | `refused:recursive-definition` |

`complex-carrier` is the mover: it was **7 two cycles ago** and is **9** now,
grown entirely by this corpus's analytic material (cycle 29's 137/140, this
cycle's 136).  `prime-predicate` is newly at 8 for the same reason.  The
`prime_number_theorem_and` corpus has been telling the loop the same thing
three cycles running — its remaining material needs a carrier and an analysis
vocabulary the fragment has never priced.

**Two exits exist and both are off this axis:**

1. A maintainer appends **one row** to
   `specs/mathsources/corpus_candidates.json` — the declaration point, whose
   URL and rationale a human writes before any yield is known.  That is the
   only lever a corpus firing can walk unattended, and it is one row.
2. The purchase driver prices a bill from the groups above.  Note that the one
   open row, `refusal-set-carrier`, is **tower-class** — and this container
   measured **`lean-local`**, which under PLAN_FRAGMENT §3.1 rule 3 is exactly
   the condition that lets an unattended purchase session take tower-class
   work.  That is a purchase-axis fact recorded here for the purchase driver,
   not an action this cycle may take.

## State

* corpus **125** (unchanged), governed readings **121**, certified **118**
* **ready 3 → 0**; blocked groups 49; refused subjects **70 → 73** (memberships
  131 → 134).  The verdict's own "72 distinct subjects in refused:* groups" is
  a different join — `supply_status` counts subjects reachable in the
  frontier's groups, the projection counts ledger subjects — and both are
  quoted as each tool computed them rather than reconciled into one number.
* census byte-identical (135 / 1521 / 296) — no growth, no re-census delta
* verdict `ready-work-available` → **`supply-blocked: tower-class-only …`**
* derived route `ready` → **`refill`**
* gate: `CGB_LEAN=0 python3 -m pytest tests/ -q`

## Bounds

No ceremony-reserved path in the diff (`kernel/certs.py`, `TRUST.md`,
`buildloop/growth_protocol.py`, `setup.sh`, `ci/`, `.claude/`, `.github/` all
untouched).  P5 not promoted.  No park lifted, none recorded.  Ledgers
append-only.  `tools/FgReflect.lean` and `results/reflect_candidates.json`
untouched; no lean-hammer lane ridden.  **No purchase priced** — every exit
named above is a purchase-axis or maintainer call, and naming one is not
taking it.
