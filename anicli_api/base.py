"""base prototype architecture for anicli extractor

Extractor works schema:
    [Extractor]
        | search()/ongoing()
        V
  [SearchResult | Ongoing]
         | get_anime()
         V
    [AnimeInfo]
        | get_episodes()
        V
    [Episodes]
        | get_videos()
        V
    [Video]
        |
        V
    {quality: url, ...} or url
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import (
    Union,
    Dict,
    Any,
    List,
    Generator,
    AsyncGenerator,
    Awaitable,
    Tuple,
    Type,
)

from html import unescape
import warnings

from bs4 import BeautifulSoup

from abc import ABC, abstractmethod
from anicli_api.re_models import ReField, ReFieldList, ReFieldListDict, parse_many
from anicli_api._http import BaseHTTPSync, BaseHTTPAsync
from anicli_api.decoders import (
    ALL_DECODERS,
    MetaVideo,
    BaseDecoder
)

__all__ = (
    'BaseModel',
    'BaseOngoing',
    'BaseEpisode',
    'BaseVideo',
    'BaseSearchResult',
    'BaseAnimeInfo',
    'BaseAnimeExtractor',
    'BaseTestCollections',
    'List'  # python 3.8 support typehint
)


@dataclass
class IterData:
    search: Union[BaseSearchResult, BaseOngoing]
    anime: Union[BaseAnimeInfo]
    episode: BaseEpisode
    video: BaseVideo


class BaseModel(ABC):
    """Base Model class

    instances:

    HTTP = BaseHTTPSync - http singleton sync requests class

    HTTP_ASYNC = BaseHTTPAsync - http singleton async requests class

    methods:

    BaseModel._soup - return BeautifulSoap instance

    BaseModel._unescape - unescape text

    optional regex search class helpers:

    _ReField - ReField

    _ReFieldList - re_models.ReFieldList

    _ReFieldListDict - re_models.ReFieldListDict

    _parse_many - re_models.parse_many
    """
    # http singleton sync requests class
    _HTTP = BaseHTTPSync
    # http singleton async requests class
    _HTTP_ASYNC = BaseHTTPAsync

    _unescape = unescape

    # optional regex search class helpers
    _ReField = ReField
    _ReFieldList = ReFieldList
    _ReFieldListDict = ReFieldListDict
    _parse_many = parse_many

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @staticmethod
    def _soup(markup: Union[str, bytes], *, parser: str = "html.parser", **kwargs) -> BeautifulSoup:
        """return BeautifulSoup object"""
        return BeautifulSoup(markup, parser, **kwargs)

    @staticmethod
    async def _async_generator(async_func: Awaitable) -> AsyncGenerator:
        """convert awaitable call to AsyncGenerator"""
        for j in (await async_func):
            yield j

    def dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dict__
                if not k.startswith("_") and not k.endswith("_")}

    def __repr__(self):
        return f"[{self.__class__.__name__}] " + ", ".join((f"{k}={v}" for k, v in self.dict().items()))


class BaseSearchResult(BaseModel):
    """Base search result class object."""

    @abstractmethod
    async def a_get_anime(self) -> BaseAnimeInfo:
        pass

    @abstractmethod
    def get_anime(self) -> BaseAnimeInfo:
        """return BaseAnimeInfo object"""
        pass

    def _full_parse(self) -> Generator:
        anime = self.get_anime()
        for episode in anime.get_episodes():
            for video in episode.get_videos():
                yield IterData(search=self,
                               anime=anime,
                               episode=episode,
                               video=video)

    async def _async_full_parse(self) -> AsyncGenerator:
        anime = await self.a_get_anime()  # type: ignore
        for episode in (await anime.a_get_episodes()):
            for video in (await episode.a_get_videos()):
                yield IterData(search=self,
                               anime=anime,
                               episode=episode,
                               video=video)

    def __iter__(self):
        return self._full_parse()

    def __aiter__(self):
        return self._async_full_parse()


class BaseOngoing(BaseSearchResult):
    @abstractmethod
    async def a_get_anime(self) -> BaseAnimeInfo:
        pass

    @abstractmethod
    def get_anime(self) -> BaseAnimeInfo:
        pass


class BaseAnimeInfo(BaseModel):
    @abstractmethod
    async def a_get_episodes(self) -> List:
        pass

    @abstractmethod
    def get_episodes(self) -> List:
        """return List[Episodes] objects"""
        pass

    def __iter__(self):
        return iter(self.get_episodes())

    def __aiter__(self):
        return self._async_generator(self.a_get_episodes())


class BaseEpisode(BaseModel):
    @abstractmethod
    async def a_get_videos(self) -> List:
        pass

    @abstractmethod
    def get_videos(self) -> List:
        """return List[BaseVideo] objects"""
        pass

    def __iter__(self):
        return iter(self.get_videos())

    def __aiter__(self):
        return self._async_generator(self.a_get_videos())


class BaseVideo(BaseModel):
    """Base video class object.

    minimum required attributes:

    url: str - url to balancer or direct video
    """
    url: str
    _DECODERS: Tuple[Type[BaseDecoder], ...] = ALL_DECODERS

    async def a_get_source(self) -> Union[str, List[MetaVideo]]:
        for decoder in self._DECODERS:
            if self.url == decoder():
                return await decoder.async_parse(self.url)
        warnings.warn(f"Fail parse {self.url}, return string", stacklevel=2)
        return self.url

    def get_source(self) -> Union[str, List[MetaVideo]]:
        # sourcery skip: use-next
        """if video is Kodik or Aniboom, return dict with videos. Else, return direct url"""
        for decoder in self._DECODERS:
            if self.url == decoder():
                return decoder.parse(self.url)
        warnings.warn(f"Fail parse {self.url}, return string", stacklevel=2)
        return self.url


class BaseAnimeExtractor(ABC):
    """First extractor entrypoint class"""
    HTTP = BaseHTTPSync
    HTTP_ASYNC = BaseHTTPAsync

    _unescape = unescape

    _ReField = ReField
    _ReFieldList = ReFieldList
    _ReFieldListDict = ReFieldListDict
    _parse_many = parse_many

    @abstractmethod
    def search(self, query: str) -> List:
        pass

    @abstractmethod
    def ongoing(self) -> List:
        pass

    @abstractmethod
    async def async_search(self, query: str) -> List:
        pass

    @abstractmethod
    async def async_ongoing(self) -> List:
        pass

    @staticmethod
    def _iter_from_result(obj: Union[BaseSearchResult, BaseOngoing]) -> Generator:
        anime = obj.get_anime()
        for episode in anime.get_episodes():
            for video in episode.get_videos():
                yield IterData(search=obj,
                               anime=anime,
                               episode=episode,
                               video=video)

    @staticmethod
    async def _aiter_from_result(obj: Union[BaseSearchResult, BaseOngoing]) -> AsyncGenerator:
        anime = await obj.a_get_anime()
        for episode in (await anime.a_get_episodes()):
            for video in (await episode.a_get_videos()):
                yield IterData(search=obj,
                               anime=anime,
                               episode=episode,
                               video=video)

    def walk_search(self, query: str) -> Generator:
        for search_result in self.search(query):
            yield from self._iter_from_result(search_result)

    def walk_ongoing(self) -> Generator:
        for ongoing in self.ongoing():
            yield from self._iter_from_result(ongoing)

    async def async_walk_search(self, query: str) -> AsyncGenerator:
        for search_result in (await self.async_search(query)):
            async for data in self._aiter_from_result(search_result):
                yield data

    async def async_walk_ongoing(self) -> AsyncGenerator:
        for ongoing in (await self.async_ongoing()):
            async for data in self._aiter_from_result(ongoing):
                yield data

    @staticmethod
    def _soup(markup: Union[str, bytes],
              *, parser: str = "html.parser",
              **kwargs
              ) -> BeautifulSoup:
        """return BeautifulSoup instance"""
        return BeautifulSoup(markup, parser, **kwargs)


class BaseTestCollections(ABC):
    @abstractmethod
    def test_search(self):
        ...

    @abstractmethod
    def test_ongoing(self):
        ...

    @abstractmethod
    def test_extract_metadata(self):
        ...

    @abstractmethod
    def test_extract_video(self):
        ...
