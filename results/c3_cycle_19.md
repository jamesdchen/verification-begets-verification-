# C3 cycle 19 — the second refusal-ledger batch, and the first spent with no purchase in between

Corpus 120 → **121**.  Governed exogenous coverage 113 → **114**.  One source
certifies; **five refusals** are recorded as first-class demand data.

## Selection: the precedence rule applied by hand

P6 retired `not-connective`, `iff-connective` and `definition-biconditional`.
Cycle 18 spent eight of the eighteen distinct subjects behind them and carried
twelve.  This cycle spends the subset of that carry whose **whole refusal set**
those three retirements meet — which is the frontier's own precedence rule
(a subject returns only when EVERY signal filed against it is met), and which
**`intake_from_frontier --unblocked` does not apply**: it hands out the first
`--take` nodes of one named group, blind to the other signals its subjects
carry.  So the rule was applied by the driver, against
`results/frontier_refusals.jsonl`, before anything was laid down:

| subject | ledger signals | spendable today |
|---|---|---|
| `09_Sets#problem-014` | not-connective, iff-connective | **yes** |
| `09_Sets#problem-015` | not-connective | **yes** |
| `04_Proofs_with_Structure_II#problem-015` | iff-connective | **yes** |
| `03_Parity_and_Divisibility#definition-003` | definition-biconditional | **yes** |
| `03_Parity_and_Divisibility#definition-004` | definition-biconditional | **yes** |
| `03_Parity_and_Divisibility#definition-005` | definition-biconditional, mod-operator (met) | **yes** |
| `09_Sets#problem-017` | not-connective, **set-membership** | no |
| `09_Sets#problem-005` | iff-connective, **exists-only-shape** | no |
| `09_Sets#definition-003` | definition-biconditional, **set-membership** | no |
| `03_Parity_and_Divisibility#definition-001/002` | definition-biconditional, **exists-only-shape** | no |
| `04_Proofs_with_Structure_II#definition-001` | definition-biconditional, **predicate-variable** | no |

Six taken — under the ceiling of 8, so the ceiling did not bind and nothing was
left out for room.  The six that were NOT taken carry a live signal; re-measuring
an unmet block is the cycle-05 re-wedge, not a new reading.  Nothing was
reordered to put a likely green in front of a likely refusal: all six were laid
down, all six were probed, and the five that refused had their source files
removed (a refused subject is demand data, never a corpus source).

## The one green: source 129

`04_Proofs_with_Structure_II#problem-015` — *"Let \(a\) be an integer. Show that
\(a^2-5a+5 \le -1\) , if and only if \(a\) is 2 or 3."*

Certifies in **both** bench arms (wave 15).  It is the first source in the
corpus to put P6's `iff` around an **order** atom rather than a parity or
divisibility one, and the first to need `or` on an arm of a biconditional — so
it prices the connective purchase against arithmetic the fragment already owned
instead of re-buying parity.  `^(a, 2)` is the admitted squaring template
(`op_34e1b706c47c`), and the quadratic is kept in the source's own written order
`(a^2 - 5a) + 5` rather than folded.

**The teeth are SHALLOW, and that is recorded rather than implied by the green.**
The instance box is the five smallest instances (a ∈ {0, −1, 1, −2, 2}) and the
true solution set is exactly {2, 3}, so **3 lies outside the sample**.  Measured,
not guessed:

| corruption | verdict |
|---|---|
| drop `a = 3` (`… <-> a = 2`) | **CERTIFIES** — no witness in the box |
| `a = 3` → `a = 4` | **CERTIFIES** — no witness in the box |
| bound `-1` → `-2` | REFUTED at a = 2 |
| coefficient `5` → `4` | REFUTED at a = 2 |

Every corruption that moves only the RIGHT arm survives; what the box separates
is the LEFT arm, where a = 2 is inside the sample.  This green is therefore
**partly COVERAGE** in the cycle-15/17/18 sense.  What it names is demand for an
instance box reaching past the five smallest — never a reason to withhold a
faithful reading.

