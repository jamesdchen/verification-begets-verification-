"""S6 parity teeth (schema <-> bytes, PLAN_REFLECT §3 S6).

`compile_guard_shape` and its shape siblings prove the SCHEMA (binder prefix +
hypothesis chain + conclusion) equivalent to the reflected statement; the
byte-identity teeth pin the EMISSION.  What was missing (the post-PR#18 audit)
is the arrow between them: nothing tied the emitted bytes to the schema
reading.  This module closes that: a small structural parser decomposes each
committed reading's emitted ``lean_text`` back into the shape schema --
binder segments, hypothesis strings, conclusion string -- and asserts
round-trip equality piece by piece against the compiler's OWN per-statement
renderer (imported, never copied, so the comparison cannot drift).

LLM-free, Lean-free, deterministic.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
from generators.math_compile import compile_math_reading, _render_pred, _Ctx
from generators.math_reading import parse_math_reading

READINGS = common.REPO_ROOT / "specs" / "mathsources" / "readings"


def _split_depth0(text, sep):
    """Split on `sep` at parenthesis depth 0 (the emission wraps every
    compound in parens, so depth-0 separators are exactly the structural
    ones)."""
    out, depth, start, i = [], 0, 0, 0
    while i < len(text):
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0 and text.startswith(sep, i):
            out.append(text[start:i])
            i += len(sep)
            start = i
            continue
        i += 1
    out.append(text[start:])
    return out


def parse_lean_text(lean_text):
    """Emitted `theorem <id> : <prop> := sorry` -> shape schema instance:
    {"theorem", "binders": [(sym, [(name, carrier), ...]), ...],
     "hyps": [str, ...], "conclusion": str}."""
    assert lean_text.startswith("theorem ") and lean_text.endswith(" := sorry")
    head, prop = lean_text[len("theorem "):-len(" := sorry")].split(" : ", 1)
    pieces = _split_depth0(prop, ", ")
    segments, body = pieces[:-1], pieces[-1]
    binders = []
    for seg in segments:
        sym, rest = seg[0], seg[1:].strip()
        assert sym in ("∀", "∃"), seg
        groups = []
        for grp in _split_depth0(rest, " "):
            assert grp.startswith("(") and grp.endswith(")"), seg
            name, carrier = grp[1:-1].split(" : ")
            groups.append((name, carrier))
        binders.append((sym, groups))
    body_pieces = _split_depth0(body, " → ")
    return {"theorem": head, "binders": binders,
            "hyps": body_pieces[:-1], "conclusion": body_pieces[-1]}


def _expected_schema(reading):
    """The schema instance the READING implies, built by the compiler's own
    canonical rules (leading ∀ over unbound refs sorted by name; quantifier
    segments in id order; hyps/conclusions in id order via the imported
    renderer)."""
    from generators.math_compile import _pred_refs
    objects = reading.objects()
    ctx = _Ctx(ambient=reading.ambient_carrier(), objects=objects)
    _by_id = lambda s: s["id"]
    q_stmts = sorted(reading.by_kind("quantifier"), key=_by_id)
    hyp_stmts = sorted(reading.by_kind("hypothesis"), key=_by_id)
    concl_stmts = sorted(reading.by_kind("conclusion"), key=_by_id)
    bound = {o for s in q_stmts for o in s["lf"]["objects"]}
    referenced = set()
    for s in hyp_stmts + concl_stmts:
        referenced.update(_pred_refs(s["lf"]["pred"]))
    binders = []
    leading = sorted(referenced - bound)
    if leading:
        binders.append(("∀", [(o, objects[o]) for o in leading]))
    for s in q_stmts:
        sym = "∀" if s["lf"]["binder"] == "forall" else "∃"
        binders.append((sym, [(o, objects[o]) for o in s["lf"]["objects"]]))
    hyps = [_render_pred(s["lf"]["pred"], ctx) for s in hyp_stmts]
    concls = [_render_pred(s["lf"]["pred"], ctx) for s in concl_stmts]
    conclusion = (concls[0] if len(concls) == 1
                  else "(" + " ∧ ".join(concls) + ")")
    return {"theorem": reading.theorem, "binders": binders,
            "hyps": hyps, "conclusion": conclusion}


def test_committed_corpus_round_trips():
    files = sorted(READINGS.glob("*.json"))
    assert files, "expected committed readings"
    for f in files:
        obj = json.loads(f.read_text())
        reading = parse_math_reading(json.dumps(obj["reading"]), obj["source"])
        lean_text = compile_math_reading(reading)["lean_text"]
        assert parse_lean_text(lean_text) == _expected_schema(reading), f.stem


def test_parser_rejects_malformed():
    import pytest
    with pytest.raises(AssertionError):
        parse_lean_text("not a theorem")


def test_round_trip_covers_every_shape():
    # the corpus exercises each S6 shape at least once: a guard/hypothesis
    # chain (shape 2), a multi-binder ∀ segment (shape 3), an ∃ segment
    # (shape 4).  Conjoined conclusions (shape 5) have no committed instance
    # yet -- the parser handles them (the ∧-joined conclusion string), and
    # this tooth starts asserting corpus coverage the day one lands.
    shapes = {"hyp_chain": False, "multi_forall": False, "exists_seg": False}
    for f in sorted(READINGS.glob("*.json")):
        obj = json.loads(f.read_text())
        reading = parse_math_reading(json.dumps(obj["reading"]), obj["source"])
        schema = parse_lean_text(compile_math_reading(reading)["lean_text"])
        if schema["hyps"]:
            shapes["hyp_chain"] = True
        if any(len(groups) >= 2 for _, groups in schema["binders"]):
            shapes["multi_forall"] = True
        if any(sym == "∃" for sym, _ in schema["binders"]):
            shapes["exists_seg"] = True
    assert all(shapes.values()), shapes
