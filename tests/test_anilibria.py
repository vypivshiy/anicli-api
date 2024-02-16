import pytest

from anicli_api.source.anilibria import Extractor

STATUS = Extractor().http.get(Extractor().BASE_URL + "getUpdates").status_code


@pytest.fixture()
def extractor():
    return Extractor()


@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
def test_search(extractor):
    # extractor.search("луна лайка и носферату")[0].get_anime().get_episodes()[0].get_sources()[0].get_videos()
    result = extractor.search("луна лайка и носферату")
    assert result[0].title == "Луна, Лайка и Носферату"
    anime = result[0].get_anime()
    episodes = anime.get_episodes()
    assert len(episodes) == 12
    assert episodes[0].title == "Episode 1"
    sources = episodes[0].get_sources()
    assert len(sources) == 1
    videos = sources[0].get_videos()
    assert sources[0].title == "Anilibria"
    assert len(videos) == 3


@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
def test_ongoing(extractor):
    result = extractor.ongoing()
    assert len(result) > 2
