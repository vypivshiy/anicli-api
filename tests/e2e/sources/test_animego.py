from __future__ import annotations

import pytest

from anicli_api.source.animego import Extractor
from tests.integration.conftest import HttpBundle, VideoChecker

pytestmark = pytest.mark.integration

PARAMS_QUERIES = [("lain",), ("Кланнад Фильм",)]


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


def test_ongoing_pipeline(http_bundle: HttpBundle, assert_video_reachable: VideoChecker) -> None:
    ex = Extractor(**http_bundle.extractor_kwargs)
    ongs = ex.ongoing()
    # animego specific:
    # может быть совсем новый тайтл без эпизодов или источников, перебираем до первого валидного
    for ong in ongs:
        anime = ong.get_anime()
        assert anime.title
        episodes = anime.get_episodes()
        if not episodes:
            continue
        assert episodes
        sources = episodes[0].get_sources()
        if not sources:
            continue
        assert sources
        videos = sources[0].get_videos()
        assert videos
        for v in videos:
            assert_video_reachable(v)
        break
    else:
        pytest.fail("Ongoings: missing episodes or sources data")


@pytest.mark.asyncio
async def test_ongoing_pipeline_async(
    http_bundle: HttpBundle, assert_video_reachable: VideoChecker) -> None:
    ex = Extractor(**http_bundle.extractor_kwargs)
    ongs = ex.ongoing()
    # animego specific:
    # может быть совсем новый тайтл без эпизодов или источников, перебираем до первого валидного
    for ong in ongs:
        anime = await ong.a_get_anime()
        assert anime.title
        episodes = await anime.a_get_episodes()
        if not episodes:
            continue
        assert episodes
        sources = await episodes[0].a_get_sources()
        if not sources:
            continue
        assert sources
        videos = await sources[0].a_get_videos()
        assert videos
        for v in videos:
            assert_video_reachable(v)
        break
    else:
        pytest.fail("Ongoings: missing episodes or sources data")
