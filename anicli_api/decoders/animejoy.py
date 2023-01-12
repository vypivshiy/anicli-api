import re
from typing import List

from anicli_api.base_decoder import BaseDecoder, MetaVideo


class AnimeJoyDecoder(BaseDecoder):
    URL_RULE = re.compile(r"animejoy\.ru/player")

    @classmethod
    def parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        # not formet url like
        # """https://animejoy.ru/player/playerjs.html?file=[1080p]https://noda3.cdnjoy.site/Tsunlise/KAZOKU/01-1080.mp4,[360p]https://noda3.cdnjoy.site/Tsunlise/KAZOKU/01-360.mp4"""
        cls._validate_url(url)
        objects: List[MetaVideo] = []
        for match in re.finditer(r"\[(?P<quality>\d+)p](?P<url>https?://.*?\.mp4)", url):
            content = match.groupdict()
            objects.append(MetaVideo(type="mp4", quality=content["quality"], url=content["url"]))  # type: ignore
        return objects

    @classmethod
    async def async_parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        cls._validate_url(url)
        objects: List[MetaVideo] = []
        for match in re.finditer(r"\[(?P<quality>\d+)p](?P<url>https?://.*?\.mp4)", url):
            content = match.groupdict()
            objects.append(MetaVideo(type="mp4", quality=content["quality"], url=content["url"]))  # type: ignore
        return objects
