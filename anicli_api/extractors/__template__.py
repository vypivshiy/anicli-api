"""Template extractor"""
from __future__ import annotations

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


class Extractor(BaseAnimeExtractor):
    # optional constants, HTTP configuration here

    def search(self, query: str) -> List['SearchResult']:  # type: ignore[override]
        # past code here
        pass

    def ongoing(self) -> List['Ongoing']:  # type: ignore[override]
        # past code here
        pass

    async def async_search(self, query: str) -> List['SearchResult']:  # type: ignore[override]
        # past async code here
        pass

    async def async_ongoing(self) -> List['Ongoing']:  # type: ignore[override]
        # past async code here
        pass


class SearchResult(BaseSearchResult):
    # optional past metadata attrs here
    async def a_get_anime(self) -> 'AnimeInfo':
        # past async code here
        pass

    def get_anime(self) -> 'AnimeInfo':
        # past code here
        pass


class Ongoing(BaseOngoing):
    # optional past metadata attrs here
    async def a_get_anime(self) -> 'AnimeInfo':
        # past async code here
        pass

    def get_anime(self) -> 'AnimeInfo':
        # past code here
        pass


class AnimeInfo(BaseAnimeInfo):
    # optional past metadata attrs here
    async def a_get_episodes(self) -> List['Episode']:  # type: ignore[override]
        # past async code here
        pass

    def get_episodes(self) -> List['Episode']:  # type: ignore[override]
        # past code here
        pass


class Episode(BaseEpisode):
    # optional past metadata attrs here
    async def a_get_videos(self) -> List['Video']:  # type: ignore[override]
        # past async code here
        pass

    def get_videos(self) -> List['Video']:  # type: ignore[override]
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
