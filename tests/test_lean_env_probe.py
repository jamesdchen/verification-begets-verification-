"""Teeth for tools/lean_env_probe.py -- the reading that un-hardcodes §3.1 rule 3.

The defect this probe exists to abolish is a CONFLATION, so the teeth that
matter are not schema teeth.  They are

    test_a_policy_denial_is_never_reported_as_not_installed
    test_a_clean_absence_is_never_reported_as_policy_denied

which drive the two evidence shapes that look identical from inside a
`lean: command not found` and have OPPOSITE fixes -- one needs a human to
edit the environment's network policy, the other needs `setup.sh
--with-lean` to be run at all.  Collapse the two arms of `_verdict` into one
and those two tests are what go red.

Its sibling is

    test_measure_hosts_makes_exactly_one_attempt_per_host

because "never retry a policy denial" is the proxy README's rule and a
comment promising it is not a mechanism.  Driven with a counting stub, so
adding a retry loop reds the suite in the container that wrote it.

Everything else pins the derivation the way its siblings are pinned (the
test_supply_status precedent): the four verdict shapes as SYNTHETIC fixtures
(no real container exhibits more than one of them), determinism and
no-clock, `derived_from` pins so a moved input reads as STALENESS distinct
from a WRONG derivation, honest degradation when the gateway's status
endpoint does not read, and the rule/mechanism drift pin that keeps
PLAN_FRAGMENT §3.1 rule 3 citing this file by name.

Stdlib + repo files only: every network-shaped reading is injected, so this
module opens no socket.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common  # noqa: E402
from tools.lean_env_probe import (  # noqa: E402
    HOST_STATES,
    HOSTS,
    INPUT_ABSENT,
    INPUTS,
    STATE_DENIED,
    STATE_REACHABLE,
    STATE_TRANSIENT,
    STATE_UNKNOWN,
    VERDICT_DENIED_PREFIX,
    VERDICT_EXACT,
    VERDICT_LOCAL,
    VERDICT_NOT_INSTALLED,
    VERDICT_PREFIXES,
    VERDICT_UNKNOWN_PREFIX,
    _write,
    build_lean_env,
    connect_via_proxy,
    denied_hosts_from_status,
    fetch_proxy_status,
    measure_hosts,
    measure_toolchain,
    proxy_url,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACT = os.path.join(ROOT, "results", "lean_env.json")
SOURCE = os.path.join(ROOT, "tools", "lean_env_probe.py")
PLAN = os.path.join(ROOT, "PLAN_FRAGMENT.md")
PROMPTS = os.path.join(ROOT, "C3_PROMPTS.md")


# ------------------------------------------------------- synthetic fixtures
def _toolchain(*, lean=False, tc=False, ml=False, l4c=False) -> dict:
    """A toolchain reading with no toolchain anywhere near it."""
    return {
        "lean_available": lean,
        "lean4checker_dir": "/x/lean4checker",
        "lean4checker_dir_present": l4c,
        "mathlib_dir": "/x/mathlib",
        "mathlib_dir_present": ml,
        "toolchain_dir": "/x/toolchains/leanprover--lean4---v4.15.0",
        "toolchain_dir_present": tc,
    }


def _hosts(states) -> list:
    """One row per declared host, forced into the given states.

    `states` is host -> state; anything unnamed is reachable, so a fixture
    says only what it is about."""
    rows = []
    for spec in HOSTS:
        state = states.get(spec["host"], STATE_REACHABLE)
        rows.append({
            "host": spec["host"], "port": spec["port"],
            "required": bool(spec.get("required", True)),
            "needed_for": spec["needed_for"],
            "state": state, "detail": f"synthetic: {state}",
            "denial_in_status_ledger": state == STATE_DENIED,
        })
    rows.sort(key=lambda r: (r["host"], r["port"]))
    return rows


def _proxy(configured=True, status="read") -> dict:
    return {"configured": configured, "status_endpoint": status,
            "hosts_denied_in_status_ledger": []}


def _build(root=ROOT, *, toolchain=None, hosts=None, proxy=None) -> dict:
    return build_lean_env(
        root,
        toolchain=_toolchain() if toolchain is None else toolchain,
        hosts=_hosts({}) if hosts is None else hosts,
        proxy=_proxy() if proxy is None else proxy)


#: The container this repo actually runs in: the toolchain BINARY hosts are
#: policy-denied while the git hosts answer.  Named once, used by both arms
#: of the conflation tooth.
_DENIED_HERE = {"elan.lean-lang.org": STATE_DENIED,
                "releases.lean-lang.org": STATE_DENIED}


# ========================================================== THE MAIN TEETH
def test_a_policy_denial_is_never_reported_as_not_installed():
    """The gateway refused; re-running setup.sh cannot help.

    Reporting this as not-installed would send the reader back to a script
    guaranteed to fail again -- and a session that retried it would be
    burning its budget re-learning a decided fact."""
    doc = _build(hosts=_hosts(_DENIED_HERE))
    v = doc["verdict"]
    assert v.startswith(VERDICT_DENIED_PREFIX), v
    assert v != VERDICT_NOT_INSTALLED
    assert "not-installed" not in v
    # ...and it must NAME the denied hosts, because "denied" without a host
    # is not a runbook entry, it is a mood.
    assert v == (VERDICT_DENIED_PREFIX
                 + "elan.lean-lang.org,releases.lean-lang.org")


def test_a_clean_absence_is_never_reported_as_policy_denied():
    """Every host answers and Lean is simply not installed.

    The opposite error: sending the reader to argue with a network policy
    that was never in the way, when `bash setup.sh --with-lean` is the fix."""
    doc = _build(hosts=_hosts({}))
    assert doc["verdict"] == VERDICT_NOT_INSTALLED
    assert "policy-denied" not in doc["verdict"]


def test_measure_hosts_makes_exactly_one_attempt_per_host():
    """A 403 is a VERDICT, not weather -- the proxy README forbids retrying it.

    Driven with a counting stub rather than read off the source, so a retry
    loop added later cannot pass by being spelled differently."""
    calls = []

    def stub(host, port, *, timeout, proxy):
        calls.append(host)
        return STATE_DENIED, "gateway answered 403 to CONNECT"

    rows = measure_hosts(timeout=0.01, proxy="http://p:1", connect=stub)
    assert len(calls) == len(HOSTS)
    assert sorted(calls) == sorted(s["host"] for s in HOSTS)
    assert all(r["state"] == STATE_DENIED for r in rows)


@pytest.mark.parametrize("state", [STATE_REACHABLE, STATE_TRANSIENT,
                                   STATE_UNKNOWN])
def test_no_state_is_ever_probed_twice(state):
    """One attempt is the rule for every outcome, not just for denials: a
    per-state retry would still be a budget the probe does not own."""
    calls = []

    def stub(host, port, *, timeout, proxy):
        calls.append(host)
        return state, "synthetic"

    measure_hosts(timeout=0.01, proxy="http://p:1", connect=stub)
    assert len(calls) == len(HOSTS)


# ================================================ the four verdict shapes
def test_shape_lean_local():
    doc = _build(toolchain=_toolchain(lean=True, tc=True, ml=True, l4c=True))
    assert doc["verdict"] == VERDICT_LOCAL


def test_shape_policy_denied():
    doc = _build(hosts=_hosts({"releases.lean-lang.org": STATE_DENIED}))
    assert doc["verdict"] == VERDICT_DENIED_PREFIX + "releases.lean-lang.org"


def test_shape_not_installed():
    assert _build()["verdict"] == VERDICT_NOT_INSTALLED


def test_shape_unknown():
    doc = _build(hosts=_hosts({"github.com": STATE_UNKNOWN}),
                 proxy=_proxy(status="unreadable: degrading"))
    assert doc["verdict"] == (VERDICT_UNKNOWN_PREFIX
                              + "hosts-unmeasured:github.com")


def test_every_shape_is_in_the_declared_vocabulary():
    """The vocabulary is what §3.1 rule 3 matches on, so it is pinned here
    rather than left to whatever string a future arm happens to return."""
    docs = [
        _build(toolchain=_toolchain(lean=True, tc=True, ml=True)),
        _build(hosts=_hosts(_DENIED_HERE)),
        _build(),
        _build(hosts=_hosts({"github.com": STATE_TRANSIENT})),
        _build(toolchain=_toolchain(lean=True, tc=True, ml=False)),
        _build(toolchain=_toolchain(lean=True, tc=False, ml=False)),
    ]
    if os.path.exists(ARTIFACT):
        with open(ARTIFACT) as fh:
            docs.append(json.load(fh))
    for doc in docs:
        v = doc["verdict"]
        assert v in VERDICT_EXACT or v.startswith(VERDICT_PREFIXES), v
    # every shape reachable, so no arm is dead code
    assert {d["verdict"].split(":")[0] for d in docs} >= {
        "lean-local", "lean-absent", "lean-unknown"}


# ============================================= what lean-local may claim
@pytest.mark.parametrize("lean,tc,ml", [
    (False, True, True), (False, False, False),
    (True, False, True), (True, True, False), (True, False, False),
])
def test_lean_local_requires_the_two_directories_the_backend_mounts(
        lean, tc, ml):
    """`lean_available()` alone is PATH gossip.

    What elaboration actually needs is what `LeanBackend._lean_mounts`
    read-only-mounts -- LEAN_MATHLIB_DIR and LEAN_TOOLCHAIN_DIR, the latter
    already resolved at the .lean-pins toolchain -- and `_scratch_package`
    prepends MATHLIB_IMPORTS to every scratch module, so even the import-free
    reflect slice elaborates against Mathlib.  A verdict claiming more than
    the backend can mount would license work the container cannot do."""
    doc = _build(toolchain=_toolchain(lean=lean, tc=tc, ml=ml))
    assert doc["verdict"] != VERDICT_LOCAL


def test_the_backend_still_mounts_exactly_the_two_dirs_we_check():
    """Cross-check against the backend itself, not against a memory of it."""
    src = open(os.path.join(ROOT, "kernel", "backends.py"),
               encoding="utf-8").read()
    idx = src.index("def _lean_mounts")
    window = src[idx:idx + 900]
    assert "common.LEAN_MATHLIB_DIR" in window
    assert "common.LEAN_TOOLCHAIN_DIR" in window
    # lean4checker is the checker=True arm (run 2, the trusted replay) -- we
    # report it but must NOT require it, since the lane owns run 2 regardless.
    assert "checker" in window


def test_lean4checker_absence_does_not_block_lean_local():
    doc = _build(toolchain=_toolchain(lean=True, tc=True, ml=True, l4c=False))
    assert doc["verdict"] == VERDICT_LOCAL
    assert doc["toolchain"]["lean4checker_dir_present"] is False


def test_lean_on_path_without_the_pin_is_unknown_not_local_and_not_absent():
    """Something answers `lean`, but not at the pinned installation.

    Neither capability nor clean absence -- calling it either would be a
    guess, and this reading's whole job is to stop guessing."""
    doc = _build(toolchain=_toolchain(lean=True, tc=False, ml=True))
    assert doc["verdict"].startswith(VERDICT_UNKNOWN_PREFIX)
    assert "toolchain" in doc["verdict"]


