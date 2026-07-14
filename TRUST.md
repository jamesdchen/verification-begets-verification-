# Trusted Computing Base

This system trusts code because it is **checked**, never because of who
produced it. The trust boundary is drawn explicitly here. Three tiers:
trusted-by-fiat (small, fixed, swap-ready), trusted-by-certificate (every
library entry, at a stated tier), and untrusted (the LLM and every candidate
spec).

Provenance flows downhill, compiler-bootstrap style: the kernel adjudicates;
generators emit; certificates record what was checked and by which agreeing
backends.

---

## 1. Trusted by fiat

These are trusted without a certificate. They are deliberately small and, per
the design, swap-ready. A bug here is a bug in the root of trust.

### 1.1 The kernel adapter — `kernel/__init__.py`
- The **only** component that issues a verdict by fiat. ~120 lines.
- Derives obligations, dispatches to backends, and enforces the
  **dual-checker rule**: no certificate is issued unless at least two
  independent evidence channels agree and none dissents.
- Holds no state; caching and event logging are injected. This is what makes
  it swap-ready — a different kernel can be dropped in without touching the
  registry or generators.
- Trusts (transitively) the backend wrappers in `kernel/backends.py` and the
  certificate/transcript records in `kernel/certs.py`.

### 1.2 The OS-level sandbox — `sandbox/__init__.py`
- Enforces containment for **all** emitted code, during kernel checking and
  at task time. Containment is the operating system's job, not a type
  system's (no effect typing anywhere in this codebase).
- Mechanism: `unshare --net --mount --pid --fork --kill-child`; tmpfs over
  `/root`, `/home`, `/tmp`; a bind-mounted scratch dir as the only writable
  persistent path; payload runs as uid/gid 65534 with a cleared environment
  and CPU/address-space/file-size rlimits.
- We trust that these namespace and privilege primitives do what the kernel
  documents. This is the largest by-fiat assumption.

### 1.2a The reference codec interpreter — `generators/refcodec.py`
- A fixed, hand-written codec interpreter used as the *independent second
  implementation* in the `codec-differential` contract. It shares no code
  with Kaitai, so its bugs are uncorrelated; the kernel diffs the two.
- It is trusted by fiat *as a checker input* the same way the Dafny model is:
  it is small, fixed, and audited, not generated. It never emits code that
  ships — it exists only to disagree with Kaitai when Kaitai is wrong.

### 1.2b The reference validators for the tool-contract domain
- The `jsonschema` library (Draft7Validator) is the *independent second
  validator* in the `tool-differential` contract, and `hypothesis-jsonschema`
  generates the test instances. Both are vendored, unmodified, and trusted
  as checker inputs the same way Hypothesis and the Dafny model are — the
  agent tool call, being LLM-generated, is untrusted; the two independent
  validators (strict Pydantic vs. jsonschema) must agree before the boundary
  is certified.

### 1.2c Incumbent validators in the schema-lift loop (UNTRUSTED, sandboxed)
- The hand-written validator an LLM-inferred schema is lifted from is
  *untrusted third-party code*.  It is never trusted; it is only ever run
  inside the OS sandbox, and it serves purely as the ground-truth anchor the
  inferred schema is differentialled against.  The LLM authors only the schema
  (a spec); the incumbent code is input, not something the LLM writes.

### 1.2d The reference service in the composition check — in `service_gen.py`
- The `service-conformance` contract diffs the composed dispatcher against an
  **independent, jsonschema-based reference service** (a separate interpreter of
  the same meta-spec, sharing no code with the emitted dispatcher). It is
  trusted as a *checker input* the same way `refcodec.py` and the jsonschema
  reference validators are: small, fixed, audited, and never shipped. Its only
  job is to disagree with the dispatcher when the dispatcher drops or misorders
  a certified layer. The layer-exercising inputs include a **Z3-generated**
  guard-boundary case (an assignment satisfying every per-call constraint while
  falsifying the guard) — the solver is a *trusted input generator* here, the
  same role it plays in `constraint-cert` and `protocol-cert`, never a verdict.
  The composition check does **not** re-prove the four layers — each already
  carries its own certificate; it certifies only that the composition preserves
  them, plus a liveness witness (the dispatcher must accept a full legal run, so
  agreement is not achieved by rejecting everything).

