"""actual source name - aniliberty:

saved old extractor name for backport support purposes
"""

from typing import TYPE_CHECKING, List, Optional, TypedDict

from attrs import define, field

from anicli_api._http import HTTPAsync, HTTPSync
from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.player.base import Video  # direct make this object
from anicli_api.source.apis.aniliberty import (
    AniLibertySync,
    AniLibertyAsync,
    T_ModelsAnimeReleasesV1Release,
    T_ModelsAnimeReleasesV1ReleaseEpisode,
)

if TYPE_CHECKING:
    from httpx import AsyncClient, Client


T_KW_APIS = TypedDict("T_KW_APIS", {"sync_api": AniLibertySync, "async_api": AniLibertyAsync})


class Extractor(BaseExtractor):
    BASE_URL = "https://api.anilibria.tv/v3/"

    def __init__(self, http_client: "Client" = HTTPSync(), http_async_client: "AsyncClient" = HTTPAsync()):
        super().__init__(http_client=http_client, http_async_client=http_async_client)
        self._sync_api = AniLibertySync(client=self.http, raise_on_error=True)
        self._async_api = AniLibertyAsync(client=self.http_async, raise_on_error=True)

    @property
    def sync_api(self) -> AniLibertySync:
        return self._sync_api

    @property
    def async_api(self) -> AniLibertyAsync:
        return self._async_api

    @property
    def _kwargs_api(self) -> T_KW_APIS:
        """shortcut for pass API objects arguments in kwargs style"""
        return {"sync_api": self.sync_api, "async_api": self.async_api}

    def search(self, query: str) -> List["Search"]:
        # https://anilibria.top/api/docs/v1#/Аниме.Каталог
        result = self.sync_api.get_anime_catalog_releases(search=query)
        searches = []
        if result.success and result.data:
            for data in result.data["data"]:
                searches.append(
                    Search(
                        title=data["name"]["main"],
                        thumbnail=data["poster"]["thumbnail"],
                        url="_",  # STUB
                        data=data,
                        **self._kwargs_api,
                        **self._kwargs_http,
                    )
                )
        return searches

    async def a_search(self, query: str) -> List["Search"]:
        # https://anilibria.top/api/docs/v1#/Аниме.Каталог
        result = await self.async_api.get_anime_catalog_releases(search=query)
        searches = []
        if result.success and result.data:
            for data in result.data["data"]:
                searches.append(
                    Search(
                        title=data["name"]["main"],
                        thumbnail=data["poster"]["thumbnail"],
                        url="_",  # STUB
                        data=data,
                        **self._kwargs_api,
                        **self._kwargs_http,
                    )
                )
        return searches

    def ongoing(self) -> List["Ongoing"]:
        # https://anilibria.top/api/docs/v1#/Аниме.Каталог
        result = self.sync_api.get_anime_catalog_releases()
        ongoings = []
        if result.success and result.data:
            for data in result.data["data"]:
                ongoings.append(
                    Ongoing(
                        title=data["name"]["main"],
                        thumbnail=data["poster"]["thumbnail"],
                        url="_",  # STUB
                        data=data,
                        **self._kwargs_api,
                        **self._kwargs_http,
                    )
                )
        return ongoings

    async def a_ongoing(self) -> List["Ongoing"]:
        # https://anilibria.top/api/docs/v1#/Аниме.Каталог
        result = await self.async_api.get_anime_catalog_releases()
        ongoings = []
        if result.success and result.data:
            for data in result.data["data"]:
                ongoings.append(
                    Ongoing(
                        title=data["name"]["main"],
                        thumbnail=data["poster"]["thumbnail"],
                        url="_",  # STUB
                        data=data,
                        **self._kwargs_api,
                        **self._kwargs_http,
                    )
                )
        return ongoings


class _ApiInstancesMixin:
    _sync_api: AniLibertySync
    _async_api: AniLibertyAsync

    @property
    def _kwargs_apis(self) -> T_KW_APIS:
        return {"sync_api": self.sync_api, "async_api": self.async_api}

    @property
    def sync_api(self) -> AniLibertySync:
        return self._sync_api

    @property
    def async_api(self) -> AniLibertyAsync:
        return self._async_api


