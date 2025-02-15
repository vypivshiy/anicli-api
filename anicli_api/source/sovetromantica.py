import warnings
from typing import TYPE_CHECKING, List, Optional

from attrs import define

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource, HttpMixin
from anicli_api.source.parsers.sovetromantica_parser import AnimePage, OngoingPage, SearchPage, T_EpisodeView

if TYPE_CHECKING:
    pass


class Extractor(BaseExtractor):
    BASE_URL = "https://sovetromantica.com/"

    def _extract_search(self, resp: str) -> List["Search"]:
        return [Search(**d, **self._kwargs_http) for d in SearchPage(resp).parse()]

    def _extract_ongoing(self, resp: str) -> List["Ongoing"]:
        return [Ongoing(**d, **self._kwargs_http) for d in OngoingPage(resp).parse()]

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
class _SearchOrOngoing(HttpMixin):
    title: str
    url: str
    alt_title: str

    def _extract(self, resp: str) -> "Anime":
        data = AnimePage(resp).parse()
        # DESCRIPTION MAYBE DOES NOT EXIST
        data["description"] = data["description"] or ""
        return Anime(**data, **self._kwargs_http)

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
    _video_url: Optional[str]  # STUB ATTRIBUTE
    _episodes: List[T_EpisodeView]

    def get_episodes(self):
        if not self._video_url:
            warnings.warn("Not available videos")
            return []

        return [
            Episode(num=str(i), url=d["url"], title=d["title"], **self._kwargs_http)
            for i, d in enumerate(self._episodes, 1)
        ]

    async def a_get_episodes(self):
        return self.get_episodes()


@define(kw_only=True)
class Episode(BaseEpisode):
    _url: str

    def _extract(self, resp: str) -> List["Source"]:
        # video link contains in anime page
        data = AnimePage(resp).parse()
        return [Source(title="Sovetromantica", url=data["video_url"], **self._kwargs_http)]

    def get_sources(self):
        resp = self.http.get(self._url)
        return self._extract(resp.text)

    async def a_get_sources(self):
        resp = await self.http_async.get(self._url)
        return self._extract(resp.text)


@define(kw_only=True)
class Source(BaseSource):
    pass


if __name__ == "__main__":
    from anicli_api.tools import cli

    cli(Extractor())
