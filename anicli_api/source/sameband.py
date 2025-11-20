from __future__ import annotations

import re
from typing import Literal

from attr import field
from attrs import define
from httpx import Response

from anicli_api.typing import TypedDict
from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.player.base import Video
from anicli_api.source.parsers.sameband_parser import PageAnime, PageOngoing, PagePlaylistURL, PageSearch


class Extractor(BaseExtractor):
    BASE_URL = "https://sameband.studio"

    def _extract_search(self, resp: str) -> list["Search"]:
        return [Search(**kw, **self._kwargs_http) for kw in PageSearch(resp).parse()]

    def _extract_ongoing(self, resp: str) -> list["Ongoing"]:
        return [Ongoing(**kw, **self._kwargs_http) for kw in PageOngoing(resp).parse()]

    def search(self, query: str) -> list["Search"]:
        resp = self.http.post(
            f"{self.BASE_URL}/index.php?do=search",
            data={
                "do": "search",
                "subaction": "search",
                "search_start": 0,
                "full_search": 0,
                "result_from": 1,
                "story": query,
            },
        )
        return self._extract_search(resp.text)

    async def a_search(self, query: str) -> list["Search"]:
        resp = await self.http_async.post(
            f"{self.BASE_URL}/index.php?do=search",
            data={
                "do": "search",
                "subaction": "search",
                "search_start": 0,
                "full_search": 0,
                "result_from": 1,
                "story": query,
            },
        )
        return self._extract_search(resp.text)

    def ongoing(self) -> list["Ongoing"]:
        resp = self.http.get(f"{self.BASE_URL}/novinki")
        return self._extract_ongoing(resp.text)

    async def a_ongoing(self) -> list["Ongoing"]:
        resp = await self.http_async.get(f"{self.BASE_URL}/novinki")
        return self._extract_ongoing(resp.text)


@define(kw_only=True)
class Search(BaseSearch):
    def _extract(self, resp: str) -> "Anime":
        return Anime(**PageAnime(resp).parse(), **self._kwargs_http)

    def get_anime(self) -> "Anime":
        resp = self.http.get(self.url)
        return self._extract(resp.text)

    async def a_get_anime(self) -> "Anime":
        resp = await self.http_async.get(self.url)
        return self._extract(resp.text)


@define(kw_only=True)
class Ongoing(BaseOngoing):
    def _extract(self, resp: str) -> "Anime":
        return Anime(**PageAnime(resp).parse(), **self._kwargs_http)

    def get_anime(self) -> "Anime":
        resp = self.http.get(self.url)
        return self._extract(resp.text)

    async def a_get_anime(self) -> "Anime":
        resp = await self.http_async.get(self.url)
        return self._extract(resp.text)


@define(kw_only=True)
class Anime(BaseAnime):
    alt_title: str
    _player_url: str = field(repr=False, alias="player_url")

    @staticmethod
    def _extract(resp: Response) -> list["Episode"]:
        jsn = resp.json()

        return [
            Episode(
                sources=[
                    # remove quality prefix
                    {
                        "url": "https://sameband.studio" + re.sub(r"^\[\d+p\]", "", u),
                        # Video object quality
                        "quality": int(re.match(r"^\[(\d+)p\]", u)[1]),  # type: ignore
                        "type": "m3u8",
                    }
                    for u in item["file"].split(",")
                ],
                ordinal=i,
                # TODO extract from item['title'] ???
                title="Серия",
            )
            for i, item in enumerate(jsn, 1)
        ]

    def get_episodes(self) -> list["Episode"]:
        resp = self.http.get(self._player_url)
        player_data = PagePlaylistURL(resp.text).parse()
        playlist_url = player_data["playlist_url"]
        resp2 = self.http.get(playlist_url)
        return self._extract(resp2)

    async def a_get_episodes(self) -> list["Episode"]:
        resp = await self.http_async.get(self._player_url)
        player_url = PagePlaylistURL(resp.text).parse()["playlist_url"]
        resp2 = await self.http_async.get(player_url)
        return self._extract(resp2)


T_SOURCE = TypedDict("T_SOURCE", {"url": str, "quality": int, "type": Literal["m3u8"]})


@define(kw_only=True)
class Episode(BaseEpisode):
    _sources: list[T_SOURCE] = field(repr=False, alias="sources")

    def get_sources(self) -> list["Source"]:
        return [
            Source(
                sources=self._sources,
                # STUBS
                title="sameband.studio",
                url="https://sameband.studio",
            )
        ]

    async def a_get_sources(self) -> list["Source"]:
        return self.get_sources()


@define(kw_only=True)
class Source(BaseSource):
    _sources: list[T_SOURCE] = field(repr=False, alias="sources")

    def get_videos(self, **_) -> list["Video"]:
        return [Video(type=kw["type"], url=kw["url"], quality=kw["quality"]) for kw in self._sources]

    async def a_get_videos(self, **_) -> list["Video"]:
        return self.get_videos()


if __name__ == "__main__":
    from anicli_api.tools import cli

    cli(Extractor())
