# C3 cycle 35 — the fresh-recertification lane is dead on arrival, and the
# step that killed it says in its own comment that it never could

**Product of this cycle: a diagnosis, and a maintainer handoff.**  Zero
certifications, zero intakes, corpus unchanged at **125** sources / 8 corpora
(2132 nodes), every DL byte-identical, no lineage entry, ready stays 0.  No
refusal and no park recorded — nothing here is a reading about a corpus
subject.

## The supply half, first and briefly

`NEXT-SELECTION: refill`.  Path (c) was tried, and it is the only lever a
corpus driver can reach unattended:

```
$ python3 tools/corpus_candidates.py
reason: registry-exhausted  (every declared row is already intaken, refused,
or documentation -- the loop consumed the list.  UNBLOCKED BY: a maintainer
appending one row (name, source, adapter, project, declared_by, rationale))
declared: candidate=0, example=1, intaken=8, refused=2
SELECTED: none -- path (c) has nothing declared to take.
```

The fallback the prompt allows — a corpus the maintainer has NAMED — has no
source this firing: **no routine-fire-payload accompanied this firing, the
open-issue list is empty (`totalCount: 0`), and PLAN_FRAGMENT §1 names none**
(it says the opposite in as many words: *"Until one is declared, every corpus
firing will guard-pass, find no ready entry, no met refusal group and no
declared candidate, and exit"*).  So path (c) is unavailable, exactly as
cycle 34 left it, and the standing demand is unchanged: the largest `refused:`
groups carry **77 distinct subjects**, and retiring one of their signals is a
PURCHASE-axis call, not this loop's.

That is the whole supply reading, and on its own this firing would have been a
one-line exit.  The lane verdict is what made it a cycle.

## The finding: `lean-fresh` has never once run since 2026-07-26

The lane-verdict-first step read the newest CI on `main` and found the
scheduled `regression` run **30251284819** RED — while every Lean lane job in
the same run was GREEN:

| job | conclusion |
|---|---|
| `lean (a)` | success (incl. the S4a′ reflect-shadow sweep) |
| `lean (b)` | success |
| `lean-smoke` | success |
| `fast` × 7 shards | success |
| **`lean-fresh`** | **failure — 19 seconds** |

Nineteen seconds is not a certification failing.  It is the job dying before
it certifies anything:

```
>> [--with-lean] Lean 4 + pinned Mathlib (F0.1)
>> elan (Lean toolchain manager)
>> clone Mathlib @ 9837ca9d65d9de6fad1ef4381750ca688774e608
HEAD is now at 9837ca9d65 chore: bot validates lean-toolchain on bump/v4.X.0 branches
error: 'leanprover/lean4:v4.15.0' is already installed
##[error]Process completed with exit code 1.
```

### Reproduced, not inferred

`elan toolchain install` on an already-installed toolchain is an **error**,
not a no-op.  Run in this container against the same pin:

```
$ elan toolchain install leanprover/lean4:v4.15.0
error: 'leanprover/lean4:v4.15.0' is already installed
EXIT=1
```

`setup.sh` runs under `set -e`, so `setup.sh:116` — a bare
`elan toolchain install "$LEAN_TOOLCHAIN"` — takes the whole script down.

### Why this job and only this job

Two facts have to meet, and they only meet here:

1. **`lean-fresh` is the one job that omits `--skip-fresh`.**  Every other
   Lean job runs `bash setup.sh --with-lean --lean-only --skip-fresh`
   (`ci.yml:178`, `:509`, …); `lean-fresh` runs it without
   (`ci.yml:402-406`), because a fresh recertification must never be skipped.
2. **The sentinel fast path is gated on `--skip-fresh`.**  `setup.sh:81`
   requires `" $* " == *" --skip-fresh "*` before it will short-circuit the
   clone/elan/lake block.

So every `--skip-fresh` job takes the fast path and never reaches line 116,
while `lean-fresh` always falls through to it — and since the
**"Prime the Lean toolchain from the per-pin image"** step (`ci.yml:363`,
landed 2026-07-26 in `74740c5`) does `rm -rf "$HOME/.elan"` and then
`docker cp leanprime:/opt/lean-cache/elan "$HOME/.elan"`, the toolchain is
*always already installed* by the time line 116 runs.

**The prime step's own comment states the invariant it breaks:**

> `setup.sh`'s sentinel fast path makes the primed state a no-op re-setup; the
> fresh recertification (lean-fresh) still runs in full — the image only ever
> replaces the FETCH, never a check.

Both clauses are false for `lean-fresh`, and for the same reason: the fast
path it relies on is unreachable without `--skip-fresh`.  The primed state is
not a no-op re-setup, it is a hard failure; and the image did not replace a
fetch, it removed a check.

### How long, and how much is unpaid

The prime step landed 2026-07-26 01:20:14 -0700 (`74740c5`).  `lean-fresh`
fires on `schedule`, `workflow_dispatch`, or a push carrying the
`[lean-fresh]` marker; **there have been no `workflow_dispatch` runs of
`ci.yml` since 2026-07-23**, so run 30251284819 (2026-07-27T08:48:00Z) is the
first `lean-fresh` execution after the step landed — and it failed.  The
scheduled slot is weekly (`cron: "17 5 * * 1"`), so unrepaired this is a
**once-a-week** miss that reports as a red `regression` run nobody is obliged
to read.

What goes unpaid is not cosmetic: `lean-fresh` is the ⚠L4 discharge — the
scheduled run pays the **whole-library replay** through `lean4checker`, and
dispatch/marker runs pay the import-surface scope.  The failure is *before*
any of it, so the discharge ledger (`.lean/fresh_discharged.txt`) gains
nothing.  The cache-save step still runs (`if: always()`-shaped ordering), so
the empty ledger is faithfully persisted — the artifact is honest, there is
simply no payment in it.

**A green `regression` on a PR does not carry this.**  `lean-fresh` is gated
off for `pull_request` events entirely (`ci.yml:337-341` admits only
`workflow_dispatch`, `schedule`, and `[lean-fresh]` pushes), which is why the
loop has been merging fully-green PRs for a day with a dead recertification
lane behind them.

## Why this cycle did not fix it, and must not have

The fix is one line and it is obvious — make the install idempotent, e.g.
guard on `elan toolchain list` or accept the already-installed exit.  **Every
surface that could carry it is ceremony-reserved:**

| candidate site | surface |
|---|---|
| `setup.sh:116` (the failing call) | `setup.sh` — reserved |
| `ci.yml:363` (the prime step) | `.github/` — reserved |
| `ci/Dockerfile.lean` (bake without installing) | `ci/` — reserved |

`trust-surface` fails any diff touching those, by design, and the driver
prompt is unambiguous: never self-merge on a red or missing `trust-surface`,
and never improvise around one.  This is the fence working — the Lean
bootstrap is exactly the thing an unattended session should not be editing —
so the honest product is the diagnosis and the handoff, not a patch that
could never land.

**The tooth is blocked for the same reason, and that is worth stating
plainly.**  The natural fence here is a source-inspecting tooth asserting that
the fresh path's `elan` install tolerates a pre-installed toolchain.  It
cannot ship in this PR: it would red the gate immediately, because the defect
it pins is live at `main` and the fix is on a surface this session may not
touch.  Fix and tooth are coupled and must land together, by maintainer.  The
lesson is therefore recorded prose-only with that reason declared, per the
declare-or-red ratchet.

## What the maintainer is being handed

1. Make `setup.sh:116` idempotent (the one-line fix), **or** drop the
   toolchain out of the primed payload so the fresh path installs it itself.
2. Land the fence with it — a tooth that reds if the fresh path can be killed
   by a pre-installed toolchain again.
3. Re-run `lean-fresh` (workflow_dispatch, or a `[lean-fresh]` push) to
   confirm the whole-library replay actually starts, rather than waiting a
   week for the cron to say so.

Independent of that, path (c) still needs **one appended row** in
`specs/mathsources/corpus_candidates.json` — and cycle 34's finding stands
about it: the URL is worth verifying at declaration time, since the loop's
only verifier is the driver's own fetch, at one cycle per miss.

## Bounds

No ceremony-reserved surface in this diff — `kernel/certs.py`, `TRUST.md`,
`buildloop/growth_protocol.py`, `buildloop/validate_lean.py`, `setup.sh`,
`ci/`, `.claude/`, `.github/` all untouched; they were **read**, never edited.
`tools/FgReflect.lean` byte-unchanged.  P5 not promoted.  No refusal recorded
and no park recorded or lifted — a CI regression is not a reading about a
corpus subject, and filing one as demand data would be exactly the distortion
the honesty rules forbid.  Ledgers append-only.  No purchase priced, so no
flywheel slot spent and no re-census delta owed.  Lean-free.

**Gate**: `CGB_LEAN=0 python3 -m pytest tests/ -q`.
