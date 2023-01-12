import httpx
import pytest

from anicli_api.decoders import OkRu

RAW_RESPONSE = ""","ondemandHls":"https://vd300.mycdn.me/expires/0/clientType/0/srcIp/192.168.0.1/type/2/mid/0/id/1/ms/127.0.0.1/srcAg/CHROME_ANDROID/oq/0/ct/28/sig/foo/ondemand/hls2_123.abc.m3u8","ondemandDash":"https://vd300.mycdn.me/expires/0/clientType/0/srcIp/192.168.0.1/type/2/mid/0/id/1/ms/127.0.0.1/srcAg/CHROME_ANDROID/oq/0/ct/29/sig/foo/ondemand/dash2_123.abc.mpd","""


def mock_transport():
    def handler(_):
        return httpx.Response(200, text=RAW_RESPONSE)

    transport = httpx.MockTransport(handler)
    return transport


def test_cmp():
    assert "https://google.com" != OkRu()
    assert "https://ok.ru/videoembed/123" == OkRu()


def test_parse():
    result = OkRu.parse("https://ok.ru/videoembed/123", transport=mock_transport())
    assert result[0].dict() == {
        "extra_headers": {},
        "quality": 1080,
        "type": "m3u8",
        "url": "https://vd300.mycdn.me/expires/0/clientType/0/srcIp/192.168.0.1/type/2/mid/0/id/1/ms/127.0.0.1/srcAg/CHROME_ANDROID/oq/0/ct/28/sig/foo/ondemand/hls2_123.abc.m3u8",
    }


@pytest.mark.asyncio
async def test_async_parse():
    result = await OkRu.async_parse("https://ok.ru/videoembed/123", transport=mock_transport())
    assert result[0].dict() == {
        "extra_headers": {},
        "quality": 1080,
        "type": "m3u8",
        "url": "https://vd300.mycdn.me/expires/0/clientType/0/srcIp/192.168.0.1/type/2/mid/0/id/1/ms/127.0.0.1/srcAg/CHROME_ANDROID/oq/0/ct/28/sig/foo/ondemand/hls2_123.abc.m3u8",
    }
