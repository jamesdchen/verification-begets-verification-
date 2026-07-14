"""P1.4 channel (a): bounded LTLf semantics as SMT-LIB, dual-checked Z3 & CVC5.

Two obligations live here, both over a symbolic finite trace:

  * protocol_temporal_smtlib(model, obligation, K)
        The "liveness becomes safety at the session boundary" proof, as PRODUCT
        DEAD-END REACHABILITY over the (protocol control state x monitor state)
        product.  Over the idle-disciplined protocol unrolling
        (generators.protocol_gen._unrolled), with the monitor's discharge guard
        applied (a marked-terminal action fires only once the obligation is
        discharged -- the dispatcher refusing a terminal call while the monitor
        pends), assert that a reachable configuration is a STRAND: the monitor is
        PENDING and the control state is an obligation DEAD-END -- one from which
        NO sequence of enabled protocol actions can ever discharge the demand.
        unsat = every reachable pending config can still discharge (certify);
        sat   = a strand exists (the shortest is extracted by
                generators.protocol_gen.temporal_counterexample).
        This does NOT depend on incidental sink/terminal structure, so it cannot
        be defeated by an inert self-loop that merely makes a session-ending
        state a non-sink (the old "last real action is a completing action"
        query was: an unguarded `abandon: held->closed` plus a dead
        `noop: closed->closed` hid the strand).  A forgotten unguarded
        session-ender (an `abandon` that is not marked terminal) reaches the
        dead-end while pending -> caught.

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
    be extracted from a sat model (protocol_gen.temporal_counterexample).

    STRAND == a reachable (control state x monitor state) config that is PENDING
    and an obligation DEAD-END.  The monitor for F(action) is the 2-state
    {pending, discharged} DFA; `disch[i]` is exactly its state bit (the demanded
    action has occurred by step i).  We unroll the legal protocol transitions,
    apply the monitor discharge guard to marked terminals, and assert that some
    reachable step lands in a dead-end control state while still pending."""
    import z3
    from generators import protocol_gen as pg

    kind = obligation["kind"]
    if kind != "eventually":
        raise UnsupportedObligation(
            f"protocol temporal obligation kind {kind!r} not yet supported "
            "(Phase-1 fragment is 'eventually')")

    s, v = pg._unrolled(model, K)
    act, ctrl = v["act"], v["ctrl"]
    aidx = {a.name: i for i, a in enumerate(model.actions)}
    a_idx = aidx[obligation["action"]]
    oid = obligation["id"]

    # disch[i]: the discharge action has occurred at some step in 0..i-1.  This
    # is exactly the monitor's non-pending bit for the F(action) monitor DFA
    # (pending <-> not disch).
    disch = [z3.Bool(f"disch_{oid}_{i}") for i in range(K + 1)]
    s.add(disch[0] == z3.BoolVal(False))
    for i in range(K):
        s.add(disch[i + 1] == z3.Or(disch[i], act[i] == a_idx))

    # The MONITOR'S DISCHARGE GUARD: a MARKED-terminal action may fire only when
    # the obligation is already discharged (== the dispatcher refusing a terminal
    # call while the monitor pends).  This is the enforcement whose completeness
    # the query verifies; an UNMARKED session-ender (e.g. a forgotten `abandon`)
    # is NOT guarded, so it can fire while pending -- the stranding gap.
    for ti in (aidx[n] for n in model.terminal_actions()):
        for i in range(K):
            s.add(z3.Implies(act[i] == ti, disch[i]))

    # PRODUCT DEAD-END: control states from which the obligation can NEVER be
    # discharged (see _deadend_states).  A reachable (control in dead-end,
    # monitor pending) config is a genuine strand -- the demand is pending and no
    # enabled continuation can ever discharge it.  This replaces the old
    # "last real action is a completing (terminal/to-sink) action" query, which
    # an inert self-loop could defeat by making a session-ending state a non-sink.
    dead_idx = [model.idx(p) for p in _deadend_states(model, obligation)]
    stranded = []
    for j in range(K + 1):
        in_dead = z3.Or([ctrl[j] == di for di in dead_idx]) \
            if dead_idx else z3.BoolVal(False)
        stranded.append(z3.And(z3.Not(disch[j]), in_dead))   # pending & dead-end
    s.add(z3.Or(stranded))       # a reachable pending dead-end -> STRANDED
    return s, v


def _deadend_states(model, obligation):
    """Control states from which the demanded F-obligation can NEVER be
    discharged, in the (protocol control state x monitor state) product.

    While the obligation is PENDING the dispatcher refuses every marked-terminal
    action (the monitor discharge guard), so only NON-TERMINAL actions are
    enabled and firing the demanded action is the only discharge.  A control
    state `can-discharge` iff, following non-terminal transitions, it reaches a
    state where the demanded (non-terminal) action is enabled; every OTHER
    control state is a DEAD-END -- being pending there is permanent.

    Guards/context are abstracted (the control-skeleton product, matching
    ProtocolModel.control_skeleton_dfa): an OVER-approximation of the discharge
    ability, which can only ever hide a guard-induced strand, never invent one.
    The verdict is independent of incidental sink/terminal structure, so an inert
    self-loop that makes a session-ending state a non-sink cannot defeat it."""
    disch_action = obligation["action"]
    # seed: control states where the demanded discharge action is directly
    # enabled (it must be non-terminal to fire while pending).
    can = {a.frm for a in model.actions
           if a.name == disch_action and not a.terminal}
    # reverse-reachability over NON-TERMINAL edges (terminals are guarded off
    # while pending): p can-discharge if some non-terminal action leads it to a
    # can-discharge state.
    nonterminal = [a for a in model.actions if not a.terminal]
    changed = True
    while changed:
        changed = False
        for a in nonterminal:
            if a.to in can and a.frm not in can:
                can.add(a.frm)
                changed = True
    return [p for p in model.states if p not in can]


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
