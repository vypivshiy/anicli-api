from __future__ import annotations

from typing import cast

from attr import define, field

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.player.base import Video
from anicli_api.player.dreamcast_chipers import extract_playlist, T_FileItem
from anicli_api.source.parsers.dreamerscast_parser import DreamCastResponseJson, PageAnime, DreamcastAPI, ReleaseJson


class Extractor(BaseExtractor):
    BASE_URL = "https://dreamerscast.com/"

    def ongoing(self) -> list["Ongoing"]:
        result = DreamcastAPI.ongoing(self.http)
        if not result.is_ok:
            # TODO: handle errors
            return []
        releases = result.value
        releases = cast(DreamCastResponseJson, releases)
        results = [
            Ongoing(
                title=data["russian"] if data.get("russian", None) else data["original"],
                thumbnail=data["image"],
                url=data["url"],  # path, not full url
                data=data,
                **self._kwargs_http,
            )
            for data in releases["releases"]
        ]
        return results

    async def a_ongoing(self) -> list["Ongoing"]:
        result = await DreamcastAPI.async_ongoing(self.http_async)
        if not result.is_ok:
            # TODO: handle errors
            return []
        releases = result.value
        releases = cast(DreamCastResponseJson, releases)
        results = [
            Ongoing(
                title=data["russian"] if data.get("russian", None) else data["original"],
                thumbnail=data["image"],
                url=data["url"],
                data=data,
                **self._kwargs_http,
            )
            for data in releases["releases"]
        ]
        return results

    def search(self, query: str) -> list["Search"]:
        result = DreamcastAPI.search(self.http, query=query)
        if not result.is_ok:
            # TODO: handle errors
            return []
        releases = result.value
        releases = cast(DreamCastResponseJson, releases)
        results = [
            Search(
                title=data["russian"] if data.get("russian", None) else data["original"],
                thumbnail=data["image"],
                url=data["url"],
                data=data,
                **self._kwargs_http,
            )
            for data in releases["releases"]
        ]
        return results

    async def a_search(self, query: str) -> list["Search"]:
        result = await DreamcastAPI.async_search(self.http_async, query=query)
        if not result.is_ok:
            # TODO: handle errors
            return []
        releases = result.value
        releases = cast(DreamCastResponseJson, releases)
        results = [
            Search(
                title=data["russian"] if data.get("russian", None) else data["original"],
                thumbnail=data["image"],
                url=data["url"],
                data=data,
                **self._kwargs_http,
            )
            for data in releases["releases"]
        ]
        return results


@define(kw_only=True)
class Ongoing(BaseOngoing):
    data: ReleaseJson

    def get_anime(self) -> "Anime":
        data = PageAnime.fetch(self.http, url_path=self.url).parse()
        return Anime(
            title=data["title"],
            thumbnail=data["thumbnail"],
            description=data["description"],  # type: ignore
            player_js_encoded=data["player_js_encoded"],
            player_js_url=data["player_js_url"],
            **self._kwargs_http,
        )

    async def a_get_anime(self) -> "Anime":
        data = (await PageAnime.async_fetch(self.http_async, url_path=self.url)).parse()
        return Anime(
            title=data["title"],
            thumbnail=data["thumbnail"],
            description=data["description"],  # type: ignore
            player_js_encoded=data["player_js_encoded"],
            player_js_url=data["player_js_url"],
            **self._kwargs_http,
        )


@define(kw_only=True)
class Search(BaseSearch):
    data: ReleaseJson

    def get_anime(self) -> "Anime":
        data = PageAnime.fetch(self.http, url_path=self.url).parse()
        return Anime(
            title=data["title"],
            thumbnail=data["thumbnail"],
            description=data["description"],  # type: ignore
            player_js_encoded=data["player_js_encoded"],
            player_js_url=data["player_js_url"],
            **self._kwargs_http,
        )

    async def a_get_anime(self) -> "Anime":
        data = (await PageAnime.async_fetch(self.http_async, url_path=self.url)).parse()
        return Anime(
            title=data["title"],
            thumbnail=data["thumbnail"],
            description=data["description"],  # type: ignore
            player_js_encoded=data["player_js_encoded"],
            player_js_url=data["player_js_url"],
            **self._kwargs_http,
        )


@define(kw_only=True)
class Anime(BaseAnime):
    # required decode, contains episodes
    _player_js_encoded: str = field(alias="player_js_encoded")
    _player_js_url: str = field(alias="player_js_url")

    def get_episodes(self) -> list["Episode"]:
        js_encoded_resp = self.http.get(self._player_js_url).text
        result = extract_playlist(js_encoded_resp, self._player_js_encoded)

        if not result.get("file", None):
            return []

        results = []
        for i, data in enumerate(result["file"], 1):
            results.append(Episode(title=data["title"] or f"Episode {i}", ordinal=i, data=data, **self._kwargs_http))
        return results

    async def a_get_episodes(self) -> list["Episode"]:
        js_encoded_resp = (await self.http_async.get(self._player_js_url)).text
        result = extract_playlist(js_encoded_resp, self._player_js_encoded)

        if not result.get("file", None):
            return []

        results = []
        for i, data in enumerate(result["file"], 1):
            results.append(Episode(title=data["title"], ordinal=i, data=data, **self._kwargs_http))
        return results


@define(kw_only=True)
class Episode(BaseEpisode):
    data: T_FileItem

    def get_sources(self) -> list["Source"]:
        return [
            Source(
                title="Dreamcast",
                url="_",  # stub
                file=self.data["file"],
                **self._kwargs_http,
            )
        ]

    async def a_get_sources(self) -> list["Source"]:
        return self.get_sources()


@define(kw_only=True)
class Source(BaseSource):
    _file: str = field(alias="file")

    def get_videos(
        self, *, headers: dict | None = None, cookies: dict | None = None, timeout: float | None = None
    ) -> list["Video"]:
        parts = self._file.split()
        videos = []
        for part in parts:
            if not part.startswith("http"):
                continue
            type_ = part.split(".")[-1]
            videos.append(
                Video(
                    # mpd or m3u8
                    type=type_,  # type: ignore
                    quality=1080,
                    url=part,
                )
            )
            # m3u8 type to first pos
        videos.reverse()
        return videos

    async def a_get_videos(
        self, *, headers: dict | None = None, cookies: dict | None = None, timeout: float | None = None
    ) -> list["Video"]:
        return self.get_videos()


if __name__ == "__main__":
    from anicli_api.tools.dummy_cli import cli

    cli(Extractor())
