"""Chain replay certificates (certifying-algorithms sweep, item 2 -- done
properly this time).

THE CLAIM A PLAN MAKES: "this chain of generators validly covers the input
spec and ends at the target language."  The certifying-algorithms rule
(Mehlhorn): the checker must be SIMPLER than the producer and must check the
claim, not re-derive it.  So this module certifies chain VALIDITY -- every
acceptance condition ``_enumerate_chains`` imposes, mirrored one-for-one
against its docstring and body (planner/__init__.py:122-166) -- and only
RECORDS the rank key.  Optimality ("no better chain exists") is a
producer-grade claim: checking it IS re-running the enumeration, so it is
deliberately out of scope here and honestly labeled as such in the result.

The conditions, each with its own named refusal (a refusal names the first
failing condition; the checker never guesses intent):

  C1 chain nonempty and at most MAX_CHAIN links;
  C2 every link IS a provided registry entry -- same generator_hash AND
     byte-equal load-bearing fields (a fabricated or tampered link must not
     pass validity on a matching hash alone);
  C3 no kind=='pass' link (internal pipeline stages are not planner-visible);
  C4 simple chain: no repeated generator_hash;
  C5 head link covers the input: spec_language matches and input atoms are a
     subset of the link's grammar atoms (the ONE coverage rule,
     ``_grammar_covers``);
  C6 every non-terminal link declares spec_grammar.output, and the next link
     covers that declared output (language + atom subset);
  C7 the last link's output_language equals the target.

``replay_chain`` returns {ok, refusal, rank_key, n_links}.  It shares
``_grammar_covers`` with the planner by IMPORT, never by copy, so the
coverage rule cannot drift (the fact-2 discipline: a hand-kept mirror is a
latent divergence)."""
from __future__ import annotations

import common
from planner import MAX_CHAIN, _grammar_covers

# The load-bearing fields a link must match byte-for-byte against its
# registry entry (C2): everything coverage or ranking reads.
_LINK_FIELDS = ("generator_hash", "spec_language", "output_language",
                "spec_grammar", "tier", "kind")


def _canon_link(entry: dict) -> str:
    return common.canonical_json({k: entry.get(k) for k in _LINK_FIELDS})


def replay_chain(chain, entries, language, atoms, target_language,
                 *, max_chain=MAX_CHAIN) -> dict:
    """Certify one chain's validity against a registry snapshot.  Pure,
    deterministic, refusal-first: the result names the FIRST violated
    condition and stops -- a certificate is all-or-nothing."""
    def refuse(cond, why):
        return {"ok": False, "refusal": {"condition": cond, "reason": why},
                "optimality": "not-checked (producer-grade; re-run the "
                              "enumeration to establish it)"}

    if not chain:
        return refuse("C1", "empty chain")
    if len(chain) > max_chain:
        return refuse("C1", f"{len(chain)} links exceeds MAX_CHAIN={max_chain}")

    by_hash = {e.get("generator_hash"): e for e in entries}
    for i, link in enumerate(chain):
        h = link.get("generator_hash")
        reg = by_hash.get(h)
        if reg is None:
            return refuse("C2", f"link {i}: hash {str(h)[:12]}... is not in "
                                f"the provided registry snapshot")
        if _canon_link(link) != _canon_link(reg):
            return refuse("C2", f"link {i}: load-bearing fields differ from "
                                f"the registry entry of the same hash "
                                f"(tampered or stale link)")
        if link.get("kind") == "pass":
            return refuse("C3", f"link {i}: kind=='pass' entries are not "
                                f"planner-visible")

    hashes = [l.get("generator_hash") for l in chain]
    if len(set(hashes)) != len(hashes):
        return refuse("C4", "repeated generator_hash (chain must be simple)")

    cur_lang, cur_atoms = language, frozenset(atoms)
    for i, link in enumerate(chain):
        if not _grammar_covers(link, cur_lang, cur_atoms):
            return refuse("C5" if i == 0 else "C6",
                          f"link {i} ({link.get('name', '?')}) does not cover "
                          f"({cur_lang}, {sorted(cur_atoms)})")
        if i == len(chain) - 1:
            break
        out = link.get("spec_grammar", {}).get("output")
        if not out:
            return refuse("C6", f"link {i}: non-terminal link declares no "
                                f"spec_grammar.output")
        cur_lang, cur_atoms = out["language"], frozenset(out["atoms"])

    if chain[-1].get("output_language") != target_language:
        return refuse("C7", f"last link outputs "
                            f"{chain[-1].get('output_language')!r}, target is "
                            f"{target_language!r}")

    return {"ok": True, "refusal": None, "n_links": len(chain),
            "rank_key": {
                "universal_links": sum(1 for l in chain
                                       if l.get("tier") == "universal"),
                "length": len(chain),
                "hashes": hashes,
            },
            "optimality": "not-checked (producer-grade; re-run the "
                          "enumeration to establish it)"}
