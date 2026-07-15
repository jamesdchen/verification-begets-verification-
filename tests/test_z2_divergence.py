"""Z2 acceptance -- buildloop.mdl.chain_length_for is VERIFIED DIVERGENT from
planner.plan_for_features.

Zone 3 strikes the legacy ``buildloop/mdl.py`` chain-cost mirror as an objective
and routes every chain-cost question through ``planner.plan_for_features`` (the
one coverage rule, ``planner._enumerate_chains``).  The justification is that the
hand-kept mirror in ``mdl.chain_length_for`` is *not interchangeable* with the
planner -- it disagrees on real inputs.  This is a standing regression test that
pins two concrete disagreements so nobody can quietly re-adopt the mirror:

  1. kind=="pass" divergence.  ``_enumerate_chains`` EXCLUDES entries with
     ``kind=="pass"`` (they are internal pipeline stages, not planner-visible).
     ``mdl.chain_length_for`` never inspects ``kind``, so it happily counts a
     pass generator as covering.  Over a backlog this is the plan's "185-vs-0
     covered" gap: mdl calls every spec covered, plan_for_features calls none.

  2. multi-link (3-link) chain divergence.  ``_enumerate_chains`` enumerates
     simple chains up to ``MAX_CHAIN==4`` links; ``mdl.chain_length_for`` is
     hard-coded to only ever find a 1-link or 2-link chain (its length-2 loop has
     no recursion / no third link).  A genuine 3-link chain therefore resolves in
     the planner (length 3) while the mirror reports None -- the plan's
     "None-vs-3" gap.

Fast, LLM-free, no external tools.  Run directly with ``python3
tests/test_z2_divergence.py`` or under pytest.
"""
import os
import sys

# Direct `python3 tests/test_z2_divergence.py` runs without the root conftest
# that adds the repo root to sys.path; add it so the runner works standalone.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import planner
import buildloop.mdl as mdl


# --- entry builders (plain dicts; generator_hash omitted -> plan_for_features
# --- defaults it via planner._hash_entry, exactly as an unregistered candidate
# --- would be priced before admission). -------------------------------------

def _emit(name, atoms, *, lang="ksy", out="python-codec", tier="emit-check",
          kind=None):
    """A terminal emitter: (lang, atoms) -> output_language."""
    g = {"name": name, "tier": tier, "spec_language": lang,
         "output_language": out,
         "spec_grammar": {"atoms": sorted(atoms)},
         "emit_entrypoint": {"kind": "e"}, "contract": {}}
    if kind is not None:
        g["kind"] = kind
    return g


def _xlate(name, in_lang, in_atoms, out_lang, out_atoms, *, tier="emit-check"):
    """A translator link: (in_lang, in_atoms) -> declared output grammar that
    feeds the next link (out_lang, out_atoms)."""
    return {"name": name, "tier": tier, "spec_language": in_lang,
            "output_language": out_lang,
            "spec_grammar": {"atoms": sorted(in_atoms),
                             "output": {"language": out_lang,
                                        "atoms": sorted(out_atoms)}},
            "emit_entrypoint": {"kind": "x"}, "contract": {}}


# --- Divergence 1: kind=="pass" --------------------------------------------

def test_pass_generator_covers_in_mdl_but_not_in_planner():
    """A single generator with kind=="pass" that directly emits python-codec.

    mdl's _covers rule matches it (spec_language + atom-subset) and it emits the
    terminal language, so mdl.chain_length_for returns 1 (covered).
    plan_for_features runs it through _enumerate_chains, which drops kind=="pass"
    entries, so no chain survives -> None (uncovered).  The two disagree on
    coverage for the SAME input."""
    atoms = ["uint:1"]
    passthru = _emit("passthru", atoms, kind="pass")

    mdl_len = mdl.chain_length_for([passthru], "ksy", atoms)
    plan_chain = planner.plan_for_features([passthru], "ksy", atoms)

    assert mdl_len == 1, "mdl mirror ignores kind and counts the pass gen covered"
    assert plan_chain is None, \
        "planner excludes kind=='pass' at _enumerate_chains, so it is uncovered"
    # The teeth: mdl says covered (length 1); planner says not covered (None).
    assert (mdl_len is None) != (plan_chain is None), \
        "mdl and plan_for_features must disagree on coverage for a pass gen"


