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
- The **only** component that issues a verdict by fiat. Small and enumerated
  here (it grows only by one honestly-labelled contract per phase — codec,
  tool, constraint, protocol, service, intent, monitor, cage, vpl — each a
  five-touchpoint entry, never a hidden checker); the trust regress stops at
  this fiat by theorem, and Phase 6 shrinks it as verified equivalents appear.
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

### 1.2j The tier-classifier — `generators/monoid.py` (Phase 5.1)
- The `tier-classification` contract classifies a protocol's **control skeleton**
  — the control states plus action-labelled transitions, with guards, integer
  context and any call/return stack **ignored** — as star-free or not.
  `generators/monoid.py` is trusted by fiat *as a checker input*, the same way
  `refcodec.py` and the reference service are: small, fixed, hand-written,
  audited, LLM-free, and never shipped. It is **pure and z3-free**, so both its
  channels run **in-process** (no sandbox, no solver); the kernel still
  adjudicates the verdict.
- **Two channels, genuinely independent (not two spellings of one algorithm).**
  Channel 1 = transition-**monoid** aperiodicity (every element has an idempotent
  power, `m^k == m^(k+1)`); channel 2 = a **counter-free** r-cycle search on the
  *minimal* DFA (r-cycle reachability in the r-fold product, r = 2..|Q|) — a
  different algorithm for the same property (Schützenberger), the z3-vs-cvc5
  independence grade. The obligation is "classify": the kernel issues a
  certificate only when the two **agree** (both star-free, or both not-star-free),
  and the tag rides on the certificate's `claims`
  (`("control_skeleton", "star-free" | "not-star-free")`, tier
  `control-skeleton-star-free` / `control-skeleton-not-star-free`). A channel
  **split** is impossible on correct code and is surfaced as a first-class
  `dual-checker-disagreement` event with no certificate.
- **Honesty.** The tag is **control-skeleton only** — the certificate's non-empty
  `non_claims` machine-readably decline to classify guards, integer context, or
  the stack (they are not in the DFA). Two correctness disciplines are baked into
  the classifier: **minimize first** (the syntactic monoid is the transition
  monoid of the *minimal* DFA — a non-minimal DFA shows spurious cycles), and a
  **feasibility cliff** — |Q| ≤ 8 after minimization, hard cap 10⁶ enumerated
  transformations. A nested/pushdown protocol (no plain DFA control skeleton) or
  the cliff yields an honest **tier-unclassified NON-certificate** — never a
  crash, never a false star-free claim. The star-free method is for **regular**
  control only; this is a non-pooled, direct-path contract (like `monitor-cert` /
  `vpl-differential`), so it adds no `channel_specs`/`run_channel` and leaves
  `POOL_SUPPORTED` and the channel-parity tripwire untouched.

### 1.2k Reading macros — `buildloop/mdl_macros.py`, `generators/reading.py` (Phase 5.2)
- A **macro** is an abbreviation that expands to ≥ 1 concrete Reading statements,
  letting a recurring Reading pattern compress future Readings. It is **not** a
  new logical-form kind: `reading.LF_KINDS` stays the single source of truth for
  the fragment, and a macro invocation
  (`lf = {"kind":"macro","name",...,"args":{param:value}}`) is expanded
  **inside `parse_reading`, before the groundedness gate**, each expanded
  statement **inheriting the invocation's force and quote** (otherwise a
  macro-expanded demand would carry no quote and be rejected). Expansion is
  purely deterministic and **LLM-free** — the macro table is a checker input,
  the same way `refcodec.py` and the reference service are. With no macro table
  (the LLM path and every pre-5.2 caller) nothing is expanded and the behaviour
  is byte-identical, so no cache re-key and no `CERTS_VERSION` bump.
- **The MDL gate** (`buildloop/mdl_macros.py`) mirrors ONLY the
  `dl_before`/`dl_after` gate shape of `buildloop.mdl.admission_decision` (the
  rest of `mdl.py` is codec-specific and is not reused). A candidate macro is
  admitted **iff** it strictly reduces the corpus description length
  (`dl_after < dl_before`, description length = statement/field counts + a token
  proxy over the logical forms) **and** it is used by **≥ 2 readings** — the
  two-witness discipline that stops a one-off from being minted.
