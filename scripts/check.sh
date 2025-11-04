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
${PREFIX}mypy $SOURCE_FILES
