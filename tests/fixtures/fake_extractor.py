"""Pseudo real extractor for tests. based on extractors/__template__.py"""
from anicli_api.base import *

__all__ = (
    'Extractor',
    'SearchResult',
    'Ongoing',
    'AnimeInfo',
    'Episode',
    'Video',
    'TestCollections'
)


class Extractor(BaseAnimeExtractor):
    # optional constants, HTTP configuration here

    # for assert tests
    WALK_SEARCH = results = [
        {'search': {'url': 'search_1', 'title': 'title_1', 'meta': 'search_1 mock meta'},
         'anime': {'title': 'Some title name', 'meta': 'anime info meta'},
         'episode': {'title': 'episode_1', 'num': 1, 'meta': 'episode_1 meta'},
         'video': {'url': 'foobar'}},

        {'search': {'url': 'search_1', 'title': 'title_1', 'meta': 'search_1 mock meta'},
         'anime': {'title': 'Some title name', 'meta': 'anime info meta'},
         'episode': {'title': 'episode_2', 'num': 2, 'meta': 'episode_2 meta'},
         'video': {'url': 'foobar'}},

        {'search': {'url': 'search_1', 'title': 'title_1', 'meta': 'search_1 mock meta'},
         'anime': {'title': 'Some title name', 'meta': 'anime info meta'},
         'episode': {'title': 'episode_3', 'num': 3, 'meta': 'episode_3 meta'},
         'video': {'url': 'foobar'}}]

    WALK_ONGOING = [
        {'search': {'url': 'ongoing_1', 'title': 'title_1', 'description': 'ongoing_1 mock meta'},
         'anime': {'title': 'Some title name', 'meta': 'anime info meta'},
         'episode': {'title': 'episode_1', 'num': 1, 'meta': 'episode_1 meta'},
         'video': {'url': 'foobar'}},
        {'search': {'url': 'ongoing_1', 'title': 'title_1', 'description': 'ongoing_1 mock meta'},
         'anime': {'title': 'Some title name', 'meta': 'anime info meta'},
         'episode': {'title': 'episode_2', 'num': 2, 'meta': 'episode_2 meta'},
         'video': {'url': 'foobar'}},
        {'search': {'url': 'ongoing_1', 'title': 'title_1', 'description': 'ongoing_1 mock meta'},
         'anime': {'title': 'Some title name', 'meta': 'anime info meta'},
         'episode': {'title': 'episode_3', 'num': 3, 'meta': 'episode_3 meta'},
         'video': {'url': 'foobar'}},
        {'search': {'url': 'ongoing_2', 'title': 'title_2', 'description': 'search_2 mock meta'},
         'anime': {'title': 'Some title name', 'meta': 'anime info meta'},
         'episode': {'title': 'episode_1', 'num': 1, 'meta': 'episode_1 meta'},
         'video': {'url': 'foobar'}},
        {'search': {'url': 'ongoing_2', 'title': 'title_2', 'description': 'search_2 mock meta'},
         'anime': {'title': 'Some title name', 'meta': 'anime info meta'},
         'episode': {'title': 'episode_2', 'num': 2, 'meta': 'episode_2 meta'},
         'video': {'url': 'foobar'}},
        {'search': {'url': 'ongoing_2', 'title': 'title_2', 'description': 'search_2 mock meta'},
         'anime': {'title': 'Some title name', 'meta': 'anime info meta'},
         'episode': {'title': 'episode_3', 'num': 3, 'meta': 'episode_3 meta'},
         'video': {'url': 'foobar'}}]

    SEARCH_META = [{'search': {'url': 'search_1', 'title': 'title_1', 'meta': 'search_1 mock meta'},
                    'anime': {'title': 'Some title name', 'meta': 'anime info meta'},
                    'episode': {'title': 'episode_1', 'num': 1, 'meta': 'episode_1 meta'},
                    'video': {'url': 'foobar'}},
                   {'search': {'url': 'search_1', 'title': 'title_1', 'meta': 'search_1 mock meta'},
                    'anime': {'title': 'Some title name', 'meta': 'anime info meta'},
                    'episode': {'title': 'episode_2', 'num': 2, 'meta': 'episode_2 meta'},
                    'video': {'url': 'foobar'}},
                   {'search': {'url': 'search_1', 'title': 'title_1', 'meta': 'search_1 mock meta'},
                    'anime': {'title': 'Some title name', 'meta': 'anime info meta'},
                    'episode': {'title': 'episode_3', 'num': 3, 'meta': 'episode_3 meta'},
                    'video': {'url': 'foobar'}}]

    ONGOING_META = [{'search': {'url': 'ongoing_1', 'title': 'title_1', 'description': 'ongoing_1 mock meta'},
                     'anime': {'title': 'Some title name', 'meta': 'anime info meta'},
                     'episode': {'title': 'episode_1', 'num': 1, 'meta': 'episode_1 meta'},
                     'video': {'url': 'foobar'}},
                    {'search': {'url': 'ongoing_1', 'title': 'title_1', 'description': 'ongoing_1 mock meta'},
                     'anime': {'title': 'Some title name', 'meta': 'anime info meta'},
                     'episode': {'title': 'episode_2', 'num': 2, 'meta': 'episode_2 meta'},
                     'video': {'url': 'foobar'}},
                    {'search': {'url': 'ongoing_1', 'title': 'title_1', 'description': 'ongoing_1 mock meta'},
                     'anime': {'title': 'Some title name', 'meta': 'anime info meta'},
                     'episode': {'title': 'episode_3', 'num': 3, 'meta': 'episode_3 meta'},
                     'video': {'url': 'foobar'}}]

    def search(self, query: str) -> List[BaseSearchResult]:
        return [SearchResult(url="search_1", title="title_1", meta="search_1 mock meta")]

    def ongoing(self) -> List[BaseOngoing]:
        return [Ongoing(url="ongoing_1", title="title_1", description="ongoing_1 mock meta"),
                Ongoing(url="ongoing_2", title="title_2", description="search_2 mock meta")]

    async def async_search(self, query: str) -> List[BaseSearchResult]:
        # past async code here
        return [SearchResult(url="search_1", title="title_1", meta="search_1 mock meta")]

    async def async_ongoing(self) -> List[BaseOngoing]:
        # past async code here
        return [Ongoing(url="ongoing_1", title="title_1", description="ongoing_1 mock meta"),
                Ongoing(url="ongoing_2", title="title_2", description="search_2 mock meta")]


