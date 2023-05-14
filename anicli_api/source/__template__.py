from typing import List

from anicli_api.base import BaseExtractor, BaseOngoing, BaseSource, BaseEpisode, BaseAnime, BaseSearch


class Extractor(BaseExtractor):
    BASE_URL = ""  # BASEURL
    def search(self, query: str) -> List["Search"]:
        # search entrypoint
        pass
    async def a_search(self, query: str) -> List["Search"]:
        # async search entrypoint
        pass

    def ongoing(self) -> List["Ongoing"]:
        # ongoing entrypoint
        pass

    async def a_ongoing(self) -> List["Ongoing"]:
        # async ongoing entrypoint
        pass


class Search(BaseSearch):
    def get_anime(self) -> "Anime":
        pass
    async def a_get_anime(self) -> "Anime":
        pass

class Ongoing(BaseOngoing):
    def get_anime(self) -> "Anime":
        pass

    async def a_get_anime(self) -> "Anime":
        pass


class Anime(BaseAnime):
    def get_episodes(self) -> List["Episode"]:
        pass
    async def a_get_episodes(self) -> List["Episode"]:
        pass


class Episode(BaseEpisode):


    def get_sources(self) -> List["Source"]:
        pass

    async def a_get_sources(self) -> List["Source"]:
        pass


class Source(BaseSource):
    url: str # should be implemented
