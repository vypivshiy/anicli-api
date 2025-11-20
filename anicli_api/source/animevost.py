from __future__ import annotations

from typing import TYPE_CHECKING
from attrs import define, field

from anicli_api.typing import TypedDict
from anicli_api._http import HTTPAsync, HTTPSync
from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.player.base import Video  # direct make this object
from anicli_api.source.apis.animevost import AnimeVostSync, AnimeVostAsync, T_Item, T_PlaylistResponse

if TYPE_CHECKING:
    from httpx import AsyncClient, Client

T_KW_APIS = TypedDict("T_KW_APIS", {"sync_api": AnimeVostSync, "async_api": AnimeVostAsync})


class Extractor(BaseExtractor):
    BASE_URL = "https://api.animevost.org/v1/"

    def __init__(self, http_client: "Client" = HTTPSync(), http_async_client: "AsyncClient" = HTTPAsync()):
        super().__init__(http_client=http_client, http_async_client=http_async_client)
        self._sync_api = AnimeVostSync(client=self.http, raise_on_error=False)
        self._async_api = AnimeVostAsync(client=self.http_async, raise_on_error=False)

    @property
    def sync_api(self) -> AnimeVostSync:
        return self._sync_api

    @property
    def async_api(self) -> AnimeVostAsync:
        return self._async_api

    @property
    def _kwargs_api(self) -> T_KW_APIS:
        """shortcut for pass API objects arguments in kwargs style"""
        return {"sync_api": self.sync_api, "async_api": self.async_api}

    def search(self, query: str) -> list["Search"]:
        result = self.sync_api.search(query)
        # not founded, not raise exception
        if result.status_code == 404:
            return []

        result.raise_for_status()

        results = []
        if result.success and result.data:
            for data in result.data["data"]:
                results.append(
                    Search(
                        title=data["title"],
                        thumbnail=data["urlImagePreview"],
                        url="_",  # STUB,
                        data=data,
                        **self._kwargs_http,
                        **self._kwargs_api,
                    )
                )
        return results

    async def a_search(self, query: str) -> list["Search"]:
        result = await self.async_api.search(query)
        # not founded, not raise exception
        if result.status_code == 404:
            return []

        result.raise_for_status()

        results = []
        if result.success and result.data:
            for data in result.data["data"]:
                results.append(
                    Search(
                        title=data["title"],
                        thumbnail=data["urlImagePreview"],
                        url="_",  # STUB,
                        data=data,
                        **self._kwargs_http,
                        **self._kwargs_api,
                    )
                )
        return results

    def ongoing(self) -> list["Ongoing"]:
        result = self.sync_api.last(page=1, quantity=20)

        result.raise_for_status()

        results = []
        if result.success and result.data:
            for data in result.data["data"]:
                results.append(
                    Search(
                        title=data["title"],
                        thumbnail=data["urlImagePreview"],
                        url="_",  # STUB,
                        data=data,
                        **self._kwargs_http,
                        **self._kwargs_api,
                    )
                )
        return results

    async def a_ongoing(self) -> list["Ongoing"]:
        result = await self.async_api.last(page=1, quantity=20)

        result.raise_for_status()

        results = []
        if result.success and result.data:
            for data in result.data["data"]:
                results.append(
                    Search(
                        title=data["title"],
                        thumbnail=data["urlImagePreview"],
                        url="_",  # STUB,
                        data=data,
                        **self._kwargs_http,
                        **self._kwargs_api,
                    )
                )
        return results


class _ApiInstancesMixin:
    _sync_api: AnimeVostSync
    _async_api: AnimeVostAsync

    @property
    def _kwargs_apis(self) -> T_KW_APIS:
        return {"sync_api": self.sync_api, "async_api": self.async_api}

    @property
    def sync_api(self) -> AnimeVostSync:
        return self._sync_api

    @property
    def async_api(self) -> AnimeVostAsync:
        return self._async_api


@define(kw_only=True)
class Search(_ApiInstancesMixin, BaseSearch):
    data: T_Item
    _sync_api: AnimeVostSync = field(alias="sync_api")
    _async_api: AnimeVostAsync = field(alias="async_api")

    def get_anime(self) -> "Anime":
        return Anime(
            title=self.data["title"],
            description=self.data["description"],
            thumbnail=self.data["urlImagePreview"],
            data=self.data,
            **self._kwargs_http,
            **self._kwargs_apis,
        )

    async def a_get_anime(self) -> "Anime":
        return self.get_anime()


@define(kw_only=True)
class Ongoing(_ApiInstancesMixin, BaseOngoing):
    data: T_Item
    _sync_api: AnimeVostSync = field(alias="sync_api")
    _async_api: AnimeVostAsync = field(alias="async_api")

    def get_anime(self) -> "Anime":
        return Anime(
            title=self.data["title"],
            description=self.data["description"],
            thumbnail=self.data["urlImagePreview"],
            data=self.data,
            **self._kwargs_http,
            **self._kwargs_apis,
        )

    async def a_get_anime(self) -> "Anime":
        return self.get_anime()


@define(kw_only=True)
class Anime(_ApiInstancesMixin, BaseAnime):
    data: T_Item
    _sync_api: AnimeVostSync = field(alias="sync_api")
    _async_api: AnimeVostAsync = field(alias="async_api")

    async def a_get_episodes(self) -> list["Episode"]:
        result = await self._async_api.playlist(str(self.data["id"]))
        result.raise_for_status()

        # wrong id, skip
        if isinstance(result.data, dict) and result.data.get("error"):
            return []

        results = []
        if result.success and isinstance(result.data, list):
            for i, data in enumerate(result.data, 1):
                results.append(
                    Episode(title=data["name"], ordinal=i, data=data, **self._kwargs_http, **self._kwargs_apis)
                )

        return results

    def get_episodes(self) -> list["Episode"]:
        result = self._sync_api.playlist(str(self.data["id"]))
        result.raise_for_status()

        # wrong id, skip
        if isinstance(result.data, dict) and result.data.get("error"):
            return []

        results = []
        if result.success and isinstance(result.data, list):
            for i, data in enumerate(result.data, 1):
                results.append(
                    Episode(title=data["name"], ordinal=i, data=data, **self._kwargs_http, **self._kwargs_apis)
                )

        return results


@define(kw_only=True)
class Episode(_ApiInstancesMixin, BaseEpisode):
    # video meta
    data: T_PlaylistResponse
    _sync_api: AnimeVostSync = field(alias="sync_api")
    _async_api: AnimeVostAsync = field(alias="async_api")

    def get_sources(self) -> list["Source"]:
        return [
            Source(
                title="Animevost",
                url="https://api.animevost.org",
                hd=self.data["hd"],
                std=self.data["std"],
                **self._kwargs_http,
                **self._kwargs_apis,
            )
        ]

    async def a_get_sources(self) -> list["Source"]:
        return self.get_sources()

    def __str__(self):
        return self.title


@define(kw_only=True)
class Source(_ApiInstancesMixin, BaseSource):
    _hd: str = field(alias="hd")
    _std: str = field(alias="std")
    _sync_api: AnimeVostSync = field(alias="sync_api")
    _async_api: AnimeVostAsync = field(alias="async_api")

    def get_videos(self, **_) -> list[Video]:
        return [
            Video(type="mp4", quality=480, url=self._std),
            Video(type="mp4", quality=720, url=self._hd),
        ]

    async def a_get_videos(self, **_) -> list[Video]:
        return self.get_videos()


if __name__ == "__main__":
    from anicli_api.tools.dummy_cli import cli

    cli(Extractor())
