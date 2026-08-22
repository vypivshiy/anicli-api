"""Tests for 5xx retry behavior in HTTPRetryConnect{Sync,Async}Transport.

Verifies that 502/503/504 responses are retried up to MAX_5XX_RETRIES, that
Retry-After header is honored when present, and that non-retryable statuses
(e.g. 200, 500) are returned immediately.
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest

from anicli_api._http import (
    HTTPRetryConnectAsyncTransport,
    HTTPRetryConnectSyncTransport,
    MAX_5XX_RETRIES,
    RETRYABLE_STATUS_CODES,
    _parse_retry_after,
)


def _build_request(url: str = "https://example.com/") -> httpx.Request:
    return httpx.Request("GET", url)


def test_parse_retry_after_seconds():
    r = httpx.Response(503, headers={"Retry-After": "5"})
    assert _parse_retry_after(r) == 5.0


def test_parse_retry_after_missing():
    r = httpx.Response(503)
    assert _parse_retry_after(r) is None


def test_parse_retry_after_garbage():
    r = httpx.Response(503, headers={"Retry-After": "not-a-number-nor-date"})
    assert _parse_retry_after(r) is None


def test_parse_retry_after_negative_treated_as_zero_or_none():
    r = httpx.Response(503, headers={"Retry-After": "-3"})
    assert _parse_retry_after(r) is None


# ---------------------------------------------------------------------------
# Sync transport: 5xx retry
# ---------------------------------------------------------------------------


def test_sync_transport_retries_503_then_succeeds():
    """Transport retries on 503 and returns the eventual 200."""
    transport = HTTPRetryConnectSyncTransport()
    responses = [
        httpx.Response(503),
        httpx.Response(503),
        httpx.Response(200, text="ok"),
    ]
    call_count = {"n": 0}

    def fake_super(_self, request):
        call_count["n"] += 1
        return responses.pop(0)

    with (
        patch("anicli_api._http.sleep", return_value=None),
        patch.object(httpx.HTTPTransport, "handle_request", fake_super),
    ):
        resp = transport.handle_request(_build_request())

    assert resp.status_code == 200
    assert call_count["n"] == 3  # 2 retries + 1 success


def test_sync_transport_returns_504_after_max_retries():
    """When 504 persists past MAX_5XX_RETRIES, the last 504 is returned."""
    transport = HTTPRetryConnectSyncTransport()
    call_count = {"n": 0}

    def fake_super(_self, request):
        call_count["n"] += 1
        return httpx.Response(504)

    with (
        patch("anicli_api._http.sleep", return_value=None),
        patch.object(httpx.HTTPTransport, "handle_request", fake_super),
    ):
        resp = transport.handle_request(_build_request())

    assert resp.status_code == 504
    # MAX_5XX_RETRIES retries on top of the initial attempt
    assert call_count["n"] == MAX_5XX_RETRIES + 1


def test_sync_transport_retries_500():
    """500 is retried: some upstreams (hdrezka CDN) glitch 500 intermittently."""
    transport = HTTPRetryConnectSyncTransport()
    call_count = {"n": 0}

    def fake_super(_self, request):
        call_count["n"] += 1
        return httpx.Response(500)

    with patch.object(httpx.HTTPTransport, "handle_request", fake_super):
        resp = transport.handle_request(_build_request())

    assert resp.status_code == 500
    assert call_count["n"] == MAX_5XX_RETRIES + 1


def test_sync_transport_does_not_retry_200():
    transport = HTTPRetryConnectSyncTransport()
    call_count = {"n": 0}

    def fake_super(_self, request):
        call_count["n"] += 1
        return httpx.Response(200)

    with patch.object(httpx.HTTPTransport, "handle_request", fake_super):
        resp = transport.handle_request(_build_request())

    assert resp.status_code == 200
    assert call_count["n"] == 1


def test_sync_transport_does_not_treat_generic_403_as_ddos():
    transport = HTTPRetryConnectSyncTransport()
    call_count = {"n": 0}

    def fake_super(_self, request):
        call_count["n"] += 1
        return httpx.Response(403)

    with patch.object(httpx.HTTPTransport, "handle_request", fake_super):
        resp = transport.handle_request(_build_request())

    assert resp.status_code == 403
    assert call_count["n"] == 1


def test_sync_transport_closes_response_before_retry():
    class TrackingStream(httpx.SyncByteStream):
        closed = False

        def __iter__(self):
            yield b""

        def close(self):
            self.closed = True

    stream = TrackingStream()
    responses = [httpx.Response(503, stream=stream), httpx.Response(200)]

    with (
        patch("anicli_api._http.sleep", return_value=None),
        patch.object(httpx.HTTPTransport, "handle_request", lambda _self, request: responses.pop(0)),
    ):
        HTTPRetryConnectSyncTransport().handle_request(_build_request())

    assert stream.closed


def test_sync_transport_honors_retry_after_header():
    """When Retry-After is present, that value (capped) is used as backoff."""
    transport = HTTPRetryConnectSyncTransport()
    sleep_calls: list[float] = []
    super_calls = {"n": 0}

    def fake_sleep(secs):
        sleep_calls.append(secs)

    def fake_super(_self, request):
        super_calls["n"] += 1
        if super_calls["n"] == 1:
            return httpx.Response(503, headers={"Retry-After": "7"})
        return httpx.Response(200)

    with (
        patch("anicli_api._http.sleep", fake_sleep),
        patch.object(httpx.HTTPTransport, "handle_request", fake_super),
    ):
        resp = transport.handle_request(_build_request())

    assert resp.status_code == 200
    assert sleep_calls == [7.0]


# ---------------------------------------------------------------------------
# Async transport: 5xx retry
# ---------------------------------------------------------------------------


async def test_async_transport_retries_503_then_succeeds():
    transport = HTTPRetryConnectAsyncTransport()
    responses = [
        httpx.Response(503),
        httpx.Response(503),
        httpx.Response(200, text="ok"),
    ]
    call_count = {"n": 0}

    async def fake_super(_self, request):
        call_count["n"] += 1
        return responses.pop(0)

    with (
        patch("anicli_api._http.asyncio.sleep", return_value=None),
        patch.object(httpx.AsyncHTTPTransport, "handle_async_request", fake_super),
    ):
        resp = await transport.handle_async_request(_build_request())

    assert resp.status_code == 200
    assert call_count["n"] == 3


async def test_async_transport_returns_504_after_max_retries():
    transport = HTTPRetryConnectAsyncTransport()
    call_count = {"n": 0}

    async def fake_super(_self, request):
        call_count["n"] += 1
        return httpx.Response(504)

    with (
        patch("anicli_api._http.asyncio.sleep", return_value=None),
        patch.object(httpx.AsyncHTTPTransport, "handle_async_request", fake_super),
    ):
        resp = await transport.handle_async_request(_build_request())

    assert resp.status_code == 504
    assert call_count["n"] == MAX_5XX_RETRIES + 1


async def test_async_transport_honors_retry_after_header():
    transport = HTTPRetryConnectAsyncTransport()
    sleep_calls: list[float] = []
    super_calls = {"n": 0}

    async def fake_sleep(secs):
        sleep_calls.append(secs)

    async def fake_super(_self, request):
        super_calls["n"] += 1
        if super_calls["n"] == 1:
            return httpx.Response(503, headers={"Retry-After": "4"})
        return httpx.Response(200)

    with (
        patch("anicli_api._http.asyncio.sleep", fake_sleep),
        patch.object(httpx.AsyncHTTPTransport, "handle_async_request", fake_super),
    ):
        resp = await transport.handle_async_request(_build_request())

    assert resp.status_code == 200
    assert sleep_calls == [4.0]


async def test_async_transport_closes_response_before_retry():
    class TrackingStream(httpx.AsyncByteStream):
        closed = False

        async def __aiter__(self):
            yield b""

        async def aclose(self):
            self.closed = True

    stream = TrackingStream()
    responses = [httpx.Response(503, stream=stream), httpx.Response(200)]

    async def fake_super(_self, request):
        return responses.pop(0)

    with (
        patch("anicli_api._http.asyncio.sleep", return_value=None),
        patch.object(httpx.AsyncHTTPTransport, "handle_async_request", fake_super),
    ):
        await HTTPRetryConnectAsyncTransport().handle_async_request(_build_request())

    assert stream.closed


async def test_base_clients_honor_http2_proxy_and_custom_transport():
    from anicli_api._http import BaseHTTPAsync, BaseHTTPSync

    sync = BaseHTTPSync(proxy="http://127.0.0.1:8080")
    async_ = BaseHTTPAsync(proxy="http://127.0.0.1:8080")
    custom_sync_transport = httpx.MockTransport(lambda request: httpx.Response(200))
    custom_async_transport = httpx.MockTransport(lambda request: httpx.Response(200))
    custom_sync = BaseHTTPSync(transport=custom_sync_transport)
    custom_async = BaseHTTPAsync(transport=custom_async_transport)
    try:
        sync_proxy_transport = sync._transport_for_url(httpx.URL("https://example.com"))
        async_proxy_transport = async_._transport_for_url(httpx.URL("https://example.com"))
        assert isinstance(sync_proxy_transport, HTTPRetryConnectSyncTransport)
        assert isinstance(async_proxy_transport, HTTPRetryConnectAsyncTransport)
        assert sync_proxy_transport._pool._http2 is True
        assert async_proxy_transport._pool._http2 is True
        assert custom_sync._transport is custom_sync_transport
        assert custom_async._transport is custom_async_transport
    finally:
        sync.close()
        await async_.aclose()
        custom_sync.close()
        await custom_async.aclose()


# ---------------------------------------------------------------------------
# Sanity: retryable codes are exactly the spec'd set
# ---------------------------------------------------------------------------


def test_retryable_status_codes_set():
    assert RETRYABLE_STATUS_CODES == (500, 502, 503, 504)
    assert 429 not in RETRYABLE_STATUS_CODES


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
