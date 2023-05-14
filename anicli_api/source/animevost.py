from typing import List, Union, Dict

from anicli_api.base import (
    BaseAnime,
    BaseEpisode,
    BaseExtractor,
    BaseOngoing,
    BaseSearch,
    BaseSource,
    MainSchema,
)
from anicli_api.player.base import Video


class VostAPI:
    """dummy animevost API implementation"""

    HTTP = BaseExtractor.HTTP
    HTTP_ASYNC = BaseExtractor.HTTP_ASYNC
    BASE_URL = "https://api.animevost.org/v1/"

    def api_request(self, method: str, *, api_method: str, **kwargs) -> Union[Dict, List[Dict]]:
        response = self.HTTP().request(method, self.BASE_URL + api_method, **kwargs)
        return response.json()

    async def a_api_request(
        self, method: str, *, api_method: str, **kwargs
    ) -> Union[Dict, List[Dict]]:
        async with self.HTTP_ASYNC() as session:
            response = await session.request(method, self.BASE_URL + api_method, **kwargs)
            return response.json()

    @staticmethod
    def _kwargs_pop_params(kwargs, **params) -> dict:
        data = kwargs.pop("params") if kwargs.get("params") else {}
        data.update(params)
        return data

    def search(self, search: str, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, name=search)
        return self.api_request("POST", api_method="search", data=params, **kwargs)  # type: ignore

    async def a_search(self, search: str, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, name=search)
        return await self.a_api_request("POST", api_method="search", data=params, **kwargs)  # type: ignore

    def last(self, *, limit: int = 20, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, page=1, quantity=limit)
        return self.api_request("GET", api_method="last", params=params, **kwargs)  # type: ignore

    async def a_last(self, *, limit: int = 20, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, page=1, quantity=limit)
        return await self.a_api_request("GET", api_method="last", params=params, **kwargs)  # type: ignore

    def playlist(self, id: int) -> List[Dict]:
        return self.api_request("POST", api_method="playlist", data={"id": id})  # type: ignore

    async def a_playlist(self, id: int) -> List[Dict]:
        return await self.a_api_request("POST", api_method="playlist", data={"id": id})  # type: ignore


class Extractor(BaseExtractor):
    API = VostAPI()

    def search(self, query: str) -> List["Search"]:
        # search entrypoint
        return [Search.from_kwargs(**kw) for kw in VostAPI().search(query)["data"]]

    async def a_search(self, query: str) -> List["Search"]:
        # async search entrypoint
        return [Search.from_kwargs(**kw) for kw in (await VostAPI().a_search(query))["data"]]

    def ongoing(self) -> List["Ongoing"]:
        # ongoing entrypoint
        return [Ongoing.from_kwargs(**kw) for kw in VostAPI().last()["data"]]

    async def a_ongoing(self) -> List["Ongoing"]:
        # async ongoing entrypoint
        return [Ongoing.from_kwargs(**kw) for kw in (await VostAPI().a_last())["data"]]


class _SearchOrOngoing(MainSchema):
    # TODO add convert camel case to snake case
    id: int
    title: str
    description: str
    genre: str
    year: str
    urlImagePreview: str
    screenImage: List[str]
    isFavorite: int
    isLikes: int
    rating: int
    votes: int
    timer: int
    type: str
    director: str
    series: str  # '{\'1 серия\':\'147459278\ ...'

    def get_anime(self) -> "Anime":
        response = VostAPI().playlist(self.id)
        return Anime.from_kwargs(**self.dict(), playlist=response)

    async def a_get_anime(self) -> "Anime":
        response = await VostAPI().a_playlist(self.id)
        return Anime.from_kwargs(**self.dict(), playlist=response)


class Search(_SearchOrOngoing, BaseSearch):
    pass


class Ongoing(_SearchOrOngoing, BaseOngoing):
    pass


class Anime(BaseAnime):
    id: int
    title: str
    description: str
    genre: str
    year: str
    urlImagePreview: str
    screenImage: List[str]
    isFavorite: int
    isLikes: int
    rating: int
    votes: int
    timer: int
    type: str
    director: str
    series: str  # '{\'1 серия\':\'147459278\ ...'
    playlist: List[Dict]

    async def a_get_episodes(self) -> List["Episode"]:
        return self.get_episodes()

    def get_episodes(self) -> List["Episode"]:
        return [Episode.from_kwargs(**kw) for kw in self.playlist]

    def __str__(self):
        return f"{self.title} {self.year} {self.rating}\n{self.genre}\n{self.description}"


class Episode(BaseEpisode):
    name: str
    preview: str

    # video meta
    hd: str
    std: str

    async def a_get_sources(self) -> List["Source"]:
        return self.get_sources()

    def get_sources(self) -> List["Source"]:
        return [Source.from_kwargs(hd=self.hd, std=self.std)]

    def __str__(self):
        return f"{self.name}"


class Source(BaseSource):
    hd: str
    std: str

    def get_videos(self) -> List[Video]:
        return [
            Video(type="mp4", quality=480, url=self.std),
            Video(type="mp4", quality=720, url=self.hd),
        ]

    async def a_get_videos(self) -> List[Video]:
        return self.get_videos()
