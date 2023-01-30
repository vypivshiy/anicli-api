## TEMPLATE FOR GENERATE DECODER
import re
from typing import List

from anicli_api.base_decoder import BaseDecoder, MetaVideo


class {{ decoder_name }}(BaseDecoder):
    # past regex url rule validator here
    URL_RULE = re.compile(r"{{ url_rule }}")

    @classmethod
    def parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        cls._validate_url(url)
        # set kwargs attrs to httpx.Client and httpx.AsyncClient
        cls_ = cls(**kwargs)

        with cls_.http as session:
            # write request and parse logic here, and convert results to List[MetaVideo]
            response = session.get(url)
            response = response.text
            ...
            return [MetaVideo(type="m3u8", quality=144, url="", extra_headers={})]

    @classmethod
    async def async_parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        cls._validate_url(url)
        cls_ = cls(**kwargs)

        async with cls_.a_http as session:
            # write request and parse logic here, and convert results to List[MetaVideo]
            response = await session.get(url)
            response = response.text
            ...
            return [MetaVideo(type="m3u8", quality=144, url="", extra_headers={})]
