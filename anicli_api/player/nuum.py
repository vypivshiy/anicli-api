import re
import warnings
from typing import List, TYPE_CHECKING

from anicli_api.player.base import BaseVideoExtractor, Video, url_validator

if TYPE_CHECKING:
    from httpx import Response

__all__ = ["Nuum"]
_URL_EQ = re.compile(r"https?://(www\.)?nuum\.ru/embed/record/\d+")
player_validator = url_validator(_URL_EQ)


class Nuum(BaseVideoExtractor):
    URL_RULE = _URL_EQ

    @player_validator
    def parse(self, url: str, **kwargs) -> List[Video]:
        # id for next API request
        video_id = url.split('/')[-1]
        response = self.http.get(f'https://nuum.ru/api/v2/media-containers/{video_id}')

        return self._extract(response)

    @player_validator
    async def a_parse(self, url: str, **kwargs) -> List[Video]:
        async with self.a_http as client:
            video_id = url.split('/')[-1]
            response = await client.get(f'https://nuum.ru/api/v2/media-containers/{video_id}')
            return self._extract(response)

    def _extract(self, response: "Response") -> List[Video]:
        if response.status_code == 404:
            msg = f"Nuum return 404 code, response: {response.json()}"
            warnings.warn(msg, stacklevel=1, category=RuntimeWarning)
            return []
        data = response.json()
        video_url = data['result']['media_container_streams'][0]['stream_media'][0]['media_meta']['media_archive_url']
        return [
            Video(type='m3u8',
                  quality=1080,
                  url=video_url)
        ]
