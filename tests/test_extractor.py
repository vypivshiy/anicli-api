from anicli_api.base import BaseModel, BaseVideo
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
    assert result.dict() == {"meta": "search_1 mock meta", "title": "title_1", "url": "search_1"}


def test_get_ongoing_metadata():
    result = Extractor().ongoing()
    assert result[0].dict() == {
        "url": "ongoing_1",
        "title": "title_1",
        "description": "ongoing_1 mock meta",
    }
    assert result[1].dict() == {
        "url": "ongoing_2",
        "title": "title_2",
        "description": "search_2 mock meta",
    }


def test_get_episodes():
    episodes = Extractor().search("")[0].get_anime().get_episodes()
    assert len(episodes) == 3
    assert episodes[0].dict()["num"] == 1
    assert episodes[1].dict()["num"] == 2
    assert episodes[2].dict()["num"] == 3


def test_get_video():
    video = Extractor().search("")[0].get_anime().get_episodes()[0].get_videos()
    assert video[0].get_source() == "video.mp4"


def test_walk_search():
    for i, meta in enumerate(Extractor().walk_search("")):
        assert {
            "search": meta.search.dict(),
            "anime": meta.anime.dict(),
            "episode": meta.episode.dict(),
            "video": meta.video.dict(),
        } == Extractor.WALK_SEARCH[i]


def test_walk_ongoing():
    for i, meta in enumerate(Extractor().walk_ongoing()):
        assert {
            "search": meta.search.dict(),
            "anime": meta.anime.dict(),
            "episode": meta.episode.dict(),
            "video": meta.video.dict(),
        } == Extractor.WALK_ONGOING[i]


def test_anime_metadata():
    search = Extractor().search("")[0]
    for i, meta in enumerate(search):
        assert {
            "search": meta.search.dict(),
            "anime": meta.anime.dict(),
            "episode": meta.episode.dict(),
            "video": meta.video.dict(),
        } == Extractor.SEARCH_META[i]


def test_ongoing_metadata():
    ongoing = Extractor().ongoing()[0]
    for i, meta in enumerate(ongoing):
        assert {
            "search": meta.search.dict(),
            "anime": meta.anime.dict(),
            "episode": meta.episode.dict(),
            "video": meta.video.dict(),
        } == Extractor.ONGOING_META[i]


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


def test_base_model_compare_models():
    base_1 = BaseModel(foo=1, bar=2, baz=3)
    base_2 = BaseModel(bar=2, foo=1, baz=3)
    assert base_1 == base_2
    assert base_1 != BaseModel(foo=2, bar=3, baz=4)


def test_base_model_compare_2():
    base_1 = BaseModel(foo=["a", "b", "c"], bar=2)
    base_2 = BaseModel(foo=["a", "b", "c"], bar=2)
    base_3 = BaseModel(foo="d", bar=2)
    assert base_1 == base_2
    assert base_1 != base_3


def test_base_model_initialization():
    bm = BaseModel(arg1=1, arg2="hello")
    assert bm.arg1 == 1
    assert bm.arg2 == "hello"
    assert bm.dict() == dict(arg1=1, arg2="hello")


def test_base_model_unescape():
    bm = BaseModel()
    test_string = "&gt; &lt; &amp;"
    unescaped_string = bm._unescape(test_string)
    assert unescaped_string == "> < &"


def test_base_model_soup():
    bm = BaseModel()
    test_html = "<html><body><h1>Test</h1></body></html>"
    soup = bm._soup(test_html)
    assert soup.find("h1").text == "Test"


def test_base_model_urlsplit():
    bm = BaseModel()
    test_url = "https://www.example.com/path?query=test#fragment"
    split_result = bm._urlsplit(test_url)
    assert split_result.netloc == "www.example.com"


def test_base_model_urlparse():
    bm = BaseModel()
    test_url = "https://www.example.com/path?query=test#fragment"
    parse_result = bm._urlparse(test_url)
    assert parse_result.netloc == "www.example.com"


def test_cmp_videos_default_flags():
    class FakeVideo(BaseVideo):
        dub: str

    vid_1 = FakeVideo(url="https://example.com", dub="foo")
    vid_2 = FakeVideo(url="https://example.com", dub="bar")
    vid_3 = FakeVideo(url="https://example2.com", dub="foo")
    assert vid_1 == vid_2
    assert vid_1 != vid_3
    assert vid_2 != vid_3


def test_cmp_videos_with_cmp_keys():
    class FakeVideo(BaseVideo):
        __CMP_KEYS__ = ("dub",)
        dub: str

    vid_1 = FakeVideo(url="https://example.com/a", dub="foo")
    vid_2 = FakeVideo(url="https://example.com/b", dub="foo")
    vid_3 = FakeVideo(url="https://example.com/a", dub="bar")
    vid_4 = FakeVideo(url="https://example2.com/b", dub="foo")
    assert vid_1 == vid_2
    assert vid_1 != vid_3
    assert vid_1 != vid_4
    assert vid_3 != vid_4


def test_cmp_videos_disable_cmp_url_netloc():
    class FakeVideo(BaseVideo):
        __CMP_URL_NETLOC__ = False
        __CMP_KEYS__ = ("dub",)
        dub: str

    vid_1 = FakeVideo(url="https://example.com/a", dub="foo")
    vid_2 = FakeVideo(url="https://example.com/b", dub="foo")
    vid_3 = FakeVideo(url="https://example.com/a", dub="bar")
    vid_4 = FakeVideo(url="https://example2.com/a", dub="foo")

    assert vid_1 == vid_2
    assert vid_1 == vid_4
    assert vid_1 != vid_3
    assert vid_3 != vid_4
