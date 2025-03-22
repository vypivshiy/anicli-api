import re
from typing import List

from anicli_api.player.base import Video, url_validator
from anicli_api.player.sovetromantica import SovietRomanticaPlayer

__all__ = ["SovietRomanticaEmbed"]
_URL_EQ = re.compile(r"https?://(www\.)?sovetromantica\.com/embed/.*")
player_validator = url_validator(_URL_EQ)


class SovietRomanticaEmbed(SovietRomanticaPlayer):
    URL_RULE = _URL_EQ

    @player_validator
    def parse(self, url: str, **kwargs) -> List[Video]:
        resp = self.http.get(url)
        url = re.search(r'"file":"(.+?)"', resp.text)[1]
        return self._extract(url)

    @player_validator
    async def a_parse(self, url: str, **kwargs) -> List[Video]:
        resp = await self.a_http.get(url)
        url = re.search(r'"file":"(.+?)"', resp.text)[1]
        return self._extract(url)
