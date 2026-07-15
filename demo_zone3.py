#!/usr/bin/env python3
"""Zone 3 end-to-end showcase -- the speculative planner, LLM-free, in one run.

This ties the three landed Zone-3 pieces together for a reader, top to bottom,
with no LLM, no kernel, no solver, no codec emission -- only pure, deterministic
accounting over hand-authored / planted inputs:

  1. READING CORPUS      -- the hand-authored seed readings (real) plus the
                            system-origin `dream/` readings the miner may propose
                            from but that never decide admission on their own.
  2. SEARCHED vs GREEDY  -- the S1 beam search over macro-admission SEQUENCES
     MACRO ADMISSION        escapes the greedy one-macro-per-iteration trap:
                            greedy admits the len-4 macro and is stranded; the
                            searched sequence admits the strictly cheaper pair.
  3. LOOKAHEAD STEERING   -- the S2 depth-bounded rollout prices a coverage group
                            by the LOWEST ledger cost reachable within `depth`
                            hypothetical admissions, so a group that scores worse
                            greedily but unlocks more coverage wins the argmin.
  4. SUMMARY              -- the printed numbers are also written to
                            results/zone3_summary.txt.

REQUIRES_LLM = False.  Determinism: no random, no clocks, no network; the beam
search breaks ties by canonical JSON, so every number here is byte-stable.

Exit status: 0 iff every invariant holds; non-zero (with a listed failure) on any
broken invariant.  Prints a clear sectioned report and ends with a single
`== ZONE 3 SHOWCASE OK ==` line on success.
"""
from __future__ import annotations

import sys

import common
from buildloop.reading_corpus import load_readings
import buildloop.mdl_macros as mdl_macros
import buildloop.recurrence as recurrence
import planner.lookahead as lh
from tests import fixtures_macro_corpora as fx

REQUIRES_LLM = False

# Beam / depth for the S1 searched sequence: greedy is beam_width == 1.
_BEAM = 10
_DEPTH = 6

_FAILURES: list[str] = []
_SUMMARY: dict[str, object] = {}


def _rule(char: str = "=") -> None:
    print(char * 72)


def _section(title: str) -> None:
    print()
    _rule("=")
    print(title)
    _rule("=")


def _check(cond: bool, label: str) -> bool:
    """Record and print one invariant; a failure is fatal at exit."""
    print(("  PASS  " if cond else "  FAIL  ") + label)
    if not cond:
        _FAILURES.append(label)
    return bool(cond)


# --------------------------------------------------------------------------- 1
def section_reading_corpus() -> None:
    _section("SECTION 1 -- reading corpus (real seed vs dream proposals)")
    readings_dir = common.REPO_ROOT / "specs" / "readings"
    dream_dir = readings_dir / "dream"

    # load_readings globs *.json NON-recursively, so the top-level load is the
    # real seed corpus only; the dream/ subdir is loaded separately.
    real = load_readings(readings_dir)
    dream = load_readings(dream_dir)
    total = len(real) + len(dream)

    print("  real  corpus entries (specs/readings/*.json)      = %d" % len(real))
    print("  dream corpus entries (specs/readings/dream/*.json) = %d" % len(dream))
    print("  total corpus entries                               = %d" % total)
    print("  real requests:")
    for e in real:
        print("    - %s" % e.request)
    print("  dream requests (system-origin proposals):")
    for e in dream:
        print("    - %s" % e.request)

    _check(len(real) >= 1, "at least one real seed reading is present")
    _check(len(dream) >= 1, "at least one dream reading is present")
    _check(total >= 8, "corpus has >= 8 total entries (real + dream)")

    _SUMMARY["real_entries"] = len(real)
    _SUMMARY["dream_entries"] = len(dream)
    _SUMMARY["total_entries"] = total


# --------------------------------------------------------------------------- 2
def _admitted_count(table: dict) -> int:
    """Number of macros a searched/greedy table admitted over the empty start."""
    return len(table)


