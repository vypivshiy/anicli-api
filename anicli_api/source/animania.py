import re
from typing import TYPE_CHECKING, Dict, List, Union

from attrs import define

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.source.parsers.animania_parser import AnimeView, DubbersView, OngoingView, SearchView, VideoView

if TYPE_CHECKING:
    from httpx import AsyncClient, Client


class Extractor(BaseExtractor):
    BASE_URL = "https://animania.online"

    def _extract_search(self, resp: str) -> List["Search"]:
        data = SearchView(resp).parse().view()
        return [Search(**d, **self._kwargs_http) for d in data]

    def _extract_ongoing(self, resp: str) -> List["Ongoing"]:
        data = OngoingView(resp).parse().view()
        return [Ongoing(**d, **self._kwargs_http) for d in data]

    def search(self, query: str):
        resp = self.http.get(
            "https://animania.online/index.php", params={"story": query, "do": "search", "subaction": "search"}
        )
        return self._extract_search(resp.text)

    async def a_search(self, query: str):
        resp = await self.http_async.get(
            "https://animania.online/index.php", params={"story": query, "do": "search", "subaction": "search"}
        )
        return self._extract_search(resp.text)

    def ongoing(self):
        resp = self.http.get(self.BASE_URL)
        return self._extract_ongoing(resp.text)

    async def a_ongoing(self):
        resp = await self.http_async.get(self.BASE_URL)
        return self._extract_ongoing(resp.text)


class _SearchOrOngoing:
    url: str
    http: "Client"
    http_async: "AsyncClient"
    _kwargs_http: Dict[str, Union["Client", "AsyncClient"]]

    def _extract(self, resp: str) -> "Anime":
        data = AnimeView(resp).parse().view()
        dubbers = DubbersView(resp).parse().view()
        videos_data = VideoView(resp).parse().view()
        # raw_episode signature:
        # {
        #   'dub_id': ...,
        #   'dub_name': ...,
        #   'count': 6,
        #   'videos': [{'title': ..., 'url': ...}, ...]
        # }
        raw_episodes = []
        # episodes values prepare
        for item in videos_data:
            dub_id = item["id"]
            dub_name = dubbers.get(dub_id, "???")
            titles, urls = item["names"], item["urls"]
            # video signature: [{'title': ..., 'url': ...}, ...]
            videos = [{"title": t.strip(), "url": u} for t, u in zip(titles, urls)]

            episode_item = {"dub_id": dub_id, "dub_name": dub_name, "count": len(urls), "videos": videos}

            raw_episodes.append(episode_item)
        return Anime(**data, raw_episodes=raw_episodes, **self._kwargs_http)

    def get_anime(self):
        resp = self.http.get(self.url)
        return self._extract(resp.text)

    async def a_get_anime(self):
        resp = await self.http_async.get(self.url)
        return self._extract(resp.text)


@define(kw_only=True)
class Search(_SearchOrOngoing, BaseSearch):
    pass


@define(kw_only=True)
class Ongoing(_SearchOrOngoing, BaseOngoing):
    pass


@define(kw_only=True)
class Anime(BaseAnime):
    raw_episodes: List[Dict[str, Union[str, Dict[str, str]]]]

    def get_episodes(self):
        episodes = {}
        for episode in self.raw_episodes:
            for i, video in enumerate(episode["videos"], 1):
                if not episodes.get(i):
                    episodes[i] = {}
                    episodes[i]["videos"] = []

                episodes[i]["title"] = f"{i} серия"
                episodes[i]["num"] = str(i)
                episodes[i]["videos"].append({"title": episode["dub_name"], "url": video["url"]})
        return [Episode(**d, **self._kwargs_http) for d in tuple(episodes.values())]

    async def a_get_episodes(self):
        return self.get_episodes()


@define(kw_only=True)
class Episode(BaseEpisode):
    videos: List[Dict[str, str]]

    def get_sources(self):
        return [Source(**d, **self._kwargs_http) for d in self.videos]

    async def a_get_sources(self):
        return self.get_sources()

    def __str__(self):
        # num contains in title, always `1 серия`, ... `N серия` naming
        return self.title


@define(kw_only=True)
class Source(BaseSource):
    pass


if __name__ == "__main__":
    from anicli_api.tools import cli

    cli(Extractor())
