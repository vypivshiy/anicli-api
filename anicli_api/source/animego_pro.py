from typing import Any, Dict, List
from urllib.parse import urlsplit

from attrs import define

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource, HttpMixin
from anicli_api.source.parsers.animego_pro_parser import (
    AnimePage,
    EpisodesPage,
    OngoingPage,
    SearchPage,
    SourceKodikSerialPage,
)


class Extractor(BaseExtractor):
    BASE_URL = "https://animego.pro/"

    def _extract_search(self, resp: str) -> List["Search"]:
        return [Search(**kw, **self._kwargs_http) for kw in SearchPage(resp).parse()]

    def _extract_ongoing(self, resp: str) -> List["Ongoing"]:
        return [Ongoing(**kw, **self._kwargs_http) for kw in OngoingPage(resp).parse()]

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


class _SearchOrOngoing(HttpMixin):
    title: str
    thumbnail: str
    url: str

    def _extract(self, resp: str) -> "Anime":
        return Anime(**AnimePage(resp).parse(), **self._kwargs_http)

    def get_anime(self):
        resp = self.http.get(self.url)
        return self._extract(resp.text)

    async def a_get_anime(self):
        resp = await self.http_async.get(self.url)
        return self._extract(resp.text)

    def __str__(self):
        return f"{self.title}"


@define(kw_only=True)
class Search(_SearchOrOngoing, BaseSearch):
    pass


@define(kw_only=True)
class Ongoing(_SearchOrOngoing, BaseOngoing):
    pass


@define(kw_only=True)
class Anime(BaseAnime):
    news_id: str

    def _extract(self, resp: str) -> List["Episode"]:
        # remap result, create player links
        result = SourceKodikSerialPage(resp).parse()
        results = [
            {
                "count": d["data_episode_count"],
                "dubber_id": d["data_id"],
                "dubber_name": d["data_title"],
                "url": self._create_kodik_ep_url(d),
            }
            for d in result["translations"]
        ]
        # calculate max episodes count
        max_episodes_count = int(max(results, key=lambda x: int(x["count"]))["count"])
        return [
            Episode(
                num=str(i),
                title="Episode",
                # send payload for extract needed Source by translation later
                player_ctx=[j for j in results if int(j["count"]) >= i],
                **self._kwargs_http,
            )
            for i in range(1, max_episodes_count + 1)
        ]

    def _create_kodik_ep_url(self, d):
        return (
            f"https://kodik.info/{d['data_media_type']}/{d['data_media_id']}/{d['data_media_hash']}/720p?translations=false"
            f"&only_translations={d['data_id']}"
        )

    def get_episodes(self):
        resp = self.http.post(
            "https://animego.pro/engine/ajax/controller.php?mod=kodik_playlist_ajax",
            data={"news_id": self.news_id, "action": "load_player"},
        )
        episodes = EpisodesPage(resp.text).parse()
        # replace params help extract ALL episodes and dubbers
        # TODO: test films (/video/ path)
        new_player_url = episodes["player_url"].split("?", 1)[0] + "?translations=true"
        resp_2 = self.http.get(new_player_url)
        return self._extract(resp_2.text)

    async def a_get_episodes(self):
        resp = await self.http_async.post(
            "https://animego.pro/engine/ajax/controller.php?mod=kodik_playlist_ajax",
            data={"news_id": self.news_id, "action": "load_player"},
        )
        episodes = EpisodesPage(resp.text).parse()
        # replace params help extract ALL episodes and dubbers
        # TODO: test films (/video/ path)
        new_player_url = episodes["player_url"].split("?", 1)[0] + "?translations=true"
        resp_2 = await self.http_async.get(new_player_url)
        return self._extract(resp_2.text)


@define(kw_only=True)
class Episode(BaseEpisode):
    _player_ctx: List[Dict[str, Any]]

    def get_sources(self) -> List["Source"]:
        # overwrite Source methods decrease http requests
        return [
            Source(
                title=d["dubber_name"],
                url="_",  # stub, parse in the Source object
                playlist_url=d["url"],
                num=self.num,
                **self._kwargs_http,
            )
            for d in self._player_ctx
        ]

    async def a_get_sources(self):
        return self.get_sources()


@define(kw_only=True)
class Source(BaseSource):
    _num: str  # this value helps match needed video (episode)
    _playlist_url: str

    def _parse_episode_url(self, resp) -> None:
        results = SourceKodikSerialPage(resp.text).parse()
        video_ctx = [d for d in results["episodes"] if d["value"] == self._num][0]
        # TODO: /video/ path coverage (films?)
        # overwrite url attribute and call base class implementation
        url = (
            f"https://{urlsplit(self._playlist_url).netloc}/seria/{video_ctx['data_id']}/{video_ctx['data_hash']}/720p"
        )
        self.url = url

    def get_videos(self, **httpx_kwargs):
        resp = self.http.get(self._playlist_url)
        self._parse_episode_url(resp)
        return super().get_videos(**httpx_kwargs)

    async def a_get_videos(self, **httpx_kwargs):
        resp = await self.http_async.get(self._playlist_url)
        self._parse_episode_url(resp)
        return await super().a_get_videos(**httpx_kwargs)


if __name__ == "__main__":
    # manual testing parser
    from anicli_api.tools import cli

    cli(Extractor())
