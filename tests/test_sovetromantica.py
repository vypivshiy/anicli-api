import pytest

from anicli_api.source.sovetromantica import Extractor

STATUS = Extractor().HTTP().get(Extractor().BASE_URL).status_code


@pytest.fixture()
def extractor():
    return Extractor()


@pytest.mark.skipif(STATUS != 200,
                    reason=f"RETURN CODE [{STATUS}]")
def test_search(extractor):
    result = extractor.search("великая")
    # Великая небесная стена
    assert result[0].dict() == {'thumbnail': 'https://sovetromantica.com/assets/images/1px.png', 'title': 'Великая небесная стена', 'url': 'https://sovetromantica.com/anime/1416-tengoku-daimakyou'}
    anime = result[0].get_anime()
    assert anime.dict() == {'aired': 2023, 'alt_titles': ['Tengoku Daimakyou '], 'description': None, 'episodes_available': None, 'episodes_total': 13, 'genres': ['Приключения', 'Фантастика'], 'thumbnail': '/assets/images/1px.png', 'title': ' Великая небесная стена'}
    episodes = anime.get_episodes()
    assert len(episodes) == 10
    videos = episodes[0].get_sources()
    assert len(videos) == 1


def test_empty_search(extractor):
    result = extractor.search('Система «спаси-себя-сам» для главного злодея')
    # Система «спаси-себя-сам» для главного злодея 2 / Chuan Shu Zijiu Zhinan: Xian Meng Pian
    anime = result[2].get_anime()
    episodes = anime.get_episodes()
    assert len(episodes) == 0

@pytest.mark.skipif(STATUS != 200,
                    reason=f"RETURN CODE [{STATUS}]")
def test_ongoing(extractor):
    result = extractor.ongoing()
    assert len(result) > 2

