# C3 cycle 18 — the first cycle spent out of the refusal ledger

**Axis:** corpus. **Shipped: 6 sources (123–128). Refusals: 2. Parks: 0.**
Corpus **114 → 120**; governed exogenous coverage **107 → 113**; ready **0 → 0**.
Full suite **1546 passed, 39 skipped**.

Cycle 17 emptied the ready list and said in writing that the corpus loop had
nothing unblocked left to mine. P6 then bought `not` and `iff` and retired three
refusal signals. This is the cycle that spends them — the first intake ever
drawn from the frontier's `refused:` blocked groups, and the first evidence that
the refusal ledger is a *purchase order* and not just a record of misses.

## Selection: 21 memberships, 18 distinct subjects, 8 taken

The three retired groups overlap, so the first job was reconciling them. A
subject listed under two signals is one subject and is intaken **once**:

| group | nodes | distinct new |
|---|---|---|
| `refused:not-connective` | 6 | 6 |
| `refused:iff-connective` | 8 | 5 (3 shared with `not`) |
| `refused:definition-biconditional` | 7 | 7 |
| **union** | **21 memberships** | **18 subjects** |

The ceiling is 8 sources. The rule, stated so it is reproducible: **run the tool
once per retired signal, in the order P6 retired them, sized so the deduplicated
union lands exactly on the ceiling** — `--take 3 / 3 / 2`. The tool's own
already-intaken check does the deduplication, so the second run silently drops
the two lemmas the first run took. No cherry-picking: nothing was reordered to
put a likely green in front of a likely refusal.

    intake_from_frontier.py --unblocked refused:not-connective          --take 3 --apply
    intake_from_frontier.py --unblocked refused:iff-connective          --take 3 --apply
    intake_from_frontier.py --unblocked refused:definition-biconditional --take 2 --apply

**Ten distinct subjects were NOT taken and are carried as demand**, not widened
into this cycle.

## The batch — sources 123–128

| src | subject | what it needed that P6 bought |
|---|---|---|
| 123 | an integer is **even iff not odd** | `not` **and** `iff` |
| 124 | an integer is **odd iff not even** | `not` **and** `iff` |
| 125 | `10 ∉ {n : ℕ ∣ n odd}` | `not` |
| 126 | `5n` is a multiple of 8 **iff** `n` is | `iff` |
| 127 | `n` odd **iff** `n ≡ 1 (mod 2)` | `iff` |
| 128 | `n` even **iff** `n ≡ 0 (mod 2)` | `iff` |

### The negation is left as a `not`, on purpose

`_check_connective_nnf` pushes `not (odd n)` to the dual atom `even n` inside
the gate — that push **is** the purchase. Doing it in the reading instead would
erase the source's own shape and turn 123 into the tautology `even n ↔ even n`,
a reading that says nothing about the word the source actually used. The duality
belongs on the machine's side of the seam, where `_ATOM_DUALS` is witnessed by
both solvers. 123 and 124 are kept as two sources because the corpus states them
as two lemmas and the dual table carries `even → odd` and `odd → even` as two
rows.

### 125 is the ledger's own pricing coming true

Cycle 16 measured `10 ∉ {n : ℕ ∣ n odd}` and recorded **one** row for it —
`not-connective` — explicitly noting that its probe past `not` reached a
positive atom entirely in fragment, so no second row was earned. P6 retired that
one signal and the subject flipped. **The row said `not` was the whole bill, and
it was.** Nothing in this batch is a better argument that the refusal ledger
prices demand accurately rather than merely recording that something failed.

Membership at a **literal** element unfolds definitionally to the
comprehension's body (`Set.mem_setOf_eq`) — the source-121 pattern from cycle
16 — so what survives is the ground `not (odd 10)`, with no objects and no
quantifier. **This is not evidence that the fragment covers sets**, for exactly
the reason cycle 16 wrote down for 121: every 09_Sets subject whose set
*survives* unfolding is still refused.

### 127/128 stay inside the word source 122 bought

Congruence is rendered `dvd(2, n − 1)` / `dvd(2, n − 0)`, the same choice source
122 recorded last cycle and for the same reasons (`dvd` is total where SMT-LIB
leaves `mod` by zero unspecified; the renderings are equivalent for every
modulus). Here it also keeps both readings inside the arity-3 congruence
template `dvd(v0, v1 − v2)` (`op_a7da9abc6817`) that 122 admitted, so the pair is
priced against a word the corpus already owns.

