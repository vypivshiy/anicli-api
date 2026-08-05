# REST DSL — Quick Reference

## `@request` body — two interchangeable formats

Both produce identical generated code. Pick whichever you have at hand.

| Raw HTTP | POSIX curl |
|---|---|
| `GET /users/{{id:int}} HTTP/1.1`<br>`Host: api.example.com` | `curl 'https://api.example.com/users/{{id:int}}'` |

Curl is especially convenient for **DevTools → Network → Copy as cURL (POSIX)**
paste-ins. Supported flags: `-X/--request`, `-H/--header`, `-d/--data/--data-raw`,
`--json`, `-u/--user`, `-F/--form`, `--data-urlencode`, `--compressed` (ignored).
Unsupported flags raise a parse error — strip them or rewrite as raw HTTP.

## `(rest)struct` — minimal vs full

### Minimal (single endpoint, no errors)

Raw HTTP form:
```kdl
json User { id int; name str }

(rest)struct Api {
    @request response=User """
    GET /users/{{id:int}} HTTP/1.1
    Host: api.example.com
    """
}
```

Equivalent curl form:
```kdl
(rest)struct Api {
    @request response=User """
    curl 'https://api.example.com/users/{{id:int}}'
    """
}
```
Both generate `Api.fetch(client, *, id: int) -> Ok[UserJson] | UnknownErr | TransportErr`.

### Full (multiple endpoints + errors + envelope unwrap)
```kdl
json User { id int; name str }
json UserList { users (array)User; total int }
json ApiError { message str }

(rest)struct Api {
    @doc "Users API — CRUD + pagination."

    @request name=get-user \
        response=User \
        doc="Fetch one user." \
        """
    GET /users/{{id:int}} HTTP/1.1
    Host: api.example.com
    Accept: application/json
    """

    @request name=list-users \
        response=UserList \
        doc="Paginated." \
        """
    GET /users?limit={{limit:int?}}&skip={{skip:int?}} HTTP/1.1
    Host: api.example.com
    Accept: application/json
    """

    @error 404 ApiError
    @error 500 ApiError
}
```

---

## Typed placeholders — full matrix

Syntax: `{{ NAME [:TYPE] [[]] [?] [|STYLE] }}`

- `NAME`  — `[A-Za-z][A-Za-z0-9_-]*`. `-` auto-converts (`page-num` → `page_num` / `pageNum`).
- `TYPE`  — `str | int | float | bool`. Default: `str`.
- `[]`    — array. Forbidden in URL path.
- `?`     — optional (generates `T | None = None`). Forbidden in URL path.
- `|STYLE`— `repeat | csv | bracket | pipe | space`. Requires `[]`. Default: `repeat`.

| Placeholder | Python signature | Sample URL |
|---|---|---|
| `{{id}}` | `id: str` | `.../{id}` |
| `{{id:int}}` | `id: int` | `.../{id}` |
| `{{flag:bool}}` | `flag: bool` | `?flag=true` |
| `{{q:str?}}` | `q: str \| None = None` | omitted if `None` |
| `{{page:int?}}` | `page: int \| None = None` | omitted if `None` |
| `{{tags:int[]}}` | `tags: list[int]` | `?tags=1&tags=2` |
| `{{tags:int[]\|csv}}` | `tags: list[int]` | `?tags=1,2` |
| `{{tags:int[]?\|csv}}` | `tags: list[int] \| None = None` | `?tags=1,2` or omitted |
| `{{tags:str[]\|bracket}}` | `tags: list[str]` | `?tags[]=a&tags[]=b` |
| `{{tags:str[]\|pipe}}` | `tags: list[str]` | `?tags=a\|b` |
| `{{tags:str[]\|space}}` | `tags: list[str]` | `?tags=a%20b` |

Parameter ordering in generated method:
- positional: `client` only
- keyword-only: required first, optional (`?`) last (PEP 3102 keyword-only).

