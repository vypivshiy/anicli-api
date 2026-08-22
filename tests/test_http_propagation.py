"""Verify per-call request kwargs (headers/cookies/timeout) flow from BaseSource
all the way down to player extractor's httpx client.get/post, and that the
source's pre-configured http/http_async clients are propagated to the player
extractor without mutation.

Regression for:
1. The bug where ``BaseSource.get_videos`` constructed extractors without
   forwarding ``self.http`` / ``self.http_async`` (proxy dropped for kodik /
   aniboom / cdnvideohub / etc players).
2. The race where ``ABCVideoExtractor.__init__`` mutated
   ``passed_client.headers.update(...)`` - clients shared across extractor
   instances or concurrent asyncio tasks would stomp each other's headers.
"""

from __future__ import annotations

from typing import List

import pytest

from anicli_api.base import BaseExtractor, BaseSource
from anicli_api.player.base import Video


class _CaptureExtractor:
    """Stand-in for a BaseVideoExtractor.

    Records the http clients received in ``__init__`` and the per-call kwargs
    received in ``parse`` / ``a_parse`` so the test can assert both.
    """

    received: List["_CaptureExtractor"] = []
    parse_calls: List[dict] = []
    a_parse_calls: List[dict] = []

    DEFAULT_REQUEST_CONFIG: dict = {}

    def __init__(self, http=None, a_http=None):
        self.http = http
        self.a_http = a_http
        type(self).received.append(self)

    @classmethod
    def _compare_url(cls, url: str) -> bool:  # pragma: no cover - trivial
        return url.startswith("https://player.example.com")

    def __eq__(self, other):  # type: ignore[override]
        if not isinstance(other, str):
            return NotImplemented
        return self._compare_url(other)

    def parse(self, url, *, headers=None, cookies=None, timeout=None):
        type(self).parse_calls.append({"headers": headers, "cookies": cookies, "timeout": timeout})
        return [Video(type="mp4", quality=720, url="https://player.example.com/v.mp4")]

    async def a_parse(self, url, *, headers=None, cookies=None, timeout=None):
        type(self).a_parse_calls.append({"headers": headers, "cookies": cookies, "timeout": timeout})
        return [Video(type="mp4", quality=720, url="https://player.example.com/v.mp4")]


def _make_source(http, http_async) -> BaseSource:
    return BaseSource(
        title="t",
        url="https://player.example.com/x",
        http=http,
        http_async=http_async,
    )


def _patch_decoders(monkeypatch):
    monkeypatch.setattr(BaseSource, "_all_video_extractors", property(lambda self: (_CaptureExtractor,)))
    _CaptureExtractor.received.clear()
    _CaptureExtractor.parse_calls.clear()
    _CaptureExtractor.a_parse_calls.clear()


def _patch_cdn(monkeypatch, capture_sync, capture_async):
    import anicli_api.base as base_mod

    monkeypatch.setattr(base_mod, "cdnvideohub_playlist_from_vkid", capture_sync)
    monkeypatch.setattr(base_mod, "async_cdnvideohub_playlist_from_vkid", capture_async)


# ---------------------------------------------------------------------------
# client propagation: source.http / source.http_async reach the extractor
# ---------------------------------------------------------------------------


def test_get_videos_propagates_source_http_to_extractor(monkeypatch):
    """Default dispatch path must forward source's http/http_async to the player extractor."""
    _patch_decoders(monkeypatch)
    sync_client = object()  # sentinel - identity is what we assert
    async_client = object()
    source = _make_source(sync_client, async_client)

    result = source.get_videos()

    assert len(_CaptureExtractor.received) == 1
    captured = _CaptureExtractor.received[-1]
    assert captured.http is sync_client, "sync client (with proxy) dropped on source -> player"
    assert captured.a_http is async_client, "async client (with proxy) dropped on source -> player"
    assert result, "extractor.parse result must be returned"


