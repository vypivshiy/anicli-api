"""
TODO sort keys for objects
"""
from typing import Optional, Any

from anicli_api.base import *

__all__ = (
    'Extractor',
    'SearchResult',
    'Ongoing',
    'AnimeInfo',
    'Episode',
    'Video',
    'TestCollections'
)


class Anilibria:
    """ For details see docs on https://github.com/anilibria/docs/blob/master/api_v2.md"""
    HTTP = BaseAnimeExtractor.HTTP
    HTTP_ASYNC = BaseAnimeExtractor.HTTP_ASYNC

    BASE_URL = "https://api.anilibria.tv/v2/"

    def api_request(self, method: str = "GET", *, api_method: str, **kwargs) -> dict:
        response = self.HTTP().request(method=method, url=f'{self.BASE_URL}{api_method}', **kwargs)
        return response.json()

    async def a_api_request(self, method: str = "GET", *, api_method: str, **kwargs) -> dict:
        async with self.HTTP_ASYNC() as session:
            response = await session.request(method, self.BASE_URL + api_method, **kwargs)
            return response.json()

    @staticmethod
    def _kwargs_pop_params(kwargs, **params) -> dict:
        data = kwargs.pop("params") if kwargs.get("params") else {}
        data.update(params)
        return data

    def search_titles(self, *, search: str, limit: int = -1, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, search=search, limit=limit)
        return self.api_request(api_method="searchTitles", params=params, **kwargs)

    async def a_search_titles(self, *, search: str, limit: int = -1, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, limit=limit)
        return await self.a_api_request(api_method="searchTitles", params=params, **kwargs)

    def get_updates(self, *, limit: int = -1, **kwargs) -> dict:
        """getUpdates method
        :param limit:
        :param kwargs:
        :return:
        """
        params = self._kwargs_pop_params(kwargs, limit=limit)
        return self.api_request(api_method="getUpdates", data=params, **kwargs)

    async def a_get_updates(self, *, limit: int = -1, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, limit=limit)
        return await self.a_api_request(api_method="getUpdates", data=params, **kwargs)


class Extractor(BaseAnimeExtractor):
    # optional constants, HTTP configuration here
    """ For details see docs on https://github.com/anilibria/docs/blob/master/api_v2.md"""
    BASE_URL = "https://api.anilibria.tv/v2/"
    ANILIBRIA = Anilibria()

    def search(self, query: str) -> List[BaseSearchResult]:
        return [SearchResult(**kw) for kw in self.ANILIBRIA.search_titles(search=query)]

    def ongoing(self) -> List[BaseOngoing]:
        return [Ongoing(**kw) for kw in self.ANILIBRIA.get_updates()]

    async def async_search(self, query: str) -> List[BaseSearchResult]:
        # past async code here
        return [SearchResult(**kw) for kw in (await self.ANILIBRIA.a_search_titles(search=query))]

    async def async_ongoing(self) -> List[BaseOngoing]:
        # past async code here
        return [Ongoing(**kw) for kw in (await self.ANILIBRIA.a_get_updates())]


class SearchResult(BaseSearchResult):
    # TODO typing keys better
    id: int
    code: str
    names: dict
    announce: Optional[Any]
    status: dict
    posters: dict
    updated: int
    last_change: int
    type: dict
    genres: List[str]
    team: dict
    season: dict
    description: str
    in_favorites: int
    blocked: dict
    player: dict
    torrents: dict

    async def a_get_anime(self) -> 'AnimeInfo':
        return AnimeInfo(**self.dict())

    def get_anime(self) -> 'AnimeInfo':
        return AnimeInfo(**self.dict())


class Ongoing(BaseOngoing):
    # TODO typing keys better
    id: int
    code: str
    names: dict
    announce: Optional[Any]
    status: dict
    posters: dict
    updated: int
    last_change: int
    type: dict
    genres: List[str]
    team: dict
    season: dict
    description: str
    in_favorites: int
    blocked: dict
    player: dict
    torrents: dict

    async def a_get_anime(self) -> 'AnimeInfo':
        return AnimeInfo(**self.dict())

    def get_anime(self) -> 'AnimeInfo':
        return AnimeInfo(**self.dict())


class AnimeInfo(BaseAnimeInfo):
    # TODO typing keys better
    id: int
    code: str
    names: dict
    announce: Optional[Any]
    status: dict
    posters: dict
    updated: int
    last_change: int
    type: dict
    genres: List[str]
    team: dict
    season: dict
    description: str
    in_favorites: int
    blocked: dict
    player: dict
    torrents: dict

    async def a_get_episodes(self) -> List['BaseEpisode']:
        return [Episode(alternative_player=self.player["alternative_player"],
                        host=self.player["host"],
                        torrents=self.torrents["list"], **p) for p in self.player["playlist"].values()]

    def get_episodes(self) -> List['BaseEpisode']:
        return [Episode(alternative_player=self.player["alternative_player"],
                        host=self.player["host"],
                        torrents=self.torrents["list"], **p) for p in self.player["playlist"].values()]


class Episode(BaseEpisode):
    alternative_player: Optional[str]
    host: str
    serie: int
    created_timestamp: int
    preview: Optional[Any]
    skips: dict
    hls: dict
    torrents: dict

    async def a_get_videos(self) -> List['BaseVideo']:
        return [Video(torrents=self.torrents,
                **{k: f"https://{self.host}{v}" if v else None for k, v in self.hls.items()})]

    def get_videos(self) -> List['BaseVideo']:
        return [Video(torrents=self.torrents,
                **{k: f"https://{self.host}{v}" if v else None for k, v in self.hls.items()})]


class Video(BaseVideo):
    torrents: dict
    fhd: Optional[str]
    hd: str
    sd: str

    def get_source(self):
        return self.dict()

    def a_get_source(self):
        return self.dict()


class TestCollections(BaseTestCollections):
    def test_search(self):
        resp = Extractor().search("Зомбиленд")
        assert resp[0].dict()["id"] == 7474
        assert resp[1].dict()["id"] == 8960

    def test_ongoing(self):
        resp = Extractor().ongoing()
        assert len(resp) > 1

    def test_extract_metadata(self):
        for meta in Extractor().search("Зомбиленд")[0]:
            assert meta["search"]["id"] == 7474
            assert meta["search"]["code"] == "zombieland-saga"
            assert meta["search"]["genres"] == ['Комедия', 'Сверхъестественное', 'Ужасы', 'Экшен']

    def test_extract_video(self):
        search = Extractor().search("Зомбиленд")[0]
        anime = search.get_anime()
        episodes = anime.get_episodes()
        video = episodes[0].get_videos()[0]
        assert video.dict()["fhd"] is None
        assert "libria.fun" in video.dict()["hd"]
        assert "libria.fun" in video.dict()["sd"]
