"""Teeth for WP-T6a-INTEGRATE (buildloop/rung_registry.py; COMPRESSION.md §11.5).

The rung registry, the canonicalization VIEW (FI-W1-2), the norm-cert producer
(FI-W1-1), and the rung admission gate.  LLM-free and Lean-free; relational /
structural asserts only, no absolute solver-count constants.  The norm-cert
solver channel uses z3 + tolerates an absent cvc5 honestly, so cert-minting
asserts are guarded by `_dual_solver_available`.

Registry isolation: every test that populates a registry monkeypatches
`CGB_RUNGS_DIR` to a tmp dir and calls `rr.reload()`, so the committed
`specs/mathsources/rungs/` is never touched.
"""
import copy
import json
import os

import pytest

import common
from buildloop import rung_registry as rr
from buildloop import mdl_macros, recurrence
from kernel import certs


# ============================================================ fixtures / helpers
# A minimal 1-rule rung: sort the children of '=' only.  Small model cost
# (rung_model_bits == 8) so an engineered corpus can make it ADMIT.
SORT_EQ = {"rung": "sort_eq", "over": "pred", "measure": ["size", "inversions"],
           "rules": [{"id": "sort_eq", "primitive": "sort-children",
                      "op": "=", "key": "canonical"}]}

R = lambda n: {"ref": n}


def _reading(theorem, pairs):
    """A math reading: ambient Int + x/y/z objects + one hypothesis per pair,
    all hypotheses sharing (force, quote) so they form a mineable window."""
    stmts = [{"id": "amb", "force": "choice", "quote": "",
              "lf": {"kind": "ambient", "carrier": "Int"}}]
    for name in ("x", "y", "z"):
        stmts.append({"id": f"o{name}", "force": "choice", "quote": "",
                      "lf": {"kind": "object", "name": name, "type": "Int"}})
    for i, (op, a, b) in enumerate(pairs):
        stmts.append({"id": f"h{i}", "force": "presupposition", "quote": "given",
                      "lf": {"kind": "hypothesis",
                             "pred": {"op": op, "args": [a, b]}}})
    return {"theorem": theorem, "statements": stmts}


def _admitting_corpus():
    """Four readings whose '=' hypotheses differ ONLY in argument order across
    readings, so canon MERGES them into one mineable cluster (searched DL drops
    below raw by more than the rung's 8 model bits)."""
    return [_reading("t1", [("=", R("x"), R("y")), ("=", R("y"), R("z"))]),
            _reading("t2", [("=", R("y"), R("x")), ("=", R("z"), R("y"))]),
            _reading("t3", [("=", R("x"), R("y")), ("=", R("y"), R("z"))]),
            _reading("t4", [("=", R("y"), R("x")), ("=", R("z"), R("y"))])]


def _dual_solver_available():
    from kernel.backends import SmtBackend
    be = SmtBackend()
    smt = "(set-logic QF_NIA)\n(assert false)\n(check-sat)\n"
    if be.run_z3(smt, expect="unsat").get("result") != "pass":
        return False
    try:
        return be.run_cvc5(smt, expect="unsat").get("result") == "pass"
    except ModuleNotFoundError:
        return False


@pytest.fixture
def rung_dir(monkeypatch, tmp_path):
    d = str(tmp_path / "rungs")
    monkeypatch.setenv("CGB_RUNGS_DIR", d)
    rr.reload()
    yield d
    rr.reload()


def _admit_and_save(corpus, rung=SORT_EQ):
    res = rr.admit_rung(rung, pricing_corpus=corpus)
    assert res["admitted"], res.get("refusal")
    rr.save_admitted({rung["rung"]: {"row": res["row"], "cert": res["cert"]}},
                     pricing_corpus=corpus)
    return res


# ===================================================================== the pin
def test_empty_registry_canon_is_identity():
    """THE rung-free pin: an empty registry ⇒ canon returns the SAME object."""
    rr.reload()
    r = _reading("t", [("=", R("y"), R("x"))])
    assert rr.canon(r, registry={}) is r
    # and _canon_all is the identity list passthrough
    lst = [r]
    assert rr._canon_all(lst, registry={}) is lst


