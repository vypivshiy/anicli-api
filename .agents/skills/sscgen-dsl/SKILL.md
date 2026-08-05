---
name: sscgen-dsl
version: "2.2"
dsl_version: "2.0"
description: >
  Generate KDL Schema DSL (v2.0) scraper configs for **HTML scraping** from HTML
  pages and skill instructions. Covers struct types (item) / (list) / (table) /
  (dict), css selectors, extract / string / regex / array / cast pipelines,
  inline constants, transforms, jsonify, and the iterative linter loop.
  Use this skill whenever the user wants to: generate a .kdl schema file for HTML
  scraping, write KDL DSL for data extraction from HTML, work with css/css-all/
  text/attr/raw pipelines, fix linter errors in an HTML-scraping .kdl, or iterate
  on a KDL schema based on linter feedback.
  Trigger on mentions of "kdl", "KDL schema", "scraper schema", "DSL для скрапинга",
  "распарсить страницу", "вытащить из HTML", or whenever the user provides an HTML
  page + extraction task.
  **Do NOT use this skill for REST/JSON HTTP API clients (`(rest)struct`,
  `@request`, `@error`, typed placeholders for HTTP) — use the sibling skill
  `sscgen-rest` instead.** The two skills share the same DSL surface but solve
  different problems and should not be mixed.
---

# sscgen-dsl — Skill (HTML scraping)

> `version` above is this skill file's own version. `dsl_version` is the KDL
> Schema DSL syntax version this skill targets. Bump them independently —
> editing skill instructions does not imply a DSL syntax change, and vice versa.

Generate valid **KDL Schema DSL v2.0** configs for HTML scraping from:
- A **skill instruction** (what to extract and how)
- An **HTML page** (structure to inspect)
- Optionally: **linter output** (text or JSON) to fix errors

> **Scope: HTML only.** This skill covers `(item)struct / (list)struct / (table)struct / (dict)struct`
> with CSS-selector pipelines. For REST/JSON HTTP APIs (`(rest)struct`,
> `@request`/`@error`, typed `{{id:int}}` placeholders) → use the **`sscgen-rest`**
> skill, not this one. Don't mix REST endpoints into HTML schemas.

> ⚠️ **SKILL ACTIVATION CONTRACT — read before any tool call**
>
> The **first** tool call after skill activation MUST be one of:
> - `bash`: `ssc-gen scout -i <existing.html> --discover -f json` (if HTML already on disk)
> - `bash`: `curl -o <file.html> <URL>` followed immediately by `ssc-gen scout -i <file.html> --discover -f json`
>
> `Read` of any `.html` file is **FORBIDDEN** under this skill — no exceptions,
> no "the file is small enough" rationalisation, regardless of file size.
> Scout is the only sanctioned HTML inspection tool — see Step 1 for usage
> and rationale.

## Constraints (always apply)

- **`ssc-gen scout` only for HTML exploration — never `Read` raw `.html`.** See the activation contract above; this constraint has no exceptions.
- **CSS selectors only** — never use `xpath`, `xpath-all`, `xpath-remove`
- **No removal operations** — never use `css-remove`, `xpath-remove`. Also `css-remove`/`xpath-remove` do not support the block pattern-match form
- **No advanced operations** — never use `transform`, `json`/`jsonify` unless the user explicitly requests them
- **Single-file, self-contained schemas only** — never use `import`. Each site = one complete standalone `.kdl` file
- **Output filename = domain name.** `example.com` → `example.kdl`. If the domain starts with a digit (`[0-9]`), prefix with `n__`: `123movies.com` → `n__123movies.kdl`
- **No `define`** — inline all values directly into ops: `fmt "https://site/{{}}"`, `re #"pat"#`, `repl { One "1"; ... }`, `@request """..."""`
- **No `(rest)struct`**, no `@error` — if the response is JSON, switch to `sscgen-rest` (see **Scope boundary** below for detection signals)
- **`css-all "..." ; index N` is unreliable for N > 0** — the `index` operator has a known ssc-gen bug where values beyond index 0 may silently fall back to the first element. Use `css "selector:nth-of-type(N)"` instead (see Array ops section)
- **CSS3 selectors by default** — attribute selectors, structural pseudo-classes (`:nth-child`, `:first-child`, `:nth-of-type`, combinators). **CSS4 pseudo-selectors (`:not()`, `:is()`, `:where()`, `:has()`) ONLY when the user's prompt explicitly says "CSS4 allowed"** — backend support varies (bs4/lxml OK, JS DOMParser/slax partial). Prefer a smarter `[attr^=...]` filter or pipeline `filter {}` over CSS4 when in doubt.
- Prefer simple, readable pipelines
- If extraction can be done with a smarter CSS selector, do that instead of adding ops to the pipeline

