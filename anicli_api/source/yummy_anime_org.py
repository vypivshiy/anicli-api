from __future__ import annotations

import re

from attrs import define

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource

# data about anime storage in iframe kodik player page
from anicli_api.player.base import Video
from anicli_api.source.parsers.yummy_anime_org_parser import PageOngoing, PageSearch, PageAnime, PageUtils
from anicli_api.player.parsers.cdnvideohub_parser import PageParseCdnVideoData, T_PageParseCdnVideoData
from anicli_api.player.apis.cdnvideohub import CdnVideoHubSync, CdnVideoHubAsync, T_PlaylistItem
from anicli_api.player.cdnvideohub import video_playlist_from_vk_id, a_video_playlist_from_vk_id

import logging

logger = logging.getLogger("anicli-api")
RE_IS_CYRRILIC = re.compile(r"[А-Яа-яЁё]")


class Extractor(BaseExtractor):
    BASE_URL = "https://yummyanime.in"

    def _extract_search(self, resp: str) -> list["Search"]:
        data = PageSearch(resp).parse()
        full_url = PageUtils(resp).parse()["url"]
        return [
            Search(title=i["title"], url=i["url"], thumbnail=full_url + i["thumbnail_path"], **self._kwargs_http)
            for i in data
        ]

    def _extract_ongoing(self, resp: str) -> list["Ongoing"]:
        data = PageOngoing(resp).parse()
        full_url = PageUtils(resp).parse()["url"]

        return [
            Ongoing(
                title=i["title"],
                url=full_url + i["url_path"],
                thumbnail=full_url + i["thumbnail_path"],
                episode=i["episode"],
                **self._kwargs_http,
            )
            for i in data
        ]

    def search(self, query: str):
        resp = self.http.post(self.BASE_URL, data={"do": "search", "subaction": "search", "story": query})
        result = self._extract_search(resp.text)
        if not result and not (RE_IS_CYRRILIC.search(query)):
            logger.warning("[yummyanime.in] search works only with cyrrilic query input")
        return result

    async def a_search(self, query: str):
        resp = await self.http_async.post(self.BASE_URL, data={"do": "search", "subaction": "search", "story": query})
        result = self._extract_search(resp.text)
        if not result and not (RE_IS_CYRRILIC.search(query)):
            logger.warning("[yummyanime.in] search works only with cyrrilic query input")
        return result

    def ongoing(self):
        resp = self.http.get(self.BASE_URL)
        return self._extract_ongoing(resp.text)

    async def a_ongoing(self):
        resp = await self.http_async.get(self.BASE_URL)
        return self._extract_ongoing(resp.text)


@define(kw_only=True)
class Search(BaseSearch):
    def _extract(self, resp: str) -> "Anime":
        data = PageAnime(resp).parse()
        cdn_data = PageParseCdnVideoData(resp).parse()
        return Anime(
            title=data["title"],
            description=data["description"],
            thumbnail=data["thumbnail"],
            cdn_data=cdn_data,
            **self._kwargs_http,
        )

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
        data = PageAnime(resp).parse()
        cdn_data = PageParseCdnVideoData(resp).parse()
        return Anime(
            title=data["title"],
            description=data["description"],
            thumbnail=data["thumbnail"],
            cdn_data=cdn_data,
            **self._kwargs_http,
        )

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
    cdn_data: T_PageParseCdnVideoData

    def get_episodes(self) -> list["Episode"]:
        result = CdnVideoHubSync().get_playlist(
            pub=int(self.cdn_data["data_publisher_id"]),
            aggr=self.cdn_data["data_aggregator"],
            id=int(self.cdn_data["data_title_id"]),
        )
        episode_mapping = {}
        for data in result.data["items"]:
            if not episode_mapping.get(data["episode"]):
                episode_mapping[data["episode"]] = []
            episode_mapping[data["episode"]].append(data)

        episodes = []
        for num, episode in episode_mapping.items():
            episodes.append(Episode(title="Episode", ordinal=int(num), data=episode, **self._kwargs_http))
        # playlist response not guarantee order
        episodes.sort(key=lambda i: i.ordinal)

        return episodes

    async def a_get_episodes(self) -> list["Episode"]:
        result = await CdnVideoHubAsync().get_playlist(
            pub=int(self.cdn_data["data_publisher_id"]),
            aggr=self.cdn_data["data_aggregator"],
            id=int(self.cdn_data["data_title_id"]),
        )
        episode_mapping = {}
        for data in result.data["items"]:
            if not episode_mapping.get(data["episode"]):
                episode_mapping[data["episode"]] = []
            episode_mapping[data["episode"]].append(data)

        episodes = []
        for num, episode in episode_mapping.items():
            episodes.append(Episode(title="Episode", ordinal=int(num), data=episode, **self._kwargs_http))
        # playlist response not guarantee order
        episodes.sort(key=lambda i: i.ordinal)

        return episodes


@define(kw_only=True)
class Episode(BaseEpisode):
    data: list[T_PlaylistItem]

    def get_sources(self) -> list["Source"]:
        results = []
        for item in self.data:
            results.append(
                Source(
                    title=item["voiceStudio"],
                    url="https://plapi.cdnvideohub.com",  # stub
                    vk_id=item["vkId"],
                )
            )
        return results

    async def a_get_sources(self) -> list["Source"]:
        return self.get_sources()


@define(kw_only=True)
class Source(BaseSource):
    vk_id: str

    # todo: move to player extractor (how?)
    def get_videos(self, **httpx_kwargs) -> list[Video]:
        return video_playlist_from_vk_id(self.vk_id)

    async def a_get_videos(self, **httpx_kwargs) -> list[Video]:
        return await a_video_playlist_from_vk_id(self.vk_id)


if __name__ == "__main__":
    # manual testing parser
    from anicli_api.tools import cli

    cli(Extractor())