def test_empty_registry_mining_pricing_byte_identical(rung_dir):
    """With no admitted rung, mine / corpus_dl over a corpus with reversed '='
    args are byte-identical whether or not the seam is invoked (canon=identity)."""
    corpus = _admitting_corpus()
    seam = mdl_macros.corpus_dl(corpus, {}, canon=True)["total"]
    raw = mdl_macros.corpus_dl(corpus, {}, canon=False)["total"]
    assert seam == raw
    assert recurrence.mine(corpus, {}) == recurrence.mine(corpus, {})


# =============================================================== registry conventions
def test_load_proposed_reads_pilot_row():
    """The committed pilot rung is loadable as proposed data and is a valid
    rung-spec."""
    from kernel import rung as _k
    rows = rr.load_proposed()          # default dir = committed specs/
    ids = [r.get("rung") for r in rows]
    assert "canon_commsort" in ids
    pilot = next(r for r in rows if r["rung"] == "canon_commsort")
    assert _k.validate_rung(pilot) is pilot


def test_save_admitted_is_sole_admitter_and_append_only(rung_dir):
    corpus = _admitting_corpus()
    res = _admit_and_save(corpus)
    reg = rr.load_admitted()
    assert set(reg) == {"sort_eq"}

    # sole-admitter: a forged cert id is refused on re-save.
    forged = {"sort_eq": {"row": res["row"],
                          "cert": {**res["cert"], "id": "forged"}}}
    with pytest.raises(rr.SaveRefused, match="cert id mismatch"):
        rr.save_admitted(forged, pricing_corpus=corpus)

    # append-only: a DIFFERENT row under the same id is refused.
    other = copy.deepcopy(res["row"])
    other["rules"][0]["op"] = "and"       # a different (still valid) rung body
    o_res = rr.admit_rung(other, registry={}, pricing_corpus=corpus)
    if o_res["admitted"]:                 # only if it independently admits
        with pytest.raises(rr.SaveRefused, match="append-only"):
            rr.save_admitted({"sort_eq": {"row": o_res["row"],
                                          "cert": o_res["cert"]}},
                             pricing_corpus=corpus)

    # idempotent same-digest re-save is allowed.
    rr.save_admitted({"sort_eq": {"row": res["row"], "cert": res["cert"]}},
                     pricing_corpus=corpus)


def test_save_refuses_row_that_no_longer_admits(rung_dir):
    """Sole-admitter: a cert minted against one corpus cannot be persisted with a
    corpus the row no longer admits over (fail-closed re-admission)."""
    corpus = _admitting_corpus()
    res = rr.admit_rung(SORT_EQ, pricing_corpus=corpus)
    assert res["admitted"]
    with pytest.raises(rr.SaveRefused, match="re-admission refused"):
        rr.save_admitted({"sort_eq": {"row": res["row"], "cert": res["cert"]}},
                         pricing_corpus=[])          # no corpus ⇒ re-admit refuses


# =============================================================== the admission gate
def test_gate_fail_closed_without_corpus():
    res = rr.admit_rung(SORT_EQ, registry={}, pricing_corpus=None)
    assert not res["admitted"]
    assert res["refusal"]["stage"] == "pricing"
    assert "fail-closed" in res["refusal"]["reason"]


def test_pilot_rung_refused_on_real_corpus():
    """The §11.5 pilot commutativity-sort rung is REFUSED on the real committed
    corpus and stays proposed -- the correct, honest outcome (§11.10)."""
    corpus = _real_governed_corpus()
    row = next(r for r in rr.load_proposed() if r["rung"] == "canon_commsort")
    res = rr.admit_rung(row, registry={}, pricing_corpus=corpus)
    assert not res["admitted"]
    # refused at the FIRST failing tooth (per-rule vacuity: most rules are dead
    # vocabulary on this corpus).
    assert res["refusal"]["stage"] == "vacuity"
    # and the MDL counterfactual would ALSO refuse.  MEASURED FLIP at C3
    # cycle-09 (82 sources): canonicalization now saves 4.0 bits, where on every
    # smaller corpus it saved nothing at all (profit >= 0).  The refusal is
    # untouched by that -- the rung's OWN model still costs 2748.0 bits, so the
    # net stays decisively positive.  `net_with_rung_bits > 0` is the tooth;
    # the savings figure is recorded because it moved, not because it decides.
    ok, _reason, pricing = rr._mdl_counterfactual(row, corpus, None)
    assert not ok
    assert pricing["profit_canon_minus_raw"] == -4.0
    assert pricing["net_with_rung_bits"] > 0.0


