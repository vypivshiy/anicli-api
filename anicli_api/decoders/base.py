"""Decoders class for video hostings

Структура Декодера:

```py

class DecoderName(BaseDecoder):
    URL_RULE: re.Pattern  # регулярное выраженье для валидации ссылки
    def parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        # парсер с применением синхронных запросов

    async def async_parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        '''парсер с применением асинхронных запросов'''

```

MetaVideo - датакласс со значениями ссылок
    type - тип файла (m3u8, mpd, mp4
    quality - разрешение видео
    url - **прямая ссылка на видео**
    extra_headers - ключи для headers, если видеопоток без них не работает
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Union

from anicli_api._http import BaseHTTPAsync, BaseHTTPSync

ALL_QUALITIES = (144, 240, 360, 480, 720, 1080)


@dataclass
class MetaVideo:
    type: Literal["mp4", "m3u8", "mpd"]
    quality: Literal[144, 240, 360, 480, 720, 1080]
    url: str
    extra_headers: Optional[Dict] = field(default_factory=dict)

    def dict(self) -> Dict[str, Any]:
        return self.__dict__


class ABCDecoder(ABC):
    def __init__(self, **kwargs):
        if kwargs:
            self.http = BaseHTTPSync(**kwargs)
            self.a_http = BaseHTTPAsync(**kwargs)
        else:
            self.http = BaseHTTPSync()
            self.a_http = BaseHTTPAsync()

    @classmethod
    @abstractmethod
    def parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        ...

    @classmethod
    @abstractmethod
    async def async_parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        ...

    @classmethod
    @abstractmethod
    def _compare_url(cls, url: str) -> bool:
        ...

    def __eq__(self, other: str):  # type: ignore
        """compare class instance with url string"""
        return self._compare_url(other)


class BaseDecoder(ABCDecoder):
    URL_RULE: Union[str, re.Pattern]

    @classmethod
    def _validate_url(cls, url: str):
        if url != cls():
            raise TypeError(f"Incorrect decoder. {url} if not {cls.__class__.__name__}")

    @classmethod
    @abstractmethod
    def parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        ...

    @classmethod
    @abstractmethod
    async def async_parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        ...

    @classmethod
    def _compare_url(cls, url: str) -> bool:
        return (
            bool(cls.URL_RULE.search(url))
            if isinstance(cls.URL_RULE, re.Pattern)
            else bool(re.search(cls.URL_RULE, url))
        )
