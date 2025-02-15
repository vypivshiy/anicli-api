import re
from typing import Any, Dict, List

from attr import field
from attrs import define
from httpx import Response

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.player.base import Video
from anicli_api.source.parsers.sameband_parser import AnimePage, OngoingPage, PlaylistURLPage, SearchPage


class Extractor(BaseExtractor):
    BASE_URL = "https://sameband.studio"

    def _extract_search(self, resp: str) -> List["Search"]:
        return [Search(**kw, **self._kwargs_http) for kw in SearchPage(resp).parse()]

    def _extract_ongoing(self, resp: str) -> List["Ongoing"]:
        return [Ongoing(**kw, **self._kwargs_http) for kw in OngoingPage(resp).parse()]

    def search(self, query: str):
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

    async def a_search(self, query: str):
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

    def ongoing(self):
        resp = self.http.get(f"{self.BASE_URL}/novinki")
        return self._extract_ongoing(resp.text)

    async def a_ongoing(self):
        resp = await self.http_async.get(f"{self.BASE_URL}/novinki")
        return self._extract_ongoing(resp.text)


@define(kw_only=True)
class Search(BaseSearch):
    def _extract(self, resp: str) -> "Anime":
        return Anime(**AnimePage(resp).parse(), **self._kwargs_http)

    def get_anime(self):
        resp = self.http.get(self.url)
        return self._extract(resp.text)

    async def a_get_anime(self):
        resp = await self.http_async.get(self.url)
        return self._extract(resp.text)


@define(kw_only=True)
class Ongoing(BaseOngoing):
    def _extract(self, resp: str) -> "Anime":
        return Anime(**AnimePage(resp).parse(), **self._kwargs_http)

    def get_anime(self):
        resp = self.http.get(self.url)
        return self._extract(resp.text)

    async def a_get_anime(self):
        resp = await self.http_async.get(self.url)
        return self._extract(resp.text)


@define(kw_only=True)
class Anime(BaseAnime):
    alt_title: str
    _player_url: str = field(repr=False)

    @staticmethod
    def _extract(resp: Response) -> List["Episode"]:
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
                num=str(i),
                # TODO extract from item['title'] ???
                title="Серия",
            )
            for i, item in enumerate(jsn, 1)
        ]

    def get_episodes(self):
        resp = self.http.get(self._player_url)
        player_url = PlaylistURLPage(resp.text).parse()["playlist_url"]
        resp2 = self.http.get(player_url)
        return self._extract(resp2)

    async def a_get_episodes(self):
        resp = await self.http_async.get(self._player_url)
        player_url = PlaylistURLPage(resp.text).parse()["playlist_url"]
        resp2 = await self.http_async.get(player_url)
        return self._extract(resp2)


@define(kw_only=True)
class Episode(BaseEpisode):
    _sources: List[Dict[str, Any]] = field(repr=False)

    def get_sources(self):
        return [
            Source(
                sources=self._sources,
                # STUBS
                title="sameband.studio",
                url="https://sameband.studio",
            )
        ]

    async def a_get_sources(self):
        return self.get_sources()


@define(kw_only=True)
class Source(BaseSource):
    _sources: List[Dict[str, Any]] = field(repr=False)

    def get_videos(self, **_) -> List["Video"]:
        return [Video(**kw) for kw in self._sources]

    async def a_get_videos(self, **_) -> List["Video"]:
        return self.get_videos()


if __name__ == "__main__":
    from anicli_api.tools import cli

    cli(Extractor())
