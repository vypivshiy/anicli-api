# anicli-api

Реализация программного интерфейса парсера аниме.

Присутствует поддержка sync и async методов с помощью `httpx`,для получения информации и прямых ссылок на видео.

# Quickstart example
Простой пример получения прямой ссылки
```python
from anicli_api.extractors import animego

extractor = animego.Extractor()
search = extractor.search("lain")
info = search[0].get_anime()
episodes = info.get_episodes()
video = episodes[0].get_videos()
link = video[0].get_source()
```

Объекты умеют итерироваться:
```python
from anicli_api.extractors import animego

extractor = animego.Extractor()
search = extractor.search("lain")
info = search[0].get_anime()
for episode in info:
    episode.get_videos()
    ...
```


Также, можно получать сразу все сырые результаты. Возвращает сырой словарь со всеми полями
```python
from anicli_api.extractors import animego

extractor = animego.Extractor()
for meta in extractor.walk_search("lain"):
    print(meta)
```
Есть возможность получать видео из таких источников, как Kodik, Aniboom:
```python
from anicli_api.decoders import Kodik, Aniboom

kodik_links = Kodik.parse("https://kodik.info/seria/1026046/02a256101df196484d68d10d28987fbb/720p")
aniboom_links = Aniboom.parse('https://aniboom.one/embed/N9QdKm4Mwz1?episode=1&translation=2')
```

# Примечание

Если вы будете этот проект использовать в **production** условиях, преимущественно в высоко нагруженных решениях, 
то выстаивайте архитектуру своих проектов **на предварительном сборе информации** 
(например, сохранять в базу данных и получать из неё нужную информацию), 
так как большинство парсеров работает в обход официальных методов, поэтому
могут быть проблемы от производительности, до получения ошибок по типу 403 (срабатывание ddos защиты), 
502 (запрет доступа к сайту).

**Этот проект не включает инструменты кеширования и сохранения всех полученных данных, только получение**

# DEV
 TODO

# Contribution
 TODO
# TODO
* CI CD автотестов
* console_enrtypoints для CLI взаимодействий
* Дописать документацию для high level применения
* Написать документацию для low level разработки экстракторов
* Дописать asyncio методы для animego
* Портировать anilibria, animevost, animania экстракторы из старого проекта
