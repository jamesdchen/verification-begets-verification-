# Certified Generator Bootstrap

Code generates code. An LLM is permitted to author **declarative
specifications only**. Generated code is trusted because it is **checked** —
never because of who produced it.

Verification begets verification, compiler-bootstrap style: a small fixed
kernel adjudicates; a library of generators (programs of type `Spec -> Code`)
does all code emission; trust flows downhill through provenance. The LLM is an
untrusted proposal engine writing spec files only.

> Build philosophy: **outsource everything that exists.** We did not build a
> verifier, a parser generator, a codec generator, or a DSL. The formal
> methods ecosystem already produced these. The new code here is the wiring,
> the trust ledger, and the measurement.

See **[TRUST.md](TRUST.md)** for the trusted computing base enumerated line by
line.

---

## The five hard constraints (and where they live)

1. **The task-time path contains no LLM calls.** `run/` goes spec → planner →
   generator chain → code, deterministically. `buildloop/llm.py` installs a
   guard (`CGB_TASK_TIME`) that makes any LLM call raise while a task run is
   in flight. Same spec + same registry state ⇒ byte-identical output.
2. **LLM output is only ever a spec.** `buildloop/validate.py` rejects any
   proposal containing general-purpose code before it reaches the kernel.
3. **Nothing is trusted without a kernel verdict.** `kernel/` is fixed, ~120
   lines, stateless, swap-ready — the only component trusted by fiat.
4. **All emitted code executes sandboxed** — `sandbox/` uses Linux namespaces
   (`unshare --net --mount --pid`), tmpfs over `/home` `/root` `/tmp`, a
   scratch-only writable dir, uid 65534, rlimits. Enforced at the OS level,
   during kernel checking and at task time. No effect typing.
5. **Every artifact records provenance** — which generator emitted it, from
   which spec, under which certificate, at which tier
   (`run/__init__.py`, `library/`).

## Two-tier trust model (the heart of the design)

- **Emit-check tier** (the on-ramp): a generator is admitted after light
  vetting, but **every output is individually checked at emission time**
  (translation-validation). For codecs the check is the round-trip contract
  `decode(encode(x)) == x` + malformed-input rejection, Hypothesis-fuzzed
  against the real emitted codec in the sandbox, cross-checked by a Dafny
  proof of the spec-level contract.
- **Universal tier**: a generator whose contract is verified for **all** valid
  specs (a Dafny proof over the generator itself). Its outputs need no
  emission check. `promote` attempts this upgrade; on success the tier flips
  and the planner prefers it.

**Dual-checker rule:** no single checker's verdict admits or promotes. Every
verdict needs two independent evidence channels to agree (Dafny/Z3 vs.
Hypothesis; or Z3 vs. CVC5 on one obligation). Disagreement is never
discarded — it is logged as a first-class event with full artifacts.

## What was outsourced, and from where

| Role | Tool | Used for |
|---|---|---|
| Proof / SMT | **Dafny 4.11** (Z3-backed) | codec contract model + universal generator theorem |
| Independent SMT | **Z3**, **CVC5** | same-obligation cross-check, disagreement detection |
| Property testing | **Hypothesis** | behavioral check of the real emitted artifact |
| Codec generator | **Kaitai Struct 0.11** (`--read-write`) | `.ksy` spec → Python encode/decode |
| Parser generator | **tree-sitter 0.26** | grammar → parser (also the meta-level demo) |
| LLM spec languages | `.ksy`, tree-sitter `grammar.js`, Dafny contracts | existing, documented, in-training-data |

The only formal artifact we authored is `generators/codec_model.dfy` — a
machine-checked model of the codec contract (round-trip + truncation
rejection), proven for every well-formed field list, plus the universal
static-offset theorem used for promotion. (EverParse was evaluated for
seeding the universal tier directly; it is not wired in this MVP — the Dafny
model plays that role instead.)

