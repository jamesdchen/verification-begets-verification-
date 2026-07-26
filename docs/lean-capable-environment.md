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
| `release.lean-lang.org` | elan's release **manifest** (the version index it parses as JSON) | **denied** — returns a block PAGE, so elan fails with `Unexpected character: H at (1:1)` |
| `releases.lean-lang.org` | the Lean toolchain **binaries** `elan toolchain install $LEAN_TOOLCHAIN` downloads | **403** |

So the request is **four hosts**: `elan.lean-lang.org:443`,
`release.lean-lang.org:443`, `releases.lean-lang.org:443` and
`lakecache.blob.core.windows.net:443`.

> **This list grew three times, each time from a real run rather than from
> reasoning, and every intermediate version looked complete.**  Treat the
> count as measured-so-far, not as proven-total: the honest procedure is to
> run `--with-lean`, read the URL in the failure, and add it.

> **BOTH lean-lang hostnames, and the singular/plural pair is not a typo.**
> This page has now been wrong in both directions, each corrected by a real
> run rather than by reasoning:
>
> * declaring only the **singular** died on
>   `downloading https://releases.lean-lang.org/lean4/v4.15.0/...tar.zst -> 403`
>   — the BINARIES come from the plural host.
> * declaring only the **plural** died on
>   `failed to parse release data: https://release.lean-lang.org` /
>   `Unexpected character: H at (1:1)` — the release MANIFEST comes from the
>   singular host, and `H at (1:1)` is elan parsing a proxy block *page* as
>   JSON, so that host is denied too; it just fails as HTML instead of as a
>   clean 403.
>
> The second correction is the one worth remembering: swapping singular for
> plural *looked* like a fix, because the plural was genuinely missing and the
> error genuinely named it.  It only moved the failure one host along.  An
> observation that explains the error in front of you is not thereby the
> complete list.

The change is made in the **environment's network policy**, configured at
`claude.ai/code` — see
<https://code.claude.com/docs/en/claude-code-on-the-web> for where the
environment's network settings live.  It is not a repo change, and no
session can make it: that is the point of calling it a policy denial.

The Mathlib olean CDN is now enumerated too, and an earlier version of this
page was wrong about it in the way that matters most.  It said a blocked CDN
merely means *"setup still completes — `lake build` falls back to building
Mathlib from source, which is hours rather than minutes."*  A real run
refuted that:

```
Downloaded: 0 file(s) [attempted 5826/5826 = 100%] (0% success), 5826 failed
5826 download(s) failed
```

and setup **exited 1**.  A fallback that is never reached is not a fallback,
and "slow" and "dead" are not the same reading — the same distinction this
whole page exists to keep straight for `policy-denied` vs `not-installed`.

The host itself was read out of Mathlib's own source at the pinned commit
rather than recalled: `Cache/Requests.lean` sets `useFROCache := false`, so
the cache URL is `https://lakecache.blob.core.windows.net/mathlib4` and NOT
`mathlib4.lean-cache.cloud` (the FRO cache, disabled upstream as flaky).  If
`.lean-pins` moves to a commit that flips that flag, the host changes with
it — which is why `derived_from` pins `.lean-pins` by sha256.

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
