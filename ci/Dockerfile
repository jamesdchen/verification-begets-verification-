# The CI toolchain image: every outsourced checker the `fast` gate needs,
# baked once instead of reinstalled on every push (Dafny ~1min, Kaitai jars
# ~1min, tree-sitter ~3min, pip closures ~1min -- the gate's dominant cost).
# Also the devcontainer image, so LOCAL DEV == CI (the divergence that let a
# demo regression hide: a thin container shows failures CI does not).
#
# Rebuilt by .github/workflows/toolchain-image.yml when this file changes.
# The Lean toolchain is DELIBERATELY not baked: it is pinned by .lean-pins,
# cached by the lean jobs, and ~5GB -- cache fits it better than layers.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
# util-linux: unshare/setpriv (the OS sandbox). openjdk+maven: Kaitai jars.
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-pip python3-venv git curl ca-certificates \
      util-linux bash coreutils gzip \
      openjdk-17-jre-headless maven \
      dotnet-sdk-8.0 \
    && rm -rf /var/lib/apt/lists/*

# Python deps into the SYSTEM interpreter: the sandbox executes payloads under
# /usr/bin/python3 as nobody with a cleared env, so this is the one
# interpreter that matters (the flloat closure is pinned -- unmaintained).
RUN pip3 install --break-system-packages --ignore-installed \
      hypothesis kaitaistruct "z3-solver==4.16.0.0" cvc5 tree_sitter pyyaml \
      pydantic jsonschema hypothesis-jsonschema pytest "matplotlib==3.11.0" \
    && pip3 install --break-system-packages --ignore-installed \
      "flloat==0.3.0" "pythomata==0.3.2" "lark-parser==0.12.0" "sympy==1.14"
# z3-solver is PINNED to the version whose Solver.to_smt2() printed the
# committed byte-identity golden (protocol_gen.bmc_smtlib embeds z3's own
# SMT-LIB rendering; the 5.0.0 major bump reformats it -- same incident
# class as matplotlib below, caught by tests/test_byte_identity.py DRIFT
# order:bmc_smtlib).  Bump ONLY together with a re-captured golden.
# matplotlib is PINNED to the version the committed golden figures were
# rendered under (the PNGs' own tEXt chunk records it): the *_fig golden
# tests byte-compare fresh renders, so an unpinned bump in the weekly image
# rebuild turns main red with zero repo changes (2026-07-20 incident: same
# commit green 06:51, red 08:18 across the rebuild).  Bump this pin ONLY
# together with re-captured goldens in the same commit.

# Dafny at the path common.DAFNY defaults to (/root/.dotnet/tools/dafny).
RUN dotnet tool install --global dafny --version "4.*"
ENV PATH="/root/.dotnet/tools:${PATH}"

# Kaitai Struct compiler 0.11 jars at CGB_KSC_CLASSPATH's default /opt/ksc/lib.
RUN mkdir -p /opt/ksc/lib && printf '%s\n' \
      '<project xmlns="http://maven.apache.org/POM/4.0.0">' \
      '  <modelVersion>4.0.0</modelVersion>' \
      '  <groupId>local</groupId><artifactId>ksc-fetch</artifactId><version>1</version>' \
      '  <dependencies>' \
      '    <dependency><groupId>io.kaitai</groupId><artifactId>kaitai-struct-compiler_2.13</artifactId><version>0.11</version></dependency>' \
      '  </dependencies>' \
      '</project>' > /opt/ksc/pom.xml \
    && cd /opt/ksc && mvn -q dependency:copy-dependencies -DoutputDirectory=/opt/ksc/lib

# tree-sitter CLI as a prebuilt binary at common.TREE_SITTER's default
# (/root/.cargo/bin/tree-sitter) -- no cargo build.
RUN mkdir -p /root/.cargo/bin \
    && curl -fsSL -o /tmp/ts.gz \
       https://github.com/tree-sitter/tree-sitter/releases/download/v0.22.6/tree-sitter-linux-x64.gz \
    && gunzip -c /tmp/ts.gz > /root/.cargo/bin/tree-sitter \
    && chmod +x /root/.cargo/bin/tree-sitter && rm /tmp/ts.gz

ENV CGB_KSC_CLASSPATH="/opt/ksc/lib/*"
WORKDIR /workspace
