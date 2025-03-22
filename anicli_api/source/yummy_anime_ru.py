import re
from typing import TYPE_CHECKING, Dict, List, Union

from attrs import define, field

from anicli_api._http import HTTPAsync, HTTPSync
from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource, HttpMixin

if TYPE_CHECKING:
    from httpx import AsyncClient, Client


class YummyAnimeRuAPI:
    """Dummmy API interface
    Browser version of https://yummy-anime.ru/api/swagger#/
    """

    BASE_URL = "https://yummy-anime.ru/api/"

    def __init__(self, http_client: "Client" = HTTPSync(), http_async_client: "AsyncClient" = HTTPAsync()):
        self.http = http_client
        self.http_async = http_async_client

    def api_request(self, method: str = "GET", *, api_method: str, **kwargs) -> dict:
        response = self.http.request(method=method, url=f"{self.BASE_URL}{api_method}", **kwargs)
        return response.json()

    async def a_api_request(self, method: str = "GET", *, api_method: str, **kwargs) -> dict:
        response = await self.http_async.request(method, self.BASE_URL + api_method, **kwargs)
        return response.json()

    @staticmethod
    def _kwargs_pop_params(kwargs, **params) -> dict:
        data = kwargs.pop("params") if kwargs.get("params") else {}
        data.update(params)
        return data

    def get_anime(self, *, alias_or_id: Union[str, int], need_videos: bool = True, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, need_videos=need_videos)
        return self.api_request(api_method=f"anime/{alias_or_id}", params=params, **kwargs)["response"]

    async def a_get_anime(self, *, alias_or_id: Union[str, int], need_videos: bool = True, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, need_videos=need_videos)
        return (await self.a_api_request(api_method=f"anime/{alias_or_id}", params=params, **kwargs))["response"]

    def search_titles(self, *, search: str, limit: int = 20, offset: int = 0, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, q=search, limit=limit, offset=offset)
        return self.api_request(api_method="search", params=params, **kwargs)["response"]

    async def a_search_titles(self, *, search: str, limit: int = 20, offset: int = 0, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, q=search, limit=limit, offset=offset)
        return (await self.a_api_request(api_method="search", params=params, **kwargs))["response"]

    def get_updates(self, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs)
        resp = self.api_request(api_method="anime/schedule", data=params, **kwargs)
        return resp["response"]

    async def a_get_updates(self, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs)
        return (await self.a_api_request(api_method="anime/schedule", data=params, **kwargs))["response"]


@define(kw_only=True, slots=False)
class APIMixin(HttpMixin):
    """this dataclass provide pre-configured API clients"""

    _api: "YummyAnimeRuAPI" = field(
        default=YummyAnimeRuAPI(http_client=HTTPSync(), http_async_client=HTTPAsync()),
        repr=False,
        kw_only=True,
        hash=False,
    )
    """pre-configured API Client"""

    @property
    def api(self):
        return self._api


class Extractor(BaseExtractor):
    BASE_URL = "https://yummy-anime.ru/catalog/item/"

    def __init__(self, http_client: "Client" = HTTPSync(), http_async_client: "AsyncClient" = HTTPAsync()):
        super().__init__(http_client=http_client, http_async_client=http_async_client)
        self._api = YummyAnimeRuAPI(http_client=http_client, http_async_client=http_async_client)

    @property
    def api(self):
        return self._api

    @classmethod
    def _extract_meta_data(cls, kw: dict) -> dict:
        """extract response data for anicli application"""
        return dict(
            **kw,
            # STUB values for API interface
            thumbnail=kw["poster"]["fullsize"],
            url=cls.BASE_URL + kw["anime_url"],
        )

    def search(self, query: str) -> List["Search"]:
        return [
            Search(**self._extract_meta_data(kw), **self._kwargs_http) for kw in self.api.search_titles(search=query)
        ]

    async def a_search(self, query: str) -> List["Search"]:
        return [
            Search(**self._extract_meta_data(kw), **self._kwargs_http)
            for kw in (await self.api.a_search_titles(search=query))
        ]

    def ongoing(self) -> List["Ongoing"]:
        return [
            Ongoing(**self._extract_meta_data(kw), **self._kwargs_http)
            for kw in filter(lambda _: _["episodes"]["aired"] > 0, self.api.get_updates())
        ]

    async def a_ongoing(self) -> List["Ongoing"]:
        return [
            Ongoing(**self._extract_meta_data(kw), **self._kwargs_http)
            for kw in filter(lambda _: _["episodes"]["aired"] > 0, await self.api.a_get_updates())
        ]


