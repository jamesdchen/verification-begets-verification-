"""The build loop: coverage misses -> LLM-proposed generator specs -> kernel
-> admission (or ErrorTranscript-driven refinement, max 5 rounds).

The LLM is an untrusted proposal engine: its output is validated to be a
pure spec, then everything it claims is checked by the kernel.  Nothing here
runs on the task-time path.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib

import common
import planner as planner_mod
from buildloop import llm, validate, admission, dl, recurrence

MAX_ROUNDS = 5

# Tie-break precedence when two moves score equal (W3.2: kind order, then
# lexicographic candidate_key).  Scores are compared first; this only settles
# genuine ties, keeping the ranked-move log deterministic.
# F-INT-1 (⚠FI-15): the fifth typed miss, `math`, ranks AFTER toll (the four
# prior values are untouched, so zero-math snapshots are byte-identical); the
# rank is frozen here, not improvised, because the math-vs-request score tie is
# common and `score_moves`' sort KeyErrors without the entry.
KIND_ORDER = {"coverage": 0, "request": 1, "recurrence": 2, "toll": 3,
              "math": 4}

# A3 refusal memory (⚠FI-3, mark-don't-omit): a math move whose demand_id has
# accrued this many `math-refused` events is marked `suppressed_by` in
# `score_moves` (never eligible for argmax) but still generated and still
# ledger-priced, so the miss stays visible in `log_moves` -- exactly the toll
# suppression pattern.
MATH_MAX_ATTEMPTS = 2

KSY_ATOM_DOC = """\
Feature-atom vocabulary for ksy generator grammars (a generator covers a task
spec iff the spec's atoms are a subset of the generator's atoms):
  endian:be endian:le       -- record endianness used by multi-byte ints
  uint:1 uint:2 uint:4 uint:8   sint:1 sint:2 sint:4 sint:8
  magic                     -- fixed 'contents' bytes fields
  str-fixed                 -- str with a literal size
  str-lenprefix:1 str-lenprefix:2 -- u1/u2 length field + str of that size
  strz                      -- null-terminated string
  repeat:lit repeat:ref     -- repeated ints (literal count / count field)
  enum                      -- uint field constrained to an enum
"""

GEN_SPEC_DOC = """\
Return ONLY a JSON object (no prose, no markdown fences) of this exact shape:
{
  "name": "<lowercase-kebab-name>",
  "spec_language": "ksy",
  "grammar_atoms": ["...atoms from the vocabulary..."],
  "emitter": "ksc-python-rw"
}
The generator you are specifying is: Kaitai Struct compiles any .ksy task
spec whose atoms fall inside grammar_atoms into a read-write Python codec.
Your job is only to DECLARE the coverage grammar. Every emission will be
individually checked by a verification kernel (Hypothesis round-trip fuzzing
of the real codec + a Dafny proof of the spec-level contract), so an
overbroad claim will be caught and rejected. An admission is also subject to
a minimum-description-length gate over the whole backlog: prefer ONE general
grammar that consolidates/subsumes existing generators and covers many
outstanding specs over a narrow one, unless breadth would break correctness.
"""

ABNF_SPEC_DOC = """\
Return ONLY a JSON object (no prose, no markdown fences) of this exact shape:
{
  "name": "<lowercase-kebab-name>",
  "spec_language": "abnf",
  "grammar_atoms": [...subset of: "abnf:lit","abnf:digit","abnf:hexdig","abnf:alpha","abnf:sp","abnf:crlf"...],
  "emitter": "abnf-to-ksy",
  "grammar_js": "<a tree-sitter grammar.js source as one JSON string>"
}
grammar_js must be a PURELY DECLARATIVE tree-sitter grammar:
`module.exports = grammar({ name: '...', rules: { ... } })` with rule bodies
that are single-expression arrow functions using only tree-sitter combinators
(seq, choice, repeat, repeat1, optional, token, and regexes). No statements,
no imports, no template literals, no `=>` with a `{` body.
It must parse single-rule ABNF specs of the form:
    record = "LIT" 4DIGIT SP 2HEXDIG CRLF
and expose these NAMED node types (the chain's mapper consumes them, in
source order):
  - literal     : a quoted string INCLUDING the quotes, e.g. "LOG"
  - repetition  : <count><CORE> for DIGIT/HEXDIG/ALPHA, e.g. 4DIGIT (count optional)
  - core_rule   : a bare core rule: SP | CRLF | DIGIT | HEXDIG | ALPHA