128 keeps the literal **`n − 0`**. "congruent to 0 modulo 2" is the corpus's own
definition instantiated at 0 (`03_Parity_and_Divisibility` definition-005);
folding it to `dvd(2, n)` is an arithmetic step taken on the source's behalf,
not a reading of it.

## Two refusals, and the demand they name

`03_Parity_and_Divisibility` **definition-001** and **definition-002** — the
corpus's own definitions of `odd` and `even` — **refuse**, recorded under
`exists-only-shape`:

    frontier_refusals.py --record 15a32e2e… exists-only-shape --by results/c3_cycle_18.md
    frontier_refusals.py --record e62fefe0… exists-only-shape --by results/c3_cycle_18.md

`iff` is only the **outer** half of what these subjects need. Their definiens is
an **existential** that has to sit *under* the biconditional, and the fragment's
quantifier is a prenex **statement block**. Prenexing it is not an equivalence:
`∀a ∃k (odd a ↔ Q)` is strictly weaker than `∀a (odd a ↔ ∃k Q)`.

**The refusal is earned by measurement, not asserted.** The prenex form was
built and run against the gate with the definiens corrupted:

| prenex definiens | verdict |
|---|---|
| `a = 2k+1` (faithful) | certifies |
| **`a = k` (vacuous)** | **CERTIFIES** |
| `a = 2k` | refuted (no in-bound ∃ witness) |
| `a = 4k+1` | refuted |

The second row is the finding. `∀a (odd a ↔ ∃k, a = k)` says *every integer is
odd* and is plainly false — yet the prenex shape certifies it. So the prenex
form does not carry the definition it claims to render, and shipping it would
have been a green bought by distortion. Refused by name instead.

**Therefore `definition-biconditional` was never one demand.** It was a
connective (retired by P6) wrapped around a **scope** demand the fragment has
not purchased. Splitting it here costs the next purchase driver nothing and
saves it from pricing a bill that would not have unblocked these subjects.

## Honesty: one green is partly coverage

Source **126**'s box has **shallow teeth**, said plainly rather than implied by
the green. The refutation sample is the five smallest instances
(`n ∈ {0, −1, 1, −2, 2}`), so a corruption is separated only when its least
witness falls inside it:

| corruption | verdict | why |
|---|---|---|
| coefficient `5 → 4` | **refuted** at `n = −2` | least witness in sample |
| modulus `8 → 2` | **refuted** | least witness in sample |
| coefficient `5 → 2`, `5 → 6`, `5 → 10` | **certifies** | least witness is `n = 4` |
| modulus `8 → 3/4/6/7/9/16` | **certifies** | least witness outside sample |

(`5 → 3`, `5 → 7`, `5 → 9` are not false variants at all: any coefficient
coprime to 8 makes the biconditional true.) This is the same disposition as
cycle 15's source 119 and cycle 17's transitivity conjunct — demand data for a
wider instance box, never a reason to withhold a faithful reading.

The other five all have refutation-backed teeth: 123/124 refute both dropping
the negation and negating the left arm (at `n = 0`); 125 refutes `odd 10` and
`not (odd 11)`; 127 refutes `odd → even`, residue `1 → 0` and modulus `2 → 3`;
128 refutes `even → odd`, residue `0 → 1` and modulus `2 → 3`.

## MEASURED — a biconditional pays twice

**Two operator words admitted** (9 → 11 mined words, plus the grandfathered
`multiple_of`), both from **one source**:

| word | template | witnesses | uses | delta |
|---|---|---|---|---|
| `op_7625d0b17443` | `dvd(8, v0)` (alias-shaped) | 126, `72_dvd_cancel8`, `74_dvd_both` | 5 | **−4.0** |
| `op_b1b8fe995481` | `dvd(8, 5·v0)` | 126, `72_dvd_cancel8` | 2 | **−2.0** |

