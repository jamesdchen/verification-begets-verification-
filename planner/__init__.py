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
    if language == "ksy":
        atoms = ksy_model.parse_ksy(text).atoms
    elif language == "abnf":
        atoms = abnf_atoms(text)
    else:
        raise ValueError(f"unknown spec language {language}")
    return language, text, atoms


def _grammar_covers(entry: dict, language: str, atoms: frozenset) -> bool:
    return (entry["spec_language"] == language
            and set(atoms) <= set(entry["spec_grammar"]["atoms"]))


def _enumerate_chains(entries, language, atoms, target_language):
    """The 1/2-link chain enumeration, factored out so both `plan` and the
    W0 `plan_for_features` wrapper share ONE coverage rule (fact 2 warns that
    a hand-kept mirror is a latent divergence).  Returns the sorted candidate
    chains (best first); each chain is a list of registry-shaped entries.

    W2 replaces the internals (bounded N-link enumeration) behind this exact
    behavior; today it enumerates single links and one intermediate hop, and
    the `target_language` parameter is the terminal condition (hardcoded
    'python-codec' until W6 needs chains ending at 'python-service')."""
    candidates = []
    # single link: spec language -> target_language
    for g in entries:
        if _grammar_covers(g, language, atoms) and \
                g["output_language"] == target_language:
            candidates.append([g])
    # two links: spec language -> intermediate spec -> target_language
    for g1 in entries:
        if not _grammar_covers(g1, language, atoms):
            continue
        out = g1.get("spec_grammar", {}).get("output", None)
        if not out or g1["output_language"] == target_language:
            continue
        out_lang, out_atoms = out["language"], frozenset(out["atoms"])
        for g2 in entries:
            if _grammar_covers(g2, out_lang, out_atoms) and \
                    g2["output_language"] == target_language:
                candidates.append([g1, g2])
    candidates.sort(key=lambda ch: (
        -sum(1 for l in ch if l["tier"] == "universal"),
        len(ch),
        tuple(l["generator_hash"] for l in ch)))
    return candidates


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