async def test_a_get_videos_propagates_source_http_to_extractor(monkeypatch):
    """Async dispatch path must forward source's http_async to the player extractor."""
    _patch_decoders(monkeypatch)
    sync_client = object()
    async_client = object()
    source = _make_source(sync_client, async_client)

    result = await source.a_get_videos()

    assert len(_CaptureExtractor.received) == 1
    captured = _CaptureExtractor.received[-1]
    assert captured.http is sync_client
    assert captured.a_http is async_client
    assert result


# ---------------------------------------------------------------------------
# per-call kwargs: headers/cookies/timeout flow through to parse/a_parse
# ---------------------------------------------------------------------------


def test_get_videos_propagates_per_call_kwargs(monkeypatch):
    """Per-call headers/cookies/timeout must reach extractor.parse."""
    _patch_decoders(monkeypatch)
    source = _make_source(object(), object())

    source.get_videos(
        headers={"X-Custom": "1"},
        cookies={"session": "abc"},
        timeout=12.5,
    )

    assert len(_CaptureExtractor.parse_calls) == 1
    call = _CaptureExtractor.parse_calls[0]
    assert call["headers"] == {"X-Custom": "1"}
    assert call["cookies"] == {"session": "abc"}
    assert call["timeout"] == 12.5


async def test_a_get_videos_propagates_per_call_kwargs(monkeypatch):
    """Per-call headers/cookies/timeout must reach extractor.a_parse."""
    _patch_decoders(monkeypatch)
    source = _make_source(object(), object())

    await source.a_get_videos(
        headers={"X-Custom": "async"},
        cookies={"session": "xyz"},
        timeout=7.0,
    )

    assert len(_CaptureExtractor.a_parse_calls) == 1
    call = _CaptureExtractor.a_parse_calls[0]
    assert call["headers"] == {"X-Custom": "async"}
    assert call["cookies"] == {"session": "xyz"}
    assert call["timeout"] == 7.0


def test_get_videos_no_kwargs_passes_none(monkeypatch):
    """When caller passes nothing, extractor receives None for each kwarg."""
    _patch_decoders(monkeypatch)
    source = _make_source(object(), object())

    source.get_videos()

    assert len(_CaptureExtractor.parse_calls) == 1
    call = _CaptureExtractor.parse_calls[0]
    assert call["headers"] is None
    assert call["cookies"] is None
    assert call["timeout"] is None


# ---------------------------------------------------------------------------
# cdn-videohub branch still propagates source clients
# ---------------------------------------------------------------------------


def test_get_videos_cdn_videohub_branch_uses_source_http(monkeypatch):
    from unittest.mock import MagicMock

    captured_sync = MagicMock(return_value=[Video(type="m3u8", quality=1080, url="https://x/x.m3u8")])
    captured_async = MagicMock()
    _patch_cdn(monkeypatch, captured_sync, captured_async)

    sync_client = object()
    async_client = object()
    src = BaseSource(
        title="t",
        url="https://ignored",
        cdn_videohub_vk_id="42",
        http=sync_client,
        http_async=async_client,
    )

    src.get_videos()

    captured_sync.assert_called_once()
    assert captured_sync.call_args.args[0] is sync_client, "proxy client dropped for cdn-videohub sync path"
    assert captured_sync.call_args.args[1] == "42"


async def test_a_get_videos_cdn_videohub_branch_uses_source_http(monkeypatch):
    from unittest.mock import AsyncMock, MagicMock

    captured_sync = MagicMock(return_value=[])
    captured_async = AsyncMock(return_value=[Video(type="m3u8", quality=1080, url="https://x/x.m3u8")])
    _patch_cdn(monkeypatch, captured_sync, captured_async)

    sync_client = object()
    async_client = object()
    src = BaseSource(
        title="t",
        url="https://ignored",
        cdn_videohub_vk_id="42",
        http=sync_client,
        http_async=async_client,
    )

    await src.a_get_videos()

    captured_async.assert_awaited_once()
    assert captured_async.call_args.args[0] is async_client, "proxy client dropped for cdn-videohub async path"
    assert captured_async.call_args.args[1] == "42"


