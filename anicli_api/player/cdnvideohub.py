from __future__ import annotations
import logging
import re
from typing import List, cast

from httpx import AsyncClient, Client, Headers

from anicli_api.player.base import BaseVideoExtractor, Video, url_validator
from anicli_api.player.parsers.cdnvideohub_parser import (
    PageParseCdnVideoData,
    CdnVideoHubAPI,
    CdnVideoFromIdResponseJson,
    CdnVideoHubResponseJson,
)


__all__ = ["CdnVideoHub", "video_playlist_from_vk_id", "a_video_playlist_from_vk_id"]
# url validator pattern
# TODO: generic url parse add
# TODO: mov extract CDN data to animego
_URL_EQ = re.compile(
    r"""
https?://(www\.)?animego\.\w+/cdn\-iframe/\d+/[\w\s]+/\d+/\d+

""",
    re.X,
)
# url validate decorator
player_validator = url_validator(_URL_EQ)
logger = logging.getLogger("anicli-api")  # type: ignore
_RESOLUTION_MAPPING = {
    "mpegTinyUrl": 144,
    "mpegLowestUrl": 240,
    "mpegLowUrl": 360,
    "mpegMediumUrl": 480,
    "mpegHighUrl": 720,
    "mpegFullHdUrl": 1080,
    "mpegQhdUrl": 1440,
    "mpeg2kUrl": 2048,
    "mpeg4kUrl": 4096,
}


def video_playlist_from_vk_id(
    http_client: Client,
    vkid: str,
    *,
    headers: dict | None = None,
    cookies: dict | None = None,
    timeout: float | None = None,
) -> list["Video"]:
    effective_headers = Headers(http_client.headers)
    effective_headers.update(headers or {})
    user_agent = effective_headers["User-Agent"]
    req: dict = {}
    if headers is not None:
        req["headers"] = headers
    if cookies is not None:
        req["cookies"] = cookies
    if timeout is not None:
        req["timeout"] = timeout
    result = CdnVideoHubAPI.from_vkid(http_client, id=vkid, **req)
    if not result.is_ok:
        return []
    value = result.value
    value = cast(CdnVideoFromIdResponseJson, value)
    sources = value["sources"]
    # late add this
    hls_video = sources.pop("hlsUrl")
    dash_video = sources.pop("dashUrl")
    videos: List[Video] = []
    for key, video in sources.items():
        if not video:
            continue
        quality = _RESOLUTION_MAPPING.get(key, 0)
        videos.append(
            Video(
                type="mp4",
                quality=quality,  # type: ignore (int)
                url=video,  # type: ignore (str)
                headers={"User-Agent": user_agent},
            )
        )
    # hls, dash - set max quality
    if videos:
        videos.sort(key=lambda i: i.quality)
        max_quality = sorted(videos, key=lambda i: i.quality, reverse=True)[0].quality
        videos.append(Video(type="m3u8", quality=max_quality, url=hls_video, headers={"User-Agent": user_agent}))  # type: ignore
        videos.append(Video(type="mpd", quality=max_quality, url=dash_video, headers={"User-Agent": user_agent}))  # type: ignore
    return videos


async def a_video_playlist_from_vk_id(
    http_client: AsyncClient,
    vkid: str,
    *,
    headers: dict | None = None,
    cookies: dict | None = None,
    timeout: float | None = None,
) -> list["Video"]:
    effective_headers = Headers(http_client.headers)
    effective_headers.update(headers or {})
    user_agent = effective_headers["User-Agent"]
    req: dict = {}
    if headers is not None:
        req["headers"] = headers
    if cookies is not None:
        req["cookies"] = cookies
    if timeout is not None:
        req["timeout"] = timeout
    result = await CdnVideoHubAPI.async_from_vkid(http_client, id=vkid, **req)
    if not result.is_ok:
        return []
    value = result.value
    value = cast(CdnVideoFromIdResponseJson, value)
    sources = value["sources"]
    # late add this
    hls_video = sources.pop("hlsUrl")
    dash_video = sources.pop("dashUrl")
    videos: List[Video] = []
    for key, video in sources.items():
        if not video:
            continue
        quality = _RESOLUTION_MAPPING.get(key, 0)
        videos.append(
            Video(
                type="mp4",
                quality=quality,  # type: ignore (int)
                url=video,  # type: ignore (str)
                headers={"User-Agent": user_agent},
            )
        )
    # hls, dash - set max quality
    if videos:
        videos.sort(key=lambda i: i.quality)
        max_quality = sorted(videos, key=lambda i: i.quality, reverse=True)[0].quality
        videos.append(Video(type="m3u8", quality=max_quality, url=hls_video, headers={"User-Agent": user_agent}))  # type: ignore
        videos.append(Video(type="mpd", quality=max_quality, url=dash_video, headers={"User-Agent": user_agent}))  # type: ignore
    return videos


