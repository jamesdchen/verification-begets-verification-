#!/usr/bin/env python3
"""Frontier-driven census-sourced intake SCAFFOLDING (WS-C).

Mechanizes the C2/C3 census-sourced intake mechanics (worked example: commit
355ca62; siblings wp_c2_readings.py / wp_c3_readings.py / wp_c4_readings.py and
manifest/registration entries for sources 67-78) so a corpus-growth driver
session does the *judgement* (author readings, certify, re-baseline the
registration DL) and the tool does the deterministic *bookkeeping* (pick the
next candidates, allocate collision-free source numbers, lay down the verbatim
source files, and emit the manifest / registration / readings SKELETONS the
driver fills in).

Two selection modes:

  --ready --take N        first N ``ready`` entries in frontier order.
  --unblocked SIGNAL --take N
                          first N nodes of the named ``blocked`` group (the
                          cycle after a purchase lands and un-gates that
                          signal; the frontier still lists them as blocked
                          because it has not been regenerated yet).

``--dry-run`` is the DEFAULT and prints the full plan deterministically (two
runs with the same arguments are byte-identical).  ``--apply`` additionally
writes the NEW files -- the ``specs/mathsources/NN_slug.txt`` sources and a
``wp_cK_readings.py`` provenance-module skeleton.  It NEVER edits an existing
committed file (manifest.json / registration.json / an existing source / an
existing readings module): those edits carry numbers only the driver's
certify+regen cycle produces, so the tool merely EMITS the blocks to paste.

Everything is read LIVE from committed artifacts (registration.json for the
source total -- never a frozen constant like promote_sources.py's stale
FROZEN_EXPECTED_TOTAL), offline, deterministic, LLM-free.

HONESTY.  Intake makes NO certification claim -- it moves *signals*, never
verdicts.  A source selected here that later fails to certify is recorded by
the driver as a first-class REFUSAL (demand data), never silently dropped or
retried wider.  The census reports signals; this tool only acts on them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

# --------------------------------------------------------------------------- #
# paths (all derived from --root so the tool is testable against a tmp mirror)
# --------------------------------------------------------------------------- #

_DEFAULT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _paths(root):
    ms = os.path.join(root, "specs", "mathsources")
    return {
        "root": root,
        "mathsources": ms,
        "manifest": os.path.join(ms, "manifest.json"),
        "registration": os.path.join(ms, "registration.json"),
        "frontier_default": os.path.join(root, "results", "frontier.json"),
    }


# --------------------------------------------------------------------------- #
# live state readers
# --------------------------------------------------------------------------- #

def _sha_stripped(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def _existing_sources(ms_dir: str):
    """(prefixes, intaken_hashes) over top-level ``*.txt`` -- read live.

    ``intaken`` keys on sha256(stripped text) per the frontier contract, NEVER
    on labels or numeric prefixes (prefixes already collide: two 67_* files).
    """
    prefixes = set()
    intaken = set()
    names = set()
    if not os.path.isdir(ms_dir):
        return prefixes, intaken, names
    for name in sorted(os.listdir(ms_dir)):
        if not name.endswith(".txt"):
            continue
        p = os.path.join(ms_dir, name)
        if not os.path.isfile(p):
            continue
        names.add(name)
        m = re.match(r"^(\d+)_", name)
        if m:
            prefixes.add(int(m.group(1)))
        with open(p, encoding="utf-8") as fh:
            intaken.add(_sha_stripped(fh.read()))
    return prefixes, intaken, names


def _expected_total(reg_path: str) -> int:
    """Live source total from the corpus-era registration (never hardcoded)."""
    with open(reg_path, encoding="utf-8") as fh:
        reg = json.load(fh)
    return int(reg["n_top_level_sources"])


def _corpus_index(ms_dir: str, corpus: str):
    """(node_id -> stripped prose) for one corpus' committed nodes.jsonl."""
    path = os.path.join(ms_dir, corpus, "nodes.jsonl")
    if not os.path.isfile(path):
        raise SystemExit(f"error: corpus nodes.jsonl not found: {path}")
    idx = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            idx[d["label"]] = d["prose"].strip()
    return idx


def _next_readings_index(root: str) -> int:
    hi = 1
    for name in sorted(os.listdir(root)):
        m = re.match(r"^wp_c(\d+)_readings\.py$", name)
        if m:
            hi = max(hi, int(m.group(1)))
    return hi + 1


# --------------------------------------------------------------------------- #
# slug / name allocation
# --------------------------------------------------------------------------- #

def _slug_from_suggested(suggested: str) -> str:
    """"NN_slug" -> "slug" (drop a leading numeric prefix if present)."""
    m = re.match(r"^\d+_(.+)$", suggested)
    return m.group(1) if m else suggested


