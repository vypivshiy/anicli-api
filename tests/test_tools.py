from anicli_api.player.base import Video
from anicli_api.tools import generate_asyncio_playlist, generate_playlist
from anicli_api.tools.m3u import generate_playlist_from_async_sources, generate_playlist_from_sources

RESULT = "#EXTM3U\n\n#EXTINF:0,Episode 1\n1.mp4\n\n#EXTINF:0,Episode 2\n2.mp4\n\n#EXTINF:0,Episode 3\n3.mp4"
RESULT_WITH_NAMES = "#EXTM3U\n\n#EXTINF:0,v1\n1.mp4\n\n#EXTINF:0,v2\n2.mp4\n\n#EXTINF:0,v3\n3.mp4"


def test_generate_m3u():
    assert generate_playlist(target=["1.mp4", "2.mp4", "3.mp4"]) == RESULT
    assert generate_playlist(target=["1.mp4", "2.mp4", "3.mp4"], names=["v1", "v2", "v3"]) == RESULT_WITH_NAMES


async def test_async_generate_m3u():
    assert (await generate_asyncio_playlist(target=["1.mp4", "2.mp4", "3.mp4"])) == RESULT
    assert (
        await generate_asyncio_playlist(target=["1.mp4", "2.mp4", "3.mp4"], names=["v1", "v2", "v3"])
    ) == RESULT_WITH_NAMES


def test_generate_m3u_from_sources_accumulates_one_video_per_source():
    class Source:
        def __init__(self, videos):
            self.videos = videos

        def get_videos(self):
            return list(self.videos)

    names = ["first", "second"]
    result = generate_playlist_from_sources(
        [
            Source([Video(type="mp4", quality=480, url="1-480.mp4"), Video(type="mp4", quality=720, url="1.mp4")]),
            Source([Video(type="mp4", quality=720, url="2.mp4")]),
        ],
        names=names,
        quality=720,
    )

    assert result == "#EXTM3U\n\n#EXTINF:0,first\n1.mp4\n\n#EXTINF:0,second\n2.mp4"
    assert names == ["first", "second"]


async def test_generate_async_m3u_from_sources_accumulates_one_video_per_source():
    class Source:
        def __init__(self, videos):
            self.videos = videos

        async def a_get_videos(self):
            return list(self.videos)

    result = await generate_playlist_from_async_sources(
        [
            Source([Video(type="mp4", quality=720, url="1.mp4")]),
            Source([Video(type="mp4", quality=720, url="2.mp4")]),
        ],
        quality=720,
    )

    assert result == "#EXTM3U\n\n#EXTINF:0,Episode 1\n1.mp4\n\n#EXTINF:0,Episode 2\n2.mp4"


def test_generate_empty_m3u():
    assert generate_playlist([]) == "#EXTM3U"
