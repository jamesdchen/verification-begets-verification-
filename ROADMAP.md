# Roadmap: from here to the two-zone economy

README.md says what the system is. TRUST.md says what is trusted. LINGUISTICS.md
says what is meant. This document says **what gets built, in what order, and
when each piece counts as done** — and, since a swarm of builder agents will
execute it without access to the conversation that produced it, it also carries
every hazard found by a five-agent adversarial sweep of the plan against the
actual codebase (findings marked ⚠, each verified by experiment or file:line
evidence), the interface freezes, the file-ownership rules, and the builder
briefing. The endgame the theory permits:

> an infinitely extensible archipelago of decidable islands (universal-tier
> proofs, amortized to zero marginal cost) inside an undecidable ocean
> (per-instance witnesses and certified monitors, amortized to a small,
> permanent, honest toll) — with specification cost attacked from both sides
> (cheaper Readings, specs lifted from the world) and the kernel remaining,
> forever and by theorem, the one thing not bootstrapped.

House rules, restated once (violating any of these is a review-blocking defect):

1. **Outsource every checker that exists**; build only wiring, ledger, and
   measurement.
2. **Dual-checker rule everywhere**: no certificate without two independent
   agreeing evidence channels; disagreement is a first-class logged event.
3. **Teeth per increment**: every phase ships a demo where the new machinery
   catches a planted defect — and, where honesty demands it, a demo of what it
   *cannot* catch.
4. **Honest tiers**: every certificate names exactly what is claimed and at
   what strength.
5. **The LLM authors only specs.** Arbitrary code enters only as *incumbent
   input*, never as LLM output.
6. **A new kernel contract lands as ONE commit touching FIVE points** ⚠:
   `_subject_and_cdesc` (the cache identity — omit it and two different specs
   collide on one cache key and silently share verdicts), `_dispatch`,
   `channel_specs`, `run_channel` (all in `kernel/__init__.py`), and a check
   method in `kernel/backends.py` — plus a TRUST.md entry for any new by-fiat
   checker input.
7. **Symmetric-implementation rule** ⚠: any feature added to the emitted
   dispatcher (`service_gen.emit_service`) must be *independently*
   re-implemented in the reference service (`ref_service_source`). Sharing
   code between them destroys the differential's meaning (TRUST §1.2d).
8. **Byte-identity rule** ⚠: emitted sources for existing spec shapes must not
   change byte-for-byte when a phase adds features (conditional emission
   only); certificates are content-addressed, so an unconditional new key in
   an emitted template invalidates every existing certificate and cache entry.

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
| infra | content-hash cert cache; channel-granular process parallelism; SMT lock; sandbox (~30 ms/invocation, measured) | — |

Fragment today: **safety-only** deontic-temporal logic (G + precedence) over
agent-symmetric integer aggregates.

---

## Phase 0.5 — Foundations freeze (LAND ALONE, BEFORE ANY PARALLEL WORK) ⚠

The sweep found that several "mid-phase" items are global interface changes
that break every consumer if landed concurrently with other work, plus four
already-latent defects. All of it is small; all of it goes first, as one
serialized phase.

- **P0.5.1 Certificate schema** (`kernel/certs.py`): add `tier: str = ""`,
  `claims: tuple = ()`, `non_claims: tuple = ()` — **plain immutable defaults,
  never `dataclasses.field(default_factory=...)`** ⚠ (verified: with
  `default_factory`, unpickling any of the 57 certificates already cached in
  the live registry raises `AttributeError` at use time; with plain defaults
  they load via class-attribute fallback). Fold the new fields into the
  `cert_id` hash body. Tier vocabulary frozen:
  `{universal, emit-check, bounded-K, complete-to-depth(D), conformance-relative(n), monitored, tier-unclassified}`.
- **P0.5.2 Cache versioning** ⚠ (verified silent-staleness): add
  `CERTS_VERSION = 2` to `kernel/certs.py`; `kernel.cache_key()` becomes
  `f"v{CERTS_VERSION}:{subject}:{contract_hash}"`. **Swarm rule: any commit
  that changes what a verdict contains or how an obligation is generated
  (e.g. `bmc_smtlib` output) bumps `CERTS_VERSION`.** Replace pickle in the
  registry cache with versioned JSON:
  `{"schema_version": N, "verdict": kind, "data": obj.to_dict()}` rehydrated
  on read, unknown versions = cache miss. Include `max_examples` in `cdesc`
  (today a 100-example verdict is served for a 10,000-example request).
  Migrate the registry's fixed 7-column `certificates` table (it silently
  drops unknown fields ⚠).
- **P0.5.3 Kernel parity tripwire** ⚠ (6 of 11 contract types already diverge
  between `_dispatch` and `channel_specs`; zero parity tests exist): add
  `POOL_SUPPORTED` list in `kernel/__init__.py` + `tests/test_channel_parity.py`
  asserting, per pool-supported type over a fixture, that
  `channel_specs`+`run_channel` reproduces `_dispatch`'s exact
  `(backend, role, result)` triples and `adjudicate` verdicts, and that every
  type used by any `run/*.py` orchestrator is pool-supported.
