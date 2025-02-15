import warnings
from abc import abstractmethod
from typing import TYPE_CHECKING, Dict, List, Union
from urllib.parse import urlsplit

from attrs import define, field

from anicli_api._http import (  # noqa: F401
    DDOSServerDetectError,
    HTTPAsync,
    HTTPRetryConnectAsyncTransport,
    HTTPRetryConnectSyncTransport,
    HTTPSync,
)
from anicli_api.player import ALL_DECODERS

if TYPE_CHECKING:
    from httpx import AsyncClient, Client

    from anicli_api.player.base import Video


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
    def _kwargs_http(self) -> Dict[str, Union["Client", "AsyncClient"]]:
        """shortcut for pass http arguments in kwargs style"""
        return {"http": self.http, "http_async": self.http_async}

    @abstractmethod
    def search(self, query: str):
        """search anime by string query

        :param query: string search query
        """
        pass

    @abstractmethod
    async def a_search(self, query: str):
        """search anime by string query in async mode

        :param query: string search query
        """
        pass

    @abstractmethod
    def ongoing(self):
        """get ongoings"""
        pass

    @abstractmethod
    async def a_ongoing(self):
        """get ongoings in async mode"""
        pass


@define(kw_only=True)
class HttpMixin:
    """this dataclass provide pre-configured http clients"""

    _http: "Client" = field(default=HTTPSync(), repr=False, kw_only=True, hash=False)
    """pre-configured sync httpx Client"""
    _http_async: "AsyncClient" = field(default=HTTPAsync(), repr=False, kw_only=True, hash=False)
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
    def _kwargs_http(self) -> Dict[str, Union["Client", "AsyncClient"]]:
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
    def get_anime(self):
        """get anime"""
        pass

    @abstractmethod
    async def a_get_anime(self):
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
    def get_anime(self):
        """get anime"""
        pass

    @abstractmethod
    async def a_get_anime(self):
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
    def get_episodes(self):
        """get episodes"""
        pass

    @abstractmethod
    async def a_get_episodes(self):
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
    num: str
    """episode number. Stars from 1"""

    @abstractmethod
    def get_sources(self):
        """get raw source player information"""
        pass

    @abstractmethod
    async def a_get_sources(self):
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

    @property
    def _all_video_extractors(self):
        return ALL_DECODERS

    def get_videos(self, **httpx_kwargs) -> List["Video"]:
        """get direct video information for direct play

        :param httpx_kwargs: httpx.Client configuration
        """
        for extractor in self._all_video_extractors:
            if self.url == extractor():
                return extractor(**httpx_kwargs).parse(self.url)
        warnings.warn(f"Failed extractor videos from {self.url}")
        return []

    async def a_get_videos(self, **httpx_kwargs) -> List["Video"]:
        """get direct video information for direct play in async mode

        :param httpx_kwargs: httpx.AsyncClient configuration
        """
        for extractor in self._all_video_extractors:
            if self.url == extractor():
                return await extractor(**httpx_kwargs).a_parse(self.url)
        warnings.warn(f"Failed extractor videos from {self.url}")
        return []

    def __str__(self):
        return f"{urlsplit(self.url).netloc} ({self.title})"

    def __hash__(self):
        return hash(tuple((self.title, self.url)))
