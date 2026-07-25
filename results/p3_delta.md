# P3 purchase — the census signal split (PLAN_FRAGMENT §2/§4 P3, prerequisite)

**What this cycle ships.** The P3 purchase (the ℚ / rational carrier) is the
next entry on the §4 queue, and §4 states its bill in two clauses: the ℚ
carrier itself **and** a *census signal split* — "Requires a census signal
split (probability-mass vs entropy-log) so the delta is honestly
attributable." This cycle pays the second clause: it splits the coarse
`probability-entropy` miss-signal into the two demand classes with **opposite
tractability under a ℚ carrier**, so that when the carrier lands its
re-census delta names exactly what it un-blocked and what it did not.

**The split (`tools/blueprint_census.py::MISS_SIGNALS`).**

- `probability-mass` — finite distributions with **rational** masses,
  expectations of rational-valued variables, independence: decidable rational
  arithmetic. This is the slice a ℚ carrier un-blocks.
- `entropy-log` — entropy, mutual information, the `H[·]` functional: the
  `log` is **transcendental**, so this stays **PARKED** (PLAN_FRAGMENT §4
  PARKED) no matter what the arithmetic carrier grows to.

A node whose prose names both (the PFR-shaped `H[X] ≤ H[X]+H[Y]`) matches
BOTH signals and stays out-of-fragment — the split narrows attribution, it
never demotes a real miss (the honesty rule: the census reports signals,
never a fidelity verdict).

**The measured delta (re-census over the committed portfolio).** The old
`probability-entropy: 116` splits into:

| signal | nodes | tractability |
|---|---|---|
| `probability-mass` | **116** | ℚ-expressible (the P3 target) |
| `entropy-log` | **3** | transcendental — PARKED |

The reading is crisp and honest: **nearly all** of the old probability demand
is mass-arithmetic (all 116 mass nodes, of which only 3 also carry an
entropy/mutual-information term). So the ℚ carrier, when purchased, addresses
a 116-node demand class and leaves a named, 3-node parked residue — the
attribution §4 asked for is now mechanical. The `frontier.json` `blocked`
projection carries the same split (`probability-mass: 116`, `entropy-log:
3`), and every downstream census artifact regenerated
(`tools/regen_downstream.py --from census_portfolio`).

**Teeth.** `tests/test_blueprint_census.py` gains a log-free rational-mass
fixture (`fix:fair-die`, probability-mass ONLY) and asserts the PFR-shaped
node lands under BOTH split signals — so the split can never silently
re-merge or mis-route. Full suite green.

---

## Why the ℚ carrier itself is NOT in this cycle (honest scope)

The carrier is a genuine structural purchase whose full bill spans layers a
single cadence session cannot certify to standard (full suite green **and**
reflect-slice lane green). The blocking facts, mapped this session:

1. **The reflect slice needs a THIRD carrier tower.** `tools/FgReflect.lean`
   is not a single carrier-agnostic model: it carries one *proven* evaluation
   tower per carrier (the Int layer, and the S6 Nat layer `evalTmN/denoteN/…`
   ~250 lines, with the D8 divergence proven on both sides). A ℚ carrier
   needs `evalTmQ/denoteQ/decDenoteQ/checkQ/…` and their subst + soundness
   lemmas. Per CLAUDE.md there is **no local Lean in remote containers**, so
   that tower is CI-lane-only and cannot be iterated to green inside an
   unattended cadence session.

2. **Eval needs a new rational-enumeration strategy, not just carrier
   threading.** The domain sweep (`generators/math_eval.py`
   `enumerate_domain`/`_ranges_for`/`_box_size`) ranges every object over an
   *integer* `range(...)`; a ℚ object has no such sweep. The bounded-shadow
   and instance gates (`satisfying_instances`, `bounded_nonvacuous`,
   `boundary_probes`, the ∃-shadow) do not operate over ℚ without it.

3. **SMT needs `Real` sort + `QF_LRA/QF_NRA`** (`generators/math_smt.py`
   declares every const `Int`), and the mass slice likely needs a new `/`
   term operator (absent from `_BUILTIN_TERM_OPS` today; `%`/`mod` is integer
   remainder, meaningless over ℚ).