def test_get_videos_cdn_videohub_branch_forwards_per_call_kwargs(monkeypatch):
    """Per-call kwargs must also reach cdn-videohub helper on the vkid path."""
    from unittest.mock import MagicMock

    captured_sync = MagicMock(return_value=[Video(type="m3u8", quality=1080, url="https://x/x.m3u8")])
    captured_async = MagicMock()
    _patch_cdn(monkeypatch, captured_sync, captured_async)

    src = BaseSource(
        title="t",
        url="https://ignored",
        cdn_videohub_vk_id="42",
        http=object(),
        http_async=object(),
    )
    src.get_videos(headers={"X": "1"}, cookies={"c": "v"}, timeout=5.0)

    captured_sync.assert_called_once()
    kw = captured_sync.call_args.kwargs
    assert kw["headers"] == {"X": "1"}
    assert kw["cookies"] == {"c": "v"}
    assert kw["timeout"] == 5.0


# ---------------------------------------------------------------------------
# ABCVideoExtractor: no client mutation, default config merge
# ---------------------------------------------------------------------------


def test_extractor_init_does_not_mutate_passed_client_headers():
    """Passing a client to ABCVideoExtractor must NOT mutate client.headers.

    Regression for the pre-refactor behavior where __init__ did
    ``http.headers.update(default_kwargs["headers"])`` on a caller-supplied
    client - this caused races when one client was shared between extractors
    or concurrent asyncio tasks.
    """
    from anicli_api.player.base import BaseVideoExtractor

    class _Ext(BaseVideoExtractor):
        URL_RULE = "https://player.example.com"
        DEFAULT_REQUEST_CONFIG = {"headers": {"referer": "https://default.example"}}
        DEFAULT_CLIENT_CONFIG = {"http2": True}

        def parse(self, url, *, headers=None, cookies=None, timeout=None):
            return []

        async def a_parse(self, url, *, headers=None, cookies=None, timeout=None):
            return []

        @classmethod
        def _compare_url(cls, url):
            return True

    from anicli_api._http import BaseHTTPSync, BaseHTTPAsync

    sync = BaseHTTPSync()
    async_ = BaseHTTPAsync()
    sync_ua_before = sync.headers.get("User-Agent")
    sync_referer_before = sync.headers.get("referer")
    async_ua_before = async_.headers.get("User-Agent")

    _Ext(http=sync, a_http=async_)

    assert sync.headers.get("User-Agent") == sync_ua_before, "sync client UA mutated by __init__"
    assert sync.headers.get("referer") == sync_referer_before, "sync client referer mutated by __init__"
    assert async_.headers.get("User-Agent") == async_ua_before, "async client UA mutated by __init__"
    # Crucially, the DEFAULT_REQUEST_CONFIG referer must NOT leak onto the client.
    assert sync.headers.get("referer") is None


def test_default_request_config_merges_per_call_headers():
    """_merge_request_kwargs merges user headers on top of DEFAULT_REQUEST_CONFIG.

    Defaults must be preserved; user headers override matching keys.
    """
    from anicli_api.player.base import BaseVideoExtractor

    class _Ext(BaseVideoExtractor):
        URL_RULE = "https://player.example"
        DEFAULT_REQUEST_CONFIG = {
            "headers": {"referer": "https://default.example", "x-foo": "default"},
            "cookies": {"default": "cookie"},
            "timeout": 3.0,
            "follow_redirects": False,
        }

        def parse(self, url, *, headers=None, cookies=None, timeout=None):
            return []

        async def a_parse(self, url, *, headers=None, cookies=None, timeout=None):
            return []

        @classmethod
        def _compare_url(cls, url):
            return True

    ext = _Ext()

    # 1) no overrides -> defaults surface
    merged = ext._merge_request_kwargs(None, None, None)
    assert merged["headers"] == {"referer": "https://default.example", "x-foo": "default"}
    assert merged["cookies"] == {"default": "cookie"}
    assert merged["timeout"] == 3.0
    assert merged["follow_redirects"] is False

    # 2) user override for x-foo, addition of x-bar; referer preserved
    merged = ext._merge_request_kwargs({"x-foo": "user", "x-bar": "added"}, None, None)
    assert merged["headers"] == {
        "referer": "https://default.example",
        "x-foo": "user",
        "x-bar": "added",
    }

    # 3) cookies + timeout flow through
    merged = ext._merge_request_kwargs(None, {"s": "1"}, 5.0)
    assert merged["cookies"] == {"default": "cookie", "s": "1"}
    assert merged["timeout"] == 5.0


