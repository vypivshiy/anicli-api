# KDL Operations — Quick Reference

> Scoped to the **sscgen-dsl** skill (HTML scraping). Operations banned by
> skill constraints (`transform`, `css-remove`, `xpath`, `xpath-all`,
> `xpath-remove`) are intentionally omitted. For critical inline rules
> (regex capture-group requirement, predicate context matrix, `index` bug,
> CSS4 opt-in rule) → see `../SKILL.md`.

## Type System

| Type | Description |
|------|-------------|
| `DOCUMENT` | HTML element node |
| `LIST_DOCUMENT` | List of HTML nodes |
| `STRING` | String value |
| `LIST_STRING` | List of strings |
| `INT` | Integer |
| `LIST_INT` | List of integers |
| `FLOAT` | Float |
| `LIST_FLOAT` | List of floats |
| `BOOL` | Boolean |
| `OPT_STRING` | STRING \| null (via `fallback #null`) |
| `OPT_INT` | INT \| null |
| `OPT_FLOAT` | FLOAT \| null |
| `NESTED` | Nested struct result (terminal) |
| `JSON` | JSON deserialized result (terminal) |

`NESTED` and `JSON` are terminal — pipeline ends after `nested`/`jsonify`.
`fallback #null` converts `STRING`→`OPT_STRING`, `INT`→`OPT_INT`,
`FLOAT`→`OPT_FLOAT`.

---

## Operations

Format: `| Operation | Accept | Return | Notes |`.
String ops have **map semantics**: same op applied to each element of
`LIST_STRING`, returning `LIST_STRING`.

### Selectors

| Operation | Accept | Return | Notes |
|-----------|--------|--------|-------|
| `css "sel"` | DOCUMENT | DOCUMENT | CSS3 selector; first match |
| `css-all "sel"` | DOCUMENT | LIST_DOCUMENT | All matches |
| `css { "q1"; "q2"; ... }` | DOCUMENT | DOCUMENT | Pattern-match: 2+ selectors, try in order, first non-empty wins |
| `css-all { "q1"; "q2"; ... }` | DOCUMENT | LIST_DOCUMENT | Pattern-match form of `css-all` |
| `css { "q1"\n"q2"\n... }` | DOCUMENT | DOCUMENT | Block form, newline-separated children also OK |

Pattern-match rules:
- Either single argument OR block children — never both.
- Block requires **≥ 2 selectors**.
- If all selectors return empty → behaves like a failed single selector
  (error caught by `fallback` if present).

### Extract

| Operation | Accept | Return | Notes |
|-----------|--------|--------|-------|
| `text` | DOCUMENT | STRING | Direct text content |
| `text` | LIST_DOCUMENT | LIST_STRING | Map over list |
| `raw` | DOCUMENT | STRING | Unescaped HTML (innerHTML) |
| `raw` | LIST_DOCUMENT | LIST_STRING | Map over list |
| `attr "name"` | DOCUMENT | STRING | Single attribute; multi-value attrs like `class` joined with space |
| `attr "name"` | LIST_DOCUMENT | LIST_STRING | Map over list |
| `attr "n1" "n2" ...` | DOCUMENT | LIST_STRING | Multi-key: returns list, missing attrs skipped |
| `attr "n1" "n2" ...` | LIST_DOCUMENT | LIST_STRING | Map over list |

### String ops (STRING → STRING, LIST_STRING → LIST_STRING)

| Operation | Notes |
|-----------|-------|
| `trim [chars]` | Whitespace (or `chars`) from both ends |
| `ltrim [chars]` | Left side only |
| `rtrim [chars]` | Right side only |
| `normalize-space` | Collapse whitespace runs to single space, strip ends |
| `lower` | ASCII lowercase |
| `upper` | ASCII uppercase |
| `rm-prefix "substr"` | Remove `substr` if at start |
| `rm-suffix "substr"` | Remove `substr` if at end |
| `rm-prefix-suffix "substr"` | Both ends, same `substr` |
| `fmt "template"` | Substitute `{{}}` placeholder or define-name into template |
| `unescape` | Decode HTML entities (`&amp;` → `&`, etc.) |
| `split "sep"` | STRING → LIST_STRING (split by separator) |
| `join "sep"` | LIST_STRING → STRING (join with separator) |

