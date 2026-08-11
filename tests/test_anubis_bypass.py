"""Tests for Anubis bot-protect passive bypass in HTTPRetryConnect{Sync,Async}Transport.

Covers:
- Challenge detection (status 200 + content-type html + both markers)
- UA stripping on retry
- Per-netloc cache with TTL fast-path
- Gates: content-type, status code, markers
- No infinite loop when bypass fails
- 5xx retry + anubis interaction
- Sync / async parity
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest

from anicli_api import _http
from anicli_api._http import (
    ANUBIS_CHALLENGE_MARKERS,
    HTTPRetryConnectAsyncTransport,
    HTTPRetryConnectSyncTransport,
    _anubis_bypass_hosts,
    _is_anubis_challenge,
    apply_anubis_bypass,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def clean_anubis_cache():
    """Reset module-level Anubis cache + TTL clock before each test."""
    _anubis_bypass_hosts.clear()
    yield
    _anubis_bypass_hosts.clear()


_ANUBIS_BODY = (
    "<html><head></style>"
    '<script id="anubis_version" type="application/json">"v1.27.1"</script>'
    '<script id="anubis_challenge" type="application/json">{"challenge":{}}</script>'
    "</head><body>challenge</body></html>"
)
_OK_BODY = "<html><body>real content</body></html>"


def _anubis_resp() -> httpx.Response:
    return httpx.Response(
        200,
        headers={"content-type": "text/html; charset=utf-8"},
        text=_ANUBIS_BODY,
    )


def _ok_resp() -> httpx.Response:
    return httpx.Response(
        200,
        headers={"content-type": "text/html; charset=utf-8"},
        text=_OK_BODY,
    )


def _build_request(url: str = "https://anubis.example.com/") -> httpx.Request:
    req = httpx.Request("GET", url)
    req.headers["User-Agent"] = "Mozilla/5.0 (Linux; Android 10.0) AppleWebKit/537.36 Chrome/114.0 Mobile"
    return req


# ---------------------------------------------------------------------------
# Pure helper unit tests
# ---------------------------------------------------------------------------


def test_is_anubis_challenge_positive():
    assert _is_anubis_challenge(_anubis_resp()) is True


def test_is_anubis_challenge_wrong_status():
    r = httpx.Response(403, headers={"content-type": "text/html"}, text=_ANUBIS_BODY)
    assert _is_anubis_challenge(r) is False


def test_is_anubis_challenge_wrong_content_type():
    r = httpx.Response(200, headers={"content-type": "application/json"}, text=_ANUBIS_BODY)
    assert _is_anubis_challenge(r) is False


def test_is_anubis_challenge_missing_markers():
    r = httpx.Response(200, headers={"content-type": "text/html"}, text=_OK_BODY)
    assert _is_anubis_challenge(r) is False


def test_is_anubis_challenge_only_one_marker():
    body = '<script id="anubis_version" type="application/json">"v"</script>'
    r = httpx.Response(200, headers={"content-type": "text/html"}, text=body)
    assert _is_anubis_challenge(r) is False


def test_is_anubis_challenge_missing_content_type_header():
    """No content-type at all -> not detected."""
    r = httpx.Response(200, text=_ANUBIS_BODY)
    assert _is_anubis_challenge(r) is False


def test_apply_anubis_bypass_strips_mozilla():
    req = _build_request()
    original = req.headers["User-Agent"]
    apply_anubis_bypass(req)
    assert "Mozilla" not in req.headers["User-Agent"]
    # Substring removed, rest preserved
    assert req.headers["User-Agent"] == original.replace("Mozilla", "")


def test_apply_anubis_bypass_idempotent_when_no_mozilla():
    req = httpx.Request("GET", "https://x.com/")
    req.headers["User-Agent"] = "curl/8.0"
    apply_anubis_bypass(req)
    assert req.headers["User-Agent"] == "curl/8.0"


def test_markers_public_constant_two_entries():
    assert isinstance(ANUBIS_CHALLENGE_MARKERS, tuple)
    assert len(ANUBIS_CHALLENGE_MARKERS) == 2
    assert 'id="anubis_version"' in ANUBIS_CHALLENGE_MARKERS
    assert 'id="anubis_challenge"' in ANUBIS_CHALLENGE_MARKERS


# ---------------------------------------------------------------------------
# Sync transport: detection + retry
# ---------------------------------------------------------------------------


def test_sync_detects_challenge_and_retries_with_stripped_ua(clean_anubis_cache):
    """First response is Anubis challenge -> transport strips UA + retries -> 200."""
    transport = HTTPRetryConnectSyncTransport()
    seen_uas: list[str] = []

    def fake_super(_self, request):
        # Snapshot UA string BEFORE any mutation can occur between iterations
        seen_uas.append(request.headers["User-Agent"])
        if len(seen_uas) == 1:
            return _anubis_resp()
        assert "Mozilla" not in request.headers["User-Agent"], "UA not stripped before retry"
        return _ok_resp()

    with patch.object(httpx.HTTPTransport, "handle_request", fake_super):
        resp = transport.handle_request(_build_request())

    assert resp.status_code == 200
    assert resp.text == _OK_BODY
    assert len(seen_uas) == 2
    assert "Mozilla" in seen_uas[0]
    assert "Mozilla" not in seen_uas[1]


def test_sync_caches_netloc_after_detection(clean_anubis_cache):
    """After first detection, netloc is cached for fast-path."""
    transport = HTTPRetryConnectSyncTransport()
    call_count = {"n": 0}

    def fake_super(_self, request):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _anubis_resp()
        return _ok_resp()

    with patch.object(httpx.HTTPTransport, "handle_request", fake_super):
        transport.handle_request(_build_request())

    assert "anubis.example.com" in _anubis_bypass_hosts


def test_sync_cache_fast_path_strips_ua_before_first_request(clean_anubis_cache):
    """Pre-populated cache: UA is stripped BEFORE sending (single super() call)."""
    _anubis_bypass_hosts["anubis.example.com"] = _http.monotonic()
    transport = HTTPRetryConnectSyncTransport()
    seen_uas: list[str] = []

    def fake_super(_self, request):
        seen_uas.append(request.headers["User-Agent"])
        return _ok_resp()

    with patch.object(httpx.HTTPTransport, "handle_request", fake_super):
        resp = transport.handle_request(_build_request())

    assert resp.status_code == 200
    assert len(seen_uas) == 1, "cached host should not trigger challenge round-trip"
    assert "Mozilla" not in seen_uas[0]


def test_sync_different_netloc_not_affected_by_cache(clean_anubis_cache):
    """Cache applies per-netloc; other hosts get no UA stripping."""
    _anubis_bypass_hosts["cached.example.com"] = _http.monotonic()
    transport = HTTPRetryConnectSyncTransport()
    seen_uas: list[str] = []

    def fake_super(_self, request):
        seen_uas.append(request.headers["User-Agent"])
        return _ok_resp()

    with patch.object(httpx.HTTPTransport, "handle_request", fake_super):
        transport.handle_request(_build_request(url="https://other.example.com/"))

    assert len(seen_uas) == 1
    assert "Mozilla" in seen_uas[0], "different netloc should keep original UA"


def test_sync_no_infinite_loop_when_bypass_also_challenged(clean_anubis_cache):
    """If bypassed retry returns another challenge, transport returns it (1 retry max)."""
    transport = HTTPRetryConnectSyncTransport()
    call_count = {"n": 0}

    def fake_super(_self, request):
        call_count["n"] += 1
        return _anubis_resp()

    with patch.object(httpx.HTTPTransport, "handle_request", fake_super):
        resp = transport.handle_request(_build_request())

    assert resp.status_code == 200
    assert resp.text == _ANUBIS_BODY
    assert call_count["n"] == 2, "exactly one bypass retry, then return"


def test_sync_5xx_retried_before_anubis_check(clean_anubis_cache):
    """503 -> Anubis challenge -> 200 sequence. Both retry mechanisms cooperate."""
    transport = HTTPRetryConnectSyncTransport()
    responses = [
        httpx.Response(503),
        _anubis_resp(),
        _ok_resp(),
    ]
    seen_uas: list[str] = []

    def fake_super(_self, request):
        seen_uas.append(request.headers["User-Agent"])
        return responses.pop(0)

    with (
        patch("anicli_api._http.sleep", return_value=None),
        patch.object(httpx.HTTPTransport, "handle_request", fake_super),
    ):
        resp = transport.handle_request(_build_request())

    assert resp.status_code == 200
    assert len(seen_uas) == 3
    # 1st: original UA (503 response)
    assert "Mozilla" in seen_uas[0]
    # 2nd: still original UA (anubis detected, bypass applied AFTER this call)
    assert "Mozilla" in seen_uas[1]
    # 3rd: stripped UA (bypass applied after 2nd call returned challenge)
    assert "Mozilla" not in seen_uas[2]


def test_sync_ttl_expiration_causes_redetection(clean_anubis_cache):
    """After TTL expires, cache entry is purged and detection reruns."""
    # Fake clock: cache entry set at t=0, current t=7200 (> TTL 3600).
    fake_now = [7200.0]

    def fake_monotonic():
        return fake_now[0]

    with patch.object(_http, "monotonic", fake_monotonic):
        _anubis_bypass_hosts["anubis.example.com"] = 0.0

        transport = HTTPRetryConnectSyncTransport()
        seen_uas: list[str] = []

        def fake_super(_self, request):
            seen_uas.append(request.headers["User-Agent"])
            if len(seen_uas) == 1:
                # UA should still have Mozilla (TTL expired, fast-path skipped)
                assert "Mozilla" in request.headers["User-Agent"]
                return _anubis_resp()
            return _ok_resp()

        with patch.object(httpx.HTTPTransport, "handle_request", fake_super):
            resp = transport.handle_request(_build_request())

    assert resp.status_code == 200
    assert len(seen_uas) == 2


def test_sync_ttl_within_window_uses_fast_path(clean_anubis_cache):
    """Within TTL window, fast-path applies (no challenge round-trip)."""
    # Fake clock at t=1100; cache entry set at t=1000 (100s ago, < 3600 TTL).
    fake_now = [1100.0]

    def fake_monotonic():
        return fake_now[0]

    with patch.object(_http, "monotonic", fake_monotonic):
        _anubis_bypass_hosts["anubis.example.com"] = 1000.0

        transport = HTTPRetryConnectSyncTransport()
        super_calls: list[str] = []

        def fake_super(_self, request):
            super_calls.append(request.headers["User-Agent"])
            return _ok_resp()

        with patch.object(httpx.HTTPTransport, "handle_request", fake_super):
            transport.handle_request(_build_request())

    assert len(super_calls) == 1
    assert "Mozilla" not in super_calls[0]


# ---------------------------------------------------------------------------
# Async transport: mirror of sync
# ---------------------------------------------------------------------------


async def test_async_detects_challenge_and_retries_with_stripped_ua(clean_anubis_cache):
    transport = HTTPRetryConnectAsyncTransport()
    seen_uas: list[str] = []

    async def fake_super(_self, request):
        seen_uas.append(request.headers["User-Agent"])
        if len(seen_uas) == 1:
            return _anubis_resp()
        assert "Mozilla" not in request.headers["User-Agent"]
        return _ok_resp()

    with patch.object(httpx.AsyncHTTPTransport, "handle_async_request", fake_super):
        resp = await transport.handle_async_request(_build_request())

    assert resp.status_code == 200
    assert len(seen_uas) == 2
    assert "Mozilla" in seen_uas[0]
    assert "Mozilla" not in seen_uas[1]


async def test_async_caches_netloc_after_detection(clean_anubis_cache):
    transport = HTTPRetryConnectAsyncTransport()
    call_count = {"n": 0}

    async def fake_super(_self, request):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _anubis_resp()
        return _ok_resp()

    with patch.object(httpx.AsyncHTTPTransport, "handle_async_request", fake_super):
        await transport.handle_async_request(_build_request())

    assert "anubis.example.com" in _anubis_bypass_hosts


async def test_async_cache_fast_path_strips_ua_before_first_request(clean_anubis_cache):
    _anubis_bypass_hosts["anubis.example.com"] = _http.monotonic()
    transport = HTTPRetryConnectAsyncTransport()
    seen_uas: list[str] = []

    async def fake_super(_self, request):
        seen_uas.append(request.headers["User-Agent"])
        return _ok_resp()

    with patch.object(httpx.AsyncHTTPTransport, "handle_async_request", fake_super):
        resp = await transport.handle_async_request(_build_request())

    assert resp.status_code == 200
    assert len(seen_uas) == 1
    assert "Mozilla" not in seen_uas[0]


async def test_async_no_infinite_loop_when_bypass_also_challenged(clean_anubis_cache):
    transport = HTTPRetryConnectAsyncTransport()
    call_count = {"n": 0}

    async def fake_super(_self, request):
        call_count["n"] += 1
        return _anubis_resp()

    with patch.object(httpx.AsyncHTTPTransport, "handle_async_request", fake_super):
        resp = await transport.handle_async_request(_build_request())

    assert resp.status_code == 200
    assert call_count["n"] == 2


async def test_async_5xx_retried_before_anubis_check(clean_anubis_cache):
    transport = HTTPRetryConnectAsyncTransport()
    responses = [
        httpx.Response(503),
        _anubis_resp(),
        _ok_resp(),
    ]
    seen_uas: list[str] = []

    async def fake_super(_self, request):
        seen_uas.append(request.headers["User-Agent"])
        return responses.pop(0)

    with (
        patch("anicli_api._http.asyncio.sleep", return_value=None),
        patch.object(httpx.AsyncHTTPTransport, "handle_async_request", fake_super),
    ):
        resp = await transport.handle_async_request(_build_request())

    assert resp.status_code == 200
    assert len(seen_uas) == 3
    assert "Mozilla" in seen_uas[0]
    assert "Mozilla" in seen_uas[1]
    assert "Mozilla" not in seen_uas[2]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
