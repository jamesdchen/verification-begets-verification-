# Making a driver container Lean-capable

## Why this page exists

`PLAN_FRAGMENT.md` §3.1 rule 3 forbids an **unattended** session from taking
TOWER-class work.  The reason was never governance — it is that a container
with no toolchain authors Lean *blind*, paying one CI round-trip per
iteration and unable to converge inside a session.  That is a claim about a
**capability**, and the rule used to spell the capability as permanently
absent.  It no longer does: the capability is measured by
`tools/lean_env_probe.py`, and when the measurement reads `lean-local` the
additive-only restriction lifts (the CI lane stays the final verdict —
see "What this does *not* change" below).

So this page is the other half of that conditional: **how an operator makes
the measurement come out `lean-local`**, and how to verify that it did.

## The measured situation today

Run the probe; it writes `results/lean_env.json` and prints the verdict:

```
python3 tools/lean_env_probe.py
```

In the current driver containers it reports:

```
lean-absent:policy-denied:elan.lean-lang.org,release.lean-lang.org
```

Read that literally.  It is **not** "setup was never run" — it is the egress
gateway answering **403 to CONNECT** for exactly two hosts.  A 403 to CONNECT
is an *organization policy decision*, not weather: it must never be retried
(the agent-proxy README says so, and the probe is written so it cannot), and
no amount of re-running `bash setup.sh --with-lean` will change it.

The split matters because the two absences have opposite fixes:

| verdict | what is actually wrong | who fixes it |
|---|---|---|
| `lean-absent:not-installed` | hosts answer; nobody ran setup | run `bash setup.sh --with-lean` |
| `lean-absent:policy-denied:<hosts>` | the gateway refuses the named hosts | a human edits the environment's network policy |
| `lean-unknown:<why>` | we could not measure it | read `<why>`; never treat as permission |
| `lean-local` | the pinned toolchain and Mathlib are both present | nothing — you are done |

## What must be allowed (option A: allow the two hosts)

`setup.sh --with-lean` needs four hosts.  Two of them **already work** in
these containers and must not be added to any request — asking for access
you already have widens the ask for no reason:

| host | needed for | status today |
|---|---|---|
| `github.com` | the `mathlib4` and `lean4checker` clones | **already reachable** |
| `raw.githubusercontent.com` | the `elan-init.sh` installer script | **already reachable** |
| `elan.lean-lang.org` | elan's own release channel (resolves the `elan` binary) | **403 to CONNECT** |
| `releases.lean-lang.org` | the Lean toolchain **binaries** `elan toolchain install $LEAN_TOOLCHAIN` downloads | **403** (measured on a real run, see below) |

So the request is narrow and precise: **allow `releases.lean-lang.org:443`
and `elan.lean-lang.org:443`.**  Nothing else about the Lean path is blocked.

> **The hostname is PLURAL, and this page said the singular until a real run
> corrected it.**  A `--with-lean` attempt got as far as cloning Mathlib and
> then died on
> `downloading https://releases.lean-lang.org/lean4/v4.15.0/lean-4.15.0-linux.tar.zst`
> `-> 403`.  `release.lean-lang.org` (singular) resolves, so a probe of it
> answers, and an allowlist entry for it would have unblocked NOTHING while
> reading as though it had.  Allowlist the plural.

The change is made in the **environment's network policy**, configured at
`claude.ai/code` — see
<https://code.claude.com/docs/en/claude-code-on-the-web> for where the
environment's network settings live.  It is not a repo change, and no
session can make it: that is the point of calling it a policy denial.

One host the probe *does not* enumerate, and you should know about it: the
Mathlib olean CDN that `lake exe cache get` fetches prebuilt `.olean`s from.
If it is also blocked, setup still completes — `lake build` falls back to
building Mathlib from source, which is hours rather than minutes.  Watch for
that in the setup log rather than assuming it.

## What must be allowed (option B: bake the image instead)

