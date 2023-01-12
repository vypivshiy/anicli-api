import httpx
import pytest

from anicli_api.decoders import CsstOnline

RAW_RESPONSE = """file:"[360p]https://www.secvideo1.online/get_file/10/hash0/1337/123/456_360p.mp4/,[720p]https://www.secvideo1.online/get_file/10/hash1/1337/123/456_720p.mp4/,[1080p]https://www.secvideo1.online/get_file/10/hash2/1337/123/456.mp4/","""


def mock_transport():
    def handler(_):
        return httpx.Response(200, text=RAW_RESPONSE)

    transport = httpx.MockTransport(handler)
    return transport


def test_cmp_sibnet():
    assert "https://google.com" != CsstOnline()
    assert "https://csst.online/embed/1337/" == CsstOnline()


def test_parse():
    result = CsstOnline.parse("https://csst.online/embed/1337/", transport=mock_transport())
    assert result[0].dict() == {
        "type": "mp4",
        "quality": 360,
        "url": "https://www.secvideo1.online/get_file/10/hash0/1337/123/456_360p.mp4",
        "extra_headers": {},
    }


@pytest.mark.asyncio
async def test_async_parse():
    result = await CsstOnline.async_parse(
        "https://csst.online/embed/1337/", transport=mock_transport()
    )
    assert result[0].dict() == {
        "type": "mp4",
        "quality": 360,
        "url": "https://www.secvideo1.online/get_file/10/hash0/1337/123/456_360p.mp4",
        "extra_headers": {},
    }
