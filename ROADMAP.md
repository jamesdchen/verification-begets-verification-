# Roadmap: from here to the two-zone economy

README.md says what the system is. TRUST.md says what is trusted. LINGUISTICS.md
says what is meant. This document says **what gets built, in what order, and
when each piece counts as done** — from the current state to the endgame the
theory permits:

> an infinitely extensible archipelago of decidable islands (universal-tier
> proofs, amortized to zero marginal cost) inside an undecidable ocean
> (per-instance witnesses and certified monitors, amortized to a small,
> permanent, honest toll) — with specification cost attacked from both sides
> (cheaper Readings, specs lifted from the world) and the kernel remaining,
> forever and by theorem, the one thing not bootstrapped.

The plan follows the house rules that built everything so far, restated once:

1. **Outsource every checker that exists**; build only wiring, ledger, and
   measurement.
2. **Dual-checker rule everywhere**: no certificate without two independent
   agreeing evidence channels; disagreement is a first-class logged event.
3. **Teeth per increment**: every phase ships a demo where the new machinery
   catches a real, planted defect — and, where honesty demands it, a demo of
   what it *cannot* catch.
4. **Honest tiers**: every certificate names exactly what is claimed and at
   what strength (proved / bounded / conformance-relative / monitored).
5. **The LLM authors only specs** (Readings, meta-specs, schemas). Arbitrary
   code enters only as *incumbent input*, never as LLM output.

---

## Phase 0 — current state (built, certified, pushed)

| asset | mechanism | tier |
|---|---|---|
| codec family (Kaitai, ABNF→tree-sitter) | roundtrip+Dafny / chain differential | universal + emit-check |
| tool contracts | strict-Pydantic vs jsonschema differential | emit-check |
| schema-lift | inferred schema vs incumbent differential | emit-check |
| cross-field constraints | Z3∧CVC5 proof + solver-boundary | proved + emit-check |
| protocols | dual BMC (global `G`, complete when acyclic) + refsim conformance | proved(-bounded) + emit-check |
| service composition | one meta-spec → all layers; dispatcher-vs-reference + liveness | checked |
| semantic path | Reading (quote+force+LF) → compositional compiler → provenance → entailed scenarios + examiner | grounded evidence |
| synthesis loops | spec path + semantic path, stage-labeled refinement | — |
| infra | content-hash cert cache; channel-granular process parallelism; SMT lock; sandbox | — |

Fragment today: **safety-only** deontic-temporal logic (G + precedence) over
agent-symmetric integer aggregates. The phases below climb from there.

---

## Phase 1 — Finish star-free: eventualities + the monitor factory

**Objective.** Add F/U/X-class temporal demands ("eventually", "until",
"before", "within n steps") as LTLf — LTL over *finite* traces, which is what
sessions are. Stays inside star-free: zero new decidability risk. Produces the
certified-monitor factory Phase 2 consumes.

**Theory.** LTLf (De Giacomo–Vardi); star-free = FO(<) = LTL (Schützenberger,
McNaughton–Papert, Kamp); on finite traces, liveness converts to safety at the
session boundary ("you may not `close` with obligations pending").

**Workpackages.**
- **P1.1 LF fragment** (`generators/reading.py`): new kinds
  `eventually {action|pred}`, `until {hold-pred, until-action}`,
  `before {first, deadline}`, `within {action, steps}`. Demands must quote;
  full validation + referential integrity as today.
- **P1.2 Dual semantics.**
  (a) `generators/ltlf_smt.py`: bounded LTLf semantics encoded into the
  existing BMC unrolling; obligations to **Z3 ∧ CVC5**; complete for acyclic
  control, K-labeled otherwise.
  (b) vendor **flloat** (pip, pure Python, pinned; TRUST §1.3 entry): the same
  formula compiled to a DFA, replayed on solver-generated accepting and
  violating traces. Two independently-authored implementations of LTLf
  semantics must agree — the dual-checker rule with genuinely uncorrelated
  channels.
