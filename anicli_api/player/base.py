from __future__ import annotations

import re
from abc import ABC, abstractmethod
from functools import wraps
from typing import TYPE_CHECKING, Any, Literal, TypeVar, Union, Callable
from urllib.parse import urlparse

from attrs import Factory, define

from anicli_api._http import BaseHTTPAsync, BaseHTTPSync

if TYPE_CHECKING:
    from httpx import AsyncClient, Client

__all__ = ["ALL_QUALITIES", "Video", "url_validator", "BaseVideoExtractor", "ABCVideoExtractor"]

ALL_QUALITIES = (144, 240, 360, 480, 720, 1080)
T = TypeVar("T")


def url_validator(pattern: Union[str, re.Pattern]) -> Callable[..., Callable[..., list["Video"]]]:
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

    - quality - video quality [0, 144, 240, 360, 480, 720, 1080, 2160] 0 - audio

    - url - direct video link

    - headers - required UserAgent values for play or download this video. If not needed, default dict is empty
    """

    type: Literal["mp4", "m3u8", "mpd", "audio", "webm"]
    quality: int  # real signature: Literal[0, 144, 240, 360, 480, 720, 1080, 2160]
    url: str
    headers: dict[str, str] = Factory(dict)

    def dict(self) -> dict[str, Any]:
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
    # config for new-client construction only (http2, transport, proxies).
    # NEVER used to mutate externally-passed http/a_http clients.
    DEFAULT_CLIENT_CONFIG: dict[str, Any] = {}
    """httpx.Client/AsyncClient configuration used ONLY when constructing new
    clients (when http/a_http not passed). Never mutates externally-passed clients."""

    # per-call request defaults merged into every client.get/post call.
    DEFAULT_REQUEST_CONFIG: dict[str, Any] = {}
    """Per-call request defaults (headers, cookies). Merged into every request
    this extractor makes; can be overridden per-call via parse/a_parse kwargs."""

    def __init__(self, http: "Client | None" = None, a_http: "AsyncClient | None" = None):
        """
        :param http: pre-configured httpx.Client. Stored as-is, NEVER mutated.
        :param a_http: pre-configured httpx.AsyncClient. Stored as-is, NEVER mutated.

        Note: per-instance request defaults come from ``DEFAULT_REQUEST_CONFIG``
        and are merged per-call via ``_merge_request_kwargs``. The previous
        behavior of mutating ``http.headers`` / ``a_http.headers`` at
        construction was racy when a client was shared across concurrent
        asyncio tasks and has been removed.
        """
        self._owns_http = http is None
        self._owns_a_http = a_http is None
        self._http = http if http is not None else BaseHTTPSync(**self.DEFAULT_CLIENT_CONFIG)
        self._a_http = a_http if a_http is not None else BaseHTTPAsync(**self.DEFAULT_CLIENT_CONFIG)

    @property
    def http(self) -> "Client":
        return self._http

    @http.setter
    def http(self, client: "Client") -> None:
        self._http = client
        self._owns_http = False

    @property
    def a_http(self) -> "AsyncClient":
        return self._a_http

    @a_http.setter
    def a_http(self, client: "AsyncClient") -> None:
        self._a_http = client
        self._owns_a_http = False

    def close(self) -> None:
        """Close the internally-created sync client, if any."""
        if self._owns_http and not self.http.is_closed:
            self.http.close()

    async def aclose(self) -> None:
        """Close clients created by this extractor without touching borrowed clients."""
        self.close()
        if self._owns_a_http and not self.a_http.is_closed:
            await self.a_http.aclose()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.aclose()

    def _merge_request_kwargs(
        self,
        headers: dict[str, str] | None,
        cookies: dict[str, str] | None,
        timeout: float | None,
    ) -> dict[str, Any]:
        """Merge per-call kwargs over DEFAULT_REQUEST_CONFIG.

        Caller-supplied ``headers`` are merged ON TOP of (not replacing)
        ``DEFAULT_REQUEST_CONFIG['headers']`` so default referer/UA etc are
        preserved unless explicitly overridden.

        Returns a plain dict ready to splat into ``client.get(..., **kwargs)``.
        """
        cfg = self.DEFAULT_REQUEST_CONFIG.copy()
        default_headers = cfg.get("headers")
        if default_headers is not None:
            cfg["headers"] = dict(default_headers)
        default_cookies = cfg.get("cookies")
        if default_cookies is not None:
            cfg["cookies"] = dict(default_cookies)
        if headers is not None:
            cfg["headers"] = {**cfg.get("headers", {}), **headers}
        if cookies is not None:
            cfg["cookies"] = {**cfg.get("cookies", {}), **cookies}
        if timeout is not None:
            cfg["timeout"] = timeout
        return cfg

    @abstractmethod
    def parse(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> list[Video]:
        pass

    @abstractmethod
    async def a_parse(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> list[Video]:
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
