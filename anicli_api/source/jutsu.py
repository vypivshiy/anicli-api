import re
import warnings
from typing import TYPE_CHECKING, Any, Dict, List

from attr import field
from attrs import define

from anicli_api._http import HTTPAsync, HTTPSync
from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.player.base import Video
from anicli_api.source.parsers.jutsu_parser import AnimeView, EpisodeView, OngoingView, SearchView, SourceView

if TYPE_CHECKING:
    from httpx import AsyncClient, Client


class Extractor(BaseExtractor):
    """NOTE: For playing video usage user-agent from http or http_async instance

    """
    BASE_URL = "https://jut.su"

    def __init__(self, http_client: "Client" = HTTPSync(), http_async_client: "AsyncClient" = HTTPAsync()):
        super().__init__(http_client=http_client, http_async_client=http_async_client)

    @staticmethod
    def _extract_search(resp: str) -> List["Search"]:
        data = SearchView(resp).parse().view()
        return [Search(**kw) for kw in data]

    @staticmethod
    def _extract_ongoing(resp: str) -> List["Ongoing"]:
        data = OngoingView(resp).parse().view()
        return [Ongoing(**kw) for kw in data]

    def search(self, query: str):
        resp = self.http.post(
            self.BASE_URL + "/anime", data={"ajax_load": "yes", "start_from_page": 1, "show_search": query}
        )
        return self._extract_search(resp.text)

    async def a_search(self, query: str):
        resp = await self.http_async.post(
            self.BASE_URL + "/anime", data={"ajax_load": "yes", "start_from_page": 1, "show_search": query}
        )
        return self._extract_search(resp.text)

    def ongoing(self):
        resp = self.http.post(self.BASE_URL + "/anime", data={"ajax_load": "yes", "start_from_page": 1})
        return self._extract_ongoing(resp.text)

    async def a_ongoing(self):
        resp = await self.http_async.post(self.BASE_URL + "/anime", data={"ajax_load": "yes", "start_from_page": 1})
        return self._extract_ongoing(resp.text)


class _SearchOrOngoing:
    url: str
    http: "Client"
    http_async: "AsyncClient"

    @staticmethod
    def _extract(resp: str) -> "Anime":
        data = AnimeView(resp).parse().view()
        # num attribute API required
        raw_episodes = [{"num": f"{i + 1}", **kw} for i, kw in enumerate(EpisodeView(resp).parse().view())]
        return Anime(**data, raw_episodes=raw_episodes)

    def get_anime(self):
        resp = self.http.get(self.url)
        return self._extract(resp.text)

    async def a_get_anime(self):
        resp = await self.http_async.get(self.url)
        return self._extract(resp.text)


@define(kw_only=True)
class Search(_SearchOrOngoing, BaseSearch):
    counts: str = field(repr=False)


@define(kw_only=True)
class Ongoing(_SearchOrOngoing, BaseOngoing):
    counts: str = field(repr=False)


@define(kw_only=True)
class Anime(BaseAnime):
    # stub attribute
    _raw_episodes: List[Dict[str, Any]] = field(repr=False)

    def get_episodes(self):
        return [Episode(**kw) for kw in self._raw_episodes]

    async def a_get_episodes(self):
        return self.get_episodes()


@define(kw_only=True)
class Episode(BaseEpisode):
    _url: str = field(repr=False)

    @staticmethod
    def _is_blocked(raw_videos, response: str) -> bool:
        if all(i["url"] is None for i in raw_videos):
            # block jquery signature:
            # var block_video_text_str = 'К сожалению, в России это видео недоступно.';
            # var block_video_text_str_everywhere = 'К сожалению, это видео недоступно.';
            if re.search(r"block_video_text_str\+", response):
                block_video = "К сожалению, в России это видео недоступно."
            elif re.search(r"block_video_text_str_everywhere\+", response):
                block_video = "К сожалению, это видео недоступно."
            else:
                block_video = ""

            reason = re.search(r"var block_[^>]+\s*=\s*['\"](?:<br>)?(.*?)['\"];", response)[1]

            msg = f"Block issue. message: '{block_video} {reason}'."
            warnings.warn(msg, stacklevel=1, category=RuntimeWarning)
            return True
        return False

    def _extract(self, resp: str) -> List["Source"]:
        data = SourceView(resp).parse().view()
        raw_videos = [{"url": v, "quality": int(k.strip("url_"))} for k, v in data.items()]
        # RKN blocks (RU region)
        # eg: https://jut.su/shingekii-no-kyojin/season-1/episode-1.html
        if self._is_blocked(raw_videos, resp):
            return []
        # STUB
        # -----------------------------------v
        return [Source(title="jut.su", url=self._url, raw_videos=raw_videos)]

    def get_sources(self):
        resp = self.http.get(self._url)
        return self._extract(resp.text)

    async def a_get_sources(self):
        resp = await self.http_async.get(self._url)
        return self._extract(resp.text)


@define(kw_only=True)
class Source(BaseSource):
    _raw_videos: List[Dict[str, Any]] = field(repr=False)

    def get_videos(self, **_) -> List["Video"]:
        # For video playing, the user-agent MUST BE equal
        # as a client user-agent in the extractor API
        # ELSE VIDEO HOSTING RETURNS 403 CODE
        return [
            Video(**kw, headers={"User-Agent": self.http.headers["user-agent"]}, type="mp4")
            for kw in self._raw_videos
            if kw["url"]
        ]

    def a_get_videos(self, **httpx_kwargs) -> List["Video"]:
        return self.get_videos()


if __name__ == "__main__":
    from anicli_api.tools import cli

    cli(Extractor())
