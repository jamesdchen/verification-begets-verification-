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
  4. REGISTRY DIFF CONFORMING (opt-in, ``--conforming``) -- the growth
     registry's diff is EXACTLY "rows added, nothing else moved".  See
     ``conforming_registry_diff`` below.

Everything else on the bill (batteries, canary, registry-row shape, suite)
is already enforced by the fast gate's teeth; this tool never re-implements
them, it only narrows what remains for the human.

THE CONFORMING-DIFF PREDICATE (check 4) and why it is written as an
EXCISION rather than a checklist.  Every full-bill purchase trips the
trust-surface check by design, because the growth registry lives on a
ceremony-reserved path.  That is correct for the general case and wasteful
for the ONE diff shape the repo has paid for twice already (P1 3f826dd-
class, P2): a new GROWERS row, its SIGNATURE_PINS entries, and nothing
else.  The temptation is to enumerate what a conforming diff may not touch
-- ANTI_LIST, ROLES, NON_GROWERS, ``conformance()``, ``completeness_scan``,
the grower-smell tuples, the module docstring -- and an enumeration is a
list somebody must remember to extend.  So the predicate inverts it: it
excises the GROWERS and SIGNATURE_PINS assignment spans by AST byte offset
and demands the ENTIRE REMAINING SOURCE be byte-identical.  Everything not
enumerated is fenced by default, including the decoy shapes an enumeration
invites (a byte-equal ANTI_LIST left at module level while the real one
moves into a function is caught by the residue, not by a rule about
anti-lists).

Green only what the machine can prove; the maintainer keeps everything
arguable.  A conforming diff still answers to the other three checks, and
"should this capability exist?" is still a human question -- this narrows
review, it never replaces it.

Usage (CI): python3 tools/purchase_bill_manifest.py --base SHA --head SHA
            python3 tools/purchase_bill_manifest.py --base SHA --head SHA \\
                --conforming
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


# --------------------------------------------------------------------------- #
# The conforming-registry-diff predicate (check 4).
# --------------------------------------------------------------------------- #
#: The two assignment spans a conforming purchase may move.  Everything else
#: in the file is fenced by residue byte-equality -- the fence is the
#: COMPLEMENT of this tuple, so it needs no maintenance when the registry
#: grows a new helper.
GROWABLE_SPANS = ("GROWERS", "SIGNATURE_PINS")

#: Dotted-name prefixes no PURCHASE may ever pin a signature under, whatever
#: its rows declare.  The pin conjunct's module scoping is derived from the
#: NEW rows' own values, i.e. from attacker-writable text -- so a row that
#: merely names a ``kernel.certs.*`` value used to donate ``kernel.certs`` to
#: the allowed set and let an unrelated kernel pin ride in behind it.  These
#: three prefixes are the ceremony surface itself (the kernel, the escape
#: gate's validator, and this registry's own machinery); reaching them is the
#: S4a->S4a'->S4b question, never a purchase, so the denial is unconditional
#: and sits ahead of every relaxation.
RESERVED_PIN_PREFIXES = ("kernel.", "buildloop.validate",
                         "buildloop.growth_protocol")


def _line_starts(data: bytes):
    """Byte offset of each line start.  AST ``col_offset`` is measured in
    UTF-8 BYTES, and the registry's comments carry non-ASCII math glyphs, so
    the whole excision runs on bytes -- a character-indexed version would
    mis-cut exactly the rows that mention a big operator."""
    starts = [0]
    for i, b in enumerate(data):
        if b == 0x0A:
            starts.append(i + 1)
    return starts