- **P1.3 Monitor factory** (`generators/monitor_gen.py`): per temporal demand,
  flloat's DFA → an emitted, dependency-free monitor module (transition
  table). New kernel contract **`monitor-cert`**: channel 1 = monitor verdicts
  vs SMT semantics on solver-generated traces; channel 2 = monitor vs a
  second, independently-emitted stepping implementation.
- **P1.4 Dispatcher integration** (`generators/service_gen.py`): monitors
  advance on every accepted call; terminal actions are refused while any
  `eventually`/`until` obligation is undischarged (liveness→safety at the
  boundary). The independent reference service implements monitor stepping
  separately, so the composition differential also covers monitor wiring.
- **P1.5 Compile + provenance + entailment** (`generators/reading_compile.py`):
  temporal LFs → obligations + monitor set, with provenance; entailed
  scenarios extended — for each `eventually` demand, a trace that attempts to
  close without discharging it, expected **rejected at close**.
- **P1.6 Loop, demo, docs**: Reading prompt teaches the new kinds;
  `demo_temporal.py` (see teeth); README / TRUST / LINGUISTICS updated
  (eventualities move from *out of fragment* to *handled, finite-session
  semantics* — the finite-horizon caveat stated plainly).

**Teeth (`demo_temporal.py`).**
- A: "every hold is eventually purchased or released" certifies end-to-end.
- B1: a stranding service (holds can leak) refuted by **both** solvers with
  the shortest stranded trace.
- B2: a dispatcher that drops monitor wiring caught by the composition
  differential.
- B3: a mutated monitor table caught by `monitor-cert` (flloat-vs-SMT
  disagreement made visible).

