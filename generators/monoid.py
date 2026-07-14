"""P5.1 tier-classification: is a DFA's CONTROL SKELETON star-free?

star-free == aperiodic == counter-free (Schutzenberger / McNaughton-Papert);
three names for one property of the language's syntactic monoid.  We decide it
with a DUAL CHECKER -- two genuinely different algorithms for the SAME property,
the Z3-vs-CVC5 independence grade (NOT two spellings of one algorithm):

  Channel 1 (monoid algebra): enumerate the transition monoid of the MINIMAL
    DFA; it is aperiodic iff every element m has an idempotent power
    (some k with m^k == m^(k+1)).  Purely algebraic, per element.
  Channel 2 (counter-free pattern search): work on the DFA directly -- it is
    counter-free iff no word induces a nontrivial r-cycle (r = 2..|Q|) on any
    r states.  We look for such an r-cycle by reachability in the r-fold
    diagonal product (a distinct-state tuple that a common word rotates).
    Never touches the monoid: a genuinely different algorithm.

The two must AGREE (aperiodic <=> counter-free).  A disagreement is a first-
class logged event (tier "unresolved", both verdicts) -- it must never happen
on correct code, which is exactly why we run both.

Two honesty rules baked in:
  * MINIMIZE FIRST.  The syntactic monoid is the transition monoid of the
    *minimal* DFA.  On a non-minimal DFA the monoid is wrong (equivalent states
    that a symbol shuffles look like a spurious cycle).  hopcroft_minimize
    completes over the full alphabet with a dead sink, then partitions.
  * The tag is "control-skeleton star-free", never unqualified "star-free":
    guards and integer context live outside the DFA, so the classification is
    about the control skeleton only.

Feasibility cliff: |Q|=6 -> 46,656 transformations (fine); |Q|=10 -> 10^10
(impossible).  We precondition |Q| <= 8 after minimization and hard-cap the
enumeration at 10^6 elements; on exceed we return the CAP_EXCEEDED sentinel so
classify() emits an honest "tier-unclassified (cap exceeded)" -- not a failure,
not a certificate.

A DFA here is a dict:
  {states:set, initial, accepting:set, delta:{(state,symbol):state}, alphabet:set}
Self-contained: no protocol_gen / monitor_gen imports; tests hand-build DFAs.
"""
from __future__ import annotations

import dataclasses
import itertools

MAX_STATES = 8            # precondition |Q| <= 8 after minimization
MAX_ELEMENTS = 10 ** 6    # hard cap on enumerated monoid transformations

_DEAD = ("<dead-sink>",)  # sentinel completion state (tuple -> hashable, unlikely clash)


class _CapExceeded:
    """Sentinel: the transition monoid hit the feasibility cliff.  Truthy
    identity check only (`mon is CAP_EXCEEDED`)."""
    __slots__ = ()

    def __repr__(self):
        return "CAP_EXCEEDED"


CAP_EXCEEDED = _CapExceeded()


def _state_key(s):
    """A stable, total sort key over heterogeneous state objects (including the
    frozenset blocks minimization produces)."""
    if isinstance(s, frozenset):
        return ("fs",) + tuple(sorted(_state_key(x) for x in s))
    return ("v", str(s))


# ---------------------------------------------------------------------------
# 1. hopcroft_minimize -- complete over the alphabet, drop unreachable, then
#    Hopcroft partition-refinement.  Returns a minimal DFA (blocks are states).
# ---------------------------------------------------------------------------

def _complete(dfa):
    """Total the transition function: any missing (state, symbol) routes to a
    fresh dead sink that loops to itself.  Required so the transition monoid is
    total (every symbol is a genuine map states->states)."""
    states = set(dfa["states"])
    alphabet = set(dfa["alphabet"])
    delta = dict(dfa["delta"])
    need_dead = False
    for s in states:
        for c in alphabet:
            if (s, c) not in delta:
                delta[(s, c)] = _DEAD
                need_dead = True
    if need_dead:
        assert _DEAD not in states, "dead-sink sentinel collides with a real state"
        states.add(_DEAD)
        for c in alphabet:
            delta[(_DEAD, c)] = _DEAD
    return {"states": states, "initial": dfa["initial"],
            "accepting": set(dfa["accepting"]) & states,
            "delta": delta, "alphabet": alphabet}


def _reachable(dfa):
    seen = {dfa["initial"]}
    stack = [dfa["initial"]]
    while stack:
        s = stack.pop()
        for c in dfa["alphabet"]:
            t = dfa["delta"][(s, c)]
            if t not in seen:
                seen.add(t)
                stack.append(t)
    return seen