---

## Scope boundary: HTML vs JSON endpoint

**Stay in `sscgen-dsl`** (this skill) when ANY is true:
- Response body is HTML (root is `<!DOCTYPE>`, `<html>`, `<body>`, etc.)
- Source is a static HTML page or server-rendered template
- Target data lives in DOM elements, attributes, or text nodes
- JSON appears **embedded** inside HTML: `<script type="application/ld+json">`,
  `<script type="application/json">`, `data-json="..."` attributes →
  use `jsonify` to deserialize after `css` + `raw`/`attr`

**Switch to `sscgen-rest` skill** when ANY is true:
- Response `Content-Type` is `application/json` (or body root is `{`/`[`, not `<!DOCTYPE`)
- URL pattern is `/api/v1/...`, `/v2/...`, ends with `.json`
- Need `(rest)struct`, `@error <status>` mappings, typed response schemas
- Multiple endpoints compose into a typed client (list → detail → action)
- User describes "API", "endpoint", "request body", "status codes"

**`@request` alone is NOT a signal** — both skills use `@request` to fetch data.
The discriminator is the **response body type** (HTML vs JSON), not the transport.

**Ambiguous cases — ask the user directly, don't guess.** Use this template:

> "This page exposes both an HTML view and a JSON response at `<url>`.
> Should I target `sscgen-dsl` (scrape the rendered HTML) or `sscgen-rest`
> (call the JSON endpoint directly)? REST is usually more stable if the JSON
> is the real data source."

Typical ambiguous cases:
- SPA initial HTML load that bootstraps from inline JSON → usually `sscgen-rest`
  if the JSON is the real data source, `sscgen-dsl` + `jsonify` if scraping SEO metadata
- Site exposes both HTML and JSON for the same resource → prefer `sscgen-rest`
  (cleaner, typed, less brittle) but confirm with the user first

---

## Input Modes

### Mode 1 — Generate from scratch
Inputs: skill instruction + HTML page URL or saved file
-> `curl -o page.html URL` → `ssc-gen scout -i page.html --discover -f json` (recon) → design selectors from `repeat_containers` + `common_descendants` → generate `.kdl`

### Mode 2 — Fix linter errors
Inputs: existing `.kdl` + linter output (text or JSON format)
-> Parse errors, locate affected fields, fix each one, re-emit corrected `.kdl`

### Mode 3 — Iterate
Inputs: existing `.kdl` + new requirements or HTML changes
-> Diff the requirements, update affected structs/fields only

---

## Generation Workflow

### Step 1 — Recon with `ssc-gen scout` (REQUIRED FIRST STEP)

Scout is the only sanctioned way to inspect HTML in this skill — see the
activation contract at the top of this file. It returns structured JSON
optimised for selector design, without dumping raw markup into context.
Two modes: **discover** (page overview) and **probe** (targeted filtering).

#### Step 1a — Discovery (FIRST CALL, ALWAYS)

```bash
ssc-gen scout -i page.html --discover -f json
```

One call, full page overview. Returns:

- `tag_stats` — top-20 tag frequencies
- `class_stats` — top-30 class frequencies (high count = repeating pattern)
- `id_stats` — top-10 id frequencies (when present)
- `data_attrs` — all `data-*` attribute names on the page (sorted, deduped)
- `repeat_containers` — top-10 groups of ≥2 sibling tags sharing the same
  `(tag, classes)` signature. **This is your list-struct candidate list.**
- `table_candidates` — `<table>` elements with pre-extracted row keys
  (from `<th>` cells, or first `<td>` of each row when no `<th>`)
- `page_summary` — `{has_table, has_embedded_json, container_count_estimate}`,
  derived from the sections above (use to quick-gate parsing strategy)
- `sample_normalized: true` — global flag: all `sample` values are
  whitespace-collapsed via `get_text(strip=True)`, NOT verbatim HTML.
  Don't write regex expecting raw `\n` / multi-space runs.

Each `repeat_container` entry includes:

