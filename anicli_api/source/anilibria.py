from dataclasses import dataclass
from typing import List, Union

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.player.base import Video  # direct make this object


class AnilibriaAPI:
    """Dummmy API interface
    https://github.com/anilibria/docs/blob/master/api_v2.md
    """

    HTTP = BaseExtractor.HTTP
    HTTP_ASYNC = BaseExtractor.HTTP_ASYNC

    BASE_URL = "https://api.anilibria.tv/v2/"

    def api_request(self, method: str = "GET", *, api_method: str, **kwargs) -> dict:
        response = self.HTTP().request(method=method, url=f"{self.BASE_URL}{api_method}", **kwargs)
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


class Extractor(BaseExtractor):
    BASE_URL = "https://api.anilibria.tv/v2/"  # BASEURL
    API = AnilibriaAPI()

    @classmethod
    def __extract_meta_data(cls, kw: dict) -> dict:
        """extract response data for anicli application"""
        return dict(
            title=kw["names"]["ru"],
            url=cls.BASE_URL,
            thumbnail=f"https://{kw['player']['host']}{kw['posters']['small']['url']}",
            # anime_info meta
            _alt_titles=[kw["names"][n] for n in kw["names"].keys() if kw["names"][n] is not None and n != "ru"],
            _description=kw["description"],
            _genres=kw["genres"],
            _episodes_available=kw["torrents"]["series"]["last"],
            _episodes_total=kw["type"]["series"],
            _aired=kw["season"]["year"],  # TODO format to full date
            # episodes and video meta
            _episodes_and_videos=kw["player"]["playlist"],
            _host=kw["player"]["host"],
        )

    def search(self, query: str) -> List["Search"]:
        return [Search(**self.__extract_meta_data(kw)) for kw in self.API.search_titles(search=query)]

    async def a_search(self, query: str) -> List["Search"]:
        return [Search(**self.__extract_meta_data(kw)) for kw in (await self.API.a_search_titles(search=query))]

    def ongoing(self) -> List["Ongoing"]:
        return [Ongoing(**self.__extract_meta_data(kw)) for kw in self.API.get_updates()]

    async def a_ongoing(self) -> List["Ongoing"]:
        return [Ongoing(**self.__extract_meta_data(kw)) for kw in (await self.API.a_get_updates())]


@dataclass
class _SearchOrOngoing:
    url: str
    title: str
    thumbnail: str
    # AnimeInfo meta
    _alt_titles: List[str]
    _description: str
    _genres: List[str]
    _episodes_available: int
    _episodes_total: int
    _aired: str
    # Episode and Video meta
    _episodes_and_videos: dict
    _host: str

    async def a_get_anime(self) -> "Anime":
        return self.get_anime()

    def get_anime(self) -> "Anime":
        return Anime(
            title=self.title,
            alt_title=self._alt_titles,
            description=self._description,
            thumbnail=self.thumbnail,
            genres=self._genres,
            episodes_available=self._episodes_available,
            episodes_total=self._episodes_total,
            aired=self._aired,
            _episodes_and_videos=self._episodes_and_videos,
            _host=self._host,
        )

    def __str__(self):
        return self.title


@dataclass
class Search(_SearchOrOngoing, BaseSearch):
    pass


@dataclass
class Ongoing(_SearchOrOngoing, BaseOngoing):
    pass


@dataclass
class Anime(BaseAnime):
    title: str
    alt_title: List[str]
    thumbnail: str
    description: str
    genres: List[str]
    episodes_available: int
    episodes_total: int
    aired: Union[str, int]
    _episodes_and_videos: dict
    _host: str

    def __str__(self):
        return self.title

    def get_episodes(self) -> List["Episode"]:
        return [
            Episode(
                title=f"Episode {num}",
                num=item["serie"],
                _fhd=f"https://{self._host}{item['hls']['fhd']}",
                _hd=f"https://{self._host}{item['hls']['hd']}",
                _sd=f"https://{self._host}{item['hls']['sd']}",
            )
            for num, item in self._episodes_and_videos.items()
        ]

    async def a_get_episodes(self) -> List["Episode"]:
        return self.get_episodes()


@dataclass
class Episode(BaseEpisode):
    title: str
    num: Union[int, str]  # type: ignore
    # video meta
    _fhd: str
    _hd: str
    _sd: str

    def __str__(self):
        return self.title

    def get_sources(self) -> List["Source"]:
        return [Source(title="Anilibria", url="https://api.anilibria.tv", _fhd=self._fhd, _hd=self._hd, _sd=self._sd)]

    async def a_get_sources(self) -> List["Source"]:
        return self.get_sources()


@dataclass
class Source(BaseSource):
    url: str
    title: str
    _fhd: str
    _hd: str
    _sd: str

    def get_videos(self, **_) -> List["Video"]:
        if self._fhd:
            return [
                Video(type="m3u8", quality=480, url=self._sd),
                Video(type="m3u8", quality=720, url=self._hd),
                Video(type="m3u8", quality=1080, url=self._fhd),
            ]
        return [
            Video(type="m3u8", quality=480, url=self._sd),
            Video(type="m3u8", quality=720, url=self._hd),
        ]

    async def a_get_videos(self, **_) -> List["Video"]:
        return self.get_videos()


if __name__ == "__main__":
    print(Extractor().search("lai")[0].get_anime().get_episodes()[0].get_sources())
    print(Extractor().ongoing()[0].get_anime().get_episodes()[0].get_sources())