def test_per_rule_vacuity_refuses_dead_rules():
    """A rung with a rule that fires on < 2 readings is refused at vacuity."""
    # sort '!=' fires nowhere in a '='-only corpus ⇒ dead rule.
    rung = {"rung": "sort_ne", "over": "pred", "measure": ["size", "inversions"],
            "rules": [{"id": "sort_ne", "primitive": "sort-children",
                       "op": "!=", "key": "canonical"}]}
    res = rr.admit_rung(rung, registry={}, pricing_corpus=_admitting_corpus())
    assert not res["admitted"]
    assert res["refusal"]["stage"] == "vacuity"


def test_anti_gaming_plant_is_refused():
    """§11.5 anti-gaming tooth: a rung whose canonicalization reproduces a
    recurrence RAW mining ALREADY finds is refused (profit not negative), even
    though its rule fires on every reading."""
    # Four IDENTICAL reversed-'=' readings: raw mining already captures the
    # recurrence; canon only relabels ⇒ profit == 0.  Mixed nesting/order plant.
    plant = [_reading(f"p{i}", [("=", R("y"), R("x")), ("=", R("z"), R("y"))])
             for i in range(4)]
    okv, _r, _w = rr._per_rule_vacuity(SORT_EQ, plant)
    assert okv                                   # the rule DOES fire (>= 2)
    res = rr.admit_rung(SORT_EQ, registry={}, pricing_corpus=plant)
    assert not res["admitted"]
    assert res["refusal"]["stage"] == "pricing"
    assert "anti-gaming" in res["refusal"]["reason"]
    assert res["pricing"]["profit_canon_minus_raw"] >= 0.0


def test_engineered_rung_admits_with_strictly_negative_net(rung_dir):
    """The gate is not vacuously-refusing: an engineered corpus where canon
    creates real mineable recurrence ADMITS with net < 0."""
    corpus = _admitting_corpus()
    res = rr.admit_rung(SORT_EQ, pricing_corpus=corpus)
    assert res["admitted"]
    pr = res["cert"]["battery"]["pricing"]
    assert pr["searched_dl_canon"] < pr["searched_dl_raw"]      # profit < 0
    assert pr["net_with_rung_bits"] < 0.0
    assert pr["rung_model_bits"] == rr.rung_model_bits(SORT_EQ)


# =============================================================== the canon view
def test_canon_changes_reversed_reading_but_not_normal(rung_dir):
    _admit_and_save(_admitting_corpus())
    reversed_r = _reading("t2", [("=", R("y"), R("x"))])
    normal_r = _reading("t1", [("=", R("x"), R("y"))])
    cv = rr.canon(reversed_r)
    assert common.canonical_json(cv) != common.canonical_json(reversed_r)
    # already-normal ⇒ byte-identical (same object): normalizing a normal corpus
    # changes nothing.
    assert rr.canon(normal_r) is normal_r


def test_canon_leaves_store_bytes_untouched(rung_dir):
    """The VIEW never mutates its input (store/certs/authored bytes stay raw)."""
    _admit_and_save(_admitting_corpus())
    r = _reading("t2", [("=", R("y"), R("x"))])
    before = common.canonical_json(r)
    rr.canon(r)
    assert common.canonical_json(r) == before        # input unchanged


def test_joint_fixpoint_is_idempotent(rung_dir):
    """canon is a fixpoint: canon(canon(r)) == canon(r) (single-rung today; the
    joint-fixpoint loop halts on a no-change pass)."""
    _admit_and_save(_admitting_corpus())
    r = _reading("t2", [("=", R("y"), R("x")), ("=", R("z"), R("y"))])
    once = rr.canon(r)
    twice = rr.canon(once)
    assert common.canonical_json(twice) == common.canonical_json(once)


def test_tamper_refuses_to_lower(rung_dir):
    _admit_and_save(_admitting_corpus())
    reg = copy.deepcopy(rr.load_admitted())
    reg["sort_eq"]["row"]["rules"][0]["op"] = "and"      # edit after admission
    with pytest.raises(rr.RungExpansionError, match="mismatch"):
        rr.canon(_reading("t2", [("=", R("y"), R("x"))]), registry=reg)