# ================================================= honest degradation
def test_an_unreadable_status_endpoint_degrades_to_unknown_never_to_absent():
    """READS FAIL SAFE: a channel we could not read is not evidence of an
    open one, so it may never harden into `not-installed`."""
    doc = _build(hosts=_hosts({h["host"]: STATE_UNKNOWN for h in HOSTS}),
                 proxy=_proxy(status="unreadable: degrading unresolved hosts"))
    assert doc["verdict"].startswith(VERDICT_UNKNOWN_PREFIX)
    assert doc["verdict"] != VERDICT_NOT_INSTALLED


def test_fetch_proxy_status_returns_none_on_any_failure():
    """Transport error, bad status, junk body -- all read as UNREAD."""
    class Boom:
        def open(self, url, timeout=None):
            raise OSError("refused")

    class Junk:
        def open(self, url, timeout=None):
            class R:
                def __enter__(self_inner):
                    return self_inner

                def __exit__(self_inner, *a):
                    return False

                def read(self_inner):
                    return b"not json"
            return R()

    assert fetch_proxy_status("http://p:1", timeout=0.01, opener=Boom()) is None
    assert fetch_proxy_status("http://p:1", timeout=0.01, opener=Junk()) is None
    assert fetch_proxy_status("", timeout=0.01, opener=Boom()) is None