4. **Silent `else → Int` sites must each be made explicit.** The systemic
   shape `if carrier == "Nat": … else: <treat as Int>` recurs in eval, smt,
   `operator_growth.py`, and — most dangerously — `run/reflect_shadow.py`
   (lines ~208/231/289), where a pure-ℚ reading currently **fails OPEN into
   the Int reflect tower**. Shipping the carrier without closing these would
   be a silent-fidelity hazard the honesty rules forbid.

**One-purchase-per-flywheel-cycle is preserved:** this cycle's purchase-axis
delta is the signal split (a real, committed, re-census-affecting change),
and it is the strictly-first, fully-verifiable half of the §4 P3 bill. The ℚ
carrier full bill (validator widening + eval rational enumeration + SMT
`Real` + `/` operator + the divergence battery `tests/test_rat_battery.py` +
a `rat-carrier` growth-registry row + the `FgReflect` ℚ tower) is the next
purchase cycle's scope, now with its attribution instrument in place.

No trust roots touched: `kernel/certs.py`, `TRUST.md`, the escape-gate
blocklist, and `buildloop/growth_protocol.py::ANTI_LIST` are all unchanged.

---

## Addendum (measured correction): the `\mathbb`-spacing leak

**The defect.** The split above was priced with a term list written in the
spelling a human types — `\mathbb{H}`, `\mathbb{Q}`, `\mathbb{R}`,
`\mathbb{F}_2` — but plasTeX, which produced every committed `nodes.jsonl`,
emits `\mathbb {H}` **with a space**. Under `_signals`' raw substring match
those terms were simply **dead**: `\mathbb{h}` scored 0 against 199 spaced
occurrences in the portfolio, `\mathbb{i}` 0 against 44, `\mathbb{f}_2` 0
against 8, `\mathbb{q}` 5 against 31 more, `\mathbb{r}` 40 against 33 more.
So the "116 vs 3" table
above is a **lexical artifact of the leak, not a measurement of the split**:
entropy-log read 3 while 123 nodes carry entropy/log content. The split's
*shape* was right; its numbers were not, and the direction of the error
flattered the purchase — it made the parked residue look 40× smaller than it
is. We record that, because the honesty rule is that we never distort a
reading to protect an earlier number, and a recorded correction beats a
silent rewrite.

