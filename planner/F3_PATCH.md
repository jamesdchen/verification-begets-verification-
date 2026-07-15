# WP-F / F3 — the wave-1 patch for `run/formalize.py` (applied by WP-G, ⚠FI-7)

`run/formalize.py` is owned by **WP-C alone**. WP-F does not touch it. This
document is the exact, frozen-text patch the **merge-owner (WP-G, §3 G3)**
applies at wave 1, *after WP-C merges*, to wire WP-F's search as evidence.

**What it adds (F-INT-6, evidence-only, L3):**
1. an optional keyword-only `choice_search=False` on `certify_statement`;
2. one stage-5 evidence block: when `choice_search=True` **and** the reading has
   choice-force carrier elements, the `search_carrier` ranking is attached to
   the examiner-grade evidence (`result.examiner["choice_search"]`).

**Guarantees.**
- **Default off ⇒ byte-identical.** With `choice_search` unset/`False` the block
  is skipped entirely and every `FormalizeResult` field is unchanged, so the
  WP-C demo-stdout golden and all existing outputs stay byte-identical.
- **Never a refusal, never a new certificate.** The block only *attaches*
  evidence; it never flips `ok`, never appends a failing stage, never issues a
  cert (F-INT-6 / the L3 discipline).
- **No import cycle.** `search_carrier` is imported *inside the function body*.
  `planner/math_choices.py` imports only `generators.*`, `buildloop.validate_lean`
  and `kernel.backends` — never `run.formalize` — so the lazy import is purely
  belt-and-suspenders; there is no cycle in either direction.

**Anchors are WP-C-stable.** WP-C's merge adds caching internals *inside*
`_nonvacuity`/`_instances` (stages 2/4); it does **not** change the
`certify_statement` signature line or the stage-5→return region this patch
edits. Both hunks therefore apply cleanly against WP-C's merged version. If WP-C
has reflowed either anchor, apply the change by meaning (add the keyword; add the
guarded block just before the `stage 6` comment / final `return`) — the semantics
above are the contract, not the exact whitespace.

---

## Hunk 1 — the signature: add `choice_search=False`

### Before
```python
def certify_statement(source_text, math_reading_json, *, event_sink=None,
                      cache_get=None, cache_put=None, expectations_json=None,
                      bound=8, source_id=None):
```

### After
```python
def certify_statement(source_text, math_reading_json, *, event_sink=None,
                      cache_get=None, cache_put=None, expectations_json=None,
                      bound=8, source_id=None, choice_search=False):
```

---

## Hunk 2 — the stage-5 evidence block, just before `stage 6` / the final return

### Before
```python
    # ---- stage 6: proof (Lean-gated F0.3) -- skipped when Lean is absent -----
    # (No layer appended: the proof cert is the deferred kernel-checked tier.)

    return FormalizeResult(
        ok=True, layers=layers, lean_text=lean_text,
        statement_hash=statement_hash, provenance=provenance,
        boundary_behavior=boundary_behavior, statement_cert=statement_cert,
        examiner=examiner)
```

### After
```python
    # ---- stage 5 (evidence): searched formalization choices (F-INT-6, WP-F) --
    # When requested AND the reading has choice-force carrier elements (typed
    # objects / operator bindings / the ambient), attach the deterministic
    # carrier-assignment ranking as examiner-grade evidence (L3): certifying
    # candidates first, then by compiled-statement DL.  EVIDENCE only -- never a
    # refusal, never a new certificate; default off => the fields below are
    # byte-identical.  search_carrier is imported lazily (belt-and-suspenders;
    # planner.math_choices never imports run.formalize, so there is no cycle).
    if choice_search:
        import json as _json
        from planner.math_choices import search_carrier, searchable_slots
        _reading_doc = _json.loads(math_reading_json)
        if searchable_slots(_reading_doc):
            _envelope = _json.dumps(
                {"source": source_text, "reading": _reading_doc})
            examiner = {**examiner,
                        "choice_search": search_carrier(_envelope, bound=bound)}

    # ---- stage 6: proof (Lean-gated F0.3) -- skipped when Lean is absent -----
    # (No layer appended: the proof cert is the deferred kernel-checked tier.)

    return FormalizeResult(
        ok=True, layers=layers, lean_text=lean_text,
        statement_hash=statement_hash, provenance=provenance,
        boundary_behavior=boundary_behavior, statement_cert=statement_cert,
        examiner=examiner)
```

---

## Unified diff (equivalent; apply with `git apply` against WP-C's merged tree)

```diff
--- a/run/formalize.py
+++ b/run/formalize.py
@@ def certify_statement
 def certify_statement(source_text, math_reading_json, *, event_sink=None,
                       cache_get=None, cache_put=None, expectations_json=None,
-                      bound=8, source_id=None):
+                      bound=8, source_id=None, choice_search=False):
@@ stage 5 examiner -> stage 6
     # ---- stage 6: proof (Lean-gated F0.3) -- skipped when Lean is absent -----
     # (No layer appended: the proof cert is the deferred kernel-checked tier.)
 
+    # ---- stage 5 (evidence): searched formalization choices (F-INT-6, WP-F) --
+    # When requested AND the reading has choice-force carrier elements, attach
+    # the deterministic carrier-assignment ranking as examiner-grade evidence
+    # (L3).  EVIDENCE only -- never a refusal, never a new certificate; default
+    # off => byte-identical.  Lazy import: no run.formalize<->math_choices cycle.
+    if choice_search:
+        import json as _json
+        from planner.math_choices import search_carrier, searchable_slots
+        _reading_doc = _json.loads(math_reading_json)
+        if searchable_slots(_reading_doc):
+            _envelope = _json.dumps(
+                {"source": source_text, "reading": _reading_doc})
+            examiner = {**examiner,
+                        "choice_search": search_carrier(_envelope, bound=bound)}
+
     return FormalizeResult(
         ok=True, layers=layers, lean_text=lean_text,
         statement_hash=statement_hash, provenance=provenance,
         boundary_behavior=boundary_behavior, statement_cert=statement_cert,
         examiner=examiner)
```

> Note the diff places the new block *after* the `stage 6` comment lines purely
> so the diff's trailing context matches; functionally the block runs before the
> `return` either way. The Before/After blocks above are the authoritative form —
> the guarded block belongs anywhere between the `examiner` assignment (stage 5)
> and the final `return`.

---

## Post-apply verification (WP-G runs these)

```python
# byte-identity: default path unchanged
r0 = certify_statement(src, reading_json)                      # choice_search off
r1 = certify_statement(src, reading_json, choice_search=True)  # evidence attached
assert dataclasses.asdict(r0) == {**dataclasses.asdict(r1),
                                  "examiner": r0.examiner}      # only examiner differs
assert r0.ok == r1.ok                                          # never a refusal
# evidence present only when there are choice-force carriers:
assert ("choice_search" in r1.examiner) == bool(
    __import__("planner.math_choices", fromlist=["searchable_slots"])
    .searchable_slots(__import__("json").loads(reading_json)))
```
