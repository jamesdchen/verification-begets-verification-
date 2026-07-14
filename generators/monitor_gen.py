"""P1.5 monitor factory -- compile an LTLf temporal demand over a finite ACTION
alphabet into a certified MONITOR DFA, emitted two independent ways.

A temporal demand ("eventually ship", "ship within 2", ...) becomes an LTLf
formula over one-hot action atoms, which flloat compiles to a SymbolicDFA whose
guards are sympy booleans.  We CONCRETIZE those guards over the finite alphabet
(evaluate each guard for each concrete action symbol -- the alphabet is exactly
one-hot over the action atoms), BFS-renumber the reachable states from the
initial one visiting actions in SORTED order, and emit a plain int-keyed table.
This kills the pythomata numbering nondeterminism (state ids vary with
PYTHONHASHSEED -- proven); after canonicalization the emitted monitor.py is
BYTE-IDENTICAL across seeds.

Two artifacts come out, sharing no code -- this is channel 2 of the future
monitor-cert:
  * monitor.py     -- a dependency-free table walk (TABLE/INITIAL/ACCEPTING/
                      step/accepting/pending), the thing that ships;
  * ref_stepper.py -- an INDEPENDENT decision procedure that re-parses the same
                      LTLf spec and drives flloat's own automaton live.  A
                      mutation in the baked table is caught by the live stepper
                      and vice-versa.

ATOM HYGIENE: raw action names NEVER enter the formula -- flloat's lexer treats
`last` as the end-of-trace constant and crashes on keyword-prefixed names.  We
prefix every action atom as `act_<name>` at formula-build time and use the SAME
mapping when concretizing.  The public API takes RAW names; the emitted TABLE is
keyed by RAW names.
"""
from __future__ import annotations

import ast
from collections import deque

_PREFIX = "act_"


def parse_monitor_module(src: bytes) -> dict:
    """Extract TABLE / INITIAL / ACCEPTING / SINK from an emitted monitor.py
    WITHOUT executing it (the module is emitted code -- never exec it in the
    trusted kernel; house rule 7).  We parse the AST and literal_eval only the
    top-level constant assignments, so a mutation in the SHIPPED table is exactly
    what the reader sees.  This feeds monitor-cert channel 1 (the SMT agreement
    encodes THIS baked table)."""
    tree = ast.parse(src.decode())
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ("TABLE", "INITIAL", "ACCEPTING", "SINK"):
                try:
                    out[name] = ast.literal_eval(node.value)
                except Exception:
                    pass
    for req in ("TABLE", "INITIAL", "ACCEPTING"):
        if req not in out:
            raise ValueError(f"monitor.py missing {req} constant")
    return out

# kind -> LTLf.  Documented in build_monitor's returned meta["formula"] too.
#   eventually(a)  : F(act_a)                         -- co-safety liveness
#   until(pre,post): act_pre U act_post               -- strong until
#   before(a,b)    : G(!act_b) | (!act_b U act_a)     -- weak precedence: b must
#                    not occur before a; a need not occur (empty trace accepted).
#                    flloat has no W operator, so weak-until is spelled out.
#   within(a,n)    : act_a | X(act_a) | ... | X^{n-1}(act_a)  -- a in first n pos.


def _atom(name: str) -> str:
    return _PREFIX + name


def _check_name(name: str):
    # act_<name> must be a clean flloat identifier; fail loud, never emit a
    # formula the lexer will choke on.
    if not (isinstance(name, str) and name and name.replace("_", "a").isalnum()
            and not name[0].isdigit()):
        raise ValueError("action name not [A-Za-z0-9_]+ (no leading digit): %r"
                         % (name,))


def _formula(kind: str, params: dict, alphabet: list) -> str:
    """Map (kind, params) -> an LTLf string over act_<name> atoms.  Every action
    named in params must be in the alphabet."""
    aset = set(alphabet)

    def act(key):
        n = params[key]
        if n not in aset:
            raise ValueError("param %r=%r not in alphabet %r"
                             % (key, n, sorted(aset)))
        return _atom(n)

    if kind == "eventually":
        return "F(%s)" % act("action")
    if kind == "until":
        return "%s U %s" % (act("pre"), act("post"))
    if kind == "before":
        a, b = act("first"), act("second")
        return "G(!%s) | (!%s U %s)" % (b, b, a)
    if kind == "within":
        a = act("action")
        n = int(params["steps"])
        if n < 1:
            raise ValueError("within steps must be >= 1, got %r" % (n,))
        # a | X(a) | X(X(a)) | ...  -- strong X is false past trace end, so a
        # trace shorter than the deadline that never does `a` is (correctly)
        # rejected as a *complete* trace while step-wise still pending.
        return " | ".join(a if i == 0 else "X(" * i + a + ")" * i
                          for i in range(n))
    raise ValueError("unknown kind %r" % (kind,))


