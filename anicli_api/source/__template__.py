from typing import Dict, List

from attrs import define

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource

# pre generated parser
# from anicli_api.source.parsers


class Extractor(BaseExtractor):
    BASE_URL = "https://example.com"

    @staticmethod
    def _extract_search(resp: str) -> List["Search"]:
        pass

    @staticmethod
    def _extract_ongoing(resp: str) -> List["Ongoing"]:
        pass

    def search(self, query: str):
        resp = self.http.get(f"")
        return self._extract_search(resp.text)

    async def a_search(self, query: str):
        resp = await self.http_async.get(f"")
        return self._extract_search(resp.text)

    def ongoing(self):
        resp = self.http.get(self.BASE_URL)
        return self._extract_ongoing(resp.text)

    async def a_ongoing(self):
        resp = await self.http_async.get(self.BASE_URL)
        return self._extract_ongoing(resp.text)


@define(kw_only=True)
class Search(BaseSearch):
    @staticmethod
    def _extract(resp: str) -> "Anime":
        pass

    def get_anime(self):
        resp = self.http.get(self.url)
        return self._extract(resp.text)

    async def a_get_anime(self):
        resp = await self.http_async.get(self.url)
        return self._extract(resp.text)


@define(kw_only=True)
class Ongoing(BaseOngoing):
    @staticmethod
    def _extract(resp: str) -> "Anime":
        pass

    def get_anime(self):
        resp = self.http.get(self.url)
        return self._extract(resp.text)

    async def a_get_anime(self):
        resp = await self.http_async.get(self.url)
        return self._extract(resp.text)


@define(kw_only=True)
class Anime(BaseAnime):
    @staticmethod
    def _extract(resp: str) -> List["Episode"]:
        pass

    def get_episodes(self):
        resp = self.http.get(f"")
        return self._extract(resp.text)

    async def a_get_episodes(self):
        resp = await self.http_async.get(f"")
        return self._extract(resp.text)


@define(kw_only=True)
class Episode(BaseEpisode):
    def _extract(self, resp: str) -> List["Source"]:
        pass

    def get_sources(self):
        resp = self.http.get("")
        return self._extract(resp.text)

    async def a_get_sources(self):
        resp = await self.http_async.get("")
        return self._extract(resp.text)


@define(kw_only=True)
class Source(BaseSource):
    pass


if __name__ == "__main__":
    # manual testing parser
    from anicli_api.tools import cli

    cli(Extractor())
