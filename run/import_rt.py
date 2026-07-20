"""WP-LI2 (PLAN_LEAN_IMPORT.md §2/§2.5/§4): the RT differential oracle.

The direction flip's trust half.  For a Mathlib declaration ``d`` with an
authored ``MathReading``, the compiled statement ``C := math_compile(reading)``
must be provably equivalent to ``d``'s ORIGINAL statement ``O`` -- the
round-trip differential no NL source can offer (plan §2).  The verdict is the
third recorded channel of the import cert story:

    rt-differential ∈ {defeq, proved, failed, deferred}

  * ``defeq``    -- the FAST PATH typechecks: a probe file uses the original
                    declaration itself as a proof of the compiled statement
                    (``example : <C-prop> := @<decl_name>``), so ``C`` is
                    definitionally the original's type.  This is exactly the
                    ``pp_roundtrip`` step-3 pattern (kernel/backends.py): the
                    def-eq verdict is Lean-typechecker-confirmed, never
                    text-compared.
  * ``proved``   -- defeq fails but an equivalence probe closes:
                    ``example : (<C-prop>) ↔ (<O-prop>) := <rung>`` for one
                    rung of the FROZEN ladder ``IFF_LADDER`` below.
  * ``failed``   -- every probe fails.  The row is REFUSED with the full probe
                    transcript, and the failure is logged as a FIRST-CLASS
                    event (``rt-differential-failure``) -- a fidelity-gates-
                    pass + RT-fail row is a *measured mistranslation*, the most
                    valuable failure class in the whole operation (plan
                    WP-LI2); it is never silently dropped (the
                    ``anchor_divergence`` / disagreement-logging discipline).
  * ``deferred`` -- ``common.lean_available()`` is False: recorded honestly,
                    never a failure -- byte-for-byte the statement-cert
                    deferral discipline (run/formalize.py stage 3.5) and the
                    run/anchor.py honest-skip of the kernel leg.

THE FROZEN LADDER (documented, bounded, never open-ended).  After the term-mode
``Iff.rfl`` fast rung (definitional equality of the two Props), one
structural unfold rung (``constructor``/``intro``/``exact``, both directions),
then the repo's existing witness-ladder rungs in their pinned order
(``generators/math_witness.py::RUNGS`` -- decide/omega/norm_num/simp;
``native_decide`` is escape-gate-forbidden and never appears):

    IFF_LADDER = ("Iff.rfl",
                  "by constructor <;> intro h <;> exact h",
                  "by decide", "by omega", "by norm_num", "by simp")

SANDBOX / ENV DISCIPLINE: probes are NEVER run through fresh subprocess
plumbing.  The default runner is ``kernel.backends.LeanBackend.elaborate`` --
the existing F0.5 jail (``unshare --net``, tmpfs, rlimits, the pinned
read-only Mathlib/toolchain mounts, the F0.4 escape gate re-applied to every
probe, the pinned ``common.MATHLIB_IMPORTS`` header).  Every probe is
additionally passed through ``validate_lean`` here (defense in depth -- the
same double-gating ``elaborate`` performs).  Consequence of reusing the pinned
import set: RT can only certify declarations reachable from the CERTIFICATION
surface (the pinned modules, WP-LI0); a declaration outside it fails to
elaborate and is honestly refused with the transcript saying so.

Honesty note (mirrors run/anchor.py's ⚠T1 discipline): probes run through
``elaborate`` are RUN-1 evidence -- an elaboration typecheck inside the jail.
The two-run L5 replay-as-data adjudication applies to the Phase-B
statement-cert mint, not to this recorded differential channel; the report
labels its channel accordingly and mints nothing.

Deterministic everything: zero LLM calls, no network, no wall-clock in any
control-flow decision or report byte (the report carries no timestamp; git
history carries the time).  Batch output ordering is sorted by ``decl_name``
and serialization is ``common.canonical_json`` -- byte-stable across reruns.
"""
from __future__ import annotations

import dataclasses
import json
import os
import pathlib