Both cross the committed two-witness bar with source 126 supplying the witness
that was missing beside long-standing sources. This is the C2-closure pattern
again, with a wrinkle worth recording: **a biconditional puts both of its arms
into the mining corpus**, which is why a single source moved two templates at
once. Priced modestly and honestly — no bar moved, and `ANTI_LIST`,
`kernel/certs.py`, `TRUST.md` and the escape-gate blocklist are untouched.
Proposals **51 → 53**.

## The macro table grew back

Where cycle 17's GC pass retired five macros, this one retires **one**: governed
final table **11 → 13**, `gc_delta` **−60.0 → −7.0** (refined greedy 6233.0 →
census-of-record 6226.0) against the same threshold-0 law. Six sources' worth of
new uses is exactly the kind of thing that lifts four macros back over the bar.
The tower census follows: max **realizable** MM adjacency **0 → 3** (raw
32 → 18, spread over a larger table), with **still zero pairs at or above the
≥7 bar**, so the T1 gate stays correctly deferred — as in every era of that
measurement. Cluster key **`all_pass = True`**, all six verdicts.

## Re-baseline and state

`registration.json` carries a cycle-18 lineage entry: **120** sources, waves
**0–14**, **116 readings / 113 certified**, stream **3165** over alphabet 69,
governed DL **6883** vs ungoverned **7293** (naive **8552**), census-of-record
governed 13 @ **6226**, ungoverned 14 @ 6005, refined-greedy 6233. Final-wave
gaps: hindsight **−410**, prequential **−290**.

Ordinary corpus-growth pins moved and were re-anchored to the live measurement
with their comments brought up to date, never loosened: `test_c2_report`,
`test_entropy_refs` (order-0, LZ77 phrases, context stats),
`test_operator_prompt_seam`, the `test_cluster_key` GC pin, and the
`test_tower_census` adjacency pins.

## Ready-list movement, measured

**Ready 0 → 0.** The window is still purchase-gated; the corpus axis did not
regain unblocked ready material. But the number that moved is the one under it:

| | before | after |
|---|---|---|
| ready | 0 | 0 |
| blocked groups | 29 | 29 |
| refused **subjects** | 46 | 46 |
| refused group **memberships** | 61 | **63** |
| distinct subjects behind the three retired signals | 18 | **12 carried** |

The subject count does **not** move, and that is the correct reading rather than
a disappointment: both new rows land on subjects that already carried
`definition-biconditional`. A signal split adds a *signal*, never a subject —
non-destructive, exactly as cycle 16 recorded when it split `set-membership`
out. What moved is the memberships, which is where the new demand actually is.

### A reading of the frontier worth recording

The three retired groups' node counts are **unchanged** (6 / 8 / 7) even though
six of their subjects are now committed sources. That is `tools/frontier.py`
working as written: the `refused:` check precedes the intaken check, because the
ledger is **append-only and its rows stand** as the pre-purchase reading. The
consequence is that those group counts now **over-report live demand by six**.
`intake_from_frontier._select` drops already-intaken nodes defensively, so no
future cycle can re-add them — the effect is on what the frontier *reports*, not
on what it hands out. Recorded here as a measurement rather than patched inside
a corpus cycle.

## Carried-over demand

Ten of the eighteen distinct subjects behind the three retired signals were not
taken (the ceiling bound first, not the clock), and two more are now refused
under `exists-only-shape` — **12 carried**. The untaken ten are mostly the
09_Sets block (`problem-005/014/015/017`, `definition-003`) plus the remaining
`03_Parity_and_Divisibility` definitions, and they are carried as demand, never
widened into this cycle. So the next corpus cycle has **work it can start
without waiting on a purchase** — the first time that has been true since cycle
15. `ready` will still read 0 (the ledger's rows stand), so the lever is the
same `--unblocked` run, not `--ready`.

The largest demands on the board are unchanged: the out-of-fragment blocks
(`magmas-equational` 156, `rational-arithmetic` 156, `real-analysis` 152,
`entropy-log` 123, `probability-mass` 116, `sequences-sums` 111,
`sets-cardinality` 102, …) and, on the refusal axis, `symbolic-exponent` 12,
`function-symbol` 11 and the newly split `exists-only-shape` 5.

No trust-root edits (`kernel/certs.py`, `TRUST.md`, escape-gate blocklist,
`ANTI_LIST` untouched); **P5 not executed**. Lean-free cycle; statement-cert
deferred in-container and recorded as deferred, never as a pass.
