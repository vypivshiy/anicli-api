"""Template extractor"""
from __future__ import annotations

from typing import Protocol, Union, cast

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


class VostAPI:
    HTTP = BaseAnimeExtractor.HTTP
    HTTP_ASYNC = BaseAnimeExtractor.HTTP_ASYNC

    BASE_URL = "https://api.animevost.org/v1/"

    def api_request(self, method: str, *, api_method: str, **kwargs) -> dict:
        response = self.HTTP().request(method, self.BASE_URL + api_method, **kwargs)
        return response.json()

    async def a_api_request(self, method: str, *, api_method: str, **kwargs) -> dict:
        async with self.HTTP_ASYNC() as session:
            response = await session.request(method, self.BASE_URL + api_method, **kwargs)
            return response.json()

    @staticmethod
    def _kwargs_pop_params(kwargs, **params) -> dict:
        data = kwargs.pop("params") if kwargs.get("params") else {}
        data.update(params)
        return data

    def search_titles(self, search: str, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, name=search)
        return self.api_request(api_method="search", request_method="POST", data=params, **kwargs)

    def get_updates(self, *, limit: int = 20, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, page=1, quantity=limit)
        return self.api_request(api_method="last", params=params, **kwargs)


class Extractor(BaseAnimeExtractor):
    # optional constants, HTTP configuration here
    def search(self, query: str) -> List[BaseSearchResult]:
        # past code here
        pass

    def ongoing(self) -> List[BaseOngoing]:
        # past code here
        pass

    async def async_search(self, query: str) -> List[BaseSearchResult]:
        # past async code here
        pass

    async def async_ongoing(self) -> List[BaseOngoing]:
        # past async code here
        pass


class SearchResult(BaseSearchResult):
    # optional past metadata attrs here
    async def a_get_anime(self) -> "AnimeInfo":
        # past async code here
        pass

    def get_anime(self) -> "AnimeInfo":
        # past code here
        pass


class Ongoing(BaseOngoing):
    # optional past metadata attrs here
    async def a_get_anime(self) -> "AnimeInfo":
        # past async code here
        pass

    def get_anime(self) -> "AnimeInfo":
        # past code here
        pass


class AnimeInfo(BaseAnimeInfo):
    # optional past metadata attrs here
    async def a_get_episodes(self) -> List["BaseEpisode"]:
        # past async code here
        pass

    def get_episodes(self) -> List["BaseEpisode"]:
        # past code here
        pass


class Episode(BaseEpisode):
    # optional past metadata attrs here
    async def a_get_videos(self) -> List["BaseVideo"]:
        # past async code here
        pass

    def get_videos(self) -> List["BaseVideo"]:
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
