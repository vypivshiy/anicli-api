# autogenerated by ssc-gen DO NOT_EDIT
from __future__ import annotations
from typing import List, Dict, TypedDict, Union
import sys

if sys.version_info >= (3, 10):
    from types import NoneType
else:
    NoneType = type(None)

from parsel import Selector, SelectorList

T_OngoingPage = TypedDict(
    "T_OngoingPage",
    {
        "url": str,
        "title": str,
        "thumbnail": str,
    },
)
T_SearchPage = TypedDict(
    "T_SearchPage",
    {
        "url": str,
        "title": str,
        "thumbnail": str,
    },
)
T_AnimePage = TypedDict(
    "T_AnimePage",
    {
        "title": str,
        "description": str,
        "thumbnail": str,
        "news_id": str,
    },
)
T_EpisodeDubbersView = Dict[str, str]
T_EpisodesPage = TypedDict(
    "T_EpisodesPage",
    {
        "dubbers": T_EpisodeDubbersView,
        "player_url": str,
    },
)
T_SourceKodikEpisodesView = TypedDict(
    "T_SourceKodikEpisodesView",
    {
        "value": str,
        "data_id": str,
        "data_hash": str,
        "data_title": str,
    },
)
T_SourceKodikTranslationsView = TypedDict(
    "T_SourceKodikTranslationsView",
    {
        "value": str,
        "data_id": str,
        "data_translation_type": str,
        "data_media_id": str,
        "data_media_hash": str,
        "data_media_type": str,
        "data_title": str,
        "data_episode_count": str,
    },
)
T_SourceKodikSerialPage = TypedDict(
    "T_SourceKodikSerialPage",
    {
        "episodes": List[T_SourceKodikEpisodesView],
        "translations": List[T_SourceKodikTranslationsView],
    },
)


class OngoingPage:
    """Get all available ongoings from main page

    GET https://animego.pro/ongoing


    [
        {
            "url": "String",
            "title": "String",
            "thumbnail": "String"
        },
        "..."
    ]"""

    def __init__(self, document: Union[str, SelectorList, Selector]) -> None:
        self._doc = Selector(document) if isinstance(document, str) else document

    def _split_doc(self, value: Selector) -> SelectorList:
        value1 = value.css(".card")
        return value1

    def _parse_url(self, value: Selector) -> str:
        value1 = value.css(".card .card__title > a")
        value2 = value1.attrib["href"]
        return value2

    def _parse_title(self, value: Selector) -> str:
        value1 = value.css(".card .card__title > a")
        value2 = "".join(value1.css("::text").getall())
        return value2

    def _parse_thumbnail(self, value: Selector) -> str:
        value1 = value.css(".card img")
        value2 = value1.attrib["src"]
        value3 = value2.lstrip("https://animego-online.org")
        value4 = "https://animego.pro{}".format(value3) if value3 else value3
        return value4

    def parse(self) -> List[T_OngoingPage]:
        return [
            {"url": self._parse_url(e), "title": self._parse_title(e), "thumbnail": self._parse_thumbnail(e)}
            for e in self._split_doc(self._doc)
        ]


class SearchPage:
    """Get all search results by query

    POST https://animego.pro
    do=search&subaction=search&story=QUERY


    [
        {
            "url": "String",
            "title": "String",
            "thumbnail": "String"
        },
        "..."
    ]"""

    def __init__(self, document: Union[str, SelectorList, Selector]) -> None:
        self._doc = Selector(document) if isinstance(document, str) else document

    def _split_doc(self, value: Selector) -> SelectorList:
        value1 = value.css(".card")
        return value1

    def _parse_url(self, value: Selector) -> str:
        value1 = value.css(".card .card__title > a")
        value2 = value1.attrib["href"]
        return value2

    def _parse_title(self, value: Selector) -> str:
        value1 = value.css(".card .card__title > a")
        value2 = "".join(value1.css("::text").getall())
        return value2

    def _parse_thumbnail(self, value: Selector) -> str:
        value1 = value.css(".card img")
        value2 = value1.attrib["src"]
        value3 = value2.lstrip("https://animego-online.org")
        value4 = "https://animego.pro{}".format(value3) if value3 else value3
        return value4

    def parse(self) -> List[T_SearchPage]:
        return [
            {"url": self._parse_url(e), "title": self._parse_title(e), "thumbnail": self._parse_thumbnail(e)}
            for e in self._split_doc(self._doc)
        ]