- **P0.5.4 Registry hardening** ⚠: `sqlite3.connect(self.path, timeout=30)` +
  `PRAGMA journal_mode=WAL; busy_timeout=30000` in `Registry.__init__`.
  Swarm rule: **one writer per DB file** — each concurrent loop sets
  `CGB_DB=.../loop-<id>.sqlite` *in the child environment before Python
  starts* (the env is read at `common` import time ⚠ — setting it after
  import is a silent no-op; see `tests/test_invariants.py`'s reload
  workaround).
- **P0.5.5 Task-time guard reentrancy** ⚠ (latent bug): `run/__init__.py`
  sets `CGB_TASK_TIME` and unconditionally pops it in `finally`, so an inner
  call clears an outer guard mid-session. Replace with a save/restore context
  manager (depth-safe) used by everything that sets the guard.
- **P0.5.6 Regression entrypoint** (W4 is currently unexecutable — no runner
  exists): add `run_regression.py` with two tiers.
  **fast** (per-commit, < 90 s, LLM-free): invariants (minus the admission
  test), parity + prompt tests, `demo_constraint demo_protocol demo_tool
  demo_reading demo_service` against a temp `CGB_DB`.
  **full** (per-phase): all demos incl. LLM-bound, full invariants, bench,
  live semantic synthesis; wall-clocks appended to `results/regression.txt`.
  New-demo rule: module constant `REQUIRES_LLM = True/False` so the runner
  tiers automatically; every demo ends `sys.exit(0 if all(flags) else 1)`
  (retrofit the existing demos — today they always exit 0 ⚠).
- **P0.5.7 Request corpus** ⚠ (P5.3 needs a *before* baseline that no phase
  creates): commit `specs/requests/` — ~20 natural-language requests spanning
  current + planned fragments (eventualities, nesting, limits).
- **P0.5.8 Prompt single-source scaffolding**: introduce
  `reading.LF_KINDS = {kind: (signature_line, force_rule)}` consumed by BOTH
  the validator and a generated grammar block in `_READING_PROMPT` (kills
  prompt-vs-validator drift ⚠); prompt tests: every accepted kind appears in
  the rendered prompt and vice versa; static prompt ≤ 6,000 chars; per-call
  prompt (base+request+feedback) ≤ 12,000 chars (keep last 2 transcripts, not
  all 5).

**Done when:** `python3 run_regression.py --fast` exits 0 on a clean checkout;
`tests/test_channel_parity.py` passes; a Certificate round-trips the cache
with all fields (guard test asserts every `dataclasses.fields` name present
after rehydration); old registry rows are unreachable (version-keyed), not
crashing.

---

## Phase 1 — Finish star-free: eventualities + the monitor factory

**Objective.** LTLf temporal demands ("eventually", "until", "before",
"within n steps") on finite session traces; every temporal demand compiles to
a certified monitor DFA; liveness becomes safety at the session boundary.

**Environment facts (verified by the sweep, do not re-litigate):**
`flloat==0.3.0` works on Python 3.11 with `pythomata==0.3.2`,
`lark-parser==0.12.0`, and sympy pinned (1.14 works today; flloat is
unmaintained — pin all four in `setup.sh`). MONA is absent; `ltlf2dfa` is NOT
an option; do not budget for it. flloat handles F/U/X/WX, proper LTLf
empty-trace semantics, and partial interpretations.

**Workpackages.**
- **P1.1 LF fragment** (`generators/reading.py` via `LF_KINDS`): frozen kinds
  and fields — `eventually {action}`, `until {hold_pred, until_action}`,
  `before {first, deadline}`, `within {action, steps}`. ⚠ Relax the gate rule
  at `reading.py:289-293`: today a demanded `always` is *required*, so a
  purely-temporal request is rejected — new rule: at least one demanded
  obligation of any kind. Temporal kinds join the "obligation cannot be a
  choice" list.
- **P1.2 Terminal actions** ⚠ (blocker found by sweep — nothing in the stack
  knows what "close" is): per-tool `"terminal": true` in the meta-spec.
  Thread it through `ServiceTool` → `protocol_spec_text()` (which currently
  drops unknown fields silently ⚠) → `ProtocolModel.Action` → BMC. Update the
  `validate_service_spec` top-level/tool key allowlists. `interface_text()`
  exposes terminal flags (it is interface, not semantics).
- **P1.3 Idle discipline in the BMC** ⚠ (blocker, proven by sat model
  `['IDLE','pay','IDLE','ship']`): assert `act[i]==IDLE → act[i+1]==IDLE` in
  `build_bmc`; trace length = first idle index; encode LTLf truth per step
  over the non-idle prefix only; fix `counterexample()`'s early `break` (it
  would extract an empty trace from an interior-idle model) in the same
  commit. `F`/`U` obligations may only be asserted violated on traces whose
  last real action is terminal — otherwise every incomplete prefix "violates"
  `F(b)` and the check is vacuous. Each LTLf obligation gets its OWN solver
  query (unsat = holds), not OR-ed into the safety disjunction.
