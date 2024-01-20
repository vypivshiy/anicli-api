import re
from dataclasses import dataclass
from typing import Dict
import logging

from httpx import Response
from parsel import Selector

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.source.parsers.animego_parser import AnimeView as AnimeViewOld
from anicli_api.source.parsers.animego_parser import DubbersView, EpisodeView, SearchView, SourceView
from anicli_api.source.parsers.animego_parser import OngoingView as OngoingViewOld


# patches
_logger = logging.getLogger('anicli-api')  # type: ignore


class AnimeView(AnimeViewOld):
    def _parse_description(self, part: Selector) -> str:
        # remove whitespaces patch
        val_0 = part.css(".description ::text").getall()
        return " ".join(line.strip() for line in val_0)  # return "" if val_0 is empty


class OngoingView(OngoingViewOld):
    def _parse_dub(self, part: Selector) -> str:
        # remove brackets patch
        val_0 = part.css(".text-gray-dark-6 ::text").get()
        return val_0.replace(")", "").replace("(", "")  # type: ignore


class Extractor(BaseExtractor):
    BASE_URL = "https://animego.org"

    @staticmethod
    def _extract_search(resp: str):
        data = SearchView(resp).parse().view()
        return [Search(**d) for d in data]

    @staticmethod
    def _extract_ongoing(resp: str):
        data = OngoingView(resp).parse().view()
        ongs = [Ongoing(**d) for d in data]
        # remove duplicates and accumulate by episode and dubber keys
        sorted_ongs: Dict[int, "Ongoing"] = {}
        for ong in ongs:
            key = hash(ong.url + ong.episode)
            if sorted_ongs.get(key):
                sorted_ongs[key].dub += f", {ong.dub}"
            else:
                sorted_ongs[key] = ong
        return list(sorted_ongs.values())

    def search(self, query: str):
        resp = self.HTTP().get(f"{self.BASE_URL}/search/anime", params={"q": query})
        return self._extract_search(resp.text)

    async def a_search(self, query: str):
        resp = await self.HTTP_ASYNC().get(f"{self.BASE_URL}/search/anime", params={"q": query})
        return self._extract_search(resp.text)

    def ongoing(self):
        resp = self.HTTP().get(self.BASE_URL)
        return self._extract_ongoing(resp.text)

    async def a_ongoing(self):
        resp = await self.HTTP_ASYNC().get(self.BASE_URL)
        return self._extract_ongoing(resp.text)


@dataclass
class Search(BaseSearch):
    @staticmethod
    def _extract(resp: str):
        data = AnimeView(resp).parse().view()[0]
        return Anime(**data)

    @staticmethod
    def _is_valid_page(resp: Response):
        # RKN blocks issues eg:
        # https://animego.org/anime/ya-predpochitayu-zlodeyku-2413
        # but API requests MAYBE still works.
        if resp.is_success:
            return True

        title = re.search(r"<title>(.*?)</title>", resp.text)[1]  # type: ignore
        _logger.warning("%s returns status code [%s] title='%s' content-length=%s",
                        resp.url, resp.status_code, title, len(resp.content))
        return False

    def _create_anime(self):
        # skip extract metadata and manual create object (API requests maybe still works)
        return Anime(
            title=self.title,
            thumbnail=self.thumbnail,
            description="",
            id=self.url.split('-')[-1],
            raw_json=""
        )

    def get_anime(self):
        resp = self._http().get(self.url)
        if self._is_valid_page(resp):
            return self._extract(resp.text)
        return self._create_anime()

    async def a_get_anime(self):
        resp = await self._a_http().get(self.url)
        if self._is_valid_page(resp):
            return self._extract(resp.text)
        return self._create_anime()


@dataclass
class Ongoing(BaseOngoing):
    episode: str
    dub: str

    @staticmethod
    def _extract(resp: str):
        data = AnimeView(resp).parse().view()[0]
        return Anime(**data)

    @staticmethod
    def _is_valid_page(resp: Response):
        # RKN blocks issues eg:
        # https://animego.org/anime/ya-predpochitayu-zlodeyku-2413
        # but API requests MAYBE still works.
        if resp.is_success:
            return True

        title = re.search(r"<title>(.*?)</title>", resp.text)[1]  # type: ignore
        _logger.warning("%s returns status code [%s] title='%s' content-length=%s",
                        resp.url, resp.status_code, title, len(resp.content))
        return False

    def _create_anime(self):
        # skip extract metadata, and manual create object (API requests still works)
        return Anime(
            title=self.title,
            thumbnail=self.thumbnail,
            description="",
            id=self.url.split('-')[-1],
            raw_json=""
        )

    def get_anime(self):
        resp = self._http().get(self.url)
        if self._is_valid_page(resp):
            return self._extract(resp.text)
        return self._create_anime()

    async def a_get_anime(self):
        resp = await self._a_http().get(self.url)
        if self._is_valid_page(resp):
            return self._extract(resp.text)
        return self._create_anime()

    def __str__(self):
        return f"{self.title} {self.episode} ({self.dub})"


@dataclass
class Anime(BaseAnime):
    id: str
    raw_json: str

    @staticmethod
    def _extract(resp: str):
        episodes_data = EpisodeView(resp).parse().view()
        dubbers_data = DubbersView(resp).parse().view()
        dubbers = {d["id"]: d["name"] for d in dubbers_data}
        return [Episode(**d, dubbers=dubbers) for d in episodes_data]
    
    @staticmethod
    def _episodes_is_available(response: str):
        sel = Selector(response)
        # RKN issue: maybe title not available in your country
        # eg:
        # https://animego.org/anime/vtorzhenie-gigantov-2-17
        # this title API request don't work in RU ip
        if sel.css("div.player-blocked").get():
            _logger.error("API not available in your country. Element: %s", sel.css('div.h5').get())
            return False
        return True
    
    def get_episodes(self):
        resp = self._http().get(f"https://animego.org/anime/{self.id}/player?_allow=true").json()["content"]
        return self._extract(resp) if self._episodes_is_available(resp) else []

    async def a_get_episodes(self):
        resp = await self._a_http().get(f"https://animego.org/anime/{self.id}/player?_allow=true")
        resp = resp.json()["content"]
        return self._extract(resp) if self._episodes_is_available(resp) else []


@dataclass
class Episode(BaseEpisode):
    dubbers: Dict[str, str]
    id: str  # episode id

    def _extract(self, resp: str):
        data = SourceView(resp).parse().view()
        data_source = [
            {"title": f'{self.dubbers.get(d["data_provide_dubbing"], "???").strip()}', "url": d["url"]} for d in data
        ]
        return [Source(**d) for d in data_source]

    def get_sources(self):
        resp = (
            self._http()
            .get(
                "https://animego.org/anime/series",
                params={"dubbing": 2, "provider": 24, "episode": self.num, "id": self.id},
            )
            .json()["content"]
        )
        return self._extract(resp)

    async def a_get_sources(self):
        resp = (
            await self._a_http().get(
                "https://animego.org/anime/series",
                params={"dubbing": 2, "provider": 24, "episode": self.num, "id": self.id},
            )
        ).json()["content"]
        return self._extract(resp)


@dataclass
class Source(BaseSource):
    pass
