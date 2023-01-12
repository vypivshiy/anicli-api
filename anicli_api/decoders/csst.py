import re
from typing import List

from anicli_api.base_decoder import BaseDecoder, MetaVideo


class CsstOnline(BaseDecoder):
    URL_RULE = re.compile(r"csst\.online/embed/\d+")

    @staticmethod
    def _response_to_metavideo(response: str) -> List["MetaVideo"]:
        objects: List[MetaVideo] = []
        seen = set()
        for match in re.finditer(
            r"\[(?P<quality>\d+)p\](?P<url>https?://[\w/\.]+.\w{3,5})/", response
        ):
            if match and match.groupdict()["url"] not in seen:
                video_meta = match.groupdict()
                seen.add(video_meta["url"])
                objects.append(
                    MetaVideo(
                        type="mp4",
                        quality=int(video_meta["quality"]),  # type: ignore
                        url=video_meta["url"],
                    )
                )
        return objects

    @classmethod
    def parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        cls._validate_url(url)
        cls_ = cls(**kwargs)

        with cls_.http as session:
            response = session.get(url).text
            return cls_._response_to_metavideo(response)

    @classmethod
    async def async_parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        cls._validate_url(url)
        cls_ = cls(**kwargs)

        async with cls_.a_http as session:
            response = await session.get(url)
            response = response.text
            return cls_._response_to_metavideo(response)
