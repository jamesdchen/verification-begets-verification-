"""The RUNG registry, the canonicalization VIEW, and the rung admission gate
(WP-T6a-INTEGRATE; COMPRESSION.md §11.5 / §11.9 FI-W1-2).

This module is the integration seam that turns kernel/rung.py (the pure
meta-interpreter, WP-T6a-CORE) into an autonomous, adversarially-gated pipeline.
It mirrors, clause for clause, the OPERATOR registry pattern in
``generators/operator_growth.py`` (T4a): an append-only ``admitted.json`` with a
``proposed/`` staging area, a ``load_admitted``-style loader, per-row digest
verification with a tamper-refusal on every use, and a ``save_admitted`` that is
the SOLE ADMITTER BY CONSTRUCTION (it re-runs the deterministic admission and
refuses a forged / stale / non-re-admitting cert).

Three things live here:

1. THE REGISTRY.  A rung ROW is a validated rung-spec ``{rung, over, measure,
   rules}`` (kernel/rung.validate_rung).  Rows are proposed as data under
   ``proposed/``; only the battery (``admit_rung``) admits them into
   ``admitted.json``.  Empty / missing ``admitted.json`` ⇒ an empty registry ⇒
   ``canon`` is the identity (THE rung-free pin, FI-W1-2's concrete form).

2. ``canon(reading)`` -- THE VIEW (FI-W1-2).  A pure function applying the
   admitted rung PIPELINE to a COPY of each statement's ``pred``.  Composition
   (documented once, here, per §11.5): the admitted rungs are applied in
   ADMISSION ORDER; ``kernel.rung.lower`` runs each rung to its own fixpoint with
   root-restart; the FULL sequence is then iterated to a JOINT fixpoint (a pass
   that changes nothing halts it).  A global finitize-then-canonicalize order
   under one lexicographic measure ``(quantifier_count, disorder)`` is RESERVED
   for the statement-level exists-finitization rung (T6b); today the registry
   holds at most the single canonicalization rung, so the reserved comment marks
   the seam without exercising it.  NOT-LOWERED discipline (FI-W1-1 channel 2):
   an enum-only pred (gcd/coprime -- no sound SMT rendering) is SKIPPED, stays
   raw, and mints no cert.  Store, certs, goldens, authored bytes, prompts: raw,
   always -- ``canon`` is applied ONLY at the four FI-W1-2 call sites
   (``mdl_macros._reading_stats``, ``recurrence.mine``, ``recurrence.gc_macros``,
   the loop's FI-2 serve-price).

3. THE ADMISSION GATE (``admit_rung``) and the NORM-CERT PRODUCER
   (``norm_certs_for_reading``).  The gate's teeth are the §11.5 battery:
   per-RULE vacuity (every rule fires on >= 2 exogenous readings), the pinned
   counterfactual MDL gate (profit = searched-DL on the canon view - searched-DL
   on raw, rung model bits charged to the canon side, admit iff strictly
   negative net), and the anti-gaming tooth (a rung whose benefit raw mining
   ALREADY captures is refused).  Fail-closed: no corpus ⇒ refuse.

BYTE-IDENTITY.  With an empty / missing ``admitted.json`` -- or a reading that
carries no lowerable pred -- ``canon`` returns the input object UNCHANGED
(identity), so mining and pricing are byte-identical (the rung-free pin).
"""
from __future__ import annotations

import copy
import json
import os

import common
from kernel import rung as _rung
from kernel import certs as _certs

# ============================================================ canonical / cert
def canonical_row(row: dict) -> dict:
    """The canonical, key-ordered view of a rung ROW used for hashing.  A rung
    row IS its validated spec; only the four schema fields participate, so an
    incidental annotation never changes a row's identity."""
    return {
        "rung": row["rung"],
        "over": row["over"],
        "measure": row["measure"],
        "rules": row["rules"],
    }


def row_digest(row: dict) -> str:
    """sha256 over the canonical row (the tamper-detection substrate)."""
    return common.sha256_json(canonical_row(row))


def cert_id(row: dict, battery_digest: str) -> str:
    """The admission-certificate id: sha256 of the canonical row bound to the
    battery digest.  Recomputed on every use to detect row tampering."""
    return common.sha256_json(
        {"row": canonical_row(row), "battery_digest": battery_digest})


