import json
import re
from base64 import b64decode
from typing import Dict, List
from urllib.parse import urlparse

from anicli_api.base_decoder import BaseDecoder, MetaVideo

from .exceptions import DecoderError, RegexParseError


class Kodik(BaseDecoder):
    URL_RULE = re.compile(r"https://\w{5,32}\.\w{2,6}/(?:seria|video|film)/\d+/\w+/\d{3,4}p")

    @classmethod
    def _response_to_meta_video(cls, response: dict) -> List[MetaVideo]:
        for quality in response:
            response[quality] = cls.decode(response[quality][0]["src"])

        if response.get("720") and "480.mp4" in response.get("720"):  # type: ignore
            response["720"] = response.get("720").replace("/480.mp4", "/720.mp4")  # type: ignore
        # noinspection PyTypeChecker
        return [
            MetaVideo(type="m3u8", quality=int(quality), url=video_url)  # type: ignore
            for quality, video_url in response.items()
        ]

    @classmethod
    def _parse_payload(cls, response: str) -> Dict:
        payload = {"bad_user": True, "info": "{}"}

        if not (result := re.search(r"var urlParams = '(?P<params>{.*?})'", response)):
            raise RegexParseError(
                "Error parse payload params with 'var urlParams = (?P<params>'{.*?}')'"
            )

        result = json.loads(result.groupdict()["params"])
        payload.update(result)  # type: ignore
        for pattern in (
            r'var type = "(?P<type>.*?)";',
            r"videoInfo\.hash = '(?P<hash>\w+)';",
            r'var videoId = "(?P<id>\d+)"',
        ):
            if result := re.search(pattern, response):
                payload.update(result.groupdict())
            else:
                raise RegexParseError(f"Error parse payload params with '{pattern}'")
        return payload

    @classmethod
    def _get_api_url(cls, url: str) -> str:
        if not url.startswith("//"):
            url = f"//{url}"
        if not url.startswith("https:"):
            url = f"https:{url}"
        if url_ := re.search(
            r"https://\w{5,32}\.\w{2,6}/(?:seria|video|film)/\d+/\w+/\d{3,4}p", url
        ):
            return f"https://{urlparse(url_.group()).netloc}/gvi"
        raise DecoderError(f"{url} is not Kodik")

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

    @classmethod
    def parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        url = url.split("?")[0]
        cls._validate_url(url)
        cls_ = cls(**kwargs)

        with cls_.http as session:
            raw_response = session.get(url, headers={"referer": "https://kodik.info"}).text
            # check error
            if re.match(r"<title>Error</title>", raw_response):
                raise DecoderError("This video is not available in your country")

            payload = cls._parse_payload(raw_response)
            api_url = cls._get_api_url(url)
            response = session.post(
                api_url,
                data=payload,
                headers={
                    "origin": "https://kodik.info",
                    "referer": api_url.replace("/gvi", ""),
                    "accept": "application/json, text/javascript, */*; q=0.01",
                },
            ).json()["links"]
            return cls._response_to_meta_video(response)

    @classmethod
    async def async_parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        url = url.split("?")[0]
        cls._validate_url(url)
        cls_ = cls(**kwargs)

        async with cls_.a_http as session:
            raw_response = (await session.get(url, headers={"referer": "https://kodik.info"})).text
            if re.match(r"<title>Error</title>", raw_response):
                raise DecoderError("This video is not available in your country")

            payload = cls._parse_payload(raw_response)  # type: ignore
            api_url = cls._get_api_url(url)
            response = (
                await session.post(
                    api_url,
                    data=payload,
                    headers={
                        "origin": "https://kodik.info",
                        "referer": api_url.replace("/gvi", ""),
                        "accept": "application/json, text/javascript, */*; q=0.01",
                    },
                )
            ).json()["links"]
            return cls._response_to_meta_video(response)
