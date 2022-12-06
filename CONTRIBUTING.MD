Перед разработкой ознакомьтесь с [dev](DEV.MD) документацией
# Quickstart:
1. Сделайте fork этого репозитория
2. Клонируйте из своего репозитория fork
3. Настройка окружения
    1. Через *Makefile* (рекомендуется): `make venv`
    2. Ручная: `python3 -m pip install poerty && poetry shell && poetry install`
4. Рекомендуется подключить git hooks: `make githooks`
5. Переключиться на `dev` ветку
6. Внести изменения, сделать commit, создать pull request
7. **!!! Ваши изменения должны пройти CI/CD проверку успешно в github actions.**

Предварительно изменения можно проверить командами:
`make check`

Или:
```shell
poetry run flake8 .
poetry run mypy .
poetry run pytest
```

Прогнать форматирование black, isort: `make fix`

Или:
```shell
poetry run black .
poetry run isort .
```

# Требования к новому Decoder'у:

Необходимо написать тест с использованием [httpx.MockTransport](https://www.python-httpx.org/advanced/#mock-transports)
для "приближенного к идентичному" заглушки ответов и проверки работы декодера и поместить в [tests/decoders](tests/decoders)

# Требования к новому Extractor'у:
1. Должны быть реализованы __все__ методы (sync and async)
2. Должны быть написаны тесты со стабильными кейсами, хотя бы из шаблона. Например, на поиск и получение метаинформации
используйте такие тайтлы, которые давно вышли и гарантированно есть на сайте (например, Serial of experiments lain, Cowboy Bebop и тп).

Онгоинги достаточно на длину сравнивать: они постоянно меняются и надежный тест сложнее написать.
3. Если будете применять регулярные выражения, то пишите максимально "гибкие", подробнее почитайте рекомендации
из [yt-dlp CONTRIBUTING.md](https://github.com/yt-dlp/yt-dlp/blob/master/CONTRIBUTING.md#regular-expressions)

Если не уверены в надежности регулярных выражений, используйте bs4 модуль или изучите эту тему детальнее.