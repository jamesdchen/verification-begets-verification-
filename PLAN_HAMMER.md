# PLAN_HAMMER.md — the hammer program as driver-cycle work packages

Status: ACTIVE — sibling packet to `PLAN_ZONE3_CYCLES.md` (which re-slices the
speculative planner) and `PLAN_FRAGMENT.md` (the corpus↔fragment flywheel).
This document plans the **hammer**: the batched proof-search lane that takes
the demand the repo has already *measured* — anchor ∃-goals, import-RT rows,
bench-certified statements — and drives it up the ladder `nothing →
statement-cert → proof-cert`, one CI round-trip at a time. It is
**documentation only.** It adds nothing to the trusted surface: per CLAUDE.md
the anti-list (`buildloop/growth_protocol.py::ANTI_LIST`), `kernel/certs.py`
pins, `TRUST.md`, and the escape-gate blocklist change **only** through the
PLAN_REFLECT S4a→S4a′→S4b ceremony with user sign-off; no package below
touches them.

Every package carries, exactly as in `PLAN_ZONE3_CYCLES.md`:

- **(a)** an **entry predicate** checkable from committed state alone (file
  existence, a symbol grep, a committed JSON count, a test node) — the driver
  runs the check before spending a lane ride;
- **(b)** **exit teeth** naming the committed test file that must stay green or
  the exact new test the package adds;
- **(c)** the **bench that measures the payoff** — for the hammer that is the
  close-rate readout (`results/flywheel_probe.json`,
  `results/hammer_readout.{json,md}`), which **measures the close-rate and
  never asserts the flywheel compounds** (the Finding-2 discipline
  `tools/flywheel_probe.py` was built under, see its module docstring).

**Ordering law (invariant for the driver), inherited verbatim from
`PLAN_ZONE3_CYCLES.md`:** packages are ordered so each cycle leaves the tree
**green and shippable** — full suite green (`python3 -m pytest tests/ -q -n
auto`) is part of every package's exit, no cycle depends on an unmerged
sibling, and no exclusive file is left half-written across a cycle boundary.
The Lean-touching half of any package rides the CI lane last, per
PLAN_FRAGMENT §3.1 (lane-verdict-first / Lean-last); the corpus/queue-assembly
half is Lean-free and verifiable in-container.

---

## Honesty posture — binding on every package

