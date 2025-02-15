import re
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Dict, List, Literal, TypeVar, Union, Callable
from urllib.parse import urlparse

from attrs import Factory, define

from anicli_api._http import BaseHTTPAsync, BaseHTTPSync

__all__ = ["ALL_QUALITIES", "Video", "url_validator", "BaseVideoExtractor", "ABCVideoExtractor"]

ALL_QUALITIES = (144, 240, 360, 480, 720, 1080)
T = TypeVar("T")


def url_validator(pattern: Union[str, re.Pattern]) -> Callable[..., Callable[..., List["Video"]]]:
    """check valid url for extractor"""
    if isinstance(pattern, str):
        pattern = re.compile(pattern)

    def decorator(func):
        @wraps(func)
        def wrapper(cls, url, **kwargs):
            if not pattern.match(url):
                msg = f"Uncorrected url for {cls.__class__.__name__} player"
                raise TypeError(msg)
            return func(cls, url, **kwargs)

        return wrapper

    return decorator


def drop_domain_levels(netloc: str, levels_to_keep: int = 2):
    """Drops domain levels higher than the specified number of levels to keep."""
    parts = netloc.split(".")
    if levels_to_keep <= 0:
        raise ValueError("levels_to_keep must be greater than 0")

    if len(parts) > levels_to_keep:
        result = ".".join(parts[-levels_to_keep:])
    else:
        result = netloc

    return result


@define(eq=False)
class Video:
    """Video container contains direct link and information like type, quality

    - type - video format type ["mp4", "m3u8", "mpd", "audio", "webm"]

    - quality - video quality [0, 144, 240, 360, 480, 720, 1080] 0 - audio

    - url - direct video link

    - headers - required UserAgent values for play or download this video. If not needed, default dict is empty
    """

    type: Literal["mp4", "m3u8", "mpd", "audio", "webm"]
    quality: Literal[0, 144, 240, 360, 480, 720, 1080]
    url: str
    headers: Dict[str, str] = Factory(dict)

    def dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "quality": self.quality,
            "url": self.url,
            "headers": self.headers,
        }

    def __str__(self):
        return f"[{self.quality}] {urlparse(self.url).netloc}...{self.type}"

    def __hash__(self):
        # aniboom hls links contains several third-level subdomain:
        # evie.yagami-light.com emily.yagami-light.com amelia.yagami-light.com calcium.yagami-light.com...
        # drop third-level or GE subdomains for correct compare
        netloc = drop_domain_levels(urlparse(self.url).netloc)
        return hash((self.type, self.quality, netloc))

    def __eq__(self, other):
        if isinstance(other, Video):
            return hash(self) == hash(other)
        msg = f"Video object required, not {type(other)}"
        raise TypeError(msg)


class ABCVideoExtractor(ABC):
    # attribute for `==` statement, for auto-detect needed extractor
    URL_RULE: Union[str, re.Pattern] = NotImplemented
    """regular expression for validate urls for `==` (__eq__) stmt"""
    # config if needed configurate HTTP classes for requests
    DEFAULT_HTTP_CONFIG: Dict[str, Any] = {}
    """minimal httpx.Client, httpx.AsyncClient configuration for correct work player provider"""

    def __init__(self, **httpx_kwargs):
        """
        :type httpx_kwargs: httpx.Client and httpx.AsyncClient configuration
        """
        default_kwargs = self.DEFAULT_HTTP_CONFIG.copy()
        default_kwargs.update(httpx_kwargs)
        self.http = BaseHTTPSync(**default_kwargs)
        self.a_http = BaseHTTPAsync(**default_kwargs)

    @abstractmethod
    def parse(self, url: str, **kwargs) -> List[Video]:
        pass

    @abstractmethod
    async def a_parse(self, url: str, **kwargs) -> List[Video]:
        pass

    @classmethod
    @abstractmethod
    def _compare_url(cls, url: str) -> bool: ...

    def __eq__(self, other: str):  # type: ignore
        """compare class instance with url string"""
        if not isinstance(other, str):
            msg = f"{other} should be str not {type(other).__name__}"
            raise TypeError(msg)
        return self._compare_url(other)


class BaseVideoExtractor(ABCVideoExtractor, ABC):
    @classmethod
    def _compare_url(cls, url: str) -> bool:
        """Provide __eq__ method

        :param url: link
        :return: True, if link valid else False
        """
        return (
            bool(cls.URL_RULE.search(url))
            if isinstance(cls.URL_RULE, re.Pattern)
            else bool(re.search(cls.URL_RULE, url))
        )
