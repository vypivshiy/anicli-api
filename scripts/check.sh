#!/bin/sh -e

export PREFIX=""
if [ -d '.venv' ] ; then
    export PREFIX=".venv/bin/"
fi
export SOURCE_FILES="anicli_api"

set -x

${PREFIX}ruff format $SOURCE_FILES
${PREFIX}ruff check $SOURCE_FILES
${PREFIX}pytest
# NOTE: invoke mypy via `python -m mypy` for cross-platform parity with check.ps1
${PREFIX}python -m mypy $SOURCE_FILES