`fmt` requires `{{}}` placeholder in template (or scalar define containing one).

### Regex ops

| Operation | Accept | Return | Notes |
|-----------|--------|--------|-------|
| `re #"(group)"#` | STRING | STRING | Extract first match of single capturing group |
| `re #"(group)"#` | LIST_STRING | LIST_STRING | Map over list |
| `re-all #"(group)"#` | STRING | LIST_STRING | All matches of single capturing group |
| `re-sub #"pattern"# "replacement"` | STRING | STRING | Substitute all matches; no group requirement |
| `re-sub #"pattern"# "replacement"` | LIST_STRING | LIST_STRING | Map over list |

⚠️ **`re` / `re-all` require exactly one capturing group** — linter rejects
0 or 2+ groups. Full regex rules (inline flags, no-match `SscRegexError`,
multiline `(?xs)` patterns, predicate-vs-op duality) → `../SKILL.md`
"Regex — critical rules".

### Replacements

| Operation | Accept | Return | Notes |
|-----------|--------|--------|-------|
| `repl "from" "to"` | STRING | STRING | Replace all occurrences of `from` with `to` |
| `repl "from" "to"` | LIST_STRING | LIST_STRING | Map over list |
| `repl { "f1" "t1"; "f2" "t2"; ... }` | STRING | STRING | Multiple replacements applied in order |
| `repl { ... }` | LIST_STRING | LIST_STRING | Map over list |

### Type conversions

| Operation | Accept | Return | Notes |
|-----------|--------|--------|-------|
| `to-int` | STRING | INT | Parse integer |
| `to-int` | LIST_STRING | LIST_INT | Map over list |
| `to-float` | STRING | FLOAT | Parse float |
| `to-float` | LIST_STRING | LIST_FLOAT | Map over list |
| `to-bool` | any scalar | BOOL | Truthiness conversion |

### Array ops

| Operation | Accept | Return | Notes |
|-----------|--------|--------|-------|
| `first` | LIST_* | scalar | First element (alias for `index 0`) |
| `last` | LIST_* | scalar | Last element (alias for `index -1`) |
| `index N` | LIST_* | scalar | Nth element (0-based, negative from end) |
| `slice N M` | LIST_* | LIST_* | Sublist from N (inclusive) to M (exclusive) |
| `len` | LIST_* | INT | Element count |
| `len` | STRING | INT | String length |
| `unique` | LIST_STRING | LIST_STRING | Deduplicate preserving order |

⚠️ **`css-all "..." ; index N` is unreliable for N > 0** — known ssc-gen bug
where values beyond index 0 may silently fall back to the first element.
Prefer `css "selector:nth-of-type(N)"`. Full note → `../SKILL.md` Constraints.

### Structured

| Operation | Accept | Return | Notes |
|-----------|--------|--------|-------|
| `nested StructName` | DOCUMENT | NESTED | Recurse into another struct; terminal |
| `jsonify SchemaName [path="..."]` | STRING | JSON | Deserialize JSON into typed schema; terminal |

`jsonify` `path` accepts dotted navigation:
- `""` — apply schema to whole value
- `"0"` — array index
- `"field"` — object key
- `"0.author.slug"` — combined

### Control

| Operation | Accept | Return | Notes |
|-----------|--------|--------|-------|
| `fallback <val>` | any | same / OPT_* | Default value on error; `#null` makes type optional |
| `fallback {}` | LIST_* | LIST_* | Empty list fallback |
| `filter { pred... }` | LIST_* | LIST_* (same) | Drop elements not matching predicates (AND) |
| `assert [msg] { pred... }` | any | same | Pass-through; raises `SscAssertionError` on failure |
| `match { pred... }` | DOCUMENT | (table field) | Select table row by key match; **first op in table field only** |

