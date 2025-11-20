from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import define, field

from anicli_api.typing import TypedDict
from anicli_api._http import HTTPAsync, HTTPSync
from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.source.apis.yummy_anime import (
    YummyAnimeAPIAsync,
    YummyAnimeAPISync,
    T_AnimeSimple,
    T_ScheduleAnime,
    T_Video,
)

if TYPE_CHECKING:
    from httpx import AsyncClient, Client


T_KW_APIS = TypedDict("T_KW_APIS", {"sync_api": YummyAnimeAPISync, "async_api": YummyAnimeAPIAsync})


class Extractor(BaseExtractor):
    BASE_URL = "https://site.yummyani.me"

    def __init__(self, http_client: "Client" = HTTPSync(), http_async_client: "AsyncClient" = HTTPAsync()):
        super().__init__(http_client=http_client, http_async_client=http_async_client)
        self._sync_api = YummyAnimeAPISync(client=http_client)
        self._async_api = YummyAnimeAPIAsync(client=http_async_client)

    @property
    def sync_api(self) -> YummyAnimeAPISync:
        return self._sync_api

    @property
    def async_api(self) -> YummyAnimeAPIAsync:
        return self._async_api

    @property
    def _kwargs_api(self) -> T_KW_APIS:
        return {"sync_api": self._sync_api, "async_api": self._async_api}

    def search(self, query: str) -> list["Search"]:
        # https://yummy-anime.ru/api/swagger#/Anime/get_anime
        result = self.sync_api.filter_anime(q=query, offset=0, limit=20)
        results = []
        if result.success and result.data:
            for data in result.data["response"]:
                results.append(
                    Search(
                        data=data,
                        title=data["title"],
                        thumbnail=data["poster"]["medium"],
                        url=self.BASE_URL + "/catalog/item/" + data["anime_url"],
                        **self._kwargs_http,
                        **self._kwargs_api,
                    )
                )

        return results

    async def a_search(self, query: str) -> list["Search"]:
        result = await self.async_api.filter_anime(q=query, offset=0, limit=20)
        results = []
        if result.success and result.data:
            for data in result.data["response"]:
                results.append(
                    Search(
                        data=data,
                        title=data["title"],
                        thumbnail=data["poster"]["medium"],
                        url=self.BASE_URL + "/catalog/item/" + data["anime_url"],
                        **self._kwargs_http,
                        **self._kwargs_api,
                    )
                )
        return results

    def ongoing(self) -> list["Ongoing"]:
        # too many output (100 items)
        # https://yummy-anime.ru/api/swagger#/Anime/get_anime_schedule
        result = self.sync_api.get_anime_schedule()
        results = []
        if result.success and result.data:
            for data in result.data["response"]:
                results.append(
                    Ongoing(
                        data=data,
                        title=data["title"],
                        thumbnail=data["poster"]["medium"],
                        url=self.BASE_URL + "/catalog/item/" + data["anime_url"],
                        **self._kwargs_http,
                        **self._kwargs_api,
                    )
                )
        return results

    async def a_ongoing(self) -> list["Ongoing"]:
        result = await self.async_api.get_anime_schedule()
        results = []
        if result.success and result.data:
            for data in result.data["response"]:
                results.append(
                    Ongoing(
                        data=data,
                        title=data["title"],
                        thumbnail=data["poster"]["medium"],
                        url=self.BASE_URL + "/catalog/item/" + data["anime_url"],
                        **self._kwargs_http,
                        **self._kwargs_api,
                    )
                )
        return results


class _ApiInstancesMixin:
    _sync_api: YummyAnimeAPISync
    _async_api: YummyAnimeAPIAsync

    @property
    def _kwargs_apis(self) -> T_KW_APIS:
        return {"sync_api": self.sync_api, "async_api": self.async_api}

    @property
    def sync_api(self) -> YummyAnimeAPISync:
        return self._sync_api

    @property
    def async_api(self) -> YummyAnimeAPIAsync:
        return self._async_api


