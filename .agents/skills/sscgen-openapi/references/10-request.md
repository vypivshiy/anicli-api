# 10. @request — встроенный HTTP конструктор

**Версия DSL:** 2.1  
**Последнее обновление:** 2026-04-17

`@request` — необязательная директива внутри `struct`. Описывает HTTP-запрос,
который нужно выполнить, чтобы получить HTML для этого парсера. Генератор
добавляет на класс метод `fetch()` с нужными параметрами.

Это **syntax sugar**: вместо `@request` можно всегда сделать запрос вручную и
передать HTML в конструктор. Парсер не знает о транспорте — он по-прежнему
получает одну HTML-страницу.

## Два формата записи

### POSIX curl

```kdl
struct ProductPage {
    @request """
    curl 'https://books.toscrape.com/catalogue/{{slug}}/index.html'
    """
    title { css "h1"; text }
}
```

### Сырой HTTP

```kdl
struct MainCatalogue {
    @request """
    GET /catalogue/page-{{page-num}}.html HTTP/1.1
    Host: books.toscrape.com
    Accept: text/html
    """
    title { css "h1"; text }
}
```

Оба формата эквивалентны: генератор нормализует их в одно представление.

## Placeholders

`{{name}}` — это параметры, которые передаются в `fetch()` при вызове.
Имена преобразуются в snake_case.

```kdl
@request """
GET /search?q={{query}}&page={{page-num}} HTTP/1.1
Host: example.com
"""
```

Генерирует (Python, httpx):

```python
@classmethod
def fetch(cls, client: httpx.Client, *, query: str, page_num: str) -> "StructName":
    ...
```

Без placeholders — запрос статический, `fetch` принимает только `client`.

### Типизированные плейсхолдеры

По умолчанию каждый `{{name}}` — обязательный `str`. Расширенный синтаксис задаёт тип, массив, опциональность и способ сериализации массива:

```
{{ NAME [:PRIM] [[]] [?] [|STYLE] }}

NAME   = [A-Za-z][A-Za-z0-9_-]*        первый символ — буква; `-` автоконвертируется
PRIM   = str | int | float | bool       default: str
STYLE  = repeat | csv | bracket | pipe | space   только при []; default: repeat
```

| Плейсхолдер | Python signature | URL (при `tags=[1,2]`) |
|---|---|---|
| `{{id}}` | `id: str` | `.../{id}` |
| `{{id:int}}` | `id: int` | `.../{id}` |
| `{{q:str?}}` | `q: str \| None = None` | опущен если `None` |
| `{{tags:int[]}}` | `tags: list[int]` | `?tags=1&tags=2` (repeat) |
| `{{tags:int[]?\|csv}}` | `tags: list[int] \| None = None` | `?tags=1,2` |
| `{{tags:int[]\|bracket}}` | `tags: list[int]` | `?tags[]=1&tags[]=2` |

Порядок параметров: required — первыми, optional (с `?`) — последними (PEP 3102 keyword-only).

**Ограничения** (проверяются линтером):
- `[]` и `?` запрещены в URL path — только query/headers/body
- style `|...` требует `[]`
- все повторные вхождения одного `NAME` должны иметь идентичную полную спецификацию
- имя не должно совпадать с ключевыми словами Python/JS (`class`, `return`, …)

## Генерация: выбор HTTP клиента

Флаг `--http-client` при генерации:

```bash
# Python: httpx (sync + async)
ssc-gen generate python schema.kdl -L bs4 -o out/ --http-client httpx

# JS: fetch (по умолчанию)
ssc-gen generate js schema.kdl -o out/

# JS: axios
ssc-gen generate js schema.kdl -o out/ --http-client axios
```

При `--http-client httpx` генерируются два метода: `fetch()` и `async_fetch()`.

Без `--http-client` методы `fetch` не генерируются, `@request` игнорируется.

## response-path и response-join

Если ответ сервера — JSON с HTML внутри, можно указать путь до нужного поля:

```kdl
@request response-path="payload.html" """
POST /api/page HTTP/1.1
Host: example.com
Content-Type: application/json

{"id": "{{id}}"}
"""
```

Если путь разрешается в список строк:

```kdl
@request response-path="chunks" response-join="\n" """
GET /api/doc/{{id}} HTTP/1.1
Host: example.com
"""
```

## define для @request

Длинный запрос можно вынести в `define`:

```kdl
define HNEWS-REQ="""
GET /?p={{page-num}} HTTP/1.1
Host: news.ycombinator.com
Accept: text/html
"""

struct MainPage {
    @request HNEWS-REQ
    news { css-all ".athing"; text }
}
```

Правило то же, что и для остальных скалярных define: это подстановка строки в аргумент.
Placeholders (`{{...}}`) внутри работают как обычно.

## Несколько struct с @request в одном файле

Каждый `struct` независим. `@request` задаётся на уровне struct, не модуля:

```kdl
struct ListPage {
    @request """
    GET /catalogue/page-{{page-num}}.html HTTP/1.1
    Host: books.toscrape.com
    """
    books { nested BookCard }
}

(list)struct BookCard {
    @split-doc { css-all ".product_pod" }
    title { css "h3 a"; attr "title" }
}
```

