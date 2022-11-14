# low level
### re_models
Экспериментальная обёртка под `re` библиотеку, для получения словаря со значениями после поиска вхождений.
Принцип работы следующий:
1. Принимает на вход регулярное выражение или строку с регулярным выражением. 
По умолчанию, берёт имя для ключа из идентификатора группы. Например, `r"(?P<integer>\d+)"` возьмет __integer__ для
ключа. Также, можно указать имя, передав аргумент `name`. Если по каким-либо причинам регулярное выражение ничего 
не найдет, то вернёт None. Это значение можно изменить передав аргумент `default`

2 Шаги преобразований:

2.1 `before_func` функция-параметр, если передан

2.2 `before_func_call` метод (если объявлен)

2.3 `result_type` меняет тип найденного результата (по умолчанию str)

2.4 `after_func_call` метод (если объявлен)

2.5 `after_func` функция-параметр, если передан

3. Возвращает словарь типа {name: result}
* ReBaseField - базовый класс. Доступные параметры:
```shell
Аргументы:

pattern: Union[Pattern, AnyStr] - регулярное выражение. Принимает строку или re.complile объект
# ниже передаются именованные аргументы
name: Optional[str] - имя ключа, если не передано, по умолчанию берёт из идентификатора группы
default: Optional[Any] - Значение, которое вернет, если регулярное выражение ничего не нашло. По умолчанию None
type: Type - тип преобразования переменной. По умолчанию str,
before_exec_type: Optional[T_BEFORE_EXEC] - функция преобразования результата поиска ДО ПРИВЕДЕНИЯ типа `type`, 
если регулярное выражение нашло значение. Если значение None, игнорируется.
after_exec_type: Optional[T_AFTER_EXEC] - функция преобразования результата поиска ПОСЛЕ ПРИВЕДЕНИЯ типа `type`, 
если регулярное выражение нашло значение. Если значение None, игнорируется.

Методы
parse(text: str) - применяет поиск значения по переданному тексту, возвращает словарь со значениями.
parse_values(text: str) - применяет поиск значения по переданному тексту, возвращает список со значениями, без ключей
```
#### Реализации на базе ReBaseField:
* ReField
Возвращает первое найденное значение
```python
from anicli_api.re_models import ReField
sample_text = "digit=1 digitt=10"

field = ReField(r"\w+=(?P<digit>\d+)",
                type=int)
# эквивалента записи:
field_2 = ReField(r"\w+=(\d+)", name="digit",
                    type=int)
print(field.parse(sample_text), field_2.parse(sample_text)) # {"digit": 1} {"digit": 1}
```

Если ничего не найдет, по умолчанию вернёт `default` значение
```python
from anicli_api.re_models import ReField
sample_text = "digit=1 digitt=10"

field = ReField(r"failedpattern",
                name="fail")
# эквивалента записи:
field_2 = ReField(r"failedpattern", 
                  name="fail",
                  default="EPIC FAIL!!!")
print(field.parse(sample_text), field_2.parse(sample_text)) # {"fail": None} {"fail": "EPIC FAIL!!!"}
```

* ReFieldList
Возвращает все найденные значения в виде {name: [result_1, result_2, ...]}. параметр `name` обязателен

```python
from anicli_api.re_models import ReFieldList
sample_text = "digit=1 digitt=10"

field = ReFieldList(r"\w+=(\d+)",
                    type=int,
                    name="digits")
# эквивалента записи:
print(field.parse(sample_text), field.parse_values(sample_text)) # {"digits": [1, 10]} [1, 10]
```
* ReFieldListDict
Возвращает все найденные значения в виде {name: [{key1: value1}, {key2: value2}, ...]}. параметр `name` 
и идентификаторы групп обязательны. Для преобразования в типы использовать after_exec_func

