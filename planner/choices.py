"""S3 -- choice-space search: the minimum-DL design that ENTAILS the demands.

A Reading (generators.reading) splits its statements by speech-act force into
three disjoint parts (Austin/Searle, see reading.py):

    demand          -- the directive's propositional content (quoted, grounded)
    presupposition  -- licensed but unstated (quoted trigger span)
    choice          -- the pragmatic residue: DESIGN FREEDOM the text leaves
                       open (the lifecycle state set, the per-action transition
                       edges, extra input fields, auxiliary actions)

Only the *choice* residue is the design's to pick.  This module performs the
deterministic, LLM-free search over that residue for the cheapest admissible
design, holding every demand/presupposition BYTE-IDENTICAL (test-pinned): the
search may re-shape the protocol skeleton, never the obligations the request
carries.

What is varied (S3.1):
  * the lifecycle template, drawn from a fixed two-member family
        {["open","closed"], ["open","active","closed"]}   (initial = "open")
  * per action, its single transition edge, ranging over the FORWARD edges and
    SELF edges of the chosen state order (state i -> state j with i <= j).
Everything else in the Reading -- quantities, actions, effects, bounds, the
`always`/`order` obligations, choice-`action`s, `input` fields -- is copied
verbatim into every variant.

The two gates a variant must pass (S3.1):
  (b) ORDER-ENTAILMENT (`reading_compile.compile_reading`): a variant is
      admissible only if compiling it does NOT raise `CompileError`.  Compile
      raises exactly when the CHOSEN transition graph fails to entail a
      demanded `order` -- i.e. a design choice would silently override a
      demand.  Refused variants are COUNTED (S3's ledger) then discarded.
  NON-VACUITY (`reading_compile.entailed_scenarios`): a variant whose demands
      entail no behavioural scenario at all (empty list -- e.g. no legal run
      exists from the initial state) is discarded: an admissible-but-vacuous
      design certifies trivially and means nothing.

Scoring (S3.2, lower is better):

    score(variant) = dl_reading(variant, table)
                     + len(canonical_json(spec_dict)) / 64.0

`dl_reading` (buildloop.mdl_macros) is the reading's minimum-description-length
under the available macro table (an abbreviation table compresses recurring
statement clusters); the second term is a size proxy over the compiled service
meta-spec.  HONEST TIE NOTE (H37): a transition's `from`/`to` are scalar leaves,
so swapping transition TARGETS leaves `dl_reading` unchanged -- the DL term is
INVARIANT across transition retargetings.  The argmin over DL is therefore a
tie CLASS, not a point; within it the spec-size proxy and finally the compile
hash (`sha256_json(spec_text)`) break the tie deterministically.  Because macros
compress only some designs (a macro that abbreviates a specific lifecycle+
transition cluster discounts exactly the variants it matches), the flat-table
argmin (`table = {}`) and a macro-aware argmin can land on DIFFERENT designs --
both admissible, both compiling.

Determinism (house rule 5): no randomness, no wall-clock.  The winner is the
argmin of `(score, sha256_json(spec_text))`, so two runs over the same inputs
return the byte-identical design regardless of enumeration order.
"""
from __future__ import annotations

import copy
import itertools
import json

import common
from generators.reading import parse_reading, BadReading
from generators.reading_compile import (compile_reading, CompileError,
                                        entailed_scenarios)
from generators.service_model import parse_service_spec
from buildloop.mdl_macros import dl_reading

# The lifecycle template family (S3.1).  Both start at "open"; every variant's
# lifecycle is one of these with initial = "open".
LIFECYCLE_FAMILY = (("open", "closed"), ("open", "active", "closed"))
_INITIAL = "open"


def _reading_parts(reading):
    """Accept a Reading dataclass OR a plain {service, statements} dict and
    return (service, [deep-copied statement dicts]).  Copies defensively so the
    caller's input is never mutated (immutability is test-pinned)."""
    if hasattr(reading, "statements"):
        stmts = reading.statements
        service = getattr(reading, "service", "service")
    else:
        stmts = reading["statements"]
        service = reading.get("service", "service")
    return service, [copy.deepcopy(s) for s in stmts]


def _candidate_edges(states):
    """The forward edges (state i -> state j, i < j) and self edges (i == j) of
    the chosen linear state order: exactly the pairs (states[i], states[j]) with
    i <= j."""
    n = len(states)
    return [(states[i], states[j]) for i in range(n) for j in range(i, n)]


def enumerate_variants(reading):
    """Every design in the choice space, as a list of {service, statements}
    dicts, deterministic in order.

    Only the lifecycle statement and the per-action transition statements are
    rewritten; every other statement (all demands and presuppositions, plus any
    choice-`action`/`input`) is copied BYTE-IDENTICALLY.  The lifecycle ranges
    over LIFECYCLE_FAMILY (initial="open"); each transition ranges independently
    over the forward/self edges of the chosen states."""
    service, stmts = _reading_parts(reading)
    life_idx = [i for i, s in enumerate(stmts) if s["lf"]["kind"] == "lifecycle"]
    trans_idx = [i for i, s in enumerate(stmts) if s["lf"]["kind"] == "transition"]
    if not life_idx:
        raise ValueError("reading has no lifecycle statement to vary")

    variants = []
    for states in LIFECYCLE_FAMILY:
        edges = _candidate_edges(states)
        for combo in itertools.product(edges, repeat=len(trans_idx)):
            new = copy.deepcopy(stmts)
            new[life_idx[0]]["lf"] = {"kind": "lifecycle",
                                      "states": list(states),
                                      "initial": _INITIAL}
            new[life_idx[0]]["quote"] = ""
            for ti, (frm, to) in zip(trans_idx, combo):
                action = new[ti]["lf"]["action"]
                new[ti]["lf"] = {"kind": "transition", "action": action,
                                 "from": frm, "to": to}
                new[ti]["quote"] = ""
            variants.append({"service": service, "statements": new})
    return variants


