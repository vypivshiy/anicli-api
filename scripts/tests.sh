#!/usr/bin/env bash
set -euo pipefail

# Run e2e tests (hit real network).
# Configure proxy/headers via env before running, e.g.:
#   ANICLI_PROXY=socks5://user:pass@host:1080 ./scripts/tests.sh

PREFIX=""
if [ -d ".venv" ]; then
    PREFIX=".venv/bin/"
fi

if [ -z "${ANICLI_PROXY:-}" ]; then
    echo "warning: ANICLI_PROXY is not set; http clients will connect directly (geo-gated targets like animego/kodik/aniboom/cdnvideohub may fail without a CIS/Baltics IP)." >&2
fi

exec "${PREFIX}python" -m pytest -m e2e tests/e2e "$@"
