import re
from typing import List

from parsel import Selector

from anicli_api.player.base import ALL_QUALITIES, BaseVideoExtractor, Video, url_validator

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

    def _extract(self, response: str) -> List[Video]:
        sel = Selector(response)
        videos = sel.xpath('//video[@id="video_player"]/source/@src').getall()
        return [Video(type="mp4", quality=q, url=u) for q, u in zip(ALL_QUALITIES, videos)]


if __name__ == "__main__":
    VkCom().parse("https://vk.com/video_ext.php?oid=793268683&id=456239019&hash=0f28589bfca114f7")
