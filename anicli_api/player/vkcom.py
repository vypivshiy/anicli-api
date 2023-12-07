import re
from typing import List

import chompjs
import jmespath
from parsel import Selector

from anicli_api.player.base import BaseVideoExtractor, Video, url_validator

_URL_EQ = re.compile(r"https://(www\.)?vk\.com/video_ext\.php\?")
player_validator = url_validator(_URL_EQ)


class VkCom(BaseVideoExtractor):
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

    @staticmethod
    def _extract(response: str) -> List[Video]:
        sel = Selector(response)
        player_params = sel.xpath("//script/text()").re(r"var playerParams = (\{.*\})")[0]
        jsn = chompjs.parse_js_object(player_params)["params"][0]
        urls_keys = jmespath.search("keys(@)[?starts_with(@, 'url')]", jsn)
        videos: List[Video] = [
            Video(type="mp4", url=jsn[url_key], quality=int(url_key.lstrip("url")))  # type: ignore
            for url_key in urls_keys
        ]
        return videos