Reuse rule: if the same `NAME` appears multiple times in one `@request`, every
occurrence must repeat the **identical full spec** (`{{id:int}}` and `{{id:int}}`,
not `{{id}}` and `{{id:int}}`).

---

## `@error` syntax and naming

Class/typedef name: `<PascalStruct>Err<Status>[<FieldPascal>]`.

### Syntax

```
@error <status:int> <SchemaName> [keys...] [key=value ...]
```

- Positional args after SchemaName → key **presence** check (`'key' in _body`)
- KDL properties → value **equality** check (`_body.get('key') == value`)
- Both can be mixed; same key in both is a lint error.

### Examples

| `@error` declaration in `struct DummyJsonApi` | Mode | Generated class |
|---|---|---|
| `@error 404 ApiError` | status-only | `DummyJsonApiErr404` |
| `@error 500 ApiError` | status-only | `DummyJsonApiErr500` |
| `@error 404 ApiError error` | key presence | `DummyJsonApiErr404Error` |
| `@error 200 ApiError error_code=#true` | value equality | `DummyJsonApiErr200ErrorCode` |
| `@error 404 ApiError error detail="msg"` | mixed | `DummyJsonApiErr404ErrorDetail` |

Universal variants (always emitted):
- `Ok[T]` — generic 2xx wrapper, `value: T`
- `UnknownErr` — undocumented status, `value: Any` (raw JSON or None)
- `TransportErr` — network/timeout/DNS, `status=0`, `value=None`, `cause: str`

Method return type:
```
Ok[<ResponseSchema>Json] | <Struct>Err<N1> | <Struct>Err<N2> | ... | UnknownErr | TransportErr
```

---

## Result variant fields

All variants share the same shape (portable across Python / JS / future Go-Rust):

| Field | Type | Ok | typed `<Struct>Err<N>` | UnknownErr | TransportErr |
|---|---|---|---|---|---|
| `is_ok` / `isOk` | bool | `True` | `False` | `False` | `False` |
| `status` | int | 2xx | declared status | the actual status | `0` |
| `headers` | `Mapping[str,str]` (lowercased) | yes | yes | yes | `{}` |
| `value` | `T` / `<Schema>Json` / `Any` / `None` | response | parsed error body | raw body | `None` |
| `cause` | str | — | — | — | repr of exception |

Header keys are always lowercase. Multi-value headers (e.g. `Set-Cookie`) are
last-wins — rare for REST APIs.

### Python usage
```python
r = Api.get_user(session, id=1)
if r.is_ok:
    print(r.value["name"])
elif isinstance(r, ApiErr404):
    print("not found:", r.value["message"])
elif isinstance(r, TransportErr):
    print("network:", r.cause)
else:                       # UnknownErr — e.g. 503
    print("unknown", r.status, r.value)
```

### JS usage
```js
const r = await Api.getUser(fetch, {id: 1});
if (r.isOk)            console.log(r.value.name);
else if (r.status === 404) console.log('nf:', r.value.message);
else if (r.status === 0)   console.log('transport:', r.cause);
else                       console.log('unknown', r.status, r.value);
```

---

## CLI reference

```bash
# lint (always run after every edit)
ssc-gen check schema.kdl                  # text output
ssc-gen check schema.kdl -f json          # JSON for automated fixing

# generate code (REST struct requires --http-client)
ssc-gen generate python schema.kdl -L bs4 --http-client httpx -o out/  # sync + async_fetch
ssc-gen generate js schema.kdl         --http-client fetch -o out/
ssc-gen generate js schema.kdl         --http-client axios -o out/
```

Languages: `python`, `js`. Python libs (`-L`): `bs4` (default) | `lxml` | `parsel` | `slax`. JS has no `--lib` (native DOMParser).
HTTP clients: Python — `httpx` (default, sync+async) | `aiohttp` (async only) | `requests` (sync only); JS — `fetch` (default) | `axios`.

Without `--http-client` the generator silently ignores `@request` — the resulting
file will not contain any HTTP methods.