# --------------------------------------------------------- rung_pipeline_hash
def rule_digest(rule: dict) -> str:
    """sha256 over one canonical rule (its ordered, key-sorted JSON)."""
    return common.sha256_json(rule)


def rung_pipeline_hash(ordered_rows: list) -> str:
    """The FI-W1-2 pipeline identity: a deterministic hash of the admitted rung
    SEQUENCE.  Defined here (§11.5): sha256 over the ordered list of
    ``[rung_id, [rule_digest, ...]]`` pairs, in ADMISSION ORDER.  The ordered rung
    ids fix the composition order; each rung's ordered rule digests fix its
    content, so any change to a rule, a rung, or the order is a different hash --
    which is exactly what stamps statement provenance and the formalize-cache key
    (FI-W1-2).  An empty pipeline hashes the empty list (the rung-free identity)."""
    body = [[r["rung"], [rule_digest(rule) for rule in r["rules"]]]
            for r in ordered_rows]
    return common.sha256_json(body)


# ===================================================================== storage
def _default_rungs_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(here),
                        "specs", "mathsources", "rungs")


def rungs_dir(rungs_dir=None) -> str:
    if rungs_dir:
        return rungs_dir
    env = os.environ.get("CGB_RUNGS_DIR")
    return env if env else _default_rungs_dir()


def _admitted_path(rd: str) -> str:
    return os.path.join(rd, "admitted.json")


# mtime-keyed cache so the hot canon path re-reads admitted.json only when it
# actually changes; ``reload()`` drops it for tests that rewrite the file.
_CACHE: dict = {}


def reload() -> None:
    """Drop the admitted.json cache (test hook after rewriting the registry)."""
    _CACHE.clear()


def load_admitted(rung_dir=None) -> dict:
    """Return the admitted registry ``{rung_id: {"row":..., "cert":...}}``.  A
    missing / empty file is an empty registry (the identity / rung-free path)."""
    path = _admitted_path(rungs_dir(rung_dir))
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return {}
    cached = _CACHE.get(path)
    if cached is not None and cached[0] == mtime:
        return cached[1]
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        data = {}
    _CACHE[path] = (mtime, data)
    return data


def load_proposed(rung_dir=None) -> list:
    """Every proposed-but-unadmitted rung row under ``proposed/`` (a dream may
    PROPOSE rungs as data; only the battery admits them).  Returned in filename
    order for determinism."""
    d = os.path.join(rungs_dir(rung_dir), "proposed")
    out = []
    if not os.path.isdir(d):
        return out
    for name in sorted(os.listdir(d)):
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(d, name), "r", encoding="utf-8") as fh:
                out.append(json.load(fh))
        except (OSError, json.JSONDecodeError):
            continue
    return out


def _ordered_rows(registry: dict) -> list:
    """The admitted rung ROWS in ADMISSION ORDER (the ``seq`` the cert stamps at
    admission time; ties -- there are none by construction -- break on rung id)."""
    entries = [e for e in registry.values() if isinstance(e, dict) and "row" in e]
    entries.sort(key=lambda e: (e.get("cert", {}).get("seq", 0), e["row"]["rung"]))
    return [e["row"] for e in entries]


def _verify_entry(rung_id: str, entry: dict) -> None:
    """Recompute the row hash and confirm it matches the stored cert id; raise on
    tamper.  This is what makes a post-admission edit of a rule refuse to lower
    instead of silently changing meaning (the operator_growth._verify_entry
    pattern)."""
    row = entry.get("row")
    cert = entry.get("cert") or {}
    if not isinstance(row, dict) or "battery_digest" not in cert:
        raise RungExpansionError(
            f"rung {rung_id!r}: malformed admitted entry (no row/battery_digest)")
    expect = cert_id(row, cert["battery_digest"])
    if expect != cert.get("id"):
        raise RungExpansionError(
            f"rung {rung_id!r}: certificate id mismatch -- the admitted row was "
            f"tampered with after admission (recomputed {expect[:12]}..., stored "
            f"{str(cert.get('id'))[:12]}...); refusing to lower")
    if "row_digest" in cert and row_digest(row) != cert["row_digest"]:
        raise RungExpansionError(
            f"rung {rung_id!r}: row_digest does not match the stored row; "
            f"refusing to lower")


class RungGrowthError(Exception):
    """Base for rung-growth failures."""


class RungExpansionError(RungGrowthError):
    """Raised during the canon view: a tampered row (cert-id mismatch).  A bad
    row can never silently lower."""


