import re
from typing import List

import chompjs
from parsel import Selector

from anicli_api.player.base import BaseVideoExtractor, Video, url_validator

__all__ = ["Dzen"]
_URL_EQ = re.compile(r"https://(www.)?dzen\.ru/embed/\w+\?")
player_validator = url_validator(_URL_EQ)


class Dzen(BaseVideoExtractor):
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
        js_script = sel.xpath("//body/script/text()").get()  # type: ignore
        jsn = chompjs.parse_js_object(js_script)
        url_audio = jsn["data"]["content"]["audio_source_url"]
        url_mpd = jsn["data"]["content"]["streams"][0]["url"]
        url_m3u8 = jsn["data"]["content"]["streams"][1]["url"]

        return [
            Video(type="audio", quality=0, url=url_audio),
            Video(type="mpd", quality=1080, url=url_mpd),
            Video(type="m3u8", quality=1080, url=url_m3u8),
        ]


if __name__ == "__main__":
    vids = Dzen().parse(
        "https://dzen.ru/embed/vh1fMeui3d3Y?from_block=partner&from=zen&mute=1&autoplay=0&tv=0-3-types4"
    )
    print(vids[0].url)
    print(vids[-1].url)
