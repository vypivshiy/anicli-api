from typing import TYPE_CHECKING, Dict, List, Union

from attrs import define

from anicli_api._http import HTTPAsync, HTTPSync
from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.player.base import Video  # direct make this object

if TYPE_CHECKING:
    from httpx import AsyncClient, Client


class AnilibriaAPI:
    """Dummmy API interface
    https://github.com/anilibria/docs/blob/master/api_v2.md
    """

    BASE_URL = "https://api.anilibria.tv/v3/"

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

    def search_titles(self, *, search: str, limit: int = -1, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, search=search, limit=limit)
        return self.api_request(api_method="title/search", params=params, **kwargs)["list"]

    async def a_search_titles(self, *, search: str, limit: int = -1, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, limit=limit)
        return (await self.a_api_request(api_method="title/search", params=params, **kwargs))["list"]

    def get_updates(self, *, limit: int = -1, **kwargs) -> dict:
        """getUpdates method
        :param limit:
        :param kwargs:
        :return:
        """
        params = self._kwargs_pop_params(kwargs, limit=limit)
        resp = self.api_request(api_method="title/updates", data=params, **kwargs)
        return resp["list"]

    async def a_get_updates(self, *, limit: int = -1, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, limit=limit)
        return (await self.a_api_request(api_method="title/updates", data=params, **kwargs))["list"]


class Extractor(BaseExtractor):
    BASE_URL = "https://api.anilibria.tv/v3/"

    def __init__(self, http_client: "Client" = HTTPSync(), http_async_client: "AsyncClient" = HTTPAsync()):
        super().__init__(http_client=http_client, http_async_client=http_async_client)
        self._api = AnilibriaAPI(http_client=http_client, http_async_client=http_async_client)

    @property
    def api(self):
        return self._api

    @classmethod
    def _extract_meta_data(cls, kw: dict) -> dict:
        """extract response data for anicli application"""
        return dict(
            **kw,
            # STUB values for API interface
            title=kw["names"]["ru"],
            thumbnail=kw["posters"]["original"],
            url="",
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
        return [Ongoing(**self._extract_meta_data(kw), **self._kwargs_http) for kw in self.api.get_updates()]

    async def a_ongoing(self) -> List["Ongoing"]:
        return [Ongoing(**self._extract_meta_data(kw), **self._kwargs_http) for kw in (await self.api.a_get_updates())]


# without @attrs.define decorator to avoid
# TypeError: multiple bases have instance lay-out conflict error
# (__slots__ magic method and attrs hooks issue)
class _SearchOrOngoing:
    # stubs
    thumbnail: str
    url: str
    title: str
    _kwargs_http: Dict[str, Union["Client", "AsyncClient"]]

    # API
    id: int
    code: str
    names: Dict[str, str]
    franchises: List[str]
    announce: str
    status: Dict[str, str]
    posters: Dict[str, Dict[str, str]]
    updated: int
    last_change: int
    type: Dict[str, str]
    genres: List[str]
    team: Dict[str, List[str]]
    season: Dict[str, Union[int, str]]
    description: str
    in_favorites: int
    blocked: Dict[str, bool]
    player: Dict[str, str]
    torrents: Dict[str, str]

    async def a_get_anime(self) -> "Anime":
        return self.get_anime()

    def get_anime(self) -> "Anime":
        return Anime(
            title=self.title,
            alt_title=self.names["en"],
            description=self.description,
            thumbnail=self.thumbnail,
            genres=self.genres,
            player=self.player,
            **self._kwargs_http,
        )

    def __str__(self):
        return self.title


@define(kw_only=True)
class Search(_SearchOrOngoing, BaseSearch):
    # API
    id: int
    code: str
    names: Dict[str, str]
    franchises: List[str]
    announce: str
    status: Dict[str, str]
    posters: Dict[str, Dict[str, str]]
    updated: int
    last_change: int
    type: Dict[str, str]
    genres: List[str]
    team: Dict[str, List[str]]
    season: Dict[str, Union[int, str]]
    description: str
    in_favorites: int
    blocked: Dict[str, bool]
    player: Dict[str, str]
    torrents: Dict[str, str]


@define(kw_only=True)
class Ongoing(_SearchOrOngoing, BaseOngoing):
    # API
    id: int
    code: str
    names: Dict[str, str]
    franchises: List[str]
    announce: str
    status: Dict[str, str]
    posters: Dict[str, Dict[str, str]]
    updated: int
    last_change: int
    type: Dict[str, str]
    genres: List[str]
    team: Dict[str, List[str]]
    season: Dict[str, Union[int, str]]
    description: str
    in_favorites: int
    blocked: Dict[str, bool]
    player: Dict[str, str]
    torrents: Dict[str, str]


@define(kw_only=True)
class Anime(BaseAnime):
    title: str
    alt_title: str
    description: str
    thumbnail: str
    genres: List[str]
    player: Dict

    def __str__(self):
        return self.title

    def get_episodes(self) -> List["Episode"]:
        host = self.player["host"]
        # TODO validate fhd key
        return [
            Episode(
                title=item["name"] or "Episode",  # maybe return None
                num=num,
                # maybe dont exist 1080p
                fhd=f"https://{host}{item['hls']['fhd']}" if item["hls"].get("fhd") else None,
                hd=f"https://{host}{item['hls']['hd']}",
                sd=f"https://{host}{item['hls']['sd']}",
            )
            for num, item in self.player["list"].items()
        ]

    async def a_get_episodes(self) -> List["Episode"]:
        return self.get_episodes()


@define(kw_only=True)
class Episode(BaseEpisode):
    title: str
    num: Union[int, str]  # type: ignore
    # video meta
    _fhd: str
    _hd: str
    _sd: str

    def get_sources(self) -> List["Source"]:
        return [Source(title="Anilibria", url="https://api.anilibria.tv", fhd=self._fhd, hd=self._hd, sd=self._sd)]

    async def a_get_sources(self) -> List["Source"]:
        return self.get_sources()


@define(kw_only=True)
class Source(BaseSource):
    url: str
    title: str
    _fhd: str
    _hd: str
    _sd: str

    def get_videos(self, **_) -> List["Video"]:
        if self._fhd:
            return [
                Video(type="m3u8", quality=480, url=self._sd),
                Video(type="m3u8", quality=720, url=self._hd),
                Video(type="m3u8", quality=1080, url=self._fhd),
            ]
        return [
            Video(type="m3u8", quality=480, url=self._sd),
            Video(type="m3u8", quality=720, url=self._hd),
        ]

    async def a_get_videos(self, **_) -> List["Video"]:
        return self.get_videos()


if __name__ == "__main__":
    from anicli_api.tools import cli

    cli(Extractor())
