import re
from typing import List

from anicli_api.player.base import BaseVideoExtractor, Video, url_validator

__all__ = ["AnimeJoy"]
_URL_EQ = re.compile(r"https://(www\.)?animejoy\.ru/player")
player_validator = url_validator(_URL_EQ)


class AnimeJoy(BaseVideoExtractor):
    URL_RULE = _URL_EQ

    @player_validator
    def parse(self, url: str, **kwargs) -> List[Video]:
        return self._extract(url)

    @player_validator
    async def a_parse(self, url: str, **kwargs) -> List[Video]:
        return self._extract(url)

    @staticmethod
    def _extract(response: str) -> List[Video]:
        url_1080, url_360 = re.findall(r"](https?://(?:www\.)?.*?\.mp4)", response)
        return [
            Video(type="mp4", quality=1080, url=url_1080),
            Video(type="mp4", quality=360, url=url_360),
        ]
