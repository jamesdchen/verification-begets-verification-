"""The build loop: coverage misses -> LLM-proposed generator specs -> kernel
-> admission (or ErrorTranscript-driven refinement, max 5 rounds).

The LLM is an untrusted proposal engine: its output is validated to be a
pure spec, then everything it claims is checked by the kernel.  Nothing here
runs on the task-time path.
"""
from __future__ import annotations

import json
import pathlib

import planner as planner_mod
from buildloop import llm, validate, admission

MAX_ROUNDS = 5

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


def pick_group(groups, policy, backlog, registry):
    """frequency: the most recurrent miss signature.
    closure: the signature whose resolution newly covers the most backlog
    specs (unification lookahead with a candidate grammar = union of the
    group's spec atoms)."""
    if not groups:
        return None
    if policy == "frequency":
        return max(groups, key=lambda g: (len(g["specs"]),
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


def run_iteration(registry, backlog, *, policy="frequency", use_corpus=False,
                  model=None):
    """One build-loop iteration.  Returns a result dict."""
    misses = coverage_misses(registry, backlog)
    if not misses:
        return {"status": "no-misses"}
    for s, m in misses:
        registry.log_event("coverage-miss", m.to_dict())
    group = pick_group(group_misses(misses), policy, backlog, registry)

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
            "proposal_sha256": __import__("common").sha256_bytes(
                resp["text"].encode()),
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