```json
{
  "parent_selector": "div.row.test-items-container",
  "item_selector": "#main-list > div.item",
  "item_tag": "div",
  "item_classes": ["col-lg-4", "col-md-4", "col-xl-4"],
  "count": 6,
  "depth": 9,
  "single_link_item": false,
  "has_th_row": false,
  "single_label_child": false,
  "common_descendants": [
    {"tag": "h3",   "classes": ["card-title"],   "in_items": 6,
     "attrs": ["title", "itemprop"], "sample": ["Mercedes-Benz W123 280E 1955", "BMW 501", "Trabant 601"]},
    {"tag": "a",    "classes": ["card-head-url"], "in_items": 6,
     "attrs": ["href"], "sample": ["/product/123", "/product/124"], "sample_tail": ["/product/126"]},
    {"tag": "img",  "classes": ["card-img-top"], "in_items": 6,
     "attrs": ["src", "alt"], "sample": ["/images/product-123.png"]},
    {"tag": "p",    "classes": ["card-text"],     "in_items": 6,
     "max_per_item": 3, "sample": ["Year:  1955", "Country:  DE"]}
  ]
}
```

`common_descendants` is the **pre-computed field list** for the list-struct
body: every descendant that appears in ≥80% of the container's items, with
the union of attributes seen across items. Use `item_selector` (preferred —
anchored on a rare id/class ancestor, capped at 3 hops) as the
`@split-doc { css-all "..." }` selector, or fall back to combining
`parent_selector` + `item_classes` when present. Each descendant's
`.classes` map to field selectors; `data-*` and `href`/`src` in `attrs`
map directly to `attr.NAME` extractors.

**Reading each container field:**
- `item_selector` — short, stable CSS selector for the items themselves.
  Built by walking up to the nearest rare anchor (`#id` or a class
  appearing ≤5 times in the document), capped at 3 hops below. When
  `selector_stability: "fragile"` is present, the path is unreliable
  (no anchor found, or path too deep) — prefer `table_candidates`,
  a more specific descendant selector, or fall back to `parent_selector`
  + `item_classes`.
- `single_link_item`, `has_th_row`, `single_label_child` — cheap boolean
  hints about the item shape. `single_link_item=true` → bare-link nav
  list. `has_th_row=true` → table body (check `table_candidates` for
  keys). `single_label_child=true` → "label: value" pattern (consider
  splitting text from the `<strong>`/`<b>`/`<dt>`/`<label>` wrapper).
- `sample` — **list** of distinct values from the first ≤3 items (text
  content preferred, else first `href`/`src`/`title`/`alt`/`content`/
  `value` attr). Use to design regex/stripping without an extra probe:
  if sample is `["USD 228 511"]`, you know to `re-sub #"[^\d]"# ""`
  before `to-int`.
- `sample_tail` — list of distinct values from the last ≤3 items (after
  dedup against `sample_head`). Omitted when the list is too short to
  produce non-overlapping tail values. Catches edge-cases at list
  boundaries (last item often missing a field, different format, etc.).
- `max_per_item` — present only when >1; means this signature appears
  multiple times per row (e.g. `<p class="card-text">` for year/country/
  mileage). Use `:nth-of-type(N)` selectors to pick each instance, or
  `css-all` + `filter`/positional ops if order varies.
- `attrs` — omitted when empty (no extractable attributes on this tag).
- Sort order: **leaf tags first** (a/img/p/h1-h6/span/li/td/th/time/etc.),
  then coverage desc. Leaves carry extractable data; intermediate container
  `<div>`s sort last so they don't displace useful fields under the cap.

**What to look for:**
- `repeat_containers` — pick the one matching your list of interest; `count`
  tells you how many items to expect at runtime
- `class_stats` — high counts corroborate container choices; also surfaces
  utility classes worth filtering on (`page-link`, `next`, `active`)
- `data_attrs` — every entry is a potential `attr.NAME` field
- `id_stats` — single-occurrence ids usually mark page landmarks (header,
  footer, sidebar) → useful for an `(item)struct` entrypoint
- `json_signals` — embedded JSON containers. **If empty, skip this
  subsection entirely** — do not force JSON extraction where none exists.
  See **Reading `json_signals`** below for subtype → extraction pattern mapping

A single `--discover` call typically answers 80–100% of selector questions.
Drop to probe mode only when `--discover` doesn't surface a specific signal.

#### Reading `json_signals`

Each entry has `kind` (`script` | `attr`), `subtype`, `selector`, `snippet`
(first ~200 chars from the JSON open bracket), `container_kind`
(`object` | `array`), `size`, and — when the body parses as a JSON
object/array of objects — `top_level_keys` (up to 10 keys from the first
object; use to design `(rest)struct` field names without re-parsing).
Detection is **lax** — inspect the snippet before extracting; some
signals may be JS object literals (Alpine `x-data`, inline Vue) that
aren't strict JSON. `top_level_keys` absence means the body either
failed to parse or was a scalar/array-of-scalars.

