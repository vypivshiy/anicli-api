import re
from typing import List

from anicli_api.decoders.base import BaseDecoder, MetaVideo


class MyDecoder(BaseDecoder):
    # past regex url rule validator here
    URL_VALIDATOR = re.compile(r".*")

    @classmethod
    def parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        cls._validate_url(url)
        cls_ = cls(**kwargs)

        with cls_.http as session:
            # write request and parse logic here, and convert results to List[MetaVideo]
            response = session.get(url)
            response = response.text
            ...
            return [MetaVideo(type="m3u8", quality=144, url="", extra_headers={})]

    @classmethod
    async def async_parse(cls, url: str, **kwargs):
        cls._validate_url(url)
        cls_ = cls(**kwargs)

        async with cls_.a_http as session:
            # write request and parse logic here, and convert results to List[MetaVideo]
            response = await session.get(url)
            response = response.text
            ...
            return [MetaVideo(type="m3u8", quality=144, url="", extra_headers={})]
