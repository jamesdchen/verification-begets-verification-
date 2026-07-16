#!/usr/bin/env python3
"""WP-T4b: the autonomous proposal EMITTER (the miner half of auto-R2).

This tool MINES recurring `pred` subtrees from a corpus of certified exogenous
readings and mechanically LIFTS each into a proposed operator ROW, which it
STAGES as inert data under ``specs/mathsources/operators/proposed/``.  It is the
producer half of the T4 loop; the R2 battery + pricing gate
(``generators/operator_growth.admit_operator``) is the SOLE admitter and the
honest judge.  **This module never imports or calls ``admit_operator`` /
``save_admitted``** -- data flows ONE WAY into staging, never into the live
registry.  ``proposed/`` is verified-inert at load (nothing in the live parse /
expand path reads it), so emission cannot change any certified byte.

WHY ``tools/`` (not ``buildloop/``).  This is an OFFLINE staging generator that
REUSES ``tools/tower_census.py``'s census logic read-only and sits beside it.
``buildloop/`` is the LIVE governor path (recurrence, mdl_macros, the parse hook);
putting a proposal emitter there would couple staging to the hot path.  Keeping
it in ``tools/`` keeps the one-way data flow structural: an offline miner that
writes dead files.

MATCHING -- alpha-canonical (sharing-preserving) ref abstraction.  The census's
middle level (``tower_census._abstract`` level 1) maps EVERY ref to ``{"ref":
"*"}``, which DISCARDS variable identity: ``=(mod(a,m),mod(b,m))`` (shared
modulus) groups with ``=(mod(a,m),mod(b,n))`` (independent moduli).  That is the
right granularity for a recurrence CENSUS but the WRONG one for a self-contained
LIFT: a subtree's free variable that recurs must become ONE parameter, not two.
So the miner refines the census's ref-abstraction to preserve sharing -- refs are
renamed to canonical positional variables ``v0, v1, ...`` by first appearance,
reusing a variable for a repeated ref.  Consequence, and the headline tooth: the
mod-congruence subtree lifts to ``=(mod(v0,v1),mod(v2,v1))`` -- a 3-param
definition whose SHARED modulus ``v1`` is exactly congruence, at 4 witnesses on
the committed corpus (fully-abstracted census level 1 over-merges it to 5).

SELF-CONTAINMENT (COMPRESSION.md §11.4).  Every free variable of a lifted subtree
becomes a parameter (there are no other free names in an F-G ``pred`` subtree --
its only leaves are ``{ref}`` and ``{lit}``).  A subtree is refused if it would
capture structure beyond plain refs (any leaf that is not ``{ref}``/``{lit}``, or
any non-``{op,args}`` interior).  Subtrees never span statement boundaries: they
are drawn from a single statement's ``pred``.  NO GUARD-IMPORTING: a subtree
whose in-corpus soundness leans on a sibling hypothesis (e.g. the corpus's
``0 < m`` modulus guard) is lifted AS-IS, guardless -- the downstream battery is
the judge, and its refusal (mod-by-zero mirror gap) is the honest outcome, not
this miner's business.

ALIAS POLICY -- emit-with-flag.  A single-kernel-atom subtree (one kernel op over
bare leaves, e.g. ``dvd(v0,v1)``) is a trivial alias -- §11.4 Critical 1's
``divides_alias`` flood.  This miner EMITS such rows but stamps
``provenance.alias_shaped = true``.  Rationale: NOT emitting them would hide the
flood the census exists to make a committed number; emitting-with-flag documents
it on the record and lets the downstream pricing gate refuse them visibly.  At
this scale the flood is benign (§11.4: <=21 proposals).

DETERMINISM.  Same corpus -> byte-identical proposal files.  No timestamps, no
randomness; witnesses are stable ``source_id``s, sorted; rows serialize through
``common.canonical_json``.  The word is a content hash of the definition
(mirroring ``buildloop.recurrence._macro_name``: ``op_`` + sha256[:12]).

Usage:
    tools/subtree_mine.py            # mine the committed corpus, emit into
                                     # specs/mathsources/operators/proposed/
    tools/subtree_mine.py --print    # also echo a summary; --dry-run: no writes
"""
from __future__ import annotations

import argparse
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import common                                      # noqa: E402
import tools.tower_census as census                # noqa: E402 (read-only reuse)

# Content-derived word prefix, mirroring recurrence._macro_name's `m_` + hash.
WORD_PREFIX = "op_"
WORD_HASH_LEN = 12
# Bumped whenever the lift semantics (matching level, param rule, provenance
# shape) change; joins each row's provenance so a re-mine under new semantics is
# distinguishable.  No timestamp -- this is the only version signal.
MINER_VERSION = "subtree_mine/1"
MIN_WITNESSES = 2

# Reused read-only from the census (single-sourced there): the kernel op
# vocabulary, the op-subtree walk, and the trivial-alias predicate.
KERNEL_OPS = census.KERNEL_OPS
_op_subtrees = census._op_subtrees
_is_single_kernel_atom_alias = census._is_single_kernel_atom_alias