def _module_assigns(tree, names):
    """({name: (body_index, node)}, refusals) -- MODULE-LEVEL assignments
    only, by target name, plus a NAMED refusal for every near miss.
    Deliberately not ``ast.walk``: a same-named assignment nested inside a
    function is a different object, and treating it as the registry is
    precisely the decoy this predicate must not fall for.

    THE SINGLE-TARGET RULE (a certified-green arbitrary-code-execution hole,
    now closed).  The earlier reading accepted a node when ANY of its targets
    was a Name in ``names`` and then excised the WHOLE ``ast.Assign``, target
    list included.  Two payloads rode straight through with ``ok=True``:

        GROWERS = _SINK[__import__("sys").stderr.write("pwned")] = {...}
        GROWERS = ANTI_LIST = {...}

    Both keep ``node.value`` a perfectly good dict literal (so
    ``literal_eval`` is happy) and both vanish inside the excised span (so the
    residue stays byte-identical).  The first RUNS ARBITRARY CODE at import --
    a subscript target's index expression is evaluated -- and the second
    REBINDS a trust root at runtime while the static extractor, reading the
    real tuple further down the module, still reports it byte-identical.  The
    excision therefore trusts nothing but ``NAME = <literal>``: exactly one
    target, that target a Name.  Everything else is a refusal by name, never
    a silent skip -- a shape this predicate does not understand is a shape it
    must not certify.

    The body INDEX rides along for the positional conjunct: the residue fence
    is position-blind (a span cut from line 141 and re-appended at EOF leaves
    byte-identical residue), and "where a module-level literal is bound"
    decides which later bindings win.  See ``conforming_registry_diff`` (2a).
    """
    out, refusals = {}, []
    for index, node in enumerate(tree.body):
        if not isinstance(node, ast.Assign):
            continue
        named = sorted({t.id for t in node.targets
                        if isinstance(t, ast.Name) and t.id in names})
        if not named:
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            shapes = ", ".join(type(t).__name__ for t in node.targets)
            refusals.append(
                f"{'/'.join(named)} assignment has {len(node.targets)} "
                f"target(s) [{shapes}] -- only a single bare NAME target is "
                f"readable; a second target rebinds something this check "
                f"never sees, and a subscript/attribute target evaluates an "
                f"expression at import")
            continue
        out[named[0]] = (index, node)
    return out, refusals


def _excise(src, span_names):
    """(residue_bytes, {name: literal_value}, {name: body_index}) -- the
    source with the named module-level assignment spans cut out, plus their
    evaluated literals and their POSITIONS in the module body.

    Raises ValueError if a named assignment is absent, is not a literal, or
    is not the single-bare-name shape ``_module_assigns`` insists on.

    THE SPAN-TEXT ASSERTION.  Cutting by AST offset alone cuts whatever the
    node happens to span, and the node spans its target list too -- which is
    how ``GROWERS = ANTI_LIST = {...}`` and
    ``GROWERS = _SINK[<call>] = {...}`` disappeared into a byte-identical
    residue.  ``_module_assigns`` now refuses those shapes structurally; this
    asserts the same fact TEXTUALLY, on the bytes actually removed, so the
    two readings have to agree before anything is cut.  Only ``NAME = `` may
    ever open an excised span."""
    data = src.encode("utf-8")
    tree = ast.parse(src)
    starts = _line_starts(data)
    assigns, refusals = _module_assigns(tree, span_names)
    if refusals:
        raise ValueError("; ".join(refusals))
    missing = [n for n in span_names if n not in assigns]
    if missing:
        raise ValueError(f"module-level assignment(s) absent: {missing}")
    spans, values, positions = [], {}, {}
    for name, (index, node) in assigns.items():
        begin = starts[node.lineno - 1] + node.col_offset
        end = starts[node.end_lineno - 1] + node.end_col_offset
        prefix = f"{name} = ".encode("utf-8")
        if not data[begin:end].startswith(prefix):
            raise ValueError(
                f"{name}: excised span does not begin {prefix!r} -- only a "
                f"plain 'NAME = <literal>' span may be cut, and this one "
                f"opens {data[begin:begin + len(prefix) + 8]!r}")
        spans.append((begin, end))
        positions[name] = index
        try:
            values[name] = ast.literal_eval(node.value)
        except (ValueError, SyntaxError, TypeError) as exc:
            raise ValueError(f"{name} is not a literal: {exc}") from exc
    residue, cursor = [], 0
    for begin, end in sorted(spans):
        residue.append(data[cursor:begin])
        cursor = end
    residue.append(data[cursor:])
    return b"".join(residue), values, positions


