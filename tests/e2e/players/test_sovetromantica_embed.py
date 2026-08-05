from __future__ import annotations

import pytest

from anicli_api.player.sovetromantica_embed import SovietRomanticaEmbed
from tests.integration.conftest import HttpBundle, VideoChecker

pytestmark = pytest.mark.integration

URLS: list[str] = [
    "https://sovetromantica.com/embed/episode_1475_1-subtitles"
]



@pytest.mark.parametrize("url", URLS)
def test_parse(http_bundle: HttpBundle, assert_video_reachable: VideoChecker, url: str) -> None:
    player = SovietRomanticaEmbed(http=http_bundle.sync, a_http=http_bundle.async_)
    videos = player.parse(url)
    assert videos, f"no videos parsed from {url}"
    for v in videos:
        assert_video_reachable(v)


@pytest.mark.asyncio
@pytest.mark.parametrize("url", URLS)
async def test_a_parse(http_bundle: HttpBundle, assert_video_reachable: VideoChecker, url: str) -> None:
    player = SovietRomanticaEmbed(http=http_bundle.sync, a_http=http_bundle.async_)
    videos = await player.a_parse(url)  # type: ignore[misc]  # @url_validator wraps async in sync
    assert videos, f"no videos parsed from {url}"
    for v in videos:
        assert_video_reachable(v)
