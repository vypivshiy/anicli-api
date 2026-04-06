from __future__ import annotations

import logging
from typing import TypedDict
from time import time

from attr import field, define
from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.source.parsers.hdrezka_parser import PageAnime, PageOngoing, PageSearch, PageUtils

# types
from anicli_api.source.parsers.hdrezka_parser import SeasonBoxType, EpisodeType, TranslationType
from anicli_api.player.base import Video

logger = logging.getLogger("anicli-api")


class HdrezkaResponse(TypedDict):
    success: bool
    message: str
    premium_content: int
    url: str
    quality: str
    subtitle: bool
    subtitle_lns: bool
    subtitle_def: bool
    thumbnails: str


class Extractor(BaseExtractor):
    BASE_URL = "https://hdrezka-home.tv"
    ONGOING_PARAMS = {"filter": "last", "genre": "82"}
    #
    SEARCH_PARAMS = {"do": "search", "subaction": "search", "q": ""}

    def _parse_search(self, resp: str):
        data = PageSearch(resp).parse()
        return [
            Search(title=f"{i['title']} {i['season']}", url=i["url"], thumbnail=i["thumbnail"], **self._kwargs_http)
            for i in data
        ]

    def _parse_ongoing(self, resp: str):
        data = PageOngoing(resp).parse()
        return [
            Ongoing(title=f"{i['title']} {i['season']}", url=i["url"], thumbnail=i["thumbnail"], **self._kwargs_http)
            for i in data
        ]

    def search(self, query):
        params = self.SEARCH_PARAMS.copy()
        params["q"] = query
        resp = self.http.get(self.BASE_URL + "/search/", params=params)
        return self._parse_search(resp.text)

    async def a_search(self, query):
        params = self.SEARCH_PARAMS.copy()
        params["q"] = query
        resp = await self.http_async.get(self.BASE_URL + "/search/", params=params)
        return self._parse_search(resp.text)

    def ongoing(self):
        resp = self.http.get(self.BASE_URL, params=self.ONGOING_PARAMS)
        return self._parse_ongoing(resp.text)

    async def a_ongoing(self):
        resp = await self.http_async.get(self.BASE_URL, params=self.ONGOING_PARAMS)
        return self._parse_ongoing(resp.text)


@define(kw_only=True)
class Search(BaseSearch):
    def get_anime(self):
        resp = self.http.get(self.url)
        data = PageAnime(resp.text).parse()
        url = PageUtils(resp.text).parse()["url"]
        return Anime(
            title=data["title"],
            thumbnail=data["thumbnail"],
            description=data["description"],
            translation_list=data["translation_list"],
            translation_id=data["translation_id"],
            episode_list=data["episode_list"],
            season_box=data["season_box"],
            favs=data["favs"],
            url=url,
            **self._kwargs_http,
        )

    async def a_get_anime(self):
        resp = await self.http_async.get(self.url)
        data = PageAnime(resp.text).parse()
        url = PageUtils(resp.text).parse()["url"]
        return Anime(
            title=data["title"],
            thumbnail=data["thumbnail"],
            description=data["description"],
            translation_list=data["translation_list"],
            translation_id=data["translation_id"],
            episode_list=data["episode_list"],
            season_box=data["season_box"],
            favs=data["favs"],
            url=url,
            **self._kwargs_http,
        )


@define(kw_only=True)
class Ongoing(BaseOngoing):
    def get_anime(self):
        resp = self.http.get(self.url)
        data = PageAnime(resp.text).parse()
        url = PageUtils(resp.text).parse()["url"]
        return Anime(
            title=data["title"],
            thumbnail=data["thumbnail"],
            description=data["description"],
            translation_list=data["translation_list"],
            translation_id=data["translation_id"],
            episode_list=data["episode_list"],
            season_box=data["season_box"],
            favs=data["favs"],
            url=url,
            **self._kwargs_http,
        )

    async def a_get_anime(self):
        resp = await self.http_async.get(self.url)
        data = PageAnime(resp.text).parse()
        url = PageUtils(resp.text).parse()["url"]
        return Anime(
            title=data["title"],
            thumbnail=data["thumbnail"],
            description=data["description"],
            translation_list=data["translation_list"],
            translation_id=data["translation_id"],
            episode_list=data["episode_list"],
            season_box=data["season_box"],
            favs=data["favs"],
            url=url,
            **self._kwargs_http,
        )


