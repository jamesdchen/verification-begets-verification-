# P5 shadow channel — S4a/S4a′ infrastructure (PLAN_FRAGMENT §4 P5)

**What §4 says, verbatim.** "**P5 — abstract algebra discharge route: TRUST
ROOT, NOT A PURCHASE.** A new rung (a group-tactic class) touches
`ANCHOR_DISCHARGE_RUNGS` (PINNED, kernel/certs.py, FI-KA-1/4). The ONLY
route: shadow channel beside the ladder → durable agreement ledger →
numeric entrance predicate → ONE-commit ceremony with explicit user sign-off
— the PLAN_REFLECT S4a→S4a′→S4b pattern verbatim. No queue entry may
shortcut this, whatever the census prices it at."

This cycle lays the **first two** of those four steps and stops there. The
ceremony is not in this diff and cannot be reached from it.

---

## What landed

**`run/algebra_shadow.py` — the paired channel.** One candidate route,
named honestly and singly: `algebra/ring_nf`. Not a tactic family, not an
alias set — the thing S4b would eventually be asked to pin is a single route
name, so the shadow measures exactly that one.

The tap point is **`results/proof_queue.json`**, read strictly read-only:
the committed, subject-hash-keyed worklist is the only stream in this repo
that actually reaches goals (112 rows; families linear/dvd/parity/gcd/exists;
every row carries a `rung_hint`). For each *queued* row whose family is
ring-shaped, the channel rebuilds the goal's own proposition from the
committed reading behind its `subject` — through the **compiler's own**
emitted statement, never a re-rendering — and emits

    set_option maxHeartbeats 400000 in
    example : <the goal's own proposition> := by ring_nf

The subject hash is **recomputed and compared** against the queue's pinned
`subject.sha256` *before* a probe is built. A probe therefore cannot assert
anything other than the goal the incumbent ladder is being measured on; a
drift is recorded staleness (a named skip), never a silently re-aimed probe.

**The measured sweep over the committed queue** (Lean-free, deterministic,
byte-stable across rebuilds):

| rows | outcome |
|---|---|
| **49** | probes built and escape-gate-clean (`linear`, 49 distinct subject hashes) |
| 26 | `family-not-algebra:dvd` |
| 19 | `family-not-algebra:parity` |
| 7 | `family-not-algebra:gcd` |
| 6 | `family-not-algebra:exists` |
| 4 | `route-not-applicable:status-infra-refused` |
| 1 | `route-not-applicable:status-shadow-refuted-excluded` |

Every non-probe row is a **named** skip from a frozen vocabulary declared in
the module docstring and pinned as a tuple (`SKIP_PREFIXES`) the teeth
assert against — a skip is never a failure, and it is never anonymous
either. The families a ring/group-normalization route cannot reach are
declined, not widened into: measuring the wrong class would manufacture
agreement rows that mean nothing.

**Ledger discipline (S4a′(i)).** `append_ledger(path, rows, lane_run_id,
module_sha)` appends canonical-JSON rows — the `_Ledger` convention, so any
prior content stays a **byte-prefix** of the new file and there is no
truncate or rewrite path. Skips never reach the ledger. Every row carries
the route, the `run_attempt` (a workflow re-run under the same
`lane_run_id` stays distinguishable instead of silently inflating counts),
the probe sha, and — on disagreement only — the root cause.

**Root causes are classified from the transcript, never guessed.** Two
explained classes: a deterministic budget timeout, and the candidate tactic
being **unreachable under the pinned narrow import set**
(`common.MATHLIB_IMPORTS`, ⚠D15). Anything else stays `unexplained`, so the
entrance predicate can never be satisfied by an unread failure.

**Entrance predicate as executable teeth (S4a′(ii)).** The reflection
channel's numeric thresholds are mirrored here — ≥25 agreements, ≥3 distinct
lane runs, ≥8 distinct statement hashes, **zero** unexplained disagreements
— measured from the ledger alone, in `tests/test_algebra_shadow.py`, *from
day one, before a single row exists*. The house rule is that no
done-condition may live only as prose; the test skips honestly
("algebra agreement ledger not yet seeded (needs a lane run)") until the
evidence store exists, and it turns red the instant the numbers are claimed
without being met. Meeting them is **necessary, never sufficient**: S4b
additionally requires explicit maintainer sign-off.

**Teeth.**
`tests/test_algebra_shadow.py` — the pins asserted and the module grepped
(`ANCHOR_CERT_CHANNELS` / `ANCHOR_DISCHARGE_RUNGS` / `ANCHOR_LIVE_DISCHARGES`
appear **only** in its docstring, and the module imports no cert surface);
probe determinism + escape-gate cleanliness; the frozen skip vocabulary,
cross-checked against the docstring so prose and code cannot drift; the
sweep sourced from the committed queue alone (zero fixture-sourced rows);
the queue verified byte-unchanged by a sweep; append-only-by-bytes; the
deferred sweep writing **no** ledger; a stub backend refusing everything, so
a planted failure is recorded as disagreement, never laundered into
agreement; both explained refusal classes planted and classified; the
discharge record byte-stable, route-qualified and tamper-evident under
replay; and planted staleness declining instead of re-aiming.

`tests/test_algebra_parity.py` — the S4b-readiness gap. Agreement must mean
"the probe asserts the RIGHT proposition", not merely "the probe
elaborated". The proposition is read back **out** of the emitted probe by an
independent slicer and compared, modulo whitespace only, against the
compiler's proposition for the reading behind the row's subject — whose
sha256 is the queue's own pinned `subject.sha256`, so the chain closes on a
committed hash rather than on a re-run of the builder's own code. Three
plants must red it: a substituted (true but different) proposition, a
single swapped operator, and a probe re-aimed at another queued goal.

---

## What is explicitly NOT here (honest scope)

1. **No CI sweep step.** `.github/` is ceremony scope, and nothing in this
   diff touches it. The channel therefore has no lane wiring: it is a module
   plus its teeth. Wiring the sweep step is the **user-gated next action**.
2. **The ledger is unseeded.** `results/algebra_agreement.jsonl` does not
   exist and is deliberately not created — rows may only ever come from a
   real lane run, and a locally fabricated seed would be exactly the
   evidence-laundering the shadow pattern exists to prevent. Every
   ledger-measured tooth skips by name until then.
3. **No kernel, cert or TRUST.md edit.** `ANCHOR_DISCHARGE_RUNGS` is
   untouched and asserted untouched. The dependency points one way, as it
   does for the reflection channel: nothing here reads or imports a cert
   surface.
4. **Elaboration is deferred, not claimed.** No local Lean in remote
   containers, so the probes are BUILT and gate-validated and the sweep
   reports `deferred: lean toolchain absent` verbatim, writing nothing.
   The first honest agreement number is a lane fact this cycle does not own.
5. **No import widening.** `ring_nf` is not on the escape-gate blocklist
   (verified through `validate_lean` on every probe), but whether it is
   *reachable* under the pinned narrow import set is a separate, measurable
   question this cycle does not answer by editing `common.MATHLIB_IMPORTS`.
   If the first lane run reports it unreachable, that is a first-class
   recorded disagreement with the named root cause
   `tactic-unavailable-under-pinned-imports` — demand for an import decision
   in a later cycle, never a quiet widening now.
6. **S4b is out of scope, by construction.** Promotion needs the full ledger
   evidence *and* explicit user sign-off in a single ceremony commit
   (PLAN_REFLECT S4b). No amount of accumulated agreement promotes anything
   on its own, and no census price shortcuts it — that is what "TRUST ROOT,
   NOT A PURCHASE" means.
