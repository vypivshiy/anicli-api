from typing import TYPE_CHECKING, Dict, List, Union, Any, Optional

from attrs import define

from anicli_api._http import HTTPAsync, HTTPSync
from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource

if TYPE_CHECKING:
    from httpx import AsyncClient, Client


class AnilibMeAPIMin:
    BASE_URL = "https://api.cdnlibs.org/api/"
    SITE_ID = 5  # header constant
    ONGOING_STATUS = 1  # magic constant: filter by "Статус тайтла -> Онгоинг"

    # params for extract anime details
    GET_ANIME_FIELD_PARAMS = {
        "fields[]": [
            "background",
            "eng_name",
            "otherNames",
            "summary",
            "releaseDate",
            "type_id",
            "caution",
            "views",
            "close_view",
            "rate_avg",
            "rate",
            "genres",
            "tags",
            "teams",
            "user",
            "franchise",
            "authors",
            "publisher",
            "userRating",
            "moderated",
            "metadata",
            "metadata.count",
            "metadata.close_comments",
            "anime_status_id",
            "time",
            "episodes",
            "episodes_count",
            "episodesSchedule",
            "shiki_rate",
        ]
    }

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

    def anime_search(self, *, query: str, **kwargs) -> dict:
        params = {
            "fields[]": ["rate", "rate_avg"],
            "q": query,
            "site_id[]": [self.SITE_ID],
        }
        return self.api_request(api_method="anime", params=params, headers={"site-id": str(self.SITE_ID)}, **kwargs)

    async def a_anime_search(self, *, query: str, **kwargs) -> dict:
        params = {
            "fields[]": ["rate", "rate_avg"],
            "q": query,
            "site_id[]": [self.SITE_ID],
        }
        return await self.a_api_request(
            api_method="anime", params=params, headers={"site-id": str(self.SITE_ID)}, **kwargs
        )

    def anime_ongoing(self, **kwargs) -> dict:
        # curl 'https://api.cdnlibs.org/api/anime?fields\[\]=rate&fields\[\]=rate_avg&fields\[\]=userBookmark&page=1&site_id\[\]=5&sort_by=last_episode_at&status\[\]=1' \
        #   -H 'site-id: 5' \
        #   -H 'user-agent: Mozilla/5.0 ...'
        params = {
            "fields[]": ["rate", "rate_avg", "userBookmark"],
            "page": 1,
            "site_id[]": [self.SITE_ID],
            "sort_by": "last_episode_at",
            "status[]": [self.ONGOING_STATUS],
        }

        resp = self.api_request(api_method="anime", params=params, headers={"site-id": str(self.SITE_ID)}, **kwargs)
        return resp

    async def a_anime_ongoings(self, *, limit: int = -1, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, limit=limit)
        return await self.a_api_request(api_method="title/updates", data=params, **kwargs)


class Extractor(BaseExtractor):
    BASE_URL = "https://api.cdnlibs.org/api/"

    def __init__(self, http_client: "Client" = HTTPSync(), http_async_client: "AsyncClient" = HTTPAsync()):
        super().__init__(http_client=http_client, http_async_client=http_async_client)
        self._api = AnilibMeAPIMin(http_client=http_client, http_async_client=http_async_client)

    @property
    def api(self):
        return self._api

    def search(self, query: str) -> List["Search"]:
        resp = self.api.anime_search(query=query)
        return [
            Search(
                thumbnail=kw["cover"]["default"],
                title=kw["rus_name"] if kw.get("rus_name") else kw["eng_name"],
                url=self.BASE_URL + "anime/" + kw["slug_url"],
                **kw,
                **self._kwargs_http,
            )
            for kw in resp["data"]
        ]

    async def a_search(self, query: str) -> List["Search"]:
        resp = await self.api.a_anime_search(query=query)
        return [
            Search(
                thumbnail=kw["cover"]["default"],
                title=kw["rus_name"] if kw.get("rus_name") else kw["eng_name"],
                url=self.BASE_URL + "anime/" + kw["slug_url"],
                **kw,
                **self._kwargs_http,
            )
            for kw in resp["data"]
        ]

    def ongoing(self) -> List["Ongoing"]:
        resp = self.api.anime_ongoing()
        # drop [links], [meta] keys, impl minimal features
        return [
            Ongoing(
                thumbnail=kw["cover"]["default"],
                title=kw["rus_name"] if kw.get("rus_name") else kw["eng_name"],
                url=self.BASE_URL + "anime/" + kw["slug_url"],
                # stubs
                **kw,
                **self._kwargs_http,
            )
            for kw in resp["data"]
        ]

    async def a_ongoing(self) -> List["Ongoing"]:
        resp = await self.api.a_anime_ongoings()
        # drop [links], [meta] keys, impl minimal features
        return [
            Ongoing(
                thumbnail=kw["cover"]["default"],
                title=kw["rus_name"] if kw.get("rus_name") else kw["eng_name"],
                url=self.BASE_URL + "anime/" + kw["slug_url"],
                # stubs
                **kw,
                **self._kwargs_http,
            )
            for kw in resp["data"]
        ]


