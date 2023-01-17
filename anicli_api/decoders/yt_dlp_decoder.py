import re
import warnings
from typing import List

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from anicli_api.base_decoder import BaseDecoder, MetaVideo


class YtDlpAdapter(BaseDecoder):
    URL_RULE = re.compile(".*")

    @classmethod
    def parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        warnings.warn(
            "This experimental decoder based on `yt_dlp` project and not support asyncio",
            stacklevel=2,
        )
        try:
            with YoutubeDL() as ydl:
                info = ydl.extract_info(url, download=False)
                objects = []
                for metadata in info["formats"]:
                    quality = metadata["resolution"].replace("p", "").split("x")[-1]
                    print(metadata["url"], metadata["resolution"])
                    quality = int(quality) if quality.isdigit() else 0
                    if metadata["video_ext"] == "none" or metadata["video_ext"].lower() == "none":
                        metadata["video_ext"] = "audio"
                    objects.append(
                        MetaVideo(
                            type=metadata["video_ext"],
                            url=metadata["url"],
                            extra_headers=metadata["http_headers"],
                            quality=quality,  # type: ignore
                        )
                    )  # type: ignore
                return objects
        except DownloadError as e:
            warnings.warn(e.msg)
            raise DownloadError from e

    @classmethod
    async def async_parse(cls, url: str, **kwargs) -> List[MetaVideo]:
        return cls.parse(url)