## Seed domain

Text/binary format codecs. Task specs describe record layouts (int fields with
endianness, magic bytes, fixed/length-prefixed/null-terminated strings,
literal/counted repeats, enums). The oracle is crisp (round-trip +
malformed-input rejection), specs are short and declarative, and layering
(field codec / framing) exercises composition.

---

## Components

```
common.py              canonical hashing, tool paths, trusted-tool runner
sandbox/               OS-level namespace jail for all emitted code
kernel/                check(artifact, contract) -> Certificate | ErrorTranscript
  backends.py            Hypothesis / Dafny / (Z3+CVC5) wrappers
  certs.py               content-hash-bound certificate & transcript records
library/               SQLite registry: tiers, emission records, provenance,
                         retirement, events, corpus, kernel cache, metrics
generators/            the Spec->Code machinery (all fixed, trusted-by-fiat only
  ksy_model.py           .ksy subset parser + feature-atom vocabulary
  codec_model.dfy        machine-checked codec contract model  (36 lemmas)
  dafny_gen.py           per-spec + universal proof-obligation generators
  harness_gen.py         Hypothesis harness derived from a spec (never the LLM)
  emitters.py            ksc / tree-sitter / cc adapters
  abnf_chain.py          ABNF -> (tree-sitter parser) -> ksy chain + AST mapper
planner/               deterministic unification over spec grammars
run/                   task-time runner (zero LLM; asserted)
buildloop/             coverage miss -> LLM spec -> kernel -> admit / refine
  llm.py                 the ONLY LLM client (headless `claude -p`)
  validate.py            pure-spec gate
  admission.py           vetting + MDL gate + subsumption
  mdl.py                 minimum-description-length accounting
  loop.py                steering policies + refinement
  promote.py             universal-tier upgrade
  disagreement_demo.py   engineered Z3/CVC5 split
metrics/               reach/cost/depth/tier-mix/DL/size logging, CSV, plots
  backlog.py             fixed ~200-spec backlog generator (seeded)
cgb.py                 CLI
```

## Library compression (MDL)

A candidate is admitted only if it **reduces total solution description
length** across the backlog (sum of chain length + spec size to cover each
spec; uncovered specs charged a fixed penalty), unless it covers previously
unreachable specs (logged as an *expansion event*). When a new generator
subsumes existing entries they are marked **retired** — kept for provenance,
excluded from planning. Total description length is a first-class metric and
trends down over a run even as reach rises.

## Counterexample corpus (`--corpus`, off by default)

Every kernel rejection stores the failing `(spec, input)` pair. With
`--corpus`, future candidates are screened against the corpus **before** fresh
adversarial generation. Its effectiveness is an open question, so it is
instrumented: the metrics log records the fraction of rejections caught by
replay vs. fresh generation, and the metrics suite is run with the flag on and
off (milestone 8).

---

## Running the milestones

Prerequisites are installed by `./setup.sh` (Dafny via dotnet, Kaitai via
Maven, tree-sitter via cargo, Python packages via pip). All commands below
write to `./artifacts` (override with `CGB_ARTIFACTS`). The build loop needs
an authenticated `claude` CLI on PATH.

```sh
export CGB_ARTIFACTS=$PWD/artifacts
```

**M1 — Kaitai on-ramp + mutation rejection.** Seed the opening library
(admitted only after a kernel emission check), drive one spec through the full
deterministic path, then show a mutated codec rejected.
```sh
python3 cgb.py seed
python3 cgb.py run specs/backlog/a_uint_be_000.ksy
python3 milestones.py m1        # includes the mutate-and-reject demo
```

**M2 — emission record + promotion.** Accumulate emission checks over 20 task
specs, then promote the fixed-uint generator to the universal tier (Dafny
proof + Hypothesis spec-fuzz); afterward emission checks stop and the planner
flips its preference.
```sh
python3 milestones.py m2
```

