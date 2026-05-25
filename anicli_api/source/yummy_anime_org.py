from __future__ import annotations

import re
from typing import Dict, List, cast

from attrs import define

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource

from anicli_api.source.parsers.yummy_anime_org_parser import PageOngoing, PageSearch, PageAnime, PageUtils
from anicli_api.player.parsers.cdnvideohub_parser import PageParseCdnVideoData, CdnVideoHubAPI

# types
from anicli_api.player.parsers.cdnvideohub_parser import PageParseCdnVideoDataType, CdnVideoHubResponseJson, ItemJson


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
                url=i["url"],
                thumbnail=full_url + i["thumbnail_path"],
                episode=i["episode"],
                **self._kwargs_http,
            )
            for i in data
        ]

    def search(self, query: str):
        result = PageSearch.fetch(self.http, query=query).parse()
        if not result and not (RE_IS_CYRRILIC.search(query)):
            logger.warning("[yummyanime.in] search works only with cyrrilic query input")
        results = [
            Search(
                title=data["title"],
                url=data["url"],
                thumbnail=self.BASE_URL + data["thumbnail_path"],
                **self._kwargs_http,
            )
            for data in result
        ]
        return results

    async def a_search(self, query: str):
        result = (await PageSearch.async_fetch(self.http_async, query=query)).parse()
        if not result and not (RE_IS_CYRRILIC.search(query)):
            logger.warning("[yummyanime.in] search works only with cyrrilic query input")
        results = [
            Search(
                title=data["title"],
                url=data["url"],
                thumbnail=self.BASE_URL + data["thumbnail_path"],
                **self._kwargs_http,
            )
            for data in result
        ]
        return results

    def ongoing(self):
        result = PageOngoing.fetch(self.http).parse()
        results = [
            Ongoing(
                title=data["title"],
                url=data["url"],
                thumbnail=self.BASE_URL + data["thumbnail_path"],
                episode=data["episode"],
                **self._kwargs_http,
            )
            for data in result
        ]
        return results

    async def a_ongoing(self):
        result = (await PageOngoing.async_fetch(self.http_async)).parse()
        results = [
            Ongoing(
                title=data["title"],
                url=data["url"],
                thumbnail=self.BASE_URL + data["thumbnail_path"],
                episode=data["episode"],
                **self._kwargs_http,
            )
            for data in result
        ]
        return results


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
    cdn_data: PageParseCdnVideoDataType

    def get_episodes(self) -> list["Episode"]:
        result = CdnVideoHubAPI.get_params_from_page(
            self.http,
            pub=self.cdn_data["data_publisher_id"],
            aggr=self.cdn_data["data_aggregator"],
            id=self.cdn_data["data_title_id"],
        )
        if not result.is_ok:
            return []
        value = result.value
        value = cast(CdnVideoHubResponseJson, value)
        episode_mapping: Dict[int, List[ItemJson]] = {}
        for data in value["items"]:
            if not episode_mapping.get(data["episode"]):
                episode_mapping[data["episode"]] = []
            episode_mapping[data["episode"]].append(data)

        episodes = [
            Episode(title="Episode", ordinal=num, data=data, **self._kwargs_http)
            for num, data in episode_mapping.items()
        ]
        # playlist response not guarantee order
        episodes.sort(key=lambda i: i.ordinal)
        return episodes

    async def a_get_episodes(self) -> list["Episode"]:
        result = await CdnVideoHubAPI.async_get_params_from_page(
            self.http_async,
            pub=self.cdn_data["data_publisher_id"],
            aggr=self.cdn_data["data_aggregator"],
            id=self.cdn_data["data_title_id"],
        )
        if not result.is_ok:
            return []
        value = result.value
        value = cast(CdnVideoHubResponseJson, value)
        episode_mapping: Dict[int, List[ItemJson]] = {}
        for data in value["items"]:
            if not episode_mapping.get(data["episode"]):
                episode_mapping[data["episode"]] = []
            episode_mapping[data["episode"]].append(data)

        episodes = [
            Episode(title="Episode", ordinal=num, data=data, **self._kwargs_http)
            for num, data in episode_mapping.items()
        ]
        # playlist response not guarantee order
        episodes.sort(key=lambda i: i.ordinal)
        return episodes


@define(kw_only=True)
class Episode(BaseEpisode):
    data: list[ItemJson]

    def get_sources(self) -> list["Source"]:
        results = [
            Source(
                title=item["voiceStudio"],
                url="https://plapi.cdnvideohub.com",  # stub
                cdn_videohub_vk_id=item["vkId"],
            )
            for item in self.data
        ]
        return results

    async def a_get_sources(self) -> list["Source"]:
        return self.get_sources()


@define(kw_only=True)
class Source(BaseSource):
    pass


if __name__ == "__main__":
    # manual testing parser
    from anicli_api.tools import cli

    cli(Extractor())
