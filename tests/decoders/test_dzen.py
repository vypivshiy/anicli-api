import httpx
import pytest

from anicli_api.decoders import Dzen

RAW_RESPONSE = ""","url":"https://cdn.dzen.ru/vod/zen-vod/vod-content/abc/1-2-3-4-5/kaltura/desc_foobar/aaa/ysign1=null,abcID=0,from=zen,pfx,region=0000,sfx,ts=63cd1709/manifest.mpd","title":"Tsundere-01KAZOKU"},{"thumbnail":"https://avatars.dzeninfra.ru/get-zen-vh/5413359/2a00000185909994edfa9566e6abd43fb684/orig","options":[],"url":"https://cdn.dzen.ru/vod/zen-vod/vod-content/a/1-2-3-4-5/kaltura/desc_foobar/aaa/ysign1=null,abcID=0,from=zen,pfx,region=0000,sfx,ts=63cd1709/master.m3u8","title":"Tsundere-01KAZOKU"}],"duration":1524,"audio_source_url":"https://zen-audio-track.s3.dzeninfra.ru/audio-source/audio_fakeaudio.mp4","""


def mock_transport():
    def handler(_):
        return httpx.Response(200, text=RAW_RESPONSE)

    transport = httpx.MockTransport(handler)
    return transport


def test_cmp():
    assert "https://google.com" != Dzen()
    assert "https://dzen.ru/embed/leet1337?fake_request" == Dzen()


def test_parse():
    result = Dzen.parse("https://dzen.ru/embed/leet1337?fake_request", transport=mock_transport())
    assert result[0].dict() == {
        "extra_headers": {},
        "quality": 1080,
        "type": "mpd",
        "url": "https://cdn.dzen.ru/vod/zen-vod/vod-content/abc/1-2-3-4-5/kaltura/desc_foobar/aaa/ysign1=null,abcID=0,from=zen,pfx,region=0000,sfx,ts=63cd1709/manifest.mpd",
    }


@pytest.mark.asyncio
async def test_async_parse():
    result = await Dzen.async_parse(
        "https://dzen.ru/embed/leet1337?fake_request", transport=mock_transport()
    )
    assert result[0].dict() == {
        "extra_headers": {},
        "quality": 1080,
        "type": "mpd",
        "url": "https://cdn.dzen.ru/vod/zen-vod/vod-content/abc/1-2-3-4-5/kaltura/desc_foobar/aaa/ysign1=null,abcID=0,from=zen,pfx,region=0000,sfx,ts=63cd1709/manifest.mpd",
    }