import common
from generators.math_reading import parse_math_reading, BadMathReading
from generators.math_compile import compile_math_reading, CompileError
from buildloop.validate_lean import validate_lean

_ROOT = pathlib.Path(__file__).resolve().parent.parent
REPORT_PATH = _ROOT / "results" / "import_rt_report.json"

# The frozen report schema tag (the run/anchor.py SCHEMA pattern).
SCHEMA = "import-rt-report/v1"

# The recorded verdict channel name (plan WP-LI2) and its frozen vocabulary.
RT_CHANNEL = "rt-differential"
RT_VERDICTS = ("defeq", "proved", "failed", "deferred", "out-of-surface")

# The first-class event kind for a both-probes-fail refusal (the
# anchor_divergence.EVENT_KIND / disagreement-logging discipline: events-only,
# never dressed as a cert row, never silently dropped).
EVENT_KIND = "rt-differential-failure"

# ---------------------------------------------------------------------------
# THE FROZEN LADDER (see module docstring).  Rung 0 is the term-mode
# definitional rung; rung 1 is the structural constructor/intro/exact unfold;
# rungs 2-5 are generators/math_witness.py::RUNGS in their pinned order.
# Bounded and closed: nothing may append to this tuple at run time, and
# `exact?` / `native_decide` (open-ended search / escape-gate-forbidden) never
# appear.
# ---------------------------------------------------------------------------
IFF_LADDER = (
    "Iff.rfl",
    "by constructor <;> intro h <;> exact h",
    "by decide",
    "by omega",
    "by norm_num",
    "by simp",
)


@dataclasses.dataclass
class RTResult:
    """The per-declaration RT differential verdict (plan WP-LI2).

    ``probe_transcripts`` is the full, ordered probe record -- one entry per
    attempted probe: ``{"probe": "defeq"|"iff"|"compile", "rung": str|None,
    "lean_text": str, "ok": bool|None, "detail": str}`` (``ok=None`` on a
    deferred probe that never ran).  ``lean_toolchain_hash`` is the pinned
    toolchain identity the probes ran under (``common.lean_toolchain_hash``),
    or ``None`` when the verdict is ``deferred`` (no probe ran; claiming a
    toolchain identity would be a false record).  ``closed_by`` names the
    ladder rung that closed a ``proved`` verdict (extension field; ``"defeq"``
    for the fast path, ``None`` otherwise)."""
    verdict: str
    probe_transcripts: list
    statement_hash_original: str
    statement_hash_compiled: str
    lean_toolchain_hash: object = None     # str | None
    closed_by: object = None               # str | None


# ============================================================ probe builders
# Pure, deterministic text functions (Lean-free-testable; golden-string
# pinned by tests/test_import_rt.py).
def compiled_prop(lean_text: str) -> str:
    """Extract ``<prop>`` from the canonical compiled emission
    ``theorem <thm> : <prop> := sorry`` (generators/math_compile.py's frozen
    byte-stable form).  Raises ``ValueError`` on any other shape -- post-gate
    this is an internal invariant violation, surfaced rather than mis-probed."""
    suffix = " := sorry"
    if not lean_text.startswith("theorem ") or not lean_text.endswith(suffix):
        raise ValueError(
            f"not a canonical compiled statement: {lean_text[:80]!r}")
    _head, sep, prop = lean_text[:-len(suffix)].partition(" : ")
    if not sep:
        raise ValueError(f"no ' : ' in compiled statement: {lean_text[:80]!r}")
    if not prop:
        raise ValueError(f"empty prop in compiled statement: {lean_text[:80]!r}")
    return prop


def _bounded(body: str) -> str:
    """Wrap one probe command under the pinned heartbeat cap (⚠D7: the same
    lexically-whitelisted ``set_option`` the eval_props ladder uses; the
    sandbox wall-clock/rlimit stays the authoritative bound)."""
    return (f"set_option maxHeartbeats {common.LEAN_MAXHEARTBEATS} in\n"
            f"{body}\n")


