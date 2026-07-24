# ARCHITECTURE.md — how this repo works, consolidated

STATUS: **DRAFT, all sections fleshed** (2026-07-18) — pending user
review before the banner comes off. Each section keeps its scope line,
sources, and must-answer questions as the acceptance test. Sections §7,
§9 (second table), and §11 describe the import layer, which landed on
main via PR #15 (merged 2026-07-19); claims resting on that work are
marked inline.

Ground rules this document was written under (and holds itself to):
(1) every claim cites a file, an artifact in `results/`, or a committed
verdict — this repo's culture is that prose without a pointer is not a
record; (2) where the honest answer is "measured and it said no," write
that — the repo's distinctive asset is instruments that refuse to
flatter it; (3) prefer the primary sources over any summary, including
this one.

---

## 0. The thesis in one page

Scope: what the repo IS — a certified generator bootstrap where code
generates code, an LLM may author *declarative specs only*, and nothing is
trusted because of who produced it, only because it was checked. Trust
flows downhill through provenance, compiler-bootstrap style.

Sources: README.md (top), TRUST.md preamble.
Must answer: the five hard constraints and where each lives in code; what
"verification begets verification" means operationally; what the LLM is
and is not allowed to do.

The repo is a **certified generator bootstrap**: code generates code, and
no artifact is ever trusted because of who produced it — only because it
was checked (README.md, opening). Three actors with sharply different
standings: the **LLM** is an untrusted proposal engine that may author
*declarative specifications only*; a library of **generators** — programs
of type `Spec → Code` — does all code emission; a small fixed **kernel**
adjudicates every artifact and is the only component trusted by fiat.