- **The `macro-expansion-cert` contract** certifies that a macro-EXPANDED reading
  is identical to its hand-INLINED form. It is a **non-pooled, direct-path
  contract** (like `monitor-cert` / `tier-classification`): not in
  `POOL_SUPPORTED`, no `channel_specs`/`run_channel`, so the channel-parity
  tripwire is untouched. Two genuinely independent channels: channel 1 =
  **compile identity** — the expanded and inlined readings compile (compositional,
  deterministic; the Reading compiler is trusted like `refcodec.py`, TRUST 1.2e)
  to a **byte-identical** meta-spec (equal compile-hash), z3-free and
  sandbox-free; channel 2 = **entailed-scenario replay** — the expanded reading's
  emitted dispatcher reproduces every accept/reject that the *inlined* reading's
  demands **solver-entail**, sandboxed behavioural N-version evidence disjoint
  from the syntactic hash check. A faithful macro passes both; a **bad macro**
  that expands to a different spec (e.g. drops a guard bound) fails BOTH — a
  different compile-hash AND a guard-less dispatcher that accepts a call the
  inlined demand entailed as a rejection.
- **Honesty.** The certificate is tier **`emit-check`** with tuple `claims`
  (`macro_expansion`, the `shared_compile_hash`, `behavioral_agreement`) and a
  non-empty `non_claims`: it certifies that **THIS** expansion equals **THIS**
  inlined reading — not that the macro is meaningful or correct for any other
  request — and behavioural agreement is checked on the solver-entailed scenarios
  to the model's structural bound, not for all inputs.

### 1.2l The translation deriver table — `generators/derivers.py` (Combined-Loop W1)

- **The `translation-cert` contract** is the generic per-emission rung: it
  certifies one translation `Spec_high → Spec_low` against a **named independent
  anchor** (house rule 11 — *no `translation-cert` without an anchor*). It is a
  **non-pooled, direct-path contract** (like `macro-expansion-cert`): not in
  `POOL_SUPPORTED`, so the channel-parity tripwire is untouched. The kernel
  dispatch only looks up the fixed, LLM-free tables in `generators/derivers.py`;
  a new rung is one entry there plus one TRUST line below — never a kernel edit.
- **Anchors** (frozen vocabulary): (a) **`reference-lowering`** — a trusted fixed
  lowering `L` of the high language (`LOWERINGS`, the macro-cert pattern
  generalised). Channel 1 = compile identity: the translator's output and a
  trusted reference input both lowered by `L` are byte-identical; channel 2 = the
  reference's solver-entailed scenarios replay on the emitted artifact. The
  channel-2 harness is derived from the HIGH spec via `L`, **never** via the
  translator under test. (b) **`fixed-deriver`** — a per-language
  `(derive_obligations, derive_harness)` pair in `DERIVERS` (the ABNF entry uses
  `abnf_chain.tokenize` / `abnf_reference_fields`); dispatch lands in W1.3b.
  (c) **`incumbent-differential`** — the conversion oracle (W4.2); its
  `oracle_ref = {incumbent_hash, cage_hash, sandbox_params}` enters the cache
  identity, and the resulting tier is capped at **`conformance-relative(n)`**.
- **The `translator_hash` / `lowering_pipeline_hash`** for a fixed lowering is
  `derivers.lowering_pipeline_hash()` — sha256 over the fixed lowering module
  sources — so the pin is single-sourced and two builders cannot silently change
  every cache key.
