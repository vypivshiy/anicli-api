"""Decoders class for video hostings"""
from abc import ABC, abstractmethod
from base64 import b64decode
from dataclasses import dataclass, field
import re
from html import unescape
from typing import Dict, Optional, Any, Literal, List
from urllib.parse import urlparse
import json

from httpx import Timeout  # fix aniboom timeouts

from anicli_api._http import BaseHTTPSync, BaseHTTPAsync
from anicli_api.exceptions import DecoderError, RegexParseError


@dataclass
class MetaVideo:
    type: Literal["mp4", "m3u8", "mpd"]
    quality: int
    url: str
    extra_headers: Optional[Dict] = field(default_factory=dict)

    def dict(self) -> Dict[str, Any]:
        return self.__dict__


class BaseDecoder(ABC):
    def __init__(self, **kwargs):
        if kwargs:
            self.http = BaseHTTPSync(**kwargs)
            self.a_http = BaseHTTPAsync(**kwargs)
        else:
            self.http = BaseHTTPSync()
            self.a_http = BaseHTTPAsync()

    @classmethod
    @abstractmethod
    def parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        ...

    @classmethod
    @abstractmethod
    async def async_parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        ...

    @classmethod
    @abstractmethod
    def _compare_url(cls, url: str) -> bool:
        ...

    def __eq__(self, other: str):  # type: ignore
        """compare class instance with url string"""
        return self._compare_url(other)


class Kodik(BaseDecoder):
    REFERER = "https://kodik.info"
    BASE_PAYLOAD = {"bad_user": True,
                    "info": "{}"}

    @classmethod
    def parse(cls, url: str, **kwargs):
        """High-level kodik video link extractor

        Usage: Kodik.parse(<url>)

        :param str url: kodik url
        :return: dict of direct links
        """
        url = url.split("?")[0]
        if url != cls():
            raise DecoderError(f"{url} is not Kodik")

        cls_ = cls(**kwargs)
        with cls_.http as session:
            raw_response = session.get(url, headers={"referer": cls.REFERER}).text
            if cls.is_banned(raw_response):
                raise DecoderError("This video is not available in your country")

            payload = cls._parse_payload(raw_response)
            api_url = cls._get_api_url(url)
            response = session.post(
                api_url,
                data=payload,
                headers={"origin": cls.REFERER,
                         "referer": api_url.replace("/gvi", ""),
                         "accept": "application/json, text/javascript, */*; q=0.01"}).json()["links"]
            return cls._response_to_meta_video(response)

    @classmethod
    def _response_to_meta_video(cls, response: dict) -> List[MetaVideo]:
        for quality in response:
            response[quality] = cls.decode(response[quality][0]['src'])

        if response.get("720") and "480.mp4" in response.get("720"):  # type: ignore
            response["720"] = response.get("720").replace("/480.mp4", "/720.mp4")  # type: ignore
        return [MetaVideo(type="m3u8", quality=int(quality), url=video_url)
                for quality, video_url in response.items()]

    @classmethod
    async def async_parse(cls, url: str, **kwargs):
        url = url.split("?")[0]
        if url != cls():
            raise DecoderError(f"{url} is not Kodik")
        cls_ = cls(**kwargs)

        async with cls_.a_http as session:
            raw_response = (await session.get(url, headers={"referer": cls.REFERER})).text
            if cls.is_banned(raw_response):  # type: ignore
                raise DecoderError("This video is not available in your country")
            payload = cls._parse_payload(raw_response)  # type: ignore
            api_url = cls._get_api_url(url)
            response = (await session.post(api_url, data=payload,
                                           headers={"origin": cls.REFERER,
                                                    "referer": api_url.replace("/gvi", ""),
                                                    "accept": "application/json, text/javascript, */*; q=0.01"}
                                           )).json()["links"]
            return cls._response_to_meta_video(response)

    @classmethod
    def _parse_payload(cls, response: str) -> Dict:
        payload = cls.BASE_PAYLOAD.copy()
        if not (result := re.search(r"var urlParams = (?P<params>'{.*?}')", response)):
            raise RegexParseError("Error parse payload params with 'var urlParams = (?P<params>'{.*?}')'")
        result = json.loads(result.groupdict()["params"].strip("'"))
        payload.update(result)  # type: ignore
        for pattern in (r'var type = "(?P<type>.*?)";',
                        r"videoInfo\.hash = '(?P<hash>\w+)';",
                        r'var videoId = "(?P<id>\d+)"'
                        ):
            if result := re.search(pattern, response):
                payload.update(result.groupdict())
            else:
                raise RegexParseError(f"Error parse payload params with '{pattern}'")
        return payload

    @classmethod
    def is_kodik(cls, url: str) -> bool:
        """return True if url player is kodik."""
        return bool(re.match(r"https://\w+\.\w{2,6}/seria/\d+/\w+/\d{3,4}p", url))

    @classmethod
    def is_banned(cls, response: str):
        return bool(re.match(r"<title>Error</title>", response))

    @classmethod
    def _get_api_url(cls, url: str) -> str:
        if not url.startswith("//"):
            url = f"//{url}"
        if not url.startswith("https:"):
            url = f"https:{url}"
        if url_ := re.search(r"https://\w+\.\w{2,6}/seria/\d+/\w+/\d{3,4}p", url):
            return f"https://{urlparse(url_.group()).netloc}/gvi"
        raise DecoderError(f"{url} is not Kodik")

    @classmethod
    def _compare_url(cls, url: str) -> bool:
        return cls.is_kodik(url) if isinstance(url, str) else NotImplemented

    @staticmethod
    def decode(url_encoded: str) -> str:
        """kodik player video url decoder (reversed base64 string)

        :param str url_encoded: encoded url
        :return: decoded video url"""
        url_encoded = url_encoded[::-1]
        if not url_encoded.endswith("=="):
            url_encoded += "=="
        link = b64decode(url_encoded).decode()
        if not link.startswith("https"):
            link = f"https:{link}"
        return link