class SaveRefused(RungGrowthError):
    """Raised by ``save_admitted`` when the append-only / sole-admitter
    invariants are violated: a forged/stale cert id, a row that does not
    re-admit, or an attempt to overwrite an existing rung with a different row
    digest.  A refusal is LOUD, never a silent last-writer-wins overwrite."""


# =================================================================== the VIEW
def _stmt_pred(stmt):
    """The pred of a hypothesis/conclusion statement, or None."""
    if not isinstance(stmt, dict):
        return None
    lf = stmt.get("lf")
    if isinstance(lf, dict) and lf.get("kind") in ("hypothesis", "conclusion") \
            and isinstance(lf.get("pred"), dict):
        return lf["pred"]
    return None


def _lower_pipeline(pred, ordered_rows):
    """Apply the admitted rung PIPELINE to ``pred`` to a JOINT fixpoint.

    Composition (§11.5, documented in the module header): each rung's
    ``kernel.rung.lower`` runs to its own fixpoint with root-restart; the full
    sequence is iterated -- a pass that changes NOTHING halts it -- so the result
    is a joint fixpoint over all admitted rungs in admission order.  Each
    ``lower`` strictly decreases its rung's well-founded measure, so the whole
    loop terminates (single-rung today; the reserved
    finitize-then-canonicalize global order for T6b would sit here)."""
    cur = pred
    while True:
        before = common.canonical_json(cur)
        for rw in ordered_rows:
            cur = _rung.lower(rw, cur)
        if common.canonical_json(cur) == before:
            return cur


def _is_representable(pred) -> bool:
    """The NOT-LOWERED gate (FI-W1-1 channel 2): a pred using an enum-only op
    (gcd/coprime) has NO sound SMT rendering, so the solver channel cannot
    corroborate raw == canon -- the statement is NOT lowered, stays raw, mints no
    cert.  Pure syntactic check (no solver run)."""
    from generators import math_smt as _smt
    try:
        return not _smt._pred_uses_enum(pred)
    except Exception:
        return False        # fail-closed: anything unclassifiable stays raw


def canon(reading, *, rung_dir=None, registry=None, verify=True):
    """The canonicalization VIEW (FI-W1-2).  Returns a reading whose lowerable
    preds are replaced by their admitted-rung-pipeline normal form, on a COPY.

    Returns the SAME object UNCHANGED when the registry is empty, the reading is
    not a plain ``{..., statements: [...]}`` dict, or no statement carries a
    lowerable, representable pred (byte-identity -- the rung-free pin).  Enum-only
    preds are skipped (not-lowered discipline).  Raises ``RungExpansionError`` on
    a tampered admitted row (when ``verify``)."""
    if registry is None:
        registry = load_admitted(rung_dir)
    if not registry or not isinstance(reading, dict):
        return reading
    stmts = reading.get("statements")
    if not isinstance(stmts, list):
        return reading
    if verify:
        for rid, entry in registry.items():
            _verify_entry(rid, entry)
    ordered = _ordered_rows(registry)
    if not ordered:
        return reading

    changed_any = False
    new_stmts = []
    for s in stmts:
        pred = _stmt_pred(s)
        if pred is None or not _is_representable(pred):
            new_stmts.append(s)
            continue
        lowered = _lower_pipeline(copy.deepcopy(pred), ordered)
        if common.canonical_json(lowered) == common.canonical_json(pred):
            new_stmts.append(s)                      # normal already: no change
            continue
        changed_any = True
        new_lf = dict(s["lf"])
        new_lf["pred"] = lowered
        new_s = dict(s)
        new_s["lf"] = new_lf
        new_stmts.append(new_s)
    if not changed_any:
        return reading                               # byte-identity preserved
    return {**reading, "statements": new_stmts}


def _canon_all(readings, *, rung_dir=None, registry=None):
    """Apply ``canon`` across a list of readings (the seam mining/GC use)."""
    if registry is None:
        registry = load_admitted(rung_dir)
    if not registry:
        return readings                              # identity (rung-free pin)
    return [canon(r, registry=registry) for r in readings]