def defeq_probe_text(decl_name: str, c_prop: str) -> str:
    """The FAST-PATH probe: the original declaration used as a proof of the
    compiled statement.  ``@`` makes every implicit argument/universe of the
    original explicit, matching the compiler's fully-explicit binder emission
    (the ``pp_roundtrip`` step-3 argument-handling pattern).  Typechecks IFF
    ``C`` is definitionally the original's type."""
    return _bounded(f"example : {c_prop} := @{decl_name}")


def iff_probe_text(c_prop: str, o_prop: str, rung: str) -> str:
    """One equivalence-probe rung: ``(C) ↔ (O)`` closed by ``rung`` (a member
    of the frozen ``IFF_LADDER``).  ``o_prop`` is the declaration's original
    pretty-printed statement (the WP-LI0 queue's ``statement_pp``)."""
    if rung not in IFF_LADDER:
        raise ValueError(f"rung {rung!r} is not in the frozen IFF_LADDER")
    return _bounded(f"example : ({c_prop}) ↔ ({o_prop}) := {rung}")


# ============================================================ default runner
class _LeanElaborateRunner:
    """The default probe runner: ``LeanBackend.elaborate`` -- the EXISTING
    F0.5 sandbox/env code path (jail, mounts, escape gate, pinned imports),
    never new subprocess plumbing.  One backend per batch; callable with the
    injected-runner signature ``runner(probe_text) -> {"ok", "unavailable",
    "detail"}`` the tests fake."""

    def __init__(self):
        from kernel.backends import LeanBackend
        self._backend = LeanBackend()

    def __call__(self, probe_text: str) -> dict:
        res = self._backend.elaborate(probe_text, expect_sorry=False)
        return {"ok": bool(res.get("ok")),
                "unavailable": bool(res.get("unavailable")),
                "detail": (res.get("detail") or res.get("reason") or "")}


def _synthetic_source(doc: dict) -> str:
    """A source that satisfies the groundedness gate for ``doc`` (the
    run/anchor.py pattern): the compiled statement is independent of the
    source, so the probes are byte-identical to the real pipeline's."""
    return "  ".join(s.get("quote", "") for s in doc.get("statements", [])
                     if s.get("quote"))


def _parse_reading(reading, statement_pp: str):
    """Reading (dict or JSON string) -> MathReading.  The authored reading was
    grounded against the FORMAL pretty-printed statement (the import prompt's
    source, plan §2), so ``statement_pp`` is tried first; the synthetic
    quote-join source is the fallback (groundedness gates parse ACCEPTANCE
    only, never the compiled bytes)."""
    if isinstance(reading, str):
        doc = json.loads(reading)
    else:
        doc = reading
    reading_json = json.dumps(doc)
    try:
        return parse_math_reading(reading_json, statement_pp)
    except BadMathReading:
        return parse_math_reading(reading_json, _synthetic_source(doc))