| `subtype` | Meaning | Extraction pattern |
|-----------|---------|--------------------|
| `json-ld` | `<script type="application/ld+json">` — schema.org / SEO data | `css "script[type='application/ld+json']"; raw; jsonify SchemaName` |
| `json-mime` | `<script type="application/json">` — Next.js `#__NEXT_DATA__`, Nuxt dehydration | if `script_id` present: `css "script#<id>"; raw; jsonify SchemaName` else use `selector` directly |
| `js-var` | `var/let/const X = ...` or `window/globalThis/self.X = ...` — SPA hydration (quotes.toscrape.com pattern) | multiline verbose regex extracting `<var_name>` body, then `jsonify`. See `references/examples/quotesToScrape.kdl` |
| `bare-json` | untyped `<script>` whose body starts with `{` or `[` | `css "script:nth-of-type(N)"; raw; jsonify SchemaName` (use `--css "script" --fields path` probe to disambiguate N) |
| `attr-json` | attribute value on an element starts with `{` or `[` (e.g. `data-config`, `data-props`) | `css "<selector>"; attr "<attr>"; jsonify SchemaName` |

**Prefer JSON sources over CSS pipelines when available** — typed JSON is
more stable than DOM scraping. Especially:
- `json-ld` on e-commerce / news / product pages → schema.org `Product`,
  `Article`, `BreadcrumbList` give canonical fields
- `js-var` on SPA pages (React/Vue hydration blob) → server-side state is
  usually the "source of truth", ignoring it means scraping rendered HTML

For `js-var`, the `var_name` field tells you what to anchor the regex on.
Quote-stable extraction pattern (from `quotesToScrape.kdl`):

```kdl
re #"""
    (?xs)
    var\s+<var_name>\s*=\s*   # anchor: var NAME =
    (                         # capture group = jsonify input
        \[                    # array form (use \{ for object)
        .*
        \]
    )
    ;\s+for                   # trailing anchor (varies per site)
"""#
jsonify SchemaName
```

#### Step 1b — Targeted probes (only if `--discover` insufficient)

```bash
# regex on text (prices, dates, IDs) — CSS cannot express these
ssc-gen scout -i page.html --text '\$\d+\.\d{2}' --fields path -f json

# attribute regex
ssc-gen scout -i page.html --attr 'href=~^/product/\d+' --fields path -f json

# CSS + climb to parent container
ssc-gen scout -i page.html --css ".price" --up 2 --fields path -f json

# one-off extraction (no .kdl needed)
ssc-gen scout -i page.html --css ".product-card" \
    --fields attr.data-id,text -f json
```

Filters (AND-combine): `--text REGEX`, `--attr NAME[=VAL|=~REGEX]`, `--tag NAME`, `--css SEL`.
Modifiers: `-I` ignore-case, `-F` fixed strings, `-v` invert.
Pagination: `--limit N` (default 50), `--offset N`, `--snippet LEN` (default 200).
Exit codes: 0 on match, 1 on no match, 2 on error.

### Step 2 — Analyse the HTML

Before writing any KDL:
0. **Verify HTML response** — if the page body is JSON (`{`/`[` at root, `Content-Type: application/json`), stop and switch to `sscgen-rest`. This skill only handles HTML documents
1. Identify the **page type**: single item, list of items, table, or mixed
2. Find **repeating patterns** (cards, rows, list items) -> these become `(list)struct` structs
3. Find **key-value tables** -> `(table)struct` structs
4. Note attribute-rich selectors: use `[attr^=...]`, `[attr$=...]` etc. in CSS for precision
5. Note what data is available: text content, attributes, nested structures

### Step 3 — Plan the struct hierarchy

```
Main struct (type=item or entry point)
|-- @doc with page URL examples
|-- nested ListStruct   (if page has a list)
\-- nested TableStruct  (if page has a table)

ListStruct (type=list)
|-- @split-doc { css-all "<card selector>" }
|-- @pre-validate (optional, for robustness)
\-- fields...

TableStruct (type=table)
|-- @table / @rows / @match / @value
\-- fields with match { ... }
```

> **Top-down ordering is enforced**: a struct referenced via `nested` MUST be
> declared above the struct that uses it. The linter emits `E302` for forward
> references and `E300` for undefined targets. Helper/nested structs go first,
> the entrypoint struct goes last.
>
> ```kdl
> // WRONG — E302: Bar declared below Foo
> struct Foo { item { nested Bar } }
> struct Bar { x { text } }
>
> // OK — top-down
> struct Bar { x { text } }
> struct Foo { item { nested Bar } }
> ```

