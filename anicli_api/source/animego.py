import logging
import re
from typing import Dict, List

from attrs import define
from httpx import Response
from parsel import Selector

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.source.parsers.animego_parser import (
    AnimePage,
    EpisodePage,
    OngoingPage,
    SearchPage,
    SourcePage,
    J_Content,
    EpisodeVideoPage,
    T_EpisodeVideoPlayersView,
)

_logger = logging.getLogger("anicli-api")  # type: ignore


class Extractor(BaseExtractor):
    BASE_URL = "https://animego.one"

    def _extract_search(self, resp: str):
        return [Search(**d, **self._kwargs_http) for d in SearchPage(resp).parse()]

    @staticmethod
    def _remove_ongoings_dups(ongoings: List["Ongoing"]):
        # remove duplicates and accumulate by episode and dubber keys
        sorted_ongs: Dict[int, "Ongoing"] = {}
        for ong in ongoings:
            key = hash(ong.url + ong.episode)
            if sorted_ongs.get(key):
                sorted_ongs[key].dub += f", {ong.dub}"
            else:
                sorted_ongs[key] = ong
        return list(sorted_ongs.values())

    def _extract_ongoing(self, resp: str):
        ongs = [Ongoing(**d, **self._kwargs_http) for d in OngoingPage(resp).parse()]
        return self._remove_ongoings_dups(ongs)

    def search(self, query: str):
        resp = self.http.get(f"{self.BASE_URL}/search/anime", params={"q": query})
        return self._extract_search(resp.text)

    async def a_search(self, query: str):
        resp = await self.http_async.get(f"{self.BASE_URL}/search/anime", params={"q": query})
        return self._extract_search(resp.text)

    def ongoing(self):
        resp = self.http.get(self.BASE_URL)
        return self._extract_ongoing(resp.text)

    async def a_ongoing(self):
        resp = await self.http_async.get(self.BASE_URL)
        return self._extract_ongoing(resp.text)


@define(kw_only=True)
class Search(BaseSearch):
    def get_anime(self):
        resp = self.http.get(self.url)
        return self._extract(resp.text) if self._is_valid_page(resp) else self._create_anime()

    async def a_get_anime(self):
        resp = await self.http_async.get(self.url)
        return self._extract(resp.text) if self._is_valid_page(resp) else self._create_anime

    def _extract(self, resp: str):
        return Anime(**AnimePage(resp).parse(), **self._kwargs_http)

    @staticmethod
    def _is_valid_page(resp: Response):
        # RKN blocks issues eg:
        # https://animego.one/anime/ya-predpochitayu-zlodeyku-2413
        # but API requests MAYBE still work.
        if resp.is_success:
            return True

        title = re.search(r"<title>(.*?)</title>", resp.text)[1]  # type: ignore
        _logger.warning(
            "%s returns status code [%s] title='%s' content-length=%s",
            resp.url,
            resp.status_code,
            title,
            len(resp.content),
        )
        return False

    def _create_anime(self):
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

    def _extract(self, resp: str):
        return Anime(**AnimePage(resp).parse(), **self._kwargs_http)

    @staticmethod
    def _is_valid_page(resp: Response):
        # RKN blocks issues eg:
        # https://animego.one/anime/ya-predpochitayu-zlodeyku-2413
        # but API requests MAYBE still work.
        if resp.is_success:
            return True

        title = re.search(r"<title>(.*?)</title>", resp.text)[1]  # type: ignore
        _logger.warning(
            "%s returns status code [%s] title='%s' content-length=%s",
            resp.url,
            resp.status_code,
            title,
            len(resp.content),
        )
        return False

    def _create_anime(self):
        # skip extract metadata, and manual creates the object (API requests MAYBE still works)
        return Anime(
            title=self.title,
            thumbnail=self.thumbnail,
            description="",
            id=self.url.split("-")[-1],
            raw_json={},  # type: ignore
            **self._kwargs_http,
        )

    def get_anime(self):
        resp = self.http.get(self.url)
        return self._extract(resp.text) if self._is_valid_page(resp) else self._create_anime()

    async def a_get_anime(self):
        resp = await self.http_async.get(self.url)
        return self._extract(resp.text) if self._is_valid_page(resp) else self._create_anime()

    def __str__(self):
        return f"{self.title} {self.episode} ({self.dub})"


@define(kw_only=True)
class Anime(BaseAnime):
    id: str
    raw_json: J_Content

    def _extract(self, resp: str):
        # magic string:
        # carousel implemented only for episodes
        # film, OVA not exists this feature
        if 'id="video-carousel"' not in resp:
            film_data = EpisodeVideoPage(resp).parse()
            return [
                Episode(
                    title=self.title,
                    num="1",
                    id=self.id,  # STUB
                    dubbers=film_data["dubbers"],
                    videos=film_data["videos"],
                    is_film=True,
                    **self._kwargs_http,
                ),
            ]

        episodes_data = EpisodePage(resp).parse()
        return [
            Episode(
                **d,
                dubbers=episodes_data["dubbers"],
                videos=[],  # stub
                **self._kwargs_http,
            )
            for d in episodes_data["episodes"]
        ]

    @staticmethod
    def _episodes_is_available(response: str):
        sel = Selector(response)
        # RKN issue: maybe title not available in your country
        # eg:
        # https://animego.one/anime/vtorzhenie-gigantov-2-17
        # this title API request don't work in RU ip
        # TODO: drop selector, rewrite in regex
        if sel.css("div.player-blocked").get():
            _logger.error("API not available in your country. Element: %s", sel.css("div.h5").get())
            return False
        return True

    def get_episodes(self):
        resp = self.http.get(f"https://animego.one/anime/{self.id}/player?_allow=true").json()["content"]
        return self._extract(resp) if self._episodes_is_available(resp) else []

    async def a_get_episodes(self):
        resp = await self.http_async.get(f"https://animego.one/anime/{self.id}/player?_allow=true")
        resp = resp.json()["content"]
        return self._extract(resp) if self._episodes_is_available(resp) else []


@define(kw_only=True)
class Episode(BaseEpisode):
    dubbers: Dict[str, str]
    id: str  # episode id (for extract videos required)
    _is_film: bool = False
    _videos: List[T_EpisodeVideoPlayersView]

    def _extract(self, resp: str):
        data = SourcePage(resp).parse()
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
