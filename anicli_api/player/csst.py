"""NOTE: THIS Extractor not work in RU"""
import re
from typing import List

from scrape_schema.fields.regex import ReMatchListDict
from anicli_api.player.base import BaseVideoExtractor, Video, url_validator

__all__ = ["CsstOnline"]
# url validator pattern
_URL_EQ = re.compile(r"https?://(www\.)?csst\.online/embed/\d+")
# url validate decorator
player_validator = url_validator(_URL_EQ)


class CsstOnline(BaseVideoExtractor):
    URL_RULE = _URL_EQ
    RE_URLS = re.compile(r'\[(?P<quality>\d{3,4})p\](?P<url>https?://(?:www\.)?.*?\.mp4)')
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
        url_data = ReMatchListDict(self.RE_URLS).extract(response)
        return [
            Video(type="mp4", quality=data["quality"], url=data["url"]) for data in url_data[:4]
        ]


if __name__ == '__main__':
    print(*CsstOnline().parse("https://csst.online/embed/487794"), sep="\n")


