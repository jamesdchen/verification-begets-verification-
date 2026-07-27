# C3 cycle 26 — the purchase met one half of the word it retired

**Product: the measurement that separates a signal that was covering
three rungs, and sixteen refusal-ledger memberships recording it.**  Eight subjects,
drawn by `--unblocked` from a group a landed purchase had retired, all eight
measured through the reading gate, **zero certified**.  No source lands, so
`specs/mathsources/registration.json` re-baselines only its lineage: **121
top-level sources and governed DL 6963.0 are unchanged and deliberately so.**

This is the first cycle to consume the `--unblocked` route end to end.  Cycle
25 fixed the route's *subject* precedence and shipped no reading; this cycle
ran the fixed route, and what it found is the same defect one level down —
**in the signal vocabulary rather than in the selection over it.**

## The take

`NEXT-SELECTION` routed `unblocked` with five signals and 23 paid subjects.
The first command, `--unblocked refused:definition-biconditional`, printed
`refills NOTHING — all 7 of its nodes are held by an unmet signal`, which is
cycle 25's fix working on the exact group that produced it.  The second,
`--unblocked refused:function-symbol --take 8`, selected its eight and held
five `prime_number_theorem_and` subjects by name.  Those eight are this
cycle's take, and the 45-minute / N=8 ceiling binds there: the remaining
groups stay carried-over demand.

## What the gate said

Every verdict below is the gate's own text, copied from the run.

| # | node | faithful reading attempted | gate verdict (verbatim) | signals filed |
|---|---|---|---|---|
| 130 | `equational_theories/edge-disjoint` | `L_y`, `L_z` as defined functions, applied at `n` | `definition 'ly': body references 'x', which is not one of its parameters — a definition body is closed over its parameters, so that a use site can be eliminated by substitution alone` (`funcdef:open-body`) | `uninterpreted-function-symbol`, `iterated-application` |
| 131 | `math2001/06_Induction#problem-005` | `b` introduced by its recurrence, `odd(b(n))` | `definition 'b': the body applies the function being defined — a recurrence has no finite unfolding at a symbolic index, and discharging one needs well-founded recursion the fragment does not have` (`funcdef:recursive-body`) | `recursive-definition`, `elided-sequence-definition` |
| 132 | `#problem-006` | `mod(x(n), 4) = 1` | `app references undefined function 'x' — a function must be introduced by a 'definition' statement EARLIER in the reading than its first use` | `recursive-definition`, `elided-sequence-definition` |
| 133 | `#problem-007` | `x(n) = 2^(n+2) + 1` | same, on `'x'` | `recursive-definition`, `elided-sequence-definition` |
| 134 | `#problem-009` | `dvd(d, factorial(n))` · then `dvd(d, bigprod(i, 1, n, i))` | `unknown term operator 'factorial'` · `bigprod: hi bound must be a LITERAL — bounded iteration is what makes the class decidable (exhaustive computation, SMT unrolling); a symbolic bound is not in the fragment` | `factorial-operator`, `bigop-symbolic-bound` |
| 135 | `#problem-010` | `2^n <= factorial(n+1)` · then the same as a `bigprod` | same two verdicts | `factorial-operator`, `bigop-symbolic-bound` |
| 136 | `#problem-011` | `a(n) = 2^n + (-1)^n` | `app references undefined function 'a'` … | `recursive-definition`, `elided-sequence-definition` |
| 137 | `#problem-012` | `or(mod(a(m),6) = 1, mod(a(m),6) = 5)` under `1 <= m` | same, on `'a'` | `recursive-definition`, `elided-sequence-definition` |

## The headline: one word was covering three rungs

All eight subjects were demoted by a **`function-symbol`** refusal.  P8
(`refusal-function-symbol`) met that signal and the projection returned all
eight to the unblock window.  **All eight refuse again — and not one of them
refuses on anything P8 got wrong.**

P8 bought a symbol given by an *explicit, non-recursive* body.  That is what
made it free: such a symbol is eliminable by substitution, so nothing entered
`Tm`/`Pd` and `decDenote` kept deciding by computation.  Its own docstring
names the boundary in advance —

> `funcdef:recursive-body` … A recurrence is the headline demand this row
> does **NOT** buy.

What overpromised was not the bill but the **map entry**, written before the
bill existed, which filed under `function-symbol`:

> an arbitrary NAMED function (**factorial, the sequences a_n/d_n/F_n**, the
> Bezout coefficients) needs a definitional-extension mechanism

Factorial and the sequences are exactly subjects 131–137.  So one word was
standing for three separable rungs, and a purchase that honestly bought the
first retired the word for subjects needing the second and third:

| rung | what it needs | this cycle's signal | met by P8? |
|---|---|---|---|
| explicit non-recursive body | substitution at the gate | `function-symbol` | **yes** |
| recurrence | well-founded recursion + termination | `recursive-definition` | no — declined by name |
| axioms only, no body | application node in `Tm` + a `Decidable` story | `uninterpreted-function-symbol` | no — unreachable by desugaring |

The third rung is precisely the cost
`tests/test_function_symbol_class.py` finding (4) priced, and which P8
correctly declined to pay *because its own symbols were eliminable*.  That
price now has a row to sit on instead of being carried, invisible, inside a
word that reads as purchased.