## Five refusals, each earned by measurement

### `exists-only-shape` (2 rows): definitions 003 and 004

`03_Parity_and_Divisibility#definition-003/004` — *"A natural number \(b\) is
divisible by another natural number \(a\) , if there exists a natural number
\(c\) , such that \(b=ac\)"* and its integer twin.

The faithful statement needs the ∃ **under** the biconditional; the fragment's
quantifier is a prenex **statement block**, so the ∃ can only sit outside it.
This is the same refusal cycle 18 recorded for definitions 001/002 — but the
measurement here is **sharper than cycle 18 could take**, and it is worth
stating exactly why.

The ∃-aware bounded-shadow gate **genuinely runs** on these readings
(`instances: bounded-shadow pass, backend exists-finitized-enum, bound 8,
outer-admitted 81`).  They are not honest-skipped.  They certify.  And they
**keep certifying when the definiens is emptied**:

| reading (∀b,a ∃c) | verdict |
|---|---|
| `dvd(a,b) <-> b = a*c` (faithful spelling) | certifies |
| `dvd(a,b) <-> b = c` — names neither divisor nor product | **certifies** |
| `dvd(a,b) <-> b = c + 0` | **certifies** |
| `even(b) <-> b = a*c` — corrupting the *definiendum* | REFUTED |

A gate that passes a definition whose definiens has been replaced by `b = c` is
not evidence for the definition.  The prenex-∃ shape carries no definitional
content at all: for any a, b a witness c can be chosen after the fact to make
the biconditional true.  (That the definiendum corruption IS refuted shows the
box is not toothless in general — the emptiness is specific to what sits under
the connective.)  So `definition-biconditional` remains, as cycle 18 put it,
a connective wrapped around a **scope** demand the fragment has not purchased.

### `defined-predicate` (1 row): definition 005

`03_Parity_and_Divisibility#definition-005` — *"The integers \(a\) and \(b\) are
congruent modulo \(n\) , if \(n\mid (a - b)\)"*.

Both `mod-operator` and `definition-biconditional` are met, so this subject was
mechanically spendable — and it still has no faithful reading, for a reason the
ledger had not yet named.  The fragment has **no atom for "congruent modulo"**:
cycle 18 established (sources 127/128, and citing *this very definition* as its
warrant) that congruence is rendered as `dvd(n, a - b)`.  So the definiendum and
the definiens render to the *same* term and the only in-fragment reading is the
tautology `dvd(n, a-b) <-> dvd(n, a-b)` — which certifies, and says nothing.
That is exactly the hazard cycle 18 named for source 123 ("doing the push here
would turn the reading into the tautology `even n <-> even n`"), arriving this
time with no way to avoid it.

Recorded under `defined-predicate`: what this subject asks for is a *defined
predicate symbol* the fragment can introduce and then characterise, not another
connective.  (Noted as measurement, not as a second ledger row: the corrupted
definiens `n | (a+b)` also certifies against the five-smallest box, so this
subject's box is shallow too.)

### `set-membership` (2 rows): problems 014 and 015

`09_Sets#problem-014` — *"\(\{n:\mathbb{Z}\mid n\text{ even}\}^{c}=
\{n:\mathbb{N}\mid n\text{ odd}\}\)"*.  The pointwise reading
`not even(n) <-> odd(n)` **certifies**, and it was refused anyway.  It is not a
reading of this source: it takes the extensionality step on the source's behalf
(the fragment has no set objects and no extensionality principle), and it
silently reconciles the source's own **ℤ / ℕ mismatch**, which is the
mathematical content of the problem.  Certifying it would be distorting a
reading to force a green.  Cycle 18 had already written the standing verdict
this honours: *"every 09_Sets subject whose set SURVIVES unfolding (problems
005/014/015/017, definition-003) is still refused."*

