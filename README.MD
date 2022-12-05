# anicli-api
[![CI](https://github.com/vypivshiy/anicli-api/actions/workflows/ci.yml/badge.svg)](https://github.com/vypivshiy/anicli-api/actions/workflows/ci.yml)

Программный интерфейс парсера аниме с различных источников.

Присутствует поддержка sync и async методов с помощью `httpx`,для получения информации и прямых ссылок на видео.
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
        | get_source()  -> Dict or Str
        V
    {quality: url, ...} or url
```

# Quickstart example
Смотрите примеры в [examples](examples)

# Примечание

Если вы будете этот проект использовать в **production** условиях, особенно в высоко нагруженных решениях, 
то выстаивайте архитектуру своих проектов **на предварительном сборе информации** 
(например, полученные данные сохранять в базу данных и только из неё возвращать), 
так как большинство парсеров работает в обход официальных методов и применяются такие библиотеки как re, bs4. 
Поэтому могут быть проблемы от производительности, до получения ошибок по типу 403 (срабатывание ddos защиты) или 
502 (доступа к сайту запрещён).

**Этот проект не включает инструменты кеширования и сохранения всех полученных данных, только эндпоинты**

# DEV
 [DEV](DEV.MD)

# Contributing
[CONTRIBUTING](CONTRIBUTING.MD)

# TODO
* ~~CI CD автотестов~~
* Получение видео по ссылке (like yt-dlp)
* ~~asyncio tests~~
* ~~coverage~~
* ~~добавить примеры~~
* ~~Написать документацию для high level применения~~ пока на уровне example примеров
* ~~Написать документацию для low level разработки экстракторов~~
* ~~Дописать asyncio методы для animego~~
* Портировать anilibria, animevost, animania экстракторы из старого проекта