def test_offline_takes_no_measurement_and_says_so():
    rows = measure_hosts(timeout=0.01, proxy=None, attempt=False,
                         connect=None)
    assert {r["state"] for r in rows} == {STATE_UNKNOWN}
    assert all("not attempted" in r["detail"] for r in rows)


def test_the_status_ledger_can_only_add_a_denial_never_remove_one():
    """The gateway reporting its own decision outranks our timed-out attempt;
    it must never launder a measured denial back into a reachable host."""
    def stub(host, port, *, timeout, proxy):
        return STATE_TRANSIENT, "gateway answered 502 to CONNECT"

    rows = measure_hosts(timeout=0.01, proxy="http://p:1", connect=stub,
                         status_denials={"releases.lean-lang.org"})
    by_host = {r["host"]: r for r in rows}
    assert by_host["releases.lean-lang.org"]["state"] == STATE_DENIED
    assert by_host["releases.lean-lang.org"]["denial_in_status_ledger"] is True
    assert by_host["github.com"]["state"] == STATE_TRANSIENT


# ============================================ reading the gateway's ledger
def test_denied_hosts_reads_only_connect_denials_and_drops_timestamps():
    status = {"recentRelayFailures": [
        {"ts": "2026-07-25T10:14:06.723Z", "kind": "connect_rejected",
         "detail": "gateway answered 403 to CONNECT (policy denial or "
                   "upstream failure)", "host": "releases.lean-lang.org:443"},
        {"ts": "2026-07-25T10:14:07.077Z", "kind": "connect_rejected",
         "detail": "gateway answered 407 to CONNECT", "host": "elan.x:443"},
        # a 502 is weather; it must not enter the denial set
        {"ts": "x", "kind": "connect_rejected",
         "detail": "gateway answered 502", "host": "weather.example:443"},
        # a different failure kind is not a CONNECT verdict at all
        {"ts": "x", "kind": "tls_error", "detail": "403 somewhere",
         "host": "tls.example:443"},
    ]}
    got = denied_hosts_from_status(status)
    assert got == {"releases.lean-lang.org", "elan.x"}