**M3 — build loop end to end.** A coverage miss becomes an admitted generator
from an LLM-authored spec (no human-edited code), with ErrorTranscript-driven
refinement when the first proposal fails.
```sh
python3 cgb.py build --policy frequency
```

**M4 — recursion demo.** tree-sitter (a generator) emits a parser that becomes
the input stage of a two-link chain (ABNF → parser → ksy → codec); provenance
depth ≥ 2.
```sh
python3 cgb.py build --policy frequency   # picks the ABNF miss once ksy is covered
python3 cgb.py run specs/backlog/k_abnf_000.abnf
```

**M5 — metrics + reach-vs-cost plot.** 20+ build-loop iterations under each
steering policy (`frequency` = most recurrent miss; `closure` = miss whose
resolution newly covers the most backlog specs), producing CSV + a matplotlib
reach-vs-cost plot with one curve per policy.
```sh
python3 milestones.py m5
```

**M6 — logged dual-checker disagreement.** A nonlinear-arithmetic obligation at
the edge of automatic decidability: Z3 proves it, CVC5 times out to `unknown`;
the kernel logs the split and issues no certificate.
```sh
python3 milestones.py m6
python3 cgb.py events dual-checker-disagreement
```

**M7 — subsumption.** A broader generator is admitted; narrower entries are
retired; total description length drops while reach does not.
```sh
python3 cgb.py events retirement
```

**M8 — corpus comparison.** Re-run the M5 metrics with `--corpus` on; report
the caught-by-replay fraction alongside the reach-vs-cost curves.
```sh
python3 milestones.py m8
```

`milestones.py all` runs the full sequence and writes every artifact under
`artifacts/` (logs, `metrics_*.csv`, `reach_vs_cost*.png`).

## Inspecting state

```sh
python3 cgb.py status                 # registry: generators, tiers, records
python3 cgb.py events [KIND]          # logged events (admission, promotion,
                                      #   retirement, expansion, disagreement, ...)
python3 cgb.py export-csv out.csv     # metrics log
```

## Independent second path (cross-implementation differential)

Round-trip (`decode(encode(x)) == x`) is a second evidence path the problem
hands you for free — encode vs. decode — but it has a structural blind spot:
a codec can be internally round-trip-consistent yet *wrong about the wire
format* (e.g. read and write a field in the wrong endianness), and round-trip
alone will never flag it. Catching that class requires a **genuinely
independent implementation** whose bugs don't correlate.

`generators/refcodec.py` is exactly that: a from-scratch reference codec that
shares no code with Kaitai. The kernel's `codec-differential` contract
certifies a codec via two independent channels — the Kaitai codec vs. the
reference codec (behavioral, byte-for-byte + cross-decode, sandboxed) and the
Dafny contract proof (logical). Independence lives in the translators, so
agreement is real N-version evidence, not one artifact checked twice.

```sh
python3 cgb.py differential specs/backlog/a_uint_be_000.ksy
python3 demo_differential.py   # shows a wrong-but-self-consistent codec that
                               # round-trip passes and the differential catches
```

The demo (`results/differential_demo.txt`) makes the point concrete: a
flipped-endian codec passes round-trip (it is self-consistent) yet the
differential catches the divergence with a witness input, and a mutated
Kaitai codec is cleanly rejected. This is path **(i)** from the design notes —
independence injected by a heterogeneous trusted artifact, which is the only
sound source of it (you cannot manufacture it by re-sampling the LLM). See the
`codec-differential` route in `kernel/__init__.py`.

