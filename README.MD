# anicli-api
[![CI](https://github.com/vypivshiy/anicli-api/actions/workflows/ci.yml/badge.svg)](https://github.com/vypivshiy/anicli-api/actions/workflows/ci.yml)
[![Documentation Status](https://readthedocs.org/projects/anicli-api/badge/?version=latest)](https://anicli-api.readthedocs.io/en/latest/?badge=latest)

Программный интерфейс парсера аниме с различных источников.

Присутствует поддержка sync и async методов с помощью `httpx` библиотеки, для получения информации и прямых ссылок 
на видео.

# install
`pip install anicli-api`

# Overview
Модуль экстрактора имеют следующую структуру пошагового получения объекта:
```shell
# Extractor works schema:
    [Extractor]
        | search(<query>)/ongoing()  -> List[SearchResult | Ongoing]
        V                           
  [SearchResult | Ongoing]          
         | get_anime()  -> AnimeInfo
         V                          
    [AnimeInfo]                     
        | get_episodes()  -> List[Episode]  
        V                           
    [Episode]                      
        | get_videos()  -> List[Video]              
        V                           
    [Video]
        | get_source()  -> MetaVideo or Str
        V
    MetaVideo(type, quality, url, extra_headers) or url
```

# Quickstart example
Смотрите примеры [examples](examples) и [документации](https://anicli-api.readthedocs.io/en/latest/index.html)!

# Примечания

Проект разработан преимущественно на личное, некоммерческое использование на стороне клиента. 
Автор проекта не несет ответственности за поломки, убытки в высоко нагруженных проектах и решение
предоставляется "Как есть" в соответствии с [MIT](LIENSE) лицензией.

Если вы всё же решили этот проект использовать в **production** условиях, 
то выстаивайте архитектуру своих проектов **на предварительный сбор информации** 
(например, полученные данные сохранять в базу данных и оттуда позже получать), 
так как большинство парсеров работает в обход официальных методов и применяются такие библиотеки как re, bs4. 

Следовательно, могут быть проблемы от производительности, до получения ошибок по типу 403 (срабатывание ddos защиты) или 
502 (доступа к сайту запрещён).

**Этот проект не включает инструменты кеширования и сохранения всех полученных данных, только эндпоинты 
с готовой реализацией архитектуры парсеров**

# DEV
 [DEV](DEV.MD)

# Contributing
[CONTRIBUTING](CONTRIBUTING.MD)

# TODO
* ~~CI CD автотестов~~
~~* Поправить sphinx документацию~~
* Получение видео по ссылке (like yt-dlp)
* расширенный поиск (по жанрам, годам, etc)
* улучшение документации
* Продумать стандартизацию атрибутов в экстракторах (если такое реально?)
* ~~asyncio tests~~
* ~~coverage~~
* ~~добавить примеры~~
* ~~Написать документацию для high level применения пока на уровне example примеров~~
* ~~Написать документацию для low level разработки экстракторов~~
* ~~Дописать asyncio методы для animego~~
* ~~Портировать anilibria, animevost, animania экстракторы из старого проекта~~
