"""Remove empty sys.version_info guard blocks left after ruff fixes.

Finds and removes blocks like:
    if sys.version_info >= (3, 11):
        pass
    else:
        pass

Also removes `import sys` if it becomes unused after cleanup.
"""

import re
from pathlib import Path

# Match: if sys.version_info >= (3, <digits>): <indent>pass else: <indent>pass
EMPTY_GUARD_RE = re.compile(r"\nif sys\.version_info >= \(3, \d+\):\n\s+pass\nelse:\n\s+pass\n")

IMPORT_SYS_RE = re.compile(r"^import sys\n", re.MULTILINE)

DIRS = [
    Path("anicli_api/player/parsers"),
    Path("anicli_api/source/parsers"),
]


def process_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if "sys.version_info" not in text:
        return False

    new_text = EMPTY_GUARD_RE.sub("\n", text)
    if new_text == text:
        return False

    # Remove unused `import sys`
    if "sys." not in new_text and "sys," not in new_text:
        new_text = IMPORT_SYS_RE.sub("", new_text)

    path.write_text(new_text, encoding="utf-8")
    return True


def main():
    changed = 0
    for d in DIRS:
        if not d.is_dir():
            print(f"skip {d} (not found)")
            continue
        for f in d.glob("*.py"):
            if process_file(f):
                print(f"cleaned: {f}")
                changed += 1
    print(f"\n{changed} file(s) cleaned")


if __name__ == "__main__":
    main()