The hammer reports **fidelity evidence, never truth verdicts.** This is the
same law the census obeys (CLAUDE.md: "the census reports signals, never
fidelity verdicts") pushed one level up: a hammer verdict row is *lane
evidence toward a future kernel mint, never a certificate*. Three rules recur
in every package and are quoted here because they are the frame:

- **The ladder is `nothing → statement-cert → proof-cert`, and that is TWO
  lane steps, not one.** The kernel **statement-cert is deferred** on this
  tree; a bench-certified statement carries dual-arm bench fidelity evidence
  (Lean-free) but no kernel statement-cert, and a closed proof is a further,
  distinct mint. A package never collapses the two steps, never labels a bench
  row "certified TRUE" — the canonical label is **"dual-arm bench-certified
  (Lean-free fidelity evidence; kernel statement-cert deferred)"**.
- **Refusals are first-class demand data.** An `elaborated=false` row is
  *statement-cert demand* (the statement did not even typecheck) and is
  reported **separately** from a tactic refusal, which is *hammer/H3 demand*
  (the statement stands, no rung closed it). Neither is a failure of the lane;
  both are recorded, never hidden, never retried-wider.
- **Infrastructure refusals are gate/rendering demand, never proof demand.**
  The four import-RT failed rows (below) are a rendering bug and an
  escape-gate refusal — *the math never ran.* They enter the queue as
  `infra-refused` and are **never batched**; the repair is a separate deferred
  package (H-D0), not proof search.

**The smoke-mint caveat (mandatory to state).** `.github/workflows/ci.yml`'s
`lean-smoke` job (`:411`) asserts the **statement-cert / proof-cert dispatch
SEAM** the anchor and hammer reuse — but it mints against **stubbed fidelity
channels** (`smoke-fidelity-a`/`smoke-fidelity-b`, `ci.yml:553-556`, each
hard-coded `result: "pass"` with the detail "fidelity is the pipeline's job,
not the seam's"). A green `lean-smoke` therefore proves the **mint seam
wiring**, not a real proof: **a real hammer mint requires the real F2.1/F2.2
fidelity channels** (cross-impl differential + behavioral witness) supplied by
the pipeline, not the smoke stubs. No package treats `lean-smoke` green as
evidence a goal is proved.

---

## The consume-before-merge protocol rule (quoted verbatim, binding)

The hammer lane commits its verdicts back with `GITHUB_TOKEN`, and a
`GITHUB_TOKEN` push fires no workflows. The tip it leaves therefore has **zero
check runs.** The rule, reproduced verbatim from the build contract's WS-S
section, binds every driver:

> the lane's commit-back tip has no check runs (GITHUB_TOKEN pushes fire no
> workflows) — drivers never merge that tip; the next driver session consumes,
> commits with its own credentials (re-arming checks), then merges.

Mechanically: the self-merge rule's missing-trust-surface refusal enforces
this — a tip with no check runs cannot be self-merged. The next driver session
CONSUMES the verdicts into the readout, commits under its own credentials
(which re-arms the checks), and only then merges. This rule appears again as
the exit discipline of every H1/H2 lane package.

---

## Demand sources (verified counts, deduped)

The hammer's proof-goal queue is assembled from three committed artifacts,
each pinned by SHA-256 in the queue's `derived_from`. Counts verified against
the tree at planning time:

- **(a) anchor-exists — 3.** `results/anchor_report.json` rows at
  `lattice_point == "shadow-certified"`: `41_division_algorithm`,
  `42_bezout_identity`, `44_divides_witness`. The fourth ∃ reading,
  `43_larger_integer_exists`, is `shadow-edge-refused` — **the bounded shadow
  REFUTED it** (`refuting_outer: {"n": 8}`); it enters the queue with status
  `shadow-refuted-excluded` and is **never queued as provable.** These route
  via the ∃-anchor kernel-leg template machinery (`run/anchor.py`), not raw
  rungs.
- **(b) rt-failed — 4.** `results/import_rt_report.json` `summary.by_verdict`
  `failed == 4`: `Even.mod_even`, `Odd.mod_even`, `Odd.ne_two_of_dvd_nat`,
  `Odd.of_dvd_nat`. **All four are infrastructure refusals**: the `defeq`
  probe hits a field-notation rendering bug (`invalid field notation, type is
  not of the form (C ...)`), and every `iff` rung is refused by the
  escape-gate on `U+2115` (`ℕ`, homoglyph-bypass T7) — *the math never ran.*
  Status `infra-refused`, **never batched**; recorded as gate/probe-surface
  demand. (The two additional `closed_by: null` rows, `numDerangements_one`
  and `rothNumberNat_zero`, carry verdict `out-of-surface` and are **not**
  among the four — they are not queued at all.)
- **(c) bench-certified — 66.** `results/formalize_bench_state.jsonl` rows with
  `arm == "governed"` and `certified == true` (66 rows, 66 distinct
  `source_id`s). Label: **dual-arm bench-certified (Lean-free fidelity
  evidence; kernel statement-cert deferred)** — never "certified TRUE".

**Dedupe.** Sources 41/42/44 appear in **both** anchor-exists and
bench-certified (verified: all three `source_id`s are in the governed-arm
certified set), so the queue dedupes by **subject SHA-256** — ref+hash, never
prose. The four infra-refused rows are queued-but-not-batched. See
`PLAN_ZONE3_CYCLES.md`'s Z1 restated for the driver: **a queued goal is a
proposal; it becomes trustworthy only by passing the unchanged kernel on the
identity the non-speculative path would use.**

---

## H0 — the proof-goal queue

### H-H0.1 — `results/proof_queue.json` + builder + teeth

- **Entry predicate:** the three demand artifacts committed. Check:
  `test -f results/anchor_report.json && test -f
  results/import_rt_report.json && test -f
  results/formalize_bench_state.jsonl`.
- **Work:** a queue-builder (lane-adjacent, **explicitly NOT in the
  `regen_downstream` DAG** — its module docstring states this, exactly as
  `run/anchor.py` sits outside the DAG) that emits `results/proof_queue.json`:
  `derived_from` pinning every input's SHA-256; `goals[]` each carrying
  `goal_id`, `source ∈ {anchor-exists, rt-failed, bench-certified}`, `subject:
  {ref, sha256}` (**ref+hash, never prose**), `status ∈ {queued, infra-refused,
  shadow-refuted-excluded}`, `family`, `rung_hint`, `provenance`; deterministic
  order; **dedupe by subject sha256**; the `honesty` string carrying the
  two-lane-step / infra-refused framing.
- **Exit teeth:** `tests/test_proof_queue.py` (new) — **regenerate-and-byte-
  compare vs committed** (precedent `tests/test_frontier.py`, whose seed-drift
  byte-identity discipline this reuses: re-deriving reproduces the committed
  bytes exactly); **schema exactness**; **dedupe** (41/42/44 collapse to one
  subject each); **counts** (3 + 4 + 66, minus dedupe). Reconciliation rides
  the pinned `derived_from` SHA-256s: **an input moved is recorded staleness
  demand** (distinct from derivation-wrong, which is red). Full suite green.
- **Bench (payoff):** none — H0 buys *inputs*, not close-rate (the S0 precedent
  in `PLAN_ZONE3_CYCLES.md`: "S0 buys inputs, not speed"). A queue that
  miscounts or fails byte-compare is a red cycle.
- **Honesty:** the queue is a table of **proposals with provenance**; no queue
  row is a certificate, and `shadow-refuted-excluded` / `infra-refused` rows
  are carried *visibly*, never dropped to inflate the queued count.

---

## H1 — the batched `[lean-hammer]` lane

The lane's workflow file, `.github/workflows/lean-hammer.yml`, is the
**integrator's deliverable** (build-contract WS-S, ceremony PR — not yet on
this branch). It is an **own workflow file by design:** `ci.yml`'s `push`
trigger carries `paths-ignore: ["**.md", "results/**"]` (`ci.yml:14`), so a
**results-only marker commit would never fire a job there**, and a bare
`workflow_dispatch` of `ci.yml` would ignite five other heavy lanes. The lane
fires on `workflow_dispatch` or a push whose head commit carries
`[lean-hammer]`; **never on schedule**; `permissions: contents: write,
packages: read` (exactly — the block replaces defaults); own concurrency group
`lean-hammer-${{ github.ref }}` with `cancel-in-progress: true` (honest note:
a superseding marker push **forfeits** the in-flight ride — the deadline-bounded
PARTIAL verdicts plus the always-uploaded artifact are the mitigation).

