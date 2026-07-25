# C3 cycle 17 — the last ready subject, and the word it bought

**Axis:** corpus. **Shipped: 1 source (122). Refusals: 0. Parks: 0.** Corpus
**113 → 114**; governed exogenous coverage **106 → 107**; ready **1 → 0**. Full
suite **1239 passed, 35 skipped**.

This is a one-source cycle because cycle 16 left the ready list at exactly one
entry. It is not a small cycle: the single source flipped a previously
**priced-refused** operator word into the fragment, and it emptied the intake
window.

## The batch — source 122

| src | subject | what it adds |
|---|---|---|
| 122 | congruence mod `n` on ℤ is an **equivalence relation** | the corpus's first `10_Relations` source |

### The relation vanishes, the way source 121's set did

The fragment has no relation objects and no second-order quantifier. This
subject never needs one: `~` is **defined in the source itself, at the point of
use**, by an in-fragment condition. Unfolding it is definitional, not a
relocation of the demand onto some corpus definition the fragment also lacks
(contrast `defined-predicate`, cycle 12). What survives the unfolding is exactly
what the phrase "is an equivalence relation" **demands**, written out:

```
forall n x y z.  n | (x - x)                                        (reflexive)
              /\ (n | (x - y) -> n | (y - x))                       (symmetric)
              /\ (n | (x - y) /\ n | (y - z) -> n | (x - z))        (transitive)
```

The single shared binder is notation, not strengthening: Int is non-empty, so
quantifying all four variables over the conjunction is equivalent to quantifying
each conjunct over only the variables it uses.

One object, `z`, is **not named in the prose**. Transitivity needs a third
element and the source names only `x` and `y` in its definition of `~`; `z` is
grounded in the phrase that demands transitivity ("is an equivalence relation"),
which is genuinely where it comes from. Recorded rather than glossed.

### Why `dvd(n, x - y)` and not source 118's residue equality

**Both renderings were measured; both certify.** The choice is recorded:

- they are **equivalent for every `n`** (Mathlib's `Int.modEq_iff_dvd`), so this
  is a choice between equivalent readings, never a weakening;
- `dvd` is **total at `n = 0`** — it compiles to `(ite (= n 0) (= (x-y) 0) …)` —
  whereas SMT-LIB leaves `mod` by zero unspecified, and "Let `n` be an integer"
  admits `n = 0`;
- under residue equality **all three conjuncts collapse into properties of `=`
  itself** (reflexivity becomes the syntactic tautology `t = t`), so the reading
  would carry no divisibility content at all.

## Honesty: the box has teeth on TWO of the three conjuncts

Four deliberately false variants were measured against the same gate:

| false variant | verdict |
|---|---|
| unconditional congruence (`n ∣ x−y` with no hypothesis) | **refuted** at `{n:0, x:−1, y:0, z:0}` |
| reflexivity corrupted to `n ∣ x` | **refuted** at `{n:0, x:−1, y:0, z:0}` |
| symmetry consequent corrupted to `n ∣ (y−x−1)` | **refuted** at `{n:0, x:0, y:0, z:0}` |
| **transitivity conclusion corrupted from `n ∣ (x−z)` to `n ∣ (x+z)`** | **CERTIFIES** |

The last row is the finding. The five smallest hypothesis-satisfying instances
are the origin and its four unit neighbours —
`{0,0,0,0}, {−1,0,0,0}, {0,−1,0,0}, {0,0,−1,0}, {0,0,0,−1}` — so `z = 0` in four
of them and the fifth has a false antecedent. The box never separates `x − z`
from `x + z`.

**The transitivity conjunct's green is coverage, not a refutation-backed
verdict.** Said plainly here rather than implied by a green, in the same spirit
as cycle 15's source 119 caveat — and, as there, it is demand data for a wider
instance box, not a reason to withhold a faithful reading.

## MEASURED — one source flipped a refused word into the fragment

**`op_a7da9abc6817` — the arity-3 congruence template `dvd(v0, v1 − v2)` —
admitted.** This is the C2-closure pattern in its cleanest form yet, because the
before/after is on the record:

| | cycle 16 (staged, refused) | cycle 17 (admitted) |
|---|---|---|
| delta | **+8.0** (4012 → 4020) | **−16.0** (4129 → 4113) |
| saving vs model bits | 12.0 vs 20.0 — *did not pay for itself* | 36.0 vs 20.0 |
| uses | 3 | **9** |
| mined witnesses | `31_cd_diff`, `37_db_diff` | `122`, `31_cd_diff`, `37_db_diff` |

Source 122's reading uses the template **four times** (once per congruence
occurrence across the three properties), which is what took it over the bar. The
word was refused last cycle by the same law that admits it now — no bar moved,
no rule changed, and `ANTI_LIST`, `kernel/certs.py`, `TRUST.md` and the
escape-gate blocklist are untouched.

