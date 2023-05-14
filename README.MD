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
Смотрите примеры [examples](examples) и [документации](https://anicli-api.readthedocs.io/en/latest/index.html)!

# Примечания

Проект разработан преимущественно на личное, некоммерческое использование с client-side 
стороны. 
Автор проекта не несет ответственности за поломки, убытки в высоко нагруженных проектах и решение
предоставляется "Как есть" в соответствии с [MIT](LIENSE) лицензией.


**Этот проект не включает инструменты кеширования и сохранения всех полученных данных, 
только готовые реализации парсеров**
