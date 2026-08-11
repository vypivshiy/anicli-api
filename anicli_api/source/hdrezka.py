from __future__ import annotations

import logging
from typing import Literal, TypedDict, Union, cast
from time import time
import re

from attr import field, define
from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.source.parsers.hdrezka_parser import PageAnime, PageOngoing, PageSearch, HdrezkaCdnSeriesAPI

# types
from anicli_api.source.parsers.hdrezka_parser import EpisodeType, PageAnimeType, HdrezkaCdnResponseJson
from anicli_api.player.base import Video

logger = logging.getLogger("anicli-api")


# API payload types. NOTE: hdrezka's CDN endpoint expects every form-field as
# string, even numeric ids (parser yields int) -> caller casts to str.
class HdrezkaApiPayloadSeries(TypedDict):
    id: str
    translator_id: str
    season: str
    episode: str
    favs: str


class HdrezkaApiPayloadMovie(TypedDict):
    id: str
    translator_id: str
    favs: str


class Extractor(BaseExtractor):
    BASE_URL = "https://hdrezka-home.tv"

    def search(self, query: str) -> list["Search"]:
        result = PageSearch.fetch(self.http, query=query).parse()
        return [
            Search(
                title=f"{data['title']} {data['season']}",
                url=data["url"],
                thumbnail=data["thumbnail"],
                **self._kwargs_http,
            )
            for data in result
        ]

    async def a_search(self, query: str) -> list["Search"]:
        result = (await PageSearch.async_fetch(self.http_async, query=query)).parse()
        return [
            Search(
                title=f"{data['title']} {data['season']}",
                url=data["url"],
                thumbnail=data["thumbnail"],
                **self._kwargs_http,
            )
            for data in result
        ]

    def ongoing(self) -> list["Ongoing"]:
        result = PageOngoing.fetch(self.http).parse()
        return [
            Ongoing(
                title=f"{data['title']} {data['season']}",
                url=data["url"],
                thumbnail=data["thumbnail"],
                **self._kwargs_http,
            )
            for data in result
        ]

    async def a_ongoing(self) -> list["Ongoing"]:
        result = (await PageOngoing.async_fetch(self.http_async)).parse()
        return [
            Ongoing(
                title=f"{data['title']} {data['season']}",
                url=data["url"],
                thumbnail=data["thumbnail"],
                **self._kwargs_http,
            )
            for data in result
        ]


@define(kw_only=True)
class Search(BaseSearch):
    def get_anime(self) -> "Anime":
        data = PageAnime.fetch_from_url(self.http, anime_url=self.url).parse()
        return Anime(
            title=data["title"],
            thumbnail=data["thumbnail"],
            description=data["description"],
            data=data,
            url=Extractor.BASE_URL,
            **self._kwargs_http,
        )

    async def a_get_anime(self) -> "Anime":
        data = (await PageAnime.async_fetch_from_url(self.http_async, anime_url=self.url)).parse()
        return Anime(
            title=data["title"],
            thumbnail=data["thumbnail"],
            description=data["description"],
            data=data,
            url=Extractor.BASE_URL,
            **self._kwargs_http,
        )


@define(kw_only=True)
class Ongoing(BaseOngoing):
    def get_anime(self) -> "Anime":
        data = PageAnime.fetch_from_url(self.http, anime_url=self.url).parse()
        return Anime(
            title=data["title"],
            thumbnail=data["thumbnail"],
            description=data["description"],
            data=data,
            url=Extractor.BASE_URL,
            **self._kwargs_http,
        )

    async def a_get_anime(self) -> "Anime":
        data = (await PageAnime.async_fetch_from_url(self.http_async, anime_url=self.url)).parse()
        return Anime(
            title=data["title"],
            thumbnail=data["thumbnail"],
            description=data["description"],
            data=data,
            url=Extractor.BASE_URL,
            **self._kwargs_http,
        )


@define(kw_only=True)
class Anime(BaseAnime):
    data: PageAnimeType
    _url: str = field(alias="url")

    # note: lazy create instances: every episode required send API request
    def get_episodes(self) -> list["Episode"]:
        if self.data["episode_list"]:
            return [
                Episode(title=e["title"], data=self.data, data_episode=e, ordinal=i, **self._kwargs_http)
                for i, e in enumerate(self.data["episode_list"])
            ]
        # movie: no episode_list, synthesize single fake episode
        return [
            Episode(
                title=self.data["title"],
                data=self.data,
                data_episode={
                    "data_id": self.data["id"],
                    "data_season_id": 0,
                    "data_episode_id": 0,
                    "title": self.data["title"],
                },
                is_movie=True,
                ordinal=0,
                **self._kwargs_http,
            )
        ]

    async def a_get_episodes(self) -> list["Episode"]:
        return self.get_episodes()


