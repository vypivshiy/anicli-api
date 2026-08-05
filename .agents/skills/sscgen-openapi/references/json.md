# JSON схемы и `jsonify`

**Версия DSL:** 2.1  
**Последнее обновление:** 2026-04-07

`json` блоки описывают структуру JSON, который затем можно разобрать через
операцию `jsonify`.

## Объявление JSON схем

```kdl
json Author {
    name str
    goodreads_links str
    slug str
}

(array)json Quote {
    tags (array)str
    author Author
    text str
}
```

Типы полей:

| Тип | Описание |
|---|---|
| `str` | Строка |
| `int` | Целое число |
| `float` | Число с плавающей точкой |
| `bool` | Логическое значение |
| `null` | Null |
| `<Name>` | Ссылка на другую `json` схему |

Модификаторы:
- `(array)type` — массивное поле, например `(array)str`.
- `type?` — optional поле (значение или null), например `str?`.
- `@omitempty` — поле может отсутствовать в JSON. В типах помечается как `NotRequired` (Python) / optional (JSDoc).
- `@skip` — полностью исключить поле из генерации (не попадает в TypedDict / JSDoc).

Модификаторы можно комбинировать:

```kdl
json Item {
    url str?                          // optional через суффикс
    id str @omitempty                 // поле может отсутствовать
    inner Inner
    meta Meta @skip                   // исключить из типов
    item2 Item? @omitempty            // комбо: может отсутствовать + nullable
}
```

Правила:
- `json <Name> { ... }` объявляет схему.
- `(array)json <Name>` помечает схему как массив верхнего уровня.
- Поля могут ссылаться на другие `json` схемы по имени.

### Alias ключей

Если ключ в JSON неудобен как имя поля, можно задать alias:

```kdl
json Schema {
    context str "@context"
}
```

`context` — имя поля в схеме, `@context` — реальный ключ в JSON.

## Использование `jsonify`

```kdl
struct Main {
    @init {
        raw-json { raw; re JSON-PATTERN }
    }

    all-quotes { @raw-json; jsonify Quote }
    first-quote { @raw-json; jsonify Quote path="0" }
    author-slug { @raw-json; jsonify Quote path="2.author.slug" }
}
```

`jsonify` принимает один обязательный аргумент — имя схемы.

### path навигация

`path` позволяет перейти к элементам или полям:

- `""` — применить схему к результату целиком
- `"0"` — индекс массива
- `"field"` — доступ к полю
- `"0.author.slug"` — комбинированный путь

## JSON в атрибуте/свойстве HTML

JSON может лежать в атрибуте:

```kdl
struct DataState {
    json {
        css "#app"
        attr "data-state"
        // Важно: jsonify не делает unescape автоматически.
        // Если JSON экранирован HTML-энтитями, добавьте unescape перед jsonify.
        unescape
        jsonify AppState
    }
}
```
