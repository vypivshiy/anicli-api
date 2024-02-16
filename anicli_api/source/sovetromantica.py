import warnings
from typing import Dict, List, Optional, Union, TYPE_CHECKING

from attrs import define

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.source.parsers.sovetromantica_parser import AnimeView
from anicli_api.source.parsers.sovetromantica_parser import EpisodeView, OngoingView, SearchView

if TYPE_CHECKING:
    from httpx import Client, AsyncClient


class Extractor(BaseExtractor):
    BASE_URL = "https://sovetromantica.com/"

    def _extract_search(self, resp: str) -> List["Search"]:
        data = SearchView(resp).parse().view()
        return [Search(**d, **self._kwargs_http) for d in data]

    def _extract_ongoing(self, resp: str) -> List["Ongoing"]:
        data = OngoingView(resp).parse().view()
        return [Ongoing(**d, **self._kwargs_http) for d in data]

    def search(self, query: str):
        resp = self.http.get(f"https://sovetromantica.com/anime?query={query}")
        return self._extract_search(resp.text)

    async def a_search(self, query: str):
        resp = await self.http_async.get(f"https://sovetromantica.com/anime?query={query}")
        return self._extract_search(resp.text)

    def ongoing(self):
        resp = self.http.get("https://sovetromantica.com/anime")
        return self._extract_ongoing(resp.text)

    async def a_ongoing(self):
        resp = await self.http_async.get("https://sovetromantica.com/anime")
        return self._extract_ongoing(resp.text)


# without @attrs.define decorator to avoid
# TypeError: multiple bases have instance lay-out conflict error
# (__slots__ magic method and attrs hooks issue)
class _SearchOrOngoing:

    title: str
    http: "Client"
    http_async: "AsyncClient"
    url: str
    alt_title: str
    _kwargs_http: Dict[str, Union["Client", "AsyncClient"]]

    def _extract(self, resp: str) -> "Anime":
        data = AnimeView(resp).parse().view()
        episodes = EpisodeView(resp).parse().view()

        return Anime(**data, episodes=episodes, **self._kwargs_http)

    def get_anime(self):
        resp = self.http.get(self.url)
        return self._extract(resp.text)

    async def a_get_anime(self):
        resp = await self.http_async.get(self.url)
        return self._extract(resp.text)

    def __str__(self):
        return f"{self.title} ({self.alt_title})"


@define(kw_only=True)
class Search(_SearchOrOngoing, BaseSearch):
    alt_title: str


@define(kw_only=True)
class Ongoing(_SearchOrOngoing, BaseOngoing):
    alt_title: str


@define(kw_only=True)
class Anime(BaseAnime):
    video: Optional[str]  # STUB ATTRIBUTE
    episodes: List[Dict[str, str]]

    def get_episodes(self):
        if not self.video:
            warnings.warn("Not available videos")
            return []

        return [Episode(num=str(i), url=d["url"], title=d["title"], **self._kwargs_http)
                for i, d in enumerate(self.episodes, 1)]

    async def a_get_episodes(self):
        return self.get_episodes()


@define(kw_only=True)
class Episode(BaseEpisode):
    url: str

    def _extract(self, resp: str) -> List["Source"]:
        # video link contains in anime page
        data = AnimeView(resp).parse().view()
        return [Source(title="Sovetromantica", url=data["video"], **self._kwargs_http)]

    def get_sources(self):
        resp = self.http.get(self.url)
        return self._extract(resp.text)

    async def a_get_sources(self):
        resp = await self.http_async.get(self.url)
        return self._extract(resp.text)


@define(kw_only=True)
class Source(BaseSource):
    pass


if __name__ == '__main__':
    from anicli_api.tools import cli
    cli(Extractor())
