from time import sleep

import pytest

from anicli_api.source.animejoy import Extractor

STATUS = Extractor().HTTP().get(Extractor().BASE_URL).status_code


@pytest.fixture()
def extractor():
    return Extractor()


@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
def test_search(extractor):
    result = extractor.search("эксперименты лэйн")
    assert result[0].title == "Эксперименты Лэйн [13 из 13]"
    sleep(.3)  # rate limit requests for trying avoid cloudflare error
    anime = result[0].get_anime()
    assert anime.alt_title == "Serial Experiments Lain"
    episodes = anime.get_episodes()
    assert len(episodes) == 13
    sources = episodes[0].get_sources()
    assert len(sources) == 3


@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
def test_ongoing(extractor):
    result = extractor.ongoing()
    assert len(result) > 2