- **Honesty.** A `reference-lowering` / `fixed-deriver` certificate is tier
  **`emit-check`**; the `claims` name the preservation relative to the named
  anchor and the `translator_hash`; the `non_claims` decline to certify the
  translator for any other input, and bound behavioural agreement to the
  solver-entailed scenarios at the model's structural bound. The anchor and every
  channel-2 oracle input enter the cache identity, so a changed anchor is a clean
  miss — never a stale false-green. Per-rung entries accumulate below:
  - **`reading` / `macro-reading`** (reference-lowering): the Reading compiler
    (TRUST 1.2e) is the trusted `L`; certifies a macro-expanded / rewritten
    reading lowers identically to its reference and reproduces its entailed
    scenarios.
  - **`abnf`** (fixed-deriver): the reference tokenizer + independent field route
    (`generators/abnf_chain.py`) are the deriver; certifies the emitted ksy
    stage reproduces the reference tokenisation (channel 1) and codec (channel 2).

### 1.2m The Lean proof-assistant backend — `kernel/backends.py: LeanBackend` (FORMALIZATION F0)
- Lean 4 + a **pinned, read-only Mathlib** join Dafny/Z3/CVC5 as vendored,
  unmodified checker binaries (TRUST 1.3, the `flloat` discipline). Two contracts
  land here — **`statement-cert`** and **`proof-cert`** — each **non-pooled,
  direct-path** (like `monitor-cert` / `tier-classification`): not in
  `POOL_SUPPORTED`, no `channel_specs`/`run_channel`, so the channel-parity
  tripwire is untouched. **No Lean text is LLM-authored (L1)**: the deterministic
  compiler emits it, the lexical escape gate re-checks it (F0.4, defense in depth,
  **never** the trust boundary — ⚠T7), the OS sandbox runs it, and **no
  verdict-bearing fact leaves a process where untrusted bytes executed (L5)**.
- **The two-run adjudication rule L5 (⚠T1/T2, review-blocking).** **Run 1**
  (untrusted) elaborates the subject in its own sandbox; its `.olean`/transcripts
  are **artifacts, not evidence**, and its exit code is a liveness signal only —
  elaboration-time code can write any file in the scratch dir, including a forged
  driver result. **Run 2** (trusted) replays the exported environment under
  `lean4checker` in a fresh sandbox where no untrusted bytes load as code, and the
  **axiom audit is enumerated by that pass** (`Lean.collectAxioms` → canonical
  JSON; `#print axioms` text is never parsed — ⚠D5). Every certificate claim is
  extracted by run 2 or by trusted code outside the sandbox.
- **`statement-cert`** — subject: a compiled Lean statement with `:= sorry` as its
  placeholder proof. Tier **`emit-check`** (⚠A9/T5 — a `sorry`-placeholder
  statement is *checked, not proved*). Channels, honestly stated (⚠T3 —
  elaboration + `lean4checker` replay of a `sorry` term are NOT two independent
  evidence channels): **channel 1** (run 1 + run 2) = elaboration succeeds AND the
  run-2 audit shows `sorryAx` present with every other axiom in the standard three
  {`propext`, `Classical.choice`, `Quot.sound`}, **plus the `pp.all` round-trip
  sub-check** (⚠D6 — the pretty-printed statement re-elaborates to a
  definitionally-equal term, catching the silent-coercion / wrong-instance class);
  **channels 2+** = the **tool-independent fidelity gates** (F2.1 non-vacuity —
  Z3∧CVC5+`decide` — and F2.2 entailed instances), whose passage is what makes the
  dual-checker rule genuinely met by **disjoint** evidence, not two kernel-family
  passes. Claims: `statement_hash, mathlib_commit, toolchain, axioms,
  independence, trivially_closed, boundary_behavior`; `non_claims`: fidelity to
  text beyond the named gates (the examiner is evidence, not a claim — ⚠T10),
  provability, novelty, and that channel 1 is `kernel-family`.
