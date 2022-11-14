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
