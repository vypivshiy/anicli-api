import re
import warnings
from dataclasses import dataclass
from typing import Dict, List, Optional

from parsel import Selector

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.source.parsers.sovetromantica_parser import AnimeView as AnimeViewOld
from anicli_api.source.parsers.sovetromantica_parser import EpisodeView, OngoingView, SearchView


# patches
class AnimeView(AnimeViewOld):
    def _parse_video(self, part: Selector) -> str:
        val = part.get()
        if match := re.search(r"<meta property=\".*\" content=\"(https://.*?\.m3u8)\"", val):
            return match[1]
        return ""


# end patches


class Extractor(BaseExtractor):
    BASE_URL = "https://sovetromantica.com/"

    @staticmethod
    def _extract_search(resp: str) -> List["Search"]:
        data = SearchView(resp).parse().view()
        return [Search(**d) for d in data]

    @staticmethod
    def _extract_ongoing(resp: str) -> List["Ongoing"]:
        data = OngoingView(resp).parse().view()
        return [Ongoing(**d) for d in data]

    def search(self, query: str):
        resp = self.HTTP().get(f"https://sovetromantica.com/anime?query={query}")
        return self._extract_search(resp.text)

    async def a_search(self, query: str):
        resp = await self.HTTP_ASYNC().get(f"https://sovetromantica.com/anime?query={query}")
        return self._extract_search(resp.text)

    def ongoing(self):
        resp = self.HTTP().get("https://sovetromantica.com/anime")
        return self._extract_ongoing(resp.text)

    async def a_ongoing(self):
        resp = await self.HTTP_ASYNC().get("https://sovetromantica.com/anime")
        return self._extract_ongoing(resp.text)


@dataclass
class Search(BaseSearch):
    alt_title: str

    @staticmethod
    def _extract(resp: str) -> "Anime":
        data = AnimeView(resp).parse().view()[0]
        if not data.get("description"):
            data["description"] = ""
        if not data.get("video"):
            data["video"] = None
        episodes = EpisodeView(resp).parse().view()
        return Anime(**data, episodes=episodes)

    def get_anime(self):
        resp = self._http().get(self.url)
        return self._extract(resp.text)

    async def a_get_anime(self):
        resp = await self._a_http().get(self.url)
        return self._extract(resp.text)

    def __str__(self):
        return f"{self.title} ({self.alt_title})"


@dataclass
class Ongoing(Search, BaseOngoing):
    pass


@dataclass
class Anime(BaseAnime):
    video: Optional[str]  # STUB ATTRIBUTE
    episodes: List[Dict[str, str]]

    def get_episodes(self):
        if not self.video:
            warnings.warn("Not available videos")
            return []
        return [Episode(num=str(i), url=d["url"], title=d["title"]) for i, d in enumerate(self.episodes, 1)]

    async def a_get_episodes(self):
        return self.get_episodes()


@dataclass
class Episode(BaseEpisode):
    url: str

    def _extract(self, resp: str) -> List["Source"]:
        # video link contains in anime page
        data = AnimeView(resp).parse().view()[0]
        return [Source(title="Sovetromantica", url=data["video"])]

    def get_sources(self):
        resp = self._http().get(self.url)
        return self._extract(resp.text)

    async def a_get_sources(self):
        resp = await self._a_http().get(self.url)
        return self._extract(resp.text)


@dataclass
class Source(BaseSource):
    pass


if __name__ == "__main__":
    print(Extractor().search("lai")[0].get_anime().get_episodes()[0].get_sources())
