import re
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
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
        jsn = sel.xpath('//*[@id="video"]/@data-parameters')
        # TODO create m3u8, dash URL parsers
        videos: List[Video] = []
        if dash := jsn.jmespath("dash"):
            videos.append(
                Video(
                    type="mpd",
                    quality=1080,
                    url=dash.re(r"https:.*\.mpd")[0].replace("\\", ""),
                    headers=self.VIDEO_HEADERS,
                )
            )
        if hls := jsn.jmespath("hls"):
            videos.append(
                Video(
                    type="m3u8",
                    quality=1080,
                    url=hls.re(r"https:.*\.m3u8")[0].replace("\\", ""),
                    headers=self.VIDEO_HEADERS,
                )
            )
        return videos
