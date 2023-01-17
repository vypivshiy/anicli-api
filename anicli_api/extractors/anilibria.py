"""
TODO sort keys for objects
"""
from __future__ import annotations

from typing import Any, AsyncGenerator, Generator, Optional, Protocol

from anicli_api.base import *
from anicli_api.base_decoder import MetaVideo

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
    search: SearchResult
    anime: AnimeInfo
    episode: Episode
    video: Video


class OngoingIterData(Protocol):
    search: Ongoing
    anime: AnimeInfo
    episode: Episode
    video: Video


class Anilibria:
    """For details see docs on https://github.com/anilibria/docs/blob/master/api_v2.md"""

    HTTP = BaseAnimeExtractor.HTTP
    HTTP_ASYNC = BaseAnimeExtractor.HTTP_ASYNC

    BASE_URL = "https://api.anilibria.tv/v2/"

    def api_request(self, method: str = "GET", *, api_method: str, **kwargs) -> dict:
        response = self.HTTP().request(method=method, url=f"{self.BASE_URL}{api_method}", **kwargs)
        return response.json()

    async def a_api_request(self, method: str = "GET", *, api_method: str, **kwargs) -> dict:
        async with self.HTTP_ASYNC() as session:
            response = await session.request(method, self.BASE_URL + api_method, **kwargs)
            return response.json()

    @staticmethod
    def _kwargs_pop_params(kwargs, **params) -> dict:
        data = kwargs.pop("params") if kwargs.get("params") else {}
        data.update(params)
        return data

    def search_titles(self, *, search: str, limit: int = -1, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, search=search, limit=limit)
        return self.api_request(api_method="searchTitles", params=params, **kwargs)

    async def a_search_titles(self, *, search: str, limit: int = -1, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, limit=limit)
        return await self.a_api_request(api_method="searchTitles", params=params, **kwargs)

    def get_updates(self, *, limit: int = -1, **kwargs) -> dict:
        """getUpdates method
        :param limit:
        :param kwargs:
        :return:
        """
        params = self._kwargs_pop_params(kwargs, limit=limit)
        return self.api_request(api_method="getUpdates", data=params, **kwargs)

    async def a_get_updates(self, *, limit: int = -1, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, limit=limit)
        return await self.a_api_request(api_method="getUpdates", data=params, **kwargs)


class Extractor(BaseAnimeExtractor):
    # optional constants, HTTP configuration here
    """For details see docs on https://github.com/anilibria/docs/blob/master/api_v2.md"""
    BASE_URL = "https://api.anilibria.tv/v2/"
    ANILIBRIA = Anilibria()

    def async_walk_search(self, query: str) -> AsyncGenerator[SearchIterData, None]:
        return super().async_walk_search(query)

    def async_walk_ongoing(self) -> AsyncGenerator[OngoingIterData, None]:
        return super().async_walk_ongoing()

    def walk_search(self, query: str) -> Generator[SearchIterData, None, None]:
        return super().walk_search(query)

    def walk_ongoing(self) -> Generator[OngoingIterData, None, None]:
        return super().walk_ongoing()

    def search(self, query: str) -> List["SearchResult"]:
        return [SearchResult(**kw) for kw in self.ANILIBRIA.search_titles(search=query)]

    def ongoing(self) -> List["Ongoing"]:
        return [Ongoing(**kw) for kw in self.ANILIBRIA.get_updates()]

    async def async_search(self, query: str) -> List["SearchResult"]:
        return [SearchResult(**kw) for kw in (await self.ANILIBRIA.a_search_titles(search=query))]

    async def async_ongoing(self) -> List["Ongoing"]:
        return [Ongoing(**kw) for kw in (await self.ANILIBRIA.a_get_updates())]


