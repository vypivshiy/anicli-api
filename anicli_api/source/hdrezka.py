from __future__ import annotations

import logging
from typing import Union, cast, TypedDict
from time import time
import re

from attr import field, define
from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.source.parsers.hdrezka_parser import PageAnime, PageOngoing, PageSearch, HdrezkaCdnSeriesAPI

from anicli_api._http import ANUBIS_BYPASS_HEADERS

# types
from anicli_api.source.parsers.hdrezka_parser import EpisodeType, PageAnimeType, HdrezkaCdnResponseJson
from anicli_api.player.base import Video

logger = logging.getLogger("anicli-api")


class HdrezkaApiPayloadSeries(TypedDict):
    id: int
    translator_id: str
    season: int
    episode: int
    favs: str


class HdrezkaApiPayloadMovie(TypedDict):
    id: int
    translator_id: str
    favs: str


class Extractor(BaseExtractor):
    BASE_URL = "https://hdrezka-home.tv"

    def search(self, query: str):
        result = PageSearch.fetch(self.http, query=query, headers=ANUBIS_BYPASS_HEADERS).parse()
        return [
            Search(
                title=f"{data['title']} {data['season']}",
                url=data["url"],
                thumbnail=data["thumbnail"],
                **self._kwargs_http,
            )
            for data in result
        ]

    async def a_search(self, query: str):
        result = (await PageSearch.async_fetch(self.http_async, query=query, headers=ANUBIS_BYPASS_HEADERS)).parse()
        return [
            Search(
                title=f"{data['title']} {data['season']}",
                url=data["url"],
                thumbnail=data["thumbnail"],
                **self._kwargs_http,
            )
            for data in result
        ]

    def ongoing(self):
        result = PageOngoing.fetch(self.http, headers=ANUBIS_BYPASS_HEADERS).parse()
        return [
            Ongoing(
                title=f"{data['title']} {data['season']}",
                url=data["url"],
                thumbnail=data["thumbnail"],
                **self._kwargs_http,
            )
            for data in result
        ]

    async def a_ongoing(self):
        result = (await PageOngoing.async_fetch(self.http_async, headers=ANUBIS_BYPASS_HEADERS)).parse()
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
    def get_anime(self):
        data = PageAnime.fetch_from_url(self.http, anime_url=self.url, headers=ANUBIS_BYPASS_HEADERS).parse()
        return Anime(
            title=data["title"],
            thumbnail=data["thumbnail"],
            description=data["description"],
            data=data,
            url=Extractor.BASE_URL,
            **self._kwargs_http,
        )

    async def a_get_anime(self):
        data = (
            await PageAnime.async_fetch_from_url(self.http_async, anime_url=self.url, headers=ANUBIS_BYPASS_HEADERS)
        ).parse()
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
    def get_anime(self):
        data = PageAnime.fetch_from_url(self.http, anime_url=self.url, headers=ANUBIS_BYPASS_HEADERS).parse()
        return Anime(
            title=data["title"],
            thumbnail=data["thumbnail"],
            description=data["description"],
            data=data,
            url=Extractor.BASE_URL,
            **self._kwargs_http,
        )

    async def a_get_anime(self):
        data = (
            await PageAnime.async_fetch_from_url(self.http_async, anime_url=self.url, headers=ANUBIS_BYPASS_HEADERS)
        ).parse()
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
    def get_episodes(self):
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

    async def a_get_episodes(self):
        return self.get_episodes()


@define(kw_only=True)
class Episode(BaseEpisode):
    data: PageAnimeType
    data_episode: EpisodeType
    is_movie: bool = False

    def get_sources(self):
        if self.is_movie:
            return self._get_movie_sources()
        return self._get_series_sources()

    def _get_movie_sources(self):
        if not self.data["translation_list"]:
            return [
                Source(
                    title="hdrezka",
                    url=Extractor.BASE_URL,
                    is_movie=True,
                    api_payload={
                        "id": self.data["id"],
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
                    "id": self.data["id"],
                    "translator_id": translation["data_translator_id"],
                    "favs": self.data["favs"],
                },
                **self._kwargs_http,
            )
            for translation in self.data["translation_list"]
        ]

    def _get_series_sources(self):
        # single translation option allowed
        if not self.data["translation_list"]:
            return [
                Source(
                    title="hdrezka",
                    url=Extractor.BASE_URL,
                    api_payload={
                        "id": self.data_episode["data_id"],
                        "translator_id": self.data["translation_id"],
                        "season": self.data_episode["data_season_id"],
                        "favs": self.data["favs"],
                        "episode": self.data_episode["data_episode_id"],
                    },
                    **self._kwargs_http,
                )
            ]

        sources = [
            Source(
                title=f"{translation['title']}",
                url=Extractor.BASE_URL,  # stub, real url generated in Source object
                api_payload={
                    "id": self.data_episode["data_id"],
                    "translator_id": translation["data_translator_id"],
                    "season": self.data_episode["data_season_id"],
                    "favs": self.data["favs"],
                    "episode": self.data_episode["data_episode_id"],
                },
                **self._kwargs_http,
            )
            for translation in self.data["translation_list"]
        ]
        return sources

    async def a_get_sources(self):
        return self.get_sources()


@define(kw_only=True)
class Source(BaseSource):
    _api_payload: Union[HdrezkaApiPayloadSeries, HdrezkaApiPayloadMovie] = field(alias="api_payload")
    is_movie: bool = False

    def _parse_videos(self, raw_urls: str) -> list["Video"]:
        videos = []
        for part in raw_urls.split(","):
            # item signature:
            # "[{int}p (Ultra)?]https://...manifest.m3u8 or https://...mp4"
            quality = re.search(r"\[.*?(\d+).*?\]", part)[1]  # type: ignore
            url = part.split("]", 1)[1]
            urls = url.split(" or ", 1)
            for url in urls:
                if url.endswith(".mp4"):
                    type_ = "mp4"
                # apologize, include only mp4 or m3u8
                else:
                    type_ = "m3u8"
                videos.append(Video(type=type_, quality=int(quality), url=url, headers={"Referer": self.url}))
        return videos

    def get_videos(self, *, headers: dict | None = None, cookies: dict | None = None, timeout: float | None = None):
        if self.is_movie:
            result = HdrezkaCdnSeriesAPI.get_movie(
                self.http,
                timestamp=int(time() - 40),
                headers=ANUBIS_BYPASS_HEADERS,
                **self._api_payload,
            )
        else:
            result = HdrezkaCdnSeriesAPI.get_stream(
                self.http,
                timestamp=int(time() - 40),
                headers=ANUBIS_BYPASS_HEADERS,
                **self._api_payload,
            )
        if not result.is_ok:
            return []
        value = result.value
        value = cast(HdrezkaCdnResponseJson, value)
        return self._parse_videos(value["url"])

    async def a_get_videos(
        self, *, headers: dict | None = None, cookies: dict | None = None, timeout: float | None = None
    ):
        if self.is_movie:
            result = await HdrezkaCdnSeriesAPI.async_get_movie(
                self.http_async,
                timestamp=int(time() - 40),
                headers=ANUBIS_BYPASS_HEADERS,
                **self._api_payload,
            )
        else:
            result = await HdrezkaCdnSeriesAPI.async_get_stream(
                self.http_async,
                timestamp=int(time() - 40),
                headers=ANUBIS_BYPASS_HEADERS,
                **self._api_payload,
            )
        if not result.is_ok:
            return []
        value = result.value
        value = cast(HdrezkaCdnResponseJson, value)
        return self._parse_videos(value["url"])


if __name__ == "__main__":
    from anicli_api.tools import cli

    cli(Extractor())
