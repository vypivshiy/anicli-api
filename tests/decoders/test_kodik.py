import httpx
import pytest

from anicli_api.decoders import Kodik


KODIK_RAW_RESPONSE = """
...
var type = "seria";
var videoId = "1025427";
var urlParams = '{"d":"animeeee.kek","d_sign":"d_signhash123","pd":"fakekodik.com","pd_sign":"pd_sign123hash","ref":"animeeee.kek","ref_sign":"ref_signhash123","translations":false}';
var autoResume = false;
var fullscreenLockOrientation = true
var videoInfo = {};
...
<td><div class='get_code_copy' data-code='//fakekodik.com/seria/123/hashfakeseria/720p'>TEST</div></td>
...

videoInfo.type = 'seria'; 
videoInfo.hash = 'b2f2a9d450ff2b2374d37c768e1b104e'; 
videoInfo.id = '1025427'; 
"""


KODIK_API_JSON = {"advert_script": "", "default": 360, "domain": "animeeee.kek", "ip": "192.168.0.1",
                  "links": {"360": [{"src": '=QDct5CM2MzX0NXZ09yL', "type": "application/x-mpegURL"}],
                            "480": [{"src": '=QDct5CM4QzX0NXZ09yL', "type": "application/x-mpegURL"}],
                            "720": [{"src": "=QDct5CMyczX0NXZ09yL", "type": "application/x-mpegURL"}]}
                  }


def mock_kodik_transport():
    def handler(request: httpx.Request):
        if request.method == "GET":
            return httpx.Response(200, text=KODIK_RAW_RESPONSE)
        return httpx.Response(200, json=KODIK_API_JSON)

    transport = httpx.MockTransport(handler)
    return transport


@pytest.mark.parametrize("url_encoded,result",
                         [('0AXbusGNfNHbpJWZk9lcvZ2Xl1WauF2Lt92YuoXYiJXYi92bm9yL',
                           "https://foobarbaz.com/anime_for_debils_4k.mp4"),

                          ("'0AXbusGNfNHbpJWZk9lcvZ2Xl1WauF2Lt92YuoXYiJXYi92bm9yL6MHc0RHa'",
                           "https://foobarbaz.com/anime_for_debils_4k.mp4")])
def test_decode(url_encoded, result):
    assert Kodik.decode(url_encoded) == result


def test_eq_cmp_kodik():
    assert "https://kodikfake.kekis/seria/00/foobar/100p" == Kodik()


def test_ne_cmp_kodik():
    assert "https://google.com" != Kodik()


def test_parse_kodik():
    result = Kodik.parse("https://kodikfake.fake/seria/00/foobar/100p", transport=mock_kodik_transport())
    assert [r.dict() for r in result] == [
        {'type': 'm3u8', 'quality': 360, 'url': 'https://test_360.mp4', 'extra_headers': {}},
        {'type': 'm3u8', 'quality': 480, 'url': 'https://test_480.mp4', 'extra_headers': {}},
        {'type': 'm3u8', 'quality': 720, 'url': 'https://test_720.mp4', 'extra_headers': {}}
    ]


@pytest.mark.asyncio
async def test_async_parse_kodik():
    result = await Kodik.async_parse("https://kodikfake.fake/seria/00/foobar/100p", transport=mock_kodik_transport())
    assert [v.dict() for v in result] == [
        {'type': 'm3u8', 'quality': 360, 'url': 'https://test_360.mp4', 'extra_headers': {}},
        {'type': 'm3u8', 'quality': 480, 'url': 'https://test_480.mp4', 'extra_headers': {}},
        {'type': 'm3u8', 'quality': 720, 'url': 'https://test_720.mp4', 'extra_headers': {}}
    ]
