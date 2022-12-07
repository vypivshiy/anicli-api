===========
Quickstart
===========
Install
=======
.. code-block:: shell

    python3 -m pip install anicli-api

How is works?
=============
Шаги выполнения:

1. Extractor.search(), Extractor.ongoing() -> (List[SearchResult]/List[Ongoing])

2. SearchResult.get_anime(), Ongoing.get_anime() -> (AnimeInfo)

3. AnimeInfo.get_episodes() -> (List[Episode])

4. Episode.get_videos() -> (List[Video])

5. Video.get_source() -> (List[MetaVideo])

.. note::
    Может итерироваться сразу и возвращать все объекты через:

    - Extractor.walk_search

    - Extractor.walk_ongoing

    - Search

    - Ongoing

Usage example
=============

#. Импортрируйте готовый экстрактор

.. literalinclude:: ../../examples/quickstart.py
    :language: python
    :lines: 1-2

Экстрактор имеет синхронные и асинхронные реализации запросов:

Sync usage example
------------------

Пошаговый поиск по строке и получение контента:

.. literalinclude:: ../../examples/quickstart.py
    :language: python
    :lines: 4-18

Пошаговый поиск онгоингов и получение контента

.. literalinclude:: ../../examples/quickstart.py
    :language: python
    :lines: 21-33

walk_search - итератор по всем объектам через search.

Возвращает датакласс со всеми объектами: Search, AnimeInfo, Episode, Video на каждом шагу итерации

.. literalinclude:: ../../examples/quickstart.py
    :language: python
    :lines: 33-42

walk_ongoing - итератор по всем объектам через ongoing

Возвращает датакласс со всеми объектами: Ongoing, AnimeInfo, Episode, Video на каждом шагу итерации

.. literalinclude:: ../../examples/quickstart.py
    :language: python
    :lines: 45-52


Можно итерировать через Ongoing, SearchResult и получить датакласс.

.. literalinclude:: ../../examples/quickstart.py
    :language: python
    :lines: 55-82

Полный код:

.. literalinclude:: ../../examples/quickstart.py
    :language: python


Async usage example
-------------------
Асинхронные методы дублируют функционал синхронных. Они имеют префикс *a_* или *async_*:

.. literalinclude:: ../../examples/quickstart_asyncio.py
    :language: python
