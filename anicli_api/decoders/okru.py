import re
from html import unescape
from typing import List

from anicli_api.base_decoder import BaseDecoder, MetaVideo


class OkRu(BaseDecoder):
    URL_RULE = re.compile(r"ok\.ru/videoembed/\d+")

    @staticmethod
    def _parse_video(response: str) -> List[MetaVideo]:
        objects: List[MetaVideo] = []
        response = unescape(response).replace('\\"', '"')
        for match in re.finditer(r'"ondemand(?:Hls|Dash)":"(?P<url>https?://.*?)"', response):
            if match.groupdict()["url"].endswith(".m3u8"):
                objects.append(MetaVideo(type="m3u8", quality=1080, url=match.groupdict()["url"]))
            elif match.groupdict()["url"].endswith(".mpd"):
                objects.append(MetaVideo(type="mpd", quality=1080, url=match.groupdict()["url"]))
        return objects

    @classmethod
    def parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        cls._validate_url(url)
        cls_ = cls(**kwargs)

        with cls_.http as session:
            response = session.get(url)
            return cls_._parse_video(response.text)

    @classmethod
    async def async_parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        cls._validate_url(url)
        cls_ = cls(**kwargs)

        async with cls_.a_http as session:
            response = await session.get(url)
            return cls_._parse_video(response.text)
