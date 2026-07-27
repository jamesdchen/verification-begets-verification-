# C3 cycle 27 — the first symbolic exponents land, and the projection comes in under its own bound

**Product: three certified corpus sources and five measured refusals.**  Eight
subjects taken by `intake_from_frontier --unblocked` — three from
`refused:function-symbol`, five from `refused:symbolic-exponent` — every one
measured, **three certified and shipped**.  Corpus **121 → 124** top-level
sources, governed readings **117 → 120**, certified **114 → 117**, governed DL
**6963.0 → 7152.0**.

This is the first cycle in four to land a reading.  Cycles 24–26 were
refusal-only and produced demand data; this one spends that data and collects
the delta a purchase was bought for.

## What landed

Sources 130–132 are the verbatim prose of three math2001 `06_Induction`
problems, and they are **the corpus's first readings with a bound variable in
an exponent** — P7's `Tm.pow` collected rather than projected.

| # | node | reading | what it exercises |
|---|---|---|---|
| 130 | `#problem-001` | `n+1 <= 2^n` | the exponent alone, nothing else in the way |
| 131 | `#problem-002` | `or(mod(4^n,15)=1, mod(4^n,15)=4)` | a symbolic exponent **under `mod`**, plus the elliptical "either 1 or 4" as `or` of two equalities |
| 132 | `#problem-003` | `2 <= n ⊢ 2^n + 5 <= 3^n` | **two** symbolic exponents in one atom, with a hypothesis-bounded index |

Carrier `Nat` throughout is P7's admission condition
(`_check_pow_exponent`), not a preference — and the same batch measured the
refusal that proves the condition binds.

## The headline: a refill projection that came in UNDER its bound

`refusal-symbolic-exponent` was priced at twelve subjects and projected to
return **five** — the five carrying no second refusal.  Cycle 27 ran
`--unblocked` against exactly those five and measured every one:

* **three certified** (130–132 above);
* **two refused**, each for a reason the row never named.

So *"at most five"* held as a bound and **the realized refill is three**.  That
is the honest shape of a refill projection: an upper bound from the ledger,
discharged subject by subject by certification, never a promise.

The two that did not return each earned their own signal:

* **`symbolic-exponent-at-int`** — `06_Induction#theorem-002` (`a ≡ b mod d`
  implies `a^n ≡ b^n mod d`).  Gate, verbatim: `` `^` admits a SYMBOLIC
  exponent only at carrier 'Nat' (non-negative by construction, so the power
  stays Monoid.npow); at 'Int' an exponent may be negative and a reciprocal
  power leaves the carrier entirely``.  The subject's objects are **integers**.
  This is **not a defect in P7**: P7's receipt states the Nat restriction as
  the condition that makes every downstream layer type-correct at once, and
  records that Lean refuses the alternative outright (`failed to synthesize
  HPow ℤ ℤ`).  It is the second half of a word, filed apart so the row that
  bought the first half does not read as having bought both.
