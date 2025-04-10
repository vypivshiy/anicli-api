import warnings
from typing import List, TypedDict, Union
from urllib.parse import urlsplit, urlencode

from attrs import define

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource

# data about anime storage in iframe kodik player page
from anicli_api.player.parsers.kodik_parser import (
    MainKodikVideoPage,
    MainKodikSerialPage,
    T_MainKodikSerialPage,
    T_MainKodikVideoPage,
)
from anicli_api.source.parsers.yummy_anime_org_parser import OngoingPage, SearchPage, AnimePage

# film and episodes have simular structures, but
# film (/video/ entrypoint) exclude "data_episode_count" key
T_TranslationLike = TypedDict(
    "T_TranslationLike",
    {
        "value": str,
        "data_id": str,
        "data_translation_type": str,
        "data_media_id": str,
        "data_media_hash": str,
        "data_media_type": str,
        "data_title": str,
        "data_episode_count": str,
        "text": str,
    },
    total=False,
)


class Extractor(BaseExtractor):
    BASE_URL = "https://yummy-anime.org"

    def _extract_search(self, resp: str) -> List["Search"]:
        data = SearchPage(resp).parse()
        return [Search(**i, **self._kwargs_http) for i in data]

    def _extract_ongoing(self, resp: str) -> List["Ongoing"]:
        data = OngoingPage(resp).parse()
        return [Ongoing(**i, **self._kwargs_http) for i in data]

    def search(self, query: str):
        resp = self.http.post(self.BASE_URL, data={"do": "search", "subaction": "search", "story": query})
        return self._extract_search(resp.text)

    async def a_search(self, query: str):
        resp = await self.http_async.post(self.BASE_URL, data={"do": "search", "subaction": "search", "story": query})
        return self._extract_search(resp.text)

    def ongoing(self):
        resp = self.http.get(self.BASE_URL)
        return self._extract_ongoing(resp.text)

    async def a_ongoing(self):
        resp = await self.http_async.get(self.BASE_URL)
        return self._extract_ongoing(resp.text)


@define(kw_only=True)
class Search(BaseSearch):
    def _extract(self, resp: str) -> "Anime":
        data = AnimePage(resp).parse()
        return Anime(**data, **self._kwargs_http)

    def get_anime(self):
        resp = self.http.get(self.url)
        return self._extract(resp.text)

    async def a_get_anime(self):
        resp = await self.http_async.get(self.url)
        return self._extract(resp.text)


@define(kw_only=True)
class Ongoing(BaseOngoing):
    episode: int

    def _extract(self, resp: str) -> "Anime":
        data = AnimePage(resp).parse()
        if not data["player_url"]:
            warnings.warn(
                "This title not available (player url not exists).its source issue, not anicli-api", category=Warning
            )
            return None
        return Anime(**data, **self._kwargs_http)

    def get_anime(self) -> "Anime":
        resp = self.http.get(self.url)
        return self._extract(resp.text)

    async def a_get_anime(self) -> "Anime":
        resp = await self.http_async.get(self.url)
        return self._extract(resp.text)

    def __str__(self):
        return f"{self.title} ({self.episode})"


@define(kw_only=True)
class Anime(BaseAnime):
    alt_title: str
    _player_url: str

    def _extract(self, resp: str) -> List["Episode"]:
        if "/serial/" in self._player_url:
            data_serial = MainKodikSerialPage(resp).parse()
            return [
                Episode(
                    title=i["data_title"],
                    num=i["value"],
                    kodik_serial_data=data_serial,
                    kodik_video_data={},  # type: ignore
                    url=self._player_url,
                    **self._kwargs_http,
                )
                for i in data_serial["series_box"]
            ]
        # film / ova with single video
        elif "/video/" in self._player_url:
            data_video = MainKodikVideoPage(resp).parse()
            return [
                Episode(
                    title=f"{self.title} ({self.alt_title})",
                    num="1",
                    kodik_video_data=data_video,
                    kodik_serial_data={},  # type: ignore
                    is_film=True,
                    url=self._player_url,
                    **self._kwargs_http,
                )
            ]
        else:
            msg = f"Unsupported player entrypoint url: {self._player_url}title name: {self.title} ({self.alt_title})"
            warnings.warn(msg, category=Warning)
            return []

    def get_episodes(self):
        resp = self.http.get(self._player_url)
        return self._extract(resp.text)

    async def a_get_episodes(self):
        resp = await self.http_async.get(self._player_url)
        return self._extract(resp.text)


@define(kw_only=True)
class Episode(BaseEpisode):
    _kodik_serial_data: T_MainKodikSerialPage
    _kodik_video_data: T_MainKodikVideoPage
    _is_film: bool = False
    # orig kodik player url. later required, for replace hashes for needed translation option
    _url: str

    def _build_episode_url(self, translation: Union[T_TranslationLike, dict]) -> str:
        """make url to target episode or film"""
        base_url = f"https://{urlsplit(self._url).netloc}"

        if self._is_film:
            url_params = self._kodik_video_data["url_params"].copy()
        else:
            url_params = self._kodik_serial_data["url_params"].copy()

        # /video/ (film) don't need marks season and episode num
        if not self._is_film:
            url_params.update(
                {"season": int(self._kodik_serial_data["season_box"][0]["value"]), "episode": int(self.num)}
            )
        url_params_encoded = urlencode(url_params)

        # maybe exclude translations choice
        # https://yummy-anime.org/5046-miru-moe-buduschee.html
        if not self._is_film and not translation:
            return self._url + "?" + url_params_encoded

        return (
            base_url
            + f"/{translation['data_media_type']}"
            + f"/{translation['data_media_id']}"
            + f"/{translation['data_media_hash']}"
            + "/720p?"
            + url_params_encoded
        )

    def _extract(self) -> List["Source"]:
        if self._is_film:
            return [
                Source(
                    title=i["data_title"],
                    url=self._build_episode_url(i),  # type: ignore
                    **self._kwargs_http,
                )
                for i in self._kodik_video_data["translation_box"]
            ]

        available_translations = [
            i for i in self._kodik_serial_data["translations_box"] if int(self.num) <= int(i["data_episode_count"])
        ]
        # maybe have single dub:
        # https://yummy-anime.org/5046-miru-moe-buduschee.html
        if not available_translations:
            return [
                # don't know what to call it when only one voice dubbing is available
                Source(
                    title="ORIGINAL (single dub)",
                    url=self._build_episode_url({}),
                    **self._kwargs_http,
                )
            ]
        return [
            Source(
                title=f"{i['data_title']} ({urlsplit(self._url).netloc})",
                url=self._build_episode_url(i),  # type: ignore
                **self._kwargs_http,
            )
            for i in available_translations
        ]

    def get_sources(self):
        return self._extract()

    async def a_get_sources(self):
        return self._extract()


@define(kw_only=True)
class Source(BaseSource):
    pass


if __name__ == "__main__":
    # manual testing parser
    from anicli_api.tools import cli

    cli(Extractor())