Worth contrasting with cycle 16's admission, which that cycle flagged for
reading narrowly: `op_a59eb3ce175d`'s two witnesses were the Nat and Int forms of
one book theorem, i.e. a carrier pair. This one's three mined witnesses are
**three independent subjects** — two long-standing difference-divisibility
sources and the new relations subject. Admitted words **8 → 9** (plus the
grandfathered `multiple_of`). Proposals stay at **51**: the miner staged nothing
new this cycle.

## The macro table shrank

The grown corpus re-priced the census-of-record table: governed final table
**13 → 11 macros**, with the GC pass retiring **five** macros (`gc_delta`
**−60.0**, refined greedy 6006.0 → census-of-record 5946.0) against the same
threshold-0 law. The tower census follows it down: max **realizable** MM
adjacency **3 → 0** (raw 18 → 32), with still zero pairs at or above the ≥7 bar,
so the T1 gate stays correctly deferred — as it has in every era of that
measurement. Both the retired count and the adjacency height are moving corpus
measurements; the law and the deferral are what the teeth hold.

## Re-baseline and state

`registration.json` carries a cycle-17 lineage entry: **114** sources, waves
**0–14** (122 joins wave 14), **110 readings / 107 certified**, stream **3065**
over alphabet 67, governed DL **6663** vs ungoverned **7093** (naive **8287**),
census-of-record governed 11 @ **5946**, ungoverned 12 @ 5835, refined-greedy
6006. Final-wave gaps: hindsight **−430**, prequential **−310**. Cluster key
**`all_pass = True`** (all six verdicts, `b_evenodd_survives` included).

Ordinary corpus-growth pins moved: `test_c2_report`, `test_entropy_refs`,
`test_operator_prompt_seam`, the `test_cluster_key` GC pin, and the
`test_tower_census` adjacency pins — each re-anchored to the live measurement
with its comment brought up to date, never loosened.

### One tooth extended rather than re-pinned

`test_frontier.test_park_is_reversible` exercises park→lift mechanics by parking
the **ready head** when the committed park ledger is empty. With ready now empty
it had no head to park and raised `IndexError`. An exhausted intake window must
not silently retire a tooth, so the scratch view now drops the **refusal ledger**
(scratch-only — the committed ledger is untouched) to recover material, and
asserts loudly if even that leaves nothing. The tooth still measures exactly what
it measured before.

## Carried-over demand: the window is EMPTY

**Ready 0**, 28 blocked groups. Every remaining census subject sits behind a
named signal — the large out-of-fragment blocks (`magmas-equational` 156,
`real-analysis` 136, `rational-arithmetic` 135, `probability-mass` 116,
`algebra-structures` 97, `maps-functions` 85, `primality` 69,
`polynomials-fields` 60, `graphs-combinatorics` 41, `geometry-topology` 33,
`entropy-log` 3) plus 17 `refused:` groups carrying the fragment's measured
demands (`iff-connective` 8, `definition-biconditional` 7, `not-connective`,
`set-membership`, `function-symbol` 11, `symbolic-exponent`, `div-operator`,
`exists-only-shape`, and the rest).

Cycle 16 flagged that the corpus axis was running out of ready material; this
cycle consumed the last of it. **The corpus loop now has nothing unblocked to
mine at the current fragment**, and the next driver firing will exit on an empty
ready list until a purchase un-gates a signal. The flywheel's next turn belongs
to the **purchase driver** — and the three demands the set block named
(propositional negation, the biconditional, a set carrier) are the nearest
targets on the record.

No trust-root edits (`kernel/certs.py`, `TRUST.md`, escape-gate blocklist,
`ANTI_LIST` untouched); **P5 not executed**. Lean-free cycle; statement-cert
deferred in-container and recorded as deferred, never as a pass.
