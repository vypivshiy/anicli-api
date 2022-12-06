===========
Quickstart
===========

Usage example
=============

#. import extractor

.. literalinclude:: ../examples/quickstart.py
    :language: python
    :lines: 1-2

Extractor has a sync and async implementations:

Sync usage example
------------------

Step-by-step get search result content:

.. literalinclude:: ../examples/quickstart.py
    :language: python
    :lines: 4-18

Step_by_step get ongoings content

.. literalinclude:: ../examples/quickstart.py
    :language: python
    :lines: 21-33

walk_search - iterate and get all objects from extractor instance

.. literalinclude:: ../examples/quickstart.py
    :language: python
    :lines: 33-42

walk_ongoing - iterate and get all objects from extractor instance

.. literalinclude:: ../examples/quickstart.py
    :language: python
    :lines: 45-52

Ongoing, SearchResult is iterable objects, and can return all objects:

.. literalinclude:: ../examples/quickstart.py
    :language: python
    :lines: 55-82

full code example:

.. literalinclude:: ../examples/quickstart.py
    :language: python


async usage example
-------------------
async methods duplicate sync methods, here it is similarЖ

.. literalinclude:: ../examples/quickstart_asyncio.py
    :language: python
decoders
--------
If you have a link to a hosting video (at the time of writing, kodik, aniboom, sibnet are implemented),
then you can import a separate decoder and get direct links to the video!

.. literalinclude:: ../examples/example_decoders.py
    :language: python

Note
-----

- Most parsers avoid official methods, 100% fail-safe is not guaranteed. They are designed for personal non-commercial use.
