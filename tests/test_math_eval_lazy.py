"""The lazy instance-enumeration rewrite is ORDER- AND VERDICT-IDENTICAL to
the reference semantics it replaced (sorted full cross product; per-hypothesis
domain re-scan with exact min-L1 probes).

The rewrite exists purely for cost: the old `enumerate_domain` materialized
and sorted 17^d tuples before a caller needing the k SMALLEST satisfiers saw
the first one, and the old `boundary_probes` recomputed a min-over-satisfiers
L1 distance for every candidate -- quadratic, ~1e10 ops on the corpus's
five-object readings.  Everything downstream (statement-cert fidelity
channels, demo goldens, the bench) depends on the CANONICAL ORDER, so the pin
here is byte-equality against a straight transcription of the old code, not a
relational property."""
import itertools
import json
import pathlib

from generators.math_reading import parse_math_reading
from generators import math_eval
from generators.math_eval import eval_pred, _id

_SRC = pathlib.Path(__file__).resolve().parent.parent / "specs" / "mathsources"


def _reference_enumerate(reading, bound):
    objects = reading.objects()
    names = sorted(objects)
    ranges = [range(0, bound + 1) if objects[n] == "Nat"
              else range(-bound, bound + 1) for n in names]
    combos = sorted(itertools.product(*ranges),
                    key=lambda vals: (sum(abs(v) for v in vals), vals))
    return [dict(zip(names, vals)) for vals in combos]


def _reference_probes(reading, bound):
    hyps = sorted(reading.by_kind("hypothesis"), key=_id)
    if not hyps:
        return []
    carrier_of = reading.objects()
    ambient = reading.ambient_carrier()
    names = sorted(carrier_of)
    domain = _reference_enumerate(reading, bound)
    results = []
    for i, h in enumerate(hyps):
        hi = h["lf"]["pred"]
        others = [hh["lf"]["pred"] for j, hh in enumerate(hyps) if j != i]
        cands, satisfiers = [], []
        for asg in domain:
            if not all(eval_pred(p, asg, carrier_of, ambient) for p in others):
                continue
            (satisfiers if eval_pred(hi, asg, carrier_of, ambient)
             else cands).append(asg)
        if not cands:
            continue
        if satisfiers:
            def _dist(v):
                return min(sum(abs(v[n] - s[n]) for n in names)
                           for s in satisfiers)
            best = min(_dist(v) for v in cands)
            probe = next(v for v in cands if _dist(v) == best)
        else:
            probe = cands[0]
        results.append({"assignment": probe, "hypothesis_id": h["id"]})
    return results


def _reading(doc, source):
    return parse_math_reading(json.dumps(doc), source)


def _committed(stem):
    obj = json.loads((_SRC / "readings" / f"{stem}.json").read_text())
    return _reading(obj["reading"], obj["source"])


def _mk(statements, source):
    return _reading({"theorem": "t", "statements": statements}, source)


def _five_object_case():
    """A 5-object Int reading (the shape whose cost motivated the rewrite),
    checked at small bounds where the reference stays tractable."""
    src = ("Here m is a positive integer.\nIf a is congruent to b modulo m "
           "and c is congruent to d modulo m, then a plus c is congruent to "
           "b plus d modulo m.")
    def obj(i, name):
        return {"id": i, "force": "presupposition", "quote": "modulo m",
                "lf": {"kind": "object", "name": name, "type": "Int"}}
    stmts = [
        {"id": "amb", "force": "choice", "quote": "",
         "lf": {"kind": "ambient", "carrier": "Int"}},
        obj("om", "m"), obj("oa", "a"), obj("ob", "b"),
        obj("oc", "c"), obj("od", "d"),
        {"id": "q", "force": "demand", "quote": "If a is congruent to b modulo m",
         "lf": {"kind": "quantifier", "binder": "forall",
                "objects": ["m", "a", "b", "c", "d"]}},
        {"id": "h0", "force": "presupposition", "quote": "positive integer",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "<", "args": [{"lit": 0}, {"ref": "m"}]}}},
        {"id": "h1", "force": "demand", "quote": "a is congruent to b modulo m",
         "lf": {"kind": "hypothesis",
                "pred": {"op": "=", "args": [
                    {"op": "mod", "args": [{"ref": "a"}, {"ref": "m"}]},
                    {"op": "mod", "args": [{"ref": "b"}, {"ref": "m"}]}]}}},
        {"id": "c", "force": "demand",
         "quote": "a plus c is congruent to b plus d modulo m",
         "lf": {"kind": "conclusion",
                "pred": {"op": "=", "args": [
                    {"op": "mod", "args": [
                        {"op": "+", "args": [{"ref": "a"}, {"ref": "c"}]},
                        {"ref": "m"}]},
                    {"op": "mod", "args": [
                        {"op": "+", "args": [{"ref": "b"}, {"ref": "d"}]},
                        {"ref": "m"}]}]}}},
    ]
    return _mk(stmts, src)


def _cases():
    yield _committed("01_dvd_reflexive"), (2, 3, 4, 8)
    yield _committed("04_even_plus_even"), (2, 3, 4, 8)
    yield _five_object_case(), (1, 2)


def test_enumerate_domain_order_byte_identical():
    for reading, bounds in _cases():
        for bound in bounds:
            assert (list(math_eval.enumerate_domain(reading, bound))
                    == _reference_enumerate(reading, bound))


def test_boundary_probes_byte_identical():
    for reading, bounds in _cases():
        for bound in bounds:
            assert (math_eval.boundary_probes(reading, bound)
                    == _reference_probes(reading, bound))


def test_satisfying_instances_prefix_of_canonical_order():
    for reading, bounds in _cases():
        for bound in bounds:
            got = math_eval.satisfying_instances(reading, 5, bound)
            ref = [a for a in _reference_enumerate(reading, bound)
                   if all(eval_pred(h["lf"]["pred"], a, reading.objects(),
                                    reading.ambient_carrier())
                          for h in reading.by_kind("hypothesis"))][:5]
            assert got == ref
