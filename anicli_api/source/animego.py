from __future__ import annotations

import logging
import re
from typing import List

from attr import define
from httpx import Response

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.source.parsers.animego_parser import (
    PageAnime,
    PageEpisode,
    PageOngoing,
    PageSearch,
    PageSource,
    ContentJson,
    EpisodeVideosType,
    PageEpisodeType,
)

logger = logging.getLogger("anicli-api")


# test not available players in country
RE_PLAYER_BLOCKED = re.compile(
    r'<div\b[^>]*\bclass\s*=\s*["\'][^"\']*\bplayer-blocked\b[^"\']*["\'][^>]*>', flags=re.IGNORECASE
)
# (msg text)
RE_DIV_H5_ERR = re.compile(
    r'<div\b([^>]*)\bclass\s*=\s*["\'][^"\']*\bh5\b[^"\']*["\']([^>]*)>(.*?)</div>', flags=re.IGNORECASE | re.DOTALL
)


class Extractor(BaseExtractor):
    BASE_URL = "https://animego.me"

    @staticmethod
    def _remove_ongoings_dups(ongoings: list["Ongoing"]) -> list["Ongoing"]:
        # remove duplicates and accumulate by episode and dubber keys
        sorted_ongs: dict[int, "Ongoing"] = {}
        for ong in ongoings:
            key = hash(ong.url + ong.episode)
            if sorted_ongs.get(key):
                sorted_ongs[key].dub += f", {ong.dub}"
            else:
                sorted_ongs[key] = ong
        return list(sorted_ongs.values())

    def search(self, query: str) -> list["Search"]:
        results = PageSearch.fetch(self.http, query=query)
        return [
            Search(title=i["title"], thumbnail=i["thumbnail"], url=i["url_path"], **self._kwargs_http)
            for i in results.parse()
        ]

    async def a_search(self, query: str) -> list["Search"]:
        results = await PageSearch.async_fetch(self.http_async, query=query)
        return [
            Search(title=i["title"], thumbnail=i["thumbnail"], url=i["url_path"], **self._kwargs_http)
            for i in results.parse()
        ]

    def ongoing(self) -> list["Ongoing"]:
        results = PageOngoing.fetch(self.http)
        ongoings = [
            Ongoing(
                title=i["title"],
                thumbnail=i["thumbnail"],
                episode=i["episode"],
                dub=i["dub"],
                url=i["url_path"],
                **self._kwargs_http,
            )
            for i in results.parse()
        ]
        return self._remove_ongoings_dups(ongoings)

    async def a_ongoing(self) -> list["Ongoing"]:
        results = await PageOngoing.async_fetch(self.http_async)
        ongoings = [
            Ongoing(
                title=i["title"],
                thumbnail=i["thumbnail"],
                episode=i["episode"],
                dub=i["dub"],
                url=i["url_path"],
                **self._kwargs_http,
            )
            for i in results.parse()
        ]
        return self._remove_ongoings_dups(ongoings)


@define(kw_only=True)
class Search(BaseSearch):
    def get_anime(self) -> "Anime":
        # manual parse instead use .fetch() constructor: title can be not allowed
        resp = self.http.get(Extractor.BASE_URL + self.url)
        return self._extract(resp.text) if self._is_valid_page(resp) else self._create_anime()

    async def a_get_anime(self) -> "Anime":
        resp = await self.http_async.get(Extractor.BASE_URL + self.url)
        return self._extract(resp.text) if self._is_valid_page(resp) else self._create_anime()

    def _extract(self, resp: str) -> "Anime":
        return Anime(**PageAnime(resp).parse(), **self._kwargs_http)

    @staticmethod
    def _is_valid_page(resp: Response) -> bool:
        # hided, but API requests by anime_id MAYBE still works.
        # example:
        # https://animego.me/anime/ya-predpochitayu-zlodeyku-2413
        if resp.is_success:
            return True

        logger.warning(
            "%s returns status code [%s] content-length=%s",
            resp.url,
            resp.status_code,
            len(resp.content),
        )
        return False

    def _create_anime(self) -> "Anime":
        # fallback
        # skip extract metadata and manually create the object (API requests maybe still works)
        return Anime(
            title=self.title,
            thumbnail=self.thumbnail,
            description="",
            # id for API requests contains in url
            id=self.url.split("-")[-1],
            raw_json={},  # type: ignore
            **self._kwargs_http,
        )


