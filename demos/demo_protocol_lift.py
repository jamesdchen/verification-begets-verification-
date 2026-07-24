#!/usr/bin/env python3
"""Protocol lift via Angluin L* -- learn an incumbent stateful service's
protocol as a Mealy machine and certify it conformance-relative to a declared
state bound n.  No LLM: the whole path is deterministic black-box learning
(membership + equivalence queries against the sandboxed incumbent) plus the
existing dual-BMC + conformance protocol-cert.

Part A -- recover the advertised order lifecycle (init -> authed -> paid ->
shipped -> closed) from the black box and certify it: dual SMT proof (Z3 &
CVC5) plus the emitted session validator vs. an independent reference
simulator, exactly the protocol-cert demo_protocol.py uses.

Part B -- the honesty tooth.  The incumbent hides a `void` trapdoor state
reachable only by a length-6 sequence (two refunds after a closed order).  At
a SMALL declared state bound the W-method equivalence oracle never explores
deep enough: L* collapses closed/refund_pending/void into one state and the
certificate is BLIND to the trapdoor.  At a LARGER bound the W-method finds a
counterexample, L* refines, and the trapdoor state is recovered -- caught.  The
certificate never lies about which n it holds for; the small-n cert's own
non_claims say a deeper state is invisible.

Part C -- the P3.5 INTEGRATION tooth: the three capabilities COMPOSE.  Bridge the
Part-A lifted protocol into a cageable service meta-spec, wrap the SAME incumbent
(behind a thin abstraction adapter) in the Phase-2 CAGE, and fold a Phase-1
MONITOR obligation over the lifted alphabet into it.  Then show: (1) TRANSPARENCY
-- a legal lifted run is byte-identical caged vs bare; (2) CONTAINMENT -- the
trapdoor's SECOND refund (refund_pending->void, which has no tool in the single-
transition service and so sits OUTSIDE the caged protocol) is REFUSED by the cage
at the learned-protocol boundary exactly where the bare incumbent tips into the
void god-mode; (3) the whole lifted+caged+monitored artifact earns a
`cage-conformance` certificate (tier "monitored").  Lift (P3) -> Cage (P2) ->
Monitor (P1), certified together.
"""
from __future__ import annotations

# demos/-layout shim: put the repo root on sys.path so the flat top-level
# modules (common, cgb, ...) resolve under direct execution
# (python3 demos/<name>.py).
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import collections
import json
import pathlib
import sys

import common
from run import protocol_lift, guarded
from buildloop import lstar
from generators import service_model, monitor_gen
from kernel.certs import Certificate

REQUIRES_LLM = False

INCUMBENT = pathlib.Path("specs/incumbent/order_service.py").read_text()
ABSTRACTION = lstar.ORDER_ABSTRACTION

SMALL_N = 5      # equals the naive lifecycle size -> too shallow for the trapdoor
LARGE_N = 7      # >= the true state count -> W-method reaches the trapdoor

# The trapdoor is reachable only by this length-6 sequence; the distinguishing
# probe appends one input on which `void` (god-mode: accepts everything) and the
# advertised `closed` state disagree.
TRAPDOOR_WITNESS = ("login", "pay_big", "ship", "close", "refund", "refund", "login")


def _incumbent_ground_truth(seq):
    """Query the real (sandboxed) incumbent for the honest output sequence."""
    orc = lstar.Oracle(INCUMBENT, list(ABSTRACTION), ABSTRACTION)
    return orc.outseq(seq)


def _print_cert(tag, cert):
    print(f"  [{tag}] tier={cert['tier']}  learned_states={cert['learned_states']}"
          f"  rounds={cert['equivalence_rounds']}  "
          f"protocol_cert.certified={cert['protocol_cert']['certified']}")
    print(f"        channels={cert['protocol_cert']['channels']}")
    print(f"        learn_stats={cert['learn_stats']}")


