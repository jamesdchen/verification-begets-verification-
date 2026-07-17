#!/usr/bin/env python3
"""FI-KA-3 anchor-divergence adjudicator acceptance -- LLM-free, Lean-free, fast.

`buildloop.anchor_divergence.record_divergence(payload, *, out_dir, registry)`
records a lattice `divergent` verdict as (a) an append-only COMMITTED artifact
under `results/anchor_divergences/<subject_hash[:16]>-<n>.json` and (b) one
first-class `anchor-divergence` event.  These teeth prove:

  * ARTIFACT + CANONICAL BYTES -- the file lands under results/anchor_divergences/
    with byte-deterministic canonical JSON, `resolution` null, no wall-clock in
    the body; two writes of the same payload are byte-identical (sweep FI-KA-3.4).
  * APPEND-ONLY / NO DELETE -- an existing file is never overwritten; a same-
    subject divergence increments `n`; there is no deletion API and recomputation
    can only ADD (sweep FI-KA-3.2, no-auto-resolve tooth 3).
  * EVENTS-ONLY (Z1) -- a supplied registry gets exactly one `anchor-divergence`
    event and NO certificate row and NO readings row (the ledger template,
    `tests/test_divergence_ledger.py`).
  * FROZEN VOCABULARY -- `trigger` outside the two frozen names is rejected with a
    ValueError writing nothing; a non-null `resolution` at write is refused
    (no-auto-resolve tooth 1, the writer half).
  * THE MINT-GUARD SEAM -- while an unresolved artifact exists,
    `unresolved_divergence` returns it and `assert_no_unresolved` RAISES, in BOTH
    orders (divergence recorded after a cert attempt still blocks the next mint,
    no-auto-resolve tooth 2); a human-style resolution edit releases the guard.
  * STATIC NO-AUTO-RESOLVE GREP -- no `.py` under kernel/ buildloop/ run/
    generators/ tools/ assigns a non-null `resolution`; the grep is proven
    non-vacuous (it catches a planted non-null) and proven not to false-positive
    on the writer's own `resolution: None` (no-auto-resolve tooth 1, the pin).

Runnable under pytest AND as a bare script
(`python3 tests/test_anchor_divergence.py` -> PASS lines, exit 0).
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import tempfile

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))          # runnable as a bare script, not just -m pytest

from buildloop import anchor_divergence as ad
from library import Registry

# The two frozen trigger names (T-a / T-b) the module freezes.
_TRIGGERS = ad.TRIGGERS
assert len(_TRIGGERS) == 2, _TRIGGERS
_SCHEMA = ad.SCHEMA
assert _SCHEMA == "anchor-divergence/v1", _SCHEMA


def _fresh_registry():
    return Registry(db_path=tempfile.mkdtemp() + "/r.sqlite")


def _out_dir() -> pathlib.Path:
    return pathlib.Path(tempfile.mkdtemp()) / "anchor_divergences"


def _payload(subject_hash="a" * 64, source_id="43_larger_integer_exists",
             trigger=None):
    """A complete, schema-valid anchor-divergence payload (the source-43-shaped
    T-a fixture: kernel-proved template whose witness lies IN the bounded box --
    the shadow's exhaustive sweep should have found it, so something is wrong)."""
    return {
        "subject_hash": subject_hash,
        "source_id": source_id,
        "trigger": trigger or _TRIGGERS[0],
        "shadow": {"verdict": "refuted", "bound": 8,
                   "refuting_outer": {"n": 3}, "n_outer_admitted": 17},
        "kernel": {"verdict": "proved", "cert_id": "cert-abc",
                   "discharge": "omega", "transcript_tail": "..."},
        "template": {"m": {"op": "+", "args": [{"ref": "n"}, {"lit": 1}]}},
        "witness_eval": {"outer": {"n": 3},
                         "template_values": {"m": 4},
                         "in_bound": True, "conclusion_holds_eval": True},
        "identity": {"certs_version": 12, "rung": "exists-anchor/v1",
                     "toolchain_hash": "tc", "mathlib_commit": "mc",
                     "driver_hash": "dh", "emitter_hash": "eh"},
    }


# --------------------------------------------------------------------------- #
def test_artifact_lands_under_results_dir_with_canonical_bytes():
    """(1) record_divergence writes results/anchor_divergences/<sh16>-0.json with
    canonical JSON, schema stamped, resolution null, no wall-clock in the body."""
    out = _out_dir()
    p = ad.record_divergence(_payload(), out_dir=out)
    # under the frozen dir, named by the 16-char subject prefix and n=0
    assert p.parent == out, p
    assert p.name == ("a" * 16) + "-0.json", p.name
    raw = p.read_text()
    body = json.loads(raw)
    # canonical bytes: exactly common.canonical_json(body) + newline
    import common
    assert raw == common.canonical_json(body) + "\n", raw
    # frozen invariants
    assert body["schema"] == _SCHEMA, body
    assert body["resolution"] is None, body
    assert body["trigger"] in _TRIGGERS, body
    # no wall-clock field (as a JSON key) anywhere in the body
    for bad in ("created_at", "timestamp", "wall_ms", "at", "time", "now_iso"):
        assert f'"{bad}":' not in raw, (bad, raw)
    # the default out_dir constant points at the committed results tree
    assert ad.RESULTS_DIR == _ROOT / "results" / "anchor_divergences", ad.RESULTS_DIR


def test_two_writes_same_payload_are_byte_identical():
    """(2) Byte-determinism tooth (sweep FI-KA-3.4): writing the SAME payload
    twice yields byte-identical bodies (n increments, the body bytes do not)."""
    out = _out_dir()
    p0 = ad.record_divergence(_payload(), out_dir=out)
    p1 = ad.record_divergence(_payload(), out_dir=out)
    assert p0.name.endswith("-0.json") and p1.name.endswith("-1.json"), (p0, p1)
    assert p0.read_text() == p1.read_text(), (p0.read_text(), p1.read_text())


def test_append_only_never_overwrites_and_only_adds():
    """(3) Append-only / no-delete (tooth 3): a same-subject divergence increments
    n and leaves the earlier file byte-identical; recomputation can only ADD; the
    module exports no deletion API."""
    out = _out_dir()
    p0 = ad.record_divergence(_payload(), out_dir=out)
    first_bytes = p0.read_text()
    p1 = ad.record_divergence(_payload(), out_dir=out)
    p2 = ad.record_divergence(_payload(), out_dir=out)
    names = sorted(q.name for q in out.glob("*.json"))
    assert names == [("a" * 16) + f"-{i}.json" for i in range(3)], names
    # the earliest artifact is untouched by later recomputation
    assert p0.read_text() == first_bytes, p0.read_text()
    assert p0.exists() and p1.exists() and p2.exists()
    # NO deletion API is exported (recomputation adds, never subtracts)
    for banned in ("delete_divergence", "remove_divergence", "purge",
                   "delete", "unlink", "clear"):
        assert not hasattr(ad, banned), banned


def test_registry_event_is_events_only_no_cert_no_reading():
    """(4) Z1 (the ledger template): a supplied registry gets exactly ONE
    anchor-divergence event carrying the body; NO certificate row and NO readings
    row are created."""
    reg = _fresh_registry()
    out = _out_dir()
    ad.record_divergence(_payload(), out_dir=out, registry=reg)
    rows = reg.events(ad.EVENT_KIND)
    assert len(rows) == 1, rows
    assert rows[0]["kind"] == "anchor-divergence", rows[0]
    assert rows[0]["payload"]["schema"] == _SCHEMA, rows[0]
    assert rows[0]["payload"]["resolution"] is None, rows[0]
    # ...but events-only: no readings row and no certificate side effect
    assert reg.readings_all() == [], reg.readings_all()
    (cert_count,) = reg.db.execute(
        "SELECT COUNT(*) FROM certificates").fetchone()
    assert cert_count == 0, cert_count
    # no registry event => no file skipped: recording without a registry still
    # writes the committed artifact (registry is optional, artifact is not)
    out2 = _out_dir()
    p = ad.record_divergence(_payload(), out_dir=out2, registry=None)
    assert p.exists(), p


def test_unknown_trigger_rejected_and_writes_nothing():
    """(5a) Frozen vocabulary: a trigger outside the two names raises ValueError
    and writes no artifact (mirrors the Z-D bad-direction discipline)."""
    out = _out_dir()
    try:
        ad.record_divergence(_payload(trigger="not-a-real-trigger"), out_dir=out)
    except ValueError:
        pass
    else:
        raise AssertionError("an unknown trigger must be rejected with ValueError")
    assert list(out.glob("*.json")) == [] if out.is_dir() else True, list(out.glob("*.json"))


def test_non_null_resolution_at_write_is_refused():
    """(5b) No-auto-resolve tooth 1 (writer half): the writer refuses to persist a
    non-null resolution -- only a human commit editing the JSON resolves."""
    out = _out_dir()
    bad = _payload()
    bad["resolution"] = {"by": "someone", "date": "2026-07-17",
                         "verdict": "kernel-right", "note": "auto"}
    try:
        ad.record_divergence(bad, out_dir=out)
    except ValueError:
        pass
    else:
        raise AssertionError("a non-null resolution at write must be refused")
    assert list(out.glob("*.json")) == [] if out.is_dir() else True, list(out.glob("*.json"))


def test_missing_required_key_is_rejected():
    """(5c) The schema has teeth: a payload missing a required data key raises
    ValueError writing nothing."""
    out = _out_dir()
    for drop in ("subject_hash", "trigger", "shadow", "kernel", "template",
                 "witness_eval", "identity", "source_id"):
        pay = _payload()
        del pay[drop]
        try:
            ad.record_divergence(pay, out_dir=out)
        except ValueError:
            pass
        else:
            raise AssertionError(f"missing {drop!r} must raise ValueError")


def test_mint_guard_blocks_while_unresolved_both_orders():
    """(6) The mint-guard seam (no-auto-resolve tooth 2): while an unresolved
    artifact exists, unresolved_divergence returns it and assert_no_unresolved
    RAISES.  Proven order-independent: a divergence recorded AFTER a (simulated)
    cert attempt still blocks the NEXT mint.  A human-style resolution edit
    releases the guard."""
    out = _out_dir()
    sh = "b" * 64
    # before any divergence: lookup is None and the guard passes (mint allowed)
    assert ad.unresolved_divergence(sh, out_dir=out) is None
    ad.assert_no_unresolved(sh, out_dir=out)  # does not raise

    # ORDER A: divergence recorded, THEN a mint is attempted -> blocked
    ad.record_divergence(_payload(subject_hash=sh), out_dir=out)
    got = ad.unresolved_divergence(sh, out_dir=out)
    assert got is not None and got["subject_hash"] == sh, got
    _assert_guard_raises(sh, out)

    # ORDER B: a fresh subject where the "cert attempt" happens first (simulated
    # by minting nothing -- the guard is a pure function of committed state), then
    # the divergence is recorded AFTER: the next mint is still blocked.
    sh2 = "c" * 64
    ad.assert_no_unresolved(sh2, out_dir=out)          # cert attempt would pass here
    ad.record_divergence(_payload(subject_hash=sh2), out_dir=out)  # divergence lands after
    _assert_guard_raises(sh2, out)                     # the NEXT mint is blocked

    # a HUMAN resolution edit (the only release) clears the guard for sh
    p = sorted(out.glob(("b" * 16) + "-*.json"))[0]
    body = json.loads(p.read_text())
    body["resolution"] = {"by": "auditor", "date": "2026-07-17",
                          "verdict": "enumerator-bug-fixed", "note": "closed"}
    p.write_text(json.dumps(body))
    assert ad.unresolved_divergence(sh, out_dir=out) is None, "resolved => cleared"
    ad.assert_no_unresolved(sh, out_dir=out)           # guard released for sh
    # ...but sh2 remains blocked: resolving one subject never releases another
    _assert_guard_raises(sh2, out)


def _assert_guard_raises(subject_hash, out):
    try:
        ad.assert_no_unresolved(subject_hash, out_dir=out)
    except ad.UnresolvedDivergenceError:
        return
    raise AssertionError(
        f"assert_no_unresolved must raise while an unresolved artifact exists "
        f"for {subject_hash[:16]!r}")


def test_multiple_divergences_first_unresolved_wins_lookup():
    """(6b) With several same-subject artifacts, the lookup returns the earliest
    UNRESOLVED one; resolving it surfaces the next; resolving all clears."""
    out = _out_dir()
    sh = "d" * 64
    ad.record_divergence(_payload(subject_hash=sh), out_dir=out)  # -0
    ad.record_divergence(_payload(subject_hash=sh), out_dir=out)  # -1
    files = sorted(out.glob(("d" * 16) + "-*.json"))
    assert len(files) == 2, files
    # resolve -0 -> lookup should surface -1 (still unresolved)
    b0 = json.loads(files[0].read_text())
    b0["resolution"] = {"by": "a", "date": "2026-07-17", "verdict": "v", "note": "n"}
    files[0].write_text(json.dumps(b0))
    got = ad.unresolved_divergence(sh, out_dir=out)
    assert got is not None, got
    # resolve -1 too -> nothing unresolved remains
    b1 = json.loads(files[1].read_text())
    b1["resolution"] = {"by": "a", "date": "2026-07-17", "verdict": "v", "note": "n"}
    files[1].write_text(json.dumps(b1))
    assert ad.unresolved_divergence(sh, out_dir=out) is None


# --------------------------------------------------------------------------- #
# The static no-auto-resolve grep (no-auto-resolve tooth 1, the repo-wide pin).
_RESOLUTION_DIRS = ("kernel", "buildloop", "run", "generators", "tools")
# Match an assignment TO the `resolution` key/attr and capture the assigned value:
#   quoted dict/JSON key form:  "resolution": <value>   or  'resolution': <value>
#   subscript-assignment form:  x["resolution"] = <value>
#   attribute-assignment form:  obj.resolution = <value>
_RES_KV = re.compile(r"""["']resolution["']\s*:\s*([^\s,}\]]+)""")
_RES_SUB = re.compile(r"""\[\s*["']resolution["']\s*\]\s*=\s*([^\s,}\]]+)""")
_RES_ATTR = re.compile(r"""(?<![\w"'])\.?\bresolution\b\s*=\s*([^\s,}\]=][^\s,}\]]*)""")
# Values that are NULL (allowed): the writer's `resolution: None` and any JSON/
# docstring `resolution: null`.
_NULL_VALUES = {"None", "None,", "null", "null,", "None}", "null}"}


def _resolution_assignments(text: str):
    """Yield every captured RHS assigned to a `resolution` key/attr in `text`."""
    for m in _RES_KV.finditer(text):
        yield m.group(1)
    for m in _RES_SUB.finditer(text):
        yield m.group(1)
    # attribute form, but skip `==` comparisons (not assignments)
    for m in _RES_ATTR.finditer(text):
        val = m.group(1)
        if val.startswith("="):     # was `resolution ==` -> a comparison, skip
            continue
        yield val


def _is_null(value: str) -> bool:
    return value.rstrip(",}])") in {"None", "null"} or value in _NULL_VALUES


def test_static_no_code_writes_non_null_resolution():
    """(7) No-auto-resolve tooth 1: NO `.py` under kernel/ buildloop/ run/
    generators/ tools/ assigns a NON-null `resolution`.  Only a human commit
    editing the JSON resolves.  The writer's own `resolution: None` must PASS."""
    offenders = []
    scanned = 0
    for d in _RESOLUTION_DIRS:
        root = _ROOT / d
        if not root.is_dir():
            continue
        for py in root.rglob("*.py"):
            scanned += 1
            for val in _resolution_assignments(py.read_text()):
                if not _is_null(val):
                    offenders.append((str(py.relative_to(_ROOT)), val))
    assert scanned > 0, "the grep scanned no files -- vacuous"
    assert offenders == [], (
        "these .py files assign a non-null resolution (no-auto-resolve "
        "VIOLATION -- only a human commit may resolve): " + repr(offenders))


def test_static_grep_is_non_vacuous_and_passes_the_writer():
    """(7b) Prove the grep is not asleep: it CATCHES a planted non-null and does
    NOT false-positive on the writer's frozen `resolution: None`."""
    # catches a planted non-null (both key and subscript forms)
    assert not _is_null("\"resolved\""), "planted string value must be non-null"
    caught = list(_resolution_assignments('{"resolution": "resolved"}'))
    assert caught and not _is_null(caught[0]), caught
    caught_sub = list(_resolution_assignments('artifact["resolution"] = verdict'))
    assert caught_sub and not _is_null(caught_sub[0]), caught_sub
    # does NOT flag the writer's own `resolution: None` / a JSON `null`
    for benign in ('"resolution": None', "'resolution': None,",
                   '"resolution": null}', 'body["resolution"] = None'):
        vals = list(_resolution_assignments(benign))
        assert vals and all(_is_null(v) for v in vals), (benign, vals)
    # and the actual writer module passes the scan (it sets None only)
    writer = (_ROOT / "buildloop" / "anchor_divergence.py").read_text()
    for val in _resolution_assignments(writer):
        assert _is_null(val), ("writer sets a non-null resolution!", val)


if __name__ == "__main__":
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print("PASS", _name)
    print("anchor-divergence adjudicator holds "
          "(committed canonical artifact; byte-deterministic; append-only/no-delete; "
          "events-only -- no cert/reading; frozen trigger vocab; non-null resolution "
          "refused; mint-guard blocks unresolved in both orders; static no-auto-resolve "
          "grep non-vacuous)")