def conforming_registry_diff(base_src, head_src):
    """(ok, notes) -- is this growth_protocol.py diff exactly "rows added,
    nothing else moved"?

    The conjuncts, each of which must hold:

      1. RESIDUE BYTE-EQUALITY.  With the GROWERS and SIGNATURE_PINS
         assignment spans excised by AST byte offset, base and head are
         byte-identical.  One stroke fences ANTI_LIST, ROLES, NON_GROWERS,
         ``conformance()``, ``completeness_scan()``, the grower-smell
         tuples and the module docstring -- and any decoy that leaves a
         byte-equal copy behind while moving the real thing.
      1a. SPAN POSITION UNMOVED.  The residue fence is POSITION-BLIND, and
         that blindness was exploitable: cutting the GROWERS span out of
         line 141 and re-appending it verbatim at end of file leaves a
         byte-identical residue, because both sides excise it wherever it
         sits.  Position is semantics in a module -- a literal bound after
         ANTI_LIST wins any rebind race against it, which is exactly how the
         relocation composed with a second target to destroy the anti-list at
         runtime while the static extractor (reading module body order) still
         reported it byte-identical.  So each growable assignment must occupy
         the SAME index in ``tree.body`` at base and at head.  A purchase adds
         rows INSIDE the literal; it never moves the literal.
      2. GROWERS ADDITIVE-ONLY.  Base keys survive into head and every
         SHARED key is deep-equal: a purchase adds rows, it never edits or
         deletes one (an edited row silently re-aims teeth that were
         already argued).
      3. SIGNATURE_PINS ADDITIVE-ONLY, plus NO SMUGGLED PINS: every NEW pin
         key must be EXACTLY one of the NEW GROWERS rows' values, or at least
         live in the same MODULE as one, and must never sit under a
         ceremony-reserved prefix.  P1 and P2 both added pins, so pins must
         be addable; a pin reaching into an unrelated module is an
         interface change wearing a purchase's coat.

         The earlier reading asked ``p not in new_row_blob`` -- a SUBSTRING
         test against the row values joined into one string, with the
         allowed module set derived from those same attacker-written values.
         Three things walked through it: a one-character pin key (``"e"``
         occurs in every blob), a PREFIX of a real dotted name
         (``...canonical_ro`` for ``...canonical_row``), and any
         ``kernel.certs.*`` pin at all, because a row that merely NAMES a
         ``kernel.certs.*`` value donates ``kernel.certs`` to the allowed
         module set.  The test is now exact SET membership against the row
         values, the module set is derived from those exact values, and the
         reserved prefixes are denied unconditionally: what a row declares
         can widen a purchase's own module, never the trust surface.

         The module scoping is a MEASURED relaxation, not a convenience.
         The name-exact rule reds P2's real diff (3f826dd): that purchase
         pinned BOTH ``_check_setbuild`` and ``_check_card`` while its row's
         ``row`` role names only ``_check_card`` -- a sibling checker of the
         same purchase, correctly pinned, referenced by no role.  Rather
         than rewrite the reading to force a green, the conjunct was
         re-argued: an unreferenced pin is INERT (``conformance()`` consults
         ``SIGNATURE_PINS`` only for names that appear as role values, so an
         extra pin can add a constraint and can never remove one), edits and
         deletions are already forbidden above, and the residue fence keeps
         ``conformance()`` itself frozen.  Module scoping therefore keeps
         the only bite this conjunct ever had -- a purchase cannot reach
         into ``kernel``/``buildloop.validate`` and call it a row.
      4. ANTI_LIST EQUAL.  Implied by (1) and asserted anyway: trust roots
         never grow by purchase or economics, and the one item on this bill
         that must never move gets its own named line.
      5. NEW ROWS ARE ROW-SHAPED.  Head parses, and every new row's key set
         is exactly head's ROLES with a non-empty ``teeth`` list -- the
         static mirror of ``conformance()``, checked here because the
         suite's canary runs on the head tree only after a human has
         already decided to look.

    Never raises: an unparseable or unshaped input is a FALSE with a named
    note.  A predicate that crashes is a predicate that gets skipped -- and
    the docstring's "never raises" was a promise the code did not keep: a
    non-dict new row (``"k": 5``, ``"k": ["a"]``) reached ``.values()`` in
    the pin conjunct BEFORE any ``isinstance`` check and came out an
    AttributeError, i.e. a traceback where a named FALSE belonged.  Row shape
    is therefore established first (2a) and every later conjunct reads only
    the rows that survived it."""
    notes = []
    try:
        base_residue, base_vals, base_pos = _excise(base_src, GROWABLE_SPANS)
    except (SyntaxError, ValueError) as exc:
        return False, [f"base growth_protocol.py unreadable or non-conforming: {exc}"]
    try:
        head_residue, head_vals, head_pos = _excise(head_src, GROWABLE_SPANS)
    except (SyntaxError, ValueError) as exc:
        return False, [f"head growth_protocol.py unreadable or non-conforming: {exc}"]

    # Both growable spans must be MAPPINGS on both sides before anything
    # indexes them; a registry rewritten to a list is a shape this predicate
    # does not read, and reading it anyway is how the AttributeError above
    # happened one conjunct later.
    for label, vals in (("base", base_vals), ("head", head_vals)):
        for name in GROWABLE_SPANS:
            if not isinstance(vals[name], dict):
                return False, [f"{label} {name} is not a mapping "
                               f"({type(vals[name]).__name__}) -- a conforming "
                               f"purchase adds rows to a dict literal"]

    ok = True

    # (1) residue byte-equality -- the fence that needs no maintenance.
    if base_residue == head_residue:
        notes.append("residue outside GROWERS/SIGNATURE_PINS byte-identical")
    else:
        ok = False
        notes.append("residue outside GROWERS/SIGNATURE_PINS CHANGED -- a "
                     "conforming purchase moves rows and nothing else")

    # (1a) span position unmoved -- the residue fence cannot see a relocation,
    # because both sides cut the span wherever it sits.
    relocated = sorted(n for n in GROWABLE_SPANS
                       if base_pos[n] != head_pos[n])
    if relocated:
        ok = False
        notes.append(
            "growable span RELOCATED in the module body: "
            + "; ".join(f"{n} body index {base_pos[n]} -> {head_pos[n]}"
                        for n in relocated)
            + " -- a purchase adds rows inside the literal, it never moves "
              "the literal (a later binding wins any rebind race the static "
              "readers below decide in body order)")
    else:
        notes.append("growable spans hold their module-body positions")

    # (2) GROWERS additive-only.
    base_g, head_g = base_vals["GROWERS"], head_vals["GROWERS"]
    # ``key=repr`` throughout: a registry literal may carry a non-string
    # key, and a bare sorted() over mixed types raises where this function
    # promises a named False.
    dropped = sorted(set(base_g) - set(head_g), key=repr)
    edited = sorted((k for k in set(base_g) & set(head_g)
                     if base_g[k] != head_g[k]), key=repr)
    new_keys = sorted(set(head_g) - set(base_g), key=repr)
    if dropped or edited:
        ok = False
        notes.append(f"GROWERS not additive: dropped={dropped or 'none'} "
                     f"edited={edited or 'none'}")
    else:
        notes.append(f"GROWERS additive: rows added {new_keys or 'none'}")

    # (2a) NEW ROWS ARE MAPPINGS -- established BEFORE anything reads a row's
    # values, because the pin conjunct below does exactly that and used to
    # crash on `"k": 5`.  Rows that fail here are dropped from `shaped`, so
    # every later conjunct reads only rows it can read.
    shaped = {k: head_g[k] for k in new_keys if isinstance(head_g[k], dict)}
    unshaped = sorted((k for k in new_keys if k not in shaped), key=repr)
    if unshaped:
        ok = False
        notes.append(f"new GROWERS rows are not dicts: {unshaped} -- a row is "
                     f"a role mapping, and a non-mapping row is unreadable, "
                     f"never conforming")

    # (3) SIGNATURE_PINS additive-only, and no pin without a row to serve.
    base_p, head_p = base_vals["SIGNATURE_PINS"], head_vals["SIGNATURE_PINS"]
    p_dropped = sorted(set(base_p) - set(head_p), key=repr)
    p_edited = sorted((k for k in set(base_p) & set(head_p)
                       if base_p[k] != head_p[k]), key=repr)
    new_pins = sorted(set(head_p) - set(base_p), key=repr)
    if p_dropped or p_edited:
        ok = False
        notes.append(f"SIGNATURE_PINS not additive: dropped="
                     f"{p_dropped or 'none'} edited={p_edited or 'none'}")
    else:
        notes.append(f"SIGNATURE_PINS additive: pins added "
                     f"{new_pins or 'none'}")
    # Exact values, not a joined blob: substring containment let a one-char
    # key and a prefix of a real dotted name both read as "referenced".
    new_row_values = {v for row in shaped.values() for v in row.values()
                      if isinstance(v, str)}
    new_modules = {v.rsplit(".", 1)[0] for v in new_row_values
                   if not v.startswith("(") and "." in v}
    reserved = sorted((p for p in new_pins if isinstance(p, str)
                       and p.startswith(RESERVED_PIN_PREFIXES)), key=repr)
    if reserved:
        ok = False
        notes.append(f"pins added under a CEREMONY-RESERVED prefix: "
                     f"{reserved} -- the trust surface is not widened by "
                     f"anything a row declares about itself")
    smuggled = [p for p in new_pins
                if p not in reserved
                and p not in new_row_values
                and (not isinstance(p, str)
                     or p.rsplit(".", 1)[0] not in new_modules)]
    if smuggled:
        ok = False
        notes.append(f"pins added outside every NEW row's module: "
                     f"{smuggled}")

    # (4) ANTI_LIST equal -- implied by (1), named anyway.
    try:
        same_anti = extract_anti_list(base_src) == extract_anti_list(head_src)
    except ValueError as exc:
        same_anti = False
        notes.append(f"ANTI_LIST unreadable: {exc}")
    if same_anti:
        notes.append("ANTI_LIST byte-identical")
    else:
        ok = False
        notes.append("ANTI_LIST CHANGED -- ceremony-only, never by purchase")

    # (5) new rows are row-shaped (the static mirror of conformance()).
    roles = None
    roles_found, roles_refusals = _module_assigns(ast.parse(head_src),
                                                  ("ROLES",))
    roles_entry = roles_found.get("ROLES")
    if roles_refusals:
        ok = False
        notes.append("head ROLES: " + "; ".join(roles_refusals))
    elif roles_entry is None:
        ok = False
        notes.append("head ROLES absent -- row shape cannot be checked")
    else:
        try:
            roles = set(ast.literal_eval(roles_entry[1].value))
        except (ValueError, SyntaxError, TypeError):
            ok = False
            notes.append("head ROLES not a literal -- row shape cannot be "
                         "checked")
    if roles is not None:
        malformed = []
        for k, row in shaped.items():
            if set(row) != roles:
                malformed.append(f"{k}: roles {sorted(row)} != {sorted(roles)}")
            elif not row.get("teeth"):
                malformed.append(f"{k}: teeth role empty (a grower without "
                                 f"planted violations is unguarded)")
        if malformed:
            ok = False
            notes.append("new row shape: " + "; ".join(malformed))
        else:
            notes.append(f"new rows role-complete and toothed "
                         f"({len(new_keys)})")

    return ok, notes


def _git(*argv):
    return subprocess.run(["git", *argv], check=True, capture_output=True,
                          text=True).stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", required=True)
    ap.add_argument("--conforming", action="store_true",
                    help="also verify the growth-registry diff is exactly "
                         "'rows added, nothing else moved' (the narrowed "
                         "trust-surface route); off by default, so the "
                         "existing CI invocation is byte-unchanged")
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

    registry_touched = "buildloop/growth_protocol.py" in changed
    base_src = head_src = None
    if registry_touched:
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

    # The narrowed trust-surface route, opt-in so the default invocation
    # stays byte-compatible: the registry diff must be exactly "rows added,
    # nothing else moved".  An untouched registry passes vacuously -- there
    # is no diff to conform -- and the ceremony-scope row above is what
    # keeps that from being a loophole.
    if args.conforming:
        if not registry_touched:
            rows.append(("registry diff conforming (rows added, nothing "
                         "else moved)", True, "growth_protocol.py untouched"))
        else:
            conf_ok, conf_notes = conforming_registry_diff(base_src, head_src)
            rows.append(("registry diff conforming (rows added, nothing "
                         "else moved)", conf_ok, "; ".join(conf_notes)))
            ok &= conf_ok

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
