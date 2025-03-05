from typing import List, Dict, Any, Optional, TYPE_CHECKING, Union

from attr import define

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.player.base import Video
from anicli_api.player.dreamcast_chipers import extract_playlist
from anicli_api.source.parsers.dreamcast_parser import AnimePage

if TYPE_CHECKING:
    from httpx import AsyncClient, Client


class Extractor(BaseExtractor):
    BASE_URL = "https://dreamerscast.com/"

    def _parse_ongoing(self, releases: List[Dict[str, Any]]) -> List["Ongoing"]:
        ongs: List[Ongoing] = []
        for release in releases:
            title = release["russian"]
            url = self.BASE_URL + release.pop("url")
            thumbnail = self.BASE_URL + release["image"]

            ongs.append(
                Ongoing(
                    title=title,
                    thumbnail=thumbnail,
                    url=url,
                    **self._kwargs_http,
                )
            )
        return ongs

    def _parse_search(self, releases: List[Dict[str, Any]]) -> List["Search"]:
        res: List[Search] = []
        for release in releases:
            title = release["russian"]
            url = self.BASE_URL + release.pop("url")
            thumbnail = self.BASE_URL + release["image"]

            res.append(
                Search(
                    title=title,
                    thumbnail=thumbnail,
                    url=url,
                    **self._kwargs_http,  # type: ignore
                )
            )
        return res

    def ongoing(self) -> List["Ongoing"]:
        resp = self.http.post(self.BASE_URL, data={"search": "", "status": "", "pageSize": 16, "pageNumber": 1}).json()
        return self._parse_ongoing(resp["releases"])

    def search(self, query: str) -> List["Search"]:
        resp = self.http.post(
            self.BASE_URL, data={"search": query, "status": "", "pageSize": 16, "pageNumber": 1}
        ).json()
        return self._parse_search(resp["releases"])

    async def a_ongoing(self):
        resp = (
            await self.http_async.post(
                self.BASE_URL, data={"search": "", "status": "", "pageSize": 16, "pageNumber": 1}
            )
        ).json()
        return self._parse_ongoing(resp["releases"])

    async def a_search(self, query: str) -> List["Search"]:
        resp = (
            await self.http_async.post(
                self.BASE_URL, data={"search": query, "status": "", "pageSize": 16, "pageNumber": 1}
            )
        ).json()
        return self._parse_search(resp["releases"])


class _SearchOrOngoing:
    http: "Client"
    http_async: "AsyncClient"
    _kwargs_http: Dict[str, Union["Client", "AsyncClient"]]

    title: str
    thumbnail: str
    url: str

    def get_anime(self):
        resp = self.http.get(self.url)
        return Anime(**AnimePage(resp.text).parse(), **self._kwargs_http)

    async def a_get_anime(self):
        resp = await self.http_async.get(self.url)
        return Anime(**AnimePage(resp.text).parse(), **self._kwargs_http)


@define(kw_only=True)
class Ongoing(_SearchOrOngoing, BaseOngoing):
    title: str
    thumbnail: str
    url: str


@define(kw_only=True)
class Search(_SearchOrOngoing, BaseSearch):
    title: str
    thumbnail: str
    url: str


@define(kw_only=True)
class Anime(BaseAnime):
    # required decode, contains episodes
    _player_js_encoded: str
    _player_js_url: str

    def get_episodes(self):
        js_encoded_resp = self.http.get(self._player_js_url).text
        result = extract_playlist(js_encoded_resp, self._player_js_encoded)
        if result.get("file"):
            return [Episode(num=str(i), **r, **self._kwargs_http) for i, r in enumerate(result["file"], 1)]
        return []

    async def a_get_episodes(self):
        js_encoded_resp = (await self.http_async.get(self._player_js_url)).text
        result = extract_playlist(js_encoded_resp, self._player_js_encoded)
        if result.get("file"):
            return [Episode(num=str(i), **r, **self._kwargs_http) for i, r in enumerate(result["file"], 1)]
        return []


@define(kw_only=True)
class Episode(BaseEpisode):
    # meta
    _label: str
    # title: str
    # video url
    _file: str
    _thumbnails: str
    embed: str
    id: str
    vars: Dict[str, Any]

    def get_sources(self):
        return [Source(title="Dreamcast", url=self._file, **self._kwargs_http)]

    async def a_get_sources(self):
        return self.get_sources()


@define(kw_only=True)
class Source(BaseSource):
    def get_videos(self, **httpx_kwargs) -> List["Video"]:
        return [Video(quality=1080, type="mpd", url=self.url)]

    async def a_get_videos(self, **httpx_kwargs) -> List["Video"]:
        return self.get_videos()


if __name__ == "__main__":
    from anicli_api.tools.dummy_cli import cli

    cli(Extractor())
