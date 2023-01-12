import re
from html import unescape
from typing import List

from anicli_api.base_decoder import BaseDecoder, MetaVideo


class VkCom(BaseDecoder):
    URL_RULE = re.compile(r"vk\.com/video_ext\.php\?")
    QUALITY = [1080, 720, 480, 360, 240, 144]

    @classmethod
    def _parse_videos(cls, response: str) -> List[MetaVideo]:
        objects: List[MetaVideo] = [
            MetaVideo(
                type="mp4",
                quality=cls.QUALITY[quality],  # type: ignore
                url=unescape(match.groupdict()["url"]),
            )
            for quality, match in enumerate(
                re.finditer('<source src="(?P<url>https?://vk[^>]+)" type=[^>]+', response)
            )
            if match
        ]
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
