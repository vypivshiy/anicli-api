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
        # KEYS SHOULD BE STARTED IN Title case, else hls/mpd return 403 error
        "Referer": "https://aniboom.one/",
        "Accept-Language": "ru-RU",  # INCREASE DOWNLOAD SPEED with this static value lol
        "Origin": "https://aniboom.one",
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
        # if pre unescape response - parsel selector incorrect get data-parameters attr
        sel = Selector(response)
        jsn = sel.xpath('//*[@id="video"]/@data-parameters')
        # TODO create m3u8, dash URL parsers in another qualities
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


if __name__ == '__main__':
    Aniboom().parse("https://aniboom.one/embed/6BmMbB7MxWO?episode=1&translation=30")
    # b'#EXTM3U\n#EXT-X-VERSION:7\n#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="group_A1",NAME="audio_1",DEFAULT=YES,URI="media_1.m3u8"\n#EXT-X-STREAM-INF:BANDWIDTH=593867,RESOLUTION=640x360,CODECS="avc1.640028,mp4a.40.2",AUDIO="group_A1"\nmedia_0.m3u8\n#EXT-X-STREAM-INF:BANDWIDTH=943867,RESOLUTION=854x480,CODECS="avc1.640028,mp4a.40.2",AUDIO="group_A1"\nmedia_2.m3u8\n#EXT-X-STREAM-INF:BANDWIDTH=1593867,RESOLUTION=1280x720,CODECS="avc1.640028,mp4a.40.2",AUDIO="group_A1"\nmedia_4.m3u8\n#EXT-X-STREAM-INF:BANDWIDTH=2882867,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",AUDIO="group_A1"\nmedia_6.m3u8\n'