class SearchResult(BaseSearchResult):
    # optional past metadata attrs here
    async def a_get_anime(self) -> 'AnimeInfo':
        # past async code here
        return AnimeInfo(title="Some title name", meta="anime info meta")

    def get_anime(self) -> 'AnimeInfo':
        # past code here
        return AnimeInfo(title="Some title name", meta="anime info meta")


class Ongoing(BaseOngoing):
    # optional past metadata attrs here
    async def a_get_anime(self) -> 'AnimeInfo':
        # past async code here
        return AnimeInfo(title="Some title name", meta="anime info meta")

    def get_anime(self) -> 'AnimeInfo':
        # past code here
        return AnimeInfo(title="Some title name", meta="anime info meta")


class AnimeInfo(BaseAnimeInfo):
    # optional past metadata attrs here
    async def a_get_episodes(self) -> List['BaseEpisode']:
        # past async code here
        return [
            Episode(title="episode_1", num=1, meta="episode_1 meta"),
            Episode(title="episode_2", num=2, meta="episode_2 meta"),
            Episode(title="episode_3", num=3, meta="episode_3 meta")
        ]

    def get_episodes(self) -> List['BaseEpisode']:
        return [
            Episode(title="episode_1", num=1, meta="episode_1 meta"),
            Episode(title="episode_2", num=2, meta="episode_2 meta"),
            Episode(title="episode_3", num=3, meta="episode_3 meta")
        ]


class Episode(BaseEpisode):
    # optional past metadata attrs here
    async def a_get_videos(self) -> List['BaseVideo']:
        # past async code here
        return [Video(url="foobar")]

    def get_videos(self) -> List['BaseVideo']:
        # past code here
        return [Video(url="foobar")]


class Video(BaseVideo):
    # optional past metadata attrs here
    def get_source(self):
        return "video.mp4"

    async def a_get_source(self):
        return "video.mp4"


class TestCollections(BaseTestCollections):
    def test_search(self):
        result = Extractor().search("")[0].dict()
        assert result == {"url": "search_1", "title": "title_1", "meta": "search_1 mock meta"}
        return result == {"url": "search_1", "title": "title_1", "meta": "search_1 mock meta"}

    def test_ongoing(self):
        assert len(Extractor().ongoing()) > 1
        return len(Extractor().ongoing()) > 1

    def test_extract_metadata(self):
        rez = Extractor().search("")[0].get_anime().dict()
        assert rez == {"title": "Some title name", "meta": "anime info meta"}
        return rez == {"title": "Some title name", "meta": "anime info meta"}

    def test_extract_video(self):
        rez = Extractor().search("")[0].get_anime().get_episodes()[0].get_videos()[0].get_source()
        assert rez == "video.mp4"
        return rez == "video.mp4"
