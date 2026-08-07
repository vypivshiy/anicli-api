from __future__ import annotations

import pytest

from anicli_api.player.aniboom import Aniboom
from tests.e2e.conftest import HttpBundle, VideoChecker

pytestmark = pytest.mark.e2e


URLS: list[str] = ["https://aniboom.one/embed/6BmMbB7MxWO?episode=1&translation=30"]


@pytest.mark.parametrize("url", URLS)
def test_parse(http_bundle: HttpBundle, assert_video_reachable: VideoChecker, url: str) -> None:
    player = Aniboom(http=http_bundle.sync, a_http=http_bundle.async_)
    for url in URLS:
        videos = player.parse(url)
        assert videos, f"no videos parsed from {url}"
        for v in videos:
            assert_video_reachable(v)


@pytest.mark.parametrize("url", URLS)
@pytest.mark.asyncio
async def test_a_parse(http_bundle: HttpBundle, assert_video_reachable: VideoChecker, url: str) -> None:
    player = Aniboom(http=http_bundle.sync, a_http=http_bundle.async_)
    for url in URLS:
        videos = await player.a_parse(url)  # type: ignore[misc]  # @url_validator wraps async in sync
        assert videos, f"no videos parsed from {url}"
        for v in videos:
            assert_video_reachable(v)
