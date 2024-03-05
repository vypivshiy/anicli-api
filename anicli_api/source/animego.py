import logging
import re
from typing import Dict, List

from attrs import define
from httpx import Response
from parsel import Selector

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.source.parsers.animego_parser import (
    AnimeView,
    DubbersView,
    EpisodeView,
    OngoingView,
    SearchView,
    SourceView,
)

_logger = logging.getLogger("anicli-api")  # type: ignore


class Extractor(BaseExtractor):
    BASE_URL = "https://animego.org"

    def _extract_search(self, resp: str):
        data = SearchView(resp).parse().view()
        return [Search(**d, **self._kwargs_http) for d in data]

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
        data = OngoingView(resp).parse().view()
        ongs = [Ongoing(**d, **self._kwargs_http) for d in data]
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
    def _extract(self, resp: str):
        data = AnimeView(resp).parse().view()
        return Anime(**data, **self._kwargs_http)

    @staticmethod
    def _is_valid_page(resp: Response):
        # RKN blocks issues eg:
        # https://animego.org/anime/ya-predpochitayu-zlodeyku-2413
        # but API requests MAYBE still works.
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
        # skip extract metadata and manual create object (API requests maybe still works)
        return Anime(
            title=self.title,
            thumbnail=self.thumbnail,
            description="",
            # id for API requests contains in url
            id=self.url.split("-")[-1],
            raw_json="",
            **self._kwargs_http,
        )

    def get_anime(self):
        resp = self.http.get(self.url)
        if self._is_valid_page(resp):
            return self._extract(resp.text)
        return self._create_anime()

    async def a_get_anime(self):
        resp = await self.http_async.get(self.url)
        if self._is_valid_page(resp):
            return self._extract(resp.text)
        return self._create_anime()


@define(kw_only=True)
class Ongoing(BaseOngoing):
    episode: str
    dub: str

    def _extract(self, resp: str):
        data = AnimeView(resp).parse().view()
        return Anime(**data, **self._kwargs_http)

    @staticmethod
    def _is_valid_page(resp: Response):
        # RKN blocks issues eg:
        # https://animego.org/anime/ya-predpochitayu-zlodeyku-2413
        # but API requests MAYBE still works.
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
        # skip extract metadata, and manual create object (API requests still works)
        return Anime(
            title=self.title,
            thumbnail=self.thumbnail,
            description="",
            id=self.url.split("-")[-1],
            raw_json="",
            **self._kwargs_http,
        )

    def get_anime(self):
        resp = self.http.get(self.url)
        if self._is_valid_page(resp):
            return self._extract(resp.text)
        return self._create_anime()

    async def a_get_anime(self):
        resp = await self.http_async.get(self.url)
        if self._is_valid_page(resp):
            return self._extract(resp.text)
        return self._create_anime()

    def __str__(self):
        return f"{self.title} {self.episode} ({self.dub})"


@define(kw_only=True)
class Anime(BaseAnime):
    id: str
    raw_json: str

    def _extract(self, resp: str):
        episodes_data = EpisodeView(resp).parse().view()

        dubbers = DubbersView(resp).parse().view()
        return [Episode(**d, dubbers=dubbers, **self._kwargs_http) for d in episodes_data]

    @staticmethod
    def _episodes_is_available(response: str):
        sel = Selector(response)
        # RKN issue: maybe title not available in your country
        # eg:
        # https://animego.org/anime/vtorzhenie-gigantov-2-17
        # this title API request don't work in RU ip
        if sel.css("div.player-blocked").get():
            _logger.error("API not available in your country. Element: %s", sel.css("div.h5").get())
            return False
        return True

    def get_episodes(self):
        resp = self.http.get(f"https://animego.org/anime/{self.id}/player?_allow=true").json()["content"]
        return self._extract(resp) if self._episodes_is_available(resp) else []

    async def a_get_episodes(self):
        resp = await self.http_async.get(f"https://animego.org/anime/{self.id}/player?_allow=true")
        resp = resp.json()["content"]
        return self._extract(resp) if self._episodes_is_available(resp) else []


@define(kw_only=True)
class Episode(BaseEpisode):
    dubbers: Dict[str, str]
    id: str  # episode id (for extract videos required)

    def _extract(self, resp: str):
        data = SourceView(resp).parse().view()
        data_source = [
            {"title": f'{self.dubbers.get(d["data_provide_dubbing"], "???").strip()}', "url": d["url"]} for d in data
        ]
        return [Source(**d, **self._kwargs_http) for d in data_source]

    def get_sources(self):
        resp = self.http.get(
            "https://animego.org/anime/series",
            params={"dubbing": 2, "provider": 24, "episode": self.num, "id": self.id},
        ).json()["content"]
        return self._extract(resp)

    async def a_get_sources(self):
        resp = (
            await self.http_async.get(
                "https://animego.org/anime/series",
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
