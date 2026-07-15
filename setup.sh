#!/usr/bin/env bash
# Install the outsourced toolchain for the certified generator bootstrap.
# Idempotent-ish; safe to re-run. Tested on Ubuntu 24.04.
set -euo pipefail

echo ">> Python packages (Hypothesis, matplotlib, Kaitai runtime, Z3, CVC5, tree_sitter, PyYAML)"
pip3 install -q hypothesis matplotlib kaitaistruct z3-solver cvc5 tree_sitter pyyaml \
  pydantic jsonschema hypothesis-jsonschema pytest

echo ">> flloat 0.3.0 LTLf->DFA (Phase 1 monitor factory) -- PINNED: flloat is"
echo "   unmaintained, so pin it and its whole dependency closure exactly."
pip3 install -q "flloat==0.3.0" "pythomata==0.3.2" "lark-parser==0.12.0" "sympy==1.14"

# --lean-only (CI): skip the non-Lean toolchains below (Dafny/Kaitai/tree-sitter)
if [[ " $* " != *" --lean-only "* ]]; then
echo ">> dotnet SDK 8 + Dafny (Z3-backed verifier)"
if ! command -v dafny >/dev/null 2>&1 && [ ! -x "$HOME/.dotnet/tools/dafny" ]; then
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq dotnet-sdk-8.0 || true
  dotnet tool install --global dafny || true
fi

echo ">> Kaitai Struct compiler 0.11 (JVM CLI, supports --read-write) via Maven"
if [ ! -e /opt/ksc/lib/kaitai-struct-compiler_2.13-0.11.jar ]; then
  sudo mkdir -p /opt/ksc
  cat > /tmp/ksc-pom.xml <<'POM'
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>local</groupId><artifactId>ksc-fetch</artifactId><version>1</version>
  <dependencies>
    <dependency><groupId>io.kaitai</groupId><artifactId>kaitai-struct-compiler_2.13</artifactId><version>0.11</version></dependency>
  </dependencies>
</project>
POM
  sudo cp /tmp/ksc-pom.xml /opt/ksc/pom.xml
  (cd /opt/ksc && sudo mvn -q dependency:copy-dependencies -DoutputDirectory=/opt/ksc/lib)
fi

echo ">> tree-sitter CLI 0.26 via cargo"
if ! command -v tree-sitter >/dev/null 2>&1 && [ ! -x "$HOME/.cargo/bin/tree-sitter" ]; then
  cargo install tree-sitter-cli
fi
fi  # --lean-only

echo ">> done. Ensure PATH includes \$HOME/.dotnet/tools and \$HOME/.cargo/bin"
echo "   Override tool locations with CGB_DAFNY, CGB_TREE_SITTER, CGB_KSC_CLASSPATH if needed."

