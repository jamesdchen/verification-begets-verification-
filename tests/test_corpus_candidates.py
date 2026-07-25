"""Teeth for tools/corpus_candidates.py -- the pre-declared corpus registry.

This selector exists to let an unattended cycle walk PLAN_FRAGMENT §3.2
path (c) WITHOUT ever choosing a corpus for what the intake would buy.  The
whole safety property is therefore negative -- what the selector must not be
able to see -- so the load-bearing tooth here is a SOURCE INSPECTION: if this
module ever learns to read the portfolio reading, the intake window or the
purchase queue, it could rank candidates by yield, and ordering by yield is
the shopping the honesty rules forbid.  A behavioural test cannot catch that
(a yield-ranked selector still returns a row); reading the source can.

The rest pin the evidence discipline: every declared row states WHY and WHO
(the park-ledger REASONS idiom -- a row with no stated reason is an
unexplained fetch), the status vocabulary is closed, an outcome FLIPS a row
rather than deleting it, and every no-selection path answers with a NAMED
reason instead of raising.  Stdlib + repo files only; no network.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import corpus_candidates as cc  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "tools", "corpus_candidates.py")


def _committed() -> dict:
    with open(cc.REGISTRY, encoding="utf-8") as fh:
        return json.load(fh)


def _write(tmp_path, rows, **extra) -> str:
    doc = {"candidates": list(rows), "schema": "corpus-candidates/1"}
    doc.update(extra)
    path = str(tmp_path / "corpus_candidates.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    return path


def _row(name, status="candidate", **over) -> dict:
    row = {"adapter": "blueprint", "declared_by": "a test", "name": name,
           "project": "p", "rationale": "near the fragment because reasons",
           "source": f"https://example.org/{name}/", "status": status}
    row.update(over)
    return row


# --------------------------------------------------------------------------
# THE LOAD-BEARING TOOTH: yield-blindness, stated mechanically.
# --------------------------------------------------------------------------

#: Spellings of every artifact that could tell this module what an intake
#: would BUY, plus the ways it could go and find out for itself.  The list is
#: deliberately dumb and substring-matched: a selector that needs one of these
#: words is a selector that could rank by outcome, and the prose in this
#: module is written to avoid them precisely so the tooth can stay dumb.
YIELD_SHAPED_TOKENS = (
    "census",              # the portfolio reading and its per-corpus reports
    "frontier",            # the intake window and the purchase queue
    "supply_status",       # the derived supply verdict
    "attempt-candidate",   # the reading's own verdict vocabulary
    "results/",            # every derived artifact lives here
    "purchase",
)

#: A selector that fetched anything could also measure it.  Path (c) is
#: network-at-intake only, and the network belongs to tools/intake_corpus.py.
REACHES_OUT_TOKENS = ("urllib", "socket", "requests", "subprocess", "http.client")


def test_the_selector_never_reads_a_yield_shaped_artifact():
    src = open(SOURCE, encoding="utf-8").read().lower()
    for token in YIELD_SHAPED_TOKENS:
        assert token not in src, (
            f"tools/corpus_candidates.py names {token!r}: the selection must "
            "be order-based and blind to what an intake would buy -- reading "
            "any of these lets it rank by yield, which is shopping")


def test_the_selector_opens_no_socket_and_shells_out_to_nothing():
    src = open(SOURCE, encoding="utf-8").read().lower()
    for token in REACHES_OUT_TOKENS:
        assert token not in src, f"selector reaches out via {token!r}"


def test_the_selector_reads_exactly_one_file(tmp_path):
    """Stated as a behaviour too: point it at a registry alone in an empty
    directory and it still answers.  Nothing else in the tree is consulted,
    so nothing else in the tree can steer the choice."""
    path = _write(tmp_path, [_row("only")])
    assert cc.next_candidate(path)["name"] == "only"
    assert sorted(os.listdir(str(tmp_path))) == ["corpus_candidates.json"]


# --------------------------------------------------------------------------
# Selection: deterministic, order-based, and nothing else.
# --------------------------------------------------------------------------

def test_selection_is_the_first_candidate_in_declaration_order(tmp_path):
    path = _write(tmp_path, [_row("first"), _row("second")])
    assert cc.next_candidate(path)["name"] == "first"


def test_selection_skips_spent_rows_but_keeps_declaration_order(tmp_path):
    path = _write(tmp_path, [_row("a", "intaken"), _row("b", "refused",
                                                        refused_reason="r"),
                             _row("c"), _row("d")])
    assert cc.next_candidate(path)["name"] == "c"


def test_selection_skips_the_documentation_row(tmp_path):
    """The example row carries a deliberately non-real URL.  Selecting it
    would send an unattended cycle to fetch a URL nobody declared."""
    path = _write(tmp_path, [_row("example_corpus", "example"), _row("real")])
    assert cc.next_candidate(path)["name"] == "real"


def test_selection_is_deterministic_across_calls(tmp_path):
    path = _write(tmp_path, [_row("x"), _row("y"), _row("z")])
    picks = {json.dumps(cc.next_candidate(path), sort_keys=True)
             for _ in range(5)}
    assert len(picks) == 1


def test_selection_ignores_row_content_other_than_status_order(tmp_path):
    """A longer rationale, a fancier project line, an alphabetically earlier
    name: none of it promotes a row.  Order is the maintainer's priority."""
    path = _write(tmp_path, [
        _row("zzz", rationale="short"),
        _row("aaa", rationale="a very much longer and more persuasive case "
                              "for this corpus " * 5)])
    assert cc.next_candidate(path)["name"] == "zzz"


