import pytest

from anicli_api.source.animejoy import Extractor

STATUS = Extractor().HTTP().get(Extractor().BASE_URL).status_code


@pytest.fixture()
def extractor():
    return Extractor()


@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
def test_search(extractor):
    result = extractor.search("эксперименты лэйн")
    assert result[0].dict() == {'alt_name': None, 'thumbnail': 'https://animejoy.ruNone', 'title': 'Эксперименты Лэйн [13 из 13]', 'url': 'https://animejoy.ru/tv-serialy/2789-eksperimenty-leyn.html'}
    anime = result[0].get_anime()
    assert anime.dict() == {'alt_titles': ['Serial Experiments Lain'], 'thumbnail': 'https://animejoy.ru/uploads/posts/2022-07/1657139510_serialexperimentslain-min.jpg', 'episodes_total': 13, 'episodes_available': 13, 'news_id': '2789', 'title': 'Эксперименты Лэйн [13 из 13]', 'description': 'Лэйн Ивакура кажется совсем обычной девочкой, которая толком не имеет даже опыта работы на компьютере, да и с людьми не особо сходится. Но после внезапного самоубийства одной из школьниц, странных слухов об этом и попыток одноклассниц вытащить её куда-нибудь, она постепенно понимает, что всё в этом мире на самом деле совсем не такое, каким представляется... Даже она сама...', 'genres': ['драма', 'детектив', 'фантастика', 'психологическое', 'сэйнэн', 'мистика'], 'aired': '\xa0c 07.07.1998 по 29.09.1998', 'url': 'https://animejoy.ru/tv-serialy/2789-eksperimenty-leyn.html'}
    episodes = anime.get_episodes()
    assert len(episodes) == 13
    sources = episodes[0].get_sources()
    assert len(sources) == 3


@pytest.mark.skipif(STATUS != 200, reason=f"RETURN CODE [{STATUS}]")
def test_ongoing(extractor):
    result = extractor.ongoing()
    assert len(result) > 2