# ============================================================================
# F0.1 -- Lean 4 + pinned Mathlib toolchain (OPT-IN: ./setup.sh --with-lean).
# ============================================================================
# Network is ON here (setup time only, ⚠T9): every lake/elan operation that
# resolves dependencies or fetches oleans happens HERE; certification runs are
# sandbox-only where `unshare --net` enforces the offline invariant (⚠D3).
# Pins are single-sourced with common.py via the same CGB_* env names (common.py
# holds the canonical defaults); this block only reads/derives/asserts them.
if [[ " $* " == *" --with-lean "* ]]; then
  echo ">> [--with-lean] Lean 4 + pinned Mathlib (F0.1)"
  # --- pins (canonical defaults live in common.py; override via env) ---------
  PINS_FILE="$(cd "$(dirname "$0")" && pwd)/.lean-pins"
  _pin() { grep "^$1=" "$PINS_FILE" 2>/dev/null | head -1 | cut -d= -f2; }
  MATHLIB_COMMIT="${CGB_MATHLIB_COMMIT:-$(_pin MATHLIB_COMMIT)}"
  LEAN_TOOLCHAIN="${CGB_LEAN_TOOLCHAIN:-$(_pin LEAN_TOOLCHAIN)}"
  LEAN_MATHLIB="${CGB_LEAN_MATHLIB:-$PWD/.lean/mathlib}"

  echo ">> elan (Lean toolchain manager)"
  if ! command -v elan >/dev/null 2>&1 && [ ! -x "$HOME/.elan/bin/elan" ]; then
    curl -fsSL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh \
      | sh -s -- -y --default-toolchain none
  fi
  export PATH="$HOME/.elan/bin:$PATH"

  echo ">> clone Mathlib @ ${MATHLIB_COMMIT}"
  mkdir -p "$(dirname "$LEAN_MATHLIB")"
  if [ ! -d "$LEAN_MATHLIB/.git" ]; then
    git clone https://github.com/leanprover-community/mathlib4.git "$LEAN_MATHLIB"
  fi
  git -C "$LEAN_MATHLIB" fetch --all --tags
  git -C "$LEAN_MATHLIB" checkout --force "$MATHLIB_COMMIT"

  # --- ⚠D1: derive the toolchain from the pinned commit and ASSERT equality --
  DERIVED_TOOLCHAIN="$(tr -d '[:space:]' < "$LEAN_MATHLIB/lean-toolchain")"
  if [ "$DERIVED_TOOLCHAIN" != "$LEAN_TOOLCHAIN" ]; then
    echo "!! toolchain pin mismatch: lean-toolchain at ${MATHLIB_COMMIT} is" >&2
    echo "!!   '${DERIVED_TOOLCHAIN}' but common.LEAN_TOOLCHAIN pins" >&2
    echo "!!   '${LEAN_TOOLCHAIN}'.  Refusing (independent pins that drift =" >&2
    echo "!!   a silent hours-long Mathlib source build).  Fix the pin." >&2
    exit 1
  fi
  elan toolchain install "$LEAN_TOOLCHAIN"

  echo ">> lake exe cache get (fetch Mathlib's prebuilt oleans; network on)"
  ( cd "$LEAN_MATHLIB" && lake exe cache get )
  ( cd "$LEAN_MATHLIB" && lake build )

  # --- ⚠D2: lean4checker ships no binaries -- build from source at the tag ---
  #     equal to the derived toolchain version; build failure = setup failure,
  #     never a soft skip.
  LEAN4CHECKER_TAG="$(echo "$LEAN_TOOLCHAIN" | sed 's#.*:##')"  # e.g. v4.15.0
  L4C_DIR="$(dirname "$LEAN_MATHLIB")/lean4checker"
  if [ ! -d "$L4C_DIR/.git" ]; then
    git clone https://github.com/leanprover/lean4checker.git "$L4C_DIR"
  fi
  git -C "$L4C_DIR" fetch --all --tags
  git -C "$L4C_DIR" checkout --force "$LEAN4CHECKER_TAG"
  cp "$LEAN_MATHLIB/lean-toolchain" "$L4C_DIR/lean-toolchain"
  ( cd "$L4C_DIR" && lake build )

  # --- L4: recertify imported Mathlib oleans ONCE per pin (a long many-core --
  #     job); per-statement runs recheck only the scratch module.
  if [[ " $* " == *" --skip-fresh "* ]]; then
    echo ">> SKIPPING lean4checker --fresh (--skip-fresh; e.g. CI).  Imported"
    echo "   Mathlib oleans are NOT recertified in this run -- per L4 the"
    echo "   certificate names which; run setup WITHOUT --skip-fresh once per"
    echo "   pin on a many-core host to discharge it."
  else
    # --fresh-imports-only: the LOW-LATENCY L4 payment (minutes, not hours):
    # skip the whole-library replay and recertify only the pinned import
    # surface (shared-env + --fresh per module).  The whole-library replay --
    # every Mathlib.* olean -- remains the weekly scheduled job's business;
    # an imports-only run narrows the debt honestly and SAYS so.
    FRESH_IMPORTS_ONLY=""
    [[ " $* " == *" --fresh-imports-only "* ]] && FRESH_IMPORTS_ONLY=1
    echo ">> lean4checker over the pinned Mathlib (once per pin, L4)"
    # lean4checker's CLI (v4.15.0 Main.lean): a module argument is a PREFIX
    # that expands to every matching olean, so \`--fresh Mathlib\` resolves to
    # thousands of target modules and is CORRECTLY refused ("--fresh flag is
    # only valid when specifying a single module").  The L4 recertification is
    # therefore two-part:
    #   (1) the whole-library shared-env replay: \`lean4checker Mathlib\`
    #       (every Mathlib.* olean re-checked -- the standard whole-library
    #       recertification);
    #   (2) a --fresh single-module replay for each module in the pinned
    #       import surface (common.MATHLIB_IMPORTS -- the exact modules the
    #       statement-cert import_set names), each in a fresh environment.
    L4C_BIN="$L4C_DIR/.lake/build/bin/lean4checker"
    if [[ -n "$FRESH_IMPORTS_ONLY" ]]; then
      echo ">> --fresh-imports-only: whole-library replay DEFERRED to the"
      echo "   weekly scheduled run; recertifying the pinned import surface."
    else
      ( cd "$LEAN_MATHLIB" && lake env "$L4C_BIN" Mathlib ) \
        || { echo "!! lean4checker whole-library replay failed on the pinned Mathlib" >&2; exit 1; }
    fi
    MATHLIB_IMPORT_SET="$(python3 -c 'import common; print(" ".join(common.MATHLIB_IMPORTS))')"
    # (ledger defined below, before first use in the shared-env guard)
    FRESH_LEDGER="$(dirname "$LEAN_MATHLIB")/fresh_discharged.txt"
    mkdir -p "$(dirname "$FRESH_LEDGER")"; touch "$FRESH_LEDGER"
    _discharged() { grep -qxF "$1" "$FRESH_LEDGER"; }
    _mark() { _discharged "$1" || echo "$1" >> "$FRESH_LEDGER"; }

    if [[ -n "$FRESH_IMPORTS_ONLY" ]]; then
      if _discharged "shared-env:surface"; then
        echo ">> shared-env surface replay already discharged for this pin (ledger)"
      else
        echo ">> shared-env replay over the pinned import surface"
        ( cd "$LEAN_MATHLIB" && lake env "$L4C_BIN" $MATHLIB_IMPORT_SET ) \
          || { echo "!! lean4checker shared-env replay failed on the import surface" >&2; exit 1; }
        _mark "shared-env:surface"
      fi
    fi
    # --fresh demands exactly ONE resolved module, and lean4checker resolves a
    # module argument as a PREFIX over its whole olean SEARCH PATH -- a
    # directory-shaped import (e.g. Mathlib.Tactic.NormNum, with NormNum.Basic
    # etc. beneath it) expands to several oleans and is refused.  Replicate
    # the checker's own resolution: scan every LEAN_PATH root (a single build
    # dir guess missed roots before) and --fresh each exact module.
    # The once-per-pin LEDGER (defined above): every discharged or honestly-
    # partial module is recorded in a file inside the pin-keyed cache dir, so
    # a re-triggered job pays only the still-missing debt (checkpoint/resume
    # -- the same pattern as the bench).  Entry kinds: shared-env:surface,
    # fresh:<module>, timeout:<module> (deterministic, so never retried),
    # parent:<module> (prefix-ambiguous, uncheckable via --fresh at this tag).
    SP_DIRS="$(cd "$LEAN_MATHLIB" && lake env printenv LEAN_PATH | tr ':' '\n')"
    echo ">> LEAN_PATH roots:"; echo "$SP_DIRS" | sed 's/^/     /'
    PENDING=""
    for m in $MATHLIB_IMPORT_SET; do
      rel="${m//./\/}"
      mods="$(
        cd "$LEAN_MATHLIB" &&
        while IFS= read -r d; do
          [[ -n "$d" ]] || continue
          [[ -f "$d/$rel.olean" ]] && echo "$m"
          if [[ -d "$d/$rel" ]]; then
            find "$d/$rel" -name '*.olean' | while IFS= read -r f; do
              sub="${f#"$d/"}"; sub="${sub%.olean}"; echo "${sub//\//.}"
            done
          fi
        done <<< "$SP_DIRS" | sort -u
      )"
      [[ -n "$mods" ]] || { echo "!! no oleans found for pinned import $m (LEAN_PATH scan)" >&2; exit 1; }
      echo ">> $m resolves to $(wc -l <<< "$mods") exact module(s) on LEAN_PATH"
      while IFS= read -r mod; do
        # A module whose name prefixes another resolved module (e.g. the
        # parent Mathlib.Tactic.NormNum over NormNum.Basic) can NEVER satisfy
        # lean4checker's single-module rule at this tag -- its own name
        # prefix-expands.  --fresh the leaves; the parent is covered by the
        # shared-env replay, and we say so instead of failing.
        if grep -q "^${mod}\." <<< "$mods"; then
          _discharged "parent:$mod" || echo ">> $mod: --fresh impossible at "\
