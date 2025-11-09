from typing import TYPE_CHECKING, List, TypedDict

from attrs import define, field

from anicli_api._http import HTTPAsync, HTTPSync
from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.player.base import Video
from anicli_api.source.apis.animelib_org import (
    AnimeliborgAPISync,
    AnimeliborgAPIAsync,
    T_AnimeListItem,
    T_AnimeDetail,
    T_EpisodeListItem,
    T_Player,
)

if TYPE_CHECKING:
    from httpx import AsyncClient, Client


T_KW_APIS = TypedDict("T_KW_APIS", {"sync_api": AnimeliborgAPISync, "async_api": AnimeliborgAPIAsync})

# consts for API requests
# params constants
_SEARCH_ANIME_FIELD_PARAMS = ["rate", "rate_avg", "releaseDate"]
_GET_ANIME_FIELD_PARAMS = [
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
_SITE_ID = [1, 3]


class Extractor(BaseExtractor):
    BASE_URL = "https://api.cdnlibs.org/api/"

    def __init__(self, http_client: "Client" = HTTPSync(), http_async_client: "AsyncClient" = HTTPAsync()):
        super().__init__(http_client=http_client, http_async_client=http_async_client)
        self._sync_api = AnimeliborgAPISync(client=http_client)
        self._async_api = AnimeliborgAPIAsync(client=http_async_client)

    @property
    def sync_api(self) -> AnimeliborgAPISync:
        return self._sync_api

    @property
    def async_api(self) -> AnimeliborgAPIAsync:
        return self._async_api

    @property
    def _kwargs_api(self) -> T_KW_APIS:
        """shortcut for pass API objects arguments in kwargs style"""
        return {"sync_api": self.sync_api, "async_api": self.async_api}

    def search(self, query: str) -> List["Search"]:
        result = self.sync_api.get_anime(fields=_SEARCH_ANIME_FIELD_PARAMS, site_id=_SITE_ID, q=query)
        results = []
        if result.success and result.data:
            for data in result.data["data"]:
                results.append(
                    Search(
                        title=data.get("rus_name", "") or data.get("name", "") or data.get("eng_name", ""),
                        thumbnail=data["cover"]["default"],
                        url=data["slug_url"],  # stub
                        data=data,
                        **self._kwargs_http,
                        **self._kwargs_api,
                    )
                )
        return results

    async def a_search(self, query: str) -> List["Search"]:
        result = await self.async_api.get_anime(fields=_SEARCH_ANIME_FIELD_PARAMS, site_id=_SITE_ID, q=query)
        results = []
        if result.success and result.data:
            for data in result.data["data"]:
                results.append(
                    Search(
                        title=data.get("rus_name", "") or data.get("name", "") or data.get("eng_name", ""),
                        thumbnail=data["cover"]["default"],
                        url=data["slug_url"],  # stub
                        data=data,
                        **self._kwargs_http,
                        **self._kwargs_api,
                    )
                )
        return results

    def ongoing(self) -> List["Ongoing"]:
        result = self.sync_api.get_anime(
            fields=["rate", "rate_avg", "userBookmark"],
            site_id=_SITE_ID,  # magic enum - sorty by ongoings
            status=[1],
            sort_by="last_episode_at",
        )
        results = []
        if result.success and result.data:
            for data in result.data["data"]:
                results.append(
                    Ongoing(
                        title=data.get("rus_name", "") or data.get("name", "") or data.get("eng_name", ""),
                        thumbnail=data["cover"]["default"],
                        url=data["slug_url"],  # stub
                        data=data,
                        **self._kwargs_http,
                        **self._kwargs_api,
                    )
                )
        return results

    async def a_ongoing(self) -> List["Ongoing"]:
        result = await self.async_api.get_anime(
            fields=["rate", "rate_avg", "userBookmark"],
            site_id=_SITE_ID,  # magic enum - sorty by ongoings
            status=[1],
            sort_by="last_episode_at",
        )
        results = []
        if result.success and result.data:
            for data in result.data["data"]:
                results.append(
                    Ongoing(
                        title=data.get("rus_name", "") or data.get("name", "") or data.get("eng_name", ""),
                        thumbnail=data["cover"]["default"],
                        url=data["slug_url"],  # stub
                        data=data,
                        **self._kwargs_http,
                        **self._kwargs_api,
                    )
                )
        return results


class _ApiInstancesMixin:
    _sync_api: AnimeliborgAPISync
    _async_api: AnimeliborgAPIAsync

    @property
    def _kwargs_apis(self) -> T_KW_APIS:
        return {"sync_api": self.sync_api, "async_api": self.async_api}

    @property
    def sync_api(self) -> AnimeliborgAPISync:
        return self._sync_api

    @property
    def async_api(self) -> AnimeliborgAPIAsync:
        return self._async_api


@define(kw_only=True)
class Search(_ApiInstancesMixin, BaseSearch):
    _sync_api: AnimeliborgAPISync = field(alias="sync_api")
    _async_api: AnimeliborgAPIAsync = field(alias="async_api")
    data: T_AnimeListItem

    def get_anime(self) -> "Anime":
        result = self.sync_api.get_anime_by_slug_url(self.data["slug_url"])
        data = result.data["data"]
        return Anime(
            title=self.title,
            thumbnail=data["cover"]["default"],
            # maybe missing key
            description=data.get("summary", ""),
            data=data,
            **self._kwargs_apis,
            **self._kwargs_http,
        )

    async def a_get_anime(self) -> BaseAnime:
        result = await self.async_api.get_anime_by_slug_url(self.data["slug_url"])
        data = result.data["data"]

        return Anime(
            title=self.title,
            thumbnail=data["cover"]["default"],
            description=data.get("summary", ""),
            data=data,
            **self._kwargs_apis,
            **self._kwargs_http,
        )


@define(kw_only=True)
class Ongoing(_ApiInstancesMixin, BaseOngoing):
    _sync_api: AnimeliborgAPISync = field(alias="sync_api")
    _async_api: AnimeliborgAPIAsync = field(alias="async_api")
    data: T_AnimeListItem

    def get_anime(self) -> "Anime":
        result = self.sync_api.get_anime_by_slug_url(self.data["slug_url"])
        data = result.data["data"]
        return Anime(
            title=self.title,
            thumbnail=data["cover"]["default"],
            description=data.get("summary", ""),
            data=data,
            **self._kwargs_apis,
            **self._kwargs_http,
        )

    async def a_get_anime(self) -> "Anime":
        result = await self.async_api.get_anime_by_slug_url(self.data["slug_url"])
        data = result.data["data"]
        return Anime(
            title=self.title,
            thumbnail=data["cover"]["default"],
            description=data.get("summary", ""),
            data=data,
            **self._kwargs_apis,
            **self._kwargs_http,
        )


@define(kw_only=True)
class Anime(_ApiInstancesMixin, BaseAnime):
    _sync_api: AnimeliborgAPISync = field(alias="sync_api")
    _async_api: AnimeliborgAPIAsync = field(alias="async_api")
    data: T_AnimeDetail

    def get_episodes(self) -> List["Episode"]:
        result = self.sync_api.get_episodes(self.data["slug_url"])
        results = []
        if result.success and result.data:
            for data in result.data["data"]:
                results.append(
                    Episode(
                        title=data.get("name", "") or "Episode",  # maybe empty string
                        ordinal=int(data["number"]),
                        data=data,
                        **self._kwargs_http,
                        **self._kwargs_apis,
                    )
                )
        return results

    async def a_get_episodes(self) -> List["Episode"]:
        result = await self.async_api.get_episodes(self.data["slug_url"])
        results = []
        if result.success and result.data:
            for data in result.data["data"]:
                results.append(
                    Episode(
                        title=data.get("name", "") or "Episode",  # maybe empty string
                        ordinal=int(data["number"]),
                        data=data,
                        **self._kwargs_http,
                        **self._kwargs_apis,
                    )
                )
        return results


@define(kw_only=True)
class Episode(_ApiInstancesMixin, BaseEpisode):
    _sync_api: AnimeliborgAPISync = field(alias="sync_api")
    _async_api: AnimeliborgAPIAsync = field(alias="async_api")
    data: T_EpisodeListItem

    def get_sources(self) -> List["Source"]:
        result = self.sync_api.get_episode_by_id(str(self.data["id"]))
        results = []
        for data in result.data["data"]["players"]:
            if data["player"].lower() == "kodik":
                # '//kodik.com/...'
                results.append(
                    Source(
                        title=data["team"]["name"],
                        url="https:" + data["src"],  # stub resolved in ,
                        data=data,
                        **self._kwargs_http,
                        **self._kwargs_apis,
                    )
                )
            elif data["player"].lower() == "animelib":
                # NOTE: not implemented change reserve servers
                # https://api.cdnlibs.org/api/constants?
                # fields[]=videoServers&fields[]=animeDistributionId&fields[]=animeDistributionUrl
                results.append(
                    Source(
                        title=data["team"]["name"],
                        url="https://video1.cdnlibs.org/.%D0%B0s/",  # base url
                        data=data,
                        **self._kwargs_http,
                        **self._kwargs_apis,
                    )
                )
        return results

    async def a_get_sources(self) -> List["Source"]:
        result = await self.async_api.get_episode_by_id(str(self.data["id"]))
        results = []
        for data in result.data["data"]["players"]:
            if data["player"].lower() == "kodik":
                # '//kodik.com/...'
                results.append(
                    Source(
                        title=data["team"]["name"],
                        url="https:" + data["src"],  # stub resolved in ,
                        data=data,
                        **self._kwargs_http,
                        **self._kwargs_apis,
                    )
                )
            elif data["player"].lower() == "animelib":
                # NOTE: not implemented change reserve servers
                # https://api.cdnlibs.org/api/constants?
                # fields[]=videoServers&fields[]=animeDistributionId&fields[]=animeDistributionUrl
                results.append(
                    Source(
                        title=data["team"]["name"],
                        url="https://video1.cdnlibs.org/.%D0%B0s/",  # base url
                        data=data,
                        **self._kwargs_http,
                        **self._kwargs_apis,
                    )
                )
        return results


@define(kw_only=True)
class Source(_ApiInstancesMixin, BaseSource):
    _sync_api: AnimeliborgAPISync = field(alias="sync_api")
    _async_api: AnimeliborgAPIAsync = field(alias="async_api")
    data: T_Player

    def get_videos(self, **httpx_kwargs) -> List[Video]:
        # implemended, run original method
        if self.data["player"].lower() == "kodik":
            return super().get_videos(**httpx_kwargs)  # type: ignore

        elif self.data["player"].lower() == "animelib":
            results = []
            # NOTE: 'video' contains only if ['player'] == "animelib"
            for video in self.data["video"]["quality"]:
                results.append(
                    Video(
                        type="mp4",
                        quality=video["quality"],
                        url=self.url + video["href"],
                        headers={"Referrer": "https://v3.animelib.org", "User-Agent": self.http.headers["User-Agent"]},
                    )
                )
            return results
        return []

    async def a_get_videos(self, **httpx_kwargs) -> List[Video]:
        # implemended, run original method
        if self.data["player"].lower() == "kodik":
            return await super().a_get_videos(**httpx_kwargs)  # type: ignore
        elif self.data["player"].lower() == "animelib":
            results = []
            # NOTE: 'video' contains only if ['player'] == "animelib"
            for video in self.data["video"]["quality"]:
                results.append(
                    Video(
                        type="mp4",
                        quality=video["quality"],
                        url=self.url + video["href"],
                        headers={"Referrer": "https://v3.animelib.org", "User-Agent": self.http.headers["User-Agent"]},
                    )
                )
            return results
        return []


if __name__ == "__main__":
    from anicli_api.tools import cli
    import os

    # allow extract anilib sources if pass auth token
    # you can auth and find token in devtools->XHR->rest-api request
    # headers requests, Authorization key
    # HEADER = {"Authorization": "Bearer ..."}
    # EXTRACTOR = Extractor()
    # EXTRACTOR.http.headers.update(HEADER)
    # cli(EXTRACTOR)
    TOKEN = os.environ.get("ANIMELIB_TOKEN", None)
    ex = Extractor()
    if TOKEN:
        if not TOKEN.startswith("Bearer"):
            TOKEN = f"Bearer {TOKEN}"
        ex.http.headers.update({"Authorization": TOKEN})
    cli(ex)
