import re
from typing import List

from anicli_api.player.base import BaseVideoExtractor, Video, url_validator

__all__ = ["PlayerExtractor"]
# url validator pattern
_URL_EQ = re.compile(r"https?://(www\.)?.")
# url validate decorator
player_validator = url_validator(_URL_EQ)


class PlayerExtractor(BaseVideoExtractor):
    URL_RULE = _URL_EQ

    @player_validator
    def parse(self, url: str, **kwargs) -> List[Video]:
        response = self.http.get(url)
        return self._extract(response)

    @player_validator
    async def a_parse(self, url: str, **kwargs) -> List[Video]:
        async with self.a_http as client:
            response = await client.get(url)
            return self._extract(response)

    def _extract(self, response) -> List[Video]:
        # any extract logic
        pass


if __name__ == "__main__":
    PlayerExtractor().parse("")
