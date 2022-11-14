from tests import fake_extractor

Extractor = fake_extractor.Extractor


def test_extractor_search():
    result = Extractor().search("")
    assert len(result) == 1


def test_extractor_ongoing():
    result = Extractor().ongoing()
    assert len(result) == 2


def test_get_search_metadata():
    result = Extractor().search("")[0]
    assert result.dict() == {'meta': 'search_1 mock meta', 'title': 'title_1', 'url': 'search_1'}


def test_get_ongoing_metadata():
    result = Extractor().ongoing()
    assert result[0].dict() == {"url": "ongoing_1", "title": "title_1", "description": "ongoing_1 mock meta"}
    assert result[1].dict() == {"url": "ongoing_2", "title": "title_2", "description": "search_2 mock meta"}


def test_get_episodes():
    episodes = Extractor().search("")[0].get_anime().get_episodes()
    assert len(episodes) == 3
    assert episodes[0].dict()["num"] == 1
    assert episodes[1].dict()["num"] == 2
    assert episodes[2].dict()["num"] == 3


def test_get_video():
    video = Extractor().search("")[0].get_anime().get_episodes()[0].get_videos()
    assert video[0].get_source() == 'video.mp4'


def test_walk_search():
    for i, meta in enumerate(Extractor().walk_search("")):
        assert meta == Extractor.WALK_SEARCH[i]


def test_walk_ongoing():
    for i, meta in enumerate(Extractor().walk_ongoing()):
        assert meta == Extractor.WALK_ONGOING[i]


def test_anime_metadata():
    search = Extractor().search("")[0]
    for i, meta in enumerate(search):
        assert meta == Extractor.SEARCH_META[i]


def test_ongoing_metadata():
    ongoing = Extractor().ongoing()[0]
    for i, meta in enumerate(ongoing):
        assert meta == Extractor.ONGOING_META[i]


def test_anime_iterables():
    anime = Extractor().search("")[0].get_anime()
    assert [ep.dict() for ep in anime] == [ep.dict() for ep in anime.get_episodes()]
    episode = anime.get_episodes()[0]
    assert [video.dict() for video in episode] == [video.dict() for video in episode.get_videos()]


def test_collections():
    tests_coll = fake_extractor.TestCollections()
    assert tests_coll.test_search()
    assert tests_coll.test_ongoing()
    assert tests_coll.test_extract_video()
    assert tests_coll.test_extract_metadata()