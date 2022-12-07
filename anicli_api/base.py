"""
Base class constructors for build extractor

Extractor works steps:

- Extractor.search(), Extractor.ongoing() -> (List[SearchResult]/List[Ongoing])

- SearchResult.get_anime(), Ongoing.get_anime() -> (AnimeInfo)

- AnimeInfo.get_episodes() -> (List[Episode])

- Episode.get_videos() -> (List[Video])

- Video.get_source() -> (List[MetaVideo])

Can be iterated from Extractor.walk_search, Extractor.walk_ongoing methods or Search, Ongoing objects and get dataclass
with all objects.


**IterData**:

- search: Union[SearchResult, Ongoing]

- anime: Union[AnimeInfo]

- episode: Episode

- video: Video
"""
from __future__ import annotations

import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass
from html import unescape
from typing import Any, AsyncGenerator, Awaitable, Dict, Generator, List, Sequence, Type, Union

from bs4 import BeautifulSoup

from anicli_api._http import BaseHTTPAsync, BaseHTTPSync
from anicli_api.base_decoder import BaseDecoder, MetaVideo
from anicli_api.decoders import ALL_DECODERS
from anicli_api.re_models import ReField, ReFieldList, ReFieldListDict, parse_many

__all__ = (
    "BaseModel",
    "BaseOngoing",
    "BaseEpisode",
    "BaseVideo",
    "BaseSearchResult",
    "BaseAnimeInfo",
    "BaseAnimeExtractor",
    "BaseTestCollections",
    "List",  # python 3.8 support typehint
)


@dataclass
class IterData:
    """
    Dataclass for iterable methods

    - search - Ongoing or SearchResult object

    - anime - AnimeInfo object

    - episode - Episode object

    - video - Video object
    """

    search: Union[BaseSearchResult, BaseOngoing]
    anime: Union[BaseAnimeInfo]
    episode: BaseEpisode
    video: BaseVideo


