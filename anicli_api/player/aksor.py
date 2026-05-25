from __future__ import annotations
import re
from typing import List, cast

from anicli_api.player.base import BaseVideoExtractor, Video, url_validator
from anicli_api.player.parsers.aksor_parser import AksorPlayerApi

# types
from anicli_api.player.parsers.aksor_parser import AksorAPIResponseJson

__all__ = ["Aksor"]

# url validator pattern
_URL_EQ = re.compile(
    r"""
    https?://(www\.)?
    (player)?\.
    aksor(\.yani)?\.tv
    /video
""",
    re.X,
)
# url validate decorator
player_validator = url_validator(_URL_EQ)


class Aksor(BaseVideoExtractor):
    URL_RULE = _URL_EQ

    _QUALITY_KEYS = {"q1080": 1080, "q360": 360, "q480": 480, "q720": 720, "q2k": 2048, "q4k": 4096}

    @player_validator
    def parse(self, url: str, **kwargs) -> list[Video]:
        url = url.split("?", 1)[0]
        video_id = url.split("/")[-1]
        result = AksorPlayerApi.fetch(self.http, video_id=video_id)
        if not result.is_ok:
            return []
        value = result.value
        value = cast(AksorAPIResponseJson, value)
        videos: List[Video] = []
        for quality, video_url in value["qualities"].items():
            if not video_url:
                continue
            quality = self._QUALITY_KEYS[quality]
            type_ = video_url.split(".")[-1]
            videos.append(
                Video(
                    type=type_,
                    url=video_url,
                    quality=quality,
                )
            )
        return videos

    @player_validator
    async def a_parse(self, url: str, **kwargs) -> list[Video]:
        url = url.split("?", 1)[0]
        video_id = url.split("/")[-1]
        result = await AksorPlayerApi.async_fetch(self.a_http, video_id=video_id)
        if not result.is_ok:
            return []
        value = result.value
        value = cast(AksorAPIResponseJson, value)
        videos: List[Video] = []
        for quality, video_url in value["qualities"].items():
            if not video_url:
                continue
            quality = self._QUALITY_KEYS[quality]
            type_ = video_url.split(".")[-1]
            videos.append(
                Video(
                    type=type_,
                    url=video_url,
                    quality=quality,
                )
            )
        return videos


if __name__ == "__main__":
    print(Aksor().parse("https://player.aksor.tv/video/be348c0423c77acd06f24bcbee51c5fc"))
