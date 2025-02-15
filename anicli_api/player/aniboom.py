import re
import warnings
from typing import List

from httpx import Response

from .base import BaseVideoExtractor, Video, url_validator
from .parsers.aniboom_parser import AniboomPage

__all__ = ["Aniboom"]

_URL_EQ = re.compile(r"https://(www.)?aniboom\.one/")
player_validator = url_validator(_URL_EQ)


class Aniboom(BaseVideoExtractor):
    URL_RULE = _URL_EQ
    DEFAULT_HTTP_CONFIG = {"headers": {"referer": "https://animego.org/"}}
    VIDEO_HEADERS = {
        # KEYS SHOULD BE STARTED IN Title case, else hls/mpd links return 403 error
        "Referer": "https://aniboom.one/",
        # INCREASE DOWNLOAD SPEED with this static value. Its works only ru-RU value lol
        "Accept-Language": "ru-RU",
        "Origin": "https://aniboom.one",
    }

    @player_validator
    def parse(self, url: str, **kwargs) -> List[Video]:
        response = self.http.get(url)
        return self._extract(response)

    @player_validator
    async def a_parse(self, url: str, **kwargs) -> List[Video]:
        async with self.a_http as client:
            response = await client.get(url)
            return self._extract(response)

    @staticmethod
    def _is_not_found(resp: Response):
        if resp.status_code == 404:
            title = re.search(r"<title>(.+?)</title>", resp.text)
            msg = (
                f"Aniboom returns 404 code with `{title}` error. "
                f"Maybe you missing `episode` and `translation` GET params or your IP not from CIS countries?"
            )
            warnings.warn(msg, stacklevel=1, category=RuntimeWarning)
            return True
        return False

    @staticmethod
    def _is_failed_dash_key(dash_url: str) -> bool:
        # https://github.com/vypivshiy/ani-cli-ru/issues/29
        #
        # actual json signature (look dash.src and hls.src keys):
        # { ...
        # "dash":"{\"src\":\"https:...master_device.m3u8\",\  <<<
        # "type\":\"application\\\/dash+xml\"}",
        # "hls":"{\"src\":\"https:...master_device.m3u8\",    <<<
        # \"type\":\"application\\\/x-mpegURL\"}"
        # ... }
        if dash_url.endswith(".m3u8"):
            warnings.warn("Missing mpd link. This aniboom issue, not anicli-api", stacklevel=1, category=RuntimeWarning)
            return True
        return False

    def _extract(self, response: Response) -> List[Video]:
        if self._is_not_found(response):
            return []

        result = AniboomPage(response.text).parse()
        hls, dash = result.get("hls", None), result.get("dash", None)

        if not hls:
            warnings.warn("Missing m3u8 link", stacklevel=1, category=RuntimeWarning)

        if not dash:
            warnings.warn("Missing dash link", stacklevel=1, category=RuntimeWarning)

        # backend sometimes return m3u8 link in src.dash key
        if self._is_failed_dash_key(dash):
            # in this case, hls.src == dash.src - return one Video object
            return [Video(type="m3u8", quality=1080, url=hls, headers=self.VIDEO_HEADERS)]

        return [
            Video(type="mpd", quality=1080, url=dash, headers=self.VIDEO_HEADERS),
            Video(type="m3u8", quality=1080, url=hls, headers=self.VIDEO_HEADERS),
        ]


if __name__ == "__main__":
    print(Aniboom().parse("https://aniboom.one/embed/6BmMbB7MxWO?episode=1&translation=30"))