# =============================================================== corpus loading
def load_corpus(checkpoint=census.CHECKPOINT):
    """The committed corpus for the emitter: the CERTIFIED EXOGENOUS readings of
    the governed arm, reconstructed exactly as ``tower_census`` does (replay the
    checkpoint's waves through today's miner).  Dream (system-origin) readings
    are exogenous-excluded by construction -- they never join the governed arm's
    corpus -- so this is exogenous-only.  Each returned reading carries ``_sid``
    (stable source id) and ``statements``."""
    records = census._load_records(checkpoint)
    dreams = census._dream_readings(records)
    _, gexo, _ = census._replay_arm(records, "governed", True, dreams)
    return [r for r in gexo if r.get("_certified")]


# =========================================================== alpha-canonical lift
def _alpha_canonical(node, mapping, counter):
    """Rename refs to canonical positional variables ``v0, v1, ...`` by first
    appearance, REUSING a variable for a repeated ref (sharing preserved); lits
    and ops stay concrete.  ``mapping`` (orig-ref -> vN) and ``counter`` (a
    one-element list) thread the state so identity is stable across the whole
    subtree."""
    if isinstance(node, dict):
        if set(node) == {"ref"}:
            r = node["ref"]
            if r not in mapping:
                mapping[r] = "v%d" % counter[0]
                counter[0] += 1
            return {"ref": mapping[r]}
        return {k: _alpha_canonical(v, mapping, counter)
                for k, v in sorted(node.items())}
    if isinstance(node, list):
        return [_alpha_canonical(x, mapping, counter) for x in node]
    return node


def _self_contained(node):
    """(ok, reason): a subtree is self-contained iff every leaf is a plain
    ``{ref}`` or ``{lit}`` and every interior is ``{op, args}`` -- so its only
    free names are refs, each of which becomes a parameter.  This is where a
    lift that would capture structure beyond plain refs (a bound-variable node, a
    non-op interior) is REFUSED (§11.4).  On the F-G ``pred`` fragment every
    op-subtree already satisfies this; the guard makes the contract explicit and
    testable, and is the seam a richer AST would trip."""
    if isinstance(node, dict):
        if set(node) == {"ref"}:
            if not isinstance(node["ref"], str):
                return False, f"non-string ref leaf: {node!r}"
            return True, ""
        if set(node) == {"lit"}:
            return True, ""
        if "op" in node and set(node) <= {"op", "args"}:
            for a in node.get("args", []):
                ok, reason = _self_contained(a)
                if not ok:
                    return False, reason
            return True, ""
        return False, (f"non-self-contained node (not a plain ref/lit leaf nor "
                       f"an {{op,args}} interior): {sorted(node)}")
    if isinstance(node, list):
        for a in node:
            ok, reason = _self_contained(a)
            if not ok:
                return False, reason
        return True, ""
    return False, f"non-object node in subtree: {node!r}"


def canonical_subtree(subtree):
    """(definition, params): the alpha-canonical lift of a pred subtree -- refs
    renamed to shared-preserving ``vN``, params the sorted distinct vars."""
    mapping, counter = {}, [0]
    definition = _alpha_canonical(subtree, mapping, counter)
    params = sorted(mapping.values())
    return definition, params


def _word_for(definition):
    """Deterministic content-derived word: ``op_`` + sha256(definition)[:12].
    Mirrors recurrence._macro_name's pattern; a valid lowercase identifier that
    never shadows a kernel op."""
    return WORD_PREFIX + common.sha256_json(definition)[:WORD_HASH_LEN]


# ==================================================================== the miner
def _object_carriers(reading):
    return {s["lf"]["name"]: s["lf"].get("type")
            for s in reading.get("statements", [])
            if isinstance(s.get("lf"), dict) and s["lf"].get("kind") == "object"}


def mine_subtrees(readings, *, min_witnesses=MIN_WITNESSES):
    """Mine recurring self-contained pred subtrees from ``readings`` (each a doc
    with ``_sid`` + ``statements``).  Groups occurrences by their alpha-canonical
    (sharing-preserving) form; a candidate needs ``>= min_witnesses`` DISTINCT
    readings.  Returns a deterministically-ordered list of candidate dicts::

        {"definition", "params", "arity", "witnesses" (int),
         "witness_sids" (sorted), "alias_shaped" (bool),
         "carriers_observed" (sorted list)}

    Refused (non-self-contained) subtrees are silently skipped -- they never
    reach staging."""
    from collections import defaultdict
    wit = defaultdict(set)
    lifted = {}                                    # key -> (definition, params)
    alias = {}
    carriers = defaultdict(set)
    for r in readings:
        sid = r.get("_sid")
        objs = _object_carriers(r)
        for s in r.get("statements", []):
            lf = s.get("lf") if isinstance(s, dict) else None
            pred = lf.get("pred") if isinstance(lf, dict) else None
            if pred is None:
                continue
            for st in _op_subtrees(pred):
                ok, _ = _self_contained(st)
                if not ok:
                    continue                       # refuse: capture guard
                definition, params = canonical_subtree(st)
                key = common.canonical_json(definition)
                wit[key].add(sid)
                lifted[key] = (definition, params)
                alias[key] = _is_single_kernel_atom_alias(st)
                # the canonical params map back to the occurrence's refs in
                # first-appearance order (the mapping _alpha_canonical builds).
                occ_refs = _first_appearance_refs(st)
                for ref in occ_refs:
                    if ref in objs and objs[ref] is not None:
                        carriers[key].add(objs[ref])

    cands = []
    for key, sids in wit.items():
        if len(sids) < min_witnesses:
            continue
        definition, params = lifted[key]
        cands.append({
            "definition": definition,
            "params": params,
            "arity": len(params),
            "witnesses": len(sids),
            "witness_sids": sorted(sids),
            "alias_shaped": bool(alias[key]),
            "carriers_observed": sorted(carriers[key]),
        })
    # stable: most-witnessed first, non-alias before alias, then canonical bytes.
    cands.sort(key=lambda c: (-c["witnesses"], c["alias_shaped"],
                              common.canonical_json(c["definition"])))
    return cands


