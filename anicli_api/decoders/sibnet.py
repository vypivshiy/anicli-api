import re
from typing import List

from anicli_api.base_decoder import BaseDecoder, MetaVideo


class Sibnet(BaseDecoder):
    URL_RULE = re.compile(r"video\.sibnet")

    @classmethod
    def parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        cls._validate_url(url)
        cls_ = cls(**kwargs)

        with cls_.http as session:
            response = session.get(url)
            result = re.search(r'"(?P<url>/v/.*?\.mp4)"', response.text)
            video_url = "https://video.sibnet.ru" + result.groupdict().get("url")  # type: ignore
            return [
                MetaVideo(type="mp4", url=video_url, extra_headers={"Referer": url}, quality=480)
            ]

    @classmethod
    async def async_parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        cls._validate_url(url)
        cls_ = cls(**kwargs)

        async with cls_.a_http as session:
            response = await session.get(url)
            result = re.search(r'"(?P<url>/v/.*?\.mp4)"', response.text)
            video_url = "https://video.sibnet.ru" + result.groupdict().get("url")  # type: ignore
            return [
                MetaVideo(type="mp4", url=video_url, extra_headers={"Referer": url}, quality=480)
            ]
