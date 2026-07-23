#!/usr/bin/env python3
"""Flywheel instrumentation: the hammer close-rate meter, v0.

THE NUMBER THIS EXISTS TO PRODUCE.  The mining flywheel (vocabulary shortens
proofs -> more goals close -> more substrate -> better mining) either
compounds or it does not, and Finding 2 taught this repo the cost of
assuming compounding without measuring it.  The direct measurement is
CLOSE-RATE: of a fixed prop set, what fraction does the frozen ladder
(decide -> omega -> norm_num -> simp) close, per rung?  Run the probe before
and after a vocabulary batch; the DELTA is the flywheel doing work or not.

MECHANICS.  Props are GROUND instantiations of corpus conclusions: take each
reading's k smallest hypothesis-satisfying instances (math_eval, the F2.2
machinery), substitute the values into the conclusion pred (pure data, the
operator-expansion substitution discipline), and render through the
COMPILER'S OWN ``_render_pred`` (imported, never copied -- rendering can
never drift from what statements compile to).  Discharge runs through
``LeanBackend.eval_props`` -- which is already the warm-batched path: ONE
sandbox, shared mounts, per-prop probe files.  The "batching" latency lever
is therefore this routing, not new machinery.

SCOPE (v0.2, S3): props carry a TYPED binder shell (forall (n : Carrier),
n = v -> conclusion), so Nat and Int readings are both in scope; the pred
body still renders through the compiler's own machinery.  Lean absent =>
every prop reports ``unavailable`` and the close-rate is honestly
``deferred``, never fabricated.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common
from generators.math_compile import _Ctx, _render_pred, CompileError
from generators.math_eval import conclusions_of, satisfying_instances
from generators.math_reading import parse_math_reading

K_INSTANCES = 3


def _lit(v: int) -> str:
    return str(v) if v >= 0 else f"({v})"


def props_for_reading(reading, *, k=K_INSTANCES):
    """Typed instance props for one reading, or a named honest skip.

    v0.2 (S3): instead of grounding refs into bare numerals (which Lean
    elaborates at the wrong carrier), each prop keeps the conclusion's refs
    and wraps them in a TYPED binder shell::

        forall (n : Int), n = 3 -> <compiled conclusion pred>

    The pred rendering stays the compiler's own ``_render_pred`` (imported,
    never copied); the binder shell is trivial local text with explicit
    carriers, so Nat and Int readings are both in scope."""
    concl = conclusions_of(reading)
    if concl is None:
        return {"status": "skip", "reason": "no-conclusion"}
    objects = reading.objects()
    ctx = _Ctx(ambient=reading.ambient_carrier(), objects=objects)
    try:
        body = _render_pred(concl, ctx)
    except CompileError as ex:
        return {"status": "skip", "reason": f"unrenderable: {ex}"}
    names = sorted(objects)
    binders = " ".join(f"({n} : {objects[n]})" for n in names)
    props = []
    for asg in satisfying_instances(reading, k=k):
        pins = " -> ".join(f"{n} = {_lit(asg[n])}" for n in names)
        if names:
            props.append(f"∀ {binders}, {pins} -> {body}")
        else:
            props.append(body)
    if not props:
        return {"status": "skip", "reason": "no-satisfying-instances"}
    return {"status": "props", "props": props}


def collect_props(root):
    """Ground props over the committed reading corpus + skips histogram."""
    all_props, skips = [], {}
    for p in sorted(glob.glob(os.path.join(
            root, "specs", "mathsources", "readings", "*.json"))):
        try:
            d = json.load(open(p))
            reading = parse_math_reading(json.dumps(d["reading"]), d["source"])
        except Exception:
            skips["parse-failure"] = skips.get("parse-failure", 0) + 1
            continue
        res = props_for_reading(reading)
        if res["status"] == "props":
            for prop in res["props"]:
                all_props.append({"source": os.path.basename(p), "prop": prop})
        else:
            skips[res["reason"]] = skips.get(res["reason"], 0) + 1
    return all_props, skips


def probe(root=None) -> dict:
    root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rows, skips = collect_props(root)
    props = [r["prop"] for r in rows]
    prop_set_sha = common.sha256_json(sorted(props))
    if not common.lean_available():
        return {"tool": "flywheel_probe", "prop_set_sha": prop_set_sha,
                "n_props": len(props), "skips": skips,
                "close_rate": "deferred: lean toolchain absent",
                "rows": rows}
    from kernel.backends import LeanBackend
    results = LeanBackend().eval_props("", props)
    by_rung: dict = {}
    closed = 0
    for row, res in zip(rows, results):
        row["closed_by"] = res.get("closed_by")
        row["value"] = res.get("value")
        if res.get("value") == "closed":
            closed += 1
            by_rung[res["closed_by"]] = by_rung.get(res["closed_by"], 0) + 1
    return {"tool": "flywheel_probe", "prop_set_sha": prop_set_sha,
            "n_props": len(props), "skips": skips,
            "closed": closed,
            "close_rate": (closed / len(props)) if props else None,
            "by_rung": dict(sorted(by_rung.items())),
            "rows": rows}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="results/flywheel_probe.json")
    args = ap.parse_args(argv)
    from buildloop import lanes
    with lanes.token_free("flywheel-probe"):
        rep = probe()
    with open(args.out, "w") as fh:
        json.dump(rep, fh, indent=1, sort_keys=True)
    print(f"flywheel_probe: {rep['n_props']} props "
          f"(skips {rep['skips']}) close_rate={rep['close_rate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
