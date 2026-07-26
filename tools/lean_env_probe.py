#!/usr/bin/env python3
"""Lean environment probe: CAN THIS CONTAINER ITERATE ON LEAN LOCALLY?

THE RULE THIS EXISTS TO UN-HARDCODE.  PLAN_FRAGMENT §3.1 rule 3 forbids an
UNATTENDED session from taking TOWER-class work.  The rule is right, but its
stated reason was never governance: a container with no toolchain would be
authoring Lean BLIND, paying one CI round-trip per iteration, unable to
converge inside a session.  That reason is CONDITIONAL ON A CAPABILITY --
and the rule spelled the capability as permanently absent, because on the
day it was written it was.  A condition written as a constant is a
measurement nobody ever takes again.  So this reading takes it.

WHAT IT ANSWERS, PRECISELY.  Not "is Lean installable" (a prediction), and
not "will the lane go green" (that is the lane's job, forever).  Only: does
THIS container, right now, hold the pinned toolchain the backend would
actually mount -- and if not, exactly WHAT is missing and WHOSE decision it
is to supply it.  Those last two words are the whole point of the
policy/absence split below.

THE SPLIT THAT MUST NOT COLLAPSE.  Two failures look identical from inside a
`lean: command not found`, and they have OPPOSITE fixes:

  NOT-INSTALLED   the hosts answer; nobody ran `bash setup.sh --with-lean`.
                  Fixed by running setup, in this container, by us.
  POLICY-DENIED   the egress gateway answers 403 to CONNECT for the toolchain
                  hosts.  Setup CANNOT fix it -- no retry, no backoff, no
                  mirror; it is an ORGANIZATION POLICY decision, and the fix
                  is a human editing the environment's network policy
                  (`docs/lean-capable-environment.md` is the runbook).

Reporting the second as the first sends the reader to re-run a script that
is guaranteed to fail again; reporting the first as the second sends them to
argue with a policy that was never in the way.  Conflating them is the
DEFECT this tool is built around, which is why the verdict vocabulary
separates them by construction and why `tests/test_lean_env_probe.py` reds
if either is ever emitted for the other's evidence.

NETWORK DISCIPLINE (⚠ the proxy README's rule, mechanized).  A 403 to CONNECT
is a VERDICT, not weather: the hiccup protocol's retry-with-backoff is for
5xx and timeouts, and retrying a policy denial is a loop that burns budget to
re-learn a decided fact.  So every host gets EXACTLY ONE attempt -- a bare
`CONNECT host:443` over the proxy socket, no TLS, no payload, hard-bounded by
`--timeout` -- and `measure_hosts` is written so that "one attempt" is a
property a test can drive rather than a promise a comment makes.  When the
gateway's own status endpoint is readable we CORROBORATE from its
`recentRelayFailures` ledger; when it is not, we degrade to `lean-unknown`
rather than guess, because an unreadable channel is not evidence of an open
one (READS FAIL SAFE).

WHY THE TOOLCHAIN TEST IS TWO DIRECTORIES, NOT ONE.  `lean_available()` only
says something answers on PATH.  What the repo actually elaborates through is
`kernel.backends.LeanBackend._lean_mounts`, which read-only-mounts EXACTLY
`common.LEAN_MATHLIB_DIR` and `common.LEAN_TOOLCHAIN_DIR` (the latter already
resolved at the `.lean-pins` toolchain via `_elan_mangle`) and degrades
honestly when either is absent -- and `_scratch_package` prepends
`common.MATHLIB_IMPORTS` to every scratch module, so even the import-free
reflect slice elaborates against Mathlib.  We therefore require the same two
directories the backend requires, no more and no less: a verdict that claimed
more than the backend can mount would license work the container cannot
actually do.  `LEAN4CHECKER_DIR` is reported but NOT required, because it
gates run-2 recheck (the trusted replay), not the authoring loop -- and the
lane owns the trusted replay regardless.

VERDICT VOCABULARY (deliberately tiny, matched mechanically by the rule):

    lean-local                      the pinned toolchain AND Mathlib are here;
                                    local elaboration can iterate
    lean-absent:policy-denied:<hosts>
                                    absent, and the gateway DENIED the named
                                    hosts -- setup cannot fix this
    lean-absent:not-installed       absent, hosts answer; setup was never run
    lean-unknown:<why>              we could not measure it, and we say so
                                    instead of guessing

SCOPE, AND THE STALENESS HAZARD WORTH SHOUTING ABOUT.  This is a reading of
the CONTAINER that ran it, not of the tree that stores it.  A committed
`results/lean_env.json` saying `lean-local` is evidence about the machine
that wrote it and licenses NOTHING for the machine reading it -- which is why
§3.1 rule 3 requires the probe to be RUN in the session that invokes the
conditional, never merely read.  We keep the artifact anyway (it is how an
operator shows what a container measured), and we drop every timestamp the
gateway hands us so two runs in one environment produce identical bytes.

Deterministic given its readings, offline-except-the-declared-probes,
LLM-free, Lean-free, no wall-clock: same canonical JSON discipline as the
census/frontier/supply writers (sorted keys, indent 1, trailing newline), and
`derived_from` pins `.lean-pins` and `setup.sh` by sha256 so a moved pin or a
rewritten install path reads as recorded staleness, distinct from a
derivation that is WRONG.

OUTPUT: ``results/lean_env.json`` (schema: ``derived_from``, ``honesty``,
``hosts``, ``pins``, ``proxy``, ``scope``, ``toolchain``, ``verdict``).
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common

#: Files this reading pins by sha256.  ``.lean-pins`` is the toolchain
#: identity the directory check resolves against; ``setup.sh``'s
#: ``--with-lean`` path is what decides WHICH hosts below are needed, so a
#: rewritten install path must read as staleness rather than pass silently.
INPUTS = (".lean-pins", "setup.sh")

#: Pin sentinel for a declared input that is not on disk (the supply_status /
#: purchase_frontier convention: the KEY stays, so "vanished" and "predates
#: the pin" never collapse into one observation).
INPUT_ABSENT = "(absent)"

#: The hosts `setup.sh --with-lean` needs, each with WHY.  Two of them are not
#: literal strings in setup.sh -- elan reaches them itself -- which is exactly
#: why they are enumerated here: the host a script never names is the host
#: whose denial nobody diagnoses.  `required` marks the ones whose state moves
#: the verdict.
HOSTS = (
    {"host": "elan.lean-lang.org", "port": 443, "required": True,
     "needed_for": "elan's own release channel; elan-init.sh resolves the "
                   "elan binary here before any toolchain is fetched"},
    {"host": "github.com", "port": 443, "required": True,
     "needed_for": "the mathlib4 and lean4checker clones in setup.sh's "
                   "--with-lean path"},
    {"host": "raw.githubusercontent.com", "port": 443, "required": True,
     "needed_for": "the elan-init.sh installer script setup.sh pipes to sh"},
    # BOTH lean-lang hosts.  The singular/plural pair is NOT a typo -- elan
    # uses them for different things and needs both.  This list has now been
    # wrong in BOTH directions, each corrected by a real --with-lean run:
    #
    #   run 1 (singular declared):  downloading https://releases.lean-lang.org
    #     /lean4/v4.15.0/lean-4.15.0-linux.tar.zst -> 403
    #     => the BINARIES come from the PLURAL host, undeclared at the time.
    #   run 2 (plural declared):    error: failed to parse release data:
    #     https://release.lean-lang.org / Unexpected character: H at (1:1)
    #     => the release MANIFEST comes from the SINGULAR host, and "H at
    #        (1:1)" is elan parsing a proxy block PAGE as JSON -- so that host
    #        is denied too, failing as HTML rather than as a clean 403.
    #
    # The second correction is the instructive one: swapping singular for
    # plural LOOKED like a fix, because the plural was genuinely missing and
    # the error genuinely named it.  It merely moved the failure one host
    # along.  An observation that explains the error in front of you is not
    # thereby the complete list, and this file -- whose whole job is refusing
    # to infer a capability it did not measure -- inferred one twice.
    {"host": "release.lean-lang.org", "port": 443, "required": True,
     "needed_for": "elan's release MANIFEST -- the toolchain version index it "
                   "parses as JSON before fetching any binary"},
    {"host": "releases.lean-lang.org", "port": 443, "required": True,
     "needed_for": "the Lean toolchain BINARIES `elan toolchain install "
                   "$LEAN_TOOLCHAIN` downloads"},
)

# Per-host measurement states.  `transient` and `unknown` are kept apart on
# purpose: the first is a gateway that answered something retryable, the
# second is a measurement we never got to take, and only the second may be
# read as "we do not know".
STATE_REACHABLE = "reachable"
STATE_DENIED = "policy-denied"
STATE_TRANSIENT = "transient"
STATE_UNKNOWN = "unknown"
HOST_STATES = (STATE_DENIED, STATE_REACHABLE, STATE_TRANSIENT, STATE_UNKNOWN)

#: HTTP statuses to CONNECT that mean "a human decided this", not "try again".
#: 403 is the gateway's policy denial; 407 is a proxy that will not carry us
#: without credentials we are not going to invent.
DENIAL_STATUSES = (403, 407)

# The verdict vocabulary.  Two exact words and two prefixes -- small enough
# that §3.1 rule 3 can match it mechanically, which is the entire reason the
# rule may now be conditional at all.
VERDICT_LOCAL = "lean-local"
VERDICT_NOT_INSTALLED = "lean-absent:not-installed"
VERDICT_DENIED_PREFIX = "lean-absent:policy-denied:"
VERDICT_UNKNOWN_PREFIX = "lean-unknown:"
VERDICT_EXACT = (VERDICT_LOCAL, VERDICT_NOT_INSTALLED)
VERDICT_PREFIXES = (VERDICT_DENIED_PREFIX, VERDICT_UNKNOWN_PREFIX)

#: The proxy's own status endpoint, relative to $HTTPS_PROXY.
STATUS_PATH = "/__agentproxy/status"

_SCOPE = (
    "a reading of the CONTAINER that ran this probe at the moment it ran, "
    "never a property of the tree that stores it: a committed lean-local "
    "verdict is evidence about the machine that wrote it and licenses "
    "nothing for the machine reading it, which is why PLAN_FRAGMENT §3.1 "
    "rule 3 requires this probe to be RUN in the session that invokes its "
    "conditional, not merely read off disk"
)

_HONESTY = (
    "this reading measures PRESENCE, never capability-to-install and never "
    "proof-correctness: lean-local says the two directories "
    "kernel.backends.LeanBackend._lean_mounts would mount are here, so local "
    "elaboration can ITERATE -- a local green remains NECESSARY and never "
    "SUFFICIENT, and the CI Lean lane is the final verdict exactly as before; "
    "host states are single-attempt readings of the egress gateway and a "
    "reachable host NEVER predicts a successful install (the Mathlib olean "
    "CDN that `lake exe cache get` fetches from is not enumerated here, and "
    "a source build is the fallback when it is blocked); a POLICY DENIAL is "
    "never retried and never reported as not-installed, because the two have "
    "opposite fixes -- one needs a human to edit the environment's network "
    "policy, the other needs setup.sh to be run at all; an unreadable status "
    "endpoint or an unattempted probe degrades the verdict to lean-unknown "
    "rather than guessing, since a channel we could not read is not evidence "
    "of an open one; and gateway timestamps are deliberately DROPPED from "
    "this artifact so two runs in one environment produce identical bytes"
)


# ------------------------------------------------------------------ readers
def _read_bytes(root: str, rel: str):
    try:
        with open(os.path.join(root, rel), "rb") as fh:
            return fh.read()
    except OSError:
        return None


def _pins(root: str) -> dict:
    out = {}
    for rel in INPUTS:
        raw = _read_bytes(root, rel)
        out[rel] = INPUT_ABSENT if raw is None else common.sha256_bytes(raw)
    return out


# -------------------------------------------------------------- the toolchain
def measure_toolchain(*, isdir=os.path.isdir, lean_available=None) -> dict:
    """What is actually on this filesystem, at the pinned identity.

    Both directory constants come from ``common`` already resolved at the
    ``.lean-pins`` toolchain (``common._elan_mangle``), so "present" here
    means present AT THE PIN -- a toolchain installed at some other version
    reads as absent, which is the honest answer for a repo whose lane pins
    one.  ``isdir``/``lean_available`` are injected so the whole reading is
    drivable from a test without a toolchain anywhere near it."""
    avail = common.lean_available if lean_available is None else lean_available
    return {
        "lean_available": bool(avail()),
        "lean4checker_dir": common.LEAN4CHECKER_DIR,
        "lean4checker_dir_present": bool(isdir(common.LEAN4CHECKER_DIR)),
        "mathlib_dir": common.LEAN_MATHLIB_DIR,
        "mathlib_dir_present": bool(isdir(common.LEAN_MATHLIB_DIR)),
        "toolchain_dir": common.LEAN_TOOLCHAIN_DIR,
        "toolchain_dir_present": bool(isdir(common.LEAN_TOOLCHAIN_DIR)),
    }


# ------------------------------------------------------------- host reachability
def proxy_url(env=None) -> str | None:
    """The configured egress proxy, or None.  Upper case wins; both spellings
    are read because the platform sets whichever it feels like."""
    env = os.environ if env is None else env
    for key in ("HTTPS_PROXY", "https_proxy"):
        val = (env.get(key) or "").strip()
        if val:
            return val
    return None


def _split_proxy(url: str):
    parts = urllib.parse.urlsplit(url if "://" in url else "http://" + url)
    return parts.hostname, (parts.port or 80)


def connect_via_proxy(host: str, port: int, *, timeout: float,
                      proxy: str) -> tuple[str, str]:
    """ONE bare `CONNECT host:port` over the proxy socket -> (state, detail).

    No TLS, no request body, no credentials, no second attempt: we want the
    gateway's verdict line and nothing else, and the whole point of the
    exercise is that a 403 here is a decision rather than a hiccup.  A
    failure to reach the PROXY ITSELF is `unknown` (we learned nothing about
    the target), while a gateway that answers a non-denial status is
    `transient` (it answered; the upstream may simply be down)."""
    phost, pport = _split_proxy(proxy)
    if not phost:
        return STATE_UNKNOWN, f"unparseable proxy url: {proxy!r}"
    req = (f"CONNECT {host}:{port} HTTP/1.1\r\n"
           f"Host: {host}:{port}\r\n\r\n").encode("ascii")
    try:
        with socket.create_connection((phost, pport), timeout=timeout) as sock:
            sock.settimeout(timeout)
            sock.sendall(req)
            buf = b""
            while b"\r\n" not in buf and len(buf) < 512:
                chunk = sock.recv(128)
                if not chunk:
                    break
                buf += chunk
    except OSError as ex:
        return STATE_UNKNOWN, f"proxy socket: {ex.__class__.__name__}"
    line = buf.split(b"\r\n", 1)[0].decode("latin-1").strip()
    bits = line.split()
    code = None
    if len(bits) >= 2 and bits[1].isdigit():
        code = int(bits[1])
    if code is None:
        return STATE_UNKNOWN, f"unparseable CONNECT reply: {line!r}"
    if code == 200:
        return STATE_REACHABLE, "gateway answered 200 to CONNECT"
    if code in DENIAL_STATUSES:
        return STATE_DENIED, (f"gateway answered {code} to CONNECT "
                              "(policy denial); NOT retried")
    return STATE_TRANSIENT, f"gateway answered {code} to CONNECT"


def connect_direct(host: str, port: int, *, timeout: float,
                   proxy: str | None = None) -> tuple[str, str]:
    """No proxy configured: a bare TCP connect is the whole measurement.

    There is no gateway to render a policy verdict, so this channel can never
    produce `policy-denied` -- a refusal here is `transient`, and the verdict
    logic turns an unresolved required host into `lean-unknown` rather than
    inventing a denial nobody issued."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
    except OSError as ex:
        return STATE_TRANSIENT, f"direct connect: {ex.__class__.__name__}"
    return STATE_REACHABLE, "direct TCP connect succeeded"


