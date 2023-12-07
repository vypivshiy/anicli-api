import re
from dataclasses import dataclass
from typing import Dict, List, Union

import chompjs

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.player.base import Video  # direct make this object


class VostAPI:
    """dummy animevost API implementation"""

    HTTP = BaseExtractor.HTTP
    HTTP_ASYNC = BaseExtractor.HTTP_ASYNC
    BASE_URL = "https://api.animevost.org/v1/"

    def api_request(self, method: str, *, api_method: str, **kwargs) -> Union[Dict, List[Dict]]:
        response = self.HTTP().request(method, self.BASE_URL + api_method, **kwargs)
        return response.json()

    async def a_api_request(self, method: str, *, api_method: str, **kwargs) -> Union[Dict, List[Dict]]:
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
    BASE_URL = "https://api.animevost.org/v1/"
    API = VostAPI()

    @classmethod
    def __extract_meta_data(cls, kw: dict) -> dict:
        """standardize API response for objects"""
        # playlist = cls.API.playlist(kw['id'])
        # get total episodes
        if match := re.search(r"\s(\d+).?\]", kw["title"]):
            total = int(match[1]) if match[1].isdigit() else -1
        else:
            total = -1
        return dict(
            title=kw["title"],
            thumbnail=kw["urlImagePreview"],
            url=cls.BASE_URL,
            # anime meta
            _alt_titles=[],  # stored to title key
            _description=kw["description"],
            _genres=kw["genre"].split(","),
            _episodes_available=len(chompjs.parse_js_object(kw["series"]).keys()),
            _episodes_total=total,
            _aired=kw["year"],  # TODO convert to date
            # episodes and video meta key. Get from API.playlist method
            _id=kw["id"],  # extract playlist key
        )

    def search(self, query: str) -> List["Search"]:
        # search entrypoint
        return [Search(**(self.__extract_meta_data(kw))) for kw in VostAPI().search(query)["data"]]

    async def a_search(self, query: str) -> List["Search"]:
        # async search entrypoint
        return [Search(**kw) for kw in (await VostAPI().a_search(query))["data"]]

    def ongoing(self) -> List["Ongoing"]:
        # ongoing entrypoint
        return [Ongoing(**(self.__extract_meta_data(kw))) for kw in VostAPI().last()["data"]]

    async def a_ongoing(self) -> List["Ongoing"]:
        # async ongoing entrypoint
        return [Ongoing(**kw) for kw in (await VostAPI().a_last())["data"]]


@dataclass
class _SearchOrOngoing:
    # TODO add convert camel case to snake case
    title: str
    thumbnail: str
    url: str
    # anime meta
    _alt_titles: List[str]
    _description: str
    _genres: List[str]
    _episodes_available: int
    _episodes_total: int
    _aired: str  # TODO convert to date
    # episodes and video meta key. Get playlist from API.playlist method
    _id: int

    def __str__(self):
        return self.title

    def get_anime(self) -> "Anime":
        playlist = VostAPI().playlist(self._id)
        # if response contains one episode - return dict else list[dict]
        if isinstance(playlist, dict):
            playlist = [playlist]
        return Anime(
            title=self.title,
            alt_titles=self._alt_titles,
            thumbnail=self.thumbnail,
            description=self._description,
            genres=self._genres,
            episodes_available=self._episodes_available,
            episodes_total=self._episodes_total,
            aired=self._aired,
            _playlist=playlist,
        )

    async def a_get_anime(self) -> "Anime":
        playlist = await VostAPI().a_playlist(self._id)
        if isinstance(playlist, dict):
            playlist = [playlist]
        return Anime(
            thumbnail=self.thumbnail,
            title=self.title,
            alt_titles=self._alt_titles,
            description=self._description,
            genres=self._genres,
            episodes_available=self._episodes_available,
            episodes_total=self._episodes_total,
            aired=self._aired,
            _playlist=playlist,
        )


@dataclass
class Search(_SearchOrOngoing, BaseSearch):
    pass


@dataclass
class Ongoing(_SearchOrOngoing, BaseOngoing):
    pass


@dataclass
class Anime(BaseAnime):
    title: str
    alt_titles: List[str]
    thumbnail: str
    description: str
    genres: List[str]
    episodes_available: int
    episodes_total: int
    aired: str  # int?
    # playlist
    _playlist: List[dict]

    def __str__(self):
        return f"{self.title} ({', '.join(self.alt_titles)})"

    async def a_get_episodes(self) -> List["Episode"]:
        return self.get_episodes()

    def get_episodes(self) -> List["Episode"]:
        return [
            Episode(
                title=kw["name"],
                num=str(i),
                # video meta
                _hd=kw["hd"],
                _std=kw["std"],
            )
            for i, kw in enumerate(self._playlist, 1)
        ]


@dataclass
class Episode(BaseEpisode):
    # video meta
    _hd: str
    _std: str

    async def a_get_sources(self) -> List["Source"]:
        return self.get_sources()

    def get_sources(self) -> List["Source"]:
        return [Source(title="Animevost", url="https://api.animevost.org", hd=self._hd, std=self._std)]

    def __str__(self):
        return self.title


@dataclass
class Source(BaseSource):
    hd: str
    std: str

    def get_videos(self, **_) -> List[Video]:
        return [
            Video(type="mp4", quality=480, url=self.std),
            Video(type="mp4", quality=720, url=self.hd),
        ]

    async def a_get_videos(self, **_) -> List[Video]:
        return self.get_videos()


if __name__ == "__main__":
    print(Extractor().search("lai")[0].get_anime().get_episodes()[0].get_sources())
    print(Extractor().ongoing()[0].get_anime().get_episodes()[0].get_sources())
