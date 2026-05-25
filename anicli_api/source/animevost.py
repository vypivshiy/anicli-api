from __future__ import annotations
from typing import List, cast

from attrs import define, field

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.player.base import Video  # direct make this object
from anicli_api.source.parsers.animevost_parser import AnimeVostAPI, PlaylistResponseJson, SearchResponseJson, ItemJson


class Extractor(BaseExtractor):
    BASE_URL = "https://api.animevost.org/v1/"

    def search(self, query: str) -> list["Search"]:
        result = AnimeVostAPI.search(self.http, query=query)
        if not result.is_ok:
            # TODO: handle errors
            return []
        value = result.value
        value = cast(SearchResponseJson, value)
        results = [
            Search(
                title=data["title"],
                thumbnail=data["urlImagePreview"],
                url="_",  # stub,
                data=data,
                **self._kwargs_http,
            )
            for data in value["data"]
        ]
        return results

    async def a_search(self, query: str) -> list["Search"]:
        result = await AnimeVostAPI.async_search(self.http_async, query=query)
        if not result.is_ok:
            # TODO: handle errors
            return []
        value = result.value
        value = cast(SearchResponseJson, value)
        results = [
            Search(
                title=data["title"],
                thumbnail=data["urlImagePreview"],
                url="_",  # stub,
                data=data,
                **self._kwargs_http,
            )
            for data in value["data"]
        ]
        return results

    def ongoing(self) -> list["Ongoing"]:
        # hardcoded values: get last 20 ongoings
        result = AnimeVostAPI.last(self.http, page=1, quantity=20)
        if not result.is_ok:
            # TODO: handle errors
            return []
        value = result.value
        value = cast(SearchResponseJson, value)
        results = [
            Ongoing(
                title=data["title"],
                thumbnail=data["urlImagePreview"],
                url="_",  # stub,
                data=data,
                **self._kwargs_http,
            )
            for data in value["data"]
        ]
        return results

    async def a_ongoing(self) -> list["Ongoing"]:
        result = await AnimeVostAPI.async_last(self.http_async, page=1, quantity=20)
        if not result.is_ok:
            # TODO: handle errors
            return []
        value = result.value
        value = cast(SearchResponseJson, value)
        results = [
            Ongoing(
                title=data["title"],
                thumbnail=data["urlImagePreview"],
                url="_",  # stub,
                data=data,
                **self._kwargs_http,
            )
            for data in value["data"]
        ]
        return results


@define(kw_only=True)
class Search(BaseSearch):
    data: ItemJson

    def get_anime(self) -> "Anime":
        return Anime(
            title=self.data["title"],
            description=self.data["description"],
            thumbnail=self.data["urlImagePreview"],
            data=self.data,
            **self._kwargs_http,
        )

    async def a_get_anime(self) -> "Anime":
        return self.get_anime()


@define(kw_only=True)
class Ongoing(BaseOngoing):
    data: ItemJson

    def get_anime(self) -> "Anime":
        return Anime(
            title=self.data["title"],
            description=self.data["description"],
            thumbnail=self.data["urlImagePreview"],
            data=self.data,
            **self._kwargs_http,
        )

    async def a_get_anime(self) -> "Anime":
        return self.get_anime()


@define(kw_only=True)
class Anime(BaseAnime):
    data: ItemJson

    async def a_get_episodes(self) -> list["Episode"]:
        result = await AnimeVostAPI.async_playlist(self.http_async, id=self.data["id"])
        if not result.is_ok:
            # TODO: handle errors
            return []
        value = result.value
        value = cast(List[PlaylistResponseJson], value)
        results = [
            Episode(title=data["name"], ordinal=i, data=data, **self._kwargs_http) for i, data in enumerate(value, 1)
        ]
        return results

    def get_episodes(self) -> list["Episode"]:
        result = AnimeVostAPI.playlist(self.http, id=self.data["id"])
        if not result.is_ok:
            # TODO: handle errors
            return []
        value = result.value
        value = cast(List[PlaylistResponseJson], value)
        results = [
            Episode(title=data["name"], ordinal=i, data=data, **self._kwargs_http) for i, data in enumerate(value, 1)
        ]
        return results


@define(kw_only=True)
class Episode(BaseEpisode):
    # video meta
    data: PlaylistResponseJson

    def get_sources(self) -> list["Source"]:
        return [
            Source(
                title="Animevost",
                url="https://api.animevost.org",
                hd=self.data["hd"],
                std=self.data["std"],
                **self._kwargs_http,
            )
        ]

    async def a_get_sources(self) -> list["Source"]:
        return self.get_sources()

    def __str__(self):
        return self.title


@define(kw_only=True)
class Source(BaseSource):
    _hd: str = field(alias="hd")
    _std: str = field(alias="std")

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
