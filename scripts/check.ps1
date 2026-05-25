$ErrorActionPreference = "Stop"

$PREFIX = ""
if (Test-Path ".venv") {
    $PREFIX = ".venv\Scripts\"
}

$SOURCE_FILES = "anicli_api"

& "${PREFIX}ruff" format $SOURCE_FILES
& "${PREFIX}ruff" check $SOURCE_FILES
& "${PREFIX}pytest"
& "${PREFIX}mypy" $SOURCE_FILES
