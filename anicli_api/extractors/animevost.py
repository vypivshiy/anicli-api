"""Animevost extractor"""
from __future__ import annotations

from typing import AsyncGenerator, Generator, Protocol, Union

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

from anicli_api.base_decoder import MetaVideo


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


class VostAPI:
    HTTP = BaseAnimeExtractor.HTTP
    HTTP_ASYNC = BaseAnimeExtractor.HTTP_ASYNC

    BASE_URL = "https://api.animevost.org/v1/"

    def api_request(self, method: str, *, api_method: str, **kwargs) -> Union[dict, list[dict]]:
        response = self.HTTP().request(method, self.BASE_URL + api_method, **kwargs)
        return response.json()

    async def a_api_request(
        self, method: str, *, api_method: str, **kwargs
    ) -> Union[dict, list[dict]]:
        async with self.HTTP_ASYNC() as session:
            response = await session.request(method, self.BASE_URL + api_method, **kwargs)
            return response.json()

    @staticmethod
    def _kwargs_pop_params(kwargs, **params) -> dict:
        data = kwargs.pop("params") if kwargs.get("params") else {}
        data.update(params)
        return data

    def search(self, search: str, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, name=search)
        return self.api_request("POST", api_method="search", data=params, **kwargs)  # type: ignore

    async def a_search(self, search: str, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, name=search)
        return await self.a_api_request("POST", api_method="search", data=params, **kwargs)  # type: ignore

    def last(self, *, limit: int = 20, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, page=1, quantity=limit)
        return self.api_request("GET", api_method="last", params=params, **kwargs)  # type: ignore

    async def a_last(self, *, limit: int = 20, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, page=1, quantity=limit)
        return await self.a_api_request("GET", api_method="last", params=params, **kwargs)  # type: ignore

    def playlist(self, id: int) -> list[dict]:
        return self.api_request("POST", api_method="playlist", data={"id": id})  # type: ignore

    async def a_playlist(self, id: int) -> list[dict]:
        return await self.a_api_request("POST", api_method="playlist", data={"id": id})  # type: ignore


class Extractor(BaseAnimeExtractor):
    def async_walk_search(self, query: str) -> AsyncGenerator[SearchIterData, None]:
        return super().async_walk_search(query)

    def walk_search(self, query: str) -> Generator[SearchIterData, None, None]:
        return super().walk_search(query)

    def async_walk_ongoing(self) -> AsyncGenerator[OngoingIterData, None]:
        return super().async_walk_ongoing()

    def walk_ongoing(self) -> Generator[OngoingIterData, None, None]:
        return super().walk_ongoing()

    def search(self, query: str) -> List[SearchResult]:
        # past code here
        response = VostAPI().search(query)
        return [SearchResult(**kw) for kw in response["data"]]

    def ongoing(self) -> List[Ongoing]:
        response = VostAPI().last()
        return [Ongoing(**kw) for kw in response["data"]]

    async def async_search(self, query: str) -> List[SearchResult]:
        # past async code here
        response = await VostAPI().a_search(query)
        return [SearchResult(**kw) for kw in response["data"]]

    async def async_ongoing(self) -> List[Ongoing]:
        response = await VostAPI().a_last()
        return [Ongoing(**kw) for kw in response["data"]]


class SResult(BaseModel):
    # TODO add convert camel case to snake case
    id: int
    title: str
    description: str
    genre: str
    year: str
    urlImagePreview: str
    screenImage: list[str]
    isFavorite: int
    isLikes: int
    rating: int
    votes: int
    timer: int
    type: str
    director: str
    series: str  # '{\'1 серия\':\'147459278\ ...'

    async def a_get_anime(self) -> "AnimeInfo":
        # past async code here
        response = await VostAPI().a_playlist(self.id)
        return AnimeInfo(**self.dict(), playlist=response)

    def get_anime(self) -> "AnimeInfo":
        response = VostAPI().playlist(self.id)
        return AnimeInfo(**self.dict(), playlist=response)

    def __str__(self):
        return f"{self.title}"


class SearchResult(SResult, BaseSearchResult):
    def __iter__(self) -> Generator[SearchIterData, None, None]:
        return super().__iter__()

    def __aiter__(self) -> AsyncGenerator[SearchIterData, None]:
        return super().__aiter__()


class Ongoing(SResult, BaseOngoing):
    def __iter__(self) -> Generator[OngoingIterData, None, None]:
        return super().__iter__()

    def __aiter__(self) -> AsyncGenerator[OngoingIterData, None]:
        return super().__aiter__()


class AnimeInfo(BaseAnimeInfo):
    id: int
    title: str
    description: str
    genre: str
    year: str
    urlImagePreview: str
    screenImage: list[str]
    isFavorite: int
    isLikes: int
    rating: int
    votes: int
    timer: int
    type: str
    director: str
    series: str  # '{\'1 серия\':\'147459278\ ...'
    playlist: list[dict]

    async def a_get_episodes(self) -> List["Episode"]:
        return [Episode(**kw) for kw in self.playlist]

    def get_episodes(self) -> List["Episode"]:
        return [Episode(**kw) for kw in self.playlist]

    def __str__(self):
        return f"{self.title} {self.year} {self.rating}\n{self.genre}\n{self.description}"


class Episode(BaseEpisode):
    name: str
    preview: str

    # video meta
    hd: str
    std: str

    async def a_get_videos(self) -> List["Video"]:
        return [Video(hd=self.hd, std=self.std)]

    def get_videos(self) -> List["Video"]:
        return [Video(hd=self.hd, std=self.std)]

    def __str__(self):
        return f"{self.name}"


class Video(BaseVideo):
    hd: str
    std: str

    def get_source(self) -> List[MetaVideo]:
        return [
            MetaVideo(type="mp4", quality=480, url=self.std),
            MetaVideo(type="mp4", quality=720, url=self.hd),
        ]

    async def a_get_source(self) -> List[MetaVideo]:
        return [
            MetaVideo(type="mp4", quality=480, url=self.std),
            MetaVideo(type="mp4", quality=720, url=self.hd),
        ]


class TestCollections(BaseTestCollections):
    def test_search(self):
        # rewrite testcase search here
        result = Extractor().search("serial experiments lain")
        assert result[0].get_anime().id == 558

    def test_ongoing(self):
        # test get ongoing
        assert len(Extractor().ongoing()) > 1

    def test_extract_metadata(self):
        # rewrite testcase get metadata here
        for meta in Extractor().search("serial experiments lain")[0]:
            # past metadata dict here
            assert meta.search.id == 558
            assert meta.anime.id == 558
            assert meta.episode.name == "1 серия"
            break

    def test_extract_video(self):
        # rewrite testcase extract video here
        for meta in Extractor().search("serial experiments lain")[0]:
            assert meta.video.get_source()[0].url.endswith(".mp4")
