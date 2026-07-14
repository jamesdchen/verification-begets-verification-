"""P1.4 channel (a): bounded LTLf semantics as SMT-LIB, dual-checked Z3 & CVC5.

Two obligations live here, both over a symbolic finite trace:

  * protocol_temporal_smtlib(model, obligation, K)
        The "liveness becomes safety at the session boundary" proof.  Over the
        idle-disciplined protocol unrolling (generators.protocol_gen._unrolled),
        assert that a COMPLETE (terminal-ending) legal session VIOLATES the LTLf
        demand.  unsat  = the demand holds on every complete session within K;
        sat    = a STRANDED trace exists (the shortest is extracted by
                 generators.protocol_gen.temporal_counterexample).
        The monitor's discharge guard -- terminal actions refused while the
        obligation is pending -- is encoded here as the enforcement whose
        COMPLETENESS the query verifies: a completing action that is NOT a marked
        terminal (e.g. a forgotten `abandon` exit that still ends the session)
        escapes the guard, which is exactly the defect the stranding query
        catches.

  * monitor_agreement_smtlib(table, initial, accepting, kind, params,
                             alphabet, max_len)
        monitor-cert channel 1: encode the EMITTED monitor DFA's table walk AND
        the LTLf semantics of the demand over every action trace up to max_len,
        and assert they DISAGREE on acceptance.  unsat = the baked table matches
        the LTLf semantics for all traces up to the bound (the certified claim);
        sat = a mutated/incorrect table (caught with the divergent trace).  The
        table is READ FROM the artifact bytes (never executed) so a mutation in
        the shipped monitor.py is what is under test.

ATOM HYGIENE / ALIGNMENT: these are ACTION-atom formulas only (F/U/before/within
over action occurrences), so both the SMT channel here and the flloat channel in
ref_stepper.py are genuinely independent decision procedures for the SAME LTLf
semantics.  Context-predicate temporal demands (e.g. "eventually balance==0") are
SMT-channel-only (flloat cannot see integers) and are out of scope here.
"""
from __future__ import annotations


class UnsupportedObligation(Exception):
    pass


# --------------------------------------------------------------- protocol side
def protocol_temporal_smtlib(model, obligation, K: int) -> str:
    """SMT-LIB asserting: a legal, idle-disciplined, COMPLETE session violates
    the temporal `obligation`.  Only `eventually` is supported today (the Phase-1
    demo fragment); other kinds raise UnsupportedObligation."""
    return _finish(protocol_temporal_solver(model, obligation, K)[0])


def protocol_temporal_solver(model, obligation, K: int):
    """(z3 Solver, vars) form of the stranding query -- so a counterexample can
    be extracted from a sat model (protocol_gen.temporal_counterexample)."""
    import z3
    from generators import protocol_gen as pg

    kind = obligation["kind"]
    if kind != "eventually":
        raise UnsupportedObligation(
            f"protocol temporal obligation kind {kind!r} not yet supported "
            "(Phase-1 fragment is 'eventually')")

    s, v = pg._unrolled(model, K)
    act, IDLE = v["act"], v["IDLE"]
    aidx = {a.name: i for i, a in enumerate(model.actions)}
    a_idx = aidx[obligation["action"]]
    oid = obligation["id"]

    # disch[i]: the discharge action has occurred at some step in 0..i-1.  This
    # is exactly the monitor's non-pending bit for the `eventually` kind.
    disch = [z3.Bool(f"disch_{oid}_{i}") for i in range(K + 1)]
    s.add(disch[0] == z3.BoolVal(False))
    for i in range(K):
        s.add(disch[i + 1] == z3.Or(disch[i], act[i] == a_idx))

    # The MONITOR'S DISCHARGE GUARD: a MARKED-terminal action may fire only when
    # the obligation is already discharged (== the dispatcher refusing a terminal
    # call while the monitor pends).  Unmarked completing actions are NOT guarded
    # -- that gap is the stranding this query detects.
    for ti in (aidx[n] for n in model.terminal_actions()):
        for i in range(K):
            s.add(z3.Implies(act[i] == ti, disch[i]))

    # A trace "completes" when its LAST REAL action leads out of the session
    # (marked terminal OR into a sink state).  P1.3: an F obligation may only be
    # asserted violated on a completing trace, else every incomplete prefix
    # vacuously "violates" F(a).
    comp_idx = [aidx[n] for n in model.completing_actions()]
    completes = []
    for j in range(K):
        is_real = act[j] != IDLE
        is_last = z3.BoolVal(True) if j == K - 1 else (act[j + 1] == IDLE)
        comp = z3.Or([act[j] == ci for ci in comp_idx]) \
            if comp_idx else z3.BoolVal(False)
        completes.append(z3.And(is_real, is_last, comp))

    s.add(z3.Not(disch[K]))      # F(action) is FALSE: it never occurs
    s.add(z3.Or(completes))      # ... yet the session completes -> STRANDED
    return s, v