class _SearchOrOngoing:
    thumbnail: str
    url: str
    title: str
    # stubs
    _kwargs_http: Dict[str, Union["Client", "AsyncClient"]]
    http_async: "AsyncClient"
    http: "Client"

    # API
    ageRestriction: Dict[str, Any]
    cover: Dict[str, Any]
    eng_name: str
    id: int
    model: str
    name: str
    rating: Dict[str, Any]
    releaseDateString: str
    rus_name: str
    shiki_rate: Optional[float]
    site: int
    slug: str
    slug_url: str
    status: Dict[str, Any]
    type: Dict[str, Any]

    async def a_get_anime(self) -> "Anime":
        # todo: move to API?
        resp = await self.http_async.get(self.url, params=AnilibMeAPIMin.GET_ANIME_FIELD_PARAMS).json()
        return Anime(
            title=self.title,
            description=resp["data"]["summary"],
            thumbnail=self.thumbnail,
            **resp["data"],
            **self._kwargs_http,
        )

    def get_anime(self) -> "Anime":
        resp = self.http.get(self.url, params=AnilibMeAPIMin.GET_ANIME_FIELD_PARAMS).json()
        return Anime(
            title=self.title,
            description=resp["data"]["summary"],
            thumbnail=self.thumbnail,
            **resp["data"],
            **self._kwargs_http,
        )


@define(kw_only=True)
class Search(_SearchOrOngoing, BaseSearch):
    # API
    ageRestriction: Dict[str, Any]
    cover: Dict[str, Any]
    eng_name: str
    id: int
    model: str
    name: str
    rating: Dict[str, Any]
    releaseDateString: str
    rus_name: str
    shiki_rate: Optional[float]
    site: int
    slug: str
    slug_url: str
    status: Dict[str, Any]
    type: Dict[str, Any]


@define(kw_only=True)
class Ongoing(_SearchOrOngoing, BaseOngoing):
    # API
    ageRestriction: Dict[str, Any]
    cover: Dict[str, Any]
    eng_name: str
    id: int
    model: str
    name: str
    rating: Dict[str, Any]
    releaseDateString: str
    rus_name: str
    shiki_rate: Optional[float]
    site: int
    slug: str
    slug_url: str
    status: Dict[str, Any]
    type: Dict[str, Any]


@define(kw_only=True)
class Anime(BaseAnime):
    title: str
    description: str
    thumbnail: str
    # API
    ageRestriction: Dict[str, Any]
    authors: List[Dict[str, Any]]
    background: Dict[str, Any]
    close_view: int
    cover: Dict[str, Any]
    eng_name: str
    episodes_schedule: List[Any]
    franchise: List[Any]
    genres: List[Dict[str, Any]]
    id: int
    is_licensed: bool
    items_count: Dict[str, Any]
    metadata: Dict[str, Any]
    model: str
    moderated: Dict[str, Any]
    name: str
    otherNames: List[str]
    publisher: List[Dict[str, Any]]
    rating: Dict[str, Any]
    releaseDate: str
    releaseDateString: str
    rus_name: str
    shiki_rate: float
    shikimori_href: str
    site: int
    slug: str
    slug_url: str
    status: Dict[str, Any]
    summary: str
    tags: List[Dict[str, Any]]
    teams: List[Dict[str, Any]]
    time: Dict[str, Any]
    type: Dict[str, Any]
    user: Dict[str, Any]
    views: Dict[str, Any]

    def __str__(self):
        return self.title

    def get_episodes(self) -> List["Episode"]:
        resp = self.http.get("https://api.cdnlibs.org/api/episodes", params={"anime_id": self.slug_url}).json()
        return [
            Episode(num=kw["number"], title=kw["name"] if kw["name"] else "Episode", **kw, **self._kwargs_http)
            for kw in resp["data"]
        ]

    async def a_get_episodes(self) -> List["Episode"]:
        resp = await self.http_async.get(
            "https://api.cdnlibs.org/api/episodes", params={"anime_id": self.slug_url}
        ).json()
        return [
            Episode(num=kw["number"], title=kw["name"] if kw["name"] else "Episode", **kw, **self._kwargs_http)
            for kw in resp["data"]
        ]


@define(kw_only=True)
class Episode(BaseEpisode):
    title: str
    num: str
    # API
    id: int
    model: str
    name: str
    number: str
    number_secondary: str
    season: str
    status: Dict[str, Any]
    anime_id: int
    created_at: str
    item_number: int
    type: str

    def get_sources(self) -> List["Source"]:
        resp = self.http.get(f"https://api.cdnlibs.org/api/episodes/{self.id}").json()
        return [
            Source(
                url=kw["src"] if kw["src"].startswith("http") else f"https:{kw['src']}",
                title=kw["team"]["name"],
                **kw,
                **self._kwargs_http,
            )
            for kw in resp["data"]["players"]
        ]

    async def a_get_sources(self) -> List["Source"]:
        resp = await self.http_async.get(f"https://api.cdnlibs.org/api/episodes/{self.id}").json()
        return [
            Source(
                url=kw["src"] if kw["src"].startswith("http") else f"https:{kw['src']}",
                title=kw["team"]["name"],
                **kw,
                **self._kwargs_http,
            )
            for kw in resp["data"]["players"]
        ]


@define(kw_only=True)
class Source(BaseSource):
    url: str
    title: str
    # API
    id: int
    episode_id: int
    player: str
    translation_type: Dict[str, Any]
    team: Dict[str, Any]
    created_at: str
    views: int
    src: str


if __name__ == "__main__":
    from anicli_api.tools import cli

    cli(Extractor())