- **P1.4 Dual semantics.** Channel (a): `generators/ltlf_smt.py`, bounded
  LTLf over the idle-disciplined unrolling, Z3 ∧ CVC5. Channel (b): flloat
  DFA replay on solver-extracted traces. ⚠ Atom hygiene (proven lexer
  hazards): NEVER put raw action names in formulas — an action named `last`
  parses as flloat's end-of-trace constant; keyword-prefixed names crash the
  lexer. Systematically prefix (`act_<name>`, `p_<demand_id>`) at
  formula-build time, same mapping for trace interpretations.
  ⚠ Honesty split: **action-atom formulas are dual-checkable by flloat+SMT;
  context-predicate formulas (`eventually balance==0`) are SMT-channel-only**
  (flloat cannot see integers; a valuation-interpreter hybrid shares
  arithmetic with one channel — if used, the certificate must say the
  independence covers LTLf semantics only). ⚠ Pin the alignment convention:
  predicate atoms at step i evaluate on post-state `ctx[i+1]`, in BOTH
  channels — a mismatch manifests as spurious dual-checker disagreements.
  ⚠ Bound interaction: `within n` needs `K ≥ n`; recompute
  `K = max(structural bound, max within-n)` and the complete/bounded label.
- **P1.5 Monitor factory** (`generators/monitor_gen.py`): per temporal
  demand, flloat DFA → dependency-free emitted table module.
  ⚠ Determinism (proven: pythomata state numbering varies with
  PYTHONHASHSEED): canonicalize — concretize sympy guards over the finite
  action alphabet, BFS-renumber from the initial state in sorted-action
  order, emit entries sorted by (state, action), `sorted(list)` for accepting
  sets. Never embed sympy reprs. ⚠ Embedding idiom: pick ONE for monitor +
  reference stepper (recommend Python-`repr` of plain sorted structures —
  int keys survive; json round-trips turn int keys into strings). Build the
  module as joined plain lines (the `emit_validator` pattern), NOT another
  40-line f-string (the brace-doubling bug class recurred here before ⚠).
  Frozen monitor interface: `TABLE` (dict state→{action→state}),
  `INITIAL`, `ACCEPTING` (sorted list), `step(state, symbol)`,
  `accepting(state)`, `pending(state) -> bool` (obligation undischarged).
  New kernel contract **`monitor-cert`** (five-touchpoint rule): channel 1 =
  monitor verdicts vs SMT semantics on solver-generated traces; channel 2 =
  monitor vs independently-emitted second stepper. `cdesc` must hash the
  trace set, or stale-cache false-greens follow trace-generation changes ⚠.
- **P1.6 Dispatcher + reference integration** (`service_gen.py`, symmetric
  rule): monitors advance on accepted calls; terminal actions refused while
  obligations pending, refusal layer name `"obligation"` (added to the frozen
  layer enum). Conditional emission ⚠: stack/monitor machinery appears in
  emitted sources ONLY when the spec uses it — plus a regression test that
  `emit_service`/`emit_validator`/`ref_service_source`/`bmc_smtlib` outputs
  are byte-identical on all existing demo specs.
- **P1.7 Obligation-aware golden run** ⚠ (blocker: with refusal-at-close, the
  current greedy `_golden_path` builds runs a CORRECT service refuses, and
  liveness fails on green services): replace the linear walk with search over
  (state, monitor-states) to a terminal configuration with obligations
  discharged; `conformance_cases` and `entailed_scenarios` inherit; new
  entailed case per `eventually` demand: attempt terminal action with the
  obligation undischarged → expect reject at that step.
- **P1.8 Loop, demo, docs**: prompt block via `LF_KINDS`; `demos/demo_temporal.py`
  (`REQUIRES_LLM=False` for parts A/B; the live synthesis goes through
  `run_regression.py --full`).

**Teeth.** A: "every hold is eventually purchased or released" certifies.
B1: a stranding service refuted by both solvers with the shortest stranded
trace. B2: dispatcher with dropped monitor wiring caught by the composition
differential. B3: mutated monitor table caught by `monitor-cert`.

**Done when (executable):** `python3 demos/demo_temporal.py` exits 0 with summary
keys `{part_a_certified, part_b1_stranding_refuted, part_b2_dropped_wiring_caught,
part_b3_mutated_table_caught}` all true, captured to
`results/temporal_demo.txt`; `python3 run_regression.py --fast` exits 0;
`python3 cgb.py synthesize "every reservation must eventually be confirmed or
released, max 4 per booking" --semantic` exits 0 with a `monitor-cert` layer
OK, captured to `results/semantic_synth_temporal.txt`.

---

## Phase 2 — The witness economy made explicit: the `monitored` tier

**Objective.** Arbitrary incumbent (third-party, never LLM-authored) code runs
inside a certified cage: ingress validation, Phase 1 monitors, egress output
contracts, OS sandbox. The certificate proves the cage and machine-readably
declines to praise the cargo.

**Frozen incumbent interface** ⚠ (nothing in the repo defines one; both P2 and
P3 depend on it; measured economics below make batch-in-sandbox the only
viable shape):
- `incumbent.py` exposes `class Incumbent: __init__(self)` (= reset),
  `call(self, tool: str, args: dict) -> jsonable`. **All state in instance
  attributes; module-level globals and /work files forbidden by contract**
  (reset = fresh object inside one sandbox run; a global-leaking incumbent
  corrupts every later query in a batch — fallback for unauditable
  incumbents: fork-per-reset *inside* the sandbox).
