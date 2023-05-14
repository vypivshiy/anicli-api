import json
import re
from html import unescape
from typing import List

from parsel import Selector

from anicli_api.player.base import BaseVideoExtractor, Video, url_validator

__all__ = ["Aniboom"]

_URL_EQ = re.compile(r"https://(www.)?aniboom\.one/")
player_validator = url_validator(_URL_EQ)


class Aniboom(BaseVideoExtractor):
    URL_RULE = _URL_EQ
    DEFAULT_HTTP_CONFIG = {"headers": {"referer": "https://animego.org/"}}
    VIDEO_HEADERS = {
        "Referer": "https://aniboom.one/",
        "Accept-Language": "ru-RU",
        "Origin": "https://aniboom.one",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
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
        # if pre unescape response - parsel selector uncorrect get data-parameters attr
        sel = Selector(response)
        jsn_string = sel.xpath('//*[@id="video"]/@data-parameters').get()
        jsn = json.loads(unescape(jsn_string))  # type: ignore
        # TODO create m3u8, dash URL parsers
        if jsn.get("dash"):
            return [
                Video(
                    type="mpd",
                    quality=1080,
                    url=json.loads(jsn["dash"])["src"],
                    headers=self.VIDEO_HEADERS,
                ),
                Video(
                    type="m3u8",
                    quality=1080,
                    url=json.loads(jsn["hls"])["src"],
                    headers=self.VIDEO_HEADERS,
                ),
            ]
        return [
            Video(
                type="m3u8",
                quality=1080,
                url=json.loads(jsn["hls"])["src"],
                headers=self.VIDEO_HEADERS,
            ),
        ]


if __name__ == "__main__":
    print(Aniboom().parse("https://aniboom.one/embed/6BmMbB7MxWO?episode=1&translation=30"))
