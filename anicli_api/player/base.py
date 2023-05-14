import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional, Union
from urllib.parse import urlparse

from anicli_api._http import BaseHTTPAsync, BaseHTTPSync

ALL_QUALITIES = (144, 240, 360, 480, 720, 1080)


def url_validator(pattern: str | re.Pattern):
    if isinstance(pattern, str):
        pattern = re.compile(pattern)

    def decorator(func):
        def wrapper(_, url, **kwargs):
            if not pattern.match(url):
                raise TypeError(f"Uncorrected url for {_.__class__.__name__} player")
            return func(_, url, **kwargs)

        return wrapper

    return decorator


class Video:
    """MetaVideo class contains direct link and information like type, quality

    - type - video format type (mp4, m3u8 or mpd)

    - quality - video quality [144, 240, 360, 480, 720, 1080]

    - url - direct video link

    - extra_headers - required UserAgent values for play or download this video. If not needed, default dict is empty
    """

    def __init__(
        self,
        type: Literal["mp4", "m3u8", "mpd", "audio", "webm"],
        quality: Literal[0, 144, 240, 360, 480, 720, 1080],
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.type = type
        self.quality = quality
        self.url = url
        self.headers = headers or {}

    def dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "quality": self.quality,
            "url": self.url,
            "headers": self.headers,
        }

    def __str__(self):
        return f"{self.type} {self.quality} {urlparse(self.url).netloc}"

    def __hash__(self):
        return hash((self.type, self.quality, urlparse(self.url).netloc))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, Video):
            return hash(self) == hash(other)
        raise TypeError(f"MetaVideo object required, not {type(other)}")


class ABCVideoExtractor(ABC):
    URL_RULE: Union[str, re.Pattern] = NotImplemented
    DEFAULT_HTTP_CONFIG: Dict[str, Any] = {}

    def __init__(self, **httpx_kwargs):
        self.http = BaseHTTPSync(**self.DEFAULT_HTTP_CONFIG, **httpx_kwargs)
        self.a_http = BaseHTTPAsync(**self.DEFAULT_HTTP_CONFIG, **httpx_kwargs)

    @abstractmethod
    def parse(self, url: str, **kwargs) -> List[Video]:
        pass

    @abstractmethod
    async def a_parse(self, url: str, **kwargs) -> List[Video]:
        pass

    @classmethod
    @abstractmethod
    def _compare_url(cls, url: str) -> bool:
        ...

    def __eq__(self, other: str):  # type: ignore
        """compare class instance with url string"""
        if not isinstance(other, str):
            raise TypeError(f"{other} should be str not {type(other).__name__}")
        return self._compare_url(other)


class BaseVideoExtractor(ABCVideoExtractor, ABC):
    @classmethod
    def _validate_url(cls, url: str):
        if url != cls():
            raise TypeError(f"Incorrect decoder. {url} if not {cls.__class__.__name__}")

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
