import re
from typing import Dict, List

import chompjs
import jmespath
from parsel import Selector

from anicli_api.player.base import BaseVideoExtractor, Video, url_validator

_URL_EQ = re.compile(r"https://(www.)?ok\.ru/videoembed/\d+")
player_validator = url_validator(_URL_EQ)


class OkRu(BaseVideoExtractor):
    URL_RULE = _URL_EQ
    _QUALITIES_TABLE: Dict[str, int] = {
        "mobile": 144,
        "lowest": 240,
        "low": 360,
        "sd": 480,
        "hd": 720,
        "full": 1080,
    }

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
        raw_jsn = sel.xpath('//div[@class="vid-card_cnt h-mod"]/@data-options').jmespath("flashvars.metadata").get()

        if jsn := chompjs.parse_js_object(raw_jsn):
            results: List[Dict[str, str]] = jmespath.search("videos[*].{name:name, url:url}", jsn)
            videos: List[Video] = [
                Video(
                    type="mp4",
                    quality=self._QUALITIES_TABLE.get(result["name"], 0),  # type: ignore
                    url=result["url"],
                )
                for result in results
            ]
            return videos
        return []
