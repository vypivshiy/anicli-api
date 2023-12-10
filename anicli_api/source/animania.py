import re
from dataclasses import dataclass
from typing import Dict, List, Union

from parsel import Selector

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.source.parsers.animania_parser import AnimeView, DubbersView, OngoingView, SearchView
from anicli_api.source.parsers.animania_parser import VideoView as VideoViewOld


# patches
class VideoView(VideoViewOld):
    def _parse_urls(self, part: Selector) -> List[str]:
        # add href prefix
        val_0 = part.get()
        val_1 = re.findall(r"'(//.*?)'", val_0)
        return [f"https:{u}" for u in val_1]


# end patches


class Extractor(BaseExtractor):
    BASE_URL = "https://animania.online"

    @staticmethod
    def _extract_search(resp: str) -> List["Search"]:
        data = SearchView(resp).parse().view()
        return [Search(**d) for d in data]

    @staticmethod
    def _extract_ongoing(resp: str) -> List["Ongoing"]:
        data = OngoingView(resp).parse().view()
        return [Ongoing(**d) for d in data]

    def search(self, query: str):
        resp = self.HTTP().get(
            "https://animania.online/index.php", params={"story": query, "do": "search", "subaction": "search"}
        )
        return self._extract_search(resp.text)

    async def a_search(self, query: str):
        resp = await self.HTTP_ASYNC().get(
            "https://animania.online/index.php", params={"story": query, "do": "search", "subaction": "search"}
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
    @staticmethod
    def _extract(resp: str) -> "Anime":
        data = AnimeView(resp).parse().view()[0]
        dubbers_data = DubbersView(resp).parse().view()
        dubbers = {d["id"]: d["name"] for d in dubbers_data}

        videos_data = VideoView(resp).parse().view()
        raw_episodes = []

        for item in videos_data:
            dub_id = item["id"]
            dub_name = dubbers.get(dub_id, "???")
            titles = item["names"]
            urls = item["urls"]

            converted_item = {"dub_id": dub_id, "dub_name": dub_name, "count": 0, "videos": []}

            if len(urls) > converted_item["count"]:
                converted_item["count"] = len(urls)

            for title, url in zip(titles, urls):
                converted_item["videos"].append({"title": title.strip(), "url": url})

            raw_episodes.append(converted_item)
        return Anime(**data, raw_episodes=raw_episodes)

    def get_anime(self):
        resp = self._http().get(self.url)
        return self._extract(resp.text)

    async def a_get_anime(self):
        resp = await self._a_http().get(self.url)
        return self._extract(resp.text)


@dataclass
class Ongoing(Search, BaseOngoing):
    pass


@dataclass
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
        return [Episode(**d) for d in tuple(episodes.values())]

    async def a_get_episodes(self):
        return self.get_episodes()


@dataclass
class Episode(BaseEpisode):
    videos: List[Dict[str, str]]

    def get_sources(self):
        return [Source(**d) for d in self.videos]

    async def a_get_sources(self):
        return self.get_sources()


@dataclass
class Source(BaseSource):
    pass


if __name__ == "__main__":
    print(Extractor().search("lai")[0].get_anime().get_episodes()[0].get_sources())
    print(Extractor().ongoing()[0].get_anime().get_episodes()[0].get_sources())