**Lifted one rung up (ABNF → codec).** The same idea applies to a *chain*, not
just a codec. `cgb.py chain-differential spec.abnf` certifies an ABNF spec's
codec by two independent end-to-end routes: the tree-sitter chain
(parser → ksy → Kaitai) versus a reference route (reference tokenizer →
`abnf_tokens_to_fields` → reference codec). The routes share no parser, no
mapper, and no codec generator, so a shared-misconception in the *mapping or
codec-generation* stages — not just a codec bug — diverges and is caught.
`demo_differential.py` Part C shows a corrupted independent mapper that
round-trips yet is caught by the rung differential. (Building this surfaced a
real bug immediately — the differential caught a magic-field mishandling in
the harness itself, which is the "independent implementations disagree →
someone is wrong" property working as intended.)

## Agent tool contracts (JSON Schema → certified tool boundary)

A tool contract *is* a message schema, so the same machinery certifies the
agent↔tool boundary — the layer where an agentic business takes untrusted,
LLM-generated tool calls. `cgb.py tool SCHEMA.json` takes a tool's JSON Schema
and emits a strict Pydantic validator + `TOOL_DEF` (the MCP / function-calling
descriptor) + `decode`/`encode`, certified by the kernel's `tool-differential`
contract over two independent channels:

- the Pydantic validator satisfies round-trip + rejection on
  **hypothesis-jsonschema**-generated instances (never LLM-authored), and
- the Pydantic validator and the independent **`jsonschema`-library**
  reference agree on accept/reject over generated + mutated instances.

Independence is free here — two separately-authored validator libraries — so
agreement is real N-version evidence. `demo_tool.py` (`results/tool_demo.txt`)
shows the teeth in the exact shape of a real bug: a "lax" validator that
forgets `extra='forbid'` **accepts unexpected keys** in a tool call — a
genuine injection surface when the caller is an LLM — yet round-trips and
accepts every valid call, so no single-validator check flags it. The
independent differential against the schema catches it. Same kernel, sandbox,
tiers, provenance, and MDL machinery as codecs; new files are
`generators/jsonschema_model.py` (spec model) and `generators/toolgen.py`
(Pydantic emitter + jsonschema reference + harnesses). What is certified is
the wire/validation shell, **not** the handler behind the tool — that stays
hand-written and labeled behind the certified boundary.

### Schema-lift: certified elimination of hand-written validators

The aggressive move — turn *existing* boilerplate into certified code with the
incumbent as the free anchor. `cgb.py lift INCUMBENT.py` hands the LLM a
hand-written validator (`accepts(data) -> bool`), the LLM infers the JSON
Schema it enforces (authoring **only** the schema — a spec, never code), and
the kernel certifies the inferred schema by the `tool-lift` contract's two
independent channels: the inferred validator is internally sound (round-trip +
rejection), and it **agrees with the incumbent** on accept/reject over
generated + mutated instances. The incumbent is the ground-truth anchor — no
external oracle needed. Divergence drives refinement (max 5 rounds); if the
incumbent's contract is inexpressible in the modeled subset, the differential
correctly refuses to certify rather than silently producing a wrong schema.

`demo_lift.py` (`results/lift_demo.txt`) shows both halves: the LLM infers the
`create_user` schema from incumbent code and it certifies against that code in
one round; and a deliberately loose schema (role as a free string instead of
the enum `{admin, user}`) is caught by the incumbent differential with a
witness input. This is the boilerplate-elimination loop — the same shadow /
differential-against-incumbent pattern, applied to validators.

## The hard case: cross-field constraints (dual-checked SMT proof + solver-as-adversary)

Everything above certifies *structural* contracts (types, shapes, enums,
round-trip). The genuinely harder layer is **cross-field semantic
constraints** — `start < end`, `priority == "high" => attendees >= 2` — which
JSON Schema provably cannot express and the schema-lift loop correctly refuses.
`cgb.py constraint SPEC.json` certifies these with a stronger oracle than any
amount of testing:

- **A real theorem, dual-checked.** The spec declares constraints and an
  `invariant` they should guarantee; the kernel proves `constraints => invariant`
  by feeding `constraints ∧ ¬invariant` to **both Z3 and CVC5** independently
  and requiring both to return `unsat`. These land in decidable QF_LIA, so the
  two solvers *agree on a load-bearing proof* (unlike the milestone-6
  disagreement, which was engineered) — and a genuine solver split would be
  logged as a first-class disagreement.
- **The solver is the adversary.** Z3 generates a satisfying model (a valid
  record) and, per constraint, the *tightest* input that violates exactly that
  constraint; those drive the emitted validator, so "code matches spec" is
  checked at the exact edges — e.g. `priority == "high" AND attendees == 1`,
  which blind fuzzing essentially never hits.

`demo_constraint.py` (`results/constraint_demo.txt`) shows all of it: a
`book_meeting` contract certifies (both solvers prove the invariant, the
validator matches at every solver edge); a validator bug (`<` → `<=`) is caught
because Z3 already produced `start == end`; and a **false invariant**
(`end_hour >= 2`) is *refuted by the proof* — Z3 and CVC5 both find a
counter-model — which no test suite could establish. Same kernel, sandbox,
tiers, and dual-checker rule; new files `generators/constraint_model.py` and
`generators/constraint_gen.py`. This is where the two evidence channels stop
being redundant: the SMT proof establishes a *universal* property (all inputs),
and the solver-boundary differential confirms the executable validator realizes
it.

## Protocol / sequencing contracts (bounded model checking)

The frontier past per-message validation: certify that a *sequence* of calls is
legal and safe — "authenticate before you act", "never ship an unpaid order" —
which no single-message schema or per-call constraint can express.
`cgb.py protocol SPEC.json` takes a spec of control states, integer context,
guarded transitions, and a safety invariant, and certifies it over three
channels:

- **Sequencing safety, dual-checked.** The kernel bounded-model-checks the
  transition relation — is any invariant-violating state reachable via legal
  transitions within the bound? — and requires **both Z3 and CVC5** to return
  `unsat`. When the control graph is acyclic the bound equals the longest path,
  so the result is **complete**, not merely bounded.
- **Solver-as-adversary, lifted to traces.** On an unsafe protocol the solver
  returns the *shortest illegal call sequence* — the exact `[pay, ship]` trace
  that reaches `shipped` with a nonzero balance.
- **Validator conformance.** The emitted session validator is differentialled
  against an independent reference simulator on solver-generated legal and
  illegal traces.

`demo_protocol.py` (`results/protocol_demo.txt`) shows all three: the `order`
protocol certifies (both solvers prove safety, complete; validator matches the
reference); an unsafe variant (partial payment, no ship guard) is caught by the
dual BMC proof with the solver's illegal trace; and a validator bug (drops the
pay guard) is caught by conformance. This is the sequencing/data class of bug —
a *legal-but-unsafe* trace — that per-message certification fundamentally
cannot see. New files: `generators/protocol_model.py`, `generators/protocol_gen.py`.