* **`exists-before-forall`** — `06_Induction#problem-004` (*"for all
  **sufficiently large** n, 2^n ≥ n²"*).  Gate, verbatim:
  `exists-before-forall: the compiled binder order is not ∀*∃* (a forall
  segment follows an exists segment); the bounded-shadow models only the
  ∀-outer/∃-inner split`.  **The elision is load-bearing, not stylistic**: the
  unqualified `∀n` reading is FALSE at n = 3 (8 < 9), so the shape cannot be
  dropped to reach a green.  Distinct from cycle 24's
  `exists-domain-too-large`, which names a *supported* shape the mirrors
  cannot afford to check; this names a binder **order** they do not model.

**This is the same finding as cycle 26's, one row over.**  Cycle 26 measured
that `function-symbol` was one word covering three rungs and that P8 bought
one.  Cycle 27 measured that `symbolic-exponent` covers two carriers and that
P7 bought one.  Two independent rows, the same defect: a signal is a promise
about which purchase returns a subject, and a word coarser than the purchase
makes that promise for subjects the purchase never reaches.

## The other three: cycle 26's split, confirmed by a subject that separates it

The `refused:function-symbol` half of the take was three subjects, none of
which certified — and one of them is the reason cycle 26's two-signal split
was worth making.

| # | node | gate verdict | signals |
|---|---|---|---|
| — | `#problem-015` (`d_n ≥ 4^n`) | `funcdef:recursive-body` | `recursive-definition`, `elided-sequence-definition` |
| — | `#problem-016` (`F_n ≤ 2^n`) | `funcdef:recursive-body` | `recursive-definition`, `elided-sequence-definition` |
| — | `#theorem-010` (`L(a,b)a + R(a,b)b = gcd(a,b)`) | `funcdef:recursive-body` | **`recursive-definition` alone** |

Cycle 26 minted `recursive-definition` and `elided-sequence-definition`
together, on five subjects that carried both, and argued they were distinct.
**`#theorem-010` separates them on the tree**: the corpus *does* define `L` and
`R`, mutually recursively, at `06_Induction#definition-002` — so the body
exists and only the recursion blocks it.  A subject carrying the first signal
and not the second is what turns that argument into a measurement.  (`d_n` and
`F_n` remain undefined anywhere in math2001; `F` appears only inside another
*claim*, `#problem-014`, never a definition.)

## What moved

| reading | before | after |
|---|---|---|
| top-level sources | 121 | **124** |
| governed readings / certified | 117 / 114 | **120 / 117** |
| governed DL | 6963.0 | **7152.0** |
| ungoverned DL | 7382.0 | **7571.0** |
| final-wave gaps | −419.0 / −299.0 | **unchanged** |
| census of record (governed) | 6304.0, 13 macros | **6493.0**, 13 macros |
| ready list | 11 | 11 |
| frontier blocked groups | 44 | **46** |
| ledger memberships | 111 | **118** |
| `awaiting_unblock_run` | 15 | **10** |

Both DLs were reproduced **live** from `results/formalize_governed.csv`; the
census-of-record block came from `tools/measure_cluster_key.py
--print-reregistration`, and `all_pass` returns **True** once registration
carries it.

The operator axis is an **honest no-delta**: the miner staged one new proposal
(54 → 55) and **no new word crossed the admission bar** — the admitted set is
byte-identical at 11.  Recorded rather than omitted.

## Derived pins re-baselined, and one fixture re-anchored

A growth cycle moves derived numbers that three refusal-only cycles never
touched.  Each was re-derived from the live artifact, never edited to fit:

* `registration.json` — sources, both DLs, stream shape (3195/70 → 3264/71),
  `naive_dl` 8641.0 → 8830.0, census of record, cluster-key re-registration.
* `test_entropy_refs.py` — order-0 7108.13 → **7256.868**, LZ77 phrases
  772 → **792**, context-stat columns.
* `test_c2_report.py` — all five headline numbers.  **The finding is
  unchanged**, and is now asserted as a *relation* rather than left implicit
  in moved numbers: the vocabulary still does not pay under C2, and the
  governance ranking still does not hold under C2.
* `test_operator_prompt_seam.py` — `n_proposed` 54 → 55, `n_admitted` still 11.
* `test_entropy_stack_fig.py` — the k=0 **fixture** re-anchored 7200.5 →
  7800.5.  Its own comment predicted this: the value must sit between the real
  order-0 line and naive, and corpus growth had moved order-0 *past* it.
* `test_symbolic_exponent_class.py` — rewritten to pin the **measured**
  partition (3 certified, 2 newly-blocked, 6 held by `function-symbol`, 1 by
  `mod-operator`) while keeping "at most five" as an inequality, so a future
  widening of the row still reds.

## Bounds

Probe verdict this container: `lean-local` (`tools/lean_env_probe.py`, run
here, not read off disk).  A Lean-free cycle: no `lean-fast` tag, no
`FgReflect.lean` edit, no ceremony-reserved path in the diff, P5 untouched, no
park lifted.  The refusal ledger stays append-only.

One correction recorded rather than quietly fixed: an early attempt at this
cycle recorded a refusal row against a **fabricated** subject hash.  It was
removed from the ledger before any commit and re-recorded against the real
hash read from `results/frontier.json` — a ledger row is evidence, and a row
whose subject id was invented is not.