# =============================================================== norm-cert producer
def _meta_class_for(raw_pred, canon_pred) -> str:
    """Which argued-safe syntactic class the raw->canon rewrite inhabits
    (FI-W1-1 channel 1).  A rewrite that removed nodes used same-op FLATTEN
    (``size`` fell); a pure reorder that kept every node is an ARG-PERM.  A
    rewrite that did both is tagged by its dominant, structure-changing class
    (``same-op-flatten``) -- the class whose safety argument subsumes the other's
    (flattening an associative op then sorting is still a member of the
    argued-safe class)."""
    if _rung._size(canon_pred) < _rung._size(raw_pred):
        return "same-op-flatten"
    return "arg-perm"


def _collect_objects(reading) -> tuple:
    """(objects, carrier): the free-object typing and ambient carrier a
    statement's pred is proved over, read from the reading's ``object`` /
    ``ambient`` statements.  Defaults to ``Int`` (the fragment's ambient) when a
    reading carries no ambient row."""
    objects, carrier = {}, "Int"
    for s in reading.get("statements", []):
        lf = s.get("lf") if isinstance(s, dict) else None
        if not isinstance(lf, dict):
            continue
        if lf.get("kind") == "ambient" and lf.get("carrier"):
            carrier = lf["carrier"]
        if lf.get("kind") == "object" and lf.get("name"):
            objects[lf["name"]] = lf.get("type", carrier)
    return objects, carrier


def _refs(node, out):
    if isinstance(node, dict):
        if set(node) == {"ref"}:
            out.add(node["ref"])
        for v in node.values():
            _refs(v, out)
    elif isinstance(node, list):
        for v in node:
            _refs(v, out)


def _solver_equivalence(raw_pred, canon_pred, objects, carrier) -> str:
    """The FI-W1-1 channel-2 dual-solver check that raw == canon over the
    fragment.  Renders ``(assert (not (= <raw> <canon>)))`` (a pred is a Bool, so
    ``=`` is iff) and requires BOTH z3 and cvc5 to return UNSAT (equivalent).
    Any unknown / timeout / all-absent ⇒ ``"unknown"`` (the NOT-LOWERED verdict --
    no cert).  Objects the solver has not been told about are declared from the
    refs actually used, typed at the ambient carrier."""
    from generators import math_smt as _smt
    from kernel.backends import SmtBackend
    used = set()
    _refs(raw_pred, used)
    _refs(canon_pred, used)
    objs = {r: objects.get(r, carrier) for r in used}
    lines = ["(set-logic QF_NIA)"]
    for name in sorted(objs):
        lines.append(f"(declare-const {name} Int)")
        if objs[name] == "Nat":
            lines.append(f"(assert (>= {name} 0))")
    try:
        rr = _smt.render_pred(raw_pred, objs, carrier)
        cc = _smt.render_pred(canon_pred, objs, carrier)
    except ValueError:
        return "enum-only"
    lines.append(f"(assert (not (= {rr} {cc})))")
    lines.append("(check-sat)")
    smt = "\n".join(lines) + "\n"
    be = SmtBackend()
    # expect='unsat': the negation is UNSAT ⟺ raw ⟺ canon is valid ⟺ equivalent.
    z = be.run_z3(smt, expect="unsat")
    if z.get("result") != "pass":
        return "unknown"
    try:
        c = be.run_cvc5(smt, expect="unsat")
    except ModuleNotFoundError:
        return "unknown"                             # no independent corroboration
    if c.get("result") != "pass":
        return "unknown"
    return _certs.NORM_CERT_LOWERED_VERDICT          # "equivalent"


