from __future__ import annotations

import re

from scrape_schema.fields.regex import ReMatch

from anicli_api.decoders.base import BaseDecoder, MetaVideo


class Decoder(BaseDecoder):
    URL_FILTER = ...

    def parse(self, url: str, **kwargs) -> list[MetaVideo]:
        self._validate_url(url)
        with self.http as client:
            response = client.get(url)
            ...

    async def a_parse(self, url: str, **kwargs) -> list[MetaVideo]:
        self._validate_url(url)
        async with self.a_http as client:
            response = await client.get(url)
            ...
