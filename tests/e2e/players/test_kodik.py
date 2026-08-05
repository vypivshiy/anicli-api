from __future__ import annotations

import pytest

from anicli_api.player.kodik import Kodik
from tests.e2e.conftest import HttpBundle, VideoChecker

pytestmark = pytest.mark.integration

# TODO: add stable kodik player URL(s); format:
#   https://<sub>.<domain>/(?:serial|season|video|film)/<id>/<hash>/<quality>p
URLS: list[str] = [

]

URLS_FAILED: list[str] = [
    # deleted
    "https://kodik.info/seria/310427/09985563d891b56b1e9b01142ae11872/720p",
    # ULTRA rare kodik backend bug
    # Spotted in 'Cyberpunk: Edgerunners' ep5 Anilibria dub
    "https://kodik.info/seria/1051016/af405efc5e061f5ac344d4811de3bc16/720p"
]

_skip_no_urls = pytest.mark.skipif(not URLS, reason="no fixture URL configured for Kodik")


@pytest.mark.parametrize("url", URLS)
def test_parse(http_bundle: HttpBundle, assert_video_reachable: VideoChecker, url: str) -> None:
    player = Kodik(http=http_bundle.sync, a_http=http_bundle.async_)
    for url in URLS:
        videos = player.parse(url)
        assert videos, f"no videos parsed from {url}"
        for v in videos:
            assert_video_reachable(v)


@pytest.mark.asyncio
@pytest.mark.parametrize("url", URLS)
async def test_a_parse(http_bundle: HttpBundle, assert_video_reachable: VideoChecker, url: str) -> None:
    player = Kodik(http=http_bundle.sync, a_http=http_bundle.async_)
    for url in URLS:
        videos = await player.a_parse(url)  # type: ignore[misc]  # @url_validator wraps async in sync
        assert videos, f"no videos parsed from {url}"
        for v in videos:
            assert_video_reachable(v)
