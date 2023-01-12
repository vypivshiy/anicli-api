"""
Decoders class for video hostings

Decoder structure:

- class DecoderName(BaseDecoder) - base decoder structure.

- URL_RULE - link validation regex.

- def parse - List[MetaVideo]: synchronous video parser class method.

- async def async_parse -> List[MetaVideo]: asynchronous video parser class method.


Video Dataclass with reference values

MetaVideo

- type file type (m3u8, mpd, mp4...)

- quality video quality, int (144,240,360,480,720,1080)

- url video link

- extra_headers - if the video stream does not work without them (like aniboom, sibnet) or set default value.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Union
from urllib.parse import urlparse

from anicli_api._http import BaseHTTPAsync, BaseHTTPSync

ALL_QUALITIES = (144, 240, 360, 480, 720, 1080)


@dataclass
class MetaVideo:
    """MetaVideo class contains direct link and information like type, quality

    - type - video format type (mp4, m3u8 or mpd)

    - quality - video quality [144, 240, 360, 480, 720, 1080]

    - url - direct video link

    - extra_headers - required UserAgent values for play or download this video. If not needed, default dict is empty
    """

    type: Literal["mp4", "m3u8", "mpd", "audio", "webm"]
    quality: Literal[0, 144, 240, 360, 480, 720, 1080]
    url: str
    extra_headers: Optional[Dict] = field(default_factory=dict)

    def dict(self) -> Dict[str, Any]:
        return self.__dict__

    def __str__(self):
        return f"{self.type} {self.quality} {urlparse(self.url).netloc}"

    def __hash__(self):
        return hash((self.type, self.quality, urlparse(self.url).netloc))

    def __eq__(self, other):
        if isinstance(other, MetaVideo):
            return hash(self) == hash(other)
        raise TypeError(f"MetaVideo object required, not {type(other)}")


class ABCDecoder(ABC):
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


class BaseDecoder(ABCDecoder):
    """Abstract decoder class

    - URL_RULE - regular expression to validate link

    - cls.parse - get videos synchronously

    - cls.async_parse - get videos asynchronously
    """

    URL_RULE: Union[str, re.Pattern]

    @classmethod
    def _validate_url(cls, url: str):
        if url != cls():
            raise TypeError(f"Incorrect decoder. {url} if not {cls.__class__.__name__}")

    @classmethod
    @abstractmethod
    def parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        """get video synchronously

        :param url: video url
        :param kwargs: optional params for httpx.Client instance
        :return: List of MetaVideo dataclasses
        """
        ...

    @classmethod
    @abstractmethod
    async def async_parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        """get video asynchronously

        :param url: video url
        :param kwargs: optional params for httpx.AsyncClient instance
        :return: List of MetaVideo dataclasses
        """
        ...

    @classmethod
    def _compare_url(cls, url: str) -> bool:
        """
        :param url: link
        :return: True, if link valid else False
        """
        return (
            bool(cls.URL_RULE.search(url))
            if isinstance(cls.URL_RULE, re.Pattern)
            else bool(re.search(cls.URL_RULE, url))
        )