`assert` is caught by `fallback` when present. Implementation: `std_assert`
in Python, `_stdAssert` in JS — not Python's `assert` keyword, survives
`python -O`. Full assert guidance → `../SKILL.md` "Predicate context table".

---

## Predicates

Used inside `filter { }`, `assert { }`, `match { }`. Multiple predicates
inside one container combine with **AND**. Use `not` / `and` / `or` for
explicit grouping.

> **Predicate context matrix** (which predicates are valid in `match` vs
> `filter` vs `assert`) lives in `../SKILL.md` — included there because
> wrong-context usage is a common `E000` pitfall. The list below is the
> full predicate inventory without context restrictions.

### String predicates

```
eq "val" [val2 ...]              ne "val" [val2 ...]
starts "val" [val2 ...]          ends "val" [val2 ...]
contains "val" [val2 ...]        in "val" [val2 ...]
re #"pattern"#
```

Multi-argument forms (`eq "a" "b"`) test against **any** of the values (OR semantics).

### Attribute predicates

```
has-attr "name" [name2 ...]
attr-eq "name" "val" [val2 ...]
attr-ne "name" "val" [val2 ...]
attr-starts "name" "val" [val2 ...]
attr-ends "name" "val" [val2 ...]
attr-contains "name" "val" [val2 ...]
attr-re "name" #"pattern"#
```

### Text predicates

```
text-starts "val" [val2 ...]
text-ends "val" [val2 ...]
text-contains "val" [val2 ...]
text-re #"pattern"#
```

### Element predicates

```
css ".selector"                   (element has child matching CSS)
```

### Numeric predicates (assert only)

```
gt N    lt N    ge N    le N
```

### Length predicates (assert only)

```
len-eq N [N2 ...]                 len-ne N [N2 ...]
len-gt N                          len-lt N
len-ge N                          len-le N
len-range MIN MAX
```

All arguments must be non-negative integers.

### Regex predicates (assert only)

```
re-any #"pattern"#                (at least one list element matches)
re-all #"pattern"#                (all list elements match)
```

### Logic containers

```
not { ... }                       negation
and { ... }                       conjunction
or { ... }                        disjunction
```

---

## Struct Special Fields

| Field | Used in | Purpose |
|-------|---------|---------|
| `@doc "..."` | all | Documentation string |
| `@split-doc { ... }` | list, dict | Split document into items |
| `@pre-validate { ... }` | all | Assert before parsing |
| `@check <name> { ... }` | all | Boolean check method; pipeline must contain `to-bool` |
| `@init { ... }` | all | Pre-compute values once, reference via `@name` in fields |
| `@table { ... }` | table | Select the table element |
| `@rows { ... }` | table | Select rows |
| `@match { ... }` | table | Pipeline for key extraction |
| `@value { ... }` | table, dict | Pipeline for value extraction |
| `@key { ... }` | dict | Key extraction pipeline |
| `@request """..."""` | all | HTTP transport template (classmethod-like constructor; requires `--http-client` at generate) |

---

## Fallback Values

```kdl
fallback #null    // None / null -> makes type OPT_*
fallback #true    // True / true
fallback #false   // False / false
fallback 0        // integer zero
fallback 0.0      // float zero
fallback ""       // empty string
fallback {}       // empty list (for LIST_* types)
```

---

## CSS Selector Syntax Reference

Default target: **CSS3** (universal across bs4 / lxml / parsel / slax / native JS DOMParser).
Prefer a more precise selector over adding pipeline operations —
`[attr^=...]` at selection stage beats `re-sub` later in the pipeline.

> **CSS4** (`:not()`, `:is()`, `:where()`, `:has()`) is **opt-in only** —
> requires explicit user's prompt "CSS4 allowed". Backend support matrix
> at end of this section. Full rule + fallback strategy → `../SKILL.md`
> Constraints.

### Attribute selectors

