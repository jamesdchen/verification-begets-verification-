"""Teeth for the purchase-bill manifest narrower (tools/purchase_bill_manifest.py).

Pure-function coverage only -- the git plumbing is exercised by the CI job;
these teeth pin the judgment logic so it cannot drift silently."""
import os
import sys

import pytest

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
    if not checked:
        # The fast gate's checkout is SHALLOW, so the historical shas are
        # unreachable there by construction -- an environment fact, not a
        # predicate verdict (the test_census_delta convention: skip by
        # name, never a silent pass, never a red for the clone's depth).
        # The synthetic-fixture teeth above pin the predicate either way.
        pytest.skip("worked-example shas unreachable (shallow clone); "
                    "predicate replayed against history where git has it")


def test_module_level_only_never_walks_into_a_function():
    """_module_assigns is deliberately not ast.walk: a same-named assignment
    inside a function is a different object, and treating it as the registry
    is the decoy above."""
    src = ("GROWERS = {}\nSIGNATURE_PINS = {}\n"
           "def f():\n    GROWERS = {'x': 1}\n    return GROWERS\n")
    residue, values, positions = m._excise(src, m.GROWABLE_SPANS)
    assert values["GROWERS"] == {}
    assert positions == {"GROWERS": 0, "SIGNATURE_PINS": 1}
    assert b"def f()" in residue and b"'x'" in residue


# =========================================================================== #
# The EXECUTED exploits.
#
# Every case below was run against the predicate as landed and came back
# ``ok=True`` (or, in the last pair, came back as a traceback where a named
# False belonged).  They are transcribed verbatim rather than paraphrased:
# a security tooth that tests the fix's shape instead of the attack's shape
# is a tooth that passes the next variant of the same attack.
# =========================================================================== #
def _growers_span(src):
    """(begin, end, text) of the module-level GROWERS assignment, in BYTES --
    the relocation fixtures move the span itself, so they need the same byte
    arithmetic the excision uses (col_offset is UTF-8 bytes and the registry
    carries math glyphs)."""
    import ast
    data = src.encode("utf-8")
    starts = m._line_starts(data)
    node = m._module_assigns(ast.parse(src), ("GROWERS",))[0]["GROWERS"][1]
    begin = starts[node.lineno - 1] + node.col_offset
    end = starts[node.end_lineno - 1] + node.end_col_offset
    return begin, end, data[begin:end].decode("utf-8")


def test_red_subscript_target_runs_arbitrary_code_at_import():
    """THE executed exploit: a second, SUBSCRIPT target whose index is a call.

        GROWERS = _SINK[__import__("sys").stderr.write("pwned")] = {...}

    ``node.value`` is still a clean dict literal, so ``literal_eval`` is
    happy; the whole Assign (target list included) vanishes into the excised
    span, so the residue stays byte-identical; and importing the file
    EXECUTES the index expression.  It certified ok=True.  Only a single
    bare-Name target may be excised."""
    src = _add_row(_base()).replace(
        "GROWERS = {\n",
        'GROWERS = _SINK[__import__("sys").stderr.write("pwned")] = {\n', 1)
    assert src != _add_row(_base()), "fixture did not apply"
    notes = _red(src, "subscript-target code execution")
    assert any("target(s)" in n for n in notes), notes


def test_red_second_name_target_rebinds_a_trust_root():
    """``GROWERS = ANTI_LIST = {...}``: at runtime ANTI_LIST becomes the
    GROWERS dict, and the static extractor -- walking module body order --
    still reads the real tuple further down and reports it byte-identical.
    The same shape aimed at NON_GROWERS blinds the completeness canary."""
    for victim in ("ANTI_LIST", "NON_GROWERS", "ROLES"):
        src = _add_row(_base()).replace(
            "GROWERS = {\n", f"GROWERS = {victim} = {{\n", 1)
        assert src != _add_row(_base()), victim
        notes = _red(src, f"{victim} rebind")
        assert any("target(s)" in n for n in notes), (victim, notes)


def test_red_growable_span_relocated_to_end_of_file():
    """The positional hole, alone: cut the GROWERS span out of its place and
    re-append it verbatim at EOF.  Both sides excise it wherever it sits, so
    the residue fence sees nothing at all -- and this is the enabler, because
    a literal bound AFTER ANTI_LIST wins the rebind race that module-body
    order decides."""
    base = _base()
    begin, end, span = _growers_span(base)
    data = base.encode("utf-8")
    moved = (data[:begin] + data[end:]).decode("utf-8") + span.replace(
        "GROWERS = {\n", "GROWERS = {\n" + _DEMO_ROW, 1)
    notes = _red(moved, "relocated GROWERS span")
    assert any("RELOCATED" in n for n in notes), notes


