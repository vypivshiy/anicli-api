import re
from base64 import b64decode
from typing import Dict, List
from urllib.parse import urlsplit

from anicli_api.player.base import BaseVideoExtractor, Video, url_validator

__all__ = ["Kodik"]
_URL_EQ = re.compile(r"https://(www\.)?\w{5,32}\.\w{2,6}/(?:seria|video|film)/\d+/\w+/\d{3,4}p")
kodik_validator = url_validator(_URL_EQ)


class Kodik(BaseVideoExtractor):
    URL_RULE = _URL_EQ

    @staticmethod
    def _decode(url_encoded: str) -> str:
        # After 30.03.23 `kodik` provider change reversed base64 string to Caesar cipher + base64.
        # This code simular original js player code for decode url.
        #
        # this code replaces all alphabetical characters in a base64 encoded string
        # with characters that are shifted 13 places in the alphabetical order,
        # wrapping around to the beginning or end of the alphabet as necessary.
        # This is a basic form of a type of substitution cipher.

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
        # parse payload for next send request to kodik API
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

    @kodik_validator
    def parse(self, url: str, **kwargs) -> List[Video]:
        response = self.http.get(url).text
        payload = self._parse_api_payload(response)
        # convert to API url. its maybe kodik, anivod or any kodik provider entrypoints
        url_api = f"https://{urlsplit(url).netloc}/gvi"
        referer = url_api.replace("/gvi", "")

        response_api = self.http.post(
            url_api,
            data=payload,
            headers={
                "origin": "https://kodik.info",
                "referer": referer,
                "accept": "application/json, text/javascript, */*; q=0.01",
            },
        ).json()["links"]
        return self._extract(response_api)

    @kodik_validator
    async def a_parse(self, url: str, **kwargs) -> List[Video]:
        async with self.a_http as client:
            response = (await client.get(url)).text
            payload = self._parse_api_payload(response)
            url_api = f"https://{urlsplit(url).netloc}/gvi"
            # convert to API url. its maybe kodik, anivod or any kodik provider entrypoints
            referer = url_api.replace("/gvi", "")

            response_api = (
                await client.post(
                    url_api,
                    data=payload,
                    headers={
                        "origin": "https://kodik.info",
                        "referer": referer,
                        "accept": "application/json, text/javascript, */*; q=0.01",
                    },
                ).json()
            )["links"]
            return self._extract(response_api)

    def _extract(self, response_api: Dict) -> List[Video]:
        # maybe not returns 720 key for VERY old anime titles
        # early 'One peace!' series or 'Evangelion' series, for example
        if response_api.get("720"):
            return [
                Video(type="m3u8",
                      quality=360,
                      url=self._decode(response_api["360"][0]["src"])
                      ),
                Video(type="m3u8",
                      quality=480,
                      url=self._decode(response_api["480"][0]["src"])
                      ),
                Video(type="m3u8",
                      quality=720,
                      # this key return 480p link
                      url=self._decode(
                          response_api["720"][0]["src"]
                      ).replace('/480.mp4:', '/720.mp4:')
                      ),
            ]
        elif response_api.get("480"):
            return [
                Video(type="m3u8",
                      quality=360,
                      url=self._decode(response_api["360"][0]["src"])
                      ),
                Video(type="m3u8",
                      quality=480,
                      url=self._decode(response_api["480"][0]["src"])
                      ),
            ]
        # OMG :O
        return [
            Video(type="m3u8",
                  quality=360,
                  url=self._decode(response_api["360"][0]["src"])
                  )
        ]