def _first_appearance_refs(node):
    """The distinct refs of a subtree in first-appearance (pre-order) order --
    the same order ``_alpha_canonical`` assigns ``v0, v1, ...``."""
    seen = []
    def walk(n):
        if isinstance(n, dict):
            if set(n) == {"ref"} and isinstance(n["ref"], str):
                if n["ref"] not in seen:
                    seen.append(n["ref"])
            else:
                for v in n.values():
                    walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)
    walk(node)
    return seen


# ===================================================================== the lift
def candidate_to_row(cand):
    """Mechanically lift a mined candidate to a proposal ROW matching the schema
    ``admit_operator`` / ``load_proposed`` expect (``word``, ``arity``,
    ``params``, ``definition`` -- the only fields ``canonical_row`` hashes), plus
    an inert ``provenance`` block (ignored by admission, ignored by the live
    path).  ``provenance`` carries the witness source ids + count, the miner
    version, the alias flag, the match level, and any derivable carrier metadata.

    Purely a function of the candidate -- no clock, no randomness -- so the row
    is byte-stable for a fixed corpus."""
    word = _word_for(cand["definition"])
    return {
        "word": word,
        "arity": cand["arity"],
        "params": list(cand["params"]),
        "definition": cand["definition"],
        "provenance": {
            "miner": MINER_VERSION,
            "match_level": "alpha-canonical (sharing-preserving ref abstraction)",
            "witness_count": cand["witnesses"],
            "witness_source_ids": list(cand["witness_sids"]),
            "alias_shaped": cand["alias_shaped"],
            # carrier is NOT derivable to a single sort -- operators are
            # carrier-polymorphic in the fragment (checked over both); we record
            # the carriers OBSERVED among the witnesses' referenced objects.
            "carrier": None,
            "carriers_observed": list(cand["carriers_observed"]),
        },
    }


def serialize_row(row):
    """Byte-stable serialization for a staged proposal file."""
    return common.canonical_json(row) + "\n"


# =================================================================== emission
def _proposed_dir(op_dir=None):
    base = op_dir or os.path.join(_ROOT, "specs", "mathsources", "operators")
    return os.path.join(base, "proposed")


def emit_proposals(readings, *, op_dir=None, min_witnesses=MIN_WITNESSES,
                   dry_run=False):
    """Mine ``readings`` and STAGE one ``<word>.json`` file per proposal under
    ``proposed/`` (following the committed ``multiple_of.json`` naming
    convention).  Staging only: writes inert data, touches nothing in the live
    path, and imports no admission code.  Returns the list of
    ``{"word", "path", "row"}`` staged, in the miner's deterministic order."""
    pdir = _proposed_dir(op_dir)
    if not dry_run:
        os.makedirs(pdir, exist_ok=True)
    out = []
    for cand in mine_subtrees(readings, min_witnesses=min_witnesses):
        row = candidate_to_row(cand)
        path = os.path.join(pdir, row["word"] + ".json")
        if not dry_run:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(serialize_row(row))
        out.append({"word": row["word"], "path": path, "row": row})
    return out


# ======================================================================== main
def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--print", action="store_true", dest="show",
                    help="echo a summary of the emitted proposals")
    ap.add_argument("--dry-run", action="store_true",
                    help="mine and report but write no files")
    args = ap.parse_args(argv)

    readings = load_corpus()
    staged = emit_proposals(readings, dry_run=args.dry_run)

    n_alias = sum(1 for s in staged if s["row"]["provenance"]["alias_shaped"])
    print(f"subtree_mine: corpus={len(readings)} certified exogenous readings | "
          f"emitted {len(staged)} proposals "
          f"({len(staged) - n_alias} non-alias, {n_alias} alias-shaped)"
          f"{' [dry-run]' if args.dry_run else ''}")
    if args.show:
        for s in staged:
            p = s["row"]["provenance"]
            tag = "ALIAS" if p["alias_shaped"] else "     "
            print(f"  {tag} {s['word']}  {p['witness_count']}w  "
                  f"params={s['row']['params']}  "
                  f"{common.canonical_json(s['row']['definition'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
