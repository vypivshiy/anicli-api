from __future__ import annotations
import logging
import re

from anicli_api.player.base import BaseVideoExtractor, Video, url_validator
from anicli_api.player.parsers.cdnvideohub_parser import PageAnimegoIframe
from anicli_api.player.apis.cdnvideohub import CdnVideoHubSync, CdnVideoHubAsync


__all__ = ["CdnVideoHub", "video_playlist_from_vk_id", "a_video_playlist_from_vk_id"]
# url validator pattern
_URL_EQ = re.compile(r"https?://(www\.)?animego\.\w+/cdn\-iframe/\d+/[\w\s]+/\d+/\d+")
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
    "mpegQhdUrl": 1440,  # TODO maybe wrong value ???
    "mpeg2kUrl": 1440,  # ???
    "mpeg4kUrl": 2160,  # ???
}


def video_playlist_from_vk_id(vkid: str) -> list["Video"]:
    result = CdnVideoHubSync().get_video_by_id(id=vkid).data["sources"]
    hls_video = result.pop("hlsUrl")
    dash_video = result.pop("dashUrl")
    videos = []
    for key, video_url in result.items():
        if not video_url:
            continue
        quality = _RESOLUTION_MAPPING.get(key, 0)
        videos.append(
            Video(
                type="mp4",
                quality=quality,  # type: ignore (int)
                url=video_url,  # type: ignore (str)
            )
        )
    # hls, dash - set max quality
    if videos:
        videos.sort(key=lambda i: i.quality)
        max_quality = sorted(videos, key=lambda i: i.quality, reverse=True)[0].quality
        videos.append(Video(type="m3u8", quality=max_quality, url=hls_video))  # type: ignore
        videos.append(Video(type="mpd", quality=max_quality, url=dash_video))  # type: ignore
    return videos


async def a_video_playlist_from_vk_id(vkid: str) -> list["Video"]:
    result = (await CdnVideoHubAsync().get_video_by_id(id=vkid)).data["sources"]
    hls_video = result.pop("hlsUrl")
    dash_video = result.pop("dashUrl")
    videos = []
    for key, video_url in result.items():
        if not video_url:
            continue
        quality = _RESOLUTION_MAPPING.get(key, 0)
        videos.append(
            Video(
                type="mp4",
                quality=quality,  # type: ignore (int)
                url=video_url,  # type: ignore (str)
            )
        )
    # hls, dash - set max quality
    if videos:
        videos.sort(key=lambda i: i.quality)
        max_quality = sorted(videos, key=lambda i: i.quality, reverse=True)[0].quality
        videos.append(Video(type="m3u8", quality=max_quality, url=hls_video))  # type: ignore
        videos.append(Video(type="mpd", quality=max_quality, url=dash_video))  # type: ignore
    return videos


class CdnVideoHub(BaseVideoExtractor):
    URL_RULE = _URL_EQ

    def __init__(self, **httpx_kwargs):
        super().__init__(**httpx_kwargs)
        self.sync_api = CdnVideoHubSync()
        self.async_api = CdnVideoHubAsync()

    @staticmethod
    def _parse_url_parts(url: str) -> tuple[str, str, str, str]:
        # eg signature url
        # https://animego.me/cdn-iframe/47158/Dream Cast/1/1
        path = url.split("cdn-iframe/")[-1]
        # 0 - id, 1 - dubber_name, 2 - season, 3 - episode
        id_, dubber_name, season, episode_num = path.strip().split("/")
        return id_, dubber_name, season, episode_num

    def _extract_videos_common(self, resp3_data):
        """Common logic for extracting videos from API response data."""
        if resp3_data.success:
            hls_video = resp3_data.data["sources"].pop("hlsUrl")
            dash_video = resp3_data.data["sources"].pop("dashUrl")
            videos = []
            for key, video_url in resp3_data.data["sources"].items():
                if not video_url:
                    continue
                quality = _RESOLUTION_MAPPING.get(key, 0)
                videos.append(
                    Video(
                        type="mp4",
                        quality=quality,  # type: ignore (int)
                        url=video_url,  # type: ignore (str)
                    )
                )
            # hls, dash - set max quality
            if videos:
                videos.sort(key=lambda i: i.quality)
                max_quality = sorted(videos, key=lambda i: i.quality, reverse=True)[0].quality
                videos.append(Video(type="m3u8", quality=max_quality, url=hls_video))  # type: ignore
                videos.append(Video(type="mpd", quality=max_quality, url=dash_video))  # type: ignore
            return videos
        return []

    @player_validator
    def parse(self, url: str, **kwargs) -> list[Video]:
        _id, dubber_name, season, episode_num = self._parse_url_parts(url)
        response = self.http.get(url, headers={"referer": "https://animego.me"})
        options = PageAnimegoIframe(response.text).parse()
        # TODO: config APIS http clients
        resp2 = self.sync_api.get_playlist(
            pub=int(options["data_publisher_id"]), aggr=options["data_aggregator"], id=int(options["data_title_id"])
        )
        if resp2.success:
            for data in resp2.data["items"]:
                if (
                    data["episode"] == int(episode_num)
                    and data["season"] == int(season)
                    and data["voiceStudio"] == dubber_name
                ):
                    resp3 = self.sync_api.get_video_by_id(id=data["vkId"])
                    return self._extract_videos_common(resp3)
            else:
                logger.warning("[cdnvideohub] failed get videos candidates")
        return []

    @player_validator
    async def a_parse(self, url: str, **kwargs) -> list[Video]:
        _id, dubber_name, season, episode_num = self._parse_url_parts(url)
        response = self.http.get(url, headers={"referer": "https://animego.me"})
        options = PageAnimegoIframe(response.text).parse()
        # TODO: config APIS http clients
        resp2 = await self.async_api.get_playlist(
            pub=int(options["data_publisher_id"]), aggr=options["data_aggregator"], id=int(options["data_title_id"])
        )
        if resp2.success:
            for data in resp2.data["items"]:
                if (
                    data["episode"] == int(episode_num)
                    and data["season"] == int(season)
                    and data["voiceStudio"] == dubber_name
                ):
                    resp3 = await self.async_api.get_video_by_id(id=data["vkId"])
                    return self._extract_videos_common(resp3)
            else:
                logger.warning("[cdnvideohub] failed get videos candidates")
        return []


if __name__ == "__main__":
    import pprint

    pprint.pp(CdnVideoHub().parse("https://animego.me/cdn-iframe/56854/AniLiberty/1/1"))