def part_a():
    print("== Part A: recover the order lifecycle from the black box and "
          "certify it ==")
    res = protocol_lift.lift_protocol(INCUMBENT, "order_lift", ABSTRACTION,
                                      LARGE_N)
    H = res.machine
    lc = H.lifecycle_path(("login", "pay_big", "ship", "close"))
    outputs = [o for _, o, _ in lc]
    states = [H.initial] + [st for _, _, st in lc]
    lifecycle_ok = (outputs == ["ok", "ok", "ok", "ok"]
                    and len(set(states)) == 5)          # 5 distinct states
    print(f"  learned lifecycle login->pay->ship->close: outputs={outputs} "
          f"states={states}")
    print(f"  distinct-lifecycle-states={len(set(states))}  "
          f"lift certified={res.ok} ({res.status})")
    _print_cert("A", res.certificate)
    recovered = bool(lifecycle_ok and res.ok)
    print(f"  => lifecycle recovered AND certified: {recovered}")
    return recovered, res


def part_b(res_large):
    print("\n== Part B: trapdoor MISSED at small n, CAUGHT at larger n ==")
    truth = _incumbent_ground_truth(TRAPDOOR_WITNESS)
    print(f"  incumbent ground truth on trapdoor witness {list(TRAPDOOR_WITNESS)}:")
    print(f"    {list(truth)}  (last='{truth[-1]}' -- the hidden god-mode 'ok')")

    small = protocol_lift.lift_protocol(INCUMBENT, "order_lift", ABSTRACTION,
                                        SMALL_N)
    large = res_large            # reuse Part A's large-n lift
    ps = small.machine.run_outputs(TRAPDOOR_WITNESS)
    pl = large.machine.run_outputs(TRAPDOOR_WITNESS)

    print(f"\n  small n={SMALL_N}: states={small.certificate['learned_states']}"
          f"  rounds={small.certificate['equivalence_rounds']}"
          f"  predicts last='{ps[-1]}'  vs incumbent '{truth[-1]}'")
    _print_cert("small", small.certificate)
    print("  small-n non_claims (the certificate is honest about its blindness):")
    for nc in small.certificate["non_claims"][:2]:
        print(f"      - {nc}")

    print(f"\n  large n={LARGE_N}: states={large.certificate['learned_states']}"
          f"  rounds={large.certificate['equivalence_rounds']}"
          f"  predicts last='{pl[-1]}'  vs incumbent '{truth[-1]}'")
    print(f"  counterexample that exposed the trapdoor: "
          f"{large.certificate['counterexamples']}")

    # MISSED: small model disagrees with the incumbent on the trapdoor probe
    #         (it says 'reject' where the incumbent says 'ok') AND has fewer
    #         states than the true machine.
    missed = (ps[-1] != truth[-1]
              and small.certificate["learned_states"]
              < large.certificate["learned_states"])
    # CAUGHT: large model matches the incumbent on the trapdoor probe and grew
    #         extra states via a real equivalence counterexample.
    caught = (pl == truth
              and pl[-1] == "ok"
              and large.certificate["equivalence_rounds"] >= 1
              and large.certificate["learned_states"]
              > small.certificate["learned_states"]
              and large.ok)
    print(f"\n  => trapdoor missed at small n={SMALL_N}: {missed}")
    print(f"  => trapdoor caught at larger n={LARGE_N}: {caught}")
    return missed, caught


def determinism_tooth():
    """The oracle checks determinism (runs the first batch twice); a
    nondeterministic incumbent yields a first-class result, not a wrong model."""
    print("\n== Determinism tooth: a nondeterministic incumbent is refused ==")
    nondet = (
        "import random\n"
        "class Incumbent:\n"
        "    def __init__(self):\n"
        "        self.s = 'init'\n"
        "    def call(self, tool, args):\n"
        "        return random.choice(['ok', 'reject'])\n"
    )
    res = protocol_lift.lift_protocol(nondet, "flaky", ABSTRACTION, SMALL_N)
    ok = (res.status == "nondeterministic-incumbent")
    print(f"  status={res.status!r}  -> first-class refusal: {ok}")
    return ok


