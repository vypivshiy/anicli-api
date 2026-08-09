"""
This module contains httpx.Client and httpx.AsyncClient classes with the following settings:

1. User-agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)
AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114

2. x-requested-with: XMLHttpRequest

"""

from __future__ import annotations

import asyncio
from time import sleep

from httpx import (
    AsyncClient,
    AsyncHTTPTransport,
    Client,
    HTTPTransport,
    NetworkError,
    ReadTimeout,
    Request,
    Response,
    TimeoutException,
    ConnectTimeout,
)

from anicli_api._logger import logger

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10.0; Nexus 5 Build/MRA58N) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
    # Often, XMLHttpRequest header required
    "x-requested-with": "XMLHttpRequest",
    "Sec-Ch-Ua": '"Not.A/Brand";v="8", "Chromium";v="114"',
    "Sec-Ch-Ua-Mobile": "?1",
    "Sec-Ch-Ua-Platform": '"Android"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
}

__all__ = (
    "BaseHTTPSync",
    "BaseHTTPAsync",
    "HTTPSync",
    "HTTPAsync",
    "HTTPRetryConnectSyncTransport",
    "HTTPRetryConnectAsyncTransport",
    "DDOSServerDetectError",
    "ANUBIS_BYPASS_HEADERS",
)

# DDoS protection check by "Server" key header
DDOS_SERVICES = ("cloudflare", "ddos-guard")

# Anubis bot-protect bypass: User-Agent without "Mozilla" substring.
# https://github.com/TecharoHQ/anubis/blob/main/docs/docs/design/how-anubis-works.mdx
#
# Anubis decides to challenge based on UA containing "Mozilla"; stripping that
# substring bypasses the challenge. Pass per-call via `headers=ANUBIS_BYPASS_HEADERS`
# to any fetch() / client.request() - the sscgen-generated fetchers already
# accept **kwargs and merge dict-valued keys (headers/params/data) with their
# own defaults, so this overrides the client's UA without mutating shared state.
ANUBIS_BYPASS_HEADERS: dict[str, str] = {"User-Agent": HEADERS["User-Agent"].replace("Mozilla", "")}


def have_ddos_protect(response: Response) -> bool:
    """detect ddos protect for next cases:

    - Server header AND Connection = close (this project usage keep-alive sessions)

    - status_code = 403
    """
    return (
        response.headers.get("Server") in DDOS_SERVICES
        and response.headers.get("Connection", None) == "close"
        or response.status_code == 403
    )


class DDOSServerDetectError(NetworkError):
    """raise this exception if detect cloudflare or ddos-guard protect"""

    pass


def _parse_retry_after(resp: Response) -> float | None:
    """Parse Retry-After header. Returns seconds or None if absent/malformed.

    Supports both delta-seconds (integer) and HTTP-date formats (RFC 7231).
    """
    val = resp.headers.get("Retry-After") or resp.headers.get("retry-after")
    if not val:
        return None
    val = val.strip()
    # delta-seconds form
    try:
        secs = float(val)
        return secs if secs >= 0 else None
    except ValueError:
        pass
    # HTTP-date form
    try:
        from email.utils import parsedate_to_datetime
        from datetime import datetime, timezone

        dt = parsedate_to_datetime(val)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = (dt - now).total_seconds()
        return max(0.0, delta)
    except (TypeError, ValueError):
        return None


# Server-side transient failures worth retrying. 500 excluded (server bug, retry
# won't help). 429 needs Retry-After handling and is a separate concern.
RETRYABLE_STATUS_CODES: tuple[int, ...] = (502, 503, 504)
MAX_5XX_RETRIES = 3
MAX_RETRY_AFTER_SECONDS = 30.0


