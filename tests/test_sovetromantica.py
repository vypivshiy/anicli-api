import pytest

from anicli_api.source.sovetromantica import Extractor

STATUS = Extractor().http.get(Extractor().BASE_URL).status_code


@pytest.fixture()
def extractor():
    return Extractor()


@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
def test_search(extractor):
    result = extractor.search("великая")
    # Великая небесная стена
    # strip issue
    assert "Великая небесная стена" in result[0].title
    anime = result[0].get_anime()
    assert "Великая небесная стена" in anime.title
    episodes = anime.get_episodes()
    assert len(episodes) == 10
    videos = episodes[0].get_sources()
    assert len(videos) == 1


def test_empty_search(extractor):
    result = extractor.search("маленькая")
    # Маленькая сэмпай с моей работы
    anime = result[0].get_anime()
    episodes = anime.get_episodes()
    assert len(episodes) == 0


@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
def test_ongoing(extractor):
    result = extractor.ongoing()
    assert len(result) > 2
