import httpx
import pytest

from anicli_api.decoders import Aniboom

ANIBOOM_RAW_RESPONSE = """
<div id="video" data-parameters="{&quot;id&quot;:&quot;Jo9ql8ZeqnW&quot;,&quot;error&quot;:&quot;\/video-error\/Jo9ql8ZeqnW&quot;,&quot;domain&quot;:&quot;animego.org&quot;,&quot;cdn&quot;:&quot;\/cdn\/foobarW&quot;,&quot;counter&quot;:&quot;\/counter\/foobar&quot;,&quot;duration&quot;:1511,&quot;poster&quot;:&quot;https:\/\/i1.fakeboom-img.com\/jo\/foobar\/mqdefault.jpg&quot;,&quot;thumbnails&quot;:&quot;https:\/\/i1.fakeboom-img.com\/jo\/foobar\/thumbnails\/thumbnails.vtt&quot;,&quot;dash&quot;:&quot;{\&quot;src\&quot;:\&quot;https:\\\/\\\/kekistan.cdn-fakeaniboom.com\\\/jo\\\/abcdef123\\\/111hash.mpd\&quot;,\&quot;type\&quot;:\&quot;application\\\/dash+xml\&quot;}&quot;,&quot;hls&quot;:&quot;{\&quot;src\&quot;:\&quot;https:\\\/\\\/kekistan.cdn-fakeaniboom.com\\\/jo\\\/abcdefg123\\\/master.m3u8\&quot;,\&quot;type\&quot;:\&quot;application\\\/x-mpegURL\&quot;}&quot;,&quot;quality&quot;:true,&quot;qualityVideo&quot;:1080,&quot;vast&quot;:true,&quot;country&quot;:&quot;RU&quot;,&quot;platform&quot;:&quot;Android&quot;,&quot;rating&quot;:&quot;16+&quot;}"></div><div class="vjs-contextmenu" id="contextmenu">aniboom.one</div>
"""


ANIBOOM_M3U8_DATA = """#EXTM3U
#EXT-X-VERSION:7
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="group_A1",NAME="audio_1",DEFAULT=YES,URI="media_1.m3u8"
#EXT-X-STREAM-INF:BANDWIDTH=593867,RESOLUTION=640x360,CODECS="avc1.640028,mp4a.40.2",AUDIO="group_A1"
media_0.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=943867,RESOLUTION=854x480,CODECS="avc1.640028,mp4a.40.2",AUDIO="group_A1"
media_2.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1593867,RESOLUTION=1280x720,CODECS="avc1.640028,mp4a.40.2",AUDIO="group_A1"
media_4.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2893867,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",AUDIO="group_A1"
media_6.m3u8
"""


def mock_aniboom_transport():
    def handler(request: httpx.Request):
        if str(request.url).endswith("m3u8"):
            return httpx.Response(200, text=ANIBOOM_M3U8_DATA)
        return httpx.Response(200, text=ANIBOOM_RAW_RESPONSE)

    transport = httpx.MockTransport(handler)
    return transport


def test_eq_cmp_aniboom():
    assert "https://aniboom.one/embed/asdasdasfasf" == Aniboom()


def test_ne_cmp_aniboom():
    assert "https://google.com" != Aniboom()


def test_parse_aniboom():
    result = Aniboom.parse("https://fakeaniboom.one/embed/fake_aniboom_la-la-la", transport=mock_aniboom_transport())
    assert [r.dict() for r in result] == [
        {'type': 'm3u8', 'quality': 360, 'url': 'https://kekistan.cdn-fakeaniboom.com/jo/abcdefg123/media_0.m3u8',
         'extra_headers': {
             'referer': 'https://aniboom.one/',
             'accept-language': 'ru-RU', 'user-agent':
             'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36'}
         },
        {'type': 'm3u8',
         'quality': 480,
         'url': 'https://kekistan.cdn-fakeaniboom.com/jo/abcdefg123/media_2.m3u8',
         'extra_headers': {
             'referer': 'https://aniboom.one/',
             'accept-language': 'ru-RU',
             'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36'}
         },
        {'type': 'm3u8',
         'quality': 720,
         'url': 'https://kekistan.cdn-fakeaniboom.com/jo/abcdefg123/media_4.m3u8',
         'extra_headers': {
             'referer': 'https://aniboom.one/',
             'accept-language': 'ru-RU',
             'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36'}},
        {'type': 'm3u8',
         'quality': 1080,
         'url': 'https://kekistan.cdn-fakeaniboom.com/jo/abcdefg123/media_6.m3u8',
         'extra_headers': {
             'referer': 'https://aniboom.one/',
             'accept-language': 'ru-RU',
             'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36'}},
        {'type': 'mpd',
         'quality': 1080,
         'url': 'https://kekistan.cdn-fakeaniboom.com/jo/abcdef123/111hash.mpd',
         'extra_headers': {
             'referer': 'https://aniboom.one/',
             'accept-language': 'ru-RU',
             'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36'}}]


@pytest.mark.asyncio
async def test_async_parse_aniboom():
    result = await Aniboom.async_parse("https://aniboom.one/embed/fake_aniboom_la-la-la",
                                       transport=mock_aniboom_transport())
    print([r.dict() for r in result])
    assert [r.dict() for r in result] == [
        {'type': 'm3u8', 'quality': 360, 'url': 'https://kekistan.cdn-fakeaniboom.com/jo/abcdefg123/media_0.m3u8',
         'extra_headers': {
             'referer': 'https://aniboom.one/',
             'accept-language': 'ru-RU', 'user-agent':
             'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36'}
         },
        {'type': 'm3u8',
         'quality': 480,
         'url': 'https://kekistan.cdn-fakeaniboom.com/jo/abcdefg123/media_2.m3u8',
         'extra_headers': {
             'referer': 'https://aniboom.one/',
             'accept-language': 'ru-RU',
             'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36'}
         },
        {'type': 'm3u8',
         'quality': 720,
         'url': 'https://kekistan.cdn-fakeaniboom.com/jo/abcdefg123/media_4.m3u8',
         'extra_headers': {
             'referer': 'https://aniboom.one/',
             'accept-language': 'ru-RU',
             'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36'}},
        {'type': 'm3u8',
         'quality': 1080,
         'url': 'https://kekistan.cdn-fakeaniboom.com/jo/abcdefg123/media_6.m3u8',
         'extra_headers': {
             'referer': 'https://aniboom.one/',
             'accept-language': 'ru-RU',
             'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36'}},
        {'type': 'mpd',
         'quality': 1080,
         'url': 'https://kekistan.cdn-fakeaniboom.com/jo/abcdef123/111hash.mpd',
         'extra_headers': {
             'referer': 'https://aniboom.one/',
             'accept-language': 'ru-RU',
             'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36'}}]