def test_pass_divergence_at_backlog_scale_185_vs_0():
    """The same disagreement, aggregated the way the DL accounting sees it:
    over a backlog every spec is 'covered' by the pass generator under mdl
    (total_dl.covered == N) while plan_for_features resolves NONE of them.
    This is the plan's "185-vs-0 covered" figure made concrete."""
    atoms = ["uint:1"]
    passthru = _emit("passthru", atoms, kind="pass")

    N = 185
    backlog = [{"path": f"s{i}.ksy", "language": "ksy", "atoms": atoms,
                "size_bytes": 100} for i in range(N)]

    mdl_covered = mdl.total_dl([passthru], backlog)["covered"]
    plan_covered = sum(
        1 for s in backlog
        if planner.plan_for_features([passthru], s["language"], s["atoms"])
        is not None)

    assert mdl_covered == 185, "mdl mirror counts all 185 specs covered"
    assert plan_covered == 0, "planner counts 0 -- pass gen is invisible to it"
    assert mdl_covered != plan_covered, "185-vs-0 standing divergence"


# --- Divergence 2: multi-link (3-link) chain --------------------------------

def test_three_link_chain_resolves_in_planner_but_is_none_in_mdl():
    """A genuine 3-link chain ksy -> L1 -> L2 -> python-codec.

    Each link's spec_grammar.output feeds the next; the terminal link emits
    python-codec.  plan_for_features (MAX_CHAIN==4) resolves it to a length-3
    chain.  mdl.chain_length_for only ever tries chains of length 1 or 2 (no
    third link in its loops), so it returns None -- the "None-vs-3" gap."""
    A = _xlate("A", "ksy", ["a1"], "L1", ["b1"])   # ksy   -> L1
    B = _xlate("B", "L1", ["b1"], "L2", ["c1"])    # L1    -> L2
    C = _emit("C", ["c1"], lang="L2")              # L2    -> python-codec
    entries = [A, B, C]

    plan_chain = planner.plan_for_features(entries, "ksy", ["a1"])
    mdl_len = mdl.chain_length_for(entries, "ksy", ["a1"])

    assert plan_chain is not None, "planner must resolve the 3-link chain"
    assert [l["name"] for l in plan_chain] == ["A", "B", "C"]
    assert len(plan_chain) == 3, "planner reports chain length 3"
    assert mdl_len is None, \
        "mdl mirror caps at 2 links, so a real 3-link chain reads as uncovered"
    # The teeth: planner length 3 vs mirror None -- not interchangeable.
    assert len(plan_chain) != (mdl_len or 0), "None-vs-3 standing divergence"


def test_two_link_chain_is_where_they_still_agree():
    """Guard-rail: the divergence is specific, not a blanket breakage.  For a
    2-link chain both agree (planner length 2, mdl 2).  This keeps divergence
    tests #1/#2 honest -- they fail for the documented structural reasons, not
    because mdl is simply broken for everything."""
    A = _xlate("A", "ksy", ["a1"], "L1", ["b1"])   # ksy -> L1
    B = _emit("B", ["b1"], lang="L1")              # L1  -> python-codec
    entries = [A, B]

    plan_chain = planner.plan_for_features(entries, "ksy", ["a1"])
    mdl_len = mdl.chain_length_for(entries, "ksy", ["a1"])

    assert plan_chain is not None and len(plan_chain) == 2
    assert mdl_len == 2, "2-link chains are the region where the mirror agrees"


if __name__ == "__main__":
    test_pass_generator_covers_in_mdl_but_not_in_planner()
    test_pass_divergence_at_backlog_scale_185_vs_0()
    test_three_link_chain_resolves_in_planner_but_is_none_in_mdl()
    test_two_link_chain_is_where_they_still_agree()
    print("OK: Z2 divergences pinned -- "
          "pass: mdl=1/plan=None (185-vs-0 covered); "
          "3-link: plan=3/mdl=None (None-vs-3).")
