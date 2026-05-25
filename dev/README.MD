# Конфигурации

Иструкции как реализовать парсеры и api клиенты для проекта

Зачем такой overengineering?

![img](assets/image.png)

ref: https://gunshowcomic.com/513

Большинство неофициальных API лишены аннотаций и документации, из-за чего их реализация становится сложной и неочевидной. При любых изменениях такие интерфейсы приходится исследовать заново, что приводит к значительным затратам времени на реверс-инжиниринг.

Для улучшения поддержки, документируемости и частичной автоматизации реализуется генерация модулей с аннотациями объектов.

Установка:

```bash
uv tool install ssc-codegen     
```

## Базовые требования к модулям для anicli-api 

* поддержка от python 3.9
* упрощённое документирование реализаций парсеров:
  * REST API — через swagger **(DEPRECATED, используется [ssc-gen](https://github.com/vypivshiy/selector_schema_codegen) kdl2.0 синтаксис)**
  * SSR — через [selector schema codegen](https://github.com/vypivshiy/selector_schema_codegen) [kdl2.0](https://kdl.dev/) DSL
* базовое аннотирование объектов (API + web scraping)
* использование `TypedDict` как компромисса:
  * остаётся обычным dict
  * даёт IDE-подсказки
  * не требует зависимостей (pydantic и т.п.)
  * устойчив к небольшим расхождениям типов (Optional) и пропущенным ключам. Для баланса стабильности работы в runtime и удобства использования.

## Описание rest-api модулей

С версии 0.9.0 больше не генерируется из swagger документаций по следующим причинам:

* для backend разработки он полезен, но для reverse-engeneering избыточен и мало информативен
  * Большинство реализаций в этом проекте основаны на серии HTTP запросов 
  * Если полная документация есть (anilibery, yummy-ani.me), то получаем много избыточных неиспользуемых методов для проекта. Например, авторизация и получения профилей - out of scope 
* нет детерменированности результата - раньше полагались на LLM генерацию.
  * единственно правильного способа генерировать код из swagger нет, а реализация универсального кодогенератора с нуля довольно сложная и неочевидная
* не удобно читать файл в plain text формате

### Чеклист проверки на rest-api

* откройте devtools -> network -> XHR:
* если присутствуют запросы, которые дают информацию о тайтлах в json формате - это REST-API (реже может быть graphql, но он тоже подойдет)
  * не путать с внешними запросами (реклама, трекеры и др)

### Пример

```kdl2
json Item {
    id int
    title str
    description str
    genre str
    year str
    urlImagePreview str
    screenImage (array)str
    isFavorite int // 0/1
    isLikes int // 0/1
    rating float
    votes int
    timer float
    type str
    director str
    series str
}

json State { status str; rek int; page int; count int }
// json Data { items (array)Item }
json SearchResponse { state State; data (array)Item }


(array)json PlaylistResponse {
    name str
    hd str
    std str
    preview str
}
json ResponseError { status str?; error str }


(rest)struct AnimeVostAPI {
    @request \
        name=search \
        response=SearchResponse \
        """
        curl -X POST "https://api.animevost.org/v1/search" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "name={{query}}"
        """
    
    /* for ongoings recommended:
    page=1; quanity=20
    */
    @request \
        name=last \
        response=SearchResponse \ 
        """
        curl -X GET "https://api.animevost.org/v1/last?page={{page:int}}&quantity={{quantity:int}}"
        """

    @request \
        name=playlist \
        response=PlaylistResponse \ 
        """
        curl -X POST "https://api.animevost.org/v1/playlist" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "id={{id:int}}"
        """

    // exclude status field
    @error 404 ResponseError

    // playlist specific error
    @error 200 ResponseError "error" 
}
```

Пояснения:

* `json NAME { field TYPE OPTS... }` - описание аннотации/сериализации структуры (схоже как в golang). внутри описываются ключ и тип поля
  * NAME - имя json структуры/типа
  * field
     * TYPE - тип поля [int, str, float, bool, JSON, (array)TYPE ]
     * OPTS - опции поля [ `@omitempty`, `@optional`, `@skip` `"NAME-ALIAS"` ]
* `(rest)struct NAME { @request... }` - объявление класса-фасада вызовов rest-api методов
  * NAME - имя класса
  * @request - request поля

* `@request name=NAME response=RESPONSE REQUEST`
  * Для удобного чтения, в kdl2.0 можно разделять построчно свойства и аргументы через символ `\` 
  * `NAME` - имя метода
  * `RESPONSE` - json для сериализации/аннотации
  * `REQUEST` - аргумент запроса. Принимает POSIX curl или RAW HTTP формат. Умышленно выбран такой формат для удобного копирования из браузера,HTTP сниффера или генерации через LLM
    * для генерации placeholder параметров используется синтаксис `{{param:OPTS}}`. Если `OPTS` пустой - по умолчанию строка
      * param должен быть в нижнем регистре
* `@error CODE RESPONSE FIELDS...` - документирование ошибок
  * CODE - статус код
  * RESPONSE - json структура
  * FIELDS - поля, по которым можно сравнить. Если сервис проектировали не по канонам rest-api и у него статус код идентичный обычному запросу
    * сравнение по наличию ключа: - аргументом `error`
    * сравнение equal - свойство `status=#false` 
  
Примеры записи REQUEST метода:

```
// POSIX CURL format
@request \
  """
  curl -X POST "https://api.animevost.org/v1/playlist" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "id={{id:int}}"
  """
// RAW HTTP format
@request \
  """
  POST /v1/playlist HTTP/1.1
  Host: api.animevost.org
  Content-Type: application/x-www-form-urlencoded

  id={{id:int}}
  """
```

## Генерация на базе swagger rest-api

>![warning]
> Deprecated, используется генерация через ssc-codegen. Позже раздел будет удален

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
3. Рекомендуется использовать модели с большим контекстом: `GLM-4.6`, `DeepSeek`, `Qwen3-Coder`, `Qwen3-Max`, `Sonnet-4.6` и др
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
> Рекомендуется выполнять серию запросов, чтобы немного повысить информативность возвращаемых объектов и перехвата ошибок

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
      # type: object
        # properties:
          # small:
            # type: string
          # full:
            # type: string
      $ref: "#/components/schemas/ScreenshotSizes"

ScreenshotSizes:
  type: object
  properties:
    small:
      type: string
    full:
      type: string
```
* конструкторы классов: убедитесь, что они сгенерированы корректно (например в клиент по умолчанию не добавляется `base_url`)
* приватные методы `_request`: убедитесь, что API запросы выполняются правильно (корректно собирается endpoint для отправки запроса)

## Генерация парсеров для SSR сервисов

Если REST API нет, работаем с HTML-документом через [selector_schema_codegen](https://github.com/vypivshiy/selector_schema_codegen).

Чеклист проверки SSR:

* Откройте devtools, Network:
   * Нет REST или GraphQL вызовов, относящихся к сервису;
   * сервер отдаёт полный HTML.
* Сохраните страницу локально (`Save page as...`) и откройте её в браузере.
   * Если структура совпадает (могут поломаться стили и вёрстка, всё нормально) — это SSR.


### Code of Conventions

* Парсеры, которые принимают весь HTML — с префиксом `Page`.
  * Например, если есть разделение под вложенные парсеры - он не пишется
* Документируйте источник HTML и шаги подготовки.

### Пример документации

```kdl2
define BASE-URL="https://animego.me"
define REQUEST-ONGOING="curl {{BASE-URL}}"
define REQUEST-ANIME-PAGE="curl {{BASE-URL}}/anime/{{slug}}"

(list)struct PageOngoing {
    @doc """
    Get all available ongoings from the main page

    GET https://animego.me

    NOTE: animego can change the domain, so only the path is returned.
    """

    @split-doc { css-all ".updates-body > div.d-grid > a.aw-item" }

    @request REQUEST-ONGOING

    url-path { attr href }
    title { css ".image__img"; attr alt }
    thumbnail { css ".image__img"; attr src }

    /* signature: 
    Серия 2 · Субтитры — Сегодня, 21:50
    */
    episode { css ".aw-meta"; text; re #"\s(\d+)\s"# }
    dub { css ".aw-meta"; text; re #"(\w+)\s+—"# }
}

json AggregateRating {
    @type str
    ratingCount int @omitempty
    bestRating int @omitempty
    ratingValue float @omitempty
    worstRating int @omitempty
}

json Director {
    @type str
    url str
    name str
}

json Actor {
    @type str
    url str
    name str
}

json Creator {
    @type str
    name str
}

json Content {
    @context str
    @type str
    url str
    name str
    alternateName str
    image str
    description str
    genre (array)str
    contentRating str
    datePublished str
    keywords str
    creator (array)Creator
    aggregateRating AggregateRating
    numberOfEpisodes int @omitempty
}

struct PageAnime {
    @doc """
    Anime page information. anime path contains in SearchView.url or Ongoing.url

    - id needed for next API requests
    - raw_json used for extract extra metadata (unescape required)

    USAGE:

        GET https://animego.me/anime/<ANIME_PATH>

    EXAMPLE:

        GET https://animego.me/anime/eksperimenty-leyn-1114


    ISSUES:
        If blocked, you can try skip extract anime metadata and send api request:

        id contains in url:
            - id=1114 for https://animego.me/anime/eksperimenty-leyn-1114
            - id=2589 for https://animego.me/anime/chelovek-muskul-2589

        GET 'https://animego.me/anime/{id}/player?_allow=true'
    """
    @request REQUEST-ANIME-PAGE

    title { css ".entity__title h1"; text }
    // maybe missing description eg:
    // https://animego.org/anime/chelovek-muskul-2589
    description {
        css-all ".description"; text
        join ""
        trim
        fallback ""
    }
    thumbnail {
        css ".d-sm-flex .image__picture img.image__img"
        attr src
    }
    id {
        css "link[rel=\"canonical\"]"; attr href
        re #"-(.?\d{2,})"#
    }
    raw-json {
        css "script[type='application/ld+json']"; text
        jsonify Content
    }
}
```

Пояснения:

* `define` - макрос частично схожий C языком. Подставляет значения и выражений в схемы на этапе генерации.
  * всегда должен быть в верхнем регистре
  * В отличии от C языка, доступна только подстановка константных значений, параметризация отсутствует
  * линтер корректно проверяет типы и значения 
* `json` - описания json типов/сериализации
* struct `NAME` { `FIELDS`... } - описание парсера. Если тип отстует аннотация типов - возвращает словарь
  * `FIELDS` - поля внутри структуры
    * `@doc """..."""` - генерирует документацию в коде. Основной способ дополнительного документирования поведения и какие могут быть ошибки
    * `@split-doc { ... }` - специальная директива до вызова парсера разделить документ на элементы-карточки
    * `@request` - синтаксический сахар, генерирует дополнительный конструктор, который принимает http клиент, который делает запрос
    * `field { ... }` - декларация поля КАК его нужно распарсить и преобразовать. Входной тип всегда документ/элемент html страницы

запуск генерации через скрипт

`./scripts/generate.sh`

Если ошибок в синтаксисе нет - успешно сегенрирует.
Синтаксис можно проверть через вызов `ssc-gen check <config.kdl>`

### briefing

TODO

### vibecoding

>[!note] PoC раздел

В проект встроен линтер на проверку синтаксиса, можете попробовать описывать через LLM агентов с вызовами скилов

https://github.com/vypivshiy/selector_schema_codegen/tree/main/.agents/skills