# --------------------------------------------------------------------------- #
#  Part C bridge: a LIFTED protocol -> a cageable service.                     #
# --------------------------------------------------------------------------- #
def _lifted_service_spec(H, name, *, obligation=None, terminal=None):
    """BRIDGE (composes existing public APIs, no kernel/lift edits): project the
    learned Mealy machine's ``ok`` edges to a *cageable* service meta-spec
    (generators.service_model).  BFS spanning-tree over the ok-transitions from
    the initial state, keeping the FIRST edge per tool name -- a service tool is
    a single transition, so the trapdoor's SECOND ``refund`` (refund_pending->
    void) gets NO tool and is structurally OUTSIDE the caged protocol.  That is
    exactly the learned-protocol boundary the cage then enforces.  Each tool
    takes an empty input schema: the concrete (tool, args) are supplied by the
    abstraction adapter, so the abstract lifted alphabet IS the dispatcher's tool
    alphabet.  Context/safety mirror ``Mealy.to_protocol_spec`` (a data-free
    structural invariant)."""
    tree, seen, used = [], {H.initial}, set()
    q = collections.deque([H.initial])
    while q:
        st = q.popleft()
        for sym in H.alphabet:
            if H.out[(st, sym)] != "ok":
                continue
            nxt = H.delta[(st, sym)]
            if nxt in seen or sym in used:
                continue
            seen.add(nxt); used.add(sym)
            tree.append((st, sym, nxt)); q.append(nxt)
    states = [H.initial] + [nxt for _, _, nxt in tree]
    empty = {"type": "object", "properties": {}, "required": [],
             "additionalProperties": False}
    tools = []
    for frm, sym, to in tree:
        t = {"name": sym, "from": frm, "to": to, "input_schema": empty}
        if terminal is not None and sym == terminal:
            t["terminal"] = True
        tools.append(t)
    spec = {"name": name,
            "context": {"ok": {"init_min": 0, "init_max": 0}},
            "states": states, "initial": H.initial, "tools": tools,
            "safety": {"when": "*",
                       "invariant": {"op": "==", "left": "ok", "right": 0}}}
    if obligation is not None:
        spec["obligations"] = [obligation]
    return spec


def _adapter_incumbent_src():
    """The SAME black-box incumbent, behind a thin abstraction adapter.  The cage
    dispatches the ABSTRACT lifted symbols (login/pay_big/ship/close/refund);
    this maps each back to the concrete (tool, args) of the DECLARED abstraction
    (lstar.ORDER_ABSTRACTION) and calls the real order_service ``Incumbent``.
    ``_RealIncumbent = Incumbent`` captures the real class BEFORE the name is
    rebound to the adapter, so the cage's ``from incumbent import Incumbent``
    loads the adapter (which threads all its state, incl. the real incumbent's,
    in instance attributes -- the frozen incumbent interface)."""
    return INCUMBENT + "\n\n_ABS = " + json.dumps(ABSTRACTION) + "\n" + '''
_RealIncumbent = Incumbent


class Incumbent:
    def __init__(self):
        self._real = _RealIncumbent()

    def call(self, tool, args):
        spec = _ABS.get(tool)
        if spec is None:
            return "__error__"
        return self._real.call(spec["tool"], spec["args"])
'''


