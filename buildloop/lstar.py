"""Angluin L* protocol lift: learn an incumbent stateful service as a Mealy
machine by black-box membership + equivalence queries.

The incumbent is only ever a black box (buildloop never reads its control
flow): the learner constructs a fresh instance per query (a total reset) and
calls ``call(tool, args)``.  Queries run inside the OS sandbox (untrusted
third-party code), and are BATCHED -- every membership query a refinement
round needs goes into ONE sandbox run, because per-query sandboxing is ~1000x
too slow to be usable.  The accept/reject verdict comparison happens OUT here,
in trusted code, never inside the sandbox.

Pieces:

  * ``Oracle`` -- translates abstract inputs (declared abstraction map) to
    concrete ``(tool, args)`` calls, batches them through a sandbox driver
    matching the frozen incumbent interface, and classifies raw outputs into a
    finite output alphabet {ok, reject, __error__, __timeout__, hash:<...>}.
    Determinism is CHECKED, not assumed: the first batch is run twice and a
    mismatch raises ``NondeterministicIncumbent`` (a first-class result).

  * ``learn`` -- L* over a closed observation table with a SUFFIX-CLOSED
    experiment set (which keeps the table consistent for free), Rivest-Schapire
    single-suffix counterexample analysis, and a W-method equivalence oracle
    bounded by an explicit declared state bound ``n``: if the incumbent has at
    most ``n`` states the learned machine is exact; beyond ``n`` there is no
    guarantee (this is the honesty tooth the trapdoor demo exercises).

  * ``Mealy`` -- the learned machine, plus ``to_protocol_spec`` which projects
    its ``ok`` transitions to a ``parse_protocol_spec``-compatible protocol
    text (legal transitions = ok; every refused input is an implicit reject).
"""
from __future__ import annotations

import dataclasses
import json
from collections import deque

import common

# The finite output alphabet.  Anything an incumbent returns that is not one of
# these canonical tokens is folded into a stable hash class, keeping the output
# alphabet finite even for services that answer with rich JSON.
KNOWN_OUTPUTS = ("ok", "reject", "__error__", "__timeout__")
ACCEPTING = "ok"           # the output class that marks a *legal* transition

# The declared abstraction map for the order-lifecycle incumbent: each abstract
# input name -> the concrete (tool, args) it stands for.  This is DECLARED, not
# inferred, and is recorded verbatim in the lift certificate.  pay_big/pay_small
# is the representative-arg-value split that exposes the amount>=100 guard.
ORDER_ABSTRACTION = {
    "login":     {"tool": "login",  "args": {}},
    "pay_big":   {"tool": "pay",    "args": {"amount": 150}},
    "pay_small": {"tool": "pay",    "args": {"amount": 10}},
    "ship":      {"tool": "ship",   "args": {}},
    "close":     {"tool": "close",  "args": {}},
    "refund":    {"tool": "refund", "args": {}},
}
ORDER_ALPHABET = list(ORDER_ABSTRACTION.keys())


class NondeterministicIncumbent(Exception):
    """Raised when the same batch of queries yields different answers on a
    repeat run: L* presupposes a deterministic (Mealy) target, so a
    nondeterministic incumbent is a first-class, reported failure, not a
    silently-wrong learned model."""


# --------------------------------------------------------------------------- #
#  Sandbox batching driver (matches the frozen incumbent interface).          #
#  Reads one JSON query per line {seq:[[tool,args],...], reset?:bool}; writes  #
#  one flushed JSON line per query = the output sequence.  A per-call          #
#  signal.alarm maps hangs to "__timeout__"; any exception maps to            #
#  "__error__".  It runs the UNTRUSTED incumbent; it makes no verdicts.        #
# --------------------------------------------------------------------------- #
_DRIVER = r'''
import json, signal
from order_service import Incumbent

class _TO(Exception):
    pass

def _alarm(signum, frame):
    raise _TO()

signal.signal(signal.SIGALRM, _alarm)
TIMEOUT_S = {timeout_s}

with open("queries.jsonl") as fin, open("outputs.jsonl", "w") as fout:
    for line in fin:
        line = line.strip()
        if not line:
            continue
        q = json.loads(line)
        inc = Incumbent()          # fresh instance == total reset
        outs = []
        for tool, args in q["seq"]:
            signal.alarm(TIMEOUT_S)
            try:
                outs.append(inc.call(tool, args))
            except _TO:
                outs.append("__timeout__")
                signal.alarm(0)
                break
            except BaseException:
                outs.append("__error__")
                signal.alarm(0)
                break
            finally:
                signal.alarm(0)
        fout.write(json.dumps(outs) + "\n")
        fout.flush()
'''