class HTTPRetryConnectSyncTransport(HTTPTransport):
    """Handle attempts connects with delay"""

    ATTEMPTS_CONNECT = 10
    RETRY_CONNECT_DELAY = 1.2
    DELAY_INCREASE_STEP = 0.3  # linear increase connect delay

    def handle_request(self, request: Request) -> Response:
        delay = self.RETRY_CONNECT_DELAY
        for i in range(self.ATTEMPTS_CONNECT):
            try:
                resp = super().handle_request(request)
                if have_ddos_protect(resp):
                    msg = f"'{resp.headers.get('Server')}': {request.url} returns code {resp.status_code}"
                    raise DDOSServerDetectError(msg)

                # Retry transient 5xx (e.g. cloudflare 502/503/504 on upstream timeout)
                if resp.status_code in RETRYABLE_STATUS_CODES and i < MAX_5XX_RETRIES:
                    retry_after = _parse_retry_after(resp)
                    sleep_for = min(retry_after, MAX_RETRY_AFTER_SECONDS) if retry_after else delay
                    logger.warning(
                        "[%s] %s status %d, retry in %.1fs",
                        i + 1,
                        request.url,
                        resp.status_code,
                        sleep_for,
                    )
                    sleep(sleep_for)
                    delay += self.DELAY_INCREASE_STEP
                    continue

                logger.debug("%s -> %s", repr(request), repr(resp))
                return resp

            except (NetworkError, TimeoutException, ReadTimeout) as exc:
                # HACK: stub response to avoid UnboundLocalError
                resp = locals().get("resp", "")

                exc_name = exc.__class__.__name__
                exc_msg = getattr(exc, "message", exc.args[0])
                sleep(delay)
                logger.warning("[%s] %s: %s, %s -> %s try again", i + 1, exc_name, exc_msg, repr(request), repr(resp))  # type: ignore
                if isinstance(exc, DDOSServerDetectError) and i == self.ATTEMPTS_CONNECT - 1:
                    raise exc
                delay += self.DELAY_INCREASE_STEP
        return super().handle_request(request)


class HTTPRetryConnectAsyncTransport(AsyncHTTPTransport):
    """Handle attempts connects with delay"""

    ATTEMPTS_CONNECT = 10
    RETRY_CONNECT_DELAY = 1.2
    DELAY_INCREASE_STEP = 0.3  # linear increase connect delay

    async def handle_async_request(
        self,
        request: Request,
    ) -> Response:
        delay = self.RETRY_CONNECT_DELAY
        for i in range(self.ATTEMPTS_CONNECT):
            try:
                resp = await super().handle_async_request(request)
                if have_ddos_protect(resp):
                    msg = f"'{resp.headers.get('Server')}': {request.url} returns code {resp.status_code}"
                    raise DDOSServerDetectError(msg)

                # Retry transient 5xx (e.g. cloudflare 502/503/504 on upstream timeout)
                if resp.status_code in RETRYABLE_STATUS_CODES and i < MAX_5XX_RETRIES:
                    retry_after = _parse_retry_after(resp)
                    sleep_for = min(retry_after, MAX_RETRY_AFTER_SECONDS) if retry_after else delay
                    logger.warning(
                        "[%s] %s status %d, retry in %.1fs",
                        i + 1,
                        request.url,
                        resp.status_code,
                        sleep_for,
                    )
                    await asyncio.sleep(sleep_for)
                    delay += self.DELAY_INCREASE_STEP
                    continue

                logger.debug(
                    "%s -> %s",
                    repr(request),
                    repr(resp),
                )

                return resp

            except (ConnectTimeout, NetworkError, TimeoutException) as exc:
                # HACK: stub response to avoid UnboundLocalError
                resp = locals().get("resp", "")

                exc_name = exc.__class__.__name__
                exc_msg = getattr(exc, "message", exc.args[0])

                if isinstance(exc, DDOSServerDetectError) and i == self.ATTEMPTS_CONNECT - 1:
                    raise exc

                logger.warning("[%s] %s: %s, %s -> %s", i + 1, exc_name, exc_msg, repr(request), repr(resp))  # type: ignore
                await asyncio.sleep(delay)
                delay += self.DELAY_INCREASE_STEP
        return await super().handle_async_request(request)


class BaseHTTPSync(Client):
    """httpx.Client class with configured user agent and enabled redirects"""

    def __init__(self, **kwargs):
        http2 = kwargs.pop("http2", True)
        transport = kwargs.pop("transport", HTTPRetryConnectSyncTransport())
        headers = kwargs.pop("headers", HEADERS.copy())
        follow_redirects = kwargs.pop("follow_redirects", True)

        super().__init__(http2=http2, transport=transport, headers=headers, follow_redirects=follow_redirects, **kwargs)


class BaseHTTPAsync(AsyncClient):
    """httpx.AsyncClient class with configured user agent and enabled redirects"""

    def __init__(self, **kwargs):
        http2 = kwargs.pop("http2", True)
        transport = kwargs.pop("transport", HTTPRetryConnectAsyncTransport())
        headers = kwargs.pop("headers", HEADERS.copy())
        follow_redirects = kwargs.pop("follow_redirects", True)

        super().__init__(http2=http2, transport=transport, headers=headers, follow_redirects=follow_redirects, **kwargs)


HTTPSync = BaseHTTPSync
HTTPAsync = BaseHTTPAsync