@define(kw_only=True)
class Search(_ApiInstancesMixin, BaseSearch):
    data: T_ModelsAnimeReleasesV1Release
    _sync_api: AniLibertySync = field(alias="sync_api")
    _async_api: AniLibertyAsync = field(alias="async_api")

    def get_anime(self) -> "Anime":
        return Anime(
            title=self.title,
            thumbnail=self.thumbnail,
            description=self.data["description"],
            data=self.data,
            **self._kwargs_http,
            **self._kwargs_apis,
        )

    async def a_get_anime(self) -> "Anime":
        return self.get_anime()


@define(kw_only=True)
class Ongoing(_ApiInstancesMixin, BaseOngoing):
    data: T_ModelsAnimeReleasesV1Release
    _sync_api: AniLibertySync = field(alias="sync_api")
    _async_api: AniLibertyAsync = field(alias="async_api")

    def get_anime(self) -> "Anime":
        return Anime(
            title=self.title,
            thumbnail=self.thumbnail,
            description=self.data["description"],
            data=self.data,
            **self._kwargs_http,
            **self._kwargs_apis,
        )

    async def a_get_anime(self) -> "Anime":
        return self.get_anime()


@define(kw_only=True)
class Anime(_ApiInstancesMixin, BaseAnime):
    data: T_ModelsAnimeReleasesV1Release
    _sync_api: AniLibertySync = field(alias="sync_api")
    _async_api: AniLibertyAsync = field(alias="async_api")

    def __str__(self):
        return self.title

    def get_episodes(self) -> List["Episode"]:
        # https://anilibria.top/api/docs/v1#/Аниме.Релизы/1a04f3ab108f6960aacb815ecabe29d2
        release_id = self.data["id"]
        result = self.sync_api.get_anime_release(id_or_alias=str(release_id), include="id,episodes")
        episodes = []
        if result.success and result.data:
            for data in result.data["episodes"]:
                episodes.append(
                    Episode(
                        # swagger schema says, contains string, but can be null
                        title=data["name"] or "Episode",
                        ordinal=int(data["ordinal"]),
                        data=data,
                        **self._kwargs_http,
                        **self._kwargs_apis,
                    )
                )
        return episodes

    async def a_get_episodes(self) -> List["Episode"]:
        # https://anilibria.top/api/docs/v1#/Аниме.Релизы/1a04f3ab108f6960aacb815ecabe29d2
        release_id = self.data["id"]
        result = await self.async_api.get_anime_release(id_or_alias=str(release_id), include="id,episodes")
        episodes = []
        if result.success and result.data:
            for data in result.data["episodes"]:
                episodes.append(
                    Episode(
                        title=data["name"],
                        ordinal=int(data["ordinal"]),
                        data=data,
                        **self._kwargs_http,
                        **self._kwargs_apis,
                    )
                )
        return episodes


@define(kw_only=True)
class Episode(_ApiInstancesMixin, BaseEpisode):
    data: T_ModelsAnimeReleasesV1ReleaseEpisode
    _sync_api: AniLibertySync = field(alias="sync_api")
    _async_api: AniLibertyAsync = field(alias="async_api")

    def get_sources(self) -> List["Source"]:
        return [
            Source(
                title="Aniliberty",
                url="_",  # STUB
                hls_480=self.data["hls_480"],
                hls_720=self.data["hls_720"],
                hls_1080=self.data["hls_1080"],
                **self._kwargs_http,
                **self._kwargs_apis,
            )
        ]

    async def a_get_sources(self) -> List["Source"]:
        return self.get_sources()


@define(kw_only=True)
class Source(_ApiInstancesMixin, BaseSource):
    url: str
    title: str

    # actual swagger model allow null
    _hls_480: Optional[str] = field(alias="hls_480")
    _hls_720: Optional[str] = field(alias="hls_720")
    _hls_1080: Optional[str] = field(alias="hls_1080")

    _sync_api: AniLibertySync = field(alias="sync_api")
    _async_api: AniLibertyAsync = field(alias="async_api")

    def get_videos(self, **_) -> List["Video"]:
        videos = []
        if self._hls_480:
            videos.append(Video(type="m3u8", quality=480, url=self._hls_480))

        if self._hls_720:
            videos.append(Video(type="m3u8", quality=720, url=self._hls_720))

        if self._hls_1080:
            videos.append(Video(type="m3u8", quality=1080, url=self._hls_1080))
        return videos

    async def a_get_videos(self, **_) -> List["Video"]:
        return self.get_videos()


if __name__ == "__main__":
    from anicli_api.tools import cli

    cli(Extractor())
