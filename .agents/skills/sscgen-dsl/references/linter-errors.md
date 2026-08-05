# Linter Errors — Canonical Fix Mapping

Complete reference of `ssc-gen check` error messages, their cause, and the fix.
The linter runs automatically before `generate`; `check` runs it standalone.

## Output formats

### Text format
```
Error at line 12: type mismatch: expected STRING, got LIST_STRING
Warning at line 8: 'fmt' template is missing the '{{}}' placeholder
```
→ Map line numbers to the current file, fix errors (warnings are optional).

### JSON format
```json
[
  { "line": 12, "col": 4, "level": "error", "message": "type mismatch: expected STRING, got LIST_STRING" },
  { "line": 8,  "col": 1, "level": "warning", "message": "'fmt' template is missing the '{{}}' placeholder" }
]
```
→ Filter `"level": "error"`, sort by line ascending, fix top-to-bottom (avoids line-number drift).

## Common errors and fixes

| Error message | Cause | Fix |
|---------------|-------|-----|
| `type mismatch: expected STRING, got LIST_STRING` | `css-all` feeds into op that needs single value | Switch to `css "selector:nth-of-type(N)"`, or use `first` / `last` after selector |
| `type mismatch: expected DOCUMENT, got STRING` | Selector used after `text`/`attr` | Reorder — selector must come before extract ops |
| `type mismatch: expected STRING, got INT` | e.g. `re` after `to-int` | Apply `re` before `to-int` |
| `unknown operation '...'` | Unknown op name or typo | Check spelling against operations list |
| `missing @split-doc` | `(list)struct` or `(dict)struct` without split | Add `@split-doc { css-all "..." }` |
| `missing match{}` | `(table)struct` field has no predicate | Add `match { eq "key" }` as first statement in field |
| `fallback value type mismatch` | `to-int` then `fallback "x"` | Use typed fallback: INT→`0`, FLOAT→`0.0`, BOOL→`#false`, any→`#null` |
| `filter requires list type` | `filter` used on scalar | Use `assert` instead, or ensure pipeline produces LIST_* |
| `match must be first operation` | `match {}` not at start of table field | Move `match { ... }` to first position |
| `'re' must have exactly 1 capture group` | Regex has 0 or 2+ groups | Ensure pattern has exactly one `(...)` group |
| `'re-all' must have exactly 1 capture group` | re-all pattern has 0 or 2+ groups | Add exactly one `(...)` group; use `(?:...)` for grouping without capturing |
| `'fmt' template missing '{{}}' placeholder` | fmt value lacks `{{}}` | Add `{{}}` where the value should be inserted |

## Iterative lint algorithm

```
1. Write/update the .kdl file
2. Run: ssc-gen check -f json <file>
3. If output is empty / exit 0 → DONE
4. If errors present → fix all errors → go to step 2
5. Repeat until no errors remain
```

**Never present the .kdl to the user until the linter reports zero errors.**
If after 5 iterations errors persist in the same location, explain the issue to
the user and ask for clarification.