### Step 4 — Write fields

For each field, build the pipeline:
```
selector -> extract -> [string ops] -> [regex] -> [type conv] -> [fallback]
```

#### Field pipeline rules
1. **Start with a selector**: `css "..."` or `css-all "..."`
2. **Then extract**: `text`, `attr "name"`, or `raw`
3. **String ops** (optional, in order): `trim`, `lower`, `upper`, `normalize-space`, `rm-prefix`, `rm-suffix`, `rm-prefix-suffix`, `fmt`, `re-sub`, `repl`, `unescape`
4. **Type conversion** (optional): `to-int`, `to-float`, `to-bool`
5. **URL normalization** (if path may be relative): `fmt "https://site.com/{{}}"` — inline template, always convert relative paths to absolute URLs
6. **Fallback** (last): `fallback #null`, `fallback 0`, `fallback ""`

#### Inline vs block syntax
Both are valid — prefer **inline** for simple 1-3 op fields:
```kdl
// inline (preferred for short pipelines)
title { css "h1"; text }
date { css ".age[title]"; attr "title"; fallback #null }

// block (preferred for 4+ ops or when readability matters)
price {
    css ".price_color"
    text
    re #"(\d+(?:\.\d+)?)"#
    to-float
}
```

---

## Quick end-to-end example

**1. HTML (excerpt):**
```html
<div class="row test-items-container">
  <div class="col-lg-4">
    <h3 class="card-title" title="Mercedes-Benz W123 280E 1955">Mercedes-Benz W123 280E 1955</h3>
    <a class="card-head-url" href="/product/123">details</a>
    <p class="card-text">Year: 1955</p>
  </div>
  <!-- 5 more similar .col-lg-4 items -->
</div>
```

**2. `ssc-gen scout --discover` (relevant excerpt):**
```json
{
  "sample_normalized": true,
  "repeat_containers": [{
    "parent_selector": "div.row.test-items-container",
    "item_selector": "div.test-items-container > div",
    "item_tag": "div", "item_classes": ["col-lg-4"], "count": 6,
    "common_descendants": [
      {"tag": "h3", "classes": ["card-title"], "attrs": ["title"], "sample": ["Mercedes-Benz W123 280E 1955"]},
      {"tag": "a", "classes": ["card-head-url"], "attrs": ["href"], "sample": ["/product/123"]},
      {"tag": "p", "classes": ["card-text"], "sample": ["Year: 1955"]}
    ]
  }]
}
```

**3. Resulting `example.kdl`:**
```kdl
@doc "https://example.com/listing"

(list)struct Listing {
    @split-doc { css-all ".col-lg-4" }

    title { css ".card-title"; text }
    url   { css ".card-head-url"; attr "href"; fmt "https://example.com{{}}" }
    year  { css ".card-text"; text; re #"(\d{4})"#; to-int; fallback 0 }
}
```

This is the pattern: **scout JSON → pick `item_classes` for `@split-doc` →
one field per `common_descendants` entry → sanity-check with `sample`.**

---

## Struct Types Reference

### `(item)` (default) — single object
```kdl
struct Page {
    @doc "..."
    title { css "h1"; text }
    url   { css "link[canonical]"; attr "href" }
}
```

### `(list)` — list of objects
```kdl
(list)struct Product {
    @split-doc { css-all ".product-card" }

    name  { css ".title"; text }
    price { css ".price"; text; re #"(\d+\.?\d*)"#; to-float }
    url   { css "a[href]"; attr "href"; fallback #null }
}
```

> **List of scalar values** — when you need just `[tag1, tag2, ...]` (strings/attrs from many elements), use a `css-all` field in an `(item)struct`:
> ```kdl
> struct Page {
>     tags { css-all ".tag"; text }   // LIST_STRING
> }
> ```

### `(table)` — key-value HTML table
```kdl
(table)struct Info {
    @table { css "table.product-info" }
    @rows  { css-all "tr" }
    @match { css "th"; text; trim; lower }
    @value { css "td"; text }

    upc   { match { eq "upc" } }
    price {
        match { starts "price" }
        re #"(\d+\.\d+)"#
        to-float
    }
    stock {
        match { eq "availability" }
        to-bool
        fallback #false
    }
}
```

### `(table)` — non-table HTML (label+value in same element)

