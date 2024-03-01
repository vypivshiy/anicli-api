import httpx
import pytest

from anicli_api.source.sameband import Extractor

STATUS = Extractor().http.get(Extractor().BASE_URL).status_code


@pytest.fixture()
def extractor():
    return Extractor()


@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
def test_search(extractor):
    result = extractor.search("Киберпанк: Бегущие по краю")
    assert result[0].title == "Киберпанк: Бегущие по краю"
    anime = result[0].get_anime()
    assert anime.title == "Киберпанк: Бегущие по краю"
    episodes = anime.get_episodes()
    assert len(episodes) == 10
    sources = episodes[0].get_sources()
    assert len(sources) == 1
    assert len(sources[0].get_videos()) == 3


@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
def test_video_status_code(extractor):
    video = \
        extractor.search("Киберпанк: Бегущие по краю")[0].get_anime().get_episodes()[0].get_sources()[0].get_videos()[0]
    resp = httpx.head(video.url, headers=video.headers)
    assert resp.is_success or resp.is_redirect


@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
def test_ongoing(extractor):
    result = extractor.ongoing()
    assert len(result) > 2


@pytest.mark.asyncio
@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
async def test_search(extractor):
    result = await extractor.a_search("Киберпанк: Бегущие по краю")
    assert result[0].title == "Киберпанк: Бегущие по краю"
    anime = await result[0].a_get_anime()
    assert anime.title == "Киберпанк: Бегущие по краю"
    episodes = await anime.a_get_episodes()
    assert len(episodes) == 10
    sources = await episodes[0].a_get_sources()
    assert len(sources) == 1
    assert len((await sources[0].a_get_videos())) == 3


@pytest.mark.asyncio
@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
async def test_ongoing(extractor):
    result = await extractor.a_ongoing()
    assert len(result) > 2
