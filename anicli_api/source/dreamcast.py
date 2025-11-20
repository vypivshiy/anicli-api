from __future__ import annotations

from typing import TYPE_CHECKING

from attr import define, field
from httpx import AsyncClient, Client

from anicli_api.typing import TypedDict
from anicli_api._http import HTTPAsync, HTTPSync
from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.player.base import Video
from anicli_api.player.dreamcast_chipers import extract_playlist, T_FileItem
from anicli_api.source.parsers.dreamerscast_parser import PageAnime
from anicli_api.source.apis.dreamerscast import DreamerscastSync, DreamerscastAsync, T_Release


if TYPE_CHECKING:
    from httpx import AsyncClient, Client


# used for sanitaize playlist file

T_KW_APIS = TypedDict("T_KW_APIS", {"sync_api": DreamerscastSync, "async_api": DreamerscastAsync})


class Extractor(BaseExtractor):
    BASE_URL = "https://dreamerscast.com/"

    def __init__(self, http_client: "Client" = HTTPSync(), http_async_client: "AsyncClient" = HTTPAsync()):
        super().__init__(http_client, http_async_client)

        self._sync_api = DreamerscastSync(client=self.http, raise_on_error=False)
        self._async_api = DreamerscastAsync(client=self.http_async, raise_on_error=False)

    @property
    def sync_api(self) -> DreamerscastSync:
        return self._sync_api

    @property
    def async_api(self) -> DreamerscastAsync:
        return self._async_api

    @property
    def _kwargs_api(self) -> T_KW_APIS:
        """shortcut for pass API objects arguments in kwargs style"""
        return {"sync_api": self.sync_api, "async_api": self.async_api}

    def ongoing(self) -> list["Ongoing"]:
        result = self.sync_api.get_releases(search_form={"search": "", "pageNumber": 1, "pageSize": 16, "status": ""})
        result.raise_for_status()

        results = []
        for data in result.data["releases"]:
            # maybe missing keys
            if data.get("russian"):
                title = data["russian"]
            else:
                title = data["original"]

            results.append(
                Ongoing(
                    title=title,
                    thumbnail=data["image"],  # type: ignore
                    url="https://dreamerscast.com" + data["url"],
                    data=data,
                    **self._kwargs_http,
                    **self._kwargs_api,
                )
            )
        return results

    async def a_ongoing(self) -> list["Ongoing"]:
        result = await self.async_api.get_releases(
            search_form={"search": "", "pageNumber": 1, "pageSize": 16, "status": ""}
        )
        result.raise_for_status()

        results = []
        for data in result.data["releases"]:
            # maybe missing keys
            if data.get("russian"):
                title = data["russian"]
            else:
                title = data["original"]

            results.append(
                Ongoing(
                    title=title,
                    thumbnail=data["image"],  # type: ignore
                    url="https://dreamerscast.com" + data["url"],
                    data=data,
                    **self._kwargs_http,
                    **self._kwargs_api,
                )
            )
        return results

    def search(self, query: str) -> list["Search"]:
        result = self.sync_api.get_releases(
            search_form={"search": query, "pageNumber": 1, "pageSize": 16, "status": ""}
        )
        result.raise_for_status()

        results = []
        for data in result.data["releases"]:
            # maybe missing keys
            if data.get("russian"):
                title = data["russian"]
            else:
                title = data["original"]

            results.append(
                Search(
                    title=title,
                    thumbnail=data["image"],  # type: ignore
                    url="https://dreamerscast.com" + data["url"],
                    data=data,
                    **self._kwargs_http,
                    **self._kwargs_api,
                )
            )
        return results

    async def a_search(self, query: str) -> list["Search"]:
        result = await self.async_api.get_releases(
            search_form={"search": query, "pageNumber": 1, "pageSize": 16, "status": ""}
        )
        result.raise_for_status()

        results = []
        for data in result.data["releases"]:
            # maybe missing keys
            if data.get("russian"):
                title = data["russian"]
            else:
                title = data["original"]

            results.append(
                Search(
                    title=title,
                    thumbnail=data["image"],  # type: ignore
                    url="https://dreamerscast.com" + data["url"],
                    data=data,
                    **self._kwargs_http,
                    **self._kwargs_api,
                )
            )
        return results