## Service composition — one meta-spec, four certified layers, one whole service

Each generator family above certifies one *kind* of contract in isolation. A
real service is all of them at once: a set of tools, each with an input schema
(tool-differential), some with cross-field logic (constraint-cert), all of them
transitions in one stateful protocol (protocol-cert). `cgb.py service SPEC.json`
takes a single **service meta-spec** and fans it out to every family, then binds
the resulting certificates into a whole-service artifact — a dispatcher whose
`call(tool, args)` enforces, in order, sequencing → schema → constraint → guard,
then applies the update and advances state.

- **Fan-out, not re-proof.** The orchestrator (`run/service.py`) certifies each
  tool's schema, each declared constraint, and the protocol *with the existing
  generators and kernel contracts* — every layer keeps its own certificate. The
  service certificate simply binds those certificate ids to the composed
  dispatcher's artifact hash; trust in the whole service reduces to trust in its
  layers plus one composition check.
- **The composition earns its own certificate.** Composing certified parts is
  not free: a dispatcher can drop or misorder a layer and still be built from
  certified pieces. A new `service-conformance` kernel contract checks the
  emitted dispatcher against an **independent jsonschema-based reference
  service** (no shared code) on call sequences that exercise every layer —
  including a **solver-generated** guard-boundary input (Z3 finds an assignment
  that satisfies every per-call constraint yet falsifies the guard, so the guard
  is the *sole* deciding layer; UNSAT means the guard is not separable and the
  case is honestly skipped) — plus a **liveness** witness that the dispatcher
  accepts a full legal run (non-vacuity). The composition thus uses the same
  solver-as-adversary discipline as the constraint and protocol layers, not a
  best-effort probe.
