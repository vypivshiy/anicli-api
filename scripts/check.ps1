$ErrorActionPreference = "Stop"

$PREFIX = ""
if (Test-Path ".venv") {
    $PREFIX = ".venv\Scripts\"
}

$SOURCE_FILES = "anicli_api"

& "${PREFIX}ruff" format $SOURCE_FILES
& "${PREFIX}ruff" check $SOURCE_FILES
& "${PREFIX}pytest"
# NOTE: invoke mypy via `python -m mypy`. The bare mypy.exe launcher created by
# uv-venv fails with "Failed to canonicalize script path" on Windows.
& "${PREFIX}python" -m mypy $SOURCE_FILES
