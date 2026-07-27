# C3 cycle 32 — the first carleson batch refuses five for five, and one of the five signals had to be split before it was filed

**Product: five measured refusals, a new refusal signal with its separation
measured in both directions, and a tooth that reds if the separation stops
being true.**  Zero certifications; corpus unchanged at **125** sources, every
DL byte-unchanged.  Ready **5 → 0**.

Probe verdict (RUN here, not read off disk): **`lean-local`**.  No Lean
touched; per-commit gate `CGB_LEAN=0 python3 -m pytest tests/ -q`.

## The route read `ready`, and the batch was the whole of it

The brief opened `NEXT-SELECTION: ready (consume the ready list in frontier
order)` with `ready 5`, all five carleson — the entries cycle 31's intake
created and correctly did not widen to consume.  `--take 8` never bound: the
list held exactly five.

## The five refusals

| src | node | first blocker, verbatim | signal |
|---|---|---|---|
| 134 | `John-Nirenberg` | `unknown term operator 'mu'` | `uninterpreted-function-symbol` |
| 135 | `a0000000013` | `unknown atom/connective 'remainstrue'` | `metatheoretic-subject` |
| 136 | `disjoint-row-support` | `mem references undefined set 'E'` | **`indexed-set-family`** |
| 137 | `pairwise-disjoint` | `mem references undefined set 'M'` | **`indexed-set-family`** |
| 138 | `row-correlation` | `unknown term operator 'intcorr'` | `integral-operator` |

Every signal was checked against the landed purchases before recording (the
cycle-29 discipline as routine).  P8 buys a function symbol the source gives a
BODY for; `mu` has none.  P9 buys a set the source gives a COMPREHENSION for;
these give none.  None of the five re-wedges.

**134 was authored so the recorded blocker is the real one.**  The source
states `μ(A(λ,k,n)) ≤ 2^{k+1-λ} μ(G)`, and the exponent is symbolic — a
careless reading would refuse there and file a verdict about the reading's
carrier choice.  The isolated-exponent probe (the cycle-13 pattern) replaces
both measure terms by plain object refs and gets the second blocker:

```
c: `^` admits a SYMBOLIC exponent only at carrier 'Nat' (non-negative by
construction, so the power stays Monoid.npow); at 'Int' an exponent may be
negative and a reciprocal power leaves the carrier entirely
```

That is `symbolic-exponent-at-int`, and it is **named here rather than
filed**: the gate never reached it, and `k+1-λ` is genuinely sign-indefinite
(λ is unbounded above), so the Nat carrier that would rescue it is not a
faithful reading of this source.  `μ` is the Chebyshev-function shape one
domain over — a measure, definable in principle, given **no definiens by this
source**, which is `uninterpreted-function-symbol` exactly.

**135's blocker is its SUBJECT, and the quoted verdict says so obliquely.**
The source is a remark about constants: it asserts that Theorems 1.1.1 and
1.1.2 "remain true with `2^{44a^3}` instead of `2^{443a^3}`".  The subject of
that assertion is a THEOREM, not a carrier value, and the fragment has no kind
for it — so the most faithful authoring puts the claim under a predicate no
lexicon can contain and the gate refuses at that predicate's name.  The
`unknown atom/connective` verdict is therefore the metatheoretic subject
wearing a predicate name, and it is recorded that way rather than as a missing
operator word.  (The exponent is NOT the blocker here: at `Nat` a symbolic
exponent is admitted.)

**138 is the fourth `integral-operator` row, and the absolute value was
unfolded first** so the recorded blocker is the source's rather than the
reading's.  Behind the integral sit the L² norms, the complex conjugate and
another symbolic exponent; the gate reached the integral, so the integral is
what is filed.

## The headline: a signal split BEFORE it was filed, not after a purchase paid for it

136 and 137 both refuse at "a set the source gives no comprehension for", and
that is exactly what `free-set-variable` already names and what
`refusal-set-carrier` already prices.  Filing them there would have been fast
and wrong, and the cycle-27/29 lesson says why in advance: **a word coarser
than its cause promises a return it cannot make.**  So the separation was
settled against the machinery instead of by preference.

Both subjects' sets are **functions of an index** — `E_j` for each j, `M(k,n)`,
`E_1(p)` for each tile p.  Two readings were written that differ in EXACTLY
one thing, whether each comprehension body mentions the index, and both were
run:

**(1) The family reading is refused STRUCTURALLY, not for missing
vocabulary.**

```
setdef 'ej': body references 'j', which is not its parameter -- a comprehension
body is closed over its parameter, so that a membership site can be eliminated
by substitution alone
```

