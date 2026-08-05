# Predicate vs Pipeline Op Disambiguation

Several DSL keywords have **dual meaning** depending on context. This file
disambiguates them so you don't confuse pipeline ops (transform values) with
predicates (return booleans inside containers).

## The dual-purpose keywords

| Keyword | As pipeline op (top-level field body) | As predicate (inside `assert`/`filter`/`match`) |
|---------|---------------------------------------|--------------------------------------------------|
| `re #"pat"#` | STRING → STRING — returns first capture group | Returns `true` if pattern matches; uses `re.search` semantics |
| `re-all #"pat"#` | STRING → LIST_STRING — returns all capture groups | Assert-only. Returns `true` if **all** elements in a list match |
| `re-any #"pat"#` | **NOT a pipeline op** | Assert-only. Returns `true` if **at least one** element matches |
| `re-sub #"pat"# "r"` | STRING → STRING — replaces matches | **NOT a predicate** |
| `css ".sel"` | DOCUMENT → DOCUMENT — selects child element | Returns `true` if element has a child matching selector |
| `xpath "//p"` | DOCUMENT → DOCUMENT | Returns `true` if element has a child matching XPath |

## How to tell which one you're writing

**Pipeline op** — appears in the **field body** at the top level:
```kdl
field_name {
    css ".title"       // pipeline op: DOCUMENT -> DOCUMENT
    text               // pipeline op: DOCUMENT -> STRING
    re #"(\d+)"#       // pipeline op: STRING -> STRING (must have 1 capture group)
    to-int             // pipeline op: STRING -> INT
}
```

**Predicate** — appears **inside** an `assert {}` / `filter {}` / `match {}` block:
```kdl
field_name {
    css ".items"
    assert {
        re #"^\d+$"#   // predicate: returns bool, no capture group required
        len-gt 0
    }
}
```

## Subtle cases

### `re` — capture group rule changes by context

| Context | Capture group requirement |
|---------|---------------------------|
| Pipeline op | **Exactly 1** capturing group required. The first group's value is returned. |
| Predicate | No group requirement. Pattern is tested via `re.search` semantics — match/no-match only. |

```kdl
field {
    text
    re #"(\d+)"#           // pipeline op: 1 group required, returns digits
    assert { re #"foo#" }  // predicate: 0 groups OK, just tests presence
}
```

### `re-all` — different return shape by context

| Context | Accept type | Returns |
|---------|-------------|---------|
| Pipeline op | STRING | LIST_STRING (all capture groups) |
| Assert-only predicate | LIST_STRING | BOOL — true iff every element matches |

```kdl
// pipeline op form — extract all numbers from a single string
codes { text; re-all #"\d+"# }  // ERROR: needs exactly 1 capture group
codes { text; re-all #"(\d+)"# } // OK: returns ["123", "456"]

// predicate form — assert every element in a list matches
codes {
    css-all ".code"
    text
    assert { re-all #"^[A-Z]{3}$"# }  // every code is 3 uppercase letters
}
```

### `css` — same syntax, different shape

| Context | Accept | Returns |
|---------|--------|---------|
| Pipeline op | DOCUMENT | DOCUMENT (first match) or LIST_DOCUMENT (with `css-all`) |
| Predicate | DOCUMENT | BOOL — true if element has matching child |

```kdl
// pipeline op form
title { css "h1"; text }       // select h1, extract text

// predicate form
container {
    assert { css ".badge" }    // element must have .badge child
    text
}
```

## Quick mental model

> If the keyword is **inside `{ }` belonging to assert/filter/match** → it's a
> predicate (returns bool). Otherwise → it's a pipeline op (transforms the value).

Predicates can be combined with `and`/`or`/`not` logic containers. Pipeline ops
cannot — they form a linear chain.