# ------------------------------------------------------------ canonicalize
def _canonize(formula: str, alphabet: list) -> dict:
    """flloat DFA -> deterministic int table.  Concretize guards over the
    one-hot alphabet, BFS-renumber from the initial state visiting actions in
    SORTED order (so numbering is input/seed-independent), append one dead sink
    (target for unknown symbols) as the last state."""
    from flloat.parser.ltlf import LTLfParser        # heavy import, keep local

    acts = sorted(alphabet)
    dfa = LTLfParser()(formula).to_automaton()
    # one concrete one-hot interpretation per action: {act_x: x is this action}
    interp = {a: {_atom(x): (x == a) for x in acts} for a in acts}

    init = dfa.initial_state
    new = {init: 0}                                    # orig id -> canonical id
    order = [init]
    q = deque([init])
    trans = {}                                         # orig id -> {act: orig id}
    while q:
        s = q.popleft()
        row = {}
        for a in acts:                                 # SORTED action order
            t = dfa.get_successor(s, interp[a])
            if t is None:                              # complete DFA -> unused
                continue
            if t not in new:
                new[t] = len(order)
                order.append(t)
                q.append(t)
            row[a] = t
        trans[s] = row

    sink = len(order)                                  # canonical dead sink last
    table = {new[s]: {a: new[t] for a, t in sorted(trans[s].items())}
             for s in order}
    table[sink] = {a: sink for a in acts}
    accepting = sorted(new[s] for s in order if dfa.is_accepting(s))
    permanent = _permanent(table, set(accepting))
    return {"table": table, "initial": 0, "accepting": accepting,
            "sink": sink, "permanent": permanent, "num_states": len(table)}


def _permanent(table: dict, acc: set) -> list:
    """Permanently-accepting states: accepting AND cannot reach a non-accepting
    state.  pending(state) == state not in this set.  Computed by reverse
    reachability from the non-accepting states over the concrete alphabet."""
    rev = {s: [] for s in table}
    for s, row in table.items():
        for t in row.values():
            rev[t].append(s)
    tainted = set(s for s in table if s not in acc)    # non-accepting seeds
    q = deque(tainted)
    while q:
        s = q.popleft()
        for p in rev[s]:
            if p not in tainted:
                tainted.add(p)
                q.append(p)
    return sorted(s for s in table if s not in tainted)


# ------------------------------------------------------------ emit monitor.py
_PENDING_DOC = (
    "pending(state): True iff an obligation is still undischarged -- i.e. from\n"
    "this state the automaton is NOT already in a permanently-accepting\n"
    "condition (accepting AND unable to ever reach a non-accepting state).\n"
    "This reduces to `not accepting(state)` for co-safety F/within (their\n"
    "accepting state is a trap), while for until/before it is exactly \"the\n"
    "until is not yet satisfied\": e.g. `before` accepts the empty trace yet\n"
    "stays pending until the guarded action locks safety in.")


def _emit_monitor(canon: dict, kind: str, params: dict, formula: str,
                  alphabet: list) -> bytes:
    acts = sorted(alphabet)
    lines = [
        '"""Monitor DFA table -- AUTOGENERATED by generators.monitor_gen.',
        "",
        "kind=%r params=%r" % (kind, params),
        "LTLf=%r over %s atoms; alphabet=%r." % (formula, _PREFIX, acts),
        "",
    ]
    lines += _PENDING_DOC.split("\n")
    lines += [
        '"""',
        "",
        "TABLE = {",
    ]
    for s in sorted(canon["table"]):                   # states sorted
        row = {a: canon["table"][s][a] for a in sorted(canon["table"][s])}
        lines.append("    %r: %r," % (s, row))         # (state, sorted-action row)
    lines += [
        "}",
        "INITIAL = %r" % canon["initial"],
        "ACCEPTING = %r" % canon["accepting"],          # sorted list of int
        "SINK = %r" % canon["sink"],
        "_PERMANENT = %r" % canon["permanent"],         # sorted list of int
        "_ACC = frozenset(ACCEPTING)",                  # sets built at import,
        "_PERM = frozenset(_PERMANENT)",                # never emitted (hashseed)
        "",
        "",
        "def step(state, symbol):",
        "    # symbol is a RAW action name; unknown symbol -> dead sink.",
        "    row = TABLE.get(state)",
        "    if row is None:",
        "        return SINK",
        "    return row.get(symbol, SINK)",
        "",
        "",
        "def accepting(state):",
        "    return state in _ACC",
        "",
        "",
        "def pending(state):",
        "    # undischarged obligation == not in a permanently-accepting trap.",
        "    return state not in _PERM",
        "",
    ]
    return ("\n".join(lines)).encode()


