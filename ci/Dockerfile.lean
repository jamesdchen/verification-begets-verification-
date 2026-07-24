# Per-pin Lean toolchain image (cgb-lean-toolchain): elan + the pinned
# Mathlib checkout with prebuilt oleans (lake exe cache get) + the built
# lean4checker + setup.sh's sentinel, baked under /opt/lean-cache.
#
# The CI lean lanes prime $HOME/.elan and .lean from this image (one registry
# pull, ci.yml "Prime the Lean toolchain" step) instead of an actions/cache
# restore whose miss costs a full re-setup; with the sentinel in place,
# `setup.sh --with-lean --lean-only --skip-fresh` fast-paths to a no-op.
# Rebuilt per .lean-pins change by .github/workflows/lean-image.yml, tagged
# pins-<hash of .lean-pins> -- the lanes pull exactly their pin, so a stale
# image can never satisfy a new pin.
#
# python3 is present only as insurance for setup.sh edge paths; the baked
# --skip-fresh pass needs bash/curl/git alone (the one python-dependent step,
# the fresh recertification's import-set derivation, is skipped by design --
# fresh recertification must never ride a cached image).
FROM ubuntu:24.04
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    --no-install-recommends ca-certificates curl git python3 xz-utils zstd \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/lean-cache/build
COPY setup.sh .lean-pins ./
RUN bash setup.sh --with-lean --lean-only --skip-fresh \
    && mv /root/.elan /opt/lean-cache/elan \
    && mv .lean /opt/lean-cache/lean \
    && cd / && rm -rf /opt/lean-cache/build
