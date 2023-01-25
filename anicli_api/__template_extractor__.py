"""Template extractor

HOW TO create custom extractor:

1. reverse required entrypoits

2. copy this template

**Write module:**

1. Extractor

- define: search, async_search with http request and parsers for get list of search resulse by string query

- define ongoing, async_ongoing with http request and parsers for get list of ongoings

2. Ongoing

- define get_anime, a_get anime with http request and parsers for get AnimeInfo

3. SearchResult

- define get_anime, a_get anime with http request and parsers for get AnimeInfo

4. AnimeInfo

- define get_episodes, a_get_episodes with http request and parsers for get list of episodes

5. Episode

- define get_videos, a_get_videos with http request and parsers for get list of Videos

6. Video

- if the video hosting service is in the decoders,
then pass the required parameter **url** to it, and it will automatically pull out and return the list MetaVideo class.

Else, define get_source, a_get_source or write a new decoder.

7. Test collections

- define a minimum number of tests to quickly check the functionality.

**Not need to be fully covered module.** Their goal is to **quickly** check the performance

**Notes:**

- To scrap the necessary data, you can use any of the following methods:
    json
    bs4.BeautifulSoup (with default html.parser)
    re
    anicli_api.re_models

- for refactoring code, use **hidden** methods

- Protocols class need for correct IDE typing help in generators and iterable methods

- If **Оngoing** and **SearchResult** by functionality are duplicate,
create an additional class, inheriting from BaseModel, add the necessary functionality there.

Example:

```py
from anicli_api.base import *

...

class SomeParser(BaseModel):
    def get_anime(self):
        return "test123"

    async def a_get_anime(self):
        return "foobar"

class SearchResult(SomeParser, BaseSearchResult):
    ...

class Ongoing(SomeParser, BaseOngoing):
    ...
```

"""
from __future__ import annotations

from typing import AsyncGenerator, Generator, Protocol

from anicli_api.base import *

__all__ = (
    "Extractor",
    "SearchResult",
    "Ongoing",
    "AnimeInfo",
    "Episode",
    "Video",
    "TestCollections",
)


class SearchIterData(Protocol):
    # IDE typing help: SearchResult.__iter__, SearchResult.__aiter__, walk_search, async_walk_search
    search: SearchResult
    anime: AnimeInfo
    episode: Episode
    video: Video


class OngoingIterData(Protocol):
    # IDE typing help: typing help: Ongoing.__iter__, Ongoing.__aiter__, walk_ongoing, async_walk_ongoing
    search: Ongoing
    anime: AnimeInfo
    episode: Episode
    video: Video


class Extractor(BaseAnimeExtractor):
    # optional constants, HTTP configuration here
    BASE_URL = "https://example.com"

    def async_walk_search(self, query: str) -> AsyncGenerator[SearchIterData, None]:
        return super().async_walk_search(query)

    def walk_search(self, query: str) -> Generator[SearchIterData, None, None]:
        return super().walk_search(query)

    def async_walk_ongoing(self) -> AsyncGenerator[OngoingIterData, None]:
        return super().async_walk_ongoing()

    def walk_ongoing(self) -> Generator[OngoingIterData, None, None]:
        return super().walk_ongoing()

    def search(self, query: str) -> List["SearchResult"]:
        # past code here
        response = self.HTTP().get(f"{self.BASE_URL}/search", params={"search": query}).text
        ...

    def ongoing(self) -> List["Ongoing"]:
        # past code here
        response = self.HTTP().get(f"{self.BASE_URL}/ongoing").text
        ...

    async def async_search(self, query: str) -> List["SearchResult"]:
        # past async code here
        async with self.HTTP_ASYNC() as session:
            response = (
                await session.get(f"{self.BASE_URL}/search", params={"search": query})
            ).text
            ...

    async def async_ongoing(self) -> List["Ongoing"]:
        # past async code here
        async with self.HTTP_ASYNC() as session:
            response = (await session.get(f"{self.BASE_URL}/search")).text
            ...


class SearchResult(BaseSearchResult):
    # optional past metadata attrs here
    def __iter__(self) -> Generator[SearchIterData, None, None]:
        return super().__iter__()

    def __aiter__(self) -> AsyncGenerator[SearchIterData, None]:
        return super().__aiter__()

    async def a_get_anime(self) -> "AnimeInfo":
        # past async code here
        pass

    def get_anime(self) -> "AnimeInfo":
        # past code here
        pass


class Ongoing(BaseOngoing):
    # optional past metadata attrs here
    def __iter__(self) -> Generator[OngoingIterData, None, None]:
        return super().__iter__()

    def __aiter__(self) -> AsyncGenerator[OngoingIterData, None]:
        return super().__aiter__()

    async def a_get_anime(self) -> "AnimeInfo":
        # past async code here
        pass

    def get_anime(self) -> "AnimeInfo":
        # past code here
        pass


class AnimeInfo(BaseAnimeInfo):
    # optional past metadata attrs here
    async def a_get_episodes(self) -> List["Episode"]:
        # past async code here
        pass

    def get_episodes(self) -> List["Episode"]:
        # past code here
        pass


class Episode(BaseEpisode):
    # optional past metadata attrs here
    async def a_get_videos(self) -> List["Video"]:
        # past async code here
        pass

    def get_videos(self) -> List["Video"]:
        # past code here
        pass


class Video(BaseVideo):
    # optional past metadata attrs here.
    # url: str
    # attribute required for automatic video parser for available decoders
    # or manually define get_source and a_get_source methods
    pass


class TestCollections(BaseTestCollections):
    def test_search(self):
        # rewrite testcase search here
        result = Extractor().search("serial experiments lain")
        # past metadata dict
        assert result[0].get_anime().dict() == {}

    def test_ongoing(self):
        # test get ongoing
        assert len(Extractor().ongoing()) > 1

    def test_extract_metadata(self):
        # rewrite testcase get metadata here
        for meta in Extractor().search("serial experiments lain")[0]:
            # past metadata dict here
            assert meta.search.dict() == {}
            assert meta.anime.dict() == {}
            assert meta.episode.dict() == {}
            break

    def test_extract_video(self):
        # rewrite testcase extract video here
        for meta in Extractor().search("serial experiments lain")[0]:
            assert "kodik" in meta.video.url
            assert meta.video.get_source()[0].url.endswith(".m3u8")