def _classify(raw):
    """Map a raw jsonable output to a finite output class."""
    if isinstance(raw, str) and raw in KNOWN_OUTPUTS:
        return raw
    return "hash:" + common.sha256_json(raw)[:12]


class Oracle:
    """Batched, sandboxed membership oracle over an abstraction map.

    ``outseq(seq)`` returns the tuple of output classes for an abstract input
    sequence (a tuple of abstract-input names); ``prefill(seqs)`` computes any
    uncached ones in ONE sandbox run.  Results are cached, so a sequence is
    queried against the incumbent at most once across the whole learning run.
    """

    def __init__(self, incumbent_src, alphabet, abstraction, *,
                 timeout_s=2, sandbox_timeout=180):
        if isinstance(incumbent_src, bytes):
            incumbent_src = incumbent_src.decode()
        self.src = incumbent_src
        self.alphabet = list(alphabet)
        self.abstraction = abstraction
        self.timeout_s = int(timeout_s)
        self.sandbox_timeout = sandbox_timeout
        self.cache = {(): ()}                 # empty seq -> empty output
        self.sandbox_runs = 0
        self.max_batch = 0
        self._determinism_checked = False

    # -- concrete translation -------------------------------------------------
    def _concrete(self, seq):
        out = []
        for sym in seq:
            spec = self.abstraction[sym]
            out.append([spec["tool"], spec["args"]])
        return out

    # -- one sandbox run over a list of abstract sequences --------------------
    def _run_batch(self, seqs):
        from sandbox import Sandbox
        payload = "".join(json.dumps({"seq": self._concrete(s)}) + "\n"
                          for s in seqs)
        driver = _DRIVER.format(timeout_s=self.timeout_s)
        with Sandbox() as sb:
            sb.add_file("order_service.py", self.src)
            sb.add_file("queries.jsonl", payload)
            sb.add_file("driver.py", driver)
            res = sb.run(["python3", "driver.py"],
                         timeout=self.sandbox_timeout, cpu_seconds=120)
            self.sandbox_runs += 1
            if not sb.exists("outputs.jsonl"):
                raise RuntimeError(
                    "incumbent driver produced no output; stderr:\n"
                    + res.stderr[-1500:].decode(errors="replace"))
            lines = sb.read("outputs.jsonl").decode().splitlines()
        if len(lines) != len(seqs):
            raise RuntimeError(
                f"driver returned {len(lines)} lines for {len(seqs)} queries")
        return [tuple(_classify(o) for o in json.loads(ln)) for ln in lines]

    def prefill(self, seqs):
        """Ensure every sequence in ``seqs`` is cached, batching the misses
        into ONE sandbox run.  EVERY batch is run twice and compared, so
        nondeterminism at ANY depth is caught -- not just the shallow first
        batch (a target that is deterministic on short prefixes but random once
        state depth is reached would otherwise be silently mis-learned).
        Determinism is checked, not assumed."""
        todo = sorted({tuple(s) for s in seqs if tuple(s) not in self.cache})
        if not todo:
            return
        self.max_batch = max(self.max_batch, len(todo))
        outs = self._run_batch(todo)
        outs2 = self._run_batch(todo)
        for s, a, b in zip(todo, outs, outs2):
            if a != b:
                raise NondeterministicIncumbent(
                    f"query {s!r} answered {a!r} then {b!r}")
        self._determinism_checked = True
        for s, o in zip(todo, outs):
            self.cache[s] = o

    def outseq(self, seq):
        seq = tuple(seq)
        if seq not in self.cache:
            self.prefill([seq])
        return self.cache[seq]