- **Failures are localized.** On a break anywhere in the stack the report names
  the *first* failing layer (`tool:pay`, `constraint:pay`, `protocol`,
  `composition`) rather than an opaque whole-service failure.

`demo_service.py` (`results/service_demo.txt`) shows all three: the `orders`
service certifies end to end (seven certificates — four tool schemas, one
constraint, the protocol, the composition); a broken protocol layer (partial
payment) is caught and localized to `protocol` by the dual BMC proof; and a
hand-mutated dispatcher that **drops the guard layer** — every individual layer
still certifying — is caught by the composition's dispatcher-vs-reference
differential, which returns the exact under-payment trace the mutant accepts and
the reference forbids. This is the step where the certified library stops
producing isolated snippets and produces practical, whole-service code. New
files: `generators/service_model.py`, `generators/service_gen.py`,
`run/service.py`, `specs/services/orders.json`.

## Closing the loop — English request to a certified service (`synthesize`)

Every spec above is hand-written. The final move closes the flywheel back to the
LLM: `cgb.py synthesize "<request>"` (or a request file) has the LLM author a
**service meta-spec from a natural-language request** — a spec, never code — and
then runs the exact deterministic pipeline above to certify the whole service.

- **The LLM only ever emits a spec.** The proposal passes
  `buildloop/validate.py:validate_service_spec` (the pure-spec gate): it must
  parse into the fixed `ServiceModel`, every tool schema into the JSON-Schema
  subset, every guard/update into the integer predicate DSL, every constraint
  into the constraint model — anything else is a structured rejection, not code.
- **Certification is the deterministic, LLM-free pipeline.**
  `buildloop/service_loop.py` calls `run/service.py:certify_service` unchanged:
  the four certified layers plus the composition check. The LLM is nowhere on
  the checking path.
- **Rejection feeds back the machine-checked witness.** On any failing layer the
  loop hands the LLM the *localized* transcript — "layer `protocol` did not
  certify; solver's illegal trace is …" — and asks for a corrected spec, bounded
  rounds. The LLM refines against proofs and differentials, not vibes.
- **Success is a whole service with a proof.** The output is a composed
  dispatcher plus its composed-service certificate. The code was emitted and
  checked by trusted machinery; it is trusted because it was checked, not because
  the LLM produced it — the thesis of the whole system, now driven end to end
  from an English sentence.

This is where *verification begets verification*: the certified library turns a
request into practical, whole-service code, and every layer of that code carries
a certificate the kernel — not the LLM — issued. New files:
`buildloop/service_loop.py`, `validate_service_spec` in `buildloop/validate.py`.

`results/synthesize_demo.txt` captures a live run: from the English request
"a prepaid ticketing service … seats_left can never go negative", the LLM
authored a `tickets` meta-spec (naming its own cross-field rule `fairness`) that
certified all six layers in **one round** — three tool schemas, the `count`
fairness constraint (dual-SMT proof), sequencing safety (dual BMC, complete,
K=3), and the composition. The seat-safety property (`when purchased,
seats_left >= 0`) is *proved* over all reachable call sequences, not tested. A
matching hand-written spec lives at `specs/services/tickets.json` for
`cgb.py service`.

## Climbing the spec-to-code tower (vague language → certified service)

