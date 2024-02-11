import re
from typing import List

from anicli_api.player.base import BaseVideoExtractor, Video, url_validator

__all__ = ["SovietRomanticaPlayer"]
_URL_EQ = re.compile(r"https?://(www\.)?[a-z1-9]{1,6}\.sovetromantica\.com/(?:anime|dorama)/.*\.m3u8")
player_validator = url_validator(_URL_EQ)


class SovietRomanticaPlayer(BaseVideoExtractor):
    URL_RULE = _URL_EQ

    @player_validator
    def parse(self, url: str, **kwargs) -> List[Video]:
        return self._extract(url)

    @player_validator
    async def a_parse(self, url: str, **kwargs) -> List[Video]:
        return self._extract(url)

    @staticmethod
    def _extract(response) -> List[Video]:
        return [Video(type="m3u8", quality=1080, url=response)]
