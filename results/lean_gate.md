# The availability gate asked about a directory the jail never uses

**Receipt for the 2026-07-26 purchase firing that yielded (PR from branch
`claude/adoring-meitner-mh1tqk`).**  Product: the SECOND of two mechanical
env-resolution defects that together hold every driver container at
`lean-absent:not-installed`.  The first is the
`CGB_LEAN_MATHLIB` / `CGB_LEAN_MATHLIB_DIR` asymmetry, **merged as #177 while
this session was working** (PR #174 proposed the same fix and was closed in
its favour).  **Neither half is sufficient alone; the pair is.**

**Live state as of this rebase:** #177 is in `main`, so this container now
reads **`lean-local`** with this change and `lean-absent:not-installed`
without it.  The remaining half is the one in this PR.

## The reading that started it

`python3 tools/lean_env_probe.py`, RUN in this container per PLAN_FRAGMENT
§3.1 rule 3, printed:

    lean-absent:not-installed

whose own pinned gloss is *"absent, hosts answer; setup was never run"*.  That
is false about this container.  Setup **was** run — by the image provisioner:

| artifact | state |
|---|---|
| `/opt/cgb-lean/mathlib/.lake/build/lib/Mathlib.olean` | built |
| `/opt/cgb-lean/lean4checker` | built |
| `/opt/cgb-lean/.setup-sentinel` | `9837ca9d…\|leanprover/lean4:v4.15.0` — **byte-equal to `.lean-pins`** |
| `/root/.elan/toolchains/leanprover--lean4---v4.15.0/bin/lean` | present, executable, `Lean (version 4.15.0, … 11651562caae, Release)` |
| all six required egress hosts | `gateway answered 200 to CONNECT` |

A trivial elaboration through that binary returns
`'t' depends on axioms: [propext]`.  The toolchain is real and it is the
pinned one.

## The defect: the gate and the resolver name different directories

`kernel.backends.LeanBackend` **never consults the host `PATH`**.  Its
`_lean_run_kw` puts the jail mount of `LEAN_TOOLCHAIN_DIR` on the in-jail
`PATH`:

    return {"extra_path": (self._RO_TOOLCHAIN + "/bin",), ...}   # /ro/toolchain

and every cert-time invocation (`sb.run(["lean", …])`, seven call sites)
resolves from there.  But the gate every one of those call sites passes
through first —

    def elaborate(self, lean_text, *, expect_sorry):
        if not common.lean_available():
            return self._unavailable(...)

— was:

    return bool(shutil.which("lake") or shutil.which("lean"))   # HOST PATH

So the gate measured a directory the backend does not use.  An image that
installs the pinned toolchain **exactly where the constant says** and does not
also export it on `PATH` is fully capable and reads as *"setup was never
run"* — the one verdict rule 3's YIELD clause fires on.  Capable container,
yielding driver, on every unattended firing.

This is the same shape as #174's defect: **the provisioner followed the
constant, the reader looked somewhere else.**  #174 found it between two env
var spellings; this is the same asymmetry between a constant and `PATH`.

## The 2×2, measured — not argued

Four probe runs in this container, one per combination:

| this fix | the mathlib fix (#177) | probe verdict |
|---|---|---|
| — | — | `lean-absent:not-installed` ← the reading this firing started from |
| — | ✓ | `lean-absent:not-installed` ← **unchanged: the mathlib half alone does NOT unblock this container** — and this is now `main` |
| ✓ | — | `lean-unknown:lean-on-path-but-unmounted:mathlib` (still a yield) |
| ✓ | ✓ | **`lean-local`** ← verified after rebasing onto `main`, with no env override |

The second row is the load-bearing one and it is why this receipt exists.
#177 merged mid-session on the reasonable belief that it unblocked the loop;
it did not, because its authoring container had `lean` on `PATH` and the
driver containers do not.  Measured directly: on `main` at `b36af99`, before
this change, `tools/lean_env_probe.py` still printed
`lean-absent:not-installed` here — and after it, `lean-local`.

## The fix, and the clause that makes it safe to land alone

`lean_available()` gains a third way — the **whole mountable installation**
`_lean_mounts` needs, not merely a binary:

    pinned = os.path.join(LEAN_TOOLCHAIN_DIR, "bin", "lean")
    return (os.path.isfile(pinned) and os.access(pinned, os.X_OK)
            and os.path.isdir(LEAN_MATHLIB_DIR))

Demanding **both** directories is deliberate and was arrived at by
measurement, not taste.  An earlier draft flipped on the binary alone; that
reports capability in the half-installed state, where `_lean_mounts` cannot
mount Mathlib, and **9 teeth went red** across `test_anchor_runner.py` (6),
`test_reflect_ride.py` (2) and `test_import_rt.py` (1) — Lean-gated tests
newly executing against an installation the jail cannot assemble.  Worse, that
breakage would have been **invisible to CI** (whose runner has no
`~/.elan/toolchains/…`) and real in every driver session.

With the mathlib half unresolved, this clause is **inert**: it returns False,
the verdict stays `lean-absent:not-installed`, and the suite is byte-for-byte
unaffected.  That property was what made it safe to ship before #177 landed;
now that #177 IS in `main`, the clause is live and the container reads
`lean-local`.  The PATH branch is untouched, so the probe's
`lean-on-path-but-unmounted:…` vocabulary stays reachable — that verdict is a
true reading of a true half-installation and this clause neither produces nor
suppresses it.

## Teeth (5, all mutation-verified)

In `tests/test_lean_env_probe.py`, beside #177's three:

1. `test_pinned_toolchain_counts_as_available_without_it_being_on_path` — the
   defect as its consequence.
2. `test_a_toolchain_without_mathlib_is_not_available` — the safe-alone clause.
3. `test_no_toolchain_invents_no_availability` — the honest-absence floor.
4. `test_a_non_executable_lean_is_not_a_toolchain` — presence ≠ capability.
5. `test_the_gate_names_the_same_bin_the_jail_puts_on_its_path` — the
   ANTI-DRIFT tooth, and the only one that would have caught this **before** a
   container met it: the gate and `_lean_run_kw` must keep naming the same
   `bin`.

Mutation-verified twice, both directions: reverting the branch to the pre-fix
`return False` reds teeth 1 and 5; weakening it to binary-only reds tooth 2.

## What this firing did NOT do, and why

**No purchase.**  `purchase_frontier`: 13 rows, 3 open, 0 ready; not one open
row is additive-class.  At the moment this session reached rule 3's
classification point, the probe verdict it had RUN was
`lean-absent:not-installed`, so the YIELD was correct and total.  This fix is
the firing's **product, not a licence it held while working** — the same
reasoning #174 states, and it binds identically here.  A tower-class bill
started on a capability measured minutes earlier is a bill this session cannot
finish.

**No authoring ride.**  The yield's fallback is empty and was re-checked, not
assumed: no open `C3 authoring…` PR (nothing to consume), and PLAN_FRAGMENT §1
records the channel OUT OF ROUNDS on all three open rows against their own
committed class measurements (`results/reflect_channel_exhausted.md`).  The
committed `results/reflect_candidates.json` holds one candidate,
`p9-parallel-tower-r2`, whose verdict row is `passed: true` with
`declared_missing: []`.  Extending it needs a class measurement naming a
construct no prototype has taken, which §1 states is not an unattended
session's to manufacture.

So the honest product of a firing with both exits closed is **the reason the
exits are closed** — and it turns out that reason is two lines of env
resolution, not a governance limit.

## Bounds held

* No ceremony-reserved surface touched (`kernel/certs.py`, `TRUST.md`,
  `buildloop/growth_protocol.py`, `setup.sh`, `ci/`, `.claude/`, `.github/`);
  `kernel/backends.py` is READ, never edited.
* `tools/FgReflect.lean` and `results/reflect_candidates.json` untouched.
* P5 not promoted; the anti-list unchanged.
* Presence, never proof: a local green remains NECESSARY and never SUFFICIENT,
  and the CI Lean lane stays the done-predicate.
* The committed `results/lean_env.json` still records this container's TRUE
  reading under the shipped code (`lean-absent:not-installed`) — the artifact
  is a reading of the container that wrote it and was not edited to flatter
  the fix.