def _synth_request(reading):
    """A permissive request that grounds every copied demand/presupposition:
    the space-join of their quotes.  Groundedness (reading.parse_reading) only
    checks that each normalized quote occurs as a substring of the normalized
    request, so this join grounds them all.  Used only when the caller does not
    pass the original request; passing the SAME request the reading was authored
    against is preferred (and is what the tests do)."""
    _, stmts = _reading_parts(reading)
    quotes = [s.get("quote", "") for s in stmts
              if s.get("force") in ("demand", "presupposition")]
    return " ".join(q for q in quotes if q and q.strip())


def score_design(variant, spec_text, macro_table=None):
    """The S3.2 objective (lower is better): the variant's macro-aware
    description length plus a size proxy over its compiled meta-spec."""
    table = macro_table or {}
    spec_dict = json.loads(spec_text)
    return dl_reading(variant, table) + len(common.canonical_json(spec_dict)) / 64.0


def score_reading(reading, macro_table=None):
    """Z-F FROZEN SCORER (WP-L): the macro-aware description length of one
    reading, ``mdl_macros.dl_reading(reading, macro_table or {})`` (lower is
    better).  This is the reading-DL term of the S3.2 objective, exposed as a
    clean, TOTAL, side-effect-free function so a caller (the speculative pre-gate
    in buildloop.speculate) can rank candidate readings with the SAME macro-aware
    DL the choice-space search uses -- no LLM, no compile, no I/O, no spec.

    `reading` is a Reading dataclass (``.statements``) or a plain {service,
    statements} dict; `macro_table` is an abbreviation table (dict of macro
    definitions, or None/{}).

    Freeze contract:
      * with an EMPTY (or None) table this is EXACTLY the flat reading DL
        ``dl_reading(reading, {})`` -- no macro can match, so every statement is
        priced as itself, and this equals the flat scorer byte-for-byte;
      * with a table whose macro body matches a consecutive window of the
        reading's statements, that MATCHED WINDOW COLLAPSES to one cheap macro
        invocation (``mdl_macros.dl_invocation``), so the macro-aware score is
        strictly LOWER than the flat score -- the compression the freeze buys.

    Deterministic (house rule 5): a greedy longest-body-first statement rewrite,
    no randomness, no wall-clock.  Does NOT change ``search_design`` (which keeps
    its own ``score_design`` = this reading DL + the compiled-spec size proxy)."""
    return dl_reading(reading, macro_table or {})


def search_design(reading, request=None, macro_table=None):
    """Return the minimum-DL admissible, non-vacuous design over the choice space.

    Signature (documented clean form): ``search_design(reading, request=None,
    macro_table=None)``.  `reading` is a Reading dataclass or a {service,
    statements} dict; `request` is the natural-language request the reading was
    grounded against -- since only choices vary (choices quote "") and every
    demand/presupposition is copied unchanged, the SAME request grounds every
    variant.  When `request` is None a permissive request is synthesized from the
    copied quotes (see `_synth_request`).  `macro_table` is the abbreviation
    table used by the DL score (default: the empty, flat table).

    Returns::

        {"reading":    <winning variant dict>,
         "spec_text":  <its compiled service meta-spec, JSON text>,
         "score":      <float, the S3.2 objective at the winner>,
         "considered": <int, variants enumerated over the whole choice space>,
         "refused":    <int, variants gate (b) refused -- CompileError>}

    A variant is admissible iff `compile_reading` does not raise `CompileError`
    (gate b: the chosen graph must entail every demanded order) AND its demands
    entail at least one scenario (non-vacuity).  Ties in `score` break by
    `sha256_json(spec_text)`, so the winner is deterministic (the DL term is a
    tie class across transition retargetings -- see the module docstring)."""
    table = macro_table or {}
    req = request if request is not None else _synth_request(reading)

    considered = 0
    refused = 0
    best_key = None       # (score, compile_hash)
    best = None           # {"reading","spec_text","score"}

    for variant in enumerate_variants(reading):
        considered += 1
        variant_json = json.dumps(variant)
        try:
            parsed = parse_reading(variant_json, req)
        except BadReading:
            # A structurally malformed variant is not part of the design space;
            # skip without counting it as a gate-(b) refusal.
            continue
        try:
            spec_text, _prov = compile_reading(parsed)
        except CompileError:
            # Gate (b): the chosen graph fails to entail a demanded order.
            refused += 1
            continue
        model = parse_service_spec(spec_text)
        if not entailed_scenarios(model, parsed):
            # Non-vacuity: the demands entail no scenario (no legal run) --
            # an admissible-but-empty design certifies trivially; discard.
            continue
        score = score_design(variant, spec_text, table)
        key = (score, common.sha256_json(spec_text))
        if best_key is None or key < best_key:
            best_key = key
            best = {"reading": variant, "spec_text": spec_text, "score": score}

    if best is None:
        raise ValueError("no admissible, non-vacuous design in the choice space")
    best["considered"] = considered
    best["refused"] = refused
    return best
