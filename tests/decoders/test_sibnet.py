import pytest
import httpx

from anicli_api.decoders import Sibnet

RAW_RESPONSE = """;player.logobrand({destination: "/video3036546?utm_source=player&utm_medium=video&utm_campaign=EMBED"});player.src([{src: "/v/67e0cd542b041cb86d7b05d32cbabce1/3036546.mp4", type: "video/mp4"},]);player.persistvolume({namespace: "Sibnet-Volume"});var vastAd = player.vastClient({adTagUrl: "//advast.sibnet.ru/getcode.php?"""


def mock_transport():
    def handler(request: httpx.Request):
        return httpx.Response(200, text=RAW_RESPONSE)
    transport = httpx.MockTransport(handler)
    return transport


def test_cmp_sibnet():
    assert "https://google.com" != Sibnet()
    assert "https://video.sibnet.ru/foobar" == Sibnet()


def test_parse():
    result = Sibnet.parse("https://video.sibnet.ru/fakevideo", transport=mock_transport())
    assert result[0].dict() == {
        'type': 'mp4',
        'quality': 480,
        'url': 'https://video.sibnet.ru/v/67e0cd542b041cb86d7b05d32cbabce1/3036546.mp4',
        'extra_headers': {'Referer': 'https://video.sibnet.ru/fakevideo'}}


@pytest.mark.asyncio
async def test_async_parse():
    result = await Sibnet.async_parse("https://video.sibnet.ru/fakevideo", transport=mock_transport())
    assert result[0].dict() == {
            'type': 'mp4',
            'quality': 480,
            'url': 'https://video.sibnet.ru/v/67e0cd542b041cb86d7b05d32cbabce1/3036546.mp4',
            'extra_headers': {'Referer': 'https://video.sibnet.ru/fakevideo'}}
