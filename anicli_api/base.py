import warnings
from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Type
from urllib.parse import urlsplit

from anicli_api._http import (  # noqa: F401
    HTTPAsync,
    HTTPRetryConnectAsyncTransport,
    HTTPRetryConnectSyncTransport,
    HTTPSync,
    DDOSServerDetectError
)
from anicli_api.player import ALL_DECODERS

if TYPE_CHECKING:
    from anicli_api.player.base import Video


class BaseExtractor:
    HTTP = HTTPSync
    HTTP_ASYNC = HTTPAsync
    BASE_URL: str = NotImplemented

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


class _HttpExtension:
    @property
    def _http(self) -> Type[HTTPSync]:
        return HTTPSync

    @property
    def _a_http(self) -> Type[HTTPAsync]:
        return HTTPAsync


@dataclass
class BaseSearch(_HttpExtension):
    title: str
    thumbnail: str
    url: str

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


@dataclass
class BaseOngoing(_HttpExtension):
    title: str
    thumbnail: str
    url: str

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


@dataclass
class BaseAnime(_HttpExtension):
    title: str
    thumbnail: str
    description: str

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
            return f"{self.title} {self.description[:(80-len(self.title)-3)]}..."
        return f"{self.title} {self.description}"


@dataclass
class BaseEpisode(_HttpExtension):
    title: str
    num: str

    @abstractmethod
    def get_sources(self):
        """get raw source player information"""
        pass

    @abstractmethod
    async def a_get_sources(self):
        """get raw source player information in async mode"""
        pass

    def __str__(self):
        return f"{self.num} {self.title}"


@dataclass
class BaseSource(_HttpExtension):
    title: str
    url: str

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
