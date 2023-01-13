import re
from html import unescape
from typing import Dict, List

from httpx import Timeout

from anicli_api.base_decoder import BaseDecoder, MetaVideo
from anicli_api.decoders.exceptions import RegexParseError


class Aniboom(BaseDecoder):
    URL_RULE = re.compile(r"aniboom\.one")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # fix very long aniboom timeouts
        self.http.timeout = Timeout(5.0, connect=0.5)
        self.a_http.timeout = Timeout(5.0, connect=0.5)

    @classmethod
    def _parse_urls(cls, response: str):
        objects: List[MetaVideo] = []

        response = unescape(response)
        if m3u8_url := re.search(r'"hls":"{\\"src\\":\\"(?P<m3u8>.*\.m3u8)\\"', response):
            objects.append(
                MetaVideo(
                    type="m3u8",
                    quality=1080,
                    url=m3u8_url.groupdict()["m3u8"].replace("\\", ""),
                    extra_headers={
                        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 "
                        "Mobile Safari/537.36",
                        "referer": "https://aniboom.one/",
                        "accept-language": "ru-RU",
                    },
                )
            )
        if mpd_url := re.search(r'"{\\"src\\":\\"(?P<mpd>.*\.mpd)\\"', response):
            objects.append(
                MetaVideo(
                    type="mpd",
                    quality=1080,
                    url=mpd_url.groupdict()["mpd"].replace("\\", ""),
                    extra_headers={
                        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 "
                        "Mobile Safari/537.36",
                        "referer": "https://aniboom.one/",
                        "accept-language": "ru-RU",
                    },
                )
            )
        if not objects:
            raise RegexParseError("Failed extract aniboom video links")
        return objects

    @classmethod
    def parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        url = unescape(url)
        cls._validate_url(url)
        cls_ = cls(**kwargs)

        with cls_.http as session:
            response = session.get(url, headers={"referer": "https://animego.org/"})
            if not response.is_success:
                raise ConnectionError(f"{url} return {response.status_code} code")
            return cls_._parse_urls(response.text)

    @classmethod
    async def async_parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        url = unescape(url)
        cls._validate_url(url)

        cls_ = cls(**kwargs)
        async with cls_.a_http as session:
            response = await session.get(url)
            if not response.is_success:
                raise ConnectionError(f"{url} return {response.status_code} code")
            return cls_._parse_urls(response.text)
