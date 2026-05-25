#!/bin/sh -e

export PREFIX="uv run "

set -x
${PREFIX}ruff format $SOURCE_FILES
${PREFIX}ruff check $SOURCE_FILES --fix --unsafe-fixes
${PREFIX}ruff format $TEST_FILES
${PREFIX}ruff check $TEST_FILES --fix --unsafe-fixes
${PREFIX}python scripts/cleanup_version_guards.py