@pytest.mark.parametrize("bad", [None, {}, {"recentRelayFailures": None},
                                 {"recentRelayFailures": ["junk"]}, "text"])
def test_denied_hosts_tolerates_every_malformed_status(bad):
    assert denied_hosts_from_status(bad) == set()


# ============================================ the CONNECT classification
def _fake_socket(monkeypatch, reply: bytes):
    import tools.lean_env_probe as mod

    class Sock:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def settimeout(self, t):
            pass

        def sendall(self, b):
            self.sent = b

        def recv(self, n):
            nonlocal reply
            out, reply = reply[:n], reply[n:]
            return out

    monkeypatch.setattr(mod.socket, "create_connection",
                        lambda *a, **k: Sock())


@pytest.mark.parametrize("reply,state", [
    (b"HTTP/1.1 200 Connection established\r\n\r\n", STATE_REACHABLE),
    (b"HTTP/1.1 403 Forbidden\r\n\r\n", STATE_DENIED),
    (b"HTTP/1.1 407 Proxy Authentication Required\r\n\r\n", STATE_DENIED),
    (b"HTTP/1.1 502 Bad Gateway\r\n\r\n", STATE_TRANSIENT),
    (b"garbage\r\n\r\n", STATE_UNKNOWN),
])
def test_connect_classification(monkeypatch, reply, state):
    _fake_socket(monkeypatch, reply)
    got, detail = connect_via_proxy("h", 443, timeout=0.01,
                                    proxy="http://p:1")
    assert got == state
    assert detail
    if state == STATE_DENIED:
        assert "NOT retried" in detail


def test_a_proxy_socket_failure_is_unknown_not_denied(monkeypatch):
    """We learned nothing about the target -- inventing a denial here would
    be exactly the fabrication the tool exists to prevent."""
    import tools.lean_env_probe as mod

    def boom(*a, **k):
        raise OSError("no route")

    monkeypatch.setattr(mod.socket, "create_connection", boom)
    state, detail = connect_via_proxy("h", 443, timeout=0.01,
                                      proxy="http://p:1")
    assert state == STATE_UNKNOWN
    assert "proxy socket" in detail


def test_an_unparseable_proxy_url_is_unknown():
    state, _ = connect_via_proxy("h", 443, timeout=0.01, proxy="")
    assert state == STATE_UNKNOWN


def test_proxy_url_reads_both_spellings_and_empty_means_unset():
    assert proxy_url({}) is None
    assert proxy_url({"HTTPS_PROXY": "  "}) is None
    assert proxy_url({"https_proxy": "http://a:1"}) == "http://a:1"
    assert proxy_url({"HTTPS_PROXY": "http://a:1",
                      "https_proxy": "http://b:2"}) == "http://a:1"


# ============================================== determinism / no clock
def test_determinism_same_readings_same_bytes():
    a = _build(hosts=_hosts(_DENIED_HERE))
    b = _build(hosts=_hosts(_DENIED_HERE))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_no_wall_clock_anywhere_in_the_probe():
    """A timestamp in this artifact would make every re-run a diff, and the
    gateway hands us several -- so `denied_hosts_from_status` drops them and
    the module reads no clock at all."""
    src = open(SOURCE, encoding="utf-8").read()
    for needle in ("time.time", "datetime", "import time", "utcnow",
                   "monotonic"):
        assert needle not in src, needle


def test_no_timestamp_survives_into_the_document():
    doc = _build(hosts=_hosts(_DENIED_HERE),
                 proxy={"configured": True, "status_endpoint": "read",
                        "hosts_denied_in_status_ledger":
                            ["releases.lean-lang.org"]})
    blob = json.dumps(doc)
    assert "2026-" not in blob and '"ts"' not in blob


def test_regenerate_byte_identical(tmp_path):
    doc = _build()
    p1 = os.path.join(str(tmp_path), "a.json")
    p2 = os.path.join(str(tmp_path), "b.json")
    _write(doc, p1)
    _write(_build(), p2)
    assert open(p1, "rb").read() == open(p2, "rb").read()
    assert open(p1, "rb").read().endswith(b"\n")


# ================================================== schema / pins / honesty
def test_top_level_schema():
    assert set(_build()) == {"derived_from", "honesty", "hosts", "pins",
                             "proxy", "scope", "toolchain", "verdict"}


def test_host_rows_are_sorted_and_exactly_shaped():
    rows = _build()["hosts"]
    assert [r["host"] for r in rows] == sorted(r["host"] for r in rows)
    for r in rows:
        assert set(r) == {"host", "port", "required", "needed_for", "state",
                          "detail", "denial_in_status_ledger"}
        assert r["state"] in HOST_STATES
        # every host says WHY it is needed: a host list without reasons is
        # not a runbook, and this list is what the runbook cites.
        assert len(r["needed_for"]) > 20


