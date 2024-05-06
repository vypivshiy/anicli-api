import pytest

from anicli_api.tools import generate_asyncio_playlist, generate_playlist

RESULT = "#EXTM3U\n\n#EXTINF:0,Episode 1\n1.mp4\n\n#EXTINF:0,Episode 2\n2.mp4\n\n#EXTINF:0,Episode 3\n3.mp4"
RESULT_WITH_NAMES = "#EXTM3U\n\n#EXTINF:0,v1\n1.mp4\n\n#EXTINF:0,v2\n2.mp4\n\n#EXTINF:0,v3\n3.mp4"


def test_generate_m3u():
    assert generate_playlist(target=["1.mp4", "2.mp4", "3.mp4"]) == RESULT
    assert generate_playlist(target=["1.mp4", "2.mp4", "3.mp4"], names=["v1", "v2", "v3"]) == RESULT_WITH_NAMES


@pytest.mark.asyncio(scope="session")
async def test_async_generate_m3u():
    assert (await generate_asyncio_playlist(target=["1.mp4", "2.mp4", "3.mp4"])) == RESULT
    assert (
        await generate_asyncio_playlist(target=["1.mp4", "2.mp4", "3.mp4"], names=["v1", "v2", "v3"])
    ) == RESULT_WITH_NAMES
