"""actual source name - aniliberty:

saved old extractor name for backport support purposes
"""

from __future__ import annotations
from typing import cast, Optional

from attrs import define, field

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.player.base import Video  # direct make this object
from anicli_api.source.parsers.aniliberty_parser import AnilibertyApi

# types
from anicli_api.source.parsers.aniliberty_parser import (
    CatalogReleasesResponseJson,
    CatalogReleaseJson,
    ReleaseDetailJson,
    EpisodeJson,
)


class Extractor(BaseExtractor):
    BASE_URL = "https://aniliberty.top/api/v1"

    def search(self, query: str) -> list["Search"]:
        # https://anilibria.top/api/docs/v1#/Аниме.Каталог
        result = AnilibertyApi.search_catalog(self.http, search=query)
        if not result.is_ok:
            return []
        value = result.value
        value = cast(CatalogReleasesResponseJson, value)
        results = [
            Search(
                title=data["name"]["main"],
                thumbnail=data["poster"]["thumbnail"],
                url="_",
                data=data,
                **self._kwargs_http,
            )
            for data in value["data"]
        ]
        return results

    async def a_search(self, query: str) -> list["Search"]:
        # https://anilibria.top/api/docs/v1#/Аниме.Каталог
        result = await AnilibertyApi.async_search_catalog(self.http_async, search=query)
        if not result.is_ok:
            return []
        value = result.value
        value = cast(CatalogReleasesResponseJson, value)
        results = [
            Search(
                title=data["name"]["main"],
                thumbnail=data["poster"]["thumbnail"],
                url="_",
                data=data,
                **self._kwargs_http,
            )
            for data in value["data"]
        ]
        return results

    def ongoing(self) -> list["Ongoing"]:
        # https://anilibria.top/api/docs/v1#/Аниме.Каталог
        result = AnilibertyApi.ongoing_catalog(self.http)
        if not result.is_ok:
            return []
        value = result.value
        value = cast(CatalogReleasesResponseJson, value)
        ongoings = [
            Ongoing(
                title=data["name"]["main"],
                thumbnail=data["poster"]["thumbnail"],
                url="_",  # STUB
                data=data,
                **self._kwargs_http,
            )
            for data in value["data"]
        ]
        return ongoings

    async def a_ongoing(self) -> list["Ongoing"]:
        # https://anilibria.top/api/docs/v1#/Аниме.Каталог
        result = await AnilibertyApi.async_ongoing_catalog(self.http_async)
        if not result.is_ok:
            return []
        value = result.value
        value = cast(CatalogReleasesResponseJson, value)
        ongoings = [
            Ongoing(
                title=data["name"]["main"],
                thumbnail=data["poster"]["thumbnail"],
                url="_",  # STUB
                data=data,
                **self._kwargs_http,
            )
            for data in value["data"]
        ]
        return ongoings


@define(kw_only=True)
class Search(BaseSearch):
    data: CatalogReleaseJson

    def get_anime(self) -> "Anime":
        return Anime(
            title=self.title,
            thumbnail=self.thumbnail,
            description=self.data["description"],
            data=self.data,
            **self._kwargs_http,
        )

    async def a_get_anime(self) -> "Anime":
        return self.get_anime()


@define(kw_only=True)
class Ongoing(BaseOngoing):
    data: CatalogReleaseJson

    def get_anime(self) -> "Anime":
        return Anime(
            title=self.title,
            thumbnail=self.thumbnail,
            description=self.data["description"],
            data=self.data,
            **self._kwargs_http,
        )

    async def a_get_anime(self) -> "Anime":
        return self.get_anime()


@define(kw_only=True)
class Anime(BaseAnime):
    data: CatalogReleaseJson

    def __str__(self):
        return self.title

    def get_episodes(self) -> list["Episode"]:
        # https://anilibria.top/api/docs/v1#/Аниме.Релизы/1a04f3ab108f6960aacb815ecabe29d2
        release_id = self.data["id"]
        result = AnilibertyApi.get_release(self.http, id=release_id)
        if not result.is_ok:
            return []
        value = result.value
        value = cast(ReleaseDetailJson, value)
        episodes = [
            Episode(
                # swagger schema says, contains string, but can be null
                title=data["name"] or "Episode",
                ordinal=int(data["ordinal"]),
                data=data,
                **self._kwargs_http,
            )
            for data in value["episodes"]
        ]
        return episodes

    async def a_get_episodes(self) -> list["Episode"]:
        # https://anilibria.top/api/docs/v1#/Аниме.Релизы/1a04f3ab108f6960aacb815ecabe29d2
        release_id = self.data["id"]
        result = await AnilibertyApi.async_get_release(self.http_async, id=release_id)
        if not result.is_ok:
            return []
        value = result.value
        value = cast(ReleaseDetailJson, value)
        episodes = [
            Episode(
                # swagger schema says, contains string, but can be null
                title=data["name"] or "Episode",
                ordinal=int(data["ordinal"]),
                data=data,
                **self._kwargs_http,
            )
            for data in value["episodes"]
        ]
        return episodes


@define(kw_only=True)
class Episode(BaseEpisode):
    data: EpisodeJson

    def get_sources(self) -> list["Source"]:
        return [
            Source(
                title="Aniliberty",
                url="_",  # STUB
                hls_480=self.data["hls_480"],
                hls_720=self.data["hls_720"],
                hls_1080=self.data["hls_1080"],
                **self._kwargs_http,
            )
        ]

    async def a_get_sources(self) -> list["Source"]:
        return self.get_sources()


@define(kw_only=True)
class Source(BaseSource):
    url: str
    title: str

    # actual swagger model allow null
    _hls_480: Optional[str] = field(alias="hls_480")
    _hls_720: Optional[str] = field(alias="hls_720")
    _hls_1080: Optional[str] = field(alias="hls_1080")

    def get_videos(self, **_) -> list["Video"]:
        videos = []
        if self._hls_480:
            videos.append(Video(type="m3u8", quality=480, url=self._hls_480))

        if self._hls_720:
            videos.append(Video(type="m3u8", quality=720, url=self._hls_720))

        if self._hls_1080:
            videos.append(Video(type="m3u8", quality=1080, url=self._hls_1080))
        return videos

    async def a_get_videos(self, **_) -> list["Video"]:
        return self.get_videos()


if __name__ == "__main__":
    from anicli_api.tools import cli

    cli(Extractor())
