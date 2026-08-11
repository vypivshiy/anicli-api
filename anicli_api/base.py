from __future__ import annotations

import warnings
from abc import abstractmethod
from typing import TYPE_CHECKING, Optional

from urllib.parse import urlsplit
from anicli_api.typing import Sequence, TypedDict

from attrs import define, field

from anicli_api._http import (  # noqa: F401
    HTTPAsync,
    HTTPSync,
)
from anicli_api.player import ALL_DECODERS
from anicli_api.player import video_playlist_from_vk_id as cdnvideohub_playlist_from_vkid
from anicli_api.player import a_video_playlist_from_vk_id as async_cdnvideohub_playlist_from_vkid

if TYPE_CHECKING:
    from httpx import AsyncClient, Client

    from anicli_api.player.base import Video


class T_KW_HTTPS(TypedDict):
    http: "Client"
    http_async: "AsyncClient"


class BaseExtractor:
    BASE_URL: str = NotImplemented
    """anime source main page"""

    @property
    def source_name(self) -> str:
        """return source name (by url netloc)"""
        return urlsplit(self.BASE_URL).netloc

    def __init__(self, http_client: "Client" = HTTPSync(), http_async_client: "AsyncClient" = HTTPAsync()):
        self._http = http_client
        self._http_async = http_async_client

    @property
    def http(self) -> "Client":
        return self._http

    @property
    def http_async(self) -> "AsyncClient":
        return self._http_async

    @http.setter
    def http(self, http_client: "Client"):
        self._http = http_client

    @http_async.setter
    def http_async(self, http_async_client: "AsyncClient"):
        self._http_async = http_async_client

    @property
    def _kwargs_http(self) -> T_KW_HTTPS:
        """shortcut for pass http arguments in kwargs style"""
        return {"http": self.http, "http_async": self.http_async}

    @abstractmethod
    def search(self, query: str) -> Sequence["BaseSearch"]:
        """search anime by string query

        :param query: string search query
        """
        pass

    @abstractmethod
    async def a_search(self, query: str) -> Sequence["BaseSearch"]:
        """search anime by string query in async mode

        :param query: string search query
        """
        pass

    @abstractmethod
    def ongoing(self) -> Sequence["BaseOngoing"]:
        """get ongoings"""
        pass

    @abstractmethod
    async def a_ongoing(self) -> Sequence["BaseOngoing"]:
        """get ongoings in async mode"""
        pass


@define(kw_only=True)
class HttpMixin:
    """this dataclass provide pre-configured http clients"""

    _http: "Client" = field(default=HTTPSync(), repr=False, kw_only=True, hash=False, alias="http")
    """pre-configured sync httpx Client"""
    _http_async: "AsyncClient" = field(default=HTTPAsync(), repr=False, kw_only=True, hash=False, alias="http_async")
    """pre-configured async httpx Client"""

    @property
    def http(self):
        return self._http

    @http.setter
    def http(self, http_client: "Client"):
        self._http = http_client

    @property
    def http_async(self):
        return self._http_async

    @http_async.setter
    def http_async(self, http_async_client: "AsyncClient"):
        self._http_async = http_async_client

    @property
    def _kwargs_http(self) -> T_KW_HTTPS:
        """shortcut for pass http arguments in kwargs style"""
        return {"http": self.http, "http_async": self.http_async}


@define(kw_only=True)
class BaseSearch(HttpMixin):
    title: str
    """Search item name"""
    thumbnail: str
    """Search item image"""
    url: str
    """Search item url to anime page"""

    @abstractmethod
    def get_anime(self) -> "BaseAnime":
        """get anime"""
        pass

    @abstractmethod
    async def a_get_anime(self) -> "BaseAnime":
        """get anime in async mode"""
        pass

    def __str__(self):
        return self.title

    def __hash__(self):
        return hash(tuple((self.title, self.thumbnail, self.url)))


@define(kw_only=True)
class BaseOngoing(HttpMixin):
    title: str
    """Ongoing item name"""
    thumbnail: str
    """Ongoing item image"""
    url: str
    """Ongoing url to main page"""

    @abstractmethod
    def get_anime(self) -> "BaseAnime":
        """get anime"""
        pass

    @abstractmethod
    async def a_get_anime(self) -> "BaseAnime":
        """get anime in async mode"""
        pass

    def __str__(self):
        return self.title

    def __hash__(self):
        return hash(tuple((self.title, self.thumbnail, self.url)))