- **`proof-cert`** — subject: statement + proof artifact (tactic script or term).
  Tier **`kernel-checked`** (the WP-G `kernel/certs.py:TIERS` amendment,
  CERTS_VERSION bumped 9→10). **Channel 1** = sandboxed DIRECT `lean`
  elaboration accepts (run 1 — no lake at cert time: `lean file.lean -o` over
  read-only setup-built oleans, so no dependency resolution, no manifest, no
  package locks exist on the cert path; ⚠D3 by construction)
  + the run-2 trusted audit shows **no `sorryAx`** and axioms ⊆ the
  standard three (⚠T2: this catches an axiom smuggled via `Lean.addDecl`
  metaprogramming with no `axiom` token — the **environment audit is the axiom
  defense, not the escape gate**); **channels 2+** = the fidelity gates.
  `lean4lean`, when pinned, participates as an additional run-2 channel and
  upgrades the independence claim to `kernel-independent` (L4).
- **Independence, honestly (L4/⚠D6).** Lean's elaborator+kernel and `lean4checker`
  are **not** independent implementations — `lean4checker` links Lean's **own**
  kernel as a library, so it defends against elaboration-time environment
  manipulation, not kernel defects. Every certificate carries
  `independence="kernel-family"` (or `"kernel-independent"` when `lean4lean`
  participates) machine-readably — weaker than Z3-vs-CVC5 and never claimed
  otherwise. **With the toolchain absent** (this container) channel 1
  honest-degrades to `unavailable` → `unknown` → **no certificate**, even when
  every fidelity channel passes: there is no false green without the kernel.
- **L2 cache identity.** Both fold the FULL checking apparatus so a changed
  statement, proof, import set, pin, escape gate, or runner/driver is a **clean
  miss, never a stale false-green** (⚠T6): the Lean-text bytes, the narrow import
  set, the joint toolchain+Mathlib pin (`common.lean_toolchain_hash()`), the
  escape-gate source hash (`common.validate_lean_hash()`), and the runner/driver
  source hash (`LeanBackend._driver_hash()` over `kernel/backends.py`). Landing
  the contracts bumped `CERTS_VERSION`.

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

### 3.5 The speculative planner (Zone 3) — `planner/search.py`, `planner/lookahead.py`, `planner/choices.py`, `buildloop/speculate.py`
- The planner is **untrusted-by-construction, exactly like the LLM**. It
  decides only *what the expensive machinery spends itself on*; it never
  produces a certificate or a verdict, and no cache entry a verdict reads may
  exist unless the **unchanged kernel** computed it on the identical
  `(artifact, contract)` identity the non-speculative path would have used
  (**Z1**). Warming a cache entry changes *when* the kernel ran, never *what it
  concluded* — a warmed loser carries **no composed certificate**.
- **Z2 — exact objectives.** The searched phases (macro admission, lookahead
  steering, choice-space search) may score only with the *exact* pure functions
  of the live economy: `dl._ledger_total` over `dl.LedgerSnapshot`,
  `planner.plan_for_features` (the one declared chain-cost source), and
  `mdl_macros.corpus_dl`/`dl_reading`. The frozen-legacy `buildloop.mdl` mirror
  (`chain_length_for`) is **struck as an objective** — it is verified divergent
  from the planner (blind to `kind=="pass"` and to 3–4-link chains) and may
  appear only as a *reported* legacy series, never as a score. The ledger itself
  now charges `dl_macro` per live macro (`dl._ledger_total`) so the search
  objective and the ledger agree (a macro admission's realized `ledger_dl` drop
  no longer beats the expected saving by exactly the definition cost). This
  agreement holds over the corpus the seed step keeps in sync — every persisted
  reading has a live `nl-request` row, so `corpus_dl` (which prices all readings)
  and the ledger (which prices readings through their demand rows) range over the
  same set; and the witness filter below confines the mining objective to the
  exogenous sub-corpus, so a dream never inflates a saving a real request did not
  earn.
- **Z3 — measured fidelity.** Any component that *predicts* a kernel or gate
  verdict logs prediction-vs-actual as a first-class `speculation-divergence`
  event, so a planner that guesses wrong is caught in the ledger, not hidden.
