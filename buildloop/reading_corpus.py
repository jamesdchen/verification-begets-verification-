"""The file->table BRIDGE for the hand-authored reading corpus.

A READING (generators/reading.py) is the semantic analysis of a request.  The
corpus under specs/readings/ is a set of hand-authored, ALREADY-GROUNDED
readings, one per file, that seed the demand ledger and anchor the reading
tests.  This module is the ONE bridge that turns those files into in-memory
rows; nothing here talks to the LLM and nothing here talks to the registry.

Why a bridge, and where the two sides live:

  * The FILES (specs/readings/*.json) plus THIS loader are the AUTHORING /
    SEEDING / TESTING side.  Tests parse every committed reading to prove it is
    grounded and structurally valid, and the seed step reads these files once to
    populate the demand ledger (provenance is derived at seed time from that
    ledger, NOT from the file -- so a corpus file carries no "source" key).

  * RUNTIME consumers never read these files.  They read the registry snapshot,
    which is the durable table the seed step wrote.  Keeping the loader out of
    the registry (house rule 9) is what makes this a bridge rather than a second
    source of truth: the files feed the table once, and the table is read
    thereafter.

Determinism: files are processed in sorted order and parsing is pure JSON; there
is no randomness, no clock, and no network.  The loader depends only on the
standard library (json / pathlib / dataclasses).
"""
from __future__ import annotations

import dataclasses
import json
import pathlib


@dataclasses.dataclass
class CorpusEntry:
    """One hand-authored reading, as loaded from a specs/readings/*.json file.

    This is deliberately NOT generators.reading.Reading: it is the raw bridge
    row, before any groundedness gate runs.  ``source`` holds the file's RAW
    JSON text (not a path), so a consumer can recover the full file object --
    including the service name and the request -- with json.loads(entry.source).
    """
    request: str
    statements: list
    source: str


def load_readings(dir_path) -> list[CorpusEntry]:
    """Load every ``*.json`` reading file in ``dir_path`` into a CorpusEntry.

    Files are read in sorted (filename) order for determinism.  Non-``.json``
    files are skipped.  Each file is expected to be
    ``{"request": <str>, "reading": {"service": <str>, "statements": [...]}}``;
    the returned CorpusEntry keeps ``request`` and the reading's ``statements``,
    and stashes the file's RAW TEXT in ``source`` so callers can round-trip back
    to the original object (and recover the service name).
    """
    directory = pathlib.Path(dir_path)
    entries: list[CorpusEntry] = []
    for path in sorted(directory.glob("*.json")):
        if not path.is_file():
            continue
        raw = path.read_text()
        obj = json.loads(raw)
        entries.append(CorpusEntry(
            request=obj["request"],
            statements=obj["reading"]["statements"],
            source=raw,
        ))
    return entries