@define(kw_only=True)
class BaseAnime(HttpMixin):
    title: str
    """anime name"""
    thumbnail: str
    """anime image"""
    description: str
    """anime description"""

    @abstractmethod
    def get_episodes(self) -> Sequence["BaseEpisode"]:
        """get episodes"""
        pass

    @abstractmethod
    async def a_get_episodes(self) -> Sequence["BaseEpisode"]:
        """get episodes in async mode"""
        pass

    def __str__(self):
        if len(self.title + self.description) > 80:
            return f"{self.title} {self.description[: (80 - len(self.title) - 3)]}..."
        return f"{self.title} {self.description}"

    def __hash__(self):
        return hash(tuple((self.title, self.thumbnail, self.description)))


@define(kw_only=True)
class BaseEpisode(HttpMixin):
    title: str
    """episode name. If api or source not provided, default naming like:

    - Episode {num}
    - Serie {num}
    - Эпизод {num}
    - Серия {num}"""
    ordinal: int

    # backport old field name
    @property
    def num(self) -> str:
        return str(self.ordinal)

    """episode number. Stars from 1"""

    @abstractmethod
    def get_sources(self) -> Sequence["BaseSource"]:
        """get raw source player information"""
        pass

    @abstractmethod
    async def a_get_sources(self) -> Sequence["BaseSource"]:
        """get raw source player information in async mode"""
        pass

    def __str__(self):
        return f"{self.title} {self.num}"

    def __hash__(self):
        return hash(tuple((self.title, self.num)))


@define(kw_only=True)
class BaseSource(HttpMixin):
    title: str
    """Source name. If source/api provide multiple dubbers - named by dubber name + source (player).

    If single dubber provide - named by source netloc
    """
    url: str
    """player (source) url"""

    cdn_videohub_vk_id: Optional[str] = None
    """special field for cdnvideohub source"""

    @property
    def _all_video_extractors(self):
        """helper property for helps dynamic match decoder parser by player url"""
        return ALL_DECODERS

    @property
    def _cdn_videohub_extractor(self):
        return cdnvideohub_playlist_from_vkid

    @property
    def _async_cdn_videohub_extractor(self):
        return async_cdnvideohub_playlist_from_vkid

    def get_videos(
        self,
        *,
        headers: dict | None = None,
        cookies: dict | None = None,
        timeout: float | None = None,
    ) -> Sequence["Video"]:
        """get direct video information for direct play

        Per-call ``headers`` / ``cookies`` / ``timeout`` apply to every HTTP
        request made inside the chosen player extractor for this call only.
        They are forwarded as per-call request kwargs to ``client.get``/``post``
        and DO NOT mutate the source's underlying ``httpx.Client``.

        For per-tenant isolation (separate proxies, IP regions) instantiate a
        separate ``httpx.Client`` per tenant and assign via ``source.http``.

        Returns:
            extracted video list
        """
        if self.cdn_videohub_vk_id:
            return cdnvideohub_playlist_from_vkid(
                self.http,
                self.cdn_videohub_vk_id,
                headers=headers,
                cookies=cookies,
                timeout=timeout,
            )

        for extractor in self._all_video_extractors:
            if self.url == extractor():
                return extractor(http=self.http, a_http=self.http_async).parse(
                    self.url,
                    headers=headers,
                    cookies=cookies,
                    timeout=timeout,
                )
        warnings.warn(f"Failed extractor videos from {self.url}")
        return []

    async def a_get_videos(
        self,
        *,
        headers: dict | None = None,
        cookies: dict | None = None,
        timeout: float | None = None,
    ) -> Sequence["Video"]:
        """get direct video information for direct play in async mode

        Per-call ``headers`` / ``cookies`` / ``timeout`` apply to every HTTP
        request made inside the chosen player extractor for this call only.
        They are forwarded as per-call request kwargs to ``client.get``/``post``
        and DO NOT mutate the source's underlying ``httpx.AsyncClient``.

        For per-tenant isolation (separate proxies, IP regions) instantiate a
        separate ``httpx.AsyncClient`` per tenant and assign via
        ``source.http_async``.

        Returns:
            extracted video list
        """
        if self.cdn_videohub_vk_id:
            return await async_cdnvideohub_playlist_from_vkid(
                self.http_async,
                self.cdn_videohub_vk_id,
                headers=headers,
                cookies=cookies,
                timeout=timeout,
            )

        for extractor in self._all_video_extractors:
            if self.url == extractor():
                return await extractor(http=self.http, a_http=self.http_async).a_parse(
                    self.url,
                    headers=headers,
                    cookies=cookies,
                    timeout=timeout,
                )
        warnings.warn(f"Failed extractor videos from {self.url}")
        return []

    def __str__(self):
        return f"{urlsplit(self.url).netloc} ({self.title})"

    def __hash__(self):
        return hash(tuple((self.title, self.url)))

