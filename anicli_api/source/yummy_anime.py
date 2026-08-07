from __future__ import annotations

from typing import Dict, List, Optional, cast
from urllib.parse import unquote_plus, urlsplit

from attrs import define

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource

from anicli_api.player.base import Video
from anicli_api.source.parsers.yummy_anime_me_parser import (
    YummyAnimeApi,
    PageJsCVHParams,
    PageCVHIframeParams,
    extract_cvh_path,
)

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
    def _cdnvideohub_extract_vkid_cadidate(
        api_response: CdnVideoHubResponseJson, episode: int, dubbing_code: str
    ) -> Optional[str]:
        # dubbing_code same value as voiceStudio key
        # may return None if studio listed in source metadata but actually
        # has no videos uploaded to cdnvideohub (stale iframe url / fresh release)
        candidates = [
            i for i in api_response["items"] if i["episode"] == int(episode) and i["voiceStudio"] == dubbing_code
        ]
        return candidates[0]["vkId"] if candidates else None

    def get_videos(self, **httpx_kwargs) -> MutableSequence[Video]:
        # TODO: move to anicli-api.player scope
        # https://ru.yummyani.me/iframeCVH.html?dubbing_code=Sanae&anime_id=339&episode=1&dubbing=%D0%9E%D0%B7%D0%B2%D1%83%D1%87%D0%BA%D0%B0+Sanae
        if "/iframeCVH.html?" in self.url:
            resp = self.http.get(self.url)
            base_url = urlsplit(self.url).netloc
            js_path = extract_cvh_path(resp.text)
            js_url = "https://" + base_url + js_path
            iframe_params = PageCVHIframeParams(self.url).parse()
            # dubbing_code captured raw from query; url-decode (+ -> space, %XX -> char)
            # so it matches voiceStudio key in cdnvideohub API response
            iframe_params["dubbing_code"] = unquote_plus(iframe_params["dubbing_code"])
            # WARNING: used brotli encoding algorithm
            # required httpx[brotli] dependency
            script_resp = self.http.get(js_url)
            script_params = PageJsCVHParams(script_resp.text).parse()
            resp_api = CdnVideoHubAPI.get_params_from_page(
                self.http, pub=script_params["data_pub_id"], aggr=script_params["aggr"], id=iframe_params["anime_id"]
            )
            if not resp_api.is_ok:
                # TODO: handle error
                return []
            # search candidate by anime_id, episode_id and dubbing code
            value = resp_api.value
            value = cast(CdnVideoHubResponseJson, value)
            vkid = self._cdnvideohub_extract_vkid_cadidate(
                value, iframe_params["episode"], iframe_params["dubbing_code"]
            )
            if not vkid:
                # studio listed in source metadata but no actual video in cdnvideohub
                return []
            return self._cdn_videohub_extractor(self.http, vkid=vkid)
        return super().get_videos(**httpx_kwargs)

    async def a_get_videos(self, **httpx_kwargs) -> MutableSequence[Video]:
        if "/iframeCVH.html?" in self.url:
            resp = await self.http_async.get(self.url)
            base_url = urlsplit(self.url).netloc
            js_path = extract_cvh_path(resp.text)
            js_url = "https://" + base_url + js_path
            iframe_params = PageCVHIframeParams(self.url).parse()
            # dubbing_code captured raw from query; url-decode (+ -> space, %XX -> char)
            # so it matches voiceStudio key in cdnvideohub API response
            iframe_params["dubbing_code"] = unquote_plus(iframe_params["dubbing_code"])
            script_resp = await self.http_async.get(js_url)
            script_params = PageJsCVHParams(script_resp.text).parse()
            resp_api = await CdnVideoHubAPI.async_get_params_from_page(
                self.http_async,
                pub=script_params["data_pub_id"],
                aggr=script_params["aggr"],
                id=iframe_params["anime_id"],
            )
            if not resp_api.is_ok:
                # TODO: handle error
                return []
            # search candidate by anime_id, episode_id and dubbing code
            value = resp_api.value
            value = cast(CdnVideoHubResponseJson, value)
            vkid = self._cdnvideohub_extract_vkid_cadidate(
                value, iframe_params["episode"], iframe_params["dubbing_code"]
            )
            if not vkid:
                # studio listed in source metadata but no actual video in cdnvideohub
                return []
            return await self._async_cdn_videohub_extractor(self.http_async, vkid=vkid)
        return await super().a_get_videos(**httpx_kwargs)


if __name__ == "__main__":
    from anicli_api.tools import cli

    cli(Extractor())