# --------------------------------------------------------------------------- #
#  The learned machine.                                                       #
# --------------------------------------------------------------------------- #
@dataclasses.dataclass
class Mealy:
    states: list                 # state names, e.g. ["q0", "q1", ...]
    initial: str
    alphabet: list
    delta: dict                  # (state, input) -> next state
    out: dict                    # (state, input) -> output class
    access: dict                 # state -> access string (tuple), a table rep

    def run_state(self, seq):
        st = self.initial
        for sym in seq:
            st = self.delta[(st, sym)]
        return st

    def run_outputs_from(self, state, seq):
        st, outs = state, []
        for sym in seq:
            outs.append(self.out[(st, sym)])
            st = self.delta[(st, sym)]
        return tuple(outs)

    def run_outputs(self, seq):
        return self.run_outputs_from(self.initial, seq)

    def to_protocol_spec(self, name, *, accepting=ACCEPTING):
        """Project to a parse_protocol_spec-compatible protocol text.

        Legal protocol transitions are exactly the ``accepting`` (ok) edges;
        every refused input is an implicit reject (absent action).  The service
        carries no data, so the certified safety invariant is a structural
        constant (a real BMC obligation, but not a data property) -- the load
        bearing evidence is the validator<->reference-simulator conformance
        channel plus the conformance-relative(n) bound recorded on the lift
        certificate.
        """
        actions = []
        for st in self.states:
            for sym in self.alphabet:
                if self.out[(st, sym)] == accepting:
                    actions.append({"name": sym, "from": st,
                                    "to": self.delta[(st, sym)]})
        spec = {
            "name": name,
            "context": {"ok": {"type": "integer", "init_min": 0, "init_max": 0}},
            "states": list(self.states),
            "initial": self.initial,
            "actions": actions,
            "safety": {"when": "*",
                       "invariant": {"op": "==", "left": "ok", "right": 0}},
        }
        return json.dumps(spec)

    def lifecycle_path(self, seq, *, accepting=ACCEPTING):
        """The (state, output) trajectory of an input sequence -- used by the
        demo to check the recovered order lifecycle and to probe the trapdoor.
        """
        st, traj = self.initial, []
        for sym in seq:
            o = self.out[(st, sym)]
            st = self.delta[(st, sym)]
            traj.append((sym, o, st))
        return traj


# --------------------------------------------------------------------------- #
#  L* observation table.                                                       #
# --------------------------------------------------------------------------- #
class _Table:
    def __init__(self, oracle, alphabet):
        self.oracle = oracle
        self.alphabet = list(alphabet)
        self.S = [()]                                   # access strings (S)
        self.E = [(i,) for i in alphabet]               # suffix-closed exps
        self.fill_and_close()

    def _needed(self):
        rows = list(self.S) + [s + (i,) for s in self.S for i in self.alphabet]
        return {u + e for u in rows for e in self.E}

    def cell(self, u, e):
        return self.oracle.outseq(u + e)[len(u):]

    def row(self, u):
        return tuple(self.cell(u, e) for e in self.E)

    def fill_and_close(self):
        """Batch every needed membership query for the current (S, E), then
        drive the table to closedness (each closure pass is one sandbox run of
        the freshly-needed queries)."""
        while True:
            self.oracle.prefill(self._needed())
            s_rows = {self.row(s) for s in self.S}
            added = False
            for s in list(self.S):
                for i in self.alphabet:
                    u = s + (i,)
                    if self.row(u) not in s_rows:
                        self.S.append(u)
                        added = True
                        break
                if added:
                    break
            if not added:
                return

    def add_suffixes(self, suffixes):
        for suf in suffixes:
            suf = tuple(suf)
            for j in range(len(suf)):          # keep E suffix-closed
                s = suf[j:]
                if s and s not in self.E:
                    self.E.append(s)

    def hypothesis(self):
        # one representative access string per distinct row
        rep = {}
        for s in self.S:
            rep.setdefault(self.row(s), s)
        rows = list(rep)
        name = {r: f"q{k}" for k, r in enumerate(rows)}
        states = [name[r] for r in rows]
        access = {name[r]: rep[r] for r in rows}
        delta, out = {}, {}
        for r in rows:
            s = rep[r]
            for i in self.alphabet:
                delta[(name[r], i)] = name[self.row(s + (i,))]
                out[(name[r], i)] = self.cell(s, (i,))[0]
        initial = name[self.row(())]
        return Mealy(states=states, initial=initial, alphabet=list(self.alphabet),
                     delta=delta, out=out, access=access)


