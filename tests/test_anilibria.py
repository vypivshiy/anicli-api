import pytest

from anicli_api.source.anilibria import Extractor

STATUS = Extractor().HTTP().get(Extractor().BASE_URL + "getUpdates").status_code


@pytest.fixture()
def extractor():
    return Extractor()


@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
def test_search(extractor):
    result = extractor.search("chainsaw")
    assert result[0].dict()['id'] == 9261
    anime = result[0].get_anime()
    episodes = anime.get_episodes()
    assert len(episodes) == 12
    sources = episodes[0].get_sources()
    assert len(sources) == 1
    videos = sources[0].get_videos()
    assert len(videos) == 3
    # videos = episodes[0].get_sources()
    # assert len(videos) == 1


@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
def test_ongoing(extractor):
    result = extractor.ongoing()
    assert len(result) > 2
