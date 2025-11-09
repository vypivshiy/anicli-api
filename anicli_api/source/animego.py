import logging
import re
from typing import Dict, List

from attr import field
from attrs import define
from httpx import Response

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.source.parsers.animego_parser import (
    PageAnime,
    PageEpisode,
    PageOngoing,
    PageSearch,
    PageSource,
    PageEpisodeVideo,
    PageUtils,
    J_Content,
    T_EpisodeVideoPlayersView,
)

logger = logging.getLogger("anicli-api")


# test not available players in country
RE_PLAYER_BLOCKED = re.compile(
    r'<div\b[^>]*\bclass\s*=\s*["\'][^"\']*\bplayer-blocked\b[^"\']*["\'][^>]*>', flags=re.IGNORECASE
)
# (msg text)
RE_DIV_H5_ERR = re.compile(
    r'<div\b([^>]*)\bclass\s*=\s*["\'][^"\']*\bh5\b[^"\']*["\']([^>]*)>(.*?)</div>', flags=re.IGNORECASE | re.DOTALL
)


class Extractor(BaseExtractor):
    BASE_URL = "https://animego.one"

    def _extract_search(self, resp: str) -> List["Search"]:
        return [Search(**d, **self._kwargs_http) for d in PageSearch(resp).parse()]

    @staticmethod
    def _remove_ongoings_dups(ongoings: List["Ongoing"]) -> List["Ongoing"]:
        # remove duplicates and accumulate by episode and dubber keys
        sorted_ongs: Dict[int, "Ongoing"] = {}
        for ong in ongoings:
            key = hash(ong.url + ong.episode)
            if sorted_ongs.get(key):
                sorted_ongs[key].dub += f", {ong.dub}"
            else:
                sorted_ongs[key] = ong
        return list(sorted_ongs.values())

    def _extract_ongoing(self, resp: str) -> List["Ongoing"]:
        netloc = PageUtils(resp).parse()["url_canonical"]

        ongs = []
        for d in PageOngoing(resp).parse():
            url = netloc + d["url_path"]
            ongs.append(
                Ongoing(
                    title=d["title"],
                    thumbnail=d["thumbnail"],
                    episode=d["episode"],
                    dub=d["dub"],
                    url=url,
                    **self._kwargs_http,
                )
            )

        return self._remove_ongoings_dups(ongs)

    def search(self, query: str) -> List["Search"]:
        resp = self.http.get(f"{self.BASE_URL}/search/anime", params={"q": query})
        return self._extract_search(resp.text)

    async def a_search(self, query: str) -> List["Search"]:
        resp = await self.http_async.get(f"{self.BASE_URL}/search/anime", params={"q": query})
        return self._extract_search(resp.text)

    def ongoing(self) -> List["Ongoing"]:
        resp = self.http.get(self.BASE_URL)
        return self._extract_ongoing(resp.text)

    async def a_ongoing(self) -> List["Ongoing"]:
        resp = await self.http_async.get(self.BASE_URL)
        return self._extract_ongoing(resp.text)


@define(kw_only=True)
class Search(BaseSearch):
    def get_anime(self) -> "Anime":
        resp = self.http.get(self.url)
        return self._extract(resp.text) if self._is_valid_page(resp) else self._create_anime()

    async def a_get_anime(self) -> "Anime":
        resp = await self.http_async.get(self.url)
        return self._extract(resp.text) if self._is_valid_page(resp) else self._create_anime()

    def _extract(self, resp: str) -> "Anime":
        return Anime(**PageAnime(resp).parse(), **self._kwargs_http)

    @staticmethod
    def _is_valid_page(resp: Response) -> bool:
        # RKN blocks issues eg:
        # https://animego.one/anime/ya-predpochitayu-zlodeyku-2413
        # but API requests MAYBE still work.
        if resp.is_success:
            return True

        title = re.search(r"<title>(.*?)</title>", resp.text)[1]  # type: ignore
        logger.warning(
            "%s returns status code [%s] title='%s' content-length=%s",
            resp.url,
            resp.status_code,
            title,
            len(resp.content),
        )
        return False

    def _create_anime(self) -> "Anime":
        # skip extract metadata and manually create the object (API requests maybe still works)
        return Anime(
            title=self.title,
            thumbnail=self.thumbnail,
            description="",
            # id for API requests contains in url
            id=self.url.split("-")[-1],
            raw_json={},  # type: ignore
            **self._kwargs_http,
        )


