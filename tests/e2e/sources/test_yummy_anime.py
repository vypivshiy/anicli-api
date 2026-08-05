from __future__ import annotations

import pytest

from anicli_api.source.yummy_anime import Extractor
from tests.integration.conftest import HttpBundle, VideoChecker

pytestmark = pytest.mark.integration

PARAMS_QUERIES = [("lain",), ("Кланнад — Фильм",)]


def test_ongoiong_pipeline(http_bundle: HttpBundle, assert_video_reachable: VideoChecker) -> None:
    ex = Extractor(**http_bundle.extractor_kwargs)
    ongs = ex.ongoing()
    assert ongs

    anime = ongs[0].get_anime()
    assert anime.title
    episodes = anime.get_episodes()
    assert episodes

    sources = episodes[0].get_sources()
    assert sources

    videos = sources[0].get_videos()
    assert videos
    for v in videos:
        assert_video_reachable(v)


@pytest.mark.asyncio
async def test_ongoiong_pipeline_async(http_bundle: HttpBundle, assert_video_reachable: VideoChecker) -> None:
    ex = Extractor(**http_bundle.extractor_kwargs)
    ongs = await ex.a_ongoing()
    assert ongs

    anime = await ongs[0].a_get_anime()
    assert anime.title
    episodes = await anime.a_get_episodes()
    assert episodes
    
    sources = await episodes[0].a_get_sources()
    assert sources

    videos = await sources[0].a_get_videos()
    assert videos
    for v in videos:
        assert_video_reachable(v)


@pytest.mark.parametrize("query", PARAMS_QUERIES)
def test_search_pipeline(http_bundle: HttpBundle, assert_video_reachable: VideoChecker, query: str) -> None:
    ex = Extractor(**http_bundle.extractor_kwargs)
    anime = ex.search(query)[0].get_anime()
    assert anime.title

    episodes = anime.get_episodes()
    assert episodes

    sources = episodes[0].get_sources()
    assert sources

    videos = sources[0].get_videos()
    assert videos
    for v in videos:
        assert_video_reachable(v)


@pytest.mark.asyncio
@pytest.mark.parametrize("query", PARAMS_QUERIES)
async def test_search_pipeline_async(http_bundle: HttpBundle, assert_video_reachable: VideoChecker, query: str) -> None:
    ex = Extractor(**http_bundle.extractor_kwargs)
    search = (await ex.a_search(query))[0]
    anime = await search.a_get_anime()
    assert anime.title

    episodes = await anime.a_get_episodes()
    assert episodes

    sources = await episodes[0].a_get_sources()
    assert sources

    videos = await sources[0].a_get_videos()
    assert videos
    for v in videos:
        assert_video_reachable(v)