# ================================================================== rt_check
def rt_check(decl_name, statement_pp, reading, *, runner=None,
             event_sink=None, statement_hash_original=None) -> RTResult:
    """Run the RT differential for ONE declaration (plan §2's RT(d)).

    ``reading`` is the authored MathReading (dict or JSON string -- the
    ``"reading"`` field of a persisted WP-LI1 reading artifact).  ``runner``
    is the probe executor (default: the sandboxed ``LeanBackend.elaborate``
    path); tests inject a deterministic fake with the same signature.
    ``statement_hash_original`` is the R1 anchor hash from the WP-LI0 queue;
    when absent it defaults to the sha256 of ``statement_pp`` bytes (recorded,
    deterministic -- never invented).

    Verdict mapping (frozen): defeq-probe pass -> ``defeq``; else first
    ``IFF_LADDER`` rung that passes -> ``proved``; every probe fails ->
    ``failed`` (+ one first-class ``rt-differential-failure`` event through
    ``event_sink``); Lean absent / runner-unavailable -> ``deferred`` (honest,
    never a failure)."""
    if statement_hash_original is None:
        statement_hash_original = common.sha256_bytes(
            str(statement_pp).encode("utf-8"))
    transcripts = []

    # ---- compile C (Lean-free, deterministic) ------------------------------
    try:
        parsed = _parse_reading(reading, statement_pp)
        compiled = compile_math_reading(parsed)
        c_prop = compiled_prop(compiled["lean_text"])
        statement_hash_compiled = compiled["statement_hash"]
    except (BadMathReading, CompileError, ValueError, KeyError, TypeError) as e:
        # An authored row whose reading no longer parses/compiles cannot be
        # RT-certified: an honest refusal with the transcript (never silent).
        transcripts.append({"probe": "compile", "rung": None, "lean_text": "",
                            "ok": False,
                            "detail": f"reading does not compile: {e}"[:1500]})
        result = RTResult(verdict="failed", probe_transcripts=transcripts,
                          statement_hash_original=statement_hash_original,
                          statement_hash_compiled="",
                          lean_toolchain_hash=None, closed_by=None)
        _emit_failure_event(event_sink, decl_name, result)
        return result

    probes = [("defeq", None, defeq_probe_text(decl_name, c_prop))]
    for rung in IFF_LADDER:
        probes.append(("iff", rung, iff_probe_text(c_prop, statement_pp, rung)))

    # ---- honest deferral (the statement-cert / anchor-runner discipline) ---
    if runner is None:
        if not common.lean_available():
            for kind, rung, text in probes:
                transcripts.append({"probe": kind, "rung": rung,
                                    "lean_text": text, "ok": None,
                                    "detail": "deferred: lean toolchain absent"})
            return RTResult(verdict="deferred", probe_transcripts=transcripts,
                            statement_hash_original=statement_hash_original,
                            statement_hash_compiled=statement_hash_compiled,
                            lean_toolchain_hash=None, closed_by=None)
        runner = _LeanElaborateRunner()

    # ---- run the probe sequence (defeq fast path, then the frozen ladder) --
    verdict, closed_by = "failed", None
    for kind, rung, text in probes:
        # Defense in depth: the F0.4 escape gate on OUR OWN probe emission,
        # exactly as elaborate() re-checks the compiler's output.  A refusal
        # is a recorded probe failure, never an exception.
        gate_ok, gate_reason = validate_lean(text)
        if not gate_ok:
            transcripts.append({"probe": kind, "rung": rung, "lean_text": text,
                                "ok": False,
                                "detail": f"escape-gate refusal: {gate_reason}"})
            continue
        res = runner(text)
        if res.get("unavailable"):
            # The toolchain vanished (or was absent behind an injected
            # runner): the remaining probes are recorded un-run and the
            # verdict is an honest deferral.
            transcripts.append({"probe": kind, "rung": rung, "lean_text": text,
                                "ok": None,
                                "detail": "deferred: lean toolchain absent"})
            return RTResult(verdict="deferred", probe_transcripts=transcripts,
                            statement_hash_original=statement_hash_original,
                            statement_hash_compiled=statement_hash_compiled,
                            lean_toolchain_hash=None, closed_by=None)
        ok = bool(res.get("ok"))
        detail = str(res.get("detail", ""))
        transcripts.append({"probe": kind, "rung": rung, "lean_text": text,
                            "ok": ok, "detail": detail[:1500]})
        if ok:
            verdict = "defeq" if kind == "defeq" else "proved"
            closed_by = "defeq" if kind == "defeq" else rung
            break
        # The ORIGINAL declaration is not nameable under the pinned import
        # surface (common.MATHLIB_IMPORTS): RT cannot test this row AT ALL --
        # "can't test" must never be conflated with "measured mistranslation"
        # (first observed live: numDerangements_one, whose original lives
        # outside the 6-module surface).  Recorded as ``out-of-surface``; the
        # row re-runs when the surface widens, and no failure event fires.
        if (kind == "defeq"
                and f"unknown identifier '{decl_name}'" in detail):
            verdict = "out-of-surface"
            break

    result = RTResult(verdict=verdict, probe_transcripts=transcripts,
                      statement_hash_original=statement_hash_original,
                      statement_hash_compiled=statement_hash_compiled,
                      lean_toolchain_hash=common.lean_toolchain_hash(),
                      closed_by=closed_by)
    if verdict == "failed":
        _emit_failure_event(event_sink, decl_name, result)
    return result