P9's `setdef` body is closed over its parameter **by construction**, and the
gate states the reason: membership must be eliminable by substitution alone.
A body that varies with a free index breaks that discipline, so **no
set-carrier purchase expresses one**.  The wall is the elimination rule, not
the carrier whitelist — which is precisely what `refusal-set-carrier` is a row
about.

**(2) The non-indexed reading GATES CLEANLY and is then REFUTED by the box.**
Read with sets that do not vary with their index — exactly the shape a
`free-set-variable` / `set-valued-param` retirement would supply — both
subjects pass the gate, are non-vacuous on the box, and are FALSE:

| subject | refuting assignment |
|---|---|
| `pairwise-disjoint` | `p=0, pp=1, x=0` |
| `disjoint-row-support` | `j=0, jp=1, x=0` |

Two sets that do not vary with their index may meet without their indices
agreeing.  So filing these rows under `free-set-variable` would return them to
`ready` on that purchase for a re-measurement **that comes back refuted** —
the promise the coarse word cannot keep, caught before the purchase rather
than after.

`indexed-set-family` is therefore appended to the refusal vocabulary as a
third rung beside P9's two, mapped to **no purchase** in
`SIGNAL_UNBLOCKED_BY` with the reason stated: what it prices is a set-valued
FUNCTION — the definitional-extension axis one level up from
`function-symbol` — and **a row is never authored from a corpus cycle**.

`tests/test_indexed_set_family_class.py` pins all of it: the closure refusal,
the box refutation (with an explicit assertion that a TRUE box would retire
the separation and should say so), the ledger filing, and the `None` in the
shipped map.  7 teeth, all reading the subjects' prose out of the primary
corpus artifact by content hash.

## What moved, and what did not

* Corpus **unchanged at 125** sources; governed readings 121, certified 118;
  governed DL 7195.0, census-of-record 6536.0 — every number byte-identical,
  so **no lineage entry** (the cycle-30 shape: a refusal-only cycle grows no
  corpus).
* Refused subjects **73 → 78**; ready **5 → 0**.
* New blocked groups: `refused:indexed-set-family` **2**,
  `refused:metatheoretic-subject` 2 → **3**,
  `refused:uninterpreted-function-symbol` 3 → **4**,
  `refused:integral-operator` 4 → **5**.
* The five laid-down source files and the readings skeleton were removed: a
  refused subject is demand data, never a corpus source.
* No park recorded or lifted.  No purchase priced.

## The supply reading: this loop is NOT blocked

```
intake-work-available: new-corpus-intake (8 corpora already intaken,
  driver-automation: automates-new-corpus-intake,
  declaration: candidate-available)
route: refill
```

`tools/corpus_candidates.py` selects **`flt`** (Fermat's Last Theorem
blueprint, adapter `blueprint`, declared 2026-07-27) in declaration order,
with `candidate=2` still declared behind it.  That is the NEXT cycle's work,
not this one's: this cycle spent its flywheel action on the ready list, and
widening to a corpus intake in the same firing is exactly the widening the
prompt forbids in the other direction.

## What carleson has now said about this fragment

Cycle 31 measured the corpus's miss histogram and read it as arithmetic-first.
Five subjects later the readings say something narrower and sharper: **this
corpus's material is about MEASURES OF INDEXED FAMILIES OF SETS.**  Four of
the five refusals are one story — an uninterpreted measure applied to an
uninterpreted family (134), the family itself (136, 137), an integral against
that measure (138) — and the fifth is not mathematics at all.  The demand is
not another operator word; it is a set-valued function and a measure on it,
which is two rungs above anything on the board.

## The demand, named

The largest `refused:` groups, which is where the next purchase should be
priced from:

| nodes | signal |
|---|---|
| 17 | `refused:function-symbol` |
| 12 | `refused:symbolic-exponent` |
| 9 | `refused:complex-carrier` |
| 8 | `refused:iff-connective` |
| 8 | `refused:prime-predicate` |
| 8 | `refused:recursive-definition` |

Unchanged at the top — this batch added no mass to any of them, which is
itself the reading: carleson's demand is filed under signals that are new or
near-empty, not under the ones the queue is already priced against.  Retiring
any of these is a **PURCHASE-axis call** and belongs to the purchase driver.

## Bounds

No ceremony-reserved surface in the diff — `kernel/certs.py`, `TRUST.md`,
`buildloop/growth_protocol.py`, `setup.sh`, `ci/`, `.claude/`, `.github/`
untouched.  `tools/FgReflect.lean` untouched; Lean-free cycle, no
`[lean-fast]`.  P5 not promoted.  Ledgers append-only.  No purchase priced.
The refusal-vocabulary append follows the file's own stated rule (grow by
appending, never rename — rows are evidence) and the cycle-28 precedent.

**Gate**: `CGB_LEAN=0 python3 -m pytest tests/ -q` → **1948 passed, 42
skipped** (1941 + 7 new teeth).