@define(kw_only=True)
class Episode(BaseEpisode):
    data: PageAnimeType
    data_episode: EpisodeType
    is_movie: bool = False

    def get_sources(self) -> list["Source"]:
        if self.is_movie:
            return self._get_movie_sources()
        return self._get_series_sources()

    def _get_movie_sources(self) -> list["Source"]:
        if not self.data["translation_list"]:
            return [
                Source(
                    title="hdrezka",
                    url=Extractor.BASE_URL,
                    is_movie=True,
                    api_payload={
                        "id": str(self.data["id"]),
                        "translator_id": self.data["translation_id"],
                        "favs": self.data["favs"],
                    },
                    **self._kwargs_http,
                )
            ]
        return [
            Source(
                title=f"{translation['title']}",
                url=Extractor.BASE_URL,
                is_movie=True,
                api_payload={
                    "id": str(self.data["id"]),
                    "translator_id": translation["data_translator_id"],
                    "favs": self.data["favs"],
                },
                **self._kwargs_http,
            )
            for translation in self.data["translation_list"]
        ]

    def _get_series_sources(self) -> list["Source"]:
        # single translation option allowed
        if not self.data["translation_list"]:
            return [
                Source(
                    title="hdrezka",
                    url=Extractor.BASE_URL,
                    api_payload={
                        "id": str(self.data_episode["data_id"]),
                        "translator_id": self.data["translation_id"],
                        "season": str(self.data_episode["data_season_id"]),
                        "favs": self.data["favs"],
                        "episode": str(self.data_episode["data_episode_id"]),
                    },
                    **self._kwargs_http,
                )
            ]

        sources = [
            Source(
                title=f"{translation['title']}",
                url=Extractor.BASE_URL,  # stub, real url generated in Source object
                api_payload={
                    "id": str(self.data_episode["data_id"]),
                    "translator_id": translation["data_translator_id"],
                    "season": str(self.data_episode["data_season_id"]),
                    "favs": self.data["favs"],
                    "episode": str(self.data_episode["data_episode_id"]),
                },
                **self._kwargs_http,
            )
            for translation in self.data["translation_list"]
        ]
        return sources

    async def a_get_sources(self) -> list["Source"]:
        return self.get_sources()


@define(kw_only=True)
class Source(BaseSource):
    _api_payload: Union[HdrezkaApiPayloadSeries, HdrezkaApiPayloadMovie] = field(alias="api_payload")
    is_movie: bool = False

    def _parse_videos(self, raw_urls: str) -> list["Video"]:
        videos: list[Video] = []
        for part in raw_urls.split(","):
            # item signature:
            # "[{int}p (Ultra)?]https://...manifest.m3u8 or https://...mp4"
            match = re.search(r"\[.*?(\d+).*?\]", part)
            if not match:
                continue
            quality = match[1]
            url = part.split("]", 1)[1]
            urls = url.split(" or ", 1)
            for url in urls:
                type_: Literal["mp4", "m3u8"] = "mp4" if url.endswith(".mp4") else "m3u8"
                videos.append(Video(type=type_, quality=int(quality), url=url, headers={"Referer": self.url}))
        return videos

    def get_videos(
        self, *, headers: dict | None = None, cookies: dict | None = None, timeout: float | None = None
    ) -> list[Video]:
        ts = int(time() - 40)
        if self.is_movie:
            payload = cast(HdrezkaApiPayloadMovie, self._api_payload)
            result = HdrezkaCdnSeriesAPI.get_movie(self.http, timestamp=ts, **payload)
        else:
            payload = cast(HdrezkaApiPayloadSeries, self._api_payload)
            result = HdrezkaCdnSeriesAPI.get_stream(self.http, timestamp=ts, **payload)
        if not result.is_ok:
            return []
        value = cast(HdrezkaCdnResponseJson, result.value)
        return self._parse_videos(value["url"])

    async def a_get_videos(
        self, *, headers: dict | None = None, cookies: dict | None = None, timeout: float | None = None
    ) -> list[Video]:
        ts = int(time() - 40)
        if self.is_movie:
            payload = cast(HdrezkaApiPayloadMovie, self._api_payload)
            result = await HdrezkaCdnSeriesAPI.async_get_movie(self.http_async, timestamp=ts, **payload)
        else:
            payload = cast(HdrezkaApiPayloadSeries, self._api_payload)
            result = await HdrezkaCdnSeriesAPI.async_get_stream(self.http_async, timestamp=ts, **payload)
        if not result.is_ok:
            return []
        value = cast(HdrezkaCdnResponseJson, result.value)
        return self._parse_videos(value["url"])


if __name__ == "__main__":
    from anicli_api.tools import cli

    cli(Extractor())