class AnimePage:
    """Anime page information. anime path contains in SearchView.url or Ongoing.url

    GET https://animego.pro/<ANIME_PATH>

    EXAMPLE:

        GET https://animego.pro/3374-serial-experiments-lain.html


    {
        "title": "String",
        "description": "String",
        "thumbnail": "String",
        "news_id": "String"
    }"""

    def __init__(self, document: Union[str, SelectorList, Selector]) -> None:
        self._doc = Selector(document) if isinstance(document, str) else document

    def _parse_title(self, value: Selector) -> str:
        value1 = value.css(".page__header h1")
        value2 = "".join(value1.css("::text").getall())
        return value2

    def _parse_description(self, value: Selector) -> str:
        value1 = value.css(".clearfix")
        value2 = value1.css("::text").getall()
        value3 = " ".join(value2)
        return value3

    def _parse_thumbnail(self, value: Selector) -> str:
        value1 = value.css(".pmovie__poster > img")
        value2 = value1.attrib["src"]
        value3 = value2.lstrip("https://animego-online.org")
        value4 = "https://animego.pro{}".format(value3) if value3 else value3
        return value4

    def _parse_news_id(self, value: Selector) -> str:
        value1 = value.css("#kodik_player_ajax")
        value2 = value1.attrib["data-news_id"]
        return value2

    def parse(self) -> T_AnimePage:
        return {
            "title": self._parse_title(self._doc),
            "description": self._parse_description(self._doc),
            "thumbnail": self._parse_thumbnail(self._doc),
            "news_id": self._parse_news_id(self._doc),
        }


class EpisodeDubbersView:
    """

    {
        "<K>": "String",
        "<KN>": "..."
    }"""

    def __init__(self, document: Union[str, SelectorList, Selector]) -> None:
        self._doc = Selector(document) if isinstance(document, str) else document

    def _split_doc(self, value: Selector) -> SelectorList:
        value1 = value.css("#translators-list > li")
        return value1

    def _parse_key(self, value: Selector) -> str:
        value1 = value.attrib["data-this_translator"]
        return value1

    def _parse_value(self, value: Selector) -> str:
        value1 = "".join(value.css("::text").getall())
        return value1

    def parse(self) -> T_EpisodeDubbersView:
        return {self._parse_key(e): self._parse_value(e) for e in self._split_doc(self._doc)}


class EpisodesPage:
    """Representation dubbers, and video url data

    Prepare:
      1. get news_id from Anime object
      2. POST 'https://animego.pro/engine/ajax/controller.php?mod=kodik_playlist_ajax'
        news_id=<AnimeView.news_id>&action=load_player
      3. send request to /serial/ link, DROP param only_translations
    EXAMPLE:

        # SOURCE:
            https://animego.pro/6240-loop-7-kaime-no-akuyaku-reijou-wa-moto-tekikoku-de-jiyuukimama-na-hanayome-seikatsu-o-mankitsu-suru.html

        POST https://animego.pro/engine/ajax/controller.php?mod=kodik_playlist_ajax
        news_id=6240&action=load_player


    {
        "dubbers": {
            "<K>": "String",
            "<KN>": "..."
        },
        "player_url": "String"
    }"""

    def __init__(self, document: Union[str, SelectorList, Selector]) -> None:
        self._doc = Selector(document) if isinstance(document, str) else document

    def _parse_dubbers(self, value: Selector) -> T_EpisodeDubbersView:
        value1 = EpisodeDubbersView(value).parse()
        return value1

    def _parse_player_url(self, value: Selector) -> str:
        value1 = value.css("#player_kodik > iframe")
        value2 = value1.attrib["src"]
        value3 = "https:{}".format(value2) if value2 else value2
        return value3

    def parse(self) -> T_EpisodesPage:
        return {"dubbers": self._parse_dubbers(self._doc), "player_url": self._parse_player_url(self._doc)}