```python
from anicli_api.re_models import ReFieldListDict
sample_text = "digit=1 digitt=10"

field = ReFieldListDict(r"(?P<key>\w+)=(?P<value>\d+)",
                        name="vals",
                        after_exec_type={"key": lambda k: k.upper(),
                                         "value": int})
# эквивалента записи:
print(field.parse(sample_text), field.parse_values(sample_text)) # {"vals": [{"DIGIT": 1}, {"DIGITT": 10}]} [{"DIGIT": 1}, {"DIGITT": 10}]
```

* parse_many
Вспомогательная функция, принимает текст и произвольное число объектов типа `ReBaseField`. 
Возвращает словарь со всеми найденными результатами.
```python
from anicli_api.re_models import ReField, ReFieldList, ReFieldListDict, parse_many
sample_text = "digit=1 digitt=10"

result = parse_many(sample_text,
                    ReField(r"\w+=(?P<digit>\d+)",
                            type=int),
                    ReFieldList(r"\w+=(\d+)",
                                type=int,
                                name="digits"),
                    ReFieldListDict(r"(?P<key>\w+)=(?P<value>\d+)",
                                    name="vals",
                                    after_exec_type={"key": lambda k: k.upper(),
                                                     "value": int}),
                    ReField(r"failedpattern",
                                name="fail",
                                ),
                    ReFieldList(r"failedpattern",
                                name="fail_list",
                                ),
                    ReFieldListDict(r"failedpattern",
                                    name="fail_list_dict"))
print(result)
# {'digit': 1, 'digits': [1, 10], 
# 'vals': [{'key': 'DIGIT', 'value': 1}, {'key': 'DIGITT', 'value': 10}], 
# 'fail': None, 'fail_list': [], 'fail_list_dict': []}
```

### http
Предварительно сконфигурированные объекты [httpx.Client](https://www.python-httpx.org/api/#client) и 
[httpx.AsyncClient](https://www.python-httpx.org/api/#asyncclient)

По умолчанию `allow_redirects=True` и `headers` имеет значение:
`{"user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)"
                                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 "
                                         "Mobile Safari/537.36",
                           "x-requested-with": "XMLHttpRequest"}`

```shell
BaseHTTPSync - httpx.Client, с включенными редиректами и установленным юзерагентом
BaseHTTPAsync - httpx.AsyncClient, с включенными редиректами и установленным юзерагентом
```
Остальные модификации имеют singleton паттерн и простую проверку на наличие ddos защиты. 
Если ddos защита присутствует (идёт проверка по заголовку сервера и коду 403 ) - выбросит ошибку ConnectionError
```shell
HTTPSync - httpx.Client, синглтон, включён редирект, есть юзерагент, установлен event_hook на проверку ddos защиты
HTTPAsync - httpx.AsyncClient, синглтон, включён редирект, есть юзерагент, установлен event_hook на проверку ddos защиты
```
Работа с методами и сессиями аналогично оригинальным классам
### loader
Динамический загрузчик Экстракторов-парсеров с предварительной типизацией
* ExtractorLoader - объект загрузчика
```shell
load(module_name: str) - загружает модуль по названию. Если модуль не имеет структуру экстрактора или он отсутствует - 
вернёт ошибку
load_all() - загружает все модули из папки extractors
```
### decoders
модуль, в котором хранятся парсеры с видеохостингов.
* BaseDecoder - базовый класс декодера
```shell
parse(cls, url: str, **kwargs) - возвращает все прямые ссылки на видео 
async_parse(cls, url: str, **kwargs) - возвращает все прямые ссылки на видео асинхронно
```
```python
from anicli_api.decoders import Kodik, Aniboom
urls_a = Aniboom.parse('https://aniboom.one/embed/N9QdKm4Mwz1?episode=1&translation=2')
urls_k = Kodik.parse("https://kodik.info/seria/1026046/02a256101df196484d68d10d28987fbb/720p")
```
### random_useragent
Простой генератор случайных юзер агентов
```python
from anicli_api.random_useragent import Agent
Agent.mobile()  # случайный мобильный юзерагент
Agent.desktop() # случайный декстоп юзерагент
Agent.random()  # случайный мобильный или декстопный юзерагент
```
