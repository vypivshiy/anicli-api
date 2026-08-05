from __future__ import annotations

import pytest

from anicli_api.player.aksor import Aksor
from tests.integration.conftest import HttpBundle, VideoChecker

pytestmark = pytest.mark.integration

# TODO: add stable aksor player URL(s)
URLS: list[str] = ["https://player.aksor.tv/video/be348c0423c77acd06f24bcbee51c5fc"]

_skip_no_urls = pytest.mark.skipif(not URLS, reason="no fixture URL configured for Aksor")


@pytest.mark.parametrize("url", URLS)
def test_parse(http_bundle: HttpBundle, assert_video_reachable: VideoChecker, url: str) -> None:
    player = Aksor(http=http_bundle.sync, a_http=http_bundle.async_)
    videos = player.parse(url)
    assert videos, f"no videos parsed from {url}"
    for v in videos:
        assert_video_reachable(v)


@pytest.mark.asyncio
@pytest.mark.parametrize("url", URLS)
async def test_a_parse(http_bundle: HttpBundle, assert_video_reachable: VideoChecker, url: str) -> None:
    player = Aksor(http=http_bundle.sync, a_http=http_bundle.async_)
    videos = await player.a_parse(url)  # type: ignore[misc]  # @url_validator wraps async in sync
    assert videos, f"no videos parsed from {url}"
    for v in videos:
        assert_video_reachable(v)
