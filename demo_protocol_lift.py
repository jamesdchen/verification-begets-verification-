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
"""
from __future__ import annotations

import json
import pathlib
import sys

from run import protocol_lift
from buildloop import lstar

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


if __name__ == "__main__":
    a, res_large = part_a()
    b_missed, b_caught = part_b(res_large)
    det = determinism_tooth()
    summary = {
        "part_a_lifecycle_recovered": bool(a),
        "part_b_trapdoor_missed_at_small_n": bool(b_missed),
        "part_b_trapdoor_caught_at_larger_n": bool(b_caught),
    }
    print("\nsummary:", json.dumps(summary))
    sys.exit(0 if all([a, b_missed, b_caught, det]) else 1)
