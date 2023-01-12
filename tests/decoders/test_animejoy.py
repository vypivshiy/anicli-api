import pytest

from anicli_api.decoders import AnimeJoyDecoder

TEST_URL = """https://animejoy.ru/player/playerjs.html?file=[1080p]https://noda3.cdnjoy.site/Tsunlise/KAZOKU/01-1080.mp4,[360p]https://noda3.cdnjoy.site/Tsunlise/KAZOKU/01-360.mp4"""


def test_cmp():
    assert "https://google.com" != AnimeJoyDecoder()
    assert "https://animejoy.ru/player/aaaa" == AnimeJoyDecoder()


def test_parse():
    result = AnimeJoyDecoder.parse(TEST_URL)
    assert result[0].dict() == {
        "extra_headers": {},
        "quality": "1080",
        "type": "mp4",
        "url": "https://noda3.cdnjoy.site/Tsunlise/KAZOKU/01-1080.mp4",
    }


@pytest.mark.asyncio
async def test_async_parse():
    result = await AnimeJoyDecoder.async_parse(TEST_URL)
    assert result[0].dict() == {
        "extra_headers": {},
        "quality": "1080",
        "type": "mp4",
        "url": "https://noda3.cdnjoy.site/Tsunlise/KAZOKU/01-1080.mp4",
    }