@define(kw_only=True)
class Ongoing(BaseOngoing):
    episode: str
    dub: str

    def _extract(self, resp: str) -> "Anime":
        return Anime(**PageAnime(resp).parse(), **self._kwargs_http)

    @staticmethod
    def _is_valid_page(resp: Response) -> bool:
        # hided, but API requests by anime_id MAYBE still works.
        # example:
        # https://animego.me/anime/ya-predpochitayu-zlodeyku-2413
        if resp.is_success:
            return True

        logger.warning(
            "%s returns status code [%s] content-length=%s",
            resp.url,
            resp.status_code,
            len(resp.content),
        )
        return False

    def _create_anime(self) -> "Anime":
        # skip extract metadata, and manual creates the object (API requests MAYBE still works)
        return Anime(
            title=self.title,
            thumbnail=self.thumbnail,
            description="",
            id=self.url.split("-")[-1],
            raw_json={},  # type: ignore
            **self._kwargs_http,
        )

    def get_anime(self) -> "Anime":
        resp = self.http.get(Extractor.BASE_URL + self.url)
        return self._extract(resp.text) if self._is_valid_page(resp) else self._create_anime()

    async def a_get_anime(self) -> "Anime":
        resp = await self.http_async.get(Extractor.BASE_URL + self.url)
        return self._extract(resp.text) if self._is_valid_page(resp) else self._create_anime()

    def __str__(self):
        return f"{self.title} {self.episode} ({self.dub})"


@define(kw_only=True)
class Anime(BaseAnime):
    id: str
    raw_json: ContentJson

    def _extract_epidodes(self, result: PageEpisodeType):
        dubbers = result["dubbers"]
        if result["episodes"]:
            return [
                Episode(
                    title=data["title"],
                    ordinal=data["num"],
                    dubbers=dubbers,
                    id=data["id"],
                    videos=[],  # stub and cond for tests
                    **self._kwargs_http,
                )
                for data in result["episodes"]
            ]
        return [
            Episode(
                title=self.title,
                ordinal=1,
                id=self.id,  # STUB
                dubbers=dubbers,
                videos=result["videos"],
                **self._kwargs_http,
            ),
        ]

    def get_episodes(self) -> list["Episode"]:
        result = PageEpisode.fetch(self.http, anime_id=self.id).parse()
        return self._extract_epidodes(result)

    async def a_get_episodes(self) -> list["Episode"]:
        result = (await PageEpisode.async_fetch(self.http_async, anime_id=self.id)).parse()
        return self._extract_epidodes(result)


@define(kw_only=True)
class Episode(BaseEpisode):
    dubbers: dict[str, str]
    id: str  # episode id (for extract videos required)
    videos: List[EpisodeVideosType]

    def get_sources(self):
        # films
        if self.videos:
            sources = [
                Source(
                    title=self.dubbers.get(data["data_provide_dubbing"], "???"), url=data["player"], **self._kwargs_http
                )
                for data in self.videos
            ]
        else:
            result = PageSource.fetch(self.http, episode_id=self.id).parse()
            dubbers = result["dubbers"]
            sources = [
                Source(title=dubbers.get(data["data_provide_dubbing"], "???"), url=data["url"], **self._kwargs_http)
                for data in result["videos"]
            ]
        return sources

    async def a_get_sources(self):
        # films
        if self.videos:
            sources = [
                Source(
                    title=self.dubbers.get(data["data_provide_dubbing"], "???"), url=data["player"], **self._kwargs_http
                )
                for data in self.videos
            ]
        else:
            result = (await PageSource.async_fetch(self.http_async, episode_id=self.id)).parse()
            dubbers = result["dubbers"]
            sources = [
                Source(title=dubbers.get(data["data_provide_dubbing"], "???"), url=data["url"], **self._kwargs_http)
                for data in result["videos"]
            ]
        return sources


@define(kw_only=True)
class Source(BaseSource):
    pass


if __name__ == "__main__":
    from anicli_api.tools import cli

    cli(Extractor())