- Cross-invocation state (a session spans user calls): explicit serializable
  state — `init() -> state_json`, `step(state_json, tool, args) ->
  (state_json', result)` — held by the cage between one-shot sandbox runs
  (~30 ms incumbent-side latency per call, measured, acceptable). Do NOT add
  a persistent-process Sandbox API (a change to the trusted-by-fiat base)
  unless this fails.
- Batch driver protocol ⚠: one JSON line per query, flushed (never last-line
  parsing — a poison query must not lose the batch); per-query
  `signal.alarm` timeout mapped to `"__timeout__"`, exceptions to
  `"__error__"`; verdict comparison happens OUTSIDE the sandbox in trusted
  code (the incumbent shares the driver process and could fake output — for
  P3 that only mislearns itself, tolerable and stated in `non_claims`; for
  P2's containment channel the adjudication must be external).

**Workpackages.**
- **P2.1 Output path** ⚠ (gap: no result flows through the dispatcher at
  all): optional per-tool `"output_schema"`; caged `call()` returns
  `{"ok": True, "result": ...}` after emitted output-validator (same
  dual-validator pattern) or `{"ok": False, "layer": "egress"}`. The PURE
  emitted Service (no incumbent) keeps returning no `result` — egress is a
  cage concern (`run/guarded.py`), which keeps every existing boolean-
  projected harness untouched. Byte-equivalence obligations: conformance /
  scenario / liveness harnesses stay `["ok"]`-projected; the transparency
  channel compares `common.canonical_json` serializations (never raw
  `json.dumps` — dict order/floats produce spurious diffs ⚠);
  `_build_jobs` extends, never reorders, the job list.
- **P2.2 The cage** (`run/guarded.py`): dispatcher → monitors → sandboxed
  incumbent (state-threading protocol above) → egress. Cage hash ⚠ must
  include the sandbox run-parameter dict (timeout, cpu, mem, fsize) and the
  `_INNER` template hash — "sandbox profile" is not otherwise reifiable —
  plus dispatcher hash, monitor hashes, incumbent hash, canonical-JSON
  encoded.
- **P2.3 Kernel contract `cage-conformance`** (five-touchpoint rule):
  channel 1 = containment (on solver-generated violating inputs, the caged
  system rejects where the bare — still sandboxed — incumbent would act);
  channel 2 = transparency (legal runs: caged ≡ bare, canonical-JSON).
- **P2.4 Demo + docs** (`demos/demo_guarded.py`): malicious incumbent (oversells,
  malformed output) stopped at the exact call; honest incumbent unaffected.
  TRUST gains the cage section; certificate `tier == "monitored"` with
  non-empty `non_claims`.

**Done when (executable):** `python3 demos/demo_guarded.py` exits 0 with
`{part_a_honest_incumbent_transparent, part_b_malicious_incumbent_contained}`
true, captured; a script assertion loads the emitted cage certificate and
checks `tier=="monitored"` and `non_claims != ()`; `run_regression.py --fast`
exits 0.

---

## Phase 3 — Acquire specs from the world: protocol-lift via L\*

**Objective.** Learn an incumbent stateful service's protocol as a Mealy
machine; certify conformance-relative to a declared state bound; feed the
result into the existing stack.

**Measured economics (sweep, this machine):** sandbox invocation ≈ 30 ms;
batched in-sandbox querying ≈ 0.031 ms/query (2,000 reset+sequence queries in
one 62 ms run). **Per-query sandboxing is not viable** (a modest L\* run +
W-suite would take minutes-to-hours); the oracle MUST batch each refinement
round's unknown observation-table cells into one sandbox run (~tens of runs,
1–3 s total). Chunk W-suites at ≤10⁵ queries/batch.

**Workpackages.**
- **P3.1 Learner** (`buildloop/lstar.py`): L\* with Rivest–Schapire; alphabet
  = tool × representative argument values. ⚠ `constraint_gen.boundary_inputs`
  is only partially reusable (it needs a constraint spec, which a black box
  lacks); values come from schema-lift output or a user-declared abstraction —
  either way the abstraction map is recorded in certificate `claims`.
  ⚠ Output alphabet must be finite and defined: `ok/reject/__error__/
  __timeout__` or canonical-JSON hash classes.
- **P3.2 Unstated requirements, now stated** ⚠: RESET is part of the frozen
  incumbent interface and is named on the certificate (a wrong reset
  falsifies everything). DETERMINISM is checked, not assumed: run each batch
  (or a sample) twice; on mismatch refuse honestly with a first-class
  `nondeterministic-incumbent` event. The state bound `n` is an explicit
  input, echoed in `claims`. `non_claims` records the circularity: the
  equivalence oracle queries the same incumbent that answered membership.
- **P3.3 Orchestration** (`run/protocol_lift.py` — deterministic only; any
  LLM-refined variant lives in `buildloop/`, preserving `run/` never imports
  the LLM client ⚠; use the P0.5.5 guard context manager): learned machine →
  protocol spec → existing `protocol-cert` + service wrap; W-suite +
  random-walk differential channels.
- **P3.4 Demo** (`demos/demo_protocol_lift.py`): recovery of a hand-written
  black-box order service; honesty tooth: hidden trapdoor state missed at
  small `n` (shown), caught at larger `n`.
- **P3.5 Integration tooth (after P2)**: a lifted protocol caged and
  monitored.