def hopcroft_minimize(dfa):
    """Minimal DFA of `dfa`.  Completes with a dead sink, restricts to the
    reachable part, then Hopcroft-refines {accepting, non-accepting}.  States of
    the result are frozenset blocks (the Myhill-Nerode classes)."""
    d = _complete(dfa)
    states = _reachable(d)
    alphabet = d["alphabet"]
    delta = {(s, c): d["delta"][(s, c)] for s in states for c in alphabet}
    accepting = d["accepting"] & states

    # predecessor index: (symbol, target) -> {sources}
    pre = {}
    for (s, c), t in delta.items():
        pre.setdefault((c, t), set()).add(s)

    F = frozenset(accepting)
    NF = frozenset(states - accepting)
    P = {b for b in (F, NF) if b}          # partition: non-empty blocks
    W = set(P)                             # worklist
    while W:
        A = W.pop()
        for c in alphabet:
            X = set()                      # states that step INTO A on c
            for t in A:
                X |= pre.get((c, t), set())
            if not X:
                continue
            Xf = frozenset(X)
            for Y in list(P):
                inter = Y & Xf
                diff = Y - Xf
                if inter and diff:         # c splits block Y
                    P.discard(Y)
                    P.add(inter)
                    P.add(diff)
                    if Y in W:
                        W.discard(Y)
                        W.add(inter)
                        W.add(diff)
                    else:
                        W.add(inter if len(inter) <= len(diff) else diff)

    rep_of = {s: block for block in P for s in block}
    m_delta = {}
    for block in P:
        s = next(iter(block))              # any representative -- block is a class
        for c in alphabet:
            m_delta[(block, c)] = rep_of[delta[(s, c)]]
    return {"states": set(P),
            "initial": rep_of[d["initial"]],
            "accepting": {b for b in P if b & F},
            "delta": m_delta,
            "alphabet": alphabet}


# ---------------------------------------------------------------------------
# 2. transition_monoid -- closure of the single-symbol maps under composition.
#    A transformation is a tuple t of length n: state i |-> t[i].  Composition
#    "first f then g" is (g[f[i]])_i.  Right-multiplying identity + generators
#    by the generators to a fixpoint yields the whole submonoid.
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class TransitionMonoid:
    n: int                 # |Q| of the minimal DFA
    states: list           # index -> state (block); the chosen ordering
    generators: dict       # symbol -> transformation tuple
    elements: frozenset    # every transformation (tuple len n), incl. identity


def transition_monoid(min_dfa):
    """The transition monoid of a (already minimal, complete) DFA, or
    CAP_EXCEEDED on the feasibility cliff (|Q| > MAX_STATES, or > MAX_ELEMENTS
    transformations)."""
    st = sorted(min_dfa["states"], key=_state_key)
    n = len(st)
    if n > MAX_STATES:                     # precondition: |Q| <= 8
        return CAP_EXCEEDED
    idx = {s: i for i, s in enumerate(st)}
    alphabet = sorted(min_dfa["alphabet"], key=str)
    gens = {c: tuple(idx[min_dfa["delta"][(st[i], c)]] for i in range(n))
            for c in alphabet}

    ident = tuple(range(n))
    elems = {ident, *gens.values()}
    frontier = list(elems)
    while frontier:
        m = frontier.pop()
        for g in gens.values():
            comp = tuple(g[m[i]] for i in range(n))   # first m, then g
            if comp not in elems:
                if len(elems) >= MAX_ELEMENTS:         # hard cap 10^6
                    return CAP_EXCEEDED
                elems.add(comp)
                frontier.append(comp)
    return TransitionMonoid(n=n, states=st, generators=gens,
                            elements=frozenset(elems))


# ---------------------------------------------------------------------------
# Channel 1: monoid is aperiodic iff every element has an idempotent power.
# The powers of m eventually cycle; m^k == m^(k+1) for some k iff that cycle
# has length 1.  We compute the power-cycle length per element.
# ---------------------------------------------------------------------------

def _power_cycle_len(m):
    seen = {m: 1}
    cur = m                                # cur == m^k
    k = 1
    while True:
        cur = tuple(m[j] for j in cur)     # m^(k+1) = first m^k, then m
        k += 1
        if cur in seen:
            return k - seen[cur]           # length of the entered cycle
        seen[cur] = k


def _channel_monoid_aperiodic(mon):
    """(is_aperiodic, witness).  witness = an element with a nontrivial
    power-cycle (a counter, algebraically) when not aperiodic."""
    for m in mon.elements:
        if _power_cycle_len(m) != 1:
            return False, m
    return True, None


# ---------------------------------------------------------------------------
# Channel 2: counter-free pattern search on the minimal DFA (NO monoid).
# A counter of order r is r distinct states and a word w whose diagonal action
# rotates them cyclically: delta(s_i, w) = s_{(i+1) mod r}.  We seek it as
# reachability of rot(T) from T in the r-fold diagonal product graph (edges
# apply ONE symbol to every coordinate; a path = a common word).  Reaching
# rot(T) once means w sends s_0->s_1->...->s_{r-1}->s_0: an r-cycle counter.
# Genuinely different from channel 1: graph reachability, never the algebra.
# ---------------------------------------------------------------------------