| Selector | Meaning |
|----------|---------|
| `[attr]` | Has attribute `attr` |
| `[attr=val]` | Attribute equals `val` exactly |
| `[attr^=val]` | Attribute starts with `val` |
| `[attr$=val]` | Attribute ends with `val` |
| `[attr~=val]` | Attribute contains `val` as whitespace-separated word |
| `[attr\|=val]` | Attribute equals `val` or starts with `val-` (locale codes) |
| `[attr!=val]` | Attribute is not `val` (CSS4 / jQuery extension — backend support varies) |
| `[attr1][attr2]` | Multiple attribute filters (AND) |

Quote values when they contain whitespace or special chars:
`[href^="https://"]`, `[class~="active"]`.

### Combinators

| Combinator | Syntax | Meaning |
|------------|--------|---------|
| Descendant | `A B` | Any `B` inside `A` at any depth |
| Child | `A > B` | `B` is direct child of `A` |
| Adjacent sibling | `A + B` | `B` immediately follows `A` (same parent) |
| General sibling | `A ~ B` | `B` follows `A` somewhere (same parent) |
| Union | `A, B` | Matches `A` or `B` (deduped) |

### Structural pseudo-classes (CSS3)

| Pseudo-class | Meaning |
|--------------|---------|
| `:first-child` | First child of its parent |
| `:last-child` | Last child of its parent |
| `:only-child` | Only child of its parent |
| `:nth-child(n)` | Nth child (1-indexed); accepts `odd`, `even`, `2n`, `2n+1` |
| `:nth-last-child(n)` | Nth child counting from the end |
| `:first-of-type` | First child of its tag type among siblings |
| `:last-of-type` | Last child of its tag type among siblings |
| `:only-of-type` | Only child of its tag type among siblings |
| `:nth-of-type(n)` | Nth child of its tag type |
| `:nth-last-of-type(n)` | Nth of type, from end |
| `:empty` | No children (text nodes count as children) |
| `:root` | Document root (rarely needed in scraping) |

### CSS4 pseudo-classes (opt-in, backend-dependent)

| Pseudo-class | bs4 | lxml | parsel | slax | JS DOMParser |
|--------------|:---:|:----:|:------:|:----:|:------------:|
| `:not(simple)` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `:not(complex)` | ✓ | ✓ | ✓ | ✓ | partial |
| `:is(...)` / `:where(...)` | ✓ | ✓ | ✓ | ✓ | partial |
| `:has(> child)` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `:has(descendant)` | ✓ | ✓ | ✓ | ✓ | ✓ |

**When in doubt under CSS4**: use `[attr^=...]` filters, `filter {}` predicate,
or split into multiple `css { ... }` pattern-match selectors — all CSS3-only.

### Common patterns

```css
/* attribute prefix match — typical for pagination links */
a[href^="/page/"]
a[href^="https://example.com/"]

/* nth card in a list (avoids `index N` bug) */
.product-card:nth-of-type(3)

/* direct child vs descendant */
div.listing > .item          /* only direct children */
div.listing .item            /* any depth */

/* class contains word (CSS3, safer than `*=` for class matching) */
div[class~="active"]
a[rel~="next"]

/* empty text filter — useful for `:empty` checks */
span:empty
```

---

## See also

- **`../SKILL.md`** — critical inline rules (regex capture-group, predicate
  context matrix, `index` bug, CSS4 opt-in, no-transform/no-xpath constraints),
  workflow, struct types reference, linter loop.
- **`predicate-vs-op.md`** — disambiguating dual-meaning keywords (`re`, `css`)
  between pipeline ops (value transforms) and predicates (boolean checks).
- **`linter-errors.md`** — canonical linter error → fix mapping.
- **`examples/`** — full `.kdl` schemas for reference:
  - `booksToScrape.kdl` — `(list)struct`, price regex, `fallback`, URL `fmt`
  - `hackernews.kdl` — `(list)struct` with `@doc`, multi-struct composition
  - `imdbcom.kdl` — search results, `nested` composition, `css-all` field
  - `quotesToScrape.kdl` — `json` schema + `jsonify`, multiline `(?xs)` regex
  - `regexFallback.kdl` — `re` no-match + `fallback`, `re-all`, `@pre-validate`
