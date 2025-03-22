import pytest

from anicli_api.source.yummy_anime_ru import Extractor

STATUS = Extractor().http.get(Extractor().BASE_URL + "eksperimenty-leyn").status_code


@pytest.fixture()
def extractor():
    return Extractor()


@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
def test_search(extractor):
    # extractor.search("Эксперименты Лэйн")[0].get_anime().get_episodes()[0].get_sources()[0].get_videos()
    result = extractor.search("Эксперименты Лэйн")
    assert result[0].title == "Эксперименты Лэйн"
    anime = result[0].get_anime()
    episodes = anime.get_episodes()
    assert len(episodes) == 13
    assert str(episodes[0]) == "Episode 1"
    sources = episodes[0].get_sources()
    assert len(sources) == 4
    videos = sources[0].get_videos()
    assert sources[0].title == "Субтитры"
    assert len(videos) == 3


@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
def test_ongoing(extractor):
    result = extractor.ongoing()
    assert len(result) > 2