# ------------------------------------------------- emit ref_stepper.py (chan 2)
# Fixed, independent decision procedure -- re-parses the LTLf spec and drives
# flloat's OWN automaton live (shares no code with monitor.py's table walk).
# Only the header constants below are parametric.
_REF_RUNTIME = r'''
# --- independent reference stepper: flloat automaton driven live -------------
from flloat.parser.ltlf import LTLfParser

_ACTS = sorted(ALPHABET)
_INTERP = {a: {PREFIX + x: (x == a) for x in _ACTS} for a in _ACTS}
_DFA = LTLfParser()(FORMULA).to_automaton()


def _run(trace):
    """Walk the trace from the initial state; None on an unknown symbol
    (dead) -- mirrors monitor.py routing unknown symbols to a dead sink."""
    st = _DFA.initial_state
    for sym in trace:
        if sym not in _INTERP:
            return None
        st = _DFA.get_successor(st, _INTERP[sym])
        if st is None:
            return None
    return st


def _reaches_nonaccepting(st):
    """BFS over the concrete alphabet: is any non-accepting state reachable
    from st (st included)?  Independent recomputation of `not permanent`."""
    seen = {st}
    q = [st]
    while q:
        s = q.pop()
        if not _DFA.is_accepting(s):
            return True
        for a in _ACTS:
            t = _DFA.get_successor(s, _INTERP[a])
            if t is None:
                return True
            if t not in seen:
                seen.add(t)
                q.append(t)
    return False


def accepting(trace):
    st = _run(trace)
    return False if st is None else bool(_DFA.is_accepting(st))


def pending(trace):
    st = _run(trace)
    if st is None:                     # dead: obligation never dischargeable
        return True
    return _reaches_nonaccepting(st)
'''


def _emit_ref(formula: str, alphabet: list) -> bytes:
    lines = [
        '"""Reference stepper -- AUTOGENERATED, channel 2 of the monitor-cert.',
        "",
        "Independent of monitor.py: decides accepting/pending for a whole trace",
        "by re-parsing the LTLf spec and driving flloat's automaton live.",
        '"""',
        "PREFIX = %r" % _PREFIX,
        "FORMULA = %r" % formula,
        "ALPHABET = %r" % sorted(alphabet),
    ]
    return ("\n".join(lines) + "\n" + _REF_RUNTIME).encode()


def build_crosscheck_harness(alphabet: list, max_len: int) -> bytes:
    """monitor-cert channel 2 harness: drive EVERY action trace up to max_len
    (plus a couple of unknown-symbol traces) through BOTH the baked table
    (monitor.py) and the independent live flloat stepper (ref_stepper.py); assert
    they agree on (accepting, pending).  A mutation in either implementation
    diverges here.  Runs inside the sandbox (ref_stepper imports flloat)."""
    acts = sorted(alphabet)
    lines = [
        "import json, sys, traceback, itertools",
        "import monitor as M",
        "import ref_stepper as R",
        "ALPHA = %r" % acts,
        "MAXLEN = %r" % int(max_len),
        "",
        "def drive(trace):",
        "    st = M.INITIAL",
        "    for sym in trace:",
        "        st = M.step(st, sym)",
        "    return bool(M.accepting(st)), bool(M.pending(st))",
        "",
        "def main():",
        "    try:",
        "        traces = []",
        "        for n in range(MAXLEN + 1):",
        "            for t in itertools.product(ALPHA, repeat=n):",
        "                traces.append(list(t))",
        "        traces += [['__unknown__'], ALPHA[:1] + ['__unknown__']]",
        "        for tr in traces:",
        "            m = drive(tr)",
        "            f = (bool(R.accepting(tr)), bool(R.pending(tr)))",
        "            assert m == f, ('table vs flloat divergence', tr,",
        "                            'monitor', m, 'ref', f)",
        "        print(json.dumps({'status': 'pass', 'examples': len(traces)}))",
        "    except BaseException as e:",
        "        print(json.dumps({'status': 'fail', 'error': repr(e)[:2000],",
        "                          'traceback': traceback.format_exc()[-2000:]}))",
        "        sys.exit(1)",
        "main()",
    ]
    return ("\n".join(lines) + "\n").encode()


# ------------------------------------------------------------------- public
def build_monitor(kind: str, params: dict, alphabet: list) -> dict:
    """Compile a temporal demand into a certified monitor DFA.

    kind in {"eventually","until","before","within"}; params name the RAW
    action(s)/steps; alphabet is the full list of RAW action names.

    Returns {"monitor.py": bytes, "ref_stepper.py": bytes, "meta": {...}}.
    monitor.py is dependency-free; ref_stepper.py drives flloat live.
    """
    if not alphabet:
        raise ValueError("empty alphabet")
    if len(set(alphabet)) != len(alphabet):
        raise ValueError("duplicate action in alphabet %r" % (alphabet,))
    for n in alphabet:
        _check_name(n)

    formula = _formula(kind, params, alphabet)
    canon = _canonize(formula, alphabet)
    return {
        "monitor.py": _emit_monitor(canon, kind, params, formula, alphabet),
        "ref_stepper.py": _emit_ref(formula, alphabet),
        "meta": {
            "kind": kind, "params": dict(params), "alphabet": sorted(alphabet),
            "formula": formula, "initial": canon["initial"],
            "accepting": canon["accepting"], "sink": canon["sink"],
            "permanent": canon["permanent"], "num_states": canon["num_states"],
        },
    }
