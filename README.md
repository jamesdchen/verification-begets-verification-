# Certified Generator Bootstrap

Code generates code. An LLM is permitted to author **declarative
specifications only**. Generated code is trusted because it is **checked** —
never because of who produced it.

Verification begets verification, compiler-bootstrap style: a small fixed
kernel adjudicates; a library of generators (programs of type `Spec -> Code`)
does all code emission; trust flows downhill through provenance. The LLM is an
untrusted proposal engine writing spec files only.

> Build philosophy: **outsource everything that exists.** We did not build a
> verifier, a parser generator, a codec generator, or a DSL. The formal
> methods ecosystem already produced these. The new code here is the wiring,
> the trust ledger, and the measurement.

See **[TRUST.md](TRUST.md)** for the trusted computing base enumerated line by
line.

---

## The five hard constraints (and where they live)

1. **The task-time path contains no LLM calls.** `run/` goes spec → planner →
   generator chain → code, deterministically. `buildloop/llm.py` installs a
   guard (`CGB_TASK_TIME`) that makes any LLM call raise while a task run is
   in flight. Same spec + same registry state ⇒ byte-identical output.
2. **LLM output is only ever a spec.** `buildloop/validate.py` rejects any
   proposal containing general-purpose code before it reaches the kernel.
3. **Nothing is trusted without a kernel verdict.** `kernel/` is fixed, ~120
   lines, stateless, swap-ready — the only component trusted by fiat.
4. **All emitted code executes sandboxed** — `sandbox/` uses Linux namespaces
   (`unshare --net --mount --pid`), tmpfs over `/home` `/root` `/tmp`, a
   scratch-only writable dir, uid 65534, rlimits. Enforced at the OS level,
   during kernel checking and at task time. No effect typing.
5. **Every artifact records provenance** — which generator emitted it, from
   which spec, under which certificate, at which tier
   (`run/__init__.py`, `library/`).

## Two-tier trust model (the heart of the design)

- **Emit-check tier** (the on-ramp): a generator is admitted after light
  vetting, but **every output is individually checked at emission time**
  (translation-validation). For codecs the check is the round-trip contract
  `decode(encode(x)) == x` + malformed-input rejection, Hypothesis-fuzzed
  against the real emitted codec in the sandbox, cross-checked by a Dafny
  proof of the spec-level contract.
- **Universal tier**: a generator whose contract is verified for **all** valid
  specs (a Dafny proof over the generator itself). Its outputs need no
  emission check. `promote` attempts this upgrade; on success the tier flips
  and the planner prefers it.

**Dual-checker rule:** no single checker's verdict admits or promotes. Every
verdict needs two independent evidence channels to agree (Dafny/Z3 vs.
Hypothesis; or Z3 vs. CVC5 on one obligation). Disagreement is never
discarded — it is logged as a first-class event with full artifacts.

## What was outsourced, and from where

| Role | Tool | Used for |
|---|---|---|
| Proof / SMT | **Dafny 4.11** (Z3-backed) | codec contract model + universal generator theorem |
| Independent SMT | **Z3**, **CVC5** | same-obligation cross-check, disagreement detection |
| Property testing | **Hypothesis** | behavioral check of the real emitted artifact |
| Codec generator | **Kaitai Struct 0.11** (`--read-write`) | `.ksy` spec → Python encode/decode |
| Parser generator | **tree-sitter 0.26** | grammar → parser (also the meta-level demo) |
| LLM spec languages | `.ksy`, tree-sitter `grammar.js`, Dafny contracts | existing, documented, in-training-data |

The only formal artifact we authored is `generators/codec_model.dfy` — a
machine-checked model of the codec contract (round-trip + truncation
rejection), proven for every well-formed field list, plus the universal
static-offset theorem used for promotion. (EverParse was evaluated for
seeding the universal tier directly; it is not wired in this MVP — the Dafny
model plays that role instead.)

## Seed domain

Text/binary format codecs. Task specs describe record layouts (int fields with
endianness, magic bytes, fixed/length-prefixed/null-terminated strings,
literal/counted repeats, enums). The oracle is crisp (round-trip +
malformed-input rejection), specs are short and declarative, and layering
(field codec / framing) exercises composition.

---

## Components

```
common.py              canonical hashing, tool paths, trusted-tool runner
sandbox/               OS-level namespace jail for all emitted code
kernel/                check(artifact, contract) -> Certificate | ErrorTranscript
  backends.py            Hypothesis / Dafny / (Z3+CVC5) wrappers
  certs.py               content-hash-bound certificate & transcript records
library/               SQLite registry: tiers, emission records, provenance,
                         retirement, events, corpus, kernel cache, metrics
generators/            the Spec->Code machinery (all fixed, trusted-by-fiat only
  ksy_model.py           .ksy subset parser + feature-atom vocabulary
  codec_model.dfy        machine-checked codec contract model  (36 lemmas)
  dafny_gen.py           per-spec + universal proof-obligation generators
  harness_gen.py         Hypothesis harness derived from a spec (never the LLM)
  emitters.py            ksc / tree-sitter / cc adapters
  abnf_chain.py          ABNF -> (tree-sitter parser) -> ksy chain + AST mapper
planner/               deterministic unification over spec grammars
run/                   task-time runner (zero LLM; asserted)
buildloop/             coverage miss -> LLM spec -> kernel -> admit / refine
  llm.py                 the ONLY LLM client (headless `claude -p`)
  validate.py            pure-spec gate
  admission.py           vetting + MDL gate + subsumption
  mdl.py                 minimum-description-length accounting
  loop.py                steering policies + refinement
  promote.py             universal-tier upgrade
  disagreement_demo.py   engineered Z3/CVC5 split
metrics/               reach/cost/depth/tier-mix/DL/size logging, CSV, plots
  backlog.py             fixed ~200-spec backlog generator (seeded)
cgb.py                 CLI
```

