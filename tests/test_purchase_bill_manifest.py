"""Teeth for the purchase-bill manifest narrower (tools/purchase_bill_manifest.py).

Pure-function coverage only -- the git plumbing is exercised by the CI job;
these teeth pin the judgment logic so it cannot drift silently."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

import purchase_bill_manifest as m  # noqa: E402


def test_ceremony_scope_allows_growth_protocol_only():
    ok, touched = m.ceremony_scope([
        "buildloop/growth_protocol.py", "specs/mathsources/registration.json",
        "results/p9_delta.md", "tests/test_operator_growth.py"])
    assert ok and touched == ["buildloop/growth_protocol.py"]


def test_ceremony_scope_rejects_other_ceremony_paths():
    for bad in ("kernel/certs.py", "TRUST.md", "setup.sh",
                "ci/Dockerfile", ".claude/hooks/x.sh",
                ".github/workflows/ci.yml"):
        ok, touched = m.ceremony_scope(["buildloop/growth_protocol.py", bad])
        assert not ok and bad in touched


def test_ceremony_scope_clean_diff_passes():
    ok, touched = m.ceremony_scope(["tools/frontier.py", "results/x.json"])
    assert ok and touched == []


ANTI_SRC = (
    "X = 1\n"
    "ANTI_LIST = (\n"
    '    "kernel checkers", "contract types", "escape-gate blocklist",\n'
    '    "primitive ladder rungs",\n'
    ")\n")


def test_anti_list_extraction_and_equality():
    assert m.extract_anti_list(ANTI_SRC) == (
        "kernel checkers", "contract types", "escape-gate blocklist",
        "primitive ladder rungs")
    grown = ANTI_SRC.replace('"primitive ladder rungs",',
                             '"primitive ladder rungs", "new root",')
    assert m.extract_anti_list(grown) != m.extract_anti_list(ANTI_SRC)


def test_anti_list_absent_is_failure_never_pass():
    try:
        m.extract_anti_list("Y = 2\n")
    except ValueError:
        return
    raise AssertionError("missing ANTI_LIST must raise, never pass")


def test_anti_list_extracts_from_the_real_file():
    root = os.path.join(os.path.dirname(__file__), "..")
    with open(os.path.join(root, "buildloop", "growth_protocol.py")) as fh:
        real = m.extract_anti_list(fh.read())
    assert "escape-gate blocklist" in real and len(real) >= 4


def test_delta_receipt_patterns():
    assert m.has_delta_receipt(["specs/mathsources/registration.json"])
    assert m.has_delta_receipt(["results/p1_delta.md"])
    assert m.has_delta_receipt(["results/p12_bigop_delta.md"])
    assert not m.has_delta_receipt(["results/c3_cycle_03.md", "tools/x.py"])


# =========================================================================== #
# The conforming-registry-diff predicate (check 4).
#
# The fixtures are built by SURGERY ON THE LIVE REGISTRY, not from a frozen
# copy: the predicate's whole claim is about the file as it actually is, and
# a snapshot fixture would keep testing a registry that no longer exists.
# Every hole the design review named gets a RED here; the two shapes the repo
# has actually shipped (P1's pure row, P2's row + sibling pins) get a GREEN.
# =========================================================================== #
ROOT = os.path.join(os.path.dirname(__file__), "..")
REGISTRY_PATH = os.path.join(ROOT, "buildloop", "growth_protocol.py")


def _base():
    with open(REGISTRY_PATH) as fh:
        return fh.read()


_DEMO_ROW = (
    '    "demo-node-class": {\n'
    '        "row": "generators.demo_growth.canonical_row",\n'
    '        "conserve": "(demo: expansion-eliminable by construction)",\n'
    '        "battery": "(demo differential battery)",\n'
    '        "price": "(census-priced: demo signal)",\n'
    '        "witnesses": "(literal bounds only)",\n'
    '        "persist": "(frozen in generators.demo_growth)",\n'
    '        "teeth": [["tests/test_purchase_bill_manifest.py",\n'
    '                   "demo-node-class"]],\n'
    '    },\n')


def _add_row(src, row_text=_DEMO_ROW):
    """Append a row to GROWERS the way a purchase does (inside the literal)."""
    head, sep, tail = src.partition("GROWERS = {\n")
    assert sep, "GROWERS literal not found in the live registry"
    return head + sep + row_text + tail


def _add_pin(src, key, sig):
    head, sep, tail = src.partition("SIGNATURE_PINS = {\n")
    assert sep, "SIGNATURE_PINS literal not found in the live registry"
    return head + sep + f'    "{key}": "{sig}",\n' + tail


def _drop_row(src, key):
    """Delete a whole GROWERS row textually (rows end on a lone `    },`)."""
    lines = src.splitlines(keepends=True)
    start = next(i for i, ln in enumerate(lines)
                 if ln.startswith(f'    "{key}": {{'))
    end = next(i for i in range(start, len(lines))
               if lines[i].rstrip("\n") == "    },")
    return "".join(lines[:start] + lines[end + 1:])


def _green(head_src, why=""):
    ok, notes = m.conforming_registry_diff(_base(), head_src)
    assert ok, f"{why}: expected conforming, got {notes}"
    return notes


def _red(head_src, why=""):
    ok, notes = m.conforming_registry_diff(_base(), head_src)
    assert not ok, f"{why}: expected NON-conforming, got {notes}"
    return notes


# ------------------------------------------------------------------ greens
def test_conforming_identity_diff():
    """No change at all is trivially conforming (the vacuous end of the
    predicate, pinned so a future refactor cannot make it accidentally red)."""
    _green(_base(), "identity")


def test_conforming_pure_growers_addition():
    _green(_add_row(_base()), "pure row addition")


def test_conforming_row_plus_matching_pin_addition():
    """The P2 3f826dd shape: a row plus signature pins in the row's own
    module, including a SIBLING checker no role references."""
    src = _add_pin(_add_row(_base()),
                   "generators.demo_growth.canonical_row", "(row: 'dict')")
    src = _add_pin(src, "generators.demo_growth._check_demo",
                   "(term, objects, in_bigop)")
    _green(src, "row + sibling pins")


def test_conforming_comment_block_beside_the_new_row():
    """Purchases document their rows in a comment block; the comment lives
    INSIDE the GROWERS literal, so the residue never sees it."""
    commented = ("    # PLAN_FRAGMENT S4 P9: a demo node class, commented\n"
                 "    # exactly as its neighbours are.\n") + _DEMO_ROW
    _green(_add_row(_base(), commented), "commented row")


def test_conforming_greens_name_what_they_verified():
    notes = _green(_add_row(_base()), "notes")
    blob = " ".join(notes)
    assert "residue" in blob and "GROWERS additive" in blob
    assert "ANTI_LIST" in blob and "role-complete" in blob


# -------------------------------------------------------------------- reds
def test_red_signature_pins_rewrite():
    """Editing an existing pin is how an interface change hides inside a
    purchase -- the pin is the fence, and moving a fence is not adding one."""
    src = _base().replace(
        '"buildloop.validate.validate_generator_spec": "(text: \'str\') -> \'dict\'"',
        '"buildloop.validate.validate_generator_spec": "(text) -> None"')
    assert src != _base(), "fixture did not apply"
    _red(src, "pin rewrite")


def test_red_growers_row_deletion():
    _red(_drop_row(_base(), "reading-macros"), "row deletion")


def test_red_growers_row_mutation():
    src = _base().replace(
        "(rung-free pin: empty registry => canon is identity)",
        "(rung-free pin: empty registry => canon is whatever)")
    assert src != _base(), "fixture did not apply"
    _red(src, "row mutation")


def test_red_conformance_gutting():
    """The registry's teeth live in conformance(); gutting it while adding a
    tidy row is the highest-value attack this predicate must refuse."""
    src = _base().replace(
        'raise KeyError(f"{grower_name}: role {role!r} unfilled")',
        "continue")
    assert src != _base(), "fixture did not apply"
    _red(_add_row(src), "conformance gutting")


def test_red_non_growers_addition():
    """Allowlisting a module in NON_GROWERS retires the completeness canary
    for it -- an exemption, never a row."""
    src = _base().replace(
        'NON_GROWERS = {\n',
        'NON_GROWERS = {\n    "generators/demo_growth.py": "trust me",\n')
    assert src != _base(), "fixture did not apply"
    _red(src, "NON_GROWERS addition")


def test_red_roles_edit():
    """Dropping a role from ROLES makes every row conformant by shrinking
    what conformance means."""
    src = _base().replace(
        'ROLES = ("row", "conserve", "battery", "price", "witnesses", '
        '"persist",\n         "teeth")',
        'ROLES = ("row", "conserve", "battery", "price", "witnesses",\n'
        '         "persist")')
    assert src != _base(), "fixture did not apply"
    _red(src, "ROLES edit")


def test_red_grower_smell_tuple_edit():
    """The completeness canary finds growers by smell; editing the smell
    tuples blinds it without touching a single row."""
    src = _base().replace('"def save_admitted"', '"def save_admitted_"')
    assert src != _base(), "fixture did not apply"
    _red(src, "smell tuple edit")


def test_red_anti_list_decoy_module_level_copy_plus_relocated_real_one():
    """The decoy the residue fence exists for: leave a BYTE-EQUAL ANTI_LIST
    at module level (so any anti-list-shaped check passes) and move the real
    one into a function.  No rule about anti-lists catches this; the residue
    does, because the relocation is source outside the two growable spans."""
    src = _base() + (
        "\n\ndef _live_anti_list():\n"
        '    ANTI_LIST = ("contract types",)\n'
        "    return ANTI_LIST\n")
    # the decoy really is byte-equal: the name-based extractor is fooled
    assert m.extract_anti_list(src) == m.extract_anti_list(_base())
    notes = _red(_add_row(src), "anti-list decoy")
    assert any("residue" in n and "CHANGED" in n for n in notes)


def test_red_smuggled_unrelated_pin():
    """A pin reaching into a module no new row lives in is an interface
    change wearing a purchase's coat."""
    src = _add_pin(_add_row(_base()), "kernel.certs.pin_hash", "(x) -> 'str'")
    notes = _red(src, "smuggled pin")
    assert any("kernel.certs.pin_hash" in n for n in notes)


