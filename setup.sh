#!/usr/bin/env bash
# Install the outsourced toolchain for the certified generator bootstrap.
# Idempotent-ish; safe to re-run. Tested on Ubuntu 24.04.
set -euo pipefail

echo ">> Python packages (Hypothesis, matplotlib, Kaitai runtime, Z3, CVC5, tree_sitter, PyYAML)"
pip3 install -q hypothesis matplotlib kaitaistruct z3-solver cvc5 tree_sitter pyyaml

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
