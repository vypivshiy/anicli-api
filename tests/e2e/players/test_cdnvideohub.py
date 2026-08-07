from __future__ import annotations

import pytest

from anicli_api.player.cdnvideohub import CdnVideoHub
from tests.e2e.conftest import HttpBundle, VideoChecker

pytestmark = pytest.mark.e2e

# TODO: add stable cdnvideohub player URL(s); format:
#   https://animego.<tld>/cdn-iframe/<id>/<title>/<x>/<y>
URLS: list[str] = [
    "https://animego.me/cdn-iframe/56854/AniLiberty/1/1"
]

@pytest.mark.parametrize("url", URLS)
def test_parse(http_bundle: HttpBundle, assert_video_reachable: VideoChecker, url: str) -> None:
    player = CdnVideoHub(http=http_bundle.sync, a_http=http_bundle.async_)
    videos = player.parse(url)
    assert videos, f"no videos parsed from {url}"
    for v in videos:
        assert_video_reachable(v)


@pytest.mark.asyncio
@pytest.mark.parametrize("url", URLS)
async def test_a_parse(http_bundle: HttpBundle, assert_video_reachable: VideoChecker, url: str) -> None:
    player = CdnVideoHub(http=http_bundle.sync, a_http=http_bundle.async_)
    videos = await player.a_parse(url)  # type: ignore[misc]  # @url_validator wraps async in sync
    assert videos, f"no videos parsed from {url}"
    for v in videos:
        assert_video_reachable(v)