class BaseModel(ABC):
    """Base Model class for extractor objects.

    **Instances, for work http requests and response data:**

    - _HTTP = BaseHTTPSync - http singleton sync requests class

    - _HTTP_ASYNC = BaseHTTPAsync - http singleton async requests class

    **Methods:**

    - _BaseModel._soup - return BeautifulSoap instance

    - _BaseModel._unescape - html.unescape function. Unescape text response

    **Optional regex search class helpers:**

    - _ReField - re_models.ReField

    - _ReFieldList - re_models.ReFieldList

    - _ReFieldListDict - re_models.ReFieldListDict

    - _parse_many - re_models.parse_many
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
    def _soup(
        markup: Union[str, bytes], *, parser: str = "html.parser", **kwargs
    ) -> BeautifulSoup:
        """Create BeautifulSoup instance

        :param markup: html page
        :param parser: soup parser. Default "html.parser"
        :param kwargs: any BeautifulSoup params
        :return: BeautifulSoup instance
        """
        return BeautifulSoup(markup, parser, **kwargs)

    @staticmethod
    async def _async_generator(async_func: Awaitable) -> AsyncGenerator:
        """Convert asyncio function to AsyncGenerator

        :param async_func: awaitable function
        :return: async generator
        """
        for j in await async_func:
            yield j

    def dict(self) -> Dict[str, Any]:
        """Convert all public class attributes to dict

        :return: all attributes in dict structure
        """
        return {
            k: getattr(self, k)
            for k in self.__dict__
            if not k.startswith("_") and not k.endswith("_")
        }

    def __repr__(self):
        return f"[{self.__class__.__name__}] " + ", ".join(
            (f"{k}={v}" for k, v in self.dict().items())
        )


class BaseSearchResult(BaseModel):
    """
    Base search result class object.
    """

    @abstractmethod
    async def a_get_anime(self) -> BaseAnimeInfo:
        """asyncio get AnimeInfo object

        :return: AnimeInfo object
        """
        pass

    @abstractmethod
    def get_anime(self) -> BaseAnimeInfo:
        """get AnimeInfo object

        :return: AnimeInfo object
        """
        pass

    def _full_parse(self) -> Generator:
        anime = self.get_anime()
        for episode in anime.get_episodes():
            for video in episode.get_videos():
                yield IterData(search=self, anime=anime, episode=episode, video=video)

    async def _async_full_parse(self) -> AsyncGenerator:
        anime = await self.a_get_anime()
        for episode in await anime.a_get_episodes():
            for video in await episode.a_get_videos():
                yield IterData(search=self, anime=anime, episode=episode, video=video)

    def __iter__(self):
        return self._full_parse()

    def __aiter__(self):
        return self._async_full_parse()


class BaseOngoing(BaseSearchResult):
    """
    Base ongoing class
    """

    @abstractmethod
    async def a_get_anime(self) -> BaseAnimeInfo:
        """asyncio get list episodes objects

        :return: AnimeInfo
        """
        pass

    @abstractmethod
    def get_anime(self) -> BaseAnimeInfo:
        """get AnimeInfo object

        :return: AnimeInfo
        """
        pass


class BaseAnimeInfo(BaseModel):
    """
    AnimeInfo object
    """

    @abstractmethod
    async def a_get_episodes(self) -> List:
        """get asyncio list episodes objects

        :return: List[Episode]
        """
        pass

    @abstractmethod
    def get_episodes(self) -> List:
        """get list episodes objects

        :return: List[Episode]
        """
        pass

    def __iter__(self):
        return iter(self.get_episodes())

    def __aiter__(self):
        return self._async_generator(self.a_get_episodes())


class BaseEpisode(BaseModel):
    """
    Episode object
    """

    @abstractmethod
    async def a_get_videos(self) -> List:
        """asyncio get list video objects

        :return: List[Video]
        """
        pass

    @abstractmethod
    def get_videos(self) -> List:
        """get list video objects

        :return: List[Video]
        """
        pass

    def __iter__(self):
        return iter(self.get_videos())

    def __aiter__(self):
        return self._async_generator(self.a_get_videos())


class BaseVideo(BaseModel):
    """Base video class object.

    **url is a required attribute to try automatic getting of direct links to videos**

    If video have decoder, return list of MetaVideo dataclasses with videos.

    Else, return direct url and throw warning or define get_source, a_get_source methods
    """

    url: str
    _DECODERS: Sequence[Type[BaseDecoder]] = ALL_DECODERS

    async def a_get_source(self) -> Union[str, List[MetaVideo]]:
        for decoder in self._DECODERS:
            if self.url == decoder():
                return await decoder.async_parse(self.url)
        warnings.warn(f"Fail parse {self.url}, return string", stacklevel=2)
        return self.url

    def get_source(self) -> Union[str, List[MetaVideo]]:
        # sourcery skip: use-next
        for decoder in self._DECODERS:
            if self.url == decoder():
                return decoder.parse(self.url)
        warnings.warn(f"Fail parse {self.url}, return string", stacklevel=2)
        return self.url


class BaseAnimeExtractor(ABC):
    """First Extractor entrypoint class

    **Instances, for work http requests and response data:**

    - _HTTP = BaseHTTPSync - http singleton sync requests class

    - _HTTP_ASYNC = BaseHTTPAsync - http singleton async requests class

    **Methods:**

    - _BaseModel._soup - return BeautifulSoap instance

    - _BaseModel._unescape - html.unescape function. Unescape text response

    **Optional regex search class helpers:**

    - _ReField - re_models.ReField

    - _ReFieldList - re_models.ReFieldList

    - _ReFieldListDict - re_models.ReFieldListDict

    - _parse_many - re_models.parse_many
    """

    HTTP = BaseHTTPSync
    HTTP_ASYNC = BaseHTTPAsync

    _unescape = unescape

    _ReField = ReField
    _ReFieldList = ReFieldList
    _ReFieldListDict = ReFieldListDict
    _parse_many = parse_many

    @abstractmethod
    def search(self, query: str) -> List:
        """Get search results from query

        :param query: string query for search
        :return: List[SearchResult] objects
        """
        pass

    @abstractmethod
    def ongoing(self) -> List:
        """Get ongoings

        :return: List[Ongoing] objects
        """
        pass

    @abstractmethod
    async def async_search(self, query: str) -> List:
        """Get asyncio search

        :param query: string query for search
        :return: List[SearchResult] objects
        """
        pass

    @abstractmethod
    async def async_ongoing(self) -> List:
        """Get asyncio ongoing

        :return: List[Ongoing] objects
        """
        pass

    @staticmethod
    def _iter_from_result(obj: Union[BaseSearchResult, BaseOngoing]) -> Generator:
        anime = obj.get_anime()
        for episode in anime.get_episodes():
            for video in episode.get_videos():
                yield IterData(search=obj, anime=anime, episode=episode, video=video)

    @staticmethod
    async def _aiter_from_result(obj: Union[BaseSearchResult, BaseOngoing]) -> AsyncGenerator:
        anime = await obj.a_get_anime()
        for episode in await anime.a_get_episodes():
            for video in await episode.a_get_videos():
                yield IterData(search=obj, anime=anime, episode=episode, video=video)

    def walk_search(self, query: str) -> Generator:
        """iter in all search result from search from query

        :param query: string query for search
        :return: dataclass generator with SearchResult, AnimeInfo, Episode and Video objects
        """
        for search_result in self.search(query):
            yield from self._iter_from_result(search_result)

    def walk_ongoing(self) -> Generator:
        """iter in all search result from ongoing

        :return: dataclass generator with Ongoing, AnimeInfo, Episode and Video objects
        """
        for ongoing in self.ongoing():
            yield from self._iter_from_result(ongoing)

    async def async_walk_search(self, query: str) -> AsyncGenerator:
        """iter all steps search result from query

        :param query: string query for search
        :return: dataclass async generator with SearchResult, AnimeInfo, Episode and Video objects
        """
        for search_result in await self.async_search(query):
            async for data in self._aiter_from_result(search_result):
                yield data

    async def async_walk_ongoing(self) -> AsyncGenerator:
        """iter all steps from ongoing class

        :return: dataclass async generator with Ongoing, AnimeInfo, Episode and Video objects
        """
        for ongoing in await self.async_ongoing():
            async for data in self._aiter_from_result(ongoing):
                yield data

    @staticmethod
    def _soup(
        markup: Union[str, bytes], *, parser: str = "html.parser", **kwargs
    ) -> BeautifulSoup:
        """Create BeautifulSoup instance

        :param markup: html page
        :param parser: soup parser. Default "html.parser"
        :param kwargs: any BeautifulSoup params
        :return: BeautifulSoup instance
        """
        return BeautifulSoup(markup, parser, **kwargs)


class BaseTestCollections(ABC):
    """Collections of testcases for quick test works parsers

    If necessary, you can add extra tests, methods names must start with **test_** prefix.

    **This class is not for embedding in CD/CD for next reasons:**

    - they are tested on **real services** and this is very slow

    - tests may not pass due to restrictions: DDoS protection, work with certain regions / IP addresses etc...
    """

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