class Aniboom(BaseDecoder):
    REFERER = "https://animego.org/"
    ACCEPT_LANG = "ru-RU"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.http.timeout = Timeout(5.0, connect=0.3)
        self.a_http.timeout = Timeout(5.0, connect=0.3)

    @classmethod
    def parse(cls, url: str, **kwargs):
        if url != cls():
            raise DecoderError(f"{url} is not Aniboom")
        url = unescape(url)
        cls_ = cls(**kwargs)
        with cls_.http as session:
            response = session.get(url, headers={"referer": cls.REFERER})
            if not response.is_success:
                raise ConnectionError(f"{url} return {response.status_code} code")

            links = cls_._extract_links(unescape(response.text))
            if len(links.keys()) == 0:
                raise RegexParseError("Failed extract aniboom video links")

            m3u8_response = session.get(links["m3u8"], headers={"referer": "https://aniboom.one",
                                                                "origin": "https://aniboom.one/",
                                                                "accept-language": cls.ACCEPT_LANG}).text
            m3u8_links = cls_._parse_m3u8(links["m3u8"], m3u8_response)
            videos = [MetaVideo(
                type="m3u8",
                quality=int(quality),
                url=link,
                extra_headers={"referer": "https://aniboom.one/",
                               'accept-language': 'ru-RU',
                               'user-agent': cls_.a_http.headers["user-agent"]}
            ) for quality, link in m3u8_links.items()]

            if links.get("mpd"):
                videos.append(MetaVideo(
                    type="mpd",
                    quality=1080,
                    url=links["mpd"],
                    extra_headers={"referer": "https://aniboom.one/",
                                   'accept-language': 'ru-RU',
                                   'user-agent': cls_.http.headers["user-agent"]}))
            return videos

    @classmethod
    async def async_parse(cls, url: str, **kwargs):
        if url != cls():
            raise DecoderError(f"{url} is not Aniboom")
        cls_ = cls(**kwargs)
        async with cls_.a_http as session:
            response = await session.get(url)
            if not response.is_success:
                raise ConnectionError(f"{url} return {response.status_code} code")

            links = cls_._extract_links(unescape(response.text))
            if len(links.keys()) == 0:
                raise RegexParseError("Failed extract aniboom video links")
            m3u8_response = (await session.get(links["m3u8"],
                                               headers={"referer": cls.REFERER,
                                                        "origin": cls.REFERER.rstrip("/"),
                                                        "accept-language": cls.ACCEPT_LANG})).text

            m3u8_links = cls_._parse_m3u8(links["m3u8"], m3u8_response)
            videos = [MetaVideo(
                type="m3u8",
                quality=int(quality),
                url=link,
                extra_headers={"referer": "https://aniboom.one/",
                               'accept-language': 'ru-RU',
                               'user-agent': cls_.a_http.headers["user-agent"]}
            ) for quality, link in m3u8_links.items()]

            if links.get("mpd"):
                videos.append(MetaVideo(
                    type="mpd",
                    quality=1080,
                    url=links["mpd"],
                    extra_headers={"referer": "https://aniboom.one/",
                                   'accept-language': 'ru-RU',
                                   'user-agent': cls_.a_http.headers["user-agent"]}))
            return videos

    @staticmethod
    def is_aniboom(url: str) -> bool:
        """return True if player url is aniboom"""
        return "aniboom" in urlparse(url).netloc

    @classmethod
    def _compare_url(cls, url: str) -> bool:
        return cls.is_aniboom(url)

    @classmethod
    def _parse_m3u8(cls, m3u8_url: str, m3u8_response: str) -> Dict[str, str]:
        result = {}
        base_m3u8_url = m3u8_url.replace("/master.m3u8", "")
        for url_data in re.finditer(r'#EXT-X-STREAM-INF:BANDWIDTH=\d+,RESOLUTION=(?P<resolution>\d+x\d+),'
                                    r'CODECS=".*?",AUDIO="\w+"\s(?P<src>\w+\.m3u8)', m3u8_response):
            if m3u8_dict := url_data.groupdict():
                result[m3u8_dict["resolution"].split("x")[-1]] = f"{base_m3u8_url}/{url_data['src']}"
        return result

    @classmethod
    def _extract_links(cls, raw_response: str) -> Dict[str, str]:
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


class Sibnet(BaseDecoder):
    @classmethod
    def parse(cls, url: str, **kwargs):
        if url != cls():
            raise DecoderError(f"{url} is not Sibnet")
        cls_ = cls(**kwargs)
        with cls_.http as session:
            response = session.get(url)
            result = re.search(r'"(?P<url>/v/.*?\.mp4)"', response.text)
            video_url = "https://video.sibnet.ru" + result.groupdict().get("url")  # type: ignore
            return [MetaVideo(type="mp4", url=video_url, extra_headers={"Referer": url}, quality=480)]

    @classmethod
    async def async_parse(cls, url: str, **kwargs):
        if url != cls():
            raise DecoderError(f"{url} is not Sibnet")
        cls_ = cls(**kwargs)
        async with cls_.a_http as session:
            response = await session.get(url)
            result = re.search(r'"(?P<url>/v/.*?\.mp4)"', response.text)
            video_url = "https://video.sibnet.ru" + result.groupdict().get("url")  # type: ignore
            return [MetaVideo(type="mp4", url=video_url, extra_headers={"Referer": url}, quality=480)]

    @classmethod
    def _compare_url(cls, url: str) -> bool:
        return "video.sibnet" in url