# ---------------------------------------------------------------- monitor side
def monitor_agreement_smtlib(table: dict, initial: int, accepting, kind: str,
                             params: dict, alphabet, max_len: int) -> str:
    """SMT-LIB asserting the emitted monitor table and the LTLf semantics of the
    demand DISAGREE on acceptance for some action trace of length <= max_len.

    Encoding: a trace sym[0..L-1] over the sorted alphabet plus an END sentinel
    (absorbing, so shorter traces are covered).  st[i] walks `table`; the LTLf
    acceptance predicate `_ltlf_accept` is the independent semantics.  unsat means
    the two agree on every trace up to the bound."""
    import z3

    acts = sorted(alphabet)
    n = len(acts)
    END = n                                # sentinel value past the alphabet
    adx = {a: i for i, a in enumerate(acts)}
    L = max_len
    s = z3.Solver()

    sym = [z3.Int(f"sym_{i}") for i in range(L)]
    for i in range(L):
        s.add(sym[i] >= 0, sym[i] <= END)
        if i + 1 < L:                      # END is an absorbing suffix
            s.add(z3.Implies(sym[i] == END, sym[i + 1] == END))

    # monitor walk over the BAKED table (read from the artifact, not rebuilt)
    st = [z3.Int(f"st_{i}") for i in range(L + 1)]
    s.add(st[0] == initial)
    states = sorted(table)
    for i in range(L):
        s.add(z3.Implies(sym[i] == END, st[i + 1] == st[i]))
        for q in states:
            row = table[q]
            for a in acts:
                # every alphabet symbol has a row entry (complete table)
                s.add(z3.Implies(z3.And(st[i] == q, sym[i] == adx[a]),
                                 st[i + 1] == row[a]))
    mon_accept = z3.Or([st[L] == q for q in sorted(accepting)]) \
        if accepting else z3.BoolVal(False)

    ltlf_accept = _ltlf_accept(kind, params, sym, adx, END, L)
    s.add(mon_accept != ltlf_accept)       # look for ANY disagreement
    return _finish(s)


def _ltlf_accept(kind, params, sym, adx, END, L):
    """The independent LTLf acceptance predicate over the symbolic trace, per
    kind, matching generators.monitor_gen's formula semantics on finite traces.
    `sym[i]==END` marks positions past the trace end."""
    import z3

    def is_act(i, name):
        return z3.And(sym[i] != END, sym[i] == adx[name])

    if kind == "eventually":               # F(a): a occurs at some position
        a = params["action"]
        return z3.Or([is_act(i, a) for i in range(L)])
    if kind == "within":                   # a in one of the first `steps` slots
        a, k = params["action"], int(params["steps"])
        return z3.Or([is_act(i, a) for i in range(min(k, L))])
    if kind == "until":                    # pre U post (strong): post reached,
        pre, post = params["pre"], params["post"]   # pre held strictly before
        clauses = []
        for k in range(L):
            before = z3.And([is_act(j, pre) for j in range(k)]) \
                if k else z3.BoolVal(True)
            clauses.append(z3.And(is_act(k, post), before))
        return z3.Or(clauses)
    if kind == "before":                   # second must not occur before first
        first, second = params["first"], params["second"]
        bad = []
        for i in range(L):
            no_first_yet = z3.And([sym[j] != adx[first] for j in range(i)]) \
                if i else z3.BoolVal(True)
            bad.append(z3.And(is_act(i, second), no_first_yet))
        return z3.Not(z3.Or(bad))
    raise UnsupportedObligation(f"unknown obligation kind {kind!r}")


def _finish(s) -> str:
    text = "(set-logic QF_LIA)\n" + s.to_smt2()
    if "(check-sat)" not in text:
        text += "\n(check-sat)\n"
    return text