def _emit_failure_event(event_sink, decl_name, result: RTResult) -> None:
    """Log the both-probes-fail refusal as ONE first-class event carrying the
    FULL transcript (the disagreement-logging discipline: a fidelity-pass +
    RT-fail row is a measured mistranslation and must never be silently
    dropped).  Events-only -- no cert row, no reading row is touched."""
    if event_sink is None:
        return
    event_sink(EVENT_KIND, {
        "decl_name": decl_name,
        "channel": RT_CHANNEL,
        "verdict": "failed",
        "statement_hash_original": result.statement_hash_original,
        "statement_hash_compiled": result.statement_hash_compiled,
        "probe_transcripts": result.probe_transcripts,
        "note": ("measured mistranslation: the reading passed the Lean-free "
                 "fidelity gates (status=authored) but the compiled statement "
                 "is NOT provably equivalent to the original declaration -- "
                 "the most valuable failure class in the import operation "
                 "(plan WP-LI2)"),
    })


# ==================================================================== batch
def _load_jsonl(path) -> list:
    rows = []
    for line in common.read_text_auto(path).splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _reading_artifact_path(readings_dir, decl_name) -> pathlib.Path:
    """The WP-LI1 ``persist_reading`` filename convention (decl name with path
    separators flattened)."""
    fname = decl_name.replace(os.sep, "_").replace("/", "_") + ".json"
    return pathlib.Path(readings_dir) / fname