# --------------------------------------------------------------------------
# No selection is an ANSWER: every empty path names its reason.
# --------------------------------------------------------------------------

def test_absent_registry_names_a_reason_and_never_crashes(tmp_path):
    sel = cc.select(str(tmp_path / "nope.json"))
    assert sel["reason"] == "registry-absent"
    assert sel["selected"] is None


def test_empty_registry_names_a_reason(tmp_path):
    sel = cc.select(_write(tmp_path, []))
    assert sel["reason"] == "registry-empty"
    assert sel["selected"] is None


def test_exhausted_registry_is_distinct_from_an_empty_one(tmp_path):
    """Three different maintainer actions must not collapse into one word:
    a missing file is a tree problem, an empty file is a loop nobody has
    turned on, an exhausted one is a loop that ran out."""
    sel = cc.select(_write(tmp_path, [_row("a", "intaken")]))
    assert sel["reason"] == "registry-exhausted"
    assert sel["selected"] is None


def test_unparseable_registry_is_unreadable_not_empty(tmp_path):
    path = str(tmp_path / "corpus_candidates.json")
    open(path, "w").write("{ not json")
    sel = cc.select(path)
    assert sel["reason"] == "registry-unreadable"
    assert sel["selected"] is None


def test_every_reason_is_in_the_declared_vocabulary(tmp_path):
    paths = [str(tmp_path / "nope.json"), _write(tmp_path, []),
             _write(tmp_path, [_row("a")])]
    for path in paths:
        assert cc.select(path)["reason"] in cc.REASONS


def test_every_reason_names_what_would_change_it():
    for reason, text in cc.REASONS.items():
        assert text.strip(), f"{reason}: unexplained reason"


# --------------------------------------------------------------------------
# Evidence discipline: WHY and WHO are mandatory; outcomes flip, never delete.
# --------------------------------------------------------------------------

def test_status_vocabulary_is_closed_and_pinned():
    assert set(cc.STATUSES) == {"candidate", "example", "intaken", "refused"}
    assert set(cc.TERMINAL_STATUSES) == {"intaken", "refused"}


def test_committed_rows_declare_a_status_in_the_vocabulary():
    for row in _committed()["candidates"]:
        assert row["status"] in cc.STATUSES, row


def test_committed_rows_all_carry_a_rationale_and_a_declared_by():
    """The park-ledger REASONS idiom, applied to intake: a candidate with no
    stated reason is an unexplained fetch, and one with no provenance is an
    anonymous one."""
    for row in _committed()["candidates"]:
        for field in ("declared_by", "rationale"):
            assert str(row.get(field, "")).strip(), \
                f"{row.get('name')}: empty {field}"


def test_committed_rows_carry_every_required_field():
    for row in _committed()["candidates"]:
        for field in cc.REQUIRED_FIELDS:
            assert str(row.get(field, "")).strip(), \
                f"{row.get('name')}: missing {field}"
        assert row["adapter"] in cc.ADAPTERS


def test_committed_row_names_are_unique():
    names = [r["name"] for r in _committed()["candidates"]]
    assert len(names) == len(set(names))


def test_a_refused_row_states_its_reason():
    for row in _committed()["candidates"]:
        if row["status"] == "refused":
            assert str(row.get("refused_reason", "")).strip(), \
                f"{row['name']}: refused with no reason is not a measurement"


def test_intaking_flips_the_status_and_keeps_the_row(tmp_path):
    """Evidence, not inventory.  The row that fed an intake stays declared,
    in place, so a later reader can see what the loop consumed and why."""
    path = _write(tmp_path, [_row("a"), _row("b")])
    before = json.load(open(path))["candidates"]
    cc.mark("a", "intaken", path=path)
    after = json.load(open(path))["candidates"]
    assert [r["name"] for r in after] == [r["name"] for r in before]
    assert after[0]["status"] == "intaken"
    assert after[0]["rationale"] == before[0]["rationale"]
    assert cc.next_candidate(path)["name"] == "b"


