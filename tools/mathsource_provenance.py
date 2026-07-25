"""Consolidate the wp_ session scripts' PROVENANCE claims into one checked record.

WHY.  The census-sourced additions of cycles c2-c17 were introduced by 17
one-shot session scripts (``wp_c*_readings.py``, ``wp_auth_readings.py``).
Each records where its sources came from -- in a module-level ``PROVENANCE``
dict (the strong form, carrying ``sha256`` of the census node's prose) or, for
the earlier cycles, in a docstring table (the weak form, node named but no
sha).  NOTHING READ EITHER ONE.  The scripts are spent the moment their
readings land in ``specs/``, so the strongest evidence in them -- 47
cryptographic pins binding a committed source to the node it was quoted from
-- was never checked by anything.  That is this repo's recurring defect: a
claim that stopped tracking its evidence.

WHAT THIS IS NOT.  It is NOT a retirement of those scripts, and the first
attempt to treat it as one was wrong in two measurable ways worth recording:
``wp_auth_readings.py`` is imported by PRODUCTION code (``run/anchor.py``,
``bench/bench_hammer.py``), and ``tools/intake_from_frontier.py``'s
``_next_readings_index`` allocates the next cycle's index by SCANNING repo
root for ``wp_c<N>_readings.py`` -- so deleting the family resets that counter
to c2 and the next intake collides with cycle 2's identity in every historical
receipt.  The scripts remain the SOURCE OF TRUTH; this artifact is derived
from them, exactly like the other derived readings in ``results/``, and the
teeth regenerate and byte-compare so the two can never drift apart.

Offline, deterministic, clock-free: a pure function of the committed scripts.
"""
from __future__ import annotations

import argparse
import ast
import glob
import json
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

ARTIFACT = os.path.join("specs", "mathsources", "provenance.json")

# The docstring table's shape: "<source_id>  <- <corpus> <node label>".
_DOCSTRING_ROW = re.compile(
    r"^\s+(\d+_[a-z0-9_]+)\s+<-\s+(\S+)\s+(\S+)\s*$", re.M)

NOTE = (
    "Per-source PROVENANCE for the census-sourced corpus additions of cycles "
    "c2-c17: which census node each source's prose was quoted from, which "
    "cycle introduced it, and -- where the introducing session pinned one -- "
    "the sha256 of that node's prose.  DERIVED from the wp_*_readings.py "
    "session scripts, which remain the source of truth; regenerate with "
    "python3 tools/mathsource_provenance.py."
)

HONESTY = (
    "Two row STRENGTHS, never conflated.  A row with text_sha256 is PINNED: "
    "the introducing session recorded the sha256 of the census node's prose, "
    "and the teeth re-derive it from specs/mathsources/<corpus>/nodes.jsonl "
    "every run, so a drifted corpus or a misattributed source reddens.  A row "
    "with text_sha256 null is DOCSTRING-SOURCED: cycles c2-c6 predate the "
    "pinned form, so the node ATTRIBUTION is checked and the TEXT IDENTITY is "
    "not -- null means unpinned and never 'verified'.  source_committed false "
    "records a subject its cycle SELECTED and NAMED whose reading did not "
    "certify; it stays in writing as the refusal it was and is never quietly "
    "dropped to flatter the coverage count.  Coverage is PARTIAL BY "
    "CONSTRUCTION: this covers what the wp_ scripts introduced and nothing "
    "else, so a source absent here is a source no wp_ script introduced -- "
    "never a source without an origin.  And this artifact CONFERS NO "
    "AUTHORITY: the scripts are the source of truth, this is a reading of "
    "them, and where the two disagree the scripts win and this file is stale."
)


def _cycle_of(path: str) -> str:
    return os.path.basename(path)[3:-len("_readings.py")]


def collect(root: str = _ROOT) -> dict:
    """Merge the strong (PROVENANCE dict) and weak (docstring) forms.

    The strong form WINS wherever both exist: it carries the sha.
    """
    rows: dict[str, dict] = {}
    for path in sorted(glob.glob(os.path.join(root, "wp_*_readings.py"))):
        cycle = _cycle_of(path)
        with open(path, encoding="utf-8") as fh:
            src = fh.read()

        for node in ast.parse(src).body:            # strong form
            if not isinstance(node, ast.Assign):
                continue
            if not any(getattr(t, "id", "") == "PROVENANCE" for t in node.targets):
                continue
            for key, val in zip(node.value.keys, node.value.values):
                d = ast.literal_eval(val)
                rows[ast.literal_eval(key)] = {
                    "corpus": d["corpus"],
                    "node_id": d["node_id"],
                    "text_sha256": d.get("text_sha256"),
                    "introduced_by": cycle,
                }

        for m in _DOCSTRING_ROW.finditer(src):      # weak form, never overwrites
            sid, corpus, label = m.groups()
            rows.setdefault(sid, {"corpus": corpus, "node_id": label,
                                  "text_sha256": None, "introduced_by": cycle})

    for sid, row in rows.items():                   # a READING of the tree
        row["source_committed"] = os.path.isfile(
            os.path.join(root, "specs", "mathsources", sid + ".txt"))
    return rows


def build(root: str = _ROOT) -> dict:
    return {"schema": "mathsource-provenance/v1", "note": NOTE,
            "honesty": HONESTY, "rows": collect(root)}


def _write(doc: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
        fh.write("\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=os.path.join(_ROOT, ARTIFACT))
    args = ap.parse_args(argv)
    doc = build()
    _write(doc, args.out)
    pinned = sum(1 for r in doc["rows"].values() if r["text_sha256"])
    print(f"provenance: {len(doc['rows'])} rows ({pinned} sha-pinned, "
          f"{len(doc['rows']) - pinned} docstring-sourced) -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
