"""Milestone 6: engineer and log a dual-checker disagreement.

The dual-checker rule feeds one SMT obligation to Z3 and CVC5 independently
and requires them to agree.  We submit a proof goal at the edge of what each
solver decides automatically -- nonlinear integer arithmetic, which is
undecidable in general -- with per-solver time limits set so one solver
closes it and the other returns `unknown`.  The kernel logs the split as a
first-class `dual-checker-disagreement` event with full artifacts, and
issues NO certificate.

The obligation is a genuine theorem (so a "pass" is correct where a solver
manages it); the disagreement reflects a solver limitation, exactly the
class of event the rule is designed to surface.
"""
from __future__ import annotations

import kernel
from kernel.certs import Certificate

# Goal: for all integers, (x*x - 2*x*y + y*y) >= 0   [ == (x-y)^2 >= 0 ].
# Asserting its negation is UNSAT (the goal is valid).  Nonlinear integer
# arithmetic is undecidable; with a short per-solver time budget the two
# engines can split (one proves UNSAT, the other returns unknown).
NONLINEAR_OBLIGATION = """
(set-logic QF_NIA)
(declare-fun x () Int)
(declare-fun y () Int)
(assert (< (+ (* x x) (* y y)) (* 2 (* x y))))
(check-sat)
"""


def run(registry, time_ms=25):
    from kernel.backends import SmtBackend
    smt = SmtBackend()
    # tighten CVC5's budget so it is more likely to time out on the nonlinear
    # goal while Z3's preprocessing still closes it -- engineered split.
    z = smt.run_z3(NONLINEAR_OBLIGATION, timeout_ms=20000)   # Z3 proves it
    c = smt.run_cvc5(NONLINEAR_OBLIGATION, timeout_ms=time_ms)  # CVC5 times out -> unknown
    channels = [z, c]
    passes = [ch for ch in channels if ch["result"] == "pass"]
    fails = [ch for ch in channels if ch["result"] != "pass"]
    if passes and fails:
        registry.log_event("dual-checker-disagreement", {
            "obligation": "(x-y)^2 >= 0 over Int, negation UNSAT",
            "smtlib": NONLINEAR_OBLIGATION,
            "channels": channels,
            "note": "nonlinear integer arithmetic at the edge of automatic "
                    "decidability; solver limitation, not an oracle bug"})
        return {"status": "disagreement-logged",
                "channels": [(ch["backend"], ch["result"]) for ch in channels]}
    # If they happened to agree, report so the caller can retighten budgets.
    return {"status": "agreed",
            "channels": [(ch["backend"], ch["result"]) for ch in channels]}