`(table)` also works for repeated elements where the label and value live inside the same container (e.g. `<div><strong>Label:</strong> value</div>`). Use `@match` to extract the label from a child element and `@value` with `re-sub` to strip the label prefix from the full text.

```kdl
// HTML structure:
// <div class="info-row"><strong>Registered: </strong>7 March 2015</div>
// <div class="info-row"><strong>Gender: </strong>Female</div>
// <div class="info-row"><strong>Publications: </strong>28</div>

(table)struct ProfileInfo {
    @table { css ".profile-data" }
    @rows  { css-all ".info-row" }
    @match { css "strong"; text; trim; lower }
    @value { text; re-sub #"^[^:]+:\s*"# ""; trim }

    registered {
        match { starts "registered" }
    }
    gender {
        match { starts "gender" }
        fallback #null
    }
    publications {
        match { starts "publications" }
        re #"(\d+)"#
        to-int
        fallback 0
    }
}
```

Use `nested` to compose with an `(item)` struct that extracts non-table fields (avatar, title, etc.):

```kdl
struct MainPage {
    display_name { css "h2"; text; trim }
    avatar { css ".avatar img"; attr "src"; fallback #null }
    info { nested ProfileInfo }
}
```

### `(dict)` — dynamic key-value map
```kdl
(dict)struct MetaTags {
    @split-doc {
        css-all "meta[property]"
        match { has-attr "property" "content" }
    }
    @key   { attr "property" }
    @value { attr "content" }
}
```

### `@check` — boolean check method

`@check` creates a public method that returns `bool` to verify the document matches expected structure. Pipeline must contain `to-bool`. Called manually before `parse()`.

```kdl
struct ProductPage {
    @check is-in-stock {
        css ".add-to-cart"
        to-bool
        fallback #false
    }

    title { css "h1"; text }
    price { css ".price"; text; to-float }
}
```

Generated as: `is_in_stock(self) -> bool` (Python) / `isInStock()` (JS).

---

## Key Operations — quick summary

Full operation signatures, type-compatibility tables, and CSS selector syntax
reference now live in `references/ops-quick-ref.md` — load it when you need
exact signatures. Summary of what's available:

- **Selectors**: `css`, `css-all`, `css { }` / `css-all { }` (pattern-match, try in order)
- **Extract**: `text`, `attr "name"`, `attr "n1" "n2" ...`, `raw`
- **String ops** (map over STRING/LIST_STRING): `trim` `ltrim` `rtrim` `normalize-space` `lower` `upper` `rm-prefix` `rm-suffix` `rm-prefix-suffix` `fmt` `re-sub` `repl` `split` `join` `unescape`
- **Type conversions**: `to-int`, `to-float`, `to-bool`
- **Array ops**: `first` `last` `index N` (⚠️ see Constraints — prefer `:nth-of-type(N)`) `slice N M` `len` `unique`
- **Control**: `fallback <val>`, `filter { <predicate> }`, `assert [msg] { <predicate> }`, `nested StructName`, `jsonify SchemaName [path="..."]`

### Regex — critical rules (keep inline, not just reference)

- `re #"(group)"#` and `re-all #"(group)"#` **require exactly one capturing
  group** — the linter rejects 0 or 2+ groups. `re-sub` has no group requirement.
- `re` raises `SscRegexError` on no match — catch with `fallback`.
- Inline flags (portable across Python/JS/Go): `(?i)` `(?m)` `(?s)` `(?x)`,
  combinable as `(?xs)` etc. Avoid `(?a)`, `(?u)`, `(?L)` — backend-specific.
- For multi-token/anchored patterns, prefer multiline raw-string with `(?xs)`:
  ```kdl
  re #"""
      (?xs)
      var\s+data\s*=\s*     # START ANCHOR
      (
          \[
          .*
          \]
      )
      ;\s+for
      """#
  ```
- `re #"pat"#` / `re-all #"pat"#` are **dual-meaning**: predicates (bool)
  inside `assert {}`/`filter {}`/`match {}`, ops (value transform) at the
  top level of a field pipeline. See `references/predicate-vs-op.md`.

### Predicate context table (critical — different contexts, different valid predicates)