def part_c(res_large):
    print("\n== Part C (P3.5): the LIFTED protocol run CAGED + MONITORED ==")
    H = res_large.machine

    # 1. BRIDGE the learned protocol to a cageable service, with a Phase-1 monitor
    obligation = {"id": "eventually_ship", "kind": "eventually", "action": "ship"}
    spec = _lifted_service_spec(H, "order_lift_svc",
                                obligation=obligation, terminal="close")
    m = service_model.parse_service_spec(json.dumps(spec))
    print(f"  bridged lifted->service tools: "
          f"{[(t.name, t.frm, t.to) for t in m.tools]}")
    print("  learned-protocol boundary: the trapdoor 2nd refund "
          "(refund_pending->void) has NO tool -- outside the caged protocol")

    # Phase-1 monitor over the LIFTED alphabet (the cage folds this SAME DFA in
    # via generators.monitor_gen.build_monitor -> monitor_<id>.py).
    mon = monitor_gen.build_monitor(obligation["kind"],
                                    {"action": obligation["action"]},
                                    [t.name for t in m.tools])
    print(f"  Phase-1 monitor {obligation['id']!r}: LTLf={mon['meta']['formula']!r}"
          f"  states={mon['meta']['num_states']}  (composed into the cage; "
          f"redundant here -- sequencing already orders ship before close)")

    # 2. wrap the SAME incumbent (behind the abstraction adapter) in the CAGE
    cage = guarded.Cage(m, _adapter_incumbent_src())
    print(f"  caged artifact files: {sorted(cage.files())}")

    # 3. TRANSPARENCY: a legal lifted run is byte-identical caged vs bare
    legal = guarded.legal_sessions(m)
    transparent = bool(legal)
    for s in legal:
        caged = cage.run(s["init"], s["seq"])
        bare = cage.run_bare(s["init"], s["seq"])
        for i in range(len(s["seq"])):
            ok = (caged[i].get("ok")
                  and common.canonical_json(caged[i].get("result"))
                  == common.canonical_json(bare[i].get("result")))
            transparent = transparent and ok
        print(f"  transparency: legal lifted run {[t for t, _ in s['seq']]}"
              f"  caged == bare = {transparent}")

    # 4. CONTAINMENT: the trapdoor's SECOND refund.  The bare incumbent tips into
    #    void (god-mode 'ok'); the caged dispatcher refuses it at the learned-
    #    protocol boundary (there is no refund_pending->void tool).
    init = {"ok": 0}
    trap = [["login", {}], ["pay_big", {}], ["ship", {}], ["close", {}],
            ["refund", {}], ["refund", {}]]
    caged = cage.run(init, trap)
    bare = cage.run_bare(init, trap)
    contained = (not caged[-1].get("ok")
                 and bare[-1].get("acted") and bare[-1].get("result") == "ok")
    print(f"  containment: trapdoor 2nd refund -> caged={caged[-1]}  bare={bare[-1]}")
    print(f"  => cage REFUSES (layer {caged[-1].get('layer')!r}) where the bare "
          f"incumbent ACTS into void god-mode 'ok': {contained}")

    # 5. CERTIFY the whole lifted+caged+monitored artifact (cage-conformance).
    v = guarded.certify_cage(cage, m)
    certified = isinstance(v, Certificate)
    for c in (v.channels if certified else v.to_dict()["channels"]):
        print(f"  {'OK' if c['result'] == 'pass' else 'XX'} channel "
              f"{c['backend']:<18} {c['result']} -- {str(c.get('detail'))[:76]}")
    tier = getattr(v, "tier", "")
    print(f"  -> lifted cage certified: {certified}  tier={tier!r}  "
          f"#non_claims={len(getattr(v, 'non_claims', ()))}")

    result = bool(transparent and contained and certified)
    print(f"  => part C (lifted protocol CAGED + MONITORED + certified): {result}")
    return result


if __name__ == "__main__":
    a, res_large = part_a()
    b_missed, b_caught = part_b(res_large)
    c = part_c(res_large)
    det = determinism_tooth()
    summary = {
        "part_a_lifecycle_recovered": bool(a),
        "part_b_trapdoor_missed_at_small_n": bool(b_missed),
        "part_b_trapdoor_caught_at_larger_n": bool(b_caught),
        "part_c_lifted_service_caged": bool(c),
    }
    print("\nsummary:", json.dumps(summary))
    sys.exit(0 if all([a, b_missed, b_caught, c, det]) else 1)