Allowing hosts is not the only route, and often not the best one.  CI already
avoids this problem entirely: `.github/workflows/lean-image.yml` bakes a
**per-pin image** (`ghcr.io/jamesdchen/cgb-lean-toolchain:pins-<hash>`) from
`ci/Dockerfile.lean`, and the Lean job primes from it rather than fetching a
toolchain at all.

If the environment supports a custom base image, pointing it at that same
ghcr image gives you `lean-local` with **no network policy change at all** —
the toolchain arrives as filesystem, not as egress.  It is the strictly
tighter option: no new hosts are ever reachable from the container.

## The costs, stated up front

* **~5 GB warm cache.**  A resolved toolchain plus a built Mathlib is a large
  filesystem, whichever route delivers it.  `.lean-pins`' own comment already
  records this: CI keys its toolchain cache on that file's hash.
* **`.lean-pins` re-keys everything.**  The pins are
  `MATHLIB_COMMIT=9837ca9d65d9de6fad1ef4381750ca688774e608` and
  `LEAN_TOOLCHAIN=leanprover/lean4:v4.15.0`, and `setup.sh` *asserts* that the
  toolchain derived from `mathlib4`'s `lean-toolchain` at that commit equals
  the pin (⚠D1) — a drifted pin is refused, not silently rebuilt.  Bumping
  `.lean-pins` therefore invalidates the CI cache **and** every baked image
  tag, and rebuilds the ~5 GB from scratch.  Under option B this is the real
  recurring cost: each pin bump needs a fresh image build before any
  container gets `lean-local` back.
* **`lean4checker` is not required for `lean-local`.**  It gates run-2
  recheck (the trusted replay), which the CI lane owns regardless.  The probe
  reports its presence but does not demand it.

## How to verify (both steps, in order)

**1. The probe must read `lean-local`.**

```
python3 tools/lean_env_probe.py
```

Anything else means you are not done, and the verdict says which of the four
situations you are in.  A `lean-unknown:*` reading is *not* a soft pass — the
rule treats it exactly like an absence.

**2. The elaboration tooth must RUN, not skip.**

```
python3 -m pytest tests/test_fg_reflect_lean.py -q
```

`test_elaborates_under_lean` carries
`@pytest.mark.skipif(not common.lean_available(), ...)`.  In a Lean-less
container it skips **with a named reason** (never a silent pass).  In a
correctly provisioned one it *runs*, driving `LeanBackend().elaborate` — which
read-only-mounts exactly `common.LEAN_MATHLIB_DIR` and
`common.LEAN_TOOLCHAIN_DIR` and prepends `common.MATHLIB_IMPORTS` to the
scratch module.  Those are the same two directories the probe checks, which
is why step 1 passing and step 2 skipping would be a bug in the probe rather
than a quirk of the environment.

Use `-rs` if you want pytest to print the skip reason explicitly.

## What this does *not* change

* **The lane is still the final verdict.**  A local green is **necessary,
  never sufficient**.  §3.1 rule 2's Lean-last batching is untouched: all
  Lean-touching edits still ride the session's final `[lean-fast]` /
  `[lean-ci]` commit, and "it elaborates here" is a reason to push, never a
  done-predicate.
* **Trust roots do not move.**  P5 and the anti-list
  (`buildloop/growth_protocol.py::ANTI_LIST`), the kernel checkers, the
  contract types, `kernel/certs.py`'s pins, `TRUST.md` and the escape-gate
  blocklist are **governance, not infrastructure**.  They never move on
  capability — only through the `PLAN_REFLECT` S4a→S4a′→S4b ceremony with
  explicit maintainer sign-off.  A container that can elaborate locally has
  bought exactly one thing: faster iteration *inside* the fence.
* **The probe must be run, not read.**  `results/lean_env.json` is a reading
  of the container that produced it.  A committed `lean-local` verdict is
  evidence about *that* machine and licenses nothing for the machine reading
  it — which is why the rule and the purchase-driver prompt both say RUN.
