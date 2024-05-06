import httpx
import pytest

from anicli_api.source.jutsu import Extractor

STATUS_JUTSU = Extractor().http.get(Extractor().BASE_URL).status_code


@pytest.fixture()
def extractor():
    return Extractor()


@pytest.mark.skipif(STATUS_JUTSU != 200, reason=f"RETURN CODE [{STATUS_JUTSU}]")
def test_search(extractor):
    result = extractor.search("lain")
    assert result[0].title == "Эксперименты Лэйн"
    anime = result[0].get_anime()
    assert anime.title == "Эксперименты Лэйн"
    episodes = anime.get_episodes()
    assert len(episodes) == 13
    sources = episodes[0].get_sources()
    assert len(sources) == 1


@pytest.mark.skipif(STATUS_JUTSU != 200, reason=f"RETURN CODE [{STATUS_JUTSU}]")
def test_video_status_code(extractor):
    result = extractor.search("lain")
    assert result[0].title == "Эксперименты Лэйн"
    anime = result[0].get_anime()
    assert anime.title == "Эксперименты Лэйн"
    episodes = anime.get_episodes()
    assert len(episodes) == 13
    sources = episodes[0].get_sources()
    video = sources[0].get_videos()[0]
    resp = httpx.head(video.url, headers=video.headers)
    assert resp.is_success or resp.is_redirect


@pytest.mark.skipif(STATUS_JUTSU != 200, reason=f"RETURN CODE [{STATUS_JUTSU}]")
def test_ongoing(extractor):
    result = extractor.ongoing()
    assert len(result) > 2


@pytest.mark.asyncio(scope="session")
@pytest.mark.skipif(STATUS_JUTSU != 200, reason=f"RETURN CODE [{STATUS_JUTSU}]")
async def test_search(extractor):
    result = await extractor.a_search("lain")
    assert result[0].title == "Эксперименты Лэйн"
    anime = await result[0].a_get_anime()
    assert anime.title == "Эксперименты Лэйн"
    episodes = await anime.a_get_episodes()
    assert len(episodes) == 13
    sources = await episodes[0].a_get_sources()
    assert len(sources) == 1


@pytest.mark.asyncio(scope="session")
@pytest.mark.skipif(STATUS_JUTSU != 200, reason=f"RETURN CODE [{STATUS_JUTSU}]")
async def test_ongoing(extractor):
    result = await extractor.a_ongoing()
    assert len(result) > 2
