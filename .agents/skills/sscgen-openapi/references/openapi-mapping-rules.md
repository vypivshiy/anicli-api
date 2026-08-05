# OpenAPI → KDL Mapping Rules

## Type Mapping

| OpenAPI type | OpenAPI format | KDL type |
|---|---|---|
| `string` | *(any)* | `str` |
| `integer` | *(any)* | `int` |
| `number` | float / double | `float` |
| `boolean` | — | `bool` |
| `array` | — | `(array)<ItemType>` |
| `object` / `$ref` | — | `<SchemaName>` |

## Modifier Mapping

| OpenAPI condition | KDL modifier |
|---|---|
| Property NOT in schema's `required` array | Append `?` → `Type?` |
| `nullable: true` | Append `?` → `Type?` |
| `readOnly: true` | Include only in response schemas |
| `writeOnly: true` | Include only in request schemas |
| `default: <val>` | No KDL equivalent; document in `@doc` |
| `enum: [...]` | `str` (no enum type in KDL) |
| `format: date-time` | `str` (no date type) |

## Alias Rules

If a JSON key is not snake_case Python identifier, use the alias syntax:

```kdl
field_name Type "originalKey"
```

Apply aliases for:
- camelCase: `urlImagePreview` → `url_image_preview str "urlImagePreview"`
- hyphens: `created-at` → `created_at str "created-at"`
- Other non-identifier chars

## $ref Resolution

| $ref path | Resolution |
|---|---|
| `#/components/schemas/Name` (OpenAPI 3) | Use `Name` as json schema name |
| `#/definitions/Name` (Swagger 2) | Use `Name` |
| `#/components/responses/Name` | Unwrap → `content.*.schema.$ref` → recurse |
| `#/paths/...` | Resolve inline |
| Nested chains | Resolve transitively until reaching a schema object |

### allOf

Merge all referenced + inline properties into one flat `json` block.

### oneOf / anyOf

Not representable in KDL `json`. Pick the first variant. If variants share common fields,
create a union schema with those fields only.

### Inline anonymous objects

Extract to a named `json` schema. Generate PascalCase name from the property name.

## Endpoint → @request Format Selection

| Method | Body type | Format |
|---|---|---|
| GET | — | curl (one-liner) |
| POST | `application/json` | Raw HTTP |
| POST | `application/x-www-form-urlencoded` | curl `--data-urlencode` |
| POST | `multipart/form-data` | curl `-F` |
| PUT / PATCH | JSON | Raw HTTP |
| DELETE | — | curl |

## Placeholder Derivation

| OpenAPI parameter location | Placeholder rule |
|---|---|
| `in: path` | `{{name:type}}` — always required, no `?`, no `[]` |
| `in: query`, required | `{{name:type}}` |
| `in: query`, optional | `{{name:type?}}` |
| Request body (JSON) | Inline in JSON body: `"key": {{name:type}}` |
| Request body (form) | `--data-urlencode 'key={{name:type}}'` |

## Struct Naming

- From `info.title`: remove spaces/special chars, PascalCase.
- Example: `"Pet Store API"` → `(rest)struct PetStoreApi`
- Example: `"Animevost"` → `(rest)struct AnimevostApi`

## @request Name Derivation

From method + path: `name=<method>-<resource>`.

| Method + Path | KDL name |
|---|---|
| `GET /pets` | `list-pets` |
| `POST /pets` | `create-pet` |
| `GET /pets/{petId}` | `get-pet` |
| `PUT /pets/{petId}` | `update-pet` |
| `DELETE /pets/{petId}` | `delete-pet` |

## json Schema Ordering

Order by dependency (leaves first):

1. Leaf schemas (no sub-references)
2. Composite schemas (reference leaves)
3. Envelope schemas (reference composites)
4. Error schemas
5. Then the `(rest)struct`