def test_red_relocation_composed_with_the_anti_list_rebind():
    """The two holes composed, which is how the review executed it: relocate
    the span past ANTI_LIST and rebind ANTI_LIST from it.  Measured against
    the landed predicate this returned ok=True while
    ``exec``-ing the head made ANTI_LIST a dict of grower rows -- a certified
    green that destroys the trust root at import."""
    base = _base()
    begin, end, span = _growers_span(base)
    data = base.encode("utf-8")
    head = (data[:begin] + data[end:]).decode("utf-8") + span.replace(
        "GROWERS = {\n", "GROWERS = ANTI_LIST = {\n" + _DEMO_ROW, 1)
    # the static extractor is fooled -- body order still finds the real tuple
    assert m.extract_anti_list(head) == m.extract_anti_list(base)
    # ...and the runtime is not: this is what the head actually binds
    ns = {}
    exec(compile(head, "<exploit>", "exec"), ns)          # noqa: S102
    assert isinstance(ns["ANTI_LIST"], dict), "fixture did not rebind"
    _red(head, "relocation + anti-list rebind")


def test_red_one_character_and_prefix_pins():
    """The substring test ``p not in new_row_blob`` admitted any pin key that
    happened to occur inside the joined row values: a one-character key, and
    a PREFIX of a real dotted name whose own module the rows never donate.
    Membership is exact now, and the module set is derived from those same
    exact values."""
    for key in ("e", "generators.demo_grow", "canonical_row"):
        src = _add_pin(_add_row(_base()), key, "(x) -> 'str'")
        notes = _red(src, f"substring pin {key!r}")
        assert any(repr(key) in n for n in notes), (key, notes)


def test_red_ceremony_reserved_pin_even_when_a_row_declares_the_module():
    """The module relaxation is derived from the NEW rows' own values, i.e.
    from text the purchase writes -- so a row naming a ``kernel.certs.*``
    value used to donate ``kernel.certs`` to the allowed set and let an
    unrelated kernel pin ride in behind it.  The reserved prefixes are denied
    ahead of every relaxation: what a row declares can widen its own module,
    never the trust surface."""
    row = _DEMO_ROW.replace('        "conserve": "(demo: expansion-eliminable '
                            'by construction)",\n',
                            '        "conserve": '
                            '"kernel.certs.ANCHOR_DISCHARGE_RUNGS",\n')
    assert row != _DEMO_ROW, "fixture did not apply"
    for pin in ("kernel.certs.pin_hash",
                "buildloop.validate.validate_generator_spec2",
                "buildloop.growth_protocol.conformance"):
        src = _add_pin(_add_row(_base(), row), pin, "(x) -> 'str'")
        notes = _red(src, f"reserved pin {pin}")
        assert any("RESERVED" in n and pin in n for n in notes), (pin, notes)


def test_a_non_dict_row_is_a_named_false_never_an_attributeerror():
    """The docstring promises "never raises"; ``head_g[k].values()`` in the
    pin conjunct ran before any isinstance check, so ``"k": 5`` and
    ``"k": ["a"]`` came out as AttributeError -- a crash is a check that gets
    skipped."""
    for literal in ('    "bogus": 5,\n', '    "bogus": ["a"],\n',
                    '    "bogus": None,\n', '    "bogus": "a string",\n'):
        ok, notes = m.conforming_registry_diff(_base(),
                                               _add_row(_base(), literal))
        assert not ok, literal
        assert any("not dicts" in n for n in notes), (literal, notes)


def test_a_non_mapping_growable_span_is_a_named_false():
    """A registry literal rewritten to a list is a shape this predicate does
    not read; reading it anyway is where the AttributeError above lived."""
    src = _base().replace("SIGNATURE_PINS = {\n", "SIGNATURE_PINS = [\n", 1)
    src = src.replace("\n}\n\n#: Trust roots", "\n]\n\n#: Trust roots", 1)
    ok, notes = m.conforming_registry_diff(_base(), src)
    assert not ok and notes


def test_excision_refuses_anything_but_name_space_equals():
    """The textual half of the single-target rule, asserted on the bytes
    actually removed: two readings (structural and textual) that must agree
    before a single byte is cut."""
    ok, notes = m.conforming_registry_diff(
        _base(), _base().replace("GROWERS = {\n", "GROWERS  = {\n", 1))
    assert not ok and any("excised span does not begin" in n
                          or "target(s)" in n for n in notes), notes
