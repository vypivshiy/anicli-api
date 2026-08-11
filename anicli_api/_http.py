"""
This module contains httpx.Client and httpx.AsyncClient classes with the following settings:

1. User-agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)
AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114

2. x-requested-with: XMLHttpRequest

"""

from __future__ import annotations

import asyncio
from time import monotonic, sleep

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
    "ANUBIS_CHALLENGE_MARKERS",
)

# DDoS protection check by "Server" key header
DDOS_SERVICES = ("cloudflare", "ddos-guard")

# Anubis bot-protect passive bypass.
#
# Anubis (https://github.com/TecharoHQ/anubis) challenges clients whose
# User-Agent contains "Mozilla". Stripping that substring from the UA bypasses
# the challenge entirely - by design, so RSS/git clients pass through.
#
# Challenge HTML page is detected by 2 stable script-id markers in the body:
#   <script id="anubis_version" ...>
#   <script id="anubis_challenge" ...>
# Ref: https://github.com/TecharoHQ/anubis/blob/main/docs/docs/design/how-anubis-works.mdx
ANUBIS_CHALLENGE_MARKERS: tuple[str, ...] = (
    'id="anubis_version"',
    'id="anubis_challenge"',
)

# Per-process cache: netloc -> timestamp (monotonic) when bypass was applied.
# TTL-bounded; never downgrades within TTL. Race-safe: dict ops are atomic in
# CPython; idempotent re-marking within TTL is a no-op.
_ANUBIS_TTL_SECONDS: float = 3600.0
_anubis_bypass_hosts: dict[str, float] = {}


def _anubis_netloc(url) -> str:
    nl = url.netloc
    return nl.decode() if isinstance(nl, bytes) else nl


def _anubis_needs_bypass(netloc: str) -> bool:
    ts = _anubis_bypass_hosts.get(netloc)
    if ts is None:
        return False
    if (monotonic() - ts) > _ANUBIS_TTL_SECONDS:
        _anubis_bypass_hosts.pop(netloc, None)
        return False
    return True


def _mark_anubis_host(netloc: str) -> None:
    _anubis_bypass_hosts[netloc] = monotonic()


def _is_anubis_challenge(resp: Response) -> bool:
    """Detect Anubis challenge page in a (sync) response.

    Gates: status 200 + Content-Type contains "html" + both markers in body.
    Materializes the streaming body via resp.read() if not yet buffered.
    """
    if resp.status_code != 200:
        return False
    if "html" not in resp.headers.get("content-type", "").lower():
        return False
    if not hasattr(resp, "_content"):
        resp.read()
    body = resp.text
    return all(marker in body for marker in ANUBIS_CHALLENGE_MARKERS)


async def _is_anubis_challenge_async(resp: Response) -> bool:
    """Async counterpart of _is_anubis_challenge. Awaits resp.aread() if needed."""
    if resp.status_code != 200:
        return False
    if "html" not in resp.headers.get("content-type", "").lower():
        return False
    if not hasattr(resp, "_content"):
        await resp.aread()
    body = resp.text
    return all(marker in body for marker in ANUBIS_CHALLENGE_MARKERS)


def apply_anubis_bypass(request: Request) -> None:
    """Strip 'Mozilla' substring from request's User-Agent header (in-place).

    Per Anubis design: UA without "Mozilla" passes the challenge gate.
    """
    ua = request.headers.get("User-Agent", "")
    if "Mozilla" in ua:
        request.headers["User-Agent"] = ua.replace("Mozilla", "")


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


# Server-side transient failures worth retrying. 500 included: some upstreams
# (notably hdrezka CDN) return 500 intermittently and a retry succeeds.
# 429 needs Retry-After handling and is a separate concern.
RETRYABLE_STATUS_CODES: tuple[int, ...] = (500, 502, 503, 504)
MAX_5XX_RETRIES = 3
MAX_RETRY_AFTER_SECONDS = 30.0


class HTTPRetryConnectSyncTransport(HTTPTransport):
    """Handle attempts connects with delay"""

    ATTEMPTS_CONNECT = 10
    RETRY_CONNECT_DELAY = 1.2
    DELAY_INCREASE_STEP = 0.3  # linear increase connect delay

    def handle_request(self, request: Request) -> Response:
        delay = self.RETRY_CONNECT_DELAY
        netloc = _anubis_netloc(request.url)
        pre_bypass = _anubis_needs_bypass(netloc)
        if pre_bypass:
            apply_anubis_bypass(request)
        anubis_attempted = False

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

                # Anubis bot-protect passive bypass (one attempt per request)
                if not pre_bypass and not anubis_attempted and _is_anubis_challenge(resp):
                    anubis_attempted = True
                    _mark_anubis_host(netloc)
                    apply_anubis_bypass(request)
                    logger.info("Anubis challenge detected for %s, applying UA bypass", netloc)
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
        netloc = _anubis_netloc(request.url)
        pre_bypass = _anubis_needs_bypass(netloc)
        if pre_bypass:
            apply_anubis_bypass(request)
        anubis_attempted = False

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

                # Anubis bot-protect passive bypass (one attempt per request)
                if not pre_bypass and not anubis_attempted and await _is_anubis_challenge_async(resp):
                    anubis_attempted = True
                    _mark_anubis_host(netloc)
                    apply_anubis_bypass(request)
                    logger.info("Anubis challenge detected for %s, applying UA bypass", netloc)
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