def _slug_from_node_id(node_id: str) -> str:
    """Deterministic slug for a blocked node (no suggested_source_name).

    Slugify the label, dropping any leading chapter-number component so the
    result is a clean stem the driver can rename before commit.
    """
    s = re.sub(r"^\d+_", "", node_id)
    s = re.sub(r"[^0-9a-zA-Z]+", "_", s).strip("_").lower()
    return s or "source"


# --------------------------------------------------------------------------- #
# selection
# --------------------------------------------------------------------------- #

def _select(frontier: dict, mode: str, signal, take: int, intaken: set):
    """Return the ordered list of candidate dicts (pre-allocation).

    Each candidate: {corpus, node_id, text_sha256, slug}.  Already-intaken
    nodes are dropped with a NOTE (defensive: ready should already exclude
    them) BEFORE taking N.  Selection order is the frontier's own order.
    """
    notes = []
    if mode == "ready":
        raw = list(frontier.get("ready", []))
        cands = [
            {"corpus": e["corpus"], "node_id": e["node_id"],
             "text_sha256": e["text_sha256"],
             "slug": _slug_from_suggested(e["suggested_source_name"])}
            for e in raw
        ]
    else:  # unblocked
        groups = {g["signal"]: g for g in frontier.get("blocked", [])}
        if signal not in groups:
            avail = ", ".join(sorted(groups)) or "(none)"
            raise SystemExit(
                f"error: no blocked group for signal {signal!r}; "
                f"available: {avail}")
        nodes = sorted(groups[signal]["nodes"],
                       key=lambda n: (n["corpus"], n["node_id"]))
        cands = [
            {"corpus": n["corpus"], "node_id": n["node_id"],
             "text_sha256": n["text_sha256"],
             "slug": _slug_from_node_id(n["node_id"])}
            for n in nodes
        ]

    kept = []
    for c in cands:
        if c["text_sha256"] in intaken:
            notes.append(
                f"NOTE: skipping already-intaken node {c['corpus']}/"
                f"{c['node_id']} (sha {c['text_sha256'][:16]})")
            continue
        kept.append(c)
    return kept[:take], notes


def _allocate(cands, existing_prefixes, existing_names):
    """Assign a fresh, collision-free numeric prefix to each candidate.

    Prefixes start above the current max (they already collide historically,
    so we never *reuse* -- only extend) and skip any in-use prefix defensively.
    Never targets an existing filename.
    """
    used = set(existing_prefixes)
    nxt = (max(existing_prefixes) + 1) if existing_prefixes else 1
    plan = []
    for c in cands:
        while nxt in used:
            nxt += 1
        prefix = nxt
        used.add(prefix)
        nxt += 1
        fname = f"{prefix:02d}_{c['slug']}.txt"
        if fname in existing_names:
            raise SystemExit(
                f"error: allocated filename already exists: {fname} "
                "(refusing to overwrite an existing top-level source)")
        plan.append({**c, "prefix": prefix, "file": fname,
                     "stem": fname[:-4]})
    return plan


# --------------------------------------------------------------------------- #
# emitted skeletons
# --------------------------------------------------------------------------- #

def _manifest_entry(stem: str) -> dict:
    # Fixed key order matches the committed manifest entry shape exactly.
    return {"file": f"{stem}.txt", "axes": ["plain"], "expect_transcribes": True}


def _lineage_skeleton(new_total: int, n_new: int, corpora):
    corpora_str = ", ".join(sorted(set(corpora)))
    return {
        "era": (f"<DRIVER FILLS: census-sourced growth (+{n_new}); "
                f"corpus {corpora_str}>"),
        "n_top_level_sources": new_total,
        "governed_legacy_dl": "<DRIVER FILLS after certify+regen_downstream>",
        "note": ("SKELETON emitted by tools/intake_from_frontier.py; the "
                 "driver authors the prose and reproduces governed_legacy_dl "
                 "LIVE from results/formalize_governed.csv -- this tool never "
                 "asserts a DL it did not recompute."),
    }


_READINGS_HELPERS = '''\
def _amb(carrier):
    return {"id": "amb", "force": "choice", "quote": "",
            "lf": {"kind": "ambient", "carrier": carrier}}


def _obj(i, name, quote, typ):
    return {"id": i, "force": "presupposition", "quote": quote,
            "lf": {"kind": "object", "name": name, "type": typ}}


def _q(sid, objects, quote):
    return {"id": sid, "force": "demand", "quote": quote,
            "lf": {"kind": "quantifier", "binder": "forall",
                   "objects": objects}}


def _hyp(i, pred, quote, force="demand"):
    return {"id": i, "force": force, "quote": quote,
            "lf": {"kind": "hypothesis", "pred": pred}}


def _con(pred, quote):
    return {"id": "c", "force": "demand", "quote": quote,
            "lf": {"kind": "conclusion", "pred": pred}}


def r(name):
    return {"ref": name}


def lit(n):
    return {"lit": n}


def op(o, *args):
    return {"op": o, "args": list(args)}


READINGS = {}
'''


