Перед разработкой ознакомьтесь с [dev](DEV.MD) документацией
# Разработка экстрактора

## Почему такая структура?
Проект изначально был небольшим скриптом на 300 строк кода под один сайт и 
позже стал универсальным под сторонние источники.

API для разработчиков там зачастую отсутствуют, поэтому применяются такие библиотеки как `re, bs4`, 
из-за этого результаты поиска поделены на этапы:
1. Искать тайтл по строке или выбрать из доступных онгоингов
2. Перейти на страницу с выбранным тайтлом, посмотреть описание, сколько серий и прочую мета информацию
3. Получить все доступные эпизоды, выбрать эпизод
4. Из выбранного эпизода получить доступные видеоплееры
5. Выбрать видеоплеер, получить из него __прямые ссылки__ для просмотра

## Структура экстрактора
Экстрактор должен обладать следующими классами и определенными __публичными__ методами:
```shell
Extractor
  def search
  def ongoing
  async async_search
  async async_ongoing

SearchResult
  def get_anime
  async a_get_anime

Ongoing
  def get_anime
  async a_get_anime

AnimeInfo
  def get_episode
  async a_get_episode

Episode
  def get_video
  async a_get_video

Video
  def get_source
  async a_get_source

TestCollections
  def test_search
  def test_ongoing
  def test_extract_metadata
  def test_extract_video
```

* Асинхронные методы идентичны синхронным, только для запросов используется httpx.AsyncClient вместо httpx.Client

### Имя файла-экстрактора:
* должен быть расширения `.py`
* не называться `base`
* не должен начинаться и заканчиваться нижним подчёркиванием `_` 

## Описание объектов

### Extractor
* Extractor - начальная точка входа в получении объектов SearchResult и Ongoing. 
Наследуется от **extractors.base.BaseAnimeExtractor** и имеет встроенные методы и инстансы
```shell
  HTTP - сконфигурированный синглтон класс httpx.Client
  HTTP_ASYNC - сконфигурированный синглтон класс httpx.AsyncClient
  _unescape - html.unescape функция
  _ReField - re_models.ReField
  _ReFieldList - re_models.ReFieldList
  _ReFieldListDict - re_models.ReFieldListDict
  _parse_many - re_models.parse_many
  _soup - возращает BeautifulSoap объект. По умолчанию использует html.parser
```

### Объекты

Объекты **SearchResult, Ongoing, AnimeInfo, Episode, Video** наследуются от **extractors.base.BaseModel** класса. 
Принимают произвольные kwargs аргументы. 
Имеют следующие методы и инстансы:
```shell
_HTTP - сконфигурированный синглтон класс httpx.Client
_HTTP_ASYNC - сконфигурированный синглтон класс httpx.AsyncClient
_unescape - html.unescape функция
_ReField - re_models.ReField
_ReFieldList - re_models.ReFieldList
_ReFieldListDict - re_models.ReFieldListDict
_parse_many - re_models.parse_many
_soup - возращает BeautifulSoap объект. По умолчанию использует html.parser
```
### TestCollections
Вспомогательный класс для быстрого тестирования на работоспособность всего экстрактора.
**Не применяется в CI/CD тестах, только локально. Они медленные и некоторые работают только с конкретными IP адресами**
Минимально необходимо реализовать следующие тесты.
```shell
test_search - тест на поиск тайтлов
test_ongoing - тест на получение онгоингов
test_extract_metadata - тест на получение метаинформации
test_extract_video - тест на получение прямых ссылок на видео
```
Можно добавить опционально дополнительные тесты.

В тестах на поиск и получение видео рекомендуется проверять на тайтлы, которые вышли давно 
и гарантированно будут на сайте. 

Например, идеальный кандидат на это - `Serial of experiments lain` (Эксперименты Лейн) или аналогичный.

В тесте на онгоинги проще: так как они регулярно обновляются, то рациональнее проверять по длине списка.

## Рекомендации по написанию парсеров

Конкретных требований на реализацию способов вытаскивания данных нет, можно применять 
`json`, `bs4`, `re` или `re_models` модуль в зависимости от ситуации. Для `публичных методов`, 
которые необходимо определить, для декомпозиции кода использовать скрытые методы (с `_` в начале).

```python
# BAD
from anicli_api.extractors.base import BaseAnimeExtractor

class Extractor(BaseAnimeExtractor):
    ...
    
    def some_parser(self, resp: str) -> dict:
        # parse response and return dict value

        ...
    
    def search(self, query: str):
        resp = self.HTTP.get("https://example.com")
        data = self.some_parser(resp.text)
        ...
```
```python
# GOOD
from anicli_api.extractors.base import BaseAnimeExtractor

class Extractor(BaseAnimeExtractor):
    ...
    
    def _some_parser(self, resp: str) -> dict:
        # parse response and return dict value
        ...
    
    def search(self, query: str):
        resp = self.HTTP.get("https://example.com")
        data = self._some_parser(resp.text)
        ...
```

В классах SearchResult, Ongoing может дублироваться код. Можно создать вспомогательный класс для рефакторинга:
```python
# Before
from anicli_api.extractors.base import BaseModel, BaseOngoing, BaseSearchResult
...
class Ongoing(BaseOngoing):
    url: str
    def get_anime(self):
        resp = self._HTTP.get(self.url)
        # parse methods
        ...
        

class SearchResult(BaseSearchResult):
    url: str
    def get_anime(self):
        resp = self._HTTP.get(self.url)
        # parse methods
        ...
```
```python
# After
from anicli_api.extractors.base import BaseModel, BaseOngoing, BaseSearchResult
...

class AnimeInfoParser(BaseModel):  # any class name
    url: str
    def get_anime(self):
        resp = self._HTTP.get(self.url)
        # parse methods
        ...

class Ongoing(AnimeInfoParser, BaseOngoing):
    ...
        
# https://docs.python.org/3/tutorial/classes.html?highlight=inheritance#multiple-inheritance
# слева-направо наследование идёт: сначала свой класс, потом базовый
class SearchResult(AnimeInfoParser, BaseSearchResult):
    ...
```
## Источники, полезные материалы
### Regex
* cool online regex tool tester [regex101](https://regex101.com)
* official guide [HOW TO regex](https://docs.python.org/3/howto/regex.html)
* yt-dlp readme, contains useful patterns [contribution guide](https://github.com/yt-dlp/yt-dlp/blob/master/CONTRIBUTING.md#regular-expressions)
* YT playlist [Indian Pythonista: RegEx in Python](https://www.youtube.com/playlist?list=PLyb_C2HpOQSDxe5Y9viJ0JDqGUCetboxB)
* YT playlist [PyMoondra: Python Regular Expressions Made Easy](https://www.youtube.com/playlist?list=PLGKQkV4guDKH1TpfM-FvPGLUyjsPGdXOg)
* YT playlist [selfedu: Python 3. Регулярные выражения](https://www.youtube.com/playlist?list=PLA0M1Bcd0w8w8gtWzf9YkfAxFCgDb09pA)

### beautifulsoup4

* [Official documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
* YT Video [John Watson Rooney: 5 Things You Might Not Be Using in BeautifulSoup](https://www.youtube.com/watch?v=3tUUVenpxbc)

### re_models
* [example](examples/example_re_models.py)
* [test](tests/test_re_models.py)
