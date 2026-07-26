# The availability gate: built, not merely unpacked

**Receipt for the 2026-07-26 purchase firing that yielded.**  It has three
parts, and the later ones correct the earlier ones.  Read all three before
touching `common.lean_available()` again.

1. **#176** widened the gate to accept the pinned toolchain the jail actually
   mounts.  The OBSERVATION was right; the PREMISE was wrong.
2. **#182** (another session, same day) read the fallout as SLOWNESS and added
   `CGB_LEAN=0` as a force-off for the per-commit gate.
3. **This change** fixes what both missed: the driver image's Mathlib is only
   PARTLY BUILT, so the widened gate produced **50 real FAILURES**, not merely
   a slow suite — and `CGB_LEAN=0` did not in fact protect the capability
   classification the way #182's own comment promised.

## What stays right

`kernel.backends.LeanBackend` never consults the host `PATH`.  `_lean_run_kw`
puts the jail mount of `LEAN_TOOLCHAIN_DIR` on the in-jail `PATH`, and all
seven cert-time `sb.run(["lean", …])` sites resolve from there.  Observed live
in this session's process table:

    mount --bind '/opt/cgb-lean/mathlib' /ro/mathlib
    mount --bind '/root/.elan/toolchains/leanprover--lean4---v4.15.0' /ro/toolchain
    env -i PATH=/ro/toolchain/bin:/usr/bin:/bin:/usr/local/bin … lean CgbScratch.lean

So a `which("lean")` gate really does ask about a directory the backend does
not use.  That part of #176 is kept.

## What was wrong: presence is not capability

The image ships a `.setup-sentinel` byte-equal to `.lean-pins`, a built
`Mathlib.olean`, a built `lean4checker`, and a working `lean 4.15.0`.  A
trivial theorem elaborates.  `run/reflect_shadow.py` agrees 18/18.  Both teeth
that *require* real elaboration pass.

**That is exactly why the spot checks passed and the conclusion was still
wrong.**  The dependency closure is not built:

| package | `.lake/build/lib` |
|---|---|
| `plausible` | **absent entirely** |
| `Cli`, `importGraph`, `proofwidgets` | present, 0 oleans |
| `batteries`, `aesop`, `Qq`, `LeanSearchClient` | 1 olean each |

So anything pulling `Mathlib.Tactic.NormNum`'s transitive closure dies:

    elaboration (run 1) did not build: CgbScratch.lean:1:0:
    error: unknown module prefix 'Plausible'

Measured, full suite in a driver container:

| state | result |
|---|---|
| gate narrow | **1777 passed, 41 skipped — 49 s** |
| gate widened (#176+#177 in main) | **50 failed, 1715 passed, 51 skipped — 1279 s** |

Failures: `test_statement_cert.py`, `test_t6b_predecessor_int.py`,
`test_speculate_math.py` and others — all Lean-gated, all on the missing
closure, none a defect in the code under test.  **#176 took the loop from
blocked-but-green to blocked-AND-RED**, which is strictly worse: a driver may
not commit on a red suite.

**CI cannot see any of it.**  Its default runner is Lean-absent, so the gate
stays False and CI stays green; its dedicated `lean` job builds Mathlib
properly via `setup.sh`.  The breakage lived only in driver sessions.

## The fix: ask whether the installation is BUILT

`_mathlib_build_complete` takes its predicate from the MECHANISM rather than
from a guess.  `LeanBackend._lean_path` builds the in-jail `LEAN_PATH` out of
Mathlib's own `.lake/build/lib` plus one entry per materialized package under
`.lake/packages/<pkg>/.lake/build/lib`.  If any entry it would add is missing,
the closure cannot resolve and the installation is not one a caller may treat
as available.  A stat per package; honest in both directions, since a complete
build has every one of those directories.

Still presence, not proof: it cannot tell a stale olean from a fresh one, and
the CI Lean lane remains the done-predicate.

## The second defect, in #182's own terms

#182 added `CGB_LEAN=0` as a suite knob and justified it with:

> the CAPABILITY classification reads `tools/lean_env_probe.py`, which checks
> the mounted directories itself and never consults this function.

**That was not true, and its tooth could not see it.**  The probe did:

    avail = common.lean_available if lean_available is None else lean_available
    ...
    "lean_available": bool(avail()),

`common.lean_available` is bound as an ATTRIBUTE on one line and called as
`avail()` on the next.  #182's tooth walked only `ast.Call` nodes and collected
`n.func.attr` / `n.func.id`, so neither node is a call named `lean_available`
— the tooth passed while the probe did exactly what it forbids.  A
gate-masking knob plus a tooth that cannot see the masking is the worse pair.

Closed by making the separation MECHANICAL rather than promised:

* `toolchain_present()` — the override-FREE capability reading, which is what
  the probe now uses and what rule 3 classifies on.
* `lean_available()` — the SUITE gate, which honours `CGB_LEAN` as #182
  intended.
* The tooth now looks for `common.<attr>` references specifically, and also
  ASSERTS the probe reaches `toolchain_present`, so the separation cannot rot
  into decoration.

So #182's intent is preserved and now actually holds: a session may run its
per-commit gate with `CGB_LEAN=0` without talking itself out of a capability
it has — or into one it does not.

## The standing conclusion for the loop

The env-var asymmetry (#177), the PATH asymmetry (#176) and the suite knob
(#182) are all real, and **none of them unblocks this loop**, because the
blocker underneath is the IMAGE: `/opt/cgb-lean/mathlib` is not a complete
build.  Until it ships one, `lean-absent` is the TRUE reading of these
containers and rule 3's YIELD is correct rather than merely conservative.
That is an image/provisioning fix, not a repo fix.

## Teeth

* `test_an_unbuilt_package_closure_is_not_availability` — the image's exact
  shape (package materialized, never built) reads False.
* `test_a_complete_build_is_still_availability` — the other direction, so this
  cannot degenerate into "always False" and disable a real host.
* `test_mathlib_without_its_own_build_lib_is_not_complete`.
* `test_the_capability_reading_ignores_the_suite_knob` — `CGB_LEAN=0` moves the
  gate and NOT the capability.
* `test_the_probe_does_not_consult_the_gate` — strengthened as above.

Mutation-verified both directions: dropping the completeness clause reds the
first; pointing the probe back at `lean_available` reds the last.

## What this firing did NOT do, and why

**No purchase.**  `purchase_frontier`: 13 rows, 3 open, 0 ready; no open row
additive-class.  At rule 3's classification point the probe verdict this
session had RUN was `lean-absent:not-installed`, so the YIELD was correct and
total — and correct for a second reason it did not know at the time.

**No authoring ride.**  Re-checked, not assumed: no open `C3 authoring…` PR to
consume, and PLAN_FRAGMENT §1 records the channel OUT OF ROUNDS on all three
open rows against their own committed class measurements.

## Bounds held

* No ceremony-reserved surface touched; `kernel/backends.py` read, never
  edited.
* `tools/FgReflect.lean` and `results/reflect_candidates.json` untouched.
* P5 not promoted; the anti-list unchanged.
* No probe artifact edited to flatter a fix.