def norm_certs_for_reading(reading, *, rung_dir=None, registry=None):
    """Mint a norm-cert for EACH statement whose lowering CHANGES the pred and
    whose raw==canon equivalence the dual solver confirms (FI-W1-1).

    Returns ``[Certificate, ...]`` (possibly empty).  The subject is the RAW
    statement hash (store/ledger/audit key on raw bytes); ``canonical_form`` is
    the canon-pred hash; ``rung_pipeline`` is ``rung_pipeline_hash`` of the
    admitted pipeline; the meta class comes from the rung's rules; the solver
    channel is the real dual check; instance replay is vacuous-by-symmetry for
    the permutation/flatten class.  NOT-LOWERED discipline: a statement the solver
    leaves ``unknown`` (or an enum-only pred) is SKIPPED -- the view keeps it raw
    and no cert is minted, so a norm-cert's very existence attests a confirmed
    lowering.  ``make_norm_cert``'s cdesc is the ONE source of truth (this
    producer never rebuilds a contract hash)."""
    if registry is None:
        registry = load_admitted(rung_dir)
    if not registry or not isinstance(reading, dict):
        return []
    ordered = _ordered_rows(registry)
    if not ordered:
        return []
    pipe_hash = rung_pipeline_hash(ordered)
    objects, carrier = _collect_objects(reading)
    out = []
    for s in reading.get("statements", []):
        pred = _stmt_pred(s)
        if pred is None or not _is_representable(pred):
            continue
        lowered = _lower_pipeline(copy.deepcopy(pred), ordered)
        if common.canonical_json(lowered) == common.canonical_json(pred):
            continue
        verdict = _solver_equivalence(pred, lowered, objects, carrier)
        if verdict != _certs.NORM_CERT_LOWERED_VERDICT:
            continue                                 # NOT lowered: no cert
        cert = _certs.make_norm_cert(
            statement_hash=common.sha256_json(s),
            canonical_form_hash=common.sha256_json(lowered),
            rung_pipeline_hash=pipe_hash,
            meta_equivalence_class=_meta_class_for(pred, lowered),
            solver_equivalence=verdict,
            instance_replay="vacuous-by-symmetry")
        out.append(cert)
    return out


# ============================================================ admission battery
def rung_model_bits(row: dict) -> float:
    """The rung's once-paid model cost, in the ``mdl_macros`` currency: the
    ``_leaf_count`` token proxy summed over the spec's rules (§11.5: "rung bits
    priced via ``_leaf_count`` over rules").  This is what the counterfactual MDL
    gate charges to the CANON side -- a rung must save more than it costs to
    store."""
    from buildloop import mdl_macros
    return float(sum(mdl_macros._leaf_count(rule) for rule in row["rules"]))


def _pred_subnodes(pred, out):
    """Every AST subnode (dicts with ``args`` and their descendants) at which a
    rule could fire."""
    if isinstance(pred, dict):
        out.append(pred)
        for v in pred.values():
            _pred_subnodes(v, out)
    elif isinstance(pred, list):
        for v in pred:
            _pred_subnodes(v, out)


def _rule_fires_in_reading(rule, reading) -> bool:
    """True iff ``rule`` produces a REAL rewrite (``_apply`` returns a node that
    differs) at some pred subnode of some statement in this reading.  A
    sort-children on already-sorted args returns ``None`` (a no-op), so "fires"
    means a genuine rewrite, never a vacuous match."""
    for s in reading.get("statements", []):
        pred = _stmt_pred(s)
        if pred is None:
            continue
        nodes = []
        _pred_subnodes(pred, nodes)
        for node in nodes:
            try:
                res = _rung._apply(rule, node)
            except Exception:
                res = None
            if res is not None and res != node:
                return True
    return False


def _per_rule_vacuity(row, corpus):
    """Battery tooth 1 (§11.5): every RULE must fire on >= 2 exogenous readings
    (the 2-witness discipline, per rule).  A rule that fires on fewer than two
    readings is dead vocabulary and refuses the whole rung.  Returns
    ``(ok, reason, witness_counts)``."""
    counts = {}
    for rule in row["rules"]:
        rid = rule["id"]
        n = sum(1 for r in corpus if _rule_fires_in_reading(rule, r))
        counts[rid] = n
    dead = sorted(rid for rid, n in counts.items() if n < 2)
    if dead:
        return (False,
                f"per-rule vacuity: {len(dead)} rule(s) fire on < 2 exogenous "
                f"readings (first: {dead[:3]}); every rule needs >= 2 witnesses "
                f"or it is dead vocabulary -- refused", counts)
    return (True, "", counts)


def _searched_dl(readings, initial_table):
    """The searched macro-admission DL of a corpus (S1.3 beam search to the best
    table), the counterfactual the MDL gate compares raw-vs-canon on.

    ``canon=False`` throughout: the gate has ALREADY materialized the canon side
    explicitly (``_mdl_counterfactual`` canonicalizes the corpus with the single
    CANDIDATE rung before calling this), so the searched sequence must NOT re-apply
    the AMBIENT admitted registry -- that would canonicalize BOTH the raw and the
    canon corpus and collapse profit to zero once ``admitted.json`` is non-empty
    (the re-admission path). Pricing the readings verbatim keeps the counterfactual
    isolated from whatever rungs are already live."""
    from buildloop import recurrence, mdl_macros
    table = recurrence.searched_macro_sequence(
        readings, dict(initial_table or {}), canon=False)
    return mdl_macros.corpus_dl(readings, table, canon=False)["total"], len(table)


