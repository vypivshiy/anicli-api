## TEMPLATE FOR GENERATE EXTRACTOR MODULE
from __future__ import annotations

from typing import AsyncGenerator, Generator, Protocol

from anicli_api.base import *

__all__ = (
    "Extractor",
    "SearchResult",
    "Ongoing",
    "AnimeInfo",
    "Episode",
    "Video",
    "TestCollections",
)


class SearchIterData(Protocol):
    # IDE typing help: SearchResult.__iter__, SearchResult.__aiter__, walk_search, async_walk_search
    search: SearchResult
    anime: AnimeInfo
    episode: Episode
    video: Video


class OngoingIterData(Protocol):
    # IDE typing help: typing help: Ongoing.__iter__, Ongoing.__aiter__, walk_ongoing, async_walk_ongoing
    search: Ongoing
    anime: AnimeInfo
    episode: Episode
    video: Video


class Extractor(BaseAnimeExtractor):
    # optional constants, HTTP configuration here
    BASE_URL = "{{ base_url }}"

    def async_walk_search(self, query: str) -> AsyncGenerator[SearchIterData, None]:
        return super().async_walk_search(query)

    def walk_search(self, query: str) -> Generator[SearchIterData, None, None]:
        return super().walk_search(query)

    def async_walk_ongoing(self) -> AsyncGenerator[OngoingIterData, None]:
        return super().async_walk_ongoing()

    def walk_ongoing(self) -> Generator[OngoingIterData, None, None]:
        return super().walk_ongoing()

    def search(self, query: str) -> List["SearchResult"]:
        # write an attributes parser for search results
        response = self.HTTP().get("{{ search_url }}", params={{ params }}).text
        return [SearchResult()]

    def ongoing(self) -> List["Ongoing"]:
        # write an attributes parser for ongoings
        response = self.HTTP().get("{{ ongoing_url }}").text
        return [Ongoing()]

    async def async_search(self, query: str) -> List["SearchResult"]:
        # write an attributes parser for search results
        async with self.HTTP_ASYNC() as session:
            response = (
                await session.get("{{ search_url }}", params={{ params }})
            ).text
            return [SearchResult()]

    async def async_ongoing(self) -> List["Ongoing"]:
        # write an attributes parser for ongoings
        async with self.HTTP_ASYNC() as session:
            response = (await session.get("{{ ongoing_url }}")).text
            return [Ongoing()]


class SearchResult(BaseSearchResult):
    # optional past metadata attrs here
    def __iter__(self) -> Generator[SearchIterData, None, None]:
        return super().__iter__()

    def __aiter__(self) -> AsyncGenerator[SearchIterData, None]:
        return super().__aiter__()

    async def a_get_anime(self) -> "AnimeInfo":
        # past async code here
        return AnimeInfo()

    def get_anime(self) -> "AnimeInfo":
        # past code here
        return AnimeInfo()


class Ongoing(BaseOngoing):
    # optional past metadata attrs here
    def __iter__(self) -> Generator[OngoingIterData, None, None]:
        return super().__iter__()

    def __aiter__(self) -> AsyncGenerator[OngoingIterData, None]:
        return super().__aiter__()

    async def a_get_anime(self) -> "AnimeInfo":
        # past async code here
        return AnimeInfo()

    def get_anime(self) -> "AnimeInfo":
        # past code here
        return AnimeInfo()


class AnimeInfo(BaseAnimeInfo):
    # optional past metadata attrs here
    async def a_get_episodes(self) -> List["Episode"]:
        # past async code here
        return [Episode()]

    def get_episodes(self) -> List["Episode"]:
        # past code here
        return [Episode()]


class Episode(BaseEpisode):
    # optional past metadata attrs here
    async def a_get_videos(self) -> List["Video"]:
        # past async code here
        url = ...
        return [Video(url=url)]

    def get_videos(self) -> List["Video"]:
        # past code here
        url = ...
        return [Video(url=url)]


class Video(BaseVideo):
    # optional past metadata attrs here.
    # url: str
    # attribute required for automatic video parser for available decoders
    # or manually define get_source and a_get_source methods
    pass


class TestCollections(BaseTestCollections):
    def test_search(self):
        # rewrite testcase search here
        result = Extractor().search("serial experiments lain")
        # past metadata dict
        assert result[0].get_anime().dict() == {}

    def test_ongoing(self):
        # test get ongoing
        assert len(Extractor().ongoing()) > 1

    def test_extract_metadata(self):
        # rewrite testcase get metadata here
        for meta in Extractor().search("serial experiments lain")[0]:
            # past metadata dict here
            assert meta.search.dict() == {}
            assert meta.anime.dict() == {}
            assert meta.episode.dict() == {}
            break

    def test_extract_video(self):
        # rewrite testcase extract video here
        for meta in Extractor().search("serial experiments lain")[0]:
            assert "kodik" in meta.video.url
            assert meta.video.get_source()[0].url.endswith(".m3u8")