def test_red_new_row_missing_a_role():
    src = _add_row(_base(), _DEMO_ROW.replace(
        '        "price": "(census-priced: demo signal)",\n', ""))
    _red(src, "role-incomplete row")


def test_red_new_row_with_empty_teeth():
    """A grower without planted violations is unguarded -- the static mirror
    of conformance()'s own refusal."""
    src = _add_row(_base(), _DEMO_ROW.replace(
        '        "teeth": [["tests/test_purchase_bill_manifest.py",\n'
        '                   "demo-node-class"]],\n',
        '        "teeth": [],\n'))
    _red(src, "toothless row")


def test_red_unparseable_head_is_a_named_false_never_a_crash():
    ok, notes = m.conforming_registry_diff(_base(), "GROWERS = {\n")
    assert not ok and notes and "head" in notes[0]
    ok, notes = m.conforming_registry_diff("X = 1\n", _base())
    assert not ok and notes and "base" in notes[0]


# --------------------------------------------- the shipped purchases, live
def test_the_real_p1_and_p2_purchases_are_conforming():
    """The two full-bill purchases this repo has actually shipped measure as
    conforming.  A predicate that reds the worked examples would be a
    predicate nobody could ever satisfy."""
    import subprocess

    def show(sha):
        r = subprocess.run(
            ["git", "show", f"{sha}:buildloop/growth_protocol.py"],
            capture_output=True, text=True, cwd=ROOT)
        return r.stdout if r.returncode == 0 else None

    checked = 0
    for sha in ("03e1a00", "3f826dd"):          # P1, P2
        base, head = show(sha + "^"), show(sha)
        if base is None or head is None:
            continue                            # shallow clone: not a failure
        ok, notes = m.conforming_registry_diff(base, head)
        assert ok, f"{sha} (a shipped purchase) measured non-conforming: {notes}"
        checked += 1
    assert checked, "neither shipped purchase was reachable from this clone"


def test_module_level_only_never_walks_into_a_function():
    """_module_assigns is deliberately not ast.walk: a same-named assignment
    inside a function is a different object, and treating it as the registry
    is the decoy above."""
    src = ("GROWERS = {}\nSIGNATURE_PINS = {}\n"
           "def f():\n    GROWERS = {'x': 1}\n    return GROWERS\n")
    residue, values = m._excise(src, m.GROWABLE_SPANS)
    assert values["GROWERS"] == {}
    assert b"def f()" in residue and b"'x'" in residue