def section_macro_admission() -> None:
    _section("SECTION 2 -- searched vs greedy macro admission (S1)")

    corpus = fx.trap_corpus()
    none = mdl_macros.corpus_dl(corpus, {})["total"]
    greedy = recurrence.searched_macro_sequence(
        corpus, {}, beam_width=1, max_depth=_DEPTH)
    searched = recurrence.searched_macro_sequence(
        corpus, {}, beam_width=_BEAM, max_depth=_DEPTH)

    greedy_dl = mdl_macros.corpus_dl(corpus, greedy)["total"]
    searched_dl = mdl_macros.corpus_dl(corpus, searched)["total"]
    n_greedy = _admitted_count(greedy)
    n_searched = _admitted_count(searched)

    print("  trap_corpus (3x [A,B,C,D] + 1x [A,B,A,B]):")
    print("    corpus_dl with NO macros        = %.1f" % none)
    print("    greedy   (beam_width=1)  corpus_dl = %.1f   macros admitted = %d"
          % (greedy_dl, n_greedy))
    print("    searched (beam_width=%d) corpus_dl = %.1f   macros admitted = %d"
          % (_BEAM, searched_dl, n_searched))
    print("    none -> greedy -> searched = %.1f -> %.1f -> %.1f"
          % (none, greedy_dl, searched_dl))

    _check(searched_dl < greedy_dl,
           "searched corpus_dl STRICTLY below greedy (the trap is escaped)")
    _check(n_greedy == 1, "greedy admits exactly 1 macro (stranded on len-4 A)")
    _check(n_searched == 2, "searched admits exactly 2 macros (the pair {B,C})")

    # incompressible: no window recurs across >= 2 readings -> nothing mineable.
    inc = fx.incompressible_corpus()
    inc_greedy = recurrence.searched_macro_sequence(
        inc, {}, beam_width=1, max_depth=_DEPTH)
    inc_searched = recurrence.searched_macro_sequence(
        inc, {}, beam_width=_BEAM, max_depth=_DEPTH)
    print("  incompressible_corpus (4 all-distinct 2-stmt readings):")
    print("    greedy macros admitted   = %d" % len(inc_greedy))
    print("    searched macros admitted = %d" % len(inc_searched))
    _check(len(inc_greedy) == 0 and len(inc_searched) == 0,
           "incompressible corpus admits NOTHING (greedy and searched)")

    _SUMMARY["macro_none_dl"] = none
    _SUMMARY["macro_greedy_dl"] = greedy_dl
    _SUMMARY["macro_searched_dl"] = searched_dl
    _SUMMARY["macro_greedy_count"] = n_greedy
    _SUMMARY["macro_searched_count"] = n_searched
    _SUMMARY["incompressible_admitted"] = len(inc_greedy) + len(inc_searched)


# --------------------------------------------------------------------------- 3
def _spec(path: str, atoms, size: int = 64) -> dict:
    return {"path": path, "language": "ksy",
            "atoms": set(atoms), "size_bytes": size}