Everything above certifies the *bottom* of the tower — spec → code — with
kernel-grade evidence. The remaining gap is the *top*: language → spec. When the
request is precise, the meta-spec is nearly a transcription; as it gets vaguer,
the LLM must *design* — invent the lifecycle, the tools, the integer
abstractions, the safety invariant — and nothing above checks that its design
means what the request meant.

The system's answer is its own founding move, lifted one rung: **the
dual-checker rule applied to the language→spec gap.** From the same request,
the LLM derives two artifacts *independently*:

1. the **service meta-spec** (the implementer's reading), and
2. **intent scenarios** — concrete call traces with accept/reject expectations
   (the examiner's reading). The scenario author is shown the request and the
   tool *interface only* (names, argument schemas, states, context ranges) —
   never the guards, updates, constraints, or safety invariant. Its
   expectations must come from the request, not from reading the spec.

A new `intent-scenarios` kernel contract replays the scenarios through **both**
the certified dispatcher and the independent reference interpreter; both must
reproduce the expectations (and the scenario set must contain at least one full
legal run and at least one forbidden step, so it has teeth in both directions —
the pure-spec gate `validate_scenarios` enforces this). Agreement means two
independent linguistic derivations of the request converge on the same
behaviour — N-version evidence at the intent level. Divergence is logged as a
first-class `intent-divergence` event and fed back; the spec is re-authored
until the two readings converge or the loop exhausts.

`demo_tower.py` (`results/tower_demo.txt`) runs one domain at three rungs of
vagueness: a fully-specified prose spec; a partial description ("never let more
seats be reserved than remain… nobody may take more than 8"); and finally *"I
run a small venue. Help me not oversell tickets."* — no states, no tools, no
fields, no numbers. At every rung the machinery designs what is missing,
certifies all layers, and then survives the independent cross-examination of
its own reading. This is the honest scope of the climb: the spec→code half is
*proved*; the language→spec half is *cross-examined* (see TRUST.md §3.4 — that
gap admits evidence, not proof).

## The semantic path (linguistic theory operationalized)

The examiner above samples agreement between two whole-request readings — it
treats meaning as a black box. The principled path (`cgb.py synthesize
--semantic`) structures the climb by the theory of how language carries
meaning, and shrinks the untrusted leap accordingly. **The LLM never writes the
spec.** It writes a **Reading** (`generators/reading.py`) — a semantic analysis
of the request:

- **Discourse referents** (DRT): the quantities and actions the request talks
  about are introduced explicitly; everything else refers to them.
- **Speech-act force** (Austin/Searle) on every statement:
  `demand` — the directive's content, which **must carry an exact quote** of
  the request span (the gate checks occurrence *verbatim* — a fabricated demand
  is a mechanical rejection, not a judgment call);
  `presupposition` — what the text takes for granted ("oversell" presupposes
  selling; selling presupposes stock that decrements), quoting its trigger;
  `choice` — the pragmatic residue, design freedom the text leaves open, which
  **must quote nothing**. The trichotomy makes the informal gap *legible*:
  what the text said, what it assumed, what we chose.
- **Logical forms** (Montague-style) in a small deontic-temporal fragment:
  quantities with ranges, verb effects (`dec/inc/set`), comparatives
  (per-call bounds and state guards), global prohibitions `G(pred)` (the BMC
  now supports `when: "*"` — a real G, not a state-local check), and temporal
  precedence (`order`).

A **deterministic compositional compiler** (`generators/reading_compile.py`,
no LLM) compiles the Reading to the meta-spec, recording **per-element
provenance**: every guard, constraint, and invariant in the shipped service
traces back to *quoted span → force → logical form → spec element → proof*
(see `provenance.json` next to every artifact). Downstream, the pipeline
(`run/semantic.py`) checks what each layer of meaning owes:

1. **Groundedness** — demand quotes occur verbatim (exact, at the gate);
2. **Consistency** — the demand set is jointly satisfiable (Z3 ∧ CVC5,
   expect-sat: contradictory requests are refused before any code exists);
3. **Choice ⊨ demand** — a chosen lifecycle must entail every demanded
   ordering (transition-graph check; a design choice can never silently
   override the text);
4. the full **certification stack** on the compiled spec;
5. **Entailed scenarios** — each demand *generates its own* violating trace
   via the solver ("at most 8" entails reject-9); expectations are derived
   from the semantics, not guessed by a second model.

`demo_reading.py` (`results/reading_demo.txt`) shows the provenance chain and
**five kinds of misreading caught at five distinct stages**: a fabricated
demand (gate), contradictory demands (dual solver), a choice overriding a
demanded order (compiler), an inverted verb effect (the dual BMC's
unconstrained-argument adversary refutes it), and — the honest one — an
*omitted* presupposition (selling never depletes stock): every written demand
then holds vacuously, the pipeline certifies, and only the independent
examiner's meaning-level scenario catches it. Fidelity to what was written and
coverage of what was meant are different properties; the semantic path
delivers the first mechanically and keeps the examiner for the second.

## Certification latency (cache + parallelism, verdicts unchanged)

Certifying a service runs many independent checks (a contract per tool, per
constraint, the protocol, the composition). These are parallelized and cached so
the checking is fast — **without ever changing a verdict or the bytes of a
certificate**. `bench_latency.py` (`results/latency_bench.txt`) on a 4-core box:

| service | layers | serial | parallel (cold) | cached (warm) | speedup |
|---------|-------:|-------:|----------------:|--------------:|--------:|
| orders  |   7    | 16.5s  |      4.5s        |     0.00s     |  3.7×   |
| tickets |   6    | 12.0s  |      4.1s        |     0.00s     |  3.0×   |

- **Certificate cache.** Every check is content-addressed by `(artifact hash,
  contract hash)`; unchanged layers hit the cache and never re-run. Re-certifying
  a service is instant, and the synthesis loop's refinement rounds only re-check
  the layer the LLM actually changed. Cache lookups/writes stay on the main
  thread (the registry's SQLite handle is single-threaded); workers are pure.
- **Channel-granular parallelism, in processes not threads.** Every independent
  evidence channel of every uncached layer becomes its own **process** task
  across one flat pool (`kernel.channel_specs` / `run_channel`; the kernel's
  `adjudicate` is factored out so the verdict is a pure function of the collected
  channels). So the *two channels of the slowest layer land on two cores* instead
  of running back-to-back, and the pool packs the cores optimally. Processes,
  not threads, because the z3/cvc5 bindings keep process-global solver state that
  is corrupted not only by concurrent calls but by cross-thread *finalization* of
  solver objects — a real segfault we hit; per-channel processes isolate z3 for
  free. On the standalone `cgb.py tool` path a single contract's z3-free channels
  still overlap via threads. Effect: on a small 3-layer service, serial 4.6s →
  channel-parallel 2.1s (2.1×) because the tool layer's two ~2s channels overlap;
  on the 7-layer `orders` the box is already core-bound, so the win comes from
  packing (16.5s → 4.5s).
- **Determinism preserved.** Results are assembled in fixed layer order
  regardless of completion order, so the composed-service certificate is
  byte-identical cold vs. warm vs. serial (asserted in the bench). Parallelism
  changes only wall-clock, never what is certified. Note startup was measured
  *not* to be the bottleneck (~0.03s sandbox, ~0.3s Hypothesis import); the real
  cost is the property testing itself, which parallelism overlaps and the cache
  elides.

## Determinism & the no-LLM-at-task-time guarantee

`tests/` asserts that a task run produces byte-identical output across repeats
and that any attempted LLM call during a run raises. Run `python3 -m pytest
tests/ -q` (or `python3 tests/test_invariants.py`).
