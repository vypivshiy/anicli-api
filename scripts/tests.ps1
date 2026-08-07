$ErrorActionPreference = "Stop"

# Run e2e tests (hit real network).
# Configure proxy/headers via env before running, e.g.:
#   $env:ANICLI_PROXY = "socks5://user:pass@host:1080"
#   .\scripts\tests.ps1

$PREFIX = ""
if (Test-Path ".venv") {
    $PREFIX = ".venv\Scripts\"
}

if (-not $env:ANICLI_PROXY) {
    Write-Warning "ANICLI_PROXY is not set; http clients will connect directly (geo-gated targets like animego/kodik/aniboom/cdnvideohub may fail without a CIS/Baltics IP)."
}

& "${PREFIX}python" -m pytest -m e2e tests/e2e @args
