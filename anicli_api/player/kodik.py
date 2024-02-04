import re
import warnings
from base64 import b64decode
from typing import Dict, List
from urllib.parse import urlsplit

from httpx import Response

from anicli_api.player.base import BaseVideoExtractor, Video, url_validator

__all__ = ["Kodik"]
_URL_EQ = re.compile(r"https://(www\.)?\w{5,32}\.\w{2,6}/(?:seria|video|film)/\d+/\w+/\d{3,4}p")
kodik_validator = url_validator(_URL_EQ)


class Kodik(BaseVideoExtractor):
    URL_RULE = _URL_EQ

    @staticmethod
    def _decode(url_encoded: str) -> str:
        # After 30.03.23 `kodik` provider change reversed base64 string to Caesar cipher (shifted 13 places) + base64.
        # This code simular original js player code for decode url.

        def char_wrapper(e):
            return chr(
                (ord(e.group(0)) + 13 - (65 if e.group(0) <= "Z" else 97)) % 26 + (65 if e.group(0) <= "Z" else 97)
            )

        base64_url = re.sub(r"[a-zA-Z]", char_wrapper, url_encoded)
        if not base64_url.endswith("=="):
            base64_url += "=="
        decoded_url = b64decode(base64_url).decode()
        return decoded_url if decoded_url.startswith("https") else f"https:{b64decode(base64_url).decode()}"

    @staticmethod
    def _parse_api_payload(response: str) -> Dict:
        return {
            "domain": re.search(r'var domain = "(.*?)";', response)[1],  # type: ignore[index]
            "d_sign": re.search(r'var d_sign = "(.*?)";', response)[1],  # type: ignore[index]
            "pd": re.search(r'var pd = "(.*?)";', response)[1],  # type: ignore[index]
            "ref": re.search(r'var ref = "(.*?)";', response)[1],  # type: ignore[index]
            "type": re.search(r"videoInfo.type = '(.*?)';", response)[1],  # type: ignore[index]
            "hash": re.search(r"videoInfo.hash = '(.*?)';", response)[1],  # type: ignore[index]
            "id": re.search(r"videoInfo.id = '(.*?)';", response)[1],  # type: ignore[index]
            "bad_user": True,
            "info": {},
        }

    @staticmethod
    def _get_netloc(url: str) -> str:
        return urlsplit(url).netloc

    @staticmethod
    def _create_url_api(netloc: str, suffix: str = "tru") -> str:
        # 22.01.24 kodik breaking changes:
        # 1. change API entrypoint: /gvi to /vdu
        # 05.02.24 /vdu to /tru

        return f"https://{netloc}/{suffix}"

    @staticmethod
    def _create_api_headers(*, url: str, netloc: str) -> Dict[str, str]:
        # 2. referer - url param (older - kodik netloc)
        return {
            "origin": f"https://{netloc}",
            "referer": url,
            "accept": "application/json, text/javascript, */*; q=0.01",
        }

    @staticmethod
    def _is_not_founded_video(response: Response) -> bool:
        """return true is video is deleted"""
        # video is deleted
        # eg:
        # Вайолет Эвергарден: День, когда ты поймешь, что я люблю тебя, обязательно наступит
        # Violet Evergarden: Kitto "Ai" wo Shiru Hi ga Kuru no Darou:
        # https://kodik.info/seria/310427/09985563d891b56b1e9b01142ae11872/720p?translations=false&min_age=16
        if bool(re.search(r'<div class="message">Видео не найдено</div>', response.text)):
            msg = (f"Error! Video not found. Is kodik issue, not api-wrapper. Response[{response.status_code}] "
                   f"len={len(response.content)}")
            warnings.warn(msg,
                          category=RuntimeWarning,
                          stacklevel=0)
            return True
        return False

    @kodik_validator
    def parse(self, url: str, **kwargs) -> List[Video]:
        response = self.http.get(url)
        # kodik issue
        if self._is_not_founded_video(response):
            return []
        response = response.text

        payload = self._parse_api_payload(response)
        # extract netloc. Its maybe kodik, anivod or any providers
        netloc = self._get_netloc(url)
        url_api = self._create_url_api(netloc)
        headers = self._create_api_headers(url=url, netloc=netloc)

        response_api = self.http.post(url_api, data=payload, headers=headers)
        return self._extract(response_api.json()["links"])

    @kodik_validator
    async def a_parse(self, url: str, **kwargs) -> List[Video]:
        async with self.a_http as client:
            response = (await client.get(url))
            # kodik issue
            if self._is_not_founded_video(response):
                return []
            response = response.text

            payload = self._parse_api_payload(response)
            # extract netloc. Its maybe kodik, anivod or any providers
            netloc = self._get_netloc(url)
            url_api = self._create_url_api(netloc)
            headers = self._create_api_headers(url=url, netloc=netloc)

            response_api = (await client.post(url_api, data=payload, headers=headers).json())["links"]
            return self._extract(response_api)

    def _extract(self, response_api: Dict) -> List[Video]:
        # maybe not returns 720 key for VERY old anime titles
        # eg: early 'One peace!', 'Evangelion' series
        if response_api.get("720"):
            return [
                Video(type="m3u8", quality=360, url=self._decode(response_api["360"][0]["src"])),
                Video(type="m3u8", quality=480, url=self._decode(response_api["480"][0]["src"])),
                Video(
                    type="m3u8",
                    quality=720,
                    # this key return 480p link
                    url=self._decode(response_api["720"][0]["src"]).replace("/480.mp4:", "/720.mp4:"),
                ),
            ]
        elif response_api.get("480"):
            return [
                Video(type="m3u8", quality=360, url=self._decode(response_api["360"][0]["src"])),
                Video(type="m3u8", quality=480, url=self._decode(response_api["480"][0]["src"])),
            ]
        # OMG :O
        return [Video(type="m3u8", quality=360, url=self._decode(response_api["360"][0]["src"]))]