**This is not a fault in P8.**  P8's re-census delta and its conservativity
battery are unaffected, and every word of its receipt remains true.  What is
newly measured is that *retiring a signal is not the same as returning its
subjects*, and the ledger had no way to say so until the word was split.

## The second finding: a definition the corpus does not carry

`elided-sequence-definition` is measured against the **corpus**, not the gate,
and it reproduces in one command: **no node of `math2001` defines `b_n`, `x_n`
or `a_n`.**  Scanning all 260 nodes for any defining index (`b_0`, `b_{n+1}`,
`x_0`, `a_{n+1}`, …) returns **zero**, and the corpus's only recursive
definitions are `gcd` and the mutually-recursive `L`/`R`.  The recurrences
live in the chapter's Lean preamble, which the Sphinx adapter does not
extract.

So subjects 131, 132, 133, 136 and 137 **would refuse even in a fragment that
had well-founded recursion** — there is no body to unfold.  Filing this signal
beside `recursive-definition` is what stops a future recursion purchase from
returning these five to ready to refuse a third time; a subject returns only
when *every* signal it carries is met.  It is the sibling of cycle 24's
`elided-ambient-hypothesis` one axis over: that names a node whose
**hypotheses** are not self-contained, this names a node whose **definitions**
are not.  Neither is fragment growth; both are corpus-extractor work.

## Isolation, where it was available

`factorial-operator` is the one signal here whose subject was re-read a second
way, and the control matters: `n!` was re-read as the bounded product the
notation abbreviates, which removes the unknown operator entirely.  It still
refuses, on `bigop-symbolic-bound`.  So **both faithful routes are closed and
they are closed for different reasons**, which is why 134 and 135 each carry
both signals rather than one — either alone would re-wedge them, the same
independence cycle 24 recorded for `filtered-bigop`.

`factorial-operator` is deliberately **not** filed under
`recursive-definition` even though factorial is defined by a recurrence: what
the fragment needs is the symbol *decidable*, not the recursion, exactly as
`gcd` and `mod` were admitted as operator words without buying anything
recursive.  And `iterated-application` is deliberately **not** filed under
`symbolic-exponent`: `L_y^n` is n-fold *composition*, not a power of a carrier
value, and P7 met the arithmetic exponent.  Filing it there would make a
landed row read as a failure it never promised.

## What moved

| reading | before | after |
|---|---|---|
| top-level sources | 121 | **121** (no source lands) |
| governed legacy DL | 6963.0 | **6963.0** (`results/formalize_governed.csv` byte-unchanged) |
| ready list | 11 | **11** |
| frontier blocked groups | 39 | **44** |
| refused subjects | 62 | **62** (all eight were already in the ledger) |
| ledger memberships | 95 | **111** |
| `awaiting_unblock_run` | 23 | **15** |
| `no_purchase_meets` | 19 | **24** |
| supply verdict | `ready-work-available` | `ready-work-available` |

All five new signals map to **no purchase**, each with its stated reason — the
honest answer here, since no row on the board buys recursion, function
iteration, an uninterpreted symbol, a term-lexicon word, or a corpus
extractor.  Two are declarable purchase-axis calls and are named as such
rather than declared here: a **term/atom lexicon** row would meet
`factorial-operator` (and `cmp-outside-lexicon`, which cycle 20 measured the
operator-words grower cannot reach), and a **tower-class recursion** row would
meet `recursive-definition`.  Declaring either is not a corpus cycle's act.

## What the next cycle gets

`NEXT-SELECTION` still routes `unblocked`, now over **15** paid subjects.
Measured selectable counts per group, after this cycle's demotions:
`refused:symbolic-exponent` **7**, `refused:function-symbol` **3**,
`refused:iff-connective` **0**, `refused:not-connective` **0**,
`refused:definition-biconditional` **0**.  The three zero groups keep printing
`refills NOTHING`, which is a live-demand reading and not an empty group.

## One committed tooth re-derived

`tests/test_symbolic_exponent_class.py::test_the_row_refills_at_most_five_subjects_even_if_it_were_bought`
went red on this cycle's own delta, and it is the right tooth to have caught
it.  **The number the bill is priced on did not move**: `solo == 5` — a full
symbolic-exponent purchase still returns five subjects on its own — and
`joint == 7` is unchanged too.  What moved is the *shape* of the joint set.
Four of the six subjects whose only other refusal was the single word
`function-symbol` are in this cycle's take, and each now carries the signal
naming which rung holds it.  All six still carry `refused:function-symbol`:
the ledger is append-only and its rows stand.

So the assertion was re-derived rather than relaxed — exact-equality on a word
whose meaning this cycle split, replaced by the containment (six of seven held
by `function-symbol`, the seventh `fermats_little` by `mod-operator`) plus a
new pin on the refinement itself, which reds if the word is ever re-widened.
Recorded plainly: this is a re-baseline of a derived pin, in the same class as
`registration.json`'s, and not a newly mutation-verified tooth.

## Bounds

Probe verdict this container: `lean-local` (`tools/lean_env_probe.py`, run here, not read off disk).  Per-commit gate run as `CGB_LEAN=0 python3 -m pytest tests/ -q` per CLAUDE.md.  A Lean-free cycle: no
`lean-fast` tag, no `FgReflect.lean` edit, no ceremony-reserved path in the
diff, P5 untouched, no park lifted.  The refusal ledger stays append-only and
every pre-existing row stands as the pre-purchase reading it was.
