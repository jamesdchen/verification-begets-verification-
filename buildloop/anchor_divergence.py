"""FI-KA-3 -- the anchor-divergence adjudicator (events-only, append-only).

This is the ``speculate.log_divergence`` precinct for the ∃-anchor channel: when
the verdict lattice (FI-KA-2) lands on ``divergent`` -- a T-a (in-bound-witness
contradiction) or T-b (decidable-instance mismatch) trigger fired -- exactly one
of enumerator / evaluator / kernel is wrong, and that fact is recorded here as a
COMMITTED artifact under ``results/anchor_divergences/`` AND (when a registry
handle is supplied) as one first-class ``anchor-divergence`` event.  It is the
mathematical sibling of the Z-D speculation ledger (``buildloop/speculate.py``,
``tests/test_divergence_ledger.py``) and inherits its two load-bearing
disciplines verbatim:

  * **Z1 (events-only, no laundering):** logging a divergence touches NONE of the
    four Combined-Loop tables -- it creates no certificate row and no readings
    row.  A divergence is a NEGATIVE fact; it is never dressed as a proof
    artifact.  The only side effects are the committed JSON file and (optionally)
    one event row of kind ``"anchor-divergence"``.
  * **no-auto-resolve (the three teeth):** ``resolution`` is ``null`` at write
    time and NO code path in the repo ever writes a non-null ``resolution`` --
    this module refuses to (``record_divergence`` raises on a non-null
    resolution, and a static grep test pins that no ``.py`` under
    ``kernel/ buildloop/ run/ generators/ tools/`` assigns the key non-null).
    Only a HUMAN commit editing the JSON (fields ``{by, date, verdict, note}``,
    the §7 auditor role) resolves a divergence.  There is no deletion API:
    recomputation can ADD artifacts, never subtract them, and an existing file is
    never overwritten (a new divergence for the same subject increments ``n``).

While an unresolved artifact exists for a subject, ``unresolved_divergence``
returns it and ``assert_no_unresolved`` RAISES -- the seam the lattice/runner
consume to force ``divergent`` and to refuse minting any anchor cert for that
subject (the divergence check runs BEFORE mint, so the block is
order-independent).

Canonical JSON, byte-deterministic: **no wall-clock field lives in the artifact
body** (E6-adjacent -- git history carries the time; the registry event row
carries its own ``at`` column, which is registry metadata, not the divergence
body).  Deterministic, LLM-free, Lean-free.
"""
from __future__ import annotations

import json
import pathlib

import common

_ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS_DIR = _ROOT / "results" / "anchor_divergences"

# The frozen schema tag (FI-KA-3).
SCHEMA = "anchor-divergence/v1"

# The TWO trigger names -- exactly the FI-KA-2 divergence triggers T-a / T-b.
# Nothing else may name a divergence; an unknown trigger is rejected (mirrors the
# Z-D ledger's `direction not in DIVERGENCE_DIRECTIONS` discipline).
TRIGGERS = ("in-bound-witness-contradiction", "decidable-instance-mismatch")

# The first-class event kind (Z1: events-only, never a cert/reading row).
EVENT_KIND = "anchor-divergence"

# The data keys the caller must supply; `schema` and `resolution` are
# writer-controlled frozen invariants and must NOT be forged by the caller.
_REQUIRED_DATA_KEYS = (
    "subject_hash", "source_id", "trigger", "shadow", "kernel",
    "template", "witness_eval", "identity",
)

# Wall-clock-shaped keys that must never enter the artifact BODY (E6 hygiene;
# the byte-determinism tooth is the real enforcer, this is belt-and-suspenders).
_FORBIDDEN_BODY_KEYS = frozenset({
    "created_at", "timestamp", "wall_ms", "wall_clock", "now_iso", "at", "time",
})


class UnresolvedDivergenceError(Exception):
    """Raised by ``assert_no_unresolved`` (the mint-guard) when an unresolved
    anchor-divergence artifact exists for a subject.  The runner calls the guard
    BEFORE minting, so an anchor cert can never be issued over an open
    divergence -- regardless of the order in which the cert attempt and the
    divergence record happened."""


def _subject_prefix(subject_hash: str) -> str:
    """The ``<subject_hash[:16]>`` filename stem shared by every divergence
    artifact for one subject (the RAW compiled-statement sha256)."""
    if not isinstance(subject_hash, str) or not subject_hash:
        raise ValueError(f"subject_hash must be a non-empty str, got {subject_hash!r}")
    return subject_hash[:16]


def _canonical_body(payload: dict) -> dict:
    """Build the frozen ``anchor-divergence/v1`` body from a caller payload,
    ENFORCING the schema invariants.  Raises ``ValueError`` on any violation and
    returns a dict; the writer never persists a body that fails here."""
    if not isinstance(payload, dict):
        raise ValueError(f"payload must be a dict, got {type(payload).__name__}")

    # The caller must supply every data key -- the schema has teeth.
    missing = [k for k in _REQUIRED_DATA_KEYS if k not in payload]
    if missing:
        raise ValueError(
            f"anchor-divergence payload is missing required key(s): {missing}")

    # `schema` is writer-controlled: absent is fine, a conflicting value is not.
    if payload.get("schema", SCHEMA) != SCHEMA:
        raise ValueError(
            f"schema must be {SCHEMA!r} (got {payload.get('schema')!r}); the "
            f"schema tag is frozen and writer-controlled")

    # `trigger` must be one of the two frozen names (T-a / T-b).
    trigger = payload["trigger"]
    if trigger not in TRIGGERS:
        raise ValueError(
            f"trigger {trigger!r} must be one of {TRIGGERS} "
            f"(the two FI-KA-2 divergence triggers)")

    # `resolution` is null AT WRITE TIME, by construction: the writer NEVER
    # persists a non-null resolution.  Only a human commit editing the JSON
    # resolves a divergence (no-auto-resolve tooth 1).
    if payload.get("resolution", None) is not None:
        raise ValueError(
            "resolution must be null at write time -- no code path may write a "
            "non-null resolution; only a human commit editing the artifact "
            "resolves a divergence (fields {by, date, verdict, note})")

    body = dict(payload)
    body["schema"] = SCHEMA
    body["resolution"] = None

    # No wall-clock in the body (E6): git history carries the time.
    _assert_no_wall_clock(body)
    return body


