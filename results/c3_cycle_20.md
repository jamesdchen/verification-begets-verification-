# C3 cycle 20 — the last zero-cost path (d) window measured SHUT

**Axis:** corpus. **Shipped: 0 sources. Refusals: 0 new rows. Parks: 0.**
Corpus **121 → 121**; governed exogenous coverage **114 → 114**; ready **0 → 0**.
Full suite green.

This cycle mined no source, and that is its result rather than its failure. It
took the one measurement the house law had left outstanding, and the measurement
came back the opposite way from the reading §1 carried — so the delta is a
**corrected supply reading**, and it closes the corpus loop's last
non-purchase-gated window.

## What §1 claimed, and why it had to be tested

§1 named two refusal groups "already MET without any purchase" and drew this
conclusion from them:

> of those 5 rows only the 3 `cmp-outside-lexicon` nodes (2 distinct subjects,
> one of them verbatim-equal across two nodes) have their WHOLE refusal set
> already met, so they are what path (d) can test TODAY at no purchase cost

That sentence was the **only** thing on the board saying the corpus loop could
move without a purchase and without a maintainer-named corpus. It also ended,
correctly, with "whether any of them certifies at the grown fragment is a
MEASUREMENT the next cycle takes, never a promise made here." This is that
cycle, and the promise it declined to make is the one the measurement refuses.

The window is still open on the tree, not merely in prose — computed here from
the ledger and the sources rather than recalled. Of 45 refused subjects, 9 have
their whole signal set met; 7 of those were consumed by cycles 18 and 19 (their
text hashes are intaken sources today), leaving exactly two:

| subject | node(s) | signal set |
|---|---|---|
| `11908b9b…` | `01_Proofs_by_Calculation#problem-016`, `02_Proofs_with_Structure#problem-006` | `{cmp-outside-lexicon}` |
| `175d8008…` | `01_Proofs_by_Calculation#problem-021` | `{cmp-outside-lexicon}` |

> Let \(x\) and \(y\) be integers, and suppose that \(x + 3 \le 2\) and
> \(y + 2x \geq 3\). Show that \(y > 3\).

> Let \(n \geq 5\) be an integer. Show that \(n^2 > 2n + 11\).

Both are ordinary integer order statements over vocabulary the fragment has
owned since the beginning. Nothing exotic is in the way. What is in the way is
one atom.

## The measurement: four probes through `certify_statement`

Not argued — run, at `bound=8`, against the fragment as it stands at
`de63273`:

| probe | reading | result |
|---|---|---|
| 1 | 021 in the source's own relation: `>(n^2, 2n+11)` | **REFUSED at `math-reading-gate`** — `unknown atom/connective '>'` |
| 2 | 021 flipped: `<(2n+11, n^2)` | **certifies** — gate/nonvacuity/compile/instances all pass |
| 3 | 016 in the source's own relations: `>=` hypothesis, `>` conclusion | **REFUSED at `math-reading-gate`** — `unknown atom/connective '>='` |
| 4 | 016 flipped: `<=(3, y+2x)` hypothesis, `<(3, y)` conclusion | **certifies** — same four layers pass |

(`statement-cert` is `deferred: lean toolchain absent` on both greens — no local
Lean in remote containers; recorded as deferred, never as a pass.)

So the refusal cycles 02/03/04/05 recorded is **reproduced exactly, today**, and
it is mechanical: `generators/math_reading.py::_BUILTIN_ATOM_OPS` is
`{"=", "!=", "<=", "<"}`, and the gate rejects `>`/`>=` outright before any
solver runs.

## Why the flipped green is not shipped

Probes 2 and 4 say a green is available this session for both subjects. It is
declined, and the reason is fidelity rather than capability, so it is written
down instead of implied.

`a > b` and `b < a` are the same proposition — Lean itself defines `>` as the
converse of `<`. What the flip changes is not the mathematics but the **written
order of the source**, and this corpus's readings discipline has already ruled
on that class of rewriting in the affirmative direction. Cycle 19, authoring the
one source that certified there, kept a quadratic as `(a^2 - 5a) + 5` rather
than folding it, and said why: *"the source's spelling, not an arithmetic step
taken on its behalf."* Reversing `n^2 > 2n + 11` into `2n + 11 < n^2` is a step
taken on the source's behalf of exactly that kind, and it is the whole distance
between a refusal and a green here — which is precisely when the honesty rule
binds hardest.

Corroborating, and the reason this is discipline rather than one session's
taste: **of 121 intaken sources, zero contain `>` or `>=` in their prose.** No
cycle has ever taken this shortcut. Four cycles measured these two subjects and
four cycles refused them.

## The correction: the operator mint cannot reach this signal

`SIGNAL_UNBLOCKED_BY["cmp-outside-lexicon"]` read: *"a comparison the
operator-words grower can price as an ordinary word; that mechanism already
exists, so this is a candidate for the operator mint."* That is wrong, and
structurally so — the same defect class as the false zero the refill projection
was built to retire.

The operator-words grower mines **templates over readings** by description
length. An atom op is not a template: it is the vocabulary a reading is built
from, and the gate refuses a reading containing `>` **before** any reading using
it can exist to be mined. The mint can never reach `cmp-outside-lexicon`,
because the mint's input is the thing the signal forbids. A mechanism that
exists is not a mechanism that applies.

The honest home is a small **atom-lexicon purchase** — `>`/`>=` as genuine atom
ops with their duals, eval, SMT mirror, Lean rendering and divergence teeth,
whatever a bill for that comes to. This cycle does **not** price it: authoring a
§4 row is purchase-axis work, and a corpus cycle never opens one. The mapping
therefore stays `None`, with the corrected reason recorded beside it.

## Ledger: nothing appended, deliberately

No new refusal row was written. The ledger is append-only and its rows **stand
as the reading**; the cycle-05 rows for these two subjects are the same
measurement this cycle re-took at an *unchanged* fragment. A duplicate row would
inflate `cmp-outside-lexicon` from 3 memberships to 6 and read as fresh
independent demand, which would be a distortion in the direction that flatters
the loop. The re-measurement lives here, in the receipt, where it belongs.

## What this leaves the corpus loop

Every remaining refused subject is now held by at least one signal no landed
purchase meets. Stated as the supply reading, with the numbers derived:

| path | state after this cycle |
|---|---|
| (a) purchase un-gates a census signal | EMPTY — structural (the portfolio census is lexical; P3/P4 both returned zero) |
| (b) a decision PR lifts a park | EMPTY — the park ledger has zero rows |
| (c) new-corpus intake | AVAILABLE, and **the only lever a driver can pull** — needs a maintainer-named near-fragment corpus |
| (d) retire a measured refusal | **zero-cost inventory now zero**; 46 subjects / 68 memberships wait behind purchases (`refusal-symbolic-exponent` 12, `refusal-function-symbol` 11, `refusal-set-carrier` 4, and the atom-lexicon row this cycle names) |

The corpus loop is therefore **starved, not broken** — the cycle-17 reading,
now with its last exception measured away. It moves again when the maintainer
names a corpus for path (c), or when the purchase loop lands one of the open
rows. An idle corpus loop with a healthy heartbeat stays a SUPPLY reading.

## Boundaries

No carrier, node class, operator word or trust root grows. `kernel/certs.py`,
`TRUST.md`, the escape-gate blocklist and `ANTI_LIST` untouched; **P5 not
executed**. Lean-free cycle. The only edits are this receipt, the corrected
reason string in `tools/purchase_frontier.py`, the §1 supply reading, the
regenerated `results/purchase_frontier.json`, and one telemetry row.