@define(kw_only=True)
class Anime(BaseAnime):
    _translation_list: list[TranslationType] = field(alias="translation_list")
    _translation_id: str = field(alias="translation_id")
    _season_box: list[SeasonBoxType] = field(alias="season_box")
    _episode_list: list[EpisodeType] = field(alias="episode_list")
    _favs: str = field(alias="favs")
    _url: str = field(alias="url")

    # note: lazy create instances: every episode required send API request
    def get_episodes(self):
        eps = []
        for i, e in enumerate(self._episode_list, 1):
            eps.append(
                Episode(
                    title=e["title"],
                    episode=e,
                    translation_list=self._translation_list,
                    translation_id=self._translation_id,
                    season_box=self._season_box,
                    ordinal=i,
                    favs=self._favs,
                    url=self._url,
                    **self._kwargs_http,
                )
            )
        return eps

    async def a_get_episodes(self):
        return self.get_episodes()


@define(kw_only=True)
class Episode(BaseEpisode):
    _translation_list: list[TranslationType] = field(alias="translation_list")
    _translation_id: str = field(alias="translation_id")
    _season_box: list[SeasonBoxType] = field(alias="season_box")
    _episode: EpisodeType = field(alias="episode")
    _favs: str = field(alias="favs")
    _url: str = field(alias="url")

    def get_sources(self):
        sources = []
        if not self._translation_list:
            payload = {
                "id": self._episode["data_id"],
                "translator_id": self._translation_id,
                "season": self._episode["data_season_id"],
                "favs": self._favs,
                "episode": self._episode["data_episode_id"],
                "action": "get_stream",
            }
            return [
                Source(
                    title="hdrezka",  # how extract dubber name in this case?
                    url=self._url,  # stub, real url generated in Source object
                    api_payload=payload,
                    **self._kwargs_http,
                )
            ]

        for translation in self._translation_list:
            payload = {
                "id": self._episode["data_id"],
                "translator_id": translation["data_translator_id"],
                "season": self._episode["data_season_id"],
                "favs": self._favs,
                "episode": self._episode["data_episode_id"],
                "action": "get_stream",
            }
            sources.append(
                Source(
                    title=f"{translation['title']}",
                    url=self._url,  # stub, real url generated in Source object
                    api_payload=payload,
                    **self._kwargs_http,
                )
            )
        return sources

    async def a_get_sources(self):
        return self.get_sources()


@define(kw_only=True)
class Source(BaseSource):
    _api_payload: dict[str, str] = field(alias="api_payload")  # todo: typing

    def _parse_videos(self, raw_urls: str) -> list["Video"]:
        videos = []
        for part in raw_urls.split(","):
            # item signature:
            # "[{int}p (Ultra)?]https://...manifest.m3u8 or https://...mp4"
            quality, raw_urls = part.split("]", 1)
            quality = quality.split("p", 1)[0].replace("[", "")
            urls = raw_urls.split(" or ", 1)
            for url in urls:
                if url.endswith(".mp4"):
                    type_ = "mp4"
                # apologize, include only mp4 or m3u8
                else:
                    type_ = "m3u8"
                videos.append(Video(type=type_, quality=int(quality), url=url, headers={"Referer": self.url}))
        return videos

    def get_videos(self, **httpx_kwargs):
        resp = self.http.post(
            self.url + "/ajax/get_cdn_series/", params={"t": int(time() - 40)}, data=self._api_payload, **httpx_kwargs
        )
        data: HdrezkaResponse = resp.json()
        return self._parse_videos(data["url"])

    async def a_get_videos(self, **httpx_kwargs):
        resp = await self.http_async.post(self.url + "/ajax/get_cdn_series/", data=self._api_payload, **httpx_kwargs)
        data: HdrezkaResponse = resp.json()
        return self._parse_videos(data["url"])


if __name__ == "__main__":
    from anicli_api.tools import cli

    cli(Extractor())