### H-H1.1 — ASSEMBLE (`bench_hammer.py assemble` → `results/hammer_batch.json`)

- **Entry predicate:** `results/proof_queue.json` committed with ≥1 `status ==
  "queued"` row. Check: `python3 -c "import json;
  print(sum(g['status']=='queued' for g in
  json.load(open('results/proof_queue.json'))['goals']))"`.
- **Work:** from `queued` rows, emit per goal the **exact rendered Lean bytes
  to elaborate**. Rendering **reuses `tools/flywheel_probe.py`'s machinery**
  (the repo's "hammer close-rate meter, v0") and `generators/math_compile`'s
  own `_render_pred` — **stated delta:** this bench renders **UNBOUNDED**
  statements, whereas `flywheel_probe` renders **grounded instances** (the *k*
  smallest satisfying instances substituted in). Rung vocabulary is
  **IMPORTED** from `generators.math_witness.RUNGS`
  (`= ("decide","omega","norm_num","simp")`, `generators/math_witness.py:98`)
  — never redeclared; the single-source equality against
  `kernel/certs.py::ANCHOR_DISCHARGE_RUNGS` (`kernel/certs.py:433`, identical
  tuple) is a tooth (precedent `tests/test_import_rt.py:129`, "the witness
  rungs ARE the math_witness RUNGS precedent, in pinned order"). `forall` goals
  get an intro prelude drawn **only** from the existing closed discharge
  vocabulary (`kernel/certs.py`) — **no new tactic surface**; `exists` goals
  route via the ∃-anchor kernel-leg template machinery (`run/anchor.py`), not
  raw rungs. First-success short-circuit ordering; **deterministic cap**
  (default 24 goals/ride, flag — see batch-cap arithmetic below).
- **Exit teeth:** `tests/test_bench_hammer.py` (new) — assemble **determinism**
  (byte-compare the committed `hammer_batch.json`) and the RUNGS single-source
  equality node; full suite green.
- **Bench (payoff):** none yet — assemble stages goals; close-rate is measured
  in H1.2/H2.
- **Honesty:** the batch is rendered proposals; the rung set is *imported*, so
  the hammer can never widen its own tactic surface as a side effect.

### H-H1.2 — RIDE + CONSUME (`run/hammer_ride.py`, `bench_hammer.py consume`)

- **Entry predicate:** `results/hammer_batch.json` committed; the `[lean-hammer]`
  lane workflow (WS-S deliverable) present. Check: `test -f
  results/hammer_batch.json && test -f .github/workflows/lean-hammer.yml`.
- **Work:** `run/hammer_ride.py` is the in-lane per-goal driver — it calls
  `LeanBackend.elaborate` / `LeanBackend.recheck` (`kernel/backends.py:724` /
  `:784`) **byte-identically to the kernel channel**, including **FAIL-CLOSED
  on audit silence**; first-success short-circuit; a wall-clock deadline writes
  **PARTIAL** verdicts with the remaining goals marked `not-run`.
  `results/hammer_verdicts.json` rows are `{goal_id, script, elaborated,
  replayed, axioms}` — **NO per-row wall seconds** (byte-stability: lean-rt's
  no-op guard and write-twice teeth depend on it; lane costs go to
  `cycle_telemetry`/lane aggregates), plus an `evidence_note` on the
  `import_rt` precedent that rows are lane evidence toward a future kernel mint,
  never certificates. CONSUME turns verdicts into
  `results/hammer_readout.{json,md}`: **per-rung AND per-family** closure table;
  **statement-stage failures (`elaborated=false`) reported SEPARATELY** as
  statement-cert demand, distinct from tactic refusals (hammer/H3 demand);
  **refusals first-class**; token columns present and **zero** (LLM off). The
  lane workflow copies the `lean-rt` skeleton (`ci.yml:617` — setup-python +
  pip cache, image prime with cache fallback, `setup.sh --with-lean
  --lean-only --skip-fresh`, TC hardcode + sudo env, tool-presence checks),
  then: ride (deadline-bounded), consume in-lane, `upload-artifact if:
  always()` **before** commit-back, a single `[skip ci]` commit of verdicts +
  readout (+ regenerated queue if inputs moved), rebase-push in a bounded
  3-attempt retry loop.
- **Exit teeth:** `tests/test_hammer_ride.py` (new) covering the **Lean-absent
  deferral path only** (precedent `tests/test_import_rt.py:207`,
  `skipif(not common.lean_available())`; Lean absent → `deferred`, honest,
  never a failure); `tests/test_bench_hammer.py` — CONSUME on a **synthetic
  verdicts fixture**, readout schema, and the separated statement-stage /
  tactic-refusal columns. **Bootstrap:** commit the honest **not-yet-run**
  readout state (the `import_rt` Lean-absent deferral precedent — an
  all-deferred report without error). Full suite green.
- **Bench (payoff):** `results/hammer_readout.{json,md}` — the per-rung /
  per-family closure table. It **measures** the close-rate; it never asserts
  the flywheel compounds.
- **Protocol (binding):** the lane's commit-back tip has zero check runs — a
  driver **never merges it**; the next session consumes, commits under its own
  credentials, then merges (the quoted rule above).

**Batch-cap arithmetic.** The `[lean-hammer]` budget is **120 min**. Image
prime + Lean toolchain restore + tool-presence checks cost **~15–25 min**,
leaving a **~95–105 min** elaboration window; worst-case a single goal costs
**3–10 min** (deep `omega`/`simp`). The two guards are distinct: the **24-goal
cap** bounds *determinism* (a reproducible, byte-stable slice — 24 is inside
the window in the expected case, where first-success short-circuit closes
rung-0 goals in *seconds* not minutes), while the **wall-clock deadline** bounds
*wall-time* (24 × 10 min worst case = 240 min ≫ window, so the cap alone cannot
guarantee fit — the deadline is what writes PARTIAL verdicts and forfeits
nothing). Both are flagged; neither is silently widened.

---

## H2 — `bench_hammer`, LLM-off (the close-rate meter)

### H-H2.0 — the near-free pre-read (one `[lean-ci]` ride)

> Placed first in H2 because it is **near-free** and it is the **entry
> predicate for H3+**: it produces the rung-0/1 close-rate readout the H3 queue
> is derived from, on machinery that already exists — no new lane, no new
> tactic surface.

- **Entry predicate:** `run/anchor.py` and `tools/flywheel_probe.py` committed
  (both present). Check: `test -f run/anchor.py && test -f
  tools/flywheel_probe.py`.
- **Work:** one `[lean-ci]` ride of the **existing** ∃-anchor runner
  (`run/anchor.py`, which ELABORATE-PROBES via `LeanBackend.elaborate`, GUARDED
  — Lean absent → honest skip) **plus** `tools/flywheel_probe.py` (`--out
  results/flywheel_probe.json`, default at `tools/flywheel_probe.py:135`; the
  frozen ladder `decide→omega→norm_num→simp` over grounded corpus props).
  Commit `results/flywheel_probe.json` (the rung-0/1 close-rate readout) beside
  the already-committed `results/anchor_report.json`.
- **Exit teeth:** the anchor teeth (`tests/test_anchor_runner.py`,
  `tests/test_anchor_cert_contract.py`) and the flywheel-probe teeth stay
  green; `results/flywheel_probe.json` committed with an honest `deferred`
  close-rate when Lean is absent (never fabricated). Full suite green.
- **Bench (payoff):** `results/flywheel_probe.json` — the close-rate DELTA
  meter. **Recorded prediction (committed and read before H3):** rung-0
  (`decide`) closes **~20–30 of 67** ground props; **refusals 35–45 = the H3
  queue.** (The 67 is the probe's ground-prop denominator — near, not identical,
  to the 66 bench + 3 anchor unbounded-statement queue after dedupe; the gap is
  honest, the probe scores grounded instances, the queue scores unbounded
  statements.)
- **Honesty:** Lean-absent → every prop `unavailable`, close-rate `deferred`,
  never a fabricated number.

### H-H2.1 — first real `[lean-hammer]` ride over the committed batch

- **Entry predicate:** `results/hammer_batch.json` committed (H1.1) **and**
  `results/flywheel_probe.json` committed and read (H2.0 — the rung-0/1 readout
  that predicts the H3 queue).
- **Work:** dispatch the `[lean-hammer]` lane over the committed batch; consume
  in-lane; land `results/hammer_readout.{json,md}`.
- **Exit teeth:** `tests/test_bench_hammer.py` readout-schema node stays green
  against the real readout; the per-rung / per-family closure table is
  populated; full suite green (doc/results-only downstream).
- **Bench (payoff):** `results/hammer_readout.{json,md}` — measured closure by
  rung and family, statement-stage failures split out from tactic refusals,
  token columns zero.
- **Protocol (binding):** consume-before-merge (quoted rule).

---

## H3 — the LLM sketch author (spec-bytes-only)

> **Implementation is out of scope for this build** (the contract lists
> H3/H4/H5 implementation and LLM tiers as out of scope). H3 is documented here
> as the next phase — entry predicate, teeth, and bench NAMED — so the driver
> knows exactly what unlocks it and on what evidence.

- **Entry predicate (the gate for all of H3+):** the **rung-0/1 readout
  committed and read** (`results/flywheel_probe.json` from H2.0 and
  `results/hammer_readout.json` from H2.1). The recorded prediction that
  *justifies* opening H3: **rung-0 closes ~20–30 of 67; the 35–45 refusals are
  the H3 queue** — H3 exists precisely to author sketches for the goals the
  frozen ladder could not close.
- **Work (future):** an LLM sketch author that sees **spec bytes only** — the
  goal's `subject: {ref, sha256}`, never surrounding prose — and proposes a
  tactic sketch. Untrusted-by-construction, exactly like every other LLM
  surface (ROADMAP/PLAN house rules). The sketch is a **proposal**; it
  authorizes nothing.
- **Exit teeth (named for the future package):** `tests/test_hammer_sketch.py`
  — spec-bytes-only isolation (the author cannot read prose), LLM-off SKIP path
  (no key → SKIPPED, green, the `bench/bench_speculate.py` skippable
  precedent), and a canned-transcript k=1 regression pinning (prompt,
  cache_key, event) sequences. Full suite green.
- **Bench (payoff):** the `results/hammer_readout` **delta** — did the H3
  queue's closure rate rise? Measured, **never asserted**: an LLM author that
  moves nothing is a recorded finding, not a failure.
- **Honesty:** a sketch is a proposal; only the kernel-adjudicated close (H4)
  means anything. The author never certifies and never rejects a goal the
  ladder would close.

---

## H4 — search closes leaves, kernel adjudicates

> **Implementation out of scope for this build.** Documented as the phase that
> turns H3 sketches into closed proofs.

- **Entry predicate (future):** H3 shipped (sketches authored for the refusal
  queue) and its readout committed.
- **Work (future):** a bounded search expands each sketch into leaves; the
  **unchanged kernel adjudicates** each candidate close through
  `LeanBackend.elaborate` + `LeanBackend.recheck` byte-identically to the
  kernel channel, fail-closed on audit silence — the same primitive
  `run/hammer_ride.py` already uses. Search **proposes**; the kernel is the only
  thing that closes.
- **Exit teeth (named):** `tests/test_hammer_search.py` — determinism of the
  leaf expansion, and a proof that a search "win" the kernel refuses is
  **discarded, never scored around** (the H35 entailment-gate-overrides-Occam
  discipline of `PLAN_ZONE3_CYCLES.md` Z3-08, one level up). Full suite green.
- **Bench (payoff):** `results/hammer_readout` — proof-cert closures split from
  statement-cert closures (the second lane step of `nothing → statement-cert →
  proof-cert`). Measured, not asserted.
- **Honesty:** this is where the **second lane step** is minted — and only with
  the **real** F2.1/F2.2 fidelity channels, never the `lean-smoke` stubs (the
  smoke-mint caveat above).

---

## H5 — proof-aware economics = definition-ladder L3

> **Implementation out of scope for this build.** Documented as the phase that
> feeds proof outcomes back into the economy.

- **Entry predicate (future):** H4 shipped (kernel-adjudicated closes committed)
  and a stable readout across ≥2 rides.
- **Work (future):** promote closure evidence to **definition-ladder rung L3** —
  proof-aware economics, where the measured cost/close of a vocabulary item
  informs the purchase queue (PLAN_FRAGMENT §4) the way the census miss
  histogram already does. This **prices** proof effort; it never grows a trust
  root (CLAUDE.md invariant — trust roots never grow by economics; PLAN_FRAGMENT
  §4 P5 is the worked refusal).
- **Exit teeth (named):** `tests/test_hammer_economics.py` — the L3 score is a
  *reported* series, verified divergent from any trust-root decision (the Z2
  "exact objectives first" discipline); no L3 number ever gates an admission.
  Full suite green.
- **Bench (payoff):** the proof-aware cost series in `results/hammer_readout`
  cross-referenced with `tools/cycle_telemetry.py` lane aggregates. Measured,
  never asserted to pay.
- **Honesty:** economics **prices**, it never certifies; L3 is proposal-grade
  input to a human-gated purchase, exactly like the census price list.

---

## Deferred packages (named, not folded into the phases)

### H-D0 — the import-RT ASCII probe repair (source-(b) demand)

- **Entry predicate:** `results/import_rt_report.json` carries the four
  `infra-refused` rows (`summary.by_verdict.failed == 4`).
- **Work (deferred, SEPARATE from this build):** repair `run/import_rt.py`'s
  probes so the math actually runs — render the `defeq` probe without the
  field-notation form that trips `invalid field notation`, and render the `iff`
  rungs in **ASCII** so the escape-gate does not refuse `U+2115` (`ℕ`). This is
  a **gate/probe-surface repair**, not proof search — it converts four
  infrastructure refusals into real elaboration attempts (which may then close
  or honestly refuse on the *math*).
- **Exit teeth:** `tests/test_import_rt.py` extended with a node proving the
  repaired probes render ASCII-only and clear the escape-gate; the four rows
  re-probe with a real verdict. Full suite green.
- **Honesty:** until repaired, the four rows stay `infra-refused` in the queue
  and are **never batched** — an infra refusal is gate demand, never proof
  demand. This package is explicitly **out of scope for the current hammer
  build** (contract "Out of scope").

---

## Package count per phase

```
H0:  H-H0.1                                    (1)
H1:  H-H1.1 (assemble) → H-H1.2 (ride+consume) (2)
H2:  H-H2.0 (near-free pre-read) → H-H2.1      (2)
H3:  H-H3   (LLM sketch author)                (1, implementation deferred)
H4:  H-H4   (search + kernel adjudicates)      (1, implementation deferred)
H5:  H-H5   (proof-aware economics = L3)        (1, implementation deferred)
Deferred:  H-D0 (import-RT ASCII probe repair)  (1, out of scope)
```

**Buildable now (H0–H2): 5 packages.** **Documented-future (H3–H5): 3
packages.** **Deferred/out-of-scope: 1 package (H-D0).** Total **9**.

Critical path: `H-H0.1 → H-H1.1 → H-H1.2 → H-H2.0 → H-H2.1`, then the H3 gate
(`rung-0/1 readout committed and read`) opens the documented-future phases.
Every arrow is a green, shippable boundary; full suite green is the exit tooth
of each node; the Lean-touching half rides the lane last.

---

## Where the plan is bounded by the tree (named, not papered over)

1. **The queue/bench/lane artifacts do not yet exist on this branch.**
   `results/proof_queue.json`, `results/hammer_batch.json`,
   `results/hammer_verdicts.json`, `results/hammer_readout.{json,md}`,
   `bench/bench_hammer.py`, `run/hammer_ride.py`, and
   `.github/workflows/lean-hammer.yml` are the **deliverables of the sibling
   workstreams** (queue-builder / bench+ride / integrator) — they are cited
   here as *targets*, with entry predicates and teeth named, not as existing
   files with line numbers. Only the machinery they REUSE is cited with
   line-verified references (`run/anchor.py`, `tools/flywheel_probe.py`,
   `generators/math_witness.py:98`, `kernel/certs.py:433`,
   `kernel/backends.py:724/784`, `ci.yml:14/411/553-556/617`,
   `tests/test_import_rt.py:129/207`, `tests/test_frontier.py`).

2. **The `67` denominator is the probe's, not the queue's.** The recorded H3
   prediction (`rung-0 closes ~20–30 of 67`) is measured by `flywheel_probe.py`
   over **grounded** props; the proof-goal queue is 3 anchor-exists + 66
   bench-certified − dedupe (41/42/44) + 4 infra-refused (not batched), scored
   as **unbounded** statements. The two numbers are near but not identical; the
   gap is stated, not reconciled by force — they measure different things
   (grounded instances vs unbounded statements).

3. **H3–H5 are documented, not built.** The contract scopes H3/H4/H5
   implementation and LLM tiers out. Their packages carry entry predicates,
   teeth, and benches so the driver knows the unlock conditions, but no code
   ships for them in this wave — stated rather than implied.

4. **Every hammer verdict is fidelity evidence, and the mint seam is
   smoke-stubbed.** `lean-smoke` green proves the mint *seam*, not a proof; a
   real mint needs the real F2.1/F2.2 channels. The plan cannot make the smoke
   job stand in for a real hammer close, and pretending otherwise would be
   dishonest — so H4's mint is gated on real fidelity channels, explicitly.
