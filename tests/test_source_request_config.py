from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from anicli_api.source.animevost import Source as AnimeVostSource
from anicli_api.source.hdrezka import Source as HdrezkaSource


def test_animevost_source_forwards_request_config():
    sync = Mock()
    sync.head.return_value.is_success = False
    source = AnimeVostSource(
        title="t",
        url="https://animevost.example",
        hd="https://cdn.example/hd.mp4",
        std="https://cdn.example/std.mp4",
        http=sync,
        http_async=Mock(),
    )

    source.get_videos(headers={"X-Test": "1"}, cookies={"session": "abc"}, timeout=7.0)

    sync.head.assert_called_once_with(
        "https://cdn.example/hd.mp4",
        follow_redirects=True,
        headers={"X-Test": "1"},
        cookies={"session": "abc"},
        timeout=7.0,
    )


async def test_animevost_async_source_forwards_request_config():
    async_client = AsyncMock()
    async_client.head.return_value.is_success = False
    source = AnimeVostSource(
        title="t",
        url="https://animevost.example",
        hd="https://cdn.example/hd.mp4",
        std="https://cdn.example/std.mp4",
        http=Mock(),
        http_async=async_client,
    )

    await source.a_get_videos(headers={"X-Test": "1"}, cookies={"session": "abc"}, timeout=7.0)

    async_client.head.assert_awaited_once_with(
        "https://cdn.example/hd.mp4",
        follow_redirects=True,
        headers={"X-Test": "1"},
        cookies={"session": "abc"},
        timeout=7.0,
    )


def test_hdrezka_source_forwards_request_config():
    source = HdrezkaSource(
        title="t",
        url="https://hdrezka.example",
        api_payload={"id": "1", "translator_id": "2", "season": "1", "episode": "1", "favs": "0"},
        http=Mock(),
        http_async=Mock(),
    )

    with patch(
        "anicli_api.source.hdrezka.HdrezkaCdnSeriesAPI.get_stream",
        return_value=SimpleNamespace(is_ok=False),
    ) as get_stream:
        source.get_videos(headers={"X-Test": "1"}, cookies={"session": "abc"}, timeout=7.0)

    assert get_stream.call_args.kwargs["headers"] == {"X-Test": "1"}
    assert get_stream.call_args.kwargs["cookies"] == {"session": "abc"}
    assert get_stream.call_args.kwargs["timeout"] == 7.0


async def test_hdrezka_async_source_forwards_request_config():
    source = HdrezkaSource(
        title="t",
        url="https://hdrezka.example",
        api_payload={"id": "1", "translator_id": "2", "season": "1", "episode": "1", "favs": "0"},
        http=Mock(),
        http_async=Mock(),
    )

    get_stream = AsyncMock(return_value=SimpleNamespace(is_ok=False))
    with patch("anicli_api.source.hdrezka.HdrezkaCdnSeriesAPI.async_get_stream", get_stream):
        await source.a_get_videos(headers={"X-Test": "1"}, cookies={"session": "abc"}, timeout=7.0)

    assert get_stream.call_args.kwargs["headers"] == {"X-Test": "1"}
    assert get_stream.call_args.kwargs["cookies"] == {"session": "abc"}
    assert get_stream.call_args.kwargs["timeout"] == 7.0
