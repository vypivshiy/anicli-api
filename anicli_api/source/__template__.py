from typing import List

from scrape_schema import Parsel, Sc

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource


class Extractor(BaseExtractor):
    BASE_URL = ""  # BASEURL

    def search(self, query: str) -> List["Search"]:
        """an anime search entrypoint"""
        pass

    async def a_search(self, query: str) -> List["Search"]:
        """an anime search entrypoint (async)"""
        pass

    def ongoing(self) -> List["Ongoing"]:
        """an ongoing search entrypoint"""
        pass

    async def a_ongoing(self) -> List["Ongoing"]:
        """an ongoing search entrypoint (async)"""
        pass


class Search(BaseSearch):
    url: Sc[str, Parsel()]
    title: Sc[str, Parsel()]
    thumbnail: Sc[str, Parsel()]

    # metadata: Sc[str, Parsel()]

    def get_anime(self) -> "Anime":
        pass

    async def a_get_anime(self) -> "Anime":
        pass

    def __str__(self):
        # past string code for print view render
        return f"{self.title}"


class Ongoing(BaseOngoing):
    url: Sc[str, Parsel()]
    title: Sc[str, Parsel()]
    thumbnail: Sc[str, Parsel()]

    # metadata: str(ep, dub, etc)

    def get_anime(self) -> "Anime":
        pass

    async def a_get_anime(self) -> "Anime":
        pass

    def __str__(self):
        return f"{self.title}"


class Anime(BaseAnime):
    # implement this minimal fields

    title: Sc[str, Parsel()]
    alt_titles: Sc[List[str], Parsel()]
    thumbnail: Sc[str, Parsel()]
    description: Sc[str, Parsel()]
    genres: Sc[str, Parsel()]
    episodes_available: Sc[int, Parsel()]
    episodes_total: Sc[int, Parsel()]
    aired: Sc[str, Parsel()]

    def get_episodes(self) -> List["Episode"]:
        pass

    async def a_get_episodes(self) -> List["Episode"]:
        pass

    def __str__(self):
        # past string code for print view render
        return (
            f"{self.title} ({', '.join(self.alt_titles)}) {self.aired} {', '.join(self.genres)} "
            f"[{self.episodes_available} of {self.episodes_total}] ~{self.description}"
        )


class Episode(BaseEpisode):
    num: Sc[int, Parsel()]
    title: Sc[str, Parsel()]

    def get_sources(self) -> List["Source"]:
        pass

    async def a_get_sources(self) -> List["Source"]:
        pass

    def __str__(self):
        # past string code for print view render
        return f"{self.num} {self.title}"


class Source(BaseSource):
    url: Sc[str, Parsel()]  # should be implemented