- **Mined macros are no longer accounting-only (H58).** The W5.2 macro-reading
  rung means every *actual* macro use is certified per-emission by
  `translation-cert(anchor="reference-lowering")` against the **retained
  original baseline reading**, with the macro table folded into cache identity
  as `expansion_context` (a lossy rewrite is refused — TRUST 1.2k,
  `tests/test_rung.py`). A mined table is therefore untrusted, data-derived
  *vocabulary*; the rung is what makes its uses safe. The searched miner adds
  only *which* macros are proposed and *in what order* — every candidate still
  passes the unchanged per-macro MDL gate (`macro_admission_decision`), which is
  the arbiter, and the H3 filter (reject bare-wildcard bodies) plus the H2
  uniform-`(force, quote)` window rule keep unrealizable candidates out.
- **Speculative synthesis is a measured trade, not a proof (H10 caveat).** The
  `buildloop/speculate.py` pre-gates rank candidates cheapest-first
  (reading-gate → SMT → compile → entailed-replay). The stage-4 entailed-scenario
  replay is **rank-only: it never rejects a candidate** — a reference replay is
  evidence about fidelity, not a kernel verdict, so using it to *reject* would
  smuggle an untrusted signal into the gate. A deterministic every-Nth loser
  audit stays on by default and the run-record states the selection claim
  honestly. Certification still happens **only through the unchanged kernel**;
  the repo's own captures show 1–3 rounds, so K-wide fan-out is reported as a
  measured trade, never a promised saving.
- **Dreams propose, only real witnesses decide.** The real/dream partition rides
  the demand ledger's own `origin` provenance (`exogenous` = real, `system` =
  dream), enforced at seed time (`cgb ledger seed-readings`): a real-classified
  reading with no committed request byte-match is a hard error. A witness filter
  restricts every `corpus_dl` computation in the miner, the gate, and GC to
  exogenous-origin readings, so a pattern that recurs only across dreams is
  mined-but-refused until real requests witness it.

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

## Formalization trust posture (L1–L5)

The formalization extension (`FORMALIZATION.md`) binds all house rules unchanged
and adds five formalization-specific rules; the per-contract entries for
`statement-cert` / `proof-cert` land in their own commits (§1.2m above).

- **L1 — the LLM never authors Lean.** It authors MathReadings (JSON, gated like
  every spec) and, on the proof path only, tactic scripts — a *checked
  certificate candidate*, never shipped code: its only execution is elaboration
  inside the OS sandbox, and the artifact trusted afterward is the kernel-checked
  proof term. The lexical escape gate (`buildloop/validate_lean.py`) is
  defense-in-depth and cheap-fast-reject, **never** the trust boundary.
- **L2 — statements are specs, and the checking apparatus is part of the
  identity.** Cache identity for the new contracts folds statement bytes, proof
  bytes, import set, toolchain hash, Mathlib commit, escape-gate source hash, and
  runner/driver source hash; a changed gate, driver, or pin is a clean cache
  miss, never a stale false-green. Landing the contracts bumped `CERTS_VERSION`.
- **L3 — fidelity gates are refusals, tripwires are events.** Non-vacuity and
  entailed-instance failures **refuse**; the triviality tripwire and the examiner
  **log first-class events and claims** but never issue or block a certificate by
  themselves — evidence, tier-labeled.
- **L4 — kernel-independence honesty.** Lean's elaborator+kernel and
  `lean4checker` are NOT independent implementations (lean4checker links Lean's
  own kernel as a library). Every statement-/proof-cert carries
  `independence="kernel-family"` (or `"kernel-independent"` when a genuinely
  independent reimplementation participates) machine-readably — weaker than
  Z3-vs-CVC5 and never claimed otherwise. What makes the dual-checker rule met by
  *disjoint* evidence is channel 2: the tool-independent fidelity gates.
- **L5 — two-run adjudication.** No verdict-bearing fact may originate from a
  process in which untrusted bytes executed: elaboration (run 1) produces
  artifacts, not evidence; a fresh trusted pass (run 2) replays the exported
  environment as *data* and enumerates the axiom audit itself.