def section_lookahead() -> None:
    _section("SECTION 3 -- lookahead steering (S2 depth-2 rollout)")

    # Planted world: 5 Z-specs each needing just {z}; 3 P-specs each needing one
    # distinct head plus the SHARED tail {t}.  Group X covers the 5 Z-specs (the
    # greedily-larger, immediate-coverage-max group); group Y covers the 3 shared
    # -tail P-specs.  Resolving Y first unlocks strictly more coverage two moves
    # out (Y then one cheap admission finishes ALL 8), so Y prices below X.
    backlog = [
        _spec("planted://P/0", {"h1", "t"}),
        _spec("planted://P/1", {"h2", "t"}),
        _spec("planted://P/2", {"h3", "t"}),
        _spec("planted://Z/0", {"z"}),
        _spec("planted://Z/1", {"z"}),
        _spec("planted://Z/2", {"z"}),
        _spec("planted://Z/3", {"z"}),
        _spec("planted://Z/4", {"z"}),
    ]
    groupX = {"language": "ksy", "missing": ["z"],
              "specs": [b for b in backlog if "z" in b["atoms"]],
              "atoms_union": {"z"}}
    groupY = {"language": "ksy", "missing": ["h1", "h2", "h3", "t"],
              "specs": [b for b in backlog if "t" in b["atoms"]],
              "atoms_union": {"h1", "h2", "h3", "t"}}

    generators: list = []
    vx = lh.rollout_value(generators, backlog, groupX, depth=2)
    vy = lh.rollout_value(generators, backlog, groupY, depth=2)

    print("  planted backlog: 5 Z-specs {z}, 3 P-specs {h_i, t} (shared tail t)")
    print("    group X  covers %d specs  atoms_union=%s"
          % (len(groupX["specs"]), sorted(groupX["atoms_union"])))
    print("    group Y  covers %d specs  atoms_union=%s"
          % (len(groupY["specs"]), sorted(groupY["atoms_union"])))
    print("    rollout_value(X) = %.6f" % vx)
    print("    rollout_value(Y) = %.6f" % vy)

    ranking = sorted([("Y", vy), ("X", vx)], key=lambda t: (t[1], t[0]))
    print("    rollout_value ranking (lower = better first admission):")
    for name, v in ranking:
        print("      %s  %.6f" % (name, v))

    _check(vy == vy and vy < float("inf"), "group Y prices to a FINITE cost")
    _check(vx == vx and vx < float("inf"), "group X prices to a FINITE cost")
    _check(vy < vx,
           "rollout_value(Y) STRICTLY below rollout_value(X) "
           "(the enabling group wins the argmin)")

    # determinism: re-price both groups; two calls must be byte-identical.
    vy2 = lh.rollout_value(generators, backlog, groupY, depth=2)
    vx2 = lh.rollout_value(generators, backlog, groupX, depth=2)
    _check(common.canonical_json(vy) == common.canonical_json(vy2)
           and common.canonical_json(vx) == common.canonical_json(vx2),
           "rollout_value is deterministic (two calls equal)")

    _SUMMARY["lookahead_vx"] = vx
    _SUMMARY["lookahead_vy"] = vy
    _SUMMARY["lookahead_ranking"] = [name for name, _ in ranking]


# --------------------------------------------------------------------------- 4
def write_summary() -> None:
    _section("SECTION 4 -- summary artifact")
    out = common.REPO_ROOT / "results" / "zone3_summary.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "Zone 3 speculative planner -- showcase summary",
        "REQUIRES_LLM = %s" % REQUIRES_LLM,
        "",
        "[1] reading corpus",
        "    real_entries   = %s" % _SUMMARY.get("real_entries"),
        "    dream_entries  = %s" % _SUMMARY.get("dream_entries"),
        "    total_entries  = %s" % _SUMMARY.get("total_entries"),
        "",
        "[2] searched vs greedy macro admission (trap_corpus)",
        "    none_dl        = %s" % _SUMMARY.get("macro_none_dl"),
        "    greedy_dl      = %s   (macros=%s)"
        % (_SUMMARY.get("macro_greedy_dl"), _SUMMARY.get("macro_greedy_count")),
        "    searched_dl    = %s   (macros=%s)"
        % (_SUMMARY.get("macro_searched_dl"),
           _SUMMARY.get("macro_searched_count")),
        "    incompressible_corpus admitted = %s"
        % _SUMMARY.get("incompressible_admitted"),
        "",
        "[3] lookahead steering (depth-2 rollout)",
        "    rollout_value(X) = %s" % _SUMMARY.get("lookahead_vx"),
        "    rollout_value(Y) = %s" % _SUMMARY.get("lookahead_vy"),
        "    ranking (best first) = %s"
        % ", ".join(_SUMMARY.get("lookahead_ranking", [])),
        "",
    ]
    out.write_text("\n".join(lines))
    print("  wrote %s" % out)


def main() -> int:
    _rule("=")
    print("ZONE 3 SHOWCASE -- speculative planner end to end (REQUIRES_LLM=%s)"
          % REQUIRES_LLM)
    _rule("=")

    section_reading_corpus()
    section_macro_admission()
    section_lookahead()
    write_summary()

    print()
    _rule("-")
    if _FAILURES:
        print("INVARIANTS FAILED: %d" % len(_FAILURES))
        for f in _FAILURES:
            print("  - " + f)
        return 1
    print("== ZONE 3 SHOWCASE OK ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
