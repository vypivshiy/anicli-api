import warnings
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional, ClassVar, Type

from parsel import Selector
from scrape_schema import BaseSchema

from anicli_api._http import HTTPAsync, HTTPSync
from anicli_api.player import ALL_DECODERS

if TYPE_CHECKING:
    from anicli_api.player.base import Video


class MainSchema(BaseSchema):
    _Selector: ClassVar[Type[Selector]] = Selector
    HTTP = HTTPSync
    HTTP_ASYNC = HTTPAsync

    @classmethod
    def from_kwargs(cls, **kwargs):
        """ignore fields parse and set attrs directly"""
        cls_ = cls("")
        for k, v in kwargs.items():
            setattr(cls_, k, v)
        return cls_


class BaseExtractor(ABC):
    HTTP = HTTPSync
    HTTP_ASYNC = HTTPAsync
    BASE_URL: str = NotImplemented

    @abstractmethod
    def search(self, query: str):
        pass

    @abstractmethod
    async def a_search(self, query: str):
        pass

    @abstractmethod
    def ongoing(self):
        pass

    @abstractmethod
    async def a_ongoing(self):
        pass


class BaseSearch(MainSchema):
    url: str = NotImplemented
    title: str = NotImplemented
    thumbnail: str = NotImplemented

    @abstractmethod
    def get_anime(self):
        pass

    @abstractmethod
    async def a_get_anime(self):
        pass


class BaseOngoing(BaseSearch):
    url: str = NotImplemented
    title: str = NotImplemented
    thumbnail: str = NotImplemented

    @abstractmethod
    def get_anime(self):
        pass

    @abstractmethod
    async def a_get_anime(self):
        pass


class BaseAnime(MainSchema):
    title: str = NotImplemented
    alt_titles: List[str] = NotImplemented
    thumbnail: str = NotImplemented
    description: Optional[str] = NotImplemented
    genres: List[str] = NotImplemented
    episodes_available: Optional[int] = NotImplemented
    episodes_total: Optional[int] = NotImplemented
    aired: Optional[str] = NotImplemented

    @abstractmethod
    def get_episodes(self):
        pass

    @abstractmethod
    async def a_get_episodes(self):
        pass


class BaseEpisode(MainSchema):
    title: str = NotImplemented
    num: str = NotImplemented

    @abstractmethod
    def get_sources(self):
        pass

    @abstractmethod
    async def a_get_sources(self):
        pass


class BaseSource(MainSchema):
    ALL_VIDEO_EXTRACTORS = ALL_DECODERS
    url: str = NotImplemented

    def _pre_validate_url_attr(self) -> None:
        if self.url is NotImplemented:
            raise AttributeError(f"{self.__class__.__name__} missing url attribute.")

    def get_videos(self) -> List["Video"]:
        self._pre_validate_url_attr()
        for extractor in self.ALL_VIDEO_EXTRACTORS:
            if self.url == extractor():
                return extractor().parse(self.url)
        warnings.warn(f"Failed extractor videos from {self.url}", stacklevel=4)
        return []

    async def a_get_videos(self) -> List["Video"]:
        self._pre_validate_url_attr()
        for extractor in self.ALL_VIDEO_EXTRACTORS:
            if self.url == extractor():
                return await extractor().a_parse(self.url)
        warnings.warn(
            f"Failed extractor videos from {self.url}. " f"Maybe needed video extractor not implemented?",
            stacklevel=4,
        )
        return []
