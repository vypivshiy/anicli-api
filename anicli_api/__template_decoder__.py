"""Video Decoder template

HOW TO create custom decoder:

1. reverse required entrypoins

2. copy this template

3. add regex rule for validate url

4. write entrypoints, parsers:

- for parse - with cls_.http session

-  for async_parse - witch cls_.a_http session

**Notes:**

* cls.http works like httpx.Client

* cls.a_http works like httpx.Client
"""

import re
from typing import List

from anicli_api.base_decoder import BaseDecoder, MetaVideo


# rename class name
class MyDecoder(BaseDecoder):
    # past regex url rule validator here
    URL_RULE = re.compile(r".*")

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
