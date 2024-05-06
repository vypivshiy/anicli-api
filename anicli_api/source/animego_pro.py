from typing import Dict, List, TYPE_CHECKING, Union, Any
from urllib.parse import urlsplit

from attrs import define

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource

# pre generated parser
from anicli_api.source.parsers.animego_pro_parser import AnimeView, EpisodesView, SearchView, OngoingView, \
    FirstPlayerUrlView, SourceKodikView

if TYPE_CHECKING:
    from httpx import Client, AsyncClient


class Extractor(BaseExtractor):
    BASE_URL = "https://animego.pro/"

    @staticmethod
    def _extract_search(resp: str) -> List["Search"]:
        result = SearchView(resp).parse().view()
        return [Search(**kw) for kw in result]

    @staticmethod
    def _extract_ongoing(resp: str) -> List["Ongoing"]:
        result = OngoingView(resp).parse().view()
        return [Ongoing(**kw) for kw in result]

    def search(self, query: str):
        resp = self.http.post(self.BASE_URL,
                              data={"do": "search", "subaction": "search", "story": query})
        return self._extract_search(resp.text)

    async def a_search(self, query: str):
        resp = await self.http_async.post(self.BASE_URL,
                                          data={"do": "search", "subaction": "search", "story": query})
        return self._extract_search(resp.text)

    def ongoing(self):
        resp = self.http.get(self.BASE_URL)
        return self._extract_ongoing(resp.text)

    async def a_ongoing(self):
        resp = await self.http_async.get(self.BASE_URL)
        return self._extract_ongoing(resp.text)


class _SearchOrOngoing:
    title: str
    thumbnail: str
    url: str

    http: "Client"
    http_async: "AsyncClient"
    _kwargs_http: Dict[str, Any]

    def _extract(self, resp: str) -> "Anime":
        data = AnimeView(resp).parse().view()
        return Anime(**data, **self._kwargs_http)

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

    @staticmethod
    def _extract(resp: str) -> List["Episode"]:
        result = EpisodesView(resp).parse().view()
        # remap result, create player links
        results = [
            {'count': d['episode_count'], 'dubber_id': d['id'], 'dubber_name': d['title'],
             'url':
                 f"https://kodik.info/{d['media_type']}/{d['media_id']}/{d['media_hash']}/720p"
                 f"?translations=false&only_translations={d['id']}"}
            for d in result
        ]
        max_episodes_count = int(
            max(
                results, key=lambda x: int(x['count'])
            )['count']
        )
        # {i: {params, dubbers:, url}]
        return [Episode(num=str(i),
                        title='Episode',
                        player_ctx=[j for j in results if int(j['count']) >= i]
                        ) for i in range(1, max_episodes_count + 1)
                ]

    def get_episodes(self):
        resp = self.http.post("https://animego.pro/engine/ajax/controller.php?mod=kodik_playlist_ajax",
                              data={'news_id': self.news_id, "action": "load_player"})
        player_url = FirstPlayerUrlView(resp.text).parse().view()['url']
        # replace params help extract ALL episodes and dubbers
        # TODO: test films (/video/ path)
        new_player_url = player_url.split("?", 1)[0] + '?translations=true'
        resp_2 = self.http.get(new_player_url)
        return self._extract(resp_2.text)

    async def a_get_episodes(self):
        resp = await self.http_async.post("https://animego.pro/engine/ajax/controller.php?mod=kodik_playlist_ajax",
                              data={'news_id': self.news_id, "action": "load_player"})
        player_url = FirstPlayerUrlView(resp.text).parse().view()['url']
        # replace params help extract ALL episodes and dubbers
        # TODO: test films (/video/ path)
        new_player_url = player_url.split("?", 1)[0] + '?translations=true'
        resp_2 = await self.http_async.get(new_player_url)
        return self._extract(resp_2.text)


@define(kw_only=True)
class Episode(BaseEpisode):
    _player_ctx: List[Dict[str, Any]]

    def get_sources(self) -> List["Source"]:
        # overwrite Source methods decrease http requests
        return [Source(title=d['dubber_name'],
                       url='_',  # stub, lazy parse
                       playlist_url=d['url'],
                       num=self.num,
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
        results = SourceKodikView(resp.text).parse().view()
        video_ctx = [d for d in results if d['value'] == self._num][0]
        # TODO: /video/ path coverage (films?)
        # overwrite url attribute and call base class implementation
        url = f"https://{urlsplit(self._playlist_url).netloc}/seria/{video_ctx['id']}/{video_ctx['hash']}/720p"
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
