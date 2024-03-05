from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Union

from attrs import define
from parsel import Selector

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.source.parsers.animejoy_parser import AnimeView, OngoingView
from anicli_api.source.parsers.animejoy_parser import PlayerUrlsView as PlayerUrlsViewOld
from anicli_api.source.parsers.animejoy_parser import PlayerView, SearchView

if TYPE_CHECKING:
    from httpx import AsyncClient, Client


# schema patches
class PlayerUrlsView(PlayerUrlsViewOld):
    """
    Represent player url and player id

        Prepare:
          1. get news_id from Anime
          2. GET https://animejoy.ru/engine/ajax/playlists.php?news_id={Anime.news_id}&xfield=playlist
          3. get json, get HTML by "response" key
          4. OPTIONAL: Unescape document

        PlayerUrlsView view() item signature:

    {
        "key": "String",
        "value": "String"
    }
    """

    def _parse_url(self, part: Selector) -> str:
        val_0 = part.attrib["data-file"]
        # maybe exclude https: prefix
        return f"https:{val_0}" if val_0.startswith("//") else val_0


# end patches


class Extractor(BaseExtractor):
    """
    WARNING:

        Sometimes this source drop cloudflare protect exceptions

        For avoid cloudflare issues, you can provide custom httpx.Client or httpx.AsyncClient client with pre extracted
        cookies and headers

        Example:

            >>> from anicli_api.source.animejoy import Extractor
            >>> from anicli_api.tools import cli
            >>> import httpx
            >>>
            >>> # pre extracted cloudflare passed cookies for avoid this issue
            >>> cookies = {"__ddg1_": ..., "PHPSESSID": ..., "cf_clearance": ...}
            >>>
            >>> # pre extracted headers browser or any app, where get cookies later
            >>> headers = {"user-agent": "Mozilla 5.0 ..."}
            >>>
            >>> # create new client instance. for async same, but usage httpx.AsyncClient class
            >>> new_client = httpx.Client(http2=True, cookies=cookies, headers=headers)
            >>> cli(Extractor(http_client=new_client))
    """

    BASE_URL = "https://animejoy.ru"

    def _extract_search(self, resp: str) -> List["Search"]:
        data = SearchView(resp).parse().view()
        return [Search(**d, **self._kwargs_http) for d in data]

    def _extract_ongoing(self, resp: str) -> List["Ongoing"]:
        data = OngoingView(resp).parse().view()
        return [Ongoing(**d, **self._kwargs_http) for d in data]

    def search(self, query: str):
        resp = self.http.post("https://animejoy.ru", data={"story": query, "do": "search", "subaction": "search"})
        return self._extract_search(resp.text)

    async def a_search(self, query: str):
        resp = await self.http_async.post(
            "https://animejoy.ru", data={"story": query, "do": "search", "subaction": "search"}
        )
        return self._extract_search(resp.text)

    def ongoing(self):
        resp = self.http.get(self.BASE_URL)
        return self._extract_ongoing(resp.text)

    async def a_ongoing(self):
        resp = await self.http_async.get(self.BASE_URL)
        return self._extract_ongoing(resp.text)


class _SearchOrOngoing:
    title: str
    alt_title: str
    url: str

    http: "Client"
    http_async: "AsyncClient"
    _kwargs_http: Dict[str, Union["Client", "AsyncClient"]]

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
        return f"{self.title} ({self.alt_title})"


@define(kw_only=True)
class Search(_SearchOrOngoing, BaseSearch):
    alt_title: str


@define(kw_only=True)
class Ongoing(_SearchOrOngoing, BaseOngoing):
    alt_title: str


@define(kw_only=True)
class Anime(BaseAnime):
    alt_title: str
    news_id: str  # for send API requests

    @staticmethod
    def _create_player_id_videos_count(data_player_urls, data_players):
        """
        calc video count for every player id (needed for correct enumerate episodes)
        signature:
        { player_id: count, ...}
        """
        return {
            pl_id: [item["url"] for item in data_player_urls if item["player_id"] == pl_id]
            for pl_id in data_players.keys()
        }

    @staticmethod
    def _create_player_id_urls_map(data_player_urls, data_players):
        player_urls_map = {
            pl_id: [item["url"] for item in data_player_urls if item["player_id"] == pl_id]
            for pl_id in data_players.keys()
        }
        return player_urls_map

    @staticmethod
    def _create_episodes_context(data_players, max_episodes_count, player_urls_map):
        """
        signature:
            [
              {
                  title: ...,
                  num: ...,
                  sources: [
                      {
                          title: ...,
                          num: ...
                      },
                      ...
                      ]
              }
            ]
        """
        episodes = [
            {
                "title": "Episode",
                "num": f"{i + 1}",
                "sources": [
                    {"title": data_players.get(player_id), "url": urls[i]}
                    for player_id, urls in player_urls_map.items()
                    if len(urls) > i
                ],
            }
            for i in range(max_episodes_count)
        ]
        return episodes

    def _extract(self, resp: str) -> List["Episode"]:
        data_players = PlayerView(resp).parse().view()
        data_player_urls = PlayerUrlsView(resp).parse().view()

        # {player_id: [url_1, ...], player_id: [url_1, ...], ...}
        player_videos_counts = self._create_player_id_videos_count(data_player_urls, data_players)

        # max videos count for correct create episodes objects
        max_episodes_count = len(max(player_videos_counts.values()))

        # {player_id: [url_1, ...], ...}
        player_urls_map = self._create_player_id_urls_map(data_player_urls, data_players)

        # episodes {title, num} + sources [{title, url}, ...] create maps
        episodes = self._create_episodes_context(data_players, max_episodes_count, player_urls_map)
        return [Episode(**d, **self._kwargs_http) for d in episodes]

    def get_episodes(self):
        resp = self.http.get(
            "https://animejoy.ru/engine/ajax/playlists.php",
            params={"news_id": self.news_id, "xfield": "playlist"},
        )
        return self._extract(resp.json()["response"])

    async def a_get_episodes(self):
        resp = await self.http_async.get(
            "https://animejoy.ru/engine/ajax/playlists.php",
            params={"news_id": self.news_id, "xfield": "playlist"},
        )
        return self._extract(resp.json()["response"])

    def __str__(self):
        title = f"{self.title} ({self.alt_title})"
        len_title = len(title)
        return f"{title} {self.description[:80 - len_title - 3]}..."


@define(kw_only=True)
class Episode(BaseEpisode):
    sources: List[Dict[str, Any]]  # provide Source objects argument

    def get_sources(self):
        return [Source(**d, **self._kwargs_http) for d in self.sources]

    async def a_get_sources(self):
        return self.get_sources()


@define(kw_only=True)
class Source(BaseSource):
    pass


if __name__ == "__main__":
    import httpx

    from anicli_api.tools import cli

    cl = httpx.Client(
        http2=True,
        cookies={
            "__ddg1_": "0HPrt5ZR3CWWXIWGf8QV",
            "PHPSESSID": "b09e9770b2ad74941d92dc7dc8e38cb7",
            "cf_clearance": "rwXam5mBN96.LO1KXYDJGmzGUlWqdP.vdv2RkaWGIVU-1708090223-1.0-AQHHuJBqyI/8sMsbrnIn2j5XumncNctbmYUJefj+aSlWQK8EQV82za3Qkj6uFJg40DpVI88bFb4dmCKYAXvbwc0=",
        },
        headers={
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        },
    )
    cli(Extractor(http_client=cl))
