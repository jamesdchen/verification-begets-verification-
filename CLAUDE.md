# CLAUDE.md — stable router (invariants only)

This file states ONLY what the mining loop cannot stale: trust rules,
command names, and where live state comes from.  **Never put mutable state
here** — corpus counts, queue contents, purchase status, and "next actions"
all decay; they live in the derived brief and in PLAN_FRAGMENT §1 (which
house law updates every cycle).

## Where state lives (never in this file)

The **session brief** is the FIRST COMMAND of every driver session
(PLAN_FRAGMENT §3.1 rule 0), and can be regenerated at any time:

    python3 tools/session_brief.py

It derives era/counts/queue/lane-state from committed artifacts and quotes
PLAN_FRAGMENT §1 verbatim.  If the brief and any prose disagree, the brief's
derived header wins — recompute beats recollection.

## The invariants

- **Trust roots never grow by purchase or economics.**  The anti-list
  (kernel checkers, contract types, escape-gate blocklist, primitive ladder
  rungs — `buildloop/growth_protocol.py::ANTI_LIST`) changes only through
  the PLAN_REFLECT S4a→S4a′→S4b ceremony with explicit user sign-off.
  No session ever edits `kernel/certs.py` pins, `TRUST.md`, or the
  escape-gate blocklist as part of ordinary work.
- **One purchase per flywheel cycle** (PLAN_FRAGMENT §2); the re-census
  delta is committed in the same session that learns it.  A no-delta
  purchase is recorded evidence, never silently retried or widened.
- **Honesty rules**: the census reports signals, never fidelity verdicts;
  refusals are first-class demand data; parked items stay parked in
  writing; never distort a reading to force a green.
- **No local Lean in remote containers** (network policy).  Every
  Lean-touching step rides the CI lane; the driver protocol
  (PLAN_FRAGMENT §3.1) is lane-verdict-first / Lean-last.
- **Corpus intake is network-at-intake only**; everything downstream is
  offline, deterministic, LLM-free.

## Command index (stable names; each --help / docstring is authoritative)

| task | command |
|---|---|
| orient | `python3 tools/session_brief.py` |
| intake a corpus | `python3 tools/intake_corpus.py --name X --source URL --adapter blueprint\|sphinx` |
| re-census portfolio | `python3 tools/census_portfolio.py` |
| regenerate downstream artifacts | `python3 tools/regen_downstream.py` (resumable: `--from STEP`) |
| next corpus-era registration block | `python3 tools/measure_cluster_key.py --print-reregistration` |
| full gate | `python3 -m pytest tests/ -q` |

Corpus growth re-baselines exactly one file —
`specs/mathsources/registration.json` (append a lineage entry; its teeth in
`tests/test_corpus_registration.py` verify every number against the primary
artifacts).

## Test subsets (fast loops; full suite before every commit)

- fragment/grammar edits: `pytest tests/test_math_reading.py
  tests/test_math_eval.py tests/test_math_smt.py tests/test_math_compile.py
  tests/test_bigop_battery.py tests/test_math_prompt.py
  tests/test_operator_prompt_seam.py -q` (~10s)
- corpus growth: `pytest tests/test_corpus_registration.py
  tests/test_census_portfolio.py tests/test_mathsources_manifest.py -q`
  then the committed-artifact files the regen touched
- reflect/Lean-adjacent (local half): `pytest tests/test_fg_reflect_lean.py
  tests/test_reflect_shadow.py -q` (elaboration itself is CI-lane only)
- parallel full suite (sessions only; CI stays serial):
  `python3 -m pytest tests/ -q -n auto` if pytest-xdist is present
- parallel gate items (sessions only; CI stays serial):
  `python3 run_regression.py --fast --jobs 4` — items are already
  subprocess-isolated; CI instead shards via `--split pytest-<i>of<n>` /
  `demos-<i>of<n>`

## The worked example

The P1 purchase (commit `03e1a00`) is the complete template for a fragment
purchase: every bill item, the battery shapes, the registry row, and the
additive-proof reflect pattern.  The C2 closure (commit `355ca62`) is the
template for a census-sourced corpus addition end to end.
