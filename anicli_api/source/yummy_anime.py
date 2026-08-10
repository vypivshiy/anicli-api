from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple, cast
from urllib.parse import unquote_plus, urlsplit

from attrs import define

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource

from anicli_api.player.base import Video
from anicli_api.source.parsers.yummy_anime_me_parser import YummyAnimeApi

# types
from anicli_api.source.parsers.yummy_anime_me_parser import (
    AnimeListResponseJson,
    AnimeItemJson,
    ScheduleResponseJson,
    ScheduleItemJson,
    VideoListResponseJson,
    VideoItemJson,
)
from anicli_api.player.parsers.cdnvideohub_parser import CdnVideoHubAPI, CdnVideoHubResponseJson

from anicli_api.typing import MutableSequence


class Extractor(BaseExtractor):
    BASE_URL = "https://site.yummyani.me"

    def search(self, query: str) -> list["Search"]:
        # https://yummy-anime.ru/api/swagger#/Anime/get_anime
        result = YummyAnimeApi.search_anime(self.http, q=query, offset=0, limit=20)
        if not result.is_ok:
            return []
        value = result.value
        value = cast(AnimeListResponseJson, value)
        results = [
            Search(
                title=data["title"],
                thumbnail=data["poster"]["medium"],
                url=self.BASE_URL + "/catalog/item/" + data["anime_url"],
                data=data,
                **self._kwargs_http,
            )
            for data in value["response"]
        ]
        return results

    async def a_search(self, query: str) -> list["Search"]:
        result = await YummyAnimeApi.async_search_anime(self.http_async, q=query, offset=0, limit=20)
        if not result.is_ok:
            return []
        value = result.value
        value = cast(AnimeListResponseJson, value)
        results = [
            Search(
                title=data["title"],
                thumbnail=data["poster"]["medium"],
                url=self.BASE_URL + "/catalog/item/" + data["anime_url"],
                data=data,
                **self._kwargs_http,
            )
            for data in value["response"]
        ]
        return results

    def ongoing(self) -> list["Ongoing"]:
        # too many output (100 items)
        # https://yummy-anime.ru/api/swagger#/Anime/get_anime_schedule
        result = YummyAnimeApi.schedule(self.http)
        if not result.is_ok:
            return []
        value = result.value
        value = cast(ScheduleResponseJson, value)
        results = [
            Ongoing(
                data=data,
                title=data["title"],
                thumbnail=data["poster"]["medium"],
                url=self.BASE_URL + "/catalog/item/" + data["anime_url"],
                **self._kwargs_http,
            )
            for data in value["response"]
            # ignore announced titles wout episodes
            if data["episodes"]["count"] > 0
        ]
        return results

    async def a_ongoing(self) -> list["Ongoing"]:
        result = await YummyAnimeApi.async_schedule(self.http_async)
        if not result.is_ok:
            return []
        value = result.value
        value = cast(ScheduleResponseJson, value)
        results = [
            Ongoing(
                data=data,
                title=data["title"],
                thumbnail=data["poster"]["medium"],
                url=self.BASE_URL + "/catalog/item/" + data["anime_url"],
                **self._kwargs_http,
            )
            for data in value["response"]
            # ignore announced titles wout episodes
            if data["episodes"]["count"] > 0
        ]
        return results


@define(kw_only=True)
class Search(BaseSearch):
    data: AnimeItemJson

    def get_anime(self) -> "Anime":
        return Anime(
            title=self.title,
            thumbnail=self.thumbnail,
            description=self.data["description"],
            data=self.data,
            **self._kwargs_http,
        )

    async def a_get_anime(self) -> "Anime":
        return self.get_anime()

    def __str__(self):
        kw_min = {}
        if year := self.data.get("year", ""):
            kw_min["year"] = year
        if status := self.data.get("anime_status", {}).get("title", ""):
            kw_min["status"] = status
        if type_ := self.data.get("type", {}).get("name", ""):
            kw_min["type"] = type_

        out = f"({kw_min!r})" if kw_min else ""

        return f"{self.title} {out}".rstrip()


