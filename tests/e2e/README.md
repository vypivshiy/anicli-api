# e2e тесты

e2e тесты с обращениями к реальным сайтам для модулей `anicli_api.source.*` и `anicli_api.player.*` —
пытаются дойти до видеопотока. Не предполагается использовать в CI/CD — работают медленно,
поведение модулей может зависеть от геолокации.

## Запуск

```bash
# linux / macos
# опционально установить proxy
ANICLI_PROXY=socks5://user:pass@host:1080 ./scripts/tests.sh

# windows powershell
# опционально установить proxy
$env:ANICLI_PROXY = "socks5://user:pass@host:1080"
.\scripts\tests.ps1
```

Либо напрямую через pytest:

```bash
pytest -m e2e tests/e2e          # обход skip-by-default через фильтр маркера
pytest --run-e2e tests/e2e        # то же самое через явный флаг
pytest -m e2e -k animego tests/e2e  # ограничить одним источником/плеером
```

## Конфигурация (env, без правок кода)

| env-переменная       | по умолчанию | назначение                                                             |
| -------------------- | ------------ | --------------------------------------------------------------------- |
| `ANICLI_PROXY`       | не задано    | url socks5/http(s)-прокси, прокидывается во все httpx-клиенты. Зависимость `httpx[socks]` уже подключена. |

Кастомные заголовки на источник: собери клиент прямо в модуле теста через
фикстуры `build_sync_client` / `build_async_client`, например:

```python
def test_pipeline(build_sync_client, build_async_client, assert_video_reachable):
    from tests.e2e.conftest import HttpBundle

    bundle = HttpBundle(
        sync=build_sync_client({"Authorization": "Bearer ..."}),
        async_=build_async_client({"Authorization": "Bearer ..."}),
    )
    ex = Extractor(**bundle.extractor_kwargs)
    ...
```

## Структура

```
tests/e2e/
  conftest.py          фикстуры + хук skip-by-default
    http_bundle                            — пара (sync, async) httpx-клиентов с .extractor_kwargs
    build_sync_client / build_async_client — фабрики для custom-headers (Bearer и т.п.)
    assert_video_reachable                 — GET-probe видео-ссылки
  sources/test_*.py    по одному модулю на source Extractor
  players/test_*.py    по одному модулю на player; URL захардкожены в модуле
```

В каждом модуле хардкодятся собственные запросы / списки URL (без параметризации).
Модули плееров с пустым списком `URLS` пропускаются (а не проходят молча) —
добавь стабильные URL по мере необходимости.

## Гео-зависимые цели

`animego`, `kodik`, `aniboom`, `cdnvideohub` могут не работать на IP отличных от СНГ/Прибалтики - могут упасть.

`anilibme` (animelib.org, требует Bearer-авторизацию) исключён из e2e-покрытия.

## Ассерты

`assert_video_reachable` - GET-stream, читает первый чанк и обрывает загрузку (mp4 целиком не качается).

Почему GET, а не HEAD: видео-CDN часто отдают 405/404 на HEAD или ломаются на signed-url
(`?X-Amz-Signature=...`); только GET доказывает, что ресурс реально отдаёт байты.

`video.headers` мерджится в запрос — некоторые CDN (sibnet, aniboom) отдают 403 без
обязательных `Referer`/`Origin`/`Accept-Language`.

Дополнительно проверяются структурные поля: `type in {mp4, m3u8, mpd, audio, webm}`,
`quality in {0, 144, 240, 360, 480, 720, 1080, 2160}`. `Video.__eq__` сравнивает по
(type, quality, netloc) — сравнения плейлистов остаются стабильными.
