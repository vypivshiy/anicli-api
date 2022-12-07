FAQ
===
Здесь будут некоторые быстрые ответы и способы решений

Как изменить объект сессии в парсерах
-------------------------------------

В библиотеке есть 2 вида классов для запросов:

Для синхронных запросов
^^^^^^^^^^^^^^^^^^^^^^^

- BaseHTTPSync, HTTPSync

BaseHTTPSync - **модифицированный** httpx.Client класс с предустановленным юзерагентом и включенными редиректами

HTTPSync - имеет свойства **BaseHTTPSync**, только он **Singleton** с установленным хуком на проверку ddos защиты

Для асинхронных запросов
^^^^^^^^^^^^^^^^^^^^^^^^

-  BaseHTTPAsync HTTPAsync

BaseHTTPAsync - **модифицированный** httpx.AsyncClient класс с предустановленным юзерагентом и включенными редиректами

HTTPAsync - имеет свойства **BaseHTTPAsync**, только он **Singleton** с установленным хуком на проверку ddos защиты

В экстракторах используются Singleton классы ``HTTPSync, HTTPAsync``, их можно модифицировать в любой точке программы.



.. code-block:: python
        from anicli_api import HTTPSync

        __SESSION = HTTPSync()
        __SESSION.headers.update({"user-agent": "my_useragent"})
        # во всех экстракторах будет использоваться юзерагент my_useragent


.. code-block:: python
        from anicli_api.extractors import anilibria, animevost

        extractor = anilibria.Extractor()

        # инициализация классов нужна!
        extractor.HTTP().headers.update({"user-agent": "my_useragent"})
        extractor.HTTP_ASYNC().headers.update({"user-agent": "my_useragent"})
        assert animevost.Extractor().HTTP().headers == extractor.HTTP().headers


Подробнее по работе c httpx читайте в официальной документации:

* https://www.python-httpx.org/advanced/
* https://www.python-httpx.org/api/#client
* https://www.python-httpx.org/api/#asyncclient

.. note::
    В Decoder классах **не используются** Singleton классы, там необходимо параметры настройки объекта сессии передавать
    в метод parse или async_parse через именованные аргументы ``**kwargs``

    Автоматически через объект **Video** не получится передать необходимые параметры для сессии,
    и придется вручную получать видео. и передавать в Decoder

    Позже эта недоработка будет устранена.