# --------------------------------------------------------------------------- #
#  Equivalence oracle: bounded W-method up to the declared state bound n.      #
# --------------------------------------------------------------------------- #
def _sigma_upto(alphabet, maxlen):
    seqs, frontier = [()], [()]
    for _ in range(maxlen):
        nxt = [p + (i,) for p in frontier for i in alphabet]
        seqs.extend(nxt)
        frontier = nxt
    return seqs


def _state_cover(H):
    access = {H.initial: ()}
    dq = deque([H.initial])
    while dq:
        st = dq.popleft()
        for i in H.alphabet:
            nx = H.delta[(st, i)]
            if nx not in access:
                access[nx] = access[st] + (i,)
                dq.append(nx)
    return list(access.values())


def w_method_ce(H, oracle, table, n):
    """Chow's W-method conformance test up to ``n`` states: state-cover .
    Sigma^<=(n-m+1) . W, with W = the table's (suffix-closed) experiment set,
    which distinguishes every hypothesis state.  Returns the shortest input
    sequence on which H and the incumbent disagree, or None (conformant up to
    n states)."""
    m = len(H.states)
    P = _state_cover(H)
    W = list(table.E)
    maxlen = max(0, n - m) + 1
    mids = _sigma_upto(H.alphabet, maxlen)
    tests = {p + mid + w for p in P for mid in mids for w in W}
    ordered = sorted(tests, key=lambda t: (len(t), t))
    oracle.prefill(ordered)
    for t in ordered:
        if H.run_outputs(t) != oracle.outseq(t):
            return t
    return None


def _rivest_schapire(ce, H, table, oracle):
    """Extract ONE distinguishing suffix from a counterexample (Rivest-Schapire
    analysis).  Replace ever-longer prefixes of ``ce`` by the hypothesis'
    access string for the state they reach; the point where the incumbent's
    behaviour stops matching the hypothesis' localizes a suffix that splits two
    currently-merged states.  All probes are computed in one batch."""
    m = len(ce)
    s = [H.access[H.run_state(ce[:i])] for i in range(m + 1)]
    oracle.prefill({s[i] + ce[i:] for i in range(m + 1)})

    def match(i):
        inc = oracle.outseq(s[i] + ce[i:])[len(s[i]):]
        hyp = H.run_outputs_from(H.run_state(ce[:i]), ce[i:])
        return inc == hyp

    for i in range(m):
        if (not match(i)) and match(i + 1):
            return ce[i + 1:]
    # monotonicity fallback: any distinguishing suffix keeps progress.
    return ce[1:] if m > 1 else ce


def learn(oracle, alphabet, state_bound_n, *, max_rounds=32):
    """Angluin L* with Rivest-Schapire CE processing and a W-method equivalence
    oracle bounded by ``state_bound_n``.  Returns a result dict carrying the
    learned ``Mealy`` machine and provenance/statistics."""
    table = _Table(oracle, alphabet)
    H = table.hypothesis()
    ces, rounds = [], 0
    stalled = False
    while rounds < max_rounds:
        ce = w_method_ce(H, oracle, table, state_bound_n)
        if ce is None:
            break
        ces.append(list(ce))
        suffix = _rivest_schapire(ce, H, table, oracle)
        before = len(H.states)
        table.add_suffixes([suffix])
        table.fill_and_close()
        H = table.hypothesis()
        rounds += 1
        if len(H.states) <= before:
            # No progress despite a REAL counterexample: suffix-closed E + RS
            # guarantee growth, so this only trips on a pathological target.
            # Report it honestly -- the model is NOT conformant up to n, so this
            # is NOT a clean "converged" (a real CE was found but not absorbed).
            stalled = True
            break
    status = ("stalled-unprocessed-ce" if stalled
              else "converged" if rounds < max_rounds else "max-rounds")
    return {
        "status": status,
        "machine": H,
        "state_bound_n": state_bound_n,
        "rounds": rounds,
        "counterexamples": ces,
        "num_states": len(H.states),
        "num_experiments": len(table.E),
        "sandbox_runs": oracle.sandbox_runs,
        "membership_queries": len(oracle.cache) - 1,   # minus the empty seq
        "max_batch": oracle.max_batch,
    }
