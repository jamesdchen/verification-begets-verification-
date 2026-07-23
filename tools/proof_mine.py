#!/usr/bin/env python3
"""Proof-layer abstraction mining -- the L5 wiring, MVP.

THE IDEA (definition ladder L5): recurring structure in PROOF artifacts is a
concept waiting for a name; admit the abstraction that compresses the proof
corpus, under the same witness + DL-descent gates as every other vocabulary.
This tool is the WIRING for that loop: substrate collection, a deterministic
subtree miner with a train/holdout split (mining on everything and scoring on
the same everything would manufacture transfer -- hold data out for
diagnostics), and an OPTIONAL deeper pass through the outsourced Stitch
compressor (``stitch_core``, the DreamCoder-lineage library learner) whose
output is recorded as evidence, never as an admission.

WHAT COUNTS AS PROOF SUBSTRATE TODAY (honest inventory):
  * witness-emitter templates (``generators/math_witness.py``): the Skolem
    term ASTs of emitted ∃ proofs -- structured, deterministic, LLM-free.
    MEASURED FACT at wiring time: the committed corpus (3 readings in
    specs/mathsources/readings + the bench checkpoint) emits ZERO of these
    -- every committed reading is forall-only or fails the shape guard.  The
    report states that zero; the pipe waits for substrate rather than
    pretending to have it.
  * a ``--proofs-jsonl`` side door: one ``{"source": ..., "sexpr": ...}``
    per line -- the intake for the real prize, Mathlib's own exported proof
    skeletons (the Lean lane's business; nothing here fabricates them).

MINER (deterministic core): closed-subtree frequency over the term ASTs, in
the ONE existing currency (``mdl_macros._leaf_count`` -- no new constants).
A candidate's score is ``(occurrences - 1) * (leaves - 1)`` -- the classic
saved-leaves-if-abbreviated arithmetic.  v0 mines CLOSED subtrees only
(variable names as-is); alpha-normalized / parametric mining is exactly what
the Stitch pass adds, which is why it is wired in as the deeper option.

HOLDOUT DISCIPLINE: sources are split train/holdout by parity of their rank
in the sorted source list (deterministic, no clocks, no seeds).  Mining sees
TRAIN only; every mined candidate is then scored on HOLDOUT occurrences --
``transfer = holdout_density / train_density`` is the diagnostic that
separates real regularity from memorized incident structure (the
holdout_transfer.py precedent).

Everything here REPORTS; nothing admits.  Admission stays with the priced
gates (mdl_macros / operator_growth), fed by this report.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from buildloop.mdl_macros import _leaf_count
from generators.math_reading import parse_math_reading
from generators.math_witness import emit_witness_proofs

DEFAULT_BOUND = 8
MIN_LEAVES = 2          # a single leaf abbreviates nothing


# ------------------------------------------------------------------ substrate
def collect_from_readings(pairs, *, bound=DEFAULT_BOUND):
    """``pairs``: iterable of (MathReading, source_id).  Returns programs
    [{source, layer, ast}] -- one per ∃-object template of every reading the
    emitter actually emits for; skips are counted, never invented."""
    programs, skips = [], {}
    for reading, source_id in pairs:
        res = emit_witness_proofs(reading, bound=bound)
        if res["status"] != "emitted":
            skips[res["reason"]] = skips.get(res["reason"], 0) + 1
            continue
        for name, term in sorted(res["template"].items()):
            programs.append({"source": source_id, "layer": "proof-template",
                             "exists_object": name, "ast": term})
    return programs, skips


def collect_repo_corpus(root, *, bound=DEFAULT_BOUND):
    """The committed substrate: specs/mathsources/readings/*.json plus the
    bench checkpoint's reading_json rows.  Tolerant of absent files; every
    parse failure is counted, never silently dropped."""
    pairs, parse_failures = [], 0
    for p in sorted(glob.glob(os.path.join(
            root, "specs", "mathsources", "readings", "*.json"))):
        try:
            d = json.load(open(p))
            pairs.append((parse_math_reading(json.dumps(d["reading"]),
                                             d["source"]),
                          os.path.basename(p)))
        except Exception:
            parse_failures += 1
    ckpt = os.path.join(root, "results", "formalize_bench_state.jsonl")
    if os.path.exists(ckpt):
        for line in open(ckpt):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                rj = rec.get("reading_json")
                if rj:
                    pairs.append((parse_math_reading(
                        rj, rec.get("source_text", "")),
                        str(rec.get("source_id", "ckpt"))))
            except Exception:
                parse_failures += 1
    programs, skips = collect_from_readings(pairs, bound=bound)
    return programs, skips, parse_failures


def load_proofs_jsonl(path):
    """The Mathlib-export side door: {"source", "sexpr"} per line.  The sexpr
    is parsed structurally (balanced parens) only for subtree walking."""
    programs = []
    for line in open(path):
        if line.strip():
            rec = json.loads(line)
            programs.append({"source": rec["source"], "layer": "external",
                             "sexpr": rec["sexpr"]})
    return programs


# ------------------------------------------------------------------- s-exprs
def to_sexpr(ast) -> str:
    """Canonical s-expression of an F-G term/pred AST (dict form)."""
    if isinstance(ast, dict):
        if "ref" in ast:
            return f"(ref {ast['ref']})"
        if "lit" in ast:
            return f"(lit {ast['lit']})"
        if "op" in ast:
            inner = " ".join(to_sexpr(a) for a in ast.get("args", []))
            return f"({ast['op']} {inner})" if inner else f"({ast['op']})"
    raise ValueError(f"not an F-G AST node: {ast!r}")


def _subtrees(ast):
    """Yield every dict subtree (including the root)."""
    if isinstance(ast, dict):
        yield ast
        for a in ast.get("args", []):
            yield from _subtrees(a)


# --------------------------------------------------------------------- miner
def _split(programs):
    """Deterministic train/holdout by parity of source rank (sorted order).
    All programs of one source land on one side -- no leakage across the
    split from a single source's internal repetition."""
    sources = sorted({p["source"] for p in programs})
    train_src = {s for i, s in enumerate(sources) if i % 2 == 0}
    train = [p for p in programs if p["source"] in train_src]
    hold = [p for p in programs if p["source"] not in train_src]
    return train, hold


def _counts(programs):
    out: dict = {}
    for prog in programs:
        if "ast" not in prog:
            continue                       # external sexprs: stitch-only v0
        for sub in _subtrees(prog["ast"]):
            if _leaf_count(sub) < MIN_LEAVES:
                continue
            key = to_sexpr(sub)
            out[key] = out.get(key, 0) + 1
    return out


def mine(programs, *, top_k=10):
    """Deterministic closed-subtree mining with the holdout transfer score."""
    train, hold = _split(programs)
    tc, hc = _counts(train), _counts(hold)
    candidates = []
    for key, n in tc.items():
        if n < 2:
            continue                       # a one-off abbreviates nothing
        leaves = key.count("(")            # node count of the canonical sexpr
        saving = (n - 1) * (leaves - 1)
        candidates.append({
            "sexpr": key, "train_occurrences": n,
            "holdout_occurrences": hc.get(key, 0),
            "approx_saving": saving,
            "transfer": (hc.get(key, 0) / n) if n else 0.0,
        })
    candidates.sort(key=lambda c: (-c["approx_saving"], c["sexpr"]))
    return {"n_programs": len(programs),
            "n_train": len(train), "n_holdout": len(hold),
            "candidates": candidates[:top_k]}


# --------------------------------------------------- two-speed ledger + rank
def corpus_digest(programs) -> str:
    """Content identity of a program corpus: sha over the sorted canonical
    s-expressions.  Deterministic (no clocks) -- ledger rows stamp WHICH
    corpus first surfaced a candidate, never when."""
    import hashlib
    sexprs = sorted((p.get("sexpr") or to_sexpr(p["ast"])) for p in programs)
    return hashlib.sha256("\n".join(sexprs).encode()).hexdigest()


def rank_for_verification(candidates):
    """Verification is the throughput ceiling, so its queue is value-ordered:
    ``approx_saving * transfer`` first (regularity that PROVED it generalizes
    outranks bigger-but-untransferred), then raw saving, then the canonical
    sexpr for a total deterministic order.  No tuned constants -- transfer=0
    candidates sink on the product alone."""
    return sorted(candidates,
                  key=lambda c: (-(c["approx_saving"] * c["transfer"]),
                                 -c["approx_saving"], c["sexpr"]))


def update_ledger(mined: dict, programs, path: str) -> dict:
    """The HOT loop's output: merge this run's candidates into an append-only
    JSONL ledger, deduplicated by candidate identity (the canonical sexpr).
    Mining is near-free and runs on every corpus append; ADMISSION reads the
    ledger in deliberate batches (the cold loop) -- decoupling the cheap
    pipeline from the expensive ceremony.  Returns {new, updated, total}."""
    import hashlib
    digest = corpus_digest(programs)
    rows = {}
    if os.path.exists(path):
        for line in open(path):
            if line.strip():
                r = json.loads(line)
                rows[r["candidate_sha"]] = r
    new = updated = 0
    for c in rank_for_verification(mined["candidates"]):
        sha = hashlib.sha256(c["sexpr"].encode()).hexdigest()
        if sha in rows:
            prev = rows[sha]
            if c["approx_saving"] * c["transfer"] > \
                    prev["approx_saving"] * prev["transfer"]:
                rows[sha] = {**prev, **c, "candidate_sha": sha,
                             "best_seen_corpus": digest}
                updated += 1
        else:
            rows[sha] = {**c, "candidate_sha": sha,
                         "first_seen_corpus": digest,
                         "best_seen_corpus": digest}
            new += 1
    with open(path, "w") as fh:
        for sha in sorted(rows):
            fh.write(json.dumps(rows[sha], sort_keys=True) + "\n")
    return {"new": new, "updated": updated, "total": len(rows)}


# ------------------------------------------------------ rewrite certificate
def certify_rewrite(programs, candidate_sexpr: str, *, name="A0",
                    cache: dict | None = None) -> dict:
    """The R3-eliminability certificate for a CLOSED mined candidate
    (certifying-algorithms sweep, item 3): abbreviating every occurrence and
    expanding back must be byte-identical, the marker must not collide with
    existing corpus text, and the candidate must actually be used.  v0 is
    string-level over canonical s-expressions -- its real failure surface is
    marker capture and overlap pathologies, which is exactly what it checks;
    AST-level rewriting with alpha-normalization arrives with parametric
    (stitch) candidates.  Returns evidence, never admits."""
    marker = f"({name})"
    if cache is not None:
        import hashlib
        key = hashlib.sha256(
            (candidate_sexpr + "\x00" + corpus_digest(programs)).encode()
        ).hexdigest()
        if key in cache:
            return cache[key]
    rows, total_uses = [], 0
    for p in programs:
        s = p.get("sexpr") or to_sexpr(p["ast"])
        collision = marker in s
        abbrev = s.replace(candidate_sexpr, marker)
        expanded = abbrev.replace(marker, candidate_sexpr)
        uses = s.count(candidate_sexpr)
        total_uses += uses
        rows.append({"source": p["source"], "uses": uses,
                     "roundtrip_ok": (expanded == s) and not collision,
                     "marker_collision": collision})
    ok = all(r["roundtrip_ok"] for r in rows) and total_uses > 0
    result = {"candidate": candidate_sexpr, "marker": marker, "ok": ok,
              "total_uses": total_uses, "rows": rows}
    if cache is not None:
        cache[key] = result
    return result


# ---------------------------------------------------------------- stitch pass
def stitch_pass(programs, *, iterations=3, max_arity=2):
    """The outsourced deeper pass: parametric abstractions via stitch_core.
    Absent library / any failure degrades to an honest record, never a crash.
    Output is EVIDENCE for the report; admission still belongs to the priced
    gates."""
    sexprs = [p.get("sexpr") or to_sexpr(p["ast"]) for p in programs]
    if len(sexprs) < 2:
        return {"ran": False, "reason": "fewer than 2 programs"}
    try:
        import stitch_core
    except ImportError:
        return {"ran": False, "reason": "stitch_core absent"}
    try:
        res = stitch_core.compress(sexprs, iterations=iterations,
                                   max_arity=max_arity)
        abstractions = [{"name": a.name, "body": a.body, "arity": a.arity}
                        for a in res.abstractions]
        return {"ran": True, "abstractions": abstractions,
                "n_programs": len(sexprs)}
    except Exception as ex:
        return {"ran": False, "reason": f"stitch_core error: {ex!r}"[:300]}


# --------------------------------------------------------------------- report
def report(root=None, *, bound=DEFAULT_BOUND, top_k=10, proofs_jsonl=None,
           with_stitch=False):
    root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    programs, skips, parse_failures = collect_repo_corpus(root, bound=bound)
    if proofs_jsonl:
        programs += load_proofs_jsonl(proofs_jsonl)
    mined = mine(programs, top_k=top_k)
    out = {
        "tool": "proof_mine",
        "honesty": ("REPORTS proof-layer regularity; admits nothing.  "
                    "Deterministic closed-subtree miner + holdout transfer; "
                    "the stitch pass (when run) is recorded evidence.  An "
                    "empty substrate is reported as the finding it is."),
        "substrate": {"programs": len(programs),
                      "emitter_skips": dict(sorted(skips.items())),
                      "parse_failures": parse_failures,
                      "bound": bound},
        "mined": mined,
    }
    if with_stitch:
        out["stitch"] = stitch_pass(programs)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="results/proof_mine")
    ap.add_argument("--bound", type=int, default=DEFAULT_BOUND)
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--proofs-jsonl", default=None,
                    help="external proof-skeleton corpus (Mathlib export)")
    ap.add_argument("--stitch", action="store_true",
                    help="also run the stitch_core parametric pass")
    args = ap.parse_args(argv)
    from buildloop import lanes
    with lanes.token_free("proof-mining"):
        rep = report(bound=args.bound, top_k=args.top_k,
                     proofs_jsonl=args.proofs_jsonl, with_stitch=args.stitch)
    with open(args.out + ".json", "w") as fh:
        json.dump(rep, fh, indent=1, sort_keys=True)
    print(f"proof_mine: {rep['substrate']['programs']} programs "
          f"({rep['substrate']['emitter_skips']}) -> {args.out}.json")
    for c in rep["mined"]["candidates"][:5]:
        print("  ", c["approx_saving"], c["train_occurrences"],
              f"transfer={c['transfer']:.2f}", c["sexpr"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
