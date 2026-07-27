# C3 cycle 34 — the registry is exhausted, and the second dead declaration was a dead ORIGIN

One measured corpus refusal, zero certifications.  Corpus unchanged at **125**
sources and **8** corpora (2132 nodes), every DL byte-identical, so no lineage
entry.  Ready stays **0**.  **The supply verdict flips**
`intake-work-available: new-corpus-intake` → `supply-blocked: tower-class-only`,
because this refusal consumed the last declared candidate.

## The route, and what the wire said

`NEXT-SELECTION: refill`.  `tools/corpus_candidates.py` selected
**`lean_cam_combi`** in declaration order (yield-blind) and its printed command
was run **VERBATIM**:

```
python3 tools/intake_corpus.py --name lean_cam_combi \
  --source https://yaeldillies.github.io/LeanCamCombi/blueprint/ \
  --adapter blueprint --project "LeanCamCombi (Dillies)"
```

`HTTP 404`.  Cycle 33's classifier read it as `resource-absent` — correct, and
**not yet the whole reading**.  Probed:

| URL | status |
|---|---|
| `…/LeanCamCombi/blueprint/` (declared) | 404 |
| `…/LeanCamCombi/blueprint`, `…/blueprint/index.html`, `…/blueprint.pdf` | 404 |
| `…/LeanCamCombi/` (project root) | **404** |
| `https://yaeldillies.github.io/` (bare origin) | **404** |
| `https://teorth.github.io/pfr/blueprint/` (control, already intaken) | **200** |

The 404s are answered by `server: GitHub.com`, so DNS resolves to GitHub Pages
and GitHub itself says there is no site.  The control answers 200 through the
same egress with the same UA in the same minute, so neither the wire nor
cycle 31's User-Agent is the cause.  **The account publishes no Pages site at
all.**

**No URL was substituted** and no second candidate was taken: one intake per
corpus cycle, and the refusal row is this cycle's honest product.  Re-declaring
`lean_cam_combi` at a verified origin is a **maintainer** call.

## The defect this cycle measured

Cycle 33 made the intake say *which act* a failure is.  It did not make it say
**which absence**, and the two are different facts about a declaration:

* **`flt`** (cycle 33): the declared path 404s, the **project root answers
  200**.  The project publishes; the path is wrong.  A re-declaration stays
  inside that project.
* **`lean_cam_combi`** (this cycle): the **bare origin** 404s.  The origin is
  wrong, and no path under it could be right.

Both cycles told those apart the same way — **by hand, with `curl`, before they
were allowed to record**.  That is a decision branching on machine-readable
state shipped as a paragraph, which CLAUDE.md's invariant forbids, so it ships
as a probe: `ABSENCE_SCOPES`, `origin_root`, `classify_absence_scope`, and
`_probe_origin_status` wired into **both** failure arms of `_fetch`.  The live
re-run now prints, with no curl session in front of it:

```
intake fetch RESOURCE-ABSENT [host-absent] (HTTP 404): https://yaeldillies.github.io/LeanCamCombi/blueprint/
  scope (https://yaeldillies.github.io/): the ORIGIN ITSELF SERVES NOTHING --
  the declared host answers the same absence at its root, so the declaration's
  origin is wrong and no path under it could be right
```

**The bound that keeps this a diagnosis and not URL-shopping**: the probe reads
the **origin root and nothing else**, exactly once.  It never walks
neighbouring paths and never proposes a substitute address — a path that
happened to serve HTML would be shopping wearing a diagnosis's clothes
(cycle 33's bound, restated as code and pinned by a source-inspecting tooth).
It runs only on an already-failed intake, so the network-at-intake bound holds,
and it fetches no bytes any downstream step sees.  An unreadable probe is
`scope-unknown` and **never disturbs the reading it refines**: the declared URL
answered 404, and that stands.

7 teeth, all network-free (the probe is injected), **mutation-verified in both
directions** — six mutations, each redding exactly its tooth:

| mutation | reds |
|---|---|
| collapse `host-absent` into `path-absent` | `…reads_as_HOST_absent` (+ the message tooth) |
| unreadable probe guesses `path-absent` | `…is_scope_unknown_and_never_guessed` |
| attach a scope to every reading | `test_only_an_ABSENCE_carries_a_scope` |
| stop printing the scope | `…reaches_the_MESSAGE_the_driver_actually_reads` |
| `_fetch` stops passing the probe | `test_the_live_fetch_wires_the_probe_in` |
| scope classifier walks candidate paths | `…touches_the_ORIGIN_ROOT_and_nothing_else` |

## What the declaration point is now worth, measured

Three rows were declared in one attended sitting, all marked *URL NOT
VERIFIED*.  All three have now been attempted: **`carleson` landed**, **`flt`
is path-absent**, **`lean_cam_combi` is host-absent**.  One in three.  That is
what an unverified declaration is worth against this loop's only verifier —
the driver's own fetch — and each miss costs a full cycle to learn.  It is also
the registry working as designed: the refused rows are evidence a
re-declaration can be written against, and no row was reordered, deleted or
rewritten.

## THE LOOP IS NOW BLOCKED (blocked, not dead)

`declared: candidate=0, example=1, intaken=8, refused=2` →
`registry-exhausted`.  Regenerated verdict:

```
supply-blocked: tower-class-only (1 open rows need attendance or lean-local:
  refusal-set-carrier [tower-class]);
new-corpus-intake (8 corpora already intaken, declaration: registry-exhausted
  -- NOT unattended-takeable);
refusal-retirement (77 distinct subjects in refused:* groups)
```

All four §3.2 supply paths, measured: (a) census-signal-ungating **0**;
(b) park-lifts **0** (ledger empty); (c) new-corpus intake **registry-exhausted**
— the lever that has moved the ready list twice now has nothing declared to
take; (d) refusal-retirement **77** subjects, whose exit is a PURCHASE-axis
call, and the one open row (`refusal-set-carrier`) is tower-class, which §3.1
rule 3 forbids an unattended session from taking.

**The exits the verdict itself names**: a maintainer appending one row to
`specs/mathsources/corpus_candidates.json` (name, source, adapter, project,
declared_by, rationale — and this cycle's finding is that the source is worth
verifying at declaration time, since the driver's fetch is otherwise the first
check), or an attended purchase of the tower-class row, or the `lean-hammer`
authoring ride already in flight on #208.

Both drivers firing and correctly finding nothing they may take is the loop
**working**; what a blocked verdict reports is a supply defect only a
maintainer decision clears.

## Bounds

No ceremony-reserved surface in the diff — `kernel/certs.py`, `TRUST.md`,
`buildloop/growth_protocol.py`, `setup.sh`, `ci/`, `.claude/`, `.github/`
untouched.  `tools/FgReflect.lean` byte-unchanged; Lean-free cycle, no lane
ridden.  P5 not promoted.  No park recorded or lifted.  Ledgers append-only.
No purchase priced.  Corpus unchanged, so no re-baseline and no lineage entry.
Intake stayed network-at-intake-only.
