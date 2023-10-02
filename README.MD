# anicli-api

Программный интерфейс набора парсеров аниме с различных источников.

Присутствует поддержка sync и async методов с помощью `httpx` библиотеки
Парсеры работают на REST-API (если у источника есть доступ), parsel и обёртки scrape-schema

# install
`pip install anicli-api`

# Overview
Структура проекта
```
anicli_api
├── base.py - базовый класс модуля-парсера
├── _http.py - сконфигурированные классы httpx
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
    [Extractor]  # результат поиска
        | search(<query>)/ongoing()  -> List[Search | Ongoing]  
        V                           
  [Search | Ongoing]     # информация о тайтле      
         | get_anime()  -> AnimeInfo  
         V                          
     [Anime]       # доступные эпизоды                
        | get_episodes()  -> List[Episode]  
        V                           
    [Episode]  # доступ к доступным видео (озвучки + хост)    
        | get_sources()  -> List[Video]   
        V                           
    [Source]  # прямые ссылки на видео, минимально необходимые заголовки, минимальная метаинформация
        | get_videos()  -> Video
        V
    Video(type, quality, url, extra_headers)
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
## Структура объектов

### История реализации структуры проекта

Это была сложная проблема проекта, которая была решена с помощью реализации дополнительной
библиотеки [scrape-schema](https://github.com/vypivshiy/scrape-schema) - dataclass-like 
(также схожая с ORM) подходом написания парсеров. Ну... насколько получилось решить проблему, 
ведь идет работа с html документами и сырым текстом, а не с готовыми структурами вида json

Изначально планировалось все реализовывать на регулярных выражениях (как в yt-dlp), но
выбрал css и xpath селекторы по следующим причинам:
- CSS и XPath селекторы проще сопровождать: просто открыть браузер, зайти в инструменты разработчика,
скопировать селектор из вкладки `Elements` и вставить в поиск. Опционально проверить с помощью [тестера 1](http://xpather.com/)
или [тестера 2](https://try.jsoup.org/)
- Просты в написании. Нужен только chromium-based браузер, плагин [selectorGadget](https://chrome.google.com/webstore/detail/selectorgadget/mhjhnkcfbdhnjickkkdbjoemdmbfginb)
и потом сгенерированный селектор идёт в код
- Чуть меньше кода писать, удобнее читать. Ну, почти... Ведь работаем с сырым html, а не структурами!
  Также, дополнительно присутствует логирование (в этом проекте выключен по умолчанию) и 
автоматическое приведение типов
- Быстрее и удобнее добавлять дополнительные поля по необходимости

### SearchResult
- url: str - URL на тайтл
- title: str - имя найденного тайтла
- thumbnail: str - изображение

### Ongoing
- url: str - URL на тайтл
- title: str - имя найденного тайтла
- thumbnail: str - изображение

### Anime
В некоторых источниках поля могут возвращать None
- title: str - имя тайтла (на русском)
- alt_titles: List[str] - альтернативные названия (английский, японский...)
- thumbnail: str - изображение
- description: Optional[str] - описание тайтла
- genres: List[str] - жанры
- episodes_available: Optional[int] - доступных эпизодов
- episodes_total: Optional[int] - максимальное число эпизодов
- aired: Optional[str] - дата выхода (или год)

### Episode
- title: str - имя эпизода
- num: str - номер эпизода

### Source
- url: str - ссылка на источник
- name: str - даббер или имя источника

### Video

Объект `Video` (полученный из `Source.get_video` или `Source.a_get_video`) имеет следующую структуру:

* type - тип видео
* quality - разрешение видео
* url - прямая ссылка на видео
* headers - заголовки требуемые для воспроизведения видео. 
Если возвращает пустой словарь - заголовки не нужны

# Примечания

- Проект разработан преимущественно на личное, некоммерческое использование с client-side 
стороны. 
Автор проекта не несет ответственности за поломки, убытки в высоко нагруженных проектах и решение
предоставляется "Как есть" в соответствии с [MIT](LIENSE) лицензией.

- Основная цель этого проекта — связать автоматизацию и эффективность извлечения того, 
что предоставляется пользователю в Интернете. 
Весь контент, доступный в рамках проекта, размещается на внешних неаффилированных источниках.

**Этот проект не включает инструменты кеширования и сохранения всех полученных данных, 
только готовые реализации парсеров**