**The fix.** `tools/blueprint_census.py::_signals` now matches every term
against the raw lowered prose **or** against a copy with `\mathbb {` folded
to `\mathbb{`. Both spellings genuinely occur across the intaken corpora, so
both are carried; the fold revives the dead terms in all fourteen categories
at once instead of duplicating fourteen term lists, and the census stays
lexical, deterministic, LLM-free. entropy-log additionally gains the
vocabulary the corrected reading exposed (`\mathbb{I}`, "conditional
entropy", "entropic", `\log`). `\log` also stays in real-analysis: a node may
carry both categories, which is the design — an additive signal never demotes
a miss.

**The corrected table** (1008 nodes, 6 corpora):

| signal | nodes | of which also the other | tractability |
|---|---|---|---|
| `probability-mass` | **116** | 65 also `entropy-log` | ℚ-expressible |
| `entropy-log` | **123** | 65 also `probability-mass` | transcendental — PARKED |

The reading that replaces "nearly all of the old probability demand is
mass-arithmetic": of the 116 mass nodes, **51 are log-free** — those are what
a ℚ carrier un-blocks — and **65 also name a `log`/`H[·]`/`I[·]` term**, so
they stay parked whatever the arithmetic carrier grows to, plus 58
entropy-only nodes beside them. The ℚ carrier's honest target is a **51-node**
slice against a **123-node** parked class, not 116 against 3. The purchase is
still the right next one; it is smaller than the leaked reading claimed, and
the attribution instrument now says so before the money is spent.

**Portfolio shift** (re-census, `tools/regen_downstream.py --from
census_portfolio`):

| | before | after |
|---|---|---|
| `attempt-candidate` | 108 | **108** (unchanged) |
| `out-of-fragment` | 711 | 731 |
| `no-signal` | 189 | 169 |

Twenty nodes move `no-signal → out-of-fragment`: their only signals were
dead-spelled, so the census had been reporting "nothing recognized" about
prose it plainly recognizes. The C2 mining queue is untouched — the leak
never manufactured attempt-candidates, it only under-reported misses, which
is the direction that costs credibility rather than spend. Per-signal:
`entropy-log` 3→123 (the fold alone accounts for 3→62, the new terms alone
for 3→50), `rational-arithmetic` 135→156, `real-analysis` 136→152;
`probability-mass`, `sequences-sums`, `sets-cardinality`, `magmas-equational`
and the rest unchanged.

## The P4 prerequisite lands here: `algebra-abstract`

PLAN_FRAGMENT §4 P4 buys a **concrete** finite carrier (`ZMod n`) and states
its own honesty clause in the same breath: "typeclass-parametric statements
(`∀ G [Group G]`) stay out-of-fragment under an honest sub-signal
(algebra-abstract), never silently claimed." That instrument has to exist
*before* the purchase, exactly as the probability-mass/entropy-log split had
to exist before the ℚ carrier, so it ships in this receipt's cycle.

Unlike the P3 split this one is **additive**: the `algebra-structures` row is
unchanged at **97** and a parametric node matches both, the way a PFR-shaped
node matches both probability signals. `algebra-abstract` measures **45**
nodes; the **52**-node concrete residue is P4's actual target. The term list
is deliberately narrow — bare "group"/"field" are excluded because they fire
on precisely the concrete `\mathbb{F}_p` / finite-field nodes P4 buys, and
"subgroup" is excluded for the same reason: the PFR statements fix
`G = \mathbb{F}_2^n` and *then* quantify a subgroup of it, so "subgroup"
alone does not witness parametricity. Checked against the corpora, the
concrete nodes stay concrete (`mult_cyclic`, `fact_A`, `a0000000352`,
`entropy-pfr`) and the parametric ones do not (`goursat`, `hb-thm` via
"homomorphism"). Two forward-looking phrasings ("for every group",
"arbitrary group") match nothing in today's portfolio; they are kept as
stated intent, not counted as evidence.

Teeth: `tests/test_blueprint_census.py` gains a concrete-algebra fixture that
must carry `algebra-structures` and **not** `algebra-abstract`, a tooth
pinning bare "group"/"field" out of the sub-signal's term list, and a
spacing fixture whose only entropy signal is reachable through the fold —
so neither the sub-signal nor the correction can silently regress.

---

# The carrier lands (second clause of the §4 P3 bill)

The clause above bought the *instrument*; this one buys the *carrier*. `Rat`
is the third entry in `generators.math_reading.CARRIERS`, spelled with its
ASCII Lean type name because the `ℚ` glyph is escape-gate refused — the
compiler emits `(x : Rat)` verbatim, so the ASCII spelling is the only one
that ever reaches Lean.

**The bill, item by item.** Validator (`CARRIERS`, the new Rat-only builtin
`/`, `_check_carrier_ops` as the carrier-admissibility walk, the reading-level
`rat:no-coercion` refusal); evaluator (exact `Fraction` throughout, the
Farey-style `rat_values` sweep, the totalisation `q/0 = 0`, boundary probes
with the integer-lattice shortcut disabled); SMT mirror (one `Real` sort per
reading, `(ite (= y 0.0) 0.0 (/ x y))` mirroring eval cell for cell, the
`QF_LRA`/`QF_NRA` split); compiler (`/` infix on typed binders, the carrier
emitted verbatim); prompt (the `/` grammar line and the regenerated golden);
registry (the `rat-carrier` GROWERS row, all seven roles, its signature pin);
reflect (the fail-open carrier sites closed); batteries
(`tests/test_rat_battery.py`, 35 teeth).

**The v1 freeze, as named limits rather than gaps.** `rat:no-coercion` — a
Rat object may not share a reading with an integer one, and no ambient
rescues the mix; there is no ℕ→ℚ coercion story this cycle and a mix is a
refusal, never a silent cast. No `%`/`mod`/`dvd`/`gcd`/`coprime`/`even`/`odd`
at Rat: remainder and divisibility over a field have no meaning we are
willing to freeze. No binder (`bigsum`/`bigprod`/`card`) inside a Rat
reading: the index is pinned Nat, which is the same coercion we just refused.
And `/` is refused *outside* Rat — at ℕ/ℤ Lean's `/` floors, and modelling a
lossy operator is precisely the divergence T4 exists to catch. Every one of
these is a first-class `FragmentMiss` (`operator:/@Nat`, `operator:%@Rat`,
`operator:bigsum@Rat`) carrying demand data, not an omission.

## The measured delta — and where it is NOT

Two censuses moved, in opposite ways, and saying which is which is the whole
point of the split clause above.

**The mathlib-side census DID move** (`specs/mathsources/mathlib/census.json`,
`python3 -m buildloop.census`, 225 916 rows at the same pin
`9837ca9d65d9`). The `carrier:Rat` blocker row retired, because a carrier
cannot be both the demand and the supply:

| | before | after | delta |
|---|---|---|---|
| `in_fragment` | 537 | **564** | **+27** |
| `single_blocker_rows` | 2 414 | 2 423 | +9 |
| `multi_blocker_rows` | 211 801 | 211 618 | −183 |
| `unclassified` | 11 164 | 11 311 | +147 |
| `blocked_by["Rat"]` | **1 487** | **0** | −1 487 |
| `unlock_counts["Rat"]` | 48 | 0 | −48 |

Twenty-seven mathlib declarations are now fully in-fragment that were not,
and 1 487 stop being priced against a carrier we now have. The `unclassified`
rise is honest bookkeeping, not a win: those are rows whose *only* recognized
blocker was `Rat`, so removing the pattern leaves them with no recognized
signal at all rather than with a verdict. And the flywheel shows in
`unlock_counts`, where the blocker behind the blocker becomes visible for the
first time: `Ring` +10, `Field` **0 → 9**, `Coe` +9, `Group` +8, `Monoid` +6,
`Inv` +5. `Field` had no demand row at all while `Rat` was masking it. That
is the purchase paying for the next question, which is what the census is for.

**The portfolio census did NOT move, and that is the honest headline.**
`tools/regen_downstream.py --from census_portfolio` over the six committed
corpora (1 008 nodes) returns `results/census_portfolio.json` **byte-identical**:

| verdict | before | after |
|---|---|---|
| `attempt-candidate` | 108 | **108** |
| `no-signal` | 169 | **169** |
| `out-of-fragment` | 731 | **731** |

The `_FRAGMENT_WORDS` change (excluding the substring-hazardous `"rat"`,
spelling the prose surface `"rational"`) did land, and it is visible in the
per-node records: **22 nodes** gained `rational` in
`fragment_vocabulary_hits` — `math2001` 14, `formal_book` 7, `flt_regular` 1;
`equational_theories`, `pfr` and `unit_fractions` 0. But **zero nodes changed
verdict**, because signals dominate a fragment-word hit and all 22 already
carried a miss signal (17 of them `rational-arithmetic` itself). The expected
`no-signal → attempt-candidate` flips did not occur, and this receipt records
that rather than widening something until they do — a no-delta reading is
evidence, not a retry cue (CLAUDE.md §invariants).

Two things worth writing down while the measurement is fresh. First, the
substring hazard is *narrowed, not eliminated*: `"rational"` is still a
substring matcher, and 6 of the 22 gainers matched it only through the word
**ir**rational — the exact opposite of a rational. They are out-of-fragment on
their `real-analysis` signal regardless, so no verdict is wrong today, but
the instrument is lexical and this is the shape of its next false positive.
Second, and more important: the probability-mass nodes this carrier was aimed
at **stay out-of-fragment, correctly**. They carry probability *vocabulary* —
"random variable", "distribution", "expectation" — which a ℚ carrier alone
cannot express; arithmetic on rational masses is necessary for them and
nowhere near sufficient. The split's corrected numbers (**51** log-free mass
nodes against **123** entropy-parked) price that *demand*; they were never a
forecast of this delta, and reading them as one would be the census claiming
a fidelity verdict, which it never does.