def _readings_module(index: int, plan) -> str:
    prov_lines = []
    for e in plan:
        prov_lines.append(f"    {e['stem']:<28} <- {e['corpus']} {e['node_id']}")
    prov = "\n".join(prov_lines)
    prov_dict = "PROVENANCE = {\n" + "".join(
        f"    {e['stem']!r}: {{\n"
        f"        \"corpus\": {e['corpus']!r},\n"
        f"        \"node_id\": {e['node_id']!r},\n"
        f"        \"text_sha256\": {e['text_sha256']!r},\n"
        f"    }},\n"
        for e in plan
    ) + "}\n"
    todo = "\n".join(
        f"# READINGS[{e['stem']!r}] = {{\"theorem\": \"...\", \"statements\": [\n"
        f"#     _amb(\"Int\"),\n"
        f"#     ...  # DRIVER AUTHORS: quotes are LITERAL source substrings;\n"
        f"#          # gate-check + box-verify TRUE before authoring; never\n"
        f"#          # distort a reading to force a green.\n"
        f"# ]}}\n"
        for e in plan
    )
    return (
        f'"""C{index} (PLAN_FRAGMENT §3.1 cadence): session-inline '
        f"MathReadings for the\n"
        f"census-sourced corpus additions below -- SKELETON emitted by\n"
        f"tools/intake_from_frontier.py.  Sibling of wp_c2/c3/c4_readings.py;\n"
        f"same discipline, next batch.\n"
        f"\n"
        f"PROVENANCE.  Each source's text is the VERBATIM prose of a census\n"
        f"attempt-candidate node (NOT a sentence a maintainer authored):\n"
        f"\n"
        f"{prov}\n"
        f"\n"
        f"The READINGS themselves are LEFT UNAUTHORED on purpose: intake is\n"
        f"mechanical and makes NO certification claim.  The driver session\n"
        f"authors one reading per source here (UNMETERED; reused identically\n"
        f"by both arms), gate-checks it, box-verifies TRUE, and certifies via\n"
        f"the inline-author checkpoint resume.  A source that then fails to\n"
        f"certify is recorded as a first-class REFUSAL, never dropped.\n"
        f'"""\n'
        f"\n"
        f"\n"
        f"{prov_dict}\n"
        f"\n"
        f"{_READINGS_HELPERS}"
        f"\n"
        f"# --- DRIVER AUTHORS BELOW (one reading per source) ------------------\n"
        f"{todo}"
    )


# --------------------------------------------------------------------------- #
# plan rendering (deterministic)
# --------------------------------------------------------------------------- #

def _render_plan(frontier, mode, signal, take, plan, notes, paths,
                 expected_total, readings_index, apply):
    out = []
    w = out.append
    w("=" * 72)
    w("intake_from_frontier -- census-sourced intake SCAFFOLDING")
    w("=" * 72)
    w("HONESTY: intake makes NO certification claim -- signals, never verdicts.")
    w("  A selected source that later fails to certify is recorded by the")
    w("  driver as a FIRST-CLASS REFUSAL (demand data), never silently dropped.")
    w("-" * 72)
    df = frontier.get("derived_from", {})
    w(f"root                : {paths['root']}")
    w(f"frontier derived_from census_portfolio_sha256: "
      f"{df.get('census_portfolio_sha256', '<absent>')}")
    w(f"mode                : "
      f"{'--ready' if mode == 'ready' else '--unblocked ' + str(signal)}")
    w(f"take                : {take}")
    w(f"live source total   : {expected_total}  "
      f"(registration.n_top_level_sources; NOT a frozen constant)")
    w(f"selected            : {len(plan)}")
    w(f"new source total    : {expected_total + len(plan)}")
    w("-" * 72)
    for n in notes:
        w(n)
    if notes:
        w("-" * 72)
    if not plan:
        w("(no candidates selected -- nothing to intake)")

    w("SELECTED SOURCES (verbatim prose written to specs/mathsources/):")
    for i, e in enumerate(plan, 1):
        w(f"  [{i}] {e['file']}")
        w(f"      corpus     : {e['corpus']}")
        w(f"      node_id    : {e['node_id']}")
        w(f"      text_sha256: {e['text_sha256']}")
        w(f"      prose      : {e['prose']}")
    w("-" * 72)

    w("MANIFEST files ENTRIES to paste into specs/mathsources/manifest.json:")
    for e in plan:
        w("  " + json.dumps(_manifest_entry(e["stem"])))
    w("-" * 72)

    w("REGISTRATION lineage-entry SKELETON to append to "
      "specs/mathsources/registration.json (\"lineage\"):")
    skel = _lineage_skeleton(expected_total + len(plan), len(plan),
                             [e["corpus"] for e in plan])
    for line in json.dumps(skel, indent=2).splitlines():
        w("  " + line)
    w("-" * 72)

    rel = f"wp_c{readings_index}_readings.py"
    w(f"READINGS PROVENANCE-MODULE SKELETON: {rel}")
    w("  (docstring + PROVENANCE dict + helpers + per-source TODO stubs; the")
    w("   READINGS bodies stay for the driver session to author.)")
    w("-" * 72)

    if apply:
        w("APPLIED: wrote the source files + readings skeleton listed above.")
        w("REMAINING (driver): paste manifest entries; author + certify the")
        w("  readings; run regen_downstream; re-baseline registration LIVE;")
        w("  full suite; commit.")
    else:
        w("DRY-RUN (default): no files written. Re-run with --apply to write")
        w("  the source files and the readings-module skeleton.")
    w("=" * 72)
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- #
# apply
# --------------------------------------------------------------------------- #

