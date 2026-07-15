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
  MATHLIB_COMMIT="${CGB_MATHLIB_COMMIT:-a1120f34fbf1c4c0f8e2b3d5c6a7e8f9012a3b4c}"
  LEAN_TOOLCHAIN="${CGB_LEAN_TOOLCHAIN:-leanprover/lean4:v4.15.0}"
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
  echo ">> lean4checker --fresh over the pinned Mathlib (once per pin, L4)"
  ( cd "$LEAN_MATHLIB" && lake env "$L4C_DIR/.lake/build/bin/lean4checker" --fresh ) \
    || { echo "!! lean4checker --fresh failed on the pinned Mathlib" >&2; exit 1; }

  echo ">> [--with-lean] done.  Pins: MATHLIB_COMMIT=${MATHLIB_COMMIT}"
  echo "   LEAN_TOOLCHAIN=${LEAN_TOOLCHAIN}  (derived+asserted from lean-toolchain)"
  echo "   Mathlib checkout: ${LEAN_MATHLIB}"
fi
