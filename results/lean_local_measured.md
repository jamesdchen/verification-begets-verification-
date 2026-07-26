# The driver containers are `lean-local`, and one variable name is why no firing could see it

*(a purchase-driver firing that found the in-flight guard clear, RAN the probe
per §3.1 rule 3, and read a verdict nobody had read before — then found the
verdict was wrong about a container that had been Lean-capable the whole time)*

## The reading that started it

`python3 tools/lean_env_probe.py`, RUN this session and never read off disk,
printed a verdict the tree had never recorded:

    lean-unknown:lean-on-path-but-unmounted:mathlib

Not `lean-absent:policy-denied:<hosts>` (the state
`docs/lean-capable-environment.md` documents as current), and not
`lean-absent:not-installed` (what the previous firing read, PR #169). A THIRD
shape, and the probe's own vocabulary says what it means: `lean` answers at the
pinned toolchain, and one of the two directories
`kernel.backends.LeanBackend._lean_mounts` would mount is missing.

Two halves of the same document made that reading impossible to leave alone:

| field | value |
|---|---|
| `toolchain.toolchain_dir_present` | **true** — `/root/.elan/toolchains/leanprover--lean4---v4.15.0` |
| `toolchain.lean4checker_dir_present` | **true** — `/opt/cgb-lean/lean4checker` |
| `toolchain.mathlib_dir_present` | **false** — `<repo>/.lean/mathlib` |
| `hosts[*].state` | **all six `reachable`**, "gateway answered 200 to CONNECT" |
| `proxy.hosts_denied_in_status_ledger` | **[]** |

The runbook's premise is retired by that host table. It says in its own words
that `elan.lean-lang.org` and `release.lean-lang.org` answer **403 to CONNECT**,
that a 403 is an organization policy decision and never weather, and that no
re-run of `setup.sh --with-lean` can change it. **Today all six answer 200.**
The maintainer's network-policy exit was walked at some point before this
firing, and no session had measured it because every session reads the verdict
and stops at the word `unknown`.

And the second half is sharper still: `lean4checker` resolved onto
**`/opt/cgb-lean/lean4checker`**, a path that appears in no committed file.

## What was actually on the disk

    /opt/cgb-lean/.setup-sentinel   9837ca9d65d9de6fad1ef4381750ca688774e608|leanprover/lean4:v4.15.0
    /opt/cgb-lean/mathlib/.lake/build/lib/Mathlib.olean                      549648 bytes
    /opt/cgb-lean/lean4checker/.lake/build/bin/lean4checker              115349264 bytes

The sentinel is **byte-equal to `.lean-pins`** (`MATHLIB_COMMIT=9837ca9d…`,
`LEAN_TOOLCHAIN=leanprover/lean4:v4.15.0`). The image ships a complete,
pin-matching `--with-lean` install. The container was never un-Lean-capable.

And the environment says so:

    CGB_LEAN_MATHLIB_DIR=/opt/cgb-lean/mathlib
    CGB_LEAN4CHECKER_DIR=/opt/cgb-lean/lean4checker

## The defect, in one line

`common.py` had three overrides for three directories, and **one of them did not
follow the convention the other two teach**:

| constant | env name it read | image exports | resolved to |
|---|---|---|---|
| `LEAN_TOOLCHAIN_DIR` | `CGB_LEAN_TOOLCHAIN_DIR` | (derived) | the pinned toolchain ✓ |
| `LEAN4CHECKER_DIR` | `CGB_LEAN4CHECKER_DIR` | `CGB_LEAN4CHECKER_DIR` | `/opt/cgb-lean/lean4checker` ✓ |
| `LEAN_MATHLIB_DIR` | `CGB_LEAN_MATHLIB` | `CGB_LEAN_MATHLIB_DIR` | **`<repo>/.lean/mathlib`** ✗ |

The provisioner followed the `_DIR` convention. `LEAN_MATHLIB_DIR` was the one
name without the suffix, so it alone missed and fell back — **silently**, to a
path the image never populates. From there the chain is deterministic:
`_lean_mounts` cannot mount Mathlib → the probe reads
`lean-on-path-but-unmounted:mathlib` → PLAN_FRAGMENT §3.1 rule 3's YIELD clause
fires → every unattended purchase firing yields the bill → §1 records that
"every exit that remains is a maintainer's".

**The exit was not a maintainer's. It was a fallback that disagreed with its own
sibling and never said so.**

## The fix, and why it is additive

`common.py` accepts BOTH spellings, un-suffixed **primary**:

    LEAN_MATHLIB_DIR = os.environ.get(
        "CGB_LEAN_MATHLIB",
        os.environ.get(
            "CGB_LEAN_MATHLIB_DIR", str(REPO_ROOT / ".lean" / "mathlib")))

Nothing that works today changes meaning. CI sets neither name (checked: the
workflows set only `CGB_LEAN_TOOLCHAIN_DIR`), so CI keeps `setup.sh`'s
repo-local default exactly as before, and any caller already setting
`CGB_LEAN_MATHLIB` still wins.

Three teeth in `tests/test_lean_env_probe.py`, all mutation-verified against the
un-aliased line (the first two go red, the third is the anti-drift pin):

* `test_mathlib_dir_reads_both_spellings` — parametrized over both names.
* `test_the_un_suffixed_mathlib_spelling_stays_primary` — the alias is additive.
* `test_every_lean_directory_override_accepts_the_dir_spelling` — **the wedge was
  an ASYMMETRY between three variables naming the same kind of thing, not a typo
  in one of them**, so the tooth is over all three. The next image cannot land
  the same wedge one variable over.

## Capability PROVEN, not merely present

The probe measures PRESENCE and says so in its own honesty string, so presence
was not left as the claim. After the fix, from the container's own environment
with no override:

    python3 tools/lean_env_probe.py     ->  lean-local
    LeanBackend._lean_mounts()          ->  {'mathlib': '/opt/cgb-lean/mathlib',
                                             'toolchain': '/root/.elan/toolchains/
                                                           leanprover--lean4---v4.15.0'}
                                            why: ''            (was: mathlib missing)
    python3 run/reflect_shadow.py       ->  18 probes, verdicts={'agree': 18,
                                                                 'disagree': 0}

Every one of those 18 rows carries `elaborated: true` over a `module_sha` of the
committed slice, and `reflect_shadow` writes verdicts **only when Lean verdicts
were actually computed, never on a deferred sweep**. This container elaborated
the FgReflect slice against the pinned Mathlib, locally, this session.

## What this firing did NOT do, and why

**No purchase.** `python3 tools/purchase_frontier.py`: 13 rows, 3 open, 0 ready.
The three open rows are `refusal-symbolic-exponent` (iteration-class),
`refusal-function-symbol` (definitional-extension) and `refusal-set-carrier`
(tower-class) — **not one is additive-class**, so at the moment this session
reached §3.1 rule 3's classification point the probe verdict it had was
`lean-unknown` and the YIELD was correct and total. The fix that turns that
verdict into `lean-local` is the product of this firing, not a licence it held
while working. Taking a multi-hour tower-class bill on a capability measured
minutes earlier would be starting a purchase this session cannot finish, and a
half-paid bill is worse than a yielded one.

The honest ordering, stated so the next firing does not re-derive it: **merge
this, and the next purchase firing runs the probe, reads `lean-local`, and rule
3's YIELD clause does not fire** — the first unattended tower-class work this
loop has ever been able to take. `results/reflect_channel_exhausted.md` stays
true and stops mattering: the authoring ride is the second route rule 3 names
for a policy-denied container, and this container is not one.

**No authoring round.** Step (1) CONSUME: `list_pull_requests(state=open)`
returned this session's own claim and nothing else — no open `C3 authoring ...`
PR, the single-slot channel is free, nothing to consume. Step (2) AUTHOR: the
three open rows' queues are terminal on their own committed class measurements
(`tests/test_symbolic_exponent_class.py`, `tests/test_function_symbol_class.py`
finding (4), `results/c3_cycle_16.md` line 93), re-verified against
`results/reflect_channel_exhausted.md`'s table. Step (3) RIDE: nothing to ride.
The route is unchanged and is now beside the point.

**No purchase title.** This buys no fragment growth and spends no flywheel slot,
so it must stay invisible to the one-per-cycle in-flight guard — the same
reasoning that keeps an authoring ride off the `C3 purchase` prefix. It is not
an authoring ride either, so it carries neither prefix and claims neither lane.

## The full-suite gate, and the SECOND finding it exposed — stated plainly

**The suite gate is NOT green for this commit, and it is not green at `main`
either.** Saying that first, because the protocol says full suite before every
commit and this firing could not pay it in the ordinary way.

`python3 -m pytest tests/ -q -n auto` with this diff: **31 failed, 1746 passed,
35 skipped** (724s). So the failures were ATTRIBUTED rather than reported as a
lump, by re-running the same 13 affected files against **`main`'s `common.py` in
this same container** (`git stash` on the one file, everything else identical):

| | failures over the 13 affected files, `-n auto` |
|---|---|
| `main`'s `common.py`, this container | **34** |
| with this diff | **31** |
| **caused by this diff** | **ZERO** — `comm -23` over the sorted node-id sets is EMPTY |
| repaired by this diff | **3** (`tests/test_formalize_cache.py`: the sqlite side-store, the zero-solver-call re-certify, the cache-flag default-output pin) |

So this diff is a strict improvement on an already-red tree, and the redness is
not its doing. Serially (the honest number, since `-n auto` inflates by ~12
through parallel contention on the now-live Lean toolchain): **19 failed, 186
passed** over the same 13 files, 814s.

**What is actually failing is the second finding, and it is the image change and
not this diff**: a family of tests encodes *"this container has no Lean"* as
their EXPECTATION, and the fleet no longer satisfies it. The clearest instance
needs no interpretation at all —

    tests/test_anchor_runner.py::test_container_is_lean_absent
        assert common.lean_available() is False
        E  assert True is False

— and its siblings fail in the same voice: `assert 'failed' in ('unavailable',
'not-attempted')`, `assert 'kernel-failed' == 'shadow-edge-refused'`,
`test_real_default_backend_defers_here`, `test_ride_real_default_backend_defers_here`.
These are the lean-absent LANE's teeth, and they were pinned to the CONTAINER
rather than constructed. `common.lean_available()` reads **True** at `main` here
with this diff reverted, so every one of them was already red before this
session touched anything.

That is the same defect this file has now logged four times, in its purest form:
**a check that stopped tracking its evidence.** The lean-absent lane is real and
still needs testing; what it may not do is assume the container supplies its
premise. The fix is to make those tests FORCE lean-absence by construction
(inject the reading, as `tests/test_lean_env_probe.py` already does for every
network-shaped measurement) instead of asserting the fleet stays incapable — and
that is a decision about what the anchor lane's teeth MEAN, across 13 files, so
it is an ATTENDED call and is deliberately not improvised here at the end of a
firing. Some rows go further than a flipped expectation (`kernel-failed` says
Lean ran and did not succeed, which may be a jail/`unshare` limit rather than an
expectation drift); characterising those is part of the same attended pass.

Recorded, attributed, and NOT quietly widened into this diff.

## Bounds

No ceremony-reserved surface touched: `kernel/certs.py` pins, `TRUST.md`, the
escape-gate blocklist, `buildloop/growth_protocol.py`, `setup.sh`, `ci/`,
`.claude/` and `.github/` are all untouched — `setup.sh` in particular is READ
here and never edited; the alias lives in `common.py`, which is not
ceremony-reserved. P5 remains a trust root this session did not promote.
`tools/FgReflect.lean` and `results/reflect_candidates.json` are untouched. No
registry row, no re-baseline, no census. A `lean-local` container relaxes WHO MAY
AUTHOR tower-class work and NOTHING else: P5 and the anti-list are governance,
not infrastructure, and a local green remains NECESSARY and never SUFFICIENT —
the CI Lean lane stays the done-predicate exactly as before. The lane marker is
written unbracketed as lean-hammer here, as it must be everywhere that is not a
ride commit message.

## For the maintainer

`docs/lean-capable-environment.md` now describes a network policy that is no
longer in force ("**403 to CONNECT**" for `elan.lean-lang.org` and
`release.lean-lang.org`; this firing measured 200 for both, and for all four
others). It is left unedited deliberately: this receipt is a measurement, and
rewriting the runbook's premise from one container's reading is an attended
call — one firing's host table is evidence about that firing, exactly as the
probe's own `scope` string insists.