## The reflect slice: a fail-CLOSED named skip

`FgReflect.lean` proves two evaluation towers, Int and Nat. A Rat reading has
no proven layer, so it **skips by name**: `carrier-out-of-reflect-slice:Rat`,
added to the frozen skip vocabulary and to the sweep's allowlist. This is the
additive-class rule applied literally — a new carrier may not ride a layer
proven for a different one, and the skip is the honest form of that refusal.

What P3 closed here was a genuine fail-open, not a hypothetical: both probe
routes chose their layer by asking whether the carrier set was exactly
`{"Nat"}`, so **any** other single carrier silently took the Int branch and
would have been probed against a mirror that says nothing about it. The
choice now runs through `_reflect_layer_is_nat`, which raises rather than
defaulting. One further correction was needed to make the skip real on route
1: the check sat *below* `emit_witness_proofs`, whose witness-template family
is integer-shaped, so a Rat reading raised on a `Fraction` before any skip
could be returned — a crash where the design promises a named skip. The
single-carrier check is now decided ahead of emission. Deliberately narrow:
the mixed-carrier row stays where it was, so every reading that skips today
keeps skipping for the reason it already reports and the committed sweep is
row-for-row unchanged.

The **ℚ tower stays the named attended follow-up** — `evalTmQ/denoteQ/…`
plus their subst and soundness lemmas, CI-lane work, on the addendum's own
blocker list. Not descoped, not silently assumed: named, with a skip that
fires until it lands.