def _mdl_counterfactual(row, corpus, initial_table):
    """Battery tooth 2 (§11.5): the pinned counterfactual MDL gate + the
    anti-gaming tooth.

    profit = [searched DL on the CANON view] - [searched DL on RAW], same initial
    table.  Rung model bits are charged to the canon side.  Admit iff the NET
    (canon_dl + rung_bits - raw_dl) is STRICTLY NEGATIVE -- the rung must save
    more DL than it costs to store.  Anti-gaming: if profit >= 0 the canon view
    does not even beat raw BEFORE the rung is charged, i.e. raw mining already
    captures whatever the rung would (a rung over what recurrence already finds),
    so it is refused with that reason named.  Returns ``(ok, reason, pricing)``."""
    ordered = [row]                                  # single candidate rung
    canon_corpus = [canon(r, registry={row["rung"]: {"row": row}}, verify=False)
                    for r in corpus]
    raw_dl, raw_macros = _searched_dl(corpus, initial_table)
    canon_dl, canon_macros = _searched_dl(canon_corpus, initial_table)
    bits = rung_model_bits(row)
    profit = canon_dl - raw_dl
    net = canon_dl + bits - raw_dl
    pricing = {
        "searched_dl_raw": round(raw_dl, 3),
        "searched_dl_canon": round(canon_dl, 3),
        "raw_macros": raw_macros, "canon_macros": canon_macros,
        "rung_model_bits": round(bits, 3),
        "profit_canon_minus_raw": round(profit, 3),
        "net_with_rung_bits": round(net, 3),
        "pricing_corpus_digest": common.sha256_json(
            [common.canonical_json(r) for r in corpus])[:16],
    }
    arith = (f"searched_dl raw={pricing['searched_dl_raw']} vs "
             f"canon={pricing['searched_dl_canon']}, rung_model_bits={bits}, "
             f"net={pricing['net_with_rung_bits']}")
    if profit >= 0:
        return (False,
                f"anti-gaming: the canon view does not lower searched DL below "
                f"raw ({arith}); raw mining already captures whatever this rung "
                f"would -- a rung over what recurrence already finds is refused",
                pricing)
    if net >= 0:
        return (False,
                f"no strict net DL drop: canonicalization saves "
                f"{round(-profit, 3)} bits but the rung's model costs {bits} "
                f"({arith}); the rung does not pay for itself -- refused",
                pricing)
    return (True, "", pricing)


def admit_rung(row: dict, *, rung_dir=None, registry=None, pricing_corpus=None,
               initial_table=None) -> dict:
    """Run the full rung-admission battery on a proposed row.

    Returns ``{"admitted": True, "cert": ..., "row": ...}`` on a green
    certificate, else ``{"admitted": False, "refusal": {"stage", "reason"},
    "pricing"?: ...}``.  Never writes anything -- persistence is the caller's
    explicit ``save_admitted`` step.

    Gate order (§11.5): schema validity (``validate_rung``), per-RULE vacuity
    (>= 2 exogenous witnesses each), then the counterfactual MDL gate WITH the
    anti-gaming tooth.  ``pricing_corpus`` (a list of reading docs) is REQUIRED;
    without it admission refuses FAIL-CLOSED (the T4a pattern)."""
    if registry is None:
        registry = load_admitted(rung_dir)

    # schema validity (kernel/rung is the source of truth).
    try:
        _rung.validate_rung(row)
    except (_rung.SpecError, _rung.FragmentMiss) as ex:
        return {"admitted": False,
                "refusal": {"stage": "schema", "reason": str(ex)}}

    # fail-closed: no corpus ⇒ refuse (T4a).
    corpus = [r for r in (pricing_corpus or [])
              if isinstance(r, dict) and isinstance(r.get("statements"), list)]
    if not corpus:
        return {"admitted": False, "refusal": {
            "stage": "pricing",
            "reason": ("no pricing corpus: rung admission charges the rung's "
                       "model bits against a corpus-wide canonicalization saving, "
                       "so a pricing corpus (list of readings) is required -- "
                       "refusing fail-closed")}}

    ok, reason, witnesses = _per_rule_vacuity(row, corpus)
    if not ok:
        return {"admitted": False,
                "refusal": {"stage": "vacuity", "reason": reason},
                "witnesses": witnesses}

    ok, reason, pricing = _mdl_counterfactual(row, corpus, initial_table)
    if not ok:
        return {"admitted": False,
                "refusal": {"stage": "pricing", "reason": reason},
                "pricing": pricing}

    battery = {
        "per_rule_witnesses": witnesses,
        "pricing": pricing,
        "n_readings": len(corpus),
    }
    battery_digest = common.sha256_json(battery)
    seq = len([e for e in registry.values()
               if isinstance(e, dict) and "row" in e])
    cert = {
        "kind": "rung-admission",
        "id": cert_id(row, battery_digest),
        "rung": row["rung"],
        "seq": seq,
        "row_digest": row_digest(row),
        "battery_digest": battery_digest,
        "battery": battery,
    }
    return {"admitted": True, "row": canonical_row(row), "cert": cert}


