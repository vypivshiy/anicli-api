"""
This module contains httpx.Client and httpx.AsyncClient classes with the following settings:

1. User-agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)
AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114

2. x-requested-with: XMLHttpRequest

"""
import asyncio
from time import sleep
from typing import Dict

from httpx import (
    AsyncClient,
    AsyncHTTPTransport,
    Client,
    ConnectError,
    HTTPTransport,
    NetworkError,
    Request,
    Response,
    TimeoutException,
)

from anicli_api._logger import logger

HEADERS: Dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
    "x-requested-with": "XMLHttpRequest",  # XMLHttpRequest required
    "Sec-Ch-Ua": '"Not.A/Brand";v="8", "Chromium";v="114"',
    "Sec-Ch-Ua-Mobile": "?1",
    "Sec-Ch-Ua-Platform": '"Android"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
}

# DDoS protection check by "Server" key header
DDOS_SERVICES = ("cloudflare", "ddos-guard")

__all__ = (
    "BaseHTTPSync",
    "BaseHTTPAsync",
    "HTTPSync",
    "HTTPAsync",
    "HTTPRetryConnectSyncTransport",
    "HTTPRetryConnectAsyncTransport",
)


class HTTPRetryConnectSyncTransport(HTTPTransport):
    """Handle attempts connects with delay"""

    ATTEMPTS_CONNECT = 5
    RETRY_CONNECT_DELAY = 0.7
    DELAY_INCREASE_STEP = 0.2  # RETRY_CONNECT_DELAY + (DELAY_INCREASE_STEP * attempt) / 2

    def handle_request(self, request: Request) -> Response:
        delay = self.RETRY_CONNECT_DELAY
        for i in range(self.ATTEMPTS_CONNECT):
            try:
                return super().handle_request(request)
            except (NetworkError, TimeoutException) as exc:
                msg = f"[{i+1}] {exc.__class__.__name__}, {request.method} {request.url} try retry connect"
                sleep(delay)
                logger.warning(msg)
                delay += (self.DELAY_INCREASE_STEP * i + 1) / 2
        return super().handle_request(request)


class HTTPRetryConnectAsyncTransport(AsyncHTTPTransport):
    """Handle attempts connects with delay"""

    ATTEMPTS_CONNECT = 5
    RETRY_CONNECT_DELAY = 0.7
    DELAY_INCREASE_STEP = 0.2  # RETRY_CONNECT_DELAY + (DELAY_INCREASE_STEP * attempt) / 2

    async def handle_async_request(
        self,
        request: Request,
    ) -> Response:
        delay = self.RETRY_CONNECT_DELAY
        for i in range(self.ATTEMPTS_CONNECT):
            try:
                return await super().handle_async_request(request)
            except (NetworkError, TimeoutException) as exc:
                await asyncio.sleep(delay)
                delay += (self.DELAY_INCREASE_STEP * i + 1) / 2
                msg = f"[{i+1}] {exc.__class__.__name__}, {request.method} {request.url} try retry connect"
                logger.warning(msg)
        return await super().handle_async_request(request)


class HttpxSingleton:
    _client_instance = None
    IS_CLIENT_INSTANCE_INIT = False

    _async_client_instance = None
    IS_ASYNC_CLIENT_INSTANCE_INIT = False

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
        http2 = kwargs.pop("http2", True)
        transport = kwargs.pop("transport", HTTPRetryConnectSyncTransport())

        super().__init__(http2=http2, transport=transport, **kwargs)
        self.headers.update(HEADERS.copy())
        self.headers.update(kwargs.pop("headers", {}))
        self.follow_redirects = kwargs.pop("follow_redirects", True)


class BaseHTTPAsync(AsyncClient):
    """httpx.AsyncClient class with configured user agent and enabled redirects"""

    def __init__(self, **kwargs):
        http2 = kwargs.pop("http2", True)
        transport = kwargs.pop("transport", HTTPRetryConnectAsyncTransport())

        super().__init__(http2=http2, transport=transport, **kwargs)
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
        msg = f"{resp.url} have '{resp.headers.get('Server', 'unknown')}' and return 403 code."
        raise ConnectError(msg)


class HTTPSync(HttpxSingleton, BaseHTTPSync):
    """
    Base singleton **sync** HTTP class with recommended config.

    Used in extractors and can configure at any point in the program"""

    def __init__(self, **kwargs):
        if not self.IS_CLIENT_INSTANCE_INIT:  # dirty hack for update arguments
            super().__init__(**kwargs)
            self.event_hooks.update({"response": [check_ddos_protect_hook]})
            self._client_instance_init = True


class HTTPAsync(HttpxSingleton, BaseHTTPAsync):
    """
    Base singleton **async** HTTP class with recommended config

    Used in extractors and can configure at any point in the program
    """

    def __init__(self, **kwargs):
        if not self.IS_ASYNC_CLIENT_INSTANCE_INIT:  # dirty hack for update arguments
            super().__init__(**kwargs)
            self.event_hooks.update({"response": [check_ddos_protect_hook]})
            self._async_client_instance_init = True