@define(kw_only=True)
class Ongoing(BaseOngoing):
    data: ScheduleItemJson

    def get_anime(self) -> "Anime":
        # transform to corrent object
        result = YummyAnimeApi.anime_by_ids(self.http, ids=[self.data["anime_id"]])
        # TODO: handle error
        if not result.is_ok:
            return
        value = result.value
        value = cast(AnimeListResponseJson, value)
        data = value["response"][0]  # single element fetched
        return Anime(
            title=data["title"],
            thumbnail=data["poster"]["medium"],
            description=data["description"],
            data=data,
            **self._kwargs_http,
        )

    async def a_get_anime(self) -> "Anime":
        result = await YummyAnimeApi.async_anime_by_ids(self.http_async, ids=[self.data["anime_id"]])
        # TODO: handle error
        if not result.is_ok:
            return
        value = result.value
        value = cast(AnimeListResponseJson, value)
        data = value["response"][0]  # single element fetched
        return Anime(
            title=data["title"],
            thumbnail=data["poster"]["medium"],
            description=data["description"],
            data=data,
            **self._kwargs_http,
        )

    def __str__(self):
        count = self.data.get("episodes", {}).get("count", 0)
        aired = self.data.get("episodes", {}).get("aired", 0)
        return f"{self.title} (ep count: {count}, aired={aired})".rstrip()


@define(kw_only=True)
class Anime(BaseAnime):
    data: AnimeItemJson

    def get_episodes(self) -> list["Episode"]:
        anime_id = self.data["anime_id"]
        result = YummyAnimeApi.anime_videos(self.http, id=anime_id)
        if not result.is_ok:
            return []
        value = result.value
        value = cast(VideoListResponseJson, value)
        data = value["response"]
        mapping_videos: Dict[str, List[VideoItemJson]] = {}
        for video in data:
            # not implemented player (too complex reverse)
            if "alloha" in video["iframe_url"]:
                continue
            if not mapping_videos.get(video["number"]):
                mapping_videos[video["number"]] = []
            mapping_videos[video["number"]].append(video)
        results = [
            Episode(title="Episode", ordinal=int(num), data=videos, **self._kwargs_http)
            for num, videos in mapping_videos.items()
        ]
        return results

    async def a_get_episodes(self) -> list["Episode"]:
        anime_id = self.data["anime_id"]
        result = await YummyAnimeApi.async_anime_videos(self.http_async, id=anime_id)
        if not result.is_ok:
            return []
        value = result.value
        value = cast(VideoListResponseJson, value)
        data = value["response"]
        mapping_videos: Dict[str, List[VideoItemJson]] = {}
        for video in data:
            # not implemented player (too complex reverse)
            if "alloha" in video["iframe_url"]:
                continue
            if not mapping_videos.get(video["number"]):
                mapping_videos[video["number"]] = []
            mapping_videos[video["number"]].append(video)
        results = [
            Episode(title="Episode", ordinal=int(num), data=videos, **self._kwargs_http)
            for num, videos in mapping_videos.items()
        ]
        return results


@define(kw_only=True)
class Episode(BaseEpisode):
    data: List[VideoItemJson]

    # def cdnvideohub_playlist(self, iframe_url: str):
    #     # if "/iframeCVH.html?" in self.url:
    #     # 1. prepare
    #     self.ordinal
    #     pass

    def get_sources(self) -> list["Source"]:
        results = [
            Source(
                title=video["data"]["dubbing"],
                url="https:" + video["iframe_url"] if video["iframe_url"].startswith("//") else video["iframe_url"],
                **self._kwargs_http,
            )
            for video in self.data
        ]
        return results

    async def a_get_sources(self) -> list["Source"]:
        return self.get_sources()