| Predicate | `match {}` | `filter {}` | `assert {}` | Notes |
|-----------|:----------:|:-----------:|:-----------:|-------|
| `eq`, `ne`, `starts`, `ends`, `contains` | ✓ | ✓ | ✓ | string comparisons |
| `re #""#` | ✓ | ✓ | ✓ | regex match |
| `and`, `or`, `not` | ✓ | ✓ | ✓ | boolean combine |
| `has-attr`, `attr-eq`, `attr-ne`, `attr-contains`, `attr-starts`, `attr-ends`, `attr-re` | ✗ | ✓ | ✓ | attribute predicates |
| `text-re`, `text-starts`, `text-ends`, `text-contains` | ✗ | ✓ | ✓ | text predicates |
| `len-eq`, `len-ne`, `len-gt`, `len-lt`, `len-ge`, `len-le`, `len-range` | ✗ | ✗ | ✓ | length checks (assert only) |
| `re-all`, `re-any` | ✗ | ✗ | ✓ | quantified regex (assert only) |
| `css`, `xpath` | ✗ | ✓ | ✓ | structural predicates |

**Common pitfall**: `match { has-attr "href" }` → `E000`. Inside `@match` use
string-comparison predicates only; for attribute filtering use `filter {}`
or `assert {}` instead.

> **assert implementation**: emitted as `std_assert(cond, msg)` helper in Python, `_stdAssert(cond, msg)` in JS. Raises `SscAssertionError` — **not** the Python `assert` keyword, so it survives `python -O`. Caught by `fallback` when present.

> **When to use assert**: rarely. A single HTML page does not give enough statistical evidence to hard-code value-shape invariants. Prefer `fallback` for resilience; reach for `assert` only when failure is genuinely exceptional and should surface (e.g. pre-validation that the document has the expected root selector before parsing).

---

## Inlining patterns

Most ops accept literal arguments directly. Common patterns:

```kdl
// URL template
url { css "a"; attr "href"; fmt "https://example.com/{{}}" }

// Regex extraction / cleanup
year   { text; re #"(\d{4})"# }
clean  { text; re-sub #"[^\d.]+" "" }

// Replacement table
rating {
    css ".stars"
    attr "class"
    repl { One "1"; Two "2"; Three "3"; Four "4"; Five "5" }
    to-int
}
```

### `@request` — HTTP transport (classmethod-like constructor)

`@request` defines an HTTP request template attached to a struct. The generated
code is a **classmethod-like constructor**: caller passes an HTTP client +
method parameters, gets back a parsed struct instance.

**Generated signatures:**
- Python: `@classmethod def fetch(cls, client: HttpClient, **params) -> Self`
- JS (ES6 class): `static async fetch(client, params) -> <Struct>`

```kdl
struct MainPage {
    @request """
    GET /?p={{page-num}} HTTP/1.1
    Host: news.ycombinator.com
    Accept: text/html
    """
    news { css-all ".athing"; text }
}
```

Call site:
```python
page = MainPage.fetch(client, page_num=2)
```
```js
const page = await MainPage.fetch(client, { page_num: 2 });
```

Lowercase `{{name}}` placeholders resolve at runtime from method params.

> Requires `--http-client httpx|requests|aiohttp` (Python) or `--http-client fetch|axios` (JS) at `ssc-gen generate python|js`. Without it, `@request` is silently ignored.

---

## Iterative Lint Loop

After generating or editing a `.kdl` file, **always run the linter and iterate until clean**.

### Linter CLI

```bash
# text output (human-readable, default)
ssc-gen check schema.kdl

# JSON output (preferred for automated fixing)
ssc-gen check schema.kdl -f json

# multiple files or directory
ssc-gen check -f json schemas/
```

### Validation CLI (test against real HTML)

```bash
# test schema against HTML file (Python only; run always uses Python)
ssc-gen run schema.kdl:StructName -L bs4 -i page.html
ssc-gen run schema.kdl:StructName -L lxml -i page.html

# test from stdin (pipe HTML)
curl https://example.com | ssc-gen run schema.kdl:StructName -L bs4

# health check — verify selectors match elements
ssc-gen health schema.kdl:StructName -i page.html

# health check from stdin
curl https://example.com | ssc-gen health schema.kdl:StructName
```

## Codegen Targets

`ssc-gen run` and `ssc-gen generate <lang>` support multiple language targets:

| Target | Command | Default lib | Alt libs | Output style |
|--------|---------|-------------|----------|--------------|
| Python | `ssc-gen generate python` (default for `run`) | `bs4` | `lxml`, `parsel`, `slax` | dataclass-like, `from_html(html) -> Self` classmethod |
| JavaScript | `ssc-gen generate js` | native DOMParser | (none; `--lib` rejected) | ES6 class with `static fromHtml(html)` |
| Go | `ssc-gen generate go` | goquery + net/http | (none; `--lib` rejected) | struct + `FromHTML(html string) (T, error)` |

