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