Hide the rule name and '=' (use anonymous tokens), so only the element nodes
above are named. The emitted parser is executed sandboxed and its AST is
cross-checked against a reference tokenizer; any mismatch rejects the
emission.
"""


def backlog_index(backlog_dir) -> list:
    out = []
    for p in sorted(pathlib.Path(backlog_dir).glob("*")):
        if p.suffix not in (".ksy", ".abnf"):
            continue
        try:
            language, text, atoms = planner_mod.load_spec(p)
        except Exception:
            continue
        out.append({"path": str(p), "language": language,
                    "atoms": frozenset(atoms), "size_bytes": len(text)})
    return out


def coverage_misses(registry, backlog):
    misses = []
    for s in backlog:
        pl = planner_mod.plan(registry, s["path"])
        if isinstance(pl, planner_mod.CoverageMiss):
            misses.append((s, pl))
    return misses


def group_misses(misses):
    groups = {}
    for s, m in misses:
        key = (s["language"], frozenset(m.missing_atoms))
        g = groups.setdefault(key, {"language": s["language"],
                                    "missing": sorted(m.missing_atoms),
                                    "specs": [], "atoms_union": set()})
        g["specs"].append(s)
        g["atoms_union"] |= set(s["atoms"])
    return list(groups.values())


LOOKAHEAD_DEPTH = 2     # S2: rollout horizon (hypothetical admissions) for the
                        # additive `lookahead` pick_group policy.


def pick_group(groups, policy, backlog, registry):
    """frequency: the most recurrent miss signature.
    closure: the signature whose resolution newly covers the most backlog
    specs (unification lookahead with a candidate grammar = union of the
    group's spec atoms).
    lookahead (S2): the group whose depth-LOOKAHEAD_DEPTH rollout of hypothetical
    admissions reaches the lowest ledger_dl -- priced in the live currency
    through `planner.plan_for_features` + `dl._ledger_total` (never a
    re-implemented coverage mirror).  Lower cost wins, so this branch takes the
    `min` where the other two take a `max`."""
    if not groups:
        return None
    if policy == "frequency":
        return max(groups, key=lambda g: (len(g["specs"]),
                                          "".join(g["missing"])))
    if policy == "lookahead":
        from planner import lookahead as _lookahead
        generators = registry.live_generators()
        return min(groups, key=lambda g: (
            _lookahead.rollout_value(generators, backlog, g,
                                     depth=LOOKAHEAD_DEPTH),
            "".join(g["missing"])))
    covered_now = {s["path"] for s in backlog
                   if not isinstance(planner_mod.plan(registry, s["path"]),
                                     planner_mod.CoverageMiss)}

    def closure_gain(g):
        cand = g["atoms_union"]
        return sum(1 for s in backlog
                   if s["language"] == g["language"]
                   and s["path"] not in covered_now
                   and set(s["atoms"]) <= cand)
    return max(groups, key=lambda g: (closure_gain(g), "".join(g["missing"])))


def build_prompt(group, registry, prior_transcripts):
    example = pathlib.Path(group["specs"][0]["path"]).read_text()
    live = registry.live_generators()
    live_desc = "\n".join(
        f"  - {g['name']} ({g['tier']}, {g['spec_language']}): "
        f"{sorted(g['spec_grammar']['atoms'])}" for g in live) or "  (none)"
    doc = GEN_SPEC_DOC if group["language"] == "ksy" else ABNF_SPEC_DOC
    parts = [
        "You are the untrusted proposal engine of a certified generator "
        "bootstrap system. You may ONLY author declarative specifications; "
        "any general-purpose code will be rejected by a validator.",
        f"COVERAGE MISS: {len(group['specs'])} backlog task specs in spec "
        f"language '{group['language']}' are uncovered. Missing feature "
        f"atoms: {group['missing']}. Union of atoms over the missed specs: "
        f"{sorted(group['atoms_union'])}.",
        "Example missed task spec:\n---\n" + example + "\n---",
        KSY_ATOM_DOC if group["language"] == "ksy" else
        "ABNF subset: one rule 'record = elements' with quoted literals, "
        "nDIGIT/nHEXDIG/nALPHA repetitions, and SP/CRLF/DIGIT/HEXDIG/ALPHA "
        "core rules.",
        "Currently registered live generators:\n" + live_desc,
        doc,
    ]
    for i, t in enumerate(prior_transcripts):
        parts.append(f"PRIOR ATTEMPT {i + 1} FAILED. Kernel/validator "
                     f"transcript:\n{t[:2500]}\nFix the specification "
                     "accordingly and return the corrected JSON only.")
    return "\n\n".join(parts)


# ============================================================ miss taxonomy
# The five typed misses (plan §4.7 + F-INT-1 G1).  CoverageMiss already lives in
# the planner (`planner_mod.CoverageMiss`); the other four are defined here.
# Each is to_dict()-able and logged verbatim.
@dataclasses.dataclass
class RequestMiss:
    demand_id: str
    request_ref: str
    reason: str

    def to_dict(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass
class RecurrenceMiss:
    cluster_key: list
    uses: int
    dl_saving: float

    def to_dict(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass
class TollMiss:
    incumbent_hash: str
    calls: float
    toll_stock: float
    evidence_hash: str

    def to_dict(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass
class MathMiss:
    demand_id: str
    source_ref: str
    attempts: int
    suppressed: bool

    def to_dict(self):
        return dataclasses.asdict(self)


# ================================================================= scoring
# Every move carries a `score` = the OPTIMISTIC upper bound on the ledger_dl it
# removes (bigger is better).  The logged `expected_dl_delta` is `-score` (a DL
# drop is a negative delta).  All scoring reads the FROZEN snapshot only -- no
# wall-clock ever enters a score or tie-break (house rule 13).


def _missing_atoms(generators, language, feats):
    """Smallest uncovered remainder of `feats` over any single live generator of
    the language (mirrors CoverageMiss.missing_atoms); the full feature set if
    nothing of the language is registered."""
    best = set(feats)
    for g in generators:
        if g.get("spec_language") != language:
            continue
        rem = set(feats) - set(g.get("spec_grammar", {}).get("atoms", []))
        if len(rem) < len(best):
            best = rem
    return best


def _coverage_moves(snap):
    groups = {}
    for r in snap.demand:
        if r["kind"] != "spec-file" or r["status"] == "retired":
            continue
        lang, feats = r.get("language"), r.get("features")
        if not lang or not feats:
            continue
        chain = planner_mod.plan_for_features(
            snap.generators, lang, feats, target_language="python-codec")
        if chain is not None:
            continue                                   # already covered
        missing = _missing_atoms(snap.generators, lang, feats)
        key = (lang, tuple(sorted(missing)))
        g = groups.setdefault(key, {"language": lang,
                                    "missing": sorted(missing),
                                    "specs": [], "atoms_union": set()})
        g["specs"].append(r)
        g["atoms_union"] |= set(feats)
    moves = []
    for (lang, _missing), g in sorted(groups.items()):
        # Optimistic UPPER bound on the ledger_dl reduction: the penalty this
        # move retires (UNCOVERED_PENALTY per spec) minus the LEAST a covering
        # generator could plausibly cost -- the description length of a MINIMAL
        # grammar over just this group's atoms.  (Deducting the median of the
        # EXISTING generators was wrong: once real generators carry a 20 KB
        # grammar_js their median exceeds the penalty, so a servable single-spec
        # group scored negative and the loop declared `converged` while a cheap
        # covering generator would still strictly reduce ledger_dl -- a
        # completeness hole found by adversarial review.)
        est = dl.generator_dl({"spec_grammar": {"atoms": sorted(g["atoms_union"])},
                               "emit_entrypoint": {}})
        score = dl.UNCOVERED_PENALTY * len(g["specs"]) - est
        ck = "coverage:%s:%s" % (lang, ",".join(g["missing"]))
        moves.append({"kind": "coverage", "candidate_key": ck,
                      "score": score, "group": g})
    return moves


def _request_moves(snap):
    moves = []
    for r in snap.demand:
        if r["kind"] != "nl-request" or r["status"] == "retired":
            continue
        if snap.readings.get(r["demand_id"]) is not None:
            continue                                   # already has a Reading
        ck = "request:%s" % r["demand_id"]
        moves.append({"kind": "request", "candidate_key": ck,
                      "score": dl.UNCOVERED_PENALTY,
                      "demand_id": r["demand_id"], "row": r})
    return moves


def _math_moves(snap):
    """F-INT-1: propose serving one unserved EXOGENOUS math-source row (G1).

    A row qualifies when it is `math-source`, not retired, `origin ==
    "exogenous"` (system-origin DREAM rows price at 0 in dl.py and MUST NOT
    generate a move), and carries no reading yet.  The score is the NET
    ledger_dl the move optimistically removes (⚠FI-2): the UNCOVERED_PENALTY it
    retires minus a cheap PRE-authoring cost proxy
    `READING_CHAIN_COST + size_bytes/8` (the `_toll_moves` idiom).  A flat +50
    would make the loop take moves it prices as DL-increasing on a served row
    (fixture 04 serves at 68.0 > 50.0); the real served price is re-checked at
    dispatch by the ⚠FI-2 price gate before any persist."""
    moves = []
    for r in snap.demand:
        if r["kind"] != "math-source" or r["status"] == "retired":
            continue
        if r.get("origin") != "exogenous":
            continue                                   # dreams never bill (E3)
        did = r["demand_id"]
        if snap.readings.get(did) is not None:
            continue                                   # already has a Reading
        est_reading_cost = (dl.READING_CHAIN_COST
                            + (r.get("size_bytes") or 0) / 8.0)
        ck = "math:%s" % did
        moves.append({"kind": "math", "candidate_key": ck,
                      "score": dl.UNCOVERED_PENALTY - est_reading_cost,
                      "demand_id": did, "row": r})
    return moves


def _exogenous_witness_filter(readings):
    """S5 witness discipline on the LIVE path: only real (exogenous-origin)
    readings may witness a macro.  Returns a predicate that keeps exogenous
    readings when ANY system-origin (dream) reading is present, else None (so a
    dream-free corpus is byte-identical to before -- and a corpus of untagged
    test readings, which carry no origin, is unaffected)."""
    if any(r.get("origin") == "system" for r in readings if isinstance(r, dict)):
        return lambda r: r.get("origin") == "exogenous"
    return None


def _recurrence_moves(snap):
    readings = list(snap.readings.values())
    wf = _exogenous_witness_filter(readings)
    moves = []
    for c in recurrence.mine(readings, snap.macro_table, witness_filter=wf):
        ck = "recurrence:%s" % c["candidate"]["name"]
        moves.append({"kind": "recurrence", "candidate_key": ck,
                      "score": float(c["dl_saving"]),
                      "candidate": c["candidate"], "uses": c["uses"],
                      "cluster_key": c["cluster_key"]})
    return moves


def _toll_evidence_hash(registry, row, incumbent_hash):
    """Evidence a conversion refusal is keyed to: the lift bound `n` (a counter
    the lift bumps as it re-attempts at larger n) and the tool surface.  An
    unchanged evidence hash means the standing toll grew but the CASE did not --
    the refusal-memory suppression condition (W3.2)."""
    n = registry.counter_get("lift_n:%s" % incumbent_hash)
    surface = row.get("payload_ref") or incumbent_hash
    return common.sha256_json({"n": n, "tool_surface": surface})


def _toll_moves(snap, registry):
    moves = []
    for r in snap.demand:
        if r["kind"] != "caged-incumbent" or r["status"] != "open":
            continue
        ih = dl.incumbent_hash_of(r)
        calls = snap.toll_calls.get(ih, 0.0)
        stock = dl.toll_stock(calls)
        est_replacement = (r.get("size_bytes") or 0) / 256.0 + 1.0
        ck = "toll:%s" % ih
        moves.append({"kind": "toll", "candidate_key": ck,
                      "score": stock - est_replacement, "row": r,
                      "incumbent_hash": ih, "calls": calls,
                      "evidence_hash": _toll_evidence_hash(registry, r, ih)})
    return moves


def score_moves(snap, registry):
    """Score the five typed misses over one FROZEN snapshot and rank them.

    Pure and side-effect-free: two calls over the same snapshot and registry
    state return byte-identical `log_moves` (plan tooth c).  Refusal memory
    (W3.2) is applied BEFORE picking, in two forms, each mark-don't-omit:

      * a toll candidate whose evidence hash matches a prior
        `conversion-suppressed` event is marked `suppressed_by` and is never
        eligible to be picked, even though its monotone toll would otherwise be
        argmax (the verified livelock);
      * a `math` candidate (F-INT-1 A3, ⚠FI-3) whose demand_id has accrued
        `MATH_MAX_ATTEMPTS` `math-refused` events is likewise marked
        `suppressed_by` -- still generated and still ledger-priced so the
        DL-priced miss stays visible in `log_moves` and `_log_miss_records`,
        just never picked.

    Returns (moves, log_moves, picked): `moves` are the full internal move dicts
    (carry dispatch payloads), `log_moves` the trimmed decision-log entries
    (§4.10), `picked` the chosen full move or None (terminal / all-suppressed)."""
    suppressed = {e["payload"].get("evidence_hash")
                  for e in registry.events("conversion-suppressed")
                  if e["payload"].get("evidence_hash")}
    math_attempts = {}
    for e in registry.events("math-refused"):
        did = e["payload"].get("demand_id")
        if did:
            math_attempts[did] = math_attempts.get(did, 0) + 1
    moves = (_coverage_moves(snap) + _request_moves(snap)
             + _recurrence_moves(snap) + _toll_moves(snap, registry)
             + _math_moves(snap))
    for m in moves:
        if m["kind"] == "toll" and m.get("evidence_hash") in suppressed:
            m["suppressed_by"] = m["evidence_hash"]
        elif (m["kind"] == "math"
              and math_attempts.get(m["demand_id"], 0) >= MATH_MAX_ATTEMPTS):
            m["suppressed_by"] = "math-attempts:%d" % math_attempts[m["demand_id"]]
    moves.sort(key=lambda m: (-m["score"], KIND_ORDER[m["kind"]],
                              m["candidate_key"]))
    picked = next((m for m in moves
                   if m["score"] > 0 and "suppressed_by" not in m), None)
    log_moves = []
    for m in moves:
        lm = {"kind": m["kind"], "candidate_key": m["candidate_key"],
              "expected_dl_delta": round(-m["score"], 3),
              "picked": m is picked}
        if "suppressed_by" in m:
            lm["suppressed_by"] = m["suppressed_by"]
        log_moves.append(lm)
    return moves, log_moves, picked


def _log_miss_records(registry, moves):
    """Log the five typed miss records verbatim (§4.7 + F-INT-1 G1).  A math
    miss is logged even when `suppressed_by` is set (A3 mark-don't-omit), so a
    ledger-priced-but-suppressed math row stays visible in the miss log."""
    for m in moves:
        if m["kind"] == "coverage":
            registry.log_event("coverage-miss", {
                "language": m["group"]["language"],
                "missing": m["group"]["missing"],
                "specs": [s["demand_id"] for s in m["group"]["specs"]]})
        elif m["kind"] == "request":
            registry.log_event("request-miss", RequestMiss(
                m["demand_id"], m["row"].get("payload_ref") or "",
                "no-certified-reading").to_dict())
        elif m["kind"] == "recurrence":
            registry.log_event("recurrence-miss", RecurrenceMiss(
                m["cluster_key"], m["uses"], m["score"]).to_dict())
        elif m["kind"] == "toll":
            registry.log_event("toll-miss", TollMiss(
                m["incumbent_hash"], m["calls"],
                dl.toll_stock(m["calls"]), m["evidence_hash"]).to_dict())
        elif m["kind"] == "math":
            sup = m.get("suppressed_by")
            attempts = int(sup.split(":")[1]) if isinstance(sup, str) \
                and sup.startswith("math-attempts:") else 0
            registry.log_event("math-miss", MathMiss(
                m["demand_id"], m["row"].get("payload_ref") or "",
                attempts, sup is not None).to_dict())


# ================================================================ move exec
# The registered-callable dispatch (§5): `run_move(kind, ...) -> event`.  W3
# lands the stubs; W4.2 plugs the real conversion move in behind the frozen
# interface.  Each executor takes the picked full move + context and returns a
# result dict with at least a `status`.
def _run_coverage_breadth(registry, backlog, group, *, policy="frequency",
                          use_corpus=False, model=None):
    """The unchanged breadth pipeline: LLM proposes a generator spec, the kernel
    checks it, admission gates on ledger_dl (max MAX_ROUNDS refinement rounds)."""
    transcripts = []
    for round_no in range(1, MAX_ROUNDS + 1):
        prompt = build_prompt(group, registry, transcripts)
        resp = llm.call_llm(prompt, model=model)
        registry.counter_add("llm_input_tokens", resp["input_tokens"])
        registry.counter_add("llm_output_tokens", resp["output_tokens"])
        try:
            doc = validate.validate_generator_spec(resp["text"])
        except validate.SpecViolation as e:
            transcripts.append(f"Spec validator rejected the proposal: {e}")
            registry.log_event("proposal-rejected", {
                "round": round_no, "reason": str(e)[:500],
                "caught_by": "spec-validator"})
            continue
        provenance = {
            "author": "buildloop-llm", "llm_model": resp["model"],
            "proposal_round": round_no,
            "proposal_sha256": common.sha256_bytes(resp["text"].encode()),
            "parents": (["tree-sitter"] if doc["spec_language"] == "abnf"
                        else ["kaitai-struct-compiler"]),
            "depth": 2 if doc["spec_language"] == "abnf" else 1,
        }
        candidate = admission.candidate_entry_from_spec(doc, provenance)
        try:
            event = admission.admit(registry, candidate, backlog,
                                    use_corpus=use_corpus)
            event.update({"status": "admitted", "rounds": round_no,
                          "policy": policy, "miss": group["missing"]})
            return event
        except admission.AdmissionFailure as e:
            transcripts.append(e.transcript.get("llm_feedback", str(e))
                               if isinstance(e.transcript, dict) else str(e))
        except Exception as e:  # emit errors etc. -> also feed back
            transcripts.append(f"Emission machinery error: {e}")
    return {"status": "exhausted", "rounds": MAX_ROUNDS, "policy": policy,
            "miss": group["missing"], "transcripts": transcripts[-1:]}


def _dispatch_coverage(move, snap, registry, backlog, policy, use_corpus, model):
    """Map the picked coverage group back to the on-disk backlog and run the
    breadth pipeline (scoring is over the snapshot; execution stays on the
    proven backlog path so cgb/run_experiment behaviour is unchanged)."""
    groups = group_misses(coverage_misses(registry, backlog))
    group = pick_group(groups, policy, backlog, registry)
    if group is None:
        return {"status": "converged"}
    return _run_coverage_breadth(registry, backlog, group, policy=policy,
                                 use_corpus=use_corpus, model=model)


def _dispatch_request(move, snap, registry, backlog, policy, use_corpus, model):
    """Schedule the existing semantic pipeline for an unserved NL request
    (W3.1).  Live synthesis needs an LLM (`--full`); with no model the move is a
    scheduled marker so the LLM-free loop never crashes (the demo seeds a
    pre-canned Reading via registry.reading_add instead)."""
    if model is None:
        return {"status": "request-scheduled", "demand_id": move["demand_id"],
                "note": "live reading synthesis deferred to --full"}
    from buildloop import service_loop
    # S4.0 fill-path fix (H46): `payload_ref` is a repo-relative PATH; the request
    # TEXT lives in that file.  The old code (1) fed the path string where the
    # request text belongs and (2) called `synthesize_service`, which never
    # returns a `reading` key -- only `synthesize_semantic` does -- so the
    # reading-persistence branch was unreachable and the live loop never grew the
    # corpus recurrence mines.  Read the text and drive the semantic path.
    ref = move["row"].get("payload_ref") or ""
    p = (common.REPO_ROOT / ref) if ref else None
    request_text = (p.read_text() if (p is not None and p.exists()
                                      and p.is_file()) else (ref or move["demand_id"]))
    res = service_loop.synthesize_semantic(request_text, model=model)
    if res.get("status") == "certified" and res.get("reading") is not None:
        cert_id = res.get("cert_id") or common.sha256_json(
            [[L[0], bool(L[1])] for L in res.get("layers", [])])
        registry.reading_add(move["demand_id"],
                             common.canonical_json(res["reading"]), cert_id)
    return {"status": "request-" + res.get("status", "scheduled"),
            "demand_id": move["demand_id"]}


# S1.3: the searched-admission upgrade is flag-gated; the default is BYTE-
# IDENTICAL to the landed greedy scheduler (one max-marginal-saving macro per
# iteration), so recorded fixtures are unchanged.  demo_macro_search.py / its
# tests flip SEARCHED_RECURRENCE on.
SEARCHED_RECURRENCE = False
SEARCH_BEAM_WIDTH = 4
SEARCH_MAX_DEPTH = 4


def _dispatch_recurrence(move, snap, registry, backlog, policy, use_corpus,
                         model):
    """Admit the mined macro(s), then run macro GC (W3.3) against the corpus.

    Default (greedy, regression-pinned): admit the single picked
    max-marginal-saving macro.  With SEARCHED_RECURRENCE on (S1.3), beam-search
    the admission SEQUENCE minimizing corpus_dl and admit every macro in the
    winning table -- each still passing the explicit macro_admission_decision
    gate inside `recurrence.searched_macro_sequence` (Z1)."""
    readings = list(snap.readings.values())
    wf = _exogenous_witness_filter(readings)      # S5: dreams never witness live
    if not SEARCHED_RECURRENCE:
        cand = move["candidate"]
        registry.macro_add(cand["name"], common.canonical_json(cand))
        retired = recurrence.gc_macros(registry, readings, witness_filter=wf)
        return {"status": "macro-admitted", "macro": cand["name"],
                "retired": retired}
    before = dict(snap.macro_table)
    best = recurrence.searched_macro_sequence(
        readings, before, beam_width=SEARCH_BEAM_WIDTH,
        max_depth=SEARCH_MAX_DEPTH, witness_filter=wf)
    admitted = [name for name in sorted(best) if name not in before]
    for name in admitted:
        registry.macro_add(name, common.canonical_json(best[name]))
    retired = recurrence.gc_macros(registry, readings, witness_filter=wf)
    return {"status": "macro-admitted", "macros": admitted,
            "strategy": "search", "retired": retired}


def _dispatch_toll(move, snap, registry, backlog, policy, use_corpus, model):
    """W3 stub for the conversion move (W4.2 lands the real one behind this
    frozen interface).  Until then a toll candidate is honestly refused; the
    scheduler records the refusal so the monotone toll cannot re-livelock it."""
    return {"status": "refused", "evidence_hash": move["evidence_hash"],
            "reason": "conversion move not yet landed (W4.2); toll accrues"}


def _dispatch_math(move, snap, registry, backlog, policy, use_corpus, model):
    """F-INT-1 (G1): serve one unserved exogenous math-source row.

    Read the source text via the row's `payload_ref` (same resolution as
    `_dispatch_request`), render the math Reading prompt with the LIVE macro
    table (the E1 seam -- `render_math_reading_prompt(source, snap.macro_table)`),
    author via `llm.call_llm`, and certify with the Lean-free fidelity pipeline
    `run.formalize.certify_statement` (event_sink + registry cache hooks,
    `source_id=demand_id`).

    ⚠FI-2 PRICE GATE: persist the reading ONLY if it is DL-lowering -- the
    reading's real served price `READING_CHAIN_COST + dl_reading(statements,
    macro_table)` must be `< UNCOVERED_PENALTY`.  Otherwise the row is left
    uncovered and the dispatch returns a `math-refused / dl-raising` status
    (fixture 04 serves at 68.0 > 50.0 and is refused).  The persisted
    `reading_doc` is exactly `{theorem, statements}` -- NO `origin` key (⚠FI-13:
    the seed path persists none and `dl.snapshot` derives origin from the demand
    row, overwriting any embedded key).

    LLM use is the established loop-time pattern (`_dispatch_request`); with no
    model the move is REFUSED (stage `llm-unavailable`) -- the toll-refusal
    precedent: the refusal is logged, counts toward `MATH_MAX_ATTEMPTS`
    suppression, and the row's penalty honestly persists in the ledger.  (The
    earlier `math-scheduled` marker sat outside the frozen status enum and
    never counted an attempt, so a no-model live loop re-proposed the same
    unactionable argmax forever instead of suppressing it.)"""
    demand_id = move["demand_id"]
    if model is None:
        return {"status": "math-refused", "demand_id": demand_id,
                "stage": "llm-unavailable"}
    from run import formalize
    from buildloop import math_prompt
    ref = move["row"].get("payload_ref") or ""
    p = (common.REPO_ROOT / ref) if ref else None
    source = (p.read_text() if (p is not None and p.exists() and p.is_file())
              else (ref or demand_id))
    prompt = math_prompt.render_math_reading_prompt(source, snap.macro_table)
    resp = llm.call_llm(prompt, model=model)
    registry.counter_add("llm_input_tokens", resp["input_tokens"])
    registry.counter_add("llm_output_tokens", resp["output_tokens"])
    res = formalize.certify_statement(
        source, resp["text"], event_sink=registry.log_event,
        cache_get=registry.cache_get, cache_put=registry.cache_put,
        source_id=demand_id)
    if not res.ok:
        return {"status": "math-refused", "demand_id": demand_id,
                "reason": res.stage or "fidelity-refused", "stage": res.stage}
    # ⚠FI-2 price gate: re-price the AUTHORED reading at its real served cost.
    try:
        doc = json.loads(resp["text"])
    except (ValueError, TypeError):
        return {"status": "math-refused", "demand_id": demand_id,
                "reason": "unparseable-reading", "stage": "math-reading-gate"}
    reading_doc = {"theorem": doc.get("theorem"),
                   "statements": doc.get("statements")}
    served_price = dl.READING_CHAIN_COST + dl.dl_reading(
        reading_doc, snap.macro_table)
    if served_price >= dl.UNCOVERED_PENALTY:
        return {"status": "math-refused", "demand_id": demand_id,
                "reason": "dl-raising", "stage": None}
    cert_id = ("statement-cert:" + res.statement_hash
               if res.statement_cert is None else res.statement_cert.cert_id)
    registry.reading_add(demand_id, common.canonical_json(reading_doc), cert_id)
    return {"status": "math-certified", "demand_id": demand_id, "stage": None}


DEFAULT_DISPATCH = {
    "coverage": _dispatch_coverage, "request": _dispatch_request,
    "recurrence": _dispatch_recurrence, "toll": _dispatch_toll,
    "math": _dispatch_math,
}


def run_iteration(registry, backlog, *, policy="frequency", use_corpus=False,
                  model=None, dispatch=None):
    """One iteration of the miss-typed scheduler (W3.2).

    Reads a frozen snapshot, scores the five typed misses over it, picks the
    argmax (refusal memory applied first), logs the decision (§4.10), then
    dispatches the picked move.  Returns `{"status": "converged"}` when no move
    scores positive and no misses remain (the honest terminal state, replacing
    the legacy `no-misses`).  `dispatch` overrides per-kind executors (used by
    the LLM-free demo/tests)."""
    snap = dl.snapshot(registry)
    snaphash = snap.snapshot_hash()
    moves, log_moves, picked = score_moves(snap, registry)
    _log_miss_records(registry, moves)

    disp = dict(DEFAULT_DISPATCH)
    if dispatch:
        disp.update(dispatch)

    before = dl._ledger_total(snap)["ledger_dl"]
    result, realized = {}, 0.0
    if picked is None:
        status = "converged"
    else:
        result = disp[picked["kind"]](
            picked, snap, registry, backlog, policy, use_corpus, model) or {}
        if picked["kind"] == "toll" and result.get("status") == "refused":
            registry.log_event("conversion-suppressed", {
                "candidate_key": picked["candidate_key"],
                "evidence_hash": picked["evidence_hash"],
                "reason": result.get("reason", "refused")})
        if picked["kind"] == "math" and result.get("status") == "math-refused":
            # A3 refusal memory (toll precedent): count this failed attempt so
            # `score_moves` suppresses the still-priced move after
            # MATH_MAX_ATTEMPTS refusals.
            registry.log_event("math-refused", {
                "demand_id": picked["demand_id"],
                "stage": result.get("stage")})
        realized = round(dl.ledger_dl(registry)["ledger_dl"] - before, 3)
        status = result.get("status", "done")

    registry.log_event("scheduler-decision", {
        "snapshot_hash": snaphash, "moves": log_moves,
        "realized_dl_delta": realized})

    out = {"status": status, "snapshot_hash": snaphash,
           "picked": picked["kind"] if picked else None,
           "picked_key": picked["candidate_key"] if picked else None,
           "moves": log_moves, "realized_dl_delta": realized}
    out.update({k: v for k, v in result.items() if k != "status"})
    return out
