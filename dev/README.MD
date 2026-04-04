# Конфигурации

Иструкции как реализовать парсеры и api клиенты для проекта

Зачем такой overengineering?

![img](assets/image.png)

ref: https://gunshowcomic.com/513

Большинство неофициальных API лишены аннотаций и документации, из-за чего их реализация становится сложной и неочевидной. При любых изменениях такие интерфейсы приходится исследовать заново, что приводит к значительным затратам времени на реверс-инжиниринг.

Для улучшения поддержки и частичной автоматизации реализуется генерация модулей с аннотациями объектов.

## Базовые требования к модулям для anicli-api 

* поддержка от python 3.9
* упрощённое документирование реализаций парсеров:
  * REST API — через swagger
  * SSR — через selector schema codegen
* базовое аннотирование объектов (API + web scraping)
* использование `TypedDict` как компромисса:
  * остаётся обычным dict
  * даёт IDE-подсказки
  * не требует зависимостей (pydantic и т.п.)
  * устойчив к небольшим расхождениям типов (Optional) и пропущенным ключам. Для баланса стабильности работы в runtime и удобства использования.

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

Если REST API нет, работаем с HTML-документом через DSL-транспилер [selector_schema_codegen](https://github.com/vypivshiy/selector_schema_codegen/tree/features-kdl).

Чеклист проверки SSR:

* Откройте devtools, Network:
   * Нет REST или GraphQL вызовов, относящихся к сервису;
   * сервер отдаёт полный HTML.
* Сохраните страницу локально (`Save page as...`) и откройте её в браузере.
   * Если структура совпадает — это SSR.


установка:

```bash
uv tool install git+https://github.com/vypivshiy/selector_schema_codegen@features-kdl
```

### Code of Conventions

* Парсеры, которые принимают весь HTML — с префиксом `Page`.
* Документируйте источник HTML и шаги подготовки.

Пример документации (DSL перенесёт её в код):

```kdl
json AggregateRating {
    type str "@type"
    ratingCount int
    bestRating int
    ratingValue str
}

json Director {
    type str "@type"
    url str
    name str
}

json Actor {
    type str "@type"
    url str
    name str
}

json Creator {
    type str "@type"
    name str
}

json Content {
    context str "@context"
    type str "@type"
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
    numberOfEpisodes int
}

struct PageAnime {
    @doc """
    Anime page information. anime path contains in SearchView.url or Ongoing.url

    - id needed for next API requests
    - raw_json used for extract extra metadata (unescape required)

    USAGE:

        GET https://animego.one/anime/<ANIME_PATH>

    EXAMPLE:

        GET https://animego.one/anime/eksperimenty-leyn-1114


    ISSUES:
        If blocked, you can try skip extract anime metadata and send api request:

        id contains in url:
            - id=1114 for https://animego.one/anime/eksperimenty-leyn-1114
            - id=2589 for https://animego.org/anime/chelovek-muskul-2589

        GET 'https://animego.one/anime/{id}/player?_allow=true'
    """

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

запуск генерации через скрипт

`./scripts/generate.sh`

Если ошибок в синтаксисе нет - успешно сегенрирует

### briefing

TODO

### vibecoding

>[!note] PoC skill

В проект встроен линтер, по экспериментам в агентах помогает генерировать валидный синтаксис

https://github.com/vypivshiy/selector_schema_codegen/tree/features-kdl/.agents/skills/kdl-schema-dsl