def test_refusing_flips_the_status_and_records_the_reason(tmp_path):
    path = _write(tmp_path, [_row("a")])
    cc.mark("a", "refused", reason="fetch refused: host not allowlisted",
            path=path)
    row = json.load(open(path))["candidates"][0]
    assert row["status"] == "refused"
    assert "not allowlisted" in row["refused_reason"]
    assert cc.select(path)["reason"] == "registry-exhausted"


def test_a_refusal_without_a_reason_is_rejected(tmp_path):
    path = _write(tmp_path, [_row("a")])
    with pytest.raises(SystemExit):
        cc.mark("a", "refused", path=path)
    assert json.load(open(path))["candidates"][0]["status"] == "candidate"


def test_a_cycle_cannot_write_a_declaration(tmp_path):
    """Only a human declares.  A driver records outcomes."""
    path = _write(tmp_path, [_row("a", "intaken")])
    for status in ("candidate", "example", "purchased"):
        with pytest.raises(SystemExit):
            cc.mark("a", status, path=path)


def test_the_documentation_row_is_never_marked(tmp_path):
    path = _write(tmp_path, [_row("example_corpus", "example")])
    with pytest.raises(SystemExit):
        cc.mark("example_corpus", "intaken", path=path)


def test_marking_an_undeclared_name_is_refused(tmp_path):
    path = _write(tmp_path, [_row("a")])
    with pytest.raises(SystemExit):
        cc.mark("ghost", "intaken", path=path)


def test_a_write_round_trips_the_committed_registry_byte_identically(tmp_path):
    """The registry is hand-edited AND tool-written; if those two forms
    disagree, every recorded outcome shows up as a whole-file diff."""
    with open(cc.REGISTRY, "rb") as fh:
        before = fh.read()
    scratch = str(tmp_path / "corpus_candidates.json")
    with open(scratch, "wb") as fh:
        fh.write(before)
    cc._write(cc.load(scratch), scratch)
    with open(scratch, "rb") as fh:
        assert fh.read() == before


# --------------------------------------------------------------------------
# The command the unattended path runs, and the seeding evidence behind it.
# --------------------------------------------------------------------------

def test_the_intake_command_is_built_from_the_row_never_composed(tmp_path):
    row = _row("k", source="https://example.org/k/", adapter="sphinx")
    cmd = cc.intake_command(row)
    assert "tools/intake_corpus.py" in cmd
    assert "--source https://example.org/k/" in cmd
    assert "--adapter sphinx" in cmd
    assert "--name k" in cmd


def test_a_row_missing_a_field_cannot_produce_a_command():
    with pytest.raises(SystemExit):
        cc.intake_command(_row("k", rationale=""))


def test_an_unknown_adapter_cannot_produce_a_command():
    with pytest.raises(SystemExit):
        cc.intake_command(_row("k", adapter="pdf"))


def test_every_intaken_row_matches_a_committed_corpus_url():
    """The seeding evidence, checked rather than asserted: a row claiming an
    intake must point at the URL that corpus's own provenance recorded.  This
    is what stops a plausible-looking URL from entering the registry as
    history."""
    for row in _committed()["candidates"]:
        if row["status"] != "intaken":
            continue
        meta_path = os.path.join(ROOT, "specs", "mathsources", row["name"],
                                 "fetch_meta.json")
        assert os.path.isfile(meta_path), f"{row['name']}: no fetch_meta.json"
        meta = json.load(open(meta_path))
        assert meta["source"] == row["source"], \
            f"{row['name']}: registry URL disagrees with its fetch_meta"


def test_the_documentation_row_points_at_no_real_host():
    for row in _committed()["candidates"]:
        if row["status"] == "example":
            assert "example.org" in row["source"] or \
                   "example.com" in row["source"], \
                "the documentation row must carry a non-real URL"


def test_the_registry_says_where_the_judgment_lives():
    """The one prose invariant worth pinning: this file is the declaration
    point, and the shopping/selection distinction is written down in it."""
    note = _committed()["note"]
    blob = " ".join(str(v) for v in note.values()).lower()
    assert "shopping" in blob and "selection" in blob
    assert "per-candidate" in blob


def test_cli_prints_a_selection_or_a_named_reason(capsys, tmp_path):
    assert cc.main([]) == 0
    assert cc.REASONS[cc.select()["reason"]][:20] in capsys.readouterr().out
    assert cc.main(["--registry", _write(tmp_path, [_row("a")])]) == 0
    out = capsys.readouterr().out
    assert "SELECTED: a" in out and "DECLARATION ORDER" in out


def test_cli_json_mode_is_machine_readable(capsys, tmp_path):
    cc.main(["--json", "--registry", _write(tmp_path, [_row("a")])])
    doc = json.loads(capsys.readouterr().out)
    assert doc["selected"]["name"] == "a"
    assert doc["reason"] == "candidate-available"
