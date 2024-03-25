import codecs
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
    # cached API path to avoid extra requests
    _CACHED_API_PATH = None

    @staticmethod
    def _decode(url_encoded: str) -> str:
        # After 30.03.23 this provider change reversed base64 string to ROT13 + base64
        # (aka Caesar cipher shifted 13 places)
        # original js code signature:
        # function (e) {
        #   var t;
        #   e.src = (
        #     t = e.src,
        #     atob(
        #       t.replace(
        #         /[a-zA-Z]/g,
        #         function (e) {
        #           return String.fromCharCode((e <= 'Z' ? 90 : 122) >= (e = e.charCodeAt(0) + 13) ? e : e - 26)
        #         }
        #       )
        #     )
        #   )
        # }

        # https://stackoverflow.com/a/3270252
        base64_url = codecs.decode(url_encoded, "rot_13")
        if not base64_url.endswith("=="):
            base64_url += "=="
        decoded_url = b64decode(base64_url).decode()
        return decoded_url if decoded_url.startswith("https") else f"https:{b64decode(base64_url).decode()}"

    @staticmethod
    def _parse_api_payload(response: str) -> Dict:
        return {
            "domain": re.search(r'var domain = ["\'](.*?)["\'];', response)[1],  # type: ignore[index]
            "d_sign": re.search(r'var d_sign = ["\'](.*?)["\'];', response)[1],  # type: ignore[index]
            "pd": re.search(r'var pd = ["\'](.*?)["\'];', response)[1],  # type: ignore[index]
            "ref": re.search(r'var ref = ["\'](.*?)["\'];', response)[1],  # type: ignore[index]
            "type": re.search(r'videoInfo\.type = ["\'](.*?)["\'];', response)[1],  # type: ignore[index]
            "hash": re.search(r'videoInfo\.hash = ["\'](.*?)["\'];', response)[1],  # type: ignore[index]
            "id": re.search(r'videoInfo\.id = ["\'](.*?)["\'];', response)[1],  # type: ignore[index]
            "bad_user": True,
            "info": {},
        }

    @staticmethod
    def _get_netloc(url: str) -> str:
        # Its maybe kodik, anivod or other providers
        return urlsplit(url).netloc

    @staticmethod
    def _create_url_api(netloc: str, path: str = "tru") -> str:
        # after 22.01.24 this provider add dynamically change API path
        return f"https://{netloc}/{path}"

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

    @staticmethod
    def _get_min_js_player_url(response: str, netloc: str) -> str:
        # get js player file for extract valid kodik api path
        min_player_path = re.search(  # type: ignore
            r'<script\s*type="text/javascript"\s*src="(/assets/js/app\.player_single.*?)">', response
        )[1]
        return f"https://{netloc}{min_player_path}"

    @staticmethod
    def _extract_api_path(player_response: str) -> str:
        # extract base64 encoded path from js code
        # original js api path signature:
        # ... $.ajax({type:"POST",url:atob("L2Z0b3I="),cache:! ...
        # ... $.ajax({type: 'POST', url:atob('L3RyaQ=='),cache: !1 ...
        path = re.search(
            r"""
        \$\.ajax\([^>]+,url:\s*atob\(
        ["']
        ([\w=]+)                        # BASE64 encoded API path
        ["']\)
        """,
            player_response,
            re.VERBOSE,
        )[1]
        if not path.endswith("=="):
            path += "=="

        decoded_path = b64decode(path).decode()
        return decoded_path[1:] if decoded_path.startswith("/") else decoded_path

    def _first_update_api_path(self, response: str, netloc: str) -> None:
        if not self._CACHED_API_PATH:
            url_player_js = self._get_min_js_player_url(response, netloc)
            response_player = self.http.get(url_player_js)
            api_path = self._extract_api_path(response_player.text)
            self._CACHED_API_PATH = api_path

    def _update_api_path(self, netloc, response):
        url_player_js = self._get_min_js_player_url(response, netloc)
        response_player = self.http.get(url_player_js)
        self._CACHED_API_PATH = self._extract_api_path(response_player.text)

    def _first_extract_api_path(self, netloc: str, response: str) -> None:
        if not self._CACHED_API_PATH:
            self._update_api_path(netloc, response)

    @kodik_validator
    def parse(self, url: str, **kwargs) -> List[Video]:
        response = self.http.get(url)
        if self._is_not_founded_video(response):
            return []
        response = response.text

        payload = self._parse_api_payload(response)
        netloc = self._get_netloc(url)

        self._first_extract_api_path(netloc, response)

        url_api = self._create_url_api(netloc, path=self._CACHED_API_PATH)
        headers = self._create_api_headers(url=url, netloc=netloc)

        response_api = self.http.post(url_api, data=payload, headers=headers)

        # expired API entry point, update
        if not response_api.is_success:
            self._update_api_path(netloc, response)
            response_api = self.http.post(url_api, data=payload, headers=headers)

        return self._extract(response_api.json()["links"])

    async def _a_first_extract_api_path(self, client, netloc: str, response: str) -> None:
        if not self._CACHED_API_PATH:
            await self._a_update_api_path(client, netloc, response)

    @kodik_validator
    async def a_parse(self, url: str, **kwargs) -> List[Video]:
        async with self.a_http as client:
            response = await client.get(url)
            if self._is_not_founded_video(response):
                return []
            response = response.text
            payload = self._parse_api_payload(response)
            netloc = self._get_netloc(url)

            await self._a_first_extract_api_path(client, netloc, response)

            url_api = self._create_url_api(netloc, path=self._CACHED_API_PATH)
            headers = self._create_api_headers(url=url, netloc=netloc)
            response_api = await client.post(url_api, data=payload, headers=headers)

            # expired API entry point, update
            if not response_api.is_success:
                await self._a_update_api_path(client, netloc, response)
                response_api = await client.post(url_api, data=payload, headers=headers)

            return self._extract(response_api.json()["links"])

    async def _a_update_api_path(self, client, netloc, response):
        url_player_js = self._get_min_js_player_url(response, netloc)
        response_player = await client.get(url_player_js)
        self._CACHED_API_PATH = self._extract_api_path(response_player.text)

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
