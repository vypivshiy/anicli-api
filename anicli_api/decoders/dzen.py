# TODO fix (how?) [ffmpeg/demuxer] hls: Can't support the subtitle...
import re
from typing import List

from anicli_api.base_decoder import BaseDecoder, MetaVideo


class Dzen(BaseDecoder):
    URL_RULE = re.compile(r"dzen\.ru/embed/\w+\?")

    @classmethod
    def _parse_videos(cls, response: str) -> List[MetaVideo]:
        objects: List[MetaVideo] = []
        for match in re.finditer(
            r'"(:?audio_source_url|url)":"(?P<url>https?://(.*?)+)"', response
        ):
            u = match.groupdict()
            if u["url"].endswith(".mpd"):
                objects.append(MetaVideo(type="mpd", quality=1080, url=u["url"]))
            elif u["url"].endswith(".m3u8"):
                objects.append(MetaVideo(type="m3u8", quality=1080, url=u["url"]))
            if u["url"].endswith(".mp4"):
                objects.append(MetaVideo(type="audio", quality=144, url=u["url"]))
        return objects

    @classmethod
    def parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        cls._validate_url(url)
        cls_ = cls(**kwargs)

        with cls_.http as session:
            # write request and parse logic here, and convert results to List[MetaVideo]
            response = session.get(url).text
            return cls_._parse_videos(response)

    @classmethod
    async def async_parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        cls._validate_url(url)
        cls_ = cls(**kwargs)

        async with cls_.a_http as session:
            # write request and parse logic here, and convert results to List[MetaVideo]
            response = await session.get(url)
            response = response.text
            return cls_._parse_videos(response)