**Done when (executable):** `python3 demos/demo_protocol_lift.py` exits 0 with
`{part_a_lifecycle_recovered, part_b_trapdoor_missed_at_small_n,
part_b_trapdoor_caught_at_larger_n}` true (plus
`part_c_lifted_service_caged` once P2 has landed); certificate `claims`
contain the state bound and abstraction map; `run_regression.py --fast`
exits 0.

---

## Phase 4 — Colonize VPL: nested sessions and recursive data

### P4a — nested sessions (visible stack)

**Objective.** Call/return tools (sub-transactions) with a visible stack;
safety by bounded-stack BMC; conformance via an independently-stacked
reference.

**Verified encoding (sweep prototype, both solvers):** per step `sp[i]: Int`
plus fixed slots `stk[d][i]: Int` for `d < D`, symbolic index case-split over
the D slots — **pure QF_LIA, no arrays**; K=8, D=4 ≈ 45 extra Ints, 17 KB
SMT-LIB, z3 12 ms / cvc5 40 ms. ⚠ Soundness condition to state on the
certificate: exploration is complete only for stack depth ≤ D, so the
dispatcher (and reference) must ENFORCE the same depth bound (refuse calls at
depth D); record `(K, D)` in claims.

**Known breaks the implementer must cover** ⚠ (from the sweep's function
inventory):
- A return tool's target is stack-determined — every reader of a static
  `t.to`/`a.to` is wrong for returns: `ServiceTool` (gains
  `kind ∈ {call, return, internal}` + return-continuation), `interface_text`
  (alphabet partition IS interface), `protocol_spec_text`,
  `protocol_model.Action`/parser, `build_bmc`, `emit_validator` (emits
  `state = to` statically today), `_table`, `conformance_traces` (BFS must
  walk (state, stack) configurations; add unmatched-return and over-pop-after-
  legal-prefix cases; the `paths[:24]` cap must prioritize configuration-
  diverse paths or nested demos only exercise shallow churn), `_REF_SIM`,
  `Service.call` (+ `self.stack`, empty-stack return → layer `"sequencing"`),
  `ref_service_source` (`_accepts` threads a stack), `validate_service_spec`
  allowlists.
- ⚠ `_golden_path` is broken for nesting BY DESIGN (verified: on
  `main→sub→main→done` it stops at the first revisited state and never
  reaches `close`; liveness would certify a run that never completes a
  session): replace with shortest-path search over (state, stack ≤ D)
  configurations to a terminal configuration **with empty stack** — merges
  with P1.7's obligation-aware search.
- ⚠ `acyclic_bound` returns the arbitrary constant `(8, False)` for ALL
  call/return protocols (they are inherently cyclic), silently weakening
  every nested certificate. Depth-aware bound: if the per-level internal-edge
  graph is acyclic, `K = (|states|−1)·(D+1) + 2·D` and the claim is
  **`complete-to-depth(D)`**; else `K = |states|·(D+1)`, claim `bounded-K`.
  Thread the third return element (depth) through all callers.
- Byte-identity: conditional emission per house rule 8, with the regression
  test from P1.6 extended.

### P4b — recursive data codecs (CORRECTED ROUTE) ⚠

**The original route is infeasible — verified**: the ksy subset rejects
`types:` outright (no user-defined or recursive types; empirically confirmed),
the ABNF front end demands exactly one flat rule, `refcodec` is a linear
field-list interpreter, and the Dafny channel is bound to the flat SpecModel.
**"JSON via the existing chain" cannot be built.** What IS verified to work:
recursive `grammar.js` (choice/seq/repeat, mutual recursion) passes
`validate_grammar_js` and compiles via `emit_tree_sitter_parser` (ABI 14) to a
working parser returning full recursive trees.

**Corrected pipeline:**
- New generator species `spec_language: "json-subset"`,
  `emitter: "ts-recursive-codec"`, own atom vocabulary
  (`json:object json:array json:string json:number json:bool json:null`,
  depth bound) added to `validate.py` and `admission.py` (skip the
  ksy-coverage check for this species).
- Implementation A (emitted): LLM-authored recursive `grammar.js` →
  tree-sitter parser → fixed trusted tree-walk decoder + fixed serializer
  (both are codecs: decode AND encode ⚠).
- Implementation B (independent): fixed, hand-audited recursive-descent
  parser + serializer (the `refcodec` pattern, recursive), sharing no code
  with tree-sitter. Optional third channel: stdlib `json` restricted to the
  subset.
- New kernel contract **`vpl-differential`** (five-touchpoint rule):
  channel 1 = cross-impl differential on Hypothesis `st.recursive` values
  (bounded depth, derandomized) incl. encode-side byte agreement and
  cross-decode; channel 2 = membership differential on mutated inputs
  (bracket deletion/swap/truncation — visibly-pushdown membership
  violations; tree-sitter side rejects via `has_error`).
- Honesty: no Dafny, tier is emit-check; the **depth bound is named on the
  certificate** (reference recursion + Hypothesis strategies + sandbox
  recursion limits make it real); cap the tree-JSON driver's nesting
  consistently or deep inputs become opaque sandbox crashes ⚠.

