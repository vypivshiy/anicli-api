from dataclasses import dataclass
from typing import Dict, List

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource

# from anicli_api.source.schemas

# schema patches

# end patches


class Extractor(BaseExtractor):
    BASE_URL = "https://example.com"

    @staticmethod
    def _extract_search(resp: str) -> List["Search"]:
        pass

    @staticmethod
    def _extract_ongoing(resp: str) -> List["Ongoing"]:
        pass

    def search(self, query: str):
        resp = self.HTTP().get(f"")
        return self._extract_search(resp.text)

    async def a_search(self, query: str):
        resp = await self.HTTP_ASYNC().get(f"")
        return self._extract_search(resp.text)

    def ongoing(self):
        resp = self.HTTP().get(self.BASE_URL)
        return self._extract_ongoing(resp.text)

    async def a_ongoing(self):
        resp = await self.HTTP_ASYNC().get(self.BASE_URL)
        return self._extract_ongoing(resp.text)


@dataclass
class Search(BaseSearch):
    @staticmethod
    def _extract(resp: str) -> "Anime":
        pass

    def get_anime(self):
        resp = self._http().get(self.url)
        return self._extract(resp.text)

    async def a_get_anime(self):
        resp = await self._a_http().get(self.url)
        return self._extract(resp.text)


@dataclass
class Ongoing(BaseOngoing):
    @staticmethod
    def _extract(resp: str) -> "Anime":
        pass

    def get_anime(self):
        resp = self._http().get(self.url)
        return self._extract(resp.text)

    async def a_get_anime(self):
        resp = await self._a_http().get(self.url)
        return self._extract(resp.text)


@dataclass
class Anime(BaseAnime):
    @staticmethod
    def _extract(resp: str) -> List["Episode"]:
        pass

    def get_episodes(self):
        resp = self._http().get(f"")
        return self._extract(resp.text)

    async def a_get_episodes(self):
        resp = await self._a_http().get(f"")
        return self._extract(resp.text)


@dataclass
class Episode(BaseEpisode):
    def _extract(self, resp: str) -> List["Source"]:
        pass

    def get_sources(self):
        resp = self._http().get("")
        return self._extract(resp.text)

    async def a_get_sources(self):
        resp = await self._a_http().get("")
        return self._extract(resp.text)


@dataclass
class Source(BaseSource):
    pass


if __name__ == "__main__":
    print(Extractor().search("lai")[0].get_anime().get_episodes()[0].get_sources())
