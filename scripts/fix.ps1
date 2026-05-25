$SOURCE_FILES = $env:SOURCE_FILES
$TEST_FILES = $env:TEST_FILES

uv run ruff format $SOURCE_FILES
uv run ruff check $SOURCE_FILES --fix --unsafe-fixes
uv run ruff format $TEST_FILES
uv run ruff check $TEST_FILES --fix --unsafe-fixes
uv run python scripts/cleanup_version_guards.py