class SourceKodikEpisodesView:
    """

    [
        {
            "value": "String",
            "data_id": "String",
            "data_hash": "String",
            "data_title": "String"
        },
        "..."
    ]"""

    def __init__(self, document: Union[str, SelectorList, Selector]) -> None:
        self._doc = Selector(document) if isinstance(document, str) else document

    def _split_doc(self, value: Selector) -> SelectorList:
        value1 = value.css(".serial-series-box > select > option")
        return value1

    def _parse_value(self, value: Selector) -> str:
        value1 = value.attrib["value"]
        return value1

    def _parse_data_id(self, value: Selector) -> str:
        value1 = value.attrib["data-id"]
        return value1

    def _parse_data_hash(self, value: Selector) -> str:
        value1 = value.attrib["data-hash"]
        return value1

    def _parse_data_title(self, value: Selector) -> str:
        value1 = value.attrib["data-title"]
        value2 = value1.strip(" ")
        return value2

    def parse(self) -> List[T_SourceKodikEpisodesView]:
        return [
            {
                "value": self._parse_value(e),
                "data_id": self._parse_data_id(e),
                "data_hash": self._parse_data_hash(e),
                "data_title": self._parse_data_title(e),
            }
            for e in self._split_doc(self._doc)
        ]


class SourceKodikTranslationsView:
    """

    [
        {
            "value": "String",
            "data_id": "String",
            "data_translation_type": "String",
            "data_media_id": "String",
            "data_media_hash": "String",
            "data_media_type": "String",
            "data_title": "String",
            "data_episode_count": "String"
        },
        "..."
    ]"""

    def __init__(self, document: Union[str, SelectorList, Selector]) -> None:
        self._doc = Selector(document) if isinstance(document, str) else document

    def _split_doc(self, value: Selector) -> SelectorList:
        value1 = value.css(".serial-translations-box > select > option")
        return value1

    def _parse_value(self, value: Selector) -> str:
        value1 = value.attrib["value"]
        return value1

    def _parse_data_id(self, value: Selector) -> str:
        value1 = value.attrib["data-id"]
        return value1

    def _parse_data_translation_type(self, value: Selector) -> str:
        value1 = value.attrib["data-translation-type"]
        return value1

    def _parse_data_media_id(self, value: Selector) -> str:
        value1 = value.attrib["data-media-id"]
        return value1

    def _parse_data_media_hash(self, value: Selector) -> str:
        value1 = value.attrib["data-media-hash"]
        return value1

    def _parse_data_media_type(self, value: Selector) -> str:
        value1 = value.attrib["data-media-type"]
        return value1

    def _parse_data_title(self, value: Selector) -> str:
        value1 = value.attrib["data-title"]
        return value1

    def _parse_data_episode_count(self, value: Selector) -> str:
        value1 = value.attrib["data-episode-count"]
        return value1

    def parse(self) -> List[T_SourceKodikTranslationsView]:
        return [
            {
                "value": self._parse_value(e),
                "data_id": self._parse_data_id(e),
                "data_translation_type": self._parse_data_translation_type(e),
                "data_media_id": self._parse_data_media_id(e),
                "data_media_hash": self._parse_data_media_hash(e),
                "data_media_type": self._parse_data_media_type(e),
                "data_title": self._parse_data_title(e),
                "data_episode_count": self._parse_data_episode_count(e),
            }
            for e in self._split_doc(self._doc)
        ]


class SourceKodikSerialPage:
    """extract videos from kodik serial path. this values helps create video player link

    Example:
         SERIAL, bot SERIA path====vvvvv
        - GET 'https://kodik.info/serial/58496/d2a8737db86989de0863bac5c14ce18b/720p?translations=false&only_translations=1895'


    {
        "episodes": [
            {
                "value": "String",
                "data_id": "String",
                "data_hash": "String",
                "data_title": "String"
            },
            "..."
        ],
        "translations": [
            {
                "value": "String",
                "data_id": "String",
                "data_translation_type": "String",
                "data_media_id": "String",
                "data_media_hash": "String",
                "data_media_type": "String",
                "data_title": "String",
                "data_episode_count": "String"
            },
            "..."
        ]
    }"""

    def __init__(self, document: Union[str, SelectorList, Selector]) -> None:
        self._doc = Selector(document) if isinstance(document, str) else document

    def _parse_episodes(self, value: Selector) -> List[T_SourceKodikEpisodesView]:
        value1 = SourceKodikEpisodesView(value).parse()
        return value1

    def _parse_translations(self, value: Selector) -> List[T_SourceKodikTranslationsView]:
        value1 = SourceKodikTranslationsView(value).parse()
        return value1

    def parse(self) -> T_SourceKodikSerialPage:
        return {"episodes": self._parse_episodes(self._doc), "translations": self._parse_translations(self._doc)}
