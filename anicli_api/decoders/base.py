from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any

from anicli_api._http import BaseHTTPAsync, BaseHTTPSync
from anicli_api.base import MetaVideo


class ABCDecoder(ABC):
    @abstractmethod
    def parse(self, url: str, **kwargs) -> list[MetaVideo]:
        ...

    @abstractmethod
    async def a_parse(self, url: str, **kwargs) -> list[MetaVideo]:
        ...

    @classmethod
    @abstractmethod
    def _compare_url(cls, url: str) -> bool:
        ...


class BaseDecoder(ABCDecoder):
    """Abstract decoder class

    - URL_RULE - regular expression to validate link

    - cls.parse - get videos synchronously

    - cls.async_parse - get videos asynchronously
    """

    # validate regex pattern url
    URL_FILTER: str | re.Pattern
    # default http config like cookies, tokens, headers etc
    DEFAULT_HTTP_CONFIG: dict[str, Any] = {}

    # Runtime checkers
    #                           |  pattern  | assert value
    RUNTIME_CHECKERS: list[tuple[re.Pattern | str, bool]] = []

    def __init__(self, **httpx_kwargs):
        httpx_kwargs.update(self.DEFAULT_HTTP_CONFIG)
        self.http = BaseHTTPSync(**httpx_kwargs)
        self.a_http = BaseHTTPAsync(**httpx_kwargs)

    @classmethod
    def _validate_url(cls, url: str):
        if url != cls():
            raise TypeError(
                f"Incorrect decoder. {url} if not for `{cls.__class__.__name__}` decoder"
            )

    def _runtime_check(self, response: str) -> None:
        for case in self.RUNTIME_CHECKERS:
            pattern, result = case
            if isinstance(pattern, str):
                pattern = re.compile(pattern)
            if flag := bool(pattern.search(response)) == result:
                raise ValueError(
                    f"pattern `{pattern.pattern}` match group in 'response' and return `{flag}`"
                )

    @abstractmethod
    def parse(self, url: str, **kwargs) -> list[MetaVideo]:
        """get video synchronously

        :param url: video url
        :param kwargs: optional params for httpx.Client instance
        :return: List of MetaVideo dataclasses
        """
        ...

    @abstractmethod
    async def a_parse(self, url: str, **kwargs) -> list[MetaVideo]:
        """get video asynchronously

        :param url: video url
        :param kwargs: optional params for httpx.AsyncClient instance
        :return: List of MetaVideo dataclasses
        """
        ...

    @classmethod
    def _compare_url(cls, url: str) -> bool:
        """
        :param url: link
        :return: True, if link valid else False
        """
        return (
            bool(cls.URL_FILTER.search(url))
            if isinstance(cls.URL_FILTER, re.Pattern)
            else bool(re.search(cls.URL_FILTER, url))
        )

    def __eq__(self, other: str):  # type: ignore
        """compare class instance with url string"""
        return self._compare_url(other)
