# anicli-api

Программный интерфейс набора парсеров аниме с различных источников.

# requirements
```python
ht
```
Присутствует поддержка sync и async методов с помощью `httpx` библиотеки
Парсеры работают на REST-API (если у источника есть доступ), parsel и обёртки scrape-schema

# install
`pip install anicli-api`

# Overview
Структура проекта
```
anicli_api
├── base.py - базовый класс модуля-парсера
├── _http.py - сконфигурированный классы httpx
├── _logger.py - логгер
├── player - модули получения ссылок на видео
│     ├── __template__.py - шаблон модуля PlayerExtractor
│     ├── ...  ready-made модули
│     ...
├── source - модули парсеров с источников
│     ├── __template__.py
│     ├─ ... ready-made парсеры
│     ...
└── tools - прочие модули

```
Модули имеют следующий алгоритм пошагового получения объектов:

```shell
# Extractor works schema:
    [Extractor]
        | search(<query>)/ongoing()  -> List[Search | Ongoing]
        V                           
  [Search | Ongoing]          
         | get_anime()  -> AnimeInfo
         V                          
    [Anime]                     
        | get_episodes()  -> List[Episode]  
        V                           
    [Episode]                      
        | get_videos()  -> List[Video]              
        V                           
    [Source]
        | get_source()  -> MetaVideo or Str
        V
    Video(type, quality, url, extra_headers) or url
```

# Quickstart example
Демонстрация простого prompt-line приложения.
```python
from anicli_api.source.animejoy import Extractor # или любой другой источник


if __name__ == '__main__':
    ex = Extractor()
    while True:
        print("PRESS CTRL + C for exit")
        results = ex.search(input("search query > "))
        print(*[f"{i}) {r}" for i, r in enumerate(results)], sep="\n")
        anime = results[int(input("anime > "))].get_anime()
        episodes = anime.get_episodes()
        print(*[f"{i}) {ep}" for i, ep in enumerate(episodes)], sep="\n")
        episode = episodes[int(input("episode > "))]
        sources = episode.get_sources()
        print(*[f"{i}) {source}" for i, source in enumerate(sources)])
        source = sources[int(input("source > "))]
        videos = source.get_videos()
        print(*videos, sep="\n")
        video = videos[int(input("video > "))]
        print(video.type, video.quality, video.url, video.headers)
```
С asyncio аналогично, но методы получения объектов имеют префикс `a_` 
# Video
Объект `Video` (полученный из `Source.get_video` или `Source.a_get_video`) имеет следующую структуру:
* type - тип видео
* quality - разрешение видео
* url - прямая ссылка на видео
* headers - заголовки требуемые для воспроизведения видео. 
Если возвращает пустой словарь - заголовки не нужны
# Примечания

Проект разработан преимущественно на личное, некоммерческое использование с client-side 
стороны. 
Автор проекта не несет ответственности за поломки, убытки в высоко нагруженных проектах и решение
предоставляется "Как есть" в соответствии с [MIT](LIENSE) лицензией.


**Этот проект не включает инструменты кеширования и сохранения всех полученных данных, 
только готовые реализации парсеров**