class CdnVideoHub(BaseVideoExtractor):
    URL_RULE = _URL_EQ
    DEFAULT_REQUEST_CONFIG = {"headers": {"referer": "https://animego.me"}}

    @staticmethod
    def _parse_url_parts(url: str) -> tuple[str, str, str, str]:
        # eg signature url
        # https://animego.me/cdn-iframe/47158/Dream Cast/1/1
        path = url.split("cdn-iframe/")[-1]
        # 0 - id, 1 - dubber_name, 2 - season, 3 - episode
        id_, dubber_name, season, episode_num = path.strip().split("/")
        return id_, dubber_name, season, episode_num

    @player_validator
    def parse(
        self, url: str, *, headers: dict | None = None, cookies: dict | None = None, timeout: float | None = None
    ) -> list[Video]:
        req = self._merge_request_kwargs(headers, cookies, timeout)
        _id, dubber_name, season, episode_num = self._parse_url_parts(url)
        response = self.http.get(url, **req)
        options = PageParseCdnVideoData(response.text).parse()
        resp = CdnVideoHubAPI.get_params_from_page(
            self.http,
            pub=options["data_publisher_id"],
            aggr=options["data_aggregator"],
            id=options["data_title_id"],
            **req,
        )
        if not resp.is_ok:
            # TODO: handle errors
            return []
        value = resp.value
        value = cast(CdnVideoHubResponseJson, value)
        for data in value["items"]:
            if (
                data["episode"] == int(episode_num)
                and data["season"] == int(season)
                and data["voiceStudio"] == dubber_name
            ):
                vkid = data["vkId"]
                return video_playlist_from_vk_id(
                    self.http,
                    vkid,
                    headers=headers,
                    cookies=cookies,
                    timeout=timeout,
                )

        logger.warning("[cdnvideohub] failed get videos candidates")
        return []

    @player_validator
    async def a_parse(
        self, url: str, *, headers: dict | None = None, cookies: dict | None = None, timeout: float | None = None
    ) -> list[Video]:
        req = self._merge_request_kwargs(headers, cookies, timeout)
        _id, dubber_name, season, episode_num = self._parse_url_parts(url)
        response = await self.a_http.get(url, **req)
        options = PageParseCdnVideoData(response.text).parse()
        resp = await CdnVideoHubAPI.async_get_params_from_page(
            self.a_http,
            pub=options["data_publisher_id"],
            aggr=options["data_aggregator"],
            id=options["data_title_id"],
            **req,
        )
        if not resp.is_ok:
            # TODO: handle errors
            return []
        value = resp.value
        value = cast(CdnVideoHubResponseJson, value)
        for data in value["items"]:
            if (
                data["episode"] == int(episode_num)
                and data["season"] == int(season)
                and data["voiceStudio"] == dubber_name
            ):
                vkid = data["vkId"]
                return await a_video_playlist_from_vk_id(
                    self.a_http,
                    vkid,
                    headers=headers,
                    cookies=cookies,
                    timeout=timeout,
                )

        logger.warning("[cdnvideohub] failed get videos candidates")
        return []


if __name__ == "__main__":
    import pprint

    pprint.pp(CdnVideoHub().parse("https://animego.me/cdn-iframe/56854/AniLiberty/1/1"))