@define(kw_only=True)
class Search(_ApiInstancesMixin, BaseSearch):
    data: T_AnimeSimple
    _sync_api: YummyAnimeAPISync = field(alias="sync_api")
    _async_api: YummyAnimeAPIAsync = field(alias="async_api")

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
    data: T_ScheduleAnime
    _sync_api: YummyAnimeAPISync = field(alias="sync_api")
    _async_api: YummyAnimeAPIAsync = field(alias="async_api")

    def get_anime(self) -> "Anime":
        # transform to corrent object
        result = self.sync_api.filter_anime(ids=[self.data["anime_id"]])
        data = result.data["response"][0]
        return Anime(
            title=data["title"],
            thumbnail=data["poster"]["medium"],
            description=data["description"],
            data=data,
            **self._kwargs_http,
            **self._kwargs_apis,
        )

    async def a_get_anime(self) -> "Anime":
        result = await self.async_api.filter_anime(ids=[self.data["anime_id"]])
        data = result.data["response"][0]
        return Anime(
            title=data["title"],
            thumbnail=data["poster"]["medium"],
            description=data["description"],
            data=data,
            **self._kwargs_http,
            **self._kwargs_apis,
        )


@define(kw_only=True)
class Anime(_ApiInstancesMixin, BaseAnime):
    data: T_AnimeSimple
    _sync_api: YummyAnimeAPISync = field(alias="sync_api")
    _async_api: YummyAnimeAPIAsync = field(alias="async_api")

    def get_episodes(self) -> list["Episode"]:
        video_data = self.sync_api.get_anime_videos(id=self.data["anime_id"]).data["response"]
        mapping_videos = {}
        for video in video_data:
            # not implemented player (too complex reverse)
            if "alloha" in video["iframe_url"]:
                continue
            if not mapping_videos.get(video["number"]):
                mapping_videos[video["number"]] = []
            mapping_videos[video["number"]].append(video)

        results = []
        for num, videos in mapping_videos.items():
            results.append(
                Episode(ordinal=int(num), title="Episode", data=videos, **self._kwargs_http, **self._kwargs_apis)
            )
        return results

    async def a_get_episodes(self) -> list["Episode"]:
        video_data = (await self.async_api.get_anime_videos(id=self.data["anime_id"])).data["response"]
        mapping_videos = {}
        for video in video_data:
            # not implemented player (too complex reverse)
            if "alloha" in video["iframe_url"]:
                continue
            if not mapping_videos.get(video["number"]):
                mapping_videos[video["number"]] = []
            mapping_videos[video["number"]].append(video)

        results = []
        for num, videos in mapping_videos.items():
            results.append(
                Episode(ordinal=int(num), title="Episode", data=videos, **self._kwargs_http, **self._kwargs_apis)
            )
        return results


@define(kw_only=True)
class Episode(_ApiInstancesMixin, BaseEpisode):
    _sync_api: YummyAnimeAPISync = field(alias="sync_api")
    _async_api: YummyAnimeAPIAsync = field(alias="async_api")
    data: list[T_Video]

    def get_sources(self) -> list["Source"]:
        results = []
        for video in self.data:
            results.append(
                Source(
                    title=video["data"]["dubbing"],
                    url="https:" + video["iframe_url"] if video["iframe_url"].startswith("//") else video["iframe_url"],
                    **self._kwargs_http,
                    **self._kwargs_apis,
                )
            )
        return results

    async def a_get_sources(self) -> list["Source"]:
        return self.get_sources()


@define(kw_only=True)
class Source(_ApiInstancesMixin, BaseSource):
    _sync_api: YummyAnimeAPISync = field(alias="sync_api")
    _async_api: YummyAnimeAPIAsync = field(alias="async_api")


if __name__ == "__main__":
    from anicli_api.tools import cli

    cli(Extractor())
