import re
import warnings
from typing import TYPE_CHECKING, Any, Dict, List

from attr import field
from attrs import define

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource, HttpMixin
from anicli_api.player.base import Video
from anicli_api.source.parsers.jutsu_parser import AnimePage, OngoingPage, SearchPage, SourcePage

if TYPE_CHECKING:
    pass


class Extractor(BaseExtractor):
    """NOTE: For playing video usage user-agent from http or http_async instance"""

    BASE_URL = "https://jut.su"

    def _extract_search(self, resp: str) -> List["Search"]:
        return [Search(**kw, **self._kwargs_http) for kw in SearchPage(resp).parse()]

    def _extract_ongoing(self, resp: str) -> List["Ongoing"]:
        return [Ongoing(**kw, **self._kwargs_http) for kw in OngoingPage(resp).parse()]

    def search(self, query: str):
        resp = self.http.post(
            f"{self.BASE_URL}/anime",
            data={"ajax_load": "yes", "start_from_page": 1, "show_search": query},
        )
        return self._extract_search(resp.text)

    async def a_search(self, query: str):
        resp = await self.http_async.post(
            f"{self.BASE_URL}/anime",
            data={"ajax_load": "yes", "start_from_page": 1, "show_search": query},
        )
        return self._extract_search(resp.text)

    def ongoing(self):
        resp = self.http.get(f"{self.BASE_URL}/anime/ongoing/")
        return self._extract_ongoing(resp.text)

    async def a_ongoing(self):
        resp = await self.http_async.post(f"{self.BASE_URL}/anime/ongoing/")
        return self._extract_ongoing(resp.text)


class _SearchOrOngoing(HttpMixin):
    def _extract(self, resp: str):
        return Anime(**AnimePage(resp).parse(), **self._kwargs_http)

    def get_anime(self):
        resp = self.http.get(self.url)  # type: ignore
        return self._extract(resp.text)  # type: ignore

    async def a_get_anime(self):
        resp = await self.http_async.get(self.url)  # type: ignore
        return self._extract(resp.text)  # type: ignore


@define(kw_only=True)
class Search(_SearchOrOngoing, BaseSearch):
    counts: str = field(repr=False)


@define(kw_only=True)
class Ongoing(_SearchOrOngoing, BaseOngoing):
    counts: str = field(repr=False)


@define(kw_only=True)
class Anime(BaseAnime):
    # stub attribute
    _episodes: List[Dict[str, Any]] = field(repr=False)

    def get_episodes(self):
        return [Episode(num=str(n), **kw, **self._kwargs_http) for n, kw in enumerate(self._episodes, 1)]

    async def a_get_episodes(self):
        return self.get_episodes()


@define(kw_only=True)
class Episode(BaseEpisode):
    _url: str = field(repr=False)

    @staticmethod
    def _is_blocked(raw_videos, response: str) -> bool:
        if not raw_videos.get("null"):
            return False

        # block jquery signature:
        # var block_video_text_str = 'К сожалению, в России это видео недоступно.';
        # var block_video_text_str_everywhere = 'К сожалению, это видео недоступно.';
        if re.search(r"block_video_text_str_everywhere\+", response):
            block_video = "К сожалению, это видео недоступно."
        elif re.search(r"block_video_text_str\+", response):
            block_video = "К сожалению, в России это видео недоступно."
        else:
            block_video = ""

        reason = re.search(r"var block_[^>]+\s*=\s*['\"](?:<br>)?(.*?)['\"];", response)[1]  # type: ignore

        msg = f"Block issue. message: '{block_video} {reason}'."
        warnings.warn(msg, stacklevel=1, category=RuntimeWarning)
        return True

    def _extract(self, resp: str) -> List["Source"]:
        data = SourcePage(resp).parse()["videos"]
        # RKN blocks (RU region)
        # eg: https://jut.su/shingekii-no-kyojin/season-1/episode-1.html
        if self._is_blocked(data, resp):
            return []
        # STUB
        # -----------------------------------v
        return [Source(title="jut.su", url=self._url, source=data)]

    def get_sources(self):
        resp = self.http.get(self._url)
        return self._extract(resp.text)

    async def a_get_sources(self):
        resp = await self.http_async.get(self._url)
        return self._extract(resp.text)


@define(kw_only=True)
class Source(BaseSource):
    _source: Dict[str, Any] = field(repr=False)

    def get_videos(self, **_) -> List["Video"]:
        # For video playing, the user-agent MUST BE equal
        # as a client user-agent in the extractor API
        # ELSE VIDEO HOSTING RETURNS 403 CODE
        return [
            Video(
                url=url,
                quality=int(quality),  # type: ignore
                headers={"User-Agent": self.http.headers["user-agent"]},
                type="mp4",
            )
            for quality, url in self._source.items()
        ]

    async def a_get_videos(self, **httpx_kwargs) -> List["Video"]:
        return [
            Video(
                url=url,
                quality=int(quality),  # type: ignore
                headers={"User-Agent": self.http_async.headers["user-agent"]},
                type="mp4",
            )
            for quality, url in self._source.items()
        ]


if __name__ == "__main__":
    from anicli_api.tools import cli

    cli(Extractor())
