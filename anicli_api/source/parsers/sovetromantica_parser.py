# Auto generated code by ssc_gen
# WARNING: Any manual changes made to this file will be lost when this
# is run again. Do not edit this file unless you know what you are doing.

from typing import List, TypedDict

from .baseStruct import BaseParser


T_OngoingPage = TypedDict("T_OngoingPage", {"title": str, "thumbnail": str, "alt_title": str, "url": str})

T_SearchPage = TypedDict("T_SearchPage", {"title": str, "thumbnail": str, "alt_title": str, "url": str})

T_EpisodeView = TypedDict("T_EpisodeView", {"url": str, "thumbnail": str, "title": str})

T_AnimePage = TypedDict(
    "T_AnimePage",
    {"title": str, "description": str, "thumbnail": str, "video_url": str, "episodes": List["T_EpisodeView"]},
)


class OngoingPage(BaseParser):
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
    ]
    """

    def parse(self) -> List["T_OngoingPage"]:
        return self._run_parse()

    def _run_parse(self) -> List["T_OngoingPage"]:
        return [
            T_OngoingPage(
                **{
                    "title": self._parse_title(el),
                    "thumbnail": self._parse_thumbnail(el),
                    "alt_title": self._parse_alt_title(el),
                    "url": self._parse_url(el),
                }
            )
            for el in self._part_document(self.__selector__)
        ]

    def _part_document(self, el):
        var = self._css_all(el, ".anime--block__desu")
        return var

    def _parse_title(self, el):
        var = self._css_all(el, ".anime--block__name > span")
        var_1 = var[-1]
        var_2 = self._attr_text(var_1)
        return var_2

    def _parse_thumbnail(self, el):
        var = self._css(el, ".anime--poster--loading > img")
        var_1 = self._attr(var, "src")
        return var_1

    def _parse_alt_title(self, el):
        var = self._css(el, ".anime--block__name > span")
        var_1 = self._attr_text(var)
        return var_1

    def _parse_url(self, el):
        var = self._css(el, ".anime--block__desu a")
        var_1 = self._attr(var, "href")
        return var_1


class SearchPage(BaseParser):
    """
        Get all search results by query

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
    ]
    """

    def parse(self) -> List["T_SearchPage"]:
        return self._run_parse()

    def _run_parse(self) -> List["T_SearchPage"]:
        return [
            T_SearchPage(
                **{
                    "title": self._parse_title(el),
                    "thumbnail": self._parse_thumbnail(el),
                    "alt_title": self._parse_alt_title(el),
                    "url": self._parse_url(el),
                }
            )
            for el in self._part_document(self.__selector__)
        ]

    def _part_document(self, el):
        var = self._css_all(el, ".anime--block__desu")
        return var

    def _parse_title(self, el):
        var = self._css_all(el, ".anime--block__name > span")
        var_1 = var[-1]
        var_2 = self._attr_text(var_1)
        return var_2

    def _parse_thumbnail(self, el):
        var = self._css(el, ".anime--poster--loading > img")
        var_1 = self._attr(var, "src")
        return var_1

    def _parse_alt_title(self, el):
        var = self._css(el, ".anime--block__name > span")
        var_1 = self._attr_text(var)
        return var_1

    def _parse_url(self, el):
        var = self._css(el, ".anime--block__desu a")
        var_1 = self._attr(var, "href")
        return var_1


class EpisodeView(BaseParser):
    """
        WARNING!

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
    ]
    """

    def parse(self) -> List["T_EpisodeView"]:
        return self._run_parse()

    def _run_parse(self) -> List["T_EpisodeView"]:
        return [
            T_EpisodeView(
                **{
                    "url": self._parse_url(el),
                    "thumbnail": self._parse_thumbnail(el),
                    "title": self._parse_title(el),
                }
            )
            for el in self._part_document(self.__selector__)
        ]

    def _part_document(self, el):
        var = self._css_all(el, ".episodes-slick_item")
        return var

    def _parse_url(self, el):
        var = self._css(el, "a")
        var_1 = self._attr(var, "href")
        var_2 = self._str_format(var_1, "https://sovetromantica.com{}")
        return var_2

    def _parse_thumbnail(self, el):
        var = self._css(el, "img")
        var_1 = self._attr(var, "src")
        return var_1

    def _parse_title(self, el):
        var = self._css(el, "img")
        var_1 = self._attr(var, "alt")
        return var_1


class AnimePage(BaseParser):
    """
        Anime page information

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
    }
    """

    def parse(self) -> T_AnimePage:
        return self._run_parse()

    def _run_parse(self) -> T_AnimePage:
        return T_AnimePage(
            **{
                "title": self._parse_title(self.__selector__),
                "description": self._parse_description(self.__selector__),
                "thumbnail": self._parse_thumbnail(self.__selector__),
                "video_url": self._parse_video_url(self.__selector__),
                "episodes": self._parse_episodes(self.__selector__),
            }
        )

    def _parse_title(self, el):
        var = self._css(el, ".anime-name .block--container")
        var_1 = self._attr_text(var)
        return var_1

    def _parse_description(self, el):
        try:
            var = self._css(el, "#js-description_open-full")
            var_1 = self._attr_text(var)
            return var_1
        except Exception:
            return None

    def _parse_thumbnail(self, el):
        var = self._css(el, "#poster")
        var_1 = self._attr(var, "src")
        var_2 = self._str_format(var_1, "https://sovetromantica.com{}")
        return var_2

    def _parse_video_url(self, el):
        try:
            var = self._attr_raw(el)
            var_1 = self._re_match(var, '"file":"([^>]+\\.m3u8)"\\s*}', 1)
            return var_1
        except Exception:
            return None

    def _parse_episodes(self, el):
        var = self._nested_parser(el, EpisodeView)
        return var