def test_every_declared_host_names_a_reason_and_the_blocker_is_named():
    reasons = {s["host"]: s["needed_for"] for s in HOSTS}
    assert "releases.lean-lang.org" in reasons
    assert "elan.lean-lang.org" in reasons
    # github/raw are measured precisely so the runbook can say they ALREADY
    # work -- dropping them would leave the operator over-allowing hosts.
    assert "github.com" in reasons and "raw.githubusercontent.com" in reasons


def test_pins_are_read_from_common_not_typed_here():
    pins = _build()["pins"]
    assert pins["lean_toolchain"] == common.LEAN_TOOLCHAIN
    assert pins["mathlib_commit"] == common.MATHLIB_COMMIT


def test_derived_from_pins_current_inputs():
    doc = _build()
    assert set(doc["derived_from"]) == set(INPUTS)
    for rel in INPUTS:
        live = common.sha256_bytes(open(os.path.join(ROOT, rel), "rb").read())
        assert doc["derived_from"][rel] == live, rel


def test_a_missing_input_is_pinned_absent_not_omitted(tmp_path):
    doc = _build(root=str(tmp_path))
    assert set(doc["derived_from"]) == set(INPUTS)
    assert all(v == INPUT_ABSENT for v in doc["derived_from"].values())


def test_honesty_string_says_what_the_reading_is_not():
    h = _build()["honesty"]
    assert h and len(h) > 200
    low = h.lower()
    # the three claims a reader could otherwise over-read out of lean-local
    assert "never" in low
    assert "sufficient" in low          # a local green is not the verdict
    assert "lane" in low                # the lane still is
    assert "never retried" in low       # the proxy rule


def test_scope_string_warns_that_a_committed_verdict_is_not_a_licence():
    scope = _build()["scope"]
    assert "container" in scope.lower()
    assert "licenses nothing" in scope.lower()


def test_measure_toolchain_is_injectable_and_reads_the_pinned_paths():
    """Drivable with no toolchain present: the readings are injected, so the
    tool is testable in exactly the container that motivated it."""
    got = measure_toolchain(isdir=lambda p: True, lean_available=lambda: True)
    assert got["lean_available"] is True
    assert got["toolchain_dir"] == common.LEAN_TOOLCHAIN_DIR
    assert got["mathlib_dir"] == common.LEAN_MATHLIB_DIR
    assert common.LEAN_TOOLCHAIN.split(":")[-1] in got["toolchain_dir"]
    off = measure_toolchain(isdir=lambda p: False, lean_available=lambda: False)
    assert off["lean_available"] is False
    assert off["toolchain_dir_present"] is False


# ================================== the rule and its mechanism cannot drift
_PLAN_NEEDLE = "tools/lean_env_probe.py"


def _plan_rule_citation():
    """(normalized plan, index of the citation that sits INSIDE §3.1 rule 3).

    Whitespace-normalized because the plan is hard-wrapped, and searched for
    the occurrence whose preceding window is the additive-class rule rather
    than the first occurrence anywhere -- §3.1's preamble cites the probe
    too, and a tooth satisfied by the preamble would not be guarding the
    rule."""
    plan = " ".join(open(PLAN, encoding="utf-8").read().split())
    start = 0
    while True:
        idx = plan.find(_PLAN_NEEDLE, start)
        if idx < 0:
            return plan, -1
        if "additive-class rule" in plan[max(0, idx - 4000):idx].lower():
            return plan, idx
        start = idx + 1


def test_plan_cites_this_probe_inside_the_additive_class_rule():
    """The growth_protocol teeth-index idiom (and test_fg_reflect_shape's own
    drift pin): a rule whose mechanism is unnamed decays back into prose the
    first time someone rewrites the paragraph.  §3.1 rule 3 is now
    CONDITIONAL on a measurement, which makes the citation load-bearing."""
    plan, idx = _plan_rule_citation()
    assert _PLAN_NEEDLE in plan, (
        f"PLAN_FRAGMENT.md no longer names {_PLAN_NEEDLE}: §3.1 rule 3's "
        "capability condition would be an assumption again.")
    assert idx >= 0, (
        f"{_PLAN_NEEDLE} is cited in PLAN_FRAGMENT.md but no longer inside "
        "the additive-class rule (§3.1 rule 3).")


def test_the_plan_states_the_lane_is_still_the_final_verdict():
    """The conditional relaxes WHO MAY AUTHOR tower-class work; it must not
    be readable as relaxing what counts as done."""
    plan, idx = _plan_rule_citation()
    assert idx >= 0
    window = plan[max(0, idx - 2500):idx + 2500].lower()
    assert "necessary" in window and "never sufficient" in window
    assert VERDICT_LOCAL in window
    assert "final verdict" in window


