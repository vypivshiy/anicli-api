"""Template extractor"""
from __future__ import annotations
from typing import Protocol, AsyncGenerator, Generator

from anicli_api.base import *

__all__ = (
    'Extractor',
    'SearchResult',
    'Ongoing',
    'AnimeInfo',
    'Episode',
    'Video',
    'TestCollections',
)


# for help typing
class SearchIterData(Protocol):
    search: SearchResult
    anime: AnimeInfo
    episode: Episode
    video: Video


class OngoingIterData(Protocol):
    search: Ongoing
    anime: AnimeInfo
    episode: Episode
    video: Video


class Extractor(BaseAnimeExtractor):
    # optional constants, HTTP configuration here

    def async_walk_search(self, query: str) -> AsyncGenerator[SearchIterData, None]:
        return super().async_walk_search(query)

    def walk_search(self, query: str) -> Generator[SearchIterData, None, None]:
        return super().walk_search(query)

    def async_walk_ongoing(self) -> AsyncGenerator[OngoingIterData, None]:
        return super().async_walk_ongoing()

    def walk_ongoing(self) -> Generator[OngoingIterData, None, None]:
        return super().walk_ongoing()

    def search(self, query: str) -> List['SearchResult']:
        # past code here
        ...

    def ongoing(self) -> List['Ongoing']:
        # past code here
        pass

    async def async_search(self, query: str) -> List['SearchResult']:
        # past async code here
        pass

    async def async_ongoing(self) -> List['Ongoing']:
        # past async code here
        pass


class SearchResult(BaseSearchResult):
    # optional past metadata attrs here
    def __iter__(self) -> Generator[SearchIterData, None, None]:
        return super().__iter__()

    def __aiter__(self) -> AsyncGenerator[SearchIterData, None]:
        return super().__aiter__()

    async def a_get_anime(self) -> 'AnimeInfo':
        # past async code here
        pass

    def get_anime(self) -> 'AnimeInfo':
        # past code here
        pass


class Ongoing(BaseOngoing):
    # optional past metadata attrs here
    def __iter__(self) -> Generator[OngoingIterData, None, None]:
        return super().__iter__()

    def __aiter__(self) -> AsyncGenerator[OngoingIterData, None]:
        return super().__aiter__()

    async def a_get_anime(self) -> 'AnimeInfo':
        # past async code here
        pass

    def get_anime(self) -> 'AnimeInfo':
        # past code here
        pass


class AnimeInfo(BaseAnimeInfo):
    # optional past metadata attrs here
    async def a_get_episodes(self) -> List['Episode']:
        # past async code here
        pass

    def get_episodes(self) -> List['Episode']:
        # past code here
        pass


class Episode(BaseEpisode):
    # optional past metadata attrs here
    async def a_get_videos(self) -> List['Video']:
        # past async code here
        pass

    def get_videos(self) -> List['Video']:
        # past code here
        pass


class Video(BaseVideo):
    # optional past metadata attrs here
    pass


class TestCollections(BaseTestCollections):
    def test_search(self):
        # test search
        pass

    def test_ongoing(self):
        # test get ongoing
        pass

    def test_extract_metadata(self):
        # test get metadata
        pass

    def test_extract_video(self):
        # test extract video
        pass