def fetch_proxy_status(proxy: str, *, timeout: float, opener=None):
    """The gateway's own status document, or None.

    Requested WITHOUT going through the proxy (it is the proxy we are asking),
    hence the empty ``ProxyHandler``.  ANY failure -- transport, status,
    encoding, schema -- returns None: an unreadable ledger degrades the
    verdict to `lean-unknown`, it never fabricates one, and there is no
    retry here either (this endpoint is local; if it does not answer once it
    is not going to answer twice inside a session's budget)."""
    phost, pport = _split_proxy(proxy)
    if not phost:
        return None
    url = f"http://{phost}:{pport}{STATUS_PATH}"
    if opener is None:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 -- transport OR schema; both mean unread
        return None


def denied_hosts_from_status(status) -> set:
    """Hostnames the gateway RECORDED a CONNECT denial for.

    Corroboration only, and deliberately lossy: we keep the host and throw the
    timestamps away, because a `ts` copied into a committed artifact would
    make every re-run a diff.  The returned set is the ledger's OWN content
    and may name hosts outside `HOSTS` (the gateway records whatever was last
    attempted); `measure_hosts` only ever intersects it with the declared
    list, while `proxy.hosts_denied_in_status_ledger` reports it whole,
    because a denial we did not ask about is still worth an operator's
    attention."""
    out = set()
    if not isinstance(status, dict):
        return out
    for row in status.get("recentRelayFailures", []) or []:
        if not isinstance(row, dict):
            continue
        if row.get("kind") != "connect_rejected":
            continue
        detail = str(row.get("detail", ""))
        if not any(str(c) in detail for c in DENIAL_STATUSES):
            continue
        host = str(row.get("host", "")).rsplit(":", 1)[0]
        if host:
            out.add(host)
    return out