class _ApiInstancesMixin:
    _sync_api: DreamerscastSync
    _async_api: DreamerscastAsync

    @property
    def _kwargs_apis(self) -> T_KW_APIS:
        return {"sync_api": self.sync_api, "async_api": self.async_api}

    @property
    def sync_api(self) -> DreamerscastSync:
        return self._sync_api

    @property
    def async_api(self) -> DreamerscastAsync:
        return self._async_api


@define(kw_only=True)
class Ongoing(_ApiInstancesMixin, BaseOngoing):
    _sync_api: DreamerscastSync = field(alias="sync_api")
    _async_api: DreamerscastAsync = field(alias="async_api")
    data: T_Release

    def get_anime(self) -> "Anime":
        resp = self.http.get(self.url)
        data = PageAnime(resp.text).parse()
        return Anime(
            title=data["title"],
            thumbnail=data["thumbnail"],
            description=data["description"],  # type: ignore
            player_js_encoded=data["player_js_encoded"],
            player_js_url=data["player_js_url"],
            **self._kwargs_http,
            **self._kwargs_apis,
        )

    async def a_get_anime(self) -> "Anime":
        resp = await self.http_async.get(self.url)
        data = PageAnime(resp.text).parse()
        return Anime(
            title=data["title"],
            thumbnail=data["thumbnail"],
            description=data["description"],  # type: ignore
            player_js_encoded=data["player_js_encoded"],
            player_js_url=data["player_js_url"],
            **self._kwargs_http,
            **self._kwargs_apis,
        )


@define(kw_only=True)
class Search(_ApiInstancesMixin, BaseSearch):
    _sync_api: DreamerscastSync = field(alias="sync_api")
    _async_api: DreamerscastAsync = field(alias="async_api")
    data: T_Release


@define(kw_only=True)
class Anime(_ApiInstancesMixin, BaseAnime):
    # required decode, contains episodes
    _sync_api: DreamerscastSync = field(alias="sync_api")
    _async_api: DreamerscastAsync = field(alias="async_api")
    _player_js_encoded: str = field(alias="player_js_encoded")
    _player_js_url: str = field(alias="player_js_url")

    def get_episodes(self) -> list["Episode"]:
        js_encoded_resp = self.http.get(self._player_js_url).text
        result = extract_playlist(js_encoded_resp, self._player_js_encoded)
        results = []
        for i, data in enumerate(result["file"], 1):
            results.append(Episode(title=data["title"], ordinal=i, data=data, **self._kwargs_http, **self._kwargs_apis))
        return results

    async def a_get_episodes(self) -> list["Episode"]:
        js_encoded_resp = (await self.http_async.get(self._player_js_url)).text
        result = extract_playlist(js_encoded_resp, self._player_js_encoded)
        result = extract_playlist(js_encoded_resp, self._player_js_encoded)
        results = []

        for i, data in enumerate(result["file"], 1):
            results.append(Episode(title=data["title"], ordinal=i, data=data, **self._kwargs_http, **self._kwargs_apis))
        return results


@define(kw_only=True)
class Episode(_ApiInstancesMixin, BaseEpisode):
    _sync_api: DreamerscastSync = field(alias="sync_api")
    _async_api: DreamerscastAsync = field(alias="async_api")
    data: T_FileItem

    def get_sources(self) -> list["Source"]:
        return [
            Source(
                title="Dreamcast",
                url="_",  # stub
                file=self.data["file"],
                **self._kwargs_http,
                **self._kwargs_apis,
            )
        ]

    async def a_get_sources(self) -> list["Source"]:
        return self.get_sources()


@define(kw_only=True)
class Source(_ApiInstancesMixin, BaseSource):
    _sync_api: DreamerscastSync = field(alias="sync_api")
    _async_api: DreamerscastAsync = field(alias="async_api")
    _file: str = field(alias="file")

    # NOTE: 'file' key signature:
    #  'file': 'https://play.dreamerscast.com/dash/.../manifest.mpd or https://play.dreamerscast.com/hls/.../master.m3u8'

    def get_videos(self, **httpx_kwargs) -> list["Video"]:
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

    async def a_get_videos(self, **httpx_kwargs) -> list["Video"]:
        return self.get_videos()


if __name__ == "__main__":
    from anicli_api.tools.dummy_cli import cli

    cli(Extractor())