**Done when:** all teeth bite; all prior demos + invariants green; a live
semantic synthesis certifies a request containing an eventuality ("every
reservation must eventually be confirmed or released").

---

## Phase 2 — The witness economy made explicit: the `monitored` tier

**Objective.** Let the system take on **arbitrary, unverifiable code** —
honestly. An incumbent black-box component runs inside a certified cage:
schema/constraint/guard layers on ingress, Phase 1 monitors on every trace,
output contracts on egress, OS sandbox around everything. The certificate
proves the cage, and explicitly claims nothing about the cargo.

**Theory.** Rice's theorem ends universal claims about arbitrary code;
safety properties are exactly the finite-prefix-refutable ones
(Alpern–Schneider), hence monitorable by the tier-3 automata Phase 1
manufactures. "Undecidable code, decidable guards."

**Workpackages.**
- **P2.1 Tier taxonomy** (`kernel/certs.py`, TRUST): new explicit tier
  **`monitored`**, with machine-readable `claims` / `non_claims` fields on
  every certificate (this is workstream W1 landing early).
- **P2.2 Egress contracts** (`generators/service_model.py`, `toolgen`):
  optional `output_schema` per tool; certified output validators (same
  dual-validator pattern as inputs).
- **P2.3 The cage** (`run/guarded.py`): wrap an incumbent handler so every
  call flows dispatcher → monitors → sandboxed incumbent → egress validation.
  Cage hash binds dispatcher + monitors + sandbox profile + incumbent hash.
- **P2.4 Kernel contract `cage-conformance`**: channel 1 = **containment**
  (on solver-generated violating inputs, the caged system rejects where the
  bare incumbent would have acted); channel 2 = **transparency** (on legal
  runs, caged output ≡ bare incumbent output byte-for-byte).
- **P2.5 Demo + docs** (`demo_guarded.py`): a malicious incumbent (oversells;
  returns malformed data) is stopped at the exact violating call; an honest
  incumbent is unaffected. TRUST gains the cage section; LINGUISTICS notes
  that deontic enforcement now extends over unverifiable conduct.

**Done when:** containment and transparency teeth both bite; certificate
renders its non-claims; regression green.

---

## Phase 3 — Acquire specs from the world: protocol-lift via L\*

**Objective.** Learn the behavior of an incumbent stateful service as an
automaton, certify the learned model against the incumbent, and feed it into
the existing protocol/service stack. Schema-lift, one floor up: attacks the
irreducible *specification* cost from the world side.

**Theory.** Angluin's L\* learns DFAs/Mealy machines in polynomial time given
membership + equivalence oracles; the sandbox **is** a membership oracle; the
W-method gives a conformance suite that is complete relative to a state
bound — a genuine, honestly-bounded certificate. Gold's theorem says this
stops at regular: the lift loop's reach *is* the learnability frontier.

**Workpackages.**
- **P3.1 Learner** (`buildloop/lstar.py`): classic L\* with Rivest–Schapire
  counterexample processing; alphabet = tool calls with representative
  argument values drawn from boundary analysis (the abstraction is *named on
  the certificate*).
- **P3.2 Equivalence approximation**: W-method suite for declared bound `n`,
  plus a random-walk differential channel.
- **P3.3 Orchestration** (`run/protocol_lift.py`): learned machine → protocol
  spec JSON → existing `protocol-cert` + service wrap. Certificate:
  "behaviorally equivalent to incumbent **up to state bound n** under suite W"
  — bound-relative, and it says so.
- **P3.4 Demo** (`demo_protocol_lift.py`): L\* recovers the lifecycle of a
  hand-written black-box order service; **honesty tooth**: an incumbent with
  a hidden trapdoor state beyond the bound is *missed* at small `n` (shown),
  caught when `n` is raised — bound-relativity demonstrated, not hidden.

**Done when:** recovery + certification work; the honesty tooth shows both
the miss and the catch; learned services compose with Phases 1–2 (a lifted
protocol can be caged and monitored).

---

## Phase 4 — Colonize VPL: nested sessions and recursive data

**Objective.** Climb to the last rung where full universal-tier discipline
survives: visibly pushdown languages — boolean closure and decidable
inclusion *with* call/return nesting (Alur–Madhusudan).

**Workpackages.**
- **P4a Nested sessions**: meta-spec gains call/return tool pairs
  (sub-transactions, `begin/end` blocks); `service_model` partitions the
  alphabet (call / return / internal); the dispatcher gains a visible stack;
  BMC extends over bounded-stack unrollings (Z3 ∧ CVC5); the reference
  service implements its own stack independently; entailed scenarios add
  unmatched-return and over-pop traces. Teeth: a dangling transaction
  (begin without commit) refused; an interleaving violation caught.
- **P4b Recursive data codecs**: a JSON-subset codec through the existing
  tree-sitter chain; VPL differential (independent recursive-descent
  reference vs emitted parser); well-formedness as visibly-pushdown
  membership.
- **P4c (optional, universal tier)**: NWA determinization + complementation +
  product emptiness, implemented once and dual-checked against the bounded
  SMT channel — inclusion *proofs* for session protocols. If the
  implementation cost outruns its value, the bounded channel alone ships and
  the certificate says "bounded".

**Done when:** nested teeth bite; JSON-subset codec certifies under the
differential; LINGUISTICS coverage table moves "hierarchical sub-dialogues"
into the handled column.

---

## Phase 5 — Compounding: tier tags and semantic macros

**Objective.** Bank the two currencies that never stop compounding.

**Workpackages.**
- **P5.1 Tier-classification certificates** (`generators/monoid.py`): from a
  protocol's DFA, compute the syntactic monoid and decide **aperiodicity**
  (Schützenberger): the kernel certifies the artifact's own hierarchy
  position ("star-free, hence LTL-definable" vs "regular, group present").
  Size-capped; dual-channel via two independent constructions (monoid
  algebra vs minimal-automaton pattern check).
- **P5.2 Reading macros under MDL** (`library/` + `buildloop/mdl.py` reuse):
  recurring statement bundles become named library entries — "the inventory
  pattern" = quantity + action + decrement + `G(q ≥ 0)` — admitted only with
  a compression win (MDL gate), expanded *before* compile so they are pure
  spec sugar, certified once as expansions. Steering by a corpus of requests.
- **P5.3 Measurement**: re-run the request corpus; Readings must shrink
  (statements/request, tokens/request) with certification rates held — the
  compounding made visible in `results/`.

**Done when:** tier tags appear on protocol certificates; the macro ledger
shows real compression on the corpus with no certification regression.

---

## Phase 6 — Horizon: shrink the fiat (never "done")

Replace hand-audited by-fiat components with verified equivalents as the
ecosystem provides them (verified LTL translators, verified parsers, verified
reference interpreters); keep the kernel swap-ready. This phase is listed so
the map is complete and its status is honest: the trust regress stops at fiat
**by theorem** (Gödel), so this phase asymptotically shrinks the base and
never eliminates it. No schedule; opportunistic.

---

## Cross-cutting workstreams (rolling, every phase)

- **W1 Ledger honesty**: machine-readable `claims`/`non_claims` on all
  certificates; tier taxonomy = {universal, emit-check, bounded-K,
  conformance-relative(n), monitored}; every demo prints the tier it earned.
- **W2 Performance inheritance**: new contracts get cache + channel-granular
  parallelism for free via `kernel.channel_specs`/`run_channel` — each new
  contract type adds its decomposition there.
- **W3 Documentation lockstep**: each phase updates README (capability),
  TRUST (trust deltas), LINGUISTICS (coverage-table moves), and captures its
  demo in `results/`.
- **W4 Regression discipline**: invariants + all demos green per phase; the
  live semantic synthesis re-runs whenever the Reading fragment changes; every
  phase commits and pushes to both branches.
- **W5 Fragment-extension checklist** (any new LF kind must ship all of):
  validation + groundedness rules · compile rule + provenance · entailed
  scenario derivation · prompt update · consistency-obligation coverage ·
  at least one tooth.

## Order and dependencies

```
P1 (LTLf + monitors) ──▶ P2 (monitored tier) ──▶ P4a (nested sessions)
        │                                            │
        └──────────▶ P5 (tags + macros) ◀────────────┘
P3 (L* lift)  — independent; composes with P2 (lifted incumbents get caged)
P6 — horizon, opportunistic
```

Recommended sequence: **P1 → P2 → P3 → P4a → P4b → P5**, W1–W5 rolling.
P1 is the keystone: it discharges the documented eventuality gap, stays
inside star-free, and manufactures the certified monitors that make P2 — and
with it, *generality* — possible.

## Risks, named

| risk | mitigation |
|---|---|
| flloat is a small third-party library | it is a checker *input*, dual-checked against the SMT channel; disagreement is first-class |
| finite-session LTLf ≠ users' infinite-horizon intuition | semantics documented; enforcement at `close` shown in the demo |
| L\* argument-alphabet explosion | boundary-value abstraction, *named on the certificate* |
| NWA inclusion implementation cost | optional (P4c); bounded channel ships regardless, labeled |
| fragment creep degrading the Reading gate | W5 checklist is mandatory per LF kind |
| monitor overhead at task time | monitors are table-lookup DFAs; measure in bench, budget < 10% dispatch cost |

## The end state, restated as acceptance

The roadmap is done — in the only sense "done" exists here — when:

1. a vague request with eventualities, sub-transactions, and per-call limits
   synthesizes to a certified service whose every element traces to a quoted
   span (P1 + P4a + semantic path);
2. an arbitrary incumbent component can be caged behind that service with a
   certificate that proves the cage and honestly declines to praise the cargo
   (P2);
3. an undocumented incumbent's behavior can be lifted into the same machinery
   with a bound-relative certificate (P3);
4. every certificate carries machine-readable claims, its hierarchy tier where
   decidable, and the ledger of interpretation (W1 + P5.1);
5. the Reading vocabulary demonstrably compresses with use (P5.2);
6. and the emit-check tier is still there — because it always will be.
