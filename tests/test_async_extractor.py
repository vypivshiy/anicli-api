import pytest

from tests import fake_extractor

Extractor = fake_extractor.Extractor


@pytest.mark.asyncio
async def test_extractor_search():
    result = await Extractor().async_search("")
    assert len(result) == 1


@pytest.mark.asyncio
async def test_extractor_ongoing():
    result = await Extractor().async_ongoing()
    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_search_metadata():
    result = (await Extractor().async_search(""))[0]
    assert result.dict() == {'meta': 'search_1 mock meta', 'title': 'title_1', 'url': 'search_1'}


@pytest.mark.asyncio
async def test_get_ongoing_metadata():
    result = await Extractor().async_ongoing()
    assert result[0].dict() == {"url": "ongoing_1", "title": "title_1", "description": "ongoing_1 mock meta"}
    assert result[1].dict() == {"url": "ongoing_2", "title": "title_2", "description": "search_2 mock meta"}


@pytest.mark.asyncio
async def test_get_episodes():
    s = await Extractor().async_search("")
    episodes = await (await s[0].a_get_anime()).a_get_episodes()
    assert len(episodes) == 3
    assert episodes[0].dict()["num"] == 1
    assert episodes[1].dict()["num"] == 2
    assert episodes[2].dict()["num"] == 3


@pytest.mark.asyncio
async def test_get_video():
    s = await Extractor().async_search("")
    a = await s[0].a_get_anime()
    eps = await a.a_get_episodes()
    video = await eps[0].a_get_videos()
    assert (await video[0].a_get_source()) == 'video.mp4'


@pytest.mark.asyncio
async def test_async_walk_search():
    i = 0
    async for meta in Extractor().async_walk_search(""):
        assert {"search": meta.search.dict(),
                "anime": meta.anime.dict(),
                "episode": meta.episode.dict(),
                "video": meta.video.dict()} == Extractor.WALK_SEARCH[i]
        i += 1


@pytest.mark.asyncio
async def test_async_walk_ongoing():
    i = 0
    async for meta in Extractor().async_walk_ongoing():
        assert {"search": meta.search.dict(),
                "anime": meta.anime.dict(),
                "episode": meta.episode.dict(),
                "video": meta.video.dict()} == Extractor.WALK_ONGOING[i]
        i += 1


@pytest.mark.asyncio
async def test_anime_metadata():
    search = (await Extractor().async_search(""))[0]
    i = 0
    async for meta in search:
        assert {"search": meta.search.dict(),
                "anime": meta.anime.dict(),
                "episode": meta.episode.dict(),
                "video": meta.video.dict()} == Extractor.SEARCH_META[i]
        i += 1


@pytest.mark.asyncio
async def test_ongoing_metadata():
    ongoing = (await Extractor().async_ongoing())[0]
    i = 0
    async for meta in ongoing:
        assert {"search": meta.search.dict(),
                "anime": meta.anime.dict(),
                "episode": meta.episode.dict(),
                "video": meta.video.dict()} == Extractor.ONGOING_META[i]
        i += 1


@pytest.mark.asyncio
async def test_anime_iterables():
    anime = (await Extractor().async_search(""))[0]
    anime = await anime.a_get_anime()

    lst_1 = []
    async for episode in anime:
        lst_1.append(episode.dict())
    lst_2 = [ep.dict() for ep in (await anime.a_get_episodes())]
    assert lst_1 == lst_2

    episode = (await anime.a_get_episodes())[0]
    lst_3 = []
    async for video in episode:
        lst_3.append(video.dict())
    lst_4 = [video.dict() for video in (await episode.a_get_videos())]
    assert lst_3 == lst_4
