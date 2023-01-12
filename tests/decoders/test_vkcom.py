import httpx
import pytest

from anicli_api.decoders import VkCom

RAW_RESPONSE = """    <source src="https://vkvd141.mycdn.me/?expires=777&amp;srcIp=127.0.0.1&amp;pr=40&amp;srcAg=CHROME_ANDROID&amp;ms=45.136.21.143&amp;type=5&amp;sig=iaKifRZETM4&amp;ct=0&amp;urls=192.168.0.1&amp;clientType=13&amp;appId=1337&amp;id=0" type="video/mp4" /><source src="https://vkvd141.mycdn.me/?expires=777&amp;srcIp=127.0.0.1&amp;pr=40&amp;srcAg=CHROME_ANDROID&amp;ms=45.136.21.143&amp;type=3&amp;sig=J_mMef208dE&amp;ct=0&amp;urls=192.168.0.1&amp;clientType=13&amp;appId=1337&amp;id=0" type="video/mp4" /><source src="https://vkvd141.mycdn.me/?expires=777&amp;srcIp=127.0.0.1&amp;pr=40&amp;srcAg=CHROME_ANDROID&amp;ms=45.136.21.143&amp;type=2&amp;sig=FFGnf12Uc8M&amp;ct=0&amp;urls=192.168.0.1&amp;clientType=13&amp;appId=1337&amp;id=0" type="video/mp4" /><source src="https://vkvd141.mycdn.me/?expires=777&amp;srcIp=127.0.0.1&amp;pr=40&amp;srcAg=CHROME_ANDROID&amp;ms=45.136.21.143&amp;type=1&amp;sig=EZ5hxDpEfw0&amp;ct=0&amp;urls=192.168.0.1&amp;clientType=13&amp;appId=1337&amp;id=0" type="video/mp4" /><source src="https://vkvd141.mycdn.me/?expires=777&amp;srcIp=127.0.0.1&amp;pr=40&amp;srcAg=CHROME_ANDROID&amp;ms=45.136.21.143&amp;type=0&amp;sig=p-0c0r6wojM&amp;ct=0&amp;urls=192.168.0.1&amp;clientType=13&amp;appId=1337&amp;id=0" type="video/mp4" /><source src="https://vkvd141.mycdn.me/?expires=777&amp;srcIp=127.0.0.1&amp;pr=40&amp;srcAg=CHROME_ANDROID&amp;ms=45.136.21.143&amp;type=4&amp;sig=97i_TwULgP8&amp;ct=0&amp;urls=192.168.0.1&amp;clientType=13&amp;appId=1337&amp;id=0" type="video/mp4" />"""

def mock_transport():
    def handler(_):
        return httpx.Response(200, text=RAW_RESPONSE)

    transport = httpx.MockTransport(handler)
    return transport


def test_cmp():
    assert "https://google.com" != VkCom()
    assert "https://vk.com/video_ext.php?oid=durov&id=0&hash=fakehash" == VkCom()


def test_parse():
    result = VkCom.parse("https://vk.com/video_ext.php?oid=durov&id=0&hash=fakehash", transport=mock_transport())
    assert result[0].dict() == {
        'type': 'mp4',
        'quality': 1080,
        'url': 'https://vkvd141.mycdn.me/?expires=777&srcIp=127.0.0.1&pr=40&srcAg=CHROME_ANDROID&ms=45.136.21.143&type=5&sig=iaKifRZETM4&ct=0&urls=192.168.0.1&clientType=13&appId=1337&id=0',
        'extra_headers': {}}


@pytest.mark.asyncio
async def test_async_parse():
    result = await VkCom.async_parse(
        "https://vk.com/video_ext.php?oid=durov&id=0&hash=fakehash", transport=mock_transport()
    )
    assert result[0].dict() == {
        'type': 'mp4',
        'quality': 1080,
        'url': 'https://vkvd141.mycdn.me/?expires=777&srcIp=127.0.0.1&pr=40&srcAg=CHROME_ANDROID&ms=45.136.21.143&type=5&sig=iaKifRZETM4&ct=0&urls=192.168.0.1&clientType=13&appId=1337&id=0',
        'extra_headers': {}}
