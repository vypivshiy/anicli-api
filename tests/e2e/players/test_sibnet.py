from __future__ import annotations

import pytest

from anicli_api.player.sibnet import SibNet

pytestmark = pytest.mark.integration

URLS: list[str] = [
    # from project README, long-stable sample
    "https://video.sibnet.ru/shell.php?videoid=432356",
]

_skip_no_urls = pytest.mark.skipif(not URLS, reason="no fixture URL configured for SibNet")


@_skip_no_urls
def test_parse(http_bundle, assert_video_reachable) -> None:
    player = SibNet(http=http_bundle.sync, a_http=http_bundle.async_)
    for url in URLS:
        videos = player.parse(url)
        assert videos, f"no videos parsed from {url}"
        for v in videos:
            assert_video_reachable(v)


@_skip_no_urls
@pytest.mark.asyncio
async def test_a_parse(http_bundle, assert_video_reachable) -> None:
    player = SibNet(http=http_bundle.sync, a_http=http_bundle.async_)
    for url in URLS:
        videos = await player.a_parse(url)  # type: ignore[misc]  # @url_validator wraps async in sync
        assert videos, f"no videos parsed from {url}"
        for v in videos:
            assert_video_reachable(v)