def _channel_counter_free(min_dfa):
    """(is_counter_free, witness).  witness = {order, cycle, word} of the found
    counter when not counter-free."""
    states = sorted(min_dfa["states"], key=_state_key)
    n = len(states)
    delta = min_dfa["delta"]
    alphabet = sorted(min_dfa["alphabet"], key=str)

    for r in range(2, n + 1):
        for T in itertools.permutations(states, r):
            # one representative per rotation orbit (T -> rot(T) chains around
            # the whole orbit, so any rotation is an equivalent start).
            rots = [T[i:] + T[:i] for i in range(r)]
            if T != min(rots, key=lambda x: tuple(_state_key(s) for s in x)):
                continue
            target = T[1:] + T[:1]         # rot(T): shift left by one
            # BFS over distinct-state r-tuples; a coordinate collision leaves
            # the distinct subgraph and cannot be part of a counter.
            seen = {T}
            parent = {T: (None, None)}
            frontier = [T]
            found = False
            while frontier:
                U = frontier.pop()
                if U == target:
                    found = True
                    break
                for c in alphabet:
                    V = tuple(delta[(u, c)] for u in U)
                    if len(set(V)) != r:
                        continue
                    if V not in seen:
                        seen.add(V)
                        parent[V] = (U, c)
                        frontier.append(V)
            if found:
                word = []
                node = target
                while parent[node][0] is not None:
                    prev, c = parent[node]
                    word.append(c)
                    node = prev
                word.reverse()
                return False, {"order": r, "cycle": T,
                               "word": "".join(str(c) for c in word)}
    return True, None


# ---------------------------------------------------------------------------
# 3. classify -- minimize, enumerate, run BOTH channels, require agreement.
# ---------------------------------------------------------------------------

def classify(dfa):
    """Tier-classify the control skeleton of `dfa`.

    Returns {"tier", "channels", "detail", ...} with tier one of:
      "control-skeleton star-free"        -- aperiodic == counter-free
      "not star-free"                     -- has a counter / non-aperiodic
      "tier-unclassified (cap exceeded)"  -- feasibility cliff, honest non-cert
    and, only if the two channels ever disagree (a bug, by construction):
      "tier-unresolved (channel disagreement)".
    """
    md = hopcroft_minimize(dfa)
    n = len(md["states"])
    mon = transition_monoid(md)

    if mon is CAP_EXCEEDED:
        note = (f"|Q|={n} after minimization exceeds precondition "
                f"|Q|<={MAX_STATES}, or enumeration exceeded {MAX_ELEMENTS} "
                f"transformations")
        return {
            "tier": "tier-unclassified (cap exceeded)",
            "channels": [
                {"backend": "monoid-algebra",
                 "algorithm": "idempotent-power (m^k==m^(k+1))",
                 "result": "unclassified", "detail": note},
                {"backend": "counter-free-search",
                 "algorithm": "r-cycle reachability in r-fold DFA product",
                 "result": "unclassified",
                 "detail": "not run: monoid enumeration hit the feasibility cliff"},
            ],
            "independent_channels": True,
            "min_states": n,
            "detail": ("control-skeleton tier-unclassified (cap exceeded): "
                       f"minimal DFA has |Q|={n}; honest non-certificate, not a "
                       "failure."),
        }

    ap, ap_w = _channel_monoid_aperiodic(mon)      # channel 1
    cf, cf_w = _channel_counter_free(md)           # channel 2

    ch1 = {"backend": "monoid-algebra",
           "algorithm": "idempotent-power (m^k==m^(k+1))",
           "result": "star-free" if ap else "not star-free",
           "monoid_size": len(mon.elements),
           "detail": ("every transition-monoid element has an idempotent power "
                      "(aperiodic)" if ap else
                      f"element {ap_w} has a nontrivial power-cycle "
                      "(non-aperiodic)")}
    ch2 = {"backend": "counter-free-search",
           "algorithm": "r-cycle reachability in r-fold DFA product",
           "result": "star-free" if cf else "not star-free",
           "detail": ("no nontrivial r-cycle (r=2..|Q|) on the minimal DFA "
                      "(counter-free)" if cf else f"counter found: {cf_w}")}
    channels = [ch1, ch2]

    if ap != cf:
        # DUAL-CHECKER DISAGREEMENT -- must never happen on correct code.
        return {
            "tier": "tier-unresolved (channel disagreement)",
            "channels": channels,
            "independent_channels": True,
            "min_states": n,
            "detail": ("DUAL-CHECKER DISAGREEMENT (impossible on correct code): "
                       f"monoid-algebra says {'aperiodic' if ap else 'non-aperiodic'}, "
                       f"counter-free-search says {'counter-free' if cf else 'has a counter'}. "
                       "No certificate; logged for human eyes."),
        }

    if ap:
        tier = "control-skeleton star-free"
        detail = ("control skeleton is star-free (aperiodic == counter-free); "
                  "the tag applies to the CONTROL SKELETON ONLY -- guards and "
                  "integer context are not in the DFA.")
    else:
        tier = "not star-free"
        detail = ("control skeleton is NOT star-free: the syntactic monoid of "
                  "the minimal DFA is non-aperiodic and the DFA has a counter "
                  "(a nontrivial cycle).")
    return {"tier": tier, "channels": channels,
            "independent_channels": True, "min_states": n, "detail": detail}
