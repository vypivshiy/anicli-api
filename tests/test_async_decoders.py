import pytest

from tests import mock_kodik, mock_aniboom  # type: ignore
from anicli_api.decoders import BaseDecoder


@pytest.mark.asyncio
async def test_async_parse_kodik(mock_kodik):
    result = await mock_kodik.async_parse("https://kodikfake.fake/seria/00/foobar/100p")
    assert result == {'360': 'https://test_360.mp4', '480': 'https://test_480.mp4', '720': 'https://test_720.mp4'}


@pytest.mark.asyncio
async def test_async_parse_aniboom(mock_aniboom):
    result = await mock_aniboom.async_parse("https://aniboom.one/embed/fake_aniboom_la-la-la")
    assert result == {'m3u8': {
        '360': 'https://kekistan.cdn-fakeaniboom.com/jo/abcdefg123/media_0.m3u8',
        '480': 'https://kekistan.cdn-fakeaniboom.com/jo/abcdefg123/media_2.m3u8',
        '720': 'https://kekistan.cdn-fakeaniboom.com/jo/abcdefg123/media_4.m3u8',
        '1080': 'https://kekistan.cdn-fakeaniboom.com/jo/abcdefg123/media_6.m3u8'},
        'mpd': 'https://kekistan.cdn-fakeaniboom.com/jo/abcdef123/111hash.mpd'}


@pytest.mark.asyncio
async def test_async_custom_decoder():
    class MyDecoder(BaseDecoder):

        @classmethod
        def parse(cls, url: str):
            ...

        @classmethod
        async def async_parse(cls, url: str):
            return "test123"

        def __eq__(self, other: str):  # type: ignore
            return "foobar" in other

    assert "foobar" == MyDecoder()
    assert "bazfoo" != MyDecoder()
    assert (await MyDecoder.async_parse("aaaaa")) == "test123"
