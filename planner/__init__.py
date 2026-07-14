"""Deterministic planner.

Matches an incoming task spec against registered spec grammars and finds a
generator or chain (unification: one link's declared output grammar must be
covered by the next link's input grammar).  Preferences, in order:

  1. more universal-tier links (the planner's preference flips after a
     promotion),
  2. shorter chains,
  3. lexicographic generator-hash (tie-break => full determinism).

Unresolvable specs produce structured coverage-miss records.
"""
from __future__ import annotations

import dataclasses
import pathlib

import common
from generators import ksy_model
from generators.abnf_chain import abnf_atoms, AbnfError

# Bounded exhaustive chain search: enumerate ALL simple chains up to this many
# links (W2.2).  A visited-set BFS is deliberately NOT used -- the top sort key
# (-universal_links) is non-monotone under path extension (a longer all-universal
# chain must beat a shorter emit-check chain reaching the same output, the exact
# behaviour W5's promotion flip relies on), and a visited set prunes precisely
# those winning chains.  Enumeration over a registry this size is cheap.
MAX_CHAIN = 4


def _reading_atoms(text: str):
    """Atoms of a Reading = the multiset of LF kinds it demands (W2.3)."""
    import json
    from generators import reading as _rd
    doc = json.loads(text)
    return frozenset(s.get("lf", {}).get("kind")
                     for s in doc.get("statements", [])
                     if isinstance(s, dict) and s.get("lf"))


# The language registry (W2.3): name -> (text -> atoms).  A *spec language* is
# any key here; `plan()` and `register()` use SPEC_LANGUAGES to decide whether a
# generator's output is an intermediate spec (a translator) or a terminal target
# (an emitter).  service-bundle / macro-reading are registered by W6 / W5.
LANGUAGES = {
    "ksy": lambda t: ksy_model.parse_ksy(t).atoms,
    "abnf": abnf_atoms,
    "reading": _reading_atoms,
}


def register_language(name, loader):
    """W6/W5 hook: add a spec language (idempotent)."""
    LANGUAGES[name] = loader


def _spec_languages():
    return frozenset(LANGUAGES)


class _SpecLanguages(frozenset):
    """A live view of the spec-language set: `in` reflects late registrations
    (W6/W5 call register_language after import)."""
    def __contains__(self, item):
        return item in LANGUAGES


SPEC_LANGUAGES = _SpecLanguages()


@dataclasses.dataclass
class Plan:
    spec_language: str
    spec_atoms: frozenset
    links: list            # registry entries, in execution order
    spec_hash: str

    @property
    def universal_links(self):
        return sum(1 for l in self.links if l["tier"] == "universal")


@dataclasses.dataclass
class CoverageMiss:
    spec_path: str
    spec_hash: str
    spec_language: str
    atoms: list
    missing_atoms: list    # smallest uncovered remainder over live generators
    reason: str

    def to_dict(self):
        return dataclasses.asdict(self)


def load_spec(path_or_text, language=None):
    """Returns (language, text, atoms). Raises on unsupported specs."""
    if isinstance(path_or_text, pathlib.Path) or (
            isinstance(path_or_text, str) and "\n" not in path_or_text
            and pathlib.Path(path_or_text).exists()):
        p = pathlib.Path(path_or_text)
        text = p.read_text()
        language = language or ("abnf" if p.suffix == ".abnf" else "ksy")
    else:
        text = path_or_text
        if language is None:
            language = "abnf" if "=" in text.splitlines()[0] and "meta" not in text \
                else "ksy"
    loader = LANGUAGES.get(language)
    if loader is None:
        raise ValueError(f"unknown spec language {language}")
    atoms = loader(text)
    return language, text, atoms


def _grammar_covers(entry: dict, language: str, atoms: frozenset) -> bool:
    return (entry["spec_language"] == language
            and set(atoms) <= set(entry["spec_grammar"]["atoms"]))