`BookCard` не имеет `@request` — он получает HTML через `nested` из `ListPage`,
а не по отдельному запросу.

## Тип возврата для `(rest)struct`

>[!note] О swagger openapi
> OpenAPI отличный стандарт, когда **автор API сам документирует свой
> backend**: на входе известная схема, на выходе формальный контракт.
> Reverse-engineering идёт в обратную сторону — на входе пара curl-запросов
> из DevTools и пример JSON-ответа, и из этого нужен типизированный клиент.
> Готового спека для скрапинг-таргета обычно нет, а писать его вручную —
> лишний слой работы поверх тех же данных.
>
> Поэтому реализован минимальный синтаксис, принимающий ровно то, что есть
> после открытия Network-вкладки: raw HTTP / curl + json-схема ответа.
>
> Если endpoint'ов десятки и нужен формальный контракт —
> снимите трафик через [mitmproxy2swagger](https://github.com/alufers/mitmproxy2swagger)
> и сгенерируйте клиент любым openapi-generator'ом
> (опционально с LLM-помощью для разметки схем).

REST-методы возвращают **Result-значение** вместо того чтобы бросать
исключение. Это единообразно для всех target-языков (Python/JS/будущие Go,
Rust) и сохраняет точную типизацию `@error`-схемы.

### Форма Result

| Вариант | Когда | Поля |
|---|---|---|
| `Ok[T]` | HTTP 2xx | `is_ok=True`, `status`, `headers`, `value: T` |
| `<Struct>Err<Status>` | объявленный `@error <status>` | `is_ok=False`, `status`, `headers`, `value: <Schema>Json` |
| `UnknownErr` | статус вне списка `@error` | `is_ok=False`, `status`, `headers`, `value: Any` (raw JSON или None) |
| `TransportErr` | сеть/таймаут/DNS | `is_ok=False`, `status=0`, `headers={}`, `value=None`, `cause: str` |

Все варианты имеют одинаковую структуру с полями `is_ok`/`status`/`headers`
/`value` — дизайн специально сделан портируемым на любой target.

### Python

```python
r = DummyJsonApi.get_product(session, id=1)
if r.is_ok:
    print(r.value["title"])          # value: ProductJson
    print(r.headers.get("x-ratelimit-remaining"))
elif isinstance(r, DummyJsonApiErr404):
    print("not found:", r.value["message"])  # value: ApiErrorJson
elif isinstance(r, TransportErr):
    print("network failed:", r.cause)
else:  # UnknownErr — напр. 503
    print("unexpected status", r.status, r.value)
```

Метод **никогда не бросает** — все HTTP-, парсинг- и транспортные ошибки
попадают в соответствующий Err-вариант.

### JS/TS

```js
const r = await DummyJsonApi.getProduct(fetch, {id: 1});
if (r.isOk) {
    console.log(r.value.title);
    console.log(r.headers['x-ratelimit-remaining']);
} else if (r.status === 404) {
    console.log('not found:', r.value.message);  // ApiErrorJson
} else if (r.status === 0) {
    console.log('transport:', r.cause);
} else {
    console.log('unknown', r.status, r.value);
}
```

IDE narrow'ит через literal-поля `isOk: true/false` и `status: 404`.

### Headers

- Ключи всегда в lowercase (нормализуется на стороне клиента), значения — str.
- Multi-value headers (напр. `Set-Cookie`) — last-wins. Для REST-API
  крайне редкий случай.

### Именование Err-подклассов

```
<PascalStructName>Err<Status>[<FieldPascal>]
```

- `@error 404 ApiError` в struct `DummyJsonApi` → `DummyJsonApiErr404`
- `@error 200 field="error_code" ApiError` → `DummyJsonApiErr200ErrorCode`

### Внутренняя структура модуля

Для устранения дублирования в REST-методах генерируются два приватных
helper'а:

- **`_parse_response(resp)`** (на уровне модуля) — извлекает
  `(status, headers, body)` из ответа HTTP-клиента. В JS-таргете две версии:
  `_parseResponse` для `fetch` и `_parseResponseAxios` для axios (axios
  заранее парсит JSON и возвращает `headers` объектом).
- **`_dispatch_err(status, headers, body)`** (static-метод каждого
  `(rest)struct`) — маршрутизация по объявленным `@error` в нужный
  Err-подкласс плюс `UnknownErr` для нераспознанных статусов. Возвращает
  `None` для 2xx (или типизированный Err при сработавшем field-discriminator).

Это детали реализации. Подклассы генерируемых классов (Python) могут их
переопределять — например, чтобы добавить нестандартную логику обработки
ошибок — но напрямую модифицировать сгенерированный файл не следует: при
перегенерации правки теряются.

## Что @request не делает

- Не управляет пагинацией — это задача вызывающего кода.
- Не задаёт ретраи, таймауты, куки сессии — конфигурируйте клиент снаружи.
- Не привязывает модуль к конкретному HTTP-клиенту на уровне импортов.
  Импорты в generated module минимальны.