def test_the_plan_says_a_local_toolchain_changes_nothing_about_trust_roots():
    """P5 / the anti-list is GOVERNANCE, not infrastructure.  A toolchain in
    the container must never read as licence over the trust surface."""
    plan, idx = _plan_rule_citation()
    assert idx >= 0
    window = plan[max(0, idx - 2500):idx + 2500].lower()
    assert "anti-list" in window
    assert "governance" in window
    assert "p5" in window


def test_the_plan_binds_the_additive_only_rule_on_every_other_verdict():
    """The permissive arm is the easy half to write and the dangerous half to
    over-read: an unmeasurable environment must never read as permission."""
    plan, idx = _plan_rule_citation()
    window = plan[max(0, idx - 2500):idx + 2500].lower()
    assert "lean-unknown" in window
    assert "binds unchanged" in window or "binds UNCHANGED".lower() in window


def test_the_purchase_driver_prompt_runs_the_probe_before_classifying():
    """The prompt is where the rule is actually executed; a conditional the
    driver never evaluates is a conditional that never fires."""
    prompt = " ".join(open(PROMPTS, encoding="utf-8").read().split())
    assert "tools/lean_env_probe.py" in prompt
    idx = prompt.index("ADDITIVE-CLASS RULE")
    window = prompt[idx:idx + 3000]
    assert "tools/lean_env_probe.py" in window
    assert VERDICT_LOCAL in window
    # the yield clause must survive verbatim for every other verdict
    assert "YIELD" in window


def test_the_runbook_exists_and_names_the_denied_hosts_and_the_verification():
    """The operator-facing half: a verdict nobody can act on is a diagnosis
    with no prescription."""
    path = os.path.join(ROOT, "docs", "lean-capable-environment.md")
    assert os.path.exists(path), path
    doc = open(path, encoding="utf-8").read()
    for needle in ("releases.lean-lang.org", "elan.lean-lang.org",
                   "tools/lean_env_probe.py", VERDICT_LOCAL,
                   "tests/test_fg_reflect_lean.py", ".lean-pins"):
        assert needle in doc, needle


def test_the_committed_artifact_reads_the_true_reading_of_this_container():
    """Not a byte pin -- a container reading changes with the container.  What
    is pinned is that the artifact EXISTS, is in the vocabulary, and carries
    the schema, so a stale or hand-edited file is visible."""
    if not os.path.exists(ARTIFACT):
        pytest.skip("results/lean_env.json not committed in this tree")
    with open(ARTIFACT) as fh:
        doc = json.load(fh)
    assert set(doc) == set(_build())
    v = doc["verdict"]
    assert v in VERDICT_EXACT or v.startswith(VERDICT_PREFIXES), v
    assert {r["host"] for r in doc["hosts"]} == {s["host"] for s in HOSTS}


# ---------------------------------------------------------------------------
# THE ENV-VAR ALIAS (the 2026-07-26 overnight wedge, pinned).
#
# common.py's three Lean directory constants read three override names, and
# two followed a `CGB_*_DIR` convention while `LEAN_MATHLIB_DIR` read the
# un-suffixed `CGB_LEAN_MATHLIB`.  A provisioner following the convention set
# `CGB_LEAN_MATHLIB_DIR`; nothing read it; the fallback fired SILENTLY; and
# every unattended firing yielded on a container that was lean-capable all
# along.  The fix accepts both spellings for Mathlib, un-suffixed PRIMARY.
#
# These teeth run common.py in a SUBPROCESS with the env var set, because the
# constants are bound at import time -- monkeypatching os.environ after import
# would test nothing (the matched-a-mention flaw, environment edition).
#
# Deliberately NOT symmetric: `CGB_LEAN_TOOLCHAIN` (un-suffixed) is already
# taken by the toolchain PIN STRING (`leanprover/lean4:v4.15.0`), so forcing
# an un-suffixed alias onto all three would collide a directory with a pin.
# The tooth asserts what each constant actually reads instead.
# ---------------------------------------------------------------------------

def _resolved(constant, env):
    import subprocess
    full = dict(os.environ)
    for k in ("CGB_LEAN_MATHLIB", "CGB_LEAN_MATHLIB_DIR",
              "CGB_LEAN_TOOLCHAIN_DIR", "CGB_LEAN4CHECKER_DIR"):
        full.pop(k, None)
    full.update(env)
    out = subprocess.run(
        [sys.executable, "-c",
         f"import common; print(getattr(common, '{constant}'))"],
        cwd=ROOT, env=full, capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-500:]
    return out.stdout.strip()