### 1.2e The Reading compiler — `generators/reading_compile.py`
- The semantic path's compositional compiler (Reading → meta-spec) is
  deterministic, LLM-free code and is trusted by fiat like the reference
  interpreters: small, fixed, audited. Two mitigations bound the damage of a
  compiler bug: (i) its *output* spec is fully certified by the existing
  stack — a compiler that emits an unsafe or inconsistent spec is caught by
  the same proofs as a hand-written one; (ii) the entailed-scenario stage
  replays each demand's solver-derived violation against the *running*
  dispatcher, so a compiler that drops a demanded bound is caught
  behaviourally. What a compiler bug could still do is mistranslate a
  logical form into a *different but internally consistent* obligation; the
  independent examiner channel and the provenance record (which exposes the
  claimed span→element mapping to human audit) are the checks on that.

### 1.2f Concurrency does not touch the verdict

Certification is parallelized and cached for latency, but the trust boundary is
unchanged: parallelism alters only wall-clock, never a verdict or a
certificate's bytes.
- Individual evidence **channels** are produced in separate **processes**
  (`run/service.py` via `kernel.channel_specs` / `run_channel`); a process shares
  no memory with another, and the kernel's `adjudicate` — the dual-checker rule —
  is a pure function of the collected channel list, run afterward on the main
  thread. Channels are reassembled in fixed order per layer, so the composed
  certificate is byte-identical to the serial run (asserted in `bench_latency.py`).
  Running each channel in its own process also isolates the z3/cvc5 solver state;
  on the standalone single-contract path, only **z3-free** channels overlap (via
  threads) and the remaining in-process z3 sites hold a process-wide lock
  (`common.SMT_LOCK`) because the solver bindings are not thread-safe.
- The certificate **cache** (`kernel.cache_key`, keyed by artifact + contract
  hash) returns a previously issued verdict for identical inputs — it is a
  memo of the kernel, not a second source of trust. A changed artifact or
  contract yields a different key and is re-checked from scratch.

### 1.2g The recursive JSON-subset codec inputs — `generators/json_codec.py`
- The `vpl-differential` contract (the corrected P4b route) certifies a
  RECURSIVE JSON-subset codec, which the .ksy/ABNF/refcodec chain structurally
  cannot express (recursion). Its by-fiat checker inputs are all small, fixed,
  hand-written, LLM-free, and never shipped:
  - **`rd.py`** — an independent recursive-DESCENT decoder + serializer (the
    `refcodec.py` role, made recursive). It shares **no code** with tree-sitter,
    so its bugs are uncorrelated; the kernel diffs the two implementations.
  - **`tswalk.py`** — the fixed tree-WALK decoder + serializer for Implementation
    A. It drives the emitted parser through the tree-sitter **C API via ctypes**,
    because the python `tree_sitter` binding is absent here; the parser `.so`
    (runtime statically linked by `emit_tree_sitter_parser_linked`) is emitted
    code and is only ever **loaded/executed inside the sandbox**, never trusted.
  - **`mutate.py`** — the fixed structural-mutation generator (bracket
    deletion/swap/truncation/stray token): the visibly-pushdown membership
    violations channel 2 requires two independent deciders to agree on rejecting.
  - stdlib `json` (restricted to the subset by canonical dumps) is a third
    independent encoder/decoder anchor, trusted the same way `hypothesis` is.
- **Honesty.** There is **no Dafny/proof channel** — the recursive language is
  outside the decidable codec model, so this contract is emit-check tier and both
  its channels are *behavioral* differentials over **disjoint input classes**
  (well-formed values vs. structurally malformed strings). Agreement is genuine
  N-version evidence but is bounded, not a proof. The **recursion depth is
  bounded and named on the certificate** (`Certificate.claims.depth_bound`, part
  of the contract identity); the Hypothesis `st.recursive`-style driver caps
  nesting to the same bound so deep inputs cannot become opaque sandbox crashes.