**Done when (executable):** `python3 demos/demo_nested.py` exits 0 with
`{part_a_nested_certified, part_b1_dangling_txn_refused,
part_b2_overpop_caught}` true; `python3 demos/demo_json_codec.py` exits 0 with
`{part_a_codec_certified, part_b_mutation_rejected_by_both}` true; both
captured; `grep -q 'hierarchical sub-dialogues' LINGUISTICS.md` finds the
coverage-table move; byte-identity regression test green on all pre-P4 specs;
`run_regression.py --fast` exits 0.

---

## Phase 5 — Compounding: tier tags and semantic macros

- **P5.1 Tier-classification certificates** (`generators/monoid.py`).
  ⚠ Correctness traps (sweep): the syntactic monoid is the transition monoid
  of the **minimal** DFA — Hopcroft-minimize first or the certificate is
  wrong; the tag applies to the **control skeleton only** (guards/context are
  not in the DFA) — certificate wording: "control-skeleton star-free".
  ⚠ Feasibility cliff: |Q|=6 → 46,656 elements (fine); |Q|=10 → 10^10
  (impossible). Precondition |Q| ≤ 8 after minimization, hard cap 10^6
  enumerated elements, on exceed emit honest `tier-unclassified (cap
  exceeded)` — not a failure, not a certificate.
  ⚠ Dual channel, honestly: NOT two implementations of the same algorithm.
  Channel 1 = monoid algebra (idempotent-power check m^k = m^(k+1)).
  Channel 2 = counter-freeness by pattern search on the minimal DFA
  (r-cycle reachability in the r-fold product, r = 2..|Q|) — a genuinely
  different algorithm for the same property, the Z3-vs-CVC5 independence
  grade; label it as such. flloat round-trip is NOT viable as a required
  channel (formula→DFA only); at most a third corroborating channel for
  protocols whose safety originated as LTLf demands.
- **P5.2 Reading macros under MDL** ⚠ (`buildloop/mdl.py` is codec-specific —
  `_covers`/`chain_length_for`/`generator_dl` are welded to
  atoms/backlogs/emit-chains; only the ~15-line gate shape is reusable): new
  `buildloop/mdl_macros.py` with
  `dl_statement / dl_reading(reading, macro_table) / dl_macro / corpus_dl /
  macro_admission_decision` (admit iff `dl_after < dl_before` AND uses ≥ 2).
  ⚠ Expansion point: inside/immediately after `parse_reading`, BEFORE the
  groundedness gate, with quote/force **inheritance from the invocation** —
  otherwise every macro-expanded Reading is rejected for quoteless demands.
  New kernel contract `macro-expansion-cert`: expanded reading compiles to a
  spec identical to the hand-inlined reading (compile-hash equality +
  entailed-scenario replay).
- **P5.3 Measurement**: re-run `specs/requests/` (created in P0.5.7, so the
  *before* baseline exists); `results/macro_compression.csv` with mean
  statements/request and tokens/request, certified-count unchanged.

**Done when (executable):** a script loads a protocol certificate and asserts
a `tier`-tag claim is present; `python3 demos/demo_macros.py` (or the measurement
script) exits 0 and `results/macro_compression.csv` shows reduced mean
statements/request with unchanged certification count; `run_regression.py
--fast` exits 0.

---

## Phase 6 — Horizon: shrink the fiat (never "done")

Replace hand-audited by-fiat components with verified equivalents as the
ecosystem provides them; keep the kernel swap-ready. The trust regress stops
at fiat by theorem; this phase shrinks the base asymptotically and never
eliminates it. No schedule; opportunistic. (Also fix in passing whenever the
kernel is touched: TRUST §1.1 still says "~120 lines"; it is 437 and growing —
replace with "small, enumerated here" ⚠.)

---

## Status — the Combined Loop (Phases 0–5 unified)

Phases 0–P5 above are executed. The successor refactor, which unifies the
breadth and height axes into one demand ledger priced in one currency
(`ledger_dl`) through one admission gate, lives in `PLAN_COMBINED_LOOP.md`, and
its landed state is documented in README's **"The Combined Loop"** section.
All workpackages are landed: W0 (ledger / currency / gate), W1
(`translation-cert` with **all three anchors** — reference-lowering,
fixed-deriver, incumbent-differential), W1.3b (the ABNF `fixed-deriver` +
per-stage cert in `run/__init__.py`), W2 (N-link planner + registry hardening),
W3 (the miss-typed scheduler), W4.1 (toll meter), W4.2 (conversion), W5.1
(promotion routing + the `universal-translation` contract), W5.2 (the
macro-reading rung), and W6 (the seven-pass decomposition + an independent
reference interpreter). What remains is verification the sandbox cannot run: the
LLM-authoring step of the conversion/rung end-to-end arcs, and the Dafny
codec-proof channel. See the README table for the authoritative breakdown.

---

## Order and dependencies (CORRECTED by the sweep ⚠)

The original graph called P3 independent; its acceptance tooth needs P1+P2
and its certificate wording needs P0.5.1. Corrected:

```
P0.5 (foundations freeze) ──▶ EVERYTHING (land alone, first)
P1 ──▶ P2 ──▶ P4a ──▶ P5.1-kernel-edit
P3-core (lstar + W-method + demo parts A/B) ─ parallel with P1/P2, after P0.5
P3-integration (lifted-protocol caged+monitored tooth) ─ after P2
P4b ─ parallel with anything (codec-side files only)
P5.2/P5.3 ─ after P1 (Reading fragment must be stable)
P6 ─ horizon
```