class SResult(BaseModel):
    id: int
    code: str
    names: dict
    announce: Optional[Any]
    status: dict
    posters: dict
    updated: int
    last_change: int
    type: dict
    genres: List[str]
    team: dict
    season: dict
    description: str
    in_favorites: int
    blocked: dict
    player: dict
    torrents: dict

    async def a_get_anime(self) -> "AnimeInfo":
        return AnimeInfo(**self.dict())

    def get_anime(self) -> "AnimeInfo":
        return AnimeInfo(**self.dict())

    def __str__(self):
        return f"{list(self.names.values())[0]}"


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
    # TODO typing keys better
    id: int
    code: str
    names: dict
    announce: Optional[Any]
    status: dict
    posters: dict
    updated: int
    last_change: int
    type: dict
    genres: List[str]
    team: dict
    season: dict
    description: str
    in_favorites: int
    blocked: dict
    player: dict
    torrents: dict

    async def a_get_episodes(self) -> List["Episode"]:
        return [
            Episode(
                alternative_player=self.player["alternative_player"],
                host=self.player["host"],
                torrents=self.torrents["list"],
                **p,
            )
            for p in self.player["playlist"].values()
        ]

    def get_episodes(self) -> List["Episode"]:
        return [
            Episode(
                alternative_player=self.player["alternative_player"],
                host=self.player["host"],
                torrents=self.torrents["list"],
                **p,
            )
            for p in self.player["playlist"].values()
        ]

    def __str__(self):
        return f"{list(self.names.values())[0]}\n{self.genres}\n{self.description}"


class Episode(BaseEpisode):
    alternative_player: Optional[str]
    host: str
    serie: int
    created_timestamp: int
    preview: Optional[Any]
    skips: dict
    hls: dict
    torrents: dict

    async def a_get_videos(self) -> List["Video"]:
        return [
            Video(
                torrents=self.torrents,
                # dirty hack for success url validate for decoder.anilibria :D
                url=self.hls["sd"],
                **{k: f"https://{self.host}{v}" if v else None for k, v in self.hls.items()},
            )
        ]

    def get_videos(self) -> List["Video"]:
        return [
            Video(
                torrents=self.torrents,
                # dirty hack for success url validate for decoder.anilibria :D
                url=self.hls["sd"],
                **{k: f"https://{self.host}{v}" if v else None for k, v in self.hls.items()},
            )
        ]

    def __str__(self):
        return f"{self.serie} episode"


class Video(BaseVideo):
    torrents: dict
    fhd: Optional[str]
    hd: str
    sd: str

    def _source(self) -> List[MetaVideo]:
        if self.fhd:
            return [
                MetaVideo(type="m3u8", quality=480, url=self.sd),
                MetaVideo(type="m3u8", quality=720, url=self.hd),
                MetaVideo(type="m3u8", quality=1080, url=self.fhd),
            ]
        return [
            MetaVideo(type="m3u8", quality=480, url=self.sd),
            MetaVideo(type="m3u8", quality=720, url=self.hd),
        ]

    def get_source(self) -> List[MetaVideo]:
        return self._source()

    async def a_get_source(self) -> List[MetaVideo]:
        return self._source()

    def __hash__(self):
        return hash(tuple(self.get_source()))


class TestCollections(BaseTestCollections):
    def test_search(self):
        resp = Extractor().search("Зомбиленд")
        assert resp[0].id == 7474
        assert resp[1].id == 8960

    def test_ongoing(self):
        resp = Extractor().ongoing()
        assert len(resp) > 1

    def test_extract_metadata(self):
        for meta in Extractor().search("Зомбиленд")[0]:
            assert meta.search.id == 7474
            assert meta.search.code == "zombieland-saga"
            assert meta.search.genres == ["Комедия", "Сверхъестественное", "Ужасы", "Экшен"]
            break

    def test_extract_video(self):
        search = Extractor().search("Зомбиленд")[0]
        anime = search.get_anime()
        episodes = anime.get_episodes()
        video = episodes[0].get_videos()[0]
        assert "libria.fun" in video.get_source()[0].url
