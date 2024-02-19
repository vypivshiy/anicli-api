import pytest

from anicli_api.source.animania import Extractor

STATUS_ANIMANIA = Extractor().http.get(Extractor().BASE_URL).status_code


@pytest.fixture()
def extractor():
    return Extractor()


@pytest.mark.skipif(STATUS_ANIMANIA != 200, reason=f"RETURN CODE [{STATUS_ANIMANIA}]")
def test_search(extractor):
    result = extractor.search("Эксперименты Лэйн")
    assert result[0].title == "Эксперименты Лэйн"
    anime = result[0].get_anime()
    assert anime.title == "Эксперименты Лэйн"
    episodes = anime.get_episodes()
    assert len(episodes) == 13
    sources = episodes[0].get_sources()
    assert len(sources) == 1


@pytest.mark.asyncio
@pytest.mark.skipif(STATUS_ANIMANIA != 200, reason=f"RETURN CODE [{STATUS_ANIMANIA}]")
async def test_search(extractor):
    result = await extractor.a_search("Эксперименты Лэйн")
    assert result[0].title == "Эксперименты Лэйн"
    anime = await result[0].a_get_anime()
    assert anime.title == "Эксперименты Лэйн"
    episodes = await anime.a_get_episodes()
    assert len(episodes) == 13
    sources = await episodes[0].a_get_sources()
    assert len(sources) == 1


@pytest.mark.skipif(STATUS_ANIMANIA != 200, reason=f"RETURN CODE [{STATUS_ANIMANIA}]")
def test_ongoing(extractor):
    result = extractor.ongoing()
    assert len(result) > 2


@pytest.mark.asyncio
@pytest.mark.skipif(STATUS_ANIMANIA != 200, reason=f"RETURN CODE [{STATUS_ANIMANIA}]")
async def test_ongoing(extractor):
    result = await extractor.a_ongoing()
    assert len(result) > 2
