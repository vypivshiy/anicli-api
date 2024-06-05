import asyncio
import codecs
import json
import re
import warnings
from base64 import b64decode
from typing import Dict, List, Any
from urllib.parse import urlsplit

from httpx import Response

from anicli_api.player.base import BaseVideoExtractor, Video, url_validator
from parsers.kodik_parser import KodikPage, KodikApiPath

__all__ = ["Kodik"]
_URL_EQ = re.compile(r"https://(www\.)?\w{5,32}\.\w{2,6}/(?:seria|video|film)/\d+/\w+/\d{3,4}p")
kodik_validator = url_validator(_URL_EQ)


class Kodik(BaseVideoExtractor):
    URL_RULE = _URL_EQ
    # cached API path to avoid extra requests
    _CACHED_API_PATH = None
    DEFAULT_HTTP_CONFIG = {"http2": True}
    API_CONSTS_PAYLOAD = {
        "bad_user": False,
        "info": {},
        "cdn_is_working": True
    }

    @staticmethod
    def _decode(url_encoded: str) -> str:
        """decode video url (ROT13 + base64)"""

        # https://stackoverflow.com/a/3270252
        base64_url = codecs.decode(url_encoded, "rot_13")
        if not base64_url.endswith("=="):
            base64_url += "=="
        decoded_url = b64decode(base64_url).decode()
        return decoded_url if decoded_url.startswith("https") else f"https:{b64decode(base64_url).decode()}"

    @staticmethod
    def _get_netloc(url: str) -> str:
        # Its maybe kodik, anivod or other providers
        return urlsplit(url).netloc

    @staticmethod
    def _create_url_api(netloc: str, path: str = "ftor") -> str:
        # after 22.01.24 this provider adds a dynamical change API path
        return f"https://{netloc}{path}"

    @staticmethod
    def _create_api_headers(*, url: str, netloc: str) -> Dict[str, str]:
        return {
            "origin": f"https://{netloc}",
            "referer": url,
            "accept": "application/json, text/javascript, */*; q=0.01",
        }

    @staticmethod
    def _is_not_founded_video(response: Response) -> bool:
        """return true is video is deleted"""
        # eg:
        # https://kodik.info/seria/310427/09985563d891b56b1e9b01142ae11872/720p
        # Вайолет Эвергарден: День, когда ты поймешь, что я люблю тебя, обязательно наступит
        # Violet Evergarden: Kitto "Ai" wo Shiru Hi ga Kuru no Darou

        if bool(re.search(r'<div class="message">Видео не найдено</div>', response.text)):
            msg = (
                f"Error! Video not found. Is kodik issue, not anicli-api. Response[{response.status_code}] "
                f"len={len(response.content)}"
            )
            warnings.warn(msg, category=RuntimeWarning, stacklevel=1)
            return True
        return False

    @kodik_validator
    def parse(self, url: str, **kwargs) -> List[Video]:
        response = self.http.get(url)
        if self._is_not_founded_video(response):
            return []
        page, payload = self._extract_api_payload(response)
        netloc = self._get_netloc(url)

        if not self._CACHED_API_PATH:
            url_js_player = f"https://{netloc}{page['player_js_path']}"
            response_player = self.http.get(url_js_player)
            self._update_api_path(response_player)

        url_api = self._create_url_api(netloc, path=self._CACHED_API_PATH)
        headers = self._create_api_headers(url=url, netloc=netloc)
        response_api = self.http.post(url_api, data=payload, headers=headers)

        # expired API entry point, update
        if not response_api.is_success:
            url_js_player = f"https://{netloc}{page['player_js_path']}"
            response_player = self.http.get(url_js_player)
            self._update_api_path(response_player)

            url_api = self._create_url_api(netloc, path=self._CACHED_API_PATH)
            response_api = self.http.post(url_api, data=payload, headers=headers)

        return self._extract(response_api.json()["links"])

    def _update_api_path(self, response_player) -> None:
        path = KodikApiPath(response_player.text).parse()['path']
        self._CACHED_API_PATH = b64decode(path).decode()

    @kodik_validator
    async def a_parse(self, url: str, **kwargs) -> List[Video]:
        async with self.a_http as client:
            response = await client.get(url)
            if self._is_not_founded_video(response):
                return []
            page, payload = self._extract_api_payload(response)
            netloc = self._get_netloc(url)

            if not self._CACHED_API_PATH:
                url_js_player = f"https://{netloc}{page['player_js_path']}"
                response_player = await client.get(url_js_player)
                self._update_api_path(response_player)

            url_api = self._create_url_api(netloc, path=self._CACHED_API_PATH)
            headers = self._create_api_headers(url=url, netloc=netloc)
            response_api = await client.post(url_api, data=payload, headers=headers)

            # expired API entry point, update
            if not response_api.is_success:
                url_js_player = f"https://{netloc}{page['player_js_path']}"
                response_player = await client.get(url_js_player)
                self._update_api_path(response_player)

                url_api = self._create_url_api(netloc, path=self._CACHED_API_PATH)
                response_api = await client.post(url_api, data=payload, headers=headers)

            return self._extract(response_api.json()["links"])

    def _extract_api_payload(self, response):
        response = response.text
        page = KodikPage(response).parse()
        payload: Dict[str, Any] = page['api_payload']
        payload.update(self.API_CONSTS_PAYLOAD)
        return page, payload

    def _extract(self, response_api: Dict) -> List[Video]:
        # maybe not exists '720' key for VERY old anime titles
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