def save_admitted(entry: dict, rung_dir=None, *, pricing_corpus=None,
                  initial_table=None) -> str:
    """Merge one ``{rung_id: {"row", "cert"}}`` admission into admitted.json and
    return the path written.

    SOLE ADMITTER BY CONSTRUCTION (T4a): rather than trust its caller,
    ``save_admitted`` RE-RUNS ``admit_rung`` on the row (admission is
    deterministic) and refuses unless the recomputed cert id equals the one handed
    in -- a forged or stale cert can never be persisted.  Re-admission uses the
    same ``pricing_corpus`` the caller admitted with; without it it refuses
    fail-closed.

    APPEND-ONLY: refuses to overwrite an existing rung with a DIFFERENT row digest
    (a same-digest re-save is idempotent), so an autonomous grower can never
    rewrite the meaning of an already-certified pipeline.  Raises ``SaveRefused``
    on any invariant violation."""
    if not (isinstance(entry, dict) and len(entry) == 1):
        raise SaveRefused(
            "save_admitted takes exactly one {rung_id: {'row','cert'}} entry")
    (rid, payload), = entry.items()
    if not isinstance(payload, dict) or not isinstance(payload.get("row"), dict):
        raise SaveRefused(f"rung {rid!r}: entry has no row")
    row = payload["row"]
    handed_cert = payload.get("cert") or {}
    if row.get("rung") != rid:
        raise SaveRefused(
            f"rung {rid!r}: entry key does not match row id {row.get('rung')!r}")

    # sole-admitter: re-run the deterministic admission against the registry as it
    # stands (minus any same-named prior admission) and require cert-id equality.
    registry = {w: e for w, e in load_admitted(rung_dir).items() if w != rid}
    res = admit_rung(row, rung_dir=rung_dir, registry=registry,
                     pricing_corpus=pricing_corpus, initial_table=initial_table)
    if not res.get("admitted"):
        ref = res.get("refusal", {})
        raise SaveRefused(
            f"rung {rid!r}: re-admission refused at {ref.get('stage')!r} -- "
            f"{ref.get('reason')}; save_admitted is the sole admitter, so a row "
            f"that does not re-admit is never persisted")
    recomputed = res["cert"]["id"]
    if recomputed != handed_cert.get("id"):
        raise SaveRefused(
            f"rung {rid!r}: cert id mismatch on re-admission (recomputed "
            f"{recomputed[:12]}..., handed {str(handed_cert.get('id'))[:12]}...); "
            f"refusing a forged or stale certificate")

    rd = rungs_dir(rung_dir)
    path = _admitted_path(rd)
    current = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                current = json.load(fh)
        except (OSError, json.JSONDecodeError):
            current = {}
    if not isinstance(current, dict):
        current = {}

    if rid in current and isinstance(current[rid], dict):
        existing_row = current[rid].get("row")
        if (isinstance(existing_row, dict)
                and row_digest(existing_row) != row_digest(row)):
            raise SaveRefused(
                f"rung {rid!r}: append-only registry -- a different row is "
                f"already admitted under this id (existing digest "
                f"{row_digest(existing_row)[:12]}..., new {row_digest(row)[:12]}"
                f"...); refusing to overwrite a certified pipeline without "
                f"re-certification")

    os.makedirs(rd, exist_ok=True)
    current[rid] = {"row": res["row"], "cert": res["cert"]}
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(common.canonical_json(current))
        fh.write("\n")
    reload()
    return path