**Honest tiers.** `statement-cert` is tier `emit-check` — a `sorry`-placeholder
statement whose meaning is corroborated by the tool-independent fidelity gates,
never by the kernel replay, which "re-typechecks; it does not corroborate
meaning". `proof-cert` is tier `kernel-checked`. In a container with no Lean
toolchain the kernel channel is *unavailable*, so no certificate issues and no
false green is possible — the fidelity layer certifies statement-vs-text, and the
F0 kernel certificate is honestly **deferred**.

**Out of scope**, tier-labeled because no checker exists: (1) mathematical
importance — the system prices compression over witnessed demand, never
significance; (2) autonomous fragment growth — new logical-form kinds land only
through the human-gated W5 checklist, permanently; (3) Mathlib contribution — the
library is a pinned, read-only checker input; (4) proof-search research — the
thesis is statement-fidelity plus governed vocabulary growth.

**Sandbox read-only mounts (F0.5 capability).** `sandbox.Sandbox` accepts
`ro_mounts` — host directories bound READ-ONLY at `/ro/<name>` inside the jail,
mounted before the tmpfs blinds so the payload sees exactly the named
checkouts and nothing else — plus `extra_path`/`extra_env` for the payload's
cleared environment. The Lean cert path uses this to expose the pinned Mathlib
checkout, the resolved toolchain, and the lean4checker build inside the jail
(require-by-local-path, ⚠D3); writes fail at the filesystem level
(`Read-only file system`), verified by live teeth in
`tests/test_lean_positive_path.py`. The `_INNER` template's bytes are folded
into cage identity (`run/guarded.py`), so this change is a clean cache miss
for every cage-conformance certificate — the designed L2 behavior, never a
stale false-green. The ⚠D6 pp.all round-trip is now a real `LeanBackend`
primitive whose def-eq verdict is kernel-checked (re-elaborating the printed
type and type-checking the original constant against it), labeled
kernel-family like the rest of channel 1.

**Reflection discharge routes (PLAN_REFLECT S4b — the promotion ceremony,
maintainer-signed 2026-07-23).** `tools/FgReflect.lean` joins the enumerated
trusted surface **as a PROVEN artifact, not by fiat**: its soundness theorems
(`check_sound`/`checkAll_witness` and the route theorems below, plus the Nat
mirror) are Lean-lane kernel-checked (runs 30034874109, 30037692348,
30050091009 at the v4.15.0 pin), so citing them is citing the kernel. The
pinned discharge vocabulary (`kernel/certs.py`, CERTS v13) gains the three
route-qualified entries — `reflection/checkAll_witness` (LIVE on
exists-anchor-cert), `reflection/checkStmtBox_sound_exOnly` and
`reflection/sall_guard_of_check` (vocabulary-reserved, refused by construction
until their own cert stanzas land). Entrance evidence, all ledger-measured
(`results/reflect_agreement.jsonl`, tooth-evaluated): 66 agreements over 8
lane runs and 10 distinct committed readings, ≥2 multi-variable and ≥2
hypothesis-bearing, zero unexplained disagreements (the four historical
disagreements carry the confirmed heartbeat-budget root-cause). The unproven
GLUE around the proven artifact is named, trusted-by-fiat with teeth: the
quoter (round-trip parity + planted mis-quote tests) and the probe/replay
construction (byte-identity replay gate, planted-failure recording tests).
The shadow pairing is PERMANENT: the sweep keeps running beside the promoted
route and the agreement ledger keeps accumulating — promotion does not retire
the differential.

**Ledger provenance attestor (accepted by the maintainer in the same
sign-off).** The lean job signs `results/reflect_agreement.jsonl` via GitHub
OIDC + Sigstore (`actions/attest-build-provenance`); verification is
`gh attestation verify results/reflect_agreement.jsonl --repo <this repo>`.
This names **GitHub's OIDC issuance and Sigstore's transparency log** on the
trusted surface as the ledger's PROVENANCE attestor — provenance only, never
correctness: a signature proves which workflow run produced the bytes, and
nothing about what the bytes mean. Correctness remains where it always was —
the kernel, the teeth, the differential.