def measure_hosts(hosts=HOSTS, *, timeout: float, proxy: str | None,
                  connect=None, status_denials=None, attempt: bool = True):
    """One row per declared host; EXACTLY ONE `connect` call per host.

    The single-attempt property is the tooth: a denial is a decided fact, and
    a retry loop against a decided fact is how a session spends its budget
    learning nothing.  `status_denials` (the gateway's own ledger) is folded
    in as a SECOND channel that can only ever ADD a denial -- a host the
    ledger names is denied even if our own attempt merely timed out, since
    the ledger is the gateway reporting its own decision."""
    if connect is None:
        connect = connect_via_proxy if proxy else connect_direct
    denials = set() if status_denials is None else set(status_denials)
    rows = []
    for spec in hosts:
        host, port = spec["host"], spec["port"]
        if not attempt:
            state, detail = STATE_UNKNOWN, "not attempted (--offline)"
        else:
            state, detail = connect(host, port, timeout=timeout, proxy=proxy)
        recorded = host in denials
        if recorded and state != STATE_DENIED:
            state = STATE_DENIED
            detail = (f"{detail}; gateway status ledger records a CONNECT "
                      "denial for this host")
        rows.append({
            "host": host,
            "port": port,
            "required": bool(spec.get("required", True)),
            "needed_for": spec["needed_for"],
            "state": state,
            "detail": detail,
            "denial_in_status_ledger": recorded,
        })
    rows.sort(key=lambda r: (r["host"], r["port"]))
    return rows


