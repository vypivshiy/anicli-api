from dataclasses import dataclass
from typing import Dict, List, Union

from parsel import Selector

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.source.parsers.animejoy_parser import AnimeView, OngoingView
from anicli_api.source.parsers.animejoy_parser import PlayerUrlsView as PlayerUrlsViewOld
from anicli_api.source.parsers.animejoy_parser import PlayerView, SearchView


# schema patches
class PlayerUrlsView(PlayerUrlsViewOld):
    def _parse_url(self, part: Selector) -> str:
        val_0 = part.attrib["data-file"]
        return f"https:{val_0}" if val_0.startswith("//") else val_0


# end patches


class Extractor(BaseExtractor):
    """
    WARNING:
        Sometimes this source drop cloudflare protect exceptions
    """

    BASE_URL = "https://animejoy.ru"

    @staticmethod
    def _extract_search(resp: str) -> List["Search"]:
        data = SearchView(resp).parse().view()
        return [Search(**d) for d in data]

    @staticmethod
    def _extract_ongoing(resp: str) -> List["Ongoing"]:
        data = OngoingView(resp).parse().view()
        return [Ongoing(**d) for d in data]

    def search(self, query: str):
        resp = self.HTTP().post("https://animejoy.ru", data={"story": query, "do": "search", "subaction": "search"})
        return self._extract_search(resp.text)

    async def a_search(self, query: str):
        resp = await self.HTTP_ASYNC().post(
            "https://animejoy.ru", data={"story": query, "do": "search", "subaction": "search"}
        )
        return self._extract_search(resp.text)

    def ongoing(self):
        resp = self.HTTP().get(self.BASE_URL)
        return self._extract_ongoing(resp.text)

    async def a_ongoing(self):
        resp = await self.HTTP_ASYNC().get(self.BASE_URL)
        return self._extract_ongoing(resp.text)


@dataclass
class Search(BaseSearch):
    alt_title: str

    @staticmethod
    def _extract(resp: str) -> "Anime":
        data = AnimeView(resp).parse().view()[0]
        return Anime(**data)

    def get_anime(self):
        resp = self._http().get(self.url)
        return self._extract(resp.text)

    async def a_get_anime(self):
        resp = await self._a_http().get(self.url)
        return self._extract(resp.text)

    def __str__(self):
        return f"{self.title} ({self.alt_title})"


@dataclass
class Ongoing(Search, BaseOngoing):
    pass


@dataclass
class Anime(BaseAnime):
    alt_title: str
    news_id: str  # for send extra requests

    @staticmethod
    def _extract(resp: str) -> List["Episode"]:
        player_urls_data = PlayerUrlsView(resp).parse().view()
        player_view_data = PlayerView(resp).parse().view()
        # players map names
        players = {d["id"]: d["name"] for d in player_view_data}

        ctx_videos: Dict[str, Dict[str, Union[str, List[str]]]]
        ctx_videos = {}
        for item in player_urls_data:
            player_id = item["id"]
            player_name = players.get(player_id, "???")
            player_url = item["url"]

            if not ctx_videos.get(player_id):
                ctx_videos[player_id] = {"player_id": player_id, "player_name": player_name, "urls": []}
            # TODO typing by TypedDict or refactoring
            ctx_videos[player_id]["urls"].append(player_url)  # type: ignore[union-attr]
        max_episodes_count = len(max((d["urls"] for d in ctx_videos.values()), key=len))

        episodes = {}  # type: ignore
        for i in range(max_episodes_count + 1):
            # enumerate from 1
            if i == 0:
                continue

            for player_id, video in ctx_videos.items():
                if not episodes.get(str(i)):
                    episodes[str(i)] = {
                        "title": f"episode {i}",
                        "num": str(i),
                        "players": {},  # player_id: {url, title}
                    }

                if not episodes[str(i)]["players"].get(player_id):  # type: ignore[attr-defined]
                    episodes[str(i)]["players"][player_id] = {}  # type: ignore[index]

                if len(video["urls"]) >= max_episodes_count:
                    episodes[str(i)]["players"][player_id]["url"] = video["urls"][i - 1]  # type: ignore[index]
                    episodes[str(i)]["players"][player_id]["title"] = video["player_name"]  # type: ignore[index]
        return [Episode(**d) for d in episodes.values()]  # type: ignore[arg-type]

    def get_episodes(self):
        resp = self._http().get(
            "https://animejoy.ru/engine/ajax/playlists.php",
            params={"news_id": self.news_id, "xfield": "playlist"},
        )
        return self._extract(resp.json()["response"])

    async def a_get_episodes(self):
        resp = await self._a_http().get(
            "https://animejoy.ru/engine/ajax/playlists.php",
            params={"news_id": self.news_id, "xfield": "playlist"},
        )
        return self._extract(resp.json()["response"])

    def __str__(self):
        title = f"{self.title} ({self.alt_title})"
        len_title = len(title)
        return f"{title} {self.description[:80 - len_title - 3]}..."


@dataclass
class Episode(BaseEpisode):
    players: Dict  # provide Source objects argument

    def get_sources(self):
        return [Source(**d) for d in self.players.values() if d]

    async def a_get_sources(self):
        return self.get_sources()


@dataclass
class Source(BaseSource):
    pass


if __name__ == "__main__":
    print(Extractor().ongoing()[0].get_anime().get_episodes()[0].get_sources())
    print(Extractor().search("lain")[0].get_anime().get_episodes()[0].get_sources())