def test_the_dir_suffixed_mathlib_spelling_is_read():
    """The wedge verbatim: a provisioner sets CGB_LEAN_MATHLIB_DIR and
    nothing else.  Before the alias, the fallback fired silently."""
    assert _resolved("LEAN_MATHLIB_DIR",
                     {"CGB_LEAN_MATHLIB_DIR": "/opt/x/mathlib"}) \
        == "/opt/x/mathlib"


def test_the_unsuffixed_mathlib_spelling_stays_primary():
    """Nothing that works today may change meaning: where both are set, the
    documented un-suffixed name wins."""
    assert _resolved("LEAN_MATHLIB_DIR",
                     {"CGB_LEAN_MATHLIB": "/opt/old/mathlib",
                      "CGB_LEAN_MATHLIB_DIR": "/opt/new/mathlib"}) \
        == "/opt/old/mathlib"


def test_all_three_constants_read_their_documented_names():
    """The trio, because the wedge was an ASYMMETRY, not a typo: each
    constant must respond to the name its own comment documents, and the
    default must hold when none is set (CI sets none)."""
    cases = (
        ("LEAN_MATHLIB_DIR", "CGB_LEAN_MATHLIB", "/opt/a"),
        ("LEAN_MATHLIB_DIR", "CGB_LEAN_MATHLIB_DIR", "/opt/b"),
        ("LEAN_TOOLCHAIN_DIR", "CGB_LEAN_TOOLCHAIN_DIR", "/opt/c"),
        ("LEAN4CHECKER_DIR", "CGB_LEAN4CHECKER_DIR", "/opt/d"),
    )
    for constant, name, value in cases:
        assert _resolved(constant, {name: value}) == value, (constant, name)
    # and the unset default is repo-local, not a leak from this shell
    assert _resolved("LEAN_MATHLIB_DIR", {}).endswith("/.lean/mathlib")
# ----------------------------------------------------------------------
# The AVAILABILITY GATE: `common.lean_available()` must ask about the same
# installation the jail actually runs.  MEASURED 2026-07-26 (results/
# lean_gate.md) -- this is the SECOND half of the wedge whose first half is
# the CGB_LEAN_MATHLIB / CGB_LEAN_MATHLIB_DIR asymmetry above, and neither
# half alone moves a driver container off `lean-absent:not-installed`.
# ----------------------------------------------------------------------

def _no_lean_on_path(monkeypatch, tmp_path):
    """Force the PATH and override branches to miss, so a tooth below reads
    the PINNED-toolchain branch and never the session's own container."""
    monkeypatch.delenv("CGB_LEAN", raising=False)
    empty = tmp_path / "empty-bin"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))


def _fake_toolchain(tmp_path):
    """A pinned-toolchain tree shaped the way the image ships one: an
    EXECUTABLE bin/lean, which is what Sandbox mounts at /ro/toolchain."""
    tc = tmp_path / "toolchain"
    (tc / "bin").mkdir(parents=True)
    lean = tc / "bin" / "lean"
    lean.write_text("#!/bin/sh\nexit 0\n")
    lean.chmod(0o755)
    return tc


def test_pinned_toolchain_counts_as_available_without_it_being_on_path(
        monkeypatch, tmp_path):
    """The defect this closes, stated as its consequence.

    `kernel.backends.LeanBackend` never consults the host PATH: `_lean_run_kw`
    puts `LEAN_TOOLCHAIN_DIR`'s own `bin` on the IN-JAIL PATH and every
    cert-time `lean` resolves from there.  A PATH-only gate therefore measured
    a directory the backend does not use, and an image that installs the
    pinned toolchain exactly where the constant says -- without also exporting
    it on PATH -- was read as `lean-absent:not-installed`, the one verdict
    PLAN_FRAGMENT 3.1 rule 3 yields on.  Capable container, yielding driver.
    """
    _no_lean_on_path(monkeypatch, tmp_path)
    mathlib = tmp_path / "mathlib"
    mathlib.mkdir()
    monkeypatch.setattr(common, "LEAN_TOOLCHAIN_DIR",
                        str(_fake_toolchain(tmp_path)))
    monkeypatch.setattr(common, "LEAN_MATHLIB_DIR", str(mathlib))
    assert common.lean_available() is True


def test_a_toolchain_without_mathlib_is_not_available(monkeypatch, tmp_path):
    """The clause that makes this fix SAFE TO LAND ALONE, and the reason it is
    written as the whole mountable installation rather than as a binary.

    A gate that flipped on the binary alone would report capability on a
    container whose Mathlib is missing -- the half-capable state -- and every
    Lean-gated test would then run against an installation `_lean_mounts`
    cannot mount.  MEASURED: that state fails 9 teeth across
    test_anchor_runner / test_reflect_ride / test_import_rt.  So the pinned
    branch demands BOTH directories, which is exactly `_lean_mounts`' own
    requirement set, and until the Mathlib half resolves this clause is inert.
    """
    _no_lean_on_path(monkeypatch, tmp_path)
    monkeypatch.setattr(common, "LEAN_TOOLCHAIN_DIR",
                        str(_fake_toolchain(tmp_path)))
    monkeypatch.setattr(common, "LEAN_MATHLIB_DIR",
                        str(tmp_path / "absent-mathlib"))
    assert common.lean_available() is False


