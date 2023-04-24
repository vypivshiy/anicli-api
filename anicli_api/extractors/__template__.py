from anicli_api.base import *


class Extractor(BaseExtractor):
    def search(self, query: str):
        pass

    async def a_search(self, query: str):
        pass

    def ongoing(self):
        pass

    async def a_ongoing(self):
        pass


class SearchResult(BaseSearch):
    def get_anime(self):
        pass

    async def a_get_anime(self):
        pass


class Ongoing(BaseOngoing):
    def get_anime(self):
        pass

    async def a_get_anime(self):
        pass


class AnimeInfo(BaseAnime):
    def get_episodes(self):
        pass

    async def a_get_episodes(self):
        pass


class Episode(BaseEpisode):
    def get_videos(self):
        pass

    async def a_get_videos(self):
        pass


class Video(BaseVideo):
    pass