**The five hard constraints and where each lives** (README.md "The five
hard constraints"):

1. **The task-time path contains no LLM calls.** `run/` goes spec →
   planner → generator chain → code deterministically, executing under
   `common.task_time_guard()` (common.py:21), which sets `CGB_TASK_TIME=1`
   for the dynamic extent of the run (run/__init__.py:105). The single LLM
   client checks that flag and raises `TaskTimeLLMViolation` if any call
   is attempted while it is set (buildloop/llm.py:43). Enforcement is
   itself tested (tests/test_invariants.py:54). Same spec + same registry
   state ⇒ byte-identical output (tests/test_byte_identity.py).
2. **LLM output is only ever a spec.** buildloop/validate.py rejects
   anything outside the declarative vocabulary — generator specs as JSON
   with a closed key set, `.ksy` documents, a declarative subset of
   tree-sitter `grammar.js`, contract annotations — before a proposal
   reaches the kernel or the registry (buildloop/validate.py docstring,
   "hard constraint #2").
3. **Nothing is trusted without a kernel verdict.**
   `kernel.check(artifact, contract) → Certificate | ErrorTranscript`
   (kernel/__init__.py) is the sole adjudicator; `common.py` explicitly
   holds no policy. The kernel is the one component trusted by fiat, and
   its exact extent is enumerated line-by-line in TRUST.md.
4. **All emitted code executes OS-sandboxed.** sandbox/ builds a jail
   from Linux namespaces (`unshare --net --mount --pid`), tmpfs over
   `/home` `/root` `/tmp`, a scratch-only writable directory, uid 65534,
   and rlimits — enforced at the OS level both during kernel checking and
   at task time; no effect typing.
5. **Every artifact records provenance** — which generator emitted it,
   from which spec, under which certificate, at which tier
   (run/__init__.py, library/).

**"Verification begets verification," operationally.** The compiler-
bootstrap move: fiat trust is confined to the kernel (plus the OS-level
sandbox), and everything else earns trust through certificates bound to
content hashes (kernel/certs.py). Certified artifacts then become the
machinery that produces and checks the next layer: a generator enters the
registry at *emit-check* tier, where every one of its outputs is
individually verified at emission; `cgb promote` (buildloop/promote.py)
can later lift it to *universal* tier once the generator itself is proven
correct for all specs, after which its outputs inherit trust from the
generator's certificate through the recorded provenance chain. Trust
flows downhill from checks — never sideways from authorship.

**What the LLM is allowed to do:** author spec files in the fixed
declarative vocabulary, in the build loop only, through the single client
module buildloop/llm.py (docstring: "the ONLY module that may talk to an
LLM"), with token usage taken from API usage metadata into the
cumulative-cost metric. **What it is not allowed to do:** emit
general-purpose code (validate.py rejects it as `SpecViolation`), run at
task time (the guard raises), adjudicate anything (only kernel verdicts
admit), or spend its way past admission — a proposal that validates and
certifies still fails unless it strictly reduces total corpus description
length under the MDL gate (buildloop/admission.py).

## 1. Trust architecture

Scope: the kernel (`kernel/` — check(artifact, contract) → Certificate |
ErrorTranscript), the two-tier model (emit-check vs universal), the
dual-checker rule (no single verdict admits), the OS-level sandbox, the
provenance ledger, and the enumerated trusted computing base.

Sources: TRUST.md (line-by-line TCB), kernel/certs.py (CERTS_VERSION,
cert/transcript records), kernel/backends.py, sandbox/, library/.
Must answer: what exactly is trusted by fiat and why; how a certificate
binds to content hashes; how promotion to universal tier works; where
disagreement between checkers goes (first-class events, never discarded).

The kernel's entire public surface is one function:
`kernel.check(artifact, contract) → Certificate | ErrorTranscript`
(kernel/__init__.py:1-13). It derives obligations, dispatches to the
backend wrappers (kernel/backends.py — Hypothesis against the real
artifact in the sandbox, Dafny/Z3 on generated obligations, and the same
SMT-LIB obligation given independently to Z3 and CVC5), then applies the
**dual-checker rule** in `adjudicate()` — deliberately a pure function of
the collected channel list, so parallel orchestration can change
wall-clock but never a verdict (kernel/__init__.py:621-627, TRUST.md
1.2f). A certificate issues only when at least two channels pass and none
dissents (kernel/__init__.py:631); the kernel holds no state — caching
and event logging are injected — which is what makes it swap-ready
(TRUST.md 1.1).

**What is trusted by fiat, and why.** TRUST.md enumerates the fiat tier
line by line; everything in it is small, fixed, audited, and never
shipped. (1) The kernel adapter itself — the trust regress has to stop
somewhere, and it stops here, growing only by one honestly-labelled
contract per phase (TRUST.md:20-31). (2) The OS sandbox
(sandbox/__init__.py): `unshare --net --mount --pid --fork --kill-child`,
tmpfs over `/root` `/home` `/tmp`, a bind-mounted scratch dir as the only
writable path, uid 65534 with a cleared environment and CPU/memory/fsize
rlimits (the `_INNER` jail template, sandbox/__init__.py:41-53). TRUST.md
calls trusting these namespace primitives "the largest by-fiat
assumption" (TRUST.md:44). (3) A family of fixed reference *checker
inputs* — `generators/refcodec.py`, the jsonschema reference validators,
the Reading compiler, flloat, and their successors (TRUST.md 1.2a-1.2m)
— trusted only to *disagree* with the primary implementation, never to
ship code. (4) The vendored checker binaries — Dafny 4.11, Z3, CVC5,
Hypothesis, Kaitai 0.11, tree-sitter 0.26 — trusted for "*soundness as
checkers*. We do **not** trust the code they *emit*" (TRUST.md:431-433).
(5) Ambiently, the Python interpreter and host OS (TRUST.md 1.4).

**How a certificate binds to content hashes** (kernel/certs.py). The
subject is `sha256` over the checked artifact's bytes —
`artifact_hash()` hashes the sorted (name, bytes) pairs
(kernel/certs.py:177-183) — and the contract hash is `sha256` of the
content-addressed contract descriptor. The `cert_id` is itself a hash
over {kind, subject_hash, contract_hash, channels, tier, claims,
non_claims} (kernel/certs.py:104-117), so a certificate cannot be
detached from what was checked, what agreed, or what it declined to
claim: `non_claims` is a first-class field (the `monitored` cage uses it
to decline to praise its cargo), and `tier` is drawn from the frozen
`TIERS` vocabulary (kernel/certs.py:137-152). `CERTS_VERSION` — 12 today,
with every bump's reason recorded in place (kernel/certs.py:8-75) —
prefixes every cache key (kernel/__init__.py:582-587), so any change to
what a verdict contains makes older cache entries a clean miss, never a
stale false-green. The cache is "a memo of the kernel, not a second
source of trust" (TRUST.md:115-118).

**The two-tier model and promotion.** An *emit-check* generator is the
on-ramp: every output is individually checked at emission time before use
(TRUST.md 2.1). A *universal* generator has its contract verified for
**all** specs in its declared grammar, and its outputs need no emission
check (TRUST.md 2.2). Promotion (`buildloop/promote.py`) is itself
dual-checked: channel 1 is the Dafny proof over the generator's
implementation shape (`UNIVERSAL_FIXED_UINT`, dafny_gen.py:75-100);
channel 2 emits `SPEC_FUZZ_N = 8` randomly sampled specs through the
*real* pipeline and property-tests the real codecs in the sandbox
(buildloop/promote.py:36, 130-151). The decision is tier-routed: the
certificate is always stored as evidence, but `set_tier("universal")`
fires **iff** the certificate literally claims `tier == "universal"`
(`_should_set_universal`, buildloop/promote.py:39-48); any other outcome
— e.g. a translator's honest bounded `complete-to-size(N)` — is logged
as `promotion-refused-bounded` and retains emit-check duty
(buildloop/promote.py:81-99). On success the planner's preference flips
(planner/__init__.py:6-8) and per-emission checks stop.

**The provenance ledger.** `library/` is a SQLite registry in which
entries are never deleted: retirement keeps a generator for provenance
while excluding it from planning, with a `subsumed_by` pointer
(library/__init__.py:1-8, TRUST.md:502-504). It stores tiers, per-entry
emission records (`emission_checked`/`emission_failures`,
library/__init__.py:31-32), every certificate, the first-class event log,
the counterexample corpus, and the kernel verdict cache
(library/__init__.py:17-67). A task run's composed certificate binds spec
hash, artifact hash, generator chain, per-link tiers, and emission-cert
ids (run/__init__.py:176-185), so trust in a run reduces to trust in its
links' certificates (TRUST.md 2.3).

**Where disagreement goes.** `adjudicate()` distinguishes honestly: a
behavioral-witness or cross-impl-differential channel that observed a
concrete counterexample is authoritative — the artifact is broken, verdict
"fail" — while a split between proof channels on the *same* obligation
(Z3 vs CVC5), or testing-clean-but-proof-failed, is a "disagreement"
reserved for human eyes (kernel/__init__.py:641-661). A disagreement is
never discarded: it is emitted as a first-class
`dual-checker-disagreement` event with the full subject, contract, and
channels (kernel/__init__.py:663-666), lands in the registry's events
table, and yields **no certificate** (TRUST.md:644-646). This is not
hypothetical machinery: milestone M6 engineers a nonlinear-arithmetic
obligation that Z3 proves and CVC5 times out on, and shows the logged
split via `cgb.py events dual-checker-disagreement` (README.md, M6).

## 2. The seed domain and the generator library

Scope: text/binary codecs as the crisp-oracle seed domain; what was
outsourced (Dafny/Z3/CVC5, Kaitai, tree-sitter, Hypothesis) vs authored
(the wiring, the ledger, the measurement).

Sources: README.md components table, generators/, generators/codec_model.dfy.
Must answer: why codecs; the spec→code path for one codec end to end; the
round-trip + malformed-rejection oracle.

**Why codecs.** The seed domain is text/binary format codecs: record
layouts of int fields with endianness, magic bytes, fixed /
length-prefixed / null-terminated strings, literal and counted repeats,
and enums (README.md "Seed domain"). The domain was chosen because its
oracle is *crisp* — round-trip plus malformed-input rejection is a
mechanical yes/no — its specs are short and declarative, and layering
(field codec / framing) exercises composition. Two further properties
make it bootstrap-friendly. First, the spec language already exists:
`.ksy` is a documented, in-training-data format the LLM can author
without any invented DSL (README.md components table). Second, coverage
is decidable by construction: `generators/ksy_model.py` parses a spec
into an ordered field list and extracts its *feature atoms* from a
closed 18-atom vocabulary (ksy_model.py:36-41), and "a generator's spec
grammar is a set of atoms; it covers a spec iff the spec's atoms are a
subset of the grammar's atoms" (ksy_model.py:22-24). A spec outside the
modeled subset raises `UnsupportedSpec` and simply becomes a permanent,
structured coverage miss (ksy_model.py:8-10, 44-45) — the build loop's
food, never a crash.

**Outsourced vs authored.** The build philosophy is "outsource everything
that exists" (README.md, top): Dafny 4.11 (Z3-backed) proves the codec
contract model and the universal theorem; Z3 and CVC5 are the independent
same-obligation cross-check; Hypothesis property-tests the real emitted
artifact; Kaitai Struct 0.11 (`--read-write`) turns `.ksy` into a Python
encode/decode pair; tree-sitter 0.26 turns a grammar into a parser
(README.md components table). "The only formal artifact we authored is
`generators/codec_model.dfy`" (README.md) — the machine-checked model
proving `Dec(Enc(vals) + rest) == Some((vals, rest))` for every
well-formed field list, plus truncation rejection and the static-offset
universal theorem (codec_model.dfy:1-10). What the repo authors beyond
that is deterministic wiring, all fixed and LLM-free:
`generators/dafny_gen.py` (pure text generation of obligations — "Dafny
does all the judging", dafny_gen.py:15), `generators/harness_gen.py`
(the Hypothesis harness derived from the spec by fixed code — "the LLM
never authors test inputs", harness_gen.py:3-4), `generators/emitters.py`
(the adapters that run the vendored tools; their outputs are never
trusted, emitters.py:1-11), and `generators/refcodec.py` (the
independent reference interpreter, below).

**One codec, end to end.** Take `specs/backlog/a_uint_be_000.ksy` (the M1
spec, README.md). (1) `ksy_model.parse_ksy` produces a `SpecModel` —
ordered `Field` descriptors, the atom set, and the raw source
(ksy_model.py:62-69). (2) The planner matches the atoms against
registered spec grammars and picks a chain. (3) `emit_ksc_python_rw`
writes the `.ksy` to a temp dir and invokes the vendored Kaitai compiler
(`java … -t python -w`), yielding a read-write Python codec module
(emitters.py:45-62) — an untrusted artifact, only ever executed in the
sandbox. (4) Because the emitting link is emit-check tier, the kernel
runs the `codec-roundtrip` contract: two independent channels run
concurrently (kernel/__init__.py:970-992) — the Hypothesis harness
derived from the SpecModel, executed against the real codec inside the
jail, and the Dafny check of `per_spec_obligation`, which appends
`const SPEC := [FUint(1, BE), …]` plus the `SpecRoundTrip` and
`SpecTruncationRejected` lemmas to the pre-verified library and makes
Dafny re-verify the instantiation (dafny_gen.py:47-72). Both must agree;
the certificate binds the emitted bytes' hash, and the run closes with a
composed certificate and a provenance record naming the chain.

**The oracle, precisely.** The derived harness checks four properties
(harness_gen.py:10-16): P1 round-trip — `decode(encode(vals)) == vals`
and re-encode byte-identical (canonicality); P2 truncation — every strict
prefix of a valid encoding is rejected (the model proves this must hold);
P3 magic-byte corruption rejected; P4 length-prefix overrun rejected.
Hypothesis runs derandomized with a fixed seed so the task-time path
stays deterministic (harness_gen.py:4-6). The honest limit of this oracle
is structural: a codec can be internally round-trip-consistent yet wrong
about the wire format — a flipped-endian codec passes round-trip
(README.md "Independent second path"). That class needs a genuinely
independent implementation: `refcodec.py` is a from-scratch interpreter
sharing no code with Kaitai, so its bugs are uncorrelated
(refcodec.py:1-16), and the `codec-differential` contract diffs the two.
The demo captures both teeth — the flipped-endian codec that round-trip
passes and the differential catches with a witness input
(results/differential_demo.txt) — and building the chain-level version
"surfaced a real bug immediately": the differential caught a magic-field
mishandling in the harness itself (README.md, chain-differential).

## 3. The task-time path (no LLM, ever)

Scope: `run/` — spec → planner → generator chain → code, deterministically;
the CGB_TASK_TIME guard that makes any LLM call raise in flight.

Sources: run/__init__.py, buildloop/llm.py (the guard), common.py
(TASK_TIME_ENV), tests/test_invariants.py.
Must answer: byte-identity guarantee (same spec + registry state ⇒
identical output); how the guard is enforced and tested.

**The run_task flow.** `run.run_task` wraps the entire run in
`common.task_time_guard()` (run/__init__.py:104-107) and then executes
four deterministic stages. First, planning: `planner.plan` matches the
spec's atoms against registered grammars by bounded exhaustive
enumeration of all simple chains up to `MAX_CHAIN = 4` links
(planner/__init__.py:29) — deliberately not a visited-set BFS, because
the top sort key (most universal-tier links) is non-monotone under path
extension and a visited set would prune exactly the chains the promotion
flip is supposed to win (planner/__init__.py:23-28). Preference order is
fully deterministic: more universal links, then shorter chains, then
lexicographic generator-hash tie-break (planner/__init__.py:5-10). An
unplannable spec returns a structured `CoverageMiss`, logged as a
first-class event and handed back as data (run/__init__.py:112-115) —
task time never improvises. Second, chain execution: each link runs its
fixed emit adapter (`ksc-python-rw` or `abnf-to-ksy`,
run/__init__.py:42-54), with an additive, non-fatal per-emission
`translation-cert` at the abnf→ksy stage (run/__init__.py:127-136).
Third, the emission check: if any link is emit-check tier, the kernel
adjudicates `codec-roundtrip` on the terminal codec; a rejection stores
the failing input in the counterexample corpus, logs an
`emission-rejection` event, and fails the run with the transcript
(run/__init__.py:147-171). Fourth, the composed-run certificate binding
`spec_hash`, `artifact_hash`, the chain, per-link tiers, and every
emission-cert id — or the honest marker `"not-required: all links
universal tier"` — plus a provenance record naming each stage's
generator, tier, and depth (run/__init__.py:176-194).

**The guard, deeper than §0.** `TASK_TIME_ENV = "CGB_TASK_TIME"`
(common.py:17) is process-environment-scoped, so it crosses every module
boundary inside the dynamic extent without any plumbing. The guard is
*depth-safe*: it restores the **prior** value on exit rather than
unconditionally popping, because a nested `run_task`/certify call under
the old finally-pop behavior would clear the outer guard mid-session — a
real bug, fixed and documented in place (common.py:20-37). Enforcement is
a single chokepoint: `buildloop/llm.py` is "the ONLY module that may talk
to an LLM" (llm.py:1), and `call_llm` checks the flag and raises
`TaskTimeLLMViolation` before any subprocess is spawned (llm.py:43-45).
The guard is the second fence, not the first: `run/` never imports the
LLM client at all (run/__init__.py:9). Both fences are tested —
`tests/test_invariants.py:52-63` sets the flag and asserts the raise, and
`tests/test_invariants.py:87-102` separately asserts the sandbox blocks
the network and hides `/home`, closing the covert-exfiltration route.

**What byte-identity is tested over.** The guarantee is "same spec + same
registry state ⇒ byte-identical output" — the registry qualifier is
load-bearing, since a promotion legitimately flips the planned chain;
that is a state change, not nondeterminism. It is measured at three
granularities. (1) Whole-path: `tests/test_invariants.py:42-49` runs the
same spec twice through a seeded registry and asserts
`r1.files == r2.files` on the emitted bytes. (2) Per-emitter golden
hashes: `tests/test_byte_identity.py` pins sha256 of the emitted
dispatcher, reference service, BMC obligation, and validators for every
committed demo spec against `tests/golden/byte_identity.json` (under
PYTHONHASHSEED=0, since emitted `set` reprs are seed-dependent), plus the
conditional-emission no-op — a spec declaring empty `obligations: []`
emits code byte-identical to a plain spec, proving new machinery cannot
perturb old artifacts and thus cannot invalidate their content-addressed
certificates (house rule 8; tests/test_byte_identity.py:1-29, 104-123).
(3) Under parallelism: channels are reassembled in fixed order, so the
composed certificate is byte-identical serial vs parallel vs cached,
asserted in `bench/bench_latency.py` (TRUST.md 1.2f). Determinism is engineered
at each source: Hypothesis runs derandomized with a fixed seed
(harness_gen.py:4-6), the planner tie-breaks lexicographically, and the
kernel cache — keyed `v{CERTS_VERSION}:{subject}:{contract}`
(kernel/__init__.py:582-587) — is a memo that changes *when* the kernel
ran, never *what* it concluded. One honest caveat: the identity claim is
over the emitted artifact bytes; the composed certificate carries a
`created_at` timestamp, which the provenance hash explicitly excludes
(run/__init__.py:190-192).

## 4. The build loop and its currency

Scope: the combined loop (`buildloop/loop.py::run_iteration`) — one move
per call over typed misses (coverage / request / recurrence / toll / math),
scored in the ONE ledger-DL currency; refusal memory; convergence as the
terminal state; house rule 13 (no wall-clock in any decision).

Sources: PLAN_COMBINED_LOOP.md, buildloop/{loop,dl,mdl}.py, cgb.py
(ledger sync / build), METRICS.md.
Must answer: what ledger_dl prices and what it deliberately does not
(tokens/time); why there is no budget primitive in the core loop (and
where the import operation added one, §7).

The combined loop is one function: `run_iteration(registry, backlog)`
(buildloop/loop.py:732). Each call reads a frozen ledger snapshot, scores
every open miss of five types — coverage / request / recurrence / toll /
math, in that frozen tie-break order (loop.py:28–29) — picks the single
argmax move, dispatches it, and logs the whole ranked decision
(loop.py:744–775). One move per call; each miss type is a `to_dict()`-able
record logged verbatim (loop.py:217–256, 466–493). Scores are declared
*optimistic upper bounds* on the ledger_dl a move could remove, with named
deductions (loop.py:259–263), and realized ΔDL is logged against expected
after every move (loop.py:770), so systematic scoring bias is visible in
the event stream rather than absorbed.

**The one currency.** `ledger_dl` (buildloop/dl.py) prices exactly three
things: (1) every demand row by kind — a covered spec-file costs its
tier-aware chain cost plus size/256, an uncovered one the finite
`UNCOVERED_PENALTY = 50` (dl.py:288–296); a served nl-request or
math-source costs `READING_CHAIN_COST + dl_reading` (dl.py:297–313); a
caged incumbent costs its capped toll stock, and a converted one is priced
by the *single* conversion formula shared verbatim with the admission gate
so ledger and gate cannot drift (dl.py:262–273, 435–456); an unknown kind
fails loud rather than pricing free (dl.py:324–327); (2) every live
generator's FULL authored artifact — including the up-to-20 KB LLM-authored
`grammar_js` payload the legacy series popped before pricing (dl.py:65–83);
(3) every live macro definition (dl.py:330–341). Chain links are priced by
tier — a universal link costs 0.0, any other 1.0 — so the promotion move
strictly lowers the ledger instead of being self-defeating (dl.py:44–61).
The policy constants are declared by-fiat inputs to admission, named in
TRUST.md (dl.py:29–42; METRICS.md:102–105). The gate itself is one
predicate: admit iff ledger_dl strictly drops, with a single bounded
exception — *expansion*, admissible only for newly covered EXOGENOUS demand
that no already-admissible alternative covers, logged as its own outcome
and never counted as a DL win; system-origin rewrites can never trigger it
(dl.py:387–432; PLAN_COMBINED_LOOP.md house rule 12, :179–193).

**Refusal memory** is mark-don't-omit: a refused conversion records an
evidence hash (the lift bound n + tool surface, loop.py:387–394), and a
toll candidate matching a prior `conversion-suppressed` event is marked
`suppressed_by` — still generated, still priced, never picked — because the
standing toll is monotone and would otherwise re-run the doomed pipeline
forever, the verified livelock (loop.py:414–450; PLAN_COMBINED_LOOP.md
:626–631). Math moves get the same treatment after `MATH_MAX_ATTEMPTS = 2`
refusals (loop.py:31–36, 448–450), so a ledger-priced miss stays visible in
the log while the loop stops paying to re-fail it.

**Convergence is the terminal state, not a disappointment.** The committed
demand corpus is finite and static (PLAN_COMBINED_LOOP.md fact 15,
:122–125), so `run_iteration` returns `{"status": "converged"}` when no
move scores positive and none remains unsuppressed (loop.py:453–454,
753–754) — "convergence on finite demand is the honest claim, not an
ever-falling curve" (PLAN_COMBINED_LOOP.md §7.1, :897–901). House rule 13
makes every decision replayable: each iteration reads one frozen snapshot
whose hash folds in everything that prices (dl.py:161–190); two runs over
the same snapshot produce byte-identical ranked-move logs (loop.py:417–419;
PLAN_COMBINED_LOOP.md :194–198), and no wall-clock value ever enters DL, a
score, or a tie-break — `wall_ms` is reporting-only, and even the toll
horizon is denominated in sync epochs (dl.py:15–17, 34–35).

**What ledger_dl deliberately does not price: tokens and time.** LLM spend
is metered — every call's usage lands in `llm_input_tokens` /
`llm_output_tokens` counters (loop.py:508–510, 718–720) and the metrics
cost axis reports kilotokens and verifier seconds (METRICS.md:6–7), never
summed into one number (E6, METRICS.md:150–152) — but none of it enters the
currency or any admission decision. Description length is the objective;
spend is telemetry. The one measured attempt to trade tokens for coverage
inside the loop — a K-wide speculative authoring mode for the math move —
bought identical coverage (4/40) at 2.9× the spend and was removed under
the house standard that a capability carries its measured tooth or it goes
(loop.py:38–46). There is consequently no budget primitive in the core
loop: on a finite committed corpus a budget would be a second stopping rule
competing with the honest one (convergence), and a spend threshold in an
admission decision would be exactly the tuned-constant anti-pattern the
currency discipline exists to refuse. Where demand stopped being finite —
the Mathlib import operation — a budget layer WAS added, outside the loop
core, as a grant plus budgeted driver; see §7.

One bookkeeping fact to hold onto when reading old numbers: there are two
DL series. The legacy codec-only `total_dl` (buildloop/mdl.py, including
its hand-kept planner mirror `chain_length_for`, mdl.py:25–44) is frozen —
milestones m5/m7/m8 read it and are labeled as such — and `ledger_dl` is
its deliberate successor with a new name and its own table, a logged
semantics change, never a silent redefinition (dl.py:9–17;
METRICS.md:77–105). The ledger is populated by `cgb.py ledger sync`
(idempotent ingestion of committed specs as exogenous rows,
`demand_id = sha256(kind + ":" + relpath)`, with dream math paraphrases
tagged system-origin and a payload-hash guard so a committed system rewrite
cannot launder itself into exogenous demand — cgb.py:343–364, 539–614), and
one loop iteration runs as `cgb.py build` (cgb.py:111–124).

## 5. The math/formalization lane

Scope: the F-G fragment (Nat/Int arithmetic; readings as speech-act-tagged
logical forms), the 6-stage fidelity pipeline
(`run/formalize.py::certify_statement`), statement-cert vs proof-cert vs
exists-anchor-cert, the verdict lattice, the L1–L5 disciplines, bounded-
shadow ∃, and the anchor runner.

Sources: FORMALIZATION.md, KA_INTERFACES.md, generators/math_reading.py
(the one grammar; roles pred/term/connective), generators/math_{compile,
smt,eval,witness}.py, kernel/{rung,verdict_lattice}.py, run/anchor.py,
wp_auth_readings.py.
Must answer: what each of the six stages catches, with the honest-deferral
branch (Lean absent); what a certificate subject binds; what the fragment
deliberately cannot say (fragment-miss as first-class data).

The math lane exists because proof checking alone verifies the wrong
thing: a kernel cert relates proof to statement, and nothing in a bare
proof pipeline checks statement against the *text it claims to
formalize* (run/formalize.py:1–8). This lane is that missing layer —
statement fidelity, checked by Lean-free decidable arithmetic.

**The F-G fragment: one grammar, four deterministic descendants.** A
MathReading is a speech-act-tagged semantic analysis of one sentence:
typed objects over the deliberately tiny carrier whitelist `("Nat",
"Int")` (generators/math_reading.py:41), plus statements carrying one of
three forces (math_reading.py:37) — a **demand** (asserted content,
quote-grounded), a **presupposition** (the implicit side conditions
autoformalization silently drops — "the killer feature",
math_reading.py:11–16), or a **choice** (formalization freedom, which
MUST quote nothing). The operator lexicon `MATH_OPERATORS`
(math_reading.py:55–68) is frozen, carrier-indexed (`coprime` is
Nat-only in v1), and each word carries one of three roles — `term`
(value), `pred` (boolean atom), `connective` (boolean over booleans) —
kept distinct so a mined operator slot can never range across a category
boundary (math_reading.py:91–93). math_reading.py is the single source
of truth (math_reading.py:25–28); four deterministic siblings descend
from it and can never drift: the compiler (math_compile.py, reading →
byte-stable `theorem … := sorry`), the SMT mirror (math_smt.py), the
direct evaluator (math_eval.py), and the witness emitter
(math_witness.py:4–11). Even the rung meta-interpreter hardcodes the
same op vocabulary, pinned equal to the grammar by test
(kernel/rung.py:26–31).

**The six-stage pipeline** (`run/formalize.py::certify_statement`,
run/formalize.py:471) runs one reading through six ordered gates; on
refusal the result names the failing stage. What each catches:

1. **math-reading-gate** — parse plus groundedness: every
   demand/presupposition quote must occur verbatim in the source;
   choices quote nothing. Catches *fabrication*
   (run/formalize.py:484–503).
2. **nonvacuity (F2.1)** — the hypothesis set must be satisfiable, else
   the theorem certifies *vacuously*. Dual-solver (Z3 ∧ CVC5) with the
   T4 direction split: unsat refuses only when the bounded-enumeration
   channel corroborates; uncorroborated dual-unsat is a first-class
   `mirror-divergence` event, never a silent refusal
   (run/formalize.py:244–322). Catches *contradictory hypotheses*.
3. **compile** — deterministic emission with per-element provenance;
   the compiler's OWN output is re-run through the escape gate, defense
   in depth (run/formalize.py:550–562).
   Then **statement-cert (F0.2)** — the deferred kernel layer. The
   honest-deferral branch: with Lean genuinely absent the cert records
   `statement_cert=None`, layer detail "deferred: lean toolchain
   absent" — NOT a pipeline failure (run/formalize.py:635–644). With
   Lean *present* and no certificate, the pipeline REFUSES — recording
   "toolchain absent" there is the named false-deferral bug
   (run/formalize.py:646–665).
4. **instances (F2.2)** — the k smallest hypothesis-satisfying
   instances replayed against the compiled statement; a False instance
   refuses with the witness. Catches *wrong operator binding* and
   *silent carrier narrowing*; boundary probes are recorded, never
   refused (run/formalize.py:326–347, 667–692).
5. **examiner (F2.4a)** — optional source-blind expectations replayed;
   divergence is a first-class `formalization-divergence` event and
   `converged=False` — evidence, never a refusal (L3;
   run/formalize.py:417–467). Catches the *omitted-presupposition* gap
   every earlier gate passes. Blindness is enforced as a call
   signature: `validate_expectations` has no reading/lean parameter, so
   the leak is unrepresentable (buildloop/validate_expectations.py:
   20–27, 84–91).
6. **proof** — Lean-gated F0.3, skipped when Lean is absent
   (run/formalize.py:722–723).

**Three certificate kinds, and what a subject binds.** A
*statement-cert*'s subject is the `statement_hash` alone — sha256 over
the compiled `lean_text` bytes, no emitted files
(run/formalize.py:88–90; KA_INTERFACES.md:15); the contract binds
lean_text, fidelity channels, Mathlib commit, toolchain, import set,
and boundary behavior (run/formalize.py:619–628), per the L2 cage-hash
discipline (FORMALIZATION.md:75–84). A *proof-cert* (F0.3) adds the
proof artifact at `kernel-checked` tier: run-2 trusted audit, no
`sorryAx`, axioms ⊆ the standard three (FORMALIZATION.md:211–223). An
*exists-anchor-cert* (v12, kernel/certs.py:392–396) mints ONLY at
lattice point `kernel-proved` (kernel/certs.py:373). The disciplines
L1–L5 (FORMALIZATION.md:59–122) govern all three: the LLM never authors
Lean (L1); the checking apparatus is part of cache identity (L2);
fidelity gates refuse, tripwires log (L3); Lean-kernel vs lean4checker
is honestly labeled `kernel-family`, not independent (L4); no
verdict-bearing fact originates in a process where untrusted bytes
executed — the two-run rule (L5). The lexical escape gate
(buildloop/validate_lean.py:1–11) — NFKC folding, homoglyph/guillemet
refusal, blocklisted metaprogramming tokens — is explicitly
defense-in-depth and "NEVER the trust boundary" (⚠T7): Lean elaboration
is metaprogramming-complete, so the boundary is the sandbox plus L5.

**Bounded-shadow ∃ and the verdict lattice.** A supported ∀-outer/
∃-inner reading is checked by exhaustive bounded model check — the full
inner product over every admitted outer point, never k-smallest, under
the 2,000,000-assignment ceiling (generators/math_eval.py:471, 483,
618); the SMT mirror's absence for ∃ is declared, not pretended
(run/formalize.py:594–601). The shadow refutes only the *bounded*
claim, so `kernel/verdict_lattice.py` joins shadow × kernel into five
points (verdict_lattice.py:26–27) via a frozen 12-cell total mapping
(verdict_lattice.py:99–112): shadow-refuted × kernel-proved is NOT
divergent — it is the permanent differential (verdict_lattice.py:
15–19, 104); `divergent` is reached only by the two concrete triggers
T-a/T-b or a sticky unresolved artifact that only a human resolution
releases (verdict_lattice.py:149–178); `unavailable` is never
`kernel-failed` (verdict_lattice.py:34–36), and `kernel-proved` is the
one terminal point with no exit but the tripwire (verdict_lattice.py:
246–247). The anchor runner (run/anchor.py:1–43) wires this per ∃
reading — fresh shadow recompute, witness-template emission, guarded
kernel leg, mint-guard, lattice — into results/anchor_report.json. The
committed measurement: 4 ∃ readings, 3 `shadow-certified`, 1
`shadow-edge-refused`, 0 `kernel-proved` (Lean-absent lane). The
refusal is source 43 (`∀ n:Int, ∃ m, n < m`): at n = B = 8 no in-box
witness exists, so a *true* statement is honestly refused at the bound
edge — the safe direction, never a false green
(wp_auth_readings.py:21–24).

**What the fragment deliberately cannot say is data, not shame.** A
source that does not transcribe raises `FragmentMiss`, logged as a
first-class `fragment-miss` event carrying the analyst's
`missing_kind_guess` (run/formalize.py:489–499); `cgb.py` aggregates
those events into the fragment demand report that prices frontier
growth (cgb.py:644–656). The committed corpus records honest declines:
51_goldbach shares 38's `prime` miss and is authored as `None`
(wp_auth_readings.py:27–28). Growth of the fragment itself is
permanently human-gated (F4, FORMALIZATION.md:130–134), and no
certificate ever claims a statement *matters*
(FORMALIZATION.md:127–129).

## 6. The compression program (and its honest verdicts)

Scope: the macro/operator towers, MDL admission gates (strict descent +
≥2 exogenous witnesses), waves 1–3, and the measured outcomes — including
the negative ones: depth-1-only history, level-2 refused at the witness
bar, the C2 currency showing vocabulary costing +365.8 bits, KT-1 beating
corpus_dl by 624, the metered run where governance lost. Then the 2026-07-17
workstream that made compounding *possible*: fixpoint expansion,
recode-then-mine, stacked pricing (dl_before(n+1)=dl_after(n)), term-role
admission, and the registered H3 limitation (organic mining is still
level-1).

Sources: COMPRESSION.md (§10 literature, §11 sweep + execution records,
§12 wave-3, §13 DRAFT + results/sweeps/s13_fable_sweep.md), buildloop/
{mdl_macros,recurrence}.py, generators/operator_growth.py,
generators/reading.py (fixpoint expander), tests/test_tower_expansion.py,
results/{tower_census,c2_report,proposal_admissions,metered_evidence}.
Must answer: the difference between the operator tower and the macro
tower; what "the machinery is in; the corpus said no" means precisely;
what the compounding instrument now measures and what it cannot yet
(H3); the §13 sweep verdicts and their binding status (pending user).

The compression program measures one number, `corpus_dl` — the description
length of the exogenous corpus under the live vocabulary, in the counting
currency of `mdl_macros` (COMPRESSION.md:3–12) — under constraints restated
once and never weakened: ≥2 exogenous witnesses at every rung (dreams
propose, never witness), admission = strict DL decrease in the named
currency (never a tuned λ), new metrics reported beside the old before
anything gates on them (COMPRESSION.md:14–20). Two towers grow under those
gates, and they are different things. The **macro tower** is abbreviation:
`buildloop/recurrence.py` mines contiguous statement windows (length 2–4,
recurrence.py:66) from certified Readings, anti-unifies occurrences into a
least-general-generalization body (recurrence.py:16–21), prices candidates
against the LIVE table (never table-blind), and admits through
`mdl_macros.macro_admission_decision`: strict corpus_dl descent AND ≥2
witnessing readings (mdl_macros.py:26–29, 192–223), with GC retiring
stranded macros as first-class events (recurrence.py:23–26). The **operator
tower** is vocabulary: `generators/operator_growth.py` admits new operator
*words* as definitional extensions — pure data rows over the frozen F-G
fragment, expanded to kernel form before any engine sees them — through an
LLM-free battery (well-formedness, dual-solver differential instances,
compile round-trip, nonvacuity) plus the same economics
(saving > model_bits AND ≥2 exogenous witnesses), with `save_admitted` as
the sole admitter over an append-only, tamper-checked registry
(operator_growth.py:1–49, 173–215). A macro compresses the corpus; an
operator extends what the corpus can say — and each is certificate-gated.

**The measured outcomes are mostly negatives, and they are the point.**
The record across waves 1–3 (COMPRESSION.md §11.10–§11.13, §12): governance
is real in the counting and prequential currencies (governed 2139 < 2371;
origin-blind prequential 2336 < 2459 in wave 1, holding through corpus
growth at 2920 ≤ 3208 and 3117 < 3296 — COMPRESSION.md:15–16, 1002–1005,
1116–1118); refined mining banked a real descent (Δ−534 on the grown
corpus, §11.13:1119–1128); four operators were admitted at Δ−116/−19/−7/−2
while pricing alone refused the literal-family flood
(results/proposal_admissions.md; §11.13:1136–1146). Against that: **the
tower has only ever been depth-1** — all four admitted operators price
against the same baseline dl_before 1285.0, four parallel flat admissions,
not a descending stack (results/proposal_admissions.md;
results/import_findings.md Finding 2 — PR #15, merged 2026-07-19). **Level-2
was measured and refused at the witness bar**: the census-of-record shows a
maximum of 2 realizable macro-macro witnesses against the pre-registered
bar of ≥7, zero pairs at the bar (results/tower_census.md:17–24), and the
anti-unified congruence slot prices at +7.0, admit False — after its
admission-time −179 was cannibalized by later admissions
(tower_census.md:57–59; COMPRESSION.md:1123–1128). The canonicalization
rung was refused on the real corpus (64/66 rules fire on <2 readings,
counterfactual profit exactly 0.0 against 2748 model bits) while the
engineered-rung tooth proves the gate CAN admit (net −61 planted) —
COMPRESSION.md:1055–1072. **The honest currency says the vocabulary costs
bits**: under the two-part KT code, governed C2 = 2284.451 vs empty-table
1918.678 — +365.773 bits, mapping-independent (results/c2_report.md:48) —
and adaptive KT order-1 codes the raw stream at 1514.5, beating corpus_dl
2139 by 624 (COMPRESSION.md:590–592): the residual headroom is sequential,
statement-internal structure the window miner cannot see. **The one
metered run lost**: governed 3 certified at 484 ktok/cert vs ungoverned 8
at 55, DL 854 > 689 over unequal subsets, both relational verdicts recorded
FAILED and demoted (results/metered_readout.json; COMPRESSION.md
§12.5:1334–1359) — with the adversarial pass equally on record that the
cost gap is 76% one runaway session and the run licenses no transfer claim.
This is what "the machinery is in; the corpus said no" (§11.11's title)
means precisely: the admission machinery works and is tooth-proven able to
admit, and the instruments — witness bar, counterfactual pricing, C2, KT —
independently refuse to find the compounding structure in THIS corpus.
Wave 3's registered predicates agreed: T1R and T2E were registered blind
and evaluated once — neither fired (results/reentry_evaluations.json;
COMPRESSION.md:1276–1289, 1301–1320).

**The 2026-07-17 workstream made compounding possible without claiming it
happened** (all on PR #15, merged 2026-07-19). Finding 3 established both
walls as buildable-through; Finding 4 records the landing
(results/import_findings.md): `_expand_macros` now runs to fixpoint (depth
bound 16, cycle ⇒ BadReading; DAG termination via the no-self/forward-
reference closure rule — generators/reading.py on the branch), and pricing
recodes-then-mines, so a level-2 body that priced uses=0 forever now finds
its uses (the test fixture: uses=4, 81.0 → 55.0, Δ−26.0, admit True) and
admissions STACK — the second admission's dl_before is byte-equal to the
first's dl_after (tests/test_tower_expansion.py:247–258). Term-role
admission (role:"term", value battery; `sq(a) := a*a` admits, `plus2`
refuses as a rename) opens the vocabulary the pred-only gate rejected as
"unknown atom/connective" (results/proposal_admissions.md refusal table),
and inline mining runs in the import driver's governed arm. The registered
H3 limitation bounds the claim: candidate GENERATION still carries the
concreteness filter (`MIN_CONCRETE_FRACTION = 0.6`, recurrence.py:78–83),
so the miner proposes level-1 bodies only — hand-built towers now PRICE
correctly, but level-2 vocabulary will not EMERGE organically until H3 is
revisited. What the compounding instrument now measures: DL descent under
level-1 mining with stacked pricing at growing corpus scale — first data
point, one organic admission at corpus_dl 2074 → 2011 (Δ−63) during C6
(Finding 5, §7). What it cannot yet measure: organic tower emergence.

The §13 draft went through its fable critique sweep on 2026-07-17
(results/sweeps/s13_fable_sweep.md — PR #15, merged 2026-07-19): no package
killed; every verdict is proceed-re-specified or a refusal upheld
(WP-KA-PRICE stands as a sound refusal), the §13.2 transfer record
survived recomputation to the last digit, the kill-list stands with three
kills added, and the sweep registered a new failure axis with a live
exhibit — BUG-S1, record/verdict divergence: the T2 evaluation cites a
byte-pinned census that does not contain its gapped-instrument inputs (the
verdict reproduced; the record discipline failed). Binding status: §13 is
still headed DRAFT — "pending its own critique sweep before binding"
(COMPRESSION.md:1418) — and the sweep's verdicts await user review before
the fold-in; until then §13 binds nothing (§11 of this document tracks the
open item).

## 7. The Lean import operation (the newest layer)

Scope: converting token spend into importing+translating Mathlib at the
pin — the four-layer operation (grant → sessions → budgeted driver →
queue/ledger), the direction flip (formal source, RT differential as the
oracle no NL corpus has), the commissioning ladder C1–C7, inline mining
co-evolving with import, and the findings record (1–6): the name-rule
wall, the macro-tower audit, D1/D2 tractability, the workstream landing,
C6's 82 authored + first organic admission (corpus_dl 2074→2011), RT
round 2's 29/35 kernel-confirmed with zero confirmed mistranslations.

Sources: PLAN_LEAN_IMPORT.md (the plan + §8 ladder + §8.1/8.2 executed
gates), results/import_findings.md (Findings 1–6 — read the corrections,
they are part of the story), buildloop/import_driver.py, buildloop/census.py,
tools/{EnumerateMathlib.lean,enumerate_mathlib.py,c6_pilot.py,dry_wave.py},
run/import_rt.py, specs/mathsources/mathlib/ (queue.jsonl.gz, census.json,
readings/, import_macros.json), results/{import_ledger.jsonl,c6_pilot/,
import_rt_report.json}.
Must answer: the unit of work and its R1 identity anchor; §2.5's
anti-lock-in contract (eliminability, certified migrators, T-LI-ENC);
what "authored" vs "imported" means (dual-channel: RT ∧ statement-cert);
current fidelity rate and the open probe fixes; what C7 requires before
unattended churn.

*Everything this section describes landed on main via PR #15 (merged
2026-07-19, branch `claude/token-spend-lean-import-qk633q`); file
citations below are to that branch.*

**The operation.** Convert token spend into importing and translating
Mathlib at the pin (`.lean-pins`: mathlib4 `9837ca9d…`, Lean v4.15.0).
"Import the entire library" is deliberately a **frontier operation, not
a finish line** (PLAN_LEAN_IMPORT.md §0): the pin holds 225,916
declarations, 537 of them in-fragment under the census's current
component-wise classifier (specs/mathsources/mathlib/census.json; the
§8.1 review was recorded against the first classifier's 921), and at
the measured ungoverned rate (~55 ktok/statement) the naive reading of
10^5 declarations is ~5.5×10^9 tokens — no such grant exists. The only
permitted headline is frontier progress per kilotoken, never "percent
of Mathlib done" (plan §7, pre-registered refusals).

Spend converts to work through four independently auditable layers
(plan §3): a USER-GATED **grant** (specs/ops/spend_grant.json — mode
`weekly-quota-exhaustion`, RULED 2026-07-17: no fixed total, run until
the subscription quota signals exhaustion, per-wave cap kept as
checkpoint hygiene) spins up **sessions** (WP-LI3: the verified
headless-CLI substrate for Phase A; Phase B defaults to the Lean CI
lane), each running the budgeted **driver** (`cgb import
--budget-ktokens B --confirm-spend`, buildloop/import_driver.py) which
consumes the **queue** (specs/mathsources/mathlib/queue.jsonl.gz, one
row per declaration, status ∈ {pending, authored, imported, refused,
fragment-miss, divergent}, import_driver.py:176-177) and appends the
append-only **ledger** (results/import_ledger.jsonl). Tokens are
counted only from returned usage metadata; breakers P-LI1-REFUSAL /
P-LI1-COST halt waves as recorded verdicts (import_driver.py:405-445);
a CLI quota error is a graceful halt, never a crash
(import_driver.py:183-197).

**The unit of work and its identity.** One Mathlib declaration. Row
identity is the R1 anchor `(decl_name, statement_hash at the pin)`
(plan §2.5 R1) — representation-invariant because Mathlib itself is
ground truth — computed by the enumeration pair
(tools/EnumerateMathlib.lean, a trusted read-only tool that never
touches the certification surface; tools/enumerate_mathlib.py, the
canonical side that attaches the hash) and stamped into every ledger
item row (import_driver.py:923). Readings are derived views — caches
of translation work — never identity.

**The direction flip.** The NL corpus argues fidelity by gates because
an English sentence has no formal ground truth. Import runs the other
way: the source object is already formal, so per declaration `d` the
oracle is the round-trip differential RT(d) — the compiled reading must
be provably equivalent to `d`'s own statement, via the defeq fast path
(`example : C := @d`) then a frozen six-rung iff ladder
(run/import_rt.py:101-108). Both failing is a refusal with the full
probe transcript, and a fidelity-pass + RT-fail row is logged as a
first-class *measured mistranslation* — the most valuable failure class
in the operation (run/import_rt.py:334-353). The English gloss is
provenance for the prompt, never a cert subject (plan §2, §7).

**"Authored" vs "imported" — the dual channel.** Phase A (token-heavy,
Lean-free) authors readings and runs the fidelity gates with the kernel
statement-cert honestly deferred; it can at most mark a row `authored`.
Phase B (token-free, Lean-lane) runs statement-cert and RT(d). A row is
`imported` only when both channels agree (plan §3), and the RT batch
tool deliberately refuses to flip `authored → imported` on its own
(run/import_rt.py:430-432). The committed queue today: 35 authored,
zero imported.

**Anti-lock-in (plan §2.5).** The risk at scale is not a wrong kernel
but a kernel expensive to be wrong about. Four mechanized rules: **R1**
anchors — after any encoding change, re-validating a migrated row is
RT(d) again, Lean compute, zero tokens; **R2** provenance is the asset
— the full decl → gloss → reading → decisions chain persists per row
(persist_reading, import_driver.py:546-566); **R3** the kernel basis is
the normal form — every layer above it is eliminable by construction,
and the census derivation refuses a registry that would silently widen
the fragment (buildloop/census.py, `derive_resident_set`); **R4**
migration is certified translation — an encoding bump ships a
universal-tier migrator or an explicit USER-GATED write-off, tooth
T-LI-ENC. Honestly: `READING_ENCODING_VERSION = 1` is stamped on every
row and artifact (import_driver.py:99), but the CI tooth refusing an
unaccompanied bump is still pending — §8.1's recorded open item.

**The commissioning ladder (plan §8).** The machine proves itself
before it churns; each gate emits an artifact. C1 logic (LLM-free
suites green) → C2 enumeration (queue + census built twice,
byte-identical, P-LI0-CENSUS) → C3 kernel-readiness review (EXECUTED,
§8.1: the pilot runs on the existing fragment with **zero primitive
additions** — pricing kernel growth on zero import evidence is the
speculation §2.5 exists to prevent; the post-pilot addition queue is
census-priced by single-blocker unlocks: Real 407, Coe 234, Iff 187,
census.json) → C4 dry wave (real queue, deterministic fake author, zero
tokens; results/dry_wave_ledger.jsonl) → C5 micro wave (first real
spend: 3 items, 116.1 ktok, zero certified,
results/import_ledger.jsonl — whose readout found ~26 of ~29 ktok/call
was CLI session overhead and cut a probe call from 25,858 to 164 input
tokens via the slim-session flags, import_driver.py:228-233) → C6 A/B
pilot (EXECUTED, below) → C7 unattended churn. **C7 requires** the
C1–C6 artifacts plus a cadence-and-scheduling decision made WITH the
user on the C6 readout, never before it; until then every wave is
started by a human or in a live supervised session (plan §8).

**Inline mining co-evolves with import (WP-LI6, RULED).** Compression
is exercised during import, never bolted on after. On the governed arm
the driver runs the bench's exact mine → price → admit discipline —
pricing never forked — over the accumulated authored readings, at wave
end and every 8 authored rows (MINE_EVERY_K_AUTHORED,
import_driver.py:133), persisting admissions append-only
(specs/mathsources/mathlib/import_macros.json) and threading the live
table into subsequent prompts. The enabling fixes landed per Finding 4:
fixpoint macro expansion (D2, generators/reading.py:227) and term-role
admission (D1), with stacked pricing pinned by test
(dl_before(n+1) = dl_after(n)).

**The findings record (results/import_findings.md — its corrections are
part of the story).** (1) C6 v1 hit a wall: 29 attempts, 0 authored.
The first committed diagnosis — "structural NL-vs-formal groundedness
mismatch, trust-critical fix required" — was wrong in kind and is kept,
superseded, in the file: all 22 refusals were the theorem-name rule
(generators/math_reading.py:424-425); the fix is deterministic
driver-side name normalization, no trusted-gate change
(import_driver.py:465-500). Cost of the wrong record: one killed pilot;
cost of checking: one 3-ktok replay. (2) The macro-tower audit: the
tower had **never compounded** — depth-1 everywhere, level-2 measured
at 0-past-bar, the honest C2 currency pricing vocabulary at +365.8
bits, KT-1 beating corpus_dl by 624, the one metered run lost. (3)
D1/D2 both tractable — the walls are buildable-through; Finding 2's
outcome evidence stands regardless. (4) The workstream landed, with the
registered H3 limitation: mining still *generates* level-1 candidates
only, so the instrument measures level-1 descent at scale, not organic
tower emergence. (5) C6 v3 EXECUTED: **82 declarations authored**
across four waves (~352 ktok), governed 4.12 vs ungoverned 4.56
ktok/authored at n=2 — the opposite sign of the old 484-vs-55 metered
ratio — and the first organic admission on a real Mathlib corpus:
corpus_dl **2074 → 2011** (Δ−63), one two-slot Nat macro witnessed by 7
Even/Odd lemmas (results/c6_pilot/c6_report.json; import_macros.json).
(6) RT round 2: of the 35 rescued authored rows, **29
kernel-confirmed** (28 defeq + 1 proved by `Iff.rfl` — 83% on
everything testable) with **zero confirmed mistranslations**
(results/import_rt_report.json). The 4 fails are transcript-verified
instrument limits — the two open probe fixes carried to §11 — and the 2
out-of-surface rows await surface widening; neither class is a semantic
verdict against a reading.

## 8. Operations: CI lanes, pins, and spend governance

Scope: the fast Lean-free gate; the opt-in Lean lanes ([lean-ci],
[lean-fresh], [lean-smoke], [lean-import], [lean-rt]) and their cache
keyed on .lean-pins; the weekly recert cron; the spend grant
(weekly-quota-exhaustion mode), the append-only ledgers, breakers
P-LI1-*, and the interlock discipline (consent AND grant, both).

Sources: .github/workflows/ci.yml, .lean-pins, setup.sh, ci/Dockerfile,
specs/ops/spend_grant.json, run_regression.py.
Must answer: which lane produces which committed artifact and how
commit-backs work ([skip ci], rebase-before-push); what a marker commit
does; what the container CAN'T do (Lean toolchain fetch blocked by
network policy) and how the operation routes around it.

One workflow (`.github/workflows/ci.yml`), one principle: **the gate you
pay on every push is Lean-free; everything Lean is opt-in and cached.**

**The fast gate.** Every push and PR runs the `fast` job:
`run_regression.py --fast --split {pytest,demos}` — the full pytest
suite, the guarded scripts, and every `REQUIRES_LLM=False` demo, each in
its own subprocess with a fresh temp registry (run_regression.py:4-14) —
sharded over two parallel runners, stale runs cancelled per shard. It
executes inside the prebaked toolchain image
`ghcr.io/jamesdchen/cgb-toolchain:latest` (ci/Dockerfile): Dafny, the
Kaitai jars, tree-sitter, and the pinned flloat closure are baked in so
the gate does not pay ~6 min of per-push installs; `--privileged`
because the OS sandbox needs `unshare`/`setpriv`; the devcontainer
points at the same image, so local dev == CI. Lean is deliberately NOT
baked (ci/Dockerfile:8-9): ~5 GB fits the Actions cache better than
image layers. The fast gate produces no committed artifact — it only
gates.

**The pin.** `.lean-pins` single-sources the toolchain:
`MATHLIB_COMMIT=9837ca9d…` is the primary pin; `LEAN_TOOLCHAIN=
leanprover/lean4:v4.15.0` is re-derived from `lean-toolchain` at that
commit and asserted equal at setup — drift refuses hard rather than
trigger a silent hours-long source build (setup.sh:79-88). Every Lean
lane keys its elan+Mathlib cache on `hashFiles('.lean-pins')` and saves
it even on failure, so edits to this one file (and only it) re-key the
~5 GB cache; a pin bump carries `[lean-ci]` and `[lean-fresh]` to re-run
shakeout and recertification (.lean-pins header).

**The Lean lanes, and what each produces:**
- `lean` (120 min): `setup.sh --with-lean --lean-only --skip-fresh`
  (Mathlib's PREBUILT oleans — a fetch, not a build), then the
  Lean-gated tests + `demo_formalize` under sudo. Commits nothing;
  uploads the `/tmp/cgb-lean-*` transcripts on failure.
- `lean-smoke` (45 min, FI-KA-5): asserts the whole seam — toolchain
  hard-asserted so green-by-skip is impossible, all four LeanBackend
  surfaces, both cert paths minting; probes pinned to `decide`-closable
  facts only. Builders may launch on smoke green; minting against the
  committed corpus still requires full `lean` green.
- `lean-fresh` (355 min): the once-per-pin L4 debt — `lean4checker`
  recertification of the imported oleans. Dispatch/`[lean-fresh]` runs
  pay the import-surface scope (`--fresh-imports-only`, minutes); the
  weekly schedule pays the whole-library replay (hours). Its ledger
  `.lean/fresh_discharged.txt` (setup.sh:143-147) is cached even on
  failure/cancel, so an interrupted run's paid debt is never re-paid.
- `lean-import` (PR #15, merged 2026-07-19; `[lean-import]`): whole-library
  enumeration + fragment-fit census, built TWICE and byte-compared
  in-lane (the P-LI0-CENSUS tooth), then
  `specs/mathsources/mathlib/{queue.jsonl.gz,census.json}` committed
  back to the triggering branch.
- `lean-rt` (PR #15, merged 2026-07-19; `[lean-rt]`): the RT differential
  batch over authored readings via `run.import_rt`; commits back
  `results/import_rt_report.json` + the queue. Failed rows flip to
  refused; authored→imported flips stay OUT of this lane — the
  dual-channel rule needs the statement-cert mint too.

**The weekly recert cron** (`17 5 * * 1`, ci.yml) fires `lean`,
`lean-smoke`, and the whole-library `lean-fresh` replay; the toolchain
image itself rebuilds weekly (toolchain-image.yml, `43 4 * * 1`).

**Marker commits.** The bot token lacks `actions:write`, so it cannot
`workflow_dispatch`; a push whose head-commit message carries a lane tag
fires that lane instead — the self-serve gate of COMPRESSION.md §12.8
item 1 — and is also how a corrected batch is deliberately re-fired
(commit 6624476, PR #15). **Commit-backs** from the artifact-producing
lanes carry `[skip ci]` (no trigger loops) and rebase onto the current
branch tip before pushing, because the branch may have moved during a
long enumeration — rebase-before-push, never a non-fast-forward failure
(ci.yml `lean-import`/`lean-rt`, PR #15).

**What the container cannot do.** The dev container's network policy
cannot fetch the Lean toolchain (ci.yml `lean-import` comment, PR #15),
and the harness is honest about the gap: `REQUIRES_LEAN` demos never
enter `FAST_DEMOS`, and `--full` skips-with-note when
`common.lean_available()` is False — deferred, not failed
(run_regression.py:94-106, 162-171). The operation routes around it by
phase split (PLAN_LEAN_IMPORT §3, PR #15): Phase A authoring is
token-heavy and Lean-free (any container); Phase B certification is
token-free and Lean-heavy and runs in the marker-fired CI lanes, whose
commit-backs put queue, census, and RT verdicts where Lean-less
containers can read them as data.

**Spend governance (PR #15, merged 2026-07-19).** The grant
`specs/ops/spend_grant.json`: mode `weekly-quota-exhaustion` (ruled
2026-07-17 — spend the subscription until exhausted, every week),
per-wave cap 2,000 ktok, expires 2026-08-17, arm
`ab-pilot-then-cheaper`. The driver's interlock is
`--confirm-spend`/`CGB_METERED_CONFIRM_SPEND=1` AND a valid unexhausted
grant — "both, not either" (buildloop/import_driver.py docstring); the
grant-expiry check is the module's single calendar comparison, made a
pure function by injecting the date. `results/import_ledger.jsonl` is
append-only and never truncated (`--fresh` truncates only the state
file), and the grant decrements against the ledger sum, so cumulative
spend is auditable from the repo alone; tokens are counted only from
`call_llm` usage metadata, never estimated (F1.2). **Breakers** are
registered predicates whose halts are recorded verdicts, never crashes:
P-LI1-REFUSAL (trailing-20 refusal rate > 60%), P-LI1-COST (wave cost >
3× trailing median), P-LI5-STOP (three zero waves → self-halt, demand a
readout) (PLAN_LEAN_IMPORT §4/§6). Measured, not hypothetical: C6 waves
halted on P-LI1-REFUSAL (results/c6_pilot/c6_report.json) — once fed by
transport failures, "the breaker did its job on the wrong disease"
(results/import_findings.md Finding 5).

## 9. The evidence landscape

Scope: a table of every load-bearing artifact under results/ and specs/ —
what claim it supports, what produced it, how to regenerate it.

Sources: results/ (ledgers, reports, censuses, sweeps, PNGs), milestones.py,
bench_{formalize,metered,speculate,latency}.py.
Must answer: for each headline number quoted anywhere in the docs, where
its artifact lives and the exact command that reproduces it.

Every headline number quoted in the docs has a committed artifact and a
regeneration path; the table maps claim → artifact → command. Three
reading rules: (1) `milestones.py` writes under `$CGB_ARTIFACTS`
(METRICS.md "Reproducing"); the committed copies live in `results/`.
(2) Rows marked [LLM] re-spend real tokens to regenerate; [gated] rows
additionally require the spend interlock (§8) — regenerating them is a
USER-GATED act, not a build step. (3) BUG-S1 (§10) is the standing
warning: an artifact must CONTAIN the numbers its record cites, so
regenerate-and-diff before trusting a quote.

| artifact (`results/`) | claim it carries | regenerate |
|---|---|---|
| `metrics_{frequency,closure}_{nocorpus,corpus}.csv`, `reach_vs_cost_{nocorpus,corpus,all}.png` | closure reaches full backlog ~3.5× cheaper than frequency (~56 vs ~198); legacy `total_dl` 7555 → ~298 (METRICS.md) | `python3 milestones.py m5` / `m8` (metrics/run_experiment.py) [LLM] |
| `math_reach_vs_cost.png` | the planted math reach-vs-cost curve (F-INT-3) | `python3 milestones.py m9_planted` (milestones.py:299; LLM-free, runs inside the fast gate) |
| `formalize_governed.csv` + `.meta.json`, `formalize_bench_state.jsonl`, `formalize_frozen_tables.json`, `formalize_reach_vs_cost.png` | the governed-vs-ungoverned wave-bench records the census replays pin against | `python3 bench/bench_formalize.py` [LLM] |
| `metered_evidence/{metered_run.json,verdicts.json}`, `metered_readout.json` | THE metered run: 484.16 vs 55.03 ktok/cert, DL 854 vs 689, coverage 3 vs 8, `verdicts_all_pass: false` — governance lost, and the record says so | `python3 bench/bench_metered.py --confirm-spend` [LLM, gated]; the readout is the wave-3 session's committed verdict (c229e5a) |
| `c2_report.{json,md}` | C2 honest currency: governed 2284.451 vs empty-table 1918.678 — the vocabulary costs +365.773 bits | `python3 tools/c2_report.py` |
| `ppm_ref.{json,md}` | adaptive KT order-1 codes the stream at 1514.5, beating `corpus_dl` 2139 by 624 (COMPRESSION.md:585-592) | `python3 tools/ppm_ref.py` |
| `entropy_refs.{json,md}`, `entropy_stack.png` | the order-k reference floors (orientation lines, not gates) | `python3 tools/entropy_refs.py`; `tools/entropy_stack_fig.py` |
| `tower_census.{json,md}` | T1/T2 gate inputs: `level2_witness_bar: 7`, macro-macro pairs at bar 0 | `python3 tools/tower_census.py` — the no-flags run is the census-of-record; the BUG-S1 caveat applies (§10) |
| `reentry_evaluations.json` | T1R/T2 evaluated once, `fired: false`; the §13.2 transfer registration + frozen-table digest | evaluation record, not a regenerable report |
| `proposal_admissions.{json,md}` | miner→gate seam: `n_proposed: 19`, `n_admitted: 4` | `python3 tools/admit_proposals.py`; admitted rows persist to `specs/mathsources/operators/admitted.json` (5 rows) |
| `holdout_transfer.json` | §13.2 transfer: data bits 645 → 559 (saving 86), KT 737.9819 → 733.7474, model bits 253 excluded as sunk | `python3 tools/holdout_transfer.py` (digest-guarded; LLM-free) |
| `cluster_key_measure.json` | the WP-FLIP refined-mining flip, `all_pass` | `python3 tools/measure_cluster_key.py` |
| `anchor_report.json` + `anchor_divergences/` | the ∃-anchor runner's reported-first record (no admission surface reads it) | run/anchor.py (REPORT_PATH, run/anchor.py:64) |
| `dl_trajectories.png`, `campaign_dashboard.html` | DL trajectory figure; the ledger dashboard | `tools/dl_trajectories_fig.py`; `tools/campaign_dashboard.py` |

Under `specs/`: `mathsources/*.txt` (the 51-sentence corpus of record)
plus `holdout/` and `dream/` are the demand the numbers above are
measured against; `mathsources/operators/admitted.json` is the priced
vocabulary itself, certificates embedded per row.

**Pending merge (PR #15) — the import operation's artifacts:**

| artifact | claim | regenerate |
|---|---|---|
| `results/import_ledger.jsonl` | the append-only spend ledger (C5's first real wave: 3 items, 116.1 ktok, zero certified — commit a621d4c) | `python3 cgb.py import --budget-ktokens B --confirm-spend` [LLM, gated] |
| `results/dry_wave_ledger.jsonl` | C4: full driver mechanics at real queue scale, zero tokens | `python3 tools/dry_wave.py` |
| `results/c6_pilot/` (`c6_report.json` + 4 ledgers) | C6: 82 authored (49/33), 4.12 vs 4.56 ktok/authored, first organic admission, `corpus_dl` 2074 → 2011 | `python3 tools/c6_pilot.py` [LLM, gated] |
| `results/import_rt_report.json` | RT round 2: defeq 28, proved 1, out-of-surface 2, failed 4 — zero confirmed mistranslations | `python3 -m run.import_rt` in the `[lean-rt]` lane |
| `results/import_findings.md`; `results/sweeps/s13_fable_sweep.md` | Findings 1–6; the §13 sweep verdicts | committed records — deliberately not regenerable |
| `specs/mathsources/mathlib/{queue.jsonl.gz,census.json}` | 225,916 declarations enumerated; 537 in-fragment under the current classifier (921 under the first — §7) | `python3 tools/enumerate_mathlib.py` + `python3 -m buildloop.census` in the `[lean-import]` lane, byte-identity toothed |
| `specs/mathsources/mathlib/readings/` (35), `import_macros.json`; `specs/ops/spend_grant.json` | the persisted certified readings; the wave-fed macro table; the grant | driver outputs / the committed human ruling |

## 10. Process culture: sweeps, records, refusals

Scope: adversarial critique sweeps as binding pre-implementation review;
record discipline (record/verdict divergence as a named failure axis —
BUG-S1, and this operation's own two exhibits: the groundedness
misdiagnosis and the persisted-vs-certified reading divergence);
pre-registered refusals; USER-GATED decisions; the Fable→Opus handoff
(§13.6) and why every gate must be a predicate a tool evaluates.

Sources: COMPRESSION.md §11/§12/§13.6/§13.A, results/sweeps/,
results/import_findings.md (the kept corrections).
Must answer: how a sweep is run and what makes its verdicts binding; the
standing list of USER-GATED items awaiting rulings.

**Sweeps are the review instrument, and they bind.** Before a plan is
implemented it is put through an adversarial critique sweep: independent
reviewers, one named failure axis each, every finding grounded in the
shipped tree — the §11 sweep's reviewers replayed the committed run
wave-by-wave (369/744/1238/1646/2139 exactly) or executed the real
battery in a scratch registry before claiming anything
(COMPRESSION.md:629-637). What makes verdicts binding is written into
the documents: "where §8's text and this section disagree, this section
wins" (§11); the wave-3 plan is titled "re-specified by its fable
critique sweep — BINDING" (COMPRESSION.md:1183); §13 was drafted
expressly "pending its own critique sweep before binding" (:1418). That
§13 sweep ran 2026-07-17 (results/sweeps/s13_fable_sweep.md, PR #15):
required to use the wave-3 results, it recomputed every number it
quotes (census rebuilt in-memory, transfer repricing re-run end-to-end)
and issued per-package verdicts; they are committed pre-binding and
await the user's ruling (commit 382cd6c). The exit discipline is itself
registered: every review must land its findings as teeth or registered
predicates and record the one axis it could NOT check mechanically —
"none" requires justification (COMPRESSION.md §13.6 item 4).

**Record/verdict divergence is a named failure axis.** The type
specimen is **BUG-S1** (s13_fable_sweep.md §13-S.1, PR #15): the T2
evaluation cites census digest e81ec84abc267875, the committed artifact
really hashes to it — and contains none of the evaluation's numbers,
which live only in results/reentry_evaluations.json. The sweep rebuilt
the census and reproduced 1/73/39 exactly: the verdict was right; the
record discipline failed. The import operation promptly produced two
exhibits of its own, both kept deliberately: (1) **the groundedness
misdiagnosis** — C6's 22 refusals were first recorded as a structural
NL-vs-formal groundedness mismatch, a diagnosis "inferred from the
stage name without replaying a single refusal transcript, and wrong in
kind": the wall was the theorem-name rule
(generators/math_reading.py:424-425). Cost of the wrong record: one
killed pilot and a misdirected plan entry; cost of checking: one 3-ktok
replay (results/import_findings.md Finding 1, PR #15 — the superseded
paragraph is retained in place). (2) **the persisted-vs-certified
divergence** — RT round 1 scored 35/35 failed because `persist_reading`
wrote the RAW pre-normalization reading while the classifier certified
the normalized one; the driver now persists exactly the certified
bytes, and the 33 stale reading artifacts were deterministically
re-normalized (commit 6624476, PR #15). Both are BUG-S1's class: record
and checkable truth diverged, and only a replay caught it.

**Pre-registered refusals.** Tempting shortcuts are refused on file
BEFORE the work that would tempt them: COMPRESSION.md §9 ("what we
deliberately will not do"), §12.9 (carried + extended), §13.7 (the
kill-list — each kill stated with its narrow re-entry predicate), and
PLAN_LEAN_IMPORT §7 (PR #15: no estimate-based token accounting, no
wall-clock in any decision, no "percent of Mathlib imported" headline,
no speculative reading-AST generality, glosses never cert subjects).

**USER-GATED decisions.** The standing list awaiting rulings:
COMPRESSION.md §13.8's four — (1) any authoring spend on a new domain,
(2) promotion of the spent holdout into the live corpus, (3)
acquisition of new sources for the existing domain, (4) any activation
of §11.8's C2/C4 revisit clause from a tripwire instance. The import
operation adds (PR #15): the §13 sweep verdicts' binding ruling;
import-surface widening (a `.lean-pins`-adjacent, cache-re-keying
event, PLAN_LEAN_IMPORT WP-LI0); the C7 unattended-churn ruling,
reachable only through the C6 readout conversation (§8 ladder); and
T-LI-ENC's corpus-write-off alternative (§2.5). Ruled items keep their
STATUS on file — §12.8's TRIGGERED / GO / RESOLVED entries, and the
2026-07-17 grant ruling recorded verbatim in specs/ops/spend_grant.json
(PR #15).

**The Fable→Opus handoff (COMPRESSION.md §13.6).** The sweeps "were the
program's most expensive input and they are going away." WP-MECH
converts what reviewers actually caught into machine-checked form: the
regeneration cascade becomes a CI-checked manifest; gate evaluation
lives in tools, never in a human re-reading a section; the honesty
block gets a schema and a lint; reviews must end as landed teeth plus a
standing register of named blind spots, re-read at every growth event.
The acceptance criterion is the reason every gate must be a predicate a
tool evaluates — "after WP-MECH, no gate exists only as prose" —
because prose gates are exactly where the sweep found drift: the §13.3
"if transfer fails" sentence whose undefined middle the marginal
transfer verdict now occupies, and BUG-S1 itself (s13_fable_sweep.md
§13-S.0/§13-S.1, PR #15).

## 11. Current state and open threads (as of 2026-07-17)

Scope: a live snapshot — what works today, what is pending.
Known-open at skeleton time: §13 sweep verdicts await user review before
binding; the two RT probe fixes (namespace-variant out-of-surface, the
iff/T7 collision); the statement-cert channel to flip 29 rows
authored→imported; import-surface widening (USER-GATED, re-keys the
cache); H3 candidate generation for organic level-2; the C7 unattended-
churn ruling (requires the C6 readout conversation); §13.2's REG-DOM-GATE-1
respec. Update this list as threads close.

*Most of what this section tracks landed on main via PR #15 (branch
`claude/token-spend-lean-import-qk633q`), merged 2026-07-19.*

**What works today.** On main: the certified task-time path, the
two-tier trust architecture, the math/formalization lane, and the
compression machinery with its honest negative verdicts (§§1–6). On PR
#15: the whole import layer — queue + census, budgeted driver, RT
oracle, inline mining — commissioned through C6, with 82 authored rows,
one organic vocabulary admission, and 29 kernel-confirmed translations
(§7). Open threads, each with its blocking condition:

- **PR #15 is open and unmerged.** The import layer, the findings
  record, the §13 sweep report, and this document's skeleton all live
  on its branch (head 3b2ebd0); nothing in §7 is on main until it
  merges. The fleshing of this file is itself in progress on branch
  `claude/architecture-docs-github-8ytcmv` (§0 landed at bfaa37d).
- **§13 sweep verdicts await user review.** §13 is a DRAFT "pending its
  own critique sweep before binding" (COMPRESSION.md:1418); the sweep
  ran 2026-07-17 and its report is committed pre-binding
  (results/sweeps/s13_fable_sweep.md — every package proceed-with-
  re-specs or refusal-sound, plus bugs BUG-S1–S3 registered). Blocked
  on: user adjudication making the verdicts binding.
- **Two RT probe fixes** (results/import_findings.md Finding 6): (a)
  the out-of-surface detector matches only `unknown identifier`
  (run/import_rt.py:319-321), but a namespace-variant miss errors as
  field-notation (Even.mod_even transcript,
  results/import_rt_report.json); (b) the iff fallback embeds the
  original pp text, whose `ℕ` the T7 escape gate refuses ("non-ASCII
  identifier character U+2115 refused (homoglyph bypass, T7)", same
  report) — the gate wins by design; the probe must reference the
  original by name. Blocked on: probe-side changes, then an RT re-run.
- **The statement-cert channel** must run to flip the 29 RT-confirmed
  rows `authored → imported`: imported requires both channels
  (PLAN_LEAN_IMPORT.md §3) and rt_batch deliberately does not flip
  (run/import_rt.py:430-432); the queue holds 35 authored, 0 imported.
  Blocked on: the Phase-B statement-cert run in the Lean lane.
- **Import-surface widening is USER-GATED**: the certification surface
  stays the pinned modules; widening re-keys the ~5 GB toolchain cache
  (plan WP-LI0). The 2 out-of-surface rows (numDerangements_one,
  rothNumberNat_zero) re-run automatically once widened
  (run/import_rt.py:396-400). Blocked on: an explicit user ruling.
- **H3 candidate generation**: the miner generates level-1
  (concrete-body) candidates only — the H3 concreteness filter rejects
  invocation templates before pricing (COMPRESSION.md:719-721; Finding
  4's registered limitation). Hand-built tower candidates now price
  correctly; organic level-2 emergence is blocked on revisiting H3.
- **The C7 unattended-churn ruling**: cadence is decided with the user
  on the C6 readout, never before it (plan §8); the readout exists
  (Findings 5–6, results/c6_pilot/c6_report.json). Until ruled, every
  wave is human-started and no Routine is scheduled.
- **§13.2's REG-DOM-GATE-1 respec**: the sweep found §13 shipped a
  prose gate at its most consequential junction ("if transfer fails
  within-domain"), whose undefined middle the marginal transfer verdict
  landed in; re-specified as REG-DOM-GATE-1
  (results/sweeps/s13_fable_sweep.md:203). Blocked on: the sweep
  binding, then the honesty-lint predicate landing.
- Carried from §7: the **T-LI-ENC CI tooth** (refuse an unaccompanied
  encoding-version bump) is registered but not yet landed — recorded as
  §8.1's one open item (PLAN_LEAN_IMPORT.md §8.1).

## 12. Glossary

Scope: the working vocabulary — DL / ledger_dl / corpus_dl, KT coder, C2,
tier, rung, tooth, arm, wave, anchor, reading, fragment-miss, defeq, RT,
census, frontier, grant, breaker, exogenous, dream lane, escape gate,
homoglyph rule (T7), pin, olean, marker commit, USER-GATED, record/verdict
divergence.

Must answer: one tight sentence each, pointing at the defining source.

- **DL** — description length, the repo's admission currency; two
  series exist and must never be confused: the frozen codec-only
  `total_dl` (buildloop/mdl.py) and the live `ledger_dl` (METRICS.md
  "Two DL series").
- **ledger_dl** — the combined loop's ONE currency: every demand kind
  priced in one ledger, every move admitted iff it strictly drops
  (buildloop/dl.py:1-7).
- **corpus_dl** — the macro-tower counting currency: per-reading data
  cost plus once-per-macro model cost over the math corpus
  (buildloop/mdl_macros.py:21).
- **KT coder** — the adaptive (prequential) Krichevsky–Trofimov order-k
  reference coder that pays full learning cost; its order-1 stream code
  of 1514.5 beats corpus_dl 2139 (tools/ppm_ref.py;
  COMPRESSION.md:587-592).
- **C2** — the reported-only two-part macro+entropy-coded currency
  upgrade (COMPRESSION.md §3; tools/c2_report.py), whose measurement
  says the vocabulary costs +365.8 bits.
- **tier** — a generator's trust standing: *emit-check* (every output
  individually verified) vs *universal* (the generator proven once,
  outputs inherit trust via provenance) (README.md constraints;
  buildloop/promote.py).
- **rung** — a ladder step, in two senses: the proof-tactic escalation
  ladder whose closing rung the certificate records (decide → norm_num
  → simp, FORMALIZATION.md:397), and kernel/rung.py's minimal lowering
  meta-interpreter (WP-T6a).
- **tooth** — an executable check (test or in-lane CI assertion) that
  enforces a stated discipline mechanically, e.g. P-LI0-CENSUS's
  build-twice byte-compare (ci.yml `lean-import`, PR #15).
- **arm** — one side of the governed-vs-ungoverned A/B protocol:
  exogenous-only mining with per-use certs on, vs all readings with
  certs off (bench/bench_formalize.py docstring).
- **wave** — one frozen-table batch: K statements authored concurrently
  against a pinned `table_hash`, then a serial LLM-free certify/mine
  tail (bench/bench_formalize.py "WAVE PROTOCOL"); also the import driver's
  unit of budgeted spend (buildloop/import_driver.py, PR #15).
- **anchor** — the identity a certificate binds to: an import row's
  `(decl_name, statement_hash)`-at-the-pin (PLAN_LEAN_IMPORT §2.5 R1,
  PR #15), and separately the ∃-witness anchor runner's
  exists-anchor-cert (run/anchor.py).
- **reading** — the speech-act-tagged declarative logical form the LLM
  is permitted to author (generators/math_reading.py;
  generators/reading.py).
- **fragment-miss** — a statement the F-G fragment cannot express,
  logged as first-class demand data that drives priced vocabulary
  growth, never a bug (run/formalize.py:491-495; FORMALIZATION.md F4).
- **defeq** — the RT differential's fast path: the compiled statement
  typechecks as definitionally equal to the original declaration's
  (run/import_rt.py:11-17, PR #15).
- **RT** — the round-trip differential RT(d): the compiled reading must
  be provably equivalent to declaration d's own statement in the Lean
  lane; both probes failing is a refusal, never a warning
  (PLAN_LEAN_IMPORT §2, PR #15).
- **census** — a deterministic measurement-of-record: the tower/idiom
  census that feeds the T1/T2 gates (tools/tower_census.py), and the
  fragment-fit census binning all 225,916 Mathlib declarations by
  needed constants with unlock counts (buildloop/census.py, PR #15).
- **frontier** — the census-ordered slice of the queue the fragment can
  currently attempt; progress per kilotoken is the only headline, never
  "percent of Mathlib" (PLAN_LEAN_IMPORT §0, PR #15).
- **grant** — the committed, USER-GATED spend authorization the driver
  checks before any token (specs/ops/spend_grant.json, PR #15;
  PLAN_LEAN_IMPORT §5).
- **breaker** — a registered per-wave circuit predicate whose halt is a
  recorded verdict, never a crash: P-LI1-REFUSAL, P-LI1-COST
  (PLAN_LEAN_IMPORT §4 WP-LI1, PR #15).
- **exogenous** — demand of origin `"exogenous"` (real, committed), as
  opposed to system-origin dreams; only exogenous rows count as reach
  or as admission witnesses (SPECULATION.md:176; METRICS.md math
  fields).
- **dream lane** — the speculative channel: LLM paraphrases seeded as
  system-origin readings under `specs/readings/dream/`; "dreams
  propose, real witnesses decide" (SPECULATION.md S5).
- **escape gate** — buildloop/validate_lean.py's lexical gate over
  emitted Lean text: defense-in-depth and cheap-fast-reject, NEVER the
  trust boundary (validate_lean.py:1-3; ⚠T7).
- **homoglyph rule (T7)** — the escape-gate rule refusing non-ASCII
  identifier characters and guillemet raw identifiers as lexical-bypass
  vectors (buildloop/validate_lean.py:57-64; FORMALIZATION.md:943) —
  the rule RT round 2's iff-fallback probe collided with (Finding 6,
  PR #15).
- **pin** — the single-sourced toolchain fix in `.lean-pins`
  (MATHLIB_COMMIT primary, LEAN_TOOLCHAIN derived and asserted); the
  one file whose edits re-key the ~5 GB CI cache.
- **olean** — a compiled Lean object file: Mathlib's prebuilt oleans
  are fetched at setup (setup.sh:90-92) and recertified once per pin by
  lean4checker (the L4 debt).
- **marker commit** — a push whose head-commit message carries a lane
  tag (`[lean-ci]`, `[lean-fresh]`, `[lean-smoke]`; PR #15 adds
  `[lean-import]`, `[lean-rt]`) to fire an opt-in CI lane, because the
  bot token lacks `actions:write` for workflow_dispatch (ci.yml;
  COMPRESSION.md §12.8 item 1).
- **USER-GATED** — a decision reserved to the human user and recorded
  with an explicit STATUS once ruled (COMPRESSION.md §12.8, §13.8).
- **record/verdict divergence** — the named failure axis where a
  committed record and the checkable truth disagree; BUG-S1 is the type
  specimen, the import operation's two exhibits its confirmation
  (results/sweeps/s13_fable_sweep.md §13-S.1;
  results/import_findings.md — both PR #15).
