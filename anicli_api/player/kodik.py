import codecs
import re
import warnings
from base64 import b64decode
from typing import Any, Dict, List
from urllib.parse import urlsplit

from httpx import Response

from .base import BaseVideoExtractor, Video, url_validator
from .parsers.kodik_parser import MainKodikMin
from .parsers.kodik_parser import MainKodikAPIPath

__all__ = ["Kodik"]
_URL_EQ = re.compile(r"https://(www\.)?\w{5,32}\.\w{2,6}/(?:serial?|season|video|film)/\d+/\w+/\d{3,4}p")
kodik_validator = url_validator(_URL_EQ)


class Kodik(BaseVideoExtractor):
    URL_RULE = _URL_EQ
    # cached API path to avoid extra requests
    _CACHED_API_PATH = None
    DEFAULT_HTTP_CONFIG = {"http2": True}
    API_CONSTS_PAYLOAD = {"bad_user": False, "info": {}, "cdn_is_working": True}

    @kodik_validator
    def parse(self, url: str, **kwargs) -> List[Video]:
        response = self.http.get(url)
        if self._is_unhandled_error_response(response):
            return []
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

    @kodik_validator
    async def a_parse(self, url: str, **kwargs) -> List[Video]:
        async with self.a_http as client:
            response = await client.get(url)
            if self._is_unhandled_error_response(response):
                return []
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

    @staticmethod
    def _decrypt_url(encoded_str: str) -> str:
        """Decrypt string with custom ROT cipher"""
        string = ""
        for char in encoded_str:
            if char.isupper():
                string += chr((ord(char) - 65 + 18) % 26 + 65)
            elif char.islower():
                string += chr((ord(char) - 97 + 18) % 26 + 97)
            else:
                string += char
        return string

    def _decode(self, url_encoded: str) -> str:
        """decode video url (custom ROT cipher + base64)"""
        # 7.03.25 kodik remove encoding urls
        if url_encoded.endswith(".m3u8"):
            return url_encoded if url_encoded.startswith("https") else f"https:{url_encoded}"

        base64_url = self._decrypt_url(url_encoded)
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
            msg = f"Error! Video not found with {response.status_code} status code. Is kodik issue, not anicli-api."
            warnings.warn(msg, category=RuntimeWarning, stacklevel=1)
            return True
        return False

    @staticmethod
    def _is_unhandled_error_response(response: Response) -> bool:
        # ULTRA rare kodik backend bug
        # Spotted in 'Cyberpunk: Edgerunners' ep5 Anilibria dub
        # https://kodik.info/seria/1051016/af405efc5e061f5ac344d4811de3bc16/720p
        if response.status_code == 500 and "An unhandled lowlevel error occurred" in response.text:
            msg = (
                f"Error! Kodik returns 'An unhandled lowlevel error occurred' with {response.status_code} status code."
                f" Is kodik issue, not anicli-api."
            )
            warnings.warn(msg, category=RuntimeWarning)
            return True
        return False

    def _update_api_path(self, response_player) -> None:
        path = MainKodikAPIPath(response_player.text).parse()["api_path"]
        self._CACHED_API_PATH = b64decode(path).decode()

    def _extract_api_payload(self, response):
        response = response.text
        page = MainKodikMin(response).parse()
        payload = page["api_payload"]
        payload.update(self.API_CONSTS_PAYLOAD)  # type: ignore
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