### 1.2h The LTLf monitor inputs — `generators/monitor_gen.py`, `generators/ltlf_smt.py`
- The `monitor-cert` contract (Phase 1) certifies an emitted LTLf **monitor DFA**
  — the artifact that turns a temporal demand ("every hold is eventually
  settled") into a table the dispatcher walks to make liveness a session-boundary
  safety check. Its by-fiat checker inputs are small, fixed, and never shipped:
  - **`flloat` 0.3.0** (+ `pythomata` 0.3.2, `lark-parser` 0.12.0, `sympy` 1.14)
    — the LTLf→DFA compiler. It is trusted as a *checker input* exactly as the
    Dafny model and `refcodec.py` are: a monitor is built by `monitor_gen`
    *from* flloat and is then dual-checked, so a flloat bug is caught, not
    shipped. flloat is unmaintained, so all four packages are pinned in
    `setup.sh`; disagreement is a first-class logged event, never a verdict.
    flloat appears in two independent places — the canonical table extraction in
    `monitor_gen` (channel 2's baked table) and the *live* automaton driven by
    the emitted `ref_stepper.py` inside the sandbox (channel 2's independent
    stepper) — and the two must agree with each other and with the SMT channel.
  - **`ltlf_smt.py`** — the bounded LTLf trace semantics as SMT-LIB, discharged by
    the already-trusted **Z3 and CVC5** (1.3). Channel 1 encodes the *baked*
    monitor table (read from the emitted `monitor.py` **by AST literal parse,
    never executed** — house rule: emitted code runs only in the sandbox) and the
    LTLf semantics of the demand and asserts they never disagree on any action
    trace up to the length bound; both solvers must return unsat.
- **Two channels, genuinely independent.** Channel 1 = baked table vs. SMT LTLf
  semantics (Z3 ∧ CVC5); channel 2 = baked table walk vs. the live flloat
  stepper (`ref_stepper.py`) over every trace in the sandbox. A mutated/incorrect
  table is refuted by BOTH.
- **Honesty.** These are **action-atom** LTLf demands only (F/U/before/within
  over action occurrences), so the SMT channel and the flloat channel are truly
  independent decision procedures for the same semantics. A context-predicate
  temporal demand ("eventually `balance==0`") would be **SMT-channel-only**
  (flloat cannot see integers) and would have to say so on the certificate. The
  agreement is verified for all traces **up to a named length bound** (tier
  `bounded-K`, `Certificate.claims.monitor_agreement_trace_len`), not proved for
  all lengths — an honest, bounded emit-check-grade guarantee, not a proof.
- The companion **protocol-cert** temporal obligation (also `ltlf_smt.py`, dual
  Z3/CVC5) proves the "liveness becomes safety" property over the *protocol*:
  no complete (terminal-ending) legal session violates the demand within the
  bound; the monitor's discharge guard on marked-terminal actions is the
  enforcement whose completeness the query verifies (an unguarded session-ending
  action is caught as a stranded trace). The BMC's idle discipline (idle is an
  absorbing suffix) makes "the trace's last real action is terminal" well-defined
  and keeps counterexamples clean.

### 1.2i The cage builder — `run/guarded.py` (Phase 2)
- The `cage-conformance` contract (tier **`monitored`**) certifies a **CAGE**: an
  arbitrary **incumbent** (untrusted third-party code, never LLM-authored —
  `class Incumbent` with `__init__` reset + `call(tool, args)`, interface-freeze
  item 7) run inside the OS sandbox behind a certified emitted dispatcher
  (ingress: sequencing / schema / per-call constraint / protocol guard / temporal
  obligation) and emitted output-contracts (egress: `output_schema`). The cage
  builder in `run/guarded.py` is trusted by fiat *as a checker input*, the same
  way `refcodec.py` and the reference service are: small, fixed, audited, never
  shipped, and it authors no verdict — the kernel adjudicates.
- **The incumbent is never trusted and never co-resident with trusted code.**
  Three separate one-shot sandbox runs draw the boundary: (1) the trusted
  dispatcher runs alone over the calls → per-call ingress verdict; (2) the
  untrusted incumbent runs alone via a batch driver — one flushed JSON line per
  query (never last-line parsing, so a poison query cannot lose the batch),
  per-query `signal.alarm` → `"__timeout__"`, exceptions → `"__error__"`, state
  threaded through the instance `__dict__`; (3) the trusted output-validators run
  alone over the incumbent's raw results *as pure data* → per-result egress
  verdict. The incumbent therefore cannot monkeypatch the dispatcher or fake an
  egress verdict, and every accept/reject/compare decision is made in this
  trusted, in-process module — the **external adjudication** P2's containment
  channel requires.
- **Two channels, disjoint input classes.** Channel 1 = **containment**: on
  solver-generated violating inputs (reused from the composition's
  `conformance_cases`, truncated at the first refusal) the caged pipeline rejects
  the exact call where the *bare*-but-sandboxed incumbent would act, with a
  non-vacuity teeth check that the bare incumbent acts on ≥1. Channel 2 =
  **transparency**: on the solver-certified legal run the caged results are
  byte-identical to the bare incumbent, compared via `common.canonical_json`
  (never raw `json.dumps`). Both must pass (dual-checker rule).
- **Cage hash** (interface-freeze item 9): canonical-JSON of the dispatcher,
  egress, and monitor file hashes, the incumbent hash, and the sandbox
  run-parameter dict + the `sandbox._INNER` jail-template hash (the "sandbox
  profile" is not otherwise reifiable). It enters the certificate's `cage_hash`
  claim and its cache identity (`_subject_and_cdesc`), so a changed incumbent,
  dispatcher, monitor **or sandbox profile** is a clean cache miss, never a stale
  false-green.
- **Honesty — the cage does not praise the cargo.** The certificate names tier
  `monitored` and carries a non-empty `non_claims`: the incumbent's business
  logic is **not** verified (only the boundary is), the cage does not certify the
  incumbent does anything useful, containment is checked on solver-generated
  boundary inputs to the model's structural bound (not proved for all inputs),
  and egress validates output **shape** against `output_schema`, never output
  truthfulness. The pure emitted dispatcher still returns no `result` — egress is
  purely a cage concern — so every existing boolean-projected harness is
  untouched and byte-identity holds.

### 1.3 Solver and compiler binaries (vendored, unmodified)
- **Dafny 4.11** (Z3-backed) — proves the codec contract model and the
  universal generator theorem.
- **Z3** and **CVC5** — independent SMT engines for the same-obligation
  cross-check.  For the `constraint-cert` contract they *prove* `constraints =>
  invariant` (both must return unsat) — a load-bearing dual-checked theorem;
  Z3 is additionally used as a *trusted input generator* (satisfying and
  tightest-violating models), but those are test inputs the sandboxed validator
  runs on, never a verdict.  For the `protocol-cert` contract the same pair
  bounded-model-checks sequencing safety (both must return unsat; complete when
  the control graph is acyclic), and Z3 also generates the shortest illegal
  trace — again a test input, not a verdict.
- **Hypothesis** — property-based testing of the real emitted artifact.
- **Kaitai Struct compiler 0.11** — `.ksy` → read-write Python codec.
- **tree-sitter 0.26** + a C compiler — grammar → parser.
- We trust these tools' *soundness as checkers*. We do **not** trust the code
  they *emit* — that is checked (emit-check tier) or covered by a proof over
  the generator (universal tier).

### 1.4 The Python standard library and interpreter, the host OS
- Ambient. Not enumerated further; standard for any tool of this kind.

Everything else in this repository is either trusted-by-certificate or
untrusted.

---

## 2. Trusted by certificate

Every library entry has type `Spec -> Code` and is trusted only at the tier
its certificates support. Certificates are content-hash-bound records naming
the backends that agreed (`kernel/certs.py`).

### 2.1 Emit-check tier (the on-ramp)
- Admitted after light vetting; **every output is individually checked at
  emission time** before use (translation-validation style).
- The emission check for the codec domain: run the emitted encoder/decoder in
  the sandbox against `decode(encode(x)) == x`, malformed-input rejection,
  and canonicality — inputs generated by **Hypothesis from the task spec,
  never by the LLM** — and, in parallel, prove the spec-level contract with
  **Dafny**. Both channels must agree (dual-checker rule).
- Trust scope: a specific emitted artifact, for a specific spec, under a
  specific certificate. Nothing about the generator in general is trusted.
- Registered emit-check generators today: the Kaitai family (various
  grammars) and the ABNF→ksy tree-sitter chain.

### 2.2 Universal tier
- A generator whose contract is verified for **all** valid specs in its
  grammar: a Dafny proof over the generator itself
  (`generators/codec_model.dfy` + the universal obligation in
  `generators/dafny_gen.py`), cross-checked by Hypothesis spec-level fuzzing
  of real emissions.
- Outputs need **no** emission check. The planner prefers universal-tier
  entries when both cover a spec.
- Trust scope: the generator, over its entire declared grammar. This is the
  strongest tier and the destination of `promote`.

### 2.3 Composed run certificates
- A task-time run emits a composed certificate binding the spec hash, the
  emitted artifact hash, the generator chain, per-link tiers, and the
  emission-check certificate ids (`run/__init__.py`). Trust in a run reduces
  to trust in its links' certificates.

### 2.4 Composed service certificates
- A `cgb.py service` run emits a **composed-service certificate**
  (`run/service.py`) binding the service spec hash, the dispatcher artifact
  hash, and the certificate id of every layer — one per tool schema, one per
  declared constraint, one for the protocol, and one for the composition itself.
  Trust in a whole service reduces to trust in its four certified layers plus the
  single `service-conformance` check that they compose faithfully. No layer is
  re-proved by the composition; the dual-checker rule holds at each layer and at
  the composition (dispatcher-vs-reference differential agreeing with the
  liveness witness).

### 2.5 Monitored tier — the cage (Phase 2)
- The `cage-conformance` certificate is tier **`monitored`**: it binds the cage
  hash (dispatcher + egress + monitor + incumbent + sandbox profile) to two
  agreeing behavioural channels — containment and transparency (§1.2i). Trust in
  a caged component reduces to trust in the certified dispatcher layers, the OS
  sandbox, and this one boundary certificate. Crucially this tier is **about the
  cage, not the cargo**: its non-empty `non_claims` machine-readably record that
  the incumbent's correctness, usefulness, and output truthfulness are *not*
  certified. A consumer of the trust ledger can therefore see exactly where the
  boundary of the guarantee lies — the same honesty discipline as the
  `intent-admission` tier (§3.4).

Retired entries remain in the registry for provenance but are excluded from
planning; they carry a `subsumed_by` pointer to the broader generator that
replaced them.

---

## 3. Untrusted

Nothing here is trusted. Its output is either validated to be a pure spec and
then checked by the kernel, or rejected.

### 3.1 The LLM (`buildloop/llm.py`)
- An untrusted **proposal engine**. It authors only declarative
  specifications: generator specs (JSON), `.ksy` documents, tree-sitter
  `grammar.js` in a declarative subset, and (where a backend needs them)
  contract annotations. It never authors general-purpose code and never
  authors test inputs.
- Every LLM output passes through `buildloop/validate.py`, which rejects
  anything containing general-purpose constructs, before it reaches the
  kernel or the registry.
- A task-time guard (`CGB_TASK_TIME`) makes any LLM call raise while the
  task-time path is executing: the task path provably contains no LLM
  involvement (asserted in tests).

- In the service-synthesis loop (`buildloop/service_loop.py`) the LLM authors a
  **service meta-spec** and nothing else. It passes the pure-spec gate
  (`validate_service_spec`) — which re-parses every embedded piece (tool schemas,
  the projected protocol, each constraint) through its own modeled parser — before
  the deterministic, LLM-free `certify_service` pipeline checks it. Refinement
  rounds feed the LLM the kernel's machine-checked transcript, never a
  human-authored hint; the LLM is never on the checking path.

### 3.2 All candidate specs
- Task specs at task time and generator/grammar specs at build time are
  untrusted input. A task spec that cannot be parsed into the modeled subset
  becomes a structured coverage miss; a generator spec that fails validation,
  the kernel, or the MDL gate is rejected with an ErrorTranscript.

### 3.3 Emitted code, before its certificate
- The Python codecs and the tree-sitter parser `.so` are untrusted artifacts.
  They are only ever executed inside the sandbox, and at the emit-check tier
  are individually checked before any use.

### 3.4 Intent scenarios — the language→spec gap (evidence, not proof)
- The scenario set an LLM authors for the `intent-scenarios` contract is an
  untrusted spec like any other: pure JSON traces + booleans, gated by
  `validate_scenarios` (which also requires at least one accepted run and one
  rejection, so the expectations cannot be vacuous).
- **What the check establishes:** two *independent* linguistic derivations of
  the same request — the spec's semantics (implementer's reading) and the
  scenario expectations (examiner's reading, derived without seeing the
  guards/updates/constraints/safety) — converge on the same concrete behaviour,
  as replayed by two independent implementations (dispatcher + reference).
- **What it does NOT establish:** that the spec matches the user's intent.
  Nothing can — intent lives outside every formal artifact in the system, so
  this gap admits *evidence*, never kernel-grade proof. Correlated
  misreadings (both derivations sharing one model's bias) survive the check;
  independence here is prompt-level, not model-level, and is therefore weaker
  than the tool-level independence of Z3-vs-CVC5 or Pydantic-vs-jsonschema.
  A divergence, conversely, is always meaningful: it is logged as a
  first-class `intent-divergence` event and drives re-authoring.
- This tier is deliberately labeled in certificates as `intent-admission`,
  distinct from every spec→code tier, so a consumer of the trust ledger can
  see exactly which claims rest on proofs and which on converging readings.

---

## Trust flow summary

```
LLM (untrusted) ──authors──▶ spec (untrusted)
     │                          │
     │                    validate.py  (pure-spec gate)
     ▼                          ▼
 generator (Spec→Code) ──emits──▶ code (untrusted artifact, sandboxed)
     │                          │
     │                     KERNEL (by fiat)  ── dual-checker rule
     │                          │
     ▼                          ▼
 certificate ◀──names agreeing backends── Dafny/Z3 · Hypothesis · CVC5
     │
     ▼
 registry entry @ tier  (trusted-by-certificate)
```

No single checker's verdict is ever sufficient. Disagreement between checkers
is never discarded — it is logged as a first-class `dual-checker-disagreement`
event with full artifacts, and yields no certificate.
