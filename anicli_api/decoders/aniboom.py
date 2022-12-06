import re
from html import unescape
from typing import Dict, List

from httpx import Timeout

from anicli_api.base_decoder import BaseDecoder, MetaVideo

from .exceptions import RegexParseError


class Aniboom(BaseDecoder):
    URL_RULE = re.compile(r"aniboom\.one")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # fix too long aniboom timeouts
        self.http.timeout = Timeout(5.0, connect=0.3)
        self.a_http.timeout = Timeout(5.0, connect=0.3)

    @classmethod
    def _parse_m3u8(cls, m3u8_url: str, m3u8_response: str) -> Dict[str, str]:
        # extract links from m3u8 response
        result = {}
        base_m3u8_url = m3u8_url.replace("/master.m3u8", "")
        for url_data in re.finditer(
            r"#EXT-X-STREAM-INF:BANDWIDTH=\d+,RESOLUTION=(?P<resolution>\d+x\d+),"
            r'CODECS=".*?",AUDIO="\w+"\s(?P<src>\w+\.m3u8)',
            m3u8_response,
        ):
            if m3u8_dict := url_data.groupdict():
                result[
                    m3u8_dict["resolution"].split("x")[-1]
                ] = f"{base_m3u8_url}/{url_data['src']}"
        return result

    @staticmethod
    def _extract_links(raw_response: str) -> Dict[str, str]:
        # get links from raw response
        raw_response = unescape(raw_response)
        result = {}
        if m3u8_url := re.search(r'"hls":"{\\"src\\":\\"(?P<m3u8>.*\.m3u8)\\"', raw_response):
            result.update(m3u8_url.groupdict())
        else:
            result["m3u8"] = None

        if mpd_url := re.search(r'"{\\"src\\":\\"(?P<mpd>.*\.mpd)\\"', raw_response):
            result.update(mpd_url.groupdict())
        else:
            result["mpd"] = None

        for k, v in result.items():
            result[k] = v.replace("\\", "")
        return result

    @classmethod
    def _raw_to_meta_videos(
        cls,
        _cls,
        links,
        m3u8_response,
    ) -> List[MetaVideo]:
        m3u8_links = cls._parse_m3u8(links["m3u8"], m3u8_response)
        videos = []
        # noinspection PyTypeChecker
        for quality, link in m3u8_links.items():
            # noinspection PyTypeChecker
            videos.append(
                MetaVideo(
                    type="m3u8",
                    quality=int(quality),  # type: ignore
                    url=link,
                    extra_headers={
                        "referer": "https://aniboom.one/",
                        "accept-language": "ru-RU",
                        "user-agent": _cls.a_http.headers["user-agent"],
                    },
                )
            )
        if links.get("mpd"):
            videos.append(
                MetaVideo(
                    type="mpd",
                    quality=1080,
                    url=links.get("mpd"),
                    extra_headers={
                        "referer": "https://aniboom.one/",
                        "accept-language": "ru-RU",
                        "user-agent": _cls.http.headers["user-agent"],
                    },
                )
            )
        return videos

    @classmethod
    def parse(cls, url: str, **kwargs):
        url = unescape(url)
        cls._validate_url(url)
        cls_ = cls(**kwargs)

        with cls_.http as session:
            response = session.get(url, headers={"referer": "https://animego.org/"})
            if not response.is_success:
                raise ConnectionError(f"{url} return {response.status_code} code")

            links = cls_._extract_links(unescape(response.text))
            if len(links.keys()) == 0:
                raise RegexParseError("Failed extract aniboom video links")

            m3u8_response = session.get(
                links["m3u8"],
                headers={
                    "referer": "https://aniboom.one",
                    "origin": "https://aniboom.one/",
                    "accept-language": "ru-RU",
                },
            ).text
            return cls_._raw_to_meta_videos(cls_, links, m3u8_response)

    @classmethod
    async def async_parse(cls, url: str, **kwargs):
        url = unescape(url)
        cls._validate_url(url)

        cls_ = cls(**kwargs)
        async with cls_.a_http as session:
            response = await session.get(url)
            if not response.is_success:
                raise ConnectionError(f"{url} return {response.status_code} code")

            links = cls_._extract_links(unescape(response.text))
            if len(links.keys()) == 0:
                raise RegexParseError("Failed extract aniboom video links")
            m3u8_response = (
                await session.get(
                    links["m3u8"],
                    headers={
                        "referer": "https://animego.org/",
                        "origin": "https://animego.org",
                        "accept-language": "ru-RU",
                    },
                )
            ).text

            return cls_._raw_to_meta_videos(cls_, links, m3u8_response)
