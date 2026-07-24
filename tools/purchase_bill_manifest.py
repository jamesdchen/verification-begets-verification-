#!/usr/bin/env python3
"""The purchase-bill manifest check (the maintainer-review narrower).

A full-bill purchase PR is big, and the maintainer is the ONLY gate it may
pass through (its trust-surface check is red by design: the growth registry
lives in buildloop/growth_protocol.py).  The firehose-discipline answer --
mechanize every mechanizable judgment, leave the human only the residue --
applies to the maintainer too: this check verifies the bill's MECHANICAL
items so the human review collapses to the one question no machine may
answer: should this capability exist?

Checks (each renders a checklist line; any failure exits nonzero):

  1. CEREMONY SCOPE -- the only ceremony-reserved path the diff touches is
     buildloop/growth_protocol.py.  A purchase that reaches kernel/certs.py,
     TRUST.md, setup.sh, ci/, .claude/, or .github/ is NOT a standard
     purchase and gets a full human review with no narrowing.
  2. ANTI_LIST BYTE-IDENTICAL -- the ANTI_LIST tuple in growth_protocol.py
     is extracted (ast) at base and head and must be exactly equal: trust
     roots never grow by purchase or economics (CLAUDE.md).
  3. DELTA RECEIPT -- the diff carries the re-census delta evidence: a
     registration.json change or a results/*delta*.md receipt (the P1
     worked example's results/p1_delta.md pattern).  "The re-census delta
     is committed in the same session that learns it."

Everything else on the bill (batteries, canary, registry-row shape, suite)
is already enforced by the fast gate's teeth; this tool never re-implements
them, it only narrows what remains for the human.

Usage (CI): python3 tools/purchase_bill_manifest.py --base SHA --head SHA
The pure functions take explicit inputs so the teeth run git-free.
"""
from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys

CEREMONY_RE = re.compile(
    r"^(kernel/certs\.py|TRUST\.md|buildloop/growth_protocol\.py|setup\.sh|"
    r"ci/|\.claude/|\.github/)")
ALLOWED_CEREMONY = {"buildloop/growth_protocol.py"}
DELTA_RECEIPT_RE = re.compile(
    r"^(specs/mathsources/registration\.json|results/[^/]*delta[^/]*\.md)$")


def ceremony_scope(changed_files):
    """(ok, touched_ceremony) -- ceremony paths in the diff vs the allowance."""
    touched = sorted(f for f in changed_files if CEREMONY_RE.match(f))
    return set(touched) <= ALLOWED_CEREMONY, touched


def extract_anti_list(source_text):
    """The ANTI_LIST tuple literal from growth_protocol.py source, as a
    tuple of strings.  Raises if absent or not a literal -- an unparseable
    anti-list is a failure, never a pass."""
    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "ANTI_LIST":
                    return tuple(ast.literal_eval(node.value))
    raise ValueError("ANTI_LIST assignment not found")


def has_delta_receipt(changed_files):
    return any(DELTA_RECEIPT_RE.match(f) for f in changed_files)


def _git(*argv):
    return subprocess.run(["git", *argv], check=True, capture_output=True,
                          text=True).stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", required=True)
    args = ap.parse_args()

    changed = [f for f in
               _git("diff", "--name-only", f"{args.base}...{args.head}")
               .splitlines() if f]
    rows = []
    ok = True

    scope_ok, touched = ceremony_scope(changed)
    rows.append(("ceremony scope limited to growth_protocol.py", scope_ok,
                 f"ceremony paths touched: {touched or 'none'}"))
    ok &= scope_ok

    if "buildloop/growth_protocol.py" in changed:
        base_src = _git("show", f"{args.base}:buildloop/growth_protocol.py")
        head_src = _git("show", f"{args.head}:buildloop/growth_protocol.py")
        try:
            same = extract_anti_list(base_src) == extract_anti_list(head_src)
            note = "byte-identical" if same else "CHANGED -- ceremony-only, never by purchase"
        except ValueError as exc:
            same, note = False, f"unparseable: {exc}"
        rows.append(("ANTI_LIST unchanged", same, note))
        ok &= same
    else:
        rows.append(("ANTI_LIST unchanged", True,
                     "growth_protocol.py untouched"))

    receipt = has_delta_receipt(changed)
    rows.append(("re-census delta receipt in diff", receipt,
                 "registration.json or results/*delta*.md"))
    ok &= receipt

    print("## purchase-bill manifest")
    for label, passed, note in rows:
        print(f"- [{'x' if passed else ' '}] {label} — {note}")
    print()
    if ok:
        print("MANIFEST PASS: mechanical bill items verified; the human "
              "question that remains is intent — should this capability exist?")
        return 0
    print("MANIFEST FAIL: a mechanical bill item is unsatisfied (above); "
          "this PR gets a full human review with no narrowing.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