class _SearchOrOngoing(APIMixin):
    # stubs
    thumbnail: str
    url: str
    title: str
    _kwargs_http: Dict[str, Union["Client", "AsyncClient"]]

    # API
    anime_id: int
    anime_url: str
    title: str
    description: str
    poster: Dict[str, str]

    def _extract(self, resp: dict):
        return Anime(
            title=self.title,
            alt_title=resp["other_titles"][0],
            description=self.description,
            thumbnail=self.thumbnail,
            genres=resp["genres"],
            videos=resp["videos"],
            episodes_available=resp["episodes"]["aired"],
            episodes_total=resp["episodes"]["count"],
            aired=resp["year"],
            **self._kwargs_http,  # type: ignore
        )

    def get_anime(self):
        resp = self.api.get_anime(alias_or_id=self.anime_id)
        return self._extract(resp)

    async def a_get_anime(self):
        resp = await self.api.a_get_anime(alias_or_id=self.anime_id)
        return self._extract(resp)

    def __str__(self):
        return self.title


@define(kw_only=True)
class Search(_SearchOrOngoing, BaseSearch):
    anime_status: Dict[str, Union[str, int]]
    rating: Dict[str, Union[int, float]]
    type: Dict[str, Union[str, int]]
    year: int
    views: int
    season: int
    min_age: Dict[str, Union[str, int]]
    top: Dict[str, Union[str, int]]
    remote_ids: Dict[str, Union[int, str]]

    # API
    anime_id: int
    anime_url: str
    title: str
    description: str
    poster: Dict[str, str]


@define(kw_only=True)
class Ongoing(_SearchOrOngoing, BaseOngoing):
    episodes: Dict[str, Union[int, float]]

    # API
    anime_id: int
    anime_url: str
    title: str
    description: str
    poster: Dict[str, str]


@define(kw_only=True)
class Anime(BaseAnime):
    title: str
    alt_title: str
    description: str
    thumbnail: str
    genres: List[str]
    episodes_available: int
    episodes_total: int
    aired: int
    videos: List[Dict[str, str]]

    def __str__(self):
        return self.title

    def map_videos(self) -> Dict[str, Dict[str, str]]:
        mapped_videos = {}
        for video in self.videos:
            mapped_videos.setdefault(video["number"], [])
            video["iframe_url"] = re.sub(r"^//", "https://", video["iframe_url"])
            mapped_videos[video["number"]].append(video)
        return mapped_videos

    def get_episodes(self) -> List["Episode"]:
        return [
            Episode(
                title="Episode",
                num=num,
                videos=item,
            )
            for num, item in self.map_videos().items()
        ]

    async def a_get_episodes(self) -> List["Episode"]:
        return self.get_episodes()


@define(kw_only=True)
class Episode(BaseEpisode):
    videos: Dict[str, str]

    def get_sources(self) -> List["Source"]:
        return [Source(title=video["data"]["dubbing"], url=video["iframe_url"]) for video in self.videos]  # type: ignore

    async def a_get_sources(self) -> List["Source"]:
        return self.get_sources()


@define(kw_only=True)
class Source(BaseSource):
    pass


if __name__ == "__main__":
    from anicli_api.tools import cli

    cli(Extractor())
