from __future__ import annotations

import pytest

from anicli_api.source.yummy_anime import Extractor
from tests.e2e.conftest import HttpBundle, VideoChecker

pytestmark = pytest.mark.e2e

PARAMS_QUERIES = [("lain",), ("Кланнад — Фильм",)]


def test_ongoiong_pipeline(http_bundle: HttpBundle, assert_video_reachable: VideoChecker) -> None:
    ex = Extractor(**http_bundle.extractor_kwargs)
    ongs = ex.ongoing()
    assert ongs
    worked = 0
    for ong in ongs:
        anime = ong.get_anime()
        assert anime.title
        episodes = anime.get_episodes()
        # эндпоинт неправильный выдает тайтлы которые выйдут нескоро
        # не знаю как переделывать лень чота
        if not episodes:
            continue
        assert episodes

        sources = episodes[0].get_sources()
        assert sources

        # some sources may have stale iframe url (studio listed in catalog
        # but no actual video in cdnvideohub). iterate until a working one.
        videos: list = []
        for src in sources:
            videos = src.get_videos()
            if videos:
                break
        assert videos, f"no working source for {anime.title!r}"
        for v in videos:
            assert_video_reachable(v)
        worked += 1
        break
    assert worked >= 1, "no ongoing produced working videos"


@pytest.mark.asyncio
async def test_ongoiong_pipeline_async(http_bundle: HttpBundle, assert_video_reachable: VideoChecker) -> None:
    ex = Extractor(**http_bundle.extractor_kwargs)
    ongs = await ex.a_ongoing()
    assert ongs
    worked = 0
    for ong in ongs:
        anime = await ong.a_get_anime()
        assert anime.title
        episodes = await anime.a_get_episodes()
        # эндпоинт неправильный выдает тайтлы которые выйдут нескоро
        # не знаю как переделывать лень чота
        if not episodes:
            continue
        assert episodes

        sources = await episodes[0].a_get_sources()
        assert sources

        # some sources may have stale iframe url (studio listed in catalog
        # but no actual video in cdnvideohub). iterate until a working one.
        videos: list = []
        for src in sources:
            videos = await src.a_get_videos()
            if videos:
                break
        assert videos, f"no working source for {anime.title!r}"
        for v in videos:
            assert_video_reachable(v)
        worked += 1
        break
    assert worked >= 1, "no ongoing produced working videos"


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