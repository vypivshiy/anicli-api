import pytest

from anicli_api.source.animevost import Extractor

STATUS = Extractor().http.get(Extractor().BASE_URL + "last").status_code


@pytest.fixture()
def extractor():
    return Extractor()


@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
def test_search(extractor):
    result = extractor.search("chainsaw")
    assert result[0]._id == 2872  # META ID
    anime = result[0].get_anime()
    assert anime.episodes_total == 12
    episodes = anime.get_episodes()
    assert len(episodes) == 12
    sources = episodes[0].get_sources()
    assert len(sources) == 1


@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
def test_ongoing(extractor):
    result = extractor.ongoing()
    assert len(result) > 2


@pytest.mark.asyncio(scope="session")
@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
async def test_search(extractor):
    result = await extractor.a_search("chainsaw")
    assert result[0]._id == 2872  # META ID
    anime = await result[0].a_get_anime()
    assert anime.episodes_total == 12
    episodes = await anime.a_get_episodes()
    assert len(episodes) == 12
    sources = await episodes[0].a_get_sources()
    assert len(sources) == 1


@pytest.mark.asyncio(scope="session")
@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
async def test_ongoing(extractor):
    result = await extractor.a_ongoing()
    assert len(result) > 2
