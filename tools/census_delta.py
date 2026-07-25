#!/usr/bin/env python3
"""The re-census delta, DERIVED -- the table a receipt pastes.

WHY THIS EXISTS (a defect, mechanized).  CLAUDE.md requires the re-census
delta to be committed in the same session that learns it, and every purchase
receipt (``results/p1_delta.md`` onward) states that delta as a small table of
numbers.  Those tables were hand-typed from a census run, which is a
transcription step with no tooth on it: the \\mathbb-spacing leak reached a
committed receipt precisely that way -- a broken reading copied faithfully
into prose that then read as evidence.  A number a human retypes is a number
nobody verified.

So the receipt stops retyping.  This tool loads ``results/census_portfolio.json``
at two points -- a git ref (``git show``) and, by default, the working tree --
and prints a deterministic markdown delta: per-signal ``miss_histogram``
changes, verdict changes, and per-corpus attempt-candidate changes, including
which node labels entered and left the mining queue.  Paste the output; do not
re-key it.

DISCIPLINE (the tower_census/blueprint_census one).  Deterministic, LLM-free
(the computation runs inside ``buildloop.lanes.token_free``), Lean-free,
clock-free -- the same inputs print the same bytes forever, which is what
makes a pasted table auditable against a re-run.  It REPORTS numbers: a
signal moving is a reading, never a fidelity verdict, and a delta of zero is
recorded evidence, never a reason to widen anything.

The git plumbing lives only in ``main``; the diff and the rendering are pure
functions over dicts (the ``tools/purchase_bill_manifest.py`` convention), so
the teeth run git-free.

Usage:
    python3 tools/census_delta.py                     # HEAD~1 -> working tree
    python3 tools/census_delta.py --base origin/main  # a named base
    python3 tools/census_delta.py --base A --head B   # two committed points

Exits 2 when either side is unreadable -- an absent or malformed census is a
failure to report, never an empty delta.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEFAULT_PATH = "results/census_portfolio.json"

# One dash for "this key did not exist on that side", which is a different
# fact from a measured zero and must never render as one.
ABSENT = "—"


def _counts(report: dict, key: str) -> dict:
    got = report.get(key) or {}
    return {str(k): int(v) for k, v in got.items()}


def _corpora(report: dict) -> dict:
    """corpus name -> its rollup row (attempt_candidates + verdicts)."""
    out = {}
    for row in report.get("corpora") or []:
        out[str(row.get("corpus", "?"))] = row
    return out


def _pair_delta(base: dict, head: dict) -> list:
    """[(key, base_or_None, head_or_None, delta_or_None)] over the union of
    keys, sorted by key.  A key present on one side only carries ``None`` on
    the other and no delta -- appearing and disappearing signals (the P3
    split's shape) must stay legible as such."""
    rows = []
    for key in sorted(set(base) | set(head)):
        b = base.get(key)
        h = head.get(key)
        d = None if b is None or h is None else h - b
        rows.append((key, b, h, d))
    return rows


def census_delta(base: dict, head: dict) -> dict:
    """The pure structural diff of two census_portfolio reports.

    Takes dicts, not paths: the git plumbing is ``main``'s job, so this is
    testable against synthetic before/after pairs with no repository at all."""
    base_c, head_c = _corpora(base), _corpora(head)
    corpora = []
    for name in sorted(set(base_c) | set(head_c)):
        b = base_c.get(name)
        h = head_c.get(name)
        b_lab = sorted(b.get("attempt_candidates") or []) if b else None
        h_lab = sorted(h.get("attempt_candidates") or []) if h else None
        corpora.append({
            "corpus": name,
            "base": None if b_lab is None else len(b_lab),
            "head": None if h_lab is None else len(h_lab),
            "delta": (None if b_lab is None or h_lab is None
                      else len(h_lab) - len(b_lab)),
            "entering": sorted(set(h_lab or []) - set(b_lab or [])),
            "leaving": sorted(set(b_lab or []) - set(h_lab or [])),
        })
    totals = _pair_delta(
        {k: v for k, v in (("corpora", base.get("n_corpora")),
                           ("nodes", base.get("n_nodes")))
         if v is not None},
        {k: v for k, v in (("corpora", head.get("n_corpora")),
                           ("nodes", head.get("n_nodes")))
         if v is not None},
    )
    return {
        "totals": totals,
        "miss_histogram": _pair_delta(_counts(base, "miss_histogram"),
                                      _counts(head, "miss_histogram")),
        "verdicts": _pair_delta(_counts(base, "verdicts"),
                                _counts(head, "verdicts")),
        "corpora": corpora,
    }


def _cell(value) -> str:
    return ABSENT if value is None else str(value)


def _delta_cell(value) -> str:
    return ABSENT if value is None else f"{value:+d}"


def _table(title: str, unit: str, rows: list) -> list:
    out = [f"## {title}", ""]
    if not rows:
        out += ["_no rows on either side._", ""]
        return out
    out += [f"| {unit} | base | head | delta |", "|---|---:|---:|---:|"]
    for key, b, h, d in rows:
        out.append(f"| `{key}` | {_cell(b)} | {_cell(h)} | {_delta_cell(d)} |")
    out.append("")
    return out


def render_md(diff: dict, base_label: str = "base",
              head_label: str = "head") -> str:
    """The pasteable receipt table.  Deterministic and clock-free: no run
    timestamp rides the output, so a re-run against the same two points
    reproduces the bytes an earlier receipt pasted."""
    lines = [f"# Census delta — `{base_label}` → `{head_label}`", "",
             "Derived by `tools/census_delta.py` from "
             f"`{DEFAULT_PATH}` at both points. Lexical census numbers: "
             "deterministic, LLM-free, Lean-free. Signals only — a moved "
             "count is a reading, never a fidelity verdict.", ""]
    lines += _table("Portfolio totals", "quantity", diff["totals"])
    lines += _table("Miss histogram (the vocabulary-growth price list)",
                    "signal", diff["miss_histogram"])
    lines += _table("Verdicts", "verdict", diff["verdicts"])

    lines += ["## Attempt candidates (per corpus)", ""]
    if not diff["corpora"]:
        lines += ["_no corpora on either side._", ""]
    else:
        lines += ["| corpus | base | head | delta |", "|---|---:|---:|---:|"]
        for row in diff["corpora"]:
            lines.append("| `{}` | {} | {} | {} |".format(
                row["corpus"], _cell(row["base"]), _cell(row["head"]),
                _delta_cell(row["delta"])))
        lines.append("")

    moved = [r for r in diff["corpora"] if r["entering"] or r["leaving"]]
    lines += ["## Queue membership changes", ""]
    if not moved:
        lines += ["_none: no node entered or left the mining queue._", ""]
    else:
        for row in moved:
            lines.append(f"- `{row['corpus']}`")
            if row["entering"]:
                lines.append("  - entering: "
                             + ", ".join(f"`{x}`" for x in row["entering"]))
            if row["leaving"]:
                lines.append("  - leaving: "
                             + ", ".join(f"`{x}`" for x in row["leaving"]))
        lines.append("")

    changed = (any(d for _, _, _, d in diff["totals"])
               or any(d for _, _, _, d in diff["miss_histogram"])
               or any(d for _, _, _, d in diff["verdicts"])
               or bool(moved))
    lines.append("**No measured delta.** Recorded as evidence, not retried."
                 if not changed else
                 "**Measured delta above.** Every number is derived; none is "
                 "re-keyed.")
    return "\n".join(lines) + "\n"


def _git_show(ref: str, path: str) -> str:
    proc = subprocess.run(["git", "show", f"{ref}:{path}"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise OSError(f"git show {ref}:{path} failed: "
                      f"{proc.stderr.strip() or 'no output'}")
    return proc.stdout


def _load(ref, path):
    """(text_source, label).  ``ref=None`` means the working tree."""
    if ref is None:
        with open(path) as fh:
            return json.load(fh), "working tree"
    return json.loads(_git_show(ref, path)), ref


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="HEAD~1",
                    help="git ref for the BEFORE census (default: HEAD~1; "
                         "no network, so name a local ref)")
    ap.add_argument("--head", default=None,
                    help="git ref for the AFTER census (default: the working "
                         "tree, which is what a mid-session receipt wants)")
    ap.add_argument("--path", default=DEFAULT_PATH,
                    help=f"census rollup path (default: {DEFAULT_PATH})")
    args = ap.parse_args(argv)

    try:
        base, base_label = _load(args.base, args.path)
        head, head_label = _load(args.head, args.path)
    except (OSError, ValueError) as exc:
        print(f"census_delta: unreadable census: {exc}", file=sys.stderr)
        return 2
    if not isinstance(base, dict) or not isinstance(head, dict):
        print("census_delta: unreadable census: expected a JSON object on "
              "both sides", file=sys.stderr)
        return 2

    from buildloop import lanes
    with lanes.token_free("census-delta"):
        diff = census_delta(base, head)
        out = render_md(diff, base_label, head_label)
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
