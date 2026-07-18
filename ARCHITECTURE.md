# ARCHITECTURE.md — how this repo works, consolidated

STATUS: **SKELETON** (drafted 2026-07-17). Each section below carries a
scope line, the sources to draw from, and the questions the finished
section must answer. A separate interactive session fleshes this out with
the user, section by section — replace each `TO FLESH OUT` block in place;
keep the questions as the section's acceptance test; delete this banner
when every section is done.

Ground rules for the fleshing session: (1) every claim cites a file, an
artifact in `results/`, or a committed verdict — this repo's culture is
that prose without a pointer is not a record; (2) where the honest answer
is "measured and it said no," write that — the repo's distinctive asset is
instruments that refuse to flatter it; (3) prefer the primary sources over
this session's summaries.

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

TO FLESH OUT

## 2. The seed domain and the generator library

Scope: text/binary codecs as the crisp-oracle seed domain; what was
outsourced (Dafny/Z3/CVC5, Kaitai, tree-sitter, Hypothesis) vs authored
(the wiring, the ledger, the measurement).

Sources: README.md components table, generators/, generators/codec_model.dfy.
Must answer: why codecs; the spec→code path for one codec end to end; the
round-trip + malformed-rejection oracle.

TO FLESH OUT

## 3. The task-time path (no LLM, ever)

Scope: `run/` — spec → planner → generator chain → code, deterministically;
the CGB_TASK_TIME guard that makes any LLM call raise in flight.

Sources: run/__init__.py, buildloop/llm.py (the guard), common.py
(TASK_TIME_ENV), tests/test_invariants.py.
Must answer: byte-identity guarantee (same spec + registry state ⇒
identical output); how the guard is enforced and tested.

TO FLESH OUT

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

TO FLESH OUT

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

TO FLESH OUT

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

TO FLESH OUT

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

TO FLESH OUT

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

TO FLESH OUT

## 9. The evidence landscape

Scope: a table of every load-bearing artifact under results/ and specs/ —
what claim it supports, what produced it, how to regenerate it.

Sources: results/ (ledgers, reports, censuses, sweeps, PNGs), milestones.py,
bench_{formalize,metered,speculate,latency}.py.
Must answer: for each headline number quoted anywhere in the docs, where
its artifact lives and the exact command that reproduces it.

TO FLESH OUT

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

TO FLESH OUT

## 11. Current state and open threads (as of 2026-07-17)

Scope: a live snapshot — what works today, what is pending.
Known-open at skeleton time: §13 sweep verdicts await user review before
binding; the two RT probe fixes (namespace-variant out-of-surface, the
iff/T7 collision); the statement-cert channel to flip 29 rows
authored→imported; import-surface widening (USER-GATED, re-keys the
cache); H3 candidate generation for organic level-2; the C7 unattended-
churn ruling (requires the C6 readout conversation); §13.2's REG-DOM-GATE-1
respec. Update this list as threads close.

TO FLESH OUT

## 12. Glossary

Scope: the working vocabulary — DL / ledger_dl / corpus_dl, KT coder, C2,
tier, rung, tooth, arm, wave, anchor, reading, fragment-miss, defeq, RT,
census, frontier, grant, breaker, exogenous, dream lane, escape gate,
homoglyph rule (T7), pin, olean, marker commit, USER-GATED, record/verdict
divergence.

Must answer: one tight sentence each, pointing at the defining source.

TO FLESH OUT