# ----------------------------------------------------------------- verdict
def _verdict(toolchain: dict, hosts: list) -> str:
    """The pinned vocabulary, in the one order that keeps the split honest.

    Presence dominates: if the directories are here, HOW they got here is
    archaeology.  Below that, a DENIAL outranks an unmeasured host, because a
    denial is the actionable fact and burying it under "we could not tell"
    would send the reader back to retry the very thing that was refused."""
    if toolchain["lean_available"]:
        missing = [name for name, present in (
            ("mathlib", toolchain["mathlib_dir_present"]),
            ("toolchain", toolchain["toolchain_dir_present"]))
            if not present]
        if not missing:
            return VERDICT_LOCAL
        # Something answers on PATH but it is not the pinned installation the
        # backend mounts.  That is neither local capability nor a clean
        # absence, and calling it either would be a guess.
        return (VERDICT_UNKNOWN_PREFIX + "lean-on-path-but-unmounted:"
                + ",".join(sorted(missing)))
    required = [r for r in hosts if r["required"]]
    denied = sorted(r["host"] for r in required if r["state"] == STATE_DENIED)
    if denied:
        return VERDICT_DENIED_PREFIX + ",".join(denied)
    unmeasured = sorted(r["host"] for r in required
                        if r["state"] in (STATE_TRANSIENT, STATE_UNKNOWN))
    if unmeasured:
        return VERDICT_UNKNOWN_PREFIX + "hosts-unmeasured:" + ",".join(unmeasured)
    return VERDICT_NOT_INSTALLED


