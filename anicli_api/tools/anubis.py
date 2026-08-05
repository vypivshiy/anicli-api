"""
Простой трюк для обхода anubis antibot

если удалить подстроку Mozilla в user-agent - проверка пропустится.

это легитимное поведение, умышленно заложено автором в дизайн

https://github.com/TecharoHQ/anubis/blob/main/docs/docs/design/how-anubis-works.mdx#challenge-presentation

```
Anubis decides to present a challenge using this logic:

    User-Agent contains "Mozilla"
...

This should ensure that git clients, RSS readers, and other low-harm clients can get through without issue, but high-risk clients such as browsers and AI scraper bots will get blocked.
```
"""

from typing import Any, Generator, Protocol, MutableMapping
from contextlib import contextmanager


class HasHeaders(Protocol):
    @property
    def headers(self) -> MutableMapping[str, str]: ...


@contextmanager
def path_anubis_user_agent(client: HasHeaders) -> Generator[None, Any, None]:
    """Временный патч user-agent для обхода anubis antibot

    в headers заголовке User-Agent убирает подстроку "Mozilla", потом автоматически восстанавливает

    Usage:

    ```
    # работает на любом клиенте, где есть доступ к заголовкам через атрибут 'headers'
    # client = httpx.AsyncClient()
    # client = requests.Session()
    client = httpx.Client()
    
    with path_anubis_user_agent(client):
        client.get("https://example.com")
    ```

    """
    tmp_ua = client.headers["User-Agent"]
    client.headers["User-Agent"] = tmp_ua.replace("Mozilla", "")
    try:
        yield
    finally:
        client.headers["User-Agent"] = tmp_ua
