# Docs

## Структуры объектов

Приведены поля, которые **гарантированно** возвращаются в API интерфейсе библиотеки.
В некоторых источниках могут присутствовать дополнительные поля или атрибуты для
использования во внутренних методах.

* Например, в `anilibria` и `animevost` дополнительные поля из API хранятся в `data`. В `animego.Anime` есть сырой несериализованный `raw_json` для извлечения дополнительных метаданных.

* В некоторых источниках на полях могут присутствовать "заглушки" для поддержания консистентности API интерфейса. Например, в модуле `anicli_api.source.jutsu.Episode` уже можно получить прямые ссылки на видео (Video объект), но для поддержания полиморфизма, необходимо возвращать объект `Source` и только потом `Video`

### Search

* url: str - URL на тайтл
* title: str - имя найденного тайтла
* thumbnail: str - изображение

### Ongoing

* url: str - URL на тайтл
* title: str - имя найденного тайтла
* thumbnail: str - изображение

### Anime

* title: str - имя тайтла (на русском)
* thumbnail: str - изображение
* description: Optional[str] - описание тайтла. может вернуть пустую строку или None

### Episode

* title: str - имя эпизода (Если источник его не хранит, то будет Серия или Serie)
* ordinal: int - номер эпизода

### Source
* url: str - ссылка на источник
* title: str - даббер или имя источника

### Video

Объект `Video`, полученный из `Source.get_video`/`Source.a_get_video`
имеет следующую структуру:

* type - тип видео (m3u8, mp4, mpd, audio)
* quality - разрешение видео (0, 144, 240, 360, 480, 720, 1080)
* url - прямая ссылка на видео
* headers - заголовки требуемые для получения потока. Если возвращает пустой словарь - заголовки не нужны

## logging

Настройка логгера идет через ключ `anicli-api`

```python
import logging
logger = logging.getLogger('anicli-api')
```

## Tools

Наборы вспомогательных модулей

### cookies.py

Опциональная зависимость для извлечения cookie данных из браузера для последующего использования в httpx.
Реализована при помощи библиотеки [rookiepy](https://github.com/thewh1teagle/rookie)

```bash
pip install anicli-api[browser-cookies]
```

```python
import httpx
from anicli_api.tools.cookies import get_raw_cookies_from_browser, raw_cookies_to_httpx_cookiejar

# по умолчанию извлекает все cookies
raw_cookies = get_raw_cookies_from_browser("firefox")
cookies = raw_cookies_to_httpx_cookiejar(raw_cookies)
# опциональный фильтр по host:
# raw_cookies = get_raw_cookies_from_browser("firefox", ["example.com"])
httpx.get("https://example.com", cookies=cookies)

# update cookies in extractors:
from anicli_api.source.yummy_anime_org import Extractor
ex = Extractor()
ex.http.cookies.update(cookies)
ex.http_async.cookies.update(cookies)
```

### dummy_cli.py

Простой cli-клиент для ручных тестов и имитации клиента

```python
from anicli_api.tools.dummy_cli import cli
from anicli_api.source.yummy_anime_org import Extractor

cli(Extractor())
```

### helpers.py

Наборы вспомогательных функций для взаимодействия с экстракторами

```python
from anicli_api.source.yummy_anime_org import Extractor
from anicli_api.tools.helpers import get_video_by_quality, video_picker_iterator, async_video_picker_iterator

ex = Extractor()
result = ex.search('lain')[0]
anime = result.get_anime()
episodes = anime.get_episodes()
sources = episodes[0].get_sources()
videos = sources[0].get_videos()

# извлечь ближайшее доступное по качеству видео
# 1080 or linear quality: 720 -> 480 -> 360 -> 240...
video = get_video_by_quality(videos, 1080)

# итератор видео и заголовка
# извлекает выбранное видео по разрешению и озвучке
for video_and_title in video_picker_iterator(
        start_source=sources[0],
        start_video=videos[0],
        anime=anime,
        episodes=episodes[3:]):  # limit episodes to 3
    v, title = video_and_title
    print(title, v)

# async реализация итератора
async def main():
    async for vid_and_title in async_video_picker_iterator(
      start_source=sources[0],
        start_video=videos[0],
        anime=anime,
        episodes=episodes[3:]  # limit episodes to 3
    ):
        v, title = vid_and_title
        print(title, v)

import asyncio
asyncio.run(main())
```

### m3u.py

Реализация создания m3u плейлиста из объектов экстрактора

```python
from anicli_api.source.yummy_anime_org import Extractor

from anicli_api.tools.m3u import generate_playlist, generate_asyncio_playlist
from anicli_api.tools.helpers import video_picker_iterator, async_video_picker_iterator

ex = Extractor()
result = ex.search('lain')[0]
anime = result.get_anime()
episodes = anime.get_episodes()
# get first source for first 3 episodes
sources =  [e.get_sources()[0] for e in episodes[:3]]
videos = sources[0].get_videos()

# generate playlist from sources
playlist_sources = generate_playlist(sources)

# generate playlist from video_picker
video_objs, titles_objs = [],[]
for video_and_title in video_picker_iterator(
        start_source=sources[0],
        start_video=videos[0],
        anime=anime,
        episodes=episodes[3:]):  # limit episodes to 3
    v, title = video_and_title
    video_objs.append(v)
    titles_objs.append(title)
playlist = generate_playlist(video_objs, titles_objs)


# asyncio
# if target not Source object - you can use sync variant
import asyncio
playlist_async = asyncio.run(generate_asyncio_playlist(sources))
```

## http client config

### source

Если по какой-то либо причине вас не устраивают настройки по умолчанию - то вы можете задать конфигурацию http клиентов для экстракторов. Или если необходимо подключить proxy

```python
from anicli_api.source.animego import Extractor
import httpx
# не обязательно настраивать все клиенты, зависит от режима использования
# например, если вы будете использовать только asyncio - настраивайте только http_async_client
my_client = httpx.Client(headers={"user-agent": "007"}, proxy="http://127.0.0.1:8080")
my_async_client = httpx.AsyncClient(headers={"user-agent": "007"}, proxy="http://127.0.0.1:8080")

# настройки клиентов будут передаваться всем объектам кроме методов Source.get_videos()
# и Source.a_get_videos()

ex = Extractor(http_client=my_client, http_async_client=my_async_client)

# изменение http клиента для объекта
results = ex.search("lain")
result = results[0]
result.http = my_client
result.http_async = my_async_client
...

```

### player

В player для модификации httpx клиентов (Client, AsyncioClient) необходимо передать kwargs аргументы:

```python
from anicli_api.source.animego import Extractor


sources = (
    Extractor()
    .search("lain")[0]
    .get_anime()
    .get_episodes()[0]
    .get_sources()
)

videos = sources[0].get_videos(transport=None,  # reset to default httpx.HTTPTransport
                               headers={"User-Agent": "i'm crushing :("})
```