# =============================================================== norm-cert producer
def test_norm_certs_only_for_changed_representable_statements(rung_dir):
    if not _dual_solver_available():
        pytest.skip("dual solver (z3+cvc5) unavailable for the equivalence channel")
    _admit_and_save(_admitting_corpus())
    reversed_r = _reading("t2", [("=", R("y"), R("x")), ("=", R("z"), R("y"))])
    out = rr.norm_certs_for_reading(reversed_r)
    assert len(out) == 2                     # both '=' statements changed
    for c in out:
        certs.validate_norm_cert(c)          # FI-W1-1 schema
        assert c.subject_hash                # subject = RAW statement hash
        claims = dict(c.claims)
        assert "canonical_form" in claims and "rung_pipeline" in claims
        result = {ch["backend"]: ch["result"] for ch in c.channels}
        assert result["solver_equivalence"] == certs.NORM_CERT_LOWERED_VERDICT
        assert result["meta_equivalence_class"] in certs.NORM_CERT_META_CLASSES
        assert result["instance_replay"] == "vacuous-by-symmetry"


def test_norm_cert_rung_pipeline_hash_is_stable_and_folds_order(rung_dir):
    _admit_and_save(_admitting_corpus())
    ordered = rr._ordered_rows(rr.load_admitted())
    h1 = rr.rung_pipeline_hash(ordered)
    h2 = rr.rung_pipeline_hash(ordered)
    assert h1 == h2                          # deterministic
    # a changed rule ⇒ a different pipeline hash (provenance/cache-key teeth).
    mutated = copy.deepcopy(ordered)
    mutated[0]["rules"][0]["op"] = "and"
    assert rr.rung_pipeline_hash(mutated) != h1
    # empty pipeline hashes the empty list (the rung-free identity).
    assert rr.rung_pipeline_hash([]) == common.sha256_json([])


def test_kernel_cache_key_reproduces_minted_norm_cert_contract_hash():
    """Dispatch wiring (§11.5 req 3): kernel._subject_and_cdesc's norm-cert branch
    is the SINGLE source of truth with make_norm_cert.  cache_key for a norm-cert
    contract descriptor reproduces the minted cert's contract_hash byte-for-byte
    (subject = raw statement hash), so producer and kernel can never drift."""
    import kernel
    cert = certs.make_norm_cert(
        statement_hash="raw-stmt", canonical_form_hash="cform",
        rung_pipeline_hash="rpipe", meta_equivalence_class="arg-perm")
    contract = {"type": "norm-cert", "statement_hash": "raw-stmt",
                "canonical_form_hash": "cform", "rung_pipeline_hash": "rpipe",
                "meta_equivalence_class": "arg-perm"}
    subject, cdesc = kernel._subject_and_cdesc({"files": {}}, contract)
    assert subject == "raw-stmt"                       # subject = RAW statement hash
    # the kernel's contract_hash == the minted cert's contract_hash (one cdesc).
    assert common.sha256_json(cdesc) == cert.contract_hash
    assert kernel.cache_key({"files": {}}, contract) \
        == f"v{certs.CERTS_VERSION}:raw-stmt:{cert.contract_hash}"
    # a changed canonicalizer (canonical_form) is a clean MISS, never a stale hit.
    contract2 = {**contract, "canonical_form_hash": "cform2"}
    assert kernel.cache_key({"files": {}}, contract2) \
        != kernel.cache_key({"files": {}}, contract)
    # still ABSENT from the channel-dispatch allowlist (direct-minted, not run).
    assert "norm-cert" not in kernel.IMPLEMENTED_CONTRACT_TYPES


def test_not_lowered_enum_only_stays_raw_and_mints_no_cert(rung_dir):
    """NOT-LOWERED discipline: an enum-only (coprime) hypothesis is skipped by the
    view and mints no norm-cert -- even with a live registry."""
    _admit_and_save(_admitting_corpus())
    enum_r = _reading("e", [])
    enum_r["statements"].append(
        {"id": "h", "force": "presupposition", "quote": "given",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "coprime", "args": [R("x"), R("y")]}}})
    assert common.canonical_json(rr.canon(enum_r)) == common.canonical_json(enum_r)
    assert rr.norm_certs_for_reading(enum_r) == []


# ================================================================= real corpus
def _real_governed_corpus():
    path = os.path.join(common.REPO_ROOT, "results", "formalize_bench_state.jsonl")
    out = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("arm") != "governed" or not rec.get("certified"):
                continue
            rj = rec.get("reading_json") or ""
            if not rj:
                continue
            doc = json.loads(rj)
            if isinstance(doc, dict) and isinstance(doc.get("statements"), list):
                out.append(doc)
    return out
