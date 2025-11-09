# Конфигурации

Иструкции как реализовать парсеры и api клиенты для проекта

Зачем такой overengineering?

![img](assets/image.png)

ref: https://gunshowcomic.com/513

Большинство неофициальных API лишены аннотаций и документации, из-за чего их реализация становится сложной и неочевидной. При любых изменениях такие интерфейсы приходится исследовать заново, что приводит к значительным затратам времени на реверс-инжиниринг.

Для улучшения поддержки и частичной автоматизации реализуется генерация модулей с аннотациями объектов.

## Базовые требования к модулям для anicli-api 

* поддержка python 3.8 (на момент написания не полностью похоронили основные модули, возможно в будущем будет поддержка прекращена)
* упрощённое документирование реализаций парсеров:
  * REST API — через swagger
  * SSR — через selector schema codegen
* базовое аннотирование объектов (API + web scraping)
* использование `TypedDict` как компромисса:
  * остаётся обычным dict
  * даёт IDE-подсказки
  * не требует зависимостей (pydantic и т.п.)
  * устойчив к небольшим расхождениям типов (Optional) и пропущенным ключам\*

## Генерация на базе swagger rest-api

HTTP-клиент генерируется на базе [swagger api](https://swagger.io/) конфигурации при помощи LLM-моделей.
Этот подход выбран вместо классической кодогенерации, по нескольким причинам:

* Официальные API фиксированы, **регулярная перегенерация не требуется**.
* В неофициальных API используется ограниченный набор методов, их структура тоже относительно стабильна.
* Современные LLM умеют неплохо генерировать код по swagger-конфигу с минимальной ручной доработкой.
* Конечный результат аннотирован, его удобно использовать в IDE и автогенерируемой документации.


Далее приведены рецепты как собирать базовые http клиенты:

### На базе официального swagger конфига

1. Берём сырой `.json` или `.yaml` конфиг (например [от aniliberty](https://anilibria.top/storage/api/docs/v1?aniliberty-api-v1-docs.json)).
2. Удаляем ненужные `path`, которые не относятся к извлечению тайтлов и получению видео:
   * Например, для aniliberty это будет `/account/*`, `/media/*`, `/teams/*` и др.
   * Не забудьте удалить неиспользуемые схемы из `components`, чтобы ещё больше сжать схему
   * для более удобной минификации API конфигурации, можете конвертировать в `.yaml` через [openapi-converter](https://openapi-converter.com/json-to-yaml)
   * чем меньше получится схема - тем будет выше точность генерации (в примере с aniliberty удалось сжать в 5 раз: с 300кб до 60кб)!
3. Рекомендуется использовать модели с большим контекстом: `GLM-4.6`, `DeepSeek`, `Qwen3-Coder`, `Qwen3-Max`, `Sonnet-4.5` и др
4. Пример промпта см. в [`llm_openapi.md`](llm_openapi.md) — генерируем код, проверяем, фиксим мелкие баги, недочёты.

### Собираем swagger конфиг самостоятельно

Чеклист проверки на rest-api:

* откройте devtools -> network -> XHR:
* если присутствуют запросы, которые дают информацию о тайтлах в json формате - это REST-API (реже может быть graphql, но он тоже подойдет)
  * не путать с внешними запросами (реклама, трекеры, плеер и др)

Если сервис не предоставляет swagger-документацию, её можно собрать вручную с помощью [mitmproxy](https://github.com/mitmproxy/mitmproxy) и [mitmproxy2swagger](https://github.com/alufers/mitmproxy2swagger).

1. Установка

```bash
   uv tool install mitmproxy mitmproxy2swagger
```

2. [добавить сертификат из mitmproxy](https://docs.mitmproxy.org/stable/concepts/certificates/) для расшифровки https траффика

3. Перехват запросов

> [!tip]
> Рекомендуется выполнять серию запросов, чтобы немного повысить информативность возвращаемых объектов и ошибки статус-кодов

* запустить `mitmweb`
* перехватывайте траффик способом на выбор:
  * вручную через браузер (не забудьте добавить прокси для перехвата) и очистить от лишнего
  * для уменьшения шума, можете написать простые скрипты как в каталоге `capture_scripts/`, и с запущенным `mitmweb` запустить
  * сохраняем `flows`

4. генерация swagger документации:

   ```bash
   mitmproxy2swagger -i flows -p "<prefix url>" -o out.yml -f flow
   # уберите 'ignore:' из x-path-templates и повторите
   mitmproxy2swagger -i flows -p "<prefix url>" -o out.yml -f flow
   ```

  * `<prefix url>` должен быть полным. Например, для animevost будет `https://api.animevost.org"`

5. Рефакторинг, оптимизация структуры:

  * имена классов генерируется на основе `info.title` - замените его на название сервиса.

  * Попросите LLM вынести `responses` в `components`, например следующим коротким промптом:

  ```
  это openapi swagger документация, улучши её, вынеси responses в components

  {{ вставить swagger схему сюда }}
  ```

  * проверьте валидность схемы в [editor.swagger.io](https://editor.swagger.io/)

6. Генерируем код как в прошлом разделе

### Ошибки которые могут встретиться при генерации

>[!tip] Очередная вайбкод победа
>
> Если ошибок в файле не очень много, в большинстве случаев быстрее вручную исправить, чем просить LLM фиксить из-за зачастую перегруженного контекста с ещё большим числом ошибок.

* Аннотации типов:

```python
# некорректная вложенность TypedDict:
# SyntaxError: invalid syntax
T_OBJ = TypedDict("T_OBJ", {"random_screenshots": TypedDict("T_ITEMS", {...})})

# слишком общая аннотация:
random_screenshots: List[Dict[str, Any]]

# пропущенные типы:
random_screenshots: Any  # потеря типизации
"""
NOTE: игнорировать, если при ручной сборке swagger документации это поле было всегда null

types.NoneType добавили только в python 3.10, а на хак аннотирования при помощи 
NoneType = type(None) могут "ругаться" некоторые анализаторы кода

https://docs.python.org/3/library/types.html#types.NoneType
"""
```

Решение - вынести внутреннюю структуру в отдельный компонент (LLM промптом или вручную), это должно повыстить точность:

```yaml
ScreenshotItem:
  type: object
  properties:
    id:
      type: number
    sizes:
      # вынесен из оригинала
      $ref: "#/components/schemas/ScreenshotSizes"

ScreenshotSizes:
  type: object
  properties:
    small:
      type: string
    full:
      type: string
```
* конструкторы классов: убедитесь, что они сгенерированы корректно (в клиент по умолчанию не добавляется `base_url`)
* приватные методы `_request`: убедитесь, что API запросы выполняются правильно (корректно собирается endpoint для отправки запроса)

## Генерация парсеров для SSR сервисов

Если REST API нет, работаем с HTML-документом через DSL-транспилер [selector_schema_codegen](https://github.com/vypivshiy/selector_schema_codegen/).

Чеклист проверки SSR:

* Откройте devtools → Network:
   * Нет REST или GraphQL вызовов, относящихся к сервису;
   * сервер отдаёт полный HTML.
* Сохраните страницу локально (`Save page as...`) и откройте её в браузере.
   * Если структура совпадает — это SSR.

### Code of Conventions

* Парсеры, которые принимают весь HTML — с префиксом `Page`.
* Документируйте источник HTML и шаги подготовки.

Пример документации (DSL перенесёт её в код):

```python
# src/animego.py
class PageAnime(ItemSchema):
    """Anime page information. anime path contains in SearchView.url or Ongoing.url

    USAGE:
        GET https://animego.one/anime/<ANIME_PATH>

    EXAMPLE:
        GET https://animego.one/anime/eksperimenty-leyn-1114

    ISSUES:
        If blocked, you can try to skip metadata extraction and send API request:
        id = 1114 for https://animego.one/anime/eksperimenty-leyn-1114
    """

class PageEpisode(ItemSchema):
    """Representation episodes

    NOTE:
        film pages do not contain <div id="video-carousel"> element
    """
```

### Брифинг по синтаксису

>[!tip]
> Это краткий брифинг, подробнее [см оригинальный репозиторий](github.com/vypivshiy/selector_schema_codegen) 

* Основные выражения

Частично напоминает jquery, используется для декларативного описания КАК извлекать данные в поле из документа

```python
from ssc_codegen import D

# извлечение текста
D().css("title::text")

# список текстов
D().css_all("p::text")

# атрибуты
D().css("a::attr(href)")
D().css_all("a::attr(href)")

# работа с текстом
D().css("a::attr(href)").ltrim('/')
D().css_all("a::attr(href)").ltrim('/')
```

* Значения по умолчанию

  * Используется, если некоторые значения могут отсутствовать, но не критично влияют на работу проекта.
  * Если значение поля зависит от работы проекта - не добавляйте значение по умолчанию - пусть падает код с ошибкой.

```python
# вернуть пустую строку с описанием тайтла если он отсуствует
# сокращенные варианты, можно описать как D().default('')...
description = D('').css(".description::text").re_trim()

# или None
description = D(None).css(".description::text").re_trim()

# для списков, ставить `[]` по умолчанию
tags = D([]).css_all(".tags a::text")
```

* Сокращения

```python
from ssc_codegen import D, N, R

D()  # обычное поле
R()  # alias D().raw() — работа с корневым HTML как со строкой
N()  # nested-парсер (вложенная структура, пример будет далее)
```

* Проверка типов

Перед генерацией кода, ssc-gen проверяет типы в chain вызовах

Краткая таблица переходов:

| Выражение                       | Возвращаемый тип | Описание                |
| ------------------------------- | ---------------- | ----------------------- |
| `D()`                           | `DOCUMENT`       | Корень документа        |
| `R()` / `D().raw()`             | `STRING`         | HTML как строка         |
| `D().css(...)`                  | `DOCUMENT`       | Первый элемент          |
| `D().css(...).text()`           | `STRING`         | Текст                   |
| `D().css_all(...)`              | `LIST_DOCUMENT`  | Список элементов        |
| `D().css_all(...).text()`       | `LIST_STRING`    | Тексты всех элементов   |
| `D().css_all(...).attr("href")` | `LIST_STRING`    | Атрибуты всех элементов |

Пример ошибки:

```python
# Wrong: 'ltrim("/")' expected [STRING, LIST_STRING], got DOCUMENT
D().css("a[href]").ltrim('/')

# Correct
D().css("a[href]::attr(href)").ltrim('/')
```

### Использования схем

* ItemSchema

Используется для извлечения одного объекта (словаря).

```python
class PageAnime(ItemSchema):
    title = D().css("h3::text")
    description = D(None).css(".postDesc::text")
    thumbnail = D().css(".details_poster img::attr(src)").fmt("https:{{}}")
    player_js_encoded = R().re(r'new Playerjs\("(.*?)"\)')
    player_js_url = R().re(r'<script[^>]+src="(/js/playerjs.*?)"').fmt(FMT_URL)
```

Пример возвращаемого значения:

```python
{
  "title": "Легенда о героях",
  "description": "Фэнтези о...",
  "thumbnail": "https://site/img/poster.jpg",
  "player_js_encoded": "encoded_value",
  "player_js_url": "/js/player.js"
}
```

* ListSchema

Используется для списков.
`__SPLIT_DOC__` определяет, **как разбить документ на элементы списка**. Должен возвращать `LIST_DOCUMENT` тип

```python
class PageSearch(ListSchema):
    __SPLIT_DOC__ = D().css_all(".row > .col-ul-2")

    title = D().css(".text-truncate a[title]::attr(title)")
    thumbnail = D().css(".lazy[data-original]::attr(data-original)")
    url = D().css(".text-truncate a[href]::attr(href)")
```

Пример возвращаемого значения:

```python
[
  {"title": "One Piece", "thumbnail": ".../1.jpg", "url": "/anime/one-piece"},
  {"title": "Naruto", "thumbnail": ".../2.jpg", "url": "/anime/naruto"},
  ...
]
```

* DictSchema

Извлекает пары ключ–значение из HTML.

```python
class SeriesOptionItem(ListSchema):
    __SPLIT_DOC__ = D().css_all("option")

    value = D().attr("value")
    data_id = D().attr("data-id")

class SeriesOptions(DictSchema):
    __SPLIT_DOC__ = D().css_all(".serial-panel > .series-options div")

    __KEY__ = D().attr("class")  # всегда должен возврашать `STRING`
    __VALUE__ = N().sub_parser(SeriesOptionItem)
```

Пример возвращаемого значения:

```python
{
  "subtitles": [{"value": "ru", "data_id": "100"}, ...],
  "voice": [{"value": "jp", "data_id": "101"}, ... ],
  ...
}
```

* Nested. Вложенные структуры.

Позволяет вкладывать один парсер в другой через `N().sub_parser(ClassSchema)`.

```python
class KodikAPIPayload(ItemSchema):
    d = R().re(r"var\s*domain\s+=\s+['\"](.*?)['\"];")
    d_sign = R().re(r"var\s*d_sign\s+=\s+['\"](.*?)['\"];")

class PageMainKodikMin(ItemSchema):
    api_payload = N().sub_parser(KodikAPIPayload)
    player_js_path = D().css('head > script[src*="assets/js"]::attr(src)')
```


Пример возвращаемого значения:

```python
{
  "api_payload": {"d": "kodik.cc", "d_sign": "abcd1234"},
  "player_js_path": "/assets/js/main.js"
}
```

* JSON внутри HTML

Если HTML содержит JSON данные и их извлечь относительно легко — его можно извлечь через `.jsonify()`.

Шаблон можно сгенерировать через:

```bash
ssc-gen json-gen jsn_file.json -o jsn_gen.py
```

* jsn_file.json - подготовленный валидный json 
* jsn_gen.py - вывод сгенерированного шаблона для аннотации

```python
import re

class UrlParams(Json):
    d: str
    d_sign: str
    pd: str
    pd_sign: str
    ref: str
    ref_sign: str
    advert_debug: bool
    min_age: int
    first_url: bool

# TIP: можно использовать VERBOSE режим (re.X), чтобы упростить описание регулярного выражения.
# или описывайте строкой:
# url_params = R().re(r"var\s*urlParams\s*=\s*['\"](\{.*\})['\"]")
RE_EXTRACT_JSON = re.compile(r"""
  var\s*urlParams\s*=\s*['\"]
  (\{.*\})  # json data in urlParams variable
  ['\"]
""", re.X)

class PageMainKodikMin(ItemSchema):
    url_params = R().re(RE_EXTRACT_JSON).jsonify(UrlParams)
```

Пример возвращаемого значения

```python
{
  "url_params": {
    "d": "kodik.cc",
    "d_sign": "abcd",
    "pd": "xyz",
    "pd_sign": "defg",
    "ref": "spam",
    "ref_sign": "egg",
    "advert_debug": False,
    "min_age": 16,
    "first_url": True
  }
}
```
