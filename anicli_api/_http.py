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
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
    # XMLHttpRequest required
    "x-requested-with": "XMLHttpRequest",
    "Sec-Ch-Ua": '"Not.A/Brand";v="8", "Chromium";v="114"',
    "Sec-Ch-Ua-Mobile": "?1",
    "Sec-Ch-Ua-Platform": '"Android"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
}
# DDoS protection check by "Server" key header
DDOS_SERVICES = ("cloudflare", "ddos-guard")

__all__ = ("BaseHTTPSync", "BaseHTTPAsync", "HTTPSync", "HTTPAsync")


class HttpxSingleton:
    _client_instance = None
    _client_instance_init = False

    _async_client_instance = None
    _async_client_instance_init = False

    def __new__(cls, *args, **kwargs):
        if issubclass(cls, HTTPSync):
            if not cls._client_instance:
                cls._client_instance = super().__new__(cls)
            return cls._client_instance

        elif issubclass(cls, HTTPAsync):
            if not cls._async_client_instance:
                cls._async_client_instance = super().__new__(cls)
            return cls._async_client_instance


class BaseHTTPSync(Client):
    """httpx.Client class with configured user agent and enabled redirects"""

    def __init__(self, **kwargs):
        super().__init__(http2=kwargs.pop("http2", True), **kwargs)
        self.headers.update(HEADERS.copy())
        self.headers.update(kwargs.pop("headers", {}))
        self.follow_redirects = kwargs.pop("follow_redirects", True)


class BaseHTTPAsync(AsyncClient):
    """httpx.AsyncClient class with configured user agent and enabled redirects"""

    def __init__(self, **kwargs):
        http2 = kwargs.pop("http2", True)
        super().__init__(http2=http2, **kwargs)
        self._headers.update(HEADERS.copy())
        self._headers.update(kwargs.pop("headers", {}))
        self.follow_redirects = kwargs.pop("follow_redirects", True)


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


class HTTPSync(HttpxSingleton, BaseHTTPSync):
    """
    Base singleton **sync** HTTP class with recommended config.

    Used in extractors and can configure at any point in the program"""

    def __init__(self, **kwargs):
        if not self._client_instance_init:  # dirty hack for update arguments
            super().__init__(**kwargs)
            self.event_hooks.update({"response": [check_ddos_protect_hook]})
            self._client_instance_init = True


class HTTPAsync(HttpxSingleton, BaseHTTPAsync):
    """
    Base singleton **async** HTTP class with recommended config

    Used in extractors and can configure at any point in the program
    """

    def __init__(self, **kwargs):
        if not self._async_client_instance_init:  # dirty hack for update arguments
            super().__init__(**kwargs)
            self.event_hooks.update({"response": [check_ddos_protect_hook]})
            self._async_client_instance_init = True