def _atomic_write(path: pathlib.Path, text: str) -> None:
    """temp + rename so a kill mid-write never leaves a torn report (the
    single-writer queue discipline)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _prior_rows(out_path: pathlib.Path) -> dict:
    """Resume state: {decl_name: row} for every prior-report row whose verdict
    is NOT ``deferred`` (deferred rows re-run once the toolchain is up; every
    other verdict is settled at the recorded toolchain identity).  A missing
    or unparseable prior report is a clean fresh start, never a crash."""
    if not out_path.exists():
        return {}
    try:
        report = json.loads(out_path.read_text(encoding="utf-8"))
        rows = report.get("rows", [])
    except (ValueError, OSError):
        return {}
    out = {}
    for r in rows:
        if isinstance(r, dict) and r.get("verdict") in RT_VERDICTS \
                and r.get("verdict") not in ("deferred", "out-of-surface") \
                and r.get("decl_name"):
            # deferred re-runs once the toolchain is up; out-of-surface
            # re-runs so a widened import surface picks the row up.
            out[r["decl_name"]] = r
    return out


def _row_from_result(decl_name, res: RTResult) -> dict:
    return {"decl_name": decl_name,
            "channel": RT_CHANNEL,
            "verdict": res.verdict,
            "closed_by": res.closed_by,
            "statement_hash_original": res.statement_hash_original,
            "statement_hash_compiled": res.statement_hash_compiled,
            "lean_toolchain_hash": res.lean_toolchain_hash,
            "probe_transcripts": res.probe_transcripts}


def rt_batch(queue_path, readings_dir, out_path=None, *, runner=None,
             event_sink=None, update_queue=False) -> dict:
    """Run the RT differential over every WP-LI0 queue row with status
    ``authored``; write the verdict report (byte-stable canonical JSON, rows
    sorted by ``decl_name``); return a summary dict.

    RESUMABLE: rows already in the report with a verdict other than
    ``deferred`` are skipped (their recorded rows are carried forward
    verbatim); ``deferred`` rows re-run.  DETERMINISTIC: output ordering is
    decl-name-sorted and the serialization carries no wall-clock, so two runs
    over the same inputs produce byte-identical reports.

    ``update_queue=True`` additionally flips FAILED rows to status
    ``refused`` in the queue file (plan WP-LI2: "``failed`` is a refusal") --
    atomically, single-writer.  Flipping ``authored`` -> ``imported`` is
    deliberately NOT done here: imported requires BOTH phases to agree
    (statement-cert AND RT, plan §3), which is the Phase-B driver's business.

    A queue row whose reading artifact is missing from ``readings_dir`` is
    recorded in ``summary.missing_readings`` (and retried next run) -- never
    silently skipped, never conflated with an RT failure."""
    queue_path = pathlib.Path(queue_path)
    out_path = pathlib.Path(out_path) if out_path else REPORT_PATH

    queue = _load_jsonl(queue_path)
    authored = sorted((r for r in queue if r.get("status") == "authored"),
                      key=lambda r: r.get("decl_name", ""))
    prior = _prior_rows(out_path)

    # One shared default runner per batch (the backend jail is per-call; the
    # object itself is stateless) -- constructed lazily only when a probe will
    # actually run.
    if runner is None and common.lean_available():
        runner = _LeanElaborateRunner()

    rows_by_decl = dict(prior)       # carried-forward settled verdicts
    n_resumed = 0
    n_checked = 0
    missing = []
    failed_decls = []
    for qrow in authored:
        decl = qrow.get("decl_name", "")
        if decl in prior:
            n_resumed += 1
            if prior[decl].get("verdict") == "failed":
                failed_decls.append(decl)
            continue
        rpath = _reading_artifact_path(readings_dir, decl)
        if not rpath.exists():
            missing.append(decl)
            continue
        doc = json.loads(rpath.read_text(encoding="utf-8"))
        res = rt_check(decl, qrow.get("statement_pp", ""), doc["reading"],
                       runner=runner, event_sink=event_sink,
                       statement_hash_original=qrow.get("statement_hash"))
        rows_by_decl[decl] = _row_from_result(decl, res)
        n_checked += 1
        if res.verdict == "failed":
            failed_decls.append(decl)

    rows = [rows_by_decl[d] for d in sorted(rows_by_decl)]
    by_verdict = {v: 0 for v in RT_VERDICTS}
    for r in rows:
        by_verdict[r["verdict"]] += 1

    report = {
        "schema": SCHEMA,
        "channel": RT_CHANNEL,
        "lean_available": bool(common.lean_available()),
        "evidence_note": ("probe passes are RUN-1 elaboration evidence inside "
                          "the F0.5 jail; the two-run L5 adjudication applies "
                          "at the Phase-B statement-cert mint, not here"),
        "rows": rows,
        "summary": {
            "n_rows": len(rows),
            "by_verdict": by_verdict,
            "missing_readings": sorted(missing),
        },
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(out_path, common.canonical_json(report) + "\n")

    if update_queue and failed_decls:
        failed_set = set(failed_decls)
        for qrow in queue:
            if qrow.get("decl_name") in failed_set \
                    and qrow.get("status") == "authored":
                qrow["status"] = "refused"
        _atomic_write(queue_path,
                      "".join(common.canonical_json(r) + "\n" for r in queue))

    return {"status": "completed",
            "out_path": str(out_path),
            "n_authored": len(authored),
            "n_checked": n_checked,
            "n_resumed": n_resumed,
            "by_verdict": by_verdict,
            "missing_readings": sorted(missing),
            "failed_decls": sorted(failed_decls),
            "lean_available": bool(common.lean_available())}


if __name__ == "__main__":                   # pragma: no cover
    import sys
    from buildloop import import_driver as _drv
    summary = rt_batch(
        sys.argv[1] if len(sys.argv) > 1 else _drv.QUEUE_PATH,
        sys.argv[2] if len(sys.argv) > 2 else _drv.READINGS_DIR,
        sys.argv[3] if len(sys.argv) > 3 else REPORT_PATH)
    print(json.dumps(summary, indent=2))