def _enumerate_chains(entries, language, atoms, target_language):
    """Bounded exhaustive enumeration of simple chains (W2.2), factored out so
    both `plan` and the `plan_for_features` wrapper share ONE coverage rule
    (fact 2 warns a hand-kept mirror is a latent divergence).

    A chain's head link must cover the input (language, atoms); each subsequent
    link must cover the previous link's declared output grammar
    (`spec_grammar.output`); a chain is complete when its last link's
    `output_language == target_language`.  Chains are SIMPLE (no repeated
    generator_hash) and at most MAX_CHAIN links, so a translator cycle (A->B,
    B->A) terminates.  Entries with kind=='pass' are excluded (they are internal
    pipeline stages, not planner-visible -- W6).

    Deliberately NOT a visited-set BFS: the sort key's `-universal_links` term is
    non-monotone under extension (a longer all-universal chain outranks a shorter
    emit-check chain to the same output), which a visited set would prune.
    Returns the sorted candidate chains (best first)."""
    entries = [e for e in entries if e.get("kind") != "pass"]
    atoms = frozenset(atoms)
    results = []

    def _extend(chain, cur_lang, cur_atoms):
        if len(chain) >= MAX_CHAIN:
            return
        used = {l.get("generator_hash") for l in chain}
        for g in entries:
            if g.get("generator_hash") in used:
                continue                       # simple chains only
            if not _grammar_covers(g, cur_lang, cur_atoms):
                continue
            new_chain = chain + [g]
            if g["output_language"] == target_language:
                results.append(new_chain)      # terminal link
            else:
                out = g.get("spec_grammar", {}).get("output", None)
                if out:
                    _extend(new_chain, out["language"],
                            frozenset(out["atoms"]))

    _extend([], language, atoms)
    results.sort(key=lambda ch: (
        -sum(1 for l in ch if l["tier"] == "universal"),
        len(ch),
        tuple(l["generator_hash"] for l in ch)))
    return results


def _hash_entry(entry: dict) -> str:
    """The registry's canonical generator hash, so an unregistered candidate
    entry sorts deterministically alongside registered ones (same rule as
    library.Registry.register)."""
    body = {"name": entry.get("name", ""),
            "spec_language": entry["spec_language"],
            "output_language": entry["output_language"],
            "spec_grammar": entry["spec_grammar"],
            "emit_entrypoint": entry.get("emit_entrypoint", {}),
            "contract": entry.get("contract", {})}
    return common.sha256_json(body)


def plan_for_features(entries, language, atoms, target_language="python-codec"):
    """One chain-cost source (W0.3 lands the wrapper; W2.4 replaces internals).

    `entries` is an EXPLICIT list of registered generators and/or unregistered
    candidates -- candidates that lack a `tier`/`generator_hash` default to
    `tier='emit-check'` and the canonical hash, so a not-yet-registered
    candidate can be priced before admission.  Returns the best chain (list of
    entries) covering (language, atoms) and ending at `target_language`, or
    None.  Deterministic and side-effect-free."""
    norm = []
    for e in entries:
        e = dict(e)
        e.setdefault("tier", "emit-check")
        if not e.get("generator_hash"):
            e["generator_hash"] = _hash_entry(e)
        norm.append(e)
    chains = _enumerate_chains(norm, language, frozenset(atoms), target_language)
    return chains[0] if chains else None


def plan(registry, spec_path_or_text, language=None):
    """-> Plan | CoverageMiss"""
    spath = str(spec_path_or_text)[:200]
    try:
        language, text, atoms = load_spec(spec_path_or_text, language)
    except (ksy_model.UnsupportedSpec, AbnfError, ValueError) as e:
        return CoverageMiss(spec_path=spath, spec_hash="", spec_language=language or "?",
                            atoms=[], missing_atoms=[],
                            reason=f"unsupported spec: {e}")
    spec_hash = common.sha256_bytes(text.encode())
    live = registry.live_generators()

    candidates = _enumerate_chains(live, language, atoms, "python-codec")
    if candidates:
        return Plan(spec_language=language, spec_atoms=atoms,
                    links=candidates[0], spec_hash=spec_hash)

    # coverage miss: report the smallest uncovered remainder
    best_missing = set(atoms)
    for g in live:
        if g["spec_language"] != language:
            continue
        missing = set(atoms) - set(g["spec_grammar"]["atoms"])
        if len(missing) < len(best_missing):
            best_missing = missing
    return CoverageMiss(
        spec_path=spath, spec_hash=spec_hash, spec_language=language,
        atoms=sorted(atoms), missing_atoms=sorted(best_missing),
        reason="no registered generator/chain covers this spec")