"this lean4checker tag (prefix-ambiguous parent); covered by shared-env replay"
          _mark "parent:$mod"
          continue
        fi
        if _discharged "fresh:$mod"; then
          echo ">> $mod: already fresh-discharged for this pin (ledger)"; continue
        fi
        if _discharged "timeout:$mod"; then
          echo ">> $mod: known deterministic-timeout partial (ledger; the "\
"budget is deterministic, so a retry cannot succeed -- not retried)"; continue
        fi
        PENDING="$PENDING $mod"
      done <<< "$mods"
    done

    if [[ -n "${PENDING// /}" ]]; then
      # PARALLEL fresh replays: each invocation is an independent process;
      # serial execution on an N-core host wastes (N-1)/N of the wall clock.
      # CGB_FRESH_PAR overrides (e.g. =1 to serialize, =2 if memory-tight:
      # each replay loads its module's whole import closure).
      PAR="${CGB_FRESH_PAR:-$(nproc)}"
      FRESH_TMP="$(mktemp -d)"
      export LEAN_MATHLIB L4C_BIN FRESH_TMP
      echo ">> fresh-replaying$(wc -w <<< "$PENDING" | tr -d ' ' | sed 's/^/ /') pending module(s), ${PAR}-way parallel (L4)"
      printf '%s\n' $PENDING | xargs -P "$PAR" -I{} bash -c \
        'out="$(cd "$LEAN_MATHLIB" && lake env "$L4C_BIN" --fresh "{}" 2>&1)"; st=$?;
         printf "%s" "$out" > "$FRESH_TMP/{}.out"; echo "$st" > "$FRESH_TMP/{}.st"' || true
      for mod in $PENDING; do
        st="$(cat "$FRESH_TMP/$mod.st" 2>/dev/null || echo 99)"
        if [[ "$st" == "0" ]]; then
          echo ">> lean4checker --fresh $mod: OK"
          _mark "fresh:$mod"
        elif grep -q "deterministic timeout" "$FRESH_TMP/$mod.out" 2>/dev/null; then
          # An honest INCOMPLETENESS (unverified-fresh within the kernel's
          # deterministic budget, not refuted): "an honest partial result
          # still narrows the debt".  Recorded so it is never re-paid.
          tail -2 "$FRESH_TMP/$mod.out"
          echo ">> $mod: fresh replay exceeded the kernel's deterministic"
          echo "   budget -- honest partial; the module stays covered by the"
          echo "   shared-env replay; its fresh debt is NARROWED, not discharged"
          _mark "timeout:$mod"
        else
          tail -20 "$FRESH_TMP/$mod.out" 2>/dev/null
          echo "!! lean4checker --fresh failed on $mod" >&2; exit 1
        fi
      done
    else
      echo ">> fresh surface fully discharged for this pin (ledger); nothing to replay"
    fi
  fi

  echo ">> [--with-lean] done.  Pins: MATHLIB_COMMIT=${MATHLIB_COMMIT}"
  echo "   LEAN_TOOLCHAIN=${LEAN_TOOLCHAIN}  (derived+asserted from lean-toolchain)"
  echo "   Mathlib checkout: ${LEAN_MATHLIB}"
fi