def _assert_no_wall_clock(obj, *, _path="body") -> None:
    """Recursively refuse any wall-clock-shaped key anywhere in the body."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in _FORBIDDEN_BODY_KEYS:
                raise ValueError(
                    f"wall-clock-shaped key {k!r} at {_path} is forbidden in the "
                    f"anchor-divergence body (E6: git history carries the time)")
            _assert_no_wall_clock(v, _path=f"{_path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            _assert_no_wall_clock(v, _path=f"{_path}[{i}]")


def _next_index(subject_hash: str, out_dir: pathlib.Path) -> int:
    """The next append-only ``n`` for a subject: ``max(existing) + 1`` (0 when
    none).  APPEND-ONLY: existing artifacts are never overwritten or deleted."""
    prefix = _subject_prefix(subject_hash)
    n = -1
    if out_dir.is_dir():
        for p in out_dir.glob(f"{prefix}-*.json"):
            stem = p.stem  # "<prefix>-<n>"
            suffix = stem[len(prefix) + 1:]
            if suffix.isdigit():
                n = max(n, int(suffix))
    return n + 1


def record_divergence(payload: dict, *, out_dir=RESULTS_DIR, registry=None) -> pathlib.Path:
    """Record ONE anchor divergence: write an append-only committed artifact and,
    when a ``registry`` handle is supplied, log ONE first-class
    ``anchor-divergence`` event (events-only, Z1 -- no cert row, no readings row).

    Writes ``<out_dir>/<subject_hash[:16]>-<n>.json`` with canonical, byte-
    deterministic JSON.  An existing file is NEVER overwritten; a new divergence
    for the same subject increments ``n``.  Returns the artifact ``Path``.

    The payload must carry every data key of the frozen ``anchor-divergence/v1``
    schema (``subject_hash, source_id, trigger, shadow, kernel, template,
    witness_eval, identity``); ``schema`` and ``resolution`` are writer-controlled
    and frozen (``resolution`` is ``null`` at write -- a non-null resolution is
    refused).  Raises ``ValueError`` on any schema violation, writing nothing."""
    body = _canonical_body(payload)
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    n = _next_index(body["subject_hash"], out_dir)
    path = out_dir / f"{_subject_prefix(body['subject_hash'])}-{n}.json"
    if path.exists():  # append-only invariant: never clobber an existing artifact
        raise FileExistsError(
            f"refusing to overwrite existing divergence artifact {path} "
            f"(append-only: recomputation adds, never subtracts)")

    # Canonical, byte-deterministic bytes (no wall-clock in the body).
    path.write_text(common.canonical_json(body) + "\n")

    # Z1: events-only.  One first-class event; no certificate, no readings row.
    if registry is not None:
        registry.log_event(EVENT_KIND, body)
    return path


def unresolved_divergence(subject_hash: str, *, out_dir=RESULTS_DIR) -> dict | None:
    """Return the earliest UNRESOLVED (``resolution is None``) divergence body for
    a subject, or ``None`` when none exists (no artifacts, or every artifact has
    been resolved by a human commit).  This is the seam the lattice/runner consume
    to force ``divergent`` and to gate minting."""
    prefix = _subject_prefix(subject_hash)
    out_dir = pathlib.Path(out_dir)
    if not out_dir.is_dir():
        return None
    candidates = []
    for p in out_dir.glob(f"{prefix}-*.json"):
        suffix = p.stem[len(prefix) + 1:]
        if not suffix.isdigit():
            continue
        candidates.append((int(suffix), p))
    for _n, p in sorted(candidates):
        body = json.loads(p.read_text())
        if body.get("resolution", None) is None:
            return body
    return None


def assert_no_unresolved(subject_hash: str, *, out_dir=RESULTS_DIR) -> None:
    """The MINT-GUARD (no-auto-resolve tooth 2): raise
    ``UnresolvedDivergenceError`` iff an unresolved divergence artifact exists for
    ``subject_hash``.  The runner calls this BEFORE minting any anchor cert, so
    the block is order-independent -- a divergence recorded after a cert attempt
    still blocks the next mint.  There is deliberately NO deletion API and no
    auto-resolve: only a human commit editing the JSON releases the guard."""
    body = unresolved_divergence(subject_hash, out_dir=out_dir)
    if body is not None:
        raise UnresolvedDivergenceError(
            f"unresolved anchor divergence exists for subject "
            f"{subject_hash[:16]!r} (trigger={body.get('trigger')!r}); refusing "
            f"to mint -- a human must resolve the committed artifact first")
