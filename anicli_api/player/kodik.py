import re
from base64 import b64decode
from typing import Dict, List
from urllib.parse import urlsplit

from scrape_schema import BaseSchema, Parsel, Sc, sc_param

from anicli_api.player.base import BaseVideoExtractor, Video, url_validator

__all__ = ["Kodik"]
_URL_EQ = re.compile(r"https://(www\.)?\w{5,32}\.\w{2,6}/(?:seria|video|film)/\d+/\w+/\d{3,4}p")
kodik_validator = url_validator(_URL_EQ)


class _KodikPayload(BaseSchema):
    # first parse params for JSON request to .../gvi entrypoint
    domain: Sc[str, Parsel().re(r'var domain = "(.*?)";')[0]]
    d_sign: Sc[str, Parsel().re(r'var d_sign = "(.*?)";')[0]]
    pd: Sc[str, Parsel().re(r'var pd = "(.*?)";')[0]]
    ref: Sc[str, Parsel().re(r'var ref = "(.*?)";')[0]]
    type: Sc[str, Parsel().re(r"videoInfo.type = '(.*?)';")[0]]
    hash: Sc[str, Parsel().re(r"videoInfo.hash = '(.*?)';")[0]]
    id: Sc[str, Parsel().re(r"videoInfo.id = '(.*?)';")[0]]
    bad_user = sc_param(lambda self: True)
    info = sc_param(lambda self: {})


class Kodik(BaseVideoExtractor):
    URL_RULE = _URL_EQ

    @staticmethod
    def _decode(url_encoded: str) -> str:
        # 30.03.23
        # This code replaces all alphabetical characters in a base64 encoded string
        # with characters that are shifted 13 places in the alphabetical order,
        # wrapping around to the beginning or end of the alphabet as necessary.
        # This is a basic form of a Caesar cipher, a type of substitution cipher.

        # Note: this solution writen by chatgpt
        def char_wrapper(e):
            return chr(
                (ord(e.group(0)) + 13 - (65 if e.group(0) <= "Z" else 97)) % 26 + (65 if e.group(0) <= "Z" else 97)
            )

        base64_url = re.sub(r"[a-zA-Z]", char_wrapper, url_encoded)
        if not base64_url.endswith("=="):
            base64_url += "=="
        return f"https:{b64decode(base64_url).decode()}"

    @kodik_validator
    def parse(self, url: str, **kwargs) -> List[Video]:
        response = self.http.get(url).text
        payload = _KodikPayload(response).dict()
        url_api = f"https://{urlsplit(url).netloc}/gvi"
        response_api = self.http.post(
            url_api,
            data=payload,
            headers={
                "origin": "https://kodik.info",
                "referer": url_api.replace("/gvi", ""),
                "accept": "application/json, text/javascript, */*; q=0.01",
            },
        ).json()["links"]
        return self._extract(response_api)

    @kodik_validator
    async def a_parse(self, url: str, **kwargs) -> List[Video]:
        async with self.a_http as client:
            response = (await client.get(url)).text
            payload = _KodikPayload(response).dict()
            url_api = f"https://{urlsplit(url).netloc}/gvi"
            response_api = (
                await client.post(
                    url_api,
                    data=payload,
                    headers={
                        "origin": "https://kodik.info",
                        "referer": url_api.replace("/gvi", ""),
                        "accept": "application/json, text/javascript, */*; q=0.01",
                    },
                ).json()
            )["links"]
            return self._extract(response_api)

    def _extract(self, response_api: Dict) -> List[Video]:
        return [
            Video(type="m3u8", quality=360, url=self._decode(response_api["360"][0]["src"])),
            Video(type="m3u8", quality=480, url=self._decode(response_api["480"][0]["src"])),
            # maybe return only 360, 480 keys
            Video(
                type="m3u8",
                quality=720,
                url=self._decode(response_api["480"][0]["src"]).replace("360.mp4", "720.mp4"),
            ),
        ]
