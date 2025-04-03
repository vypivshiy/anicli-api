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
        response = self.http.get(url)
        return self._extract(response.text)

    @player_validator
    async def a_parse(self, url: str, **kwargs) -> List[Video]:
        async with self.a_http as client:
            response = await client.get(url)
            return self._extract(response.text)

    def _extract(self, response: str) -> List[Video]:
        if url := re.search(r'"file":"(.+?)"', response):
            return super()._extract(url[1])
        return []


if __name__ == "__main__":
    SovietRomanticaEmbed().parse("https://sovetromantica.com/embed/episode_1475_1-subtitles")
