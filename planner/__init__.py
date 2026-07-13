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

    candidates = []
    # single link: spec language -> python-codec
    for g in live:
        if _grammar_covers(g, language, atoms) and \
                g["output_language"] == "python-codec":
            candidates.append([g])
    # two links: spec language -> intermediate spec -> python-codec
    for g1 in live:
        if not _grammar_covers(g1, language, atoms):
            continue
        out = g1.get("spec_grammar", {}).get("output", None)
        if not out or g1["output_language"] == "python-codec":
            continue
        out_lang, out_atoms = out["language"], frozenset(out["atoms"])
        for g2 in live:
            if _grammar_covers(g2, out_lang, out_atoms) and \
                    g2["output_language"] == "python-codec":
                candidates.append([g1, g2])

    if candidates:
        candidates.sort(key=lambda ch: (
            -sum(1 for l in ch if l["tier"] == "universal"),
            len(ch),
            tuple(l["generator_hash"] for l in ch)))
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
