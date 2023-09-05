from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource, MainSchema
from anicli_api.player.base import Video


class Anilibria:
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
    API = Anilibria()

    def search(self, query: str) -> List["Search"]:
        # search entrypoint
        return [Search.from_kwargs(**kw) for kw in self.API.search_titles(search=query)]

    async def a_search(self, query: str) -> List["Search"]:
        # async search entrypoint
        return [Search.from_kwargs(**kw) for kw in (await self.API.a_search_titles(search=query))]

    def ongoing(self) -> List["Ongoing"]:
        # ongoing entrypoint
        return [Ongoing.from_kwargs(**kw) for kw in self.API.get_updates()]

    async def a_ongoing(self) -> List["Ongoing"]:
        # async ongoing entrypoint
        return [Ongoing.from_kwargs(**kw) for kw in (await self.API.a_get_updates())]


class _SearchOrOngoing(MainSchema):
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

    def dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "names": self.names,
            "announce": self.announce,
            "status": self.status,
            "posters": self.posters,
            "updated": self.updated,
            "last_change": self.last_change,
            "type": self.type,
            "genres": self.genres,
            "team": self.team,
            "season": self.season,
            "description": self.description,
            "in_favorites": self.in_favorites,
            "blocked": self.blocked,
            "player": self.player,
            "torrents": self.torrents,
        }

    async def a_get_anime(self) -> "Anime":
        return self.get_anime()

    def get_anime(self) -> "Anime":
        return Anime.from_kwargs(**self.__dict__)  # dict() method didn't see annotated attrs

    def __str__(self):
        return f"{list(self.names.values())[0]}"


class Search(_SearchOrOngoing, BaseSearch):
    pass


class Ongoing(_SearchOrOngoing, BaseOngoing):
    pass


class Anime(BaseAnime):
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

    def dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "names": self.names,
            "announce": self.announce,
            "status": self.status,
            "posters": self.posters,
            "updated": self.updated,
            "last_change": self.last_change,
            "type": self.type,
            "genres": self.genres,
            "team": self.team,
            "season": self.season,
            "description": self.description,
            "in_favorites": self.in_favorites,
            "blocked": self.blocked,
            "player": self.player,
            "torrents": self.torrents,
        }

    def __str__(self):
        return f"{list(self.names.values())}"

    def get_episodes(self) -> List["Episode"]:
        return [
            Episode.from_kwargs(
                alternative_player=self.player["alternative_player"],
                host=self.player["host"],
                torrents=self.torrents["list"],
                **p,
            )
            for p in self.player["playlist"].values()
        ]

    async def a_get_episodes(self) -> List["Episode"]:
        return self.get_episodes()


class Episode(BaseEpisode):
    alternative_player: Optional[str]
    host: str
    serie: int
    created_timestamp: int
    preview: Optional[Any]
    skips: dict
    hls: dict
    torrents: dict

    def dict(self) -> Dict[str, Any]:
        return {
            "alternative_player": self.alternative_player,
            "host": self.host,
            "serie": self.serie,
            "created_timestamp": self.created_timestamp,
            "preview": self.preview,
            "skips": self.skips,
            "hls": self.hls,
            "torrents": self.torrents,
        }

    def __str__(self):
        return f"{self.host} {self.serie}"

    def get_sources(self) -> List["Source"]:
        return [
            Source.from_kwargs(
                torrents=self.torrents,
                # dirty hack for success url validate for decoder.anilibria :D
                url=self.hls["sd"],
                **{k: f"https://{self.host}{v}" if v else None for k, v in self.hls.items()},
            )
        ]

    async def a_get_sources(self) -> List["Source"]:
        return self.get_sources()


class Source(BaseSource):
    torrents: dict
    fhd: Optional[str]
    hd: str
    sd: str

    def dict(self) -> Dict[str, Any]:
        return {"torrents": self.torrents, "fhd": self.fhd, "hd": self.hd, "sd": self.sd}

    def __str__(self):
        return f"{urlsplit(self.fhd).netloc or urlsplit(self.hd).netloc}"

    def get_videos(self) -> List["Video"]:
        if self.fhd:
            return [
                Video(type="m3u8", quality=480, url=self.sd),
                Video(type="m3u8", quality=720, url=self.hd),
                Video(type="m3u8", quality=1080, url=self.fhd),
            ]
        return [
            Video(type="m3u8", quality=480, url=self.sd),
            Video(type="m3u8", quality=720, url=self.hd),
        ]

    async def a_get_videos(self) -> List["Video"]:
        return self.get_videos()


if __name__ == "__main__":
    ex = Extractor()
    r = ex.search("lai")
    an = r[0].get_anime()
    eps = an.get_episodes()
    sss = eps[0].get_sources()
    vids = sss[0].get_videos()
    print(*vids)