@define(kw_only=True)
class Source(BaseSource):
    @staticmethod
    def _get_js_url(base_url: str, iframe_response: str) -> str:
        # 1. extract js path and build URL
        # <script type="module" crossorigin src="/assets/iframeCVH-Co2NOptb.js"></script>
        js_path = re.search(r'<script[^>]+src="(/assets/iframe[^"]+)">', iframe_response)[1]
        return "https://" + base_url + js_path

    @staticmethod
    def _extract_iframe_params(iframe_url: str) -> Tuple[int, int, str]:
        # 2. params
        anime_id = re.search(r"anime_id=(\d+)", iframe_url)[1]
        episode = re.search(r"episode=(\d+)", iframe_url)[1]
        dubbing_code = re.search(r"dubbing_code=([^&]+)", iframe_url)[1]
        # compared as-is with the voiceStudio value, so it must be decoded (cyrillic names, spaces as "+")
        return int(anime_id), int(episode), unquote_plus(dubbing_code)

    @staticmethod
    def _extract_script_params(js_script_response: str) -> Tuple[str, str]:
        """
        3. extract "data-publisher-id" and "aggr"
        signature script example:

        o = document.createElement("video-player"),
        o.id = "video-player"; const t = new URLSearchParams(window.location.search);
        i = t.get("dubbing_code");
        const a = { "priority-voice": i, episode: t.get("episode"),
        "data-aggregator": "mali",
        "data-title-id": t.get("anime_id") || "",
        "data-publisher-id": 745,
        "is-show-voice-only": !0 };
        for (const i in a) o.setAttribute(i, (null == (e = a[i]) ? void 0 : e.toString()) || "") }
        """
        data_pub_id = re.search(r'"data-publisher-id":\s?(\d+)', js_script_response)[1]
        aggr = re.search(r'"data-aggregator":\s?"([^"]+)"', js_script_response)[1]
        return data_pub_id, aggr

    @staticmethod
    def _cdnvideohub_extract_vkid_cadidate(
        api_response: CdnVideoHubResponseJson, episode: int, dubbing_code: str
    ) -> Optional[str]:
        # dubbing_code same value as voiceStudio key
        # subtitle entries ("voiceType": "Субтитры") come without the voiceStudio key at all
        candidates = [
            i for i in api_response["items"] if i["episode"] == int(episode) and i.get("voiceStudio") == dubbing_code
        ]
        return candidates[0]["vkId"] if candidates else None

    def get_videos(self, **httpx_kwargs) -> MutableSequence[Video]:
        # TODO: move to anicli-api.player scope
        # https://ru.yummyani.me/iframeCVH.html?dubbing_code=Sanae&anime_id=339&episode=1&dubbing=%D0%9E%D0%B7%D0%B2%D1%83%D1%87%D0%BA%D0%B0+Sanae
        if "/iframeCVH.html?" not in self.url:
            return super().get_videos(**httpx_kwargs)
        resp = self.http.get(self.url)
        base_url = urlsplit(self.url).netloc
        js_url = self._get_js_url(base_url, resp.text)
        anime_id, episode, dubbing_code = self._extract_iframe_params(self.url)
        # WARNING: used brotli encoding algorithm
        # required httpx[brotli] dependency
        script = self.http.get(js_url)
        pub_id, aggr = self._extract_script_params(script.text)
        resp_api = CdnVideoHubAPI.get_params_from_page(self.http, pub=pub_id, aggr=aggr, id=anime_id)
        if not resp_api.is_ok:
            # TODO: handle error
            return []
        # search candidate by anime_id, episode_id and dubbing code
        value = resp_api.value
        value = cast(CdnVideoHubResponseJson, value)
        vkid = self._cdnvideohub_extract_vkid_cadidate(value, episode, dubbing_code)
        return self._cdn_videohub_extractor(self.http, vkid=vkid) if vkid else []

    async def a_get_videos(self, **httpx_kwargs) -> MutableSequence[Video]:
        if "/iframeCVH.html?" not in self.url:
            return await super().a_get_videos(**httpx_kwargs)
        resp = await self.http_async.get(self.url)
        base_url = urlsplit(self.url).netloc
        js_url = self._get_js_url(base_url, resp.text)
        anime_id, episode, dubbing_code = self._extract_iframe_params(self.url)
        script = await self.http_async.get(js_url)
        pub_id, aggr = self._extract_script_params(script.text)
        resp_api = await CdnVideoHubAPI.async_get_params_from_page(self.http_async, pub=pub_id, aggr=aggr, id=anime_id)
        if not resp_api.is_ok:
            # TODO: handle error
            return []
        # search candidate by anime_id, episode_id and dubbing code
        value = resp_api.value
        value = cast(CdnVideoHubResponseJson, value)
        if vkid := self._cdnvideohub_extract_vkid_cadidate(value, episode, dubbing_code):
            return await self._async_cdn_videohub_extractor(self.http_async, vkid=vkid)
        else:
            return []


if __name__ == "__main__":
    from anicli_api.tools import cli

    cli(Extractor())