## Out-of-bill fixes, one sentence each

1. **`kernel/rung.py` arity pin.** `_TERM_OPS`/`_ARITY` gain `/` at exactly 2,
   because that table is pinned equal to the grammar by
   `tests/test_rung_interp.py` and pins SHAPE, not admissibility — whether a
   `/` is legal at the reading's carrier stays the gate's call.
2. **Planner `Fraction` serialization.** `planner/math_choices.py` renders a
   Rat instance assignment as its canonical `p/q` string before it reaches
   `canonical_json`, because the boundary evidence gets serialized and a
   float would make the record a rounding of the value it claims to report.
3. **`_BUILTIN_CARRIER_SUPPORT` decoupling.** `op_signature`'s carrier-support
   field feeds one consumer — the recurrence miner's op-slot typing — so it
   stays the integer carriers rather than following `CARRIERS`, and `/` is
   pinned to `{Rat}` alone; widening it would have re-keyed every mined
   skeleton for a reason unrelated to what the readings say, and the tower
   census stays byte-stable as a result.
4. **The reflect emission-order fix** described above — the named skip is now
   reachable on both routes instead of only route 2.
5. **A corrected number in a comment.** The Rat sweep's width at bound 8 is
   **23**, not the 25 the grid's corner count suggests: `p/q` duplicates
   collapse under `Fraction`, which is exactly why `_box_size` counts the
   grid instead of multiplying a formula. Corrected in place rather than left
   to be re-derived wrongly later.

## Teeth

`tests/test_rat_battery.py` — 35 teeth on the bigop/finset battery template:
a differential value battery (9 planted rows: exact halves and thirds, a
negative difference, the totalisation at zero in both its literal and
object-divisor forms, a fraction to a literal power, a mixed `+ * - /`
expression) where eval is corroborated by an independent `Fraction` oracle
*and* by the ground-equation differential on z3 **and** cvc5; an order
battery carrying both directions, so a false row must come back `unsat`; a
symbolic battery over free Real params including a deliberately false
identity that must be satisfiable; the D8-class carrier-stability xor
obligations, where the Rat and Nat renderings of one ground atom are asserted
`xor` (`sat` = the carriers can disagree, corroborated by eval-witnessed
verdicts, never a solver existence claim alone) against an agreeing control
that must be `unsat`; the gate's whole refusal surface as demand data; the
logic classification pinned on both sides, with the integer classification
pinned *unchanged*; and the Lean rendering, escape gate and hash
byte-stability.

The divergence tooth is `test_lossy_division_gets_no_certificate`, and its
shape is worth the sentence it costs. The obvious recipe — drop the
`ite` guard, plant a divisor-zero row, expect a refusal — **does not work**,
measured: SMT-LIB leaves `(/ x 0)` *unconstrained*, so the guard-dropped
rendering does not merely compute something else, it lets the solver invent a
value that happens to match, and a ground obligation still answers `sat`.
Only the universal shape separates them — "is this term zero at *every*
numerator?" — which the totalised rendering satisfies (`unsat`) and the lossy
one does not (`sat`). The same D9 hazard `math_smt`'s `%`-totalisation
comment names, in its division form.

The `rat-carrier` GROWERS row indexes one tooth per half of the bill: the
gate tooth `test_div_outside_rat_is_a_fragment_miss` in
`tests/test_math_reading.py`, where the refusal is decided, and the
divergence tooth above in the battery, where a lowering is caught lying.

Mutation-checked, not merely green: dropping the SMT div-by-zero guard reds 3
teeth including the named one; making eval's `/` floor instead of divide reds
10. Full suite green — **1 299 passed, 38 skipped**.
