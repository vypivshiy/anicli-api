import pytest

from anicli_api.source.animego import Extractor

STATUS_ANIMEGO = Extractor().HTTP().get(Extractor().BASE_URL).status_code


@pytest.fixture()
def extractor():
    return Extractor()


@pytest.mark.skipif(STATUS_ANIMEGO != 200,
                    reason=f"RETURN CODE [{STATUS_ANIMEGO}]")
def test_search(extractor):
    result = extractor.search("lain")
    assert result[0].dict() == {'url': 'https://animego.org/anime/eksperimenty-leyn-1114', 'title': 'Эксперименты Лэйн', 'thumbnail': 'https://animego.org/media/cache/thumbs_300x420/upload/anime/images/5d1b809ecb40b061887856.jpg', 'rating': 8.5, 'name': 'Serial Experiments Lain'}
    anime = result[0].get_anime()
    assert anime.dict() == {'title': 'Эксперименты Лэйн', 'alt_titles': ['Serial Experiments Lain', 'Serial Experiments Lain', 'シリアルエクスペリメンツレイン'], 'description': 'Сильно ли связана реальность с виртуальной вселенной? Главная героиня не задумывалась об этом. довольно тихая и замкнутая особа. Она мало чем интересуется и с одноклассницами особо не общается. Держа в руках плюшевого мишку, она редко когда пользуется личным компьютером. Но однажды жизнь девушки кардинально изменилась. Вскоре на электронную почту Лэйн как и многим другим из школы приходит странное письмо от своей одноклассницы —  той самой Тисы, которая недавно совершила самоубийство. Все эти события заставили девушку покопаться в интернете для разрешения вопросов. Но старенький компьютер мало подходил для дела, поэтому она попросила купить ей современную модель. Вскоре Лэйн из разговора выясняет что в клубе Сайберия увидели двойника главной героини – «другую Лэйн». Загадки и необычные события меняют жизнь девушки. Стараясь разобраться в происходящем, она оказывается глубже в пучине вопросов, которые пока что остаются без ответа. В странницах виртуальных миров предстоит разгадать не мало тайн, начиная с пришествием, заканчивая личными неприятностями. Похоже, что девушка глубоко встряла в так называемой сети. Как будет развиваться история в дальнейшем?', 'genres': ['Безумие', 'Детектив', 'Драма', 'Психологическое', 'Сверхъестественное', 'Фантастика'], 'episodes_total': 13, 'aired': '1998-07-06 1998-09-28', 'anime_id': '1114', 'rating': 8.5, 'thumbnail': 'https://animego.org/media/cache/thumbs_250x350/upload/anime/images/5d1b809ecb40b061887856.jpg', 'episodes_available': 6, 'url': 'https://animego.org/anime/eksperimenty-leyn-1114'}
    episodes = anime.get_episodes()
    assert len(episodes) == 13
    videos = episodes[0].get_sources()
    assert len(videos) == 1


@pytest.mark.skipif(STATUS_ANIMEGO != 200,
                    reason=f"RETURN CODE [{STATUS_ANIMEGO}]")
def test_ongoing(extractor):
    result = extractor.ongoing()
    assert len(result) > 2