## Library compression (MDL)

A candidate is admitted only if it **reduces total solution description
length** across the backlog (sum of chain length + spec size to cover each
spec; uncovered specs charged a fixed penalty), unless it covers previously
unreachable specs (logged as an *expansion event*). When a new generator
subsumes existing entries they are marked **retired** — kept for provenance,
excluded from planning. Total description length is a first-class metric and
trends down over a run even as reach rises.

## Counterexample corpus (`--corpus`, off by default)

Every kernel rejection stores the failing `(spec, input)` pair. With
`--corpus`, future candidates are screened against the corpus **before** fresh
adversarial generation. Its effectiveness is an open question, so it is
instrumented: the metrics log records the fraction of rejections caught by
replay vs. fresh generation, and the metrics suite is run with the flag on and
off (milestone 8).

---

## Running the milestones

Prerequisites are installed by `./setup.sh` (Dafny via dotnet, Kaitai via
Maven, tree-sitter via cargo, Python packages via pip). All commands below
write to `./artifacts` (override with `CGB_ARTIFACTS`). The build loop needs
an authenticated `claude` CLI on PATH.

```sh
export CGB_ARTIFACTS=$PWD/artifacts
```

**M1 — Kaitai on-ramp + mutation rejection.** Seed the opening library
(admitted only after a kernel emission check), drive one spec through the full
deterministic path, then show a mutated codec rejected.
```sh
python3 cgb.py seed
python3 cgb.py run specs/backlog/a_uint_be_000.ksy
python3 milestones.py m1        # includes the mutate-and-reject demo
```

**M2 — emission record + promotion.** Accumulate emission checks over 20 task
specs, then promote the fixed-uint generator to the universal tier (Dafny
proof + Hypothesis spec-fuzz); afterward emission checks stop and the planner
flips its preference.
```sh
python3 milestones.py m2
```

**M3 — build loop end to end.** A coverage miss becomes an admitted generator
from an LLM-authored spec (no human-edited code), with ErrorTranscript-driven
refinement when the first proposal fails.
```sh
python3 cgb.py build --policy frequency
```

**M4 — recursion demo.** tree-sitter (a generator) emits a parser that becomes
the input stage of a two-link chain (ABNF → parser → ksy → codec); provenance
depth ≥ 2.
```sh
python3 cgb.py build --policy frequency   # picks the ABNF miss once ksy is covered
python3 cgb.py run specs/backlog/k_abnf_000.abnf
```

**M5 — metrics + reach-vs-cost plot.** 20+ build-loop iterations under each
steering policy (`frequency` = most recurrent miss; `closure` = miss whose
resolution newly covers the most backlog specs), producing CSV + a matplotlib
reach-vs-cost plot with one curve per policy.
```sh
python3 milestones.py m5
```

**M6 — logged dual-checker disagreement.** A nonlinear-arithmetic obligation at
the edge of automatic decidability: Z3 proves it, CVC5 times out to `unknown`;
the kernel logs the split and issues no certificate.
```sh
python3 milestones.py m6
python3 cgb.py events dual-checker-disagreement
```

**M7 — subsumption.** A broader generator is admitted; narrower entries are
retired; total description length drops while reach does not.
```sh
python3 cgb.py events retirement
```

**M8 — corpus comparison.** Re-run the M5 metrics with `--corpus` on; report
the caught-by-replay fraction alongside the reach-vs-cost curves.
```sh
python3 milestones.py m8
```

`milestones.py all` runs the full sequence and writes every artifact under
`artifacts/` (logs, `metrics_*.csv`, `reach_vs_cost*.png`).

## Inspecting state

```sh
python3 cgb.py status                 # registry: generators, tiers, records
python3 cgb.py events [KIND]          # logged events (admission, promotion,
                                      #   retirement, expansion, disagreement, ...)
python3 cgb.py export-csv out.csv     # metrics log
```

## Independent second path (cross-implementation differential)

Round-trip (`decode(encode(x)) == x`) is a second evidence path the problem
hands you for free — encode vs. decode — but it has a structural blind spot:
a codec can be internally round-trip-consistent yet *wrong about the wire
format* (e.g. read and write a field in the wrong endianness), and round-trip
alone will never flag it. Catching that class requires a **genuinely
independent implementation** whose bugs don't correlate.

`generators/refcodec.py` is exactly that: a from-scratch reference codec that
shares no code with Kaitai. The kernel's `codec-differential` contract
certifies a codec via two independent channels — the Kaitai codec vs. the
reference codec (behavioral, byte-for-byte + cross-decode, sandboxed) and the
Dafny contract proof (logical). Independence lives in the translators, so
agreement is real N-version evidence, not one artifact checked twice.

```sh
python3 cgb.py differential specs/backlog/a_uint_be_000.ksy
python3 demo_differential.py   # shows a wrong-but-self-consistent codec that
                               # round-trip passes and the differential catches
```

The demo (`results/differential_demo.txt`) makes the point concrete: a
flipped-endian codec passes round-trip (it is self-consistent) yet the
differential catches the divergence with a witness input, and a mutated
Kaitai codec is cleanly rejected. This is path **(i)** from the design notes —
independence injected by a heterogeneous trusted artifact, which is the only
sound source of it (you cannot manufacture it by re-sampling the LLM). See the
`code-differential` route in `kernel/__init__.py`.

## Determinism & the no-LLM-at-task-time guarantee

`tests/` asserts that a task run produces byte-identical output across repeats
and that any attempted LLM call during a run raises. Run `python3 -m pytest
tests/ -q` (or `python3 tests/test_invariants.py`).