async def test_default_clients_are_scoped_per_root_extractor():
    class _Ext(BaseExtractor):
        BASE_URL = "https://example.com"

        def search(self, query):
            return []

        async def a_search(self, query):
            return []

        def ongoing(self):
            return []

        async def a_ongoing(self):
            return []

    first = _Ext()
    second = _Ext()
    try:
        assert first.http is not second.http
        assert first.http_async is not second.http_async
    finally:
        await first.aclose()
        await second.aclose()


async def test_custom_httpx_clients_are_borrowed_and_not_closed():
    import httpx

    class _Ext(BaseExtractor):
        BASE_URL = "https://example.com"

        def search(self, query):
            return []

        async def a_search(self, query):
            return []

        def ongoing(self):
            return []

        async def a_ongoing(self):
            return []

    sync = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200)))
    async_ = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200)))
    ext = _Ext(http_client=sync, http_async_client=async_)

    await ext.aclose()

    assert ext.http is sync
    assert ext.http_async is async_
    assert not sync.is_closed
    assert not async_.is_closed
    sync.close()
    await async_.aclose()


async def test_owned_clients_are_closed_by_root_extractor():
    class _Ext(BaseExtractor):
        BASE_URL = "https://example.com"

        def search(self, query):
            return []

        async def a_search(self, query):
            return []

        def ongoing(self):
            return []

        async def a_ongoing(self):
            return []

    ext = _Ext()
    sync = ext.http
    async_ = ext.http_async

    await ext.aclose()

    assert sync.is_closed
    assert async_.is_closed


def test_sameband_preserves_clients_through_episode_and_source():
    from anicli_api.source.sameband import Anime

    sync = object()
    async_ = object()
    anime = Anime(
        title="t",
        thumbnail="thumb",
        description="d",
        player_url="https://sameband.studio/player",
        http=sync,
        http_async=async_,
    )

    episodes = anime._extract(
        [{"title": "Episode 1", "file": "[720p]/video/episode.m3u8", "thumbnails": ""}]
    )
    source = episodes[0].get_sources()[0]

    assert episodes[0].http is sync
    assert episodes[0].http_async is async_
    assert source.http is sync
    assert source.http_async is async_


# ---------------------------------------------------------------------------
# BaseExtractor constructible with explicit http/http_async kwargs
# ---------------------------------------------------------------------------


def test_kwargs_http_dict_carries_clients_through_extractor_chain():
    """BaseExtractor._kwargs_http is the shape consumed downstream."""
    sync_client = object()
    async_client = object()

    class _Ext(BaseExtractor):
        BASE_URL = "https://example.com"

        def search(self, query):
            raise NotImplementedError

        async def a_search(self, query):
            raise NotImplementedError

        def ongoing(self):
            raise NotImplementedError

        async def a_ongoing(self):
            raise NotImplementedError

    ext = _Ext(http_client=sync_client, http_async_client=async_client)
    src = BaseSource(
        title="t",
        url="https://player.example.com/x",
        http=ext.http,
        http_async=ext.http_async,
    )
    assert src.http is sync_client
    assert src.http_async is async_client


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
