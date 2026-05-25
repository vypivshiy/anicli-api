from __future__ import annotations

import logging
from typing import cast, TypedDict
from time import time
import re

from attr import field, define
from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.source.parsers.hdrezka_parser import PageAnime, PageOngoing, PageSearch, HdrezkaCdnSeriesAPI

# types
from anicli_api.source.parsers.hdrezka_parser import EpisodeType, PageAnimeType, HdrezkaCdnResponseJson
from anicli_api.player.base import Video

logger = logging.getLogger("anicli-api")


class HdrezkaApiPayload(TypedDict):
    id: int
    translator_id: str
    season: int
    favs: str
    episode: int
    action: str


class Extractor(BaseExtractor):
    BASE_URL = "https://hdrezka-home.tv"

    def search(self, query: str):
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

    async def a_search(self, query: str):
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

    def ongoing(self):
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

    async def a_ongoing(self):
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
    def get_anime(self):
        data = PageAnime.fetch_from_url(self.http, anime_url=self.url).parse()
        return Anime(
            title=data["title"],
            thumbnail=data["thumbnail"],
            description=data["description"],
            data=data,
            url=Extractor.BASE_URL,
            **self._kwargs_http,
        )

    async def a_get_anime(self):
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
    def get_anime(self):
        data = PageAnime.fetch_from_url(self.http, anime_url=self.url).parse()
        return Anime(
            title=data["title"],
            thumbnail=data["thumbnail"],
            description=data["description"],
            data=data,
            url=Extractor.BASE_URL,
            **self._kwargs_http,
        )

    async def a_get_anime(self):
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
    def get_episodes(self):
        eps = [
            Episode(title=e["title"], data=self.data, data_episode=e, ordinal=i, **self._kwargs_http)
            for i, e in enumerate(self.data["episode_list"])
        ]
        return eps

    async def a_get_episodes(self):
        return self.get_episodes()


@define(kw_only=True)
class Episode(BaseEpisode):
    data: PageAnimeType
    data_episode: EpisodeType

    def get_sources(self):
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
                        "action": "get_stream",
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
                    "action": "get_stream",
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
    _api_payload: HdrezkaApiPayload = field(alias="api_payload")  # todo: typing

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

    def get_videos(self, **httpx_kwargs):
        result = HdrezkaCdnSeriesAPI.fetch(
            self.http,
            timestamp=int(time() - 40),
            **self._api_payload,
        )
        if not result.is_ok:
            return []
        value = result.value
        value = cast(HdrezkaCdnResponseJson, value)
        return self._parse_videos(value["url"])

    async def a_get_videos(self, **httpx_kwargs):
        result = await HdrezkaCdnSeriesAPI.async_fetch(
            self.http_async,
            timestamp=int(time() - 40),
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
