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
