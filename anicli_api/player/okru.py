#
import json
import re
from html import unescape
from typing import List

from parsel import Selector

from anicli_api.player.base import ALL_QUALITIES, BaseVideoExtractor, Video, url_validator

_URL_EQ = re.compile(r"https://(www.)?ok\.ru/videoembed/\d+")
player_validator = url_validator(_URL_EQ)


class OkRu(BaseVideoExtractor):
    URL_RULE = _URL_EQ

    @player_validator
    def parse(self, url: str, **kwargs) -> List[Video]:
        response = self.http.get(url).text
        return self._extract(response)

    @player_validator
    async def a_parse(self, url: str, **kwargs) -> List[Video]:
        async with self.a_http as client:
            response = (await client.get(url)).text
            return self._extract(response)

    def _extract(self, response: str) -> List[Video]:
        sel = Selector(response)
        raw_jsn = sel.xpath('//div[@class="vid-card_cnt h-mod"]/@data-options').get()
        jsn_1 = json.loads(unescape(raw_jsn))
        json_metadata = json.loads(jsn_1["flashvars"]["metadata"])
        return [
            Video(type="m3u8", quality=q, url=data["url"])
            for q, data in zip(ALL_QUALITIES, json_metadata["videos"])
        ]


if __name__ == "__main__":
    OkRu().parse("https://ok.ru/videoembed/4998442453635")
