Decoders
--------
Если у вас есть непрямая ссылка на видео с хостинга (на момент написания реализованы kodik, aniboom, sibnet),
вы можете импортировать декодер и получить видео

.. literalinclude:: ../../examples/example_decoders.py
    :language: python

extra_headers содержит словарь с минимально необходимыми значениями headers, чтобы позже получить видео напрямую.

У Decoder классов реализован оператор сравнения. Можно определить, будет он работать ссылкой или нет:

.. code-block:: python
    from anicli_api.decoders import Aniboom, Kodik
    url_unknown = "https://youtube.com"
    url_kodik = "https://kodik.info/seria/1026046/02a256101df196484d68d10d28987fbb/720p"
    url_aniboom = "https://aniboom.one/embed/N9QdKm4Mwz1?episode=1&translation=2"
    url_unknown == Aniboom(), url_unknown == Kodik() # False, False
    url_kodik == Kodik(), url_kodik == Aniboom() # True, False
    url_aniboom == Kodik(), url_aniboom == Aniboom() # False, True