def build_lean_env(root: str, *, toolchain: dict, hosts: list,
                   proxy: dict) -> dict:
    """The pure build: readings in, canonical document out.

    Every fact this consumes is passed in, so the whole verdict surface is
    drivable from synthetic fixtures -- the four verdict shapes are precisely
    the ones no single real container can exhibit."""
    return {
        "derived_from": _pins(root),
        "honesty": _HONESTY,
        "hosts": hosts,
        "pins": {"lean_toolchain": common.LEAN_TOOLCHAIN,
                 "mathlib_commit": common.MATHLIB_COMMIT},
        "proxy": proxy,
        "scope": _SCOPE,
        "toolchain": toolchain,
        "verdict": _verdict(toolchain, hosts),
    }


def probe(root: str, *, timeout: float = 4.0, offline: bool = False) -> dict:
    """Measure this container, then build.  The only IO-bearing entry point."""
    toolchain = measure_toolchain()
    url = proxy_url()
    status = None
    if url and not offline:
        status = fetch_proxy_status(url, timeout=timeout)
    if url is None:
        status_state = "not attempted: no proxy configured"
    elif offline:
        status_state = "not attempted: --offline"
    elif status is None:
        status_state = "unreadable: degrading unresolved hosts to lean-unknown"
    else:
        status_state = "read"
    denials = denied_hosts_from_status(status)
    hosts = measure_hosts(timeout=timeout, proxy=url,
                          status_denials=denials, attempt=not offline)
    return build_lean_env(root, toolchain=toolchain, hosts=hosts,
                          proxy={"configured": url is not None,
                                 "status_endpoint": status_state,
                                 "hosts_denied_in_status_ledger":
                                     sorted(denials)})


def _write(doc: dict, out_path: str) -> None:
    with open(out_path, "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
        fh.write("\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))),
        help="repo root holding the pinned inputs")
    ap.add_argument("--results", default=None,
                    help="dir lean_env.json is written to "
                         "(default: <root>/results)")
    ap.add_argument("--timeout", type=float, default=4.0,
                    help="per-probe socket timeout in seconds (hard bound; "
                         "there is no second attempt to spend it twice)")
    ap.add_argument("--offline", action="store_true",
                    help="take no network measurement at all; unresolved "
                         "hosts read unknown and the verdict degrades "
                         "honestly to lean-unknown")
    args = ap.parse_args(argv)
    from buildloop import lanes
    with lanes.token_free("lean_env_probe"):
        doc = probe(args.root, timeout=args.timeout, offline=args.offline)
    results = args.results or os.path.join(args.root, "results")
    out_path = os.path.join(results, "lean_env.json")
    _write(doc, out_path)
    print(f"lean env: {doc['verdict']} -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
