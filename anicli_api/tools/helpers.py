from typing import TYPE_CHECKING, List, Callable, Generator, Tuple, AsyncGenerator
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from anicli_api.base import Video, BaseEpisode, BaseAnime, BaseSource


def get_video_by_quality(videos: List["Video"], quality: int) -> "Video":
    """get video by quality from collection
    if current quality not exist - get closest

    Example:

    >>> ex_videos = [Video('m3u8', quality=1080, url=...), Video('m3u8', quality=720), Video('m3u8', quality=480)]
    >>> get_video_by_quality(ex_videos, 1080) # Video('m3u8', quality=1080, url=...)
    >>> get_video_by_quality(ex_videos, 2000) # Video('m3u8', quality=1080, url=...)
    >>> get_video_by_quality(ex_videos, 720) # Video('m3u8', quality=720, url=...)
    >>> get_video_by_quality(ex_videos, 144) # Video('m3u8', quality=480, url=...)
    """
    if not videos:
        raise TypeError("No videos specified")

    closest_video = min(videos, key=lambda video: abs(video.quality - quality))

    return closest_video


def _source_hash(source: "BaseSource") -> int:
    """default hash function helper for build playlist"""
    return hash((source.title, urlsplit(source.url).netloc))


def title_callback(anime: "BaseAnime", episode: "BaseEpisode", source: "BaseSource") -> str:
    """default title callback function"""
    return f"{episode.num} {episode.title} ({source.title}) - {anime.title}"


def video_picker_iterator(
    *,
    start_source: "BaseSource",
    start_video: "Video",
    anime: "BaseAnime",
    episodes: List["BaseEpisode"],
    title_cb: Callable[["BaseAnime", "BaseEpisode", "BaseSource"], str] = title_callback,
) -> Generator[Tuple["Video", str], None, None]:
    """video picker generator. compare by start_source hash function

    useful, for implementation playlists features.

    :param anime: Anime object
    :param episodes: list of Episode objects
    :param start_source: start Source for compare next iterations
    :param start_video: start Video for compare next iterations
    :param title_cb: callback for generate string title
    :return: iterator with Video object and title

    example build playlist:

    >>> from anicli_api.source.animego import Extractor
    >>>
    >>> an = Extractor().search('lain')[0].get_anime()
    >>> eps = an.get_episodes()
    >>> s = eps[0].get_source()[0]
    >>> vid = s.get_videos()[-1]
    >>> playlist = [(v, name) for v, name in video_picker_iterator(start_source=s, start_video=vid, anime=an, episodes=eps)]
    """
    base_source_hash = _source_hash(start_source)

    for episode in episodes:
        sources = episode.get_sources()
        for source in sources:
            if base_source_hash == _source_hash(source):
                break
        else:
            # not founded by source hash - exit from main loop
            break

        videos = source.get_videos()
        for video in videos:
            if video == start_video:
                title = title_cb(anime, episode, start_source)
                yield video, title
                break


async def async_video_picker_iterator(
    *,
    anime: "BaseAnime",
    episodes: List["BaseEpisode"],
    start_source: "BaseSource",
    start_video: "Video",
    title_cb: Callable[["BaseAnime", "BaseEpisode", "BaseSource"], str] = title_callback,
) -> AsyncGenerator[Tuple["Video", str], None]:
    """video picker generator. compare by start_source hash function

    useful, for implementation playlists features.

    :param anime: Anime object
    :param episodes: list of Episode objects
    :param start_source: start Source for compare next iterations
    :param start_video: start Video for compare next iterations
    :param title_cb: callback for generate string title
    :return: iterator with Video object and title
    """
    base_source_hash = _source_hash(start_source)

    for episode in episodes:
        sources = await episode.a_get_sources()
        for source in sources:
            if base_source_hash == _source_hash(source):
                break
        else:
            # not founded by source hash - exit from main loop
            break

        videos = await source.a_get_videos()
        for video in videos:
            if video == start_video:
                title = title_cb(anime, episode, start_source)
                yield video, title
                break