@define(kw_only=True)
class Ongoing(BaseOngoing):
    episode: str
    dub: str

    def _extract(self, resp: str) -> "Anime":
        return Anime(**PageAnime(resp).parse(), **self._kwargs_http)

    @staticmethod
    def _is_valid_page(resp: Response) -> bool:
        # RKN blocks issues eg:
        # https://animego.one/anime/ya-predpochitayu-zlodeyku-2413
        # but API requests MAYBE still work.
        if resp.is_success:
            return True

        title = re.search(r"<title>(.*?)</title>", resp.text)[1]  # type: ignore
        logger.warning(
            "%s returns status code [%s] title='%s' content-length=%s",
            resp.url,
            resp.status_code,
            title,
            len(resp.content),
        )
        return False

    def _create_anime(self) -> "Anime":
        # skip extract metadata, and manual creates the object (API requests MAYBE still works)
        return Anime(
            title=self.title,
            thumbnail=self.thumbnail,
            description="",
            id=self.url.split("-")[-1],
            raw_json={},  # type: ignore
            **self._kwargs_http,
        )

    def get_anime(self) -> "Anime":
        resp = self.http.get(self.url)
        return self._extract(resp.text) if self._is_valid_page(resp) else self._create_anime()

    async def a_get_anime(self) -> "Anime":
        resp = await self.http_async.get(self.url)
        return self._extract(resp.text) if self._is_valid_page(resp) else self._create_anime()

    def __str__(self):
        return f"{self.title} {self.episode} ({self.dub})"


@define(kw_only=True)
class Anime(BaseAnime):
    id: str
    raw_json: J_Content

    def _extract(self, resp: str) -> List["Episode"]:
        # magic string:
        # carousel implemented only for episodes
        # film, OVA not exists this feature
        if 'id="video-carousel"' not in resp:
            film_data = PageEpisodeVideo(resp).parse()
            return [
                Episode(
                    title=self.title,
                    ordinal=1,
                    id=self.id,  # STUB
                    dubbers=film_data["dubbers"],
                    videos=film_data["videos"],
                    is_film=film_data["is_film"],  # true
                    **self._kwargs_http,
                ),
            ]

        episodes_data = PageEpisode(resp).parse()
        return [
            Episode(
                dubbers=episodes_data["dubbers"],
                ordinal=int(d["num"]),
                title=d["title"],
                id=d["id"],
                videos=[],  # stub, used in film object
                **self._kwargs_http,
            )
            for d in episodes_data["episodes"]
        ]

    @staticmethod
    def _episodes_is_available(response: str) -> bool:
        # RKN issue: maybe title not available in your country
        # eg:
        # https://animego.one/anime/vtorzhenie-gigantov-2-17
        # this title API request don't work in RU ip
        if RE_PLAYER_BLOCKED.search(response):
            element = RE_DIV_H5_ERR.search(response)
            element = element[0] if element else ""
            logger.error("API not available in your country. Element: %s", element)
            return False
        return True

    def get_episodes(self) -> List["Episode"]:
        resp = self.http.get(f"https://animego.one/anime/{self.id}/player?_allow=true")
        resp = resp.json()["content"]
        return self._extract(resp) if self._episodes_is_available(resp) else []

    async def a_get_episodes(self) -> List["Episode"]:
        resp = await self.http_async.get(f"https://animego.one/anime/{self.id}/player?_allow=true")
        resp = resp.json()["content"]
        return self._extract(resp) if self._episodes_is_available(resp) else []


@define(kw_only=True)
class Episode(BaseEpisode):
    dubbers: Dict[str, str]
    id: str  # episode id (for extract videos required)
    _is_film: bool = field(alias="is_film", default=False)
    _videos: List[T_EpisodeVideoPlayersView] = field(alias="videos")

    def _extract(self, resp: str):
        data = PageSource(resp).parse()
        dubbers_ = data["dubbers"]
        data_source = [
            {"title": dubbers_.get(d["data_provide_dubbing"], "???"), "url": d["url"]} for d in data["videos"]
        ]
        return [Source(**d, **self._kwargs_http) for d in data_source]

    def _extract_film(self):
        return [
            Source(
                # FIXME: sideeffect: dubber name duplicate
                title=self.dubbers.get(v["data_provide_dubbing"], "???").split()[0],
                url=v["player"],
                **self._kwargs_http,
            )
            for v in self._videos
        ]

    def get_sources(self):
        if self._is_film:
            return self._extract_film()
        resp = self.http.get(
            "https://animego.one/anime/series",
            params={"dubbing": 2, "provider": 24, "episode": self.num, "id": self.id},
        ).json()["content"]
        return self._extract(resp)

    async def a_get_sources(self):
        if self._is_film:
            return self._extract_film()
        resp = (
            await self.http_async.get(
                "https://animego.one/anime/series",
                params={"dubbing": 2, "provider": 24, "episode": self.num, "id": self.id},
            )
        ).json()["content"]
        return self._extract(resp)


@define(kw_only=True)
class Source(BaseSource):
    pass


if __name__ == "__main__":
    from anicli_api.tools import cli

    cli(Extractor())