```bash
ssc-gen generate python schema.kdl -L bs4 -o out/   # -> schema.py
ssc-gen generate js     schema.kdl        -o out/   # -> schema.js
ssc-gen generate go     schema.kdl        -o out/   # -> schema.go + sscgen_runtime.go
```

All targets share the same `.kdl` schema — only codegen differs. For `@request`-bearing structs, pass `--http-client httpx|aiohttp|requests` (Python) or `--http-client axios|fetch` (JS). Go uses net/http exclusively (no `--http-client`).

### Loop algorithm

```
1. Write/update the .kdl file
2. Run: ssc-gen check -f json <file>
3. If output is empty / exit 0 -> DONE
4. If errors present -> fix all errors -> go to step 2
5. Repeat until no errors remain
```

**Never present the .kdl to the user until the linter reports zero errors.**
If after 5 iterations errors persist in the same location, explain the issue to the user and ask for clarification.

### Optional: runtime validation

After linting passes, if an HTML file is available:
```
6. Run: ssc-gen run schema.kdl:StructName -L bs4 -i page.html
7. Inspect output — verify fields are extracted correctly
8. If selectors miss elements: ssc-gen health schema.kdl:StructName -i page.html
```

---

### Parsing linter output

#### Text format
```
Error at line 12: type mismatch: expected STRING, got LIST_STRING
Warning at line 8: 'fmt' template is missing the '{{}}' placeholder
```
-> Map line numbers to the current file, fix errors (warnings are optional).

#### JSON format
```json
[
  { "line": 12, "col": 4, "level": "error", "message": "type mismatch: expected STRING, got LIST_STRING" },
  { "line": 8,  "col": 1, "level": "warning", "message": "'fmt' template is missing the '{{}}' placeholder" }
]
```
-> Filter `"level": "error"`, sort by line ascending, fix top-to-bottom (avoids line-number drift).

> Full error-to-fix table: see `references/linter-errors.md`.

---

## CSS Selector Tips

Default target: CSS3 (universal across bs4 / lxml / parsel / native JS DOMParser). Prefer a
more precise selector over adding pipeline operations. Full selector syntax
(attribute selectors, combinators, pseudo-classes) → `references/ops-quick-ref.md`.

**Rule of thumb:** if you're about to write `re-sub` just to strip a known
prefix/suffix from an attribute value, check first if a smarter `[attr^=...]`
or `[attr$=...]` selector can filter at the selection stage instead.

**CSS4** (`:not()`, `:is()`, `:where()`, `:has()`) — opt-in only, when the
user's prompt explicitly says "CSS4 allowed". bs4/lxml/parsel: OK. JS
DOMParser: `:has` OK, `:is`/`:where` partial. slax: `:not` simple-selector
only, rest unsupported. When in doubt, use `[attr^=...]` or `filter {}` instead.

---

## Output Format

Always emit a complete, lintable `.kdl` file:
1. `@doc` module docstring (page URL, usage notes)
2. Nested/helper structs (referenced by main) — **each `nested X` target must be declared above the caller (top-down, enforced by E302)**
3. Main entrypoint struct last

Filename: domain name (`example.kdl`), `n__` prefix if domain starts with a digit.

If fixing linter errors: emit the **full corrected file**, not just changed lines.

---

## See also

- **`sscgen-rest`** — for REST/JSON HTTP API clients (`(rest)struct`, `@request`, `@error`, typed placeholders). Share the same DSL surface but a different problem domain.
- **`sscgen-openapi`** — for converting OpenAPI/Swagger specs to `.kdl` REST clients deterministically.

---

## Reference Files

For detailed operation signatures, type compatibility tables, and full CSS
selector syntax:
-> See `references/ops-quick-ref.md`

For disambiguation between pipeline ops and predicates (`re`, `re-all`, `css`):
-> See `references/predicate-vs-op.md`

For the canonical linter error → fix mapping:
-> See `references/linter-errors.md`

For full KDL examples:
-> See `references/examples/`
- `booksToScrape.kdl` — `(list)struct` with price regex extraction, `fallback`, URL normalization via `fmt`
- `hackernews.kdl` — `(list)struct` with `@doc` HTML signature, multi-struct composition, `fmt` URL building
- `imdbcom.kdl` — search results page, `nested` struct composition, `css-all` field for genres
- `quotesToScrape.kdl` — `json` schema + `jsonify`, inline multiline regex with `(?xs)` flags, `path="0"` accessor
- `regexFallback.kdl` — `re` no-match + `fallback` recovery, `re-all` single-group extraction, `@pre-validate`