**Serialization rule (not preference):** P0.5 → P1 → P2 → P4a → P5.1 share
`kernel/__init__.py`, `kernel/backends.py`, `generators/service_gen.py`,
`generators/service_model.py`, `run/service.py` — they may not run
concurrently. Safely parallel: P3-core ∥ {P1, P2}; P4b ∥ anything; P5.2/P5.3
∥ P4. **Docs and shared results files are merge-owned** ⚠: README/TRUST/
LINGUISTICS edits are each phase's final serialized commit, never edited in a
parallel worktree; `results/semantic_synth*.txt` is re-captured by any phase
changing the Reading fragment (P1, P5.2) — serialized.

### File-ownership matrix (W = writes, N = new, r = reads; ★ = hot, 3+ writers)

| file | P0.5 | P1 | P2 | P3 | P4a | P4b | P5 |
|---|---|---|---|---|---|---|---|
| ★ `kernel/__init__.py` (five touchpoints) | W | W | W | r | W | W | W |
| ★ `kernel/backends.py` | | W | W | r | W | W | W |
| `kernel/certs.py` | **W** | r | r | r | r | r | W |
| ★ `generators/service_gen.py` (dispatcher AND reference, symmetric) | | W | W | r | W | | |
| ★ `generators/service_model.py` | | W | W | r | W | | |
| ★ `run/service.py` (`_build_jobs`) | | W | W | r | W | | |
| `generators/reading.py` (+`LF_KINDS`) | W | W | | | | | W |
| `generators/reading_compile.py` | | W | | | | | W |
| `run/semantic.py` | | W | | | | | W |
| `buildloop/service_loop.py` (prompt) | W | W | | | | | W |
| `generators/toolgen.py` | | | W | | | | |
| `generators/protocol_gen.py` / `protocol_model.py` | | W | | r | W | | r |
| `generators/constraint_gen.py` | | | | r | | | |
| `generators/ltlf_smt.py`, `monitor_gen.py` | | **N** | r | | | | |
| `run/guarded.py` | | | **N** | r | | | |
| `buildloop/lstar.py`, `run/protocol_lift.py` | | | | **N** | | | |
| `generators/monoid.py`, `buildloop/mdl_macros.py` | | | | | | | **N** |
| JSON-codec species (validate/admission/emitters + new) | | | | | | W/N | |
| `sandbox/__init__.py` | | | r (no API change) | r | | | |
| demos (each phase's, named above) | retrofit | N | N | N | N | N | N |
| `setup.sh` (flloat pins) | | W | | | | | |
| `tests/` (invariants, parity, prompt, byte-identity) | W | W | W | | W | | |
| README / TRUST / LINGUISTICS | W | W | W | W | W | W | W — merge-owned |

### Interface-freeze list (agree before ANY parallel work; changes require a serialized cross-phase commit)

1. **Certificate**: `{cert_id, kind, subject_hash, contract_hash, channels,
   created_at, tier: str = "", claims: tuple = (), non_claims: tuple = ()}` —
   plain immutable defaults; new fields inside the `cert_id` hash;
   `CERTS_VERSION` in the cache key.
2. **Dispatcher `call()`**: `{"ok": True}` (pure) / `{"ok": True, "result": …}`
   (caged) / `{"ok": False, "layer": <enum>}`; layer enum
   `{sequencing, schema, constraint, guard, obligation, egress}` (P4a may add
   none — empty-stack return is `sequencing`); reference `_accepts` extended
   symmetrically and independently.
3. **Reading statements**: `{id, force ∈ {demand, presupposition, choice},
   quote, lf}`; LF kinds and their exact field names live in
   `reading.LF_KINDS` (single source for validator AND prompt); temporal
   kinds as named in P1.1; gate rule "≥1 demanded obligation of any kind".
4. **Kernel channel dicts**: `{backend, result ∈ {pass, fail, unknown,
   error}, detail, role?, transcript?}`; role vocabulary `{smt-proof,
   behavioral-witness, cross-impl-differential}` (adjudicate keys on it);
   `channel_specs` entries are picklable primitive tuples; `POOL_SUPPORTED`
   is the registry of pool-safe types.
5. **Service meta-spec keys**: existing frozen; new — per-tool
   `"terminal": bool` (P1), `"output_schema"` (P2), call/return kind +
   pairing (P4a). `parse_service_spec`, `validate_service_spec`, the
   reference, and the prompt parse them in the same commit that introduces
   each.
6. **Monitor module**: `TABLE`, `INITIAL`, `ACCEPTING`, `step`, `accepting`,
   `pending`; canonical numbering (BFS, sorted actions); Python-repr
   embedding of plain sorted structures.
7. **Incumbent interface** (P2+P3): `class Incumbent` /
   `init()/step(state_json, tool, args)`; batch driver = one flushed JSON
   line per query; `__error__`/`__timeout__` symbols; reset = fresh object;
   no module globals.
8. **Result dataclasses**: `ServiceResult` / `SemanticResult` shapes as today
   (extend, never rename).
9. **Cage hash**: canonical-JSON of `(dispatcher hash, monitor hashes,
   sandbox run-parameter dict + _INNER template hash, incumbent hash)`.

### Builder briefing (prepend to every builder agent's task prompt)

1. Repo `/home/user/verification-begets-verification-`; Python 3.11, no venv;
   deps installed by `./setup.sh` (no requirements.txt — pin new packages
   there; flloat is NOT installed until P1 lands its pins).
2. Toolchain (env-overridable, defaults in `common.py`): Dafny
   `/root/.dotnet/tools/dafny`; Kaitai classpath `/opt/ksc/lib/*`;
   tree-sitter `/root/.cargo/bin/tree-sitter`; claude CLI
   `/opt/node22/bin/claude` (needed only for `synthesize`/`build`; demos with
   hand-written specs are LLM-free).
3. Isolation: export `CGB_DB` (and ideally `CGB_ARTIFACTS`) **in the child
   environment before Python starts** — they are read at import time; one
   writer per DB file; never share a `Registry` across threads/processes.
4. Git: commit to `claude/certified-generator-bootstrap-j32rpj`, push to BOTH
   that branch and `main`; single-line descriptive subjects in the existing
   style.
5. New kernel contract = five touchpoints + TRUST entry (house rule 6).
6. Concurrency: `with common.SMT_LOCK:` around every in-process z3/cvc5
   call; picklable `channel_specs`; fixed-order channel assembly
   (certificates must be byte-identical serial vs parallel —
   `bench/bench_latency.py` asserts it).
7. Sandbox rule: emitted/generated code runs only via the sandbox;
   `common.run_cmd` is for trusted tool binaries only.
8. Symmetric-implementation rule (house rule 7) and byte-identity rule
   (house rule 8) — both have dedicated regression tests; run them.
9. Demo conventions: docstring naming each part and its failure class;
   `part_a` happy path with per-layer OK/XX lines; one `part_b*` per tooth
   asserting the RIGHT stage caught it; final
   `print("\nsummary:", json.dumps({...}))` + `sys.exit(0 if all else 1)`;
   `REQUIRES_LLM` constant; capture via
   `python3 demo_X.py | tee results/X_demo.txt` and commit the capture.
10. Regression gate before pushing: `python3 run_regression.py --fast`
    (< 90 s, LLM-free) green; `--full` per phase; if the Reading fragment
    changed, re-run and re-capture a live semantic synthesis.
11. W5 checklist per new LF kind: `LF_KINDS` entry (validator+prompt) ·
    compile rule + provenance · entailed-scenario derivation ·
    `demands_smt` coverage · ≥1 tooth.
12. Docs are merge-owned: README/TRUST/LINGUISTICS edits are your phase's
    final commit, never made while another phase's worktree is open.

## Risks, named (updated by the sweep)

| risk | mitigation |
|---|---|
| stale cached verdicts across schema/obligation changes (⚠ verified) | `CERTS_VERSION` in cache key + JSON-not-pickle + field-presence guard test (P0.5.2) |
| `_dispatch`/`channel_specs` divergence (⚠ 6/11 types already) | parity test + `POOL_SUPPORTED` tripwire (P0.5.3) |
| SQLite lock collisions under a swarm | per-loop `CGB_DB` pre-import + WAL/timeout (P0.5.4) |
| spurious dual-checker disagreements from idle steps / atom lexing / alignment (⚠ proven) | P1.3 idle discipline; P1.4 atom prefixing + post-state convention |
| liveness failing on CORRECT services (⚠ two independent causes) | P1.7 obligation-aware + P4a stack-aware golden-run search |
| certificate/cache invalidation via emitted-source drift | conditional emission + byte-identity regression test (house rule 8) |
| flloat unmaintained | exact pins; it is a checker *input*, dual-checked; disagreement is first-class |
| pythomata nondeterministic DFA output (⚠ proven) | canonical extraction (P1.5) |
| L\* economics (⚠ measured 1000×) | batch-in-sandbox oracle; per-query timeouts; poison-query isolation |
| nondeterministic / global-leaking incumbents | determinism double-run check; instance-state contract; fork-per-reset fallback |
| P4b infeasible as originally written (⚠ verified) | corrected `ts-recursive-codec` + `vpl-differential` route |
| arbitrary K=8 for cyclic protocols weakening nested certificates | depth-aware bound + `complete-to-depth(D)` claim (P4a) |
| monoid blowup / wrong monoid on non-minimal DFA | minimize-first, |Q| ≤ 8, 10^6 cap, honest `tier-unclassified` |
| prompt-vs-validator drift; prompt bloat | `LF_KINDS` single source + budgets + prompt tests (P0.5.8) |
| regression wall-clock explosion | two-tier `run_regression.py` (P0.5.6) |

## The end state, restated as acceptance

1. a vague request with eventualities, sub-transactions, and per-call limits
   synthesizes to a certified service whose every element traces to a quoted
   span (P1 + P4a + semantic path);
2. an arbitrary incumbent component runs caged behind that service with a
   certificate that proves the cage and machine-readably declines to praise
   the cargo (P2);
3. an undocumented incumbent's behavior is lifted into the same machinery
   with a bound-relative certificate (P3);
4. every certificate carries machine-readable claims, its hierarchy tier
   where decidable, and the ledger of interpretation (P0.5 + P5.1);
5. the Reading vocabulary demonstrably compresses with use (P5.2);
6. and the emit-check tier is still there — because it always will be.
