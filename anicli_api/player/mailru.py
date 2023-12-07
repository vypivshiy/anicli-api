import re
from typing import List

from httpx import Response

from anicli_api.player.base import BaseVideoExtractor, Video, url_validator

__all__ = ["MailRu"]
# url validator pattern
_URL_EQ = re.compile(r"https?://(www\.)?my\.mail\.ru/video/embed")
# url validate decorator
player_validator = url_validator(_URL_EQ)


class MailRu(BaseVideoExtractor):
    URL_RULE = _URL_EQ
    DEFAULT_HTTP_CONFIG = {
        "headers": {
            "Upgrade-Insecure-Requests": "1",
            "Accept": "text/html,application/xhtml+xml,application/"
            "xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
            "application/signed-exchange;v=b3;q=0.7",
        }
    }

    @player_validator
    def parse(self, url: str, **kwargs) -> List[Video]:
        video_id = url.split("/")[-1]
        response = self.http.get(f"https://my.mail.ru/+/video/meta/{video_id}")
        return self._extract(response)

    @player_validator
    async def a_parse(self, url: str, **kwargs) -> List[Video]:
        video_id = url.split("/")[-1]
        async with self.a_http as client:
            response = await client.get(f"https://my.mail.ru/+/video/meta/{video_id}")
            return self._extract(response)

    def _extract(self, response: Response) -> List[Video]:
        cookie = response.cookies.get("video_key")
        return [
            Video(
                type="mp4",
                url=f"https:{video['url']}" if video["url"].startswith("//") else video["url"],
                quality=int(video["key"].rstrip("p")),  # type: ignore
                headers={"Cookie": f"video_key={cookie}"},
            )
            for video in response.json()["videos"]
        ]
