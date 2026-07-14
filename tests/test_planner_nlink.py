"""Combined-Loop W2 -- N-link planner + registry hardening teeth.

(a) a 2-link all-universal chain beats a 1-link emit-check chain to the same
    output (the non-monotone universal-links preference a visited-set BFS would
    prune);
(b) a cyclic translator pair (A->B, B->A) terminates with the right plan
    (simple-chain + MAX_CHAIN bound);
(c) whole-backlog plans are deterministic across two runs;
(d) generators-table migration parity: an old DB with the narrow tier CHECK and
    no `kind` column, once opened, has the same columns and dict-equal rows as a
    fresh DB (the tier-vocabulary widening is a rebuild, not an ALTER).
"""
import sqlite3

import planner
from library import Registry


def _emit(name, atoms, *, tier="emit-check", lang="ksy", out="python-codec"):
    g = {"name": name, "tier": tier, "spec_language": lang,
         "output_language": out, "spec_grammar": {"atoms": sorted(atoms)},
         "emit_entrypoint": {"kind": "e"}, "contract": {}}
    g["generator_hash"] = planner._hash_entry(g)
    return g


def _xlate(name, in_lang, in_atoms, out_lang, out_atoms, *, tier="emit-check"):
    g = {"name": name, "tier": tier, "spec_language": in_lang,
         "output_language": out_lang,
         "spec_grammar": {"atoms": sorted(in_atoms),
                          "output": {"language": out_lang,
                                     "atoms": sorted(out_atoms)}},
         "emit_entrypoint": {"kind": "x"}, "contract": {}}
    g["generator_hash"] = planner._hash_entry(g)
    return g


def test_two_link_universal_beats_one_link_emit_check():
    X = ["uint:1"]
    Y = ["mid:1"]
    one = _emit("one", X, tier="emit-check")                 # ksy -> codec (1)
    a = _xlate("a", "ksy", X, "ksyM", Y, tier="universal")   # ksy -> ksyM
    b = _emit("b", Y, tier="universal", lang="ksyM")         # ksyM -> codec
    chain = planner.plan_for_features([one, a, b], "ksy", X)
    assert chain is not None
    assert [l["name"] for l in chain] == ["a", "b"], \
        "the 2-link all-universal chain must win over the 1-link emit-check one"


def test_cyclic_translator_pair_terminates():
    A = _xlate("A", "P", ["p"], "Q", ["q"])
    B = _xlate("B", "Q", ["q"], "P", ["p"])   # the cycle back-edge
    T = _emit("T", ["q"], lang="Q")           # Q -> codec terminal
    chain = planner.plan_for_features([A, B, T], "P", ["p"])
    assert chain is not None
    assert [l["name"] for l in chain] == ["A", "T"]


def test_whole_backlog_plan_is_deterministic(tmp_path):
    import common
    from buildloop.loop import backlog_index
    reg = Registry(db_path=str(tmp_path / "r.sqlite"))
    reg.register(name="kaitai", tier="emit-check", spec_language="ksy",
                 output_language="python-codec",
                 spec_grammar={"atoms": ["endian:be", "endian:le", "uint:1",
                                         "uint:2", "uint:4", "uint:8",
                                         "sint:1", "sint:2", "sint:4", "sint:8",
                                         "magic", "str-fixed", "strz",
                                         "str-lenprefix:1", "str-lenprefix:2",
                                         "repeat:lit", "repeat:ref", "enum"]},
                 emit_entrypoint={"kind": "ksc-python-rw"},
                 contract={"type": "codec-roundtrip"}, provenance={})
    backlog = backlog_index(common.REPO_ROOT / "specs" / "backlog")
    assert backlog, "backlog must be present"

    def serialize():
        out = []
        for s in backlog:
            p = planner.plan(reg, s["path"])
            if isinstance(p, planner.CoverageMiss):
                out.append((s["path"], "MISS"))
            else:
                out.append((s["path"],
                            tuple(l["generator_hash"] for l in p.links)))
        return out

    a = serialize()
    b = serialize()
    assert a == b, "two runs over the same registry must produce identical plans"
    # every ksy spec the single emitter covers routes as a 1-link chain.
    covered = [x for x in a if x[1] != "MISS"]
    assert covered and all(len(x[1]) == 1 for x in covered)


def test_generators_migration_parity(tmp_path):
    fresh = str(tmp_path / "fresh.sqlite")
    Registry(db_path=fresh).db.close()

    legacy = str(tmp_path / "legacy.sqlite")
    con = sqlite3.connect(legacy)
    con.executescript("""
      CREATE TABLE generators(
        generator_hash TEXT PRIMARY KEY, name TEXT NOT NULL,
        tier TEXT NOT NULL CHECK(tier IN ('emit-check','universal')),
        spec_language TEXT NOT NULL, output_language TEXT NOT NULL,
        spec_grammar TEXT NOT NULL, emit_entrypoint TEXT NOT NULL,
        contract TEXT NOT NULL, provenance TEXT NOT NULL,
        emission_checked INTEGER NOT NULL DEFAULT 0,
        emission_failures INTEGER NOT NULL DEFAULT 0, admitted_at TEXT NOT NULL,
        retired INTEGER NOT NULL DEFAULT 0, subsumed_by TEXT,
        description_length REAL NOT NULL DEFAULT 0);
    """)
    con.execute(
        "INSERT INTO generators(generator_hash,name,tier,spec_language,"
        "output_language,spec_grammar,emit_entrypoint,contract,provenance,"
        "admitted_at) VALUES('h','g','emit-check','abnf','ksy',"
        "'{\"atoms\":[]}','{}','{}','{}','t')")
    con.commit()
    con.close()

    reg = Registry(db_path=legacy)   # opening runs the rebuild migration
    cols = [(r[1], r[2]) for r in reg.db.execute(
        "PRAGMA table_info(generators)").fetchall()]
    fresh_reg = Registry(db_path=fresh)
    fcols = [(r[1], r[2]) for r in fresh_reg.db.execute(
        "PRAGMA table_info(generators)").fetchall()]
    assert cols == fcols, "migrated column set/types must equal fresh"
    # the migrated row is intact and its kind was backfilled (abnf->ksy is a
    # translator: output_language 'ksy' is a spec language).
    row = reg.get("h")
    assert row["kind"] == "translator"
    assert row["name"] == "g" and row["tier"] == "emit-check"
