#!/usr/bin/env python3
"""tools/promote_sources.py -- WP-SRC promotion: staged/ -> top-level (files[]).

The checked procedure behind the promotion path documented in
`specs/mathsources/staged/README.md`.  DRY-RUN BY DEFAULT: invoked with no
``--apply`` flag, this tool prints the full change plan and touches nothing
on disk.  ``--apply`` is exercised in this package's tests ONLY against a
temp copy of the specs tree + a temp copy of the manifest -- never against
the real repo (house rule).

Background (see ``specs/mathsources/staged/README.md`` and the WP-SRC merge
at 853dcee / parents 1aa058a, 32a846d): 11 exogenous sources were staged
under ``specs/mathsources/staged/`` rather than committed top-level, because
top-level placement would move three things that are currently pinned:

  * ``bench_formalize.py``'s ``_CORPUS.glob("*.txt")`` denominators
    (committed ``results/formalize_bench_state.jsonl``: ``ungoverned:40`` /
    ``governed:40``, and the "><= 30/40 certified" headline),
  * ``cgb.py``'s ``_ledger_sync`` (``ms.glob("*.txt")``), which bills every
    top-level source as a math-source demand row (the corpus DL base), and
  * ``tests/test_mathsources_manifest.py``'s frozen ``EXPECTED_TOTAL = 40``
    and top-level ``.txt`` <-> ``manifest["files"]`` bijection.

The 853dcee review verdict was MERGE, with promotion-time to-dos recorded
("provenance nits recorded for promotion time"; promotion path documented).
Two of those to-dos are GENERAL/mechanical and are surfaced as a checklist on
every dry-run plan (see ``_readme_checklist`` / axis reconciliation below):

  (a) the ad-hoc ``existential`` axis (staging-only) must reconcile with the
      frozen test's ``VALID_AXES`` set at promotion time -- either add
      ``existential`` to ``VALID_AXES`` or retag the axis as ``plain``
      (README's own words).  This tool retags to ``plain`` by default
      (self-contained: it never edits the frozen test file), or preserves
      the ``existential`` tag with ``--keep-existential-axis`` if a reviewer
      would rather bump ``VALID_AXES`` by hand.
  (b) the downstream re-baseline obligations (bench denominators, ledger
      demand rows, the frozen test's pins) must be re-run/re-verified once
      any promotion lands -- reported as a checklist, read from the staged
      README's own bullet list rather than hardcoded.

The other two were PER-SOURCE provenance nits that this tool encoded as
BLOCKERS: --apply refuses to promote a source with an unresolved blocker
unless the caller passes an explicit, auditable --waive for it (written into
the manifest entry as `promotion_note` -- never silent):

  (c) ``43_larger_integer_exists.txt`` -- provenance.verbatim was a composed
      paraphrase, not a literal quote from one primary, citable source (the
      staged reference cited a *class* of standard texts: Epp's Discrete
      Mathematics with Applications; ProofWiki's Greatest/Least Elements
      category page).
  (d) ``44_divides_witness.txt`` -- provenance.license was CC BY-NC-SA
      (LibreTexts), a Non-Commercial license; promoting it to committed
      top-level status needed an explicit licensing decision.

RESOLUTION (commit 2c2a2a1): both (c) and (d) were cleared the decided-proper
way -- by FIXING the citations, not by waiving.  (c) now cites one pinned
primary page, ProofWiki "Set of Integers is not Bounded" (CC BY-SA 4.0); (d)
now cites ProofWiki "Definition:Divisor of Integer" (CC BY-SA 4.0), a
license-compatible page carrying the same divisibility definition.  Both rows
have therefore been removed from BLOCKER_TABLE, which is now empty.  The waiver
machinery itself is unchanged and is still tested (via a synthetic blocker).

See BLOCKER_TABLE below.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import common  # noqa: E402

# --------------------------------------------------------------------------- #
# defaults (overridable so tests can point every path at a temp copy)
# --------------------------------------------------------------------------- #

DEFAULT_MATHSOURCES = common.REPO_ROOT / "specs" / "mathsources"

# Read-only mirrors of the frozen pins in tests/test_mathsources_manifest.py
# and tests/test_mathsources_staged.py.  This tool never edits those files;
# it only reads/reports against these mirrored constants so the dry-run plan
# can say what *must* change without assuming write access to test code.
FROZEN_EXPECTED_TOTAL = 40
FROZEN_VALID_AXES = {"side-condition", "ambient-ambiguity", "non-transcribable", "plain"}
FROZEN_EXPECTED_MISSES = {"operator:prime", "carrier:Real", "kind:set-object"}
IDIOM_PREFIX = "idiom:"

FILES_SCHEMA_FIELDS = {"file", "axes", "expect_transcribes", "miss_kind_guess"}
# promotion_note is the one field this tool itself adds beyond the frozen
# files-schema, to record an auditable waiver (never silent).
FILES_SCHEMA_FIELDS_WITH_NOTE = FILES_SCHEMA_FIELDS | {"promotion_note"}
STAGING_ONLY_FIELDS = {"existential", "binder_hint", "provenance", "staged_reason"}


@dataclass(frozen=True)
class Blocker:
    code: str
    reason: str


# --------------------------------------------------------------------------- #
# WP-SRC review to-do table (853dcee: "provenance nits recorded for promotion
# time").  Per-source, per-code blockers.  --apply refuses to promote a
# source appearing here unless every one of its blockers is waived (an
# explicit --waive with a non-empty reviewer reason, recorded verbatim into
# the promoted manifest entry's `promotion_note`).  Keyed by the staged
# filename; add rows here -- never silently -- as future reviews record more.
# --------------------------------------------------------------------------- #
BLOCKER_TABLE: Dict[str, Tuple[Blocker, ...]] = {
    # Both WP-SRC promotion blockers were CLEARED by fixing the citations (the
    # decided-proper path, no waivers) in commit 2c2a2a1:
    #
    #   * 43_larger_integer_exists.txt [composed-verbatim] -- the class-of-texts
    #     citation (Epp; ProofWiki Category:Greatest/Least Elements) was replaced
    #     with one pinned primary page, ProofWiki "Set of Integers is not Bounded"
    #     (CC BY-SA 4.0), verbatim "The set $\Z$ of integers is not bounded in
    #     $\R$."  The provenance block records the forall-exists rendering and the
    #     convergent-search verification method.
    #   * 44_divides_witness.txt [nc-license] -- the CC BY-NC-SA LibreTexts source
    #     was swapped for ProofWiki "Definition:Divisor of Integer" (canonical
    #     Definition:Divisor (Algebra)/Integer, CC BY-SA 4.0), a license-compatible
    #     page carrying the same divisibility definition.
    #
    # The table is intentionally empty now: no real staged source carries an
    # unresolved review blocker.  The waiver machinery below (BLOCKER_TABLE ->
    # unresolved/waived -> promotion_note) is preserved and is exercised in the
    # tests against a SYNTHETIC blocker injected into this table, not a real one.
    # Add rows here -- never silently -- if a future review records a new nit.
}


class PromotionError(RuntimeError):
    """Raised by --apply when a source cannot be promoted (unresolved
    blocker, unknown id, schema problem, ...). Nothing is mutated when this
    is raised -- validation runs fully before any file/manifest write."""


# --------------------------------------------------------------------------- #
# manifest / staged-tree plumbing
# --------------------------------------------------------------------------- #

def _load_manifest(manifest_path: Path) -> dict:
    with open(manifest_path, encoding="utf-8") as fh:
        return json.load(fh)


def _dump_manifest(manifest: dict, manifest_path: Path) -> None:
    # Mirrors the on-disk style exactly (verified byte-identical round-trip
    # against the real manifest.json): indent=2, trailing newline, no key
    # sorting (preserves the human-authored top-level key order).
    text = json.dumps(manifest, indent=2) + "\n"
    manifest_path.write_text(text, encoding="utf-8")


def _staged_entries(manifest: dict) -> List[dict]:
    return sorted(manifest.get("staged", []), key=lambda e: e["file"])


def _resolve_id(raw: str, staged: List[dict]) -> dict:
    """Match a user-supplied id against a staged entry's filename.

    Accepts the bare numeric prefix ("43"), the stem ("43_larger_integer_exists"),
    or the full filename ("43_larger_integer_exists.txt")."""
    candidates = []
    for entry in staged:
        fname = entry["file"]
        stem = fname[:-4] if fname.endswith(".txt") else fname
        prefix = stem.split("_", 1)[0]
        if raw in (fname, stem, prefix):
            candidates.append(entry)
    if not candidates:
        known = ", ".join(e["file"] for e in staged)
        raise PromotionError(f"no staged source matches {raw!r} (known: {known})")
    if len(candidates) > 1:
        raise PromotionError(f"{raw!r} matches multiple staged sources: "
                              f"{[c['file'] for c in candidates]}")
    return candidates[0]


def select_sources(manifest: dict, ids: List[str], all_staged: bool) -> List[dict]:
    staged = _staged_entries(manifest)
    if all_staged:
        if ids:
            raise PromotionError("pass either --all-staged or explicit ids, not both")
        return staged
    if not ids:
        raise PromotionError("no source ids given (use --all-staged or name one or more ids)")
    seen = {}
    for raw in ids:
        entry = _resolve_id(raw, staged)
        seen[entry["file"]] = entry
    return sorted(seen.values(), key=lambda e: e["file"])


# --------------------------------------------------------------------------- #
# axis reconciliation (README's two documented options)
# --------------------------------------------------------------------------- #

def _reconcile_axes(axes: List[str], keep_existential_axis: bool) -> Tuple[List[str], bool]:
    """Returns (new_axes, needed_reconciliation).

    ``needed_reconciliation`` is True iff the entry carried the staging-only
    ``existential`` axis, which is not in the frozen VALID_AXES set.  Default
    behaviour retags ``existential`` -> ``plain`` (README option 2, and the
    only option this self-contained tool can perform without editing the
    frozen test file); ``--keep-existential-axis`` preserves the tag
    unreconciled (README option 1), leaving the VALID_AXES bump to a
    reviewer editing tests/test_mathsources_manifest.py by hand.
    """
    if "existential" not in axes:
        return list(axes), False
    if keep_existential_axis:
        return list(axes), True
    new_axes = ["plain" if a == "existential" else a for a in axes]
    # de-dup while preserving order (e.g. an entry that was already ["existential", "plain"])
    out = []
    for a in new_axes:
        if a not in out:
            out.append(a)
    return out, True


def _files_schema_entry(staged_entry: dict, keep_existential_axis: bool,
                         promotion_note: Optional[str]) -> Tuple[dict, bool]:
    axes, needed_reconciliation = _reconcile_axes(staged_entry["axes"], keep_existential_axis)
    out = {
        "file": staged_entry["file"],
        "axes": axes,
        "expect_transcribes": staged_entry["expect_transcribes"],
    }
    if "miss_kind_guess" in staged_entry:
        out["miss_kind_guess"] = staged_entry["miss_kind_guess"]
    if promotion_note:
        out["promotion_note"] = promotion_note
    return out, needed_reconciliation


# --------------------------------------------------------------------------- #
# README-derived re-baseline checklist (obligation 1: read from the README
# rather than hardcoding where possible)
# --------------------------------------------------------------------------- #

def _readme_bullets(readme_text: str) -> List[str]:
    """Extract top-level `* ...` bullets (with wrapped continuation lines)
    from the staged README, in file order.  This is how the dry-run plan's
    re-baseline checklist stays sourced from the README's own words instead
    of a hardcoded copy that could drift."""
    bullets: List[str] = []
    cur: Optional[List[str]] = None
    for line in readme_text.splitlines():
        if line.startswith("* "):
            if cur is not None:
                bullets.append(" ".join(cur))
            cur = [line[2:].strip()]
        elif cur is not None and line.strip() and not line.startswith("#"):
            cur.append(line.strip())
        else:
            if cur is not None:
                bullets.append(" ".join(cur))
                cur = None
    if cur is not None:
        bullets.append(" ".join(cur))
    return bullets


# Downstream consumers of results/formalize_bench_state.jsonl beyond the ones
# the README names directly (repo scan, not README text -- kept separate and
# labeled so provenance stays honest): once bench_formalize.py's denominators
# move, anything replaying that checkpoint is stale until re-run.
_DOWNSTREAM_CASCADE = (
    "tools/entropy_refs.py reads results/formalize_bench_state.jsonl "
    "(STATE_PATH) to produce results/entropy_refs.json -- rerun it.",
    "tools/entropy_stack_fig.py renders results/entropy_stack.png from "
    "results/entropy_refs.json -- rerun it after entropy_refs.py.",
    "tools/tower_census.py replays the same "
    "results/formalize_bench_state.jsonl checkpoint (CHECKPOINT) -- rerun it "
    "and re-check results/tower_census.{json,md}.",
)


# --------------------------------------------------------------------------- #
# plan
# --------------------------------------------------------------------------- #

@dataclass
class SourcePlan:
    file: str
    existing_axes: List[str]
    new_axes: List[str]
    needs_axis_reconciliation: bool
    expect_transcribes: bool
    miss_kind_guess: Optional[str]
    unresolved_blockers: List[Blocker]
    waived_blockers: List[Blocker]
    waiver_reason: Optional[str]


@dataclass
class Plan:
    sources: List[SourcePlan]
    expected_total_before: int
    expected_total_after: int
    non_transcribable_before: int
    non_transcribable_after: int
    misses_added: List[str]
    readme_checklist: List[str]
    downstream_cascade: List[str]

    @property
    def blocked(self) -> bool:
        return any(s.unresolved_blockers for s in self.sources)


def build_plan(manifest: dict, selected: List[dict], readme_text: str,
               keep_existential_axis: bool,
               waivers: Dict[str, str]) -> Plan:
    files_now = manifest.get("files", [])
    nt_before = sum(1 for e in files_now if "non-transcribable" in e["axes"])
    misses_added = []
    sources: List[SourcePlan] = []
    for entry in selected:
        axes, needs_recon = _reconcile_axes(entry["axes"], keep_existential_axis)
        blockers = list(BLOCKER_TABLE.get(entry["file"], ()))
        waiver_reason = waivers.get(entry["file"])
        waived = list(blockers) if (blockers and waiver_reason) else []
        unresolved = [] if waived else blockers
        if "non-transcribable" in entry["axes"] and entry.get("miss_kind_guess"):
            misses_added.append(entry["miss_kind_guess"])
        sources.append(SourcePlan(
            file=entry["file"],
            existing_axes=list(entry["axes"]),
            new_axes=axes,
            needs_axis_reconciliation=needs_recon,
            expect_transcribes=entry["expect_transcribes"],
            miss_kind_guess=entry.get("miss_kind_guess"),
            unresolved_blockers=unresolved,
            waived_blockers=waived,
            waiver_reason=waiver_reason if waived else None,
        ))
    nt_after = nt_before + sum(
        1 for s in sources if "non-transcribable" in s.new_axes)
    return Plan(
        sources=sources,
        expected_total_before=len(files_now),
        expected_total_after=len(files_now) + len(sources),
        non_transcribable_before=nt_before,
        non_transcribable_after=nt_after,
        misses_added=sorted(misses_added),
        readme_checklist=_readme_bullets(readme_text),
        downstream_cascade=list(_DOWNSTREAM_CASCADE),
    )


def render_plan(plan: Plan) -> str:
    """Deterministic (sorted, no timestamps/randomness) plan text."""
    lines: List[str] = []
    lines.append("=== promote_sources.py :: DRY-RUN PLAN (nothing on disk changes) ===")
    lines.append(f"sources selected: {len(plan.sources)}")
    lines.append("")
    for s in sorted(plan.sources, key=lambda s: s.file):
        lines.append(f"--- {s.file} ---")
        lines.append(f"  move: specs/mathsources/staged/{s.file} -> specs/mathsources/{s.file}")
        lines.append(f"  manifest: staged[] entry -> files[] entry")
        lines.append(f"  axes: {s.existing_axes} -> {s.new_axes}"
                     + ("  [VALID_AXES reconciliation: 'existential' is not in the "
                        "frozen VALID_AXES set (tests/test_mathsources_manifest.py); "
                        "retagged to 'plain' -- pass --keep-existential-axis to instead "
                        "keep 'existential' and bump VALID_AXES by hand]"
                        if s.needs_axis_reconciliation else ""))
        lines.append(f"  expect_transcribes: {s.expect_transcribes}"
                     + (f"  (miss_kind_guess={s.miss_kind_guess!r})" if s.miss_kind_guess else ""))
        if s.unresolved_blockers:
            lines.append("  BLOCKED (--apply will refuse):")
            for b in s.unresolved_blockers:
                lines.append(f"    - [{b.code}] {b.reason}")
            lines.append(f"    waive with: --waive {s.file}=<reason>")
        elif s.waived_blockers:
            lines.append("  blockers WAIVED (will be written as promotion_note):")
            for b in s.waived_blockers:
                lines.append(f"    - [{b.code}] waived; reviewer reason: {s.waiver_reason}")
        else:
            lines.append("  blockers: none recorded")
        lines.append("")

    lines.append("--- test pins that must change (tests/test_mathsources_manifest.py) ---")
    lines.append(f"  EXPECTED_TOTAL: {plan.expected_total_before} -> {plan.expected_total_after}")
    if plan.misses_added:
        new_misses = sorted(FROZEN_EXPECTED_MISSES | set(plan.misses_added))
        lines.append(
            "  non-transcribable quota: EXACTLY 3 pinned "
            f"(misses={sorted(FROZEN_EXPECTED_MISSES)}) -> would become "
            f"{plan.non_transcribable_after} "
            f"(misses added: {plan.misses_added}; reviewer must re-baseline "
            f"test_non_transcribable_quota_and_misses' EXPECTED_MISSES to "
            f"{new_misses} or its EXACTLY-3 assertion, since this promotion "
            "adds a non-transcribable entry)")
    if any(s.needs_axis_reconciliation for s in plan.sources):
        lines.append(
            "  VALID_AXES: no change needed IF the default retag-to-'plain' "
            "reconciliation above is used; if any source was promoted with "
            "--keep-existential-axis, VALID_AXES must gain 'existential'")
    lines.append("")

    lines.append("--- downstream re-baseline obligations (from staged/README.md) ---")
    for b in plan.readme_checklist:
        lines.append(f"  [ ] {b}")
    lines.append("")
    lines.append("--- downstream cascade (repo scan, not README) ---")
    for c in plan.downstream_cascade:
        lines.append(f"  [ ] {c}")
    lines.append("")
    lines.append("(this is a dry run -- no files or manifest entries have been touched;"
                 " pass --apply to perform the moves)")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# --apply
# --------------------------------------------------------------------------- #

def apply_promotion(mathsources_root: Path, manifest_path: Path,
                     ids: List[str], all_staged: bool,
                     waivers: Dict[str, str],
                     keep_existential_axis: bool = False) -> Plan:
    """Performs the promotion. Raises PromotionError (mutating nothing) if
    any selected source has an unresolved blocker, an unknown id, or a
    malformed waiver. All file moves + the manifest write happen only after
    every source has been validated -- and if a file move fails partway
    through, already-completed moves are rolled back, so the operation is
    all-or-nothing."""
    manifest = _load_manifest(manifest_path)
    selected = select_sources(manifest, ids, all_staged)
    readme_path = mathsources_root / "staged" / "README.md"
    readme_text = readme_path.read_text(encoding="utf-8") if readme_path.is_file() else ""

    for source_id, reason in waivers.items():
        if not reason or not reason.strip():
            raise PromotionError(f"--waive {source_id}=... requires a non-empty reason")
        if source_id not in BLOCKER_TABLE:
            raise PromotionError(
                f"--waive target {source_id!r} has no recorded blockers "
                f"(known blocker sources: {sorted(BLOCKER_TABLE)})")

    plan = build_plan(manifest, selected, readme_text, keep_existential_axis, waivers)
    if plan.blocked:
        blocked = [s.file for s in plan.sources if s.unresolved_blockers]
        raise PromotionError(
            f"refusing to apply: unresolved WP-SRC review blockers on {blocked} "
            f"(see plan for reasons; waive with --waive <file>=<reason>)")

    staged_dir = mathsources_root / "staged"
    moved: List[Tuple[Path, Path]] = []
    try:
        for s in plan.sources:
            src = staged_dir / s.file
            dst = mathsources_root / s.file
            if not src.is_file():
                raise PromotionError(f"staged source missing on disk: {src}")
            if dst.exists():
                raise PromotionError(f"promotion target already exists: {dst}")
            before_hash = common.sha256_bytes(src.read_bytes())
            shutil.move(str(src), str(dst))
            after_hash = common.sha256_bytes(dst.read_bytes())
            if before_hash != after_hash:
                raise PromotionError(f"byte content changed across move for {s.file}")
            moved.append((src, dst))

        promoted_files = {s.file: s for s in plan.sources}
        staged_by_file = {e["file"]: e for e in manifest.get("staged", [])}
        new_files_entries = []
        for s in plan.sources:
            note = None
            if s.waived_blockers:
                codes = ", ".join(b.code for b in s.waived_blockers)
                note = f"WAIVED at promotion ({codes}) -- reviewer reason: {s.waiver_reason}"
            entry, _ = _files_schema_entry(staged_by_file[s.file], keep_existential_axis, note)
            new_files_entries.append(entry)

        manifest["files"] = list(manifest.get("files", [])) + new_files_entries
        manifest["staged"] = [e for e in manifest.get("staged", [])
                               if e["file"] not in promoted_files]
        _dump_manifest(manifest, manifest_path)
    except Exception:
        # roll back any completed moves so the operation is all-or-nothing
        for src, dst in moved:
            if dst.exists() and not src.exists():
                shutil.move(str(dst), str(src))
        raise
    return plan


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _parse_waivers(raw: List[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for item in raw:
        if "=" not in item:
            raise PromotionError(f"--waive value {item!r} must be '<source_id>=<reason>'")
        source_id, reason = item.split("=", 1)
        out[source_id.strip()] = reason.strip()
    return out


def _resolve_waivers(manifest: dict, raw_waivers: Dict[str, str]) -> Dict[str, str]:
    """Re-key waivers by resolved staged filename (so --waive 43=... matches
    43_larger_integer_exists.txt the same way a bare id would)."""
    staged = _staged_entries(manifest)
    out: Dict[str, str] = {}
    for source_id, reason in raw_waivers.items():
        entry = _resolve_id(source_id, staged)
        out[entry["file"]] = reason
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("ids", nargs="*", help="staged source ids, e.g. 43 or 43_larger_integer_exists")
    ap.add_argument("--all-staged", action="store_true", help="select every staged source")
    ap.add_argument("--apply", action="store_true",
                    help="perform the promotion (default: dry-run only)")
    ap.add_argument("--waive", action="append", default=[],
                    metavar="SOURCE_ID=REASON",
                    help="waive a source's recorded review blockers with an explicit reason "
                         "(repeatable); required before --apply will promote a blocked source")
    ap.add_argument("--keep-existential-axis", action="store_true",
                    help="preserve the 'existential' axis tag instead of retagging to 'plain' "
                         "(README option 1: requires a reviewer to bump VALID_AXES by hand)")
    ap.add_argument("--mathsources-root", type=Path, default=DEFAULT_MATHSOURCES,
                    help="root of the specs/mathsources tree (default: the real repo tree)")
    ap.add_argument("--manifest", type=Path, default=None,
                    help="manifest.json path (default: <mathsources-root>/manifest.json)")
    args = ap.parse_args(argv)

    mathsources_root = args.mathsources_root
    manifest_path = args.manifest or (mathsources_root / "manifest.json")

    try:
        raw_waivers = _parse_waivers(args.waive)
        manifest = _load_manifest(manifest_path)
        waivers = _resolve_waivers(manifest, raw_waivers)

        if args.apply:
            plan = apply_promotion(mathsources_root, manifest_path, args.ids,
                                    args.all_staged, waivers, args.keep_existential_axis)
            print(f"APPLIED: promoted {len(plan.sources)} source(s): "
                  f"{[s.file for s in plan.sources]}")
            return 0
        else:
            selected = select_sources(manifest, args.ids, args.all_staged)
            readme_path = mathsources_root / "staged" / "README.md"
            readme_text = readme_path.read_text(encoding="utf-8") if readme_path.is_file() else ""
            plan = build_plan(manifest, selected, readme_text,
                               args.keep_existential_axis, waivers)
            sys.stdout.write(render_plan(plan))
            return 1 if plan.blocked else 0
    except PromotionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
