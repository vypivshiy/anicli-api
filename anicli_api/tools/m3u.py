"""simple M3U playlist generators"""

from typing import Optional, Union, cast

from anicli_api.typing import NamedTuple, Sequence
from anicli_api.base import BaseSource
from anicli_api.player.base import Video

_M3U_HEADER = "#EXTM3U"
_M3U_ITEM = "#EXTINF:0,{name}\n{url}"

__all__ = ["M3UPlaylistItem", "Playlist", "generate_playlist", "generate_asyncio_playlist"]


class M3UPlaylistItem(NamedTuple):
    url: str
    name: Optional[str] = None

    def __str__(self):
        return _M3U_ITEM.format(name=self.name, url=self.url)


class Playlist:
    def __init__(self, playlist: Sequence[M3UPlaylistItem]):
        self._playlist = playlist

    @classmethod
    def from_urls(cls, urls: Sequence[str], names: Optional[Sequence[str]] = None):
        if not names:
            names = [f"Episode {i + 1}" for i in range(len(urls))]

        playlists: list["M3UPlaylistItem"] = []

        for url, name in zip(urls, names):
            playlists.append(M3UPlaylistItem(url=url, name=name))
        return cls(playlists).generate()

    @classmethod
    def from_videos(cls, videos: Sequence["Video"], names: Optional[Sequence[str]]) -> str:
        if not names:
            names = [f"Episode {i + 1}" for i in range(len(videos))]
        playlists: list["M3UPlaylistItem"] = []
        for video, name in zip(videos, names):
            playlists.append(M3UPlaylistItem(url=video.url, name=name))
        return cls(playlists).generate()

    def generate(self) -> str:
        raw_playlist = _M3U_HEADER

        for video in self._playlist:
            raw_playlist += "\n\n"
            raw_playlist += str(video)

        return raw_playlist


def generate_playlist_from_urls(videos: Sequence[Union[str, Video]], names: Optional[Sequence[str]] = None) -> str:
    if not videos:
        return _M3U_HEADER
    if isinstance(videos[0], Video):
        urls = [v.url for v in cast(Sequence[Video], videos)]
    else:
        urls = list(cast(Sequence[str], videos))
    if not names:
        names = [f"Episode {i + 1}" for i in range(len(urls))]
    return Playlist.from_urls(urls=urls, names=names)


def _get_preferred_video_quality(videos: Sequence[Video], quality: int) -> Video:
    return sorted(videos, key=lambda x: abs(x.quality - quality))[0]


def generate_playlist_from_sources(
    sources: Sequence["BaseSource"], names: Optional[Sequence[str]] = None, quality: int = 1080
) -> str:
    selected_videos: list[Video] = []
    selected_names: Optional[list[str]] = [] if names is not None else None

    for i, source in enumerate(sources):
        print(f"Parse source: {i + 1}/{len(sources)}", end="\r")
        available_videos = source.get_videos()
        if not available_videos:
            continue
        selected_videos.append(_get_preferred_video_quality(list(available_videos), quality))
        if names is not None:
            assert selected_names is not None
            selected_names.append(names[i] if i < len(names) else f"Episode {i + 1}")

    return Playlist.from_videos(selected_videos, selected_names)


async def generate_playlist_from_async_sources(
    target: Sequence["BaseSource"], names: Optional[Sequence[str]] = None, quality: int = 1080
) -> str:
    """generate m3u playlist structure IN ASYNCIO MODE

    :param target: sequence of source, video or direct url links
    :param names: names for urls. If not passed, default naming `Episode {i}`
    :param quality: preferred near video quality (if passed Source object)
    """
    selected_videos: list[Video] = []
    selected_names: Optional[list[str]] = [] if names is not None else None

    for i, source in enumerate(target):
        print(f"Parse source: {i + 1}/{len(target)}", end="\r")
        available_videos = await source.a_get_videos()
        if not available_videos:
            continue
        selected_videos.append(_get_preferred_video_quality(list(available_videos), quality))
        if names is not None:
            assert selected_names is not None
            selected_names.append(names[i] if i < len(names) else f"Episode {i + 1}")

    return Playlist.from_videos(selected_videos, selected_names)


def generate_playlist(
    target: Sequence[Union[BaseSource, Video, str]],
    names: Optional[Sequence[str]] = None,
    quality: int = 1080,
) -> str:
    """generate m3u playlist structure

    :param target: sequence of source, video or direct url links
    :param names: names for urls. If not passed, default naming `Episode {i}`
    :param quality: preferred near video quality (if passed Source object)
    """
    if not target:
        return _M3U_HEADER
    if isinstance(target[0], BaseSource):
        return generate_playlist_from_sources(cast(Sequence[BaseSource], target), names, quality=quality)
    elif isinstance(target[0], Video):
        return Playlist.from_videos(cast(Sequence[Video], target), names)
    elif isinstance(target[0], str):
        return Playlist.from_urls(cast(Sequence[str], target), names)


async def generate_asyncio_playlist(
    target: Sequence[Union[BaseSource, Video, str]],
    names: Optional[Sequence[str]] = None,
    quality: int = 1080,
) -> str:
    if not target:
        return _M3U_HEADER
    if isinstance(target[0], BaseSource):
        return await generate_playlist_from_async_sources(cast(Sequence[BaseSource], target), names, quality=quality)
    elif isinstance(target[0], Video):
        return Playlist.from_videos(cast(Sequence[Video], target), names)
    elif isinstance(target[0], str):
        return Playlist.from_urls(cast(Sequence[str], target), names)


if __name__ == "__main__":
    urls_ = [
        "1.mp4",
        "2.mp4",
        "3.mp4",
        "4.mp4",
        "5.mp4",
    ]
    names_ = [
        "name_1",
        "name_2",
        "name_3",
        "name_4",
        "name_5",
    ]
    print(generate_playlist(urls_, names_, 1080))
