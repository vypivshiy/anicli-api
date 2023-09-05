"""
This module contains httpx.Client and httpx.AsyncClient classes with the following settings:

1. User-agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)
AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114

2. x-requested-with: XMLHttpRequest

"""
from typing import Dict

from httpx import AsyncClient, Client, Response

from anicli_api._logger import logger

HEADERS: Dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    # XMLHttpRequest required
    "x-requested-with": "XMLHttpRequest",
}
# DDoS protection check by "Server" key header
DDOS_SERVICES = ("cloudflare", "ddos-guard")

__all__ = ("BaseHTTPSync", "BaseHTTPAsync", "HTTPSync", "HTTPAsync", "Singleton")


class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance


class BaseHTTPSync(Client):
    """httpx.Client class with configured user agent and enabled redirects"""

    def __init__(self, **kwargs):
        super().__init__(http2=True, **kwargs)
        self.headers.update(HEADERS)
        self.follow_redirects = True


class BaseHTTPAsync(AsyncClient):
    """httpx.AsyncClient class with configured user agent and enabled redirects"""

    def __init__(self, http2: bool = True, **kwargs):
        super().__init__(http2=http2, **kwargs)
        self.headers.update(HEADERS)
        self.follow_redirects = True


def check_ddos_protect_hook(resp: Response):
    """
    Simple ddos protect check hook.

    If response return 403 code or server headers contains *cloudflare* or *ddos-guard* strings and
    **Connection = close,** throw ConnectionError traceback
    """
    logger.debug("%s check DDOS protect :\nstatus [%s] %s", resp.url, resp.status_code, resp.headers)
    if (
        resp.headers.get("Server") in DDOS_SERVICES
        and resp.headers.get("Connection", None) == "close"
        or resp.status_code == 403
    ):
        logger.error("Ooops, %s have ddos protect :(", resp.url)
        raise ConnectionError(f"{resp.url} have '{resp.headers.get('Server', 'unknown')}' and return 403 code.")


class HTTPSync(Singleton, BaseHTTPSync):
    """
    Base singleton **sync** HTTP class with recommended config.

    Used in extractors and can configure at any point in the program"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event_hooks.update({"response": [check_ddos_protect_hook]})


class HTTPAsync(Singleton, BaseHTTPAsync):
    """
    Base singleton **async** HTTP class with recommended config

    Used in extractors and can configure at any point in the program
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event_hooks.update({"response": [check_ddos_protect_hook]})