def test_no_toolchain_invents_no_availability(monkeypatch, tmp_path):
    """Nothing present, nothing claimed -- the honest-absence floor."""
    _no_lean_on_path(monkeypatch, tmp_path)
    mathlib = tmp_path / "mathlib"
    mathlib.mkdir()
    monkeypatch.setattr(common, "LEAN_TOOLCHAIN_DIR", str(tmp_path / "nope"))
    monkeypatch.setattr(common, "LEAN_MATHLIB_DIR", str(mathlib))
    assert common.lean_available() is False


def test_a_non_executable_lean_is_not_a_toolchain(monkeypatch, tmp_path):
    """Presence is not enough: a file the jail could not exec is not a
    capability, and reporting it as one would be the fail-OPEN this whole
    gate exists to refuse."""
    _no_lean_on_path(monkeypatch, tmp_path)
    tc = tmp_path / "toolchain"
    (tc / "bin").mkdir(parents=True)
    (tc / "bin" / "lean").write_text("not executable\n")
    (tc / "bin" / "lean").chmod(0o644)
    mathlib = tmp_path / "mathlib"
    mathlib.mkdir()
    monkeypatch.setattr(common, "LEAN_TOOLCHAIN_DIR", str(tc))
    monkeypatch.setattr(common, "LEAN_MATHLIB_DIR", str(mathlib))
    assert common.lean_available() is False


def test_the_gate_names_the_same_bin_the_jail_puts_on_its_path():
    """The ANTI-DRIFT tooth, and the only one that would have caught the
    original defect BEFORE a container met it.

    Two places name the toolchain's executable directory: this gate, and
    `LeanBackend._lean_run_kw`, whose `extra_path` is the jail mount of
    `LEAN_TOOLCHAIN_DIR` plus `/bin`.  The defect was precisely that the gate
    consulted something else, so the invariant worth pinning is that they
    agree on the SUFFIX -- if a future edit moves the binaries, both must
    move together or this goes red.
    """
    import inspect
    from kernel import backends
    gate = inspect.getsource(common.lean_available)
    runkw = inspect.getsource(backends.LeanBackend._lean_run_kw)
    assert 'LEAN_TOOLCHAIN_DIR, "bin", "lean"' in gate, gate
    assert '_RO_TOOLCHAIN + "/bin"' in runkw, runkw
    assert backends.LeanBackend._RO_TOOLCHAIN == "/ro/toolchain"


# ---------------------------------------------------------------------------
# THE FORCE-OFF HALF OF CGB_LEAN (suite discipline in lean-local containers).
#
# 113 tests gate on lean_available(), each a real full-Mathlib elaboration,
# and `full suite before every commit` binds every driver session.  The day
# the capability turned on, the per-commit gate went from ~90 seconds to
# hours, and the first lean-local session ground to a halt mid-suite
# (2026-07-26: the run it promised to report never arrived).  CGB_LEAN=0 runs
# the gate exactly as CI's fast shards run it.  Rule 3 is untouched: the
# capability classification reads the PROBE, which checks mounted directories
# itself and never consults lean_available().
# ---------------------------------------------------------------------------

def _lean_available_with(env):
    import subprocess
    full = dict(os.environ)
    full.pop("CGB_LEAN", None)
    full.update(env)
    out = subprocess.run(
        [sys.executable, "-c", "import common; print(common.lean_available())"],
        cwd=ROOT, env=full, capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-500:]
    return out.stdout.strip()


def test_cgb_lean_0_forces_the_gate_off():
    """The per-commit suite knob: with it, a lean-local container's gate is
    byte-identical to what every pre-lean-local commit ran."""
    assert _lean_available_with({"CGB_LEAN": "0"}) == "False"


def test_cgb_lean_truthy_still_forces_on():
    assert _lean_available_with({"CGB_LEAN": "1"}) == "True"


def test_the_probe_does_not_consult_the_gate():
    """The clause that keeps the knob from masking capability: rule 3's
    classification reads tools/lean_env_probe.py, so the probe module must
    never call lean_available -- checked in its AST, not its prose."""
    import ast
    tree = ast.parse(open(os.path.join(ROOT, "tools", "lean_env_probe.py"),
                          encoding="utf-8").read())
    calls = {n.func.attr if isinstance(n.func, ast.Attribute)
             else getattr(n.func, "id", "")
             for n in ast.walk(tree) if isinstance(n, ast.Call)}
    assert "lean_available" not in calls, (
        "the probe consults lean_available(); CGB_LEAN=0 during a suite run "
        "could then mask a capability the classification must see")
