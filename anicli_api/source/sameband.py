from __future__ import annotations

import re
from typing import Literal

from attr import field
from attrs import define

from anicli_api.typing import TypedDict
from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.player.base import Video
from anicli_api.source.parsers.sameband_parser import (
    PageAnime,
    PageOngoing,
    PagePlaylistURL,
    PageSearch,
    PlaylistJson,
    PlaylistTxtAPI,
)


class Extractor(BaseExtractor):
    BASE_URL = "https://sameband.studio"

    def _extract_search(self, resp: str) -> list["Search"]:
        return [Search(**kw, **self._kwargs_http) for kw in PageSearch(resp).parse()]

    def _extract_ongoing(self, resp: str) -> list["Ongoing"]:
        return [Ongoing(**kw, **self._kwargs_http) for kw in PageOngoing(resp).parse()]

    def search(self, query: str) -> list["Search"]:
        results = PageSearch.fetch(self.http, query=query).parse()
        return [Search(**i, **self._kwargs_http) for i in results]

    async def a_search(self, query: str) -> list["Search"]:
        results = (await PageSearch.async_fetch(self.http_async, query=query)).parse()
        return [Search(**i, **self._kwargs_http) for i in results]

    def ongoing(self) -> list["Ongoing"]:
        results = PageOngoing.fetch(self.http).parse()
        return [Ongoing(**i, **self._kwargs_http) for i in results]

    async def a_ongoing(self) -> list["Ongoing"]:
        results = (await PageOngoing.async_fetch(self.http_async)).parse()
        return [Ongoing(**i, **self._kwargs_http) for i in results]


@define(kw_only=True)
class Search(BaseSearch):
    def get_anime(self) -> "Anime":
        result = PageAnime.fetch(self.http, anime_page_url=self.url).parse()
        return Anime(**result, **self._kwargs_http)

    async def a_get_anime(self) -> "Anime":
        result = (await PageAnime.async_fetch(self.http_async, anime_page_url=self.url)).parse()
        return Anime(**result, **self._kwargs_http)


@define(kw_only=True)
class Ongoing(BaseOngoing):
    def get_anime(self) -> "Anime":
        result = PageAnime.fetch(self.http, anime_page_url=self.url).parse()
        return Anime(**result, **self._kwargs_http)

    async def a_get_anime(self) -> "Anime":
        result = (await PageAnime.async_fetch(self.http_async, anime_page_url=self.url)).parse()
        return Anime(**result, **self._kwargs_http)


@define(kw_only=True)
class Anime(BaseAnime):
    _player_url: str = field(repr=False, alias="player_url")

    def _extract(self, playlist: list[PlaylistJson]) -> list["Episode"]:
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
                **self._kwargs_http,
            )
            for i, item in enumerate(playlist, 1)
        ]

    def get_episodes(self) -> list["Episode"]:
        playlist_url = PagePlaylistURL.fetch(self.http, player_url=self._player_url).parse()["playlist_url"]
        playlist = PlaylistTxtAPI.playlist(self.http, playlist_txt_url=playlist_url)
        if playlist.is_ok:
            return self._extract(playlist.value)
        # TODO: handle exceptions?
        return []

    async def a_get_episodes(self) -> list["Episode"]:
        playlist_url = (await PagePlaylistURL.async_fetch(self.http_async, player_url=self._player_url)).parse()[
            "playlist_url"
        ]
        playlist = await PlaylistTxtAPI.async_playlist(self.http_async, playlist_txt_url=playlist_url)
        if playlist.is_ok:
            return self._extract(playlist.value)
        # TODO: handle exceptions?
        return []


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
                **self._kwargs_http,
            )
        ]

    async def a_get_sources(self) -> list["Source"]:
        return self.get_sources()


@define(kw_only=True)
class Source(BaseSource):
    _sources: list[T_SOURCE] = field(repr=False, alias="sources")

    def get_videos(
        self, *, headers: dict | None = None, cookies: dict | None = None, timeout: float | None = None
    ) -> list["Video"]:
        return [Video(type=kw["type"], url=kw["url"], quality=kw["quality"]) for kw in self._sources]

    async def a_get_videos(
        self, *, headers: dict | None = None, cookies: dict | None = None, timeout: float | None = None
    ) -> list["Video"]:
        return self.get_videos()


if __name__ == "__main__":
    from anicli_api.tools import cli

    cli(Extractor())
