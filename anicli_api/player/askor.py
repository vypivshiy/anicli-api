import re
from typing import List

from anicli_api.player.base import BaseVideoExtractor, Video, url_validator

__all__ = ["Askor"]
# url validator pattern
_URL_EQ = re.compile(r"https?://(www\.)?aksor\.(yani\.)?tv/.*")
# url validate decorator
player_validator = url_validator(_URL_EQ)


class Askor(BaseVideoExtractor):
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
        if url := re.search(r'var videoUrl = "(.+?)";', response):
            return [Video(type="mpd", quality=1080, url=url[1])]
        return []


if __name__ == "__main__":
    Askor().parse("https://aksor.yani.tv/anime/a10374/AniLibria/01/1080")