`09_Sets#problem-015` — *"\(\{n:\mathbb{Z}\mid n\equiv 1\mod 5\}\cap
\{n:\mathbb{N}\mid n\equiv 1\mod 5\}=\emptyset\)"*.  Refused by the **gate
itself**, with a named miss:

> `dvd` has no negation dual in the fragment, so a negation cannot be pushed to
> an atom

Worth recording as its own reading, because it prices something P6 did not buy:
P6's negation-normal form pushes `not` to an atom **dual**, and `_ATOM_DUALS`
carries the parity pair only.  A negated `dvd` has nowhere to go.  The ledger
row is `set-membership` (the demand that would actually admit the subject —
its sets survive unfolding exactly as problem-014's do), and the missing
`dvd` dual is stated here rather than minted as a new signal: inventing
purchase-axis vocabulary inside a corpus cycle would price a purchase this
cycle did not measure.

## One session-hygiene note, recorded rather than quietly fixed

A `bench_formalize.py --help` probe in this session did not print help: the
file has no argparse, so `main()` fell through to `run_bench()` with the
**default LLM author**, and before it was killed it appended a *metered*
governed checkpoint record for source 129 — 32252/2182 tokens, carrying a
reading this session never authored and never verified (its `reading_json`
hashed differently from the inline one).  Both wave-15 records were dropped
from `results/formalize_bench_state.jsonl` (leaving it byte-identical to its
committed state) and the bench was re-run with the session-inline author only.
The corpus reading committed here is therefore the one in
`wp_c17_readings.py`, and the whole live run is unmetered — which the
`cumulative_ktokens_*` columns now show as 0 on every row, and which
`test_live_csv_extends_frozen_prefix_with_new_waves` re-checks.  The governed
final-wave DL differs between the two runs (6959.0 with the LLM reading,
**6963.0** with this one); 6963.0 is what is registered, because it is what
the committed reading measures.

## Ready-list movement, measured

| | before | after |
|---|---|---|
| ready | 0 | 0 |
| blocked groups | 29 | 29 |
| refused **subjects** | 46 | 46 |
| refused group **memberships** | 63 | **68** |
| top-level sources | 120 | **121** |
| governed exogenous coverage | 113 | **114** |

The subject count does not move: all five refusals land on subjects the ledger
already held.  Memberships +5 is where the new demand actually is.  `ready`
stays 0 and stays purchase-gated — as cycle 18 wrote, the lever for a carried
subject is the `--unblocked` run, never `--ready`, because the ledger's rows
stand.

**The carry is now spent.**  Of the twelve subjects cycle 18 carried, six were
spendable under the precedence rule and all six were taken here.  The remaining
six each carry a live signal (`set-membership` ×2, `exists-only-shape` ×2 plus
the two definitions cycle 18 refused, `predicate-variable` ×1), so the next
corpus cycle has **no non-purchase-gated work from the P6 window** — path (c),
new-corpus intake, or a purchase is what moves it next.  Said plainly so the
next firing does not re-derive it: this cycle closes the window P6 opened.

The largest demands on the board: out-of-fragment blocks (`magmas-equational`
156, `rational-arithmetic` 156, `real-analysis` 152, `entropy-log` 123,
`probability-mass` 116, `sequences-sums` 111, `sets-cardinality` 102) and, on
the refusal axis, `symbolic-exponent` 12, `function-symbol` 11, and now
`exists-only-shape` **7** — which this cycle's corruption probe prices more
precisely than any census term can: it is a **scope** purchase, not a
connective one.

No new operator word crossed the admission bar (52 proposals emitted, 22
non-alias).  No carrier, node class or trust root grows.  `kernel/certs.py`,
`TRUST.md`, the escape-gate blocklist and `ANTI_LIST` are untouched; **P5 not
executed**.  Lean-free cycle; the statement-cert layer is `deferred: lean
toolchain absent` in-container and is recorded as deferred, never as a pass.
