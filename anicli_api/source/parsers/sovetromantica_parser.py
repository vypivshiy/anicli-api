# autogenerated by ssc-gen DO NOT_EDIT
from __future__ import annotations
import re
from typing import List, TypedDict, Union, Optional
from contextlib import suppress
import sys

if sys.version_info >= (3, 10):
    from types import NoneType
else:
    NoneType = type(None)

from parsel import Selector, SelectorList

T_OngoingPage = TypedDict(
    "T_OngoingPage",
    {
        "title": str,
        "thumbnail": str,
        "alt_title": str,
        "url": str,
    },
)
T_SearchPage = TypedDict(
    "T_SearchPage",
    {
        "title": str,
        "thumbnail": str,
        "alt_title": str,
        "url": str,
    },
)
T_EpisodeView = TypedDict(
    "T_EpisodeView",
    {
        "url": str,
        "thumbnail": str,
        "title": str,
    },
)
T_AnimePage = TypedDict(
    "T_AnimePage",
    {
        "title": str,
        "description": Optional[str],
        "thumbnail": str,
        "video_url": Optional[str],
        "episodes": List[T_EpisodeView],
    },
)


class OngoingPage:
    """
    GET https://sovetromantica.com/anime


    [
        {
            "title": "String",
            "thumbnail": "String",
            "alt_title": "String",
            "url": "String"
        },
        "..."
    ]"""

    def __init__(self, document: Union[str, SelectorList, Selector]) -> None:
        self._doc = Selector(document) if isinstance(document, str) else document

    def _split_doc(self, value: Selector) -> SelectorList:
        value1 = value.css(".anime--block__desu")
        return value1

    def _parse_title(self, value: Selector) -> str:
        value1 = value.css(".anime--block__name > span")
        value2 = value1[-1]
        value3 = "".join(value2.css("::text").getall())
        return value3

    def _parse_thumbnail(self, value: Selector) -> str:
        value1 = value.css(".anime--poster--loading > img")
        value2 = value1.attrib["src"]
        return value2

    def _parse_alt_title(self, value: Selector) -> str:
        value1 = value.css(".anime--block__name > span")
        value2 = "".join(value1.css("::text").getall())
        return value2

    def _parse_url(self, value: Selector) -> str:
        value1 = value.css(".anime--block__desu a")
        value2 = value1.attrib["href"]
        return value2

    def parse(self) -> List[T_OngoingPage]:
        return [
            {
                "title": self._parse_title(e),
                "thumbnail": self._parse_thumbnail(e),
                "alt_title": self._parse_alt_title(e),
                "url": self._parse_url(e),
            }
            for e in self._split_doc(self._doc)
        ]


class SearchPage:
    """Get all search results by query

    GET https://sovetromantica.com/anime
    query=<QUERY>

    EXAMPLE:
        GET https://sovetromantica.com/anime
        query=LAIN


    [
        {
            "title": "String",
            "thumbnail": "String",
            "alt_title": "String",
            "url": "String"
        },
        "..."
    ]"""

    def __init__(self, document: Union[str, SelectorList, Selector]) -> None:
        self._doc = Selector(document) if isinstance(document, str) else document

    def _split_doc(self, value: Selector) -> SelectorList:
        value1 = value.css(".anime--block__desu")
        return value1

    def _parse_title(self, value: Selector) -> str:
        value1 = value.css(".anime--block__name > span")
        value2 = value1[-1]
        value3 = "".join(value2.css("::text").getall())
        return value3

    def _parse_thumbnail(self, value: Selector) -> str:
        value1 = value.css(".anime--poster--loading > img")
        value2 = value1.attrib["src"]
        return value2

    def _parse_alt_title(self, value: Selector) -> str:
        value1 = value.css(".anime--block__name > span")
        value2 = "".join(value1.css("::text").getall())
        return value2

    def _parse_url(self, value: Selector) -> str:
        value1 = value.css(".anime--block__desu a")
        value2 = value1.attrib["href"]
        return value2

    def parse(self) -> List[T_SearchPage]:
        return [
            {
                "title": self._parse_title(e),
                "thumbnail": self._parse_thumbnail(e),
                "alt_title": self._parse_alt_title(e),
                "url": self._parse_url(e),
            }
            for e in self._split_doc(self._doc)
        ]


class EpisodeView:
    """WARNING!

    target page maybe does not contain video!

    GET https://sovetromantica.com/anime/<ANIME PATH>

    EXAMPLE:
        GET https://sovetromantica.com/anime/1459-sousou-no-frieren



    [
        {
            "url": "String",
            "thumbnail": "String",
            "title": "String"
        },
        "..."
    ]"""

    def __init__(self, document: Union[str, SelectorList, Selector]) -> None:
        self._doc = Selector(document) if isinstance(document, str) else document

    def _split_doc(self, value: Selector) -> SelectorList:
        value1 = value.css(".episodes-slick_item")
        return value1

    def _parse_url(self, value: Selector) -> str:
        value1 = value.css("a")
        value2 = value1.attrib["href"]
        value3 = "https://sovetromantica.com{}".format(value2) if value2 else value2
        return value3

    def _parse_thumbnail(self, value: Selector) -> str:
        value1 = value.css("img")
        value2 = value1.attrib["src"]
        return value2

    def _parse_title(self, value: Selector) -> str:
        value1 = value.css("img")
        value2 = value1.attrib["alt"]
        return value2

    def parse(self) -> List[T_EpisodeView]:
        return [
            {"url": self._parse_url(e), "thumbnail": self._parse_thumbnail(e), "title": self._parse_title(e)}
            for e in self._split_doc(self._doc)
        ]


class AnimePage:
    """Anime page information

    GET https://sovetromantica.com/anime/<ANIME PATH>

    EXAMPLE:
        GET https://sovetromantica.com/anime/1459-sousou-no-frieren

    ISSUES:
        - description maybe does not exist and return null (CHECK IT)
        - video key maybe returns null (not available)


    {
        "title": "String",
        "description": "String",
        "thumbnail": "String",
        "video_url": "String",
        "episodes": [
            {
                "url": "String",
                "thumbnail": "String",
                "title": "String"
            },
            "..."
        ]
    }"""

    def __init__(self, document: Union[str, SelectorList, Selector]) -> None:
        self._doc = Selector(document) if isinstance(document, str) else document

    def _parse_title(self, value: Selector) -> str:
        value1 = value.css(".anime-name .block--container")
        value2 = "".join(value1.css("::text").getall())
        return value2

    def _parse_description(self, value: Selector) -> Optional[str]:
        value1 = value
        with suppress(Exception):
            value2 = value1.css("#js-description_open-full")
            value3 = "".join(value2.css("::text").getall())
            return value3
        return None

    def _parse_thumbnail(self, value: Selector) -> str:
        value1 = value.css("#poster")
        value2 = value1.attrib["src"]
        value3 = "https://sovetromantica.com{}".format(value2) if value2 else value2
        return value3

    def _parse_video_url(self, value: Selector) -> Optional[str]:
        value1 = value
        with suppress(Exception):
            value2 = value1.get()
            value3 = re.search('"file":"([^>]+\\.m3u8)"\\s*}', value2)[1]
            return value3
        return None

    def _parse_episodes(self, value: Selector) -> List[T_EpisodeView]:
        value1 = EpisodeView(value).parse()
        return value1

    def parse(self) -> T_AnimePage:
        return {
            "title": self._parse_title(self._doc),
            "description": self._parse_description(self._doc),
            "thumbnail": self._parse_thumbnail(self._doc),
            "video_url": self._parse_video_url(self._doc),
            "episodes": self._parse_episodes(self._doc),
        }
