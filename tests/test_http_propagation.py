"""Verify pre-configured HTTP clients (carrying proxy / socks5 settings) propagate
from BaseExtractor all the way down to the player extractor when BaseSource.get_videos
runs the default extractor-dispatch path.

Regression for the bug where ``BaseSource.get_videos`` constructed extractors without
forwarding ``self.http`` / ``self.http_async``, so any proxy configured on the source
was silently dropped for kodik / aniboom / cdnvideohub / etc. players.
"""
from __future__ import annotations

from typing import List
from unittest.mock import AsyncMock, MagicMock

import pytest

from anicli_api.base import BaseExtractor, BaseSource
from anicli_api.player.base import Video


PROXY_URL = "socks5://user:pass@127.0.0.1:1080"


class _CaptureExtractor:
    """Minimal stand-in for a BaseVideoExtractor used by BaseSource.get_videos.

    Records the http clients received in ``__init__`` so the test can assert identity
    with the source's own clients.
    """

    # captured across all instances for assertions
    received: List["_CaptureExtractor"] = []

    def __init__(self, http=None, a_http=None, **kwargs):
        self.http = http
        self.a_http = a_http
        self.kwargs = kwargs
        type(self).received.append(self)

    def _compare_url(self, url: str) -> bool:  # pragma: no cover - trivial
        return url.startswith("https://player.example.com")

    def __eq__(self, other):  # type: ignore[override]
        if not isinstance(other, str):
            return NotImplemented
        return self._compare_url(other)

    def parse(self, url: str, **kwargs) -> list[Video]:
        return [Video(type="mp4", quality=720, url="https://player.example.com/v.mp4")]

    async def a_parse(self, url: str, **kwargs) -> list[Video]:
        return [Video(type="mp4", quality=720, url="https://player.example.com/v.mp4")]


def _make_source(http, http_async) -> BaseSource:
    """Build a minimal BaseSource instance with proxy-carrying clients."""
    return BaseSource(
        title="t",
        url="https://player.example.com/x",
        http=http,
        http_async=http_async,
    )


def _patch_decoders(monkeypatch):
    """Force BaseSource to dispatch to our capture extractor."""
    monkeypatch.setattr(
        BaseSource, "_all_video_extractors", property(lambda self: (_CaptureExtractor,))
    )
    _CaptureExtractor.received.clear()


def _patch_cdn(monkeypatch, capture_sync, capture_async):
    """Stub the module-level cdnvideohub helpers used by the ``cdn_videohub_vk_id`` branch."""
    import anicli_api.base as base_mod

    monkeypatch.setattr(base_mod, "cdnvideohub_playlist_from_vkid", capture_sync)
    monkeypatch.setattr(base_mod, "async_cdnvideohub_playlist_from_vkid", capture_async)


def test_get_videos_propagates_source_http_to_extractor(monkeypatch):
    """Default dispatch path must forward source's http/http_async to the player extractor."""
    _patch_decoders(monkeypatch)
    sync_client = MagicMock(name="sync_proxy_client")
    async_client = MagicMock(name="async_proxy_client")
    source = _make_source(sync_client, async_client)

    result = source.get_videos()

    # BaseSource.get_videos instantiates the extractor twice:
    #   1) bare `extractor()` for url-equality check, 2) `extractor(**kwargs)` for parse.
    # The last instance carries the propagated clients.
    assert len(_CaptureExtractor.received) == 2
    captured = _CaptureExtractor.received[-1]
    assert captured.http is sync_client, "sync client (with proxy) dropped on source -> player"
    assert captured.a_http is async_client, "async client (with proxy) dropped on source -> player"
    assert result, "extractor.parse result must be returned"


async def test_a_get_videos_propagates_source_http_to_extractor(monkeypatch):
    """Async dispatch path must forward source's http_async to the player extractor."""
    _patch_decoders(monkeypatch)
    sync_client = MagicMock(name="sync_proxy_client")
    async_client = MagicMock(name="async_proxy_client")
    source = _make_source(sync_client, async_client)

    result = await source.a_get_videos()

    assert len(_CaptureExtractor.received) == 2
    captured = _CaptureExtractor.received[-1]
    assert captured.http is sync_client
    assert captured.a_http is async_client
    assert result


def test_get_videos_explicit_kwargs_override_source_clients(monkeypatch):
    """Caller-provided http/a_http via httpx_kwargs must win over source's defaults."""
    _patch_decoders(monkeypatch)
    source = _make_source(MagicMock(), MagicMock())
    override_sync = MagicMock(name="override_sync")
    override_async = MagicMock(name="override_async")

    source.get_videos(http=override_sync, a_http=override_async)

    assert len(_CaptureExtractor.received) == 2
    captured = _CaptureExtractor.received[-1]
    assert captured.http is override_sync
    assert captured.a_http is override_async


def test_get_videos_cdn_videohub_branch_uses_source_http(monkeypatch):
    """cdn_videohub_vk_id path must pass source's http directly to the helper."""
    captured_sync = MagicMock(return_value=[Video(type="m3u8", quality=1080, url="https://x/x.m3u8")])
    captured_async = AsyncMock(
        return_value=[Video(type="m3u8", quality=1080, url="https://x/x.m3u8")]
    )
    _patch_cdn(monkeypatch, captured_sync, captured_async)

    sync_client = MagicMock(name="sync_proxy_client")
    async_client = MagicMock(name="async_proxy_client")
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
    # cdnvideohub_playlist_from_vkid(http, vkid) — positional args
    assert captured_sync.call_args.args[1] == "42"


async def test_a_get_videos_cdn_videohub_branch_uses_source_http(monkeypatch):
    captured_sync = MagicMock(return_value=[])
    captured_async = AsyncMock(return_value=[Video(type="m3u8", quality=1080, url="https://x/x.m3u8")])
    _patch_cdn(monkeypatch, captured_sync, captured_async)

    sync_client = MagicMock(name="sync_proxy_client")
    async_client = MagicMock(name="async_proxy_client")
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


def test_kwargs_http_dict_carries_clients_through_extractor_chain():
    """BaseExtractor._kwargs_http is the shape consumed by BaseVideoExtractor.__init__ after the fix."""
    sync_client = MagicMock(name="sync_proxy_client")
    async_client = MagicMock(name="async_proxy_client")

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
    # Source must be constructible with explicit http/http_async kwargs
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