def _apply(plan, paths, readings_index):
    written = []
    ms = paths["mathsources"]
    for e in plan:
        dest = os.path.join(ms, e["file"])
        if os.path.exists(dest):
            raise SystemExit(f"error: refusing to overwrite {dest}")
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(e["prose"] + "\n")
        written.append(dest)
    rmod = os.path.join(paths["root"], f"wp_c{readings_index}_readings.py")
    if os.path.exists(rmod):
        raise SystemExit(f"error: refusing to overwrite {rmod}")
    with open(rmod, "w", encoding="utf-8") as fh:
        fh.write(_readings_module(readings_index, plan))
    written.append(rmod)
    return written


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Frontier-driven census-sourced intake scaffolding "
                    "(signals, never verdicts).")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--ready", action="store_true",
                      help="select the first --take ready entries "
                           "(frontier order).")
    mode.add_argument("--unblocked", metavar="SIGNAL",
                      help="select the first --take nodes of the named "
                           "blocked group (post-purchase cycle).")
    ap.add_argument("--take", type=int, required=True,
                    help="number of entries to select.")
    ap.add_argument("--apply", action="store_true",
                    help="write files (default is a dry-run plan).")
    ap.add_argument("--frontier", default=None,
                    help="path to results/frontier.json "
                         "(default: <root>/results/frontier.json).")
    ap.add_argument("--root", default=_DEFAULT_ROOT,
                    help="repo root (default: this file's repo).")
    args = ap.parse_args(argv)

    if args.take < 0:
        raise SystemExit("error: --take must be >= 0")

    paths = _paths(os.path.abspath(args.root))
    frontier_path = args.frontier or paths["frontier_default"]
    if not os.path.isfile(frontier_path):
        raise SystemExit(f"error: frontier not found: {frontier_path}")
    with open(frontier_path, encoding="utf-8") as fh:
        frontier = json.load(fh)

    expected_total = _expected_total(paths["registration"])
    existing_prefixes, intaken, existing_names = _existing_sources(
        paths["mathsources"])

    mode = "ready" if args.ready else "unblocked"
    cands, notes = _select(frontier, mode, args.unblocked, args.take, intaken)
    plan = _allocate(cands, existing_prefixes, existing_names)

    # resolve verbatim prose live from the committed corpus nodes.jsonl, and
    # verify the frontier hash matches (frontier/corpus desync is an error).
    corpus_idx = {}
    for e in plan:
        if e["corpus"] not in corpus_idx:
            corpus_idx[e["corpus"]] = _corpus_index(
                paths["mathsources"], e["corpus"])
        idx = corpus_idx[e["corpus"]]
        if e["node_id"] not in idx:
            raise SystemExit(
                f"error: node {e['node_id']} not in corpus {e['corpus']}")
        prose = idx[e["node_id"]]
        got = _sha_stripped(prose)
        if got != e["text_sha256"]:
            raise SystemExit(
                f"error: text_sha256 mismatch for {e['corpus']}/{e['node_id']}: "
                f"frontier {e['text_sha256'][:16]} != corpus {got[:16]} "
                "(frontier is stale; regenerate it)")
        e["prose"] = prose

    readings_index = _next_readings_index(paths["root"])

    plan_text = _render_plan(frontier, mode, args.unblocked, args.take, plan,
                             notes, paths, expected_total, readings_index,
                             args.apply)
    sys.stdout.write(plan_text)

    if args.apply and plan:
        written = _apply(plan, paths, readings_index)
        for w in written:
            sys.stdout.write(f"WROTE {w}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
